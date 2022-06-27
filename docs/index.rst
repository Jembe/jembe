Welcome to Jembe Framework
==========================

`Jembe <https://jembe.io>`_  is Web Framework for rapid development of business applications. Jembe is written in Python on top of Flask.

.. warning:: This documentation is far from completed. All sugestions are Welcome.

Design Principes of Jembe
-------------------------

- Arange **Components** like Lego bricks to build an application;
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
