from typing import (
    Iterable,
    TYPE_CHECKING,
    Optional,
    Union,
    Dict,
    Any,
    List,
    Tuple,
    get_args,
    get_origin,
    Type,
)
from collections.abc import Sequence as collectionsSequence
from urllib.parse import quote_plus
from functools import cached_property
from copy import deepcopy, copy
from abc import ABCMeta
from inspect import Parameter, isclass, signature, getmembers, Signature
from .exceptions import JembeError, NotFound
from flask import render_template, render_template_string, current_app
from markupsafe import Markup
from .component_config import ComponentConfig
from .app import get_processor
from .processor import (
    CallActionCommand,
    CallDisplayCommand,
    InitialiseCommand,
    EmitCommand,
    Processor,
)
from .common import (
    JembeInitParamSupport,
    exec_name_to_full_name,
    get_annotation_type,
    DisplayResponse,
)
from .files import Storage


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

    def tojsondict(
        self, component_class: Union[Type["Component"], "Component"], full=False
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
    usage for displaying compoennt in template:
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
                name_split[0] = "/{}".format(name_split[0])
            for pname in name_split[:-1]:
                if cr is None:
                    cr = cls(
                        caller_exec_name,
                        pname,
                        {},
                        merge_existing_params,
                    )
                else:
                    cr = cr.component(pname)
            cr = (
                cr.component(name_split[-1], **kwargs)
                if cr is not None
                else cls(
                    caller_exec_name, name_split[-1], kwargs, merge_existing_params
                )
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
        self.kwargs = kwargs
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
        self._aditional_components: List["Component"] = []
        self.base_jrl = "$jmb"

    def _component(
        self, merge_existing_params, jmb_exec_name: str, **kwargs
    ) -> "ComponentReference":
        cr = ComponentReference(
            self.exec_name, jmb_exec_name, kwargs, merge_existing_params
        )
        cr.root_renderer = self.root_renderer
        cr.root_renderer.active_renderer = cr
        cr._aditional_components = self._aditional_components.copy()
        if (
            self.component_instance is not None
            and self.component_instance.exec_name not in self.processor.components
        ):
            cr._aditional_components.append(self.component_instance)
        cr.base_jrl = self.jrl
        return cr

    def component(self, jmb_exec_name: str, **kwargs) -> "ComponentReference":
        if self.action != ComponentConfig.DEFAULT_DISPLAY_ACTION:
            raise JembeError(
                "<{}> Cant reference child component when action '{}' is called".format(
                    str(self), self.action
                )
            )
        return self._component(True, jmb_exec_name, **kwargs)

    def component_reset(self, jmb_exec_name: str, **kwargs) -> "ComponentReference":
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
    def component_instance(self) -> Optional["Component"]:
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
                    "Component '{}' can't acuire referenced component '{}' to check if action '{}' is accessible".format(
                        self.root_renderer.caller_exec_name, self.exec_name, self.action
                    )
                )
                return True
            return self.action not in ci._jembe_disabled_actions
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
        if not self.is_accessible:
            raise NotFound()

        def _prep_v(v):
            if isinstance(v, bool):
                return "true" if v else "false"
            elif isinstance(v, (int, float)):
                return v
            return "'{}'".format(v)

        jrl = (
            "component{reset}('{name}'{kwargs}{key})".format(
                reset="_reset" if not self.merge_existing_params else "",
                name=self.name,
                key=",key='{}'".format(self._key) if self._key else "",
                kwargs=",{{{}}}".format(
                    ",".join(
                        (
                            "{}:{}".format(k, _prep_v(v))
                            for k, v in self.kwargs.items()
                            if not k.startswith("_")
                        )
                    )
                )
                if self.kwargs
                else "",
            )
            if self.name != "."
            else ""
        )
        jrl += (
            # ".call('{name}',{{{kwargs}}},[{args}])".format(
            ".call('{name}',{{{kwargs}}})".format(
                name=self.action,
                # args=",".join((_prep_v(v) for v in self.action_args)),
                kwargs=",".join(
                    (
                        "{}:{}".format(k, _prep_v(v))
                        for k, v in self.action_kwargs.items()
                    )
                ),
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
        return Markup("{}.{}".format(base_jrl, jrl))

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
    def processor(self) -> Processor:
        return get_processor()

    def __call__(self) -> str:
        """
        Do render

        Component initialisation must be executed in place in order to know
        will it raise exception (like NotFound, Forbidden, Unauthorized etc.)
        so that we can decide how to render template
        """
        self.processor.add_command(
            InitialiseCommand(self.exec_name, self.kwargs, self.merge_existing_params),
            end=True,
        )
        # self._component_instance = None  # stop using component from is_accessible check

        # call action command is put in que to be executed latter
        # if this command raises exception parent should chach it and call display
        # with appropriate template
        if self.action == ComponentConfig.DEFAULT_DISPLAY_ACTION:
            self.processor.add_command(
                CallDisplayCommand(self.exec_name, not self.merge_existing_params),
                end=True,
            )
        else:
            self.processor.add_command(
                CallActionCommand(
                    self.exec_name,
                    self.action,
                    self.action_args,
                    self.action_kwargs,
                ),
                end=True,
            )
        return Markup(
            '<template jmb-placeholder="{}"></template>'.format(self.exec_name)
        )

    def key(self, key: str) -> "ComponentReference":
        self._key = key
        return self

    def call(self, action: str, *args, **kwargs) -> "ComponentReference":
        self.action = action
        self.action_args = args
        self.action_kwargs = kwargs
        return self

    def __html__(self):
        return self.__call__()


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
                        "Injecting already set param {} in component {}".format(
                            name, self._config.full_name
                        )
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
                "{}: {};  args={}; kwargs={};".format(
                    self.__class__.__name__, e, args, kwargs
                )
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
    @classmethod
    def _jembe_init_(
        cls,
        _config: ComponentConfig,
        _component_exec_name: str,
        _jembe_injected_params_names: List[str],
        _jembe_merged_existing_params: bool,
        **init_params
    ):
        """
        Instance creation by explicitly calling __new__ and __init__
        because _config should be avaiable in __init__
        """
        component: "Component" = object.__new__(cls)
        component._config = _config  # type: ignore
        component._jembe_injected_params_names = _jembe_injected_params_names
        component._jembe_merged_existing_params = _jembe_merged_existing_params
        component._jembe_disabled_actions = []
        component.exec_name = _component_exec_name
        component.__init__(**init_params)  # type: ignore
        component.init()
        return component

    _jembe_init_signature: "Signature"
    _jembe_init_param_names: Tuple[str, ...]
    _jembe_state_param_names: Tuple[str, ...]
    _jembe_state_param_default_values: Dict[str, Any]
    _jembe_injected_params_names: List[str]
    _jembe_config_init_params: Dict[str, Any]
    _jembe_merged_existing_params: bool
    _jembe_inject_into_overriden: bool
    _config: "Config"

    state: "ComponentState"
    _jembe_disabled_actions: List[str]

    class Config(ComponentConfig):
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

        Executed after __init__, usefull for adding logic that should be
        executed on init but without need to rewrite/list init params.
        """
        pass

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

    @property
    def has_action_or_listener_executed(self) -> bool:
        return self.__has_action_or_listener_executed

    @has_action_or_listener_executed.setter
    def has_action_or_listener_executed(self, value: bool):
        if value != True:
            raise JembeError(
                "Cannot reset action or listener execution status on component"
            )
        self.__has_action_or_listener_executed = True

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
    def url(self) -> str:
        """
        Returns url of this component build using url_path of parent
        components and url_path of this component
        """
        url = self._config.build_url(self.exec_name, self)
        url_get_params = []
        for url_param_name, state_param_name in self._config.url_query_params.items():
            if self.state.get(state_param_name, None) is not None:
                url_get_params.append(
                    "{}={}".format(
                        url_param_name, quote_plus(str(self.state[state_param_name]))
                    )
                )
        if url_get_params:
            url = "{}?{}".format(url, "&".join(url_get_params))
        return url

    @classmethod
    def dump_init_param(cls, name: str, value: Any) -> Any:
        """
        Encode state param for sending to client (dumped param will be  transformed to json).

        dumped value (return value) should be build using only following types:

        - dict, list, tuple, str, int, float, init- & float-deriveted Enums, True, False, None
        so that it can be jsonified

        """

        def _dump_supported_types(value, annotation):
            atype, is_optional = get_annotation_type(annotation)
            try:
                if atype == set or get_origin(atype) == set:
                    return None if (is_optional and value is None) else list(value)
                if atype == list or get_origin(atype) == list:
                    # TODO support tuple, dict etc.
                    el_annotation = get_args(atype)[0]
                    return (
                        None
                        if (is_optional and value is None)
                        else list(
                            _dump_supported_types(v, el_annotation) for v in value
                        )
                    )
                elif (
                    atype == JembeInitParamSupport
                    or (isclass(atype) and issubclass(atype, JembeInitParamSupport))
                    or (
                        isclass(get_origin(atype))
                        and issubclass(get_origin(atype), JembeInitParamSupport)
                    )
                    or isinstance(value, JembeInitParamSupport)
                ):
                    return (
                        None
                        if (is_optional and value is None)
                        else atype.dump_init_param(value)
                    )
            except Exception as e:
                raise ValueError(e)
            return value

        if name in cls._jembe_init_signature.parameters:
            try:
                param_hint = cls._jembe_init_signature.parameters[name]
                if param_hint.annotation == Parameter.empty:
                    raise ValueError("Parameter without annotation")
                return _dump_supported_types(value, param_hint.annotation)
            except ValueError as e:
                if current_app.debug or current_app.testing:
                    raise JembeError(
                        "State param {} of {}.{} with hint {} is not supported for json dump/load "
                        "nor custom encoding/decoding logic is defined in dump_init_param/load_init_param. ({}) ".format(
                            name,
                            cls.__module__,
                            cls.__name__,
                            cls._jembe_init_signature.parameters[name],
                            e,
                        )
                    )
        return value

    @classmethod
    def load_init_param(cls, config: "ComponentConfig", name: str, value: Any) -> Any:
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

        def _load_supported_types(value, annotation):
            """ returns loaded value or raise ValueError"""
            # TODO add support for multiple annotation types Union[a,b,c] etc

            atype, is_optional = get_annotation_type(annotation)
            try:
                if atype == bool:
                    return None if (is_optional and value is None) else bool(value)
                elif atype == int:
                    return None if (is_optional and value is None) else int(value)
                elif atype == str:
                    return None if (is_optional and value is None) else str(value)
                elif atype == float:
                    return None if (is_optional and value is None) else float(value)
                elif atype == dict or get_origin(atype) == dict:
                    # TODO recursive dict
                    return None if (is_optional and value is None) else dict(value)
                elif atype == tuple or get_origin(atype) == tuple:
                    # TODO recursive tuple
                    return None if (is_optional and value is None) else tuple(value)
                elif atype == list or get_origin(atype) == list:
                    el_annotation = get_args(atype)[0]
                    return (
                        None
                        if (is_optional and value is None)
                        else list(
                            _load_supported_types(v, el_annotation) for v in value
                        )
                    )
                elif atype == set or get_origin(atype) == set:
                    # TODO recursive set
                    return None if (is_optional and value is None) else set(value)
                elif get_origin(atype) == collectionsSequence:
                    # TODO recursive collection
                    return None if (is_optional and value is None) else tuple(value)
                elif (
                    atype == JembeInitParamSupport
                    or (isclass(atype) and issubclass(atype, JembeInitParamSupport))
                    or (
                        isclass(get_origin(atype))
                        and issubclass(get_origin(atype), JembeInitParamSupport)
                    )
                ):
                    if is_optional and value is None:
                        return None
                    elif isinstance(value, atype):
                        return value.load_init_param(value)
                    else:
                        return atype.load_init_param(value)
            except Exception as e:
                raise ValueError(e)

            raise ValueError("Unsuported annotation type {}".format(annotation))

        if name in cls._jembe_init_signature.parameters:
            try:
                param_hint = cls._jembe_init_signature.parameters[name]
                if param_hint.annotation == Parameter.empty:
                    raise ValueError("Parameter without annotation")
                return _load_supported_types(value, param_hint.annotation)
            except ValueError as e:
                if current_app.debug or current_app.testing:
                    raise JembeError(
                        "State param {} of {}.{} with hint {} is not supported for json dump/load "
                        "nor custom encoding/decoding logic is defined in dump_init_param/load_init_param. ({}) ".format(
                            name,
                            cls.__module__,
                            cls.__name__,
                            cls._jembe_init_signature.parameters[name],
                            e,
                        )
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

    def inject_into(self, cconfig: "ComponentConfig") -> Dict[str, Any]:
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
        #  Not supportting this becouse it will force reinitialise of all childrens if
        #   parent component action changes state regardles if parent injects params with
        #   this method
        return dict()

    def isinjected(self, param_name: str) -> bool:
        return param_name in self._jembe_injected_params_names

    def display(self) -> "DisplayResponse":
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
                    self.__class__,
                    lambda o: isinstance(o, property) or isinstance(o, cached_property),
                )
            },
            # command to render subcomponents
            "component": self._jinja2_component,
            "component_reset": self._jinja2_component_reset,
            # add helpers
            "_config": self._config,
        }

    def _component_reference(
        self,
        kwargs: Dict[str, Any],
        name: Optional[str] = None,
        merge_existing_params: bool = True,
    ) -> "ComponentReference":
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
        self, _jmb_component_name: str = ".", **kwargs
    ) -> "ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name)

    def component_reset(
        self, _jmb_component_name: str = ".", **kwargs
    ) -> "ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name, False)

    def _jinja2_component(
        self, _jmb_component_name: Optional[str] = None, **kwargs
    ) -> "ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name)

    def _jinja2_component_reset(
        self, _jmb_component_name: Optional[str] = None, **kwargs
    ) -> "ComponentReference":
        return self._component_reference(kwargs, _jmb_component_name, False)

    def emit(self, name: str, **params) -> "EmitCommand":
        processor = get_processor()
        emmit_command = EmitCommand(self.exec_name, name, params)
        processor.add_command(emmit_command)
        return emmit_command

    def get_storage(self, storage_name: Optional[str] = None) -> "Storage":
        processor = get_processor()
        return processor.jembe.get_storage(storage_name)

    def redirect_to(self, component_ref: "ComponentReference"):
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
            self.exec_name.startswith("{}/".format(root_cr.exec_name)),
        )

        # Creates new commands to init and display for redirect components
        # and puts in processenig que
        component_ref()

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
        """
        Apply access control rules
        """
        if ComponentConfig.DEFAULT_DISPLAY_ACTION in self._jembe_disabled_actions:
            return False
        return action_name not in self._jembe_disabled_actions
