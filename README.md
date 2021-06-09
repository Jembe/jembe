# Jembe Web Framework

Jembe is a Python Web Framework for building modern web applications, running on top of Flask and designed with the following goals:

- Developer creates an App by combing custom, reusable, reactive, and responsive UI components;
- Developers is focused primarily on "business" logic and writes UI/Frontend logic only for very specific use cases;
- New UI Components are created by extending Python class, with simple API, and writing associated Jinja2 template; 
- Complex UI interactions can be created without or with minimal use of javascript code by utilizing server-side HTML rendering and partial updating;
- There should be no reason to think off, consider or implement the logic for:
    - Handling HTTP request-response cycle;
    - URL Routing;
    - Handling any "low level" web/HTTP API;

Official web site https://jembe.io

## Quickly start with a new project

Requires **Python 3.8** or above:

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

# Install developer dependencies in virtual environment
$ pip install -e .[dev]

# Run application
$ flask run
```

## Add Jembe to an Existing Flask Project

Jembe components can not currently be used inside regular flask route/view, instead of whole HTML page must be created from Jembe components. This usually means that one component will be responsible for rendering HTML HEAD and BODY tags. Let's call this component PageComponent and all other
Jembe components will be called and rendered inside this component to form a web application.

So to integrate Jembe Framework into the existing flask project we must:
 
### Registred and initialise Jembe as Flask extension;
```python
"""When flask is statically loaded"""
from jembe import Jembe

app = Flask(__name__)
jmb = Jembe(app)
```

```python
"""When flask is dynamically loaded"""
from jembe import Jembe

jmb = Jembe()

def create_app(config):
    # ...
    app = Flask(__name__)
    jmb.init_app(app)
```    

### Register Top Level PageComponents to Jembe Instance

```python
"""Using 'page' decorator"""
from jembe import Component
# from [place where you have defined jmb as jmb = Jembe(..)] import jmb

@jmb.page("main")
class PageComponent(Component):
    pass
```
```python
"""Using add_page method"""
from jembe import Component
# from [place where you have defined jmb as jmb = Jembe(..)] import jmb

class PageComponent(Component):
    pass
#...
jmb.add_page("main", PageComponent)
```

### Add necessary javascript to PageComponent HTML/Jinja2 template

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

### Hello world

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
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
