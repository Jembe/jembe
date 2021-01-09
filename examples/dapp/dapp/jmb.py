from examples.dapp.instance.config import JEMBE_UPLOAD_FOLDER
from jembe.files import Storage
from typing import TYPE_CHECKING, Type
from jembe import Jembe
from flask import current_app

if TYPE_CHECKING:
    from flask import Flask

__all__ = ("jmb", "init_jembe")


jmb = Jembe()


def init_jembe(app: "Flask"):
    jmb.init_app(app)
