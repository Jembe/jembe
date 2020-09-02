from typing import TYPE_CHECKING, Optional, Union, Dict, Any, List, Tuple
from abc import ABCMeta
from inspect import signature
from .errors import JembeError
from flask import render_template, render_template_string, Markup
from .component_config import ComponentConfig
from .app import get_processor
from .processor import CallCommand, InitialiseCommand

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
        if name not in self.keys():
            raise JembeError("Can't set arbitrary attribute to component state")
        self[name] = value
        # return super().__setattr__(name, value)


class _SubComponentRenderer:
    def __init__(self, component: "Component", name: str, **kwargs):
        self.component = component
        self.name = name
        self._key = ""
        self.action = ComponentConfig.DEFAULT_DISPLAY_ACTION
        self.action_args: Tuple[Any, ...] = ()
        self.action_kwargs: dict = {}
        self.kwargs = kwargs

    def __call__(self) -> str:
        """Do render"""
        processor = get_processor()
        component_exec_name = Component._build_exec_name(
            self.name, self._key, self.component.exec_name
        )
        processor.commands.append(
            CallCommand(
                component_exec_name, self.action, self.action_args, self.action_kwargs
            )
        )
        if not component_exec_name in processor.components:
            # create new component if component with same exec_name
            # does not exist
            processor.commands.append(
                InitialiseCommand(component_exec_name, self.kwargs)
            )
        else:
            # if state params are same continue
            # else raise jembeerror until find better solution
            component = processor.components[component_exec_name]
            for key, value in component.state.items():
                if key in self.kwargs and value != self.kwargs[key]:
                    raise JembeError(
                        "Rendering component with different state params from existing compoenent {}".format(
                            component
                        )
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
        """Saves states params in component state """
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
        self.__exec_name = exec_name
        # TODO verify exec_name with _config.full_name
        # TODO set , __key

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
            "component": self._render_subcomponent_template,
        }

    def _render_subcomponent_template(
        self, name: str, *args, **kwargs
    ) -> "_SubComponentRenderer":
        return _SubComponentRenderer(self, name, *args, **kwargs)

