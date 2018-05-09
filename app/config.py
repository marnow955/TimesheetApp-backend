class Config(object):
    PROJECT = 'Content filtering server'
    SECRET_KEY = 'dev key'
    CORS_HEADERS = 'Content-Type'
    DEBUG = False


class DbConfig(object):
    HOST = "localhost"
    USER = "root"
    PASSWORD = ""
    DATABASE = "timesheet_db"


EXPIRATION_TIME = 3600
