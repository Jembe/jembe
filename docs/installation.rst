Installation and Configuration
------------------------------

Jembe is installed into python environment with pip command:

.. code:: bash

    $ pip install jembe

    When developing or deploying python projects it is recomended to use
    diferent python virtual enviroment for every project.

    .. code:: bash

        # create new virtual enviroment
        $ python -m venv .venv
        # activate virtual enviroment
        $ . .venv/bin/activate
        # install jembe into active virtual enviroment
        (.venv) $ pip install jembe

To create Web Application with Jembe you must: - create Flask
Application and initialize Jembe as a regular Flask extension; -
registrer Root/Page Components to Jembe extension instance; - add
``script`` tag to Root/Page Components HTML template.

A Minimal Jembe Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

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
      Jinja2 template. We could also use regular string if we wanted.
   3. Because we registred this component as page it's HTML contains
      ``script`` tag to include JavaScript.

5. Lastly we use **route()** decorator to tell Flask what URL should
   triger our **index** function that will redirect browser to our Jembe
   Page Componnet "main".

To run this application use:

.. code:: bash

    $ export FLASK_APP=minimal
    $ flask run
     * Running on http://127.0.0.1:5000/

Use Flask Application Factory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When we create application with Jembe Components we can anticipiate that
lots of components will be created and used.

In order to improve development expirence we can use Flask Application
Factory pattern to organise our code.

Use Flask Application Factory With Pages "Autodiscovery"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use Jembe Application Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding Jembe to an Existing Flask Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Adding Jembe Components in the regular Flask view is not currently
    supported. Entire HTML pages should be build from Jembe Components.

    One Component should be responsible for rendering HTML HEAD and BODY
    tags, and all other Components are rendered inside this Component to
    form a web application.

To integrate Jembe into an existing Flask project we must:

Registred and initialize Jembe as Flask extension;
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
