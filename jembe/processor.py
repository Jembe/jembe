from typing import (
    Tuple,
    Union,
    TYPE_CHECKING,
    TypeVar,
    Dict,
    List,
    Optional,
    Sequence,
    Deque,
    Any,
    NamedTuple,
)
from abc import ABC, abstractmethod
import re
from copy import deepcopy
from enum import Enum
from collections import deque
from itertools import accumulate, chain
from functools import cached_property
from operator import add
from urllib.parse import unquote_plus
from flask.globals import current_app
from jinja2 import Undefined
from lxml import etree
from lxml.html import Element
from flask import json, jsonify, g
from werkzeug import Response
from .common import (
    convert_to_annotated_type,
    exec_name_to_full_name,
    is_direct_child_name,
    is_page_exec_name,
    parent_exec_name,
)
from .exceptions import JembeError
from .component_config import ComponentConfig, RedisplayFlag as RedisplayFlag


if TYPE_CHECKING:  # pragma: no cover
    from .app import Jembe
    from flask import Request
    from .component import Component
    from .component_config import ComponentListener


class Event:
    def __init__(
        self,
        source_exec_name: str,
        source: Optional["Component"],
        event_name: str,
        to: Optional[str],
        params: dict,
    ):
        self.source_exec_name = source_exec_name
        self.name = event_name
        self.params = params
        self.to: Optional[str] = to

        self.source: Optional["Component"] = source

    def __repr__(self):
        return "Event: source={}, name={}, to={} params={}".format(
            self.source_exec_name, self.name, self.to, self.params
        )

    # can access parameters like attribures if name does not colide
    def __getattr__(self, name):
        if name in self.params.keys():
            return self.params[name]
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if "params" in self.__dict__ and name in self.params:
            self.params[name] = value
        return super().__setattr__(name, value)

    @cached_property
    def source_full_name(self) -> str:
        if self.source:
            return self.source._config.full_name
        else:
            return exec_name_to_full_name(self.source_exec_name)

    @cached_property
    def source_name(self) -> str:
        if self.source and self.source._config.name:
            return self.source._config.name
        else:
            return exec_name_to_full_name(self.source_full_name).split("/")[-1]


class SystemEvents(Enum):
    # after display action is executed
    DISPLAY = "_display"
    # after exception is raised by command
    EXCEPTION = "_exception"


TCommand = TypeVar("TCommand", bound="Command")


class Command(ABC):
    jembe: "Jembe"

    def __init__(self, component_exec_name: str):
        self.component_exec_name = component_exec_name
        self.processor: "Processor"
        self.is_mounted = False

    def mount(self: TCommand, processor: "Processor") -> TCommand:
        if self.is_mounted:
            raise JembeError("Command {} is already mounted".format(self.__repr__()))

        self.is_mounted = True
        self.processor = processor
        return self

    @abstractmethod
    def execute(self):
        raise NotImplementedError()

    def __repr__(self):
        return "Command: {} Base".format(self.component_exec_name)

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        return ()

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        return ()

    @property
    def component_full_name(self):
        return exec_name_to_full_name(self.component_exec_name)


class CallActionCommand(Command):
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

        self._do_reinject_into_children = False
        self._component_state_before_execute = None

    def execute(self):
        component = self.processor.components[self.component_exec_name]
        cconfig = component._config
        if self.action_name not in cconfig.component_actions:
            raise JembeError(
                "Action {}.{} does not exist or is not marked as public action".format(
                    cconfig.full_name, self.action_name
                )
            )
        # check if action passes access control
        if not component.ac_check(self.action_name):
            raise ComponentConfig.DEFAULT_AC_EXCEPTION()

        # if component injects params into children save component state json hesh
        if (
            cconfig._inject_into_components is not None
            or cconfig.component_class._jembe_inject_into_overriden
        ):
            self._component_state_before_execute = component.state.tojsondict(
                component, True
            )

        # execute action
        action_result = getattr(component, self.action_name)(*self.args, **self.kwargs)
        component.has_action_or_listener_executed = True

        # process action result
        if action_result is None or (
            isinstance(action_result, bool) and action_result == True
        ):
            if self.component_exec_name in self.processor.components.keys():
                # after executing action that returns True or None
                # component should be rendered by executing display
                self.processor.add_command(
                    CallDisplayCommand(
                        self.component_exec_name, force=action_result == True
                    ),
                    end=True,
                )
        elif isinstance(action_result, bool) and action_result == False:
            # Do nothing
            pass
        elif isinstance(action_result, Response):
            # TODO If self.component is component directly requested via http request
            # and it is not x-jembe request return respon
            # othervise raise JembeError
            raise NotImplementedError()
        else:
            raise JembeError(
                "Invalid action result type: {}.{} {}".format(
                    cconfig.full_name,
                    self.action_name,
                    action_result,
                )
            )

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        return ()

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        commands: List["EmitCommand"] = []
        # reinject params to child components
        if self._component_state_before_execute is not None:
            component = self.processor.components[self.component_exec_name]
            current_state = self.processor.components[
                self.component_exec_name
            ].state.tojsondict(component, True)
            if current_state != self._component_state_before_execute:
                for exec_name, render in self.processor.renderers.items():
                    if render.fresh and is_direct_child_name(
                        self.component_exec_name, exec_name
                    ):
                        # reinitialise component is freshly rerendered forcing it to apply
                        # new injected params
                        commands.extend((InitialiseCommand(exec_name, dict()),))
        return commands

    def __repr__(self):
        return "CallAction({}, {})".format(self.component_exec_name, self.action_name)


class CallDisplayCommand(CallActionCommand):
    def __init__(self, component_exec_name: str, force: bool = False) -> None:
        super().__init__(
            component_exec_name=component_exec_name,
            action_name=ComponentConfig.DEFAULT_DISPLAY_ACTION,
            args=None,
            kwargs=None,
        )
        self.force = force

    @cached_property
    def _component(self) -> "Component":
        return self.processor.components[self.component_exec_name]

    @cached_property
    def _redisplay_needed(self):
        if self.component_exec_name in self.processor.renderers and not (
            self.force
            or (
                # redisplay component created without merging params even if
                # it is rendered with same state (in order to provoke chain redisplayint)
                not self._component._jembe_merged_existing_params
                and not self.processor.renderers[self.component_exec_name].fresh
            )
            or RedisplayFlag.WHEN_ON_PAGE in self._component._config.redisplay
            or RedisplayFlag.WHEN_DISPLAY_EXECUTED in self._component._config.redisplay
            or (
                RedisplayFlag.WHEN_STATE_CHANGED in self._component._config.redisplay
                and self.processor.renderers[self.component_exec_name].state_jsondict
                != self._component.state.tojsondict(self._component, True)
            )
        ):
            # if compoent is already displayed/rendered in same state and no force is set
            # no need to execute display again because it should return same result
            return False
        return True

    def execute(self) -> Optional["Response"]:
        if not self._redisplay_needed:
            return None

        # check if action passes access control
        if not self.force and not self._component.ac_check():
            raise ComponentConfig.DEFAULT_AC_EXCEPTION()

        # execute action
        action_result = getattr(self._component, self.action_name)(
            *self.args, **self.kwargs
        )
        # process action result
        if isinstance(action_result, str):
            # save component display responses in memory
            # Add component html to processor rendererd
            self.processor.renderers[self.component_exec_name] = ComponentRender(
                True,
                self._component.state.tojsondict(self._component, True),
                self._component._jembe_disabled_actions.copy(),
                self._component.state._injected_params_names,
                self._component.url,
                self._component._config.changes_url,
                action_result,
            )
        elif isinstance(action_result, Response):
            # TODO If self.component is component directly requested via http request
            # othervise raise JembeError
            # if not self.processor.renderers:
            #     return action_result
            # else:
            #     raise JembeError(
            #         "{} action should be first one to return responses if that response is not html string but full response object".format(
            #             self._component._config.full_name
            #         )
            #     )
            return action_result
        elif not isinstance(action_result, str):
            # Display should return html string if not raise JembeError
            raise JembeError(
                "{} action of {} shuld return html string not {}".format(
                    ComponentConfig.DEFAULT_DISPLAY_ACTION,
                    self._component._config.full_name,
                    action_result,
                )
            )
        else:
            raise JembeError(
                "Invalid display result type: {}.{} {}".format(
                    self._component._config.full_name,
                    self.action_name,
                    action_result,
                )
            )
        return None

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        return super().get_before_emit_commands()

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        commands = list(super().get_after_emit_commands())
        if self._redisplay_needed:
            commands.append(
                EmitCommand(
                    self.component_exec_name,
                    SystemEvents.DISPLAY.value,
                    dict(action=self.action_name),
                ).mount(self.processor)
            )
        return commands

    def __repr__(self):
        return "DisplayAction({}, {})".format(
            self.component_exec_name, self.action_name
        )


class CallListenerCommand(Command):
    def __init__(
        self,
        component_exec_name: str,
        listener_name: str,
        event: "Event",
    ):
        super().__init__(component_exec_name)
        self.listener_name = listener_name
        self.event = event

    def execute(self):
        component = self.processor.components[self.component_exec_name]
        cconfig = component._config
        if self.listener_name not in cconfig.component_listeners:
            raise JembeError(
                "Listener {}.{} does not exist".format(
                    cconfig.full_name, self.listener_name
                )
            )

        # execute listener
        listener_result = getattr(component, self.listener_name)(self.event)
        component.has_action_or_listener_executed = True
        if listener_result is None or (
            isinstance(listener_result, bool) and listener_result == True
        ):
            # after executing listener that returns True or None
            # component should be rendered by executing display
            self.processor.add_command(
                CallDisplayCommand(component.exec_name, force=listener_result == True),
                end=True,
            )
        elif isinstance(listener_result, bool) or listener_result == False:
            # Do nothing
            pass
        else:
            raise JembeError(
                "Invalid listener result type: {}.{} {}".format(
                    cconfig.full_name,
                    self.listener_name,
                    listener_result,
                )
            )

    def __repr__(self):
        return "CallListener({},{})".format(
            self.component_exec_name, self.listener_name
        )


class EmitCommand(Command):
    # TODO match listner extract as method
    def __init__(
        self,
        component_exec_name: str,
        event_name: str,
        params: dict,
        to: Optional[Union[str, Sequence[str]]] = None,
    ):
        super().__init__(component_exec_name)
        self.event_name = event_name
        self.params = params
        self._to: Tuple[str, ...] = ()
        if to is not None:
            self.to(to)

        self.primary_execution = True

        self.event: "Event"

    def to(self, to: Optional[Union[str, Sequence[str]]]) -> "EmitCommand":
        """
        emit_event_to is glob like string for finding component.

        if emit_event_to is:

            - None -> match to every initialised component
            - /compoent1.key1/compoent2.key2    -> compoenent with complete exec_name
            - ./component                       -> emit to direct child named "component" without key
            - ./component.*                     -> emit to direct child named "component" with any key
            - ./component.key                   -> emit to direct child named "component with key equals "key"
            - ./**/component[.[*|<key>]]        -> emit to child at any level
            - ..                                -> emit to parent
            - ../component[.[*|<key>]]          -> emit to sibling
            - /**/.                             -> emit to parent at any level
            - /**/component[.[*|<key>]]/**/.    -> emit to parent at any level named
            - //                                -> emit to my root page TODO
            - etc.
        """
        if to is None:
            pass
        elif isinstance(to, str):
            self._to = (to,)
        else:
            self._to = tuple(to)
        return self

    def execute(self):
        """
        finds all components mathcing self.to that have registred listeners
        whose source is matched to self.component.exec_name and calls matching
        listeners
        """
        self.event = Event(
            source_exec_name=self.component_exec_name,
            source=self.processor.components.get(self.component_exec_name, None),
            event_name=self.event_name,
            to=self._to,
            params=self.params,
        )
        execute_over: List[Tuple["Component", str]] = []
        for exec_name, component in self.processor.components.items():
            for (
                listener_method_name,
                listener,
            ) in component._config.component_listeners.items():
                if self._is_match(
                    source_exec_name=self.component_exec_name,
                    event_name=self.event_name,
                    source_to=self._to,
                    destination_exec_name=component.exec_name,
                    destination_listener=listener,
                ):
                    execute_over.append((component, listener_method_name))

        # order components from top to bottom if message is send only to parents
        # this is required for proper handling of exceptions
        if self._to == "/**/.":
            execute_over.sort(key=lambda t: t[0]._config.hiearchy_level, reverse=True)
        for comp, listener_method_name in execute_over:
            self.processor.add_command(
                CallListenerCommand(comp.exec_name, listener_method_name, self.event)
            )

        if self.primary_execution:
            self.processor._emited_event_commands.append(self)

    @classmethod
    def _glob_match_exec_name(
        cls, pattern_exec_name, pattern, component_exec_name
    ) -> bool:
        """
        Check if glob pattern set by component with pattern_exec_name match
        with compoment_exec_name

        if pattern is:

            - None -> match to every initialised component
            - /compoent1.key1/compoent2.key2    -> compoenent with complete exec_name
            - *                               -> direct children with or without key
            - *.*                             -> direct children with any key
            - **/*                            -> all children with or without key
            - **/*.*                          -> all children with any key
            - component                       -> match to direct child named "component" without key
            - component.*                     -> match to direct child named "component" with any key
            - component.key                   -> match to direct child named "component with key equals "key"
            - **/component[.[*|<key>]]        -> match to child at any level
            - ..                                -> match to parent
            - ../component[.[*|<key>]]          -> match to sibling
            - /**/.                             -> match to parent at any level
            - /**/component[.[*|<key>]]/**/.    -> match to parent at any level named
            - //                                -> process event from root page
            - .                                 -> component that emited event
            - etc.
        """

        if pattern is None:
            # match any component
            return True

        if "/**/." in pattern:
            # reverse match for parent
            if pattern_exec_name == component_exec_name:
                return False
            if not pattern_exec_name.startswith(component_exec_name):
                return False
            if not pattern.startswith("/**/") or pattern == "/**/.":
                return True
            else:
                re_pattern = (
                    "(/{p}/)|(/{p}$)".format(
                        p=re.escape(
                            # removes /**/ from begining and /**/. from end
                            pattern[4:-5]
                        )
                    )
                    .replace(
                        "/\\*\\*/",
                        "((/.*/)|(/))",  # ** replace wit regex to match compoente path
                    )
                    .replace("\\*\\.\\*", "[^./]+\\.[^./]+")
                    .replace(
                        "\\.\\*", "\\.[^./]+"
                    )  # replace with regex to match any key
                    .replace("\\*", "[^/]*")  # replace to match compoent name
                )
                return re.search(re_pattern, pattern_exec_name) is not None
        else:
            # regular path match
            if pattern.startswith("/"):
                pass
            elif pattern == ".":
                pattern = pattern_exec_name
            elif not (pattern.startswith(".") or pattern.startswith("/")):
                pattern = "{}/{}".format(pattern_exec_name, pattern)
            elif pattern.startswith("./"):
                pattern = "{}{}".format(pattern_exec_name, pattern.lstrip("."))
            elif pattern.startswith(".."):
                pattern_begins = pattern_exec_name.lstrip("/").split("/")
                while pattern.startswith(".."):
                    pattern = pattern.lstrip(".").lstrip("/")
                    try:
                        pattern_begins = pattern_begins[:-1]
                    except KeyError:
                        # no parrent so no match
                        return False
                pattern = "/".join(["", *pattern_begins, pattern]).rstrip("/")

            re_pattern = (
                re.escape(pattern)
                .replace(
                    "/\\*\\*/",
                    "((/.*/)|(/))",  # ** replace wit regex to match component path
                )
                .replace("\\*\\.\\*", "[^./]+\\.[^./]+")
                .replace("\\.\\*", "\\.[^./]+")  # replace with regex to match any key
                .replace("\\*", "[^/]*")  # replace to match compoent name
            )
            return re.fullmatch(re_pattern, component_exec_name) is not None

    def __repr__(self):
        return "Emit({}, {}, {})".format(
            self.component_exec_name, self.event_name, self._to
        )

    def reemit_over(
        self, reemit_component_exec_name: str
    ) -> List["CallListenerCommand"]:
        reemit_component = self.processor.components[reemit_component_exec_name]
        commands = list()
        for (
            listener_method_name,
            listener,
        ) in reemit_component._config.component_listeners.items():
            if self._is_match(
                source_exec_name=self.component_exec_name,
                event_name=self.event_name,
                source_to=self._to,
                destination_exec_name=reemit_component_exec_name,
                destination_listener=listener,
            ):
                commands.append(
                    CallListenerCommand(
                        reemit_component.exec_name,
                        listener_method_name,
                        self.event,
                    )
                )
        return commands

    @classmethod
    def _is_match(
        cls,
        source_exec_name: str,
        event_name: str,
        source_to: Tuple[str, ...],
        destination_exec_name: str,
        destination_listener: "ComponentListener",
    ) -> bool:
        def __is_match(
            _source_to: str,
            listener_event_name: Optional[str],
            listener_source: Optional[str],
        ) -> bool:
            return (
                (
                    # if listener_event_name is None only catch user event but not
                    # jembe system events that starts with underscore (_)
                    (listener_event_name is None and not event_name.startswith("_"))
                    or listener_event_name == event_name
                )
                and cls._glob_match_exec_name(
                    # match emit.to with compoenent name
                    source_exec_name,
                    _source_to,
                    destination_exec_name,
                )
                and cls._glob_match_exec_name(
                    # match for compoennt filter on listener end
                    destination_exec_name,
                    listener_source,
                    source_exec_name,
                )
            )

        sources_to: tuple = tuple((None,)) if not source_to else source_to
        listener_events: tuple = (
            tuple((None,))
            if not destination_listener.event_names
            else destination_listener.event_names
        )
        listener_sources: tuple = (
            tuple((None,))
            if not destination_listener.sources
            else destination_listener.sources
        )

        for s_to in sources_to:
            for dl_event in listener_events:
                for dl_source in listener_sources:
                    if __is_match(s_to, dl_event, dl_source):
                        return True
        return False


class InitialiseCommand(Command):
    def __init__(
        self,
        component_exec_name: str,
        init_params: dict,
        merge_existing_params: bool = True,
        exist_on_client: bool = False,
    ):
        super().__init__(component_exec_name)
        self.init_params = {
            k: (v if not isinstance(v, Undefined) else None)
            for k, v in init_params.items()
        }
        self.merge_existing_params = merge_existing_params
        self.exist_on_client = exist_on_client

        self.initialised_component: Optional["Component"] = None
        self._cconfig: "ComponentConfig"

    def mount(self, processor: "Processor") -> "InitialiseCommand":
        self._cconfig = processor.jembe.get_component_config(self.component_exec_name)
        return super().mount(processor)

    @cached_property
    def _inject_into_params(self) -> Dict[str, Any]:
        parent_cconfig = self._cconfig.parent
        if parent_cconfig:
            parent_component = self.processor.components[
                parent_exec_name(self.component_exec_name)
            ]
            injected_params = (
                parent_component.inject_into(self._cconfig)
                if parent_component._jembe_inject_into_overriden
                else dict()
            )
            if parent_cconfig._inject_into_components:
                injected_params.update(
                    parent_cconfig._inject_into_components(
                        parent_component,
                        self._cconfig,
                    )
                )
            # clean up injected params
            if injected_params:
                injected_params = {
                    key: value
                    for key, value in injected_params.items()
                    if key in self._cconfig.component_class._jembe_init_param_names
                }
            return injected_params
        else:
            return dict()

    def _must_do_init(self, is_accessible_run: bool):
        if self.component_exec_name in self.processor.components:
            component = self.processor.components[self.component_exec_name]
            new_params = (
                {}
                if self.merge_existing_params
                else {**self._cconfig.component_class._jembe_state_param_default_values}
            )
            new_params.update(
                {**self.init_params, **self._inject_into_params, **component.inject()}
            )
            # if state params are same continue
            # else raise jembeerror until find better solution
            has_new_params = False
            for k, v in new_params.items():
                if k in component.state and v != component.state[k]:
                    has_new_params = True
                    break

            if component.has_action_or_listener_executed:
                if has_new_params:
                    if is_accessible_run:
                        return True
                    else:
                        raise JembeError(
                            (
                                "Cant reinitialise component {} with new parametes after "
                                "action or listener is executed by this component."
                            ).format(component.exec_name)
                        )
                else:
                    return False
            else:
                return has_new_params
        return True

    def execute(self, is_accessible_run=False):
        # create new component if component with identical exec_name does not exist
        # or component with identical exec_name has not action or listener executed
        if self._must_do_init(is_accessible_run):
            existing_component = self.processor.components.get(
                self.component_exec_name, None
            )
            existing_params = (
                {
                    k: v
                    for k, v in existing_component.state.items()
                    if k in existing_component.state._injected_params_names
                }
                if self.merge_existing_params and existing_component
                else dict()
            )
            init_params = (
                {}
                if self.merge_existing_params
                else {**self._cconfig.component_class._jembe_state_param_default_values}
            )
            init_params.update(
                {**existing_params, **self.init_params, **self._inject_into_params}
            )

            component = self._cconfig.component_class._jembe_init_(
                self._cconfig,
                self.component_exec_name,
                list(self._inject_into_params.keys()),
                self.merge_existing_params,
                **init_params
            )

            # check if action passes access control
            if not component.ac_check():
                raise ComponentConfig.DEFAULT_AC_EXCEPTION()

            self.initialised_component = component
            if not is_accessible_run:
                self.processor.components[component.exec_name] = component

                if self.exist_on_client:
                    self.processor.renderers[component.exec_name] = ComponentRender(
                        False,
                        component.state.tojsondict(component, True),
                        component._jembe_disabled_actions.copy(),
                        component.state._injected_params_names,
                        component.url,
                        component._config.changes_url,
                        None,
                    )

                if self.processor._emited_event_commands:
                    # we need to reemit commands to this component
                    for emited_command in self.processor._emited_event_commands:
                        reemit_commands = emited_command.reemit_over(
                            self.component_exec_name
                        )
                        for remit_cmd in reemit_commands:
                            self.processor.add_command(remit_cmd, end=True)
        else:
            self.initialised_component = self.processor.components[
                self.component_exec_name
            ]

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        return ()

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        return ()

    def __repr__(self):
        return "Init({})".format(self.component_exec_name)


class ComponentRender(NamedTuple):
    """represents rendered coponent html with additional parametars"""

    fresh: bool
    state_jsondict: Dict[str, Any]
    disabled_actions: List[str]
    injected_params: List[str]
    url: Optional[str]
    changes_url: bool
    html: Optional[str]


class CommandsQue:
    def __init__(self, jembe: "Jembe") -> None:
        self.commands: Deque["Command"] = deque()
        self.deferred_commands: Deque["Command"] = deque()

        self.jembe = jembe

    def add_command(self, command: "Command", end=False) -> None:
        """
        Adds new command into staginig commands que.
        if end is True command is added at the end of que (last to execute)

        Staging que exist in order to allow commands generated by while
        execution one command to be internally ordered by appending at
        the beginig or the end of staging que

        It also addes all before and after commands in staging que
        """
        if not command.is_mounted:
            raise JembeError("Cann't add unmounted command to commands que")

        def _do_add_command(que, command, end):
            """ Adds command with before and after command to stack"""
            before_emit_commands = command.get_before_emit_commands()

            if end:
                # adds to the end of que .. last to execute
                for before_cmd in before_emit_commands:
                    que.appendleft(before_cmd)

                que.appendleft(command)

            else:
                # adds at the begingin of que .. first to execute
                que.append(command)

                for before_cmd in reversed(before_emit_commands):
                    que.append(before_cmd)

        # Check if command should be deffered
        is_deferred_command = False
        if isinstance(command, CallActionCommand):
            try:
                cconfig = self.jembe.components_configs[command.component_full_name]
            except AttributeError:
                raise JembeError(
                    "Component {} does not exist".format(command.component_full_name)
                )
            try:
                caction = cconfig.component_actions[command.action_name]
            except AttributeError:
                raise JembeError(
                    "Action {} is not defined for component {}".format(
                        command.action_name, command.component_full_name
                    )
                )
            is_deferred_command = caction.deferred

        if is_deferred_command:
            _do_add_command(self.deferred_commands, command, end)
        else:
            _do_add_command(self.commands, command, end)

    def move_commands_to(self, que: Deque["Command"]) -> None:
        """Moves commands from staging que to execution que"""
        while self.deferred_commands:
            que.append(self.deferred_commands.popleft())
        while self.commands:
            que.append(self.commands.popleft())

    def clear(self) -> None:
        self.commands.clear()
        self.deferred_commands.clear()

    def __repr__(self) -> str:
        return "CommandsQue({}, defered={})".format(
            self.commands, self.deferred_commands
        )


class Processor:
    """
    1. Will use deapest component.url from all components on the page as window.location
    2. When any component action or listener returns False default action
       (display) will not be called
    """

    def __init__(self, jembe: "Jembe", component_full_name: str, request: "Request"):
        g.jmb_processor = self

        self.jembe = jembe
        self.request = request

        self.components: Dict[str, "Component"] = dict()
        self._commands: Deque["Command"] = deque()
        # already emited and processed event commands
        # that will be executed over newelly initialised component
        self._emited_event_commands: Deque["EmitCommand"] = deque()
        # commands created while executing some command and that needs to be
        # added to commands at the end of command execution
        self._staging_commands = CommandsQue(self.jembe)
        # component renderers is dict[exec_name] = (componentState, url, rendered_str)
        self.renderers: Dict[str, "ComponentRender"] = dict()
        # component that raised exception on initialise
        # any subsequent command on this component should be ignored
        self._raised_exception_on_initialise: Dict[str, dict] = dict()
        # direct response if component display returns it
        self._response: Optional["Response"] = None

        self.__create_commands(component_full_name)
        self._staging_commands.move_commands_to(self._commands)

    def add_command(self, command: "Command", end=False) -> None:
        self._staging_commands.add_command(
            command if command.is_mounted else command.mount(self), end
        )

    def _load_init_params(self, exec_name: str, init_params: dict) -> dict:
        component_config = self.jembe.get_component_config(exec_name)
        component_class = component_config.component_class

        load_params = dict()
        for param_name, param_value in init_params.items():
            load_params[param_name] = component_class.load_init_param(
                component_config, param_name, param_value
            )
        return load_params

    def _x_jembe_command_factory(
        self, command_data: dict, is_component: bool = False
    ) -> "Command":
        """Process data received by json and build commands

        is_component - mark that command_data is received in components section of x-jembe request
                    describing current compoents and their state displayed to the user
        """

        if is_component:
            return InitialiseCommand(
                command_data["execName"],
                self._load_init_params(command_data["execName"], command_data["state"]),
                exist_on_client=True,
            )
        elif command_data["type"] == "init":
            return InitialiseCommand(
                command_data["componentExecName"],
                self._load_init_params(
                    command_data["componentExecName"], command_data["initParams"]
                ),
                merge_existing_params=command_data["mergeExistingParams"],
            )
        elif (
            command_data["type"] == "call"
            and command_data["actionName"] == ComponentConfig.DEFAULT_DISPLAY_ACTION
        ):
            return CallDisplayCommand(command_data["componentExecName"])
        elif (
            command_data["type"] == "call"
            and command_data["actionName"] != ComponentConfig.DEFAULT_DISPLAY_ACTION
        ):
            return CallActionCommand(
                command_data["componentExecName"],
                command_data["actionName"],
                command_data["args"],
                command_data["kwargs"],
            )
        elif command_data["type"] == "emit":
            return EmitCommand(
                command_data["componentExecName"],
                command_data["eventName"],
                command_data["params"],
                command_data["to"],
            )
        raise NotImplementedError()

    def __create_commands(self, component_full_name: str):
        if self._is_x_jembe_request:
            # x-jembe ajax request
            data = json.loads(self.request.data)
            # init components from data["components"]
            to_be_initialised = []
            for component_data in data["components"]:
                self.add_command(
                    self._x_jembe_command_factory(component_data, is_component=True),
                    end=True,
                )
                to_be_initialised.append(component_data["execName"])
            # init components from url_path if thay doesnot exist in data["compoenents"]
            self.__create_commands_from_url_path(component_full_name, to_be_initialised)

            # init commands
            for command_data in data["commands"]:
                self.add_command(self._x_jembe_command_factory(command_data), end=True)
        else:
            # regular http/s GET request
            exec_names = self.__create_commands_from_url_path(
                component_full_name, list()
            )

            self.add_command(
                CallDisplayCommand(exec_names[-1]),
                end=True,
            )
            for exec_name in exec_names[:-1]:
                self.add_command(
                    CallDisplayCommand(exec_name),
                    end=True,
                )

    def __create_commands_from_url_path(
        self, component_full_name: str, to_be_initialised: List[str]
    ) -> List[str]:
        """
        inits components from request url_path
        if component with same exec_name is not already initialised

        returns exec names from root to component_full_name
        """
        from .component import Component

        exec_names = []

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
            if exec_name not in to_be_initialised:
                init_params = {
                    up.name: self.request.view_args[up.identifier]
                    for up in cconfig._url_params
                }
                if (
                    not self._is_x_jembe_request
                    and exec_name_to_full_name(exec_name) == component_full_name
                ):
                    # do mapping for get query url params
                    for (
                        url_param_name,
                        state_param_name,
                    ) in cconfig.url_query_params.items():
                        value = self.request.args.get(url_param_name, None)
                        if value is not None:
                            try:
                                init_params[
                                    state_param_name
                                ] = convert_to_annotated_type(
                                    unquote_plus(self.request.args[url_param_name]),
                                    cconfig.component_class._jembe_init_signature.parameters[
                                        state_param_name
                                    ],
                                )
                            except ValueError:
                                pass

                self.add_command(
                    self._x_jembe_command_factory(
                        dict(
                            type="init",
                            componentExecName=exec_name,
                            initParams=init_params,
                            mergeExistingParams=True,
                        )
                    ),
                    end=True,
                )
            exec_names.append(exec_name)

        return exec_names

    def process_request(self) -> "Processor":
        try:
            response = self._execute_commands()

            if response is not None:
                self._delete_tmp_uploads()
                self._response = response
                return self

            # for all freshly rendered component who does not have parent renderers
            # eather at client (send via x-jembe.components) nor just created by
            # server call display command
            needs_render_exec_names = set(
                chain.from_iterable(
                    accumulate(
                        map(lambda x: "/" + x, exec_name.strip("/").split("/")), add
                    )
                    for exec_name, cr in self.renderers.items()
                    if cr.fresh == True
                )
            )
            missing_render_exec_names = needs_render_exec_names - set(
                self.renderers.keys()
            )
            for exec_name in sorted(
                missing_render_exec_names,
                key=lambda exec_name: self.components[exec_name]._config.hiearchy_level,
            ):
                self.add_command(CallDisplayCommand(exec_name))
            self._staging_commands.move_commands_to(self._commands)

            self._execute_commands()
            return self

        finally:
            self._delete_tmp_uploads()

    def _execute_commands(self) -> Optional["Response"]:
        """executes all commands from self._commands que"""
        while self._commands:
            response = self._execute_command(self._commands.pop())
            if response is not None:
                return response
        return None

    def _execute_command(self, command: "Command") -> Optional["Response"]:
        # command is over component that raised exception on initialise and
        # it is not new initialise command over that commponent, so we skip its execution
        if command.component_exec_name in self._raised_exception_on_initialise:
            if (
                isinstance(command, InitialiseCommand)
                and command.init_params
                == self._raised_exception_on_initialise[command.component_exec_name]
            ):
                return None
            if (
                not isinstance(command, InitialiseCommand)
                and command.component_exec_name not in self.components
            ):
                return None

        try:
            response = command.execute()
            self._staging_commands.move_commands_to(self._commands)
            if response is not None:
                return response
        except JembeError as jmberror:
            # JembeError are exceptions raised by jembe
            # and thay indicate bad usage of framework and
            # thay should not be raised in production
            raise jmberror
        except Exception as exc:
            self._handle_exception_in_command(command, exc)
            return None
        else:
            # If execution of command is successfull then
            # add after commands into command que
            for after_cmd in reversed(command.get_after_emit_commands()):
                self.add_command(after_cmd)
            self._staging_commands.move_commands_to(self._commands)
            return None

    def execute_initialise_command_successfully(
        self, command: "InitialiseCommand", *additional_components: "Component"
    ) -> Tuple[bool, Optional["Component"]]:
        """
        Directly out of commands que execute initialise command
        in order to check will it raise Exception

        no additional after or before commands will be executed
        """
        # check if component with requested full_name exist or if
        # initialisation with same init_params already failed
        if exec_name_to_full_name(
            command.component_exec_name
        ) not in self.jembe.components_configs or (
            command.component_exec_name in self._raised_exception_on_initialise
            and (
                command.init_params
                == self._raised_exception_on_initialise[command.component_exec_name]
            )
        ):
            return (False, None)

        # execute initialise command without running before or after commands
        backup_current_staging_commands = self._staging_commands
        self._staging_commands = CommandsQue(self.jembe)
        backup_current_components = self.components.copy()
        # add additional components into components
        for acomp in additional_components:
            self.components[acomp.exec_name] = acomp

        cmd: "InitialiseCommand" = (
            command if command.is_mounted else command.mount(self)
        )
        try:
            cmd.execute(is_accessible_run=True)
        except JembeError as jmb_error:
            # JembeError are exceptions raised by jembe
            # and thay indicate bad usage of framework
            self.components = backup_current_components
            raise jmb_error
        except Exception as exc:
            self._raised_exception_on_initialise[cmd.component_exec_name] = deepcopy(
                cmd.init_params
            )
            # initalise command is not run properly

            # restore _staging_commands
            self._staging_commands = backup_current_staging_commands
            self.components = backup_current_components
            if current_app.debug or current_app.testing:
                # import traceback
                # traceback.print_exc()
                current_app.logger.warning(
                    "Exception when initialising component out of proccessing que {}: {}".format(
                        cmd, exc.__repr__()
                    )
                )
            return (False, None)
        self._staging_commands = backup_current_staging_commands
        self.components = backup_current_components
        return (True, cmd.initialised_component)

    def _handle_exception_in_command(self, command: "Command", exc: "Exception"):
        """
        Exception that ocure while executing command (call action, display, listener invocation etc)
        are handled in following way.

        Event('_exception', source=command.component_exec_name, params=dict(exception=exc, handled=False)) is created
        and emited to all its parent components from top to bottom.
        This is only time when ordering for receiving messages is guaranted, so that root components can know if
        exception is already handled by its children.

        Parent component can use regular listener to catch event do whatever thay want. @listener('_exception')
        If any of parrent compoennt mark event as handled event.params["handled"] = True exception will not be raised again.

        If there is not listener for _exception event in parent compoent or exception event is not handled. Processor
        will rerise exception and it will be handled like regular flask exception.
        """
        # Clear all staging commands because command has raised exception
        self._staging_commands.clear()

        # Create emit command to emit exception to component parents
        emit_command = (
            EmitCommand(
                command.component_exec_name,
                SystemEvents.EXCEPTION.value,
                dict(
                    exception=exc,
                    handled=False,
                    in_action=command.action_name
                    if isinstance(command, CallActionCommand)
                    else None,
                ),
            )
            .to((".", "/**/."))
            .mount(self)
        )
        emit_command.execute()
        # self._staging_commands is fill with calllistener commands
        # move it to exception_commands que that will be used
        # to process exception
        exception_commands: Deque["Command"] = deque()
        self._staging_commands.move_commands_to(exception_commands)
        # executes commands from exception_commands que and
        # all new generated commands will be saved in now empty
        # staging_commands que
        while exception_commands:
            # simple loop no catchin exception when handlin exception
            # commands from exception commands dont have after command
            cmd = exception_commands.pop()
            # if exception is raised during handling exception ... dont try to catch it :)
            cmd.execute()
            self._staging_commands.move_commands_to(exception_commands)

        if not emit_command.event.params["handled"]:
            # if exception is not handled by parent components
            # rerise exception
            current_app.logger.error(
                "Unhandled exception in {}: {}".format(command, exc)
            )
            raise emit_command.event.params["exception"]

        # if exception is handled dont raise exception
        if isinstance(command, InitialiseCommand):
            # save initialises command that raised exception with params
            # so we can skip executing other commants on this component
            # (save to skip execution because we handled exception)
            self._raised_exception_on_initialise[
                command.component_exec_name
            ] = deepcopy(command.init_params)

    def build_response(self) -> "Response":
        if self._response:
            return self._response
        # compose full page
        if self._is_x_jembe_request:
            ajax_responses = []
            for (
                exec_name,
                (
                    fresh,
                    state_jsondict,
                    disabled_actions,
                    injected_params_names,
                    url,
                    changes_url,
                    html,
                ),
            ) in self.renderers.items():
                if fresh:
                    ajax_responses.append(
                        dict(
                            execName=exec_name,
                            state={
                                k: v
                                for k, v in state_jsondict.items()
                                if k not in injected_params_names
                            },
                            dom=html,
                            url=url,
                            changesUrl=changes_url,
                            actions={
                                action_name: action_name not in disabled_actions
                                for action_name in self.jembe.get_component_config(
                                    exec_name
                                ).component_actions.keys()
                                if action_name != ComponentConfig.DEFAULT_DISPLAY_ACTION
                            },
                        )
                    )
            return jsonify(ajax_responses)
        else:
            # for page with components build united response
            c_etrees = {
                exec_name: self._lxml_add_dom_attrs(
                    html,
                    exec_name,
                    {
                        k: v
                        for k, v in state_jsondict.items()
                        if k not in injected_params_names
                    },
                    url,
                    changes_url,
                    disabled_actions,
                )
                for exec_name, (
                    fresh,
                    state_jsondict,
                    disabled_actions,
                    injected_params_names,
                    url,
                    changes_url,
                    html,
                ) in self.renderers.items()
                if fresh
                and state_jsondict is not None
                and url is not None
                and html is not None
            }
            unused_exec_names = sorted(
                c_etrees.keys(),
                key=lambda exec_name: self.components[exec_name]._config.hiearchy_level,
            )
            response_etree = None
            can_find_placeholder = True
            while unused_exec_names and can_find_placeholder:
                can_find_placeholder = False
                if response_etree is None:
                    response_etree = c_etrees[unused_exec_names.pop(0)]
                # compose response including all components not just page
                # find all placeholders in response_tree and replace them with
                # appropriate etrees
                for placeholder in response_etree.xpath(
                    ".//template[@jmb-placeholder]"
                ):
                    can_find_placeholder = True
                    exec_name = placeholder.attrib["jmb-placeholder"]
                    try:
                        c_etree = c_etrees[exec_name]
                        unused_exec_names.pop(unused_exec_names.index(exec_name))
                        placeholder.addnext(c_etree)
                        placeholder.getparent().remove(placeholder)
                    except KeyError:
                        # exec_name referenced by this placeholder does not exist
                        # so we will just remove placeholder
                        # This situation can ocure when handling exceptions
                        # of child components but not changing display html
                        # so we can assume that developer just want to ignore
                        # exception and dont display component that coused exception
                        placeholder.getparent().remove(placeholder)
            # Remove empty placeholder if thay are left in response
            # because above logic will not find all empty placeholders
            if response_etree is not None:
                for placeholder in response_etree.xpath(
                    ".//template[@jmb-placeholder]"
                ):
                    placeholder.getparent().remove(placeholder)
            return etree.tostring(response_etree, method="html")

    def _lxml_add_dom_attrs(
        self,
        html: str,
        exec_name: str,
        state_jsondict: Dict[str, Any],
        url: str,
        changes_url: bool,
        disabled_actions: List[str],
    ):  # -> "lxml.html.HtmlElement":
        """
        Adds dom attrs to html.
        If html has one root tag attrs are added to that tag othervise
        html is souranded with div
        """

        def set_jmb_attrs(elem):
            elem.set("jmb-name", exec_name)
            elem.set(
                "jmb-data",
                json.dumps(
                    dict(
                        actions={
                            action_name: action_name not in disabled_actions
                            for action_name in self.jembe.get_component_config(
                                exec_name
                            ).component_actions.keys()
                            if action_name != ComponentConfig.DEFAULT_DISPLAY_ACTION
                        },
                        changesUrl=changes_url,
                        state=state_jsondict,
                        url=url,
                    ),
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            )

        if not html:
            html = "<div></div>"
        root = etree.HTML(html)
        if is_page_exec_name(exec_name):
            # exec_name is fom page component, component with no parent
            doc = root.getroottree()
            set_jmb_attrs(root)
            return doc
        else:
            doc = root[0]
            if (
                len(root[0]) == 1
                and "jmb-placeholder" not in root[0][0].attrib
                and "jmb-name" not in root[0][0].attrib
            ):
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

    @cached_property
    def _is_x_jembe_request(self) -> bool:
        return bool(
            self.request.headers.has_key(self.jembe.X_JEMBE)
            and self.request.headers.get(self.jembe.X_JEMBE) != "upload"
        )

    @cached_property
    def _is_x_jembe_upload_followup_request(self) -> bool:
        return self._is_x_jembe_request and self.request.headers.has_key(
            self.jembe.X_RELATED_UPLOAD
        )

    @cached_property
    def is_x_jembe_upload_request(self) -> bool:
        return bool(self.request.headers.get(self.jembe.X_JEMBE, None) == "upload")

    def _delete_tmp_uploads(self):
        from jembe.app import get_temp_storage

        if self._is_x_jembe_upload_followup_request:
            upload_request_id = self.request.headers.get(self.jembe.X_RELATED_UPLOAD)
            ts = get_temp_storage()
            try:
                ts.rmtree(ts.path_join("uploads", upload_request_id))
            except:
                # TODO log error
                pass
            try:
                ts.rmdir("uploads")
            except:
                pass

    def remove_component(self, exec_name: str, only_children: bool = False):
        def match_exec_name(match: str) -> bool:
            if match.startswith("{}/".format(exec_name)):
                return True
            if only_children == False and match == exec_name:
                return True
            return False

        self._commands = deque(
            (
                c
                for c in self._commands
                if not match_exec_name(c.component_exec_name)
                or isinstance(c, EmitCommand)
            )
        )
        self.renderers = {
            en: r for en, r in self.renderers.items() if not match_exec_name(en)
        }
        self.components = {
            en: c for en, c in self.components.items() if not match_exec_name(en)
        }
