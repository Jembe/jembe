from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .component import Component


class Event:
    def __init__(self, source: "Component", name: str, *args, **kwargs):
        self.name = name
        self.source = source
        self.args = args
        self.kwargs = kwargs

