from typing import TYPE_CHECKING, Any, Dict, Tuple
from inspect import cleandoc
from jembe import Component, action, listener, config

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
        return self.render_template_string("""<div>View task: {{id}}</div>""")

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

    @listener(event=("cancel"), source="view")
    def on_cancel_view(self, event: "jembe.Event"):
        self.state.routing = ("self",)

    @listener(event="_display", source=("view", "update", "create"))
    def on_swap_display(self, event: "jembe.Event"):
        self.state.routing = (event.source_name,)

    # modals
    @listener(event=("submit", "cancel"), source=("mupdate", "mcreate"))
    def on_mu_submit_or_cancel(self, event: "jembe.Event"):
        self.remove_subcomponent(event.source_name)
        self.display_subcomponent("mview", id=event.id)
        if event.name == "submit":
            return True

    @listener(event="cancel", source=("mview",))
    def on_mview_cancel(self, event: "jembe.Event"):
        self.remove_subcomponent(event.source_name)

    @listener(event="submit", source="mview/delete")
    def on_mvdelete(self, event: "jembe.Event"):
        self.remove_subcomponent(event.source_name)
        return True

    # details
    @listener(event=("submit", "cancel"), source=("mdupdate", "mdcreate"))
    def on_mdu_submit_or_cancel(self, event: "jembe.Event"):
        self.remove_subcomponent(event.source_name)
        self.display_subcomponent("mdview", id=event.id)
        if event.name == "submit":
            return True

    @listener(event="cancel", source=("mdview",))
    def on_mdview_cancel(self, event: "jembe.Event"):
        self.remove_subcomponent(event.source_name)

    @listener(event="submit", source="mdview/delete")
    def on_mdvdelete(self, event: "jembe.Event"):
        self.remove_subcomponent(event.source_name)
        return True

    def display(self) -> "jembe.DisplayResponse":
        return self.render_template_string(
            cleandoc(
                """
                <div>
                    {% if "self" in routing %}
                    <div>Task List</div>
                    {% endif %}
                    {% if "view" in routing %}{{component("view", **routing_to.get("view",dict()))}}{% endif %}
                    {% if "update" in routing %}{{component("update", **routing_to.get("update",dict()))}}{% endif %}
                    {% if "create" in routing %}{{component("create")}}{% endif %}
                    {{placeholder("mdview")}}
                    {{placeholder("mdupdate")}}
                    {{placeholder("mdcreate")}}
                    {{placeholder("mview")}}
                    {{placeholder("mupdate")}}
                    {{placeholder("mcreate")}}
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
