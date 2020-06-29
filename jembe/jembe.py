from typing import List, Optional, Type, Tuple, Dict, Union

__all__ = (
    "App",
    "Component",
    "page",
    "config",
    "Event",
    "action",
    "listener",
    "singleton",
)


def page(name: str, component_config: Optional["ComponentConfig"] = None):
    """Decorator that adds page to App"""
    # App.add_page(name, Page, Page.Config(**params))
    raise NotImplementedError()


def config(comoponent_conifg: "ComponentConfig"):
    """
    Decorator that adds Default init values for component
    in order to avoid overriding __init__ just to set config params

    result should be similar
    @config(default_template="test.jinja2")
    class component:
        ....
    translates into:
    class compoent:
        class config:
            def __init__(default_template="test.jinja2", **params):
            super().__init__(default_template=default_template, **params)
    """
    raise NotImplementedError()


def action():
    """
    decorator to mark method as public action inside component
    """
    # This decorator should not do anytthing except allow
    # componentconfig.set_compoenent_class to
    # recognise method as action
    pass


def listener(event_name: Optional[str] = None, source_name: Optional[str] = None):
    """
    decorator to mark method as action listener
    """
    pass


def singleton():
    """
    decorator to make class singleton

    usefull for services
    """
    pass


class App:
    """
    Represents whole jembe applictions with all its modules and pages
    """

    pages_configs: List[Tuple[Type["Component"], "ComponentConfig"]] = []

    @classmethod
    def add_page(
        cls,
        name: str,
        page_type: Type["Component"],
        page_config: Optional["ComponentConfig"] = None,
    ):
        """Adds component as root component in url_patterns"""
        if not page_config:
            cls.pages_configs.append((page_type, page_type.Config(name)))
        else:
            if page_config.name is None:
                page_config.name = name
            cls.pages_configs.append((page_type, page_config))


class ComponentConfig:
    """
    Component config must have metaclass which will "decorate" __init__
    to save raw __init__ params in ._raw_init_params to enable
    @page decorator, components config params and @config decorator to work
    """

    def __init__(
        self,
        name: Optional[str] = None,
        url_path: Optional[str] = None,
        template: Optional[str] = None,
        components: Optional[Dict[str, Tuple["Component", "ComponentConfig"]]] = None,
        public_actions: Optional[Tuple[str, ...]] = None,
        public_model: Optional[Tuple[str, ...]] = None,
        default_action: str = "display",
        **params,
    ):
        self.name = name
        self.url_path = url_path
        self.template = template
        self.components = components
        self.public_actions = public_actions
        self.public_model = public_model
        self.default_action = default_action

    def _set_component_class(self, component_class: Type["Component"]):
        """
        Called by jembe processor after init to set component class that
        is using this concret config 

        usefull for setting/checking public_actions and public_model
        """
        self.component_class = component_class
        # Using explict public_actions and public_model is better than
        # using just convenction in cases when someting special needs to be
        # done

        # if public_actions is None
        # public actions are all methos in Component marked with decorator @action
        # or whose name doesn't start with _

        # component should check is the signature (typing) of actions valid

        # if public_model is None
        # public models are all param names of init whose name doesn't start with _
        # public model must conatain all params from url_path

    def mount(self):
        """
        Preparing config for use as source of truth for all its 
        components.

        Doing all calculatio that can be done once for all components
        instances
        """
        if self.name is None:
            raise ValueError("name must be set")
        # TODO check name if its valid and can be used as url_path
        self.url_path = self.url_path if self.url_path is not None else self.name
        # self.uuid
        
        # set initialised child components configs
        self.components_configs:Dict[str, ComponentConfig] = {} 


class Component:
    """

    1. All instance variables that are defined by user and dont start with underscore are aviable in
       template context
    2. All methods defined by user that don't start with underscore are actions that can be called via ajax 
       request

    3. All paramters of __init__ method are forwarded tu client and are send back wia ajax together with call to
      any action in order to reinitialise state of the component
    4. If component is unaccessible mount should raise Error ??


    """

    class Config(ComponentConfig):
        pass

    # def __init__(self, key: Optional[Union[str, int]] = None):
    #     self.key = key
    def __init__(self):

        # Sets and updated by processor 
        # Child component created by processor when parsing url
        self.child_component:Optional["Component"] = None 
        # Child components created when rendering this component including
        # child component created by processor when parsing url if exist
        self.child_components:List["Component"] = []

    # def mount(self):
    #     pass

    def display(self):
        return self.render_template(self._config.template)

    def _render_template(self, template_name: Optional[str] = None, **context):
        """Renderes jinja2 template into html, adds default context variables
        
        - context param defines additional template context variables
        - if template_name is none render default template
        """
        pass

    def _render_template_string(self, source, **context):
        """
        Renderes jinja2 template string into html, adds default context variables

        - context param defines additional template context variables
        """
        pass

    def _get_query_param(self, param_name: str, *default_values) -> str:
        """returns http query param named param_name if exist with as string
        developr should converti it to proper type

        if query param not exist or http request is not directed primary to this compononet
        return default_values[0] or raise error"""
        return ""

    def _set_key(self, key: str) -> "Component":
        self._key = key
        return self

    def _is_requested_directly(self) -> bool:
        """Returns true if this component is directly called via http request"""
        raise NotImplementedError()


class Event:
    pass
