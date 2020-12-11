"""
Creates Project/Tasks application component by component
with JUST MAKE IT WORK mindset. 
"""
from functools import cached_property

from wtforms import form
from jembe.component_config import CConfigRedisplayFlag, ComponentConfig
from jembe.common import ComponentRef
from jembe.utils import run_only_once
from typing import (
    Callable,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
    Any,
    Dict,
)
from uuid import uuid1
from math import ceil
from dataclasses import dataclass, field
from jembe import Component, action, config, listener, BadRequest
from sqlalchemy.exc import SQLAlchemyError
from wtforms_sqlalchemy.orm import model_form
from dapp.models import Project, Task
from dapp.jmb import jmb
from dapp.db import db

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model
    from flask import Response
    from wtforms import Form
    from jembe import Event

ProjectForm = model_form(Project, db, exclude=("tasks",))
TaskForm = model_form(Task, db, exclude=("project",))


@dataclass
class Confirmation:
    title: str
    question: str
    action: str
    params: dict = field(default_factory=dict)


@config(Component.Config(changes_url=False, template="confirmation.html"))
class ConfirmationDialog(Component):
    def __init__(
        self, confirmation: Optional[Confirmation] = None, source: Optional[str] = None
    ) -> None:
        super().__init__()

    @classmethod
    def load_init_param(cls, name: str, value: Any) -> Any:
        if name == "confirmation":
            return (
                Confirmation(
                    title=value.get("title"),
                    question=value.get("question"),
                    action=value.get("action"),
                    params=value.get("params"),
                )
                if value is not None
                else None
            )
        return super().load_init_param(name, value)

    @listener(event="requestConfirmation")
    def on_request_confirmation(self, event: "Event"):
        self.state.confirmation = event.confirmation
        self.state.source = event.source_exec_name

    @action
    def choose(self, choice: str):
        self.emit(
            "confirmation",
            choice=choice,
            action=self.state.confirmation.action,
            action_params=self.state.confirmation.params,
        ).to(self.state.source)
        self.state.confirmation = None
        self.state.source = None


@dataclass
class Notification:
    message: str
    level: str = "info"


@config(Component.Config(changes_url=False, template="notifications.html"))
class Notifications(Component):
    def __init__(self, notifications: Optional[Dict[str, Notification]] = None) -> None:
        if notifications is not None:
            # remove notifications id where notification[id] == None
            self.state.notifications = {
                id: n for id, n in notifications.items() if n is not None
            }
        else:
            self.state.notifications = dict()

        super().__init__()

    @listener(event="pushNotification")
    def on_push_notification(self, event):
        self.state.notifications[str(uuid1())] = event.params.get(
            "notification", Notification("Undefined message")
        )


# lib
#######
class FormLoadDumpMixin:
    @classmethod
    def dump_init_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return value.data if value is not None else dict()
        return super().dump_init_param(name, value)  # type:ignore

    @classmethod
    def load_init_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return ProjectForm(data=value)
        return super().load_init_param(name, value)  # type:ignore


class OnConfirmationSupportMixin:
    @listener(event="confirmation")
    def on_confirmation(self, event: "Event"):
        if hasattr(self, event.action) and event.choice == "ok":
            return getattr(self, event.action)(**event.action_params)


class EditRecord(FormLoadDumpMixin, OnConfirmationSupportMixin, Component):
    class Config(Component.Config):
        def __init__(
            self,
            model: Type["Model"],
            form: Type["Form"],
            name: Optional[str] = None,
            ask_for_prev_next_record: bool = False,
            template: Optional[str] = None,
            components: Optional[Dict[str, ComponentRef]] = None,
            inject_into_components: Optional[
                Callable[["Component", "ComponentConfig"], dict]
            ] = None,
            redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
            changes_url: bool = True,
            url_query_params: Optional[Dict[str, str]] = None,
            # TODO remove those two parameters and set it manually like the compoent.__init__
            _component_class: Optional[Type["Component"]] = None,
            _parent: Optional["ComponentConfig"] = None,
        ):
            self.model = model
            self.form = form
            self.ask_for_prev_next_record = ask_for_prev_next_record
            if template is None:
                template = "lib/edit.html"
            super().__init__(
                name=name,
                template=template,
                components=components,
                inject_into_components=inject_into_components,
                redisplay=redisplay,
                changes_url=changes_url,
                url_query_params=url_query_params,
                _component_class=_component_class,
                _parent=_parent,
            )

    _config: Config

    def __init__(
        self,
        record_id: int,
        form: Optional["Form"] = None,
        prev_record_id: Optional[int] = None,
        next_record_id: Optional[int] = None,
        _record: Optional["Model"] = None,
    ):
        self._record = _record
        super().__init__()

    @run_only_once(for_state="record_id")
    def mount(self):
        if self._record is not None:
            self.record = self._record
        else:
            self.record = self._config.model.query.get(self.state.record_id)

        if self.state.form is None:
            self.state.form = self._config.form(obj=self.record)

        if (
            self._config.ask_for_prev_next_record
            and self.state.prev_record_id is None
            and self.state.next_record_id is None
        ):
            self.emit(
                "askQuestion", question="getPrevNext", record_id=self.state.record_id
            ).to("/**/.")

    @action
    def save(self):
        self.mount()
        if self.state.form.validate():
            try:
                self.state.form.populate_obj(self.record)
                db.session.commit()
                self.emit("save", record=self.record, record_id=self.record.id)
                self.emit(
                    "pushNotification",
                    notification=Notification("{} saved.".format(str(self.record))),
                )
                # don't execute display
                # parent should listen for save and decite what to do
                return False
            except SQLAlchemyError as sql_error:
                self.emit(
                    "pushNotification",
                    notification=Notification(
                        str(getattr(sql_error, "orig", sql_error)), "error"
                    ),
                )
                return True
        # form is invalid redislay compoent and show errors
        # if the state is changed
        return None

    @action
    def cancel(self, confirmed=False):
        if self._is_record_modified() and not confirmed:
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Cancel Edit",
                    question="Are you sure, all changes will be lost?",
                    action="cancel",
                    params=dict(confirmed=True),
                ),
            )
        else:
            self.emit("cancel")
            # don't execute display even if the state has changed
            return False

    @action
    def goto_record(self, record_id: int, confirmed=False):
        if self._is_record_modified() and not confirmed:
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Moving to",
                    question="Are you sure, all changes will be lost?",
                    action="goto",
                    params=dict(record_id=record_id, confirmed=True),
                ),
            )
        else:
            # display edit with other record
            self.state.record_id = record_id
            self.state.form = None
            self.state.prev_record_id = None
            self.state.next_record_id = None
            self.mount()
        return True

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()

    @listener(event="answerQuestion", source="/**/.")
    def on_answer_question(self, answer: "Event"):
        if answer.question == "getPrevNext":
            self.state.prev_record_id = answer.prev_record_id
            self.state.next_record_id = answer.next_record_id

    def _is_record_modified(self) -> bool:
        self.mount()
        db.session.begin_nested()
        self.state.form.populate_obj(self.record)
        is_modified = db.session.is_modified(self.record)
        db.session.rollback()
        return is_modified


# Tasks
########
@config(Component.Config(template="tasks/view.html", changes_url=False,))
class ViewTask(Component):
    def __init__(self, task_id: int, _task: Optional[Task] = None) -> None:
        self._task = _task
        super().__init__()

    @cached_property
    def task(self) -> Task:
        if self._task is not None and self._task.id == self.state.task_id:
            return self._task
        return Task.query.get(self.state.task_id)

    @listener(event="confirmation")
    def on_confirmation(self, event: "Event"):
        # if this component has a method with named like event.action and if
        # user confirmed operation by selecting "ok" choice
        if hasattr(self, event.action) and event.choice == "ok":
            # execute this component method anmed event.action
            # with named parameters received via event.action_params
            return getattr(self, event.action)(**event.action_params)
        return True

    @action
    def delete_task(self, task_id: int, confirmed: bool = False):
        if not confirmed:
            # if delelete is not confirmed by user
            # emit event to ConfirmationDialog component instructing it
            # to display confirmation dialog
            self.emit(
                "request_confirmation",
                confirmation=Confirmation(
                    title="Delete task",
                    question="Are you sure?",
                    action="delete_task",
                    params=dict(task_id=task_id, confirmed=True),
                ),
            )
        else:
            # delete is confirmed by user proceide with
            # delete operation
            task = Task.query.get(task_id)
            db.session.delete(task)
            db.session.commit()
            # emit delete event to inform parent component so
            # that parent can redisplay itself
            self.emit("delete", task=task, task_id=task_id)
            # emit pushNotification event to instruct Notification component
            # to display new notification
            self.emit(
                "pushNotification",
                notification=Notification("{} deleted.".format(task.name)),
            )
            # don't redisplay this component
            # redisplaying this componet will couse error becaouse taks
            # is deleted
            return False


@config(Component.Config(template="tasks/add.html", changes_url=False,))
class AddTask(FormLoadDumpMixin, Component):
    def __init__(
        self, project_id: Optional[int] = None, form: Optional["Form"] = None
    ) -> None:
        super().__init__()

    @run_only_once
    def mount(self):
        if self.state.form is None:
            self.state.form = TaskForm(obj=Task(project_id=self.state.project_id))

    @listener(event="confirmation")
    def on_confirmation(self, event: "Event"):
        if hasattr(self, event.action) and event.choice == "ok":
            return getattr(self, event.action)(**event.action_params)
        return True

    @action
    def cancel(self, confirmed=False):
        if self._is_task_modified() and not confirmed:
            self.emit(
                "request_confirmation",
                confirmation=Confirmation(
                    title="Cancel Add",
                    question="Are you sure, all changes will be lost?",
                    action="cancel",
                    params=dict(confirmed=True),
                ),
            )
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
        components=dict(
            view=ViewTask,
            add=AddTask,
            edit=(
                EditRecord,
                EditRecord.Config(
                    model=Task,
                    form=TaskForm,
                    template="tasks/edit.html",
                    changes_url=False,
                ),
            ),
        ),
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
            self.state.editing_tasks.add(event.source.state.record_id)

    @listener(event="cancel", source=["./add"])
    def on_add_cancel(self, event: "Event"):
        self.state.mode = None

    @listener(event="save", source=["./add"])
    def on_add_save(self, event: "Event"):
        self.state.mode = None

    @listener(event=["save", "cancel"], source=["./edit.*"])
    def on_edit_finish(self, event: "Event"):
        if event.source:
            self.state.editing_tasks.remove(event.source.state.record_id)

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
class AddProject(FormLoadDumpMixin, Component):
    def __init__(self, form: Optional["Form"] = None) -> None:
        super().__init__()

    @run_only_once
    def mount(self):
        if self.state.form is None:
            self.state.form = ProjectForm(obj=Project())

    @listener(event="confirmation")
    def on_confirmation(self, event: "Event"):
        if hasattr(self, event.action) and event.choice == "ok":
            return getattr(self, event.action)(**event.action_params)
        return True

    @action
    def cancel(self, confirmed=False):
        if self._is_project_modified() and not confirmed:
            self.emit(
                "request_confirmation",
                confirmation=Confirmation(
                    title="Cancel Add",
                    question="Are you sure, all changes will be lost?",
                    action="cancel",
                    params=dict(confirmed=True),
                ),
            )
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


# TODO procede with modifing this version until we reduce duplicate code and make configurable reusable components and extend version
# generalize add, view and list
# add generalized templates for edit, add, view and list
# TODO display generic error dialog when error is hapend in x-jembe request
# TODO add task mark completed
# TODO add more fields to project and task
# TODO make it looks nice
# TODO add remove polyfil in js (??)
# TODO add jmb:on.keydown/keyup.enter.esc etc mofifiers
# TODO use regular if else for readability in examples
# TODO extensive comment all python code that is not understud to someone who does know python
# TODO make course that will be created to build this version step by step
# TODO When going back with browser execute confirmation if needed --for next version
# generate system event _browser_navigation
@jmb.page(
    "projects",
    Component.Config(
        components=dict(
            edit=(
                EditRecord,
                EditRecord.Config(
                    model=Project,
                    form=ProjectForm,
                    ask_for_prev_next_record=True,
                    template="projects/edit.html",
                    components=dict(tasks=Tasks),
                    inject_into_components=lambda self, _config: dict(
                        project_id=self.state.record_id
                    ),
                ),
            ),
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

    @listener(event="confirmation")
    def on_confirmation(self, event: "Event"):
        if hasattr(self, event.action) and event.choice == "ok":
            return getattr(self, event.action)(**event.action_params)
        return True

    @action
    def delete_project(self, project_id: int, confirmed: bool = False):
        if not confirmed:
            # display confirmation dialog
            self.emit(
                "requestConfirmation",
                confirmation=Confirmation(
                    title="Delete project",
                    question="Are you sure?",
                    action="delete_project",
                    params=dict(project_id=project_id, confirmed=True),
                ),
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

    @listener(event="askQuestion", source="./edit")
    def on_question_asked(self, event: "Event"):
        if event.question == "getPrevNext":
            prev_record_id, next_record_id = self.get_prev_next_id(event.record_id)
            self.emit(
                "answerQuestion",
                question=event.question,
                record_id=event.record_id,
                prev_record_id=prev_record_id,
                next_record_id=next_record_id,
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
