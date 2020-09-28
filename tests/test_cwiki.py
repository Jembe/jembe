from typing import TYPE_CHECKING, Optional, Tuple, Sequence, List
from flask import json
from jembe import (
    Component,
    action,
    listener,
    config,
    redisplay,
    NotFound,
    Forbidden,
    Unauthorized,
    UrlPath,
)
from dataclasses import dataclass


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
            self.pages: Dict[str, "WikiPage"] = dict(
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
        error: Optional[str] = None

    @dataclass
    class WikiAddForm:
        name: str
        title: str
        error: Optional[str] = None

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
                """<div>{% for c in children %}<a onclick="$jmb.set(page_path={{c.path}})">{{c.title}}</a><br>{% endfor %}</div></div>"""
            )

    class Edit(Component):
        def __init__(
            self,
            page_path: UrlPath,
            form: Optional["WikiEditForm"] = None,
            user: Optional["User"] = None,
        ):
            if not wikidb.exist(page_path):
                raise NotFound()

            if user is None or user.username != "admin":
                raise Unauthorized()

            if form is None:
                self.state.form = WikiEditForm(title=self.page.title)

            super.__init__()

        def inject(self):
            return dict(user=session.get("user", None))

        @action
        def save(self):
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
                """<label>Title: <input type="text" value="{{form.title}}" onchange="$jmb.set('form.title', this.value).deffer()"></label>"""
                """<button type="button" onclick="$jmb.call('save')">Save</button>"""
                """<button type="button" onclick="$jmb.emit('cancel').to('..')">Cancel</button>"""
            )

        @property
        def page(self) -> "WikiPage":
            try:
                return self._page
            except AttributeError:
                self._page = wikidb.get(self.state.page_path)
                return self._page

    class Add(Component):
        def __init__(
            self,
            page_path: UrlPath,
            form: Optional["WikiAddForm"] = None,
            user: Optional["User"] = None,
        ):
            if not wikidb.exist(page_path):
                raise NotFound()

            if user is None or user.username != "admin":
                raise Unauthorized()

            if form is None:
                self.state.form = WikiAddForm(name="", title="")

            super.__init__()

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
                """<label>Name: <input type="text" value="{{form.name}}" onchange="$jmb.set('form.name', this.value).deffer()"></label>"""
                """<label>Title: <input type="text" value="{{form.title}}" onchange="$jmb.set('form.title', this.value).deffer()"></label>"""
                """<button type="button" onclick="$jmb.call('save')">Save</button>"""
                """<button type="button" onclick="$jmb.emit('cancel').to('..')">Cancel</button>"""
            )

    @config(Component.Config(changes_url=False))
    class PageTitle(Component):
        def __init__(self, title: str = "Wiki"):
            super().__init__()

        @listener(event="set_page_title")
        def on_set_page_title(self, event):
            self.state.title = event.title
            return False

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

        # @listener(event="_display", source=["./view", "./edit", "./add"])
        @listener(event="_display", source="./view")
        def on_display_child(self, event):
            self.state.mode = event.source._config.name
            self.goto = event.source.state.page_path

        # @listener(event=["cancel", "save"], source=["./edit", "./add"])
        # def on_cancel_edit_or_add(self, event):
        #     self.goto = event.source.state.page_path
        #     self.state.mode = "view"

        def display(self):
            if self.goto is None:
                self.goto = wikidb.get_root_page().path

            return self.render_template_string(
                "<html><head>{{component('page_title')}}</head>"
                "<body>{{component(mode, page_path=goto)}}</body></html>"
            )

    # TODO initial display
    r = client.get("/wiki")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/wiki" jmb:data=\'{"changes_url":true,"state":{"mode":"view"},"url":"/wiki"}\'>"""
        """<head><title jmb:name="/wiki/page_title" jmb:data=\'{"changes_url":false,"state":{"title":"Root"},"url":"/wiki/page_title"}\'>Root</title></head>"""
        """<body>"""
        """<div jmb:name="/wiki/view" jmb:data=\'{"changes_url":true,"state":{"page_path":"root"},"url":"/wiki/view/root"}\'>"""
        """<h1>Root</h1>"""
        """<div></div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")
    # TODO staging deffered command not working when handlig exception make test case and fix it
        # Create add_staging_command and move_staging_commands methods to handle this if necessary

    # TODO try edit root before loggedin
    # login
    # TODO change root title - invalid title
    # TODO change root title - valid title - goto view
    # TODO add page to root
    # TODO add page to root
    # TODO add invalid page to root
    # TODO add page under existing page
    # TODO edit page under existing page
    # TODO get wiki page via direct http get

    # TODO add back link, navigation menu etc in demo app
