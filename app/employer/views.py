from flask import Blueprint
from ..db.db_manager_abc import DbManagerABC
from ..db.mysql_db_manager import MySqlDbManager
from ..config import DbConfig


def construct_employer(db_manager: DbManagerABC = None) -> Blueprint:
    employer = Blueprint('employer', __name__, url_prefix='/employer')
    database = db_manager

    if database is None:
        database = MySqlDbManager(DbConfig)

    @employer.route('/timesheet-management/<username>/<week>', methods=['GET'])
    def get_timesheets(username, week):
        return username + " " + week

    @employer.route('/task-management', methods=['GET'])
    def get_tasks():
        return "List of tasks"

    return employer
