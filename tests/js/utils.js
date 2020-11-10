import { JembeClient } from "../../jembe/static/js/jembeClient"

function buildDocument(docStr) {
  const doc = (new DOMParser()).parseFromString(docStr, "text/html")
  document.documentElement.innerHTML = doc.documentElement.innerHTML
  document.documentElement.setAttribute("jmb:name", doc.documentElement.getAttribute("jmb:name"))
  document.documentElement.setAttribute("jmb:data", doc.documentElement.getAttribute("jmb:data"))
  window.jembeClient = new JembeClient(document)
}
export {buildDocument}