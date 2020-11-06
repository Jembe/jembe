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
    this.placeHolders = {}
    this.onDocument = onDocument
    this.getPlaceHolders()
  }
  getPlaceHolders() {
    this.placeHolders = {}
    for (const placeholder of this.dom.querySelectorAll("template[jmb-placeholder]")) {
      this.placeHolders[placeholder.getAttribute("jmb-placeholder")] = placeholder
    }
    for (const placeholder of this.dom.querySelectorAll("[jmb\:name]")) {
      this.placeHolders[placeholder.getAttribute("jmb:name")] = placeholder
    }
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
    if (!this.isPageExecName(execName)) {
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
    } else {
      const doc = this.domParser.parseFromString(domString, "text/html")
      doc.documentElement.setAttribute("jmb:name", execName)
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
    // make list of all existing components that can be display on updated document
    // list contains all from this.components merged with components where
    // if there is components with same execname one from components is used
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
        currentComponents[execName] = compRef
      }
    }
    //process current components one by one starting with root page
    // all components gatthered from document but whitout its placeholder
    // will be ignored.
    // chose root/page component from compoents if it exist otherwise use
    // one on the document
    let pageExecNames = Object.keys(currentComponents).filter(
      execName => this.isPageExecName(execName)
    )
    let pageExecName = pageExecNames[0]
    if (pageExecNames.length > 1) {
      for (const pen of pageExecNames) {
        if (!currentComponents[pen].onDocument) {
          pageExecName = pen
        }
      }
    }
    let processingExecNames = [pageExecName]
    this.components = {}
    while (processingExecNames.length > 0) {
      const currentExecName = processingExecNames.shift()
      const currentCompoRef = currentComponents[currentExecName]
      this.mergeComponent(currentCompoRef)
      this.components[currentCompoRef.execName] = currentCompoRef
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
    if (this.isPageExecName(componentRef.execName)) {
      // if page component is alrady on document dont do nothing
      if (!componentRef.onDocument) {
        this.document.documentElement.innerHTML = componentRef.dom.innerHTML
        componentRef.dom = this.document.documentElement
        componentRef.dom.setAttribute("jmb:name", componentRef.execName)
        componentRef.getPlaceHolders() // becouse we use innerHTML not appendChild
        componentRef.onDocument = true
      }
    } else {
      // search this.components for component with placeholder for this component
      let parentComponent = Object.values(this.components).filter(
        comp => Object.keys(comp.placeHolders).includes(componentRef.execName)
      )[0]
      parentComponent.placeHolders[componentRef.execName].replaceWith(componentRef.dom)
      componentRef.onDocument = true
    }
  }
  isPageExecName(execName) {
    return execName.split("/").length === 2
  }
}

export { JembeClient }