from os import path, getcwd


class Config(object):
    PROJECT = 'Content filtering server'
    SECRET_KEY = 'dev key'
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = path.join(getcwd(), 'flask_session')
    SESSION_FILE_THRESHOLD = 500
    SESSION_FILE_MODE = 384
    SESSION_KEY_PREFIX = 'session:'
    SESSION_USE_SIGNER = False
    SESSION_PERMANENT = True
    DEBUG = False


class DbConfig(object):
    HOST = "localhost"
    USER = "root"
    PASSWORD = ""
    DATABASE = "timesheet_db"


EXPIRATION_TIME = 3600
