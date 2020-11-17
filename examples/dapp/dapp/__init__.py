import os
from flask import Flask
from . import jmb, db, commands

def create_app(config=None):
    from . import models, views, pages

    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_mapping({SECRET_KEY="dev",})
    if config is not None:
        if isinstance(config, dict):
            app.config.from_mapping(config)
        elif config.endswith(".py"):
            app.config.from_pyfile(config)
    else:
        app.config.from_pyfile("config.py", silent=True)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    jmb.init_jembe(app)
    db.init_db(app)
    views.init_views(app)
    commands.init_commands(app)

    return app
