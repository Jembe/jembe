/**
 * Havily modified alpine.js 2.8.1 to:
 *  - user 'jmb-' instead 'x-' as prefix
 *  - jembe component becomes alpine component
 *  - jembe compoenent state params and actions becomes alpine x-data params and actions
 *  - when jembe state params are changed or action is called in x-data,
 *     call appropriate function on jembeclient
 *  - support local variables accessible only in alpine componetn with jmb-local,
 *    jmb-init, jmb-update directives
 *  - alpine/copmonentapi local variables are accessible with $local prefix
 *  - $node references current node on witch action is executed (jmb-on etc.)
 *  - add $jmb magic variable to reference jembeClient.component(this) to access set, cal display emit and init commands
 *  - when componentApi action changes any state variable are call any jembe action jembeClient.executeCommands() will be called
 *    if there is not defer modifier
 *  
 * modification are enclosed with @jembeModification
 */
import { walk, saferEval, saferEvalNoReturn, getXAttrs, debounce, convertClassStringToArray, TRANSITION_CANCELLED } from './utils'
import { handleForDirective } from './directives/for'
import { handleAttributeBindingDirective } from './directives/bind'
import { handleTextDirective } from './directives/text'
import { handleHtmlDirective } from './directives/html'
import { handleShowDirective } from './directives/show'
import { handleIfDirective } from './directives/if'
import { registerModelListener } from './directives/model'
import { registerListener } from './directives/on'
import { unwrap, wrap } from './observable'
// import Alpine from './index'
import JMB from './magic/jmb'

export default class Component {
    // @jembeModification
    // constructor is separated in constructor + mount and havily modified to support
    // jembeComponents
    // mount do actual initialisation of component cunstructor don't do anything
    constructor(el) {
        this.$el = el

        this.mounted = false
        this.jembeClient = undefined
        this.execName = undefined
        this.state = undefined
        this.actions = undefined
        this.unnamedTimers = []
        this.namedTimers = {}
        this.originalComponentNamedTimers = {}
    }
    /**
     * @param {Component} originalComponent 
     */
    mount(jembeClient, execName, state, actions, originalComponent = undefined) {
        if (this.mounted
            && (
                this.jembeClient !== jembeClient
                || this.execName !== execName
            )) {
            throw (`Mounting ComponetApi for new component: ${this.execName} -> ${execName}`)
        } else {
            this.mounted = true

            this.jembeClient = jembeClient
            this.execName = execName
            this.$jmb = new JMB(this.jembeClient, this.execName)
        }
        if (originalComponent !== undefined) {
            this.originalComponentNamedTimers = originalComponent.namedTimers
        }

        this.state = JSON.parse(JSON.stringify(state));
        this.actions = actions

        for (const stateName of Object.keys(this.state)) {
            if (this.actions.includes(stateName)) {
                console.warn(`state param '${stateName}' overrides action with same name in component ${this.execName}!`)
            }
        }

        const localAttr = this.$el.getAttribute('jmb-local')
        const localExpression = (localAttr === '' || localAttr === null) ? '{}' : localAttr
        const initAttr = this.$el.getAttribute('jmb-init')
        const initExpression = (initAttr === '' || initAttr === null) ? '{}' : initAttr
        const updateAttr = this.$el.getAttribute('jmb-update')
        const updateExpression = (updateAttr === '' || updateAttr === null) ? '{}' : updateAttr
        let dataExtras = {
            $el: this.$el,
            $jmb: this.$jmb
        }

        let canonicalComponentElementReference = this.$el

        // Object.entries(Alpine.magicProperties).forEach(([name, callback]) => {
        //     Object.defineProperty(dataExtras, `$${name}`, { get: function () { return callback(canonicalComponentElementReference) } });
        // })

        this.unobservedData = {
            $local: (originalComponent === undefined)
                ? saferEval(this.$el, localExpression, dataExtras)
                : originalComponent.getUnobservedData()['$local']
        }
        // add actions
        this.actions.forEach(actionName => {
            Object.defineProperty(
                this.unobservedData,
                `${actionName}`,
                { get: function () { return (...params) => { this.$jmb.call(actionName, ...params) } } }
            )
        })
        // add states
        Object.entries(this.state).forEach(([name, value]) => {
            this.unobservedData[name] = value
        })
        // TODO add watcher to state data and fire init commands accoringly

        /* IE11-ONLY:START */
        // For IE11, add our magic properties to the original data for access.
        // The Proxy polyfill does not allow properties to be added after creation.
        // this.unobservedData.$el = null
        // this.unobservedData.$refs = null
        // this.unobservedData.$nextTick = null
        // this.unobservedData.$watch = null
        // this.unobservedData.$jmb = null
        // The IE build uses a proxy polyfill which doesn't allow properties
        // to be defined after the proxy object is created so,
        // for IE only, we need to define our helpers earlier.
        // Object.entries(Alpine.magicProperties).forEach(([name, callback]) => {
        //     Object.defineProperty(this.unobservedData, `$${name}`, { get: function () { return callback(canonicalComponentElementReference, this.$el) } });
        // })
        /* IE11-ONLY:END */

        // Construct a Proxy-based observable. This will be used to handle reactivity.
        let { membrane, data } = this.wrapDataInObservable(this.unobservedData)
        this.$data = data
        this.membrane = membrane

        // After making user-supplied data methods reactive, we can now add
        // our magic properties to the original data for access.
        this.unobservedData.$el = this.$el
        this.unobservedData.$refs = this.getRefsProxy()
        this.unobservedData.$jmb = this.$jmb

        this.nextTickStack = []
        this.unobservedData.$nextTick = (callback) => {
            this.nextTickStack.push(callback)
        }

        this.watchers = {}
        this.unobservedData.$watch = (property, callback) => {
            if (!this.watchers[property]) this.watchers[property] = []
            this.watchers[property].push(callback)
        }


        /* MODERN-ONLY:START */
        // We remove this piece of code from the legacy build.
        // In IE11, we have already defined our helpers at this point.

        // Register custom magic properties.
        // Object.entries(Alpine.magicProperties).forEach(([name, callback]) => {
        //     Object.defineProperty(this.unobservedData, `$${name}`, { get: function () { return callback(canonicalComponentElementReference, this.$el) } });
        // })
        /* MODERN-ONLY:END */

        this.showDirectiveStack = []
        this.showDirectiveLastElement

        // Alpine.onBeforeComponentInitializeds.forEach(callback => callback(this))

        var initReturnedCallback
        // If jmb-init is present AND we aren't cloning (skip jmb-init on clone)
        if (originalComponent === undefined && initExpression) {
            // We want to allow data manipulation, but not trigger DOM updates just yet.
            // We haven't even initialized the elements with their Alpine bindings. I mean c'mon.
            this.pauseReactivity = true
            initReturnedCallback = this.evaluateReturnExpression(this.$el, initExpression)
            this.pauseReactivity = false
        } else if (originalComponent !== undefined && updateExpression) {
            this.pauseReactivity = true
            initReturnedCallback = this.evaluateReturnExpression(this.$el, updateExpression)
            this.pauseReactivity = false
        }

        // Register all our listeners and set all our attribute bindings.
        // If we're cloning a component, the third parameter ensures no duplicate
        // event listeners are registered (the mutation observer will take care of them)
        // this.initializeElements(this.$el, () => { }, originalComponent === undefined)
        this.initializeElements(this.$el, () => { })

        // Use mutation observer to detect new elements being added within this component at run-time.
        // Alpine's just so darn flexible amirite?
        this.listenForNewElementsToInitialize()

        if (typeof initReturnedCallback === 'function') {
            // Run the callback returned from the "jmb-init" hook to allow the user to do stuff after
            // Alpine's got it's grubby little paws all over everything.
            initReturnedCallback.call(this.$data)
        }

        // setTimeout(() => {
        //     Alpine.onComponentInitializeds.forEach(callback => callback(this))
        // }, 0)
    }
    unmount() {
        for (const timerId of this.unnamedTimers) {
            window.clearTimeout(timerId)
        }
        for (const [timerName, timerInfo] of Object.entries(this.namedTimers)) {
            window.clearTimeout(timerInfo.id)
        }
    }
    getUnobservedData() {
        return unwrap(this.membrane, this.$data)
    }

    findTargetPathInData(tree, target, key = "", level = 0) {
        if (Object.is(tree, target)) {
            return key
        }
        const treeIsArray = Array.isArray(tree)
        for (const [name, value] of Object.entries(tree)) {
            if (!((level === 0 && name.startsWith('$')) || (treeIsArray && name === 'length')) && typeof value === "object") {
                const subpath = this.findTargetPathInData(value, target, name, level + 1)
                if (subpath !== undefined) {
                    return key !== "" ? `${key}.${subpath}` : subpath
                }
            }
        }
    }
    wrapDataInObservable(data) {
        var self = this

        let updateDom = debounce(function () {
            self.updateElements(self.$el)
        }, 0)

        return wrap(data, (target, key) => {
            // check if is state variable by compoaring target
            let path = this.findTargetPathInData(this.unobservedData, target)
            if (path !== undefined) {
                this.$jmb.set(path === "" ? key : `${path}.${key}`, target[key])
            }
            if (Object.is(target, this.unobservedData) && Object.keys(this.state).includes(key)) {
                this.$jmb.set(key, target[key])
            }
            if (self.watchers[key]) {
                // If there's a watcher for this specific key, run it.
                self.watchers[key].forEach(callback => callback(target[key]))
            } else if (Array.isArray(target)) {
                // Arrays are special cases, if any of the items change, we consider the array as mutated.
                Object.keys(self.watchers)
                    .forEach(fullDotNotationKey => {
                        let dotNotationParts = fullDotNotationKey.split('.')

                        // Ignore length mutations since they would result in duplicate calls.
                        // For example, when calling push, we would get a mutation for the item's key
                        // and a second mutation for the length property.
                        if (key === 'length') return

                        dotNotationParts.reduce((comparisonData, part) => {
                            if (Object.is(target, comparisonData[part])) {
                                self.watchers[fullDotNotationKey].forEach(callback => callback(target))
                            }

                            return comparisonData[part]
                        }, self.unobservedData)
                    })
            } else {
                // Let's walk through the watchers with "dot-notation" (foo.bar) and see
                // if this mutation fits any of them.
                Object.keys(self.watchers)
                    .filter(i => i.includes('.'))
                    .forEach(fullDotNotationKey => {
                        let dotNotationParts = fullDotNotationKey.split('.')

                        // If this dot-notation watcher's last "part" doesn't match the current
                        // key, then skip it early for performance reasons.
                        if (key !== dotNotationParts[dotNotationParts.length - 1]) return

                        // Now, walk through the dot-notation "parts" recursively to find
                        // a match, and call the watcher if one's found.
                        dotNotationParts.reduce((comparisonData, part) => {
                            if (Object.is(target, comparisonData)) {
                                // Run the watchers.
                                self.watchers[fullDotNotationKey].forEach(callback => callback(target[key]))
                            }

                            return comparisonData[part]
                        }, self.unobservedData)
                    })
            }

            // Don't react to data changes for cases like the `jmb-created` hook.
            if (self.pauseReactivity) return

            updateDom()
        })
    }

    walkAndSkipNestedComponents(el, callback, initializeComponentCallback = () => { }) {
        walk(el, el => {
            // We've hit a component.
            if (el.hasAttribute('jmb-name') || el.hasAttribute('jmb-placeholder')) {
                // If it's not the current one.
                if (!el.isSameNode(this.$el)) {
                    // Initialize it if it's not.
                    if (!el.__jmb) initializeComponentCallback(el)

                    // Now we'll let that sub-component deal with itself.
                    return false
                }
            }

            return callback(el)
        })
    }

    initializeElements(rootEl, extraVars = () => { }) {
        this.walkAndSkipNestedComponents(rootEl, el => {
            // Don't touch spawns from for loop
            if (el.__jmb_for_key !== undefined) return false

            // Don't touch spawns from if directives
            if (el.__jmb_inserted_me !== undefined) return false

            this.initializeElement(el, extraVars)
        }, el => {
            el.__jmb = new Component(el)
        })

        this.executeAndClearRemainingShowDirectiveStack()

        this.executeAndClearNextTickStack(rootEl)
    }

    initializeElement(el, extraVars) {
        // To support class attribute merging, we have to know what the element's
        // original class attribute looked like for reference.
        if (el.hasAttribute('class') && getXAttrs(el, this).length > 0) {
            el.__jmb_original_classes = convertClassStringToArray(el.getAttribute('class'))
        }
        // remove all existing listeners
        if (el.__jmb_listeners !== undefined) {
            for (const [ltarget, event, handler, options] of el.__jmb_listeners) {
                ltarget.removeEventListener(event, handler, options)
            }
            el.__jmb_listeners = undefined
        }
        this.registerListeners(el, extraVars)
        // shouldRegisterListeners && this.registerListeners(el, extraVars)
        this.resolveBoundAttributes(el, true, extraVars)
    }

    updateElements(rootEl, extraVars = () => { }) {
        this.walkAndSkipNestedComponents(rootEl, el => {
            // Don't touch spawns from for loop (and check if the root is actually a for loop in a parent, don't skip it.)
            if (el.__jmb_for_key !== undefined && !el.isSameNode(this.$el)) return false

            this.updateElement(el, extraVars)
        }, el => {
            el.__jmb = new Component(el)
        })

        this.executeAndClearRemainingShowDirectiveStack()

        this.executeAndClearNextTickStack(rootEl)
    }

    executeAndClearNextTickStack(el) {
        // Skip spawns from alpine directives
        if (el === this.$el && this.nextTickStack.length > 0) {
            // We run the tick stack after the next frame to allow any
            // running transitions to pass the initial show stage.
            requestAnimationFrame(() => {
                while (this.nextTickStack.length > 0) {
                    this.nextTickStack.shift()()
                }
            })
        }
    }

    executeAndClearRemainingShowDirectiveStack() {
        // The goal here is to start all the jmb-show transitions
        // and build a nested promise chain so that elements
        // only hide when the children are finished hiding.
        this.showDirectiveStack.reverse().map(handler => {
            return new Promise((resolve, reject) => {
                handler(resolve, reject)
            })
        }).reduce((promiseChain, promise) => {
            return promiseChain.then(() => {
                return promise.then(finishElement => {
                    finishElement()
                })
            })
        }, Promise.resolve(() => { })).catch(e => {
            if (e !== TRANSITION_CANCELLED) throw e
        })

        // We've processed the handler stack. let's clear it.
        this.showDirectiveStack = []
        this.showDirectiveLastElement = undefined
    }

    updateElement(el, extraVars) {
        this.resolveBoundAttributes(el, false, extraVars)
    }

    registerListeners(el, extraVars) {
        getXAttrs(el, this).forEach(({ type, value, modifiers, expression }) => {
            switch (type) {
                case 'on':
                    registerListener(this, el, value, modifiers, expression, extraVars)
                    break;

                case 'model':
                    registerModelListener(this, el, modifiers, expression, extraVars)
                    break;
                default:
                    break;
            }
        })
    }

    resolveBoundAttributes(el, initialUpdate = false, extraVars) {
        let attrs = getXAttrs(el, this)
        attrs.forEach(({ type, value, modifiers, expression }) => {
            switch (type) {
                case 'model':
                    handleAttributeBindingDirective(this, el, 'value', expression, extraVars, type, modifiers)
                    break;

                case 'bind':
                    // The :key binding on an jmb-for is special, ignore it.
                    if (el.tagName.toLowerCase() === 'template' && value === 'key') return

                    handleAttributeBindingDirective(this, el, value, expression, extraVars, type, modifiers)
                    break;

                case 'text':
                    var output = this.evaluateReturnExpression(el, expression, extraVars);

                    handleTextDirective(el, output, expression)
                    break;

                case 'html':
                    handleHtmlDirective(this, el, expression, extraVars)
                    break;

                case 'show':
                    var output = this.evaluateReturnExpression(el, expression, extraVars)

                    handleShowDirective(this, el, output, modifiers, initialUpdate)
                    break;

                case 'if':
                    // If this element also has jmb-for on it, don't process jmb-if.
                    // We will let the "jmb-for" directive handle the "if"ing.
                    if (attrs.some(i => i.type === 'for')) return

                    var output = this.evaluateReturnExpression(el, expression, extraVars)

                    handleIfDirective(this, el, output, initialUpdate, extraVars)
                    break;

                case 'for':
                    handleForDirective(this, el, expression, initialUpdate, extraVars)
                    break;

                case 'cloak':
                    el.removeAttribute('jmb-cloak')
                    break;

                default:
                    break;
            }
        })
    }

    evaluateReturnExpression(el, expression, extraVars = () => { }) {
        return saferEval(el, expression, this.$data, {
            ...extraVars(),
            $dispatch: this.getDispatchFunction(el),
        })
    }

    evaluateCommandExpression(el, expression, extraVars = () => { }) {
        return saferEvalNoReturn(el, expression, this.$data, {
            ...extraVars(),
            $dispatch: this.getDispatchFunction(el),
        })
    }

    getDispatchFunction(el) {
        return (event, detail = {}) => {
            el.dispatchEvent(new CustomEvent(event, {
                detail,
                bubbles: true,
            }))
        }
    }

    listenForNewElementsToInitialize() {
        const targetNode = this.$el

        const observerOptions = {
            childList: true,
            attributes: true,
            subtree: true,
        }

        const observer = new MutationObserver((mutations) => {
            for (let i = 0; i < mutations.length; i++) {
                // Filter out mutations triggered from child components.
                const closestParentComponent = mutations[i].target.closest('[jmb-name]')

                if (!(closestParentComponent && closestParentComponent.isSameNode(this.$el))) continue

                if (mutations[i].type === 'attributes' && mutations[i].attributeName === 'jmb-local') {
                    // @jembeModification
                    // do nothing jmb-local on subsequent update should be ignore and jmb-update shold be used
                    // const xAttr = mutations[i].target.getAttribute('jmb-local') || '{}';
                    // const rawData = saferEval(this.$el, xAttr, { $el: this.$el })

                    // Object.keys(rawData).forEach(key => {
                    //     if (this.$data[key] !== rawData[key]) {
                    //         this.$data[key] = rawData[key]
                    //     }
                    // })
                }

                if (mutations[i].addedNodes.length > 0) {
                    mutations[i].addedNodes.forEach(node => {
                        if (node.nodeType !== 1 || node.__jmb_inserted_me) return

                        // @jembeModification
                        // can only create component for jembe component it ignores jmb-local on
                        // other components
                        // if (node.matches('[jmb-local]') && !node.__jmb) {
                        //     node.__jmb = new Component(node)
                        //     return
                        // }

                        this.initializeElement(node)
                    })
                }
            }
        })

        observer.observe(targetNode, observerOptions);
    }

    getRefsProxy() {
        var self = this

        var refObj = {}

        /* IE11-ONLY:START */
        // // Add any properties up-front that might be necessary for the Proxy polyfill.
        // refObj.$isRefsProxy = false;
        // refObj.$isAlpineProxy = false;

        // // If we are in IE, since the polyfill needs all properties to be defined before building the proxy,
        // // we just loop on the element, look for any jmb-ref and create a tmp property on a fake object.
        // this.walkAndSkipNestedComponents(self.$el, el => {
        //     if (el.hasAttribute('jmb-ref')) {
        //         refObj[el.getAttribute('jmb-ref')] = true
        //     }
        // })
        /* IE11-ONLY:END */

        // One of the goals of this is to not hold elements in memory, but rather re-evaluate
        // the DOM when the system needs something from it. This way, the framework is flexible and
        // friendly to outside DOM changes from libraries like Vue/Livewire.
        // For this reason, I'm using an "on-demand" proxy to fake a "$refs" object.
        return new Proxy(refObj, {
            get(object, property) {
                if (property === '$isAlpineProxy') return true

                var ref

                // We can't just query the DOM because it's hard to filter out refs in
                // nested components.
                self.walkAndSkipNestedComponents(self.$el, el => {
                    if (el.hasAttribute('jmb-ref') && el.getAttribute('jmb-ref') === property) {
                        ref = el
                    }
                })

                return ref
            }
        })
    }
}
