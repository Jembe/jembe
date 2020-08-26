from typing import TYPE_CHECKING, Optional, Union, Tuple, Type, List, Dict
from flask import Blueprint, request
from .component import Component
from .processor import Processor
from .errors import JembeError

if TYPE_CHECKING:
    from .common import ComponentRef
    from flask import Flask, Request, Response
    from .component import ComponentConfig


jembe: "Jembe"


class Jembe:
    """
    This class is used to configure Jembe pages and Flask integration.
    """

    def __init__(self, app: Optional["Flask"] = None):
        """Initialise jembe configuration"""
        self.flask: Optional["Flask"] = None
        # all registred jembe components configs [full_name, config instance]
        self.components_configs: Dict[str, "ComponentConfig"] = {}
        # pages waiting to be registred
        self._unregistred_pages: Dict[str, "ComponentRef"] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: "Flask"):
        """
        This callback is used to initialize an applicaiton for the use
        with Jembe components.
        """
        global jembe
        jembe = self

        self.flask = app
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

        component_ref: "ComponentRef" = (
            component,
            component_config,
        ) if component_config else component

        if self.flask is not None:
            self._register_page(name, component_ref)
        else:
            self._unregistred_pages[name] = component_ref

    def page(
        self,
        name: str,
        component_config: Optional["ComponentConfig"] = None,
    ):
        """
        A decorator that is used to register a jembe page commponent.
        It does same thing as add_page but is intended for decorator usage::

            @jmb.page("page", Component.Config(components={..}))
            class SimplePage(Component):
                pass
        """
        def decorator(component):
            self.add_page(name, component ,component_config)
            return component
        return decorator

    def _register_page(self, name: str, component_ref: "ComponentRef"):
        if self.flask is None:
            raise NotImplementedError()
        # fill components_configs
        # TODO handle config with custom config default values
        if isinstance(component_ref, tuple):
            # create config with custom params
            page = component_ref[0]
            config = page.Config(
                **{**component_ref[1]._raw_init_params, "name": name}  # type:ignore
            )
        elif issubclass(component_ref, Component):
            # create config with default params
            page = component_ref
            config = page.Config(name=name)

        # accosciate component with config and vice verse
        # config will set its remaining params reading component classs description
        config.component_class = page

        # TODO go down component hiearchy
        bp = Blueprint(name, page.__module__)
        page_url_path = config.url_path

        self.components_configs[config.full_name] = config
        bp.add_url_rule(
            config.url_path[len(page_url_path) :],
            config.full_name,
            jembe_master_view,
            methods=["GET", "POST"],
        )
        self.flask.register_blueprint(bp, url_prefix=config.url_path)
        # TODO register with route


def jembe_master_view(**kwargs) -> "Response":
    global jembe
    if not (request.endpoint and request.blueprint):
        raise JembeError("Request {} can't be handled by jembe processor")
    component_full_name = request.endpoint[len(request.blueprint) + 1 :]
    processor = Processor(jembe, component_full_name, request)
    return processor.process_request()
