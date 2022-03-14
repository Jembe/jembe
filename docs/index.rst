Welcome to Jembe Framework
==========================

`Jembe <https://jembe.io>`_  is Web Framework written in Python on top of Flask, for rapid development of business oriented datacentric applications.

.. warning:: This documentation is under writing and it is far from completed. All sugestions are Welcome.

Design Principes of Jembe
-------------------------

- Application is build by laying **Components** on top of ech other; 
- **Component** is:
   - Python class with, 
   - associated Jinja2 template, 
- **Component** is:
   - responsible for displaying part of the web page and 
   - handling all user interaction with that part of the page;
- Components communicate with each other by dispatching and listening for events;
- Components are configurable;


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
