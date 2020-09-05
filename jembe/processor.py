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
    NamedTuple,
)
from collections import deque, namedtuple
from itertools import accumulate, chain
from operator import add
from lxml import etree
from lxml.html import Element
from flask import json, escape, jsonify, Response
from .errors import JembeError
from .component_config import ComponentConfig


if TYPE_CHECKING:  # pragma: no cover
    from .app import Jembe
    from flask import Request
    from .component import Component, ComponentState


class Event:
    def __init__(self, source: "Component", name: str, to: Optional[str], params: dict):
        self.source = source
        self.name = name
        self.params = params
        self.to: Optional[str] = None


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
            and self.processor.renderers[self.component.exec_name].state
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
            self.processor.renderers[self.component.exec_name] = ComponentRender(
                True,
                self.component.state.deepcopy(),
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
    def __init__(self, component_exec_name: str, event_name: str, params: dict):
        super().__init__(component_exec_name)
        self.event_name = event_name
        self.params = params
        self._to: Optional[str] = None

    def mount(self, processor: "Processor") -> "Command":
        self.component = processor.components[self.component_exec_name]
        return super().mount(processor)

    def to(self, to: Optional[str]):
        """
        emit_event_to is glob like string for finding compoennt.

        if emit_event_to is:

            - None -> emit to every initialised component 
            - /compoent1.key1/compoent2.key2    -> compoenent with complete exec_name
            - ./component                       -> emit to direct child named "component" without key
            - ./component.*                     -> emit to direct child named "component" with any key
            - ./component.key                   -> emit to direct child named "component with key equals "key"
            - ./**/component[.[*|<key>]]        -> emit to child at any level
            - ..                                -> emit to parent
            - ../component[.[*|<key>]]          -> emit to sibling 
            - /**/.                             -> emit to parent at any level
            - /**/component[.[*|<key>]]/**/.    -> emit to parent at any level named
            - etc.
        """
        self._to = to

    def execute(self):
        """
        finds all components mathcing self.to that have registred listeners
        whose source is matched to self.component.exec_name and calls matching 
        listeners
        """
        # TODO create function glob_match_exec_name(pattern_exec_name, pattern, component_exec_name)
        event = Event(self.component, self.event_name, self._to, self.params)
        # ignore emit.to, emit.event_name and listener.event_name, listener.source
        for exec_name, component in self.processor.components.items():
            for (
                listener_method_name,
                listener,
            ) in component._config.component_listeners.items():
                # TODO filter by glob match both way
                if listener.event_name is None or listener.event_name == self.event_name:
                    self._execute_listener(component, listener_method_name, event)

    def _execute_listener(
        self, component: "Component", listener_method_name: str, event: "Event"
    ):
        listener_result = getattr(component, listener_method_name)(event)
        if listener_result is None or (
            isinstance(listener_result, bool) and listener_result == True
        ):
            # after executing listener that returns True or None
            # component should be rendered by executing display
            self.processor.commands.append(
                CallCommand(
                    component.exec_name, ComponentConfig.DEFAULT_DISPLAY_ACTION
                )
            )
        elif isinstance(listener_result, bool) or listener_result == False:
            # Do nothing
            pass
        else:
            raise JembeError(
                "Invalid listener result type: {}.{} {}".format(
                    component._config.full_name,
                    listener_method_name,
                    listener_result,
                )
            )


class InitialiseCommand(Command):
    def __init__(self, component_exec_name: str, init_params: dict):
        super().__init__(component_exec_name)
        self.init_params = init_params

    def execute(self):
        if not self.component_exec_name in self.processor.components:
            # create new component if component with identical exec_name
            # does not exist
            self.processor.init_component(self.component_exec_name, self.init_params)
        else:
            # if state params are same continue
            # else raise jembeerror until find better solution
            component = self.processor.components[self.component_exec_name]
            for key, value in component.state.items():
                if key in self.init_params and value != self.init_params[key]:
                    raise JembeError(
                        "Rendering component with different state params from existing compoenent {}".format(
                            component
                        )
                    )


def command_factory(command_data: dict) -> "Command":
    if command_data["type"] == "call":
        return CallCommand(
            command_data["componentExecName"],
            command_data["actionName"],
            command_data["args"],
            command_data["kwargs"],
        )
    raise NotImplementedError()


class ComponentRender(NamedTuple):
    """represents rendered coponent html with additional parametars"""

    fresh: bool
    state: "ComponentState"
    url: Optional[str]
    html: Optional[str]


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
        self.renderers: Dict[str, "ComponentRender"] = dict()
        self.__init_components(component_full_name)

    def __init_components(self, component_full_name: str):
        if self.is_x_jembe_request():
            # x-jembe ajax request
            data = json.loads(self.request.data)
            # init components from data["components"]
            for component_data in data["components"]:
                component = self.init_component(
                    component_data["execName"], component_data["state"]
                )
                # mark component as already rendered/displayed at client browser
                self.renderers[component.exec_name] = ComponentRender(
                    False, component.state.deepcopy(), component_data["url"], None
                )
            # init components from url_path if thay doesnot exist in data["compoenents"]
            self._init_components_from_url_path(component_full_name)

            # init commands
            for command_data in reversed(data["commands"]):
                self.commands.append(command_factory(command_data))
        else:
            # regular http/s GET request
            self._init_components_from_url_path(component_full_name)

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

    def _init_components_from_url_path(self, component_full_name: str):
        """ 
            inits components from request url_path 
            if component with same exec_name is not already initialised
        """
        from .component import Component

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

            key = self.request.view_args[cconfig._key_url_param.identifier].lstrip(".")
            exec_name = Component._build_exec_name(cconfig.name, key, parent_exec_name)
            parent_exec_name = exec_name
            if exec_name not in self.components:
                init_params = {
                    up.name: self.request.view_args[up.identifier]
                    for up in cconfig._url_params
                }
                self.init_component(exec_name, init_params)

    def init_component(self, exec_name: str, init_params: dict,) -> "Component":
        from .component import Component

        component_full_name = Component._exec_name_to_full_name(exec_name)
        cconfig = self.jembe.components_configs[component_full_name]
        component = cconfig.component_class(**init_params)  # type:ignore
        component.exec_name = exec_name
        self.components[component.exec_name] = component
        return component

    def process_request(self) -> "Processor":
        # execute all commands from self.commands stack
        while self.commands:
            command = self.commands.pop()
            command.mount(self).execute()
        # for all freshly rendered component who does not have parent renderers
        # eather at client (send via x-jembe.components) nor just created by
        # server call display command
        needs_render_exec_names = set(
            chain.from_iterable(
                accumulate(map(lambda x: "/" + x, exec_name.strip("/").split("/")), add)
                for exec_name, cr in self.renderers.items()
                if cr.fresh == True
            )
        )
        missing_render_exec_names = needs_render_exec_names - set(self.renderers.keys())
        for exec_name in sorted(
            missing_render_exec_names,
            key=lambda exec_name: self.components[exec_name]._config._hiearchy_level,
        ):
            self.commands.append(
                CallCommand(exec_name, ComponentConfig.DEFAULT_DISPLAY_ACTION)
            )
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
            for exec_name, (fresh, state, url, html) in self.renderers.items():
                if fresh:
                    ajax_responses.append(
                        dict(execName=exec_name, state=state, dom=html, url=url)
                    )
            return jsonify(ajax_responses)
        else:
            # TODO for page with components build united response
            c_etrees = {
                exec_name: self._lxml_add_dom_attrs(html, exec_name, state, url)
                for exec_name, (fresh, state, url, html) in self.renderers.items()
                if fresh and state is not None and url is not None and html is not None
            }
            unused_exec_names = sorted(
                c_etrees.keys(),
                key=lambda exec_name: self.components[
                    exec_name
                ]._config._hiearchy_level,
            )
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
        self, html: str, exec_name: str, state: "ComponentState", url: str
    ):  # -> "lxml.html.HtmlElement":
        """
        Adds dom attrs to html.
        If html has one root tag attrs are added to that tag othervise
        html is souranded with div
        """
        from .component import Component

        def set_jmb_attrs(elem):
            elem.set("jmb:name", exec_name)
            json_state = json.dumps(state, separators=(",", ":"), sort_keys=True)
            elem.set("jmb:state", json_state)
            elem.set("jmb:url", url)

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

