import { expect } from "@jest/globals";
import { JembeClient } from "../../jembe/src/js/client.js";
import { buildDocument } from "./utils.js";

test('identify component on simple page', () => {
  buildDocument(
    `<!DOCTYPE html>
    <html lang="en" jmb-name="/simple_page" jmb-data='{"changesUrl":true,"state":{},"url":"/simple_page","actions":{}}'>
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
    <html jmb-name="/cpage" jmb-data='{"changesUrl":true,"state":{},"url":"/cpage","actions":{}}'>
      <head></head>
      <body>
        <div jmb-name="/cpage/counter" 
             jmb-data='{"changesUrl":true,"state":{"value":0},"url":"/cpage/counter","actions":{}}'>
          <div>Count: 0</div>
          <a jmb:click="increase()">increase</a>
        </div>
      </body>
    </html>
  `)

  expect(document.documentElement.outerHTML).toContain(`<html jmb-name="/cpage">`)
  expect(document.documentElement.outerHTML).toContain(`<div jmb-name="/cpage/counter">`)
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
      "dom": `<div>Count: 1</div><a jmb-on:click="increase()">increase</a>`,
    }
  ]
  const jembeClient = new JembeClient()
  const { components, globals } = jembeClient.getComponentsAndGlobalsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)

  const counterCompRef = components["/cpage/counter"]
  expect(counterCompRef.execName).toBe('/cpage/counter')
  expect(counterCompRef.state).toEqual({ "value": 1 })
  expect(counterCompRef.changesUrl).toBe(true)
  expect(counterCompRef.url).toBe('/cpage/counter')
  expect(counterCompRef.dom.outerHTML).toBe(
    `<div jmb-name="/cpage/counter"><div>Count: 1</div><a jmb-on:click="increase()">increase</a></div>`
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
  const { components, globals } = jembeClient.getComponentsAndGlobalsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)

  const counterCompRef = components["/page/test"]
  expect(counterCompRef.execName).toBe('/page/test')
  expect(counterCompRef.state).toEqual({})
  expect(counterCompRef.changesUrl).toBe(true)
  expect(counterCompRef.url).toBe('/page/test')
  expect(counterCompRef.dom.outerHTML).toBe(
    `<td jmb-name="/page/test">test</td>`
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
  const { components, globals } = jembeClient.getComponentsAndGlobalsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)

  const pageCompRef = components["/page"]
  expect(pageCompRef.execName).toBe('/page')
  expect(pageCompRef.state).toEqual({})
  expect(pageCompRef.changesUrl).toBe(true)
  expect(pageCompRef.url).toBe('/page')
  expect(pageCompRef.dom.outerHTML).toBe(
    `<html jmb-name="/page"><head><template jmb-placeholder="/page/title"></template></head>
      <body><template jmb-placeholder="/page/tasks"></template>
      </body></html>`,
  )
})
// TODO First write tests here for updatePage (page, page with counters, 
// capp tasks with subtasks and all)

test('update document with x-response - page component', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{"value":0},"url":"/page","actions":{}}'>
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
  window.jembeClient.updateDocument(jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page1"><head><title>Test1</title></head>
      <body>Test1</body></html>`
  )
})

test('update document with x-response', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
        <title jmb-name="/page/title" jmb-data='{"changesUrl":false,"state":{"title":"Title"},"url":"/page/title","actions":{}}'>
          Title
        </title>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
             jmb-data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks","actions":{}}'>
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
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head>
        <title jmb-name="/page/title">Task</title>
      </head>
      <body>
        <div jmb-name="/page/view">Task 1</div>
      
    </body></html>`
  )
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(
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
    `<html jmb-name="/page"><head>
        <title jmb-name="/page/title">Title changed</title>
      </head>
      <body>
        <div jmb-name="/page/view">Task 1</div>
      
    </body></html>`
  )
})

test('build initialise and display command', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
             jmb-data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks","actions":{}}'>
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
          "initParams": { "page": 1, "page_size": 10 },
          "mergeExistingParams": true
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
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head>
      </head>
      <body>
        <div jmb-name="/page/tasks" 
             jmb-data='{"changesUrl":true,"state":{"page":0,"page_size":10,"filter":null},"url":"/page/tasks","actions":{}}'>
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
          "initParams": { "page": 1, "page_size": 5, "filter": null },
          "mergeExistingParams": true
        }
      ]
    }
  ))
})


test('update x-response dom with souranding div', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
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
  let { components, globals } = window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse)
  expect(components["/page/test1"].dom.outerHTML).toBe('<div jmb-name="/page/test1"></div>')
  expect(components["/page/test2"].dom.outerHTML).toBe('<div jmb-name="/page/test2"><div>1</div><div>2</div></div>')
  expect(components["/page/test3"].dom.outerHTML).toBe('<div jmb-name="/page/test3">Test 3</div>')
  expect(components["/page/test4"].dom.outerHTML).toBe('<div jmb-name="/page/test4"></div>')
})

test('update window.location on x-response', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
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
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  window.jembeClient.updateLocation()
  expect(window.location.pathname).toBe("/page/test")
})

test("update url when change_url is false", () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <body>
        <div jmb-name="/page/tasks" 
             jmb-data='{"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/page/tasks","actions":{}}'>
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
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  window.history.pushState = jest.fn((state, title, url) => {
    return url
  })
  window.jembeClient.updateLocation()
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head><body>
        <div jmb-name="/page/tasks">Tasks<div jmb-name="/page/tasks/confirm">Confirm</div></div>
      
    
  </body></html>`
  )
  expect(window.history.pushState.mock.calls.length).toBe(1)
  expect(window.history.pushState.mock.results[0].value).toBe("/page/tasks")
})
test("update keyed components", () => {
  buildDocument(`
    <html jmb-name="/projects" jmb-data='{"changesUrl":true,"state":{},"url":"/tasks","actions":{}}'>
      <body>
        <div jmb-name="/projects/edit" jmb-data='{"changesUrl":true,"state":{"id":1},"url":"/projects/edit/1","actions":{}}'>
          <div jmb-name="/projects/edit/tasks" jmb-data='{"changesUrl":true,"state":{},"url":"/projects/edit/1/tasks","actions":{}}'>
            <div jmb-name="/projects/edit/tasks/view.1" jmb-data='{"changesUrl":false,"state":{"id":1},"url":"/projects/edit/1/tasks/view.1/1","actions":{}}'>Task 1</div>
            <div jmb-name="/projects/edit/tasks/view.2" jmb-data='{"changesUrl":false,"state":{"id":2},"url":"/projects/edit/1/tasks/view.2/2","actions":{}}'>Task 2</div>
            <div jmb-name="/projects/edit/tasks/view.3" jmb-data='{"changesUrl":false,"state":{"id":2},"url":"/projects/edit/1/tasks/view.3/3","actions":{}}'>Task 3</div>
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
      "actions": []
    },
    {
      "execName": "/projects/edit/tasks/add",
      "state": {},
      "url": "/projects/edit/1/tasks/add",
      "changesUrl": false,
      "dom": `<div>Add task</div>`,
      "actions": []
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(`<html jmb-name="/projects"><head></head><body>
        <div jmb-name="/projects/edit">
          <div jmb-name="/projects/edit/tasks">
        
          <div jmb-name="/projects/edit/tasks/add">Add task</div>
          <div jmb-name="/projects/edit/tasks/view.1">Task 1</div>
          <div jmb-name="/projects/edit/tasks/view.2">Task 2</div>
          <div jmb-name="/projects/edit/tasks/view.3">Task 3</div>
        
       </div>
        </div>
      
    
  </body></html>`
  )
})

test('dont add souranundin div to component if not necessary', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <body>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/page/test",
      "state": {},
      "url": "/page/test",
      "changesUrl": true,
      "dom": `
      <div>a</div>  `,
    }
  ]
  const jembeClient = new JembeClient()
  const { components, globals } = jembeClient.getComponentsAndGlobalsFromXResponse(xResponse)
  expect(Object.keys(components).length).toBe(1)
  expect(components["/page/test"].dom.outerHTML).toBe(
    `<div jmb-name="/page/test">a</div>`
  )
})

test('update nested component templates', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <body>
      <div jmb-name="/page/a" jmb-data='{"changesUrl":true,"state":{},"url":"/page/a","actions":{}}'></div>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/page/a",
      "state": {},
      "url": "/page/a",
      "changesUrl": true,
      "dom": `<template jmb-placeholder="/page/a/b">`
    },
    {
      "execName": "/page/a/b",
      "state": {},
      "url": "/page/a/b",
      "changesUrl": true,
      "dom": `<template jmb-placeholder="/page/a/b/c">`
    },
    {
      "execName": "/page/a/b/c",
      "state": {},
      "url": "/page/a/b/c",
      "changesUrl": true,
      "dom": `<div>C</div>`,
    },
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(`<html jmb-name="/page"><head></head><body>
      <div jmb-name="/page/a"><div jmb-name="/page/a/b"><div jmb-name="/page/a/b/c">C</div></div></div>
      
    
  </body></html>`
  )
})

// upload
test('addFilesForUploadCommand store files in jembeClient', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{"photo":null},"url":"/page","actions":{}}'>
      <body></body>
    </html>
  `)
  const foo = new File(["foo"], "foo.txt", {
    type: "text/plain",
  });
  const bar = new File(["bar"], "bar.txt", {
    type: "text/plain",
  });
  const jc = window.jembeClient

  jc.addFilesForUpload("/page", "photo", [foo])

  // should add file to filesForUpload
  let keys = Object.keys(jc.filesForUpload)
  expect(keys.length).toBe(1)
  const fooId = keys[0]
  const fooUploadedFile = jc.filesForUpload[keys[0]]
  expect(fooUploadedFile.fileUploadId).toBe(fooId)
  expect(fooUploadedFile.execName).toBe("/page")
  expect(fooUploadedFile.paramName).toBe("photo")
  expect(fooUploadedFile.files[0]).toBe(foo)

  // should add/ upload init command
  expect(jc.commands.length).toBe(1)
  expect(jc.commands[0].type).toBe("init")
  expect(jc.commands[0].initParams.photo).toBe(fooId)

  // replace file
  jc.addFilesForUpload("/page", "photo", [bar])
  keys = Object.keys(jc.filesForUpload)
  expect(keys.length).toBe(1)
  const barId = keys[0]
  const barUploadedFile = jc.filesForUpload[keys[0]]
  expect(fooId).not.toBe(barId)
  expect(barUploadedFile.fileUploadId).toBe(barId)
  expect(barUploadedFile.execName).toBe("/page")
  expect(barUploadedFile.paramName).toBe("photo")
  expect(barUploadedFile.files[0]).toBe(bar)

  // should add/ upload init command
  expect(jc.commands.length).toBe(1)
  expect(jc.commands[0].type).toBe("init")
  expect(jc.commands[0].initParams.photo).toBe(barId)


  //delete file
  jc.addFilesForUpload("/page", "photo", [])
  expect(Object.keys(jc.filesForUpload).length).toBe(0)

  // should add/ upload init command
  expect(jc.commands.length).toBe(0)

  // support multiple files upload for one param
  jc.addFilesForUpload("/page", "photo", [foo, bar])
  keys = Object.keys(jc.filesForUpload)
  expect(keys.length).toBe(1)
  expect(jc.filesForUpload[keys[0]].files[0]).toBe(foo)
  expect(jc.filesForUpload[keys[0]].files[1]).toBe(bar)
})

test('create file X Upload request  in jembeClient', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{"photo":null},"url":"/page","actions":{}}'>
      <body></body>
    </html>
  `)
  const foo = new File(["foo"], "foo.txt", {
    type: "text/plain",
  });
  const bar = new File(["bar"], "bar.txt", {
    type: "text/plain",
  });
  const jc = window.jembeClient

  // dont create upload request if no files are submited
  let fd = jc.getXUploadRequestFormData()
  expect(fd).toBe(null)

  // create upload request when files are submited
  jc.addFilesForUpload("/page", "photo", [foo])
  fd = jc.getXUploadRequestFormData()
  expect(fd).not.toBeNull()
  let fooUploadId = Object.keys(jc.filesForUpload)[0]
  expect(fd.has(fooUploadId)).toBe(true)
  expect(fd.get(fooUploadId)).toBe(foo)

  jc.addFilesForUpload("/page", "photo", [bar])
  fd = jc.getXUploadRequestFormData()
  let barUploadId = Object.keys(jc.filesForUpload)[0]
  expect(fd.get(barUploadId)).toBe(bar)

  jc.addFilesForUpload("/page", "photo", [])
  fd = jc.getXUploadRequestFormData()
  expect(fd).toBe(null)

  jc.addFilesForUpload("/page", "photo", [foo, bar])
  fd = jc.getXUploadRequestFormData()
  let uploadId = Object.keys(jc.filesForUpload)[0]
  expect(fd.getAll(uploadId).length).toBe(2)

  jc.addFilesForUpload("/page", "photo", foo)
  fd = jc.getXUploadRequestFormData()
  uploadId = Object.keys(jc.filesForUpload)[0]
  expect(fd.getAll(uploadId).length).toBe(1)
})

test('dont merge under jmb-ignore', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{"value":0},"url":"/page","actions":{}}'>
      <head><title>Test</title></head>
      <body>Test<div jmb-ignore>T1</div></body></html>`)
  const xResponse = [
    {
      "execName": "/page1",
      "state": { "value": 1 },
      "url": "/page1",
      "changesUrl": true,
      "dom": `<html>
      <head><title>Test1</title></head>
      <body>Test1<div jmb-ignore>T2</div></body></html>`
    },
  ]
  window.jembeClient.updateDocument(jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page1"><head><title>Test1</title></head>
      <body>Test1<div jmb-ignore="">T1</div></body></html>`
  )
  window.jembeClient.updateDocument(jembeClient.getComponentsAndGlobalsFromXResponse(
    [
      {
        "execName": "/page1",
        "state": { "value": 1 },
        "url": "/page1",
        "changesUrl": true,
        "dom": `<html>
      <head><title>Test2</title></head>
      <body>Test2</body></html>`
      },
    ]))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page1"><head><title>Test2</title></head>
      <body>Test2</body></html>`
  )
})
test('support permanent placeholder and remove component command in x-response', () => {
  buildDocument(`
        <html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><head></head>
        <body>
        <div jmb-name="/page/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"routing":["self"]},"url":"/page/tasks"}\'>
            <div>Task List</div>
            <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
            <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
            <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
            <template jmb-placeholder-permanent="/page/tasks/mview"></template>
            <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
            <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
            <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
        </div>
        </body></html>
  `)
  expect(Object.keys(window.jembeClient.components).length).toBe(2)

  let tasksCompRef = window.jembeClient.components["/page/tasks"]
  expect(Object.keys(tasksCompRef.permanentPlaceHolders).length).toBe(7)
  let xResponse = [
    {
      "execName": "/page/tasks",
      "state": { "routing": ["view"] },
      "actions": {},
      "changesUrl": true,
      "url": "/page/tasks",
      "dom": `<div>
                <template jmb-placeholder="/page/tasks/view"></template>
              </div>`
    },
    {
      "execName": "/page/tasks/view",
      "state": { "id": 1 },
      "actions": { "cancel": true },
      "changesUrl": true,
      "url": "/page/tasks/view/1",
      "dom": `<div>
                View task: 1
                <template jmb-placeholder-permanent="/page/tasks/view/delete"></template>
              </div>`
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div jmb-name="/page/tasks/view">
                View task: 1
                <template jmb-placeholder-permanent="/page/tasks/view/delete"></template>
              </div>
              </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(3)

  const viewCompRef = window.jembeClient.components["/page/tasks/view"]
  expect(Object.keys(viewCompRef.permanentPlaceHolders).length).toBe(1)

  // show view delete modal
  xResponse = [
    {
      "execName": "/page/tasks/view/delete",
      "state": { "id": 1 },
      "actions": { "submit": true, "cancel": true },
      "changesUrl": false,
      "url": "/page/tasks/view/1/delete/1",
      "dom": `<div class="modal">Delete task: 1</div>`
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div jmb-name="/page/tasks/view">
                View task: 1
                <template jmb-placeholder-permanent="/page/tasks/view/delete"></template><div jmb-name="/page/tasks/view/delete" class="modal">Delete task: 1</div>
              </div>
              </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(4)

  // cancel view delete
  xResponse = [
    {
      "globals": true,
      "removeComponents": ["/page/tasks/view/delete"]
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div jmb-name="/page/tasks/view">
                View task: 1
                <template jmb-placeholder-permanent="/page/tasks/view/delete"></template>
              </div>
              </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(3)
  // submit view delete
  xResponse = [
    {
      "execName": "/page/tasks/view/delete",
      "state": { "id": 1 },
      "actions": { "submit": true, "cancel": true },
      "changesUrl": false,
      "url": "/page/tasks/view/1/delete/1",
      "dom": `<div class="modal">Delete task: 1</div>`
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  xResponse = [
    {
      "execName": "/page/tasks",
      "state": { "routing": ["self"] },
      "actions": {},
      "changesUrl": true,
      "url": "/page/tasks",
      "dom":   `<div>
                <div>Task List</div>
                <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                </div>`
    },
    {
      "globals": true,
      "removeComponents": ["/page/tasks/view/delete", "/page/tasks/view"]
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))

  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div>Task List</div>
                <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(2)
  // show mdview 
  xResponse = [
    {
      "execName": "/page/tasks/mdview",
      "state": { "id": 1 },
      "actions": { "submit": true, "cancel": true },
      "changesUrl": false,
      "url": "/page/tasks/mdview/1",
      "dom": `<div class="modal">MD View task: 1</div>`
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div>Task List</div>
                <template jmb-placeholder-permanent="/page/tasks/mdview"></template><div jmb-name="/page/tasks/mdview" class="modal">MD View task: 1</div>
                <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(3)

  // remove mdview
  xResponse = [
    {
      "globals": true,
      "removeComponents": ["/page/tasks/mdview"]
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div>Task List</div>
                <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(2)
  expect(window.jembeClient.getXRequestJson()).toBe(JSON.stringify(
    {
      "components": [
        { "execName": "/page", "state": {} },
        { "execName": "/page/tasks", "state": { "routing": ["self"] } },
      ],
      "commands": []
    }
  ))
  expect(Object.keys(window.jembeClient.components["/page/tasks"].placeHolders).includes("/page/tasks/mdview")).toBe(false)
  // remove not existing components
  xResponse = [
    {
      "execName": "/page/tasks",
      "state": { "routing": ["self"] },
      "actions": {},
      "changesUrl": true,
      "url": "/page/tasks",
      "dom":   `<div>
                <div>Task List</div>
                <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                </div>`
    },
    {
      "globals": true,
      "removeComponents": ["/page/tasks/mdview","/page/tasks/mdcreate","/page/tasks/mdupdate"]
    }
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
        <body>
        <div jmb-name="/page/tasks">
                <div>Task List</div>
                <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                </div>
        
  </body></html>`
  )
  expect(Object.keys(window.jembeClient.components).length).toBe(2)
})

//end upload
test('update input value with x-response', () => {
  buildDocument(`
    <html jmb-name="/page" jmb-data='{"changesUrl":true,"state":{},"url":"/page","actions":{}}'>
      <head></head>
      <body>
        <div jmb-name="/page/form" 
             jmb-data='{"changesUrl":true,"state":{},"url":"/page/form","actions":{}}'>
        <input class="form-input " id="-main-tasks-settings-rename--name" jmb-on:change.defer="form.name = $self.value;modified_fields.indexOf('name') === -1 &amp;&amp; modified_fields.push('name');" jmb-on:keydown.enter="$self.blur();$self.focus();submit()" name="name" required="" type="text" value="Value1">
        </div>
      </body>
    </html>
  `)
  const xResponse = [
    {
      "execName": "/page/form",
      "state": {},
      "url": "/page/form",
      "changesUrl": true,
      "dom": `<div>
        <input class="form-input " id="-main-tasks-settings-rename--name" jmb-on:change.defer="form.name = $self.value;modified_fields.indexOf('name') === -1 &amp;&amp; modified_fields.push('name');" jmb-on:keydown.enter="$self.blur();$self.focus();submit()" name="name" required="" type="text" value="Value2">
        </div>`
    },
  ]
  window.jembeClient.updateDocument(window.jembeClient.getComponentsAndGlobalsFromXResponse(xResponse))
  expect(document.documentElement.outerHTML).toBe(
    `<html jmb-name="/page"><head></head>
      <body>
        <div jmb-name="/page/form">
        <input class="form-input " id="-main-tasks-settings-rename--name" jmb-on:change.defer="form.name = $self.value;modified_fields.indexOf('name') === -1 &amp;&amp; modified_fields.push('name');" jmb-on:keydown.enter="$self.blur();$self.focus();submit()" name="name" required="" type="text" value="Value2">
        </div>
      
    
  </body></html>`
  )
})