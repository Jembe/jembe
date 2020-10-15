from typing import (
    TYPE_CHECKING,
    ForwardRef,
    Optional,
    Union,
    Dict,
    Any,
    List,
    Tuple,
    get_args,
    Type,
)
from copy import deepcopy
from abc import ABCMeta
from inspect import isclass, isfunction, signature, getmembers
from .exceptions import JembeError
from flask import render_template, render_template_string, current_app
from .component_config import ComponentConfig
from .app import get_processor
from .processor import CallActionCommand, CallDisplayCommand, InitialiseCommand, EmitCommand
from .common import exec_name_to_full_name

if TYPE_CHECKING:  # pragma: no cover
    from flask import Response
    from inspect import Signature


class ComponentState(dict):
    """
    Two instance of the same compoennt, component with same full_name, in the same
    state should behawe identically.

    State of the component is defined by state params, __init__ params whose name 
    doesn't start with _ (underscore).

    Appon initialising component_state params can't be added or deleted from 
    that state but values of the existing params can change
    """

    def __init__(self, *args, **kwargs):
        self._injected_params_names: List[str] = []
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if not key in self.keys():
            raise JembeError("Can't add new param to component state")
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        raise JembeError("Can't delete param from component state")

    def __getattr__(self, name):
        if name in self.keys():
            return self[name]
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name == "_injected_params_names":
            super().__setattr__(name, value)
        else:
            if name not in self.keys():
                raise JembeError("Can't set arbitrary attribute to component state")
            self[name] = value
        # return super().__setattr__(name, value)

    def __eq__(self, value):
        return super().__eq__(value)

    def deepcopy(self):
        c = ComponentState(**self)
        for key, value in self.items():
            c[key] = deepcopy(value)
        c._injected_params_names = deepcopy(self._injected_params_names)
        return c

    def tojsondict(self, component_class: Type["Component"]):
        return {
            k: component_class.encode_param(k, v)
            for k, v in self.items()
            if k not in self._injected_params_names
        }


class _SubComponentRenderer:
    def __init__(self, component: "Component", name: str, args: tuple, kwargs: dict):
        self.component = component
        self.name = name
        self._key = ""
        self.action = ComponentConfig.DEFAULT_DISPLAY_ACTION
        self.action_args: Tuple[Any, ...] = ()
        self.action_kwargs: dict = {}
        self.kwargs = kwargs

    def is_accessible(self) -> bool:
        # TODO add param ignore_incoplete_params = Truo so that exception trown during initialise
        # becouse not all required init parameters are suplied are treated as not accessible (
        # catch exception and return False in this case)
        processor = get_processor()
        component_exec_name = Component._build_exec_name(
            self.name, self._key, self.component.exec_name
        )
        initialise_command = InitialiseCommand(component_exec_name, self.kwargs)
        return processor.execute_initialise_command_successfully(initialise_command)

    def __call__(self) -> str:
        """
        Do render

        Component initialisation must be executed in place in order to know
        will it raise exception (like NotFound, Forbidden, Unauthorized etc.)
        so that we can decide how to render template
        """
        processor = get_processor()
        component_exec_name = Component._build_exec_name(
            self.name, self._key, self.component.exec_name
        )

        processor.add_command(
            InitialiseCommand(component_exec_name, self.kwargs), end=True
        )
        # call action command is put in que to be executed latter
        # if this command raises exception parent should chach it and call display
        # with appropriate template
        if self.action == ComponentConfig.DEFAULT_DISPLAY_ACTION:
            processor.add_command(
                CallDisplayCommand(
                    component_exec_name
                ),
                end=True,
            )
        else:
            processor.add_command(
                CallActionCommand(
                    component_exec_name, self.action, self.action_args, self.action_kwargs,
                ),
                end=True,
            )
        return '<jmb-placeholder exec-name="{}"/>'.format(component_exec_name)

    def key(self, key: str) -> "_SubComponentRenderer":
        self._key = key
        return self

    def call(self, action: str, *args, **kwargs) -> "_SubComponentRenderer":
        self.action = action
        self.action_args = args
        self.action_kwargs = kwargs
        return self

    def __html__(self):
        return self.__call__()


def componentInitDecorator(init_method):
    def decoratedInit(self, *args, **kwargs):
        """
        Inject params from inject method and saves states params in component state
        """
        # Inject params from inject method
        # if signature(init_method) == self._jembe_init_signature:
        if not hasattr(self, "_jembe_injected_params_names"):
            params_to_inject = self.inject()
            self._jembe_injected_params_names = list(params_to_inject.keys())
            for name, value in params_to_inject.items():
                if current_app.debug and name in kwargs:
                    current_app.logger.warning(
                        "Injecting already set param {} in component {}".format(
                            name, self._config.full_name
                        )
                    )
                kwargs[name] = value

        # Saves states params in component state
        if not hasattr(self, "state"):
            # only top most class in hieararchy sets componentState
            self.state = ComponentState(
                **{
                    spn: kwargs.get(
                        spn, self._jembe_init_signature.parameters[spn].default
                    )
                    for spn in self._jembe_state_param_names
                }
            )
            self.state._injected_params_names = self._jembe_injected_params_names
        # TODO raise Jembe error if not all required params are present
        init_method(self, *args, **kwargs)

    return decoratedInit


class ComponentMeta(ABCMeta):
    def __new__(cls, name, bases, attrs, **kwargs):
        # decorate __init__ to create self.state varible from init params
        if "__init__" in attrs:
            # attach original init signature to bu used by component config
            # to define url params
            init_signature = signature(attrs["__init__"])
            attrs["_jembe_init_signature"] = init_signature
            attrs["_jembe_state_param_names"] = tuple(
                p.name
                for p in init_signature.parameters.values()
                if p.name != "self" and not p.name.startswith("_")
            )
            attrs["__init__"] = componentInitDecorator(attrs["__init__"])
        new_class = super().__new__(cls, name, bases, dict(attrs), **kwargs)
        return new_class


class Component(metaclass=ComponentMeta):
    state: "ComponentState"
    _jembe_init_signature: "Signature"
    _jembe_state_param_names: Tuple[str, ...]
    _jembe_injected_params_names: List[str]
    _jembe_config_init_params: Dict[str, Any]
    _config: "Config"

    class Config(ComponentConfig):
        pass

    def __init__(self):
        self.__key: str = ""
        self.__exec_name: str

    @property
    def key(self) -> str:
        return self.__key

    @key.setter
    def key(self, key: str):
        self.__key = key
        # TODO update __exec_name
        # self.__update_exec_name()

    @property
    def exec_name(self) -> str:
        return self.__exec_name

    @exec_name.setter
    def exec_name(self, exec_name: str):
        # verify exec_name with _config.full_name
        if exec_name_to_full_name(exec_name) != self._config.full_name:
            raise JembeError(
                "Invalid exec_name {} for {}".format(exec_name, self._config.full_name)
            )

        self.__exec_name = exec_name

        # set , __key
        name_key = exec_name.strip("/").split("/")[-1].split(".")
        if len(name_key) == 2:
            self.__key = name_key[1]

    def set_parent_exec_name(self, parent_exec_name: str):
        self.__exec_name = "{}/{}.{}".format(
            parent_exec_name, self._config.name, self.key
        )
        # TODO verify parent_exec_name with _config.full_name
        # TODO set __exec_name

    @classmethod
    def _build_exec_name(
        cls, name: str, key: str = "", parent_exec_name: str = ""
    ) -> str:
        """Build component exec name"""
        local_exec_name = name if not key else "{}.{}".format(name, key)
        return "/".join((parent_exec_name, local_exec_name))

    @property
    def url(self) -> Optional[str]:
        """
        Returns url of this component build using url_path of parent
        components and url_path of this component
        """
        return self._config.build_url(self.exec_name)

    @classmethod
    def encode_param(cls, param_name: str, param_value: Any) -> Any:
        """
        Encode state param for sending to client (encoded param will be  transformed to json).

        Encoded value (return value) should be build using only following types:

        - dict, list, tuple, str, int, float, init- & float-deriveted Enums, True, False, None

        """
        return param_value

    @classmethod
    def decode_param(cls, param_name: str, param_value: Any) -> Any:
        """
        Decode state param received via json call to be uset to initialise in __init__.
        param_value is decoded from json received from client.

        Default implemntation suports:
            - dict, list, tuple, str, int, float, init- & float-deriveted Enums, True, False, None, via
              default json decode.
            - if any other type hint (or no hint) is set for state param and we are running in 
              debug mode exception will be raised (No exception will be raised in production
              because hint checking can be expensive)
        """

        def _supported_hint(param_hint):
            # TODO Grrr not good hint checking, need to learn more before making it good
            valid_annotations = ("str", "int", "NoneType")
            if isinstance(param_hint.annotation, ForwardRef):
                return False
            elif isfunction(param_hint.annotation):
                # should handle annoation with new type
                # or raise exception
                return param_hint.annotation.__supertype__.__name__ in valid_annotations
            elif isclass(param_hint.annotation):
                return param_hint.annotation.__name__ in valid_annotations
            else:
                hint_args = get_args(param_hint.annotation)
                if not hint_args:
                    raise NotImplementedError()
                for arg in hint_args:
                    if isinstance(arg, ForwardRef):
                        return False
                    elif isfunction(arg):
                        return (
                            param_hint.annotation.__supertype__.__name__
                            in valid_annotations
                        )
                    elif isclass(arg) and not arg.__name__ in valid_annotations:
                        return False
            return True

        if current_app.debug or current_app.testing:
            if param_name in cls._jembe_init_signature.parameters:
                # check if param hint is supported
                param_hint = cls._jembe_init_signature.parameters[param_name]
                if not _supported_hint(param_hint):
                    raise JembeError(
                        "State param {} of {} with hint {} is not supported for json encode/decode "
                        "nor custom encoding/decoding logic is defined in encode_param/decode_param."
                        "Supported type hints are equivalent of: dict, list, tuple, str, int, float, "
                        "init- & float-derivated Enums, bool, Optional".format(
                            param_name, cls._config.full_name, param_hint
                        )
                    )
            else:
                raise JembeError(
                    "State param {} of {} does not have supported json encode/decode type hint "
                    "nor custom encoding/decoding logic is defined in encode_param/decode_param."
                    "Supported type hints are equivalent of: dict, list, tuple, str, int, float, "
                    "init- & float-derivated Enums, bool, Optional".format(
                        param_name, cls._config.full_name
                    )
                )

        return param_value

    def inject(self) -> Dict[str, Any]:
        """
        inject params are used to inject cross functional params into component.
        This params usually defines enviroment in which component is exected and
        are not related nor handled by parent compoenents or url params.

        Typical examples of inject params are user_id, userObject of current user usually stored
        in session. Current user language or similar that is stored in session/cookie
        or passed as header param to every request.

        Component will inject this paramas into its __init__ method, it will ignore
        existing values of params set by default, manually or via parent component. 
        If for some reason injected params are explicitly set they will be ignored in 
        production but in development warrning will be displayed. 

        inject can set any type of init param except for url param (params without default value).
        if some param is injected it value will not be send to client nor acepted from x-jembe
        http request.
        """
        return dict()

    def inject_into(self, component: "Component") -> Dict[str, Any]:
        """
        inject_into params are used to inject  params into child component.
        This params usually defines values required by child compoennt that are
        generated or optained by parent component.

        inject_into is called when child component is initialised, which can
        happend right after parent comonent is intialised or during execution
        of display on parent component.

        Typical examples of inject_into params are:
        - parent_record_id, 

        Child component will inject this paramas into its __init__ method, it will ignore
        existing values of params set by default or manualy (in template or via ajax request), 
        but will be overrriden if same param is injected by the child component. 

        If for some reason injected_into params are explicitly set manually they will be ignored in 
        production but in development warrning will be displayed. 
        Also if child component does not accept injected_into param this param will be ignored
        and during development info will be displayed.

        inject into can set any type of init param except for url param (params without default value).
        if some param is injected it value will not be send to client nor acepted from x-jembe
        http request and JembeError will be raised.
        """
        return dict()

    def isinjected(self, param_name: str) -> bool:
        return param_name in self._jembe_injected_params_names

    def display(self) -> Union[str, "Response"]:
        return self.render_template()

    def render_template(self, template: Optional[str] = None, **context) -> str:
        """Renderes jinja2 template into html, adds default context variables

        TODO 
        - context param defines additional template context variables
        - if template_name is none render default template

        TODO IF init_params are the same in two renderes of the same component
        (same full_name and same key and same init_params, excluding init params
        which name starts with underscore) then dont rerender component
        """
        context = {
            **self._get_default_template_context(),
            **context,
        }
        template = template if template else self._config.template
        return render_template(template, **context)

    def render_template_string(self, source, **context):
        """
        Renderes jinja2 template string into html, adds default context variables

        - context param defines additional template context variables


        TODO IF init_params are the same in two renderes of the same component
        (same full_name and same key and same init_params, excluding init params
        which name starts with underscore) then dont rerender component
        """
        context = {
            **self._get_default_template_context(),
            **context,
        }
        return render_template_string(source, **context)

    def _get_default_template_context(self) -> Dict[str, Any]:
        """
        returns dict with:
            - state params decomposed in context
            - and all instance variables not starting with underscore including (self.state)

        Note: decomposed state params are overiden by instnace variable if
        instance variable with same name as state param exist
        """
        return {
            # adds state params
            **self.state,
            # add instance variables not starting with underscore
            **{
                name: value
                for name, value in vars(self).items()
                if not name.startswith("_")
            },
            # add properties not starting with underscore
            # exec_name, key, url and all user defined properties
            **{
                property_name: getattr(self, property_name)
                for property_name, property in getmembers(
                    self.__class__, lambda o: isinstance(o, property)
                )
            },
            # command to render subcomponents
            "component": self._render_subcomponent_template,
        }

    def _render_subcomponent_template(
        self, name: str, *args, **kwargs
    ) -> "_SubComponentRenderer":
        return _SubComponentRenderer(self, name, args, kwargs)

    def emit(self, name: str, **params) -> "EmitCommand":
        processor = get_processor()
        emmit_command = EmitCommand(self.exec_name, name, params)
        processor.add_command(emmit_command)
        return emmit_command
