from typing import TYPE_CHECKING
from flask import redirect
from jembe import page_url

if TYPE_CHECKING:
    from flask import Flask

def init_views(app:"Flask"):
    """Example how to add regular routes unrelated to Jembe pages"""

    @app.route("/")
    def index():
        """Redirect to jembe page"""
        return redirect(page_url("/simple_page"))

    @app.route("/hello")
    def hello():
        return "Hello, World!"