from jembe import Component


def test_simple_page(jmb, client):
    class SimplePage(Component):
        pass

    jmb.add_page("simple_page", SimplePage)
    r = client.get("/simple_page")
    assert r.status_code == 200
    assert b"<h1>Simple page</h1>" in r.data
    assert b'<html lang="en" jmb:name="/simple_page" jmb:data="{}"' in r.data


def test_empty_page(jmb, client):
    class EmptyPage(Component):
        def display(self):
            return self.render_template_string("")

    jmb.add_page("page", EmptyPage)
    r = client.get("/page")
    assert r.status_code == 200
    assert b'<html jmb:name="/page" jmb:data="{}">' in r.data
    assert b"<div></div>" in r.data


def test_simple_page_with_custom_template(jmb, client):
    class SimplePage(Component):
        pass

    jmb.add_page(
        "simple_page",
        SimplePage,
        SimplePage.Config(template="simple_page_custom.jinja2"),
    )

    r = client.get("/simple_page")
    assert r.status_code == 200
    assert b"<h1>Custom simple page</h1>" in r.data


def test_page_with_template(jmb, client):
    class Page(Component):
        class Config(Component.Config):
            def __init__(self, template="simple_page_custom.jinja2", **params):
                super().__init__(template=template, **params)

    jmb.add_page("page", Page)
    r = client.get("/page")
    assert r.status_code == 200
    assert b"<h1>Custom simple page</h1>" in r.data


def test_page_with_decorator(jmb, client):
    @jmb.page("welcome")
    class WelcomePage(Component):
        pass

    @jmb.page("hello", Component.Config(template="simple_page.jinja2"))
    class HelloPage(Component):
        pass

    r = client.get("/welcome")
    assert r.status_code == 200
    assert b"<h1>Welcome</h1>" in r.data

    r = client.get("/hello")
    assert r.status_code == 200
    assert b"<h1>Simple page</h1>" in r.data

def test_blog_post_page(jmb, client):
    @jmb.page("blogpost")
    class BlogPost(Component):
        def __init__(self, id:int):
            self.id = id

        def display(self):
            return self.render_template_string(
                """
                <html>
                <head></head>
                <body>Blog post id == {{id}}</body>
                </html>
                """
            )

    r = client.get("/blogpost/1")
    assert r.status_code == 200
    assert b'Blog post id == 1' in r.data