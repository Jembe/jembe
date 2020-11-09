import { expect } from "@jest/globals";
import { JembeClient } from "../../jembe/static/js/jembeClient.js";

test('identify component on simple page', () => {
  const doc = (new DOMParser()).parseFromString(
    `<!DOCTYPE html>
    <html lang="en" jmb:name="/simple_page" jmb:data='{"changesUrl":true,"state":{},"url":"/simple_page"}'>
    <head>
        <title>Simple page</title>
    </head>
    <body>
      <h1>Simple page</h1> 
    </body>
    </html>`, "text/html"
  )
  const jembeClient = new JembeClient(doc)

  expect(Object.keys(jembeClient.components).length).toBe(1)

  const simplePageCompRef = jembeClient.components["/simple_page"]
  expect(simplePageCompRef.execName).toBe('/simple_page')
  expect(simplePageCompRef.state).toEqual({})
  expect(simplePageCompRef.changesUrl).toBe(true)
  expect(simplePageCompRef.url).toBe('/simple_page')
})

test('indentify components on page with counter', () => {
  const doc = (new DOMParser()).parseFromString(`
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
    <html jmb:name="/cpage" jmb:data='{"changesUrl":true,"state":{},"url":"/cpage"}'>
      <head></head>
      <body>
        <div jmb:name="/cpage/counter" 
             jmb:data='{"changesUrl":true,"state":{"value":0},"url":"/cpage/counter"}'>
          <div>Count: 0</div>
          <a jmb:click="increase()">increase</a>
        </div>
      </body>
    </html>
  `, "text/html")
  const jembeClient = new JembeClient(doc)

  expect(doc.documentElement.outerHTML).toContain(`<html jmb:name="/cpage">`)
  expect(doc.documentElement.outerHTML).toContain(`<div jmb:name="/cpage/counter">`)
  expect(Object.keys(jembeClient.components).length).toBe(2)

  const cPageCompRef = jembeClient.components["/cpage"]
  expect(cPageCompRef.execName).toBe('/cpage')
  expect(cPageCompRef.state).toEqual({})
  expect(cPageCompRef.changesUrl).toBe(true)
  expect(cPageCompRef.url).toBe('/cpage')

  const counterCompRef = jembeClient.components["/cpage/counter"]
  expect(counterCompRef.execName).toBe('/cpage/counter')
  expect(counterCompRef.state).toEqual({ "value": 0 })
  expect(counterCompRef.changesUrl).toBe(true)
  expect(counterCompRef.url).toBe('/cpage/counter')
})

test('indentify components from x-jembe response v1', () => {
  const xResponse = [
    {
      "execName": "/cpage/counter",
      "state": { "value": 1 },
      "url": "/cpage/counter",
      "changesUrl": true,
      "dom": `<div>Count: 1</div><a jmb:on.click="increase()">increase</a>`,
    }
  ]
  const jembeClient = new JembeClient()
  const components = jembeClient.getComponentsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)

  const counterCompRef = components["/cpage/counter"]
  expect(counterCompRef.execName).toBe('/cpage/counter')
  expect(counterCompRef.state).toEqual({ "value": 1 })
  expect(counterCompRef.changesUrl).toBe(true)
  expect(counterCompRef.url).toBe('/cpage/counter')
  expect(counterCompRef.dom.outerHTML).toBe(
    `<div jmb:name="/cpage/counter"><div>Count: 1</div><a jmb:on.click="increase()">increase</a></div>`
  )
})
test('indentify components from x-jembe response v2', () => {
  const xResponse = [
    {
      "execName": "/page/test",
      "state": {},
      "url": "/page/test",
      "changesUrl": true,
      "dom": `<td>test</td>`,
    }
  ]
  const jembeClient = new JembeClient()
  const components = jembeClient.getComponentsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)

  const counterCompRef = components["/page/test"]
  expect(counterCompRef.execName).toBe('/page/test')
  expect(counterCompRef.state).toEqual({})
  expect(counterCompRef.changesUrl).toBe(true)
  expect(counterCompRef.url).toBe('/page/test')
  expect(counterCompRef.dom.outerHTML).toBe(
    `<td jmb:name="/page/test">test</td>`
  )
})
test('indentify components from x-jembe response - page component', () => {
  const xResponse = [
    {
      "execName": "/page",
      "state": {},
      "url": "/page",
      "changesUrl": true,
      "dom": `<html>
      <head><template jmb-placeholder="/page/title"></template></head>
      <body><template jmb-placeholder="/page/tasks"></template></body>
      </html>`,
    }
  ]
  const jembeClient = new JembeClient()
  const components = jembeClient.getComponentsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)

  const pageCompRef = components["/page"]
  expect(pageCompRef.execName).toBe('/page')
  expect(pageCompRef.state).toEqual({})
  expect(pageCompRef.changesUrl).toBe(true)
  expect(pageCompRef.url).toBe('/page')
  expect(pageCompRef.dom.outerHTML).toBe(
    `<html jmb:name="/page"><head><template jmb-placeholder="/page/title"></template></head>
      <body><template jmb-placeholder="/page/tasks"></template>
      </body></html>`,
  )
})
// TODO First write tests here for updatePage (page, page with counters, 
// capp tasks with subtasks and all)

test('update document with x-response - page component', () => {
  const doc = (new DOMParser()).parseFromString(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{"value":0},"url":"/page"}'>
      <head><title>Test</title></head>
      <body>Test</body></html>`, "text/html")
  const xResponse = [
    {
      "execName": "/page1",
      "state": { "value": 1 },
      "url": "/page1",
      "changesUrl": true,
      "dom": `<html>
      <head><title>Test1</title></head>
      <body>Test1</body></html>`
    },
  ]
  const jembeClient = new JembeClient(doc)
  jembeClient.updateDocument(jembeClient.getComponentsFromXResponse(xResponse))
  expect(doc.documentElement.outerHTML).toBe(
    `<html jmb:name="/page1"><head><title>Test1</title></head>
      <body>Test1</body></html>`
  )
})
test('update document with x-response', () => {
  const doc = (new DOMParser()).parseFromString(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page"}'>
      <head>
        <title jmb:name="/page/title" jmb:data='{"changesUrl":false,"state":{"title":"Title"},"url":"/page/title"}'>
          Title
        </title>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks"}'>
             Tasks
        </div>
      </body>
    </html>
  `, "text/html")
  const xResponse = [
    {
      "execName": "/page",
      "state": {},
      "url": "/page",
      "changesUrl": true,
      "dom": `<html>
      <head>
        <template jmb-placeholder="/page/title"></template>
      </head>
      <body>
        <template jmb-placeholder="/page/view"></template>
      </body>
    </html>`
    },
    {
      "execName": "/page/title",
      "state": { "title": "Task" },
      "url": "/page/title",
      "changesUrl": false,
      "dom": `<title>Task</title>`,
    },
    {
      "execName": "/page/view",
      "state": { "id": 1 },
      "url": "/page/view/1",
      "changesUrl": true,
      "dom": `<div>Task 1</div>`,
    }
  ]
  const jembeClient = new JembeClient(doc)
  jembeClient.updateDocument(jembeClient.getComponentsFromXResponse(xResponse))
  expect(doc.documentElement.outerHTML).toBe(
    `<html jmb:name="/page"><head>
        <title jmb:name="/page/title">Task</title>
      </head>
      <body>
        <div jmb:name="/page/view">Task 1</div>
      
    </body></html>`
  )
  jembeClient.updateDocument(jembeClient.getComponentsFromXResponse(
    [
      {
        "execName": "/page",
        "state": {},
        "url": "/page",
        "changesUrl": true,
        "dom": `<html>
      <head>
        <template jmb-placeholder="/page/title"></template>
      </head>
      <body>
        <template jmb-placeholder="/page/view"></template>
      </body>
    </html>`
      },
      {
        "execName": "/page/title",
        "state": { "title": "Title changed" },
        "url": "/page/title",
        "changesUrl": false,
        "dom": `<title>Title changed</title>`,
      }
    ]
  ))
  expect(doc.documentElement.outerHTML).toBe(
    `<html jmb:name="/page"><head>
        <title jmb:name="/page/title">Title changed</title>
      </head>
      <body>
        <div jmb:name="/page/view">Task 1</div>
      
    </body></html>`
  )
})

test('build initialise and display command', () => {
  const doc = (new DOMParser()).parseFromString(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page"}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks"}'>
             Tasks
        </div>
      </body>
    </html>
  `, "text/html")
  const jembeClient = new JembeClient(doc)
  jembeClient.addInitialiseCommand(
    "/page/tasks",
    { "page": 1, "page_size": 10 }
  )
  jembeClient.addCallCommand("/page/tasks", "display", [], {})
  expect(jembeClient.getXRequestJson()).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": { "page": 0, "page_size": 10 } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/page/tasks",
          "initParams": { "page": 1, "page_size": 10 }
        },
        {
          "type": "call",
          "componentExecName": "/page/tasks",
          "actionName": "display",
          "args": [],
          "kwargs": {}
        }
      ]
    }
  ))
})
// initialise same component called two times
test('initialise same component two times', () => {
  const doc = (new DOMParser()).parseFromString(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page"}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10,"filter":null},"url":"/page/tasks"}'>
             Tasks
        </div>
      </body>
    </html>
  `, "text/html")
  const jembeClient = new JembeClient(doc)
  jembeClient.addInitialiseCommand(
    "/page/tasks",
    { "page": 1, }
  )
  jembeClient.addInitialiseCommand(
    "/page/tasks",
    { "page_size": 5 }
  )
  expect(jembeClient.getXRequestJson()).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": { "page": 0, "page_size": 10, "filter":null } },
      ],
      "commands": [
        {
          "type": "init",
          "componentExecName": "/page/tasks",
          "initParams": { "page": 1, "page_size": 5, "filter": null }
        }
      ]
    }
  ))
})