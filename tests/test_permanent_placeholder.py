from jembe.component import component
from typing import TYPE_CHECKING, Any, Dict, Tuple
from inspect import cleandoc
from jembe import Component, action, listener, config
from flask import json

if TYPE_CHECKING:
    import jembe


@config(Component.Config(changes_url=False))
class DeleteTask(Component):
    def __init__(self, id: int):
        super().__init__()

    def display(self) -> "jembe.DisplayResponse":
        return self.render_template_string(
            # <button jmb-on:click="submit()">Delete</button>
            # <button jmb-on:click="cancel()">cancel</button>
            """<div class="modal">Delete task: {{id}}</div>"""
        )

    @action
    def cancel(self):
        self.emit("cancel", id=self.state.id)

    @action
    def submit(self):
        self.emit("submit", id=self.state.id)


@config(Component.Config(components=dict(delete=DeleteTask)))
class ViewTask(Component):
    def __init__(self, id: int):
        super().__init__()

    def display(self) -> "jembe.DisplayResponse":
        if self._config.template == "modal":
            return self.render_template_string(
                cleandoc(
                    # <button jmb-on:click="{{component('delete', id=id).jrl()}}">
                    #   delete
                    # </button>
                    # <button jmb-on:click="{{component('../update', id=id).jrl()}}">
                    #   update
                    # </button>
                    # <button jmb-on:click="cancel()">Cancel</button>
                    """
                    <div class="modal">
                        View task: {{id}}
                        {{placeholder("delete")}}
                    </div>
                    """
                )
            )
        return self.render_template_string(
            cleandoc(
                """
                <div>
                    View task: {{id}}
                    {{placeholder("delete")}}
                </div>
                """
            )
        )

    @listener(event=("cancel", "submit"), source="delete")
    def on_delete_cancel(self, event: "jembe.Event"):
        self.remove_component("delete")

    @action
    def cancel(self):
        self.emit("cancel", id=self.state.id)


class UpdateTask(Component):
    def __init__(self, id: int):
        super().__init__()

    def display(self) -> "jembe.DisplayResponse":
        if self._config.template == "modal":
            return self.render_template_string(
                """<div class="modal">Update task: {{id}}</div>"""
            )
        return self.render_template_string("""<div>Update task: {{id}}</div>""")

    @action
    def cancel(self):
        self.emit("cancel", id=self.state.id)

    @action
    def submit(self):
        self.emit("submit", id=self.state.id)


class CreateTask(Component):
    def display(self) -> "jembe.DisplayResponse":
        if self._config.template == "modal":
            return self.render_template_string(
                """<div class="modal">Create task</div>"""
            )
        return self.render_template_string("""<div>Create task</div>""")

    @action
    def cancel(self):
        self.emit("cancel", id=None)

    @action
    def submit(self):
        self.emit("submit", id=0)


def firstinset(s):
    for i in s:
        break
    return i


@config(
    Component.Config(
        components=dict(
            view=ViewTask,
            update=UpdateTask,
            create=CreateTask,
            mview=(ViewTask, ViewTask.Config(template="modal")),
            mupdate=(UpdateTask, UpdateTask.Config(template="modal")),
            mcreate=(CreateTask, CreateTask.Config(template="modal")),
            mdelete=DeleteTask,
            # master - detail
            mdview=ViewTask,
            mdupdate=UpdateTask,
            mdcreate=CreateTask,
        )
    )
)
class TaskList(Component):
    def __init__(self, routing: Tuple[str, ...] = ("self",)):
        self.routing_to: Dict[str, Dict[str, Any]] = dict()
        rswaps = set(self.state.routing).intersection(("view", "update", "create"))
        if len(rswaps) >= 1:
            self.state.routing = (firstinset(rswaps),)
        super().__init__()

    # swaps
    @listener(event=("submit", "cancel"), source=("update", "create"))
    def on_uc_submit_or_cancel(self, event: "jembe.Event"):
        self.state.routing = ("view",)
        self.routing_to["view"] = dict(id=event.id)

    @listener(event=("submit"), source="view/delete")
    def on_delete(self, event: "jembe.Event"):
        self.state.routing = ("self",)
        self.remove_component("view")

    @listener(event=("cancel"), source="view")
    def on_cancel_view(self, event: "jembe.Event"):
        self.state.routing = ("self",)

    @listener(event="_display", source=("view", "update", "create"))
    def on_swap_display(self, event: "jembe.Event"):
        self.state.routing = (event.source_name,)

    # modals
    @listener(event=("submit", "cancel"), source=("mupdate", "mcreate"))
    def on_mu_submit_or_cancel(self, event: "jembe.Event"):
        self.remove_component(event.source_name)
        self.display_component("mview", id=event.id)
        if event.name == "submit":
            return True

    @listener(event="cancel", source=("mview",))
    def on_mview_cancel(self, event: "jembe.Event"):
        self.remove_component(event.source_name)

    @listener(event="submit", source="mview/delete")
    def on_mvdelete(self, event: "jembe.Event"):
        self.remove_component(event.source_name)
        return True

    # details
    @listener(event=("submit", "cancel"), source=("mdupdate", "mdcreate"))
    def on_mdu_submit_or_cancel(self, event: "jembe.Event"):
        self.remove_component(event.source_name)
        self.display_component("mdview", id=event.id)
        if event.name == "submit":
            return True

    @listener(event="cancel", source=("mdview",))
    def on_mdview_cancel(self, event: "jembe.Event"):
        self.remove_component(event.source_name)

    @listener(event="submit", source="mdview/delete")
    def on_mdvdelete(self, event: "jembe.Event"):
        self.remove_component(event.source_name)
        return True

    def display(self) -> "jembe.DisplayResponse":
        return self.render_template_string(
            cleandoc(
                """
                <div>
                {%- if "self" in routing %}
                    <div>Task List</div>
                    {{placeholder("mdview")}}
                    {{placeholder("mdupdate")}}
                    {{placeholder("mdcreate")}}
                    {{placeholder("mview")}}
                    {{placeholder("mupdate")}}
                    {{placeholder("mcreate")}}
                    {{placeholder("mdelete")}}
                {% elif "view" in routing %}
                    {{component("view", **routing_to.get("view",dict()))}}
                {% elif "update" in routing %}
                    {{component("update", **routing_to.get("update",dict()))}}
                {% elif "create" in routing %}
                    {{component("create")}}
                {% endif -%}
                </div>
                """
            )
        )


@config(
    Component.Config(
        components=dict(
            tasks=TaskList,
        )
    )
)
class Page(Component):
    def display(self) -> "jembe.DisplayResponse":
        return self.render_template_string(
            cleandoc(
                """
                <html><head></head>
                <body>
                {{component("tasks")}}
                </body>
                """
            )
        )


def test_display_tasks(jmb, client):
    jmb.add_page("page", Page)

    # display page
    res = client.get("/page")
    assert res.status_code == 200
    assert str(res.data, "utf-8") == cleandoc(
        """
        <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
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
        """
    )
    # View -> Update (Submit, Cancle) -> View/Delete (Submit,Cancel), View(Cancel)
    # Go to View
    r = client.post(
        "/page/tasks",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/tasks", state=dict(routing=("self",))),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/page/tasks/view",
                        initParams=dict(id=1),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/page/tasks/view",
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
    assert json_response == (
        [
            dict(
                execName="/page/tasks",
                state=dict(routing=["view"]),
                actions=dict(),
                changesUrl=True,
                url="/page/tasks",
                dom=cleandoc(
                    """
                    <div>
                        <template jmb-placeholder="/page/tasks/view"></template>
                    </div>
                    """
                ),
            ),
            dict(
                execName="/page/tasks/view",
                state=dict(id=1),
                actions=dict(cancel=True),
                changesUrl=True,
                url="/page/tasks/view/1",
                dom=cleandoc(
                    """
                <div>
                    View task: 1
                    <template jmb-placeholder-permanent="/page/tasks/view/delete"></template>
                </div>
                """
                ),
            ),
        ]
    )
    # Display View/Delete
    r = client.post(
        "/page/tasks/view/1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/tasks", state=dict(routing=("view",))),
                    dict(execName="/page/tasks/view", state=dict(id=1)),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/page/tasks/view/delete",
                        initParams=dict(id=1),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/page/tasks/view/delete",
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
    assert json_response == (
        [
            dict(
                execName="/page/tasks/view/delete",
                state=dict(id=1),
                actions=dict(submit=True, cancel=True),
                changesUrl=False,
                url="/page/tasks/view/1/delete/1",
                dom=cleandoc(
                    """
                    <div class="modal">Delete task: 1</div>
                    """
                ),
            ),
        ]
    )
    # Display View/Delete Cancel
    r = client.post(
        "/page/tasks/view/1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/tasks", state=dict(routing=("view",))),
                    dict(execName="/page/tasks/view", state=dict(id=1)),
                    dict(execName="/page/tasks/view/delete", state=dict(id=1)),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/page/tasks/view/delete",
                        actionName="cancel",
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
    assert json_response == (
        [
            dict(
                globals=True,
                removeComponents=["/page/tasks/view/delete"],
            ),
        ]
    )
    # Display View/Delete Submit
    r = client.post(
        "/page/tasks/view/1/delete/1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/tasks", state=dict(routing=("view",))),
                    dict(execName="/page/tasks/view", state=dict(id=1)),
                    dict(execName="/page/tasks/view/delete", state=dict(id=1)),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/page/tasks/view/delete",
                        actionName="submit",
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
    assert json_response == (
        [
            dict(
                execName="/page/tasks",
                state=dict(routing=["self"]),
                actions=dict(),
                changesUrl=True,
                url="/page/tasks",
                dom=cleandoc(
                    """
                    <div>
                        <div>Task List</div>
                        <template jmb-placeholder-permanent="/page/tasks/mdview"></template>
                        <template jmb-placeholder-permanent="/page/tasks/mdupdate"></template>
                        <template jmb-placeholder-permanent="/page/tasks/mdcreate"></template>
                        <template jmb-placeholder-permanent="/page/tasks/mview"></template>
                        <template jmb-placeholder-permanent="/page/tasks/mupdate"></template>
                        <template jmb-placeholder-permanent="/page/tasks/mcreate"></template>
                        <template jmb-placeholder-permanent="/page/tasks/mdelete"></template>
                    </div>
                    """
                ),
            ),
            dict(
                globals=True,
                removeComponents=["/page/tasks/view/delete", "/page/tasks/view"],
            ),
        ]
    )


def test_display_view_task(jmb, client):
    jmb.add_page("page", Page)

    res = client.get("/page/tasks/view/1")
    assert res.status_code == 200
    assert str(res.data, "utf-8") == cleandoc(
        """
        <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
        <html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><head></head>
        <body>
        <div jmb-name="/page/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"routing":["view"]},"url":"/page/tasks"}\'>
            <div jmb-name="/page/tasks/view" jmb-data=\'{"actions":{"cancel":true},"changesUrl":true,"state":{"id":1},"url":"/page/tasks/view/1"}\'>
            View task: 1
            <template jmb-placeholder-permanent="/page/tasks/view/delete"></template>
        </div>
        </div>
        </body></html>
        """
    )

