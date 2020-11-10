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
             <button onclick="jembeClient.component(this).call('test_action', 1,2, test='test', a='a'); jembeClient.executeCommands();">Test</button>
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
          "args": [1, 2],
          "kwargs": { "test": "test", a: "a" }
        }
      ]
    }
  ))
})