import { JembeClient } from "./client"
import { walkComponentDom, AsyncFunction, deepCopy } from "./utils";
import { isAbsolute, join } from "path";
/**
 * jembeClient.component(this).set('paramName', paramValue)
 * jembeClient.component(this).call('actionName', {kwargs})
 * jembeClient.component(this).display()
 * jembeClient.component(this).emit('eventName', {kwargs})
 * jembeClient.component(this).init('componentRelativeOrFullName', {kwargs})
 * jembeClient.executeCommands()
 * 
 * Short form that needs to be support for jmb:on.<eventName>[.defer]:
 * $jmb.set('paramName', paramValue)
 * $jmb.call('actionName', {kwargs}) or actionName({kwargs})
 * $jmb.display() // call('display',{})
 * $jmb.emit('eventName',{kwargs})
 * $jmb.[init|component]('componentRelativeOrFullName', {kwargs})[.call|.display|.emit]
 * 
 * $jmb.ref('referencedDomName') // jmb:ref="referencedDomName"
 */
class JembeComponentAPI {
  constructor(jembeClient, componentExecName, initListeners = true) {
    /** @type {JembeClient} */
    this.jembeClient = jembeClient
    /** @type {ComponentRef} */
    this.execName = componentExecName
    if (initListeners) {
      this.initialiseJmbOnListeners()
    }
    this.refs = {}
  }
  call(actionName, kwargs = {}, args = []) {
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
    let params = {}
    params[stateName] = value
    this.jembeClient.addInitialiseCommand(
      this.execName,
      params
    )
  }
  emit(eventName, kwargs = {}, to = null) {
    this.jembeClient.addEmitCommand(
      this.execName,
      eventName,
      kwargs,
      to
    )
  }
  component(relativeExecName, kwargs = {}) {
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
        index == componentNames.length - 1 ? kwargs : {}
      )
      index++
    }
    return new JembeComponentAPI(this.jembeClient, execName, false)
  }
  init(relativeExecName, kwargs = {}) {
    return this.component(relativeExecName, kwargs)
  }
  ref(referenceName) {
    return this.refs[referenceName]
  }
  initialiseJmbOnListeners() {
    /** @type {ComponentRef} */
    const componentRef = this.jembeClient.components[this.execName]
    if (componentRef !== undefined) {
      // TODO walk dom and select elements
      walkComponentDom(componentRef.dom, el => {
        // initialise event listeneres for jmb:on. attributes
        if (el.hasAttributes()) {
          for (const attribute of el.attributes) {
            this._processDomAttribute(el, attribute.name, attribute.value)
          }
        }
      })
    }
  }
  _processDomAttribute(el, attrName, attrValue) {
    attrName = attrName.toLowerCase()
    if (attrName.startsWith('jmb:on.')) {
      this._processJmbOnAttribute(el, attrName, attrValue)
    } else if (attrName === "jmb:ref") {
      this._processJmbRefAttribute(el, attrName, attrValue)
    }
  }
  _processJmbOnAttribute(el, attrName, attrValue) {

    let [jmbOn, eventName, ...decorators] = attrName.split(".")

    let expression = `${attrValue}`

    // support defer decorator
    if (decorators.indexOf("defer") < 0) {
      expression += ';window.jembeClient.executeCommands();'
    }
    //support delay decorator
    // must be last decorator
    const delayIndexOf = decorators.indexOf("delay")
    if (delayIndexOf >= 0) {
      let timer = 1000
      if (delayIndexOf +1 < decorators.length && decorators[delayIndexOf + 1].endsWith('ms')) {
        timer = parseInt(decorators[delayIndexOf + 1].substr(0, decorators[delayIndexOf + 1].length - 2)) * 10
      }
      expression = `setTimeout(function() {${expression}}, ${timer})`
    }

    if (eventName === 'ready') {
      // support on.ready event, that is executed when component is rendered
      // that means execute it right now
      this._executeJmbOnLogic(el, null, expression)
    } else {
      // support for browser events
      el.addEventListener(eventName, (event) => {
        this._executeJmbOnLogic(el, event, expression)
      })
    }

  }
  _processJmbRefAttribute(el, attrName, attrValue) {
    this.refs[attrValue] = el
  }
  _executeJmbOnLogic(el, event, expression) {
    /** @type {Array<string>} */
    const actions = this.jembeClient.components[this.execName].actions
    let helpers = {
      "$jmb": this,
      "$state": deepCopy(this.jembeClient.components[this.execName].state),
      "$event": event,
      "$el": el
    }
    // allow action functions to be called directly 
    for (const action of actions) {
      helpers[action] = (kwargs = {}, args = []) => {
        this.call(action, kwargs, args)
      }
    }

    let scope = {
    }
    return Promise.resolve(
      (
        new AsyncFunction(
          ['scope', ...Object.keys(helpers)],
          `with(scope) { ${expression} }`
        )
      )(
        scope, ...Object.values(helpers)
      )
    )
  }
}
export { JembeComponentAPI }