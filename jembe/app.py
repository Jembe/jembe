from typing import TYPE_CHECKING, Optional, Union, Tuple, Type, List, Dict
from .component import Component
from flask import Blueprint, request

if TYPE_CHECKING:
    from .common import ComponentRef
    from flask import Flask
    from .component import ComponentConfig


class Jembe:
    """
    This class is used to configure Jembe pages and Flask integration.
    """

    def __init__(self, app: Optional["Flask"] = None):
        """Initialise jembe configuration"""
        self._flask: Optional["Flask"] = None
        # all registred jembe components configs [full_name, config instance]
        self._components_configs: Dict[str, "ComponentConfig"] = {}
        # pages waiting to be registred
        self._unregistred_pages: Dict[str, "ComponentRef"] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: "Flask"):
        """
        This callback is used to initialize an applicaiton for the use
        with Jembe components.
        """
        self._flask = app
        if self._unregistred_pages:
            for name, component in self._unregistred_pages.items():
                self._register_page(name, component)
            self._unregistred_pages = {}

    def add_page(
        self, name: str, component: "ComponentRef",
    ):
        if self._flask is not None:
            self._register_page(name, component)
        else:
            self._unregistred_pages[name] = component

    def _register_page(self, name: str, page: "ComponentRef"):
        if self._flask is None:
            raise NotImplementedError()
        # fill _components_configs
        # TODO go down component hiearchy
        # TODO handle config with custom config default values
        if isinstance(page, tuple):
            raise NotImplementedError()
        elif issubclass(page, Component):
            bp = Blueprint(name, page.__module__)
            config = page.Config(name)
            page_url_path = config.url_path

            self._components_configs[name] = config
            bp.add_url_rule(
                config.url_path[len(page_url_path):],
                config.full_name,
                jembe_master_view,
                methods=["GET", "POST"],
            )
            self._flask.register_blueprint(bp, url_prefix=config.url_path)
            # TODO register with route


def jembe_master_view(*args, **kwargs):
    # TODO use partial to provide full_name of the component
    print(*args, **kwargs)
    print(request)
    raise NotImplementedError()
