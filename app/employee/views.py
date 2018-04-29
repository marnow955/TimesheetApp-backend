from flask import Blueprint, jsonify
from ..db.db_manager_abc import DbManagerABC
from ..db.mysql_db_manager import MySqlDbManager
from ..config import DbConfig


def construct_employee(db_manager: DbManagerABC = None) -> Blueprint:
    employee = Blueprint('employee', __name__, url_prefix='/employee')

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @employee.route('/fetch-employees', methods=['GET'])
    def fetch_employees():
        employees_list = []
        try:
            users = db_manager.select_from_table('users', ('username', ),
                                                 'role=\'employee\'', False)
            for user in users:
                user_dict = {'username': user[0]}
                employees_list.append(user_dict)

        except Exception as e:
            print(e)
        return jsonify(employees=employees_list)

    return employee
