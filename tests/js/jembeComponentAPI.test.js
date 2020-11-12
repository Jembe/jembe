import { expect, jest } from "@jest/globals";
import { buildDocument } from "./utils.js";

test('call component action from javascript event', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page"}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{},"url":"/page/tasks"}'>
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
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page"}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
            jmb:data='{"changesUrl":true,"state":{},"url":"/page/tasks"}'>
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
          "kwargs": {1:1, 2:2, t:"test", l:"a"}
        }
      ]
    }
  ))
})
test('call nested component actions from javascript event', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page"}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
            jmb:data='{"changesUrl":true,"state":{},"url":"/page/tasks"}'>
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
          "initParams": {a:1, b:2},
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
        },
        {
          "type": "init",
          "componentExecName": "/nav/view1",
          "initParams": {id:1},
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
          "initParams": {c:3},
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