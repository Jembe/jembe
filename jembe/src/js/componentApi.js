import { JembeClient } from "./client"
import { walkComponentDom, AsyncFunction, deepCopy } from "./utils";
import { isAbsolute, join } from "path";
import { clearTimeout } from "timers";
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
 * 
 * RETHINKIG
 * From alpine: $el, $refs, $event, $dispatch, $nextTick, $watch
 * From jmb: $jmb with $jmb.emit, $jmb.init|component, $jmb.call
 *           $self - referenc on curent node
 *           $local - reference local javascript variables tied to component.localData
 * all actions and state params are localy avaiable so
 * paramName = paramValue or paramName = $self.value or file = $self.files[0] are valid
 * also actionName({kwargs}) or display() are valid
 * param names overrides actionNames and prints warning in console if thay colides
 * All changes to state valiables should call display if defer modifier is not present
 * If no chages are made to state variables (only to $local etc) display will not be called
 * 
 * what to use jmb-on.click j-on.click jmb-on.click
 * jmb-local, jmb-local.init, jmb-local.update
 * jmb-show, jmb-bind, jmb-on, jmb-model
 * jmb-text jmb-html, jmb-ref jmb-if, jmb-for, jmb-transition, jmb-spread, jmb-cloak
 * 
 * jmb-data, jmb-name, jmb-placeholder
 */
class JembeComponentAPI {
  constructor(componentRef, jembeClient = undefined, execName = undefined) {
    if (componentRef !== undefined && componentRef !== null) {
      /** @type {JembeClient} */
      this.jembeClient = componentRef.jembeClient
      /** @type {ComponentRef} */
      this.componentRef = componentRef
      this.execName = componentRef.execName
      this.localData = componentRef.localData
    } else {
      /** @type {JembeClient} */
      this.jembeClient = jembeClient
      /** @type {ComponentRef} */
      this.componentRef = undefined
      this.execName = execName
      this.localData = {}
    }
    this.refs = {}

    // internal
    this.onReadyEvents = []
    this.unnamedTimers = []
    this.previouseNamedTimers = {}
    if (this.localData.namedTimers !== undefined) {
      this.previouseNamedTimers = this.localData.namedTimers
    } 

    this.localData.namedTimers = {}

    // initialistion
    this.initialiseJmbOnListeners()
  }
  call(actionName, ...params) {
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
    return new JembeComponentAPI(undefined, this.jembeClient, execName)
  }
  init(relativeExecName, kwargs = {}) {
    return this.component(relativeExecName, kwargs)
  }
  ref(referenceName) {
    return this.refs[referenceName]
  }
  initialiseJmbOnListeners() {
    if (this.componentRef !== undefined) {
      // TODO walk dom and select elements
      this.onReadyEvents = []
      for (const jmbddattr of this.componentRef.jmbDoubleDotAttributes) {
        this._processDomAttribute(jmbddattr.el, jmbddattr.name, jmbddattr.value)
      }
      for (const eventFunction of this.onReadyEvents) {
        eventFunction()
      }
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
    let [jmbTag, onEventAndDecorators, actionName] = attrName.split(":")
    let [onTag, eventName, ...decorators] = onEventAndDecorators.split(".")

    let expression = `${attrValue}`

    // support defer decorator
    if (decorators.indexOf("defer") < 0) {
      if (expression.includes("$jmb.set(")) {
        // if action is not deferred and has $jmb.set then call display
        expression += ";$jmb.display();"
      }
      expression += ';window.jembeClient.executeCommands();'
    } 
    //support delay decorator
    // must be last decorator
    const delayIndexOf = decorators.indexOf("delay")
    if (delayIndexOf >= 0) {
      let timer = 1000
      if (delayIndexOf + 1 < decorators.length && decorators[delayIndexOf + 1].endsWith('ms')) {
        timer = parseInt(decorators[delayIndexOf + 1].substr(0, decorators[delayIndexOf + 1].length - 2)) * 10
      }
      if (actionName === undefined) {
        expression = `
        var timerId = window.setTimeout(function() {${expression}}, ${timer});
        $jmb.unnamedTimers.push(timerId);
        `
      } else {
        let start = new Date().getTime()
        if (this.previouseNamedTimers[actionName] !== undefined) {
          start = this.previouseNamedTimers[actionName].start
          timer = timer - ((new Date().getTime()) - start)
        }

        if (timer > 0) {
          expression = `
          var timerId = window.setTimeout(function() {
            ${expression};
            delete $jmb.localData.namedTimers['${actionName}'];
          }, ${timer});
          $jmb.localData.namedTimers['${actionName}'] = {id: timerId, start: ${start}};
          `
        } else {
          //run emidiatly like on.ready
          this.onReadyEvents.push(() => this._executeJmbOnLogic(el, null, expression))
        }
      }
    }

    if (eventName === 'ready') {
      // support on.ready event, that is executed when component is rendered
      // that means execute it right now
      this.onReadyEvents.push(() => this._executeJmbOnLogic(el, null, expression))
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
    const actions = this.componentRef.actions
    let helpers = {
      "$jmb": this,
      "$event": event,
      "$el": el,
    }
    // allow action functions to be called directly 
    for (const action of actions) {
      helpers[action] = (...params) => {
        this.call(action, ...params)
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
  mount() {

  }
  unmount() {
    for (const timerId of this.unnamedTimers) {
      window.clearTimeout(timerId)
    }
    for (const [timerName, timerInfo] of Object.entries(this.localData.namedTimers)) {
      window.clearTimeout(timerInfo.id)
    }
  }
}
export { JembeComponentAPI }