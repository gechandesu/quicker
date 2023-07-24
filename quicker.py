#
#    .88888.            oo          dP
#   d8'   `8b                       88
#   88     88  dP    dP dP .d8888b. 88  .dP  .d8888b. 88d888b.
#   88  db 88  88    88 88 88'  `"" 88888"   88ooood8 88'  `88
#   Y8.  Y88P  88.  .88 88 88.  ... 88  `8b. 88.  ... 88
#    `8888PY8b `88888P' dP `88888P' dP   `YP `88888P' dP
#
#   Quicker -- pythonic tool for querying databases.

__all__ = ['Connection', 'mklist', 'Provider']

import logging
import importlib.util
from enum import Enum
from typing import Optional, List, Union, Tuple


logger = logging.getLogger(__name__)


def _import(module_name: str, symbol: Optional[str] = None):
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise ImportError(f"Module '{module_name}' not found.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if symbol:
        try:
            return getattr(module, symbol)
        except AttributeError:
            raise ImportError()
    return module


def mklist(column_names: List[str], rows: Union[tuple, Tuple[dict, ...]]) -> List[dict]:
    """
    Convert output to list of dicts from tuples. `rows` can be
    default tuple or tuple of dicts if MySQL provider is used with
    MySQLdb.cursors.DictCursor cursor class.
    """
    data = []
    for row in rows:
        if isinstance(row, dict):
            data.append(row)
        else:
            item  = {}
            for i in range(len(row)):
                item[column_names[i]] = row[i]
            data.append(item)
    return data


class Provider(str, Enum):
    MYSQL = 'mysql'
    POSTGRES = 'postgres'
    SQLITE = 'sqlite'


class Connection:
    """
    Connection is context manager that allows to establish connection
    with database and make queries. Example::

    >>> from quicker import Connection
    >>> with Connection(provider='mysql', read_default_file='~/.my.cnf') as q:
    ...     server = q('SELECT * FROM `servers` WHERE `id` = %s', (1735781,))
    >>>
    """

    def __init__(self, provider: Provider, commit: bool = True, **kwargs):
        self._provider = Provider(provider)
        self._commit = commit
        self._connection_args = kwargs
        logger.debug(f'Database provider={self._provider}')

        if self._provider == Provider.MYSQL:
            MySQLdb = _import('MySQLdb')
            DictCursor = _import('MySQLdb.cursors', 'DictCursor')
            try:
                cursorclass = self._connection_args.pop('cursorclass')
            except KeyError:
                cursorclass = DictCursor
            self._connection = MySQLdb.connect(
                **self._connection_args,
                cursorclass=cursorclass,
            )
            logger.debug('Session started')
            self._cursor = self._connection.cursor()
            self._queryobj = Query(self)

        if self._provider == Provider.POSTGRES:
            psycopg2 = _import('psycopg2')
            dbname = self._connection_args.pop('database')
            self._connection_args['dbname'] = dbname
            self._connection = psycopg2.connect(**self._connection_args)
            self._cursor = self._connection.cursor()
            self._queryobj = Query(self)

        if self._provider == Provider.SQLITE:
            sqlite3 = _import('sqlite3')  # Python may built without SQLite
            self._connection = sqlite3.connect(**self._connection_args)
            self._cursor = self._connection.cursor()
            self._queryobj = Query(self)

    def __enter__(self):
        return self._queryobj

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.close()

    def close(self):
        if self._commit:
            logger.debug('Commiting changes into database')
            self._connection.commit()
        logger.debug('Closing cursor and connection')
        self._cursor.close()
        self._connection.close()


class Query:
    def __init__(self, connect):
        self._provider = connect._provider
        self._connection = connect._connection
        self._cursor = connect._cursor

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def query(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def execute(self, *args, **kwargs) -> Union[List[dict], None]:
        """Execute SQL query and return list of dicts or None."""
        if self._provider == Provider.MYSQL:
            self._cursor.execute(*args, **kwargs)
            logger.debug(f'MySQLdb ran: {self._cursor._executed}')
            self._fetchall = self._cursor.fetchall()
        if self._provider == Provider.POSTGRES:
            pgProgrammingError = _import('psycopg2', 'ProgrammingError')
            self._cursor.execute(*args, **kwargs)
            logger.debug(f'psycopg2 ran: {self._cursor.query}')
            try:
                self._fetchall = self._cursor.fetchall()
            except pgProgrammingError as e:
                self._fetchall = None
        if self._provider == Provider.SQLITE:
            self._cursor.execute(*args, **kwargs)
            logger.debug(f'sqlite3 ran: {args}')
            self._fetchall = self._cursor.fetchall()
        if self._fetchall is not None:
            self._colnames = []
            if self._cursor.description is not None:
                self._colnames = [
                    desc[0] for desc in self._cursor.description
                ]
            return mklist(self._colnames, self._fetchall)
        return None

    def commit(self) -> None:
        """Commit changes into database."""
        self._connection.commit()
        logger.debug('Changes commited into database')

    @property
    def connection(self):
        return self._connection

    @property
    def cursor(self):
        return self._cursor
