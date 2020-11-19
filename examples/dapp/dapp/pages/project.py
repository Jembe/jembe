from jembe.exceptions import BadRequest
from typing import Optional, TYPE_CHECKING, Union, Any
from jembe.component_config import action, listener
from jembe import Component
from dapp.models import Project
from dapp.jmb import jmb
from dapp.db import db
from wtforms_sqlalchemy.orm import model_form

if TYPE_CHECKING:
    from flask import Response
    from wtforms import Form
    from jembe import Event

ProjectForm = model_form(Project, db, exclude=("tasks",))


class EditProject(Component):
    def __init__(self, project_id: int, form: Optional["Form"] = None) -> None:
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
            return ProjectForm(value)
        return super().decode_param(name, value)

    @action
    def save(self) -> Optional[bool]:
        if self.state.form.validate():
            self.state.form.populate_obj(self.project)
            db.commit()
            # dont execute display
            return False
        # execute display if state is changed
        return None

    def display(self) -> Union[str, "Response"]:
        self.mount()
        return super().display()


# TODO add rename/edit project, add project delete project as modals
# TODO add tasks list, add, edit, delete and mark completed
@jmb.page(
    "projects",
    Component.Config(
        components=dict(edit=EditProject),
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

    @listener(event="_display", source="./*")
    def on_display_child(self, event: "Event"):
        self.state.mode = event.source_name

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
