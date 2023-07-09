import importlib.util
from enum import Enum


class Provider(str, Enum):

    MYSQL = 'mysql'
    POSTGRES = 'postgres'
    SQLITE = 'sqlite'


class Connection:
    """
    Connection is context manager that allows to establish connection
    with database.
    """

    def __init__(self,
        provider: Provider = None,
        commit: bool = True,
        **kwargs
    ):
        if not provider:
            raise ValueError('Database provider is not set')
        self._provider = provider
        self._commit = commit
        self._connection_args = kwargs

    def __enter__(self):
        if self._provider == Provider.MYSQL:
            MySQLdb = self._import('MySQLdb')
            self._connection = MySQLdb.connect(**self._connection_args)
            self._cursor = self._connection.cursor()
            return Query(self)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self._provider == Provider.MYSQL:
            if self._commit:
                self._connection.commit()
            self._cursor.close()
            self._connection.close()

    def _import(self, lib: str):
        spec = importlib.util.find_spec(lib)
        if spec is None:
            raise ImportError(f"Module '{lib}' not found.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class Query:
    def __init__(self, connect):
        self._provider = connect._provider
        self._connection = connect._connection
        self.cursor = self._connection.cursor()

    def __call__(self, *args, **kwargs):
        return self.exec(*args, **kwargs)

    def query(self, *args, **kwargs):
        return self.exec(*args, **kwargs)

    def exec(self, *args, **kwargs):
        """Execute SQL query and return output if available."""
        self.cursor.execute(*args, **kwargs)
        self._fetchall = self.cursor.fetchall()
        if self._fetchall is not None:
            if self.cursor.description is not None:
                self._field_names = [i[0] for i in self.cursor.description]
            return self._conv(self._field_names, self._fetchall)

    def commit(self):
        """Commit changes into database."""
        if self._provider == Provider.MYSQL:
            self._connection.commit()

    def _conv(self, field_names, rows) -> list[dict]:
        data = []
        for row in rows:
            item  = {}
            for i in range(len(row)):
                item[field_names[i]] = row[i]
            data.append(item)
        return data
