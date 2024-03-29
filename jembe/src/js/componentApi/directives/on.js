import { kebabCase, camelCase, debounce, isNumeric } from '../utils'

export function registerListener(component, el, event, modifiers, expression, extraVars = () => { }, mutated=false) {
    const options = {
        passive: modifiers.includes('passive'),
    };

    if (modifiers.includes('camel')) {
        event = camelCase(event);
    }

    let handler, listenerTarget

    if (modifiers.includes('away')) {
        listenerTarget = document

        handler = e => {
            // Don't do anything if the click came from the element or within it.
            if (el.contains(e.target)) return

            // Don't do anything if this element isn't currently visible.
            if (el.offsetWidth < 1 && el.offsetHeight < 1) return

            // Now that we are sure the element is visible, AND the click
            // is from outside it, let's run the expression.
            runListenerHandler(component, expression, e, extraVars, el)

            if (modifiers.includes('once')) {
                document.removeEventListener(event, handler, options)
            }
        }
    } else {
        listenerTarget = modifiers.includes('window')
            ? window : (modifiers.includes('document') ? document : el)

        handler = e => {
            // Remove this global event handler if the element that declared it
            // has been removed. It's now stale.
            if (listenerTarget === window || listenerTarget === document) {
                if (!document.body.contains(el)) {
                    listenerTarget.removeEventListener(event, handler, options)
                    return
                }
            }

            if (isKeyEvent(event)) {
                if (isListeningForASpecificKeyThatHasntBeenPressed(e, modifiers)) {
                    return
                }
            }

            if (modifiers.includes('prevent')) e.preventDefault()
            if (modifiers.includes('stop')) e.stopPropagation()

            // If the .self modifier isn't present, or if it is present and
            // the target element matches the element we are registering the
            // event on, run the handler
            const target = e.type === 'ready'? e.detail['target'] : e.target
            if (!modifiers.includes('self') || target === el) {
                const returnValue = runListenerHandler(component, expression, e, extraVars, el)

                returnValue.then(value => {
                    if (value === false) {
                        e.preventDefault()
                    } else {
                        if (modifiers.includes('once')) {
                            listenerTarget.removeEventListener(event, handler, options)
                        }
                    }
                })
            }
        }
    }

    // if expression adds commands to jembeClient
    // then execute jembeClient comands and refresh page
    if (!modifiers.includes('defer')) {
        handler = ((component, func) => {
            return e => {
                component.$jmb.callsCommands = false
                func(e)
                if (component.$jmb.callsCommands === true) {
                    component.$jmb.executeCommands(!modifiers.includes('nonblocking'))
                }
            }
        })(component, handler)
    }

    if (modifiers.includes('debounce')) {
        let nextModifier = modifiers[modifiers.indexOf('debounce') + 1] || 'invalid-wait'
        let wait = isNumeric(nextModifier.split('ms')[0]) ? Number(nextModifier.split('ms')[0]) : 250
        handler = debounce(handler, wait, this)
    }
    const delayModifier = modifiers.find(m => m.startsWith('delay'))
    if (delayModifier !== undefined) {
        const delayId = delayModifier.split('-').slice(1).join('-')
        let delayTime = modifiers[modifiers.indexOf(delayModifier) + 1]
        delayTime = delayTime !== undefined && delayTime.endsWith('ms') ? parseInt(delayTime.substr(0, delayTime.length - 2)) : 250
        if (delayId === undefined) {
            handler = ((comp, func) => {
                return (e) => {
                    var timerId = window.setTimeout(function () { func(e) }, delayTime);
                    comp.unnamedTimers.push(timerId)

                }
            })(component, handler)
        } else {
            let start = new Date().getTime()
            if (component.originalComponentNamedTimers[delayId] !== undefined) {
                start = component.originalComponentNamedTimers[delayId].start
                delayTime = delayTime - ((new Date().getTime()) - start)
            }

            if (delayTime > 0) {
                handler = ((comp, func) => {
                    return (e) => {
                        var timerId = window.setTimeout(function () {
                            delete comp.namedTimers[delayId]
                            window.clearTimeout(timerId)
                            func(e);
                        }, delayTime);
                        comp.namedTimers[delayId] = {
                            id: timerId,
                            start: start
                        }
                    }
                })(component, handler)
            } else {
                //run emidiatly like on:ready
                component.nextTickStack.push(() => {
                    handler(new CustomEvent('ready', {detail: {target: el }}))
                })
                return // dont register listener nor 
            }
        }
    }

    if (event === 'ready') {
        if (! (mutated && modifiers.includes("once"))) {
            component.nextTickStack.push(() => {
                handler(new CustomEvent('ready', {detail:{ target: el }}))
            })
        }
    } else {
        // register listener so it can be removed when morphing dom
        if (el.__jmb_listeners === undefined) {
            el.__jmb_listeners = []
        }
        el.__jmb_listeners.push([listenerTarget, event, handler, options])
        listenerTarget.addEventListener(event, handler, options)
    }
}

function runListenerHandler(component, expression, e, extraVars, self) {
    const target = e.type === 'ready'? e.detail['target'] : e.target
    return component.evaluateCommandExpression(target, expression, () => {
        return { ...extraVars(), '$event': e, '$self': self }
    })
}

function isKeyEvent(event) {
    return ['keydown', 'keyup'].includes(event)
}

function isListeningForASpecificKeyThatHasntBeenPressed(e, modifiers) {
    let keyModifiers = modifiers.filter(i => {
        return !['window', 'document', 'prevent', 'stop'].includes(i)
    })

    if (keyModifiers.includes('debounce')) {
        let debounceIndex = keyModifiers.indexOf('debounce')
        keyModifiers.splice(debounceIndex, isNumeric((keyModifiers[debounceIndex + 1] || 'invalid-wait').split('ms')[0]) ? 2 : 1)
    }

    // If no modifier is specified, we'll call it a press.
    if (keyModifiers.length === 0) return false

    // If one is passed, AND it matches the key pressed, we'll call it a press.
    if (keyModifiers.length === 1 && keyModifiers[0] === keyToModifier(e.key)) return false

    // The user is listening for key combinations.
    const systemKeyModifiers = ['ctrl', 'shift', 'alt', 'meta', 'cmd', 'super']
    const selectedSystemKeyModifiers = systemKeyModifiers.filter(modifier => keyModifiers.includes(modifier))

    keyModifiers = keyModifiers.filter(i => !selectedSystemKeyModifiers.includes(i))

    if (selectedSystemKeyModifiers.length > 0) {
        const activelyPressedKeyModifiers = selectedSystemKeyModifiers.filter(modifier => {
            // Alias "cmd" and "super" to "meta"
            if (modifier === 'cmd' || modifier === 'super') modifier = 'meta'

            return e[`${modifier}Key`]
        })

        // If all the modifiers selected are pressed, ...
        if (activelyPressedKeyModifiers.length === selectedSystemKeyModifiers.length) {
            // AND the remaining key is pressed as well. It's a press.
            if (keyModifiers[0] === keyToModifier(e.key)) return false
        }
    }

    // We'll call it NOT a valid keypress.
    return true
}

function keyToModifier(key) {
    switch (key) {
        case '/':
            return 'slash'
        case ' ':
        case 'Spacebar':
            return 'space'
        default:
            return key && kebabCase(key)
    }
}
