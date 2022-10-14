from re import T
from typing import (
    Callable,
    Iterable,
    TYPE_CHECKING,
    Optional,
    Type,
    Dict,
    List,
    Tuple,
    Union,
    Sequence,
    NewType,
)
from abc import ABCMeta
from enum import Enum
from itertools import accumulate
from operator import add
from inspect import getmembers, isfunction, signature, Parameter

from jembe.common import import_by_name
from .exceptions import AccessDenied, JembeError
from flask import url_for

if TYPE_CHECKING:  # pragma: no cover
    import inspect
    import jembe
    from .component import ComponentState

UrlPath = NewType("UrlPath", str)


class UrlConvertor(Enum):
    STR0 = "string(minlength=0)"
    STR = "string"
    PATH = "path"
    INT = "int"
    FLOAT = "float"
    UUID = "uuid"


def calc_url_param_identifier(name: str, level: int):
    return name if level == 0 else f"{name}__{level}"


class UrlParamDef:
    def __init__(
        self,
        name: str,
        convertor: Optional["UrlConvertor"] = None,
        identifier: Optional[str] = None,
    ):
        self.name = name
        self.identifier = name if not identifier else identifier
        self.convertor = convertor if convertor else UrlConvertor.STR

    @classmethod
    def from_inspect_parameter(
        cls, param: "inspect.Parameter", level: int
    ) -> "UrlParamDef":
        convertor = UrlConvertor.STR
        if param.annotation.__name__ == "int":
            convertor = UrlConvertor.INT
        elif param.annotation.__name__ == "str":
            convertor = UrlConvertor.STR
        elif param.annotation.__name__ == "float":
            convertor = UrlConvertor.FLOAT
        elif param.annotation.__name__ == "UUID":
            convertor = UrlConvertor.UUID
        elif param.annotation.__name__ == "UrlPath":
            convertor = UrlConvertor.PATH
        return UrlParamDef(
            param.name, convertor, calc_url_param_identifier(param.name, level)
        )

    @property
    def url_pattern(self) -> str:
        return f"<{self.convertor.value}:{self.identifier}>"

    def __repr__(self):
        return self.url_pattern


def action(
    _method=None,
    *,
    deferred=False,
    # deferred_after: Optional[str] = None,
    # deferred_before: Optional[str] = None,
):

    # deferred aciton is executed last after allother actions from parent action template
    # are executed no matter of its postion inside parent action template.

    # Usefull if we need to create breadcrumb or other summary report
    # based from already executed actions

    # deferred_after and deferred_before are used to execute this action after or before
    # other specific deferred action, when multiple actions has deferred execution
    """Decorator to mark Component method as public action

    Public actions can be called from browser using javascript, as follows:

    .. code-block:: html

        <button onclick="jembeClient.component(this).call('action',{param1:value1, param2:value2})">
            Action
        </button>

        Or using Jembe Js ComponentApi:

        <button jmb-on:click="action(value1)">
            Action
        </button>

        or

        <a href="" jmb-on:click.prevent="action()">
            Action
        </a>

    If action is defered than it is executed last, after all other actions from parent action template
    are executed no matter of its postion inside parent action template. This is usefull if we need
    to create breadcrumb or other summary report based from already executed actions.

    Args:
        deferred (bool, optional): If action is deffered. Defaults to False.

    Returns:
        Optional[bool]: Decorated action should return None, True or False
            If decorated action returns:

            - True: then component will redisplay itself.
            - False: then component will NOT redisplay itself.
            - None: then component will redisplay it self based on values of Config.redisplay and state parameters. Defult if will redisplay itself only if state params are changed.
    """
    # This decorator don't anytthing except allow
    # componentconfig.set_compoenent_class to
    # recognise method as action
    def decorator_action(method):
        setattr(method, "_jembe_action", True)
        setattr(method, "_jembe_action_deferred", deferred)
        # setattr(method, "_jembe_action_deferred_after", deferred_after)
        # setattr(method, "_jembe_action_deferred_before", deferred_before)
        return method

    if _method is None:
        return decorator_action
    else:
        return decorator_action(_method)


def listener(
    _method=None,
    *,
    event: Optional[Union[str, Sequence[str]]] = None,
    source: Optional[Union[str, Sequence[str]]] = None,
):
    """Decorator to mark Component method as event listener.

    Event listener listens for emited events.

    Event listener must accepet event parameter like:

    .. code-block:: python

        @listener("_display", source="*")
        def on_display_any_direct_childred(self, event:"jembe.Event"):
            pass

    Args:
        event (Optional[Union[str, Sequence[str]]], optional): Event name to listen for. Defaults to None.

            If event name is:

            - None: it will listen for any event
            - str: it will listen for only event with the same name
            - Sequence[str]: it will listen for any event name from the list of names

        source (Optional[Union[str, Sequence[str]]], optional): Listens for events emited by component specified as source. Defaults to None.

            Listen for:

            - None -> events from any component
            - *                               -> direct children with or without key
            - *.*                             -> direct children with any key
            - **/*                            -> all children with or without key
            - **/*.*                          -> all children with any key
            - component                       -> match to direct child named "component" without key
            - component.*                     -> match to direct child named "component" with any key
            - component.key                   -> match to direct child named "component with key equals "key"
            - **/component[.[*|<key>]]        -> match to child at any level with "component" name
            - ..                                -> match to parent component
            - ../component[.[*|<key>]]          -> match to sibling
            - /**/.                             -> match to parent at any level
            - /**/component[.[*|<key>]]/**/.    -> match to parent at any level named "component"
            - //                                -> process event from root/page component
            - .                                 -> self

    Returns:
        Optional[bool]: Decorated method should return None, True or False

            If decorated listener returns:

            - True: then component will redisplay itself.
            - False: then component will NOT redisplay itself.
            - None: then component will redisplay it self based on values of Config.redisplay and state parameters. Defult if will redisplay itself only if state params are changed.

    """
    # This decorator don't anytthing except allow
    # componentconfig.set_compoenent_class to
    # recognise method as listener
    def decorator_listener(method):
        setattr(method, "_jembe_listener", True)
        setattr(method, "_jembe_listener_event_name", event)
        setattr(method, "_jembe_listener_source", source)
        return method

    if _method is None:
        return decorator_listener
    else:
        return decorator_listener(_method)


def redisplay(
    _method=None,
    *,
    when_state_changed: Optional[bool] = None,
    when_executed: Optional[bool] = None,
    when_on_page: Optional[bool] = None,
):
    """Decorator for Component.display method to configure when component will be redisplayed

    It's used instead of Component.Config redisplay parameter, when it's more convinient.


    Args:
        when_state_changed (Optional[bool], optional): Redisplay component whent its state is changed. Defaults to None.
        when_executed (Optional[bool], optional): Redisplay component when ever "display" action is called regradles of the component state. Defaults to None.
        when_on_page (Optional[bool], optional): Redisplay component whenever it's on the page. Defaults to None.
    """

    def decorator_action(method):
        flags = set(ComponentConfig.REDISPLAY_DEFAULT_FLAGS)

        def update_flags(state, flag):
            if state == True:
                flags.add(flag)
            elif state == False:
                flags.remove(flag)

        update_flags(when_executed, RedisplayFlag.WHEN_DISPLAY_EXECUTED)
        update_flags(when_state_changed, RedisplayFlag.WHEN_STATE_CHANGED)
        update_flags(when_on_page, RedisplayFlag.WHEN_ON_PAGE)
        setattr(method, "_jembe_redisplay", tuple(flags))
        return method

    if _method is None:
        return decorator_action
    else:
        return decorator_action(_method)


def config(component_config: "jembe.ComponentConfig"):
    """Component decorator to declarativly change Component Configuration

    This decorator changes Component Configuration by suplaying predefined
    params to Component.ComponentConfig.__init__ method.

    .. note::
        ComponentConfig instance in argument is used only to get values of __init__ params.

        Collected params are used when component is registred to Jembe instance,
        allowing parent component to overide configuration of its subcomponents when needed.

    Args:
        component_config (jembe.ComponentConfig): Instance of Component.Config class
    """

    def decorator_class(component_class):
        setattr(
            component_class,
            "_jembe_config_init_params",
            component_config._raw_init_params,
        )
        return component_class

    return decorator_class


class ComponentAction:
    def __init__(
        self,
        name: str,
        deferred: bool = False,
        # deferred_after: Optional[str] = None,
        # deferred_before: Optional[str] = None,
    ):
        self.name = name
        self.deferred = deferred
        # self.deferred_after = deferred_after
        # self.deferred_before = deferred_before

    @classmethod
    def from_method(cls, method) -> "ComponentAction":
        return cls(
            method.__name__,
            getattr(method, "_jembe_action_deferred", False),
            # getattr(method, "_jembe_action_deferred_after", None),
            # getattr(method, "_jembe_action_deferred_before", None),
        )


class ComponentListener:
    def __init__(
        self,
        method_name: str,
        event_name: Union[str, Sequence[str]],
        source: Union[str, Sequence[str]] = (),
    ):
        self.method_name: str = method_name

        self.event_names: Tuple[str, ...] = ()
        if event_name is None:
            pass
        elif isinstance(event_name, str):
            self.event_names = (event_name,)
        else:
            self.event_names = tuple(event_name)

        self.sources: Tuple[str, ...] = ()
        if source is None:
            pass
        elif isinstance(source, str):
            self.sources = (source,)
        else:
            self.sources = tuple(source)

    @classmethod
    def from_method(cls, method) -> "ComponentListener":
        return cls(
            method.__name__,
            getattr(method, "_jembe_listener_event_name", ()),
            getattr(method, "_jembe_listener_source", ()),
        )


class RedisplayFlag(Enum):
    WHEN_STATE_CHANGED = "wsc"
    WHEN_DISPLAY_EXECUTED = "wde"
    WHEN_ON_PAGE = "wop"


def componentConfigInitDecorator(init_method):
    def decoratedInit(self, *args, **kwargs):
        """Saves named init params as self._raw_init_params and apply params from @config"""
        # save original init_params as _raw_init_prams

        # update init params default values form @config decorator
        if hasattr(self, "_name"):
            # we need to initialise config
            # get init params set by @config decorator
            default_init_params = getattr(
                self.component_class, "_jembe_config_init_params", dict()
            )
            init_params = default_init_params.copy()
            init_params.update(kwargs.copy())
            init_parameters = signature(init_method).parameters

            init_named_params = [
                name
                for name, param in init_parameters.items()
                if param.kind == Parameter.POSITIONAL_OR_KEYWORD and name != "self"
            ]
            init_has_kwarg_param = (
                len(
                    [
                        name
                        for name, param in init_parameters.items()
                        if param.kind == Parameter.VAR_KEYWORD
                    ]
                )
                > 0
            )
            try:
                if init_has_kwarg_param:
                    # init has **kwargs param so use all init_params suplied
                    init_method(self, *args, **init_params)
                else:
                    # from init-params use only params that actual exesit in __init__
                    # becouse __init__ does not have **kwargs
                    init_method(
                        self,
                        *args,
                        **{
                            key: value
                            for key, value in init_params.items()
                            if key in init_named_params[len(args) :]
                        },
                    )
            except Exception as e:
                print(f"Error in {kwargs} __init__: {e}\n\n")
                raise e
        else:
            # Component config is used inside @config or @page decorator
            # no need to proper initialise class
            # just set _raw_init_params that will be picked up by @config or @page
            # decorator and used to set _jembe_config_init_params
            self._raw_init_params = kwargs.copy()

    return decoratedInit


class ComponentConfigMeta(ABCMeta):
    def __new__(cls, name, bases, attrs, **kwargs):
        # decorate __init__ to create _raw_init_params dict
        if "__init__" in attrs:
            attrs["__init__"] = componentConfigInitDecorator(attrs["__init__"])
        new_class = super().__new__(cls, name, bases, dict(attrs), **kwargs)
        return new_class


class ComponentConfig(metaclass=ComponentConfigMeta):
    """
    Compononent config defines behavior of all instances of component that
    are known at build time, like: url_path, subcomponents, name etc.
    """

    # initialised by _jembe_init
    _name: str
    _component_class: Type["jembe.Component"]
    _parent: Optional["jembe.ComponentConfig"]

    # initilised by _jembe_prepare_component_init run inside _jembe_init
    component_actions: Dict[str, "ComponentAction"]  # [method_name]
    component_listeners: Dict[str, "ComponentListener"]  # [method_name]
    redisplay: Tuple["jembe.RedisplayFlag", ...]
    _hiearchy_level: int
    _url_params: Tuple["UrlParamDef", ...]
    _key_url_param: "UrlParamDef"

    # intialise by Jembe app after registring route
    __endpoint: str

    @classmethod
    def _jembe_init_(
        cls,
        _name: str,
        _component_class: Type["jembe.Component"],
        _parent: Optional["jembe.ComponentConfig"],
        **init_params,
    ):
        """
        Instance creation by explicitly calling __new__ and __init__
        becouse _parent should be avaible in __init__
        """
        try:
            cconfig = object.__new__(cls)
            cconfig._name = _name
            cconfig._component_class = _component_class
            cconfig._parent = _parent
            cconfig._jembe_prepare_component_init()
            cconfig.__init__(**init_params)  # type:ignore
        except Exception as err:
            # Add place of the error for debuging purpuse
            err.args = (f"Error in: {_component_class}", ) + err.args
            raise err
        return cconfig

    def _jembe_prepare_component_init(self):
        """
        Called by _jembe_init_, when actually inicitialising component
        to calculate and set all attributes required by jembe framework.
        Reads component class description and sets appropriate config params
        like url_path state and init params, etc.

        This method is not run when you initiate Config inside @config or @page
        decorator in order to set default values.
        """
        ### attributes configured by component_class
        # obtain component actions
        display_method = getattr(self.component_class, self.DEFAULT_DISPLAY_ACTION)
        self.component_actions = {
            self.DEFAULT_DISPLAY_ACTION: ComponentAction.from_method(display_method)
        }
        for method_name, method in getmembers(
            self.component_class,
            lambda o: isfunction(o) and getattr(o, "_jembe_action", False),
        ):
            self.component_actions[method_name] = ComponentAction.from_method(method)

        # obtain component listeners
        self.component_listeners = dict()
        for method_name, method in getmembers(
            self.component_class,
            lambda o: isfunction(o) and getattr(o, "_jembe_listener", False),
        ):
            self.component_listeners[method_name] = ComponentListener.from_method(
                method
            )

        # set redisplay from @redisplay decorator or with default value
        redisplay_settings = getattr(display_method, "_jembe_redisplay", ())
        if redisplay_settings:
            self.redisplay = redisplay_settings
        else:
            self.redisplay = self.REDISPLAY_DEFAULT_FLAGS

        ### attributes configured by parent
        self._hiearchy_level = 0 if not self.parent else self.parent._hiearchy_level + 1
        # Gets all component.__init__ paramters without default value
        # and populate self._url_params
        self._url_params = tuple(
            UrlParamDef.from_inspect_parameter(p, self._hiearchy_level)
            for p in self.component_class._jembe_init_signature.parameters.values()
            if p.default == p.empty and p.name != "self" and not p.name.startswith("_")
        )
        self._key_url_param = UrlParamDef(
            self.KEY_URL_PARAM_NAME,
            identifier=calc_url_param_identifier(
                self.KEY_URL_PARAM_NAME, self._hiearchy_level
            ),
            convertor=UrlConvertor.STR0,
        )

    KEY_URL_PARAM_NAME = "component_key"
    KEY_URL_PARAM_SEPARATOR = "."
    DEFAULT_DISPLAY_ACTION = "display"
    DEFAULT_AC_EXCEPTION = AccessDenied

    _raw_init_params: dict

    WHEN_STATE_CHANGED = RedisplayFlag.WHEN_STATE_CHANGED
    WHEN_DISPLAY_EXECUTED = RedisplayFlag.WHEN_DISPLAY_EXECUTED
    WHEN_ON_PAGE = RedisplayFlag.WHEN_ON_PAGE

    REDISPLAY_DEFAULT_FLAGS = (RedisplayFlag.WHEN_STATE_CHANGED,)

    def __init__(
        self,
        template: Optional[Union[str, Iterable[str]]] = None,
        components: Optional[Dict[str, "jembe.ComponentRef"]] = None,
        inject_into_components: Optional[
            Callable[["jembe.Component", "jembe.ComponentConfig"], dict]
        ] = None,  # TODO
        redisplay: Tuple["jembe.RedisplayFlag", ...] = (),
        changes_url: bool = True,
        url_query_params: Optional[Dict[str, str]] = None,
    ):
        """_summary_

        template: path to default template for displaying component
        components: Definition of subcomponents
        inject_into_components: Callable to inject init params into subcomponents
        redisplay: Flag to define when componnet will be redisplayed on client depending of its state
        changes_url: Does this component changes location url and allow back browser navigation to it
        url_query_params: Mapping from GET Query params to state params used when component is called directly via regular http get request dict(<name of get queryparam> = <name of state param>)
        Args:
            template (Optional[Union[str, Iterable[str]]], optional): _description_. Defaults to None.
            components (Optional[Dict[str, &quot;jembe.ComponentRef&quot;]], optional): _description_. Defaults to None.
            inject_into_components (Optional[ Callable[[&quot;jembe.Component&quot;, &quot;jembe.ComponentConfig&quot;], dict] ], optional): _description_. Defaults to None.
            changes_url (bool, optional): _description_. Defaults to True.
            url_query_params (Optional[Dict[str, str]], optional): _description_. Defaults to None.
        """

        # use default template if template name is not provided
        if template is None:
            self.template: Tuple[str, ...] = self.default_template_names
        elif isinstance(template, str):
            self.template = (template,)
        else:
            templates: List[str] = []
            for t in template:
                if t == "":
                    templates.extend(self.default_template_names)
                else:
                    templates.append(t)
            self.template = tuple(templates)

        self.components: Dict[str, "jembe.ComponentRef"] = (
            components if components else dict()
        )
        self._inject_into_components = inject_into_components

        # if redisplay is set use it, otherwise leave
        # redisplay set by @redisplay decorator or default value
        if redisplay:
            self.redisplay = redisplay
        self.changes_url = changes_url
        self.url_query_params = (
            url_query_params if url_query_params is not None else dict()
        )

        if not self.changes_url:
            # set changes_url to False to all its children components
            self.update_components_config(None, dict(changes_url=False))

    @property
    def endpoint(self) -> str:
        try:
            return self.__endpoint
        except AttributeError:
            raise JembeError(f"Endpoint not set by jembe app: {self.full_name}")

    @endpoint.setter
    def endpoint(self, endpoint: str):
        self.__endpoint = endpoint

    @property
    def component_class(self) -> Type["jembe.Component"]:
        try:
            return getattr(self, "_component_class")
        except AttributeError:
            raise JembeError(
                f"Component Config {self.full_name} is not initialised properly, 'component_class' is missing."
            )

    @property
    def name(self) -> str:
        try:
            return getattr(self, "_name")
        except AttributeError:
            raise JembeError(
                f"Component Config {self.full_name} is not initialised properly, 'name' is missing."
            )

    @property
    def parent(self) -> Optional["jembe.ComponentConfig"]:
        try:
            return getattr(self, "_parent")
        except AttributeError:
            raise JembeError(
                f"Component Config {self.full_name} is not initialised properly, 'parent' is missing."
            )

    @property
    def full_name(self) -> str:
        if self.parent:
            return f"{self.parent.full_name}/{self.name}"
        return f"/{self.name}"

    @property
    def url_path(self) -> str:
        if not self._url_params:
            url_path = f"/{self.name}{self._key_url_param.url_pattern}"
        else:
            url_params = "/".join(up.url_pattern for up in self._url_params)
            url_path = f"/{self.name}{self._key_url_param.url_pattern}/{url_params}"
        url_path = f"{self.parent.url_path}{url_path}" if self.parent else url_path
        return url_path

    @property
    def hiearchy_level(self) -> int:
        try:
            return self._hiearchy_level
        except AttributeError:
            raise JembeError("Componet config initialisation is not complete")

    def get_raw_url_params(self, state: "ComponentState", key: str) -> dict:
        url_params = {up.identifier: state[up.name] for up in self._url_params}
        url_params[self._key_url_param.identifier] = (
            f"{self.KEY_URL_PARAM_SEPARATOR}{key}" if key else ""
        )
        return url_params

    def build_url(
        self, exec_name: str, component: Optional["jembe.Component"] = None
    ) -> str:
        from .app import get_processor

        processor: "jembe.Processor" = get_processor()
        exec_names = tuple(
            accumulate(map(lambda x: "/" + x, exec_name.strip("/").split("/")), add)
        )
        url_params = dict()
        for en in exec_names:
            if component is not None and en == component.exec_name:
                cmp = component
            else:
                cmp = processor.components[en]

            url_params.update(cmp._config.get_raw_url_params(cmp.state, cmp.key))
        return url_for(self.endpoint, **url_params)

    @property
    def default_template_names(self) -> Tuple[str, ...]:
        tname = f"{self.full_name.strip('/')}.html"
        return (tname, f"pages/{tname}")

    def update_components_config(
        self,
        name: Optional[str],
        params: Dict,
    ):
        """
        For use inside __init__ to change sub components config init params
        regardless if component is referenced with or without componentconfig part.

        name: name of the component config to change if name is None apply params to all components
        params: dict with new params to set
        """
        if not self.components:
            return

        def _update_cref(cname: str, params: Dict):
            """Update self.compoennts"""
            comp_ref: "jembe.ComponentRef" = self.components[cname]
            if not isinstance(comp_ref, tuple):
                comp_ref = (comp_ref, dict())
                self.components[cname] = comp_ref
            if isinstance(comp_ref[1], ComponentConfig):
                comp_ref = (comp_ref[0], comp_ref[1]._raw_init_params)
                self.components[cname] = comp_ref
            if isinstance(comp_ref[1], dict):  # just to satisfy typing check
                comp_ref[1].update(params)
            else:
                # this shuld never happend
                raise NotImplementedError()

        if name is None:
            for name in self.components.keys():
                _update_cref(name, params)
        else:
            if name not in self.components:
                raise ValueError(
                    f"Component with name {name} is not defined inside {self.name}"
                )
            _update_cref(name, params)

    @property
    def components_configs(self) -> Dict[str, "jembe.ComponentConfig"]:
        from .app import get_processor

        processor: "jembe.Processor" = get_processor()
        configs: Dict[str, "jembe.ComponentConfig"] = dict()
        for component_name in self.components.keys():
            configs[component_name] = processor.jembe.components_configs[
                f"{self.full_name}/{component_name}"
            ]
        return configs

    @property
    def components_classes(self) -> Dict[str, Type["jembe.Component"]]:
        def _get_cref_class(cref: "jembe.ComponentRef") -> Type["jembe.Component"]:
            cc = cref[0] if isinstance(cref, tuple) else cref
            if isinstance(cc, str):
                return import_by_name(cc)
            return cc

        return {name: _get_cref_class(cref) for name, cref in self.components.items()}

    @property
    def super(self):
        return super(self.__class__, self)
