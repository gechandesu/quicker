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


def make_list(
    column_names: List[str], rows: Union[tuple, Tuple[dict, ...]]
) -> List[dict]:
    """Convert output to list of dicts from tuples."""
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

    def __init__(self,
        provider: Provider = None,
        commit: bool = True,
        **kwargs
    ):
        if not provider:
            raise ValueError('Database provider is not set')
        self._provider = Provider(provider)
        self._commit = commit
        self._connection_args = kwargs

    def __enter__(self):
        logger.debug(f'Database provider={self._provider}')
        # -- MySQL / MariaDB --
        if self._provider == Provider.MYSQL:
            MySQLdb = _import('MySQLdb')
            DictCursor = _import('MySQLdb.cursors', 'DictCursor')
            try:
                if self._connection_args['cursorclass']:
                    cursorclass = DictCursor
            except KeyError:
                cursorclass = DictCursor
            self._connection = MySQLdb.connect(
                **self._connection_args,
                cursorclass=cursorclass,
            )
            logger.debug('Session started')
            self._cursor = self._connection.cursor()
            return Query(self)
        # -- PostgreSQL --
        if self._provider == Provider.POSTGRES:
            psycopg2 = _import('psycopg2')
            dbname = self._connection_args.pop('database')
            self._connection_args['dbname'] = dbname
            self._connection = psycopg2.connect(**self._connection_args)
            self._cursor = self._connection.cursor()
            return Query(self)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self._commit:
            self._connection.commit()
            logger.debug('Changes commited into database')
        self._cursor.close()
        self._connection.close()
        logger.debug('Connection closed')


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
        if self._fetchall is not None:
            self._colnames = []
            if self._cursor.description is not None:
                self._colnames = [
                    desc[0] for desc in self._cursor.description
                ]
            return make_list(self._colnames, self._fetchall)
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
