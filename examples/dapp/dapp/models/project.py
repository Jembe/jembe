from enum import unique
from dapp.db import db


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    __table_args__ = {
        "info": dict(verbose_name="Project", verbose_name_plural="Projects")
    }

    def __str__(self) -> str:
        return self.name
