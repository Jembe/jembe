from typing import TYPE_CHECKING, Dict, cast, Type, List, Optional, Union
from lxml import etree
from flask import json, escape
from .errors import JembeError
from .component import ComponentConfig


if TYPE_CHECKING:  # pragma: no cover
    from .app import Jembe
    from flask import Request, Response
    from .component import Component


class Command:
    jembe: "Jembe"

    def mount(self, processor: "Processor") -> "Command":
        self.processor = processor
        return self

    def execute(self):
        raise NotImplementedError()


class CallCommand(Command):
    def __init__(self, component_exec_name: str, action_name: str, *args, **kwargs):
        self.component_exec_name = component_exec_name
        self.action_name = action_name
        self.args = args
        self.kwargs = kwargs

        self.component: "Component"

    def mount(self, processor: "Processor") -> "CallCommand":
        super().mount(processor)
        self.component = processor.components[self.component_exec_name]
        return self

    def execute(self) -> Union[None, bool, str, "Response"]:
        if self.action_name in self.component._config.public_actions:
            return getattr(self.component, self.action_name)(*self.args, **self.kwargs)
        raise JembeError(
            "Action {}.{} does not exist or is not marked as public action".format(
                self.component._config.full_name, self.action_name
            )
        )


class EmitCommand(Command):
    pass


class InitialiseCommand(Command):
    pass


def command_factory(command_data: dict) -> "Command":
    if command_data["type"] == "call":
        return CallCommand(
            command_data["componentExecName"],
            command_data["actionName"],
            *command_data["args"],
            **command_data["kwargs"],
        )
    raise NotImplementedError()


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

        self.components: Dict[str, "Component"]
        self.commands: List["Command"]
        self._init_components(component_full_name)

    def _init_components(self, component_full_name: str):
        # TODO initialise parent components
        # TODO create component hiearachy etc.
        self.components = {}
        self.commands = []
        if self.request.headers.get(self.jembe.X_JEMBE, False):
            # x-jembe ajax request
            data = json.loads(self.request.data)
            # TODO order components from lower to deeper so that parent can be set
            for component_data in data["components"]:
                # TODO exec_name to full_name
                component_full_name = component_data["execName"]
                cconfig = self.jembe.components_configs[component_full_name]

                parent_exec_name = "/".join(component_data["execName"].split("/")[:-1])
                parent = self.components[parent_exec_name] if parent_exec_name else None
                component = cconfig._init_component_from_json_data(
                    parent, component_data
                )
                self.components[component.exec_name] = component
            for command_data in data["commands"]:
                self.commands.append(command_factory(command_data))
        else:
            # regular http/s GET request
            cconfig = self.jembe.components_configs[component_full_name]
            component = cconfig._init_component_from_url_path(self.request)
            self.components[component.exec_name] = component
            direct_component_exec_name = component.exec_name

            self.commands.append(
                CallCommand(
                    direct_component_exec_name, ComponentConfig.DEFAULT_DISPLAY_ACTION
                )
            )

    def process_request(self) -> "Response":
        # TODO pickup responses from other components
        # TODO handle AJAX request
        # cresponse = getattr(
        #     self.directly_requested_component, self.directly_requested_component_action
        # )()
        cresponse = self.commands[0].mount(self).execute()

        if isinstance(cresponse, str):
            # action returns html
            cresponse = self.add_dom_attrs(self.commands[0].component, cresponse)

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

