from jembe.processor import Event
from jembe import component
from jembe.exceptions import BadRequest, JembeError
from jembe.component_config import ComponentConfig
from typing import Any, Dict, TYPE_CHECKING, Dict, Optional, Union
from jembe import (
    Component,
    action,
    listener,
    config,
    NotFound,
    Unauthorized,
    isinjected,
)
from dataclasses import dataclass, field

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


# database
tasks_db: Dict[int, Task] = dict()
session: dict = dict(user=None)

# helpers
def wip_db_decoder(wip_db: Optional[Dict[int, dict]]) -> Any:
    if wip_db is not None:
        tasks = dict()
        for wt_id, wt in wip_db.items():
            tasks[wt_id] = Task(**wt)
        return tasks


# form
@dataclass
class TaskForm:
    title: str
    description: Optional[str]
    error: Optional[str] = field(default=None, init=False)


# components
@config(
    Component.Config(
        components=dict(
            list="tests.test_capp.TaskList",
            view="tests.test_capp.ViewTask",
            edit="tests.test_capp.EditTask",
            add="tests.test_capp.AddTask",
            delete="tests.test_capp.DeleteTask",
        )
    )
)
class Tasks(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def inject_into(self, component: Component) -> Dict[str, Any]:
        iinto = super().inject_into(component)
        if self.state.parent_task_id is not None:
            iinto["parent_task_id"] = self.state.parent_task_id
        if self.state.wip_db is not None:
            iinto["wip_db"] = self.state.wip_db
        return iinto

    def __init__(
        self,
        mode: str = "list",
        parent_task_id: Optional[int] = None,
        wip_db: Optional[Dict[int, Task]] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if parent_task_id is not None and (
            parent_task_id not in tasks_db
            or (wip_db is not None and parent_task_id not in self.state.wip_db)
        ):
            raise NotFound()
        if mode not in self._config.components.keys():
            raise BadRequest()
        super().__init__()

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        if param_name == "wip_db":
            return wip_db_decoder(param_value)
        return super().decode_param(param_name, param_value)

    @listener(event="_display", source="./*")
    def on_display_child(self, event: Event):
        self.state.mode = event.source_name

    def display(self) -> Union[str, "Response"]:
        if self.state.mode == "list":
            return self.render_template_string("{{component('list')}}")
        elif self.state.mode == "view":
            return self.render_template_string("{{component('view')}}")
        elif self.state.mode == "edit":
            return self.render_template_string("{{component('edit')}}")
        elif self.state.mode == "add":
            return self.render_template_string("{{component('add')}}")
        elif self.state.mode == "delete":
            return self.render_template_string(
                "{{component('list')}}{{component('delete')}}"
            )
        raise JembeError("invalid mode {}".format(self.state.mode))


class TaskList(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None),)

    def __init__(
        self,
        parent_task_id: Optional[int] = None,
        wip_db: Optional[Dict[int, Task]] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if parent_task_id is not None and (
            parent_task_id not in tasks_db
            or (wip_db is not None and parent_task_id not in self.state.wip_db)
        ):
            raise NotFound()

        super().__init__()

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        if param_name == "wip_db":
            return wip_db_decoder(param_value)
        return super().decode_param(param_name, param_value)

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
                or self.state.parent_task_id is None
            }
            # replace tasks in db with task from wip
            if self.state.wip_db:
                for tid, t in self.state.wip_db:
                    if tid > 0 and tid not in self._tasks:
                        raise ValueError(
                            "Work in progress task that does not exist in db must have negative id"
                        )
                    self._tasks[tid] = t
            return self._tasks

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
            # """<a href="{{component.url}}" onclick="$jmb.component('../view', task_id=t.id)">{{t.title}}</a>"""
            """{% else %}{{t.title}}{% endif %}"""
            "</td>"
            "<td>"
            """{% if component("../edit", task_id=t.id).is_accessible() %}"""
            """<a href="{{component.url}}" onclick="{{component.jrl}}">edit</a>{% endif %}"""
            """{% if component("../edit", task_id=t.id).is_accessible() %}"""
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
        #  2. setting list of by parent via config or in init params that will be emited
        # in eigher case task list must distinguish components/actions/events that are called/emited on
        # indipendent of current record (add), in context of one recorord (view, edit) or in context of
        # multiple records (delete all)


class TaskComponentBase(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def inject_into(self, component: Component) -> Dict[str, Any]:
        iinto = super().inject_into(component)
        if component._config.name == "subtasks":
            iinto["parent_task_id"] = self.state.task_id
            if self.state.wip_db is not None:
                iinto["wip_db"] = self.state.wip_db
        return iinto

    def __init__(
        self,
        task_id: int,
        wip_db: Optional[Dict[int, Task]] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if task_id not in tasks_db or (
            wip_db is not None and task_id not in self.state.wip_db
        ):
            raise NotFound()

        super().__init__()

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        if param_name == "wip_db":
            return wip_db_decoder(param_value)
        return super().decode_param(param_name, param_value)

    @property
    def task(self) -> Task:
        try:
            return self._task
        except AttributeError:
            if self.state.wip_db and self.state.task_id in self.state.wip_db:
                self._task: Task = self.state.wip_db[self.state.task_id]
            else:
                self._task = tasks_db[self.state.task_id]
            return self._task


@config(Component.Config(components=dict(subtasks=Tasks)))
class ViewTask(TaskComponentBase):
    def display(self) -> Union[str, Response]:
        return self.render_template_string(
            """<h1><a href="#" onclick="$jmb.component("..")">Back</a> {{task.title}}</h1>"""
            "<div>{{task.description}}</div>"
            "<h2>Sub tasks</h2>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


@config(Component.Config(components=dict(subtasks=TaskList)))
class EditTask(TaskComponentBase):
    def __init__(
        self,
        task_id: int,
        form: Optional[TaskForm] = None,
        wip_db: Optional[Dict[int, Task]] = None,
        user: Optional[User] = None,
    ) -> None:
        super().__init__(task_id=task_id, user=user, wip_db=wip_db)

        if form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )

    @action
    def save(self):
        if isinjected(self.state.wip_db):
            # save in wip_db
            # TODO
            self.emit("saved", in_wip_db=True)
        else:
            # save in task_db and save all from wip_db
            # TODO
            self.emit("saved", in_wip_db=False)
        return False

    def display(self) -> Union[str, Response]:
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
            """<button type="button" onclick="$jmb.emit('cancel').to('..')">Cancel</button>"""
            "<h2>Subtasks</h2>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


# @config(Component.Config(components=dict(subtasks=TaskList)))
# class AddTask(TaskComponentBase):
#     def __init__(
#         self,
#         task_id: int = 0, # just to use taskcompoenntbase
#         parent_task_id: Optional[int] = None,
#         form: Optional[TaskForm] = None,
#         wip_db: Optional[Dict[int, Task]] = None,
#         user: Optional[User] = None,
#     ) -> None:
#         if parent_task_id is not None and (
#             parent_task_id not in tasks_db or parent_task_id not in self.state.wip_db
#         ):
#             raise NotFound()

#         if task_id == 0:
#             task_id = min(0, min(wip_db.keys())) - 1
#             new_task = Task(id=task_id, title="", parent_id=parent_task_id)
#             self.state.wib_db[task_id] = new_task
#             self.emit("update_wip_db")

#         super().__init__(task_id=task_id,wip_db=wip_db,user=user)

#         if form is None:
#             self.state.form = TaskForm(title="", description=None)

# @action
# def add_task(self):
#     task_id = min(0, min(self.state.wip_db.keys())) - 1
#     new_task = Task(id=task_id, title="", parent_id=self.state.parent_task_id)
#     self.state.wip_db[task_id] = new_task
#     self.emit("update_wip")
#     return False

#     @action
#     def save(self):
#         if isinjected(self.state.wip_db):
#             # save in wip_db
#             # TODO
#             self.emit("saved", in_wip_db=True)
#         else:
#             # save in task_db and save all from wip_db
#             # TODO
#             self.emit("saved", in_wip_db=False)
#         return False

#     def display(self) -> Union[str, Response]:
#         return self.render_template_string(
#             "<h1>New task</h1>"
#             """{% if form.error %}<div>{{form.error}}</div>{% endif %}"""
#             """<label>Title:"""
#             """<input type="text" value="{{form.title}}" """
#             """onchange="$jmb.set('form.title', this.value).deffer()"></label>"""
#             """<label>Description:"""
#             """<input type="text" value="{{form.description}}" """
#             """onchange="$jmb.set('form.description', this.value).deffer()"></label>"""
#             """<button type="button" onclick="$jmb.call('save')">Save</button>"""
#             """<button type="button" onclick="$jmb.emit('cancel').to('..')">Cancel</button>"""
#             "<h2>Subtasks</h2>"
#             "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
#         )


class DeleteTask(TaskComponentBase):
    def delete(self):
        raise NotImplementedError()

    def display(self) -> Union[str, Response]:
        return self.render_template_string(
            "<h1>Delete {{task.title}}</h1>"
            # TODO add confirm buttons
            "<div>{{task.title}}</div>"
            "<div>{{task.description}}</div>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


def test_capp(jmb, client):
    """build simple task apps for testing server side processing and jembe api"""

    @jmb.page(
        "tasks",
        Component.Config(
            components=dict(
                tasks=TaskList,
                view=ViewTask,
                edit=EditTask,
                add=AddTask,
                delete=DeleteTask,
            )
        ),
    )
    class TasksPage(Component):
        pass
