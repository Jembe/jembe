from jembe.processor import Event
from jembe import component
from jembe.exceptions import BadRequest, JembeError
from jembe.component_config import ComponentConfig
from typing import Any, Dict, List, TYPE_CHECKING, Dict, Optional, Union
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


class WipDb:
    # temporary storage of modified and new tasks (Work in Progress)
    def __init__(self, *tasks: Task) -> None:
        self._tasks: Dict[int, Task] = {t.id: t for t in tasks}

    def encode(self) -> Any:
        return self._tasks.values()

    @classmethod
    def decode(cls, encoded_value: List[dict]) -> Any:
        tasks = dict()
        for t in encoded_value:
            tasks[t["id"]] = Task(**t)
        return tasks

    def save(self):
        map_new_ids: Dict[int, int] = dict()
        tasks = self._tasks.values()

        index = 0
        while tasks:
            task = tasks[index]
            if task is None:
                del(tasks[index])
                del(tasks_db[index])
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

                if task.parent_id < 0:
                    task.parent_id = map_new_ids[task.parent_id]

                tasks_db[task.id] = task
                del tasks[index]

                index += 1

            if index >= len(tasks):
                index = 0

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
        wip_db: Optional[WipDb] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if parent_task_id is not None and (
            parent_task_id not in tasks_db
            or (wip_db is not None and not self.state.wip_db.has(parent_task_id))
        ):
            raise NotFound()

        if mode not in self._config.components.keys():
            raise BadRequest()

        super().__init__()

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        if param_name == "wip_db" and param_value is not None:
            return WipDb.decode(param_value)
        return super().decode_param(param_name, param_value)

    @listener(event="_display", source="./*")
    def on_display_child(self, event: Event):
        self.state.mode = event.source_name
    
    # TODO handle save(wip) delete(wip) etc from edit,add and delete compoennts

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
                "{{component('delete')}}{{component('list')}}"
            )
        raise JembeError("invalid mode {}".format(self.state.mode))


class TaskList(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None),)

    def __init__(
        self,
        parent_task_id: Optional[int] = None,
        wip_db: Optional[WipDb] = None,
        user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if parent_task_id is not None and (
            parent_task_id not in tasks_db
            or (wip_db is not None and not self.state.wip_db.has(parent_task_id))
        ):
            raise NotFound()

        super().__init__()

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        if param_name == "wip_db" and param_value is not None:
            return WipDb.decode(param_value)
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
            }
            # replace tasks in db with task from wip
            if self.state.wip_db:
                for tid, t in self.state.wip_db.tasks:
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


class TaskComponentBase(Component):
    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    def inject_into(self, component: Component) -> Dict[str, Any]:
        iinto = super().inject_into(component)
        if component._config.name == "subtasks" and "task_id" in self.state:
            iinto["parent_task_id"] = self.state.task_id
            if self.state.wip_db is not None:
                iinto["wip_db"] = self.state.wip_db
        return iinto

    def __init__(
        self, wip_db: Optional[WipDb] = None, user: Optional[User] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        if (
            "task_id" in self.state
            and self.state.task_id not in tasks_db
            or (wip_db is not None and not self.state.wip_db.has(self.state.task_id))
        ):
            raise NotFound()

        super().__init__()

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        if param_name == "wip_db" and param_value is not None:
            return WipDb.decode(param_value)
        return super().decode_param(param_name, param_value)

    @property
    def task(self) -> Task:
        if "task_id" not in self.state:
            raise ValueError("task_id state param does not exist")
        try:
            return self._task
        except AttributeError:
            if self.state.wip_db and self.state.wip_db.has(self.state.task_id):
                self._task: Task = self.state.wip_db.get(self.state.task_id)
            else:
                self._task = tasks_db[self.state.task_id]
            return self._task


@config(Component.Config(components=dict(subtasks=Tasks)))
class ViewTask(TaskComponentBase):
    def __init__(
        self, task_id: int, wip_db: Optional[WipDb] = None, user: Optional[User] = None,
    ) -> None:
        super().__init__(user=user, wip_db=wip_db)

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
        wip_db: Optional[WipDb] = None,
        user: Optional[User] = None,
    ) -> None:
        super().__init__(user=user, wip_db=wip_db)

        if form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )

        if self.state.wip_db is None:
            # Initialise wip_db that will be injectected
            # in subtasks component if needed
            self.state.wip_db = WipDb()

    @action
    def save(self):
        if self.state.form.is_valid():
            # save in wip_db
            # create new task becaouse we dont want jet
            # to change task in task_db (self.tasks)
            task = Task(
                self.state.task_id,
                self.state.form.title,
                self.state.form.description,
                self.task.parent_id,
            )
            # do not care if already exist or not
            self.state.wip_db.put(task)
            if isinjected(self.state.wip_db):
                # wipdb is changed, inform component who first initialised wipdb
                # to know to redisplay itself
                self.emit("save", wip=True)
            else:
                # saving from component who created wip_db
                # save all changes from wip_db
                self.state.wip_db.save()
                # emit save to parent to decide what to display next
                self.emit("save", wip=False)
            # dont redisplay parent (Tasks) should decide what to display after
            # successful save or
            return False
        # form is not valid redisplay it with error

    @listener(event="save", source="./**")
    def on_save(self, event: Event):
        if event.params["wip"] and not isinjected(self.state.wip_db):
            # redisplay so that client get new encoded wip_db
            raise NotImplementedError()
        # if this is not save in wip_db (this should not happend but..)
        # just ignore it becouse we have our on wip_db :) to maintain that
        # is not changed
        # if wip_db is injected into this Edit ... than this compoennt
        # displays record from wip_db that is not changed and it does not
        # send encoded wip_db to client so there is no need to redisplay it

        # TODO are we coping wip_db on inject_into if so that si bad (lots of duplication), or not
        # if we are just referencing wip_db than when wip_db is changed display on every compoent
        # including notinjected will force them to redisplay becaouse wip_db data has changed
        # TODO test all of this and modified implementation accordinly and
        # try to do without isinjected and any new API
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
            """<button type="button" onclick="$jmb.emit('cancel')">Cancel</button>"""
            "<h2>Subtasks</h2>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


@config(Component.Config(components=dict(subtasks=TaskList)))
class AddTask(TaskComponentBase):
    def __init__(
        self,
        parent_task_id: Optional[int] = None,
        form: Optional[TaskForm] = None,
        wip_db: Optional[WipDb] = None,
        user: Optional[User] = None,
    ) -> None:
        if parent_task_id is not None and (
            parent_task_id not in tasks_db
            or (
                self.state.wip_db is not None
                and not self.state.wip_db.has(parent_task_id)
            )
        ):
            raise NotFound()

        super().__init__(wip_db=wip_db, user=user)

        if form is None:
            self.state.form = TaskForm(title="", description=None)

    @action
    def add_task(self):
        task_id = min(0, min(self.state.wip_db.keys())) - 1
        new_task = Task(id=task_id, title="", parent_id=self.state.parent_task_id)
        self.state.wip_db[task_id] = new_task
        self.emit("update_wip")
        return False

    @action
    def save(self):
        if self.state.form.is_valid():
            task = Task(
                min(0, min(self.state.wip_db.ids())) - 1,
                self.state.form.title,
                self.state.form.description,
                self.state.parent_task_id,
            )
            self.state.wip_db.put(task)
            if isinjected(self.state.wip_db):
                # wipdb is changed, inform component who first initialised wipdb
                # to know to redisplay itself
                self.emit("save", wip=True)
            else:
                # saving from component who created wip_db
                # save all changes from wip_db
                self.state.wip_db.save()
                # emit save to parent to decide what to display next
                self.emit("save", wip=False)
            # dont redisplay parent (Tasks) should decide what to display after
            # successful save or
            return False

    def display(self) -> Union[str, Response]:
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
            "<h2>Subtasks</h2>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


class DeleteTask(TaskComponentBase):
    def __init__(
        self, task_id: int, wip_db: Optional[WipDb] = None, user: Optional[User] = None,
    ) -> None:
        super().__init__(user=user, wip_db=wip_db)

    def delete(self):
        if isinjected(self.state.wip_db) and self.state.wip_db is not None and self.state.wip_db.has(self.state.task_id):
            # delete from wip_db
            self.state.wip_db[self.state.task_id] = None
            self.emit("delete", wip=True)
        else:
            # direct delte from tasks_db
            del(tasks_db[self.state.task_id])
            self.emit("delete", wip=False)
        # dont redisplay parent (Tasks) should decide what to display after
        # successful delete
        return False

    def display(self) -> Union[str, Response]:
        return self.render_template_string(
            "<h1>Delete {{task.title}}</h1>"
            """<button type="button" onclick="$jmb.call('save')">Save</button>"""
            """<button type="button" onclick="$jmb.emit('cancel')">Cancel</button>"""
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
