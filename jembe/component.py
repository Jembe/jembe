from typing import TYPE_CHECKING, Optional, Type, Tuple, Dict

if TYPE_CHECKING:
    from .common import ComponentRef


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
        public_actions: Optional[Tuple[str, ...]] = None,
        public_model: Optional[Tuple[str, ...]] = None,
        default_action: str = "display",
        **params,
    ):
        self.name = name
        self.template = template
        self.components = components
        self.public_actions = public_actions
        self.public_model = public_model
        self.default_action = default_action

        self._component_class: Optional[Type["Component"]]

    def _set_component_class(self, component_class: Type["Component"]):
        """
        Called by jembe processor after init to set component class that
        is using this concret config 

        usefull for setting/checking public_actions and public_model
        """
        self._component_class = component_class

    @property
    def full_name(self) -> str:
        return "/{}".format(self.name)
    
    @property
    def url_path(self) -> str:
        return "/{}".format(self.name)


class Component:
    class Config(ComponentConfig):
        pass
