from sqlalchemy.orm import backref
from dapp.db import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project_id'), nullable=False)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))