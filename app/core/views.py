from flask import Blueprint, jsonify, json, request, abort
from flask_cors import cross_origin

from ..config import DbConfig
from ..db import DbManagerABC, MySqlDbManager
from ..token_auth import generate_auth_token, check_auth, remove_user


def construct_core(db_manager: DbManagerABC = None) -> Blueprint:
    core_blp = Blueprint('core', __name__)

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @core_blp.route('/')
    def index():
        return "TimesheetApp-backend"

    @core_blp.route('/login', methods=['POST'])
    @cross_origin()
    def login():
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['username', 'password']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        auth = check_auth(data_dict['username'], data_dict['password'])
        if not auth:
            abort(401)
        token = generate_auth_token(data_dict['username'])
        role = db_manager.select_from_table('users', ('role',),
                                            'username=\'' + data_dict['username'] + '\'')[0][0]
        return jsonify(username=data_dict['username'], role=role, token=token.decode('utf-8'))

    @core_blp.route('/logout', methods=['GET', 'POST'])
    @cross_origin()
    def logout():
        token = request.headers.get('Token')
        remove_user(token)
        return "OK"

    return core_blp
