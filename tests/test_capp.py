from jembe import component
from typing import Any, Dict, List, TYPE_CHECKING, Dict, Optional, Union
from functools import cached_property
from dataclasses import dataclass, field
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
    from flask import Response


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
                    task.id = max(tid for tid in tasks_db.keys())
                    map_new_ids[old_id] = task.id

                if task.parent_id and task.parent_id < 0:
                    task.parent_id = map_new_ids[task.parent_id]

                tasks_db[task.id] = task
                del tasks[index]

                index += 1

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
session: dict = dict(user=None, wipdbs=Dict[int, WipDb])


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


# components
@config(
    Component.Config(
        # components=dict(
        #     list="tests.test_capp.TaskList",
        #     view="tests.test_capp.ViewTask",
        #     edit="tests.test_capp.EditTask",
        #     add="tests.test_capp.AddTask",
        #     delete="tests.test_capp.DeleteTask",
        # ),
        inject_into_components=lambda self, component_config: Tasks.inject_into_components(self, component_config)
    )
)
class Tasks(Component):
    """
    Displayes task list with view, edit add and delete operation.

    It can have list, view, edit, add and delete components.
    list component is required

    it passes (injects into its components) parent_task_id and wip_id if
    thay are not None.
    """

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

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

        if mode not in self._config.components.keys():
            raise BadRequest()

        self.goto_task_id: Optional[int] = None

        super().__init__()

    @listener(event="_display", source="./*")
    def on_display_child(self, event: Event):
        self.state.mode = self, event.source_name

    @listener(event="save", source=["./edit", "./add"])
    def on_tasks_changed(self, event: Event):
        self.state.mode = "view" if "view" in self._config.components else "edit"
        self.goto_task_id = event.params["task_id"]

    @listener(event="cancel", source="./*")
    def on_cancel_operation(self, event: Event):
        self.state.mode = "list"

    @listener(event="delete", source=["./delete"])
    def on_delete_task(self, event: Event):
        self.state.mode = "list"

    def display(self) -> Union[str, "Response"]:
        if self.state.mode == "list":
            return self.render_template_string("{{component('list')}}")
        elif self.state.mode == "view":
            if self.goto_task_id:
                return self.render_template_string(
                    "{{component('view', task_id=goto_task_id)}}"
                )
            else:
                return self.render_template_string("{{component('view')}}")
        elif self.state.mode == "edit":
            return self.render_template_string("{{component('edit')}}")
        elif self.state.mode == "add":
            return self.render_template_string("{{component('add')}}")
        elif self.state.mode == "delete":
            return self.render_template_string(
                "{{component('delete')}}{{component('list')}}"
            )
        raise JembeError("invalid mode {}".format(self.state.mode))


class TaskList(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None),)

    def __init__(
        self,
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
                for tid, t in self._wipdb.tasks:
                    if tid > 0 and tid not in self._tasks:
                        raise ValueError(
                            "Work in progress task that does not exist in db must have negative id"
                        )
                    self._tasks[tid] = t
            return self._tasks

    # redisplay whenever it is executed regardles if the state is changed
    # becouse state changes in task_db or wipdb will not be reflected to the state
    @redisplay(when_executed=True)
    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            """{% if component("../add").is_accessible() %}"""
            """<button type="button" onclick="{{component.jrl}}">Add</button>{% endif %}"""
            "<table>"
            "<tr><th>Task</th><th>Actions</th></tr>"
            "{% for t in tasks %}<tr>"
            "<td>"
            """{% if component("../view", task_id=t.id).is_accessible() %}"""
            """<a href="{{component.url}}" onclick="{{component.jrl}}">{{t.title}}</a>"""
            """{% elif component("../edit", task_id=t.id).is_accessible() %}"""
            """<a href="{{component.url}}" onclick="{{component.jrl}}">{{t.title}}</a>"""
            # """<a href="{{component.url}}" onclick="$jmb.component('../view', task_id=t.id)">{{t.title}}</a>"""
            """{% else %}{{t.title}}{% endif %}"""
            "</td>"
            "<td>"
            """{% if not component("../view", task_id=t.id).is_accessible() and  component("../edit", task_id=t.id).is_accessible() %}"""
            """<a href="{{component.url}}" onclick="{{component.jrl}}">edit</a>{% endif %}"""
            """{% if component("../delete", task_id=t.id).is_accessible() %}"""
            """<a href="{{component.url}}" onclick="{{component.jrl}}">delete</a>{% endif %}"""
            "</td>"
            "</tr>{% endfor %}"
            "</table>"
        )
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

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    @cached_property
    def task(self) -> Task:
        if self._wipdb and self._wipdb.has(self.state.task_id):
            return self._wipdb.get(self.state.task_id)
        else:
            return tasks_db[self.state.task_id]

    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            """<h1><a href="#" onclick="$jmb.component("..")">Back</a> {{task.title}}</h1>"""
            "<div>{{task.description}}</div>"
            "{% if component('subtasks', parent_task_id=task_id).is_accessible() %}"
            "<h2>Sub tasks</h2>"
            "<div>{{component}}</div>"
            "{% endif %}"
        )


class EditTask(Component):
    def __init__(
        self,
        task_id: int,
        form: Optional[TaskForm] = None,
        wip_id: Optional[int] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if self.state.wip_id is None:
            # Initialise wipdb with wip_id
            self.state.wip_id = max(session["wipdbs"].keys()) + 1
            session["wipdbs"][self.state.wip_id] = WipDb()
        self._wipdb = session["wipdbs"][wip_id]

        if not (
            self.state.task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(self.state.task_id))
        ):
            raise NotFound()

        if form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )

        super().__init__()

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    @cached_property
    def task(self) -> Task:
        if self._wipdb.has(self.state.task_id):
            return self._wipdb.get(self.state.task_id)
        else:
            return tasks_db[self.state.task_id]

    @listener(event=["cancel", "save"], source=".")
    def on_self_cancel(self, event: Event):
        if not self.isinjected("wip_id"):
            # delete wipdb
            del session["wipdbs"][self.state.wip_id]
            self.state.wip_id = None

    @action
    def save(self):
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
            self.state.wip_db.put(task)
            if self.isinjected("wip_id"):
                # wipdb is changed
                pass
            else:
                # saving from component who created wip_db
                # save all changes from wip_db
                self._wip_db.save()
            # emit save so that parent can decide what to display next
            self.emit("save", task_id=self.state.task_id)
            # dont redisplay this component after successfull save
            return False
        # form is not valid redisplay it with error

    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            "<h1>Edit {{task.title}}</h1>"
            """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
            """<label>Title:"""
            """<input type="text" value="{{form.title}}" """
            """onchange="$jmb.set('form.title', this.value).deffer()"></label>"""
            """<label>Description:"""
            """<input type="text" value="{{form.description}}" """
            """onchange="$jmb.set('form.description', this.value).deffer()"></label>"""
            """<button type="button" onclick="$jmb.call('save')">Save</button>"""
            """<button type="button" onclick="$jmb.emit('cancel')">Cancel</button>"""
            "{% if component('subtasks', parent_task_id=task_id).is_accessible() %}"
            "<h2>Sub tasks</h2>"
            "<div>{{component}}</div>"
            "{% endif %}"
        )


class AddTask(Component):
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

        if self.state.wip_id is None:
            self.state.wip_id = max(session["wipdbs"].keys()) + 1
            session["wipdbs"][self.state.wip_id] = WipDb()
        self._wipdb = session["wipdbs"][self.state.wip_id]

        if parent_task_id is not None and not (
            parent_task_id in tasks_db
            or (self._wipdb is not None and self._wipdb.has(parent_task_id))
        ):
            raise NotFound()

        if self.state.task_id is None:
            self.state.task_id = min(0, min(self.state.wip_db.keys())) - 1
            new_task = Task(
                id=self.state.task_id, title="", parent_id=self.state.parent_task_id
            )
            self._wipdb.add(new_task)

        if form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )
        super().__init__()

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

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

    @action
    def save(self):
        if self.state.form.is_valid():
            task = Task(
                self.state.task_id,
                self.state.form.title,
                self.state.form.description,
                self.state.parent_task_id,
            )
            self.state.wip_db.put(task)
            # save in wip_db
            # becaouse we dont want jet to change task in task_db (self.task)
            # do not care if already exist or not
            self.state.wip_db.put(task)
            if self.isinjected("wip_id"):
                # wipdb is changed
                pass
            else:
                # saving from component who created wip_db
                # save all changes from wip_db
                self.state.task_id = self._wip_db.save(self.state.task_id)
            # emit save so that parent can decide what to display next
            self.emit("save", task_id=self.state.task_id)
            # dont redisplay this component after successfull save
            return False
        # form is not valid redisplay it with error

    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            "<h1>New task</h1>"
            """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
            """<label>Title:"""
            """<input type="text" value="{{form.title}}" """
            """onchange="$jmb.set('form.title', this.value).deffer()"></label>"""
            """<label>Description:"""
            """<input type="text" value="{{form.description}}" """
            """onchange="$jmb.set('form.description', this.value).deffer()"></label>"""
            """<button type="button" onclick="$jmb.call('save')">Save</button>"""
            """<button type="button" onclick="$jmb.emit('cancel')">Cancel</button>"""
            "{% if component('subtasks', parent_task_id=task_id).is_accessible() %}"
            "<h2>Subtasks</h2>"
            "<div>{{component}}</div>"
            "{% endif %}"
        )


class DeleteTask(Component):
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

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

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

    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            "<h1>Delete {{task.title}}</h1>"
            """<button type="button" onclick="$jmb.call('save')">Save</button>"""
            """<button type="button" onclick="$jmb.emit('cancel')">Cancel</button>"""
        )


def test_capp(jmb, client):
    """build simple task apps for testing server side processing and jembe api"""

    def inject_parent_and_wip_id(self: Component, component_config: ComponentConfig):
        return dict(parent_task_id=self.state.task_id, wip_id=self.state.wip_id)

    @jmb.page(
        "tasks",
        Tasks.Config(
            components=dict(
                list=TaskList,
                view=(
                    ViewTask,
                    ViewTask.Config(
                        components=dict(
                            subtasks=(
                                Tasks,
                                Tasks.Config(
                                    components=dict(list=TaskList, view=ViewTask)
                                ),
                            )
                        ),
                        inject_into_components=inject_parent_and_wip_id,
                    ),
                ),
                edit=(
                    EditTask,
                    EditTask.Config(
                        components=dict(
                            sustasks=(
                                Tasks,
                                Tasks.Config(
                                    components=dict(
                                        list=TaskList,
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
                                Tasks,
                                Tasks.Config(
                                    components=dict(
                                        list=TaskList,
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
    )
    class TasksPage(Tasks):
        pass

    # TODO compile
    # TODO display empty list
    # TODO add task (x-jembe)
    # TODO add second task (x-jembe)
    # TODO edit first task (x-jembe)
    # TODO edit second task and add subtasks (x-jembe)
    # TODO add subtask with two level subtasks (x-jembe)
    # TODO edit task and add, edit and delete subtasks in bulk (x-jembe)
    # TODO delete task
