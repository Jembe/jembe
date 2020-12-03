"""
Creates Project/Tasks application component by component
with JUST MAKE IT WORK mindset. 
"""
from functools import cached_property
from jembe.utils import run_only_once
from typing import List, Optional, Set, TYPE_CHECKING, Tuple, Union, Any, Dict
from uuid import uuid1
from math import ceil
from dataclasses import dataclass
from jembe import Component, action, config, listener, BadRequest
from sqlalchemy.exc import SQLAlchemyError
from wtforms_sqlalchemy.orm import model_form
from dapp.models import Project, Task
from dapp.jmb import jmb
from dapp.db import db

if TYPE_CHECKING:
    from flask import Response
    from wtforms import Form
    from jembe import Event

ProjectForm = model_form(Project, db, exclude=("tasks",))
TaskForm = model_form(Task, db, exclude=("project",))


@config(Component.Config(changes_url=False, template="confirmation.html"))
# TODO confirm dialog should have click outside set to cancel it
class ConfirmationDialog(Component):
    def __init__(
        self,
        title: str = "",
        question: str = "",
        action: Optional[str] = None,
        params: Optional[dict] = None,
        choices: Optional[Dict[str, str]] = None,
    ) -> None:
        if action is None:
            raise ValueError("action:str parameter is required")
        if choices is None:
            self.state.choices = dict(
                ok=dict(title="Ok", css=""), cancel=dict(title="Cancel", css="")
            )
        super().__init__()

    @action
    def choose(self, choice: str):
        self.emit(
            choice, action=self.state.action, params=self.state.params,
        )
        return False


@dataclass
class Notification:
    message: str
    level: str = "info"


@config(Component.Config(changes_url=False, template="notifications.html"))
class Notifications(Component):
    def __init__(self, notifications: Optional[Dict[str, Notification]] = None) -> None:
        self.state.notifications = (
            {id: n for id, n in notifications.items() if n is not None}
            if notifications is not None
            else dict()
        )
        super().__init__()

    @listener(event="pushNotification")
    def on_push_notification(self, event):
        self.state.notifications[str(uuid1())] = event.params.get(
            "notification", Notification("Undefined message")
        )


class FormEncodingSupportMixin:
    @classmethod
    def encode_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return value.data if value is not None else dict()
        return super().encode_param(name, value)  # type:ignore

    @classmethod
    def decode_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return ProjectForm(data=value)
        return super().decode_param(name, value)  # type:ignore


# Tasks
########
@config(
    Component.Config(
        template="tasks/view.html",
        components=dict(confirmation=ConfirmationDialog),
        changes_url=False,
    )
)
class ViewTask(Component):
    def __init__(self, task_id: int, _task: Optional[Task] = None) -> None:
        self._task = _task
        super().__init__()

    @cached_property
    def task(self) -> Task:
        return (
            self._task
            if self._task is not None and self._task.id == self.state.task_id
            else Task.query.get(self.state.task_id)
        )

    @listener(source="./confirmation")
    def on_confirmation(self, event: "Event"):
        if event.action == "delete_task" and event.name == "ok":
            return self.delete_task(event.params["params"]["task_id"], True)
        return True

    @action
    def delete_task(self, task_id: int, confirmed: bool = False):
        if not confirmed:
            # display confirmation dialog
            self.confirmation = dict(
                title="Delete task",
                question="Are you sure?",
                action="delete_task",
                params=dict(task_id=task_id),
            )
            # redisplay this compomenonet
            return True
        else:
            # delete task
            task = Task.query.get(task_id)
            db.session.delete(task)
            db.session.commit()
            self.emit("delete", task=task, task_id=task_id)
            self.emit(
                "pushNotification",
                notification=Notification("{} deleted.".format(task.name)),
            )
            return False


@config(
    Component.Config(
        template="tasks/edit.html",
        components=dict(confirmation=ConfirmationDialog),
        changes_url=False,
    )
)
class EditTask(FormEncodingSupportMixin, Component):
    def __init__(
        self, task_id: int, form: Optional["Form"] = None, _task: Optional[Task] = None
    ) -> None:
        self._task = _task
        super().__init__()

    @run_only_once
    def mount(self):
        self.task = (
            Task.query.get(self.state.task_id) if self._task is None else self._task
        )
        if self.state.form is None:
            self.state.form = TaskForm(obj=self.task)

    @listener(source="./confirmation")
    def on_confirmation(self, event: "Event"):
        if event.action == "cancel" and event.name == "ok":
            return self.cancel(True)
        return True

    @action
    def cancel(self, confirmed=False):
        if self._is_task_modified() and not confirmed:
            self.confirmation = dict(
                title="Cancel Edit",
                question="Are you sure, all changes will be lost?",
                action="cancel",
            )
            return True  # force redisplay to show confirmation dialog
        else:
            self.emit("cancel")
            return False  # don't execute display

    @action
    def save(self):
        self.mount()
        if self.state.form.validate():
            try:
                self.state.form.populate_obj(self.task)
                db.session.commit()
                self.emit("save", task=self.task, task_id=self.task.id)
                self.emit(
                    "pushNotification",
                    notification=Notification("{} saved.".format(self.task.name)),
                )
                # dont execute display
                return False
            except SQLAlchemyError as sql_error:
                self.emit(
                    "pushNotification",
                    notification=Notification(
                        str(getattr(sql_error, "orig", sql_error)), "error"
                    ),
                )
                return True

        # execute display if state is changed
        return None

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()

    def _is_task_modified(self) -> bool:
        self.mount()
        db.session.begin_nested()
        self.state.form.populate_obj(self.task)
        task_is_modified = db.session.is_modified(self.task)
        db.session.rollback()
        return task_is_modified


@config(
    Component.Config(
        template="tasks/add.html",
        components=dict(confirmation=ConfirmationDialog),
        changes_url=False,
    )
)
class AddTask(FormEncodingSupportMixin, Component):
    def __init__(
        self, project_id: Optional[int] = None, form: Optional["Form"] = None
    ) -> None:
        super().__init__()

    @run_only_once
    def mount(self):
        if self.state.form is None:
            self.state.form = TaskForm(obj=Task(project_id=self.state.project_id))

    @listener(source="./confirmation")
    def on_confirmation(self, event: "Event"):
        if event.action == "cancel" and event.name == "ok":
            return self.cancel(True)
        return True

    @action
    def cancel(self, confirmed=False):
        if self._is_task_modified() and not confirmed:
            self.confirmation = dict(
                title="Cancel Add",
                question="Are you sure, all changes will be lost?",
                action="cancel",
            )
            return True  # force redisplay to show confirmation dialog
        else:
            self.emit("cancel")
            return False  # don't execute display

    @action
    def save(self):
        self.mount()
        if self.state.form.validate():
            try:
                task = Task(project_id=self.state.project_id)
                self.state.form.populate_obj(task)
                db.session.add(task)
                db.session.commit()
                self.emit("save", task=task, task_id=task.id)
                self.emit(
                    "pushNotification",
                    notification=Notification("{} saved.".format(task.name)),
                )
                # dont execute display
                return False
            except SQLAlchemyError as sql_error:
                self.emit(
                    "pushNotification",
                    notification=Notification(
                        str(getattr(sql_error, "orig", sql_error)), "error"
                    ),
                )
                return True

        # execute display if state is changed
        return None

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()

    def _is_task_modified(self) -> bool:
        self.mount()
        task = Task(project_id=self.state.project_id)
        self.state.form.populate_obj(task)
        empty_task = Task(project_id=self.state.project_id)
        for column_name in task.__table__.columns.keys():
            if getattr(task, column_name) != getattr(empty_task, column_name):
                return True
        return False


@config(
    Component.Config(
        url_query_params=dict(p="page", ps="page_size"),
        template="tasks.html",
        components=dict(view=ViewTask, add=AddTask, edit=EditTask),
        inject_into_components=lambda self, _config: dict(
            project_id=self.state.project_id
        ),
    )
)
class Tasks(Component):
    def __init__(
        self,
        project_id: Optional[int] = None,
        mode: Optional[str] = None,
        editing_tasks: Set[int] = set(),
        page: int = 0,
        page_size: int = 5,
    ) -> None:
        if mode not in (None, "add"):
            self.state.mode = None
        super().__init__()

    @listener(event="delete", source=["./view.*"])
    def on_child_deleted(self, event: "Event"):
        # redisplay tasks
        return True

    @listener(event="_display", source=["./add"])
    def on_add_display(self, event: "Event"):
        if self.state.mode != event.source_name:
            # when adding go to first page
            # but allow navigation afterward
            self.state.page = 1
        self.state.mode = event.source_name

    @listener(event="_display", source=["./edit.*"])
    def on_edit_display(self, event: "Event"):
        if event.source:
            self.state.editing_tasks.add(event.source.state.task_id)

    @listener(event="cancel", source=["./add"])
    def on_add_cancel(self, event: "Event"):
        self.state.mode = None

    @listener(event="save", source=["./add"])
    def on_add_save(self, event: "Event"):
        self.state.mode = None

    @listener(event=["save", "cancel"], source=["./edit.*"])
    def on_edit_finish(self, event: "Event"):
        if event.source:
            self.state.editing_tasks.remove(event.source.state.task_id)

    def display(self) -> Union[str, "Response"]:

        tasks = Task.query
        if self.state.project_id is not None:
            tasks = tasks.filter_by(project_id=self.state.project_id)

        self.tasks_count = tasks.count()
        self.total_pages = ceil(self.tasks_count / self.state.page_size)
        if self.state.page < 1:
            self.state.page = 1
        if self.state.page >= self.total_pages:
            self.state.page = self.total_pages
        start = (self.state.page - 1) * self.state.page_size
        self.tasks = tasks.order_by(Task.id.desc())[
            start : start + self.state.page_size
        ]
        return super().display()


# Projects
##########
@config(Component.Config(components=dict(confirmation=ConfirmationDialog)))
class AddProject(FormEncodingSupportMixin, Component):
    def __init__(self, form: Optional["Form"] = None) -> None:
        self.confirmation: Optional[dict] = None
        super().__init__()

    @run_only_once
    def mount(self):
        if self.state.form is None:
            self.state.form = ProjectForm(obj=Project())

    @listener(source="./confirmation")
    def on_confirmation(self, event: "Event"):
        if event.action == "cancel" and event.name == "ok":
            return self.cancel(True)
        return True

    @action
    def cancel(self, confirmed=False):
        if self._is_project_modified() and not confirmed:
            self.confirmation = dict(
                title="Cancel Add",
                question="Are you sure, all changes will be lost?",
                action="cancel",
            )
            return True  # force redisplay to show confirmation dialog
        else:
            self.emit("cancel")
            return False  # don't execute display

    @action
    def save(self) -> Optional[bool]:
        self.mount()
        if self.state.form.validate():
            try:
                project = Project()
                self.state.form.populate_obj(project)
                db.session.add(project)
                db.session.commit()
                self.emit("save", project=project, project_id=project.id)
                self.emit(
                    "pushNotification",
                    notification=Notification("{} saved.".format(project.name)),
                )
                # dont execute display
                return False
            except SQLAlchemyError as sql_error:
                self.emit(
                    "pushNotification",
                    notification=Notification(
                        str(getattr(sql_error, "orig", sql_error)), "error"
                    ),
                )
                return True

        # execute display if state is changed
        return None

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()

    def _is_project_modified(self) -> bool:
        self.mount()
        project = Project()
        self.state.form.populate_obj(project)
        empty_project = Project()
        for column_name in project.__table__.columns.keys():
            if getattr(project, column_name) != getattr(empty_project, column_name):
                return True
        return False


@config(
    Component.Config(
        components=dict(tasks=Tasks, confirmation=ConfirmationDialog),
        inject_into_components=lambda self, _config: dict(
            project_id=self.state.project_id
        ),
    )
)
class EditProject(FormEncodingSupportMixin, Component):
    def __init__(
        self,
        project_id: int,
        form: Optional["Form"] = None,
        prev_project_id: Optional[int] = None,
        next_project_id: Optional[int] = None,
    ) -> None:
        self.confirmation: Optional[dict] = None
        super().__init__()

    def mount(self):
        if getattr(self, "_mounted_for", None) == self.state.project_id:
            return
        self._mounted_for = self.state.project_id

        if self.state.prev_project_id is None and self.state.next_project_id is None:
            self.emit(
                "ask_question",
                question="get_prev_next",
                project_id=self.state.project_id,
            ).to("/**/.")
        self.project = Project.query.get(self.state.project_id)
        if self.state.form is None:
            self.state.form = ProjectForm(obj=self.project)

    @listener(event="answer_question", source="/**/.")
    def on_answer_question(self, answer: "Event"):
        if answer.question == "get_prev_next":
            self.state.prev_project_id = answer.prev_project_id
            self.state.next_project_id = answer.next_project_id

    @listener(source="./confirmation")
    def on_confirmation(self, event: "Event"):
        if event.action == "cancel" and event.name == "ok":
            return self.cancel(True)
        elif event.action == "goto" and event.name == "ok":
            return self.goto(**event.params["params"], confirmed=True)
        return True

    @action
    def cancel(self, confirmed=False):
        if self._is_project_modified() and not confirmed:
            self.confirmation = dict(
                title="Cancel Edit",
                question="Are you sure, all changes will be lost?",
                action="cancel",
            )
            return True  # force redisplay to shown confirmation dialog
        else:
            self.emit("cancel")
            return False

    @action
    def goto(self, project_id: int, confirmed=False):
        if self._is_project_modified() and not confirmed:
            self.confirmation = dict(
                title="Moving out",
                question="Are you sure, all changes will be lost?",
                action="goto",
                params=dict(project_id=project_id),
            )
        else:
            # display edit with other record
            self.state.project_id = project_id
            self.state.form = None
            self.state.prev_project_id = None
            self.state.next_project_id = None
            self.mount()
        return True

    @action
    def save(self) -> Optional[bool]:
        self.mount()
        if self.state.form.validate():
            self.state.form.populate_obj(self.project)
            db.session.commit()
            self.emit("save", project=self.project, project_id=self.state.project_id)
            self.emit(
                "pushNotification",
                notification=Notification("{} saved.".format(self.project.name)),
            )
            # dont execute display
            # return False
        # execute display if state is changed
        return None

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()

    def _is_project_modified(self) -> bool:
        self.mount()
        db.session.begin_nested()
        self.state.form.populate_obj(self.project)
        project_is_modified = db.session.is_modified(self.project)
        db.session.rollback()
        return project_is_modified


# TODO when using got on edit tasks are not changed
# TODO When going back with browser execute confirmation if needed
# TODO add decorator run_only_once_for
# TODO display generic error dialog when error is hapend in x-jembe request
# TODO add task mark completed
# TODO add more fields to project and task
# TODO make it looks nice
# TODO add remove polyfil in js (??)
# TODO add jmb:on.keydown/keyup.enter.esc etc mofifiers
@jmb.page(
    "projects",
    Component.Config(
        components=dict(
            edit=EditProject,
            add=AddProject,
            confirmation=ConfirmationDialog,
            notifications=Notifications,
        ),
        url_query_params=dict(p="page", ps="page_size"),
    ),
)
class ProjectsPage(Component):
    def __init__(
        self, mode: Optional[str] = None, page: int = 0, page_size: int = 5
    ) -> None:
        if mode not in (None, "edit", "add"):
            raise BadRequest()
        self.goto = None
        self.confirmation: Optional[dict] = None
        super().__init__()

    @listener(event="_display", source=["./edit", "./add"])
    def on_child_display(self, event: "Event"):
        self.state.mode = event.source_name

    @listener(event="cancel", source=["./edit", "./add"])
    def on_child_cancel(self, event: "Event"):
        self.state.mode = None

    @listener(event="save", source=["./add"])
    def on_add_successful(self, event: "Event"):
        self.state.mode = "edit"
        self.goto = event.params["project_id"]

    @listener(source="./confirmation")
    def on_confirmation(self, event: "Event"):
        if event.action == "delete_project" and event.name == "ok":
            return self.delete_project(event.params["params"]["project_id"], True)
        return True

    @action
    def delete_project(self, project_id: int, confirmed: bool = False):
        if not confirmed:
            # display confirmation dialog
            self.confirmation = dict(
                title="Delete project",
                question="Are you sure?",
                action="delete_project",
                params=dict(project_id=project_id),
            )
        else:
            # delete project
            project = Project.query.get(project_id)
            db.session.delete(project)
            db.session.commit()
            self.emit(
                "pushNotification",
                notification=Notification("{} deleted.".format(project.name)),
            )
        # always redisplay this compomenonet
        return True

    def display(self) -> Union[str, "Response"]:
        if self.state.mode is None:
            # if mode is display projects table
            # othervise instead of table subcomponent specified by mode will be displayd
            self.projects_count = Project.query.count()
            self.total_pages = ceil(self.projects_count / self.state.page_size)
            if self.state.page < 1:
                self.state.page = 1
            if self.state.page >= self.total_pages:
                self.state.page = self.total_pages
            start = (self.state.page - 1) * self.state.page_size
            self.projects = Project.query.order_by(Project.id.desc())[
                start : start + self.state.page_size
            ]
        return super().display()

    @listener(event="ask_question", source="./edit")
    def on_question_asked(self, event: "Event"):
        if event.question == "get_prev_next":
            prev_project_id, next_project_id = self.get_prev_next_id(event.project_id)
            self.emit(
                "answer_question",
                question=event.question,
                project_id=event.project_id,
                prev_project_id=prev_project_id,
                next_project_id=next_project_id,
            ).to(event.source_full_name)
        return False

    def get_prev_next_id(self, project_id) -> Tuple[Optional[int], Optional[int]]:
        # TODO make abstraction of this query manipulation to get next, previous when
        # order is by any other field or when additional filters are applied
        prev = (
            Project.query.with_entities(Project.id)
            .order_by(Project.id)
            .filter(Project.id > project_id)
            .first()
        )
        next = (
            Project.query.with_entities(Project.id)
            .order_by(Project.id.desc())
            .filter(Project.id < project_id)
            .first()
        )
        return (
            prev[0] if prev is not None else None,
            next[0] if next is not None else None,
        )

