from typing import TYPE_CHECKING, Optional, Tuple, Sequence, List
from jembe import Component
from flask import json
from jembe import action, listener, config, redisplay


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
                """<div>Counter ({{key}}): {{value}}<button onclick="$jmb.set('value', {{value + 1}})">Increase</button></div>"""
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
                """<button onclick="$jmb.call('add_counter', $jmb.ref('key').value)">Add counter</button>"""
                """{% for counter in counters %}"""
                """<div>{{component("counter").key(counter)}}<button onclick="$jmb.call('remove_counter', '{{counter}}')">Remove</div></div>"""
                "{% endfor %}"
                "</body></html>"
            )

    # display page with no counters
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

    # call to first counter with url should add that counter
    r = client.get("/cpage/counter.first")
    assert r.status_code == 200
    assert r.data == (
        """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">"""
        "\n"
        """<html jmb:name="/cpage" jmb:state=\'{"counters":["first"]}\' jmb:url="/cpage"><head></head><body>"""
        """<input jmb:ref="key" name="key" value="">"""
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref(\'key\').value)">Add counter</button>"""
        """<div><div jmb:name="/cpage/counter.first" jmb:state=\'{"value":0}\' jmb:url="/cpage/counter.first">Counter (first): 0<button onclick="$jmb.set('value', 1)">Increase</button></div>"""
        """<button onclick="$jmb.call('remove_counter', 'first')">Remove</button></div>"""
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
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><div jmb-placeholder="/cpage/counter.first"></div><button onclick="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.first"
    assert json_response[1]["dom"] == (
        """<div>Counter (first): 0<button onclick="$jmb.set('value', 1)">Increase</button></div>"""
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
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><div jmb-placeholder="/cpage/counter.first"></div><button onclick="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><div jmb-placeholder="/cpage/counter.second"></div><button onclick="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.second"
    assert json_response[1]["dom"] == (
        """<div>Counter (second): 0<button onclick="$jmb.set('value', 1)">Increase</button></div>"""
    )
    # increase and add counter
    r = client.post(
        "/cpage",
        data=json.dumps(
            dict(
                components=[
                    dict(execName="/cpage", state=dict(counters=["first", "second"])),
                    dict(execName="/cpage/counter.first", state=dict(value=0)),
                    # dict(execName="/cpage/counter.second", state=dict(value=0)),
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
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><div jmb-placeholder="/cpage/counter.first"></div><button onclick="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><div jmb-placeholder="/cpage/counter.second"></div><button onclick="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
        """<div><div jmb-placeholder="/cpage/counter.third"></div><button onclick="$jmb.call('remove_counter', 'third')">Remove</div></div>"""
        "</body></html>"
    )
    assert json_response[1]["execName"] == "/cpage/counter.second"
    assert json_response[1]["dom"] == (
        """<div>Counter (second): 1<button onclick="$jmb.set('value', 2)">Increase</button></div>"""
    )
    assert json_response[2]["execName"] == "/cpage/counter.third"
    assert json_response[2]["dom"] == (
        """<div>Counter (third): 0<button onclick="$jmb.set('value', 1)">Increase</button></div>"""
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
                    # dict(execName="/cpage/counter.second", state=dict(value=2)),
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
        """<div>Counter (second): 2<button onclick="$jmb.set('value', 3)">Increase</button></div>"""
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
        """<button onclick="$jmb.call(\'add_counter\', $jmb.ref('key').value)">Add counter</button>"""
        """<div><div jmb-placeholder="/cpage/counter.first"></div><button onclick="$jmb.call('remove_counter', 'first')">Remove</div></div>"""
        """<div><div jmb-placeholder="/cpage/counter.second"></div><button onclick="$jmb.call('remove_counter', 'second')">Remove</div></div>"""
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
        """<html jmb:name="/cpage" jmb:state="{}" jmb:url="/cpage"><head></head><body>"""
        """<div jmb:name="/cpage/counter" jmb:state=\'{"value":10}\' jmb:url="/cpage/counter">10</div>"""
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
        """<html jmb:name="/cpage" jmb:state="{}" jmb:url="/cpage"><head></head><body>"""
        """<div jmb:name="/cpage/counter.1" jmb:state=\'{"id":1}\' jmb:url="/cpage/counter.1/1">10</div>"""
        """<div jmb:name="/cpage/counter.2" jmb:state=\'{"id":2}\' jmb:url="/cpage/counter.2/2">20</div>"""
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
    assert len(ajax_data) ==1
    assert ajax_data[0]["execName"] == "/cpage/counter.1"
    assert ajax_data[0]["state"] == dict(id=1)
    assert ajax_data[0]["dom"] == "<div>11</div>"

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
