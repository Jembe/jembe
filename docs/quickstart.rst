Quickstart
----------

Install Jembe
~~~~~~~~~~~~~

.. important::
    Jembe requires **Python 3.8** or above.

Install Jembe using `pip`, and use premade project template to create and run new project.

.. code-block:: bash

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

With browser open http://localhost:5000 to view newly created jembe
application.


Project Examples
~~~~~~~~~~~~~~~~

The following examples assumes that the Jembe project is named
**'myproject'** and it's created with ``$ jembe startproject``
command.


Hello World Example
===================

In this example, we'll create a simple Component to render a static HTML page.


.. code-block:: python
    :caption: myproject/pages/hello_world.py

    from jembe import Component
    from myproject.app import jmb

    @jmb.page('hello')
    class HellowWorld(Component):
        pass

.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add at the end of the file
    from .hello_world import HelloWorld

.. code-block:: jinja
    :caption: myproject/templates/hello.html

    <html>
    <body>
        <h1>Hello World!</h1>
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
    </body>
    </html>


Visit ``http://localhost:5000/hello``.

Making Hello World Dynamic
==========================

Now let's allow a user to change its name by:

-  Using Component **state variable** to store his name,
-  and HTML Input field to update his name stored in Component **state**.


.. code-block:: python
    :caption: myproject/pages/hello_world.py

    from jembe import Component
    from myproject.app import jmb

    @jmb.page('hello')
    class HellowWorld(Component):
        # all __init__ parameters whose name 
        # does not start with an underscore (_)
        # will be state variables
        # and they must have type annotation
        def __init__(self, name: str = "World"):
            super().__init__()

.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add at the end of the file
    from .hello_world import HelloWorld

.. code-block:: jinja
    :caption: myproject/templates/hello.html

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

.. figure:: /img/hello_world.gif
   :alt: Hello World

Notice that the input field doesn't lose focus when the page is updated.

.. note::
    -  First ``script`` tag is required only for Page Component, aka component decorated with ``@jmb.page(..)``;
    -  Second ``script`` tag is required by ``jembe startproject`` template to add CSRF protection, and it should be added only to component decorated with ``@jmb.page(..)``;

Counter Example
===============

In this example, we'll:

-  create **actions** that will be executed when a user press button;
-  and combine multiple components to create complex pages;


.. code-block:: python
    :caption: myproject/pages/counter.py

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

.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add at the end of the file
    from .counter import CounterPage


.. code-block:: html
    :caption: myproject/templates/counter/counter.html

    <h2>Counter</h2>
    <div>
        Value: {{count}}
        <button jmb-on:click="decrease()" type="button">-</button>
        <button jmb-on:click="increase()" type="button">+</button>
    </div>


.. code-block:: jinja
    :caption: myproject/templates/counter.html

    <html>
    <body>
        <!-- adds "counter" component to page -->
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

.. figure:: /img/counter.gif
   :alt: Counter Demo

When increasing/decreasing counter, Counter Component HTML is rendered and updated, the rest of the HTML on the page is not changed.

Multiple Counters Example
=========================

-  Changes component configuration, instructing Jembe that URL should
   not be changed when the component is displayed on the page;
-  Communicate between components using **events** and **listeners**.
-  Use multiple instances of the same component on a page.


.. code-block:: python
    :caption: myproject/pages/multi\_counter.py

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


.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add at the end of the file
    from .multi_counter import MultiCountPage

.. code-block:: jinja
    :caption: myproject/templates/multicount/counter.html

    <div>
        Counter {{key}}: {{count}}
        <button jmb-on:click="decrease()" type="button">-</button>
        <button jmb-on:click="increase()" type="button">+</button>
    </div>


.. code-block:: jinja
    :caption: myproject/templates/multicount/sum.html

    <div>
        <strong>Total: {{sum}}</strong>
    </div>


.. code-block:: jinja
    :caption: myproject/templates/multicount.html

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

.. figure:: /img/multicounter.gif
   :alt: Multi Counter Demo

When the user changes the value of one Counter Component, only that
Counter and CounterSum Component HTML are redisplayed and updated.
