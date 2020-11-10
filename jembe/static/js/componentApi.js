import { JembeClient } from "./jembeClient"

class InitialiseCommand {
  constructor(execName, state) {
    this.execName = execName
    this.state = state
  }
}
class EmitCommand {
  constructor(execName, eventName, params) {
    this.execName = execName
    this.eventName = eventName
    this.params = params
    this.emitTo = null
  }
  to(emitTo) {
    this.emitTo = emitTo
  }
}
class JembeComponentAPI {
  constructor(jembeClient, componentRef) {
    /** @type {JembeClient} */
    this.jembeClient = jembeClient
    /** @type {ComponentRef} */
    this.componentRef = componentRef
    this.commands = []
  }
  call(actionName) {
    // TODO add args and kwargs
    this.jembeClient.addCallCommand(
      this.componentRef.execName,
      actionName,
      [],
      {}
    )
  }
  set() { }
  emit() { }
  component() { }
}
export { JembeComponentAPI }