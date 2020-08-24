from typing import TYPE_CHECKING, Optional, Type, Tuple, Dict, List, Union
from .errors import JembeError
from flask import render_template, render_template_string

if TYPE_CHECKING:
    from .common import ComponentRef
    from flask import Response


class ComponentConfig:
    """
    Compononent config defines behavior of all instances of component that
    are known at build time, like: url_path, subcomponents, name etc.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        template: Optional[str] = None,
        components: Optional[Dict[str, "ComponentRef",]] = None,
        **params,
    ):
        self.name = name
        self.template = (
            template if template is not None else self._get_default_template_name()
        )
        self.components = components
        self.public_model: List[str] = []
        self.default_action: str = "display"
        self.public_actions: List[str] = [self.default_action]

        self._component_class: Optional[Type["Component"]]
        self._parent: Optional["ComponentConfig"] = None

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
        Called by jembe app after init to set component class that
        is using this concret config 

        usefull for setting/checking public_actions and public_model
        """
        self._component_class = component_class

    @property
    def parent(self) -> Optional["ComponentConfig"]:
        return self._parent

    @parent.setter
    def parent(self, parent: "ComponentConfig"):
        """
        Called by jembe app after init to set parent componet config
        """
        self._parent = parent

    @property
    def full_name(self) -> str:
        return "/{}".format(self.name)

    @property
    def url_path(self) -> str:
        return "/{}".format(self.name)

    def _get_default_template_name(self) -> str:
        return "{}.jinja2".format(self.full_name.strip("/"))


class Component:
    class Config(ComponentConfig):
        pass

    def __init__(self):
        self.__config: Optional[Config] = None

    @property
    def _config(self) -> Config:
        if self.__config is None:
            raise JembeError("_config is not set for component {}".format(self))
        return self.__config

    @_config.setter
    def _config(self, config: Config):
        self.__config = config

    @property
    def key(self) -> str:
        return ""

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
            # TODO add instance variables not starting with underscore
            # TODO add init_params
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
            # TODO add instance variables not starting with underscore
            # TODO add init_params
            **context,
        }
        return render_template_string(source, **context)

