import { isAbsolute, join } from "path";
export default class JMB {
  constructor(jembeClient, execName) {
    this.jembeClient = jembeClient
    this.execName = execName
    this.callsCommands = false
  }
  call(actionName, ...params) {
    this.callsCommands = true

    let kwargs = {}
    let args = []
    if (params.length === 1 && params[0].constructor == Object) {
      kwargs = params[0]
    } else {
      args = params
    }
    this.jembeClient.addCallCommand(
      this.execName,
      actionName,
      args,
      kwargs
    )
  }
  display() {
    this.call("display")
  }
  /**
   *  Change state param of current component,
   *  by addig initialise command with only state param 
   *  defined by stateName changed to newlly provided value
   * stateName can use dots (.) to set attribure of object
   * Examples: "someObject.paramName" 
   * @param {string} stateName 
   * @param {*} value 
   */
  set(stateName, value) {
    this.callsCommands = true
    if (value instanceof FileList || value instanceof File) {
      this.jembeClient.addFilesForUpload(this.execName, stateName, value)
    } else {
      let params = {}
      params[stateName] = value
      this.jembeClient.addInitialiseCommand(
        this.execName,
        params
      )
    }
  }
  emit(eventName, kwargs = {}, to = null) {
    this.callsCommands = true
    this.jembeClient.addEmitCommand(
      this.execName,
      eventName,
      kwargs,
      to
    )
  }
  component(relativeExecName, kwargs = {}, mergeExistingParams = true) {
    this.callsCommands = true

    let execName = relativeExecName
    if (!isAbsolute(relativeExecName)) {
      execName = join(this.execName, relativeExecName)
    }
    let componentNames = []
    let startWith = []
    let index = 0
    let equalSoFar = true
    let execNameSplit = execName.split("/")
    let thisExecNameSplit = this.execName.split("/")
    while (index < execNameSplit.length) {
      if (equalSoFar === true &&
        (
          // if execName is different (including key) we need to genereate init command
          execNameSplit[index] !== thisExecNameSplit[index] ||
          // alsy if kwargs are specified for last component we need do generate init command
          (index === execNameSplit.length - 1 && kwargs !== {})
        )
      ) {
        equalSoFar = false
      }
      if (!equalSoFar) {
        componentNames.push(execNameSplit[index])
      } else {
        startWith.push(execNameSplit[index])
      }
      index++
    }

    index = 0
    while (index < componentNames.length) {
      this.jembeClient.addInitialiseCommand(
        [
          startWith.join("/"),
          componentNames.slice(0, index + 1).join("/")
        ].join("/"),
        index == componentNames.length - 1 ? kwargs : {},
        mergeExistingParams
      )
      index++
    }
    return new JMB(this.jembeClient, execName)
  }
  component_reset(relativeExecName, kwargs = {}) {
    return this.component(relativeExecName, kwargs, false)
  }
  executeCommands() {
    this.jembeClient.consolidateCommands()
    this.jembeClient.executeCommands()
  }
  componentsOnPage() {
    return Object.keys(this.jembeClient.components)
  }
}