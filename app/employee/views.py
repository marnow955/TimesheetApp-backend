from flask import Blueprint
from ..db.db_manager_abc import DbManagerABC
from ..db.mysql_db_manager import MySqlDbManager
from ..config import DbConfig


def construct_employee(db_manager: DbManagerABC = None) -> Blueprint:
    employee = Blueprint('employee', __name__, url_prefix='/employee')
    database = db_manager

    if database is None:
        database = MySqlDbManager(DbConfig)

    @employee.route('/timesheet/<username>/<week>', methods=['GET'])
    def get_timesheet(username, week):
        return username + " " + week

    return employee
