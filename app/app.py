from flask import Flask

from .config import Config, DbConfig
from .core import construct_core
from .db.db_manager_abc import DbManagerABC
from .db.mysql_db_manager import MySqlDbManager
from .employee import construct_employee
from .task import construct_task
from .timesheet import construct_timesheet
from .token_auth import configure_auth


def create_app(app_config=None, app_name: str = None,
               blueprints: tuple = None, db_manager: DbManagerABC = None) -> Flask:
    if app_name is None:
        app_name = Config.PROJECT
    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)
    if blueprints is None:
        blueprints = (
            construct_core(db_manager),
            construct_employee(db_manager),
            construct_timesheet(db_manager),
            construct_task(db_manager)
        )
    app = Flask(app_name)
    configure_app(app, app_config)
    register_blueprints(app, blueprints)
    configure_auth(app)
    return app


def configure_app(app: Flask, config=None):
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(Config)


def register_blueprints(app: Flask, blueprints: tuple):
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
