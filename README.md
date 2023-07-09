![](https://i.nxhs.cloud/FIc.png)

**Quicker** is a pythonic tool for querying databases.

Quicker wraps popular Python packages:

- `mysqlclient` for MySQL.
- `psycopg2` for PostgreSQL (not implemented yet).
- Python builtin `sqlite` for SQLite (not implemented yet).

Connection parameters will passed to "backend" module as is.

# Installation

```
pip install git+https://git.nxhs.cloud/ge/quicker
```

# Usage

`Connection` is context manages and must be used with `with` keyword. `Connection` returns `Query` callable object. `Query` can be called in this ways:

```python
with Connection(**config) as db:
    db.exec("sql query here...")
    db.query("sql query here...")  # query is alias for exec()

# Query is callable and you can also do this:
with Connection(**config) as query:
    query("sql query here...")
```

`Query` cannot be called itself, you must use `Connection` to correctly initialise `Query` object. Available methods and properties:

- `query()`, `exec()`. Execute SQL. There is You can use here this syntax: `query('SELECT * FROM users WHERE id = %s', (15,))`.
- `commit()`. Write changes into database.
- `cursor`. Call [MySQLdb Cursor object](https://mysqlclient.readthedocs.io/user_guide.html#cursor-objects) methods directly.

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
    db.query("INSERT INTO users VALUE (3, 'user2', 'user2@example.org')")
```

Quicker by default make commit after closing context. Set option `commit=False` to disable automatic commit.