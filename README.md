# Jembe Web Framework

Jembe is a Python Web Framework for developing modern web applications, build on top of Flask, and designed with the following goals:

- Web UI is created by combing and nesting configurable, reusable, and adaptable UI components;
- Building new UI components should be easy to do by extending Python class, with simple API, and writing associated Jinja2 template creates new UI Component;
- There should be no reason to think off, consider or implement the logic for:
    - Handling HTTP request-response cycle;
    - URL Routing;
    - Handling any "low level" web/HTTP API;
- Complex UI interactions should be achievable with minimal use of javascript by utilizing server-side HTML rendering and partial page updating, allowing all UI and business logic to be written in python and executed on the server;
- Once a set of "basic" UI components is created Developer should be focused primarily on "business" logic and write new UI/Frontend logic only for specific use cases;

Official web site https://jembe.io

## Install Jembe Framework

``` bash
$ pip install jembe
```

### Start a new project with a project template

Use premade application template to start a new project.

> Requires **Python 3.8** or above.

``` bash
# Create project directory
$ mkdir myproject
$ cd myproject

# Create python virtual enviroment and activate it
$ python -m venv .venv
$ . .venv/bin/activate 

# Install Jembe framework
$ pip install jembe

# Start a new project with the premade project template
$ jembe startproject

# Install developer dependencies in a virtual environment
$ pip install -e .[dev]

# Run application
$ flask run
```

### Add Jembe to an Existing Flask Project

> Adding Jembe Components in the regular flask view is not currently supported. Entire HTML pages should be build from Jembe Components. 
>
> One Component should be responsible for rendering HTML HEAD and BODY tags, and all other Components are rendered inside this Component to form a web application.

To integrate Jembe into an existing Flask project we must:
 
#### Registred and initialize Jembe as Flask extension;

```python
"""When statically load Flask"""
from jembe import Jembe

app = Flask(__name__)
jmb = Jembe(app)
```

```python
"""When dynamically load Flask"""
from jembe import Jembe

jmb = Jembe()

def create_app(config):
    # ...
    app = Flask(__name__)
    jmb.init_app(app)
```    

#### Register Top Level PageComponents to Jembe Instance

```python
"""Use 'page' decorator"""
from jembe import Component
# from [place where you have defined jmb as jmb = Jembe(..)] import jmb

@jmb.page("main")
class PageComponent(Component):
    pass
```
```python
"""Use add_page method"""
from jembe import Jembe

jmb = Jembe()

def create_app(config):
    from .pages import PageComponent
    # ...
    app = Flask(__name__)
    jmb.init_app(app)
    #..
    jmb.add_page("main", PageComponent)
```

#### Add necessary javascript to PageComponent HTML/Jinja2 template

Default template for PageComponent registred as 'main' is 'main.html' 

```html
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
```

## How to use Jembe Components

To test the following examples, add code to a new project created with `$ jembe startproject` command.

> Following examples assumes that the project is named **'myproject'**.

### Hello World

Hello World is a not very exciting minimal Jembe application.

##### myproject/pages/hello_world.py
``` python
from jembe import Component
from myproject.app import jmb

@jmb.page('hello')
class HellowWorld(Component):
    pass
```

##### myproject/templates/hello.html
``` jinja
<html>
<body>
    <h1>Hello World!</h1>
    <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
</body>
</html>
```

> Don't forget to add `from .hello_world import HelloWorld` in `myproject/pages/__init__.py` so that Jembe initializes 'hello' page.

> Visit `http://localhost:5000/hello` to see the Hello World page.

### Better Hello World

##### myproject/pages/hello_world.py
``` python
from jembe import Component
from myproject.app import jmb

@jmb.page('hello')
class HellowWorld(Component):
    def __init__(self, name: str = "World"):
        super().__init__()
```

##### myproject/templates/hello.html
``` jinja
<html>
<body>
    <h1>Hello {{name}}!</h1>
    <input jmb-on:keydown.debounce="name = $self.value" value="{{name}}">

    <script src="{{ url_for('jembe.static', filename='js/jembe.js') }}"></script>
    <script defer>
    {# Adds CSRF protection Jembe AJAX requests #}
    window.addEventListener('DOMContentLoaded', function(event){
        window.jembeClient.addXRequestHeaderGenerator(function () {
            return {'X-CSRFToken': window.jembeClient.getCookie("_csrf_token")};
        })
    })
    </script>
</body>
</html>
```

![Hello World](/doc/hello_world.gif)

> - Both `script` tags are required only on top most component, aka PageComponent;
> - Second `script` tag is required by projects created with `jembe startproject` command and it adds CSRF protection Jembe AJAX requests for page update;


### Counter

### Searchable list

## Jembe Component Essentials

### Component State Params

### Rendering

### Actions

### Events

## Reference

### Component

### Component.Config

### Component JS Client


## License


Jembe Web Framework 
Copyright (C) 2021 BlokKod <info@blokkod.me>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
