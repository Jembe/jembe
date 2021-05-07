from typing import Any, Dict, List, TYPE_CHECKING, Dict, Optional, Union
from functools import cached_property
from dataclasses import dataclass, field

from flask import json
from jembe.processor import Event
from jembe.exceptions import BadRequest, JembeError
from jembe.component_config import ComponentConfig, redisplay
from jembe import (
    Component,
    action,
    listener,
    config,
    NotFound,
    Unauthorized,
)

if TYPE_CHECKING:
    from jembe import DisplayResponse

    """build simple task apps for testing server side processing and jembe api"""

# data definition
@dataclass
class User:
    username: str


@dataclass
class Task:
    id: int
    title: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class WipDb:
    # temporary storage of modified and new tasks (Work in Progress)
    def __init__(self, *tasks: Task) -> None:
        self._tasks: Dict[int, Task] = {t.id: t for t in tasks}

    def save(self, original_id: Optional[int] = None) -> Optional[int]:
        map_new_ids: Dict[int, int] = dict()
        tasks = list(self._tasks.values())

        index = 0
        while tasks:
            task = tasks[index]
            if task is None:
                del tasks[index]
                del tasks_db[index]
            elif (
                task.parent_id is None
                or task.parent_id > 0
                or task.parent_id in map_new_ids.keys()
            ):
                # save task
                if task.id < 0:
                    old_id = task.id
                    task.id = (
                        max(tid for tid in tasks_db.keys()) + 1
                        if tasks_db.keys()
                        else 1
                    )
                    map_new_ids[old_id] = task.id

                if task.parent_id and task.parent_id < 0:
                    task.parent_id = map_new_ids[task.parent_id]

                tasks_db[task.id] = task
                del tasks[index]

            if index >= len(tasks):
                index = 0

        if original_id:
            if original_id > 0:
                return original_id
            else:
                return map_new_ids[original_id]
        return None

    def put(self, task: Task):
        self._tasks[task.id] = task

    def get(self, task_id: int) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise ValueError("Requested task does not exist")

    def has(self, task_id: int) -> bool:
        return task_id in self._tasks

    @property
    def tasks(self) -> Dict[int, Task]:
        return self._tasks

    def ids(self) -> List[int]:
        return list(self._tasks.keys())


# database
tasks_db: Dict[int, Task] = dict()
session: dict = dict(user=None, wipdbs=dict())

# form
@dataclass
class TaskForm:
    title: str
    description: Optional[str]
    error: Optional[str] = field(default=None, init=False)

    def is_valid(self) -> bool:
        if not self.title:
            self.error = "Title is required"
            return False
        return True

    @classmethod
    def load_init_param(cls, param_value) -> Optional["TaskForm"]:
        return (
            cls(
                title=param_value.get("title", ""),
                description=param_value.get("description", None),
            )
            if param_value is not None
            else None
        )


# components
@config(
    Component.Config(
        # components=dict(
        #     view="tests.test_capp.ViewTask",
        #     edit="tests.test_capp.EditTask",
        #     add="tests.test_capp.AddTask",
        #     delete="tests.test_capp.DeleteTask",
        # ),
        inject_into_components=lambda self, component_config: TaskList.inject_into_components(
            self, component_config
        )
    )
)
class TaskList(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None),)

    @classmethod
    def inject_into_components(cls, self: Component, component_config: ComponentConfig):
        result = dict()
        if self.state.parent_task_id is not None:
            result["parent_task_id"] = self.state.parent_task_id
        if self.state.wip_id is not None:
            result["wip_id"] = self.state.wip_id
        return result

    def __init__(
        self,
        mode: str = "list",
        parent_task_id: Optional[int] = None,
        wip_id: Optional[int] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        self._wipdb = session["wipdbs"][wip_id] if wip_id else None
        if parent_task_id is not None and not (
            parent_task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(parent_task_id))
        ):
            raise NotFound()

        if mode != "list" and mode not in self._config.components.keys():
            raise BadRequest()

        self.goto_task_id: Optional[int] = None

        super().__init__()

    @property
    def tasks(self) -> Dict[int, Task]:
        """
        Returns list of tasks where parent_id == state.parent_task_id from 
        tasks_db and wip_db.
        Replacing tasks from tasks_db with task from wip_db if taks have same id
        "new" tasks in wip_db that does not exist in tasks_db must have negative id
        """
        try:
            return self._tasks
        except AttributeError:
            self._tasks: Dict[int, Task] = {
                tid: t
                for tid, t in tasks_db.items()
                if t.parent_id == self.state.parent_task_id
            }
            # replace tasks in db with task from wip
            if self._wipdb:
                for tid, t in self._wipdb.tasks.items():
                    if tid > 0 and tid not in self._tasks:
                        raise ValueError(
                            "Work in progress task that does not exist in db must have negative id"
                        )
                    if t.parent_id == self.state.parent_task_id:
                        self._tasks[tid] = t
            return self._tasks

    @listener(event="_display", source="*")
    def on_display_child(self, event: Event):
        self.state.mode = event.source_name
        self.goto_task_id = event.params.get("task_id", None)

    @listener(event="save", source=["edit", "add"])
    def on_tasks_changed(self, event: Event):
        self.state.mode = "view" if "view" in self._config.components else "edit"
        self.goto_task_id = event.params.get("task_id", None)

    @listener(event="cancel", source="*")
    def on_cancel_operation(self, event: Event):
        self.state.mode = "list"

    @listener(event="delete", source=["delete"])
    def on_delete_task(self, event: Event):
        self.state.mode = "list"

    # redisplay whenever it is executed regardles if the state is changed
    # becouse state changes in task_db or wipdb will not be reflected to the state
    @redisplay(when_executed=True)
    def display(self) -> "DisplayResponse":
        list_template = (
            """<div>"""
            """{% if component("add").is_accessible %}"""
            """<button type="button" jmb-on:click="{{component().jrl}}">Add</button>{% endif %}"""
            "<table>"
            "<tr><th>Task</th><th>Actions</th></tr>"
            "{% for t in tasks.values() %}<tr>"
            "<td>"
            """{% if component("view", task_id=t.id).is_accessible %}"""
            """<a href="{{component().url}}" jmb-on:click="{{component().jrl}}">{{t.title}}</a>"""
            """{% elif component("edit", task_id=t.id).is_accessible %}"""
            """<a href="{{component().url}}" jmb-on:click="{{component().jrl}}">{{t.title}}</a>"""
            # """<a href="{{component.url}}" jmb-on:click="$jmb.component('../view', {task_id:t.id}).display">{{t.title}}</a>"""
            """{% else %}{{t.title}}{% endif %}"""
            "</td>"
            "<td>"
            """{% if component("edit", task_id=t.id).is_accessible %}"""
            """<a href="{{component().url}}" jmb-on:click="{{component().jrl}}">edit</a>{% endif %}"""
            """{% if component("delete", task_id=t.id).is_accessible %}"""
            """<a href="{{component().url}}" jmb-on:click="{{component().jrl}}">delete</a>{% endif %}"""
            "</td>"
            "</tr>{% endfor %}"
            "</table>"
            "</div>"
        )
        if self.state.mode == "list":
            if self.state.parent_task_id is None:
                self.emit("set_page_title", title="Tasks")
            return self.render_template_string(list_template)
        elif self.state.mode == "view":
            if self.goto_task_id:
                return self.render_template_string(
                    "{{component('view', task_id=goto_task_id)}}"
                )
            else:
                return self.render_template_string("{{component('view')}}")
        elif self.state.mode == "edit":
            if self.goto_task_id:
                return self.render_template_string(
                    "{{component('edit', task_id=goto_task_id)}}"
                )
            else:
                return self.render_template_string("{{component('edit')}}")
            return self.render_template_string("{{component('edit')}}")
        elif self.state.mode == "add":
            return self.render_template_string("{{component('add')}}")
        elif self.state.mode == "delete":
            return self.render_template_string(
                "{{component('delete')}}" + list_template
            )
        raise JembeError("invalid mode {}".format(self.state.mode))
        # About strong cupling between compoentes by usint component("../view") which
        # requre that parent component have subcompoenet named view with excepted behavior:
        # This can be avioded by:
        #  1. defining list of components/actions either in init params or in _config that will be
        #     set by parent component
        #  2. setting list of events by parent via config or in init params that will be emited
        #  3. defining list of components/actions factories by parent config etc.
        # in eigher case task list must distinguish components/actions/events that are called/emited on
        # indipendent of current record (add), in context of one recorord (view, edit) or in context of
        # multiple records (delete all)

        # action(title, help_text, icon??, url, jrl,  **whatever)
        # component.action_factory(component_relative_name, title, help_text, icon, init_params, **whatever)


class ViewTask(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def __init__(
        self, task_id: int, wip_id: Optional[int] = None, user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        self._wipdb = session["wipdbs"][wip_id] if wip_id else None

        if not (
            self.state.task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(self.state.task_id))
        ):
            raise NotFound()

        super().__init__()

    @cached_property
    def task(self) -> Task:
        if self._wipdb and self._wipdb.has(self.state.task_id):
            return self._wipdb.get(self.state.task_id)
        else:
            return tasks_db[self.state.task_id]

    def display(self) -> "DisplayResponse":
        self.emit("set_page_title", title="View {}".format(self.task.title))
        return self.render_template_string(
            """<h1><a href="#" jmb-on:click="$jmb.component('..').display()">Back</a> {{task.title}}</h1>"""
            "<div>{{task.description}}</div>"
            "{% if component('subtasks', parent_task_id=task_id).is_accessible %}"
            "<h2>Sub tasks</h2>"
            "<div>{{component()}}</div>"
            "{% endif %}"
        )


class EditTask(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def __init__(
        self,
        task_id: int,
        form: Optional[TaskForm] = None,
        wip_id: Optional[int] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        self._wipdb = session["wipdbs"][wip_id] if wip_id is not None else None
        if not (
            self.state.task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(self.state.task_id))
        ):
            raise NotFound()
        self.__mounted = False

        super().__init__()

    @classmethod
    def load_init_param(
        cls, config: "ComponentConfig", param_name: str, param_value: Any
    ) -> Any:
        if param_name == "form":
            return TaskForm.load_init_param(param_value)
        return super().load_init_param(config, param_name, param_value)

    def mount(self):
        if self.__mounted:
            return

        if self.state.wip_id is None:
            # Initialise wipdb with wip_id
            self.state.wip_id = (
                max(session["wipdbs"].keys()) + 1 if session["wipdbs"] else 1
            )
            self._wipdb = WipDb()
            session["wipdbs"][self.state.wip_id] = self._wipdb

        if self.state.form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )

    @cached_property
    def task(self) -> Task:
        if self._wipdb.has(self.state.task_id):
            return self._wipdb.get(self.state.task_id)
        else:
            return tasks_db[self.state.task_id]

    @listener(event=["cancel", "save"], source=".")
    def on_self_save_or_cancel(self, event: Event):
        if not self.isinjected("wip_id"):
            del session["wipdbs"][self.state.wip_id]
            self.state.wip_id = None
        return False

    @action
    def save(self):
        self.mount()
        if self.state.form.is_valid():
            # create new task
            task = Task(
                self.state.task_id,
                self.state.form.title,
                self.state.form.description,
                self.task.parent_id,
            )
            # save in wip_db
            # becaouse we dont want jet to change task in task_db (self.task)
            # do not care if already exist or not
            self._wipdb.put(task)
            if self.isinjected("wip_id"):
                # wipdb is changed
                pass
            else:
                # saving from component who created wip_db
                # save all changes from wip_db
                self._wipdb.save()
            # emit save so that parent can decide what to display next
            self.emit("save", task_id=self.state.task_id)
            # dont redisplay this component after successfull save
            return False
        # form is not valid redisplay it with error

    def display(self) -> "DisplayResponse":
        self.mount()
        self.emit("set_page_title", title="Edit {}".format(self.task.title))
        return self.render_template_string(
            "<div>"
            "<h1>Edit {{task.title}}</h1>"
            """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
            """<label>Title:"""
            """<input type="text" value="{{form.title}}" """
            """jmb-on.change.deferred="$jmb.set('form.title', this.value)"></label>"""
            """<label>Description:"""
            """<input type="text" value="{{form.description}}" """
            """jmb-on.change.deferred="$jmb.set('form.description', this.value)"></label>"""
            """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
            """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
            "{% if component('subtasks', parent_task_id=task_id).is_accessible %}"
            "<h2>Subtasks</h2>"
            "<div>{{component()}}</div>"
            "{% endif %}"
            "</div>"
        )


class AddTask(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def __init__(
        self,
        parent_task_id: Optional[int] = None,
        task_id: Optional[int] = None,
        form: Optional[TaskForm] = None,
        wip_id: Optional[int] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        self._wipdb = session["wipdbs"][wip_id] if wip_id else None
        if parent_task_id is not None and not (
            parent_task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(parent_task_id))
        ):
            raise NotFound()

        self._mounted = False
        super().__init__()

    @classmethod
    def load_init_param(
        cls, config: "ComponentConfig", param_name: str, param_value: Any
    ) -> Any:
        if param_name == "form":
            return TaskForm.load_init_param(param_value)
        return super().load_init_param(config, param_name, param_value)

    def mount(self) -> None:
        if self._mounted:
            return
        self._mounted = True

        if self.state.wip_id is None:
            self.state.wip_id = (
                max(session["wipdbs"].keys()) + 1 if session["wipdbs"] else 1
            )
            self._wipdb = WipDb()
            session["wipdbs"][self.state.wip_id] = self._wipdb

        if self.state.task_id is None:
            self.state.task_id = min([0, *self._wipdb.ids()]) - 1
            new_task = Task(
                id=self.state.task_id, title="", parent_id=self.state.parent_task_id
            )
            self._wipdb.put(new_task)

        if self.state.form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )

    @cached_property
    def task(self) -> Task:
        if self._wipdb.has(self.state.task_id):
            return self._wipdb.get(self.state.task_id)
        else:
            return tasks_db[self.state.task_id]

    @listener(event=["cancel", "save"], source=".")
    def on_self_save_or_cancel(self, event: Event):
        if not self.isinjected("wip_id"):
            del session["wipdbs"][self.state.wip_id]
            self.state.wip_id = None
        return False

    @action
    def save(self):
        self.mount()
        if self.state.form.is_valid():
            task = Task(
                self.state.task_id,
                self.state.form.title,
                self.state.form.description,
                self.state.parent_task_id,
            )
            # save in wip_db
            # becaouse we dont want jet to change task in task_db (self.task)
            # do not care if already exist or not
            self._wipdb.put(task)
            if self.isinjected("wip_id"):
                # wipdb is changed
                pass
            else:
                # saving from component who created wip_db
                # save all changes from wip_db
                self.state.task_id = self._wipdb.save(self.state.task_id)
                # remove wipdb becouse we dont need it anymore
                # del session["wipdbs"][self.state.wip_id]
                # self.state.wip_id = None
                # # TODO change injected into of child components when state is changed
            # emit save so that parent can decide what to display next
            self.emit("save", task_id=self.state.task_id)
            # dont redisplay this component after successfull save
            return False
        # form is not valid redisplay it with error

    def display(self) -> "DisplayResponse":
        self.mount()
        self.emit("set_page_title", title="Add task")
        return self.render_template_string(
            "<div>"
            "<h1>New task</h1>"
            """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
            """<label>Title:"""
            """<input type="text" value="{{form.title}}" """
            """jmb-on.change.deferred="$jmb.set('form.title', this.value)"></label>"""
            """<label>Description:"""
            """<input type="text" value="{{form.description|default("",true)}}" """
            """jmb-on.change.deferred="$jmb.set('form.description', this.value)"></label>"""
            """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
            """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
            "{% if component('subtasks').is_accessible %}"
            "<h2>Subtasks</h2>"
            "<div>{{component()}}</div>"
            "{% endif %}"
            "</div>"
        )


class DeleteTask(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def __init__(
        self, task_id: int, wip_id: Optional[int] = None, user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        self._wipdb = session["wipdbs"][wip_id] if wip_id else None

        if not (
            self.state.task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(self.state.task_id))
        ):
            raise NotFound()

        super().__init__()

    @cached_property
    def task(self) -> Task:
        if self._wipdb and self._wipdb.has(self.state.task_id):
            return self._wipdb.get(self.state.task_id)
        else:
            return tasks_db[self.state.task_id]

    def delete(self):
        if (
            self.isinjected("wip_id")
            and self._wipdb
            and self._wipdb.has(self.state.task_id)
        ):
            # delete from wip_db
            self.state.wip_db[self.state.task_id] = None
            self.emit("delete")
        else:
            # direct delte from tasks_db
            del tasks_db[self.state.task_id]
            self.emit("delete")
        # dont redisplay parent (Tasks) should decide what to display after
        # successful delete
        return False

    def display(self) -> "DisplayResponse":
        self.emit("set_page_title", title="Delete {}".format(self.task.title))
        return self.render_template_string(
            "<h1>Delete {{task.title}}</h1>"
            """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
            """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
        )


@config(Component.Config(changes_url=False))
class PageTitle(Component):
    def __init__(self, title: str = ""):
        self._level: Optional[int] = None
        super().__init__()

    @listener(event="set_page_title")
    def on_set_page_title(self, event: Event):
        if self._level is None or (
            event.source and event.source._config.hiearchy_level > self._level
        ):
            self._level = event.source._config.hiearchy_level if event.source else 0
            self.state.title = event.title

    @action(deferred=True)
    def display(self):
        return self.render_template_string("<title>{{title}}</title>")


def inject_parent_and_wip_id(self: Component, component_config: ComponentConfig):
    return dict(parent_task_id=self.state.task_id, wip_id=self.state.wip_id)


@config(
    Component.Config(
        components=dict(
            page_title=PageTitle,
            tasks=(
                TaskList,
                TaskList.Config(
                    components=dict(
                        view=(
                            ViewTask,
                            ViewTask.Config(
                                components=dict(
                                    subtasks=(
                                        TaskList,
                                        TaskList.Config(components=dict(view=ViewTask)),
                                    )
                                ),
                                inject_into_components=inject_parent_and_wip_id,
                            ),
                        ),
                        edit=(
                            EditTask,
                            EditTask.Config(
                                components=dict(
                                    subtasks=(
                                        TaskList,
                                        TaskList.Config(
                                            components=dict(
                                                add=AddTask,
                                                edit=EditTask,
                                                delete=DeleteTask,
                                            )
                                        ),
                                    )
                                ),
                                inject_into_components=inject_parent_and_wip_id,
                            ),
                        ),
                        add=(
                            AddTask,
                            AddTask.Config(
                                components=dict(
                                    subtasks=(
                                        TaskList,
                                        TaskList.Config(
                                            components=dict(
                                                add=AddTask,
                                                edit=EditTask,
                                                delete=DeleteTask,
                                            ),
                                        ),
                                    )
                                ),
                                inject_into_components=inject_parent_and_wip_id,
                            ),
                        ),
                        delete=DeleteTask,
                    ),
                ),
            ),
        )
    ),
)
class TasksPage(Component):
    def __init__(self) -> None:
        super().__init__()
        self.unauthorized = False

    @listener(event="_exception")
    def on_exception(self, event):
        if isinstance(event.exception, Unauthorized):
            self.unauthorized = True
            event.handled = True
            return True  # Force redisplay

    def display(self) -> "DisplayResponse":
        return self.render_template_string(
            "<html><head>{{component('page_title')}}</head>"
            "<body>"
            "{% if unauthorized %}User is not authorized"
            "{% else %}{{component('tasks')}}"
            "{% endif %}"
            "</body></html>"
        )


def test_unauthorisied(jmb, client):
    global session, tasks_db
    jmb.add_page("tasks", TasksPage)

    # display unauthorized
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/tasks"}\'>"""
        """<head><title jmb-name="/tasks/page_title" jmb-data=\'{"actions":{},"changesUrl":false,"state":{"title":""},"url":"/tasks/page_title"}\'></title></head>"""
        """<body>"""
        "User is not authorized"
        """</body></html>"""
    ).encode("utf-8")


def test_empty_list(jmb, client):
    global session, tasks_db
    jmb.add_page("tasks", TasksPage)
    # login
    session["user"] = User("admin")

    # display empty list
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/tasks"}\'>"""
        """<head><title jmb-name="/tasks/page_title" jmb-data=\'{"actions":{},"changesUrl":false,"state":{"title":"Tasks"},"url":"/tasks/page_title"}\'>Tasks</title></head>"""
        """<body>"""
        """<div jmb-name="/tasks/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"mode":"list","parent_task_id":null,"wip_id":null},"url":"/tasks/tasks"}\'>"""
        """<button type="button" jmb-on:click="$jmb.component('add').display()">Add</button>"""
        "<table>"
        "<tr><th>Task</th><th>Actions</th></tr>"
        "</table>"
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")


def test_add_task_x(jmb, client):
    global session, tasks_db
    jmb.add_page("tasks", TasksPage)
    # login
    session["user"] = User("admin")
    # display add page
    r = client.post(
        "/tasks/tasks",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(execName="/tasks/page_title", state=dict(title="Tasks"),),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="list", parent_task_id=None, wip_id=None),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/add",
                        initParams=dict(),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/add",
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
    assert len(json_response) == 4
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="Add task")
    assert json_response[0]["dom"] == ("""<title>Add task</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks"
    assert json_response[1]["state"] == dict(
        mode="add", parent_task_id=None, wip_id=None
    )
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/add"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/add"
    assert json_response[2]["state"] == dict(
        form=dict(title="", description=None, error=None),
        parent_task_id=None,
        task_id=-1,
        wip_id=1,
    )
    assert json_response[2]["dom"] == (
        "<div>"
        "<h1>New task</h1>"
        """<label>Title:"""
        """<input type="text" value="" """
        """jmb-on.change.deferred="$jmb.set('form.title', this.value)"></label>"""
        """<label>Description:"""
        """<input type="text" value="" """
        """jmb-on.change.deferred="$jmb.set('form.description', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
        "<h2>Subtasks</h2>"
        """<div><template jmb-placeholder="/tasks/tasks/add/subtasks"></template></div>"""
        "</div>"
    )
    assert json_response[3]["execName"] == "/tasks/tasks/add/subtasks"
    assert json_response[3]["state"] == dict(mode="list")
    assert json_response[3]["dom"] == (
        "<div>"
        """<button type="button" jmb-on:click="$jmb.component('add').display()">Add</button>"""
        "<table>"
        "<tr><th>Task</th><th>Actions</th></tr>"
        "</table>"
        "</div>"
    )
    # add new task
    r = client.post(
        "/tasks/tasks/add",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(execName="/tasks/page_title", state=dict(title="Add task")),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="add", parent_task_id=None, wip_id=None),
                    ),
                    dict(
                        execName="/tasks/tasks/add",
                        state=dict(
                            form=dict(title="", description=None, error=None),
                            parent_task_id=None,
                            wip_id=1,
                            task_id=-1,
                        ),
                    ),
                    dict(
                        execName="/tasks/tasks/add/subtasks", state=dict(mode="list"),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/add",
                        initParams=dict(
                            form=dict(
                                title="Task 1", description="First task", error=None
                            ),
                            parent_task_id=None,
                            wip_id=1,
                            task_id=-1,
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/add",
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
    assert len(json_response) == 4
    assert len(session["wipdbs"]) == 0
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="View Task 1")
    assert json_response[0]["dom"] == ("""<title>View Task 1</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks"
    assert json_response[1]["state"] == dict(
        mode="view", wip_id=None, parent_task_id=None
    )
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/view"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/view"
    assert json_response[2]["state"] == dict(task_id=1, wip_id=None)
    assert json_response[2]["dom"] == (
        """<h1><a href="#" jmb-on:click="$jmb.component('..').display()">Back</a> Task 1</h1>"""
        """<div>First task</div>"""
        "<h2>Sub tasks</h2>"
        """<div><template jmb-placeholder="/tasks/tasks/view/subtasks"></template></div>"""
    )
    assert json_response[3]["execName"] == "/tasks/tasks/view/subtasks"
    assert json_response[3]["state"] == dict(mode="list")
    assert json_response[3]["dom"] == (
        "<div><table><tr><th>Task</th><th>Actions</th></tr></table></div>"
    )
    assert session == dict(user=User(username="admin"), wipdbs={})
    assert tasks_db == {1: Task(1, "Task 1", "First task")}
    # TODO check state of every component


def test_add_second_task_x(client, jmb):
    """Calling save without properly created seted wipdb_id and task_id"""
    global session, tasks_db
    jmb.add_page("tasks", TasksPage)
    session = dict(user=User("admin"), wipdbs=dict())
    tasks_db = {1: Task(1, "Task 1", "First task")}
    r = client.post(
        "/tasks/tasks/add",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(execName="/tasks/page_title", state=dict(title="Add task")),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="add", parent_task_id=None, wip_id=None),
                    ),
                    dict(
                        execName="/tasks/tasks/add",
                        state=dict(
                            form=dict(title="", description=None, error=None),
                            parent_task_id=None,
                            wip_id=None,
                            task_id=None,
                        ),
                    ),
                    dict(
                        execName="/tasks/tasks/add/subtasks", state=dict(mode="list"),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/add",
                        initParams=dict(
                            form=dict(
                                title="Task 2", description="Second task", error=None
                            ),
                            parent_task_id=None,
                            wip_id=None,
                            task_id=None,
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/add",
                        actionName="save",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert session == dict(user=User(username="admin"), wipdbs={})
    assert tasks_db == {
        1: Task(1, "Task 1", "First task"),
        2: Task(2, "Task 2", "Second task"),
    }
    assert r.status_code == 200
    json_response = json.loads(r.data)
    assert len(json_response) == 4
    assert len(session["wipdbs"]) == 0
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="View Task 2")
    assert json_response[0]["dom"] == ("""<title>View Task 2</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks"
    assert json_response[1]["state"] == dict(
        mode="view", wip_id=None, parent_task_id=None
    )
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/view"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/view"
    assert json_response[2]["state"] == dict(task_id=2, wip_id=None)
    assert json_response[2]["dom"] == (
        """<h1><a href="#" jmb-on:click="$jmb.component('..').display()">Back</a> Task 2</h1>"""
        """<div>Second task</div>"""
        "<h2>Sub tasks</h2>"
        """<div><template jmb-placeholder="/tasks/tasks/view/subtasks"></template></div>"""
    )
    assert json_response[3]["execName"] == "/tasks/tasks/view/subtasks"
    assert json_response[3]["state"] == dict(mode="list")
    assert json_response[3]["dom"] == (
        "<div><table><tr><th>Task</th><th>Actions</th></tr></table></div>"
    )


def test_refresh_task_list_x(jmb, client):
    jmb.add_page("tasks", TasksPage)

    global session, tasks_db
    session = dict(user=User(username="admin"), wipdbs={})
    tasks_db = {
        1: Task(1, "Task 1", "First task"),
        2: Task(2, "Task 2", "Second task"),
    }
    # refresh tasks list
    r = client.post(
        "/tasks/tasks",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(execName="/tasks/page_title", state=dict(title="Tasks"),),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="list", parent_task_id=None, wip_id=None),
                    ),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks",
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
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/tasks/tasks"
    assert json_response[0]["state"] == dict(
        mode="list", parent_task_id=None, wip_id=None
    )
    assert json_response[0]["dom"] == (
        "<div>"
        """<button type="button" jmb-on:click="$jmb.component('add').display()">Add</button>"""
        "<table>"
        "<tr><th>Task</th><th>Actions</th></tr>"
        "<tr>"
        "<td>"
        """<a href="/tasks/tasks/view/1" jmb-on:click="$jmb.component('view',{task_id:1}).display()">Task 1</a>"""
        "</td>"
        "<td>"
        """<a href="/tasks/tasks/edit/1" jmb-on:click="$jmb.component('edit',{task_id:1}).display()">edit</a>"""
        """<a href="/tasks/tasks/delete/1" jmb-on:click="$jmb.component('delete',{task_id:1}).display()">delete</a>"""
        "</td>"
        "</tr>"
        "<tr>"
        "<td>"
        """<a href="/tasks/tasks/view/2" jmb-on:click="$jmb.component('view',{task_id:2}).display()">Task 2</a>"""
        "</td>"
        "<td>"
        """<a href="/tasks/tasks/edit/2" jmb-on:click="$jmb.component('edit',{task_id:2}).display()">edit</a>"""
        """<a href="/tasks/tasks/delete/2" jmb-on:click="$jmb.component('delete',{task_id:2}).display()">delete</a>"""
        "</td>"
        "</tr>"
        "</table>"
        "</div>"
    )


def test_edit_first_task_x(jmb, client):
    jmb.add_page("tasks", TasksPage)

    global session, tasks_db
    session = dict(user=User(username="admin"), wipdbs={})
    tasks_db = {
        1: Task(1, "Task 1", "First task"),
        2: Task(2, "Task 2", "Second task"),
    }
    # display edit first task
    r = client.post(
        "/tasks/tasks",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(execName="/tasks/page_title", state=dict(title="Tasks"),),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="list", parent_task_id=None, wip_id=None),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/edit",
                        initParams=dict(task_id=1,),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/edit",
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
    assert len(json_response) == 4
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="Edit Task 1")
    assert json_response[0]["dom"] == ("""<title>Edit Task 1</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks"
    assert json_response[1]["state"] == dict(
        mode="edit", parent_task_id=None, wip_id=None
    )
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/edit"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/edit"
    assert json_response[2]["state"] == dict(
        form=dict(title="Task 1", description="First task", error=None),
        task_id=1,
        wip_id=1,
    )
    assert json_response[2]["dom"] == (
        "<div>"
        "<h1>Edit Task 1</h1>"
        """<label>Title:"""
        """<input type="text" value="Task 1" """
        """jmb-on.change.deferred="$jmb.set('form.title', this.value)"></label>"""
        """<label>Description:"""
        """<input type="text" value="First task" """
        """jmb-on.change.deferred="$jmb.set('form.description', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
        "<h2>Subtasks</h2>"
        """<div><template jmb-placeholder="/tasks/tasks/edit/subtasks"></template></div>"""
        "</div>"
    )
    assert json_response[3]["execName"] == "/tasks/tasks/edit/subtasks"
    assert json_response[3]["state"] == dict(mode="list")
    assert json_response[3]["dom"] == (
        "<div>"
        """<button type="button" jmb-on:click="$jmb.component('add').display()">Add</button>"""
        "<table>"
        "<tr><th>Task</th><th>Actions</th></tr>"
        "</table>"
        "</div>"
    )

    assert len(session["wipdbs"]) == 1
    assert tasks_db == {
        1: Task(1, "Task 1", "First task"),
        2: Task(2, "Task 2", "Second task"),
    }
    # do edit second task
    r = client.post(
        "/tasks/tasks",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(
                        execName="/tasks/page_title", state=dict(title="Edit Task 1"),
                    ),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="edit", parent_task_id=None, wip_id=None),
                    ),
                    dict(
                        execName="/tasks/tasks/edit",
                        state=dict(
                            form=dict(
                                title="Task 1", description="First task", error=None
                            ),
                            task_id=1,
                            wip_id=1,
                        ),
                    ),
                    dict(
                        execName="/tasks/tasks/edit/subtasks", state=dict(mode="list"),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/edit",
                        initParams=dict(
                            form=dict(
                                title="Extended task 1",
                                description="Extended first task",
                                error=None,
                            ),
                            task_id=1,
                            wip_id=1,
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/edit",
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
    assert len(json_response) == 4
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="View Extended task 1")
    assert json_response[0]["dom"] == ("""<title>View Extended task 1</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks"
    assert json_response[1]["state"] == dict(
        mode="view", parent_task_id=None, wip_id=None
    )
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/view"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/view"
    assert json_response[2]["state"] == dict(task_id=1, wip_id=None)
    assert json_response[2]["dom"] == (
        """<h1><a href="#" jmb-on:click="$jmb.component('..').display()">Back</a> Extended task 1</h1>"""
        """<div>Extended first task</div>"""
        "<h2>Sub tasks</h2>"
        """<div><template jmb-placeholder="/tasks/tasks/view/subtasks"></template></div>"""
    )
    assert json_response[3]["execName"] == "/tasks/tasks/view/subtasks"
    assert json_response[3]["state"] == dict(mode="list")
    assert json_response[3]["dom"] == (
        "<div><table><tr><th>Task</th><th>Actions</th></tr></table></div>"
    )

    assert session == dict(user=User(username="admin"), wipdbs={})
    assert tasks_db == {
        1: Task(1, "Extended task 1", "Extended first task"),
        2: Task(2, "Task 2", "Second task"),
    }


def test_add_subtask_to_second_task_x(jmb, client):
    jmb.add_page("tasks", TasksPage)

    global session, tasks_db
    session = dict(user=User(username="admin"), wipdbs={1: WipDb()})
    tasks_db = {
        1: Task(1, "Extended task 1", "Extended first task"),
        2: Task(2, "Task 2", "Second task"),
    }
    # display add
    r = client.post(
        "/tasks/tasks/edit/1/subtasks",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(
                        execName="/tasks/page_title", state=dict(title="Edit Task 2"),
                    ),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="edit", parent_task_id=None, wip_id=None),
                    ),
                    dict(
                        execName="/tasks/tasks/edit",
                        state=dict(
                            form=dict(
                                title="Task 2", description="Second task", error=None
                            ),
                            task_id=2,
                            wip_id=1,
                        ),
                    ),
                    dict(
                        execName="/tasks/tasks/edit/subtasks", state=dict(mode="list"),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/edit/subtasks/add",
                        initParams=dict(),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/edit/subtasks/add",
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
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="Add task")
    assert json_response[0]["dom"] == ("""<title>Add task</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks/edit/subtasks"
    assert json_response[1]["state"] == dict(mode="add")
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/edit/subtasks/add"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/edit/subtasks/add"
    assert json_response[2]["state"] == dict(
        form=dict(title="", description=None, error=None), task_id=-1
    )
    assert json_response[2]["dom"] == (
        "<div>"
        "<h1>New task</h1>"
        """<label>Title:"""
        """<input type="text" value="" """
        """jmb-on.change.deferred="$jmb.set('form.title', this.value)"></label>"""
        """<label>Description:"""
        """<input type="text" value="" """
        """jmb-on.change.deferred="$jmb.set('form.description', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
        "</div>"
    )
    # add subtask
    r = client.post(
        "/tasks/tasks/edit/2/subtasks/add",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(execName="/tasks/page_title", state=dict(title="Add task"),),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="edit", parent_task_id=None, wip_id=None),
                    ),
                    dict(
                        execName="/tasks/tasks/edit",
                        state=dict(
                            form=dict(
                                title="Task 2", description="Second task", error=None
                            ),
                            task_id=2,
                            wip_id=1,
                        ),
                    ),
                    dict(
                        execName="/tasks/tasks/edit/subtasks", state=dict(mode="add"),
                    ),
                    dict(
                        execName="/tasks/tasks/edit/subtasks/add",
                        state=dict(
                            form=dict(title="", description=None, error=None),
                            task_id=-1,
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/tasks/tasks/edit/subtasks/add",
                        initParams=dict(
                            form=dict(
                                title="Subtask 2.1",
                                description="First subtask of second task",
                                error=None,
                            ),
                            task_id=-1,
                        ),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/edit/subtasks/add",
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
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="Edit Subtask 2.1")
    assert json_response[0]["dom"] == ("""<title>Edit Subtask 2.1</title>""")
    assert json_response[1]["execName"] == "/tasks/tasks/edit/subtasks"
    assert json_response[1]["state"] == dict(mode="edit")
    assert json_response[1]["dom"] == (
        """<template jmb-placeholder="/tasks/tasks/edit/subtasks/edit"></template>"""
    )
    assert json_response[2]["execName"] == "/tasks/tasks/edit/subtasks/edit"
    assert json_response[2]["state"] == dict(
        form=dict(
            title="Subtask 2.1", description="First subtask of second task", error=None
        ),
        task_id=-1,
    )
    assert json_response[2]["dom"] == (
        "<div>"
        "<h1>Edit Subtask 2.1</h1>"
        """<label>Title:"""
        """<input type="text" value="Subtask 2.1" """
        """jmb-on.change.deferred="$jmb.set('form.title', this.value)"></label>"""
        """<label>Description:"""
        """<input type="text" value="First subtask of second task" """
        """jmb-on.change.deferred="$jmb.set('form.description', this.value)"></label>"""
        """<button type="button" jmb-on:click="$jmb.call('save')">Save</button>"""
        """<button type="button" jmb-on:click="$jmb.emit('cancel')">Cancel</button>"""
        "</div>"
    )
    # Save second task so that newlly created subtask is saved
    r = client.post(
        "/tasks/tasks/edit/2",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/tasks", state=dict()),
                    dict(
                        execName="/tasks/page_title",
                        state=dict(title="Edit Subtask 2.1"),
                    ),
                    dict(
                        execName="/tasks/tasks",
                        state=dict(mode="edit", parent_task_id=None, wip_id=None),
                    ),
                    dict(
                        execName="/tasks/tasks/edit",
                        state=dict(
                            form=dict(
                                title="Task 2", description="Second task", error=None
                            ),
                            task_id=2,
                            wip_id=1,
                        ),
                    ),
                    dict(
                        execName="/tasks/tasks/edit/subtasks", state=dict(mode="edit"),
                    ),
                    dict(
                        execName="/tasks/tasks/edit/subtasks/edit",
                        state=dict(
                            form=dict(
                                title="Subtask 2.1",
                                description="First subtask of second task",
                                error=None,
                            ),
                            task_id=-1,
                        ),
                    ),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/tasks/tasks/edit",
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
    assert len(session["wipdbs"]) == 0
    assert tasks_db == {
        1: Task(1, "Extended task 1", "Extended first task"),
        2: Task(2, "Task 2", "Second task"),
        3: Task(3, "Subtask 2.1", "First subtask of second task", parent_id=2),
    }
    json_response = json.loads(r.data)
    assert json_response[0]["execName"] == "/tasks/page_title"
    assert json_response[0]["state"] == dict(title="View Task 2")
    assert json_response[1]["execName"] == "/tasks/tasks"
    assert json_response[1]["state"] == dict(
        mode="view", parent_task_id=None, wip_id=None
    )
    assert json_response[2]["execName"] == "/tasks/tasks/view"
    assert json_response[2]["state"] == dict(task_id=2, wip_id=None)
    assert json_response[3]["execName"] == "/tasks/tasks/view/subtasks"
    assert json_response[3]["state"] == dict(mode="list")


# TODO edit second task and add subtasks (x-jembe)
# TODO add subtask with two level subtasks (x-jembe)
# TODO edit task and add, edit and delete subtasks in bulk (x-jembe)
# TODO delete task
