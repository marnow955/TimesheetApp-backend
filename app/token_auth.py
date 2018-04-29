import hashlib
from functools import wraps

from flask import Flask, request, abort, session
from flask_session import Session, FileSystemSessionInterface
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from app.db.db_manager_abc import DbManagerABC
from .config import Config, EXPIRATION_TIME


def configure_auth(app: Flask):
    Session(app)
    app.session_interface = FileSystemSessionInterface(
        app.config['SESSION_FILE_DIR'], app.config['SESSION_FILE_THRESHOLD'],
        app.config['SESSION_FILE_MODE'], app.config['SESSION_KEY_PREFIX'],
        app.config['SESSION_USE_SIGNER'], app.config['SESSION_PERMANENT']
    )


def check_auth(db_manager: DbManagerABC, username: str, password: str):
    db_result = db_manager.select_from_table('users', ('password',),
                                             'username=\'' + username + '\'', False)
    if len(db_result) != 1:
        return False
    user_password_hash = db_result[0][0]
    pass_hash = hashlib.sha512(password.encode('utf-8')).hexdigest()
    if pass_hash.lower() == user_password_hash.lower():
        return True
    return False


def generate_auth_token(username, expiration=EXPIRATION_TIME):
    s = Serializer(Config.SECRET_KEY, expires_in=expiration)
    session['username'] = username
    return s.dumps({'username': username})


def verify_auth_token(token):
    s = Serializer(Config.SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    if session.get('username', None) == data['username']:
        return True
    return False


def destroy_session():
    session.clear()


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Token')
        if not token or not verify_auth_token(token):
            abort(403)
        return f(*args, **kwargs)

    return decorated
