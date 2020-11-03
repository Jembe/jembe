
class InitialiseCommand {
  constructor(execName, state) {
    this.execName = execName
    this.state = state
  }
}
class CallCommand {
  constructor(execName, actionName, args, kwargs) {
    this.execName = execName
    this.actionName = actionName
    this.args = args
    this.kwargs = kwargs
  }
}
class DisplayCommand extends CallCommand {
  constructor(execName) {
    super(execName, "display", [], {})
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

  call() { }
  set() { }
  emit() { }
  component() { }
}
export {JembeComponentAPI}