from typing import TYPE_CHECKING, Optional, Union

from .component_config import UrlPath, config
from .component import Component

# from flask import send_from_directory
from .app import get_processor

if TYPE_CHECKING:
    from flask import Response


class FileComponent(Component):
    def __init__(self, storage_name: str, file_path: UrlPath):
        super().__init__()

    def display(self) -> Union[str, "Response"]:
        return (
            get_processor()
            .jembe.get_storage(self.state.storage_name)
            .send_file(self.state.file_path)
        )


@config(Component.Config(components=dict(file=FileComponent)))
class JembePage(Component):
    pass
