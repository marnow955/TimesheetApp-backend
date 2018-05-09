import hashlib
from functools import wraps

from flask import request, abort
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from app.db import DbManagerABC
from .config import Config, EXPIRATION_TIME

db_manager = None


def configure_auth(db: DbManagerABC):
    global db_manager
    db_manager = db


def check_auth(username: str, password: str):
    db_result = db_manager.select_from_table('users', ('password',), 'username=\'' + username + '\'')
    if len(db_result) != 1:
        return False
    user_password_hash = db_result[0][0]
    pass_hash = hashlib.sha512(password.encode('utf-8')).hexdigest()
    if pass_hash.lower() == user_password_hash.lower():
        return True
    return False


def generate_auth_token(username, expiration=EXPIRATION_TIME):
    s = Serializer(Config.SECRET_KEY, expires_in=expiration)
    token = s.dumps({'username': username})
    db_manager.update_columns('users', {'token': token.decode('utf-8')}, 'username=\'' + username + '\'')
    return token


def verify_auth_token(token):
    s = Serializer(Config.SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    username = db_manager.select_from_table('users', ('username',), 'token=\'' + token + '\'')
    if len(username) != 1:
        return False
    if username[0][0] == data['username']:
        return True
    return False


def remove_user(token):
    username = db_manager.select_from_table('users', ('username',), 'token=\'' + token + '\'')
    if len(username) == 1:
        db_manager.update_columns('users', {'token': ''}, 'username=\'' + username[0][0] + '\'')


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Token')
        if not token or not verify_auth_token(token):
            abort(403)
        return f(*args, **kwargs)

    return decorated
