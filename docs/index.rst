Jembe Web Framework
===================

Jembe is a Python Web Framework for developing modern web applications,
build on top of Flask, and designed to achieve the following goals:

-  Web Frontend/UI is created by combing UI Components;
-  UI Component is responsible for rendering a part of a web page and
   handling all user interaction with that part of the page;
-  UI Component must be configurable, reusable, and easily adaptable;
-  New UI component is created by extending Python Component class, and
   writing associated Jinja2 template;
-  There should be no reason to think about, consider or implement the
   logic for:

   -  Handling HTTP request-response cycle;
   -  URL Routing;
   -  Handling any "low level" web/HTTP API;

-  After a user interacts with the UI Component, the HTML is updated using server-side rendering and partial page updating;
-  Server-side rendering must allow developers to keep the majority of the app logic in Python and write javascript code only 
   to implement unusual and complex UI interactions.
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
