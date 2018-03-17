from sqlite3 import connect
from .db_manager_abc import DbManagerABC


class SqliteDbManager(DbManagerABC):
    def __init__(self, config):
        self._config = config
        self._conn = None
        self._is_open = False

    def connect(self):
        self._conn = connect(self._config.DATABASE_PATH)
        self._is_open = True

    def disconnect(self):
        self._conn.close()
        self._is_open = False

    def commit(self):
        try:
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print(e)

    def execute_query(self, query: str, join_transaction: bool = False) -> list:
        result = None
        if join_transaction is not True or self._conn is None or self._is_open is False:
            self.connect()
        try:
            cur = self._conn.cursor()
            cur.execute(query)
            result = cur.fetchall()
            cur.close()
            if join_transaction is not True:
                self.commit()
        except Exception as e:
            self._conn.rollback()
            self.disconnect()
            print(e)
        if join_transaction is not True:
            self.disconnect()
        return result
