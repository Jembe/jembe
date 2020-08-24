import os
import pytest
from jembe import Jembe

from flask import Flask as _Flask


class Flask(_Flask):
    testing = True
    secret_key = "test key"


@pytest.fixture
def app():
    app = Flask("flask_test", root_path=os.path.dirname(__file__))
    yield app


@pytest.fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def req_ctx(app):
    with app.test_request_context() as ctx:
        yield ctx

@pytest.fixture
def jmb(app):
    yield Jembe(app)

@pytest.fixture
def client(app):
    yield app.test_client()
