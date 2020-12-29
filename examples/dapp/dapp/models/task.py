from sqlalchemy.orm import backref
from dapp.db import db


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    project = db.relationship("Project", backref=db.backref("tasks", lazy=True, cascade="all,delete-orphan"))
    __table_args__ = {"info": dict(verbose_name="Task", verbose_name_plural="Tasks")}

    def __str__(self) -> str:
        return self.name
