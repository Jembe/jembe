from typing import TYPE_CHECKING, Optional
from jembe import Component
from flask import json
from jembe import action

# from jembe import action, listener
# from jembe.utils import build_url

if TYPE_CHECKING:
    from uuid import UUID

    # from jembe import Event


def test_simple_page(jmb, client):
    class SimplePage(Component):
        pass

    jmb.add_page("simple_page", SimplePage)
    r = client.get("/simple_page")
    assert r.status_code == 200
    assert b"<h1>Simple page</h1>" in r.data
    assert (
        b'<html lang="en" jmb-name="/simple_page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/simple_page"}\''
        in r.data
    )


def test_empty_page(jmb, client):
    class EmptyPage(Component):
        def display(self):
            return self.render_template_string("")

    jmb.add_page("page", EmptyPage)
    r = client.get("/page")
    assert r.status_code == 200
    assert (
        b'<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'>'
        in r.data
    )
    assert b"<div></div>" in r.data


def test_simple_page_with_custom_template(jmb, client):
    class SimplePage(Component):
        pass

    jmb.add_page(
        "simple_page",
        SimplePage,
        SimplePage.Config(template="simple_page_custom.html"),
    )

    r = client.get("/simple_page")
    assert r.status_code == 200
    assert b"<h1>Custom simple page</h1>" in r.data


def test_page_with_template(jmb, client):
    class Page(Component):
        class Config(Component.Config):
            def __init__(self, template="simple_page_custom.html", **params):
                super().__init__(template=template, **params)

    jmb.add_page("page", Page)
    r = client.get("/page")
    assert r.status_code == 200
    assert b"<h1>Custom simple page</h1>" in r.data


def test_page_with_decorator(jmb, client):
    @jmb.page("welcome")
    class WelcomePage(Component):
        pass

    @jmb.page("hello", Component.Config(template="simple_page.html"))
    class HelloPage(Component):
        pass

    r = client.get("/welcome")
    assert r.status_code == 200
    assert b"<h1>Welcome</h1>" in r.data

    r = client.get("/hello")
    assert r.status_code == 200
    assert b"<h1>Simple page</h1>" in r.data


def test_blog_post_page(jmb, client):
    @jmb.page("blogpost")
    class BlogPost(Component):
        def __init__(self, id: int):
            self.id = id
            super().__init__()

        def display(self):
            return self.render_template_string(
                """
                <html>
                <head></head>
                <body>Blog post id == {{id}}</body>
                </html>
                """
            )

    r = client.get("/blogpost/1")
    assert r.status_code == 200
    assert b"Blog post id == 1" in r.data


def test_counter_on_page(jmb, client):
    @jmb.page("cop")
    class CounterOnPage(Component):
        def __init__(self, counter: int = 0):
            super().__init__()

        @action
        def increase(self):
            self.state.counter += 1

        def display(self):
            return self.render_template_string(
                """<html>
                <head></head>
                <body>
                    <div>Counter: {{counter}}</div>
                    <div>c={{state.counter}}</div>
                    <button jmb:click="increase()"/>
                </body>
                </html>"""
            )

    # First load
    res = client.get("/cop")
    assert res.status_code == 200
    assert b"Counter: 0" in res.data
    assert b"c=0" in res.data
    assert (
        b'jmb-name="/cop" jmb-data=\'{"actions":{"increase":true},"changesUrl":true,"state":{"counter":0},"url":"/cop"}\''
        in res.data
    )
    assert b'<button jmb:click="increase()"' in res.data

    # Refresh page with ajax request
    ajax_post_data = json.dumps(
        dict(
            components=[],
            commands=[
                dict(
                    type="call",  # emit, initialise
                    componentExecName="/cop",
                    actionName="display",
                    args=list(),
                    kwargs=dict(),
                )
            ],
        )
    )
    r = client.post("/cop", data=ajax_post_data, headers={"x-jembe": True})
    assert r.status_code == 200

    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 1
    assert ajax_response_data[0]["dom"].startswith("<html")
    assert ajax_response_data[0]["dom"].endswith("</html>")
    assert "Counter: 0" in ajax_response_data[0]["dom"]
    assert "c=0" in ajax_response_data[0]["dom"]
    assert '<button jmb:click="increase()"' in ajax_response_data[0]["dom"]
    assert ajax_response_data[0]["execName"] == "/cop"
    assert ajax_response_data[0]["state"] == {"counter": 0}
    assert ajax_response_data[0]["url"] == "/cop"

    # Call increase action
    ajax_post_data = json.dumps(
        dict(
            components=[dict(execName="/cop", state=dict(counter=0))],
            commands=[
                dict(
                    type="call",
                    componentExecName="/cop",
                    actionName="increase",
                    args=list(),
                    kwargs=dict(),
                )
            ],
        )
    )
    r = client.post("/cop", data=ajax_post_data, headers={"x-jembe": True})
    assert r.status_code == 200

    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 1
    assert "Counter: 1" in ajax_response_data[0]["dom"]
    assert "c=1" in ajax_response_data[0]["dom"]
    assert ajax_response_data[0]["state"] == {"counter": 1}
    assert ajax_response_data[0]["url"] == "/cop"
    assert ajax_response_data[0]["execName"] == "/cop"

