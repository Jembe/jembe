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
    this.changesUrl = data.changesUrl
    this.dom = dom
    this.placeHolders = this.getPlaceHolders(this.dom)
    this.onDocument = onDocument
  }
  getPlaceHolders(dom) {
    let placeHolders = {}
    for (const placeholder of dom.querySelectorAll("jmb-placeholder[exec-name]")) {
      placeHolders[placeholder.getAttribute("exec-name")] = placeholder
    }
    for (const placeholder of dom.querySelectorAll("[jmb\:name]")) {
      placeHolders[placeholder.getAttribute("jmb:name")] = placeholder
    }
    return placeHolders
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
    this.domParser = new DOMParser()
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
    if (! this.isPageExecName(execName)) {
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
      console.warn(template.outerHTML)
      return template.content.firstChild
    } else {
      const doc = this.domParser.parseFromString(domString, "text/html")
      console.error(doc.documentElement.outerHTML)
      return doc.documentElement
    }
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
          "changesUrl": xComp.changesUrl,
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
  updateDocument(components) {
    // by the name we know if component has subcomponents so...
    // always go from root(bottom) to leafs(top)
    // first find page component eitehr on document or in component
    // if component does not exist in components carry on leave it as is on document
    // if component exist in components replace component on document with component on page
    // than go its child and replace it one by one either by from compoennts if it exist
    // or by old component from document.

    // make list of all components that should be display on updated document
    let currentComponents = {}
    // add from this.components if not exist in components otherwise add from components
    for (const [execName, compRef] of Object.entries(this.components)) {
      if (components[execName] === undefined) {
        currentComponents[execName] = compRef
      } else {
        currentComponents[execName] = components[execName]
      }
    }
    // add from components if not already added
    for (const [execName, compRef] of Object.entries(components)) {
      if (currentComponents[execName] === undefined) {
        currentComponents[execName], compRef
      }
    }
    //process current components one by one starting with root page
    // all components gatthered from document but whitout its placeholder
    // will be ignored 
    let pageExecName = Object.keys(currentComponents).filter(
      execName => execName.split("/").length === 2
    )[0]
    let processingExecNames = [pageExecName]
    while (processingExecNames.length > 0) {
      const currentExecName = processingExecNames.shift()
      const currentCompoRef = currentComponents[currentExecName]
      this.mergeComponent(currentCompoRef)
      for (const placeHolderName of Object.keys(currentCompoRef.placeHolders)) {
        processingExecNames.push(placeHolderName)
      }
    }
  }
  /**
   * Replaces component dom in this.document
   * and update this.components
   */
  mergeComponent(componentRef) {
    console.log(componentRef.execName)
  }
  isPageExecName(execName) {
    return execName.split("/").length === 2
  }
}

export { JembeClient }