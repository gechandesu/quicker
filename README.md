```
   ____        _      __
  / __ \__  __(_)____/ /_____  _____
 / / / / / / / / ___/ //_/ _ \/ ___/
/ /_/ / /_/ / / /__/ ,< /  __/ /
\___\_\__,_/_/\___/_/|_|\___/_/
```

**Quicker** is a pythonic tool for querying databases.

Quicker wraps Python bindings on DBMS libraries:

- `mysqlclient` for MySQL.
- `psycopg2` for PostgreSQL.
- `sqlite` from Python standard library for SQLite (not implemented yet).

Connection parameters will passed to "backend" module as is.

# Installation

```
pip install git+https://git.nxhs.cloud/ge/quicker
```

# Usage

`Connection` is context manages and must be used with `with` keyword. `Connection` returns `Query` callable object. `Query` can be called in this ways:

```python
with Connection(**config) as db:
    db.execute("sql query here...")
    db.query("sql query here...")  # query is alias for exec()

# Query is callable and you can also do this:
with Connection(**config) as query:
    query("sql query here...")
```

`Query` cannot be called itself, you must use `Connection` to correctly initialise `Query` object. Available methods and properties:

- `query()`, `execute()`. Execute SQL. There is You can use here this syntax: `query('SELECT * FROM users WHERE id = %s', (15,))`.
- `commit()`. Write changes into database.
- `cursor`. Access cursor object directly.
- `connection`. Access connection object directly.

Full example:

```python
import json

from quicker import Connection


config = {
    'provider': 'mysql',
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'myuser',
    'database': 'mydb',
    'password': 'example',
}

with Connection(**config) as query:
    users = query("SELECT * FROM `users`")

print(json.dumps(users, indent=4))
```

`users` will presented as list of dicts:

```python
[
    {
        'id': 1,
        'name': 'test',
        'email': 'noreply@localhost'
    },
    {
        'id': 2,
        'name': 'user1',
        'email': 'my@example.com'
    }
]
```

Changing database:

```python
from quicker import Connection

with Connection(provider='mysql', read_default_file='~/.my.cnf') as db:
    db.query("INSERT INTO `users` VALUE (3, 'user2', 'user2@example.org')")
```

Quicker by default make commit after closing context. Set option `commit=False` to disable automatic commit.

For logging add following code:

```
import logging

logging.basicConfig(level=logging.DEBUG)
```

Direct access to Cursor object:

```
from quicker import Connection, make_list

# config declaration here...

with Connection(**config) as db:
    db.cursor.execute('SELECT `id`, `name`, `email` FROM `users` WHERE `name` = %s', ('John',))
    users = db.cursor.fetchall()
    # Note: user is tuple! Convert it to list of dicts!
    colnames = [desc[0] for desc in db.cursor.description]
    users_list = make_list(colnames, users)
```
