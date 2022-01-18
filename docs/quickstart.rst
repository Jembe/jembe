Quickstart
----------

Install Jembe
~~~~~~~~~~~~~

.. important::
    Jembe requires **Python 3.8** or above.

To install Jembe using `pip`, and start new project with premade project template:

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

Project Folder Structure
========================

.. code-block:: bash

    myproject                       # - Project root directory
    ├── data                        # - Permanent and temporary storage 
    │                               #   for application files, images, etc.
    ├── instance                    # - Flask instance folder
    │   └── config.py               # - Application configuration settings
    ├── myproject                   # - Package with your application
    │   │                           #   source code
    │   ├── __init__.py             # - Initilase Flask
    │   ├── app.py                  # - Initialise Jembe and other Flask 
    │   │                           #   extensions
    │   ├── commands.py             # - Custom Flask CLI commands
    │   │                             
    │   ├── pages                   # - Package for Jembe Components
    │   │   ├── __init__.py         # - Imports Jembe Component decorated
    │   │                           #   with @page so that Jembe instance
    │   │                           #   can find them
    │   │   ├── _counter.py         
    │   │   └── main.py
    │   ├── static                  # - Static resources
    │   │   └── css
    │   │       └── myproject.css   
    │   ├── templates               # - Jinja2 templates for Jembe 
    │   │   │                       #   components
    │   │   ├── main
    │   │   │   └── counter.html
    │   │   └── main.html
    │   └── views
    │       └── __init__.py         # - Flask view for redirecting 
    │                               #   requsets from root URL 
    │                               #   to "/main" Jembe @page Component
    ├── .flaskenv                   # - Sets required OS enviroment variables
    │                               #   before starting app
    ├── pyproject.toml              # - packaging configuration
    ├── README.md
    ├── LICENSE
    ├── setup.cfg                   # - setuptools configuration
    ├── setup.py                    # - script to run setuptools
    └── tests                       # - place for tests
        └── conftest.py             # - pytest configuration

You can organize your code as you want, the structure above is used by default
template created with ``jembe startproject`` command.

Main advantages of this project structure are:

1. Easy packaging and publishing on private or public `pip` repositories;
2. Easy installation in production with:

   1. ``pip install myproject``;
   2. create ``config.py`` for production and put it in ``instance`` subfolder;
   3. create ``data`` directory;

3. Easy production update with ``pip install --update myproject``;
4. Application data (files, images, etc.) are separated from application code in ``data`` directory;
5. Easy creation of development enviroment with ``pip install .[dev]`` 
6. Development and production enviroment are created with same commands and are "exacly the same";
7. All Jembe Components are organized inside ``pages`` subpackage.

Main drawbacks are:

1. Dependencies in setup.cfg must be manually maintained;
2. Whole application is in one package, which is not ideal for very large 
   application maintained by multiple teams.


Introduction to Jembe
~~~~~~~~~~~~~~~~~~~~~

To better understand how Jembe works, let's write couple simple applications.

The following examples assumes that the project is named
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

-  Using **state variable** to store his name,
-  and HTML Input field to update his name stored in **state variable**.


.. code-block:: python
    :caption: myproject/pages/hello_world.py

    from jembe import Component
    from myproject.app import jmb

    @jmb.page('hello')
    class HellowWorld(Component):
        # all __init__ parameters whose name 
        # does not start with an underscore (_)
        # will be state variables
        # and they must been annotated with type
        def __init__(self, name: str = "World"):
            """
                State variable "name" is avaiable in this component as
                ''self.state.name'' without any need to explicitly 
                set it in __init__ method.
            """
            super().__init__()

.. code-block:: python
    :caption: myproject/pages/__init__.py

    # add at the end of the file
    # to enable application to find your
    # newlly crated @jmb.page
    from .hello_world import HelloWorld

.. code-block:: jinja
    :caption: myproject/templates/hello.html

    <html>
    <body>
        <h1>Hello {{name}}!</h1>
        <input 
            jmb-on:keydown.debounce="name = $self.value" 
            value="{{name}}"
        >

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

In this example, we'll:

-  create **actions** that will be executed when a user press button;
-  and combine multiple components to create complex pages;


.. code-block:: python
    :caption: myproject/pages/counter.py

    from jembe import Component, action, config
    from myproject.app import jmb


    class Counter(Component):
        """ 
            Keeps track of current count and defines 
            actions to increase and decrease it.
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

    # add at the end of the file
    # for application to find CounterPage
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
        <!-- displays "counter" subcomponent -->
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

Using multiple components of same class on one page, demonstrates how to:

-  Changes component configuration without extending its class, by instructing Jembe that URL 
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
