from typing import Callable, Dict, Optional, Tuple, Type, Union, TYPE_CHECKING
from jembe import Component, config, redisplay, Jembe

if TYPE_CHECKING:
    from flask import Response
    from jembe.component_config import CConfigRedisplayFlag, ComponentConfig
    from jembe.common import ComponentRef


def test_redisplay_settings(jmb: Jembe):
    @config(Component.Config(redisplay=(Component.Config.WHEN_ON_PAGE,)))
    class Comp1(Component):
        pass

    class Comp2(Component):
        @redisplay(when_on_page=True, when_state_changed=False)
        def display(self):
            return super().display()

    config1 = Comp1.Config(name="c1", _component_class=Comp1)
    config2 = Comp2.Config(name="c2", _component_class=Comp2)
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
                model:str,
                name: Optional[str] = None,
                template: Optional[str] = None,
                components: Optional[Dict[str, "ComponentRef"]] = None,
                inject_into_components: Optional[
                    Callable[["Component", "ComponentConfig"], dict]
                ] = None,
                redisplay: Tuple["CConfigRedisplayFlag", ...] = (),
                changes_url: bool = True,
                url_query_params: Optional[Dict[str, str]] = None,
                _component_class: Optional[Type["Component"]] = None,
                _parent: Optional["ComponentConfig"] = None,
            ):
                super().__init__(
                    name=name,
                    template=template,
                    components=components,
                    inject_into_components=inject_into_components,
                    redisplay=redisplay,
                    changes_url=changes_url,
                    url_query_params=url_query_params,
                    _component_class=_component_class,
                    _parent=_parent,
                )
        _config: Config

        def display(self) -> Union[str, "Response"]:
            return self.render_template_string("a")

    @config(A.Config(model='test'))
    class AA(A):
        def __init__(self):
            super().__init__()

    @jmb.page(
        "page",
        Component.Config(
            components=dict(a=AA),
        ),
    )
    class Page(Component):
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )
    # this shuld not rise any error
    r = client.get("/page")
