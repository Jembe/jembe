import { transitionIn, transitionOut, warnIfMalformedTemplate } from '../utils'

export function handleIfDirective(component, el, expressionResult, initialUpdate, extraVars) {
    warnIfMalformedTemplate(el, 'jmb-if')

    const elementHasAlreadyBeenAdded = el.nextElementSibling && el.nextElementSibling.__jmb_inserted_me === true

    if (expressionResult && (! elementHasAlreadyBeenAdded || el.__jmb_transition)) {
        const clone = document.importNode(el.content, true);

        el.parentElement.insertBefore(clone, el.nextElementSibling)

        transitionIn(el.nextElementSibling, () => {}, () => {}, component, initialUpdate)

        component.initializeElements(el.nextElementSibling, extraVars)

        el.nextElementSibling.__jmb_inserted_me = true
    } else if (! expressionResult && elementHasAlreadyBeenAdded) {
        transitionOut(el.nextElementSibling, () => {
            el.nextElementSibling.remove()
        }, () => {}, component, initialUpdate)
    }
}
