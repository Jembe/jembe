/**
 * Return null or the execName of the component 
 * @param {Element} el 
 */
function elIsNewComponent(el) {
  if (el.hasAttribute('jmb-name')) {
    return el.getAttribute('jmb-name')
  } else if (el.hasAttribute('jmb-placeholder')) {
    return el.getAttribute('jmb-placeholder')
  } else {
    return null
  }
}

function walkComponentDom(el, callback, callbackOnNewComponent, myExecName) {
  if (myExecName === undefined) {
    myExecName = el.getAttribute('jmb-name')
  }
  let componentExecName = elIsNewComponent(el)
  if (componentExecName !== null && componentExecName !== myExecName) {
    callbackOnNewComponent(el, componentExecName)
  } else {
    if (callback !== undefined) {
      callback(el)
    }
    el = el.firstElementChild
    while (el) {
      walkComponentDom(el, callback, callbackOnNewComponent, myExecName)
      el = el.nextElementSibling
    }
  }
}

let AsyncFunction = Object.getPrototypeOf(async function () { }).constructor


function deepCopy(inObject) {
  let outObject, value, key

  if (typeof inObject !== "object" || inObject === null) {
    return inObject // Return the value if inObject is not an object
  }

  // Create an array or object to hold the values
  outObject = Array.isArray(inObject) ? [] : {}

  for (key in inObject) {
    value = inObject[key]

    // Recursively (deep) copy for nested objects, including arrays
    outObject[key] = deepCopy(value)
  }

  return outObject
}
export { walkComponentDom, AsyncFunction, deepCopy }