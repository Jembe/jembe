Using setuptools
----------------

```
$ mkdir project
$ cd project
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install --upgrade pip
$ pip install jembe
$ jembe startproject
    Package project with: [setuptools, poetry]   
    Project template: [basic, standard, jui_standard]
    Project name:
    Project Description:
    ...
$ pip install -e .
$ flask run
```

Production deployment:

$ mkdir project
$ cd project
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install project
$ project create-example config.py | gunicorn.conf.py | project.service | project.socket| nginx.site
$ vi config.py
$ export FLASK_ENV=project
$ flask run

Dich poetry use setuptools exclusivly?


Using poetry
------------

```
$ mkdir project
$ cd project
$ poetry project
$ poetry add jembe
$ jembe startproject
    runs poetry add package in order to modify pyproject.toml that is already created
    not very flexible or use sed to create and replace pyproject.toml ... NO NO
    ...
$ poetry update
$ poetry install
$ flask run
```