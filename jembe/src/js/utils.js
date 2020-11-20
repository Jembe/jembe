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
export { walkComponentDom, AsyncFunction }