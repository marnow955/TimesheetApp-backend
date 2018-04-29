from flask import Blueprint, jsonify, abort

from ..config import DbConfig
from ..db.db_manager_abc import DbManagerABC
from ..db.mysql_db_manager import MySqlDbManager
from ..token_auth import generate_auth_token, check_auth, destroy_session


def construct_core(db_manager: DbManagerABC = None) -> Blueprint:
    core = Blueprint('core', __name__)

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @core.route('/')
    def index():
        return "TimesheetApp-backend"

    @core.route('/login/<username>/<password>', methods=['GET'])
    def login(username, password):
        auth = check_auth(db_manager, username, password)
        if not auth:
            abort(401)
        token = generate_auth_token(username)
        role = db_manager.select_from_table('users', ('role',),
                                            'username=\'' + username + '\'', False)[0][0]
        return jsonify(username=username, role=role, token=token.decode('utf-8'))

    @core.route('/logout', methods=['GET'])
    def logout():
        destroy_session()
        return "OK"

    return core
