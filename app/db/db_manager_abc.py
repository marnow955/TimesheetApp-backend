from abc import ABC, abstractmethod


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
    def select_from_table(self, table_name: str, columns: tuple = ('*',),
                          condition: str = None, join_transaction: bool = False) -> list:
        query = "SELECT " + columns[0]
        for column in columns[1:]:
            query += ", " + column
        query += " FROM " + table_name
        if condition:
            query += " WHERE " + condition
        return self.execute_query(query, join_transaction)

    @abstractmethod
    def update_columns(self, table_name: str, names_and_values: dict,
                       condition: str = None, join_transaction: bool = False):
        query = "UPDATE " + table_name + " SET "
        name, value = names_and_values.popitem()
        query += name + "=" + value
        for name, value in names_and_values.items():
            query += ", " + name + "=" + value
        if condition:
            query += " WHERE " + condition
        self.execute_query(query, join_transaction)

    @abstractmethod
    def execute_query(self, query: str, join_transaction: bool = False) -> list:
        pass
