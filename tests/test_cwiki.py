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
            self.pages: Dict[str, "WikiPage"] = [
                WikiPage(name="root", title="Root", parent=None)
            ]

        def exist(self, page_path: str) -> bool:
            return page_path in self.pages

        def add(self, page: "WikiPage"):
            self.pages[page.path] = page

        def get(self, page_path: str):
            return self.pages[page_path]

        def get_children(self, page_path: str):
            return [page for page in self.pages if page.parent == page_path]

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

    @dataclass
    class WikiAddForm:
        name: str
        title: str
        error: Optional[str] = None

    # components
    class View(Component):
        def __init__(self, page_path: UrlPath):
            super.__init__()
            if not wikidb.exist(page_path):
                raise NotFound()

        def display(self):
            self.page = wikidb.get(self.state.page_path)
            self.children = wikidb.get_children(self.state.page_path)
            self.emit("set_page_title", title=self.page.title).to_page()
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
            self.page.title = self.state.form.title
            self.emit("saved")
            # don't redisplay
            return False

        def display(self):
            self.emit(
                "set_page_title", title="Edit: {}".format(self.page.title)
            ).to_root_page()
            return self.render_template_string(
                "<h1>Edit: {{page.title}}</h1>"
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
                # don't redisplay
                return False

            # redisplay form
            self.state.form.error = "Name and title are required"

        def display(self):
            self.page_title = wikidb.get(self.state.page_path).title
            self.emit(
                "set_page_title", title="Add under {}".format(self.page_title),
            ).to_root_page()
            return self.render_template_string(
                "<h1>Add under {{page_title}}</h1>"
                """<label>Name: <input type="text" value="{{form.name}}" onchange="$jmb.set('form.name', this.value).deffer()"></label>"""
                """<label>Title: <input type="text" value="{{form.title}}" onchange="$jmb.set('form.title', this.value).deffer()"></label>"""
                """<button type="button" onclick="$jmb.call('save')">Save</button>"""
                """<button type="button" onclick="$jmb.emit('cancel').to('..')">Cancel</button>"""
            )

    @jmb.page("wiki", Component.Config(components=dict(view=View, edit=Edit, add=Add)))
    class Wiki(Component):
        def __init__(self, mode: str = "view", title: str = "Wiki"):
            self.goto: Optional[str] = None
            super().__init__()

        @listener(event="_display", source="./*")
        def on_display_child(self, event):
            self.state.mode = event.source._config.name

        @listener(event="set_page_title", source="./**")
        def on_set_page_title(self, event):
            self.state.title = event.params.title
            return False

        @listener(event=["cancel", "save"], source=["./edit", "./add"])
        def on_cancel_edit_or_add(self, event):
            self.state.mode = "view"
            self.goto = event.source.state.page_path

        def display(self):
            return self.render_template_string(
                "<html><head><title>{{title}}</title></head>"
                "<body>{{component(mode, page_path=goto) if goto else component(mode)}}</body></html>"
            )
    # TODO initial display
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