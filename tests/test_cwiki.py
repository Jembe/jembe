from typing import Any, Dict, Optional
from flask import json
from jembe import (
    Component,
    action,
    listener,
    config,
    NotFound,
    Unauthorized,
    UrlPath,
    ComponentConfig
)
from dataclasses import dataclass, field


def test_wiki(jmb, client):
    """bulding simple wiki app for testing server side processing and api"""

    # data definition
    @dataclass
    class User:
        username: str

    @dataclass
    class WikiPage:
        name: str
        title: str
        parent: Optional[str]

        @property
        def path(self):
            return "{}/{}".format(self.parent, self.name) if self.parent else self.name

    # database
    class WikiDb:
        def __init__(self):
            self.pages: Dict[str, WikiPage] = dict(
                root=WikiPage(name="root", title="Root", parent=None)
            )

        def exist(self, page_path: str) -> bool:
            return page_path in self.pages

        def add(self, page: "WikiPage"):
            self.pages[page.path] = page

        def get(self, page_path: str):
            return self.pages[page_path]

        def get_children(self, page_path: str):
            return [page for page in self.pages.values() if page.parent == page_path]

        def get_root_page(self):
            return self.pages["root"]

    wikidb = WikiDb()

    # service to get currently logged user
    # so we dont need to create login components
    session: dict = dict(user=None)

    # forms
    @dataclass
    class WikiEditForm:
        title: str
        error: Optional[str] = field(default=None, init=False)

    @dataclass
    class WikiAddForm:
        name: str
        title: str
        error: Optional[str] = field(default=None, init=False)

    # components
    class View(Component):
        def __init__(self, page_path: UrlPath):
            if not wikidb.exist(self.state.page_path):
                raise NotFound()
            super().__init__()

        def display(self):
            self.page = wikidb.get(self.state.page_path)
            self.children = wikidb.get_children(self.state.page_path)
            self.emit("set_page_title", title=self.page.title)
            return self.render_template_string(
                """<div><h1>{{page.title}}</h1>"""
                """<div>{% for c in children %}<a jmb-on:click="$jmb.set('page_path','{{c.path}}')">{{c.title}}</a><br>{% endfor %}</div></div>"""
            )

    class Edit(Component):
        def __init__(
            self,
            page_path: UrlPath,
            form: Optional[WikiEditForm] = None,
            user: Optional[User] = None,
        ):
            if not wikidb.exist(page_path):
                raise NotFound()

            if user is None or user.username != "admin":
                raise Unauthorized()

            if form is None:
                self.state.form = WikiEditForm(title=self.page.title)

            super().__init__()

        @classmethod
        def load_init_param(
            cls, config: "ComponentConfig", param_name: str, param_value: Any
        ) -> Any:
            if param_name == "form":
                if param_value is None:
                    return None
                return WikiEditForm(title=param_value.get("title", ""))
            else:
                return super().load_init_param(config, param_name, param_value)

        def inject(self):
            return dict(user=session.get("user", None))

        @action
        def save(self):
            # TODO state.form is dict it should be casted to WikiEditForm from jsonobject on initialise
            is_form_valid = bool(self.state.form.title)
            if is_form_valid:
                self.page.title = self.state.form.title
                self.emit("save")
                return False  # don't redisplay
            self.state.form.error = "Title is required"

        def display(self):
            self.emit("set_page_title", title="Edit: {}".format(self.page.title))
            return self.render_template_string(
                "<h1>Edit: {{page.title}}</h1>"
                """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
                """<label>Title: <input type="text" value="{{form.title}}" jmb-on.change="$jmb.set('form.title', this.value)"></label>"""
                """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
                """<button type="button" jmb-on:click="$jmb.emit('cancel', to='..')">Cancel</button>"""
            )

        @property
        def page(self) -> "WikiPage":
            try:
                return self._page
            except AttributeError:
                self._page: "WikiPage" = wikidb.get(self.state.page_path)
                return self._page

    class Add(Component):
        def __init__(
            self,
            page_path: UrlPath,
            form: Optional[WikiAddForm] = None,
            user: Optional[User] = None,
        ):
            if not wikidb.exist(page_path):
                raise NotFound()

            if user is None or user.username != "admin":
                raise Unauthorized()

            if form is None:
                self.state.form = WikiAddForm(name="", title="")

            super().__init__()

        @classmethod
        def load_init_param(
            cls, config: "ComponentConfig", param_name: str, param_value: Any
        ) -> Any:
            if param_name == "form":
                if param_value is None:
                    return None
                return WikiAddForm(
                    name=param_value.get("name", ""), title=param_value.get("title", "")
                )
            else:
                return super().load_init_param(config, param_name, param_value)

        def inject(self):
            return dict(user=session.get("user", None))

        @action
        def save(self):
            form_is_valid = bool(self.state.form.name) and bool(self.state.form.title)
            if form_is_valid:
                wpage = WikiPage(
                    name=self.state.form.name,
                    title=self.state.form.title,
                    parent=self.state.page_path,
                )
                wikidb.add(wpage)
                self.state.page_path = wpage.path
                self.emit("save")
                return False  # don't redisplay
            self.state.form.error = "Name and title are required"

        def display(self):
            self.page_title = wikidb.get(self.state.page_path).title
            self.emit("set_page_title", title="Add under {}".format(self.page_title))
            return self.render_template_string(
                "<h1>Add under {{page_title}}</h1>"
                """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
                """<label>Name: <input type="text" value="{{form.name}}" jmb-on.change="$jmb.set('form.name', this.value)"></label>"""
                """<label>Title: <input type="text" value="{{form.title}}" jmb-on.change="$jmb.set('form.title', this.value)"></label>"""
                """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
                """<button type="button" jmb-on:click="$jmb.emit('cancel', to='..')">Cancel</button>"""
            )

    @config(Component.Config(changes_url=False))
    class PageTitle(Component):
        def __init__(self, title: str = "Wiki"):
            super().__init__()

        @listener(event="set_page_title")
        def on_set_page_title(self, event):
            self.state.title = event.title
            # return False

        @action(deferred=True)
        def display(self):
            return self.render_template_string("<title>{{title}}</title>")

    @jmb.page(
        "wiki",
        Component.Config(
            components=dict(page_title=PageTitle, view=View, edit=Edit, add=Add)
        ),
    )
    class Wiki(Component):
        def __init__(self, mode: str = "view"):
            self.goto: Optional[str] = None
            super().__init__()

        @listener(event="_display", source=["view", "edit", "add"])
        def on_display_child(self, event):
            self.state.mode = event.source._config.name
            self.goto = event.source.state.page_path

        @listener(event=["cancel", "save"], source=["edit", "add"])
        def on_cancel_edit_or_add(self, event):
            self.goto = event.source.state.page_path
            self.state.mode = "view"

        def display(self):
            if self.goto is None:
                self.goto = wikidb.get_root_page().path

            return self.render_template_string(
                "<html><head>{{component('page_title')}}</head>"
                "<body>{{component(mode, page_path=goto)}}</body></html>"
            )

    # initial display
    ######################################
    r = client.get("/wiki")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/wiki" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"mode":"view"},"url":"/wiki"}\'>"""
        """<head><title jmb-name="/wiki/page_title" jmb-data=\'{"actions":{},"changesUrl":false,"state":{"title":"Root"},"url":"/wiki/page_title"}\'>Root</title></head>"""
        """<body>"""
        """<div jmb-name="/wiki/view" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page_path":"root"},"url":"/wiki/view/root"}\'>"""
        """<h1>Root</h1>"""
        """<div></div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")

    # try edit root before loggedin
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="view")),
                    dict(execName="/wiki/page_title", state=dict(title="Root")),
                    dict(execName="/wiki/view", state=dict(page_path="root")),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/edit",
                        initParams=dict(page_path="root"),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/edit",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 401

    # login
    ######################################
    session["user"] = User("admin")

    # display edit
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="view")),
                    dict(execName="/wiki/page_title", state=dict(title="Root")),
                    dict(execName="/wiki/view", state=dict(page_path="root")),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/edit",
                        initParams=dict(page_path="root"),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/edit",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/wiki"
    assert json_response[0]["state"] == dict(mode="edit")
    assert json_response[0]["dom"] == (
        """<html><head><template jmb-placeholder="/wiki/page_title"></template></head>"""
        """<body><template jmb-placeholder="/wiki/edit"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/wiki/page_title"
    assert json_response[1]["state"] == dict(title="Edit: Root")
    assert json_response[1]["dom"] == "<title>Edit: Root</title>"
    assert json_response[2]["execName"] == "/wiki/edit"
    assert json_response[2]["state"] == dict(
        form=dict(error=None, title="Root"), page_path="root"
    )
    assert json_response[2]["dom"] == (
        """<h1>Edit: Root</h1>"""
        """<label>Title: <input type="text" value="Root" jmb-on.change="$jmb.set('form.title', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel', to='..')">Cancel</button>"""
    )

    # change root title - to invalid title
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="edit")),
                    dict(execName="/wiki/page_title", state=dict(title="Edit: Root")),
                    dict(
                        execName="/wiki/edit",
                        state=dict(
                            form=dict(error=None, title="Root"), page_path="root"
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/edit",
                        initParams=dict(
                            form=dict(error=None, title=""), page_path="root"
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/edit",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/wiki/edit"
    assert json_response[0]["state"] == dict(
        form=dict(error="Title is required", title=""), page_path="root"
    )
    assert json_response[0]["dom"] == (
        """<h1>Edit: Root</h1>"""
        """<div>Title is required</div>"""
        """<label>Title: <input type="text" value="" jmb-on.change="$jmb.set('form.title', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel', to='..')">Cancel</button>"""
    )

    # change root title - valid title - goto view
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="edit")),
                    dict(execName="/wiki/page_title", state=dict(title="Edit: Root")),
                    dict(
                        execName="/wiki/edit",
                        state=dict(
                            form=dict(error="Title is required", title=""),
                            page_path="root",
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/edit",
                        initParams=dict(
                            form=dict(error="Title is required", title="New Root"),
                            page_path="root",
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/edit",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/wiki"
    assert json_response[0]["state"] == dict(mode="view")
    assert json_response[0]["dom"] == (
        """<html><head><template jmb-placeholder="/wiki/page_title"></template></head>"""
        """<body><template jmb-placeholder="/wiki/view"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/wiki/page_title"
    assert json_response[1]["state"] == dict(title="New Root")
    assert json_response[1]["dom"] == ("""<title>New Root</title>""")
    assert json_response[2]["execName"] == "/wiki/view"
    assert json_response[2]["state"] == dict(page_path="root")
    assert json_response[2]["dom"] == ("""<div><h1>New Root</h1><div></div></div>""")

    # add page to root - display
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="view")),
                    dict(execName="/wiki/page_title", state=dict(title="New Root")),
                    dict(execName="/wiki/view", state=dict(page_path="root")),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/add",
                        initParams=dict(page_path="root"),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/add",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/wiki"
    assert json_response[0]["state"] == dict(mode="add")
    assert json_response[0]["dom"] == (
        """<html><head><template jmb-placeholder="/wiki/page_title"></template></head>"""
        """<body><template jmb-placeholder="/wiki/add"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/wiki/page_title"
    assert json_response[1]["state"] == dict(title="Add under New Root")
    assert json_response[1]["dom"] == ("""<title>Add under New Root</title>""")
    assert json_response[2]["execName"] == "/wiki/add"
    assert json_response[2]["state"] == dict(
        page_path="root", form=dict(error=None, name="", title="")
    )
    assert json_response[2]["dom"] == (
        "<h1>Add under New Root</h1>"
        """<label>Name: <input type="text" value="" jmb-on.change="$jmb.set('form.name', this.value)"></label>"""
        """<label>Title: <input type="text" value="" jmb-on.change="$jmb.set('form.title', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel', to='..')">Cancel</button>"""
    )

    # add page to root - save valid
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="add")),
                    dict(
                        execName="/wiki/page_title",
                        state=dict(title="Add under New Root"),
                    ),
                    dict(
                        execName="/wiki/add",
                        state=dict(
                            page_path="root", form=dict(error=None, name="", title="")
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/add",
                        initParams=dict(
                            page_path="root",
                            form=dict(error=None, name="jembe", title="Jembe Page"),
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/add",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/wiki"
    assert json_response[0]["state"] == dict(mode="view")
    assert json_response[0]["dom"] == (
        """<html><head><template jmb-placeholder="/wiki/page_title"></template></head>"""
        """<body><template jmb-placeholder="/wiki/view"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/wiki/page_title"
    assert json_response[1]["state"] == dict(title="Jembe Page")
    assert json_response[1]["dom"] == ("""<title>Jembe Page</title>""")
    assert json_response[2]["execName"] == "/wiki/view"
    assert json_response[2]["state"] == dict(page_path="root/jembe")
    assert json_response[2]["dom"] == ("""<div><h1>Jembe Page</h1><div></div></div>""")

    # add invalid page to root
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="add")),
                    dict(
                        execName="/wiki/page_title",
                        state=dict(title="Add under New Root"),
                    ),
                    dict(
                        execName="/wiki/add",
                        state=dict(
                            page_path="root", form=dict(error=None, name="", title="")
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/add",
                        initParams=dict(
                            page_path="root",
                            form=dict(error=None, name="", title="Jembe Invalid Page"),
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/add",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/wiki/add"
    assert json_response[0]["state"] == dict(
        form=dict(
            error="Name and title are required", name="", title="Jembe Invalid Page"
        ),
        page_path="root",
    )
    assert json_response[0]["dom"] == (
        "<h1>Add under New Root</h1>"
        "<div>Name and title are required</div>"
        """<label>Name: <input type="text" value="" jmb-on.change="$jmb.set('form.name', this.value)"></label>"""
        """<label>Title: <input type="text" value="Jembe Invalid Page" jmb-on.change="$jmb.set('form.title', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel', to='..')">Cancel</button>"""
    )

    # view root page with link to jembe page
    ######################################
    r = client.get("/wiki")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/wiki" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"mode":"view"},"url":"/wiki"}\'>"""
        """<head><title jmb-name="/wiki/page_title" jmb-data=\'{"actions":{},"changesUrl":false,"state":{"title":"New Root"},"url":"/wiki/page_title"}\'>New Root</title></head>"""
        """<body>"""
        """<div jmb-name="/wiki/view" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page_path":"root"},"url":"/wiki/view/root"}\'>"""
        """<h1>New Root</h1>"""
        """<div><a jmb-on:click="$jmb.set('page_path',\'root/jembe\')">Jembe Page</a><br></div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")

    # add page under jembe page
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="add")),
                    dict(
                        execName="/wiki/page_title",
                        state=dict(title="Add under Jembe Page"),
                    ),
                    dict(
                        execName="/wiki/add",
                        state=dict(
                            page_path="root/jembe",
                            form=dict(error=None, name="", title=""),
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/add",
                        initParams=dict(
                            page_path="root/jembe",
                            form=dict(error=None, name="suite", title="Suite Page"),
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/add",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/wiki"
    assert json_response[0]["state"] == dict(mode="view")
    assert json_response[0]["dom"] == (
        """<html><head><template jmb-placeholder="/wiki/page_title"></template></head>"""
        """<body><template jmb-placeholder="/wiki/view"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/wiki/page_title"
    assert json_response[1]["state"] == dict(title="Suite Page")
    assert json_response[1]["dom"] == ("""<title>Suite Page</title>""")
    assert json_response[2]["execName"] == "/wiki/view"
    assert json_response[2]["state"] == dict(page_path="root/jembe/suite")
    assert json_response[2]["dom"] == ("""<div><h1>Suite Page</h1><div></div></div>""")
    # edit page under existing page
    ######################################
    r = client.post(
        "/wiki",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/wiki", state=dict(mode="edit")),
                    dict(
                        execName="/wiki/page_title",
                        state=dict(title="Edit Suite Page"),
                    ),
                    dict(
                        execName="/wiki/edit",
                        state=dict(
                            page_path="root/jembe/suite",
                            form=dict(error=None, title="Suite Page"),
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/wiki/edit",
                        initParams=dict(
                            page_path="root/jembe/suite",
                            form=dict(error=None, title="Jembe Suite Page"),
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/wiki/edit",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/wiki"
    assert json_response[0]["state"] == dict(mode="view")
    assert json_response[0]["dom"] == (
        """<html><head><template jmb-placeholder="/wiki/page_title"></template></head>"""
        """<body><template jmb-placeholder="/wiki/view"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/wiki/page_title"
    assert json_response[1]["state"] == dict(title="Jembe Suite Page")
    assert json_response[1]["dom"] == ("""<title>Jembe Suite Page</title>""")
    assert json_response[2]["execName"] == "/wiki/view"
    assert json_response[2]["state"] == dict(page_path="root/jembe/suite")
    assert json_response[2]["dom"] == (
        """<div><h1>Jembe Suite Page</h1><div></div></div>"""
    )
    # get wiki page via direct http get
    ######################################
    r = client.get("/wiki/view/root/jembe")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/wiki" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"mode":"view"},"url":"/wiki"}\'>"""
        """<head><title jmb-name="/wiki/page_title" jmb-data=\'{"actions":{},"changesUrl":false,"state":{"title":"Jembe Page"},"url":"/wiki/page_title"}\'>Jembe Page</title></head>"""
        """<body>"""
        """<div jmb-name="/wiki/view" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page_path":"root/jembe"},"url":"/wiki/view/root/jembe"}\'>"""
        """<h1>Jembe Page</h1>"""
        """<div><a jmb-on:click="$jmb.set('page_path',\'root/jembe/suite\')">Jembe Suite Page</a><br></div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")

    # TODO add back link, navigation menu etc in demo app
