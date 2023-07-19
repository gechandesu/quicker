<img width="320px" src="logo.svg"/>

**Quicker** is a pythonic 🐍 tool for querying databases.

Quicker wraps popular Python libraries:

- `mysqlclient` for MySQL.
- `psycopg2` for PostgreSQL.
- `sqlite` from Python standard library for SQLite (not implemented yet).

# Why is it needed?

Briefly — just make queries without bothering to learn the abstractions of the library.

At work, I periodically have to make queries to different databases and then somehow process the information. I am not an analyst and Quicker is not intended for analysts. The main use of the library is to quickly execute raw SQL queries into the database. You may want to do this entirely in the Python interactive shell. Quicker interface is as simple as possible, thanks to which lazy system administrators can now effortlessly extract data from the database.

Of course, this library **should not be used in production**. This is just a small assistant in routine tasks.

# Installation

```
pip install git+https://git.nxhs.cloud/ge/quicker
```

# Usage

Quicker uses a context manager. All that is needed for work is to pass connection parameters to object and write the queries themselves. See MySQL example:

```python
from quicker import Connection


with Connection(provider='mysql', read_default_file='~/.my.cnf') as query:
    users = query("SELECT * FROM `users` WHERE admin = 'N'")
```

`Connection` object initialises `Query` callable object for interacting with cursor. You can use `query("sql there..")` or `query.execute("sql...")` syntax. There are the same.

`Query` object methods and properties:

- `query()`, `execute()`. Execute SQL. There is you can use here this syntax: `query('SELECT * FROM users WHERE id = %s', (15,))`.
- `commit()`. Write changes into database.
- `cursor`. Access cursor object directly.
- `connection`. Access connection object directly.

You don't need to commit to the database, Quicker will do it for you, but if you need to, you can commit manually calling `query.commit()`. You can also turn off automatic commit when creating a `Connection` object — pass it the argument `commit=Fasle`.

That's not all — Quicker converts the received data into a list of dictionaries. The list will be empty if nothing was found for the query. If the request does not imply a response, `None` will be returned.

## MySQL example

```python
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
    query(
        """
        CREATE TABLE IF NOT EXISTS users (
            id int AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    query(
        "INSERT INTO users VALUES (NULL, %s, %s, current_timestamp)",
        ('john', 'john@exmpl.org',)
    )
    query.commit()
    users = query("SELECT * FROM users")

print('ID\t NAME\t EMAIL')
for user in users:
    print(user['id'], '\t', user['name'], '\t', user['email'])
```

## PostgreSQL example

```python
import logging

from quicker import Connection


logging.basicConfig(level=logging.DEBUG)

config = {
    'provider': 'postgres',
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'myuser',
    'database': 'mydb',
    'password': 'example',
}

with Connection(**config) as query:
    query(
        """
        CREATE TABLE IF NOT EXISTS users (
            id serial PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    query(
        "INSERT INTO users VALUES ((SELECT MAX(id)+1 FROM users), %s, %s, current_timestamp)",
        ('phil', 'phil@exmpl.org',)
    )
```


## Logging

For logging add following code in your module:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## Direct access to Cursor object

```python
from quicker import Connection, make_list

# config declaration here...

with Connection(**config) as db:
    db.cursor.execute('SELECT id, name, email FROM users WHERE name = %s', ('John',))
    users = db.cursor.fetchall()
    # Note: "users" is tuple! Convert it to list of dicts!
    colnames = [desc[0] for desc in db.cursor.description]
    users_list = make_list(colnames, users)
```