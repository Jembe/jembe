import { JembeClient } from "../../jembe/static/js/jembeClient.js";

test('identify component on simple page', () =>{
  const jembeClient = new JembeClient('create document from html string')
  except(jembeClient.components.length).toBe(1)
  except(jembeClient.components[0].execName).toBe('simple_page')
  except(jembeClient.components[0].state).toBe({})
  except(jembeClient.components[0].changes_url).toBe(true)
  except(jembeClient.components[0].url).toBe('/simple_page')
})