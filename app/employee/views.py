from flask import Blueprint, jsonify, abort
from flask_cors import cross_origin

from ..config import DbConfig
from ..db import DbManagerABC, MySqlDbManager
from ..token_auth import requires_auth


def construct_employee(db_manager: DbManagerABC = None) -> Blueprint:
    employee_blp = Blueprint('employee', __name__, url_prefix='/employee')

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @employee_blp.route('/fetch-employees', methods=['GET'])
    @cross_origin()
    @requires_auth
    def fetch_employees():
        employees_list = []
        try:
            users = db_manager.select_from_table('users', ('username',), 'role=\'employee\'')
            for user in users:
                user_dict = {'username': user[0]}
                employees_list.append(user_dict)

        except Exception as e:
            print(e)
            abort(500)
        return jsonify(employees=employees_list)

    return employee_blp
