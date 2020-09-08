from typing import TYPE_CHECKING, Optional, Tuple
from jembe import Component
from flask import json
from jembe import action, listener


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
                dict(execName="/cpage", state=dict(), url="/cpage"),
                dict(
                    execName="/cpage/counter", state=dict(value=0), url="/cpage/counter"
                ),
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
                dict(execName="/cpage", state=dict(), url="/cpage"),
                dict(
                    execName="/cpage/counter", state=dict(value=0), url="/cpage/counter"
                ),
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
    assert len(ajax_response_data) == 1
    assert ajax_response_data[0]["execName"] == "/cpage/counter"
    assert ajax_response_data[0]["state"] == {"value": 1}
    assert ajax_response_data[0]["dom"] == counter1_html
    assert ajax_response_data[0]["url"] == "/cpage/counter"


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
    ).encode("utf-8")
    assert r.data == test_r_data

    # display second counter and build page
    r = client.get("/cpage/counter.second")
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
    ).encode("utf-8")
    assert r.data == test_r_data
   
    # increase first counter - ajax simulate
    r = client.post(
        "/cpage/counter.first",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(), url="/cpage"),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(increment=1, value=0),
                        url="/cpage/counter.first",
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(increment=1, value=0),
                        url="/cpage/counter.second",
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(increment=1, value=0),
                        url="/cpage/counter.third",
                    ),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.first",
                        actionName="increase",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 1
    assert ajax_response_data[0]["execName"] == "/cpage/counter.first"
    assert ajax_response_data[0]["state"] == dict(increment=1, value=1)
    assert ajax_response_data[0]["dom"] == (
        """<div>Count: 1</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[0]["url"] == "/cpage/counter.first"
    # increase second counter - ajax simulate without components
    # when calling from navigation for example
    # this call should never be fired without commands to intialise
    # /cpage/counter.second parents but processor should be able to handle this
    # initialising /cpage with url_params ...
    r = client.post(
        "/cpage/counter.second",
        data=json.dumps(
            dict(
                components=[],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.second",
                        actionName="increase",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 4
    assert ajax_response_data[0]["execName"] == "/cpage/counter.second"
    assert ajax_response_data[0]["state"] == dict(increment=1, value=1)
    assert ajax_response_data[0]["dom"] == (
        """<div>Count: 1</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[0]["url"] == "/cpage/counter.second"
    assert ajax_response_data[1]["execName"] == "/cpage"
    assert ajax_response_data[1]["state"] == dict()
    assert ajax_response_data[1]["dom"] == (
        """<html><head></head><body>"""
        """<div jmb-placeholder="/cpage/counter.first"></div>"""
        """<div jmb-placeholder="/cpage/counter.second"></div>"""
        """<div jmb-placeholder="/cpage/counter.third"></div>"""
        """</body></html>"""
    )
    assert ajax_response_data[1]["url"] == "/cpage"
    assert ajax_response_data[2]["execName"] == "/cpage/counter.first"
    assert ajax_response_data[2]["state"] == dict(increment=1, value=0)
    assert ajax_response_data[2]["dom"] == (
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[2]["url"] == "/cpage/counter.first"
    assert ajax_response_data[3]["execName"] == "/cpage/counter.third"
    assert ajax_response_data[3]["state"] == dict(increment=1, value=0)
    assert ajax_response_data[3]["dom"] == (
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[3]["url"] == "/cpage/counter.third"
    # change third counter increment and icrease it - ajax simulate
    r = client.post(
        "/cpage/counter.first",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(), url="/cpage"),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(increment=1, value=1),
                        url="/cpage/counter.first",
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(increment=1, value=2),
                        url="/cpage/counter.second",
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(increment=1, value=3),
                        url="/cpage/counter.third",
                    ),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.third",
                        actionName="set_increment",
                        args=[10],
                        kwargs=dict(),
                    ),
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.third",
                        actionName="increase",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 1
    assert ajax_response_data[0]["execName"] == "/cpage/counter.third"
    assert ajax_response_data[0]["state"] == dict(increment=10, value=13)
    assert ajax_response_data[0]["dom"] == (
        """<div>Count: 13</div>"""
        """<input jmb:change="set_increment($elm.value)" value="10">"""
        """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[0]["url"] == "/cpage/counter.third"


def test_multi_counter_intercommunication_events(jmb, client):
    class Counter(Component):
        def __init__(
            self, value: int = 0, connected_counter_exec_name: Optional[str] = None
        ):
            super().__init__()

        @action
        def increase(self):
            self.state.value += 1
            if self.state.connected_counter_exec_name:
                self.emit("increase").to(self.state.connected_counter_exec_name)

        @listener(event="increase")
        def on_event_increase(self, event):
            self.state.value += 1

        def display(self):
            return self.render_template_string(
                """<div>Count: {{value}}</div>"""
                """<a jmb:click="increase()">increase</a>"""
            )

    @jmb.page("cpage", Component.Config(components={"counter": Counter}))
    class CPage(Component):
        @action
        def increase_all(self):
            self.emit("increase").to("./*")  # direct children

        def display(self):
            return self.render_template_string(
                """<html><head></head><body>"""
                """{{component("counter", "./counter.second").key("first")}}"""
                """{{component("counter").key("second")}}"""
                """{{component("counter").key("third")}}"""
                """<a jmb:click="increase_all()">Increase all</a>"""
                """</body></html>"""
            )

    # test increase all
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(), url="/cpage"),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(
                            connected_counter_exec_name="../counter.second", value=0
                        ),
                        url="/cpage/counter.first",
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(connected_counter_exec_name=None, value=0),
                        url="/cpage/counter.second",
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(connected_counter_exec_name=None, value=0),
                        url="/cpage/counter.third",
                    ),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage",
                        actionName="increase_all",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 3
    assert ajax_response_data[0]["execName"] == "/cpage/counter.first"
    assert ajax_response_data[0]["state"] == dict(
        connected_counter_exec_name="../counter.second", value=1
    )
    assert ajax_response_data[0]["dom"] == (
        """<div>Count: 1</div>""" """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[0]["url"] == "/cpage/counter.first"

    assert ajax_response_data[1]["execName"] == "/cpage/counter.second"
    assert ajax_response_data[1]["state"] == dict(
        connected_counter_exec_name=None, value=1
    )
    assert ajax_response_data[1]["dom"] == (
        """<div>Count: 1</div>""" """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[1]["url"] == "/cpage/counter.second"

    assert ajax_response_data[2]["execName"] == "/cpage/counter.third"
    assert ajax_response_data[2]["state"] == dict(
        connected_counter_exec_name=None, value=1
    )
    assert ajax_response_data[2]["dom"] == (
        """<div>Count: 1</div>""" """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[2]["url"] == "/cpage/counter.third"
    # test increase first counter and check if second is increased to
    r = client.post(
        "/cpage/counter.first",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(), url="/cpage"),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(
                            connected_counter_exec_name="../counter.second", value=0
                        ),
                        url="/cpage/counter.first",
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(connected_counter_exec_name=None, value=0),
                        url="/cpage/counter.second",
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(connected_counter_exec_name=None, value=0),
                        url="/cpage/counter.third",
                    ),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.first",
                        actionName="increase",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    ajax_response_data = json.loads(r.data)
    assert len(ajax_response_data) == 2
    assert ajax_response_data[0]["execName"] == "/cpage/counter.first"
    assert ajax_response_data[0]["state"] == dict(
        connected_counter_exec_name="../counter.second", value=1
    )
    assert ajax_response_data[0]["dom"] == (
        """<div>Count: 1</div>""" """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[0]["url"] == "/cpage/counter.first"

    assert ajax_response_data[1]["execName"] == "/cpage/counter.second"
    assert ajax_response_data[1]["state"] == dict(
        connected_counter_exec_name=None, value=1
    )
    assert ajax_response_data[1]["dom"] == (
        """<div>Count: 1</div>""" """<a jmb:click="increase()">increase</a>"""
    )
    assert ajax_response_data[1]["url"] == "/cpage/counter.second"


def test_dynamic_add_remove_counters(jmb, client):
    class Counter(Component):
        def __init__(self, value: int = 0):
            super().__init__()

        def display(self):
            # uses $jmb.set to increase and redisplay counter
            # puts logic in template which is not very good but it can be done
            return self.render_template_string(
                """<div>Counter ({{self.key}}): {{value}}<button onclick="$jmb.set("value", {{value + 1}})">Increase</button></div>"""
            )

    @jmb.page("cpage", Component.Config(components={"counter": Counter}))
    class Page(Component):
        def __init__(self, counters: Tuple[str, ...] = ()):
            super().__init__()

        @action
        def add_counter(self, key: str):
            if key and key not in self.state.counters:
                self.state.counters = self.state.counters + (key,)

        @action
        def remove_counter(self, key: str):
            if key and key in self.state.counters:
                l = list(self.state.counters)
                l.remove(key)
                self.state.counters = tuple(l)

        @listener(event="_rendered", source="./*")
        def on_counter_render(self, event):
            if event.source.key not in self.state.counters:
                self.state.counters = self.state.counters + (event.source.key)

        def display(self):
            return self.render_template_string(
                "<html><head></head><body>"
                """<input jmb:ref="key" name="key" value="">"""
                """<button onclick="$jmb.call('add_counter', $jmb.ref('key').value)">Add counter</button>"""
                """{% for counter in counters %}"""
                """<div>{{component("counter").key(counter)}}<button onclick="$jmb.call('remove_counter', '{{counter}}')">Remove</div></div>"""
                "{% endfor %}"
                "</body></html>"
            )

    # TODO display page with no counters
    r = client.get("/cpage")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:state=\'{"counters":[]}\' jmb:url="/cpage"><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        "</body></html>"
    ).encode("utf-8")
    # TODO call to some counter with url should add that counter
    r = client.get("/cpage/counter.first")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:state=\'{"counters":[]}\' jmb:url="/cpage"><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><div jmb:name="/cpage/counter.first" jmb:state=\'{"value":0}\' jmb:url="/cpage.counter.first">Counter (first): 0<button onclick="$jmb.set("value", 1)">Increase</button></div>"""
        """<button onclick="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        "</body></html>"
    ).encode("utf-8")
    # TODO call add_counter three times in row
    # TODO increase some counter two times in row
    # TODO remove counter


# TODO make dynamic counter with persisted data on server


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
