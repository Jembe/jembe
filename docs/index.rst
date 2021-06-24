Jembe Web Framework
===================

Jembe is a Python Web Framework for developing modern web applications,
build on top of Flask, and designed with the following goals:

-  Web Frontend/UI is created by combing and nesting configurable,
   reusable, and adaptable UI components;
-  UI Component is responsible for rendering one part of a web page and
   handling all user interaction regarding that part of the page;
-  New UI components are created by extending Python Component class, and
   writing associated Jinja2 template;
-  There should be no reason to think about, consider or implement the
   logic for:

   -  Handling HTTP request-response cycle;
   -  URL Routing;
   -  Handling any "low level" web/HTTP API;

-  On user interaction Components should be redisplayed/refreshed using server-side HTML rendering and partial page update, allowing developers to minimize javascript code when implementing complex UI behaviors.
-  Majority UI logic and ALL "business logic" should be written in Python and executed on the server.
-  Once a set of "basic" UI components is created Developer should be
   able to stay focused primarily on "business" logic and write new
   UI/Frontend logic only for specific use cases;

Official web site https://jembe.io

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   installation
   component


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
