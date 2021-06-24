Quickstart
----------

Install Jembe
~~~~~~~~~~~~~

.. important::
    Jembe requires **Python 3.8** or above.


.. code:: bash

    # Create project directory
    $ mkdir myproject
    $ cd myproject

    # Create Python virtual enviroment and activate it
    $ python -m venv .venv
    $ . .venv/bin/activate 

    # Install Jembe framework in newly created vritual enviroment
    $ pip install jembe

    # Start a new project with the premade project template
    $ jembe startproject

    # Install developer dependencies in a virtual environment
    $ pip install -e .[dev]

    # Run application
    $ flask run

With broswer open http://localhost:5000 to view newly created jembe
application.

.. note::
    Following examples assumes that the Jembe project is named
    **'myproject'** and it's created with ``$ jembe startproject``
    command.

Hello World Example
~~~~~~~~~~~~~~~~~~~

Create a simple Component to render a static HTML page.

myproject/pages/hello\_world.py
'''''''''''''''''''''''''''''''

.. code:: python

    from jembe import Component
    from myproject.app import jmb

    @jmb.page('hello')
    class HellowWorld(Component):
        pass

myproject/templates/hello.html
''''''''''''''''''''''''''''''

.. code:: jinja

    <html>
    <body>
        <h1>Hello World!</h1>
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
    </body>
    </html>

In ``myproject/pages/__init__.py`` add
``from .hello_world import HelloWorld``.

Visit ``http://localhost:5000/hello``.

Making Hello World Dynamic
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Use Component **state variable** to represent the current state of
   the Component.
-  Allow a user to update Component **state** by interacting with HTML
   input field.

myproject/pages/hello\_world.py
'''''''''''''''''''''''''''''''

.. code:: python

    from jembe import Component
    from myproject.app import jmb

    @jmb.page('hello')
    class HellowWorld(Component):
        def __init__(self, name: str = "World"):
            super().__init__()

myproject/templates/hello.html
''''''''''''''''''''''''''''''

.. code:: jinja

    <html>
    <body>
        <h1>Hello {{name}}!</h1>
        <input jmb-on:keydown.debounce="name = $self.value" value="{{name}}">

        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        <script defer>
        {# Adds CSRF protection to Jembe AJAX requests #}
        window.addEventListener('DOMContentLoaded', function(event){
            window.jembeClient.addXRequestHeaderGenerator(function () {
                return {'X-CSRFToken': window.jembeClient.getCookie("_csrf_token")};
            })
        })
        </script>
    </body>
    </html>

.. figure:: /doc/hello_world.gif
   :alt: Hello World

   Hello World
Notice that the input field doesn't lose focus when the page is updated.

    -  First ``script`` tag is required only on Root/Page component, aka
       ``@jmb.page(..)`` Component;
    -  Second ``script`` tag is required by ``jembe startproject``
       template to add CSRF protection, and it is added only to
       Root/Page component;

Counter Example
~~~~~~~~~~~~~~~

-  Defines component **actions**.
-  Execute **actions** when an user press button inside component HTML.
-  Creates complex pages by nesting multiple components.

myproject/pages/counter.py
''''''''''''''''''''''''''

.. code:: python

    from jembe import Component, action, config
    from myproject.app import jmb


    class Counter(Component):
        def __init__(self, count:int = 0):
            super().__init__()

        @action
        def increase(self):
            self.state.count += 1

        @action
        def decrease(self):
            self.state.count -= 1


    @jmb.page(
        "counter",
        Component.Config(
            components={
                "counter": Counter
            }
        )
    )
    class CounterPage(Component):
        pass

In ``myproject/pages/__init__.py`` add
``from .counter import CounterPage``.

myproject/templates/counter/counter.html
''''''''''''''''''''''''''''''''''''''''

.. code:: jinja

    <h2>Counter</h2>
    <div>
        Value: {{count}}
        <button jmb-on:click="decrease()" type="button">-</button>
        <button jmb-on:click="increase()" type="button">+</button>
    </div>

myproject/templates/counter.html
''''''''''''''''''''''''''''''''

.. code:: jinja

    <html>
    <body>
        {{component('counter')}}

        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        <script defer>
        {# Adds CSRF protection to Jembe AJAX requests #}
        window.addEventListener('DOMContentLoaded', function(event){
            window.jembeClient.addXRequestHeaderGenerator(function () {
                return {'X-CSRFToken': window.jembeClient.getCookie("_csrf_token")};
            })
        })
        </script>
    </body>
    </html>

.. figure:: /doc/counter.gif
   :alt: Counter Demo

   Counter Demo
When increasing/decreasing counter, Jembe only renderers and updated
Counter Component HTML, the rest of the HTML on the page is not changed.

Multiple Counters Example
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Changes component configuration, instructing Jembe that URL should
   not be changed when the component is displayed on the page;
-  Communicate between components using events and listeners.
-  Use multiple instances of the same component on a page.

myproject/pages/multi\_counter.py
'''''''''''''''''''''''''''''''''

.. code:: python

    from jembe import Component, Event, action, config, listener
    from myproject.app import jmb

    @config(Component.Config(changes_url=False))
    class Counter(Component):
        def __init__(self, count:int = 0):
            super().__init__()

        @action
        def increase(self):
            self.state.count += 1
            self.emit("updateSum", value=1)

        @action
        def decrease(self):
            self.state.count -= 1
            self.emit("updateSum", value=-1)


    @config(Component.Config(changes_url=False))
    class CounterSum(Component):
        def __init__(self, sum:int = 0):
            super().__init__()

        @listener(event="updateSum")
        def on_update_sum(self, event:"Event"):
            self.state.sum += event.params["value"]


    @jmb.page(
        'multicount',
        Component.Config(
            components={
                "counter": Counter,
                "sum": CounterSum,
            }
        )
    )
    class MultiCountPage(Component):
        pass

In ``myproject/pages/__init__.py`` add
``from .multi_counter import MultiCountPage``.

myproject/templates/multicount/counter.html
'''''''''''''''''''''''''''''''''''''''''''

.. code:: jinja

    <div>
        Counter {{key}}: {{count}}
        <button jmb-on:click="decrease()" type="button">-</button>
        <button jmb-on:click="increase()" type="button">+</button>
    </div>

myproject/templates/multicount/sum.html
'''''''''''''''''''''''''''''''''''''''

.. code:: jinja

    <div>
        <strong>Total: {{sum}}</strong>
    </div>

myproject/templates/multicount.html
'''''''''''''''''''''''''''''''''''

.. code:: jinja

    <html>
    <body>
        {{component('counter').key('a')}}
        {{component('counter').key('b')}}
        {{component('counter').key('c')}}
        {{component('sum')}}

        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        <script defer>
        {# Adds CSRF protection to Jembe AJAX requests #}
        window.addEventListener('DOMContentLoaded', function(event){
            window.jembeClient.addXRequestHeaderGenerator(function () {
                return {'X-CSRFToken': window.jembeClient.getCookie("_csrf_token")};
            })
        })
        </script>
    </body>
    </html>

.. figure:: /doc/multicounter.gif
   :alt: Multi Counter Demo

   Multi Counter Demo
When the user changes the value of one Counter Component, only that
Counter and CounterSum Component HTML are redisplayed and updated.
