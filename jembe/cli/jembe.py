import os
import click
from getpass import getuser
from click import echo, secho
from click.termui import prompt
from .utils import make_python_identifier


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
    default="standard",
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
@click.option(
    "--author",
    help="Author full name",
    default=lambda: getuser(),
)
@click.option("--author-email", help="Author email")
def startproject(template, name, description, author, author_email):
    """Starts new Jembe project in current directory"""
    name = make_python_identifier(name)
    ctx = dict(
        project=dict(
            template=template,
            name=name,
            description=description,
            author=author,
            author_email=author_email
        )
    )
    echo("startproject: {}".format(ctx))

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
