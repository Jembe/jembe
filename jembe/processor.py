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
from flask.globals import current_app
from jinja2 import Undefined
from lxml import etree
from lxml.html import Element
from flask import json, jsonify, Response
from .common import exec_name_to_full_name, is_page_exec_name, parent_exec_name
from .exceptions import JembeError
from .component_config import ComponentConfig, CConfigRedisplayFlag as RedisplayFlag


if TYPE_CHECKING:  # pragma: no cover
    from .app import Jembe
    from flask import Request
    from .component import Component, ComponentState
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
            return exec_name_to_full_name(self.source_full_name)

    @cached_property
    def source_name(self) -> str:
        if self.source and self.source._config.name:
            return self.source._config.name
        else:
            return exec_name_to_full_name(self.source_full_name).split("/")[-1]


class SystemEvents(Enum):
    # before calling display action
    DISPLAYING = "_displaying"
    # after display action is executed
    DISPLAY = "_display"
    # before initialising component
    INITIALISING = "_initialising"
    # after component has been initialised
    INIT = "_init"
    # before calling component action including display action
    CALLING = "_calling"
    # after component action (including display action) has beend executed
    CALL = "_call"
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

    def execute(self):
        component = self.processor.components[self.component_exec_name]
        cconfig = component._config
        if self.action_name not in cconfig.component_actions:
            raise JembeError(
                "Action {}.{} does not exist or is not marked as public action".format(
                    cconfig.full_name, self.action_name
                )
            )

        # execute action
        action_result = getattr(component, self.action_name)(*self.args, **self.kwargs)
        # process action result
        if action_result is None or (
            isinstance(action_result, bool) and action_result == True
        ):
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
                    cconfig.full_name, self.action_name, action_result,
                )
            )

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        return [
            EmitCommand(
                self.component_exec_name,
                SystemEvents.CALLING.value,
                dict(action=self.action_name),
            ).mount(self.processor),
        ]

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        return [
            EmitCommand(
                self.component_exec_name,
                SystemEvents.CALL.value,
                dict(action=self.action_name),
            ).mount(self.processor),
        ]

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

    def execute(self):
        component = self.processor.components[self.component_exec_name]
        cconfig = component._config

        if self.component_exec_name in self.processor.renderers and not (
            self.force
            or RedisplayFlag.WHEN_ON_PAGE in cconfig.redisplay
            or RedisplayFlag.WHEN_DISPLAY_EXECUTED in cconfig.redisplay
            or (
                RedisplayFlag.WHEN_STATE_CHANGED in cconfig.redisplay
                and self.processor.renderers[self.component_exec_name].state
                != component.state
            )
        ):
            # if compoent is already displayed/rendered in same state and no force is set
            # no need to execute display again because it should return same result
            return

        # execute action
        action_result = getattr(component, self.action_name)(*self.args, **self.kwargs)
        # process action result
        if isinstance(action_result, str):
            # save component display responses in memory
            # Add component html to processor rendererd
            self.processor.renderers[self.component_exec_name] = ComponentRender(
                True,
                component.state.deepcopy(),
                component.url,
                component._config.changes_url,
                action_result,
            )
        elif isinstance(action_result, Response):
            # TODO If self.component is component directly requested via http request
            # and it is not x-jembe request return respon
            # othervise raise JembeError
            raise NotImplementedError()
        elif not isinstance(action_result, str):
            # Display should return html string if not raise JembeError
            raise JembeError(
                "{} action of {} shuld return html string not {}".format(
                    ComponentConfig.DEFAULT_DISPLAY_ACTION,
                    cconfig.full_name,
                    action_result,
                )
            )
        else:
            raise JembeError(
                "Invalid display result type: {}.{} {}".format(
                    cconfig.full_name, self.action_name, action_result,
                )
            )

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        commands = list(super().get_before_emit_commands())
        commands.append(
            EmitCommand(
                self.component_exec_name,
                SystemEvents.DISPLAYING.value,
                dict(action=self.action_name),
            ).mount(self.processor)
        )
        return commands

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        commands = list(super().get_after_emit_commands())
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
        self, component_exec_name: str, listener_name: str, event: "Event",
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
                    cconfig.full_name, self.listener_name, listener_result,
                )
            )

    def __repr__(self):
        return "CallListener({},{})".format(
            self.component_exec_name, self.listener_name
        )


class EmitCommand(Command):
    # TODO match listner extract as method
    def __init__(
        self, component_exec_name: str, event_name: str, params: dict,
    ):
        super().__init__(component_exec_name)
        self.event_name = event_name
        self.params = params
        self._to: Tuple[str, ...] = ()

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
            - ./*                               -> direct children with or without key
            - ./*.*                             -> direct children with any key
            - ./**/*                            -> all children with or without key
            - ./**/*.*                          -> all children with any key
            - ./component                       -> match to direct child named "component" without key
            - ./component.*                     -> match to direct child named "component" with any key
            - ./component.key                   -> match to direct child named "component with key equals "key"
            - ./**/component[.[*|<key>]]        -> match to child at any level
            - ..                                -> match to parent
            - ../component[.[*|<key>]]          -> match to sibling 
            - /**/.                             -> match to parent at any level
            - /**/component[.[*|<key>]]/**/.    -> match to parent at any level named
            - //                                -> process event from root page
            - etc.
        """

        if pattern is None:
            # match any compoennt
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
                    "((/.*/)|(/))",  # ** replace wit regex to match compoente path
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
                        reemit_component.exec_name, listener_method_name, self.event,
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
                (listener_event_name is None or listener_event_name == event_name)
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
        listener_events: tuple = tuple(
            (None,)
        ) if not destination_listener.event_names else destination_listener.event_names
        listener_sources: tuple = tuple(
            (None,)
        ) if not destination_listener.sources else destination_listener.sources

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
        exist_on_client: bool = False,
    ):
        super().__init__(component_exec_name)
        self.init_params = {
            k: (v if not isinstance(v, Undefined) else None)
            for k, v in init_params.items()
        }
        self.exist_on_client = exist_on_client

        self._cconfig: "ComponentConfig"
        self._inject_into_params: Dict[str, Any]

    @cached_property
    def _must_do_init(self):

        self._cconfig = self.processor.jembe.get_component_config(
            self.component_exec_name
        )
        parent_cconfig = self._cconfig.parent
        self._inject_into_params = (
            parent_cconfig._inject_into_components(
                self.processor.components[parent_exec_name(self.component_exec_name)],
                self._cconfig,
            )
            if parent_cconfig and parent_cconfig._inject_into_components
            else dict()
        )

        if self.component_exec_name in self.processor.components:
            new_params = {**self.init_params, **self._inject_into_params}
            # if state params are same continue
            # else raise jembeerror until find better solution
            component = self.processor.components[self.component_exec_name]
            raise JembeError(str(new_params))
            for key, value in component.state.items():
                if key in new_params and value != new_params[key]:
                    # TODO reinitialise component if it is not displayed/mounted (any action called including display)???
                    # what to do with children components?? do thay needs to be reinitialised
                    # can I just change state param?? Will some logic needs to be executed when changing state params I don't know?
                    # Only way to change state params from outside params should be during initialisation
                    # but does that mean that we need some kind of clean method to release resources when doing reinitialisation?
                    # will clean method complicated api to much ?
                    # TODO why this method dont fall more offten.. with current tests??
                    # no i cannot to this simple test if part of the params are changed .. must do all of them including
                    # default ones that is whay test not faling as it should
                    raise JembeError(
                        "Initialising component with different state params from existing compoenent {}".format(
                            component
                        )
                    )
            return False
        return True

    def execute(self):
        # create new component if component with identical exec_name
        # does not exist
        if self._must_do_init:
            # Instance createion by excplictly calling __new__ and __init__
            # becouse _config should be avaiable in __init__
            parent_cconfig = self._cconfig.parent
            inject_into = (
                parent_cconfig._inject_into_components(
                    self.processor.components[
                        parent_exec_name(self.component_exec_name)
                    ],
                    self._cconfig,
                )
                if parent_cconfig and parent_cconfig._inject_into_components
                else dict()
            )
            component = object.__new__(self._cconfig.component_class)
            component._config = self._cconfig
            component._jembe_injected_into = inject_into
            component.__init__(**self.init_params)  # type:ignore

            component.exec_name = self.component_exec_name
            self.processor.components[component.exec_name] = component

            if self.exist_on_client:
                self.processor.renderers[component.exec_name] = ComponentRender(
                    False,
                    component.state.deepcopy(),
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

    def get_before_emit_commands(self) -> Sequence["EmitCommand"]:
        return (
            (
                EmitCommand(
                    self.component_exec_name,
                    SystemEvents.INITIALISING.value,
                    dict(init_params=self.init_params, _config=self._cconfig),
                ).mount(self.processor),
            )
            if self._must_do_init
            else ()
        )

    def get_after_emit_commands(self) -> Sequence["EmitCommand"]:
        return (
            (
                EmitCommand(
                    self.component_exec_name, SystemEvents.INIT.value, dict(),
                ).mount(self.processor),
            )
            if self._must_do_init
            else ()
        )

    def __repr__(self):
        return "Init({})".format(self.component_exec_name)


class ComponentRender(NamedTuple):
    """represents rendered coponent html with additional parametars"""

    fresh: bool
    state: "ComponentState"
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


class Processor:
    """
    1. Will use deapest component.url from all components on the page as window.location
    2. When any component action or listener returns False default action 
       (display) will not be called 
    """

    def __init__(self, jembe: "Jembe", component_full_name: str, request: "Request"):
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

        self.__create_commands(component_full_name)
        self._staging_commands.move_commands_to(self._commands)

    def add_command(self, command: "Command", end=False) -> None:
        self._staging_commands.add_command(
            command if command.is_mounted else command.mount(self), end
        )

    def _decode_init_params(self, exec_name: str, init_params: dict) -> dict:
        component_class = self.jembe.get_component_config(exec_name).component_class

        decoded_params = dict()
        for param_name, param_value in init_params.items():
            decoded_params[param_name] = component_class.decode_param(
                param_name, param_value
            )
        return decoded_params

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
                self._decode_init_params(
                    command_data["execName"], command_data["state"]
                ),
                exist_on_client=True,
            )
        elif command_data["type"] == "init":
            return InitialiseCommand(
                command_data["componentExecName"],
                self._decode_init_params(
                    command_data["componentExecName"], command_data["initParams"]
                ),
            )
        elif (
            command_data["type"] == "call"
            and command_data["actionName"] == ComponentConfig.DEFAULT_DISPLAY_ACTION
        ):
            return CallDisplayCommand(command_data["componentExecName"],)
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
        raise NotImplementedError()

    def __create_commands(self, component_full_name: str):
        if self._is_x_jembe_request():
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
                CallDisplayCommand(exec_names[-1]), end=True,
            )
            for exec_name in exec_names[:-1]:
                self.add_command(
                    CallDisplayCommand(exec_name), end=True,
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
                self.add_command(
                    self._x_jembe_command_factory(
                        dict(
                            type="init",
                            componentExecName=exec_name,
                            initParams=init_params,
                        )
                    ),
                    end=True,
                )
            exec_names.append(exec_name)

        return exec_names

    def process_request(self) -> "Processor":
        self._execute_commands()
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
            key=lambda exec_name: self.components[exec_name]._config.hiearchy_level,
        ):
            self.add_command(CallDisplayCommand(exec_name))
        self._staging_commands.move_commands_to(self._commands)

        self._execute_commands()

        return self

    def _execute_commands(self):
        """executes all commands from self._commands que"""
        while self._commands:
            # print(self._commands)
            self._execute_command(self._commands.pop())

    def _execute_command(self, command: "Command"):
        # command is over component that raised exception on initialise and
        # it is not new initialise command over that commponent, so we skip its execution
        if command.component_exec_name not in self._raised_exception_on_initialise or (
            isinstance(command, InitialiseCommand)
            and command.init_params
            != self._raised_exception_on_initialise[command.component_exec_name]
        ):
            try:
                command.execute()
                self._staging_commands.move_commands_to(self._commands)
            except JembeError as jmberror:
                # JembeError are exceptions raised by jembe
                # and thay indicate bad usage of framework and
                # thay should not be raised in production
                raise jmberror
            except Exception as exc:
                self._handle_exception_in_command(command, exc)
            else:
                # If execution of command is successfull then
                # add after commands into command que
                for after_cmd in reversed(command.get_after_emit_commands()):
                    self.add_command(after_cmd)

    def execute_initialise_command_successfully(
        self, command: "InitialiseCommand"
    ) -> bool:
        """
        Directly out of commands que execute initialise command
        in order to check will it raise Exception

        if initialise is successfull all before and after commands should be executed.
        """

        if exec_name_to_full_name(
            command.component_exec_name
        ) not in self.jembe.components_configs or (
            command.component_exec_name in self._raised_exception_on_initialise
            and (
                command.init_params
                == self._raised_exception_on_initialise[command.component_exec_name]
            )
        ):
            # component does not exist (component_config with requested full_name does not exist)
            # or initailisation of component with same init_params already failed
            return False

        backup_current_staging_commands = self._staging_commands
        self._staging_commands = CommandsQue(self.jembe)

        local_que: Deque["Command"] = deque()
        local_que.append(command if command.is_mounted else command.mount(self))
        for emit_cmd in command.get_before_emit_commands():
            local_que.append(emit_cmd)

        while local_que:
            # execute command without handling exception
            cmd: "Command" = local_que.pop()
            try:
                cmd.execute()
                self._staging_commands.move_commands_to(local_que)
            except JembeError as jmberror:
                # JembeError are exceptions raised by jembe
                # and thay indicate bad usage of framework
                raise jmberror
            except Exception as exc:
                if (
                    cmd.component_exec_name == command.component_exec_name
                    and isinstance(cmd, InitialiseCommand)
                ):
                    self._raised_exception_on_initialise[
                        cmd.component_exec_name
                    ] = deepcopy(cmd.init_params)
                    # initalise command is not run properly
                    # becouse this is check we are not running
                    # exception listeners

                    # restore _staging_commands
                    self._staging_commands = backup_current_staging_commands
                    if current_app.debug or current_app.testing:
                        current_app.logger.exception(
                            "Exception when initialising component out of proccessing que {}: {}".format(
                                cmd, exc
                            )
                        )
                    return False
                # Before or after command raised exception
                # this should not happend and that indicated bug so
                # just reraise exception
                raise exc
            else:
                # If execution of init command is successfull then
                # add after commands into command que
                for after_cmd in reversed(cmd.get_after_emit_commands()):
                    local_que.append(after_cmd)

        self._staging_commands = backup_current_staging_commands
        return True

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

        # Clear all staging commands becouse command has raised exception
        self._staging_commands.clear()

        # Create emit command to emit exception to component parents
        emit_command = (
            EmitCommand(
                command.component_exec_name,
                SystemEvents.EXCEPTION.value,
                dict(exception=exc, handled=False),
            )
            .to("/**/.")
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
        # compose full page
        if self._is_x_jembe_request():
            ajax_responses = []
            for (
                exec_name,
                (fresh, state, url, changes_url, html),
            ) in self.renderers.items():
                if fresh:
                    ajax_responses.append(
                        dict(
                            execName=exec_name,
                            state=state.tojsondict(
                                self.jembe.get_component_config(
                                    exec_name
                                ).component_class
                            ),
                            dom=html,
                            url=url,
                            changes_url=changes_url,
                        )
                    )
            return jsonify(ajax_responses)
        else:
            # for page with components build united response
            c_etrees = {
                exec_name: self._lxml_add_dom_attrs(
                    html, exec_name, state, url, changes_url
                )
                for exec_name, (
                    fresh,
                    state,
                    url,
                    changes_url,
                    html,
                ) in self.renderers.items()
                if fresh and state is not None and url is not None and html is not None
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
                    ".//jmb-placeholder[@exec-name]"
                ):
                    can_find_placeholder = True
                    exec_name = placeholder.attrib["exec-name"]
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
                    ".//jmb-placeholder[@exec-name]"
                ):
                    placeholder.getparent().remove(placeholder)
            return etree.tostring(response_etree, method="html")

    def _lxml_add_dom_attrs(
        self,
        html: str,
        exec_name: str,
        state: "ComponentState",
        url: str,
        changes_url: bool,
    ):  # -> "lxml.html.HtmlElement":
        """
        Adds dom attrs to html.
        If html has one root tag attrs are added to that tag othervise
        html is souranded with div
        """

        def set_jmb_attrs(elem):
            elem.set("jmb:name", exec_name)
            elem.set(
                "jmb:data",
                json.dumps(
                    dict(
                        state=state.tojsondict(
                            self.jembe.get_component_config(exec_name).component_class
                        ),
                        url=url,
                        changes_url=changes_url,
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

    def _is_x_jembe_request(self) -> bool:
        return bool(self.request.headers.get(self.jembe.X_JEMBE, False))

