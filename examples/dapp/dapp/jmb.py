from typing import TYPE_CHECKING
from jembe import Jembe

if TYPE_CHECKING:
    from flask import Flask

__all__ = ("jmb", "init_jembe")

jmb = Jembe()


def init_jembe(app: "Flask"):
    jmb.init_app(app)
