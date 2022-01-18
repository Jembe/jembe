Welcome to Jembe Framework
==========================

`Jembe <https://jembe.io>`_  is a Python web Framework build on top of Flask, to fullfill following goals:

-  Frontend is build from configurable, reusable and easily adaptable UI Components;
-  After developing a "fundamental" set of UI components developer:

   -  can stay focused on "business" logic on all his/her future project;
   -  and write new UI Components only for specific use cases;

-  UI Component is created by extending Python Component class, and
   writing associated Jinja2 template;
-  UI Component is responsible for rendering a part of a web page and
   handling all user interaction with that part of the page;
-  After a user interacts with the UI Component, the HTML of that Component is updated using 
   server-side rendering and partial HTML updating;
-  UI Component allows developers to develop frontend logic in Python and HTML
   and write javascript code only to implement unusual and complex User interactions;
-  There should be no reason to think about or implement the logic for:

   -  Handling HTTP request-response cycle;
   -  URL Routing;
   -  Handling any "low level" web/HTTP API;



User Guide
----------

.. toctree::
   :maxdepth: 2

   quickstart
   installation
   component
   
API Reference
-------------

.. toctree::
   :maxdepth: 2

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
