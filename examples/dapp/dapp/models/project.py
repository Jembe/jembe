from enum import unique
from dapp.db import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __str__(self) -> str:
        return self.name