import { expect, jest } from "@jest/globals";
import { buildDocument } from "./utils.js";

beforeEach(() => {
  jest.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => cb());
});

afterEach(() => {
  window.requestAnimationFrame.mockRestore();
});

test('call component action from javascript event', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
             jmb-data='{"changesUrl":true,"state":{},"url":"/page/tasks","actions":{}}'>
             <button onclick="jembeClient.component(this).call('test_action'); jembeClient.executeCommands();">Test</button>
        </div>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": {} },
      ],
      "commands": [
        {
          "type": "call",
          "componentExecName": "/page/tasks",
          "actionName": "test_action",
          "args": [],
          "kwargs": {}
        }
      ]
    }
  ))
})
test('call component action with params from javascript event', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
            jmb-data='{"changesUrl":true,"state":{},"url":"/page/tasks","actions":{}}'>
            <button onclick="
                jembeClient.component(this).call('test_action', {1:1,2:2,t:'test',l:'a'}); 
                jembeClient.executeCommands();">
                Test
            </button>
        </div>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": {} },
      ],
      "commands": [
        {
          "type": "call",
          "componentExecName": "/page/tasks",
          "actionName": "test_action",
          "args": [],
          "kwargs": { 1: 1, 2: 2, t: "test", l: "a" }
        }
      ]
    }
  ))
})
test('call nested component actions from javascript event', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
            jmb-data='{"changesUrl":true,"state":{},"url":"/page/tasks","actions":{}}'>
            <button onclick="
                jembeClient.component(this).component('view',{a:1, b:2}).call('display'); 
                jembeClient.component(this).component('/nav/view1', {id:1}).call('display');
                jembeClient.component(this).component('../test', {c:3}).call('increase');
                jembeClient.executeCommands();">
                Test
            </button>
        </div>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": {} },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/page/tasks/view",
          "initParams": { a: 1, b: 2 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/page/tasks/view",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        },
        {
          "type": "init",
          "componentExecName": "/nav",
          "initParams": {},
          "mergeExistingParams": true
        },
        {
          "type": "init",
          "componentExecName": "/nav/view1",
          "initParams": { id: 1 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/nav/view1",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        },
        {
          "type": "init",
          "componentExecName": "/page/test",
          "initParams": { c: 3 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/page/test",
          "actionName": "increase",
          "args": [],
          "kwargs": {}
        },
      ]
    }
  ))
})
test('call nested component actions', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
            jmb-data='{"changesUrl":true,"state":{},"url":"/page/tasks","actions":{}}'>
            <button jmb-on:click="
                $jmb.component('view',{a:1, b:2}).call('display'); 
                $jmb.component('/nav/view1', {id:1}).call('display');
                $jmb.component('../test', {c:3}).call('increase');">
                Test
            </button>
        </div>
      </body>
    </html>
  `)
  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": {} },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/page/tasks/view",
          "initParams": { a: 1, b: 2 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/page/tasks/view",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        },
        {
          "type": "init",
          "componentExecName": "/nav",
          "initParams": {},
          "mergeExistingParams": true
        },
        {
          "type": "init",
          "componentExecName": "/nav/view1",
          "initParams": { id: 1 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/nav/view1",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        },
        {
          "type": "init",
          "componentExecName": "/page/test",
          "initParams": { c: 3 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/page/test",
          "actionName": "increase",
          "args": [],
          "kwargs": {}
        },
        // {
        //   "type": "call",
        //   "componentExecName": "/nav",
        //   "actionName": "display",
        //   "args": [],
        //   "kwargs": {}
        // },
      ]
    }
  ))
})
test("back button", () => {
  buildDocument(`
    <html jmb-name="/tasks" jmb-data='{"changesUrl":true,"state":{"mode":"edit"},"url":"/tasks","actions":{}}'>
      <body>
        <div jmb-name="/tasks/edit" 
            jmb-data='{"changesUrl":true,"state":{"record_id":1},"url":"/tasks/edit/1","actions":{}}'>
            <button jmb-on:click="$jmb.component('..',{mode:'list'}).display()">
                Back
            </button>
        </div>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/tasks", "state": { "mode": "edit" } },
        { "execName": "/tasks/edit", "state": { "record_id": 1 } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/tasks",
          "initParams": { "mode": "list" },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/tasks",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        }
      ]
    }
  ))
})
test("directly calling components actions", () => {
  buildDocument(`
    <html jmb-name="/tasks" jmb-data='{"changesUrl":true,"state":{},"url":"/tasks","actions":{"my_action":true}}'>
      <body>
          <button jmb-on:click="my_action({a:'AA'})">
              Back
          </button>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/tasks", "state": {} },
      ],
      "commands": [
        {
          "type": "call",
          "componentExecName": "/tasks",
          "actionName": "my_action",
          "args": [],
          "kwargs": { a: "AA" }
        }
      ]
    }
  ))
})
test("test setting nested component init params", () => {
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{"obj":{"a":"A", "b":{1:"1"}},"ar":[]},"url":"/test","actions":{}}'>
      <body>
          <button jmb-on:click="
            $jmb.set('obj.a','AAA')">
              Run sets
          </button>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      components: [
        {
          execName: "/test",
          state: {
            obj: { "a": "A", "b": { 1: "1" } },
            ar: []
          }
        }
      ],
      commands: [
        {
          type: "init",
          componentExecName: "/test",
          initParams: {
            obj: { "a": "AAA", "b": { 1: "1" } },
            ar: []
          },
          mergeExistingParams: true
        },
        // {
        //   type: "call",
        //   componentExecName: "/test",
        //   actionName: "display",
        //   args: [],
        //   kwargs: {}
        // }
      ]
    }
  ))
})

test("test setting nested component init params - direct", () => {
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{"obj":{"a":"A", "b":{1:"1"}},"ar":[]},"url":"/test","actions":{}}'>
      <body>
          <button jmb-on:click="obj.a='AAA'">
              Run sets
          </button>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      components: [
        {
          execName: "/test",
          state: {
            obj: { "a": "A", "b": { 1: "1" } },
            ar: []
          }
        }
      ],
      commands: [
        {
          type: "init",
          componentExecName: "/test",
          initParams: {
            obj: { "a": "AAA", "b": { 1: "1" } },
            ar: []
          },
          mergeExistingParams: true
        },
        // {
        //   type: "call",
        //   componentExecName: "/test",
        //   actionName: "display",
        //   args: [],
        //   kwargs: {}
        // }
      ]
    }
  ))
})
test("test on ready event", () => {
  window.fetch = jest.fn(() => {return Promise.resolve({ ok: true, json: async () => [] })})
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{}}'>
      <body>
        <p jmb-on:ready="$self.remove()"></p>
        <div jmb-on:ready="$self.innerText='test'"></div>
        <span jmb-on:ready.defer="$self.innerText='test'"></span>
      </body>
    </html>
  `)

  expect(document.querySelector('p')).toBe(null)
  expect(document.querySelector('div').innerText).toBe('test')
  expect(document.querySelector('span').innerText).toBe('test')
  // expect(window.fetch).toHaveBeenCalledTimes(2)
})
test("test on delay event modifier", () => {
  jest.useFakeTimers()
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{}}'>
      <body>
        <div id="one" jmb-on:ready.delay="$el.innerText='one'"></div>
        <div id="two" jmb-on:ready.delay.200ms="$el.innerText='one'"></div>
        <button id="three" jmb-on:click.delay.defer="$el.innerText='three'"></button>
        <button id="four" jmb-on:click.delay.200ms.defer="$el.innerText='four'"></button>
      </body>
    </html>
  `)
  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('#three').click()
  document.querySelector('#four').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(0)
  expect(setTimeout).toHaveBeenCalledTimes(4)
  expect(setTimeout).toHaveBeenNthCalledWith(1, expect.any(Function), 250)
  expect(setTimeout).toHaveBeenNthCalledWith(2, expect.any(Function), 200)
  expect(setTimeout).toHaveBeenNthCalledWith(3, expect.any(Function), 250)
  expect(setTimeout).toHaveBeenNthCalledWith(4, expect.any(Function), 200)
  jest.runAllTimers()

})
test("test on refresh delay clears all timers", () => {
  jest.useFakeTimers()
  document.test = undefined
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{}}'>
      <body>
        <div id="one" jmb-on:ready.delay-t1.500ms.defer="document.test='one'"></div>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/test",
      "state": {},
      "url": "/test",
      "changesUrl": true,
      "actions": [],
      "dom": `
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{}}'>
      <body>
        <div id="one" jmb-on:ready.delay-t1.300ms.defer="document.test='two'"></div>
      </body>
    </html>
    `},
  ]
  window.jembeClient.updateDocument(jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(setTimeout).toHaveBeenCalledTimes(2)
  expect(setTimeout).toHaveBeenNthCalledWith(1, expect.any(Function), 500)
  // expect(setTimeout).toHaveBeenNthCalledWith(2, expect.any(Function), 300)
  jest.advanceTimersByTime(300)
  expect(document.test).toBe('two')
  jest.advanceTimersByTime(500)
  expect(document.test).toBe('two')

})
test("test on refresh delay continue named timers", () => {
  jest.useFakeTimers()
  document.test = undefined
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{}}'>
      <body>
        <div id="one" jmb-on:ready.delay-actionOne.50ms.defer="document.test='one'"></div>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/test",
      "state": {},
      "url": "/test",
      "changesUrl": true,
      "actions": [],
      "dom": `
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{}}'>
      <body>
        <div id="one" jmb-on:ready.delay-actionOne.50ms.defer="document.test='two'"></div>
      </body>
    </html>
    `},
  ]
  jest.advanceTimersByTime(1)
  expect(document.test).toBe(undefined)
  window.jembeClient.updateDocument(jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(setTimeout).toHaveBeenCalledTimes(2)
  expect(setTimeout).toHaveBeenNthCalledWith(1, expect.any(Function), 50)
  expect(setTimeout.mock.calls[1][1]).toBeLessThan(50) 
  jest.advanceTimersByTime(50)
  expect(document.test).toBe('two')
})

test("test call action without named params", () => {
  buildDocument(`
    <html jmb-name="/test" jmb-data='{"changesUrl":true,"state":{},"url":"/test","actions":{"choose":true}}'>
      <body>
          <button jmb-on:click="choose('test')">Test</button>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('button').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      components: [
        {
          execName: "/test",
          state: {}
        }
      ],
      commands: [
        {
          type: "call",
          componentExecName: "/test",
          actionName: "choose",
          args: ["test"],
          kwargs: {}
        }
      ]
    }
  ))
})
test("$jmb.set not deferred shout call display", () => {
  buildDocument(`
    <html jmb-name="/tasks" jmb-data='{"changesUrl":true,"state":{"a":0},"url":"/tasks","actions":{}}'>
      <body>
          <button id="test1" jmb-on:click="a=1">Test 1</button>
          <button id="test2" jmb-on:click.defer="a=2">Test 2</button>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('#test1').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/tasks", "state": { "a": 0 } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/tasks",
          "initParams": { "a": 1 },
          "mergeExistingParams": true
        },
        // {
        //   "type": "call",
        //   "componentExecName": "/tasks",
        //   "actionName": "display",
        //   "args": [],
        //   "kwargs": {}
        // }
      ]
    }
  ))
  window.jembeClient.commands = []
  document.querySelector('#test2').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.getXRequestJson()).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/tasks", "state": { "a": 0 } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/tasks",
          "initParams": { "a": 2 },
          "mergeExistingParams": true
        },
      ]
    }
  ))
})
test("$jmb.component chain", () => {
  buildDocument(`
    <html jmb-name="/tasks" jmb-data='{"changesUrl":true,"state":{"a":0},"url":"/tasks","actions":{}}'>
      <body>
          <button id="testA" jmb-on:click="$jmb.component('/main').component('a',{id:1}).display()">Display A</button>
          <button id="testB" jmb-on:click="$jmb.component('/tasks').component('b').display()">Display B</button>
      </body>
    </html>
  `)

  window.jembeClient.executeCommands = jest.fn(() => {
    return window.jembeClient.getXRequestJson()
  })
  document.querySelector('#testA').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(1)
  expect(window.jembeClient.executeCommands.mock.results[0].value).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/tasks", "state": { "a": 0 } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/main",
          "initParams": {},
          "mergeExistingParams": true
        },
        {
          "type": "init",
          "componentExecName": "/main/a",
          "initParams": { id:1 },
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/main/a",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        },
        // {
        //   "type": "call",
        //   "componentExecName": "/main",
        //   "actionName": "display",
        //   "args": [],
        //   "kwargs": {}
        // }
      ]
    }
  ))
  window.jembeClient.commands = []
  document.querySelector('#testB').click()
  expect(window.jembeClient.executeCommands.mock.calls.length).toBe(2)
  expect(window.jembeClient.getXRequestJson()).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/tasks", "state": { "a": 0 } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/tasks/b",
          "initParams": {},
          "mergeExistingParams": true
        },
        {
          "type": "call",
          "componentExecName": "/tasks/b",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        },
      ]
    }
  ))
})
test("$updateDom() call", () => {
  buildDocument(`
    <html jmb-name="/tasks" jmb-data='{"changesUrl":true,"state":{"a":0},"url":"/tasks","actions":{}}'>
      <body jmb-on:jembe-test.camel.window.defer="a = a+1; $updateDom()">
          <div id="testA" jmb-text="a"></div>
          <button id="buttonA" jmb-on:click.defer="a=a+1; $updateDom()">Increase A</button>
      </body>
    </html>
  `)
  document.querySelector('#buttonA').click()
  // window.dispatchEvent(new CustomEvent('jembeTest',{}))
  expect(window.jembeClient.components['/tasks'].api.$data.a).toBe(1)
  //test: except(

  })