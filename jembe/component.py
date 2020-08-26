from typing import TYPE_CHECKING, Optional, Union, Dict, Any
from .errors import JembeError
from flask import render_template, render_template_string
from .component_config import ComponentConfig

if TYPE_CHECKING:
    from .common import ComponentRef
    from flask import Response


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
        returns dict with all instance variables not starting with underscore
        and init_params dict
        """
        # TODO add init_params
        # add instance variables not starting with underscore
        return {name:value for name, value in vars(self).items() if not name.startswith("_")}

