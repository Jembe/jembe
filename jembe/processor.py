from typing import TYPE_CHECKING, Dict, cast, Type
from lxml import etree


if TYPE_CHECKING:
    from .app import Jembe
    from flask import Request, Response
    from .component import Component


class Processor:
    """
    1. Will use deapest component.url from all components on the page as window.location
    2. When any component action or listener returns template string default 
        action (display) will not be called instead returned template string
        will be used to render compononet 
    """

    def __init__(self, jembe: "Jembe", component_full_name: str, request: "Request"):
        self.jembe = jembe
        self.request = request

        self.components: Dict[str, "Component"] = self.init_components(
            component_full_name
        )
        self.directly_requested_component = self.components[component_full_name]
        self.directly_requested_component_action = (
            self.directly_requested_component._config.default_action
        )

    def init_components(self, component_full_name: str) -> Dict[str, "Component"]:
        # TODO initialise parent components
        # TODO create component hiearachy etc.
        components = {}

        cconfig = self.jembe.components_configs[component_full_name]
        component = cconfig._init_component_class_from_request(self.request)
        component._config = cconfig  # type:ignore
        components[component_full_name] = component

        return components

    def process_request(self) -> "Response":
        # TODO pickup responses from other components
        # TODO handle AJAX request
        cresponse = getattr(
            self.directly_requested_component, self.directly_requested_component_action
        )()
        if isinstance(cresponse, str):
            # action returns html
            cresponse = self.add_dom_attrs(self.directly_requested_component, cresponse)

        return cresponse

    def add_dom_attrs(self, component: "Component", html: str) -> str:
        """
        Adds dom attrs to html.
        If html has one root tag attrs are added to that tag othervise
        html is souranded with div
        """

        def set_jmb_attrs(elem):
            elem.set("jmb:name", component._config.full_name)
            if component.key:
                elem.set("jmb:key", None)
            elem.set("jmb:data", "{}")

        if not html:
            html = "<div></div>"
        root = etree.HTML(html)
        if component._config.parent is None:
            doc = root.getroottree()
            set_jmb_attrs(root)
            return etree.tostring(doc, method="html")
        else:
            doc = root[0]
            if len(root[0]) == 1:
                set_jmb_attrs(root[0][0])
            else:
                # add div tag at root[0][0] and move all root[0][0..len] to new tag
                raise NotImplementedError()

            return etree.tostring(doc[0], method="html")

