/*
  TODO
  On page load register all components and its states.
    - jmb:name jmb:data {changes_url, state, url}
  Genrate new commands with:
    # $jmb.call(<method_name>, params)[.redisplay(force=True)]
    # $jmb.emit(<event_name>, event_params).to(<selector>)
    # $jmb.set(<state_praam_name>, value).deffer()
    # <comand_name>() (call action on current component)
    # $jmb.component(<component_name>, <state_params>).key(<key>).[call|emit|component]
  Supported tags:
    # jmb:on.<eventname>.<modifier>.<modifier>
    # jmb:model=
    <button jmb:on.click="$jmb.call('increase',10)"
  On x-jembe response update page:  
    - update components refs in JembeClient.compoennts
    - update only changed html of received components html
*/
import { JembeComponentAPI } from "./componentApi.js";

/**
 * Reference to component html with associated data
 */
class ComponentRef {

  constructor(execName, data, dom, onDocument) {
    this.execName = execName
    this.state = data.state
    this.url = data.url
    this.changesUrl = data.changes_url
    this.dom = dom
    this.onDocument = onDocument
  }
}
/**
 * Handle all jembe logic on client side, primarly building, sending, processing 
 * and refreshing page for/on x-jembe requests
 */
class JembeClient {
  constructor(doc = document) {
    this.document = doc
    this.components = this.getComponentsFromDocument()
    this.commands = []
  }
  /**
   * Finds all jmb:name and associate jmb:data tags in document 
   * and create ComponentRefs
   */
  getComponentsFromDocument() {
    // 
    let components = {}
    // TODO traverse dom dont use querySelectorAll
    let componentsNodes = this.document.querySelectorAll("[jmb\\:name][jmb\\:data]")
    for (const componentNode of componentsNodes) {
      const execName = componentNode.getAttribute('jmb:name')
      components[execName] = new ComponentRef(
        execName,
        eval(`(${componentNode.getAttribute('jmb:data')})`),
        componentNode,
        true
      )
      componentNode.removeAttribute('jmb:data')
    }
    return components
  }
  transformXResponseDom(execName, domString) {
    // if html dom has only one child use that child to put jmb:name tag
    // if not enclose html with div and put jmb:name into it
    // TODO: How to run event handlers onclick jmb:on.click <script> etc found in
    // html after integration with document
    let template = this.document.createElement("template")
    template.innerHTML = domString
    if (template.content.childNodes.length > 1) {
      let div = this.document.createElement("div")
      let curChild = template.content.firstChild
      while (curChild) {
        let nextChild = curChild.nextSibling
        div.appendChild(curChild)
        curChild = nextChild
      }
      template.content.appendChild(div)
    }
    // add jmb:name tag
    template.content.firstChild.setAttribute("jmb:name", execName)
    return template.content.firstChild
  }
  /**
   * Create dict of {execName:component} for all components find in
   * x-jembe response
   * @param {*} xJembeResponse 
   */
  getComponentsFromXResponse(xJembeResponse) {
    let components = {}
    for (const xComp of xJembeResponse) {
      const dom = xComp.dom
      components[xComp.execName] = new ComponentRef(
        xComp.execName,
        {
          "url": xComp.url,
          "changes_url": xComp.changesUrl,
          "state": xComp.state,
        },
        this.transformXResponseDom(xComp.execName, xComp.dom),
        false
      )
    }
    return components
  }
  /**
   * Update document with new components:dict
   * @param {} components 
   */
  updatePage(components) {
    // by the name we know if component has subcomponents so...
    // always go from root(bottom) to leafs(top)
    // first find page component eitehr on document or in component
    // if component does not exist in components carry on leave it as is on document
    // if component exist in components replace component on document with component on page
    // than go its child and replace it one by one either by from compoennts if it exist
    // or by old component from document.

  }
}

export { JembeClient }