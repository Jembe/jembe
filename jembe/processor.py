from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import Jembe


class Processor:
    """
    1. Will use deapest component.url from all components on the page as window.location
    2. When any component action or listener returns template string default 
        action (display) will not be called instead returned template string
        will be used to render compononet 
    """

    def __init__(self, jembe: "Jembe"):
        self.jembe = jembe
