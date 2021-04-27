from typing import Callable, Dict, Iterable, Optional, Tuple, Type, Union, TYPE_CHECKING
from jembe import Component, config, redisplay, Jembe

if TYPE_CHECKING:
    from flask import Response
    from jembe.component_config import RedisplayFlag, ComponentConfig
    from jembe.common import ComponentRef, DisplayResponse


def test_redisplay_settings(jmb: Jembe):
    @config(Component.Config(redisplay=(Component.Config.WHEN_ON_PAGE,)))
    class Comp1(Component):
        pass

    class Comp2(Component):
        @redisplay(when_on_page=True, when_state_changed=False)
        def display(self):
            return super().display()

    config1 = Comp1.Config._jembe_init_(
        _name="c1", _component_class=Comp1, _parent=None
    )
    config2 = Comp2.Config._jembe_init_(
        _name="c2", _component_class=Comp2, _parent=None
    )
    assert config1.redisplay == config2.redisplay
    assert config1.redisplay == (Component.Config.WHEN_ON_PAGE,)
    assert config2.redisplay == (Component.Config.WHEN_ON_PAGE,)

    @jmb.page("p", Component.Config(components=dict(c1=Comp1, c2=Comp2)))
    class Page(Component):
        pass

    assert (
        jmb.components_configs["/p/c1"].redisplay
        == jmb.components_configs["/p/c2"].redisplay
    )
    assert jmb.components_configs["/p/c2"].redisplay == (Component.Config.WHEN_ON_PAGE,)
    assert jmb.components_configs["/p/c1"].redisplay == (Component.Config.WHEN_ON_PAGE,)


def test_config_init_params(jmb: Jembe, client):
    class A(Component):
        class Config(Component.Config):
            def __init__(
                self,
                model: str,
                template: Optional[Union[str, Iterable[str]]] = None,
                components: Optional[Dict[str, "ComponentRef"]] = None,
                inject_into_components: Optional[
                    Callable[["Component", "ComponentConfig"], dict]
                ] = None,
                redisplay: Tuple["RedisplayFlag", ...] = (),
                changes_url: bool = True,
                url_query_params: Optional[Dict[str, str]] = None,
            ):
                super().__init__(
                    template=template,
                    components=components,
                    inject_into_components=inject_into_components,
                    redisplay=redisplay,
                    changes_url=changes_url,
                    url_query_params=url_query_params,
                )

        _config: Config

        def display(self) -> "DisplayResponse":
            return self.render_template_string("a")

    @config(A.Config(model="test"))
    class AA(A):
        def __init__(self):
            super().__init__()

    @jmb.page(
        "page", Component.Config(components=dict(a=AA),),
    )
    class Page(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )

    # this shuld not rise any error
    r = client.get("/page")


def test_template_config_param(jmb: Jembe):
    class A(Component):
        pass

    class B(Component):
        pass

    @jmb.page(
        "p",
        Component.Config(
            components=dict(a=A, b=(B, B.Config(template=("", "test.html")))),
            template="p.html",
        ),
    )
    class Page(Component):
        pass

    assert jmb.components_configs["/p/a"].template == ("p/a.html",)
    assert jmb.components_configs["/p/b"].template == ("p/b.html", "test.html")
    assert jmb.components_configs["/p"].template == ("p.html",)
