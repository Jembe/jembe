import os
from flask import Flask
from jembe import Jembe
from .simple_page import SimplePage

jmb = Jembe()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping({SECRET_KEY="dev",})
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    jmb.init_app(app)
    jmb.add_page("simple_page", SimplePage)

    @app.route("/")
    def index():
        return "Index page!"

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    return app
