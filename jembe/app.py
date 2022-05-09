from typing import Sequence, TYPE_CHECKING, Optional, Tuple, Type, List, Dict, Any
from os import path
from .defaults import (
    DEFAULT_JEMBE_MEDIA_FOLDER,
    PRIVATE_STORAGE_NAME,
    PUBLIC_STORAGE_NAME,
    TEMP_STORAGE_NAME,
)
from flask import Blueprint, request
from .processor import Processor
from .exceptions import JembeError
from flask import g, current_app
from .common import ComponentRef, exec_name_to_full_name, import_by_name


if TYPE_CHECKING:  # pragma: no cover
    import jembe
    from flask import Flask, Response


class _JembeState:
    def __init__(self, jembe: "Jembe") -> None:
        self.jembe = jembe


class Jembe:
    """Keeps track of all application Components and Storages.

    Jembe instance is initilised only once per application and its main purpose
    is to keep track of all Componets and Storages used by application itself.

    Usually you create ``Jembe`` instance and register it as Flask extension
    in ``yourproject/__init__.py``, or in ``yourproject/app.py``
    when using ``jembe startproject`` template, similar to:

    .. code-block:: python

        from flask import Flask
        from jembe import Jembe

        app = Flask(__name__)
        jmb = Jembe(app)


    Attributes:
        app:
            Optional Flask application instance.

            If Flask application instance is not provided than ``Jembe.init_app``
            method must be executed after Flask instance becomes avaiable like so:

            .. code-block:: python

                from flask import Flask
                from jembe import Jembe

                jmb = Jembe()

                def create_app(config):
                    app = Flask()
                    jmb.init_app(app)
                    return app

        storages:
            Optional Jembe storages definitions.

            Files created or uploaded by end user are saved in this storages.

            If storages are not defined than default storages configuration will be used:

            - Public storage named `public` in ``data/media/public`` directory;
            - Private storage named `private` in ``data/media/private`` directory;
            - Temporary storage named `temp` in ``data/media/temp`` directory;

            .. code-block:: python

                from jembe import DiskStorage

                # example storage configuration
                Jembe(storages=[
                    DiskStorage("public", "data/media/public"),
                    DiskStorage("private", "data/media/private", type=DiskStorage.Type.PRIVATE),
                    DiskStorage("temp", "data/media/temp", type=DiskStorage.Type.TEMP),
                ])

            If you want to change location of media folder but keep the same
            configuration of public, private and temporary storage you can
            alter Flask config variable ``JEMBE_MEDIA_FOLDER`` like so:

            .. code-block:: python
                :caption: instance/config.py

                JEMBE_MEDIA_FOLDER = "/var/yourproject/media"

            If you manually define one storage, Jembe will not add other default storages,
            and you must define all storages used by your application including at
            least one temporary storage.

    Raises:
        JembeError: When: More then one Jembe extension is initialised for a Flask instance;
            Storage is initialised before associating Jembe with Flask instance; Temporary Storage is not configured;

    Returns:
        :obj:`Jembe`: Jembe instance
    """

    X_JEMBE = "X-Jembe"
    X_RELATED_UPLOAD = "X-Jembe-Related-Upload"

    def __init__(
        self,
        app: Optional["Flask"] = None,
        storages: Optional[Sequence["jembe.Storage"]] = None,
    ):
        """Initialise jembe configuration"""
        self.__flask: "Flask"
        # all registred jembe components configs [full_name, config instance]
        self.components_configs: Dict[str, "jembe.ComponentConfig"] = {}
        # pages waiting to be registred
        self._unregistred_pages: Dict[str, "jembe.ComponentRef"] = {}

        self._storages: Dict[str, "jembe.Storage"]
        self.extensions: Dict[str, Any] = dict()
        self.initialised_extensions: List[str] = []

        from .jembe_page import JembePage

        self.add_page("jembe", JembePage)

        if app is not None:
            self.init_app(app, storages)

    @property
    def flask(self) -> Optional["Flask"]:
        """Returns associated Flask instance"""
        try:
            return self.__flask
        except AttributeError:
            return None

    def init_app(
        self, app: "Flask", storages: Optional[Sequence["jembe.Storage"]] = None
    ):
        """
        Use this callback to initialize Jembe with Flask application dynamicaly.
        """
        self.__flask = app

        # init extensions
        for k, w in self.extensions.items():
            if k not in self.initialised_extensions:
                w.do_init_jembe()
                self.initialised_extensions.append(k)

        # app.teardown_appcontext(self.teardown)
        # app.context_processor(self.template_processor)
        if "jembe" in self.__flask.extensions:
            raise JembeError(
                "Only one Jembe extension can be initialise for a Flask instance."
            )
        self.__flask.extensions["jembe"] = _JembeState(self)

        # Init storages
        self._init_storages(storages)

        # register all unregistred pages added to app before associating
        # app with flask instance
        if self._unregistred_pages:
            for name, component in self._unregistred_pages.items():
                self._register_page(name, component)
            self._unregistred_pages = {}

    def _init_storages(self, storages: Optional[Sequence["jembe.Storage"]]):
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
        component: Type["jembe.Component"],
        component_config: Optional["jembe.ComponentConfig"] = None,
    ):
        """
        Register Jembe Component as Page to Jembe instance.

        Page Component and all its sub-component will be recursivlly
        registred.
        Page component becomes avaiable under `/<name>` URL.

        Args:
            name: Unique name of the component.
            component: Component Class
            component_config: Optional instance of Component.Config to
                configure Component behavior
        """
        component_ref: ComponentRef = (
            (
                component,
                component_config,
            )
            if component_config
            else component
        )

        if self.flask is not None:
            self._register_page(name, component_ref)
        else:
            self._unregistred_pages[name] = component_ref

    def page(
        self,
        name: str,
        component_config: Optional["jembe.ComponentConfig"] = None,
    ):
        """
        A decorator that registers a Jembe Page Component.

        It does same thing as add_page but its used as deocrator:

        .. code-block:: python

            @jmb.page("simple", Component.Config(components={..}))
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
        component_refs: List[
            Tuple[str, ComponentRef, Optional["jembe.ComponentConfig"]]
        ] = [(name, component_ref, None)]
        while component_refs:
            component_name, curent_ref, parent_config = component_refs.pop(0)
            if isinstance(curent_ref, tuple):
                # create config with custom params
                component_class: Type["jembe.Component"] = (
                    curent_ref[0]
                    if not isinstance(curent_ref[0], str)
                    else import_by_name(curent_ref[0])
                )
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

    def get_component_config(self, exec_name: str) -> "jembe.ComponentConfig":
        try:
            return self.components_configs[exec_name_to_full_name(exec_name)]
        except KeyError:
            raise JembeError(
                "Component {} does not exist".format(exec_name_to_full_name(exec_name))
            )

    def get_storage_by_type(
        self, storage_type: "jembe.Storage.Type", storage_name: Optional[str] = None
    ) -> "jembe.Storage":
        """
        Returns first storage of the provided type if it exists.

        Args:
            storage_type: Storage type one of `Storage.Type.PRIVATE`, `Storage.Type.PUBLIC` or `Storage.Type.TEMP`
            storage_name: Optional name of the storage
        Raises:
            JembeError: When storage does not exists
        """
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

    def get_storages(self) -> List["jembe.Storage"]:
        """Returns list of all configured Jembe storages"""
        return list(self._storages.values())

    def get_storage(self, storage_name: str) -> "jembe.Storage":
        """Returns storage by storage name

        Args:
            storage_name (str): Name of the storage

        Raises:
            JembeError: Storage does not exist
        """
        try:
            return self._storages[storage_name]
        except KeyError:
            raise JembeError("Storage '{}' does not exist".format(storage_name))


def get_processor():
    """Returns current Jembe Processors

    Raises:
        JembeError: When current HTTP request can't be handled by jembe processor or when Jembe extension is not initialised
    """
    if "jmb_processor" not in g:
        if not (request.endpoint and request.blueprint):
            raise JembeError("Request {} can't be handled by jembe processor")
        component_full_name = request.endpoint[len(request.blueprint) + 1 :]
        jembe_state = current_app.extensions.get("jembe", None)
        if jembe_state is None:
            raise JembeError("Jembe extension is not initialised")
        return Processor(jembe_state.jembe, component_full_name, request)
    return g.jmb_processor


def get_jembe() -> "Jembe":
    """Returns current Jembe instance

    Raises:
        JembeError: When Jembe extension is not initialised
    """

    jembe_state = current_app.extensions.get("jembe", None)
    if jembe_state is None:
        raise JembeError("Jembe extension is not initialised")
    return jembe_state.jembe


def get_storage(storage_name: str) -> "jembe.Storage":
    """Returns storage by storage name from current Jembe instance

    Args:
        storage_name (str): Name of the storage

    Raises:
        JembeError: Storage does not exist
    """
    try:
        return get_processor().jembe.get_storage(storage_name)
    except JembeError:
        # cant get processor becouse we are not in valid requst context
        # return storage of default jembe app
        return get_jembe().get_storage(storage_name)


def get_storages() -> List["jembe.Storage"]:
    """Returns list of all registred Storages in current Jembe instance"""
    return get_processor().jembe.get_storages()


def get_temp_storage(storage_name: Optional[str] = None) -> "jembe.Storage":
    """Returns temporary storage of current Jembe instance.

    When storage_name is provided it will return temporary storage with given name,
    otherwise it will return first temporary storage from storage list.

    Args:
        storage_name (Optional[str], optional): Name of the temporary storage. Defaults to None.
    """
    from .files import Storage

    return get_processor().jembe.get_storage_by_type(Storage.Type.TEMP, storage_name)


def get_public_storage(storage_name: Optional[str] = None) -> "jembe.Storage":
    """Returns public storage of current Jembe instance.

    When storage_name is provided it will return public storage with given name,
    otherwise it will return first public storage from storage list.

    Args:
        storage_name (Optional[str], optional): Name of the public storage. Defaults to None.
    """
    from .files import Storage

    return get_processor().jembe.get_storage_by_type(Storage.Type.PUBLIC, storage_name)


def get_private_storage(storage_name: Optional[str] = None) -> "jembe.Storage":
    """Returns private storage of current Jembe instance.

    When storage_name is provided it will return private storage with given name,
    otherwise it will return first private storage from storage list.

    Args:
        storage_name (Optional[str], optional): Name of the private storage. Defaults to None.
    """
    from .files import Storage

    return get_processor().jembe.get_storage_by_type(Storage.Type.PRIVATE, storage_name)


def jembe_master_view(**kwargs) -> "Response":
    """Process HTTP request with Jembe Processors"""
    return get_processor().process_request().build_response()
