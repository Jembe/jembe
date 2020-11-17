from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def init_commands(app: "Flask"):
    @app.cli.command("create-db")
    def create_db():
        from .db import db
        from .models import Project, Task
        # Create database
        db.create_all()

        # Populate database with test data
        p1 = Project(name="Learn Jembe")
        p2 = Project(name="Develop awesome app")
        t1 = Task(name="Create component", project=p1)
        t2 = Task(name="Use components to build application", project=p1)
        t3 = Task(name="Abstract common logic in configurable component", project=p1)
        t4 = Task(name="Rebuild application with plugable components", project=p1)
        t5 = Task(name="Decide what you want to build", project=p2)
        t5 = Task(name="Start coding", project=p2)
        db.session.add_all(
            [p1, p2, t1, t2, t3]
        )
        db.session.commit()

