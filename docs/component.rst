
Jembe Component Essentials
--------------------------

Jembe Component is the primary building block for creating Web
Application Frontend. Components are combined/nested to create a Web
Application User Interface.

Components are combined in a hierarchy. At least one component will be
Root/Page Component.

.. figure:: doc/components.png
   :alt: Components diagram

   Components diagram
Web application can have multiple Root/Page Components if needed.

Jembe Component is made of two main parts: 

- **Component.Config class** responsible for: 
    - configuring the behavior of te Component class instances; - it's initialized: - only once for every registred
component, when an application is started; - **Component class** -
responsible for: - rendering part of the HTML page; - handling user
interaction with that part of the page; - initalized: - on every HTTP
request (user interaction) with application when that specific component
is displayed.

The following example creates a simplified web application with one
Root/Page component and three subcomponents.

myproject/pages/main.py
'''''''''''''''''''''''

.. code:: python

    from jembe import Component
    from myproject.app import jmb

    class TopMenuComponent(Component):
        pass

    class SidebarComponent(Component):
        pass

    class FormComponent(Component):
        pass

    class PageComponent(Component):
        class Config(Component.Config):
            def __init__(
                self,
                template=None, 
                components=None, 
                inject_into_components=None,
                redisplay=(), 
                changes_url=True, 
                url_query_params=None
            ):
                # Adds three subcomponent to PageComponent named
                # top, side and form
                if components is None:
                    components = {}
                components["top"] = TopMenuComponent
                components["side"] = SidebarComponent
                components["form"] = FormComponent
                
                super().__init__(
                    template=template, 
                    components=components, 
                    inject_into_components=inject_into_components, 
                    redisplay=redisplay, 
                    changes_url=changes_url, 
                    url_query_params=url_query_params
                )

    # Registers PageComponent as Root Component of Web application
    jmb.add_page("demo", PageComponent)

    # Since PageComponent is registred as "demo" it's default template is:
    # - demo.html

    # Subcomponents "top", "side" and "form" will use:
    # - demo/top.html
    # - demo/side.html
    # - demo/form.html
    # as their default templates respectivly.

myproject/templates/demo.html
'''''''''''''''''''''''''''''

.. code:: html

    <html>
        <head></head>
        <body>
            <div>{{component("top")}}</div>
            <div style="display:flex; gap:16px;">
                <div>{{component("side")}}</div>
                <div>{{component("form")}}</div>
            </div>
        </body>
    <html>

myproject/templates/demo/top.html
'''''''''''''''''''''''''''''''''

.. code:: html

    <div>Top Menu</div>

myproject/templates/demo/side.html
''''''''''''''''''''''''''''''''''

.. code:: html

    <div>Sidebar</div>

myproject/templates/demo/form.html
''''''''''''''''''''''''''''''''''

.. code:: html

    <div>Form</div>

.. figure:: doc/demo_app.png
   :alt: Demo app

   Demo app
Configuring PageComponent by extending the Component class, like in the
example above, is the most powerful and flexible way to configure a
Component's behavior, and it's usually used when creating new components
to add additional configuration parameters.

To combine existing components it's easier and less verbose to use
``page`` decorator:

.. code:: python

    from jembe import Component
    from myproject.app import jmb

    class TopMenuComponent(Component):
        pass

    class SidebarComponent(Component):
        pass

    class FormComponent(Component):
        pass

    @jmb.page("main",
        Component.Config(
            components=dict(
                top=TopMenuComponent,
                side=SidebarComponent,
                form=FormComponent
            )
        ))
    class PageComponent(Component):
        pass

    Component instance can access its Config class using ``_config``
    attribute.

Registring Components
~~~~~~~~~~~~~~~~~~~~~

Rendering
~~~~~~~~~

Default

Component State Params
~~~~~~~~~~~~~~~~~~~~~~

Actions
~~~~~~~

Events
~~~~~~