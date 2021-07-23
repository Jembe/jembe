Installation
------------

.. _installation:

Install Jembe
=============

The Latest Jembe version from pypi.org is installed using `pip` command:

.. code-block:: bash

    $ pip install jembe

To install Jembe in new Python virtual environments do:

.. code-block:: bash

    # Create new virtual enviroment
    $ python -m venv .venv

    # Activate virtual enviroment
    $ . .venv/bin/activate

    # Install Jembe into an active virtual environment
    (.venv) $ pip install jembe

Minimal Application
===================

Bellow is minimal one file "Hello World" example.

.. code-block:: python
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

1. First we imported **Flask** class and **Component** classs together
   with **redirect** and **page\_url** functions.
2. Next we create an instance of Flask class, this instance will be our
   application. The first argument is the name of the application's
   module or package, it's needed for Flask to knows where to look for
   resources such as templates and static files.
3. We then create an instance of Jembe class, this instance will
   initialise and manage Jembe Components. The first argument is the
   instance of associated Flask application.
4. Then we use **page** decorator to register MainPage class to Jembe
   instance.

   1. Registring page to Jembe instance tells Jembe that this component
      is part of our web application and what URL should display it.
   2. Component **display** method returns HTML that we want to display
      in user's browser. To create HTML we used inline rendering of
      Jinja2 template. We could also use regular string if we wanted to.
   3. Because we registred this component as page it's HTML must contains
      ``script`` tag to include Jembe JavaScript.

5. Lastly we use **route()** decorator to tell Flask what URL should
   redirect browser to our "main" Jembe Page Component.

To run this application use:

.. code:: bash

    $ export FLASK_APP=minimal
    $ flask run
     * Running on http://127.0.0.1:5000/

.. note::
    'Hello World' example above does not use any of the Jembe Components advantages, it just demonstrates how to write a minimal Jembe application.
    

Start a New Project
===================

To create Web Application that uses Jembe components you must:

1. Create Flask Application and initialize Jembe as a regular Flask extension; 
2. Create and register your Jembe Page Components to Jembe extension instance;  
3. Add ``script`` HTML tag to load "jembe javascript" only in Page Components HTML.

The tasks above can be accomplished:

- using ``jembe startproject`` command to create new web application or;
- manually adding Jembe extension to the existing Flask application.

.. note::
    Add Jembe extension manually only if it's absolutely necessary, otherwise use ``jembe startproject`` to create new applications.




Use ``jembe startproject`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: 
    To use ``jembe startproject`` command, you must first install ``jembe`` package
    in your Python virtual environment as explained in the :ref:`installation` chapter.

**TODO** 

- write how to start project
- explain project structure



Add to an Existing Project
==========================

.. note::
    Adding Jembe Components in the regular Flask view is not currently supported. Entire HTML pages should be built with Jembe Components.


To integrate Jembe into an existing Flask project we must:

Registred and initialize Jembe as Flask extension;
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    """When Flask is statically loaded"""
    from jembe import Jembe

    app = Flask(__name__)
    jmb = Jembe(app)

.. code:: python

    """When Flask is dynamically loaded"""
    from jembe import Jembe

    jmb = Jembe()

    def create_app(config):
        # ...
        app = Flask(__name__)
        jmb.init_app(app)

Register Top Level @jmb.page Components to Jembe Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    """Using 'page' decorator"""
    from jembe import Component
    # from [place where you have defined jmb as jmb = Jembe(..)] import jmb

    @jmb.page("main")
    class PageComponent(Component):
        pass

.. code:: python

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

.. code:: html

    <!-- templates/main.html -->
    <html>
    <head>
    <!-- ... -->
    </head>
    <body>
    <!-- ... -->
        <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}" defer></script>
    </body>
    <html>
