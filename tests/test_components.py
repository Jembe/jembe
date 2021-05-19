from jembe.app import get_processor
from typing import (
    Any,
    NewType,
    Set,
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
    Event,
)

if TYPE_CHECKING:
    from jembe import ComponentConfig, Jembe, DisplayResponse


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
<html jmb-name="/cpage" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body><div jmb-name="/cpage/counter" jmb-data=\'{"actions":{"increase":true},"changesUrl":true,"state":{"value":0},"url":"/cpage/counter"}\'><div>Count: 0</div> <a jmb:click="increase()">increase</a></div></body></html>"""
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
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb-name="/cpage/counter.first" jmb-data=\'{"actions":{"increase":true,"set_increment":true},"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.first"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb-name="/cpage/counter.second" jmb-data=\'{"actions":{"increase":true,"set_increment":true},"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.second"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb-name="/cpage/counter.third" jmb-data=\'{"actions":{"increase":true,"set_increment":true},"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.third"}\'>"""
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
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb-name="/cpage/counter.first" jmb-data=\'{"actions":{"increase":true,"set_increment":true},"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.first"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb-name="/cpage/counter.second" jmb-data=\'{"actions":{"increase":true,"set_increment":true},"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.second"}\'>"""
        """<div>Count: 0</div>"""
        """<input jmb:change="set_increment($elm.value)" value="1">"""
        """<a jmb:click="increase()">increase</a>"""
        """</div>"""
        """<div jmb-name="/cpage/counter.third" jmb-data=\'{"actions":{"increase":true,"set_increment":true},"changesUrl":true,"state":{"increment":1,"value":0},"url":"/cpage/counter.third"}\'>"""
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
            self.emit("increase").to("*")  # direct children

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
                """<div>Counter ({{key}}): {{value}}<button jmb-on:click="$jmb.set('value', {{value + 1}})">Increase</button></div>"""
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

        @listener(event="_display", source="*")
        def on_counter_render(self, event):
            if event.source.key not in self.state.counters:
                self.state.counters.append(event.source.key)
                return True
            return False

        def display(self):
            return self.render_template_string(
                "<html><head></head><body>"
                """<input jmb:ref="key" name="key" value="">"""
                """<button jmb-on:click="$jmb.call('add_counter', $jmb.ref('key').value)">Add counter</button>"""
                """{% for counter in counters %}"""
                """<div>{{component("counter").key(counter)}}<button jmb-on:click="$jmb.call('remove_counter', '{{counter}}')">Remove</div></div>"""
                "{% endfor %}"
                "</body></html>"
            )

    # display page with no counters
    r = client.get("/cpage")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{"add_counter":true,"remove_counter":true},"changesUrl":true,"state":{"counters":[]},"url":"/cpage"}\'><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb-on:click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        "</body></html>"
    ).encode("utf-8")

    # call to first counter with url should add that counter
    r = client.get("/cpage/counter.first")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{"add_counter":true,"remove_counter":true},"changesUrl":true,"state":{"counters":["first"]},"url":"/cpage"}\'><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button jmb-on:click="$jmb.call(\'add_counter\', $jmb.ref(\'key\').value)">Add counter</button>"""
        """<div><div jmb-name="/cpage/counter.first" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"value":0},"url":"/cpage/counter.first"}\'>Counter (first): 0<button jmb-on:click="$jmb.set('value', 1)">Increase</button></div>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'first')">Remove</button></div>"""
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
        """<button jmb-on:click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.first"
    assert json_response[1]["dom"] == (
        """<div>Counter (first): 0<button jmb-on:click="$jmb.set('value', 1)">Increase</button></div>"""
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
        """<button jmb-on:click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.second"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.second"
    assert json_response[1]["dom"] == (
        """<div>Counter (second): 0<button jmb-on:click="$jmb.set('value', 1)">Increase</button></div>"""
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
                        mergeExistingParams=True,
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
        """<button jmb-on:click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.second"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.third"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'third')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.second"
    assert json_response[1]["dom"] == (
        """<div>Counter (second): 1<button jmb-on:click="$jmb.set('value', 2)">Increase</button></div>"""
    )
    assert json_response[2]["execName"] == "/cpage/counter.third"
    assert json_response[2]["dom"] == (
        """<div>Counter (third): 0<button jmb-on:click="$jmb.set('value', 1)">Increase</button></div>"""
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
                        mergeExistingParams=True,
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
        """<div>Counter (second): 2<button jmb-on:click="$jmb.set('value', 3)">Increase</button></div>"""
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
        """<button jmb-on:click="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><template jmb-placeholder="/cpage/counter.first"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><template jmb-placeholder="/cpage/counter.second"></template>"""
        """<button jmb-on:click="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        "</body></html>"
    )


def test_initialising_listener(jmb, client):
    """ page sets value of child counter on counter initialisation event.source.init_params.value = 10"""

    class Counter(Component):
        def __init__(self, value: int = 0):
            super().__init__()

        def display(self):
            return self.render_template_string("<div>{{value}}</div>")


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
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{"add_counter":true,"remove_counter":true},"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb-name="/cpage/counter.1" jmb-data=\'{"actions":{"increase":true},"changesUrl":true,"state":{"id":1},"url":"/cpage/counter.1/1"}\'>10</div>"""
        """<div jmb-name="/cpage/counter.2" jmb-data=\'{"actions":{"increase":true},"changesUrl":true,"state":{"id":2},"url":"/cpage/counter.2/2"}\'>20</div>"""
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
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{"add_counter":true,"remove_counter":true},"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body>"""
        """<div jmb-name="/cpage/counter.1" jmb-data=\'{"actions":{"increase":true},"changesUrl":true,"state":{"id":1},"url":"/cpage/counter.1/1"}\'>11</div>"""
        """<div jmb-name="/cpage/counter.2" jmb-data=\'{"actions":{"increase":true},"changesUrl":true,"state":{"id":2},"url":"/cpage/counter.2/2"}\'>20</div>"""
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

        @listener(event="_display", source="counter")
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
        @listener(event="_exception", source="**")
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
        """<html jmb-name="/cpage" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/cpage"}\'><head></head><body></body></html>"""
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
                "<div>{% if component('e', record_id=record_id).key(record_id).is_accessible %}edit {{record_id}}{% else %}view {{record_id}}{%endif%}</div>"
                "{% endfor %}"
                "</body></html>"
            )

    r = client.get("/list")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/list" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/list"}\'><body>"""
        "<div>edit 1</div><div>view 2</div>"
        """</body></html>"""
    ).encode("utf-8")


def test_error_handling_leaves_empty_placeholder(client, jmb):
    class A(Component):
        def display(self):
            raise ValueError()

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        @listener(event="_exception", source="a")
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
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body></body></html>"""
    ).encode("utf-8")


def test_error_handling_leaves_empty_placeholder_deep(client, jmb):
    class B(Component):
        def display(self):
            raise ValueError()

    @config(Component.Config(components=dict(b=B)))
    class A(Component):
        @listener(event="_exception", source="b")
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
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/a"}\'></div>"""
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

        @listener(event="_exception", source="b")
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
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/c" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/c"}\'>errors 1</div>"""
        """<div jmb-name="/page/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"b_has_error":true},"url":"/page/a"}\'>b has error</div>"""
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
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>1 Jembe 1</body></html>"""
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
                        mergeExistingParams=True,
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
                    dict(
                        type="init",
                        componentExecName="/page",
                        initParams=dict(),
                        mergeExistingParams=True,
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
        def display(self) -> "DisplayResponse":
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

        def display(self) -> "DisplayResponse":
            return self.render_template_string("<html><body></body></html>")

    r = client.get("/list")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/list" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/list?p=0&amp;ps=10"}\'><body></body></html>"""
    ).encode("utf-8")

    r = client.get("/list?p=3&ps=20")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/list" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page":3,"page_size":20},"url":"/list?p=3&amp;ps=20"}\'><body></body></html>"""
    ).encode("utf-8")
    r = client.get("/list/a?p=100&ps=100")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/list" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/list?p=0&amp;ps=10"}\'><body></body></html>"""
    ).encode("utf-8")


def test_url_get_query_params_not_used_on_x_jembe_request(jmb, client):
    @jmb.page(
        "list", Component.Config(url_query_params=dict(p="page", ps="page_size"),),
    )
    class ListComponent(Component):
        def __init__(self, page: Optional[int] = None, page_size: int = 10) -> None:
            if self.state.page is None:
                self.state.page = 0
            super().__init__()

        def display(self) -> "DisplayResponse":
            return self.render_template_string("<html><body></body></html>")

    r = client.get("/list")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/list" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"page":0,"page_size":10},"url":"/list?p=0&amp;ps=10"}\'><body></body></html>"""
    ).encode("utf-8")
    r = client.post(
        "/list?p=0&ps=10",
        data=json.dumps(
            dict(
                components=[dict(execName="/list", state=dict(page=0, page_size=10))],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/list",
                        initParams=dict(page=1, page_size=10),
                        mergeExistingParams=True,
                    ),
                    dict(
                        type="call",
                        componentExecName="/list",
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
    assert json_response[0]["execName"] == "/list"
    assert json_response[0]["url"] == "/list?p=1&ps=10"
    assert json_response[0]["changesUrl"] == True
    assert json_response[0]["state"] == dict(page=1, page_size=10)


def test_client_emit_event_handling(jmb, client):
    class TestComponent(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                """<div><button jmb-on:click="$jmb.emit('cancel')">Cancel</button></div>"""
            )

    @jmb.page("page", Component.Config(components=dict(test=TestComponent)))
    class Page(Component):
        def __init__(self) -> None:
            self.canceled = False
            super().__init__()

        @listener(event="cancel", source="*")
        def on_cancel(self, event: "Event"):
            self.canceled = True

        @redisplay(when_executed=True)
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('test')}}<div>{{canceled}}</div></body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/test" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/test"}\'>"""
        """<button jmb-on:click="$jmb.emit(\'cancel\')">Cancel</button>"""
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
                    dict(
                        type="init",
                        componentExecName="/page",
                        initParams=dict(),
                        mergeExistingParams=True,
                    ),
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
        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div></div>")

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        def __init__(self) -> None:
            super().__init__()
            self.events: List[str] = []

        @listener(source="a")
        def on_a_events(self, event):
            self.events.append(event.name)

        @redisplay(when_executed=True)
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('a')}}<div>{{events|safe}}</div></body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/a"}\'></div>"""
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


def test_component_default_dump_and_load_init_param(app_ctx):
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
            st: Set[int] = set(),
            st1: set = set(),
        ) -> None:

            super().__init__()

    with app_ctx:
        assert C.load_init_param(None, "i", 1) == 1
        assert C.load_init_param(None, "oi", None) == None
        assert C.load_init_param(None, "oi", 1) == 1
        assert C.load_init_param(None, "s", "test") == "test"
        assert C.load_init_param(None, "os", None) == None
        assert C.load_init_param(None, "os", "test") == "test"
        assert C.load_init_param(None, "f", 1.0) == 1.0
        assert C.load_init_param(None, "of", None) == None
        assert C.load_init_param(None, "of", 1) == 1
        assert C.load_init_param(None, "od1", None) == None
        assert C.load_init_param(None, "od1", dict(a="A", b=2)) == dict(a="A", b=2)
        assert C.load_init_param(None, "od1", {1: "1", 2: 20}) == {1: "1", 2: 20}
        assert C.load_init_param(None, "od2", None) == None
        assert C.load_init_param(None, "od2", dict(a="A", b=2)) == dict(a="A", b=2)
        assert C.load_init_param(None, "ts", ("1", "2")) == ("1", "2")
        assert C.load_init_param(None, "ots", None) == None
        assert C.load_init_param(None, "ots", ("1", "b")) == ("1", "b")
        assert C.load_init_param(None, "sq", ()) == ()
        assert C.load_init_param(None, "sq", (1, 2)) == (1, 2)
        assert C.load_init_param(None, "sq", [1, "2"]) == (1, "2")
        assert C.load_init_param(None, "urlpath", "test") == "test"
        assert C.load_init_param(None, "urlpath", "test") == UrlPath("test")
        assert C.load_init_param(None, "ourlpath", None) == None
        assert C.load_init_param(None, "ourlpath", "test") == UrlPath("test")
        assert C.load_init_param(None, "st", set([1, 2])) == set([1, 2])
        assert C.load_init_param(None, "st1", set(["a", 1])) == set(["a", 1])


def test_add_actions_data_in_response(jmb, client):
    class A(Component):
        @action
        def action1(self):
            pass

        @action
        def action2(self):
            pass

        @redisplay(when_executed=True)
        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div></div>")

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/a" jmb-data=\'{"actions":{"action1":true,"action2":true},"changesUrl":true,"state":{},"url":"/page/a"}\'></div>"""
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
    assert json_response[0]["actions"] == dict(action1=True, action2=True)


def test_event_source_name_with_keyed_exec_name(jmb, client):
    from jembe.processor import EmitCommand
    from jembe.component_config import ComponentListener

    event = Event(
        source_exec_name="/test/view.1",
        source=None,
        event_name="test",
        to=None,
        params=dict(),
    )
    assert event.source_name == "view"
    assert (
        EmitCommand._is_match(
            source_exec_name="/test/view.1",
            event_name="test",
            source_to=None,
            destination_exec_name="/test",
            destination_listener=ComponentListener(
                method_name="on_test", event_name="test", source=["view.*"]
            ),
        )
        == True
    )


def test_inject_into_should_refresh_childs_when_parent_state_is_changed(jmb, client):
    class Project(Component):
        def __init__(self, project_id: int):
            super().__init__()

        @action
        def goto(self, project_id: int):
            self.state.project_id = project_id

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>Project {{project_id}}{{component('tasks')}}</div>"
            )

    class Tasks(Component):
        def __init__(self, project_id: Optional[int] = None):
            super().__init__()

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>Tasks for project: {{project_id}}</div>"
            )

    @jmb.page(
        "test",
        Component.Config(
            components=dict(
                project=(
                    Project,
                    Component.Config(
                        components=dict(tasks=Tasks),
                        inject_into_components=lambda self, _config: dict(
                            project_id=self.state.project_id
                        ),
                    ),
                )
            )
        ),
    )
    class Test(Component):
        @listener(event="_display", source="project")
        def on_project_display(self, event):
            self.project_id = event.source.state.project_id

        def display(self) -> "DisplayResponse":
            self.project_id = getattr(self, "project_id", 1)
            return self.render_template_string(
                "<html><body>{{component('project', project_id=project_id)}}</body></html>"
            )

    r = client.get("/test")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/test" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test"}\'><body>"""
        """<div jmb-name="/test/project" jmb-data=\'{"actions":{"goto":true},"changesUrl":true,"state":{"project_id":1},"url":"/test/project/1"}\'>"""
        """Project 1"""
        """<div jmb-name="/test/project/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test/project/1/tasks"}\'>"""
        """Tasks for project: 1"""
        """</div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")
    r = client.post(
        "/test/project/1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/test", state=dict()),
                    dict(execName="/test/project", state=dict(project_id=1)),
                    dict(execName="/test/project/tasks", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/test/project",
                        actionName="goto",
                        args=list(),
                        kwargs=dict(project_id=2),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 2
    assert json_response[0]["execName"] == "/test/project"
    assert (
        json_response[0]["dom"]
        == """<div>Project 2<template jmb-placeholder="/test/project/tasks"></template></div>"""
    )
    assert json_response[1]["execName"] == "/test/project/tasks"
    assert json_response[1]["dom"] == """<div>Tasks for project: 2</div>"""


def test_component_inside_component(jmb, client):
    class B(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>B</div>")

    @config(Component.Config(components=dict(b=B)))
    class A(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string("{{component('b')}}")

    @jmb.page("test", Component.Config(components=dict(a=A)))
    class Page(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('a')}}</body></html>"
            )

    r = client.get("/test")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/test" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test"}\'><body>"""
        """<div jmb-name="/test/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test/a"}\'>"""
        """<div jmb-name="/test/a/b" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test/a/b"}\'>"""
        """B"""
        """</div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")


def test_component_is_accessible_can_execute_for_jrl(jmb, client):
    class A(Component):
        def __init__(self, rid: int):
            super().__init__()

        @action
        def cancel(self):
            self.emit("cancel")

        def display(self) -> "DisplayResponse":
            return self.render_template_string("C{{rid}}")

    @jmb.page("page", Component.Config(components=dict(a=A)))
    class Page(Component):
        def __init__(self, display_mode: Optional[str] = None):
            super().__init__()

        @listener(event="_display", source="a")
        def on_display_a(self, event):
            self.state.display_mode = "a"

        @listener(event="cancel", source="a")
        def on_cancel_a(self, event):
            self.state.display_mode = None

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>"
                "{%if display_mode is none %}"
                "{%if component('a', rid=1).is_accessible %}"
                """<button jmb-on:click="{{component().jrl}}">C1</button>"""
                "{% endif %}"
                "{%if component('a', rid=2).is_accessible %}"
                """<button jmb-on:click="{{component().jrl}}">C2</button>"""
                "{% endif %}"
                "{% else %}"
                "{{component('a')}}"
                "{% endif %}"
                "</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"display_mode":null},"url":"/page"}\'><body>"""
        """<button jmb-on:click="$jmb.component('a',{rid:1}).display()">C1</button>"""
        """<button jmb-on:click="$jmb.component('a',{rid:2}).display()">C2</button>"""
        """</body></html>"""
    ).encode("utf-8")

    r = client.post(
        "/page/a/1",
        data=json.dumps(
            dict(
                components=[dict(execName="/page", state=dict(display_mode=None)),],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/page/a",
                        initParams=dict(rid=1),
                        mergeExistingParams=True,
                    ),
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
    assert len(json_response) == 2
    assert json_response[0]["execName"] == "/page"
    assert (
        json_response[0]["dom"]
        == """<html><body><template jmb-placeholder="/page/a"></template></body></html>"""
    )
    assert json_response[1]["execName"] == "/page/a"
    assert json_response[1]["dom"] == """C1"""

    r = client.post(
        "/page/a/1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict(display_mode="a")),
                    dict(execName="/page/a", state=dict(rid=1)),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/page/a",
                        actionName="cancel",
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
    print(json_response)
    assert len(json_response) == 1
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["dom"] == (
        """<html><body>"""
        """<button jmb-on:click="$jmb.component('a',{rid:1}).display()">C1</button>"""
        """<button jmb-on:click="$jmb.component('a',{rid:2}).display()">C2</button>"""
        """</body></html>"""
    )


def test_page_with_two_components(jmb, client):
    class A(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>A</div>")

    class B(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>B</div>")

    @jmb.page("page", Component.Config(components=dict(a=A, b=B)))
    class Page(Component):
        def __init__(self, display_mode: str = ""):
            if not display_mode:
                self.state.display_mode = "a"
            super().__init__()

        @listener(event="_display", source="*")
        def on_child_display(self, event: "Event"):
            self.state.display_mode = event.source_name

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component(display_mode)}}</body></html>"
            )

    r = client.get("/page/b")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"display_mode":"b"},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/b" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/b"}\'>"""
        """B"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")

    r = client.get("/page/a")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"display_mode":"a"},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/a"}\'>"""
        """A"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")


def test_component_load_dump_params(app, jmb: "Jembe"):
    from jembe import File

    class FC(Component):
        def __init__(self, files: Optional[List[File]] = None):
            super().__init__()

    @jmb.page("page", Component.Config(components=dict(fc=FC)))
    class Page(Component):
        pass

    with app.test_request_context(path="/page"):
        files_json = [
            {
                "path": "uploads/2d2dfe28-71bb-11eb-9dcc-8cc84b229c61/Screenshot_from_2020-08-14_11-06-33.png",
                "storage": "temp",
            },
            {
                "path": "uploads/2d2dfe28-71bb-11eb-9dcc-8cc84b229c61/Screenshot_from_2020-07-22_23-21-24.png",
                "storage": "temp",
            },
            {
                "path": "uploads/2d2dfe28-71bb-11eb-9dcc-8cc84b229c61/Screenshot_from_2020-07-22_23-21-21.png",
                "storage": "temp",
            },
        ]
        files = FC.load_init_param(
            jmb.components_configs["/page/fc"], "files", files_json
        )

        assert isinstance(files, list)
        assert len(files) == 3
        assert isinstance(files[0], File)
        f: File = files[0]
        assert (
            f.path
            == "uploads/2d2dfe28-71bb-11eb-9dcc-8cc84b229c61/Screenshot_from_2020-08-14_11-06-33.png"
        )
        assert f.in_temp_storage() == True

        files_dump = FC.dump_init_param("files", files)
        assert json.dumps(files_dump) == json.dumps(files_json)


def test_component_renderer_absolute_path(jmb, client):
    class A(Component):
        def __init__(self, rid: int):
            super().__init__()

        def display(self) -> "DisplayResponse":
            return self.render_template_string("{{exec_name}}:{{rid}}")

    class B(Component):
        def __init__(self):
            super().__init__()

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                """<ul>"""
                """{% if component('/page').component('a1', rid=1).is_accessible %}"""
                """<li><a href="{{component().url}}" jmb-on.click.stop.prevent="{{component().jrl}}">A1</a></li>"""
                """{% endif %}"""
                """{% if component('/page').component('a2', rid=2).is_accessible %}"""
                """<li><a href="{{component().url}}" jmb-on.click.stop.prevent="{{component().jrl}}">A2</a></li>"""
                """{% endif %}"""
                """</ul>"""
            )

    @jmb.page("page", Component.Config(components=dict(a1=A, a2=A, b=B)))
    class Page(Component):
        def __init__(self, display_mode: str = "a1"):
            super().__init__()

        @listener(event="_display", source="*")
        def on_display_a(self, event: "Event"):
            if event.source_name in ("a1", "a2"):
                self.state.display_mode = event.source_name

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>"
                "{{component('b')}}"
                "{% if component(display_mode).is_accessible %}"
                "{{component()}}"
                "{% else %}"
                "{{component(display_mode, rid=0)}}"
                "{% endif %}"
                "</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"display_mode":"a1"},"url":"/page"}\'><body>"""
        """<ul jmb-name="/page/b" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/b"}\'>"""
        """<li><a href="/page/a1/1" jmb-on.click.stop.prevent="$jmb.component(\'/page\').component(\'a1\',{rid:1}).display()">A1</a></li>"""
        """<li><a href="/page/a2/2" jmb-on.click.stop.prevent="$jmb.component(\'/page\').component(\'a2\',{rid:2}).display()">A2</a></li>"""
        """</ul>"""
        """<p jmb-name="/page/a1" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"rid":0},"url":"/page/a1/0"}\'>/page/a1:0</p>"""
        """</body></html>"""
    ).encode("utf-8")


def test_component_can_use_relative_reference(jmb, client):
    class A(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string("A")

    class B(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "B2A: {{component('..').component('a').url}}, {{component('../a').url}}"
            )

    @jmb.page("page", Component.Config(components=dict(a=A, b=B)))
    class Page(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>"
                "{{component('a')}}"
                "{{component('b')}}"
                "</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page"}\'><body>"""
        """<p jmb-name="/page/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/a"}\'>A</p>"""
        """<p jmb-name="/page/b" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/b"}\'>B2A: /page/a, /page/a</p>"""
        """</body></html>"""
    ).encode("utf-8")


def test_inject_into_component_method(jmb, client):
    class Project(Component):
        def __init__(self, id: int):
            super().__init__()

        def inject_into(self, cconfig: "ComponentConfig") -> Dict[str, Any]:
            return dict(project_id=self.state.id)

        @action
        def goto(self, id: int):
            self.state.id = id

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>Project {{id}}{{component('tasks')}}</div>"
            )

    class Tasks(Component):
        def __init__(self, project_id: Optional[int] = None):
            super().__init__()

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>Tasks for project: {{project_id}}</div>"
            )

    @jmb.page(
        "test",
        Component.Config(
            components=dict(
                project=(Project, Project.Config(components=dict(tasks=Tasks)))
            )
        ),
    )
    class Test(Component):
        @listener(event="_display", source="project")
        def on_project_display(self, event):
            self.project_id = event.source.state.id

        def display(self) -> "DisplayResponse":
            self.project_id = getattr(self, "project_id", 1)
            return self.render_template_string(
                "<html><body>{{component('project', id=project_id)}}</body></html>"
            )

    r = client.get("/test")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/test" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test"}\'><body>"""
        """<div jmb-name="/test/project" jmb-data=\'{"actions":{"goto":true},"changesUrl":true,"state":{"id":1},"url":"/test/project/1"}\'>"""
        """Project 1"""
        """<div jmb-name="/test/project/tasks" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test/project/1/tasks"}\'>"""
        """Tasks for project: 1"""
        """</div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")
    r = client.post(
        "/test/project/1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/test", state=dict()),
                    dict(execName="/test/project", state=dict(id=1)),
                    dict(execName="/test/project/tasks", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/test/project",
                        actionName="goto",
                        args=list(),
                        kwargs=dict(id=2),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 2
    assert json_response[0]["execName"] == "/test/project"
    assert (
        json_response[0]["dom"]
        == """<div>Project 2<template jmb-placeholder="/test/project/tasks"></template></div>"""
    )
    assert json_response[1]["execName"] == "/test/project/tasks"
    assert json_response[1]["dom"] == """<div>Tasks for project: 2</div>"""


def test_redirect_to(jmb, client):
    class B(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>{{exec_name}}</div>")

    @config(Component.Config(components=dict(b=B)))
    class A(Component):
        @action
        def goto(self, where):
            self.redirect_to(self.component(where))

        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>{{component('b')}}</div>")

    @jmb.page(
        "page", Component.Config(components=dict(a1=A, a2=A)),
    )
    class Page(Component):
        def __init__(self, display_mode: str = "a1"):
            super().__init__()

        @listener(event="_display", source="*")
        def on_display(self, event):
            self.state.display_mode = event.source_name

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component(display_mode)}}</body></html>"
            )

    r = client.get("/page")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n"""
        """<html jmb-name="/page" jmb-data=\'{"actions":{},"changesUrl":true,"state":{"display_mode":"a1"},"url":"/page"}\'><body>"""
        """<div jmb-name="/page/a1" jmb-data=\'{"actions":{"goto":true},"changesUrl":true,"state":{},"url":"/page/a1"}\'>"""
        """<div jmb-name="/page/a1/b" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/page/a1/b"}\'>"""
        """/page/a1/b"""
        """</div>"""
        """</div>"""
        """</body></html>"""
    ).encode("utf-8")
    r = client.post(
        "/page/a1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict(display_mode="a1")),
                    dict(execName="/page/a1", state=dict()),
                    dict(execName="/page/a1/b", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/page/a1",
                        actionName="goto",
                        args=list(),
                        kwargs=dict(where="../a2"),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["state"] == dict(display_mode="a2")
    assert json_response[1]["execName"] == "/page/a2"
    assert json_response[2]["execName"] == "/page/a2/b"
    r = client.post(
        "/page/a1",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/page", state=dict(display_mode="a1")),
                    dict(execName="/page/a1", state=dict()),
                    dict(execName="/page/a1/b", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/page/a1",
                        actionName="goto",
                        args=list(),
                        kwargs=dict(where="/page/a2"),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    json_response = json.loads(r.data)
    assert r.status_code == 200
    assert len(json_response) == 3
    assert json_response[0]["execName"] == "/page"
    assert json_response[0]["state"] == dict(display_mode="a2")
    assert json_response[1]["execName"] == "/page/a2"
    assert json_response[2]["execName"] == "/page/a2/b"


def test_build_exec_name(app, jmb: "Jembe"):
    class A(Component):
        def display(self) -> "DisplayResponse":
            return ""

    @jmb.page(
        "page",
        Component.Config(
            components=dict(
                a=(A, A.Config(components=dict(a1=A, a2=A, a3=A))),
                b=(A, A.Config(components=dict(b1=A, b2=A, b3=A))),
                c=(A, A.Config(components=dict(c1=A, c2=A, c3=A))),
            )
        ),
    )
    class Page(Component):
        def display(self) -> "DisplayResponse":
            return ""

    with app.test_request_context(path="/page/a"):
        processor = get_processor()
        processor.process_request()

        def getc(exec_name):
            return processor.components[exec_name]

        assert (
            getc("/page/a").component("a1").call("update").jrl
            == "$jmb.component('a1').call('update',{})"
        )
        assert (
            getc("/page/a").component("a1").call("update", a=1, b=2).jrl
            == "$jmb.component('a1').call('update',{a:1,b:2})"
        )
        assert getc("/page/a").component(".").call("display").jrl == "$jmb.display()"
        assert (
            getc("/page/a").component(".").call("update").jrl
            == "$jmb.call('update',{})"
        )
        assert getc("/page").component().call("display").jrl == "$jmb.display()"


def test_handling_exception_raised_by_action(jmb, client):
    class A(Component):
        @action
        def test_action(self):
            raise NotFound

        @action
        def test_action2(self):
            raise Forbidden

        @listener(event="_exception")
        def on_exception(self, event: "Event"):
            if event.handled:
                return

            if event.in_action == "test_action2":
                event.handled = True
                return True

        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>A</div>")

    @jmb.page("test", Component.Config(components=dict(a=A)))
    class Test(Component):
        def __init__(self):
            self.exc_from = ""
            super().__init__()

        @listener(event="_exception")
        def on_exception(self, event: "Event"):
            if event.handled:
                return

            self.exc_from = "{}:{}".format(event.source_full_name, event.in_action)
            event.handled = True
            return True

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{exc_from}}{{component('a')}}</body></html>"
            )

    r = client.get("/test")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/test" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/test"}\'><body>"""
        """"""
        """<div jmb-name="/test/a" jmb-data=\'{"actions":{"test_action":true,"test_action2":true},"changesUrl":true,"state":{},"url":"/test/a"}\'>A</div>"""
        "</body></html>"
    ).encode("utf-8")

    r = client.post(
        "/test/a",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/test", state=dict()),
                    dict(execName="/test/a", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/test/a",
                        actionName="test_action",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    res = json.loads(r.data)
    assert len(res) == 1
    assert res[0]["execName"] == "/test"
    assert (
        res[0]["dom"]
        == """<html><body>/test/a:test_action<template jmb-placeholder="/test/a"></template></body></html>"""
    )
    r = client.post(
        "/test/a",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/test", state=dict()),
                    dict(execName="/test/a", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/test/a",
                        actionName="test_action2",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    res = json.loads(r.data)
    assert len(res) == 1
    assert res[0]["execName"] == "/test/a"
    assert res[0]["dom"] == """<div>A</div>"""


def test_access_control(jmb, client):
    class B(Component):
        def __init__(self):
            super().__init__()
            self.ac_deny()

    class A(Component):
        def __init__(self):
            super().__init__()
            self.ac_deny("test_action")

        @action
        def test_action(self):
            pass

        def display(self) -> "DisplayResponse":
            return self.render_template_string("<div>A</div>")

    @jmb.page("test", Component.Config(components=dict(a=A, b=B)))
    class Test(Component):
        exec_from = ""

        @listener(event="_exception")
        def on_exception(self, event: "Event"):
            if event.handled:
                return

            self.exc_from = "{}:{}".format(event.source_full_name, event.in_action)
            event.handled = True
            return True

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{exc_from}}{{component('a')}}</body></html>"
            )

    r = client.post(
        "/test/a",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/test", state=dict()),
                    dict(execName="/test/a", state=dict()),
                ],
                commands=[
                    dict(
                        type="call",
                        componentExecName="/test/a",
                        actionName="test_action",
                        args=list(),
                        kwargs=dict(),
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    res = json.loads(r.data)
    assert len(res) == 1
    assert res[0]["execName"] == "/test"
    assert (
        res[0]["dom"]
        == """<html><body>/test/a:test_action<template jmb-placeholder="/test/a"></template></body></html>"""
    )
    r = client.post(
        "/test/a",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/test", state=dict()),
                    dict(execName="/test/a", state=dict()),
                ],
                commands=[
                    dict(
                        type="init",
                        componentExecName="/test/b",
                        initParams=dict(),
                        mergeExistingParams=True,
                    ),
                ],
            )
        ),
        headers={"x-jembe": True},
    )
    assert r.status_code == 200
    res = json.loads(r.data)
    assert len(res) == 1
    assert res[0]["execName"] == "/test"
    assert (
        res[0]["dom"]
        == """<html><body>/test/b:None<template jmb-placeholder="/test/a"></template></body></html>"""
    )


def test_reference_call_action_is_accessible(app, jmb: "Jembe"):
    class A(Component):
        def __init__(self):
            self.ac_deny("taction")
            super().__init__()

        @action
        def taction(self):
            pass

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>A{% if component('c').is_accessible %}{{component()}}{% endif %}</div>"
            )

    class B(Component):
        @action
        def taction(self):
            pass

        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>B{% if component('c').is_accessible %}{{component()}}{% endif %}</div>"
            )

    @jmb.page(
        "page",
        Component.Config(
            components=dict(
                a=(A, A.Config(components=dict(c=B))),
                b=(B, B.Config(components=dict(c=A))),
            )
        ),
    )
    class Page(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('a')}}{{component('b')}}</body></html>"
            )

    with app.test_request_context(path="/page/a"):
        processor = get_processor()
        processor.process_request()

        def getc(exec_name):
            return processor.components[exec_name]

        assert getc("/page/a").component().call("taction").is_accessible == False
        assert getc("/page/b").component().call("taction").is_accessible == True
        assert getc("/page/a/c").component().call("taction").is_accessible == True
        assert getc("/page/b/c").component().call("taction").is_accessible == False

def test_reference_deep_component_on_another_page(app, jmb: "Jembe", client):
    class A(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>A</div>"
            )

    class B(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<div>B</div>"
            )

    @jmb.page(
        "pagea",
        Component.Config(
            components=dict(
                a=A,
            )
        ),
    )
    class PageA(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('a')}}<div>{{component('/pageb/b').url}}</div></body></html>"
            )
    @jmb.page(
        "pageb",
        Component.Config(
            components=dict(
                b=B,
            )
        ),
    )
    class PageB(Component):
        def display(self) -> "DisplayResponse":
            return self.render_template_string(
                "<html><body>{{component('b')}}</body></html>"
            )


    r = client.get("/pagea")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb-name="/pagea" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/pagea"}\'><body>"""
        """<div jmb-name="/pagea/a" jmb-data=\'{"actions":{},"changesUrl":true,"state":{},"url":"/pagea/a"}\'>A</div><div>/pageb/b</div>"""
        "</body></html>"
    ).encode("utf-8")