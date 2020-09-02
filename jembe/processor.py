from typing import (
    TYPE_CHECKING,
    Dict,
    cast,
    Type,
    List,
    Optional,
    Union,
    Sequence,
    Tuple,
    Deque,
    Any,
)
from collections import deque
from lxml import etree
from lxml.html import Element
from flask import json, escape, jsonify, Response
from .errors import JembeError
from .component_config import ComponentConfig


if TYPE_CHECKING:  # pragma: no cover
    from .app import Jembe
    from flask import Request
    from .component import Component, ComponentState


class Command:
    jembe: "Jembe"

    def __init__(self, component_exec_name: str):
        self.component_exec_name = component_exec_name

        self.component: "Component"

    def mount(self, processor: "Processor") -> "Command":
        self.processor = processor
        return self

    def execute(self):
        raise NotImplementedError()


class CallCommand(Command):
    def __init__(
        self,
        component_exec_name: str,
        action_name: str,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[dict] = None,
    ):
        super().__init__(component_exec_name)
        self.action_name = action_name
        self.args = args if args is not None else tuple()
        self.kwargs = kwargs if kwargs is not None else dict()

    def mount(self, processor: "Processor") -> "Command":
        self.component = processor.components[self.component_exec_name]
        return super().mount(processor)

    def execute(self):
        if self.action_name not in self.component._config.component_actions:
            raise JembeError(
                "Action {}.{} does not exist or is not marked as public action".format(
                    self.component._config.full_name, self.action_name
                )
            )

        if (
            self.action_name == ComponentConfig.DEFAULT_DISPLAY_ACTION
            and self.component.exec_name in self.processor.renderers
            and self.processor.renderers[self.component.exec_name][0]
            == self.component.state
        ):
            # if action is display and compoent already is displayed/rendered in same state
            # no need to execute display again because it should return same result
            return

        action_result = getattr(self.component, self.action_name)(
            *self.args, **self.kwargs
        )
        if action_result is None or (
            isinstance(action_result, bool) and action_result == True
        ):
            # after executing action that returns True or None
            # component should be rendered by executing display
            self.processor.commands.append(
                CallCommand(
                    self.component.exec_name, ComponentConfig.DEFAULT_DISPLAY_ACTION
                )
            )
        elif isinstance(action_result, bool) or action_result == False:
            # Do nothing
            pass
        elif self.action_name == ComponentConfig.DEFAULT_DISPLAY_ACTION and isinstance(
            action_result, str
        ):
            # save component display responses in memory
            # Add component html to processor rendererd
            self.processor.renderers[self.component.exec_name] = (
                self.component.state,
                self.component.url,
                action_result,
            )
        elif (
            self.action_name == ComponentConfig.DEFAULT_DISPLAY_ACTION
            and not isinstance(action_result, str)
        ):
            # Display should return html string if not raise JembeError
            raise JembeError(
                "{} action of {} shuld return html string not {}".format(
                    ComponentConfig.DEFAULT_DISPLAY_ACTION,
                    self.component._config.full_name,
                    action_result,
                )
            )

        elif isinstance(action_result, Response):
            # TODO If self.component is component directly requested via http request
            # and it is not x-jembe request return respon
            # othervise raise JembeError
            raise NotImplementedError()
        else:
            raise JembeError(
                "Invalid action result type: {}.{} {}".format(
                    self.component._config.full_name, self.action_name, action_result,
                )
            )


class EmitCommand(Command):
    def mount(self, processor: "Processor") -> "Command":
        self.component = processor.components[self.component_exec_name]
        return super().mount(processor)


class InitialiseCommand(Command):
    def __init__(self, component_exec_name: str, init_params: dict):
        super().__init__(component_exec_name)
        self.init_params = init_params

    def execute(self):
        self.processor.init_component(self.component_exec_name, self.init_params)


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

        self.components: Dict[str, "Component"] = dict()
        self.commands: Deque["Command"] = deque()
        # component renderers is dict[exec_name] = (componentState, url, rendered_str)
        self.renderers: Dict[str, Tuple["ComponentState", str, str]] = dict()
        self.__init_components(component_full_name)

    def __init_components(self, component_full_name: str):
        from .component import Component

        if self.is_x_jembe_request():
            # x-jembe ajax request
            data = json.loads(self.request.data)
            # init components
            for component_data in data["components"]:
                self.init_component(component_data["execName"], component_data["state"])

            # init commands
            for command_data in reversed(data["commands"]):
                self.commands.append(command_factory(command_data))
        else:
            # regular http/s GET request
            c_configs: List["ComponentConfig"] = list()
            # get all components configs from root to requested component
            for cname in component_full_name.strip("/").split("/"):
                c_configs.append(
                    self.jembe.components_configs[
                        "/".join((c_configs[-1].full_name if c_configs else "", cname))
                    ]
                )
            # initialise all components from root to requested component
            # >> parent component exec name, makes easy to build next component exec_name
            parent_exec_name = ""
            for cconfig in c_configs:
                if cconfig.name is None:
                    raise JembeError()
                key = self.request.view_args[cconfig._key_url_param.identifier]
                exec_name = Component._build_exec_name(
                    cconfig.name, key, parent_exec_name
                )
                parent_exec_name = exec_name
                init_params = {
                    up.name: self.request.view_args[up.identifier]
                    for up in cconfig._url_params
                }
                self.init_component(exec_name, init_params)

            # init commands
            c_full_names = list(self.components.keys())
            for c in reversed(c_full_names[:-1]):
                self.commands.append(
                    CallCommand(
                        self.components[c].exec_name,
                        ComponentConfig.DEFAULT_DISPLAY_ACTION,
                    )
                )
            self.commands.append(
                CallCommand(
                    self.components[c_full_names[-1]].exec_name,
                    ComponentConfig.DEFAULT_DISPLAY_ACTION,
                )
            )

    def init_component(self, exec_name: str, init_params: dict,) -> "Component":
        from .component import Component

        component_full_name = Component._exec_name_to_full_name(exec_name)
        cconfig = self.jembe.components_configs[component_full_name]
        component = cconfig.component_class(**init_params)  # type:ignore
        component.exec_name = exec_name
        component.processor = self
        self.components[component.exec_name] = component
        return component

    def process_request(self) -> "Processor":
        while self.commands:
            command = self.commands.pop()
            command.mount(self).execute()
        return self

    def build_response(self) -> "Response":
        # TODO compose respons from components here if is not ajax request otherwise let javascript
        # TODO dont display execute action in ajax that is already on client in proper state
        # TODO handle AJAX request
        # compose full page
        if self.is_x_jembe_request():
            ajax_responses = []
            for exec_name, (state, url, html) in self.renderers.items():
                ajax_responses.append(
                    dict(execName=exec_name, state=state, dom=html, url=url)
                )
            return jsonify(ajax_responses)
        else:
            # TODO for page with components build united response
            c_etrees = {
                exec_name: self._lxml_add_dom_attrs(html, exec_name, state)
                for exec_name, (state, url, html) in self.renderers.items()
            }
            unused_exec_names = sorted(c_etrees.keys(), key=len)
            response_etree = None
            can_find_placeholder = True
            while unused_exec_names and can_find_placeholder:
                can_find_placeholder = False
                if response_etree is None:
                    response_etree = c_etrees[unused_exec_names.pop(0)]
                # TODO compose response including all components not just page
                # find all placeholders in response_tree and replace them with
                # appropriate etrees
                for placeholder in response_etree.xpath(".//div[@jmb-placeholder]"):
                    can_find_placeholder = True
                    exec_name = placeholder.attrib["jmb-placeholder"]
                    c_etree = c_etrees[exec_name]
                    unused_exec_names.pop(unused_exec_names.index(exec_name))
                    placeholder.addnext(c_etree)
                    placeholder.getparent().remove(placeholder)
            return etree.tostring(response_etree, method="html")

    def _lxml_add_dom_attrs(
        self, html: str, exec_name: str, state: "ComponentState"
    ):  # -> "lxml.html.HtmlElement":
        """
        Adds dom attrs to html.
        If html has one root tag attrs are added to that tag othervise
        html is souranded with div
        """
        from .component import Component

        def set_jmb_attrs(elem):
            elem.set("jmb:name", exec_name)
            json_state = json.dumps(state, separators=(",", ":"))
            elem.set("jmb:state", json_state)

        if not html:
            html = "<div></div>"
        root = etree.HTML(html)
        if Component._is_page_exec_name(exec_name):
            # exec_name is fom page component, component with no parent
            doc = root.getroottree()
            set_jmb_attrs(root)
            return doc
        else:
            doc = root[0]
            if len(root[0]) == 1:
                set_jmb_attrs(root[0][0])
            else:
                # add div tag at root[0][0] and move all root[0][0..len] to new tag
                div = Element("div")
                set_jmb_attrs(div)
                children = root[0].getchildren()
                root[0][0].addprevious(div)
                for child in children:
                    div.append(child)
            return doc[0]

    def is_x_jembe_request(self) -> bool:
        return bool(self.request.headers.get(self.jembe.X_JEMBE, False))

