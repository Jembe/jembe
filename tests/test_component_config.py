from jembe import Component, config, redisplay, Jembe


def test_redisplay_settings(jmb: Jembe):
    @config(Component.Config(redisplay=(Component.Config.WHEN_ON_PAGE,)))
    class Comp1(Component):
        pass

    class Comp2(Component):
        @redisplay(when_on_page=True, when_state_changed=False)
        def display(self):
            return super().display()

    @jmb.page("p", Component.Config(components=dict(c1=Comp1, c2=Comp2)))
    class Page(Component):
        pass

    assert (
        jmb.components_configs["/p/c1"].redisplay
        == jmb.components_configs["/p/c2"].redisplay
    )
    assert jmb.components_configs["/p/c2"].redisplay == (Component.Config.WHEN_ON_PAGE,)
    assert jmb.components_configs["/p/c1"].redisplay == (Component.Config.WHEN_ON_PAGE,)

