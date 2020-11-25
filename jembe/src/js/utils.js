function elIsNewComponent(el) {
  return el.hasAttribute('jmb:name')
}

function walkComponentDom(el, callback) {

  if (!elIsNewComponent(el)) {
    callback(el)
  }
  el = el.firstElementChild
  while (el) {
    if (!elIsNewComponent(el)) {
      walkComponentDom(el, callback)
    }
    el = el.nextElementSibling
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