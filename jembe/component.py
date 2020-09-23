from typing import TYPE_CHECKING, Optional, Union, Dict, Any, List, Tuple
from copy import deepcopy
from abc import ABCMeta
from inspect import signature
from .exceptions import JembeError
from flask import render_template, render_template_string, Markup, current_app
from .component_config import ComponentConfig
from .app import get_processor
from .processor import CallActionCommand, InitialiseCommand, EmitCommand

if TYPE_CHECKING:  # pragma: no cover
    from .common import ComponentRef
    from flask import Response
    from inspect import Signature
    from .processor import Processor


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
        self._injected_params_names:List[str] = []
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

    def tojsondict(self):
        return {k:v for k, v in self.items() if k not in self._injected_params_names}


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
        processor.add_command(
            CallActionCommand(
                component_exec_name, self.action, self.action_args, self.action_kwargs
            ),
            end=True,
        )
        return '<div jmb-placeholder="{}"></div>'.format(component_exec_name)

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
        if self._exec_name_to_full_name(exec_name) != self._config.full_name:
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
    def _exec_name_to_full_name(cls, exec_name: str) -> str:
        """
        Removes component keys from exec name to get full_name.

        keys in exec_name are separated by . (dot)
        """
        return "/".join(ck.split(".")[0] for ck in exec_name.split("/"))

    @classmethod
    def _build_exec_name(
        cls, name: str, key: str = "", parent_exec_name: str = ""
    ) -> str:
        """Build component exec name"""
        local_exec_name = name if not key else "{}.{}".format(name, key)
        return "/".join((parent_exec_name, local_exec_name))

    @classmethod
    def _is_page_exec_name(cls, exec_name: str) -> bool:
        return len(exec_name.strip("/").split("/")) == 1

    @property
    def url(self) -> Optional[str]:
        """
        Returns url of this component build using url_path of parent
        components and url_path of this component
        """
        return self._config.build_url(self.exec_name)

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

    def display(self) -> Union[str, None, "Response"]:
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
            "key": self.key,
            "exec_name": self.exec_name,
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
