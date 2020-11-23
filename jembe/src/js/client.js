/*
  Supported tags:
    # jmb:on.<eventname>.<modifier>.<modifier>
    # jmb:model=
    <button jmb:on.click="$jmb.call('increase',10)"
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
    this.api = null
    this.hierarchyLevel = execName.split("/").length
  }

  getPlaceHolders() {
    this.placeHolders = {}
    for (const placeholder of this.dom.querySelectorAll("template[jmb-placeholder]")) {
      this.placeHolders[placeholder.getAttribute("jmb-placeholder")] = placeholder
    }
    for (const placeholder of this.dom.querySelectorAll("[jmb\\:name]")) {
      this.placeHolders[placeholder.getAttribute("jmb:name")] = placeholder
    }
  }
  toJsonRequest() {
    return {
      "execName": this.execName,
      "state": this.state
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
    this.initComponentsAPI()
    this.updateLocation(true)
    this.commands = []
    this.domParser = new DOMParser()
    this.xRequestUrl = null

    window.onpopstate = this.onHistoryPopState
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
      // check is it needed to add souranding DIV tag
      // add jmb:name tag
      if (template.content.childNodes.length > 1 ||
          template.content.childNodes.length === 0 ||
          template.content.firstChild.nodeType === Node.TEXT_NODE) {
        let div = this.document.createElement("div")
        for (const child of template.content.childNodes) {
          div.appendChild(child)
        }
        div.setAttribute("jmb:name", execName)
        return div
      } else {
        template.content.firstChild.setAttribute("jmb:name", execName)
        return template.content.firstChild
      }
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
    this.initComponentsAPI()
  }
  /**
   * Replaces component dom in this.document
   * and update this.components
   */
  mergeComponent(componentRef) {
    if (this.isPageExecName(componentRef.execName)) {
      // if page component is already on document do nothing
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
      parentComponent.placeHolders[componentRef.execName] = componentRef.dom
      componentRef.onDocument = true
    }
  }
  isPageExecName(execName) {
    return execName.split("/").length === 2
  }

  addInitialiseCommand(execName, initParams) {
    const exisitingInitCommands = this.commands.filter(
      x => x.type === "init" && x.componentExecName === execName
    )
    if (exisitingInitCommands.length > 0) {
      for (const key of Object.keys(initParams)) {
        exisitingInitCommands[0].initParams[key] = initParams[key]
      }
    } else if (this.components[execName] !== undefined) {
      this.commands.push(
        {
          "type": "init",
          "componentExecName": execName,
          "initParams": { ...(this.components[execName].state), ...initParams }
        }
      )
    } else {
      this.commands.push(
        {
          "type": "init",
          "componentExecName": execName,
          "initParams": initParams
        }
      )
    }
  }

  addCallCommand(execName, actionName, args, kwargs) {
    this.commands.push(
      {
        "type": "call",
        "componentExecName": execName,
        "actionName": actionName,
        "args": args,
        "kwargs": kwargs
      }
    )
  }
  addEmitCommand(execName, eventName, kwargs = {}, to = null) {
    this.commands.push(
      {
        "type": "emit",
        "componentExecName": execName,
        "eventName": eventName,
        "params": kwargs,
        "to": to
      }
    )

  }
  getXRequestJson() {
    return JSON.stringify({
      "components": Object.values(this.components).map(x => x.toJsonRequest()),
      "commands": this.commands
    })
  }
  setXRequestUrl(url) {
    this.xRequestUrl = url
  }
  executeCommands(updateLocation = true) {
    const url = this.xRequestUrl !== null ? this.xRequestUrl : window.location.href
    const requestBody = this.getXRequestJson()
    // reset commads since we create request body from it
    this.commands = []
    // fetch request and process response
    fetch(url, {
      method: "POST",
      cache: "no-cache",
      credentials: "same-origin",
      redirect: "follow",
      referrer: "no-referrer",
      headers: { 'X-JEMBE': true },
      body: requestBody
    }).then(
      response => {
        if (response.ok) {
          return response.json()
        } else {
          console.error("Request not successfull")
        }
      }
    ).catch(error => {
      console.error("Error in request", error)
    }).then(
      json => this.getComponentsFromXResponse(json)
    ).then(
      components => {
        this.updateDocument(components)
        if (updateLocation) {
          this.updateLocation()
        }
      }
    )
  }
  initComponentsAPI() {
    for (const component of Object.values(this.components)) {
      if (component.api === null) {
        component.api = new JembeComponentAPI(this, component.execName)
      }
    }
  }
  updateLocation(replace = false) {
    let topComponent = null
    let level = -1
    let historyState = []
    for (const component of Object.values(this.components)) {
      if (component.hierarchyLevel > level && component.changesUrl === true) {
        topComponent = component
        level = component.hierarchyLevel
      }
      historyState.push({ execName: component.execName, state: component.state })
    }
    if (topComponent !== null) {
      if (replace) {
        window.history.replaceState(historyState, '', topComponent.url)
      } else {
        window.history.pushState(historyState, '', topComponent.url)
      }
    }
  }
  onHistoryPopState(event) {
    if (event.state === null) {
      window.location = document.location
    } else {
      for (const comp of event.state) {
        this.jembeClient.addInitialiseCommand(comp.execName, comp.state)
        this.jembeClient.addCallCommand(comp.execName, "display")
      }
      this.jembeClient.executeCommands(false)
    }
  }
  /**
   * Used for geting jembeCompoentApi usually attached to document or window.jembeComponent 
   * @param {*} domNode 
   */
  component(domNode) {
    const componentExecName = domNode.closest('[jmb\\:name]').getAttribute('jmb:name')
    return this.components[componentExecName].api
  }
}

export { JembeClient }