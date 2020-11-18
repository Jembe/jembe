from typing import (
    Callable,
    TYPE_CHECKING,
    Optional,
    Type,
    Dict,
    Tuple,
    Union,
    Sequence,
    NewType,
)
from abc import ABCMeta
from enum import Enum
from copy import deepcopy
from itertools import accumulate
from operator import add
from inspect import getmembers, isfunction
from .exceptions import JembeError
from flask import url_for
from .common import ComponentRef

if TYPE_CHECKING:  # pragma: no cover
    import inspect
    from .component import Component, ComponentState
    from .processor import Processor
    from flask import Request

UrlPath = NewType("UrlPath", str)


class UrlConvertor(Enum):
    STR0 = "string(minlength=0)"
    STR = "string"
    PATH = "path"
    INT = "int"
    FLOAT = "float"
    UUID = "uuid"


def calc_url_param_identifier(name: str, level: int):
    return name if level == 0 else "{}__{}".format(name, level)


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
        return "<{convertor}:{identifier}>".format(
            convertor=self.convertor.value, identifier=self.identifier
        )

    def __repr__(self):
        return self.url_pattern


def action(
    _method=None,
    *,
    deferred=False,
    # deferred_after: Optional[str] = None,
    # deferred_before: Optional[str] = None,
):
    """
    decorator to mark method as public action inside component

    deferred aciton is executed last after allother actions from parent action template
    are executed no matter of its postion inside parent action template.

    Usefull if we need to create breadcrumb or other summary report 
    based from already executed actions

    deferred_after and deferred_before are used to execute this action after or before 
    other specific deferred action, when multiple actions has deferred execution
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
    """
    decorator to mark method as action listener inside component
    filter by:
    source = glob like component exec_name matcher
    if source is:

        - None -> process event from any compoenent
        - /compoent1.key1/compoent2.key2    -> process event from  compoenent with this exec_name
        - ./component                       -> process event from direct child named "component" without key
        - ./component.*                     -> process event from direct child named "component" with any key
        - ./component.key                   -> process event from direct child named "component with key equals "key"
        - ./**/component[.[*|<key>]]        -> process event from child at any level
        - ..                                -> process event from parent
        - ../component[.[*|<key>]]          -> process event from sibling 
        - /**/.                             -> process event from parent at any level
        - /**/component[.[*|<key>]]/**/.    -> process event from parent at any level named
        - //                                -> process event from root page
        - etc.
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
    """
    Decorates display method in order to set redisplay ComponentConfig param.
    
    Made for easy use when configuring components
    """

    def decorator_action(method):
        flags = set(ComponentConfig.REDISPLAY_DEFAULT_FLAGS)

        def update_flags(state, flag):
            if state == True:
                flags.add(flag)
            elif state == False:
                flags.remove(flag)

        update_flags(when_executed, CConfigRedisplayFlag.WHEN_DISPLAY_EXECUTED)
        update_flags(when_state_changed, CConfigRedisplayFlag.WHEN_STATE_CHANGED)
        update_flags(when_on_page, CConfigRedisplayFlag.WHEN_ON_PAGE)
        setattr(method, "_jembe_redisplay", tuple(flags))
        return method

    if _method is None:
        return decorator_action
    else:
        return decorator_action(_method)


def config(component_config: "ComponentConfig"):
    """
    Decorates Component to chante its ComponentConfig init parameters
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


class CConfigRedisplayFlag(Enum):
    WHEN_STATE_CHANGED = "wsc"
    WHEN_DISPLAY_EXECUTED = "wde"
    WHEN_ON_PAGE = "wop"


def componentConfigInitDecorator(init_method):
    def decoratedInit(self, *args, **kwargs):
        """Saves named init params as self._raw_init_params and apply params from @config"""
        # save original init_params as _raw_init_prams

        # update init params default values form @config decorator
        if "name" in kwargs and "_component_class" in kwargs:
            # we need to initialise config
            _component_class: Type["Component"] = kwargs["_component_class"]
            # get init params set by @config decorator
            default_init_params = getattr(
                _component_class, "_jembe_config_init_params", dict()
            )
            init_params = default_init_params.copy()
            init_params.update(kwargs.copy())
            init_method(self, *args, **init_params)
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

    KEY_URL_PARAM_NAME = "component_key"
    KEY_URL_PARAM_SEPARATOR = "."
    DEFAULT_DISPLAY_ACTION = "display"

    _raw_init_params: dict

    WHEN_STATE_CHANGED = CConfigRedisplayFlag.WHEN_STATE_CHANGED
    WHEN_DISPLAY_EXECUTED = CConfigRedisplayFlag.WHEN_DISPLAY_EXECUTED
    WHEN_ON_PAGE = CConfigRedisplayFlag.WHEN_ON_PAGE

    REDISPLAY_DEFAULT_FLAGS = (CConfigRedisplayFlag.WHEN_STATE_CHANGED,)

    def __init__(
        self,
        name: Optional[str] = None,
        template: Optional[str] = None,
        components: Optional[Dict[str, ComponentRef]] = None,
        inject_into_components: Optional[
            Callable[["Component", "ComponentConfig"], dict]
        ] = None,  # TODO
        redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
        changes_url: bool = True,
        url_query_params: Optional[Dict[str,str]] = None,
        _component_class: Optional[Type["Component"]] = None,
        _parent: Optional["ComponentConfig"] = None,
    ):
        """
        name: name of the component
        template: path to default template for displaying component
        components: Definition of subcomponents
        inject_into_components: Callable to inject init params into subcomponents
        redisplay: Flag to define when componnet will be redisplayed on client depending of its state
        changes_url: Does this component changes location url and allow back browser navigation to it
        url_query_params: Mapping from GET Query params to state params used when component is called directly via regular http get request dict(<name of get queryparam> = <name of state param>)

        _component_class, _parent: used internally by jembe library
        """
        self.name = name
        self.components: Dict[str, ComponentRef] = components if components else dict()
        self._template = template
        self._inject_into_components = inject_into_components
        self._redisplay_temp = redisplay
        self.changes_url = changes_url
        self.url_query_params = url_query_params if url_query_params is not None else dict()

        if not self.changes_url:
            # set changes_url to False to all its children components
            self.update_components_config(None, dict(changes_url=False))

        # intialise by Jembe app after registring route
        self.__endpoint: str

        # initialise after setting component_class
        self._component_class: Optional[Type["Component"]]
        self.component_actions: Dict[str, "ComponentAction"]  # [method_name]
        self.component_listeners: Dict[str, "ComponentListener"]  # [method_name]
        self.redisplay: Tuple["CConfigRedisplayFlag", ...]

        # initalise after setting parent
        self._parent: Optional["ComponentConfig"]
        self._hiearchy_level: int
        self._url_params: Tuple["UrlParamDef", ...]
        self._key_url_param: "UrlParamDef"
        self.template: str

        if _component_class and name:
            self._set_component_class(_component_class)
            self._set_parent(_parent)

    @property
    def endpoint(self) -> str:
        try:
            return self.__endpoint
        except AttributeError:
            raise JembeError("Endpoint not set by jembe app: {}".format(self.full_name))

    @endpoint.setter
    def endpoint(self, endpoint: str):
        self.__endpoint = endpoint

    @property
    def component_class(self) -> Type["Component"]:
        if self._component_class is None:
            raise JembeError(
                "Component Config {} is not initialised properly".format(self.full_name)
            )
        return self._component_class

    def _set_component_class(self, component_class: Type["Component"]):
        """
        Called by __init__,  to set associated component class.
        Reads component class description and sets appropriate config params 
        like url_path state and init params, etc.

        comonent_class is not argument of __init__ because it should not ever 
        be set or changed by end user or any other class except Jembe app.
        """
        self._component_class = component_class
        self.component_actions = {
            self.DEFAULT_DISPLAY_ACTION: ComponentAction.from_method(
                getattr(self._component_class, self.DEFAULT_DISPLAY_ACTION)
            )
        }
        for method_name, method in getmembers(
            self._component_class,
            lambda o: isfunction(o) and getattr(o, "_jembe_action", False),
        ):
            self.component_actions[method_name] = ComponentAction.from_method(method)

        self.component_listeners = {}
        for method_name, method in getmembers(
            self._component_class,
            lambda o: isfunction(o) and getattr(o, "_jembe_listener", False),
        ):
            self.component_listeners[method_name] = ComponentListener.from_method(
                method
            )

        # update redisplay if necessary
        display_method = getattr(self._component_class, self.DEFAULT_DISPLAY_ACTION)
        redisplay_settings = getattr(display_method, "_jembe_redisplay", ())
        if self._redisplay_temp:
            # if redisplay is set for config ignore settings on method
            self.redisplay = self._redisplay_temp
        elif redisplay_settings:
            self.redisplay = redisplay_settings
        else:
            self.redisplay = self.REDISPLAY_DEFAULT_FLAGS

    @property
    def parent(self) -> Optional["ComponentConfig"]:
        return self._parent

    def _set_parent(self, parent: Optional["ComponentConfig"]):
        """
        Called by __init__ to set parent componet config
        """
        self._parent = parent
        self._hiearchy_level = 0 if not parent else parent._hiearchy_level + 1
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
        # populate default template
        self.template = (
            self._template
            if self._template is not None
            else self._get_default_template_name()
        )

    @property
    def full_name(self) -> str:
        if self.parent:
            return "{}/{}".format(self.parent.full_name, self.name)
        return "/{}".format(self.name)

    @property
    def url_path(self) -> str:
        if not self._url_params:
            url_path = "/{}{}".format(self.name, self._key_url_param.url_pattern)
        else:
            url_params = "/".join(up.url_pattern for up in self._url_params)
            url_path = "/{name}{key}/{url_params}".format(
                name=self.name,
                key=self._key_url_param.url_pattern,
                url_params=url_params,
            )
        url_path = (
            "{}{}".format(self.parent.url_path, url_path) if self.parent else url_path
        )
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
            "{}{}".format(self.KEY_URL_PARAM_SEPARATOR, key) if key else ""
        )
        return url_params

    def build_url(self, exec_name: str) -> str:
        from .app import get_processor

        processor: "Processor" = get_processor()
        exec_names = tuple(
            accumulate(map(lambda x: "/" + x, exec_name.strip("/").split("/")), add)
        )
        url_params = dict()
        for en in exec_names:
            component = processor.components[en]
            url_params.update(
                component._config.get_raw_url_params(component.state, component.key)
            )
        return url_for(self.endpoint, **url_params)

    def _get_default_template_name(self) -> str:
        return "{}.html".format(self.full_name.strip("/"))

    def update_components_config(
        self, name: Optional[str], params: Dict,
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
            """ Update self.compoennts """
            comp_ref: ComponentRef = self.components[cname]
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
                    "Component with name {} is not defined inside {}".format(
                        name, self.name
                    )
                )
            _update_cref(name, params)

