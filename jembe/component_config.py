from typing import TYPE_CHECKING, Optional, Type, Dict, List
from abc import ABCMeta
from .errors import JembeError

if TYPE_CHECKING:
    from .component import Component
    from .common import ComponentRef


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
    _raw_init_params:dict

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
