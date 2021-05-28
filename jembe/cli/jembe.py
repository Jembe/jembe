import os
import click
import importlib.metadata
from getpass import getuser
from click import echo, secho
from .utils import extract_project_template, make_python_identifier


@click.group()
def jembe():
    pass


@jembe.command()
@click.option(
    "--template",
    help="Project temlate",
    prompt="Choose Project Template",
    type=click.Choice(["basic", "standard"], case_sensitive=False),
    required=True,
    default="basic",
)
@click.option(
    "--name",
    help="Name",
    prompt="Project Name",
    required=True,
    default=lambda: make_python_identifier(os.path.basename(os.getcwd())),
)
@click.option(
    "--description", help="Description", prompt=True, required=False, default=""
)
def startproject(template, name, description):
    """Starts new Jembe project in current directory"""
    name = make_python_identifier(name)
    ctx = dict(
        project_name=name,
        project_description=description,
        project_author=getuser(),
        jembe_version=importlib.metadata.version("jembe"),
        secret_key=str(os.urandom(24).__repr__()),
    )
    extract_project_template(template, ctx=ctx)

    echo()
    echo("New project is suceessfully created in current directory!", color=True)
    echo()
    echo("To install required development dependencies execute:")
    secho("\t$ pip install -e .[dev]", bold=True)
    echo()
    echo("To start development web server execute:")
    secho("\t$ flask run", bold=True)
    echo()
    echo("To package project for deployment run:")
    secho("\t$ python -m build", bold=True)
    echo()
