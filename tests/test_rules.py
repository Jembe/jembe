from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


def test_roule_routing(app: "Flask", client: "FlaskClient"):
    """Testing flask routes for adding compoent key in url_path"""
    @app.route("/test<string(minlength=0):key>")
    def test(key):
        return key

    @app.route("/test<string(minlength=0):key>/comp<string(minlength=0):key1>")
    def comp(key, key1):
        return "{} {}".format(key, key1)

    res = client.get("/test")
    assert res.data == b""
    res = client.get("/test.key")
    assert res.data == b".key"
    res = client.get("/test/comp")
    assert res.data == b" "
    res = client.get("/test/comp.k1")
    assert res.data == b" .k1"
    res = client.get("/test.k/comp")
    assert res.data == b".k "
    res = client.get("/test.k/comp.k1")
    assert res.data == b".k .k1"

