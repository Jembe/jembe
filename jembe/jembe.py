from typing import List, Optional, Type, Tuple, Dict, Union, Sequence

__all__ = (
    "App",
    "Component",
    "Processor",
    "page",
    "config",
    "Event",
    "action",
    "listener",
    "singleton",
    "execute_last",
)


def deferred_action(after: Optional[str] = None, before: Optional[str] = None):
    """
    """
    raise NotImplementedError()


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


def action(
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
    # This decorator should not do anytthing except allow
    # componentconfig.set_compoenent_class to
    # recognise method as action
    pass


def listener(
    event_name: Optional[str] = None,
    source_name: Optional[Union[str, Sequence[str]]] = None,
    children: Optional[bool] = None,
    child: Optional[bool] = None,
    parents: Optional[bool] = None,
    parent: Optional[bool] = None,
    siblings: Optional[bool] = None,
):
    """
    decorator to mark method as action listener
    source_name = relative source name 

    if any of paramters child, childs, parent, parents and siblings is provided
    than additonal filtering is enabled 
    children - execute for any children
    child - execute for direct child only
    parents - execute for any parents action
    parent - executef for direct parent only
    siblings - execute for any sibling action

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
    Compononent config defines behavior of all instances of component that
    are known at build time, like: url_path, subcomponents, name etc.

    Component config must have metaclass which will "decorate" __init__
    to save raw __init__ params in ._raw_init_params to enable
    @page decorator, components config params and @config decorator to work
    """

    def __init__(
        self,
        name: Optional[str] = None,
        url_path: Optional[str] = None,
        template: Optional[str] = None,
        components: Optional[
            Dict[str, Union[Tuple["Component", "ComponentConfig"], "Component"]]
        ] = None,
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
        self.components_configs: Dict[str, ComponentConfig] = {}


class Component:
    """
    Represents UI self suficient component with its HTML representations and
    behaviors.

    1. All instance variables that are defined by user and dont start with 
        underscore are aviable in template context
    2. All methods decorated with @action or defined in Component.Config(public_actions) 
        are actions that can be called via ajax request

    3. All paramters of __init__ method that don't begin with underscore
        or whose name is listed Component.Config(public_model)
        are forwarded tu client and are send back wia ajax together 
        with call to any action in order to reinitialise state of the component
    4. If component is unaccessible __init__ should raise Error ??
    """

    class Config(ComponentConfig):
        pass

    # def __init__(self, key: Optional[Union[str, int]] = None):
    #     self.key = key
    def __init__(self):
        """
        __init__ parameters if exist should be runtime parameters like:
        currnet record id, current user etc.

        Paramters whose name doesn't begin with underscore are send back and
        forth via ajax request in order to reinitialise current state of the component.

        Parameters whose name doesn't begin with underscore and thay DO NOT have
        default value (*args) are used to build url_path if url_path is not provided.

        Parameters whose name begins with underscore "_" are so called
        performance parameters and should be obtainable from state parameters
        of __init__. Thay are used to avoid doing same calculations multiple times
        by different components. 

        For example if record is already obtained from database calling edit component
        with EditRecordComponent.__init__(record_id=record.id, _record=record)
        should avoid aditionally quering database.
        """

        # Sets and updated by processor
        # Child component created by processor when parsing url
        self.child_component: Optional["Component"] = None
        # Child components created when rendering this component including
        # child component created by processor when parsing url if exist
        self.child_components: List["Component"] = []

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

    def get_query_param(self, param_name: str, *default_values) -> str:
        """
        returns http query param named param_name if exist with as string
        developr should converti it to proper type

        if query param not exist or http request is not directed primary to 
        this compononet return default_values[0] or raise error
        """
        raise NotImplementedError()
        # return ""

    def _set_key(self, key: str) -> "Component":
        self._key = key
        return self

    def is_ajax(self) -> bool:
        """REturns if initial request is ajax request"""
        raise NotImplementedError()

    def url(self) -> str:
        """
        Returns url of this component build using url_path of parent
        components and url_path of this component
        """
        raise NotImplementedError()


class Event:
    def __init__(self, source:"Component"):
        self.source = source


class Processor:
    """
    1. Will use deapest component.url from all components on the page as window.location
    2. When any component action or listener returns template string default 
        action (display) will not be called instead returned template string
        will be used to render compononet 
    """

    pass

