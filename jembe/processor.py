from typing import TYPE_CHECKING, Dict, cast, Type, List, Optional
from lxml import etree
from flask import json, escape
from .component import ComponentState


if TYPE_CHECKING:  # pragma: no cover
    from .app import Jembe
    from flask import Request, Response
    from .component import Component, ComponentConfig


class AppState:
    def __init__(self, app_state: Dict[str, "ComponentState"]):
        self.app_state = app_state
        self.components: Dict[str, "Component"] = {}

    @classmethod
    def from_request(
        cls, request: "Request", component_full_name: str, jembe: "Jembe"
    ) -> "AppState":
        if request.headers.get(jembe.X_JEMBE, False):
            data = json.loads(request.data)
            # self.components: Dict[str, "Component"] = self.init_components(
            #     app_state=data.state
            # )
            raise NotImplementedError("Handling ajax requst")
        else:
            return AppState({component_full_name: ComponentState()})
            # self.components: Dict[str, "Component"] = self.init_components(
            #     component_full_name
            # )


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

        # TODO create app state for direct or ajax request
        # refactor init_components to accept AppState
        # do
        self.request_app_state = AppState.from_request(
            request, component_full_name, jembe
        )

        self.components: Dict[str, "Component"] = self._init_components()
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
            json_state = json.dumps(component.state, separators=(",", ":"))
            elem.set("jmb:state", json_state)

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

