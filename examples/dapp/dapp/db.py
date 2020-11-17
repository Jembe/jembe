from flask_sqlalchemy import SQLAlchemy

__all__ = ("db", "init_db")

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
