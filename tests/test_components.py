from typing import TYPE_CHECKING, Optional
from jembe import Component
from flask import json
from jembe import action


def test_counter(jmb, client):
    class Counter(Component):
        def __init__(self, value: int = 0):
            super().__init__()

        @action
        def increase(self):
            self.state.value += 1

        def display(self):
            return self.render_template_string(
                """<div>Count: {{value}}</div> <a jmb:click="increase()">increase</a>"""
            )

    @jmb.page("cpage", Component.Config(components={"counter": Counter}))
    class CPage(Component):
        def display(self):
            return self.render_template_string(
                """<html><head></head><body>{{component("counter")}}</body></html>"""
            )

    # call page
    counter0_page_html = b"""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
<html jmb:name="/cpage" jmb:state="{}" jmb:url="/cpage"><head></head><body><div jmb:name="/cpage/counter" jmb:state=\'{"value":0}\' jmb:url="/cpage/counter"><div>Count: 0</div> <a jmb:click="increase()">increase</a></div></body></html>"""
    r = client.get("/cpage")
    assert r.status_code == 200
    assert r.data == counter0_page_html

    # call counter
    r = client.get("/cpage/counter")
    assert r.status_code == 200
    assert r.data == counter0_page_html

    # increase counter
    ajax_post_data = json.dumps(
        dict(
            components=[
                dict(execName="/cpage", state=dict()),
                dict(execName="/cpage/counter", state=dict(value=0)),
            ],
            commands=[
                dict(
                    type="call",
                    componentExecName="/cpage/counter",
                    actionName="increase",
                    args=list(),
                    kwargs=dict(),
                )
            ],
        )
    )
    r = client.post("/cpage/counter", data=ajax_post_data, headers={"x-jembe": True})
    assert r.status_code == 200

    ajax_response_data = json.loads(r.data)
    counter1_html = """<div>Count: 1</div> <a jmb:click="increase()">increase</a>"""
    assert len(ajax_response_data) == 1
    assert ajax_response_data[0]["execName"] == "/cpage/counter"
    assert ajax_response_data[0]["state"] == {"value": 1}
    assert ajax_response_data[0]["dom"] == counter1_html
    assert ajax_response_data[0]["url"] == "/cpage/counter"

    ajax_post_data2 = json.dumps(
        dict(
            components=[
                dict(execName="/cpage", state=dict()),
                dict(execName="/cpage/counter", state=dict(value=0)),
            ],
            commands=[
                dict(
                    type="call",
                    componentExecName="/cpage/counter",
                    actionName="increase",
                    args=list(),
                    kwargs=dict(),
                ),
                dict(
                    type="call",
                    componentExecName="/cpage",
                    actionName="display",
                    args=list(),
                    kwargs=dict(),
                ),
            ],
        )
    )
    r = client.post("/cpage", data=ajax_post_data2, headers={"x-jembe": True})
    assert r.status_code == 200

    ajax_response_data = json.loads(r.data)
    counter1_page_html = """<html><head></head><body><div jmb-placeholder="/cpage/counter"></div></body></html>"""
    assert len(ajax_response_data) == 2
    assert ajax_response_data[0]["execName"] == "/cpage/counter"
    assert ajax_response_data[0]["state"] == {"value": 1}
    assert ajax_response_data[0]["dom"] == counter1_html
    assert ajax_response_data[0]["url"] == "/cpage/counter"
    assert ajax_response_data[1]["execName"] == "/cpage"
    assert ajax_response_data[1]["state"] == {}
    assert ajax_response_data[1]["dom"] == counter1_page_html
    assert ajax_response_data[1]["url"] == "/cpage"


def test_multi_counter(jmb, client):
    class Counter(Component):
        def __init__(self, value: int = 0, increment: int = 1):
            super().__init__()

        @action
        def increase(self):
            self.state.value += self.state.increment

        @action
        def set_increment(self, increment: int):
            self.state.increment = increment

        def display(self):
            return self.render_template_string(
                """<div>Count: {{value}}</div>"""
                """<input jmb:change="set_increment($elm.value)" value="{{increment}}">"""
                """<a jmb:click="increase()">increase</a>"""
            )

    @jmb.page("cpage", Component.Config(components={"counter": Counter}))
    class CPage(Component):
        def display(self):
            return self.render_template_string(
                """<html><head></head><body>"""
                """{{component("counter").key("first")}}"""
                """{{component("counter").key("second")}}"""
                """{{component("counter").key("third")}}"""
                """</body></html>"""
            )

    # display page with counters
    r = client.get("/cpage")
    assert r.status_code == 200
    test_r_data = (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n'
        """<html jmb:name="/cpage" jmb:state="{}" jmb:url="/cpage"><head></head><body>"""
        """<div jmb:name="/cpage/counter.first" jmb:state=\'{"increment":1,"value":0}\' jmb:url="/cpage/counter.first">"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb:name="/cpage/counter.second" jmb:state=\'{"increment":1,"value":0}\' jmb:url="/cpage/counter.second">"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb:name="/cpage/counter.third" jmb:state=\'{"increment":1,"value":0}\' jmb:url="/cpage/counter.third">"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """</body></html>"""
    ).encode('utf-8')
    assert r.data == test_r_data
    # display second counter and build page
    # increase first counter - ajax simulate
    # increase second counter - ajax simulate
    # change first counter increment - ajax simulate
    # change second counter increment - ajax simulate


# TODO test counter with configurable increment
# TODO
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
