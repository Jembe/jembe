from typing import TYPE_CHECKING, Optional, Type, Dict, List, Tuple, Any
from abc import ABCMeta
from enum import Enum
from inspect import signature, getmembers, isfunction
from .errors import JembeError

if TYPE_CHECKING:  # pragma: no cover
    import inspect
    from .component import Component
    from .common import ComponentRef
    from flask import Request


class UrlConvertor(Enum):
    STR0 = "string(minlength=0)"
    STR = "string"
    PATH = "path"
    INT = "int"
    FLOAT = "float"
    UUID = "uuid"


def calc_url_param_identifier(name: str, level: int):
    return name if level == 0 else "{}.{}".format(name, level)


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
        cls, p: "inspect.Parameter", level: int
    ) -> "UrlParamDef":
        convertor = UrlConvertor.STR
        if p.annotation.__name__ == "int":
            convertor = UrlConvertor.INT
        elif p.annotation.__name__ == "str":
            convertor = UrlConvertor.STR
        elif p.annotation.__name__ == "float":
            convertor = UrlConvertor.FLOAT
        elif p.annotation.__name__ == "UUID":
            convertor = UrlConvertor.UUID
        # TODO convertor PATH
        return UrlParamDef(p.name, convertor, calc_url_param_identifier(p.name, level))

    @property
    def url_pattern(self) -> str:
        return "<{convertor}:{identifier}>".format(
            convertor=self.convertor.value, identifier=self.identifier
        )

    def __repr__(self):
        return self.url_pattern


def action(
    method,
    deferred=False,
    deferred_after: Optional[str] = None,
    deferred_before: Optional[str] = None,
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

    setattr(method, "_jembe_action", True)
    setattr(method, "_jembe_action_deferred", deferred)
    setattr(method, "_jembe_action_deferred_after", deferred_after)
    setattr(method, "_jembe_action_deferred_before", deferred_before)
    return method


class ComponentAction:
    def __init__(
        self,
        name: str,
        deferred: bool = False,
        deferred_after: Optional[str] = None,
        deferred_before: Optional[str] = None,
    ):
        self.name = name
        self.deferred = deferred
        self.deferred_after = deferred_after
        self.deferred_before = deferred_before

    @classmethod
    def from_method(cls, method) -> "ComponentAction":
        return cls(
            method.__name__,
            getattr(method, "_jembe_action_deferred", False),
            getattr(method, "_jembe_action_deferred_after", None),
            getattr(method, "_jembe_action_deferred_before", None),
        )


def componentConfigInitDecorator(init_method):
    def decoratedInit(self, *args, **kwargs):
        """Saves named init params as self._raw_init_params"""
        self._raw_init_params = kwargs.copy()
        init_method(self, *args, **kwargs)

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

    def __init__(
        self,
        name: Optional[str] = None,
        template: Optional[str] = None,
        components: Optional[Dict[str, "ComponentRef",]] = None,
    ):
        self.name = name
        self.template = (
            template if template is not None else self._get_default_template_name()
        )
        self.components = components
        # initialise after setting component_class

        self._component_class: Optional[Type["Component"]]
        self.component_actions: Dict[str, "ComponentAction"]

        # initalise after setting parent
        self._parent: Optional["ComponentConfig"]
        self._hiearchy_level: int
        self._url_params: Tuple["UrlParamDef", ...]
        self._key_url_param: "UrlParamDef"

    @property
    def component_class(self) -> Type["Component"]:
        if self._component_class is None:
            raise JembeError(
                "Component Config {} is not initialised properly".format(self.full_name)
            )
        return self._component_class

    @component_class.setter
    def component_class(self, component_class: Type["Component"]):
        """
        Called by Jembe app imidiatlly after __init__,  to set associated 
        component class.
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

    @property
    def parent(self) -> Optional["ComponentConfig"]:
        return self._parent

    @parent.setter
    def parent(self, parent: Optional["ComponentConfig"]):
        """
        Called by jembe app after init to set parent componet config
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

    @property
    def full_name(self) -> str:
        return "/{}".format(self.name)

    @property
    def url_path(self) -> str:
        if not self._url_params:
            return "/{}{}".format(self.name, self._key_url_param.url_pattern)
        else:
            url_params = "/".join(up.url_pattern for up in self._url_params)
            return "/{name}{key}/{url_params}".format(
                name=self.name,
                key=self._key_url_param.url_pattern,
                url_params=url_params,
            )

    def _get_default_template_name(self) -> str:
        return "{}.jinja2".format(self.full_name.strip("/"))

