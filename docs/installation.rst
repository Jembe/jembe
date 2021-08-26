Installation
------------

.. _installation:

Install Jembe
=============

Install the latest version of Jembe from pypi.org using `pip` command:

.. code-block:: bash

    $ pip install jembe

It's recommended to install Jembe in a separate Python virtual environment:

.. code-block:: bash

    # Create new virtual enviroment
    $ python -m venv .venv

    # Activate virtual enviroment
    $ . .venv/bin/activate

    # Install Jembe into an active virtual environment
    (.venv) $ pip install jembe

Minimal Jembe Application
=========================

Bellow is minimal one file "Hello World" example.

.. code-block:: python
    :caption: helloworld.py
    :linenos:

    from flask import Flask, redirect
    from jembe import Component, page_url

    app = Flask(__name__)
    jmb = Jembe(app)

    @jmb.page("main")
    class MainPage(Component):
        def display():
            return self.render_template_string("""
    <html>
    <body>
        <h1>Welcome from Jembe</h1>
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}" defer></script>
    </body>
    </html>
            """)


    @app.route("/")
    def index():
        """Redirect request for root url to 'main' Jembe page"""
        return redirect(page_url("/main"))

What does the code do?

1. First we imported **Flask** and Jembe **Component** classes, together with 
   **redirect** and **page\_url** functions.
2. Next we create an instance of Flask class. This instance will be our
   application. The first argument is the name of the application's
   module or package, it's needed for Flask to knows where to look for
   resources such as templates and static files.
3. Then we create an instance of Jembe class, this instance will
   initialise and manage Jembe Components. The first argument of Jembe instance is 
   the instance of the Flask application.

   Jembe instance uses Flask for handling HTTP request/response cycle,
   loading templates and resources etc..

4. Using **page** decorator we register MainPage Component to Jembe
   instance.

   1. Registring Component with page decorator tells Jembe that this component
      is part of our web application.
   2. First parameter of page decorator is component name that is used to generate URL for that
      component and to uniquly idnetify this component inside Jembe application.
   3. **display** method returns HTML that we want to display in the browser. 
      
      To create HTML we used inline rendering of
      Jinja2 template. We could also use regular string if we wanted to or load Jinja2 template.

   4. Because we registred this component as page it's HTML must contains
      ``script`` tag to include Jembe JavaScript.

5. Lastly we use Flask **route()** decorator to redirect the browser to our "main" page.

To run this application use:

.. code:: bash

    $ export FLASK_APP=helloworld
    $ flask run
     * Running on http://127.0.0.1:5000/

.. note::
    'Hello World' example above does not use any of the Jembe Components advantages, it just demonstrates how to write a minimal Jembe application.
    

Use ``jembe startproject`` command
==================================

New project that uses Jembe components can be craeted in two ways:

1. Using project templates with ``jembe startproject`` command, or;
2. Manually by adding Jembe extension to a new or existing Flask project.



.. note::
    Add Jembe extension manually only if it's absolutely necessary 
    otherwise use ``jembe startproject`` to create new applications.


.. code:: bash

    # Starting a new project 
    $ jembe startproject

    # ... Follow instruction and chose basic settings 
    # ... of your new project

    # Install developer dependencies 
    $ pip install -e .[dev]

    # Run application
    $ flask run


.. note:: 
    To use ``jembe startproject`` command, you must first install ``jembe`` package
    in your Python virtual environment as explained in the :ref:`installation` chapter.

New Project Folder Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code::

    myproject                       # Project root directory
    ├── data                        # Application data and files
    ├── instance                    # Flask instance folder
    │   └── config.py               # Application configuration 
    ├── myproject                   # Python package with application 
    │   │                             source code                       
    │   ├── __init__.py             # Initilase Flask
    │   ├── app.py                  # Initialise Jembe and other Flask 
    │   │                             extensions
    │   ├── commands.py             # Custom Flask CLI commands
    │   │                             
    │   ├── pages                   # Package for Jembe Components
    │   │   ├── __init__.py         # Imports Jembe Component decorated
    │   │                             with @page so that Jembe instance
    │   │                             can find them
    │   │   ├── _counter.py         
    │   │   └── main.py
    │   ├── static                  # Static resources
    │   │   └── css
    │   │       └── myproject.css   
    │   ├── templates               # Jinja2 templates for Jembe 
    │   │   │                         components
    │   │   ├── main
    │   │   │   └── counter.html
    │   │   └── main.html
    │   └── views
    │       └── __init__.py         # Flask view for redirecting 
    │                                 requsets from root URL 
    │                                 to "/main" Jembe @page Component
    ├── .flaskenv                   # Sets required OS enviroment variables
    │                                 before starting app
    ├── pyproject.toml              # packaging configuration
    ├── README.md
    ├── LICENSE
    ├── setup.cfg                   # setuptools configuration
    ├── setup.py                    # script to run setuptools
    └── tests                       # place for tests
        └── conftest.py             # pytest configuration

You can organize your code as you want, the structure above is our recommendation for Jembe projects.

Main benefit of this project structure are:

1. Easy packaging and publishing on private or public repository;
2. Easy installation in production:

   1. ``pip install myproject``;
   2. create ``config.py`` for production and put it in ``instance`` folder;
   3. create ``data`` directory;

3. Easy production update with ``pip install --update myproject``;
4. Application data (files etc.) are separated from application code in ``data`` directory;
5. Easy creation of development enviroment with ``pip install .[dev]`` 
6. Jembe Components is organized insiede ``pages`` subpackage.

Main drawbacks are:

1. Dependencies in setup.cfg must be manually maintained;
2. Whole application is in one package, which is not ideal for realy large 
   application.

Add Jembe to an Existing Project
================================

In order to use Jembe components inside existing Flask app you must do the following:

1. Create Flask Application and initialize Jembe as a regular Flask extension; 
2. Create and register your Jembe @page Components to Jembe extension instance;  
3. Add ``script`` HTML tag to load "jembe javascript" only in @page Components HTML templates.

``jembe startproject`` command will do all above for you, but you can allso do it manually when needed.

.. note::
    Usin Jembe Components inside regular Flask views is not currently supported. 
    Entire HTML pages should be built with Jembe Components.



Registring and initializing Jembe as Flask extension;
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
    :caption: myproject/__init__.py

    """Loading Flask statically"""
    from jembe import Jembe

    app = Flask(__name__)
    jmb = Jembe(app)

.. code-block:: python
    :caption: myproject/__init__.py

    """Loadding Flask dynamically"""
    from jembe import Jembe

    jmb = Jembe()

    def create_app(config):
        # ...
        app = Flask(__name__)
        jmb.init_app(app)

Register Jembe @page Components 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
    :caption: myproject/jembe.py

    """Using 'page' decorator"""
    from jembe import Component
    # from [place where you have defined jmb as jmb = Jembe(..)] import jmb
    # from . import jmb

    @jmb.page("main")
    class PageComponent(Component):
        pass

.. code-block:: python
    :caption: myproject/__init__.py

    """Using add_page method"""
    from jembe import Jembe

    jmb = Jembe()

    def create_app(config):
        from .pages import PageComponent
        # ...
        app = Flask(__name__)
        jmb.init_app(app)
        #..
        jmb.add_page("main", PageComponent)

Add necessary javascript to @jmb.page Component HTML/Jinja2 template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default template for @jmba.page Component registred as 'main' is
'main.html'

.. code-block:: html
    :caption: templates/main.html

    <html>
    <head>
    <!-- ... -->
    </head>
    <body>
    <!-- ... -->
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}" defer></script>
    </body>
    <html>
