class Config(object):
    PROJECT = 'Content filtering server'
    SECRET_KEY = 'dev key'
    DEBUG = False


class DbConfig(object):
    HOST = "localhost"
    USER = "root"
    PASSWORD = ""
    DATABASE = "timesheet"
