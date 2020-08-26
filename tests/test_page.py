from typing import TYPE_CHECKING, Optional
from jembe import Component
# from jembe import action, listener
# from jembe.utils import build_url

if TYPE_CHECKING:
    from uuid import UUID
    # from jembe import Event


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
        def __init__(self, id: int):
            self.id = id
            super().__init__()

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
    assert b"Blog post id == 1" in r.data


# #TODO do counter test before blog test 
# def test_blog(jmb, client):
#     # TODO create mock post class with mock blog posts
#     class ViewBlogPost(Component):
#         def __init__(self, uuid: "UUID"):
#             self.uuid = uuid
#             self.title = "Blog post title"
#             self.content = "Blog post content"
#             super().__init__()

#         def display(self):
#             return self.render_template_string(
#                 """
#                 <div>
#                     <h2>{{uuid}} {{title}}</h2>
#                     <div>{{content}}</div>
#                     <a jmb:click="$emit_up('close')">Back</a>
#                 </div>
#             """
#             )

#         @jmb.page("blog", Component.Config(components={"post": ViewBlogPost}))
#         class BlogPage(Component):
#             def __init__(
#                 self,
#                 render_post: bool = False,
#                 order_by: Optional[str] = None,
#                 page_size: Optional[int] = None,
#                 page: Optional[int] = None,
#             ):
#                 self.state.order_by = (
#                     order_by
#                     if order_by is not None
#                     else self.get_query_param("o", "-id")
#                 )
#                 self.state.page_size = (
#                     page_size
#                     if page_size is not None
#                     else self.get_query_param("s", 10)
#                 )
#                 self.state.page = (
#                     page if page is not None else self.get_query_param("p", 1)
#                 )
#                 super().__init__()

#             def url(self) -> str:
#                 """
#                 bulding url (window.location) in order to allow navigation bach forward
#                 and sharing urls
#                 """
#                 return build_url(
#                     super.url(),
#                     o=self.state.order_by,
#                     s=self.state.page_size,
#                     p=self.state.page,
#                 )

#             @action
#             def next_page(self):
#                 self.state.order_by += 1
#                 return self.display()

#             @action
#             def prev_page(self):
#                 self.state.order_by -= 1
#                 return self.display()

#             @listener("_render", child=True)
#             def on_render_post(self, event: "Event"):
#                 self.state.render_post = True

#             @listener("close", child=True)
#             def on_post_close(self, event:"Event"):
#                 self.state.render_post = False
#                 return self.display()
            
#             def display(self):
#                 if self.state.render_post:
#                     return self.render_template_string(
#                         """
#                         <html>
#                         <head>
#                             <title>Blog</title>
#                         </head>
#                         <body>
#                             {{component("post")}}
#                         </body>
#                         </html>
#                         """
#                     )
#                 else:
#                     self.posts = []
#                     return self.render_template_string(
#                         """
#                         <html>
#                         <head>
#                             <title>Blog</title>
#                         </head>
#                         <body>
#                             <ul>
#                                 {% for post in posts %}
#                                 <li>
#                                     <a jmb:click="$component('post', uuid=post.uuid)">
#                                         {{post.title}}
#                                     </a>
#                                 </li>
#                                 {% endfor %}
#                             </ul>
#                         </body>
#                         </html>
#                         """
#                     )

#     # TODO create tests for 
#     # displaying blog lists with jmb:click navigation
#     # displaying blog post with jmb:click back event
#     # calling blog with direct request
#     # calling post with direct request
#     # calling post with ajax request
#     # calling calling back event
#     # incoplete ajax calls should return badrequest
#     assert False == True