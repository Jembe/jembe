"""
Creates Project/Tasks application component by component
with JUST MAKE IT WORK mindset. 
"""
from typing import Optional, TYPE_CHECKING, Union, Any, Tuple, Dict
from uuid import uuid1
from dataclasses import dataclass
from jembe.exceptions import BadRequest, JembeError
from jembe.component_config import action, config, listener
from jembe import Component
from sqlalchemy.exc import SQLAlchemyError
from dapp.models import Project, Task
from dapp.jmb import jmb
from dapp.db import db
from wtforms_sqlalchemy.orm import model_form

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
        action_params: Optional[dict] = None,
    ) -> None:
        if action is None:
            raise JembeError("action:str parameter is required")
        super().__init__()

    @action
    def ok(self):
        self.emit(
            "ok", action=self.state.action, action_params=self.state.action_params
        )
        return False

    @action
    def cancel(self):
        self.emit(
            "cancel", action=self.state.action, action_params=self.state.action_params
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


@config(Component.Config(components=dict(confirmation=ConfirmationDialog)))
class AddProject(Component):
    def __init__(
        self, form: Optional["Form"] = None, confirm_action: Optional[str] = None,
    ) -> None:
        self._mounted = False
        super().__init__()

    def mount(self):
        if self._mounted:
            return
        self._mounted = True

        if self.state.form is None:
            self.state.form = ProjectForm(obj=Project())

    @classmethod
    def encode_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return value.data if value is not None else dict()
        return super().encode_param(name, value)

    @classmethod
    def decode_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return ProjectForm(data=value)
        return super().decode_param(name, value)

    @listener(source="./confirmation")
    def on_action_confirmation(self, event: "Event"):
        self.state.confirm_action = None
        if event.params["action"] == "cancel" and event.name == "ok":
            self.emit("cancel")
            return False  # don't execute display

    @action
    def cancel(self):
        self.mount()

        project = Project()
        self.state.form.populate_obj(project)
        empty_project = Project()
        project_is_modified = False
        for column_name in project.__table__.columns.keys():
            project_is_modified = getattr(project, column_name) != getattr(
                empty_project, column_name
            )
            if project_is_modified:
                break
        if project_is_modified:
            self.state.confirm_action = "cancel"
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


@config(Component.Config(components=dict(confirmation=ConfirmationDialog)))
class EditProject(Component):
    def __init__(
        self,
        project_id: int,
        form: Optional["Form"] = None,
        confirm_action: Optional[str] = None,
    ) -> None:
        self._mounted = False
        super().__init__()

    def mount(self):
        if self._mounted:
            return
        self._mounted = True

        self.project = Project.query.get(self.state.project_id)
        if self.state.form is None:
            self.state.form = ProjectForm(obj=self.project)

    @classmethod
    def encode_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return value.data if value is not None else dict()
        return super().encode_param(name, value)

    @classmethod
    def decode_param(cls, name: str, value: Any) -> Any:
        if name == "form":
            return ProjectForm(data=value)
        return super().decode_param(name, value)

    @listener(source="./confirmation")
    def on_action_confirmation(self, event: "Event"):
        self.state.confirm_action = None
        if event.params["action"] == "cancel" and event.name == "ok":
            self.emit("cancel")
            return False  # don't execute display

    @action
    def cancel(self):
        self.mount()
        db.session.begin_nested()
        self.state.form.populate_obj(self.project)
        project_is_modified = db.session.is_modified(self.project)
        db.session.rollback()
        if project_is_modified:
            self.state.confirm_action = "cancel"
        else:
            self.emit("cancel")
            return False  # don't execute display

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


# TODO Refactor confirmation in edit and add to match confirmation in project
# TODO add tasks list, add, edit, delete and mark completed
# TODO add more fields to project and task
# TODO  add remove polyfil in js (??)
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
        if event.name == "ok":
            if event.action == "delete_project":
                return self.delete_project(event.action_params["project_id"], True)
        return True

    @action
    def delete_project(self, project_id: int, _confirmed: bool = False):
        if not _confirmed:
            self.confirmation = dict(
                title="Delete project",
                question="Are you sure?",
                action="delete_project",
                action_params=dict(project_id=project_id),
            )
        else:
            project = Project.query.get(project_id)
            db.session.delete(project)
            db.session.commit()
        return True

    def display(self) -> Union[str, "Response"]:
        if self.state.mode is None:
            # if mode is display projects table
            # othervise instead of table subcomponent specified by mode will be displayd
            self.projects_count = Project.query.count()
            self.total_pages = self.projects_count // self.state.page_size
            if self.state.page < 0:
                self.state.page = 0
            if self.state.page > self.total_pages:
                self.state.page = self.total_pages
            start = self.state.page * self.state.page_size
            self.projects = Project.query.order_by(Project.id)[
                start : start + self.state.page_size
            ]
            self.projects_count = Project.query.count()
        return super().display()
