import { expect } from "@jest/globals";
import { JembeClient } from "../../jembe/src/js/client.js";
import { buildDocument } from "./utils.js";

test('identify component on simple page', () => {
  buildDocument(
    `<!DOCTYPE html>
    <html lang="en" jmb:name="/simple_page" jmb:data='{"changesUrl":true,"state":{},"url":"/simple_page","actions":[]}'>
    <head>
        <title>Simple page</title>
    </head>
    <body>
      <h1>Simple page</h1> 
    </body>
    </html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(1)

  const simplePageCompRef = window.jembeClient.components["/simple_page"]
  expect(simplePageCompRef.execName).toBe('/simple_page')
  expect(simplePageCompRef.state).toEqual({})
  expect(simplePageCompRef.changesUrl).toBe(true)
  expect(simplePageCompRef.url).toBe('/simple_page')
})

test('indentify components on page with counter', () => {
  buildDocument(`
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
    <html jmb:name="/cpage" jmb:data='{"changesUrl":true,"state":{},"url":"/cpage","actions":[]}'>
      <head></head>
      <body>
        <div jmb:name="/cpage/counter" 
             jmb:data='{"changesUrl":true,"state":{"value":0},"url":"/cpage/counter","actions":[]}'>
          <div>Count: 0</div>
          <a jmb:click="increase()">increase</a>
        </div>
      </body>
    </html>
  `)

  expect(document.documentElement.outerHTML).toContain(`<html jmb:name="/cpage">`)
  expect(document.documentElement.outerHTML).toContain(`<div jmb:name="/cpage/counter">`)
  expect(Object.keys(window.jembeClient.components).length).toBe(2)

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
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{"value":0},"url":"/page","actions":[]}'>
      <head><title>Test</title></head>
      <body>Test</body></html>`)
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
  window.jembeClient.updateDocument(jembeClient.getComponentsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb:name="/page1"><head><title>Test1</title></head>
      <body>Test1</body></html>`
  )
})
test('update document with x-response', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page","actions":[]}'>
      <head>
        <title jmb:name="/page/title" jmb:data='{"changesUrl":false,"state":{"title":"Title"},"url":"/page/title","actions":[]}'>
          Title
        </title>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks","actions":[]}'>
             Tasks
        </div>
      </body>
    </html>
  `)
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
  window.jembeClient.updateDocument(window.jembeClient.getComponentsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb:name="/page"><head>
        <title jmb:name="/page/title">Task</title>
      </head>
      <body>
        <div jmb:name="/page/view">Task 1</div>
      
    </body></html>`
  )
  window.jembeClient.updateDocument(window.jembeClient.getComponentsFromXResponse(
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
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb:name="/page"><head>
        <title jmb:name="/page/title">Title changed</title>
      </head>
      <body>
        <div jmb:name="/page/view">Task 1</div>
      
    </body></html>`
  )
})

test('build initialise and display command', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page","actions":[]}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks","actions":[]}'>
             Tasks
        </div>
      </body>
    </html>
  `)
  window.jembeClient.addInitialiseCommand(
    "/page/tasks",
    { "page": 1, "page_size": 10 }
  )
  window.jembeClient.addCallCommand("/page/tasks", "display", [], {})
  expect(window.jembeClient.getXRequestJson()).toBe(JSON.stringify(
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
test('initialise same component two times', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page","actions":[]}'>
      <head>
      </head>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10,"filter":null},"url":"/page/tasks","actions":[]}'>
             Tasks
        </div>
      </body>
    </html>
  `)
  window.jembeClient.addInitialiseCommand(
    "/page/tasks",
    { "page": 1, }
  )
  window.jembeClient.addInitialiseCommand(
    "/page/tasks",
    { "page_size": 5 }
  )
  expect(window.jembeClient.getXRequestJson()).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": { "page": 0, "page_size": 10, "filter": null } },
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


test('update x-response dom with souranding div', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page","actions":[]}'>
      <body></body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/page/test1",
      "state": {},
      "url": "/page/test1",
      "changesUrl": true,
      "dom": `<div></div>`
    },
    {
      "execName": "/page/test2",
      "state": {},
      "url": "/page/test2",
      "changesUrl": true,
      "dom": `<div>1</div><div>2</div>`,
    },
    {
      "execName": "/page/test3",
      "state": {},
      "url": "/page/test3",
      "changesUrl": true,
      "dom": `Test 3`,
    },
    {
      "execName": "/page/test4",
      "state": {},
      "url": "/page/test3",
      "changesUrl": true,
      "dom": ``,
    }
  ]
  let components = window.jembeClient.getComponentsFromXResponse(xResponse)
  expect(components["/page/test1"].dom.outerHTML).toBe('<div jmb:name="/page/test1"></div>')
  expect(components["/page/test2"].dom.outerHTML).toBe('<div jmb:name="/page/test2"><div>1</div><div>2</div></div>')
  expect(components["/page/test3"].dom.outerHTML).toBe('<div jmb:name="/page/test3">Test 3</div>')
  expect(components["/page/test4"].dom.outerHTML).toBe('<div jmb:name="/page/test4"></div>')
})

test('update window.location on x-response', () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page","actions":[]}'>
      <body></body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/page",
      "state": {},
      "url": "/page",
      "changesUrl": true,
      "dom": `<html><body><template jmb-placeholder="/page/test"></template></body></html>`
    },
    {
      "execName": "/page/test",
      "state": {},
      "url": "/page/test",
      "changesUrl": true,
      "dom": `<div>Test</div>`,
    },
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsFromXResponse(xResponse))
  window.jembeClient.updateLocation()
  expect(window.location.pathname).toBe("/page/test")
})

test("update url when change_url is false", () => {
  buildDocument(`
    <html jmb:name="/page" jmb:data='{"changesUrl":true,"state":{},"url":"/page","actions":[]}'>
      <body>
        <div jmb:name="/page/tasks" 
             jmb:data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks","actions":[]}'>
             Tasks
        </div>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/page/tasks",
      "state": { "page": 0, "page_size": 10 },
      "url": "/page/tasks",
      "changesUrl": true,
      "dom": `<div>Tasks<template jmb-placeholder="/page/tasks/confirm"></template></div>`,
    },
    {
      "execName": "/page/tasks/confirm",
      "state": {},
      "url": "/page/tasks/confirm",
      "changesUrl": false,
      "dom": `<div>Confirm</div>`,
    }
  ]
  const components = window.jembeClient.getComponentsFromXResponse(xResponse)
  window.jembeClient.updateDocument(components)
  window.history.pushState = jest.fn((state, title, url) => {
    return url
  })
  window.jembeClient.updateLocation()
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb:name="/page"><head></head><body>
        <div jmb:name="/page/tasks">Tasks<div jmb:name="/page/tasks/confirm">Confirm</div></div>
      
    
  </body></html>`
  )
  expect(window.history.pushState.mock.calls.length).toBe(1)
  expect(window.history.pushState.mock.results[0].value).toBe("/page/tasks")
})
test("update keyed components", () => {
  buildDocument(`
    <html jmb:name="/projects" jmb:data='{"changesUrl":true,"state":{},"url":"/tasks","actions":[]}'>
      <body>
        <div jmb:name="/projects/edit" jmb:data='{"changesUrl":true,"state":{"id":1},"url":"/projects/edit/1","actions":[]}'>
          <div jmb:name="/projects/edit/tasks" jmb:data='{"changesUrl":true,"state":{},"url":"/projects/edit/1/tasks","actions":[]}'>
            <div jmb:name="/projects/edit/tasks/view.1" jmb:data='{"changesUrl":false,"state":{"id":1},"url":"/projects/edit/1/tasks/view.1/1","actions":[]}'>Task 1</div>
            <div jmb:name="/projects/edit/tasks/view.2" jmb:data='{"changesUrl":false,"state":{"id":2},"url":"/projects/edit/1/tasks/view.2/2","actions":[]}'>Task 2</div>
            <div jmb:name="/projects/edit/tasks/view.3" jmb:data='{"changesUrl":false,"state":{"id":2},"url":"/projects/edit/1/tasks/view.3/3","actions":[]}'>Task 3</div>
          </div>
        </div>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/projects/edit/tasks",
      "state": {},
      "url": "/projects/edit/1/tasks",
      "changesUrl": true,
      "dom": `
       <html>
        <body>
          <template jmb-placeholder="/projects/edit/tasks/add"></template>
          <template jmb-placeholder="/projects/edit/tasks/view.1"></template>
          <template jmb-placeholder="/projects/edit/tasks/view.2"></template>
          <template jmb-placeholder="/projects/edit/tasks/view.3"></template>
        </body>
       </html>`,
       "actions":[]
    },
    {
      "execName": "/projects/edit/tasks/add",
      "state": {},
      "url": "/projects/edit/1/tasks/add",
      "changesUrl": false,
      "dom": `<div>Add task</div>`,
      "actions":[]
    }
  ]
  const components = window.jembeClient.getComponentsFromXResponse(xResponse)
  window.jembeClient.updateDocument(components)
  expect(document.documentElement.outerHTML).toBe(`<html jmb:name="/projects"><head></head><body>
        <div jmb:name="/projects/edit">
          <div jmb:name="/projects/edit/tasks">
       
        
          <div jmb:name="/projects/edit/tasks/add">Add task</div>
          <div jmb:name="/projects/edit/tasks/view.1">Task 1</div>
          <div jmb:name="/projects/edit/tasks/view.2">Task 2</div>
          <div jmb:name="/projects/edit/tasks/view.3">Task 3</div>
        
       </div>
        </div>
      
    
  </body></html>`
  )
})