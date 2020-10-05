from jembe.component_config import ComponentConfig
from typing import Any, Dict, TYPE_CHECKING, List, Optional, Union
from jembe import Component, action, listener, config, NotFound, Unauthorized
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
            view="tests.test_capp.ViewTask",
            edit="tests.test_capp.EditTask",
            add="tests.test_capp.AddTask",
            delete="tests.test_capp.DeleteTask",
        )
    )
)
class TaskList(Component):
    def __init__(
        self,
        parent_task_id: Optional[int] = None,
        user: Optional[User] = None,
        _wip_tasks: Optional[Dict[int, Task]] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()
        self._wip_tasks = _wip_tasks if _wip_tasks is not None else dict()
        if parent_task_id is not None and (
            parent_task_id not in tasks_db or parent_task_id not in self._wip_tasks
        ):
            raise NotFound()
        super().__init__()

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    @property
    def tasks(self) -> List[Task]:
        """
        TODO
        Returns list of tasks hepre parent_id == state.parent_task_id from 
        tasks_db and _wip_tasks.
        Replacing tasks from tasks_db with task from _wip_tasks if taks have same id
        "new" tasks in _wip_tasks that does not exist in tasks_db must have negative id
        """
        try:
            return self._tasks
        except AttributeError:
            # TODO
            self._tasks: List[Task] = list()
            return self._tasks

    def display(self) -> Union[str, "Response"]:
        return self.render_template_string(
            "<ul>"
            "{% for t in tasks %}<li>"
            """<a href="{{component('view', task_id=t.id)}}" """
            """onclick="$jmb.component('view', task_id={{t.id}})">"""
            "{{t.title}}</a></li>{% endfor %}"
            "</ul>"
        )


@config(
    Component.Config(
        components=dict(
            view="tests.test_capp.ViewTask",
            edit="tests.test_capp.EditTask",
            add="tests.test_capp.AddTask",
            delete="tests.test_capp.DeleteTask",
        )
    )
)
class EditTaskList(Component):
    pass


@config(
    Component.Config(
        components=dict(
            view="tests.test_capp.ViewTask",
            edit="tests.test_capp.EditTask",
            add="tests.test_capp.AddTask",
            delete="tests.test_capp.DeleteTask",
        )
    )
)
class AddTaskList(Component):
    pass


class TaskComponentBase(Component):
    def __init__(
        self,
        task_id: int,
        user: Optional[User] = None,
        _wip_tasks: Optional[Dict[int, Task]] = None,
    ) -> None:
        if user is None:
            raise Unauthorized()

        self._wip_tasks = _wip_tasks if _wip_tasks is not None else dict()

        if task_id not in tasks_db or task_id not in self._wip_tasks:
            raise NotFound()

        super().__init__()

    def inject(self) -> Dict[str, Any]:
        return dict(user=session.get("user", None))

    @property
    def task(self) -> Task:
        try:
            return self._task
        except AttributeError:
            if self.state.task_id in self._wip_task:
                self._task: Task = self._wip_tasks[self.state.task_id]
            else:
                self._task = tasks_db[self.state.task_id]
            return self._task


@config(Component.Config(components=dict(subtasks=TaskList)))
class ViewTask(TaskComponentBase):
    def display(self) -> Union[str, Response]:
        return self.render_template_string(
            "<h1>{{task.title}}</h1>"
            "<div>{{task.description}}</div>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


@config(Component.Config(components=dict(subtasks=EditTaskList)))
class EditTask(TaskComponentBase):
    def __init__(
        self,
        task_id: int,
        form: Optional[TaskForm] = None,
        user: Optional[User] = None,
        _wip_tasks: Optional[Dict[int, Task]] = None,
    ) -> None:
        if form is None:
            self.state.form = TaskForm(
                title=self.task.title, description=self.task.description
            )
        super().__init__(task_id=task_id, user=user, _wip_tasks=_wip_tasks)

    @action
    def save(self):
        raise NotImplementedError()

    def display(self) -> Union[str, Response]:
        return self.render_template_string(
            "<h1>Edit {{task.title}}</h1>"
            # TODO add inputs
            "<div>{{task.title}}</div>"
            "<div>{{task.description}}</div>"
            "<div>{{component('subtasks', parent_task_id=task_id)}}</div>"
        )


@config(Component.Config(components=dict(subtasks=AddTaskList)))
class AddTask(Component):
    pass


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
