import collections
from abc import ABC, abstractmethod

DbResult = collections.namedtuple('DbResult', ['rowcount', 'query_results'])


class DbManagerABC(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def insert_values(self, table_name: str, columns: tuple = None,
                      values: tuple = None, join_transaction: bool = False) -> int:
        """
        This function insert values to table and return id of inserted row.
        When id is not autoincrement or inserting failed then return 0
        """
        pass

    @abstractmethod
    def select_from_table(self, table_name: str, columns: tuple = ('*',),
                          condition: str = None, join_transaction: bool = False) -> list:
        """
        This function return selected rows
        """
        query = "SELECT " + columns[0]
        for column in columns[1:]:
            query += ", " + column
        query += " FROM " + table_name
        if condition:
            query += " WHERE " + condition
        return self.execute_query(query, join_transaction).query_results

    @abstractmethod
    def update_columns(self, table_name: str, names_and_values: dict,
                       condition: str = None, join_transaction: bool = False) -> int:
        """
        This function update values in columns and return number of updated rows
        """
        query = "UPDATE " + table_name + " SET "
        name, value = names_and_values.popitem()
        query += name + "=\'" + value + "\'"
        for name, value in names_and_values.items():
            query += ", " + name + "=\'" + value + "\'"
        if condition:
            query += " WHERE " + condition
        return self.execute_query(query, join_transaction).rowcount

    @abstractmethod
    def delete_rows(self, table_name: str, condition: str = None, join_transaction: bool = False) -> int:
        """
        This function return number of deleted rows
        """
        query = "DELETE FROM " + table_name
        if condition:
            query += " WHERE " + condition
        return self.execute_query(query, join_transaction).rowcount

    @abstractmethod
    def execute_query(self, query: str, join_transaction: bool = False) -> DbResult:
        pass
