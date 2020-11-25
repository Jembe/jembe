"""
Creates Project/Tasks application component by component
with JUST MAKE IT WORK mindset. 
"""
from jembe.app import get_processor
from typing import List, Optional, TYPE_CHECKING, Union, Any, Tuple
from dataclasses import dataclass
from jembe.exceptions import BadRequest, JembeError
from jembe.component_config import action, config, listener
from jembe import Component
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
        self, title: str = "", question: str = "", action: Optional[str] = None
    ) -> None:
        if action is None:
            raise JembeError("action:str parameter is required")
        super().__init__()


@dataclass
class Notification:
    message: str
    timer: Optional[int] = None
    level: str = "info"


@config(Component.Config(changes_url=False, template="notifications.html"))
class Notifications(Component):
    def __init__(self, notifications: List[Notification] = []) -> None:
        super().__init__()

    @listener(event="pushNotification")
    def on_push_notification(self, event):
        self.state.notifications.append(
            event.params.get("notification", Notification("Undefined message"))
        )


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
        self.state.confirm_action = "cancel"

    @action
    def save(self) -> Optional[bool]:
        self.mount()
        if self.state.form.validate():
            self.state.form.populate_obj(self.project)
            db.session.commit()
            self.emit("save", project=self.project, project_id=self.state.project_id)
            self.emit("pushNotification", notification=Notification("Save successfull", 2000))
            # dont execute display
            # return False
        # execute display if state is changed
        return None

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()

# TODO make notiications timer work: jmb:on.init event fired add remove polyfil in js (??), make $jmb.set('notification[index].timer', 0) work
# TODO notifications should have state time to update timers on post and redisplay when has messages 
# TODO successfull save should show notification to user (undo operation is quite complex to implement so skip that for now)
# TODO join back and cancel buttons on edit taking account is form changed
# TODO add rename/edit project, add project delete project as modals
# TODO add tasks list, add, edit, delete and mark completed
@jmb.page(
    "projects",
    Component.Config(
        components=dict(edit=EditProject, notifications=Notifications),
        url_query_params=dict(p="page", ps="page_size"),
    ),
)
class ProjectsPage(Component):
    def __init__(
        self, mode: Optional[str] = None, page: int = 0, page_size: int = 5
    ) -> None:
        if mode not in (None, "edit"):
            raise BadRequest()
        super().__init__()

    @listener(event="_display", source="./edit")
    def on_child_display(self, event: "Event"):
        self.state.mode = event.source_name

    @listener(event="cancel", source="./edit")
    def on_child_cancel(self, event: "Event"):
        self.state.mode = None

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
