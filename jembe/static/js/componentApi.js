import { JembeClient } from "./jembeClient"
import { isAbsolute, join } from "path";
/**
 * jembeClient.component(this).set('paramName', paramValue)
 * jembeClient.component(this).call('actionName', {kwargs})
 * jembeClient.component(this).display()
 * jembeClient.component(this).emit('eventName', {kwargs})
 * jembeClient.component(this).init('componentRelativeOrFullName', {kwargs})
 * jembeClient.executeCommands()
 * 
 * Short form that needs to be support for jmb:on.<eventName>[.deferred]:
 * $jmb.set('paramName', paramValue)
 * $jmb.call('actionName', {kwargs}) or actionName({kwargs})
 * $jmb.display() // call('display',{})
 * $jmb.emit('eventName',{kwargs})
 * $jmb.[init|component]('componentRelativeOrFullName', {kwargs})[.call|.display|.emit]
 * 
 * $jmb.ref('referencedDomName') // jmb:ref="referencedDomName"
 */
class JembeComponentAPI {
  constructor(jembeClient, componentExecName) {
    /** @type {JembeClient} */
    this.jembeClient = jembeClient
    /** @type {ComponentRef} */
    this.execName = componentExecName
    this.commands = []
  }
  call(actionName, kwargs={}, args=[]) {
    this.jembeClient.addCallCommand(
      this.execName,
      actionName,
      args,
      kwargs
    )
  }
  set(stateName, value) {
    //TODO set deep parameters
    params = {}
    params[stateName] = value
    this.jembeClient.addInitialiseCommand(
      this.execName,
      params
    )
  }
  emit(eventName, kwargs={}, to=null) {
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
      if (equalSoFar === true && execNameSplit[index] !== thisExecNameSplit[index]) {
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
    return new JembeComponentAPI(this.jembeClient, execName)
  }
}
export { JembeComponentAPI }