import os
import pytest
from jembe import Jembe
from jembe.files import Storage
from jembe.exceptions import JembeError

from flask import Flask as _Flask


class Flask(_Flask):
    testing = True
    secret_key = "test key"

class TempTestStorage(Storage):
    pass

@pytest.fixture
def app():
    app = Flask("flask_test", root_path=os.path.dirname(__file__))

    @app.errorhandler(JembeError)
    def handle_jembe_errror(error):
        app.logger.exception(error)
        return "JembeError", 500
    yield app


@pytest.fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def req_ctx(app):
    with app.test_request_context(path="/") as ctx:
        yield ctx


@pytest.fixture
def jmb(app):
    yield Jembe(app)


@pytest.fixture
def client(app):
    yield app.test_client()
