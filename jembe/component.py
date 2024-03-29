from typing import (
    TYPE_CHECKING,
    Iterable,
    Optional,
    Union,
    Dict,
    Any,
    List,
    Tuple,
    Type,
)
import re
from urllib.parse import quote_plus
from functools import cached_property
from copy import deepcopy, copy
from abc import ABCMeta
from inspect import Parameter, signature, getmembers, Signature

from flask.json import dumps
from .exceptions import JembeError, NotFound, ComponentPreviousStateUnavaiableError
from flask import render_template, render_template_string, current_app
from markupsafe import Markup
from .component_config import ComponentConfig
from .app import get_processor
from .processor import (
    CallActionCommand,
    CallDisplayCommand,
    InitialiseCommand,
    EmitCommand,
)
from .common import (
    exec_name_to_full_name,
    load_param,
    dump_param,
)

if TYPE_CHECKING:
    import jembe


class ComponentState(dict):
    """
    Two instance of the same component, component with same full_name, in the same
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
            raise JembeError(f"Can't add new param '{key}' to component state {self}")
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

    def tojsondict(
        self,
        component_class: Union[Type["jembe.Component"], "jembe.Component"],
        full=False,
    ):
        return {
            k: copy(component_class.dump_init_param(k, v))
            for k, v in self.items()
            if full == True or k not in self._injected_params_names
        }


class ComponentReference:
    """
    Notes:
    usage for link:
    lamda self: self.component('name')[.jrl...]
    lambda self: self.component('/main').component('name')[.jrl|url|is_accessible]
    usage for displaying component in template:
    {{component('name')}}
    {{component('name').component('name')}} -- shuld raise exception
    usage in template to display link
    {{component('name').is_accessible}}..{{component().jrl}}...
    Add comand 'init' with same usage as component but without
    using state params of exisiting component if its on page ??


    factory class method allow use of {{component('../name')}} or {{component('/a/b/c')}}
    """

    @classmethod
    def factory(
        cls,
        caller_exec_name: Optional[str],
        name: str,
        kwargs: dict,
        merge_existing_params: bool = True,
    ) -> "ComponentReference":
        name_split = name.split("/")
        cr: Optional["ComponentReference"] = None
        if (name_split[0] == "" and len(name_split) > 2) or (  # /a/b
            name_split[0] != "" and len(name_split) > 1
        ):  # a/b ../b
            if name_split[0] == "":
                name_split = name_split[1:]
                name_split[0] = f"/{name_split[0]}"
            for pname in name_split[:-1]:
                if cr is None:
                    cr = cls(
                        caller_exec_name,
                        pname,
                        {},
                        # merge_existing_params,
                    )
                else:
                    cr = cr.component(pname)
            if cr is not None:
                cr = (
                    cr.component(name_split[-1], **kwargs)
                    if merge_existing_params
                    else cr.component_reset(name_split[-1], **kwargs)
                )
            else:
                cr = cls(
                    caller_exec_name, name_split[-1], kwargs, merge_existing_params
                )
        elif "/" not in name and "." not in name and "()" in name:
            # compoent("cancel()").is_accessible
            cr = cls(caller_exec_name, ".", dict(), merge_existing_params).call(
                name.replace("()", ""), **kwargs
            )
        else:
            cr = cls(caller_exec_name, name, kwargs, merge_existing_params)
        return cr

    def __init__(
        self,
        caller_exec_name: Optional[str],
        name: str,
        kwargs: dict,
        merge_existing_params: bool = True,
    ):
        """
        - name can be name of subcomponent or if it starts with '/' name of root component
        """
        self._key = ""

        if name == "":
            raise JembeError("Component name can't be empty string")

        if name == "." and caller_exec_name is None:
            raise JembeError(
                "ComponentReference can't be called  to reference self without caller_exec_name specified"
            )

        self.caller_exec_name = caller_exec_name
        self.name = name
        self.action = ComponentConfig.DEFAULT_DISPLAY_ACTION
        self.action_args: Tuple[Any, ...] = ()
        self.action_kwargs: dict = {}
        self.state_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        self.kwargs = {k: v for k, v in kwargs.items()}
        self.merge_existing_params = merge_existing_params

        self._component_initialise_done = False
        self._component_instance: Optional["Component"] = None
        self._is_accessible: Optional[bool] = None

        if self.caller_exec_name is None and not self.name.startswith("/"):
            raise JembeError(
                "ComponentReference can't be called with relative path without caller_exec_name specified"
            )

        if (".." in self.name and self.name != "..") or (
            "/" in self.name
            and not self.name.startswith("/")
            # and len(self.name.split("/")) == 2
        ):
            raise JembeError(
                "Component reference only supports rendering and accessing direct childs, root page or parent component"
            )

        self.root_renderer = self
        self.active_renderer = self
        self.parent_reference = self
        self._aditional_components: List["Component"] = []
        self.base_jrl = "$jmb"

    def _component(
        self, merge_existing_params, jmb_exec_name: str, **kwargs
    ) -> "jembe.ComponentReference":
        cr = ComponentReference(
            self.exec_name, jmb_exec_name, kwargs, merge_existing_params
        )
        cr.root_renderer = self.root_renderer
        cr.root_renderer.active_renderer = cr
        cr.parent_reference = self
        cr._aditional_components = self._aditional_components.copy()
        if (
            self.component_instance is not None
            and self.component_instance.exec_name not in self.processor.components
        ):
            cr._aditional_components.append(self.component_instance)
        cr.base_jrl = self.jrl
        return cr

    def component(self, jmb_exec_name: str, **kwargs) -> "jembe.ComponentReference":
        if self.action != ComponentConfig.DEFAULT_DISPLAY_ACTION:
            raise JembeError(
                f"<{str(self)}> Cant reference child component when action '{self.action}' is called"
            )
        return self._component(True, jmb_exec_name, **kwargs)

    def component_reset(
        self, jmb_exec_name: str, **kwargs
    ) -> "jembe.ComponentReference":
        return self._component(False, jmb_exec_name, **kwargs)

    def _init_component(self):
        if self._component_initialise_done:
            return
        self._component_initialise_done = True

        if not (self.name == "." and self.root_renderer == self):
            initialise_command = InitialiseCommand(
                self.exec_name, self.kwargs, self.merge_existing_params
            )
            (
                self._is_accessible,
                self._component_instance,
            ) = self.processor.execute_initialise_command_successfully(
                initialise_command, *self._aditional_components
            )

    @property
    def component_instance(self) -> Optional["jembe.Component"]:
        if self.name == "." and self.root_renderer == self:
            return self.processor.components[self.exec_name]
        else:
            self._init_component()
            return self._component_instance

    @property
    def is_accessible(self) -> bool:
        # TODO add param ignore_incoplete_params = True so that exception trown during initialise
        # becouse not all required init parameters are suplied are treated as not accessible (
        # catch exception and return False in this case)
        if self.action != ComponentConfig.DEFAULT_DISPLAY_ACTION:
            ci = self.component_instance
            if ci is None:
                current_app.logger.warning(
                    f"Component '{self.root_renderer.caller_exec_name}' can't acuire referenced component '{self.exec_name}' to check if action '{self.action}' is accessible"
                )
                return True

            return (
                self.action in ci._config.component_actions
                and self.action not in ci._jembe_disabled_actions
            )
        else:
            if self.name == ".":
                return True
            self._init_component()
            return (
                self._is_accessible == True
                and self._component_instance is not None
                and self._component_instance.ac_check()
            )

    @cached_property
    def url(self) -> str:
        if not self.is_accessible:
            raise NotFound()
        if self._aditional_components:
            backup_components = self.processor.components.copy()
            for acomp in self._aditional_components:
                self.processor.components[acomp.exec_name] = acomp
            url = self.component_instance.url  # type: ignore
            self.processor.components = backup_components
            return url
        else:
            return self.component_instance.url  # type: ignore

    @cached_property
    def jrl(self) -> str:
        """JRL of this component reference"""
        if not self.is_accessible:
            raise NotFound()
        return self._calculate_jrl()

    @cached_property
    def jrl_absolute(self) -> str:
        """JRL of this component reference including full component exec_name

        Usefull for generating links that can be passed and displayed by
        other components.
        """
        if not self.is_accessible:
            raise NotFound()
        return self._calculate_jrl(True)

    def _calculate_jrl(self, is_absolute: bool = False) -> str:
        """Returns jrl of the component reference

        Absolute jrl are in form $jmb.component(exec_name).call(action) even
        if action is on current component. Thay are usefull when link is
        created by one and passed to other component to be rendered in HTML.

        - is_absolute(bool): Should JRL include exec_path of the component.
          Default False.
        """
        name = self.name
        if is_absolute and name == ".":
            name = self.exec_name

        jrl = (
            "component{reset}('{name}'{kwargs}{key})".format(
                reset="_reset" if not self.merge_existing_params else "",
                name=name,
                key=f",key='{self.key}'" if self._key else "",
                kwargs=",{}".format(
                    re.sub(
                        '(?<!\\\\)"',
                        "'",
                        dumps(self.state_kwargs, separators=(",", ":")),
                    )
                )
                if self.state_kwargs
                else "",
            )
            if name != "."
            else ""
        )
        jrl += (
            # ".call('{name}',{{{kwargs}}},[{args}])".format(
            ".call('{name}'{kwargs})".format(
                name=self.action,
                # args=",".join((_prep_v(v) for v in self.action_args)),
                kwargs=",{}".format(
                    re.sub(
                        '(?<!\\\\)"',
                        "'",
                        dumps(self.action_kwargs, separators=(",", ":")),
                    )
                )
                if self.action_kwargs
                else "",
            )
            if self.action != ComponentConfig.DEFAULT_DISPLAY_ACTION
            else ".display()"
        )
        if jrl.startswith("."):
            jrl = jrl[1:]
        base_jrl = (
            self.base_jrl[:-10]
            if self.base_jrl.endswith(".display()")
            else self.base_jrl
        )
        return Markup(f"{base_jrl}.{jrl}")

    @cached_property
    def exec_name(self) -> str:
        if self.name == ".":
            return self.caller_exec_name  # type:ignore
        elif self.name.startswith("/"):
            return Component._build_exec_name(self.name.split("/")[1], self._key)
        elif self.caller_exec_name is not None and self.name == "..":
            caller_exec_name_split = self.caller_exec_name.split("/")
            return Component._build_exec_name(
                caller_exec_name_split[-2],
                self._key,
                "/".join(caller_exec_name_split[:-2]),
            )
        elif self.caller_exec_name is not None:
            return Component._build_exec_name(
                self.name, self._key, self.caller_exec_name
            )
        else:
            raise JembeError(
                "ComponentReference can't be called with relative path without caller_exec_name specified"
            )

    @cached_property
    def processor(self) -> "jembe.Processor":
        return get_processor()

    def execute(self):
        """Calls all necessary init, display and call components to execute this component reference
        inside current jembe processor.

        When executing chained component references first call all initialise and then all action
        commands in reverse order to avoid unecessary component renderes/displays.
        """
        if self.exec_name in self.processor.components_marked_for_removal:
            raise JembeError(
                f"Cant display component '{self.exec_name}' marked for removal in parent component template!"
            )
        current_reference = self
        reference_chain = [current_reference]
        while current_reference.parent_reference != current_reference:
            current_reference = current_reference.parent_reference
            reference_chain.append(current_reference)
        reference_chain.reverse()

        init_commands = []
        action_commands = []
        for creference in reference_chain:
            init_commands.append(
                InitialiseCommand(
                    creference.exec_name,
                    creference.kwargs,
                    creference.merge_existing_params,
                )
            )
            # call action command is put in que to be executed latter
            # if this command raises exception parent should chach it and call display
            # with appropriate template
            if creference.action == ComponentConfig.DEFAULT_DISPLAY_ACTION:
                action_commands.append(
                    CallDisplayCommand(
                        creference.exec_name,
                        not creference.merge_existing_params,
                        displayed_by_exec_name=creference.caller_exec_name,
                    )
                )
            else:
                action_commands.append(
                    CallActionCommand(
                        creference.exec_name,
                        creference.action,
                        creference.action_args,
                        creference.action_kwargs,
                    )
                )
        for init_cmd in init_commands:
            self.processor.add_command(init_cmd, end=True)
        for act_cmd in reversed(action_commands):
            self.processor.add_command(act_cmd, end=True)

    def __call__(self) -> str:
        """
        Do render

        Component initialisation must be executed in place in order to know
        will it raise exception (like NotFound, Forbidden, Unauthorized etc.)
        so that we can decide how to render template
        """
        self.execute()
        return Markup(f'<template jmb-placeholder="{self.exec_name}"></template>')

    def key(self, key: str) -> "jembe.ComponentReference":
        self._key = str(key)
        return self

    def call(self, action: str, *args, **kwargs) -> "jembe.ComponentReference":
        self.action = action
        self.action_args = args
        self.action_kwargs = kwargs
        return self

    def __html__(self):
        return self.__call__()

    def if_accessible(self) -> str:
        if self.is_accessible:
            return self.__html__()
        return ""


def component(
    jmb_exec_name: str, jmb_reset: bool = True, **kwargs
) -> "ComponentReference":
    """Creates component renderer that can be used to obtain any component url, jrl or check if it is accessible"""
    return ComponentReference.factory(None, jmb_exec_name, kwargs, not jmb_reset)


def componentInitDecorator(init_method):
    def decoratedInit(self, *args, **kwargs):
        """
        Inject params from inject method and saves states params in component state
        """
        if not hasattr(self, "state"):
            # only top most class in hieararchy sets componentState and injects from self.inject()

            # Inject params from inject method
            params_to_inject = self.inject()
            self._jembe_injected_params_names.extend(params_to_inject.keys())

            for name, value in params_to_inject.items():
                if current_app.debug and name in kwargs:
                    current_app.logger.warning(
                        f"Injecting already set param {name} in component {self._config.full_name}"
                    )
                kwargs[name] = value

            # Saves states params in component state
            self.state = ComponentState(
                **{
                    spn: kwargs.get(
                        spn, self._jembe_init_signature.parameters[spn].default
                    )
                    for spn in self._jembe_state_param_names
                }
            )
            self.state._injected_params_names = self._jembe_injected_params_names
        try:
            init_method(self, *args, **kwargs)
        except Exception as e:
            current_app.logger.warning(
                f"{self.__class__.__name__}: {e};  args={args}; kwargs={kwargs};"
            )
            raise e

    return decoratedInit


class ComponentMeta(ABCMeta):
    def __new__(cls, name, bases, attrs, **kwargs):
        # decorate __init__ to create self.state varible from init params
        if "__init__" in attrs:
            # attach original init signature to bu used by component config
            # to define url params
            init_signature = signature(attrs["__init__"])
            attrs["_jembe_init_signature"] = init_signature
            attrs["_jembe_init_param_names"] = tuple(
                p.name for p in init_signature.parameters.values() if p.name != "self"
            )
            attrs["_jembe_state_param_names"] = tuple(
                p.name
                for p in init_signature.parameters.values()
                if p.name != "self" and not p.name.startswith("_")
            )
            attrs["_jembe_state_param_default_values"] = {
                p.name: p.default
                for p in init_signature.parameters.values()
                if p.default != Parameter.empty
                and p.name != "self"
                and not p.name.startswith("_")
            }
            attrs["__init__"] = componentInitDecorator(attrs["__init__"])

        # check if inject_into is overriden
        inject_into_overriden = False
        if "inject_into" in attrs:
            inject_into_overriden = True
        else:
            for b in bases:
                if b != Component and getattr(b, "_jembe_inject_into_overriden", False):
                    inject_into_overriden = True
                    break
        attrs["_jembe_inject_into_overriden"] = inject_into_overriden

        new_class = super().__new__(cls, name, bases, dict(attrs), **kwargs)
        return new_class


class Component(metaclass=ComponentMeta):
    """Component is the primary building block for creating Web Applications using Jembe Framework.

    Component is responsible:
        - for displaying part of the web page, and
        - handling all user interaction with that part of the page.

    Component is made from two parts:
        - Python class that holds and executes application logic, and
        - associated Jinja template that renderes, component in browser;


    Component can:
        - be comined with other components in nested hirearchy to form web application;
        - execute "actions" when end user interacts with component in browser;
        - dispatch events to other components in application;
        - listen for events dispatched to them;

    .. note::

        Component behavior can be configured with Component.Config class that is initialised only once when the application starts.

    Component has **State variables**. State variables defines component state. Two instance of same component are
    equal if they are having equal state variables.


    - State variable are passed to component on its initialisation;
    - Same component with same values of state variables are considered equal (thay should display exacly same HTML in browser)
    - When value of any state variable is changed component will redisplay itself;
    - State variables are defined as arguments to __init__ method.
    - State varibales must have type annotation, and type annotation cannot be in double quotes.
    - State variables are directly accessible to JavaScript in browser;
    - State variables can be changed by JavaScript in browser cosing component to redisplay itself.

    .. code-block:: python

        @jmb.page('hello')
        class HelloWorld(Component):
            def __init__(self, name:str = "World"):
                ''' name is state variable '''
                pass

    .. code-block:: html

        <html><body>
            <h1>Hello {{name}}</h1>
            <input type="text" value="{{name}}" jmb-on:keydown.debounce="name = $self.value">

            <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        </body></html>

    .. figure:: /img/hello_world.gif
        :alt: Hello World

    **Component __init__ arguments**

    Component init argumets are used to define:

    - **state variables** and,
    - performance variables.

    **State variables** are __init__ arguments that does not start with '_' (underscore).
    State variables defines the state of the component. Two instance of the same component in the same state are
    considered equal and thay should behaive in the exacly same way.

    **Performance variables** are __init__ arguments whose name starts with underscore '_'.
    Performance variables are used to avoid unnecesary calculations or call to database, when parent component
    has already calculated or aquiried value needed by component.

    State variables without default values will become **URL arguments**. Value of Url arguments
    must be provided as part of URL (for example: https://your_site/project/project/1).
    State variables without default values, can be one of following types: int, str, URI.

    .. code-block:: python

        @jmb.page('demo')
        class CDemo(Component):
            def __init__(self, id: int, find:Optional[str] = None, _record:Optional[dict] = None):
                '''
                    - 'id' is State variable of type int.
                    - 'id' is also URL variable because it does not have default value.
                      When browser access:

                      -  https://your_site/demo/1 id will have value of 1
                      -  https://your_site/demo/2 id will have value of 2, and so on

                    - 'find' is state variable of type optional str with default value of None.
                      This variable can't be set via url like 'id'.
                    - '_record' is performance variable it is not state variable.
                '''
                if record['id'] = id:
                    # if _record is valid use it
                    self._record = record

            @property
            def record(self):
                try:
                    return self._record
                except:
                    self._record = db.session.query(Record).get(self.state.id)
                    return self._record


    Args:
        metaclass (_type_, optional): _description_. Defaults to ComponentMeta.

    Raises:
        JembeError: When something goes wrong with component initialisation
    """

    @classmethod
    def _jembe_init_(
        cls,
        _config: ComponentConfig,
        _component_exec_name: str,
        _jembe_injected_params_names: List[str],
        _jembe_merged_existing_params: bool,
        _jembe_existing_component_state: Optional["ComponentState"],
        **init_params,
    ):
        """
        Instance creation by explicitly calling __new__ and __init__
        because _config should be avaiable in __init__
        """
        component: "Component" = object.__new__(cls)
        component._jembe_component_initialising = True
        component._config = _config  # type: ignore
        component._jembe_injected_params_names = _jembe_injected_params_names
        component._jembe_merged_existing_params = _jembe_merged_existing_params
        component._jembe_existing_component_state = _jembe_existing_component_state
        component._jembe_disabled_actions = []
        component.exec_name = _component_exec_name
        component.__init__(**init_params)  # type: ignore
        # init is called after __init__ so it can access all state variables regardles if __init__ is overwriten
        component.init()
        component._jembe_component_initialising = None
        component._jembe_existing_component_state = None
        return component

    _jembe_init_signature: "Signature"
    _jembe_init_param_names: Tuple[str, ...]
    _jembe_state_param_names: Tuple[str, ...]
    _jembe_state_param_default_values: Dict[str, Any]
    _jembe_injected_params_names: List[str]
    _jembe_config_init_params: Dict[str, Any]
    _jembe_merged_existing_params: bool
    _jembe_existing_component_state: Optional["ComponentState"]
    _jembe_inject_into_overriden: bool
    _jembe_component_initialising: Optional[bool]
    _config: "Config"

    state: "ComponentState"
    _jembe_disabled_actions: List[str]

    class Config(ComponentConfig):
        """Compononent config defines behavior of all instances of component, with what is
        known at build time, like: url_path, subcomponents, name etc.

        Component can access his config instance using ``self._config``.

        Args:
            template (Optional[Union[str, Iterable[str]]], optional): Path to default template for displaying component. If not provided template name will be same as ``self.full_name`` with '.html' extension added. Defaults to None.
            components (Optional[Dict[str, jembe.ComponentRef]], optional): Subcomponent definitions. Defaults to None.
            inject_into_components (Optional[ Callable[[jembe.Component, jembe.ComponentConfig], dict] ], optional): Callable to inject __init__ paramas into subcomponents. Defaults to None.
            changes_url (bool, optional): Does this componet changes location URL when displayed on page. Defaults to True.
            url_query_params (Optional[Dict[str, str]], optional): Mapping from GET Query params to state variables allowing state variables to be set with GET Query params (?var1=value&var2=value).dict(<name of get queryparam> = <name of state variable>) . Defaults to None.
        """

        pass

    def __init__(self):
        try:
            self.__key: str = self.__key
        except:
            self.__key = ""
        self.__exec_name: str
        self.__has_action_or_listener_executed: bool = False

    def init(self):
        """
        Normalised __init__ without params definition.

        init is called after __init__ so it can access all state variables
        regardles if __init__ is overwriten.

        Executed after __init__, usefull for adding logic that should be
        executed on init but without need to rewrite/list init params.
        """
        # raise NotFound when componet is not accessible
        if not self.ac_check():
            raise self._config.DEFAULT_AC_EXCEPTION()

    @property
    def previous_state(self) -> Optional["ComponentState"]:
        """Returns previous state of the component when component state is changed in browser using javascript.

        Accesible only in ``__init__`` and ``init`` methods.
        """
        if not self._jembe_component_initialising:
            raise ComponentPreviousStateUnavaiableError(
                "Component previous state is only avaiable during "
                "component intialisation in __init__ and init methods."
            )
        return self._jembe_existing_component_state

    @property
    def key(self) -> str:
        """Returns component key.

        ``key`` can be set by parent component, allowing us to have multiple
        instance of same component in different state. Parent component
        must make sure that there is not two component with same key.

        Usefull when displaying list of records with cards.

        If we try to display multiple components in diferent state without setting key,
        only last component will be displayed overwriting all previous ones.

        Returns:
            str: component key
        """
        return self.__key

    @key.setter
    def key(self, key: str):
        self.__key = key
        # self.__dict__.pop("key", None) # delete cached property
        # TODO update __exec_name
        # self.__update_exec_name()

    @property
    def exec_name(self) -> str:
        """Uniquly identifies instance of the Component in application.

        It is created from component ``full_name`` adding all ``keys`` where necessary
        (/component1/component2.key2/component3/component4.key4).

        Returns:
            str: Component Execution Name
        """
        return self.__exec_name

    @exec_name.setter
    def exec_name(self, exec_name: str):
        # verify exec_name with _config.full_name
        if exec_name_to_full_name(exec_name) != self._config.full_name:
            raise JembeError(
                f"Invalid exec_name {exec_name} for {self._config.full_name}"
            )

        self.__exec_name = exec_name

        # set , __key
        name_key = exec_name.strip("/").split("/")[-1].split(".")
        if len(name_key) == 2:
            self.__key = name_key[1]

    @property
    def _jembe_has_action_or_listener_executed(self) -> bool:
        return self.__has_action_or_listener_executed

    @_jembe_has_action_or_listener_executed.setter
    def _jembe_has_action_or_listener_executed(self, value: bool):
        if value != True:
            raise JembeError(
                "Cannot reset action or listener execution status on component"
            )
        self.__has_action_or_listener_executed = True

    def set_parent_exec_name(self, parent_exec_name: str):
        self.__exec_name = f"{parent_exec_name}/{self._config.name}.{self.key}"
        # TODO verify parent_exec_name with _config.full_name
        # TODO set __exec_name

    @classmethod
    def _build_exec_name(
        cls, name: str, key: str = "", parent_exec_name: str = ""
    ) -> str:
        """Build component exec name"""
        local_exec_name = name if not key else f"{name}.{key}"
        return "/".join((parent_exec_name, local_exec_name))

    @property
    def url(self) -> str:
        """Returns url of this component.

        Url is build using url_path of parent components and url_path of this component
        """
        url = self._config.build_url(self.exec_name, self)
        url_get_params = []
        for url_param_name, state_param_name in self._config.url_query_params.items():
            if self.state.get(state_param_name, None) is not None:
                url_get_params.append(
                    f"{url_param_name}={quote_plus(str(self.state[state_param_name]))}"
                )
        if url_get_params:
            url = f"{url}?{'&'.join(url_get_params)}"
        return url

    @classmethod
    def dump_init_param(cls, name: str, value: Any) -> Any:
        """
        Encode state param for sending to client (dumped param will be  transformed to json).

        dumped value (return value) should be build using only following types:

        - dict, list, tuple, str, int, float, init- & float-deriveted Enums, True, False, None
        so that it can be jsonified

        """
        if name in cls._jembe_init_signature.parameters:
            try:
                param_hint = cls._jembe_init_signature.parameters[name]
                if param_hint.annotation == Parameter.empty:
                    raise ValueError("Parameter without annotation")
                return dump_param(param_hint.annotation, value)
            except Exception as e:
                if current_app.debug or current_app.testing:
                    raise JembeError(
                        f"State param {name} of {cls.__module__}.{cls.__name__} with hint {cls._jembe_init_signature.parameters[name]} is not supported for json dump/load "
                        f"nor custom encoding/decoding logic is defined in dump_init_param/load_init_param.\n ({e})\n\n "
                    )
        return value

    @classmethod
    def load_init_param(
        cls, config: "jembe.ComponentConfig", name: str, value: Any
    ) -> Any:
        """
        load and Decode init/state param received via json call to be uset to initialise in __init__.
        param_value is decoded from json received from client.

        Default implemntation suports:
            - dict, list, tuple, str, int, float, init- & float-deriveted Enums, True, False, None, via
              default json load.
            - if any other type hint (or no hint) is set for state param and we are running in
              debug mode exception will be raised (No exception will be raised in production
              because hint checking can be expensive)
        """
        if name in cls._jembe_init_signature.parameters:
            try:
                param_hint = cls._jembe_init_signature.parameters[name]
                if param_hint.annotation == Parameter.empty:
                    raise ValueError("Parameter without annotation")
                return load_param(param_hint.annotation, value)
            except ValueError as e:
                if current_app.debug or current_app.testing:
                    raise JembeError(
                        f"State param {name} of {cls.__module__}.{cls.__name__} with hint {cls._jembe_init_signature.parameters[name]} is not supported for json dump/load "
                        f"nor custom encoding/decoding logic is defined in dump_init_param/load_init_param. \n\n({e}) "
                    )
        return value

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

    def inject_into(self, cconfig: "jembe.ComponentConfig") -> Dict[str, Any]:
        """
        inject_into params are used to inject  params into child component.
        This params usually defines values required by child component that are
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
        #  Not supportting this becouse it will force reinitialise of all childrens if
        #   parent component action changes state regardles if parent injects params with
        #   this method
        return dict()

    def isinjected(self, param_name: str) -> bool:
        return param_name in self._jembe_injected_params_names

    def display(self) -> "jembe.DisplayResponse":
        return self.render_template()

    def render_template(
        self, template: Optional[Union[str, Iterable[str]]] = None, **context
    ) -> str:
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
        if not isinstance(template, str):
            template = list(template)
        # add reference to itself in context (usefull for passing parameters in macros)
        context["_context"] = context
        return render_template(template, **context)  # type:ignore

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
        # add reference to itself in context (usefull for passing parameters in macros)
        context["_context"] = context
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
            # add class variables not starting with underscore
            **{
                name: value
                for name, value in vars(self.__class__).items()
                if not name.startswith("_")
            },
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
                    self.__class__,
                    lambda o: isinstance(o, property) or isinstance(o, cached_property),
                )
                if property_name != "previous_state"
            },
            # command to render subcomponents
            "component": self._jinja2_component,
            "component_reset": self._jinja2_component_reset,
            "placeholder": self._jinja2_placeholder,
            # add helpers
            "_config": self._config,
        }

    def _component_reference(
        self,
        kwargs: Dict[str, Any],
        name: Optional[str] = None,
        merge_existing_params: bool = True,
    ) -> "jembe.ComponentReference":
        if name is None:
            try:
                return self.__prev_sub_component_renderer.active_renderer
            except AttributeError:
                raise JembeError("Previous component renderer is not set")
        else:
            self.__prev_sub_component_renderer: "ComponentReference" = (
                ComponentReference.factory(
                    self.exec_name, name, kwargs, merge_existing_params
                )
            )
            return self.__prev_sub_component_renderer

    def component(
        self, _jembe_component_name: str = ".", **kwargs
    ) -> "jembe.ComponentReference":
        return self._component_reference(kwargs, _jembe_component_name)

    def component_reset(
        self, _jmb_component_name: str = ".", **kwargs
    ) -> "jembe.ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name, False)

    def _jinja2_component(
        self, _jmb_component_name: Optional[str] = None, **kwargs
    ) -> "jembe.ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name)

    def _jinja2_component_reset(
        self, _jmb_component_name: Optional[str] = None, **kwargs
    ) -> "jembe.ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name, False)

    def _jinja2_placeholder(self, _jmb_copmonent_name: str):
        return Markup(
            f'<template jmb-placeholder-permanent="{self.exec_name}/{_jmb_copmonent_name}"></template>'
        )

    def emit(
        self, _jmb_event_name: str, _deferred: bool = False, **params
    ) -> "EmitCommand":
        """Emits event with message to other components

        Args:
            _jmb_event_name (str): event name
            _as_last (bool, optional): Emit event las when all other commands are executed. Defaults to False.
            params: message parametes passed to reciving components

        Returns:
            EmitCommand: _description_
        """
        processor = get_processor()
        emmit_command = EmitCommand(self.exec_name, _jmb_event_name, params)
        emmit_command.is_deferred = _deferred
        processor.add_command(emmit_command)
        return emmit_command

    def display_component(
        self,
        _jmb_component_name: str,
        _jmb_component_key: Optional[str] = None,
        **init_params,
    ):
        """
        Calls initCommand and displayComand of subcomponent without need to
        redisplay this commponent.
        """
        if _jmb_component_name not in self._config.components.keys():
            raise JembeError(
                f"Component '{_jmb_component_name,}' is not valid sub component of '{self._config.full_name}'!"
            )
        cr = self.component(_jmb_component_name, **init_params)
        if _jmb_component_key:
            cr.key(_jmb_component_key)
        cr.execute()

    def remove_component(
        self, _jmb_component_name: str, _jmb_component_key: Optional[str] = None
    ):
        """
        Marks component for removal from user page (will not be displayed to the user)
        without need to redisplay this entire component.

        TODO: Check if component is rendered with {{component()}} and removed, if so
        raise exception.
        """
        if _jmb_component_name not in self._config.components.keys():
            raise JembeError(
                f"Component '{_jmb_component_name}' is not valid sub component of '{self._config.full_name}'!"
            )
        processor = get_processor()
        cexec_name = "{}/{}".format(
            self.exec_name,
            _jmb_component_name
            if _jmb_component_key is None
            else "{}.{}".format(_jmb_component_name, _jmb_component_key),
        )
        self.emit("_remove", removed_exec_name=cexec_name)
        if cexec_name not in processor.components_marked_for_removal:
            processor.components_marked_for_removal.append(cexec_name)

    def get_storage(self, storage_name: Optional[str] = None) -> "jembe.Storage":
        processor = get_processor()
        return processor.jembe.get_storage(storage_name)

    def redirect_to(self, component_ref: "jembe.ComponentReference"):
        """
        Redirects request to another component removing all unecessory
        components from processing.
        """
        processor = get_processor()
        # Remove all unecessary components that should not be needed after
        # redirect by finding first component that is parent to both this compoment
        # and redirected to compomennt (have same exec_name and same state)
        # and remove all existing components and its assciated commands from
        # jembe processors
        root_cr = component_ref.root_renderer
        processor.remove_component(
            root_cr.exec_name,
            self.exec_name.startswith("{root_cr.exec_name}/"),
        )

        # Creates new commands to init and display for redirect components
        # and puts in processenig que
        component_ref.execute()

    def ac_allow(self, *action_names):
        """
        Allow execution of listed actions.
        If no acction is listed allow execution of all actions.
        """
        if len(action_names) == 0:
            self._jembe_disabled_actions = []
        else:
            for a in action_names:
                try:
                    self._jembe_disabled_actions.remove(a)
                except ValueError:
                    pass

    def ac_deny(self, *action_names):
        """
        Deny execution of listed actions.
        If no action is listed or "display" is listed
        whole component is not accesible (__init__ will raise NotFound)
        """
        if len(action_names) == 0:
            self._jembe_disabled_actions = [ComponentConfig.DEFAULT_DISPLAY_ACTION]
            for a in self._config.component_actions.keys():
                self._jembe_disabled_actions.append(a)
        else:
            for a in action_names:
                if a not in self._jembe_disabled_actions and (
                    a in self._config.component_actions.keys()
                    or a == ComponentConfig.DEFAULT_DISPLAY_ACTION
                ):
                    self._jembe_disabled_actions.append(a)

    def ac_check(self, action_name: Optional[str] = None) -> bool:
        """Check if access control rules are satisfied

        Args:
            action_name (Optional[str], optional): Check if action is accessible, when none it will check is whole component is accessible. Defaults to None.

        Returns:
            bool: returns true if action or whole compoennt is accesible
        """
        # Apply access control rules
        if ComponentConfig.DEFAULT_DISPLAY_ACTION in self._jembe_disabled_actions or (
            action_name is not None and action_name in self._jembe_disabled_actions
        ):
            return False
        return True
