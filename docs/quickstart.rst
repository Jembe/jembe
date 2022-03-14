Quickstart
----------

Install Jembe
~~~~~~~~~~~~~

.. important::
    Jembe requires **Python 3.8** or above.

Installing Jembe using `pip`, and starting new project from project template:

.. code-block:: bash

    # Create project directory
    $ mkdir myproject
    $ cd myproject

    # Create Python virtual enviroment and activate it
    $ python -m venv .venv
    $ . .venv/bin/activate 

    # Install Jembe framework in newly created vritual enviroment
    $ pip install jembe

    # Start a new project
    $ jembe startproject

    # Install developer dependencies in a virtual environment
    $ pip install -e .[dev]

    # Run application
    $ flask run

Open http://localhost:5000 in browser to view newly created application.

Project Folder Structure
========================

You can organize your code as you want, the structure bellow is used by default
with ``jembe startproject`` command, this structure is recomended for developing applications 
with Jembe Components.

.. code-block:: bash

    myproject                       # - Project root directory
    ├── data                        # - Permanent and temporary data storage 
    │                               #   for application files, images, etc.
    │
    ├── instance                    # - Flask instance folder
    │   └── config.py               # - Application configuration
    ├── myproject                   # - Package with your application source code
    │   ├── __init__.py             # - Initilase Flask
    │   ├── app.py                  # - Initialise Jembe and other Flask extensions
    │   ├── commands.py             # - Custom Flask CLI commands
    │   ├── pages                   # - Package for Jembe Components
    │   │   ├── __init__.py         # - Imports Jembe @page Components 
    │   │   │                       #   so that Jembe instance can find them
    │   │   ├── _counter.py         
    │   │   └── main.py
    │   ├── static                  # - Static resources
    │   │   └── css
    │   │       └── myproject.css   
    │   ├── templates               # - Jinja2 templates
    │   │   ├── main
    │   │   │   └── counter.html
    │   │   └── main.html
    │   └── views
    │       └── __init__.py         # - Flask view that redirects request for / 
    │                               #   to "/main" Jembe Component
    ├── .flaskenv                   # - Sets OS enviroment variables 
    ├── pyproject.toml              # - packaging configuration
    ├── README.md
    ├── LICENSE
    ├── setup.cfg                   # - setuptools configuration
    ├── setup.py                    # - script to run setuptools
    └── tests                       # - place for tests
        └── conftest.py             # - pytest configuration


Main advantages of this project structure are:

1. Easy packaging and publishing on private or public `pip` repositories;
2. Easy installation in production with:

   1. ``pip install myproject``;
   2. creating ``instance/config.py`` with production settings;
   3. creating ``data`` directory;

3. Easy production update with ``pip install --update myproject``;
4. Application data (files, images, etc.) are separated from application code in ``data`` directory;
5. Creation of development enviroment with ``pip install .[dev]`` 
6. Development and production enviroment are created with same commands and are "exacly the same";
7. All Jembe Components are organized inside ``pages`` subpackage.

Main drawbacks are:

1. Dependencies in setup.cfg must be manually maintained;
2. Whole application is in one package, which may not be ideal for very large 
   application maintained by multiple teams.


Jembe Examples
~~~~~~~~~~~~~~

To better understand how Jembe works, let's write some simple applications.

.. important:: 
    The following examples assumes that the project is named
    **'myproject'** and it's created with ``$ jembe startproject``
    command.


Hello World Example
===================

Let's create a simple Component to render a static HTML page.


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


Open http://localhost:5000/hello in browser to see Helo World page.

Making Hello World Dynamic
==========================

Now let's allow a user to say Hello to himself by:

-  Typing name in input field and updating Hello message.

.. note:: 
    This example uses Component **state variable** to store name from input field. Component HTML is redisplayed every time
    any state variable is changed.


.. code-block:: python
    :caption: myproject/pages/hello_world.py

    from jembe import Component
    from myproject.app import jmb

    @jmb.page('hello')
    class HellowWorld(Component):
        # all __init__ parameters whose name 
        # does not start with an underscore (_)
        # will become state variables.
        # 
        # State variables must be annotated with type 
        # in order to be serialized and used by
        # javascript in jinja2 template.
        def __init__(self, name: str = "World"):
            """
                State variable "name" is avaiable in this component as
                ''self.state.name'' without any need to explicitly 
                set it in __init__ method.
            """
            super().__init__()

.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add this at the end of the __init__.py
    # for Jembe instance to find HelloWorld @page 
    from .hello_world import HelloWorld

.. code-block:: jinja
    :caption: myproject/templates/hello.html

    <html>
    <body>
        <h1>Hello {{name}}!</h1>
        {# on keydown change component state 'name' to value of input field #}
        <input 
            jmb-on:keydown.debounce="name = $self.value" 
            value="{{name}}">

        {# Following is boilerplate code required only for 
           @jmb.page component to:
            - import Jembe client javascript and,
            - add CSRF protection to Jembe AJAX requests. #}
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        <script defer>
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

In this example, we'll create "counter" that can be increased or decreased by clicking on ``+`` or ``-`` buttons.

.. note:: 
    This example uses **actions** that will be executed when a user clicks on buttons, it also uses multiple components to create complex application;


.. code-block:: python
    :caption: myproject/pages/counter.py

    from jembe import Component, action, config
    from myproject.app import jmb


    class Counter(Component):
        """ 
            Component that tracks current count and
            defines increase and decrease actions.
        """
        def __init__(self, count:int = 0):
            """ 
                Defines "count" as integer state variable default value 0.
            """
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
        """Page component with one sub-component "counter". """"
        pass

.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add this at the end of the __init__.py
    # for Jembe instance to find CounterPage 
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
        {# display "counter" subcomponent #}
        {{component('counter')}}

        {# Boilerplate code required by Jembe only for @jmb.page Compoennt #}
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        <script defer>
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

Let's put multiple counters on page and display sum of all counters.


.. note::
    This example demonstrates how to:

    -  Change component configuration without extending its class, by instructing Jembe that URL 
       should not be changed when the component is displayed on the page;
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

    # add at the end of the __init__.py file
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

        {# Boilerplate code required by Jembe only for @jmb.page Component #}
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
        <script defer>
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
