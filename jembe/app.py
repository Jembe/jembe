from typing import Sequence, TYPE_CHECKING, Optional, Tuple, Type, List, Dict
from flask import Blueprint, request
from .processor import Processor
from .exceptions import JembeError
from .files import Storage
from flask import g
from .common import ComponentRef, exec_name_to_full_name, import_by_name


if TYPE_CHECKING:  # pragma: no cover
    from flask import Flask, Request, Response
    from .component_config import ComponentConfig
    from .component import Component


jembe: "Jembe"


class Jembe:
    """
    This class is used to configure Jembe pages and Flask integration.
    """

    X_JEMBE = "X-Jembe"

    def __init__(
        self,
        app: Optional["Flask"] = None,
        storages: Optional[Sequence["Storage"]] = None,
    ):
        """Initialise jembe configuration"""
        self.__flask: "Flask"
        # all registred jembe components configs [full_name, config instance]
        self.components_configs: Dict[str, "ComponentConfig"] = {}
        # pages waiting to be registred
        self._unregistred_pages: Dict[str, ComponentRef] = {}

        self._storages: Dict[str, "Storage"]

        from .jembe_page import JembePage

        self.add_page("jembe", JembePage)

        if app is not None:
            self.init_app(app, storages)

    @property
    def flask(self) -> Optional["Flask"]:
        try:
            return self.__flask
        except AttributeError:
            return None
            # raise JembeError(
            #     "Jembe app is not initilised with flask app. Call init_app first."
            # )

    def init_app(self, app: "Flask", storages: Optional[Sequence["Storage"]] = None):
        """
        This callback is used to initialize an applicaiton for the use
        with Jembe components.
        """
        global jembe
        jembe = self
        # app.teardown_appcontext(self.teardown)
        # app.context_processor(self.template_processor)
        if storages is None and not hasattr(self, "_storages"):
            upload_folder = app.config.get("JEMBE_UPLOAD_FOLDER", "../data/media")
            storages = [
                Storage("public", "{}/public".format(upload_folder)),
                Storage(
                    "private",
                    "{}/private".format(upload_folder),
                    type=Storage.Type.PRIVATE,
                ),
                Storage("tmp", "{}/temp".format(upload_folder), type=Storage.Type.TEMP),
            ]
        if storages is not None:
            self._storages = {s.name: s for s in storages}

        self.__flask = app
        if self._unregistred_pages:
            for name, component in self._unregistred_pages.items():
                self._register_page(name, component)
            self._unregistred_pages = {}

    def add_page(
        self,
        name: str,
        component: Type["Component"],
        component_config: Optional["ComponentConfig"] = None,
    ):

        component_ref: ComponentRef = (
            component,
            component_config,
        ) if component_config else component

        if self.flask is not None:
            self._register_page(name, component_ref)
        else:
            self._unregistred_pages[name] = component_ref

    def page(
        self, name: str, component_config: Optional["ComponentConfig"] = None,
    ):
        """
        A decorator that is used to register a jembe page commponent.
        It does same thing as add_page but is intended for decorator usage::

            @jmb.page("page", Component.Config(components={..}))
            class SimplePage(Component):
                pass
        """

        def decorator(component):
            self.add_page(name, component, component_config)
            return component

        return decorator

    def _register_page(self, name: str, component_ref: ComponentRef):
        if self.flask is None:  # pragma: no cover
            raise NotImplementedError()

        # go down component hiearchy
        bp: Optional["Blueprint"] = None
        component_refs: List[Tuple[str, ComponentRef, Optional["ComponentConfig"]]] = [
            (name, component_ref, None)
        ]
        while component_refs:
            component_name, curent_ref, parent_config = component_refs.pop(0)
            if isinstance(curent_ref, tuple):
                # create config with custom params
                component_class: Type["Component"] = curent_ref[0] if not isinstance(
                    curent_ref[0], str
                ) else import_by_name(curent_ref[0])
                curent_ref_params = (
                    curent_ref[1]
                    if isinstance(curent_ref[1], dict)
                    else curent_ref[1]._raw_init_params
                )
                component_config = component_class.Config._jembe_init_(
                    _name=component_name,
                    _parent=parent_config,
                    _component_class=component_class,
                    **curent_ref_params,
                )
            else:
                # create config with default params
                component_class = (
                    curent_ref
                    if not isinstance(curent_ref, str)
                    else import_by_name(curent_ref)
                )
                component_config = component_class.Config._jembe_init_(
                    _name=component_name,
                    _parent=parent_config,
                    _component_class=component_class,
                )
            # fill components_configs
            self.components_configs[component_config.full_name] = component_config

            if bp is None:
                bp = Blueprint(
                    component_name,
                    component_class.__module__,
                    template_folder="templates",
                    static_folder="static",
                    static_url_path="/{}/static".format(component_name),
                )

            bp.add_url_rule(
                component_config.url_path,
                component_config.full_name,
                jembe_master_view,
                methods=["GET", "POST"],
            )
            component_config.endpoint = "{}.{}".format(
                bp.name, component_config.full_name
            )

            if component_config.components:
                component_refs.extend(
                    (name, cref, component_config)
                    for name, cref in component_config.components.items()
                )

        if bp:
            self.flask.register_blueprint(bp)

    def get_component_config(self, exec_name: str) -> "ComponentConfig":
        try:
            return self.components_configs[exec_name_to_full_name(exec_name)]
        except KeyError:
            raise JembeError(
                "Component {} does not exist".format(exec_name_to_full_name(exec_name))
            )

    def get_storage(self, storage_name: Optional[str] = None) -> "Storage":
        try:
            if storage_name is None:
                storage_name = list(self._storages.keys())[0]
            return self._storages[storage_name]
        except (KeyError, IndexError):
            raise JembeError("Storage '{}' does not exist".format(storage_name))


def get_processor():
    if "jmb_processor" not in g:
        global jembe
        if not (request.endpoint and request.blueprint):
            raise JembeError("Request {} can't be handled by jembe processor")
        component_full_name = request.endpoint[len(request.blueprint) + 1 :]
        g.jmb_processor = Processor(jembe, component_full_name, request)
    return g.jmb_processor


def jembe_master_view(**kwargs) -> "Response":
    return get_processor().process_request().build_response()
