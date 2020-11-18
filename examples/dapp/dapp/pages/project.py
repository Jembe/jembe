from typing import TYPE_CHECKING, Union
from jembe import Component
from dapp.models import Project
from dapp.jmb import jmb

if TYPE_CHECKING:
    from flask import Response

# TODO add rename/edit project, add project delete project as modals
# TODO add tasks list, add, edit, delete and mark completed
@jmb.page("projects", Component.Config(url_query_params=dict(p="page", ps="page_size")))
class ProjectPage(Component):
    def __init__(self, page: int = 0, page_size: int = 5) -> None:
        super().__init__()

    def mount(self):
        self.projects_count = Project.query.count()
        self.total_pages = self.projects_count // self.state.page_size
        if self.state.page < 0:
            self.state.page = 0
        if self.state.page > self.total_pages:
            self.state.page = self.total_pages

    def display(self) -> Union[str, "Response"]:
        self.mount()

        start = self.state.page * self.state.page_size
        self.projects = Project.query.order_by(Project.id)[
            start : start + self.state.page_size
        ]
        self.projects_count = Project.query.count()
        return super().display()
