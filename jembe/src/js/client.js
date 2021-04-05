import ComponentAPI from "./componentApi/index.js"
import { deepCopy, walkComponentDom } from "./utils.js"
import morphdom from "./morphdom/index.js"
import { walk } from "./componentApi/utils.js"
import JMB from "./componentApi/magic/jmb.js"

/**
 * Reference to component html with associated data
 */
class ComponentRef {

  constructor(jembeClient, execName, data, dom, onDocument) {
    this.jembeClient = jembeClient

    this.execName = execName
    this.hierarchyLevel = execName.split("/").length
    this.isPageComponent = this.hierarchyLevel === 2

    this.state = data.state
    this.url = data.url
    this.changesUrl = data.changesUrl
    this.actions = data.actions !== undefined ? data.actions : []
    this.dom = this._cleanDom(dom)
    this.onDocument = onDocument

    this.placeHolders = {}
    this.api = null
  }
  mount(originalComponentRef = undefined) {
    this._getPlaceHolders()
    if (this.api === null) {
      this.api = new ComponentAPI(this)
    }
    this.api.mount(originalComponentRef)
  }
  unmount() {
    if (this.api !== null) {
      this.api.unmount()
    }
    this.api = null
    this.dom = null
  }
  toJsonRequest() {
    return {
      "execName": this.execName,
      "state": this.state
    }
  }

  merge(parentComponent, originalComponent) {
    if (this.isPageComponent && this.onDocument) {
      // if page component is already on document do nothing
      // because it is already mounted and it's not changed
      return
    }
    if (this.onDocument
      && originalComponent !== undefined
      && originalComponent.dom.isSameNode(this.dom)) {
      // no need to unmount-merge-mount component that is already on document
      if (!parentComponent.placeHolders[this.execName].isSameNode(this.dom)) {
        // but if paramet is changed we need to update parent place holders
        parentComponent.placeHolders[this.execName].replaceWith(this.dom)
        parentComponent.placeHolders[this.execName] = this.dom
      }
      return
    }

    if (this.isPageComponent) {
      let documentElement = this.jembeClient.document.documentElement
      this.dom = documentElement = this._morphdom(documentElement, this.dom)
      this.dom.setAttribute("jmb-name", this.execName)
    } else {
      this.dom = this._morphdom(parentComponent.placeHolders[this.execName], this.dom)
      parentComponent.placeHolders[this.execName] = this.dom
    }

    this.onDocument = true

    this.mount(
      originalComponent !== undefined && originalComponent.execName === this.execName
        ? originalComponent
        : undefined
    )

  }

  _morphdom(from, to) {
    return morphdom(
      from,
      to,
      {
        getNodeKey: node => {
          return (node.nodeType === Node.ELEMENT_NODE && node.hasAttribute('jmb-name'))
            ? node.getAttribute('jmb-name')
            : node.id
        },
        onBeforeElUpdated: (fromEl, toEl) => {
          // spec - https://dom.spec.whatwg.org/#concept-node-equals
          if (fromEl.isEqualNode(toEl)) {
            return false
          }
          // don't pass to next component or template
          if (!this.isPageComponent
            && fromEl.hasAttribute('jmb-name')
            && fromEl.getAttribute('jmb-name') !== this.execName) return false
          if (fromEl.hasAttribute('jmb-placeholder')
            && fromEl.getAttribute('jmb-placeholder') !== this.execName) return false
          if (fromEl.hasAttribute('jmb-ignore')) {
            return false
          }

          return true
        },
        childrenOnly: this.isPageComponent
      }
    )
  }
  _getPlaceHolders() {
    this.placeHolders = {}
    walkComponentDom(
      this.dom,
      undefined,
      (el, execName) => {
        // populate placeHolders
        this.placeHolders[execName] = el
      }
    )
  }
  _cleanDom(dom) {
    // if html dom has only one child use that child to put jmb-name tag
    // if not enclose html with div and put jmb-name into it
    if (typeof dom === "string") {
      let domString = dom.trim()
      if (!this.isPageComponent) {

        let template = this.jembeClient.document.createElement("template")
        template.innerHTML = domString
        // check is it needed to add souranding DIV tag
        if (template.content.childNodes.length > 1 ||
          template.content.childNodes.length === 0 ||
          template.content.firstChild.nodeType === Node.TEXT_NODE ||
          (template.content.childNodes.length === 1 &&
            (template.content.firstChild.hasAttribute("jmb-name") ||
              template.content.firstChild.hasAttribute("jmb-placeholder")))) {
          let div = this.jembeClient.document.createElement("div")
          let curChild = template.content.firstChild
          while (curChild) {
            let nextChild = curChild.nextSibling
            div.appendChild(curChild)
            curChild = nextChild
          }
          template.content.appendChild(div)
        }
        // add jmb-name tag
        template.content.firstChild.setAttribute("jmb-name", this.execName)
        dom = template.content.firstChild
      } else {
        const doc = this.jembeClient.domParser.parseFromString(domString, "text/html")
        doc.documentElement.setAttribute("jmb-name", this.execName)
        dom = doc.documentElement
      }
    }
    dom.removeAttribute('jmb-data')
    return dom
  }
}


class UploadedFile {
  constructor(execName, paramName, fileUploadId, files) {
    this.execName = execName
    this.paramName = paramName
    this.fileUploadId = fileUploadId
    this.files = files
    this.multipleFiles = files instanceof FileList || files instanceof Array
  }
  addToFormData(formData) {
    if (this.multipleFiles) {
      for (const file of this.files) {
        formData.append(this.fileUploadId, file)
      }
    } else {
      formData.append(this.fileUploadId, this.files)
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
    this.components = {}
    this.getComponentsFromDocument()
    this.updateLocation(true)
    this.commands = []
    this.filesForUpload = {}
    this.domParser = new DOMParser()
    this.xRequestUrl = null

    this.xRequestsInProgress = 0
    this.xRequestActiveElement = null
    this.xRequestDisabledElements = []

    window.onpopstate = this.onHistoryPopState
  }
  /**
   * Finds all jmb-name and associate jmb-data tags in document 
   * and create ComponentRefs
   */
  getComponentsFromDocument() {
    this.components = {}
    let componentsNodes = this.document.querySelectorAll("[jmb-name][jmb-data]")
    for (const componentNode of componentsNodes) {
      const componentRef = new ComponentRef(
        this,
        componentNode.getAttribute('jmb-name'),
        eval(`(${componentNode.getAttribute('jmb-data')})`),
        componentNode,
        true
      )
      this.components[componentRef.execName] = componentRef
      componentRef.mount()
    }
    this.dispatchUpdatePageEvent(false)
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
        this,
        xComp.execName,
        {
          "url": xComp.url,
          "changesUrl": xComp.changesUrl,
          "state": xComp.state,
          "actions": xComp.actions
        },
        xComp.dom,
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
    let pageExecNames = Object.values(currentComponents).filter(
      c => c.isPageComponent
    ).map(
      c => c.execName
    )
    // execName of new pageComponent 
    let pageExecName = pageExecNames[0]
    if (pageExecNames.length > 1) {
      for (const pen of pageExecNames) {
        if (!currentComponents[pen].onDocument) {
          pageExecName = pen
        }
      }
    }
    let processingExecNames = [pageExecName]
    let newComponents = {}
    while (processingExecNames.length > 0) {
      const currentComponent = currentComponents[
        processingExecNames.shift()
      ]
      let orignalComponent = this.components[currentComponent.execName]
      let parentComponent = Object.values(newComponents).find(
        c => Object.keys(c.placeHolders).includes(currentComponent.execName)
      )
      currentComponent.merge(parentComponent, orignalComponent)
      newComponents[currentComponent.execName] = currentComponent
      for (const placeHolderName of Object.keys(currentComponent.placeHolders)) {
        processingExecNames.push(placeHolderName)
      }
    }
    // unmount components that will be removed
    for (const [execName, component] of Object.entries(this.components)) {
      if (!Object.keys(newComponents).includes(execName)
        || newComponents[execName] !== component) {
        component.unmount()
      }
    }

    this.components = newComponents
  }

  addInitialiseCommand(execName, initParams, mergeExistingParams = true) {
    const exisitingInitCommands = this.commands.filter(
      x => x.type === "init" && x.componentExecName === execName
    )
    if (mergeExistingParams === true && exisitingInitCommands.length > 0) {
      const existingCmd = exisitingInitCommands[0]
      for (const [paramName, paramValue] of Object.entries(initParams)) {
        existingCmd.initParams = this._updateParam(
          existingCmd.initParams, paramName, paramValue
        )
      }

    } else {
      if (mergeExistingParams === true
        && Object.keys(initParams).length === 0 &&
        this.components[execName] !== undefined) {
        // dont add init command for existing components if no params are changed
        return
      }
      let params = (mergeExistingParams === true && this.components[execName] !== undefined) ? deepCopy(this.components[execName].state) : {}
      for (const [paramName, paramValue] of Object.entries(initParams)) {
        params = this._updateParam(params, paramName, paramValue)
      }
      if (mergeExistingParams === false && exisitingInitCommands > 0) {
        const existingCmd = exisitingInitCommands[0]
        existingCmd.initParams = params
        existingCmd.mergeExistingParams = mergeExistingParams
      } else {
        this.commands.push(
          {
            "type": "init",
            "componentExecName": execName,
            "initParams": params,
            "mergeExistingParams": mergeExistingParams
          }
        )

      }
    }
  }
  /**
   * Update params with [paramName] =  paramValue
   * paramName can contain dots (.) to separate object attributes
   * @param {dict} params 
   * @param {string} paramName 
   * @param {*} paramValue 
   */
  _updateParam(params, paramName, paramValue) {
    if (paramName.startsWith('.') || paramName.endsWith(".")) {
      throw "paramName cant start or end in dot (.)"
    }
    return this._updateParamR(params, paramName.split("."), paramValue)
  }
  _updateParamR(params, paramNames, paramValue) {
    let pName = paramNames[0]
    if (paramNames.length === 1) {
      // last element
      params[pName] = paramValue
    } else if (params[pName] === undefined) {
      params[pName] = this._updateParamR({}, paramNames.slice(1), paramValue)
    } else {
      params[pName] = this._updateParamR(params[pName], paramNames.slice(1), paramValue)
    }
    return params
  }

  addCallCommand(execName, actionName, args = [], kwargs = {}) {
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
  addFilesForUpload(execName, paramName, files) {
    // remove existing files for same param name
    let existingFileId = null
    for (const uf of Object.values(this.filesForUpload)) {
      if (uf.execName === execName && uf.paramName === paramName) {
        existingFileId = uf.fileUploadId
      }
    }
    if (existingFileId !== null) {
      delete this.filesForUpload[existingFileId]
    }

    if (((files instanceof FileList || files instanceof Array) && files.length > 0)
      || (files instanceof File)) {
      // add files to paramName
      let fileId = null
      while (fileId == null || Object.keys(this.filesForUpload).includes(fileId)) {
        fileId = Math.random().toString(36).substring(7)
      }
      this.filesForUpload[fileId] = new UploadedFile(
        execName, paramName, fileId, files
      )
      // add init command if not exist
      this.addInitialiseCommand(execName, {
        [paramName]: fileId
      })
    } else {
      // remove init command if only containt file init param
      let initCommandIndex = this.commands.findIndex(cmd =>
      (cmd.componentExecName === execName
        && cmd.type === "init"
        && Object.keys(cmd.initParams).includes(paramName)
        && Object.keys(cmd.initParams).length === 1
      )
      )
      if (initCommandIndex >= 0) {
        this.commands.splice(initCommandIndex, 1)
      }
    }
  }
  getXUploadRequestFormData() {
    if (Object.keys(this.filesForUpload).length === 0) {
      // no files for uplaod
      return null
    }
    let fd = new FormData()
    for (const uf of Object.values(this.filesForUpload)) {
      uf.addToFormData(fd)
    }
    return fd
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
  executeUpload() {
    const url = "/jembe/upload_files"
    const uploadFormData = this.getXUploadRequestFormData()
    if (uploadFormData === null) {
      return new Promise((resolve, reject) => {
        resolve(null)
      })
    }
    return window.fetch(url, {
      method: "POST",
      cache: "no-cache",
      credentials: "same-origin",
      redirect: "follow",
      referrer: "no-referrer",
      headers: { 'X-JEMBE': 'upload' },
      body: uploadFormData
    }).then(response => {
      if (!response.ok) {
        // throw Error(response.statusText)
        this.dispatchUpdatePageErrorEvent(response)
        throw Error("errorInJembeResponse")
      }
      return response.json()
    }).then(json => {
      // fileupload returns files = dict(fileUploadId, [{storage=storage_name, path=file_path}]) and unique fileUplaodResponseId
      for (const fileUploadId of Object.keys(json.files)) {
        // replace all uploaded files init params with 
        //(storage=storage_name, path=file_path) returned from x-jembe=fileupload request
        const ufiles = json.files[fileUploadId]
        const fu = this.filesForUpload[fileUploadId]
        this.addInitialiseCommand(
          fu.execName, {
          [fu.paramName]: fu.multipleFiles ? ufiles : ufiles[0]
        }
        )
      }

      this.filesForUpload = {}
      return json.fileUploadResponseId
    })
  }
  executeCommands(updateLocation = true) {
    const url = this.xRequestUrl !== null ? this.xRequestUrl : window.location.href
    this.dispatchStartUpdatePageEvent()
    this.executeUpload().then(
      fileUploadResponseId => {
        const requestBody = this.getXRequestJson()
        // reset commads since we create request body from it
        this.commands = []
        // fetch request and process response
        window.fetch(url, {
          method: "POST",
          cache: "no-cache",
          credentials: "same-origin",
          redirect: "follow",
          referrer: "no-referrer",
          headers: fileUploadResponseId !== null ? { 'X-JEMBE': 'commands', 'X-JEMBE-RELATED-UPLOAD': fileUploadResponseId } : { 'X-JEMBE': 'commands' },
          body: requestBody
        }).then(response => {
          if (!response.ok) {
            // throw Error(response.statusText)
            this.dispatchUpdatePageErrorEvent(response)
            throw Error("errorInJembeResponse")
          }
          return response.json()
        }).then(
          json => this.getComponentsFromXResponse(json)
        ).then(
          components => {
            this.updateDocument(components)
            if (updateLocation) {
              this.updateLocation()
            }
            this.dispatchUpdatePageEvent()
          }).catch(error => {
            this.dispatchUpdatePageErrorEvent(null, error)
          })
      }
    ).catch(error => {
      this.dispatchUpdatePageErrorEvent(null, error)
    })
  }
  consolidateCommands() {
    let initCommandsExecNames = this.commands.filter(
      c => c.type === 'init'
    ).map(
      c => c.componentExecName
    )
    let callCommandsExecNames = this.commands.filter(
      c => c.type === 'call'
    ).map(
      c => c.componentExecName
    )
    for (const execName of initCommandsExecNames) {
      if (!callCommandsExecNames.includes(execName)) {
        this.addCallCommand(execName, "display")
      }
    }
    //TODO
    // - display error if actions over two different component are called
    //   and this components are not on ignore part of flow list, also define flow list    
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
    const componentExecName = domNode.closest('[jmb-name]').getAttribute('jmb-name')
    return new JMB(this, componentExecName)
  }

  dispatchUpdatePageEvent(isXUpdate = true) {
    if (isXUpdate) {
      this.xRequestsInProgress -= 1
    }
    if (this.xRequestsInProgress === 0) {
      this.enableInputsAfterResponse()
    }
    window.dispatchEvent(
      new CustomEvent(
        'jembeUpdatePage',
        {
          detail: {
            isXUpdate: isXUpdate
          }
        }
      )
    )
  }
  dispatchStartUpdatePageEvent(isXUpdate = true) {
    if (isXUpdate) {
      this.xRequestsInProgress += 1
    }
    if (this.xRequestsInProgress === 1) {
      this.disableInputsBeforeRequest()
    }
    window.dispatchEvent(
      new CustomEvent(
        'jembeStartUpdatePage',
        {
          detail: {
            isXUpdate: isXUpdate
          }
        }
      )
    )
  }
  dispatchUpdatePageErrorEvent(response = null, error = null) {
    if (response === null && error.message !== "errorInJembeResponse") {
      this.xRequestsInProgress -= 1
      console.info('Error x-jembe request', error)
    } else if (response !== null) {
      this.xRequestsInProgress -= 1
      console.info('Error x-jembe response', response)
    } else if (response === null && error.message === "errorInJembeResponse") {
      return
    }
    window.dispatchEvent(
      new CustomEvent(
        'jembeUpdatePageError',
        {
          detail: {
            networkError: error !== null,
            response: response,
            error: error
          }
        }
      )
    )
  }
  disableInputsBeforeRequest() {
    // save currently focused element
    if (this.document.activeElement !== null) {
      this.xRequestActiveElement = this.document.activeElement
    }
    // walk over whole document and disable inputs
    walk(this.document.documentElement, node => {
      if (node.hasAttribute('jmb-ignore')) return false
      if (
        // <button>
        (node.tagName.toLowerCase() === 'button') ||
        // <select>
        node.tagName.toLowerCase() === 'select' ||
        // <input type="checkbox|radio">
        (node.tagName.toLowerCase() === 'input' &&
          (node.type === 'checkbox' || node.type === 'radio'))
      ) {
        node.setAttribute('jmb-node-initially-disabled', node.disabled)
        if (!node.disabled) {
          node.disabled = true
          this.xRequestDisabledElements.push(() => { 
            if (node.hasAttribute("jmb-node-initially-disabled")) {
              node.disabled = node.getAttribute("jmb-node-initially-disabled") === "true"
              node.removeAttribute("jmb-node-initially-disabled")
            }
          })
        }
      } else if (
        // <input type="text">
        node.tagName.toLowerCase() === 'input' ||
        // <textarea>
        node.tagName.toLowerCase() === 'textarea'
      ) {
        node.setAttribute('jmb-node-initially-readonly', node.readOnly)
        if (!node.readOnly) {
          node.readOnly = true
          this.xRequestDisabledElements.push(() => { 
            if (node.hasAttribute("jmb-node-initially-readonly")) {
              node.readOnly = node.getAttribute("jmb-node-initially-readonly") === "true"
              node.removeAttribute("jmb-node-initially-readonly")
            }
          })
        }
      }
    })
  }
  enableInputsAfterResponse() {
    //enable disabled inputs (not updated by morph) 
    for (let f of this.xRequestDisabledElements) {
      f()
    }
    this.xRequestDisabledElements = []
    // refocus active element
    if (this.xRequestActiveElement !== null && this.document.contains(this.xRequestActiveElement)) {
      this.xRequestActiveElement.focus()
    }
    this.xRequestActiveElement = null
  }
}

export { JembeClient }