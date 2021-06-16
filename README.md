# Jembe Web Framework

Jembe is a Python Web Framework for developing modern web applications, build on top of Flask, and designed with the following goals:

- Web Frontend/UI is created by combing and nesting configurable, reusable, and adaptable UI components;
- UI Component is responsible for rendering one part of a web page and handling all user interaction regarding that part of the page;
- New UI components are created by extending Component class, and writing associated Jinja2 template;
- There should be no reason to think about, consider or implement the logic for:
    - Handling HTTP request-response cycle;
    - URL Routing;
    - Handling any "low level" web/HTTP API;
- Complex UI behaviors and user interactions are handled with minimal javascript code, using server-side HTML rendering and partial page updating, allowing the majority of UI and all business logic to be written in Python and executed on the server;
- Once a set of "basic" UI components is created Developer should be able to stay focused primarily on "business" logic and write new UI/Frontend logic only for specific use cases;

Official web site https://jembe.io

## Install Jembe Framework

``` bash
$ pip install jembe
```

### Starting a new project with a project template

> Requires **Python 3.8** or above.

``` bash
# Create project directory
$ mkdir myproject
$ cd myproject

# Create Python virtual enviroment and activate it
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

### Adding Jembe to an Existing Flask Project

> Adding Jembe Components in the regular Flask view is not currently supported. Entire HTML pages should be build from Jembe Components. 
>
> One Component should be responsible for rendering HTML HEAD and BODY tags, and all other Components are rendered inside this Component to form a web application.

To integrate Jembe into an existing Flask project we must:
 
#### Registred and initialize Jembe as Flask extension;

```python
"""When Flask is statically loaded"""
from jembe import Jembe

app = Flask(__name__)
jmb = Jembe(app)
```

```python
"""When Flask is dynamically loaded"""
from jembe import Jembe

jmb = Jembe()

def create_app(config):
    # ...
    app = Flask(__name__)
    jmb.init_app(app)
```    

#### Register Top Level PageComponents to Jembe Instance

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

## Code Examples

To run examples, add code into a new project created with `$ jembe startproject` command.

> Following examples assumes that the Jembe project is named **'myproject'**.

### Hello World

Example on creating simple static Jembe Component.

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

> Visit `http://localhost:5000/hello`.

### Making Hello World Dynamic

Example on:
- using Component **state** variable to represent the current state of Component;
- updating Component **state** from user input.

Notice that the input field doesn't lose focus when the page is updated.

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

> - Both `script` tags are required only on top most component, aka `@jmb.page(..)` Component;
> - Second `script` tag is required by `jembe startproject` template to add CSRF protection;


### Counter

Example on:
- executing Component **actions** by a user 
- building page by nesting multiple components. 


##### myproject/pages/counter.py
``` python
from jembe import Component, action, config
from myproject.app import jmb


class Counter(Component):
    def __init__(self, count:int = 0):
        super().__init__()

    @action
    def increase(self):
        self.state.count += 1

    @action
    def decrease(self):
        self.state.count -= 1


@jmb.page(
    'counter',
    Component.Config(
        components={
            "counter": Counter
        }
    )
)
class CounterPage(Component):
    pass
```

##### myproject/templates/counter/counter.html
``` jinja
<h2>Counter</h2>
<div>
    Value: {{count}}
    <button jmb-on:click="decrease()" type="button">-</button>
    <button jmb-on:click="increase()" type="button">+</button>
</div>
```

##### myproject/templates/counter.html
``` jinja
<html>
<body>
    {{component('counter')}}

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

![Counter Demo](/doc/counter.gif)

> Don't forget to add `from .counter import CounterPage` in `myproject/pages/__init__.py` so that Jembe initializes 'counter' page.

### Multiple Counters

Example on:
- using events and listeners to communicate between components.

##### myproject/pages/multi_counter.py
``` python
from jembe import Component, action, config, listener
from myproject.app import jmb


class Counter(Component):
    def __init__(self, count:int = 0):
        super().__init__()

    @action
    def increase(self):
        self.state.count += 1
        self.emit("updateSum", value=1)

    @action
    def decrease(self):
        self.state.count -= 1
        self.emit("updateSum", value=-1)

class CounterSum(Component):
    def __init__(self, sum:int = 0):
        super().__init__()

    @listener(event="updateSum")
    def on_update_sum(self, event:"Event"):
        self.state.sum += event.params["value"]


@jmb.page(
    'multicount',
    Component.Config(
        components={
            "counter": (Counter, Counter.Config(changes_url=False)),
            "sum": (CounterSum, CounterSum.Config(changes_url=False)),
        }
    )
)
class MultiCountPage(Component):
    pass
```

##### myproject/templates/multicount/counter.html
``` jinja
<div>
    Counter {{key}}: {{count}}
    <button jmb-on:click="decrease()" type="button">-</button>
    <button jmb-on:click="increase()" type="button">+</button>
</div>
```

##### myproject/templates/multicount/sum.html
``` jinja
<div>
    <strong>Total: {{sum}}</strong>
</div>
```

##### myproject/templates/multicount.html
``` jinja
<html>
<body>
    {{component('counter').key('a')}}
    {{component('counter').key('b')}}
    {{component('counter').key('c')}}
    {{component('sum')}}

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

![Multi Counter Demo](/doc/multicounter.gif)

> Don't forget to add `from .multi_counter import MultiCounterPage` in `myproject/pages/__init__.py` so that Jembe initializes 'multicount' page.


## Jembe Component Essentials

TODO How Component works (concept)

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
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
