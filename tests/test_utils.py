from jembe.utils import page_url
from typing import TYPE_CHECKING
from jembe import Component, page_url

if TYPE_CHECKING:
    from jembe import Jembe


def test_page_url_on_page(jmb: "Jembe", req_ctx):
    class AComponent(Component):
        pass

    class BComponent(Component):
        def __init__(self, b1: int) -> None:
            super().__init__()

    @jmb.page(
        "simple_page", Component.Config(components=dict(a=AComponent, b=BComponent))
    )
    class SimplePage(Component):
        pass

    with req_ctx:
        assert page_url("simple_page") == "/simple_page"
        assert page_url("simple_page.key1") == "/simple_page.key1"
        assert page_url("simple_page/a.key2") == "/simple_page/a.key2"
        assert page_url("simple_page/b", [{}, {"b1": 1}]) == "/simple_page/b/1"
