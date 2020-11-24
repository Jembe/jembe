from typing import (
    Any,
    NewType,
    TYPE_CHECKING,
    Optional,
    Tuple,
    Sequence,
    List,
    Dict,
    Union,
)
from jembe import Component
from flask import json
from jembe import (
    action,
    listener,
    config,
    redisplay,
    NotFound,
    Forbidden,
    Unauthorized,
    BadRequest,
)

if TYPE_CHECKING:
    from flask import Response
    from jembe import Event


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
<html jmb:name="/cpage" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body><div jmb:name="/cpage/counter" jmb:data=\'{"actions":["increase"],"changesUrl":true,"state":{"value":0},"url":"/cpage/counter"}\'><div>Count: 0</div> <a jmb:click="increase()">increase</a></div></body></html>"""
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
    counter1_page_html = """<html><head></head><body><template jmb-placeholder="/cpage/counter"></template></body></html>"""
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
        """<html jmb:name="/cpage" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb:name="/cpage/counter.first" jmb:data=\'{"actions":["increase","set_increment"],"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.first"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb:name="/cpage/counter.second" jmb:data=\'{"actions":["increase","set_increment"],"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.second"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb:name="/cpage/counter.third" jmb:data=\'{"actions":["increase","set_increment"],"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.third"}\'>"""
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
        """<html jmb:name="/cpage" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb:name="/cpage/counter.first" jmb:data=\'{"actions":["increase","set_increment"],"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.first"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb:name="/cpage/counter.second" jmb:data=\'{"actions":["increase","set_increment"],"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.second"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb:name="/cpage/counter.third" jmb:data=\'{"actions":["increase","set_increment"],"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.third"}\'>"""
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
                    dict(execName="/cpage", state=dict()),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(increment=1, value=0),
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(increment=1, value=0),
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(increment=1, value=0),
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
        """<template jmb-placeholder="/cpage/counter.first"></template>"""
        """<template jmb-placeholder="/cpage/counter.second"></template>"""
        """<template jmb-placeholder="/cpage/counter.third"></template>"""
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
                    dict(execName="/cpage", state=dict()),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(increment=1, value=1),
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(increment=1, value=2),
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(increment=1, value=3),
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
                    dict(execName="/cpage", state=dict()),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(
                            connected_counter_exec_name="../counter.second", value=0
                        ),
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(connected_counter_exec_name=None, value=0),
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(connected_counter_exec_name=None, value=0),
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
                    dict(execName="/cpage", state=dict()),
                    dict(
                        execName="/cpage/counter.first",
                        state=dict(
                            connected_counter_exec_name="../counter.second", value=0
                        ),
                    ),
                    dict(
                        execName="/cpage/counter.second",
                        state=dict(connected_counter_exec_name=None, value=0),
                    ),
                    dict(
                        execName="/cpage/counter.third",
                        state=dict(connected_counter_exec_name=None, value=0),
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
                """<div>Counter ({{key}}): {{value}}<button jmb:on.click="$jmb.set('value', {{value + 1}})">Increase</button></div>"""
            )

    @jmb.page("cpage", Component.Config(components={"counter": Counter}))
    class Page(Component):
        def __init__(self, counters: Sequence[str] = ()):
            self.state.counters = list(counters)
            super().__init__()

        @action
        def add_counter(self, key: str):
            if key and key not in self.state.counters:
                self.state.counters.append(key)

        @action
        def remove_counter(self, key: str):
            if key and key in self.state.counters:
                self.state.counters.remove(key)

        @listener(event="_display", source="./*")
        def on_counter_render(self, event):
            if event.source.key not in self.state.counters:
                self.state.counters.append(event.source.key)
                return True
            return False

        def display(self):
            return self.render_template_string(
                "<html><head></head><body>"
                """<input jmb:ref="key" name="key" value="">"""
                """<button jmb:on.click="$jmb.call('add_counter', $jmb.ref('key').value)">Add counter</button>"""
                """{% for counter in counters %}"""
                """<div>{{component("counter").key(counter)}}<button jmb:on.click="$jmb.call('remove_counter', '{{counter}}')">Remove</div></div>"""
                "{% endfor %}"
                "</body></html>"
            )

    # display page with no counters
    r = client.get("/cpage")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:data=\'{"actions":["add_counter","remove_counter"],"changesUrl":true,"state":{"counters":[]},"url":"/cpage"}\'><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb:on.click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        "</body></html>"
    ).encode("utf-8")

    # call to first counter with url should add that counter
    r = client.get("/cpage/counter.first")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:data=\'{"actions":["add_counter","remove_counter"],"changesUrl":true,"state":{"counters":["first"]},"url":"/cpage"}\'><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb:on.click="$jmb.call(\'add_counter\', $jmb.ref(\'key\').value)">Add counter</button>"""
        """<div><div jmb:name="/cpage/counter.first" jmb:data=\'{"actions":[],"changesUrl":true,"state":{"value":0},"url":"/cpage/counter.first"}\'>Counter (first): 0<button jmb:on.click="$jmb.set('value', 1)">Increase</button></div>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'first')">Remove</button></div>"""
        "</body></html>"
    ).encode("utf-8")

    # call add_counter three times in row
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[dict(execName="/cpage", state=dict()),],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage",
                        actionName="add_counter",
                        args=["first"],
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 2
    assert json_response[0]["execName"] == "/cpage"
    assert json_response[0]["dom"] == (
        """<html><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb:on.click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.first"
    assert json_response[1]["dom"] == (
        """<div>Counter (first): 0<button jmb:on.click="$jmb.set('value', 1)">Increase</button></div>"""
    )

    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(counters=["first"])),
                    dict(execName="/cpage/counter.first", state=dict(value=0)),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage",
                        actionName="add_counter",
                        args=["second"],
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 2
    assert json_response[0]["execName"] == "/cpage"
    assert json_response[0]["dom"] == (
        """<html><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb:on.click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.second"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.second"
    assert json_response[1]["dom"] == (
        """<div>Counter (second): 0<button jmb:on.click="$jmb.set('value', 1)">Increase</button></div>"""
    )
    # increase and add counter
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(counters=["first", "second"])),
                    dict(execName="/cpage/counter.first", state=dict(value=0)),
                    dict(execName="/cpage/counter.second", state=dict(value=0)),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/cpage/counter.second",
                        initParams=dict(value=1),
                    ),
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.second",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                    dict(
                        type="call",
                        componentExecName="/cpage",
                        actionName="add_counter",
                        args=["third"],
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/cpage"
    assert json_response[0]["dom"] == (
        """<html><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb:on.click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.second"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.third"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'third')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.second"
    assert json_response[1]["dom"] == (
        """<div>Counter (second): 1<button jmb:on.click="$jmb.set('value', 2)">Increase</button></div>"""
    )
    assert json_response[2]["execName"] == "/cpage/counter.third"
    assert json_response[2]["dom"] == (
        """<div>Counter (third): 0<button jmb:on.click="$jmb.set('value', 1)">Increase</button></div>"""
    )

    # increase second counter
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(
                        execName="/cpage",
                        state=dict(counters=["first", "second", "third"]),
                    ),
                    dict(execName="/cpage/counter.first", state=dict(value=0)),
                    dict(execName="/cpage/counter.second", state=dict(value=1)),
                    dict(execName="/cpage/counter.third", state=dict(value=0)),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/cpage/counter.second",
                        initParams=dict(value=2),
                    ),
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.second",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/cpage/counter.second"
    assert json_response[0]["dom"] == (
        """<div>Counter (second): 2<button jmb:on.click="$jmb.set('value', 3)">Increase</button></div>"""
    )

    # remove counter
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(
                        execName="/cpage",
                        state=dict(counters=["first", "second", "third"]),
                    ),
                    dict(execName="/cpage/counter.first", state=dict(value=0)),
                    dict(execName="/cpage/counter.second", state=dict(value=3)),
                    dict(execName="/cpage/counter.third", state=dict(value=0)),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage",
                        actionName="remove_counter",
                        args=["third"],
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/cpage"
    assert json_response[0]["dom"] == (
        """<html><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb:on.click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.second"></template>"""
        """<button jmb:on.click="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        "</body></html>"
    )


def test_initialising_listener(jmb, client):
    """ page sets value of child counter on counter initialisation event.source.init_params.value = 10"""

    class Counter(Component):
        def __init__(self, value: int = 0):
            super().__init__()

        def display(self):
            return self.render_template_string("<div>{{value}}</div>")

    @jmb.page("cpage", Component.Config(components=dict(counter=Counter)))
    class Page(Component):
        @listener(event="_initialising", source="./counter")
        def when_init_counter(self, event):
            # TODO change to StateParam like dict
            event.params["init_params"]["value"] = 10

        def display(self):
            return self.render_template_string(
                "<html><head></head><body>" "{{component('counter')}}" "</body></html>"
            )

    html = (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb:name="/cpage/counter" jmb:data=\'{"actions":[],"changesUrl":true,"state":{"value":10},"url":"/cpage/counter"}\'>10</div>"""
        "</body></html>"
    ).encode("utf-8")
    r = client.get("/cpage")
    assert r.status_code == 200
    assert r.data == html

    r = client.get("/cpage/counter")
    assert r.status_code == 200
    assert r.data == html


def test_counter_data_on_server(jmb, client):
    """make dynamic counter with persisted data on server"""
    counters: Dict[int, int] = {1: 10, 2: 20}

    class Counter(Component):
        def __init__(self, id: int, _value: Optional[int] = None):
            self.value = _value if _value is not None else counters[self.state.id]
            super().__init__()

        @action
        def increase(self):
            self.value += 1
            counters[self.state.id] = self.value

        @redisplay(when_executed=True)
        def display(self):
            return self.render_template_string("<div>{{value}}</div>")

    @jmb.page("cpage", Component.Config(components=dict(counter=Counter)))
    class Page(Component):
        @action
        def add_counter(self, id: int, value: int):
            counters[id] = value

        @action
        def remove_counter(self, id: int):
            del counters[id]

        def display(self):
            self.counters = counters
            return self.render_template_string(
                "<html><head></head><body>"
                """{% for id, value in counters.items() %}{{component("counter", id=id, _value=value).key(id)}}{% endfor %}"""
                "</body></html>"
            )

    r = client.get("/cpage")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:data=\'{"actions":["add_counter","remove_counter"],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb:name="/cpage/counter.1" jmb:data=\'{"actions":["increase"],"changesUrl":true,"state":{"id":1},"url":"/cpage/counter.1/1"}\'>10</div>"""
        """<div jmb:name="/cpage/counter.2" jmb:data=\'{"actions":["increase"],"changesUrl":true,"state":{"id":2},"url":"/cpage/counter.2/2"}\'>20</div>"""
        "</body></html>"
    ).encode("utf-8")
    # increase counter
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict()),
                    dict(execName="/cpage/counter.1", state=dict(id=1)),
                    dict(execName="/cpage/counter.2", state=dict(id=2)),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/cpage/counter.1",
                        actionName="increase",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )

    assert counters[1] == 11

    assert r.status_code == 200
    ajax_data = json.loads(r.data)
    assert len(ajax_data) == 1
    assert ajax_data[0]["execName"] == "/cpage/counter.1"
    assert ajax_data[0]["state"] == dict(id=1)
    assert ajax_data[0]["dom"] == "<div>11</div>"

    # request get counter with wrong key should reinitialise counter with correct key
    r = client.get("/cpage/counter.1/2")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:data=\'{"actions":["add_counter","remove_counter"],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb:name="/cpage/counter.1" jmb:data=\'{"actions":["increase"],"changesUrl":true,"state":{"id":1},"url":"/cpage/counter.1/1"}\'>11</div>"""
        """<div jmb:name="/cpage/counter.2" jmb:data=\'{"actions":["increase"],"changesUrl":true,"state":{"id":2},"url":"/cpage/counter.2/2"}\'>20</div>"""
        "</body></html>"
    ).encode("utf-8")


def test_error_handlings(jmb, client):
    counters = {1: 1, 2: 2}

    class Counter(Component):
        def __init__(self, counter_id: int):
            self.value = counters[counter_id]

        def display(self):
            return self.render_template_string("<div>{{value}}</div>")

    class CounterHandled(Counter):
        def __init__(self, counter_id: int):
            try:
                super().__init__(counter_id)
            except KeyError:
                raise NotFound()

    @jmb.page(
        "cpage", Component.Config(components=dict(counter=Counter, ch=CounterHandled))
    )
    class Page(Component):
        def __init__(self, display_counter: bool = False):
            super().__init__()

        @listener(event="_display", source="./counter")
        def on_display_counter(self, event):
            self.state.display_counter = True

        def display(self):
            if self.state.display_counter:
                return self.render_template_string(
                    """<html><head></head><body>"""
                    """{{component("counter")}}"""
                    """</body>"""
                )
            else:
                self.counters = counters
                return self.render_template_string(
                    """<html><head></head><body>"""
                    """{% for counter_id in counters %}<a href="#">{{counter_id}}</a>{% endfor %}"""
                    """</body>"""
                )

    r = client.get("/cpage/ch/3")
    assert r.status_code == 404
    # r = client.get("/cpage/counter/3")
    # assert r.status_code == 400


def test_catch_exception_by_parent_and_ignore_it(jmb, client):
    class Counter(Component):
        def __init__(self, counter_id: int):
            raise Forbidden()

    @jmb.page("cpage", Component.Config(components=dict(c=Counter)))
    class Page(Component):
        @listener(event="_exception", source="./**")
        def on_exception(self, event):
            if isinstance(event.exception, Forbidden):
                event.handled = True

        def display(self):
            return super().render_template_string(
                "<html><head></head><body></body></html>"
            )

    r = client.get("/cpage/c/3")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body></body></html>"""
    ).encode("utf-8")


def test_catch_errors_while_rendering(jmb, client):
    class View(Component):
        def __init__(self, record_id: int):
            super().__init__()

        def display(self):
            return self.render_template_string("<div>{{record_id}}</div>")

    class Edit(Component):
        def __init__(self, record_id: int):
            if record_id % 2 == 0:
                raise Unauthorized()
            super().__init__()

        def display(self):
            return self.render_template_string("<div>Edit {{record_id}}</div>")

    @jmb.page("list", Component.Config(components=dict(e=Edit, v=View)))
    class List(Component):
        def display(self):
            self.records = {1: 1, 2: 2}
            return self.render_template_string(
                "<html><body>"
                "{% for record_id in records %}"
                "<div>{% if component('e', record_id=record_id).key(record_id).is_accessible() %}edit {{record_id}}{% else %}view {{record_id}}{%endif%}</div>"
                "{% endfor %}"
                "</body></html>"
            )

    r = client.get("/list")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/list" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/list"}\'><body>"""
        "<div>edit 1</div><div>view 2</div>"
        """</body></html>"""
    ).encode("utf-8")


def test_error_handling_leaves_empty_placeholder(client, jmb):
    class A(Component):
        def display(self):
            raise ValueError()

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        @listener(event="_exception", source="./a")
        def on_error_in_a(self, event):
            event.handled = True

        def display(self):
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body></body></html>"""
    ).encode("utf-8")


def test_error_handling_leaves_empty_placeholder_deep(client, jmb):
    class B(Component):
        def display(self):
            raise ValueError()

    @config(Component.Config(components=dict(b=B)))
    class A(Component):
        @listener(event="_exception", source="./b")
        def on_error_in_b(self, event):
            event.handled = True

        def display(self):
            return self.render_template_string("<div>{{component('b')}}</div>")

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        def display(self):
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb:name="/page/a" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page/a"}\'></div>"""
        """</body></html>"""
    ).encode("utf-8")


def test_error_handling_with_listener_on_display_with_deferred_action(client, jmb):
    class B(Component):
        def display(self):
            raise (ValueError())

    class C(Component):
        def __init__(self):
            self.error_counter = 0
            super().__init__()

        @listener(event="update_error_counter")
        def on_error(self, event):
            self.error_counter += 1

        @action(deferred=True)
        def display(self):
            return self.render_template_string("<div>errors {{error_counter}}</div>")

    @config(Component.Config(components=dict(b=B)))
    class A(Component):
        def __init__(self, b_has_error: bool = False):
            # self.b_has_error = False
            super().__init__()

        @listener(event="_exception", source="./b")
        def on_error_in_b(self, event):
            event.handled = True
            self.state.b_has_error = True

        def display(self):
            if self.state.b_has_error:
                self.emit("update_error_counter")
                return self.render_template_string("<div>b has error</div>")
            else:
                return self.render_template_string("<div>{{component('b')}}</div>")

    @jmb.page("page", Component.Config(components=dict(a=A, c=C)))
    class Page(Component):
        def display(self):
            return self.render_template_string(
                "<html><body>{{component('c')}}{{component('a')}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb:name="/page/c" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page/c"}\'>errors 1</div>"""
        """<div jmb:name="/page/a" jmb:data=\'{"actions":[],"changesUrl":true,"state":{"b_has_error":true},"url":"/page/a"}\'>b has error</div>"""
        """</body></html>"""
    ).encode("utf-8")
    r2 = client.get("/page/c")
    assert r2.status_code == 200
    assert r2.data == r.data
    r2 = client.get("/page/a")
    assert r2.status_code == 200
    assert r2.data == r.data
    r2 = client.get("/page/a/b")
    assert r2.status_code == 200
    assert r2.data == r.data


# def test_error_handling_of_itself
def test_inject_init_params_to_component(jmb, client):
    """
    inject params are used to inject cross functional params into component.
    This params usually defines enviroment in which component is exected and
    are not related nor handled by parent compoenents or url params.

    Inject params are usualu user_id, userObject of current user usually stored
    in session. Current user language or similar that is stored in session/cookie
    or pased as header to every request.

    Component will inject this paramas. If injected params are explicitly set
    they will be ignored in production but in development will raise JembeError.

    injected params are not send to client
    """

    class User:
        def __init__(self, id: int, name: str):
            if id is None:
                raise ValueError
            self.id = id
            self.name = name

    @jmb.page("page")
    class Page(Component):
        def __init__(
            self, user_id: Optional[int] = None, _user: Optional["User"] = None
        ):
            if user_id is None:
                raise Unauthorized()
            self.user = _user if _user else User(user_id, "Jembe {}".format(user_id))
            super().__init__()

        def inject(self):
            """ usualy call some services or flask session, g, request to prepare params to inject"""
            return dict(user_id=1, _user=User(1, "Jembe {}".format(1)))

        def display(self):
            return self.render_template_string(
                "<html><body>{{user.id}} {{user.name}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body>1 Jembe 1</body></html>"""
    ).encode("utf-8")

    # ignore injected params
    r = client.post(
        "/page",
        data=json.dumps(
            dict(
                components=[],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/page",
                        initParams=dict(user_id=5),
                    ),
                    dict(
                        type="call",
                        componentExecName="/page",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["dom"] == ("<html><body>1 Jembe 1</body></html>")
    assert json_response[0]["state"] == dict()


def test_update_window_location(jmb, client):
    """
    When rendering components via x-jembe ajax request/response cycle
    deepest-latest component url should be used as window.location and it should
    be set via javascript part of framework. 
    Component can opt-out from window.location settings which will make
    that compoennt and all its children url not be used when determing 
    window.location. This can be usefull for supporting compoentns on page like
    navigation etc.

    When displaying page via regular http get request, just use requested url as
    window.location (no need to change it), becaouse all subsequent request should
    use x-jembe request and all will be fine.
    """

    class S2(Component):
        def display(self):
            return self.render_template_string("<div>S2</div>")

    @config(Component.Config(components=dict(s2=S2)))
    class S1(Component):
        def display(self):
            return self.render_template_string("<div>S1{{component('s2')}}</div>")

    class C1(Component):
        def display(self):
            return self.render_template_string("<div>C1</div>")

    class C2(Component):
        def display(self):
            return self.render_template_string("<div>C2</div>")

    @jmb.page(
        "page",
        Component.Config(
            components=dict(s1=(S1, S1.Config(changes_url=False)), c1=C1, c2=C2)
        ),
    )
    class Page(Component):
        def display(self):
            return self.render_template_string(
                "<html><body>{{component('s1')}}{{component('c1')}}{{component('c2')}}</body></html>"
            )

    r = client.post(
        "/page",
        data=json.dumps(
            dict(
                components=[],
                commands=[
                    dict(type="init", componentExecName="/page", initParams=dict(),),
                    dict(
                        type="call",
                        componentExecName="/page",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 5
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["url"] == "/page"
    assert json_response[0]["changesUrl"] == True
    assert json_response[1]["execName"] == "/page/s1"
    assert json_response[1]["url"] == "/page/s1"
    assert json_response[1]["changesUrl"] == False
    assert json_response[2]["execName"] == "/page/s1/s2"
    assert json_response[2]["url"] == "/page/s1/s2"
    assert json_response[2]["changesUrl"] == False
    assert json_response[3]["execName"] == "/page/c1"
    assert json_response[3]["url"] == "/page/c1"
    assert json_response[3]["changesUrl"] == True
    assert json_response[4]["execName"] == "/page/c2"
    assert json_response[4]["url"] == "/page/c2"
    assert json_response[4]["changesUrl"] == True


def test_url_get_query_params(jmb, client):
    class AComponent(Component):
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string("<div></div>")

    @jmb.page(
        "list",
        Component.Config(
            url_query_params=dict(p="page", ps="page_size"),
            components=dict(a=AComponent),
        ),
    )
    class ListComponent(Component):
        def __init__(self, page: Optional[int] = None, page_size: int = 10) -> None:
            if self.state.page is None:
                self.state.page = 0
            super().__init__()

        def display(self) -> Union[str, "Response"]:
            return self.render_template_string("<html><body></body></html>")

    r = client.get("/list")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb:name="/list" jmb:data=\'{"actions":[],"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/list?p=0&amp;ps=10"}\'><body></body></html>"""
    ).encode("utf-8")

    r = client.get("/list?p=3&ps=20")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb:name="/list" jmb:data=\'{"actions":[],"changesUrl":true,"state":{"page":3,"page_size":20},"url":"/list?p=3&amp;ps=20"}\'><body></body></html>"""
    ).encode("utf-8")
    r = client.get("/list/a?p=100&ps=100")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb:name="/list" jmb:data=\'{"actions":[],"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/list?p=0&amp;ps=10"}\'><body></body></html>"""
    ).encode("utf-8")


def test_client_emit_event_handling(jmb, client):
    class TestComponent(Component):
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string(
                """<div><button jmb:on.click="$jmb.emit('cancel')">Cancel</button></div>"""
            )

    @jmb.page("page", Component.Config(components=dict(test=TestComponent)))
    class Page(Component):
        def __init__(self) -> None:
            self.canceled = False
            super().__init__()

        @listener(event="cancel", source="./*")
        def on_cancel(self, event: "Event"):
            self.canceled = True

        @redisplay(when_executed=True)
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string(
                "<html><body>{{component('test')}}<div>{{canceled}}</div></body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb:name="/page/test" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page/test"}\'>"""
        """<button jmb:on.click="$jmb.emit(\'cancel\')">Cancel</button>"""
        """</div>"""
        """<div>False</div>"""
        """</body></html>"""
    ).encode("utf-8")
    r = client.post(
        "/page/test",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/test", state=dict()),
                ],
                commands=[
                    dict(type="init", componentExecName="/page", initParams=dict(),),
                    dict(
                        type="emit",
                        componentExecName="/page/test",
                        eventName="cancel",
                        params=dict(),
                        to=None,
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["dom"] == (
        """<html><body>"""
        """<template jmb-placeholder="/page/test"></template>"""
        """<div>True</div>"""
        """</body></html>"""
    )


def test_dont_fire_listener_for_system_events_if_not_set_explicitly(jmb, client):
    class A(Component):
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string("<div></div>")

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        def __init__(self) -> None:
            super().__init__()
            self.events: List[str] = []

        @listener(source="./a")
        def on_a_events(self, event):
            self.events.append(event.name)

        @redisplay(when_executed=True)
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string(
                "<html><body>{{component('a')}}<div>{{events|safe}}</div></body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb:name="/page/a" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page/a"}\'></div>"""
        """<div>[]</div>"""
        """</body></html>"""
    ).encode("utf-8")

    r = client.post(
        "/page/a",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/a", state=dict()),
                ],
                commands=[
                    dict(
                        type="emit",
                        componentExecName="/page/a",
                        eventName="cancel",
                        params=dict(),
                        to=None,
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["dom"] == (
        """<html><body>"""
        """<template jmb-placeholder="/page/a"></template>"""
        """<div>['cancel']</div>"""
        """</body></html>"""
    )


def test_component_default_encode_decode_params(app_ctx):
    # - dict, list, tuple, str, int, float, init- & float-deriveted Enums, True, False, None, via
    UrlPath = NewType("UrlPath", str)

    class C(Component):
        def __init__(
            self,
            i: int = 1,
            oi: Optional[int] = None,
            s: str = "",
            os: Optional[str] = None,
            f: float = 1,
            of: Optional[float] = None,
            od1: Optional[dict] = None,
            od2: Optional[Dict[str, Any]] = None,
            ts: Tuple[str, ...] = (),
            ots: Optional[Tuple[str, ...]] = None,
            sq: Sequence[Any] = (),
            urlpath: UrlPath = UrlPath(""),
            ourlpath: Optional[UrlPath] = None,
        ) -> None:

            super().__init__()

    with app_ctx:
        assert C.decode_param("i", 1) == 1
        assert C.decode_param("oi", None) == None
        assert C.decode_param("oi", 1) == 1
        assert C.decode_param("s", "test") == "test"
        assert C.decode_param("os", None) == None
        assert C.decode_param("os", "test") == "test"
        assert C.decode_param("f", 1.0) == 1.0
        assert C.decode_param("of", None) == None
        assert C.decode_param("of", 1) == 1
        assert C.decode_param("od1", None) == None
        assert C.decode_param("od1", dict(a="A", b=2)) == dict(a="A", b=2)
        assert C.decode_param("od1", {1: "1", 2: 20}) == {1: "1", 2: 20}
        assert C.decode_param("od2", None) == None
        assert C.decode_param("od2", dict(a="A", b=2)) == dict(a="A", b=2)
        assert C.decode_param("ts", ("1", "2")) == ("1", "2")
        assert C.decode_param("ots", None) == None
        assert C.decode_param("ots", ("1", "b")) == ("1", "b")
        assert C.decode_param("sq", ()) == ()
        assert C.decode_param("sq", (1, 2)) == (1, 2)
        assert C.decode_param("sq", [1, "2"]) == (1, "2")
        assert C.decode_param("urlpath", "test") == "test"
        assert C.decode_param("urlpath", "test") == UrlPath("test")
        assert C.decode_param("ourlpath", None) == None
        assert C.decode_param("ourlpath", "test") == UrlPath("test")


def test_add_actions_data_in_response(jmb, client):
    class A(Component):
        @action
        def action1(self):
            pass

        @action
        def action2(self):
            pass
        @redisplay(when_executed=True)
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string("<div></div>")

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        def display(self) -> Union[str, "Response"]:
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb:name="/page" jmb:data=\'{"actions":[],"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb:name="/page/a" jmb:data=\'{"actions":["action1","action2"],"changesUrl":true,"state":{},"url":"/page/a"}\'></div>"""
        """</body></html>"""
    ).encode("utf-8")

    r = client.post(
        "/page/a",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict()),
                    dict(execName="/page/a", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/page/a",
                        actionName="display",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/page/a"
    assert json_response[0]["dom"] == ("""<div></div>""")
    assert json_response[0]["actions"] == ["action1", "action2"]


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
