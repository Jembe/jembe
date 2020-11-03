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
import { JembeComponentAPI} from "./componentApi.js";

class ComponentRef {
  constructor(name, data, dom, onDocument) {
    this.name = name
    this.state = data.state
    this.url = data.url
    this.changes_url = data.changes_url
    this.dom = dom
    this.onDocument = onDocument
  }
}

class JembeClient {
  constructor() {
    console.log('init $jmb')
    this.components = this.getComponentsFromDocument()
    this.commands = []
  }
  getComponentsFromDocument() {
    // Find all jmb:name and associate jmb:data tags and create ComponentRefs
    let components = []
    // TODO traverse dom dont use querySelectorAll
    let componentsNodes = document.querySelectorAll("[jmb\\:name][jmb\\:data]")
    for (const componentNode of componentsNodes) {
      components.push(new ComponentRef(
        componentNode.getAttribute('jmb:name'),
        eval(`(${componentNode.getAttribute('jmb:data')})`),
        componentNode,
        true
      ))
    }
    return components
  }
}

export {JembeClient}