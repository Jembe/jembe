import { expect } from "@jest/globals";
import { JembeClient } from "../../jembe/static/js/jembeClient.js";

test('identify component on simple page', () => {
  const doc = (new DOMParser()).parseFromString(
    `<!DOCTYPE html>
    <html lang="en" jmb:name="/simple_page" jmb:data='{"changes_url":true,"state":{},"url":"/simple_page"}'>
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
    <html jmb:name="/cpage" jmb:data='{"changes_url":true,"state":{},"url":"/cpage"}'>
      <head></head>
      <body>
        <div jmb:name="/cpage/counter" 
             jmb:data='{"changes_url":true,"state":{"value":0},"url":"/cpage/counter"}'>
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
// TODO First write tests here for updatePage (page, page with counters, 
// capp tasks with subtasks and all)