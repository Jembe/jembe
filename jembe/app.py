from typing import Sequence, TYPE_CHECKING, Optional, Tuple, Type, List, Dict
from os import path
from .defaults import (
    DEFAULT_JEMBE_MEDIA_FOLDER,
    DEFAULT_TEMP_STORAGE_UPLOAD_FOLDER,
    PRIVATE_STORAGE_NAME,
    PUBLIC_STORAGE_NAME,
    TEMP_STORAGE_NAME,
)
from flask import Blueprint, request
from .processor import Processor
from .exceptions import JembeError
from flask import g
from .common import ComponentRef, exec_name_to_full_name, import_by_name


if TYPE_CHECKING:  # pragma: no cover
    from flask import Flask, Response
    from .component_config import ComponentConfig
    from .component import Component
    from .files import Storage


jembe: "Jembe"


class Jembe:
    """
    This class is used to configure Jembe pages and Flask integration.
    """

    X_JEMBE = "X-Jembe"
    X_RELATED_UPLOAD = "X-Jembe-Related-Upload"

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

        self.__flask = app

        # Init storages
        self._init_storages(storages)

        # register all unregistred pages added to app before associating
        # app with flask instance
        if self._unregistred_pages:
            for name, component in self._unregistred_pages.items():
                self._register_page(name, component)
            self._unregistred_pages = {}

    def _init_storages(self, storages: Optional[Sequence["Storage"]]):
        if not self.flask:
            raise JembeError(
                "Cannot initialise storages before "
                "initialising jembe with flask instance"
            )
        from .files import DiskStorage

        if storages is None and not hasattr(self, "_storages"):
            # initialise default storages

            media_folder = self.flask.config.get(
                "JEMBE_MEDIA_FOLDER", DEFAULT_JEMBE_MEDIA_FOLDER
            )
            storages = [
                DiskStorage(PUBLIC_STORAGE_NAME, path.join(media_folder, "public")),
                DiskStorage(
                    PRIVATE_STORAGE_NAME,
                    path.join(media_folder, "private"),
                    type=DiskStorage.Type.PRIVATE,
                ),
                DiskStorage(
                    TEMP_STORAGE_NAME,
                    path.join(media_folder, "temp"),
                    type=DiskStorage.Type.TEMP,
                ),
            ]
        if storages is None or not next(
            (s for s in storages if s.type == DiskStorage.Type.TEMP), False
        ):
            raise JembeError(
                "Temporary Storage must be configured in order for file upload to work"
            )

        self._storages = {s.name: s for s in storages}

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

    def get_storage_by_type(
        self, storage_type: "Storage.Type", storage_name: Optional[str] = None
    ) -> "Storage":
        # returs named storage if exist and it's right type
        if storage_name is not None:
            try:
                if self._storages[storage_name].type == storage_type:
                    return self._storages[storage_name]
                else:
                    raise JembeError(
                        "Storage '{}' is not '{}'".format(
                            storage_name, storage_type.value
                        )
                    )
            except KeyError:
                raise JembeError("Storage '{}' does not exist".format(storage_name))

        # returns first storage of adequate type
        try:
            return next(s for s in self._storages.values() if s.type == storage_type)
        except StopIteration:
            raise JembeError(
                "Storage of type '{}' does not exist".format(storage_type.value)
            )

    def get_storages(self) -> List["Storage"]:
        return list(self._storages.values())

    def get_storage(self, storage_name: str) -> "Storage":
        try:
            return self._storages[storage_name]
        except KeyError:
            raise JembeError("Storage '{}' does not exist".format(storage_name))


def get_processor():
    if "jmb_processor" not in g:
        global jembe
        if not (request.endpoint and request.blueprint):
            raise JembeError("Request {} can't be handled by jembe processor")
        component_full_name = request.endpoint[len(request.blueprint) + 1 :]
        return Processor(jembe, component_full_name, request)
    return g.jmb_processor


def get_storage(storage_name: str) -> "Storage":
    return get_processor().jembe.get_storage(storage_name)


def get_storages() -> List["Storage"]:
    return get_processor().jembe.get_storages()


def get_temp_storage(storage_name: Optional[str] = None) -> "Storage":
    from .files import Storage

    return get_processor().jembe.get_storage_by_type(Storage.Type.TEMP, storage_name)


def get_public_storage(storage_name: Optional[str] = None) -> "Storage":
    from .files import Storage

    return get_processor().jembe.get_storage_by_type(Storage.Type.PUBLIC, storage_name)


def get_private_storage(storage_name: Optional[str] = None) -> "Storage":
    from .files import Storage

    return get_processor().jembe.get_storage_by_type(Storage.Type.PRIVATE, storage_name)


def jembe_master_view(**kwargs) -> "Response":
    return get_processor().process_request().build_response()
