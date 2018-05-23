import MySQLdb

from .db_manager_abc import DbManagerABC, DbResult


class MySqlDbManager(DbManagerABC):
    def __init__(self, config):
        self._config = config
        self._conn = None

    def connect(self):
        self._conn = MySQLdb.connect(host=self._config.HOST, user=self._config.USER,
                                     passwd=self._config.PASSWORD, db=self._config.DATABASE, charset='utf8')
        self._conn.autocommit(False)

    def disconnect(self):
        self._conn.close()

    def commit(self):
        try:
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print(e)

    def insert_values(self, table_name: str, columns: tuple = None,
                      values: tuple = None, join_transaction: bool = False) -> int:
        if values is None:
            return 0
        query = "INSERT INTO " + table_name
        if columns:
            query += " (" + columns[0]
            for column in columns[1:]:
                query += ", " + column
            query += ") "
        query += "VALUES (\'" + values[0]
        for value in values[1:]:
            query += "\', \'" + value
        query += "\');"
        self.execute_query(query, True)
        insert_id = self._conn.insert_id()
        self.commit()
        self.disconnect()
        return insert_id

    def select_from_table(self, table_name: str, columns: tuple = ('*',),
                          condition: str = None, join_transaction: bool = False) -> list:
        return super().select_from_table(table_name, columns, condition, join_transaction)

    def update_columns(self, table_name: str, names_and_values: dict,
                       condition: str = None, join_transaction: bool = False) -> int:
        return super().update_columns(table_name, names_and_values, condition, join_transaction)

    def delete_rows(self, table_name: str, condition: str = None, join_transaction: bool = False) -> int:
        return super().delete_rows(table_name, condition, join_transaction)

    def execute_query(self, query: str, join_transaction: bool = False) -> DbResult:
        print(query)
        result = None
        if join_transaction is not True or self._conn is None or self._conn.open is 0:
            self.connect()
        try:
            cur = self._conn.cursor()
            cur.execute(query)
            result = DbResult(cur.rowcount, cur.fetchall())
            print(result)
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
