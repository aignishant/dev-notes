# Module 3 — Databases (SQLite, MySQL, SQLAlchemy 2.x, Redis)

> **Bible Module 3 of 14.** Self-contained. Written for **SQLite 3.45+, MySQL 8.x, SQLAlchemy 2.x, Redis 7.x, Alembic 1.13+**. All code runnable as-is. Assumes Modules 1–2.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: model a domain in tables; write performant SQL by hand; use SQLAlchemy 2.x's modern API for both quick scripts and production services; run schema migrations with Alembic; pick the right isolation level; cache with Redis without corrupting your data; and reason about indexes well enough to fix slow queries.

**Target reader.** Modules 1 and 2 done, or already comfortable with Python and pandas. SQL knowledge from zero is fine — §2 is a complete refresher.

**How to use it.** Same as before. Do all 36 problems before reading the solutions.

**Prerequisites.** Module 1 (Python). Module 2 helps but isn't required.
**Next steps after this module.** Module 4 (FastAPI) builds directly on this. Module 5 (BigQuery) extends SQL to columnar warehouses.

---

## 1. The database landscape — pick the right tool

| Use case | Right tool |
|---|---|
| Local file DB, single-process, embedded | **SQLite** (Python built-in) |
| App backend, transactional, well-known | **MySQL** or **PostgreSQL** |
| Caching, sessions, rate limits, queues | **Redis** |
| Document/JSON-shaped data, flexible schema | **MongoDB** |
| Analytics on >10M rows, columnar | **DuckDB**, **ClickHouse**, **BigQuery** (Module 5) |
| Search and full-text | **Elasticsearch** / **OpenSearch** |
| Vector similarity for ML / RAG | **pgvector**, **Qdrant**, **Pinecone** (Module 10) |
| Distributed, multi-region SQL | **CockroachDB**, **Spanner** |

**Rule of thumb in 2026.** If you're starting a new app, default to **PostgreSQL** for the primary store, **Redis** for cache, and reach for specialized stores only when you've measured a real need. We'll cover MySQL because it's still ubiquitous (TCS/Infosys/most enterprise stacks run it). The principles transfer 1:1 to Postgres.

### 1.1 The two database mental models

- **Relational (SQL):** Data is rows in tables with fixed columns and types. Relationships via foreign keys. Strong consistency. Great when your domain has clear nouns and verbs (users, orders, payments) — i.e. 90% of business apps.
- **Key-value / document (NoSQL):** Data is blobs keyed by something. Faster to start; harder to query complex relationships. Best for caches, sessions, or genuinely document-shaped data.

You will use SQL more than anything else for the rest of your career. Master it.

---

## 2. SQL fundamentals refresher

If you already know SELECT/JOIN/GROUP BY, skim this. If not, read carefully — every other section assumes it.

### 2.1 Setting up a sandbox

You don't need a server. SQLite is built into Python:

```python
import sqlite3
conn = sqlite3.connect(":memory:")           # ephemeral DB in RAM
conn.row_factory = sqlite3.Row                # rows behave like dicts
cur = conn.cursor()
cur.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, age INT)")
cur.executemany("INSERT INTO users(name, age) VALUES (?, ?)",
                [("Ada", 30), ("Bob", 25), ("Cal", 40)])
conn.commit()
for row in cur.execute("SELECT * FROM users WHERE age > 25 ORDER BY age"):
    print(dict(row))
# {'id': 1, 'name': 'Ada', 'age': 30}
# {'id': 3, 'name': 'Cal', 'age': 40}
```

### 2.2 The eight statements that do 95% of the work

```sql
-- DDL
CREATE TABLE orders (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id       INTEGER NOT NULL REFERENCES users(id),
  amount        DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
  status        TEXT NOT NULL DEFAULT 'pending',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_user ON orders(user_id);

-- DML
INSERT INTO orders(user_id, amount) VALUES (1, 49.99);
SELECT * FROM orders WHERE status = 'pending';
UPDATE orders SET status = 'shipped' WHERE id = 7;
DELETE FROM orders WHERE created_at < DATE('now', '-90 days');

-- TCL (transactions)
BEGIN TRANSACTION;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;        -- or ROLLBACK on error
```

### 2.3 SELECT — the one statement to master

```sql
SELECT
    u.id,
    u.name,
    COUNT(o.id)        AS n_orders,
    SUM(o.amount)      AS total,
    AVG(o.amount)      AS avg_order
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.country = 'US'
  AND o.created_at >= '2026-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) >= 3
ORDER BY total DESC
LIMIT 10
OFFSET 0;
```

**Order of evaluation (logical, not written):** `FROM` → `JOIN` → `WHERE` → `GROUP BY` → `HAVING` → `SELECT` → `ORDER BY` → `LIMIT/OFFSET`. Knowing this fixes most "why doesn't my query work" problems. For example: you can't reference `total` (a `SELECT` alias) in `WHERE` because `WHERE` runs first. You can in `HAVING` and `ORDER BY` (in most dialects) because they run after.

### 2.4 Joins — visualized

```
       INNER JOIN          LEFT JOIN           FULL OUTER JOIN
       (intersection)      (all of left)       (everything)

         A   B               A   B                A   B
        ___ ___             ___ ___              ___ ___
        | |X| |             |#|X| |              |#|X|#|
        --- ---             --- ---              --- ---
```

```sql
SELECT u.name, o.amount
FROM users u
INNER JOIN orders o ON o.user_id = u.id;     -- only matched rows

SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;      -- all users, NULL where no orders

-- Semi-join (does it exist at all?) and anti-join
SELECT * FROM users u WHERE EXISTS  (SELECT 1 FROM orders o WHERE o.user_id = u.id);
SELECT * FROM users u WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

### 2.5 Aggregations and GROUP BY

```sql
-- per-user metrics
SELECT user_id,
       COUNT(*)          AS n_orders,
       SUM(amount)       AS total,
       MIN(created_at)   AS first_order,
       MAX(created_at)   AS last_order
FROM orders
GROUP BY user_id;

-- one row per group; every column in SELECT must be in GROUP BY or an aggregate
```

**The "non-aggregated column" rule.** Strict SQL (and modern MySQL with `ONLY_FULL_GROUP_BY`) requires every selected column to be either in `GROUP BY` or wrapped in an aggregate. SQLite is lax — it'll silently pick *some* row's value, which is a bug factory.

### 2.6 Window functions — the SQL feature most engineers underuse

A window function computes a value across a set of rows *related to the current row*, without collapsing rows like `GROUP BY` does.

```sql
-- top 3 highest-paid per department, with rank
SELECT name, dept, salary, rn
FROM (
    SELECT name, dept, salary,
           ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS rn,
           AVG(salary) OVER (PARTITION BY dept)                       AS dept_avg,
           SUM(salary) OVER (PARTITION BY dept ORDER BY hire_date)    AS running_total
    FROM employees
) t
WHERE rn <= 3;
```

**The four window function families:**
- **Ranking:** `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `NTILE(n)`
- **Aggregate:** `SUM/AVG/COUNT/MIN/MAX OVER (...)`
- **Offset:** `LAG(col, n)`, `LEAD(col, n)`, `FIRST_VALUE`, `LAST_VALUE`
- **Statistical:** `PERCENT_RANK`, `CUME_DIST`, `PERCENTILE_CONT`

`OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ... AND ...)` controls the window. Master this; it eliminates most subqueries.

### 2.7 CTEs — the readability fix for nested queries

```sql
WITH high_spenders AS (
    SELECT user_id, SUM(amount) AS total
    FROM orders
    GROUP BY user_id
    HAVING SUM(amount) > 1000
),
recent_signups AS (
    SELECT id FROM users WHERE created_at >= DATE('now', '-30 days')
)
SELECT u.id, u.name, hs.total
FROM users u
JOIN high_spenders hs ON hs.user_id = u.id
JOIN recent_signups rs ON rs.id = u.id;
```

CTEs (Common Table Expressions) are temporary named result sets. They're not strictly faster than subqueries (most planners inline them), but they're vastly more readable. **Default to CTEs over deeply nested subqueries.**

Recursive CTEs handle hierarchies (org charts, comment threads):

```sql
WITH RECURSIVE org AS (
    SELECT id, name, manager_id, 1 AS depth
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, org.depth + 1
    FROM employees e JOIN org ON e.manager_id = org.id
)
SELECT * FROM org;
```

### 2.8 NULLs — the silent bug factory

NULL means "unknown," not "empty." Three rules people forget:

1. `NULL = NULL` is **NULL**, not TRUE. Use `IS NULL` / `IS NOT NULL`.
2. `NULL` propagates through expressions: `5 + NULL` → `NULL`. `'abc' || NULL` → `NULL`.
3. Aggregates **skip NULLs** (except `COUNT(*)`). `AVG(col)` ignores NULLs.

```sql
-- WRONG: this won't find rows where deleted_at is NULL
SELECT * FROM users WHERE deleted_at != '2026-01-01';

-- RIGHT: be explicit
SELECT * FROM users WHERE deleted_at IS NULL OR deleted_at != '2026-01-01';

-- COALESCE provides defaults
SELECT name, COALESCE(nickname, name) AS display_name FROM users;
```

---

## 3. SQLite — Python's built-in database

SQLite is a serverless, zero-config SQL engine that lives in a single file. Python ships with `sqlite3` in the standard library. It is genuinely production-grade for many use cases (the Apple Mail database, Firefox bookmarks, every smartphone) — it is **not** a toy.

### 3.1 When to use SQLite (and when not to)

| Good for | Bad for |
|---|---|
| Single-process apps | Multi-writer concurrent writes |
| CLI tools, desktop apps | Networked apps with >1 server |
| Tests for code that hits a "real" DB | Apps needing strict per-row locking |
| Local data analysis | Datasets bigger than disk |
| Embedded in a service for cache/queue | Anything requiring user/role auth |

### 3.2 The `sqlite3` module — what every Python dev should know

```python
import sqlite3

# 1) Open a connection. On-disk or in-memory.
conn = sqlite3.connect("app.db", detect_types=sqlite3.PARSE_DECLTYPES)
conn.row_factory = sqlite3.Row                # rows act like dicts AND tuples
conn.execute("PRAGMA foreign_keys = ON")       # foreign keys are OFF by default(!)
conn.execute("PRAGMA journal_mode = WAL")      # better concurrency than default

# 2) Always parameterize. Never f-string user input into SQL.
cur = conn.execute(
    "SELECT * FROM users WHERE email = ? AND active = ?",
    ("ada@example.com", 1),
)
row = cur.fetchone()
print(row["email"] if row else "not found")

# 3) Many rows
conn.executemany(
    "INSERT INTO users(name, email) VALUES (?, ?)",
    [("Ada", "a@x"), ("Bob", "b@x"), ("Cal", "c@x")],
)

# 4) Transactions — sqlite3 implicitly opens one. Commit or rollback explicitly.
try:
    conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    conn.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    conn.commit()
except Exception:
    conn.rollback()
    raise

conn.close()
```

**Three things that bite people every time:**

1. **Foreign keys are OFF by default.** Run `PRAGMA foreign_keys = ON` on every connection.
2. **Default journal mode is slow** for concurrent reads. `PRAGMA journal_mode = WAL` (write-ahead log) lets readers and writers operate concurrently.
3. **`sqlite3` opens an implicit transaction.** Use `conn` as a context manager (auto-commits on success):

```python
with conn:
    conn.execute("UPDATE ...")          # commits if no exception, rolls back otherwise
```

### 3.3 Type adapters — datetime, JSON

SQLite has 5 storage classes (NULL, INTEGER, REAL, TEXT, BLOB). Python types map via *adapters*. Modern usage:

```python
import json, sqlite3

# Register JSON as a serializable type
sqlite3.register_adapter(dict, json.dumps)
sqlite3.register_converter("JSON", json.loads)

conn = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
conn.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, payload JSON)")
conn.execute("INSERT INTO events(payload) VALUES (?)", ({"event": "login", "ip": "1.2.3.4"},))
row = conn.execute("SELECT payload FROM events").fetchone()
print(row[0])    # {'event': 'login', 'ip': '1.2.3.4'}  — already a dict
```

For datetimes, use ISO 8601 strings (text) — they sort correctly and are readable.

### 3.4 SQLite-specific power features

- **JSON1 extension.** Built-in. `SELECT json_extract(payload, '$.event') FROM events`.
- **Full-text search (FTS5).** `CREATE VIRTUAL TABLE docs USING fts5(title, body)` — gives you a search engine in 1 line.
- **R-Tree.** Spatial indexing for geometry.
- **WAL mode** for concurrency.

```sql
-- FTS5 example
CREATE VIRTUAL TABLE articles_fts USING fts5(title, body);
INSERT INTO articles_fts VALUES ('Python tips', 'Use list comprehensions...');
SELECT title FROM articles_fts WHERE articles_fts MATCH 'list AND comprehension';
```

---

## 4. MySQL with PyMySQL

MySQL is a client/server relational DB. We'll use `PyMySQL` (pure Python, easiest to install) for examples; `mysql-connector-python` (Oracle's official) and `mysqlclient` (C-extension, fastest) have nearly identical APIs.

### 4.1 Connecting

```python
import pymysql

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="appuser",
    password="...",                    # never hardcode in prod — env var
    database="myapp",
    charset="utf8mb4",                 # always utf8mb4, NOT utf8 — see below
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=False,                  # explicit transactions
)
```

**The `utf8mb4` rule.** MySQL's `utf8` is a historical 3-byte subset of UTF-8. It cannot store emoji or many CJK characters — they will be silently truncated or rejected. **Always use `utf8mb4`** for both connection and table charset. Use `utf8mb4_0900_ai_ci` (or `_unicode_ci` on older MySQL) collation.

### 4.2 The query API

```python
with conn.cursor() as cur:
    cur.execute("SELECT id, name FROM users WHERE email = %s", ("ada@x",))
    user = cur.fetchone()                         # dict {'id': 1, 'name': 'Ada'}

    cur.execute(
        "INSERT INTO users(name, email) VALUES (%s, %s)",
        ("Bob", "bob@x"),
    )
    new_id = cur.lastrowid

    cur.executemany(
        "INSERT INTO logs(user_id, action) VALUES (%s, %s)",
        [(new_id, "signup"), (new_id, "verify")],
    )

conn.commit()
conn.close()
```

**Note the placeholder.** PyMySQL uses `%s` (not `?` like SQLite) — DB-API doesn't standardize the marker style. SQLAlchemy abstracts this away.

### 4.3 Storage engines and DDL

MySQL has multiple storage engines. **Always use InnoDB** (the default since 5.5) — it's the only one with row-level locking, foreign keys, and crash recovery. MyISAM is a relic.

```sql
CREATE TABLE orders (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 4.4 SQL injection — and why we never f-string SQL

```python
# CATASTROPHIC — never do this
email = request.args["email"]
cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
# Attacker sends: '; DROP TABLE users; --
# Your SQL becomes:  SELECT * FROM users WHERE email = ''; DROP TABLE users; --'

# CORRECT — parameterized
cur.execute("SELECT * FROM users WHERE email = %s", (email,))
# The driver escapes/binds — safe
```

**The rule:** SQL strings are static; data goes through bind parameters. The same applies to `IN` clauses (build the right number of placeholders, never interpolate) and to `LIKE` (escape `%` and `_` if they're literal).

For dynamic identifiers (table or column names — which can't be parameterized), use a strict allow-list:

```python
ALLOWED_SORT_COLS = {"created_at", "amount", "name"}
if sort_col not in ALLOWED_SORT_COLS:
    raise ValueError("invalid sort column")
cur.execute(f"SELECT * FROM orders ORDER BY {sort_col}")   # safe — value is allow-listed
```

---

## 5. SQLAlchemy 2.x — Core

SQLAlchemy is the standard Python SQL toolkit. It has two layers:
- **Core:** SQL expression language. You build queries as Python objects; SA emits SQL.
- **ORM:** Object-relational mapping on top of Core.

In 2026 you should use **SQLAlchemy 2.x** (not 1.x). The API is genuinely different and much cleaner.

### 5.1 The Engine and connections

```python
from sqlalchemy import create_engine, text

# URL format: dialect+driver://user:password@host:port/database
engine = create_engine(
    "mysql+pymysql://user:pass@localhost:3306/myapp?charset=utf8mb4",
    pool_size=10,                     # connections in the pool
    max_overflow=20,                  # extra under load
    pool_pre_ping=True,               # detect dead conns (very recommended)
    pool_recycle=3600,                # recycle conns hourly
    echo=False,                       # echo=True logs every SQL — great for dev
)

# A short-lived connection
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name FROM users WHERE id = :id"), {"id": 1})
    row = result.first()
    print(row.id, row.name)
```

**`text()` is for raw SQL.** Note the `:name` parameter style — SA standardizes this. Never f-string user data.

### 5.2 The expression language (no ORM yet)

```python
from sqlalchemy import (MetaData, Table, Column, Integer, String, DateTime,
                         ForeignKey, select, insert, update, func)

metadata = MetaData()
users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("email", String(255), unique=True, nullable=False),
)
orders = Table(
    "orders", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("users.id"), nullable=False),
    Column("amount", Integer, nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

metadata.create_all(engine)            # CREATE TABLE for any not yet existing

# expression-language SELECT
stmt = (
    select(users.c.name, func.sum(orders.c.amount).label("total"))
    .join(orders, orders.c.user_id == users.c.id)
    .where(orders.c.created_at >= "2026-01-01")
    .group_by(users.c.name)
    .having(func.sum(orders.c.amount) > 100)
    .order_by(func.sum(orders.c.amount).desc())
    .limit(10)
)

with engine.connect() as conn:
    for row in conn.execute(stmt):
        print(row.name, row.total)
```

This is the same as the SQL in §2.3 — but it's typed Python, refactor-safe, and dialect-portable.

### 5.3 INSERT / UPDATE / DELETE / UPSERT

```python
from sqlalchemy import insert, update, delete
from sqlalchemy.dialects.mysql import insert as mysql_insert

with engine.begin() as conn:    # begin() = transaction; commits on exit, rolls back on error
    conn.execute(insert(users).values(name="Ada", email="ada@x"))
    conn.execute(update(users).where(users.c.id == 1).values(name="Adelle"))
    conn.execute(delete(users).where(users.c.id == 99))

    # MySQL-style UPSERT (ON DUPLICATE KEY UPDATE)
    stmt = mysql_insert(users).values(id=1, name="Ada")
    stmt = stmt.on_duplicate_key_update(name=stmt.inserted.name)
    conn.execute(stmt)
```

**`engine.begin()` vs `engine.connect()`.** `connect()` gives you a connection with manual transaction control. `begin()` is a context manager that auto-commits or auto-rolls back. Prefer `begin()` for any block that writes.

---

## 6. SQLAlchemy 2.x — ORM

The ORM gives you classes that map to tables. Modern SQLAlchemy 2.x ORM uses Python type hints (`Mapped[...]`) — much cleaner than the old syntax.

### 6.1 Declarative model definitions

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id:    Mapped[int]           = mapped_column(primary_key=True)
    name:  Mapped[str]           = mapped_column(String(100))
    email: Mapped[str]           = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self): return f"User(id={self.id!r}, email={self.email!r})"

class Order(Base):
    __tablename__ = "orders"

    id:        Mapped[int]   = mapped_column(primary_key=True)
    user_id:   Mapped[int]   = mapped_column(ForeignKey("users.id"))
    amount:    Mapped[int]
    note:      Mapped[Optional[str]] = mapped_column(String(255), default=None)

    user: Mapped[User] = relationship(back_populates="orders")
```

Notice: `Mapped[int]` → NOT NULL int column. `Mapped[Optional[str]]` → NULL allowed. The ORM picks the right SQL type for native Python types automatically.

### 6.2 Sessions — the unit of work

```python
from sqlalchemy.orm import Session

with Session(engine) as session:
    # add new objects
    ada = User(name="Ada", email="ada@x")
    ada.orders = [Order(amount=50), Order(amount=100)]    # cascade inserts both orders
    session.add(ada)
    session.commit()

    # the IDs are populated after commit
    print(ada.id, ada.orders[0].id)
```

A `Session` is a "unit of work." Changes are tracked and flushed atomically on `commit()`.

### 6.3 Querying (the modern way)

```python
from sqlalchemy import select

with Session(engine) as session:
    # SELECT one
    user = session.get(User, 1)                            # by primary key
    user = session.scalar(select(User).where(User.email == "ada@x"))

    # SELECT many
    users = session.scalars(select(User).order_by(User.created_at.desc()).limit(10)).all()

    # JOIN + filter
    stmt = (
        select(User.name, func.sum(Order.amount).label("total"))
        .join(Order)
        .group_by(User.id)
        .having(func.sum(Order.amount) > 100)
    )
    for name, total in session.execute(stmt):
        print(name, total)
```

**`session.scalars()`** is the modern way to get model objects out. **`session.execute()`** returns rows of mixed columns. The 1.x `query()` API still works but is legacy.

### 6.4 The N+1 problem — and how to fix it

```python
# DANGEROUSLY slow — emits one query per user
for user in session.scalars(select(User)):
    print(user.name, len(user.orders))      # each user.orders triggers a SELECT

# FIX: eager-load the relationship
from sqlalchemy.orm import selectinload

for user in session.scalars(select(User).options(selectinload(User.orders))):
    print(user.name, len(user.orders))      # one extra query total — not N
```

Loading strategies:
- **`selectinload`** — issues a second query with `WHERE id IN (...)`. **Default choice.**
- **`joinedload`** — single query with a LEFT OUTER JOIN. Best for one-to-one and small one-to-many.
- **`raiseload`** — raise if accessed lazily. Use to enforce eager loading in production.

The N+1 problem is the #1 ORM performance issue. Run with `echo=True` or use `sqltap` to count queries during dev.

### 6.5 Sessions and transactions — patterns

```python
def transfer(session: Session, from_id: int, to_id: int, amount: int):
    src = session.get(User, from_id, with_for_update=True)        # SELECT ... FOR UPDATE
    dst = session.get(User, to_id,   with_for_update=True)
    src.balance -= amount
    dst.balance += amount

# Caller
with Session(engine) as session, session.begin():     # nested context = transaction
    transfer(session, 1, 2, 100)
# auto-commit on exit, rollback on exception
```

`Session.begin()` makes the session itself a transactional context — the cleanest pattern.

---

## 7. SQLModel — when you want pydantic + SQLAlchemy in one type

[SQLModel](https://sqlmodel.tiangolo.com) (by FastAPI's author) merges SQLAlchemy ORM and pydantic models. One class, two purposes: DB row + API schema.

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select

class User(SQLModel, table=True):
    id:    Optional[int] = Field(default=None, primary_key=True)
    name:  str
    email: str           = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    orders: list["Order"] = Relationship(back_populates="user")

class Order(SQLModel, table=True):
    id:      Optional[int] = Field(default=None, primary_key=True)
    user_id: int           = Field(foreign_key="user.id")
    amount:  int
    user:    Optional[User] = Relationship(back_populates="orders")

engine = create_engine("sqlite:///app.db")
SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    ada = User(name="Ada", email="ada@x")
    session.add(ada); session.commit(); session.refresh(ada)

    user = session.exec(select(User).where(User.email == "ada@x")).one()
    print(user)
```

**When to use SQLModel:** new FastAPI service where you want one class for DB row and request/response. Smaller projects.
**When to stick with raw SQLAlchemy ORM:** complex relationships, custom column types, polymorphism, large existing codebases.


---

## 8. Migrations with Alembic

Schema must evolve. Alembic is the standard SQLAlchemy migration tool.

### 8.1 Setup

```bash
uv add sqlalchemy alembic
alembic init alembic                          # creates alembic/, alembic.ini
```

Edit `alembic.ini` and set `sqlalchemy.url` (or read it from env in `env.py`). Then in `env.py`:

```python
from myapp.db import Base                      # your DeclarativeBase
target_metadata = Base.metadata
```

### 8.2 Generating and applying migrations

```bash
# autogenerate from model diffs
alembic revision --autogenerate -m "add users.email_verified column"

# review the generated file in alembic/versions/ — autogenerate is helpful but never blindly trust it
alembic upgrade head                           # apply
alembic downgrade -1                           # one back
alembic history                                # see chain
```

A generated file looks like:

```python
def upgrade():
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="0"))
    op.create_index("idx_users_email_verified", "users", ["email_verified"])

def downgrade():
    op.drop_index("idx_users_email_verified", "users")
    op.drop_column("users", "email_verified")
```

### 8.3 Migration safety rules (production)

1. **Always make migrations backward-compatible** for the duration of a deployment. Otherwise an old code version + new schema (or vice versa) crashes during rollout.
2. **Adding a column:** safe if NULL or has a server default.
3. **Dropping a column:** stop reading it in code → deploy → wait → drop. Never drop in the same release.
4. **Renaming a column:** add new → backfill → switch reads → switch writes → drop old. Multi-release dance.
5. **Adding an index:** can lock the table in MySQL. Use `ALGORITHM=INPLACE, LOCK=NONE` or `pt-online-schema-change` / `gh-ost` for big tables.
6. **NEVER edit a migration file that's been applied to a real environment.** Add a new one instead.

---

## 9. Transactions, isolation levels, deadlocks

### 9.1 ACID

- **Atomic.** All or nothing.
- **Consistent.** Constraints hold before and after.
- **Isolated.** Concurrent transactions don't see each other's intermediate state.
- **Durable.** Once committed, survives crashes.

### 9.2 Isolation levels

The SQL standard defines four; here's how they prevent or allow specific anomalies:

| Level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED *(Postgres default)* | no | possible | possible |
| REPEATABLE READ *(MySQL InnoDB default)* | no | no | possible (no in InnoDB due to gap locks) |
| SERIALIZABLE | no | no | no |

In practice:
- **MySQL InnoDB:** default is REPEATABLE READ. Uses gap locks to prevent phantoms. Often *too* aggressive — common deadlock source.
- **PostgreSQL:** default READ COMMITTED. Use SERIALIZABLE for true correctness; uses optimistic concurrency that aborts conflicting transactions.

```python
# In SQLAlchemy
from sqlalchemy.orm import Session
with Session(engine, isolation_level="SERIALIZABLE") as session:
    ...
```

### 9.3 Locking

Two important locks to know:

```sql
-- Pessimistic: lock rows for update
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
-- now no one else can write to this row until we commit/rollback

-- Pessimistic shared lock (read but block writers)
SELECT * FROM accounts WHERE id = 1 FOR SHARE;

-- Optimistic: don't lock; check version on update
UPDATE accounts SET balance = balance - 100, version = version + 1
WHERE id = 1 AND version = ?;
-- if rowcount == 0, someone else updated; retry the whole transaction
```

Optimistic locking is preferred at scale — locks don't pile up under high concurrency. Pessimistic is right for short critical sections (transfers).

### 9.4 Deadlocks

Two transactions each hold a lock the other wants → deadlock. The DB detects it and aborts one with an error.

```
T1: lock A → wants B
T2: lock B → wants A   →  one is killed
```

**Rules to minimize them:**
1. Always acquire locks in the **same order** across all code paths (e.g., always `min(id) before max(id)`).
2. Keep transactions **short**.
3. **Retry** on deadlock errors automatically — they're a normal part of life:

```python
from sqlalchemy.exc import OperationalError
import time, random

def with_deadlock_retry(fn, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return fn()
        except OperationalError as e:
            if "deadlock" not in str(e).lower(): raise
            if attempt == max_attempts - 1: raise
            time.sleep(random.uniform(0, 0.1 * 2**attempt))
```

---

## 10. Connection pooling

Every TCP connection to a DB has setup cost (~10ms+ for MySQL with TLS). Re-creating one per request is suicide for throughput. Pool them.

### 10.1 SQLAlchemy's pool

```python
engine = create_engine(
    URL,
    pool_size=20,                  # baseline conns
    max_overflow=30,               # burst conns above pool_size
    pool_timeout=10,               # max seconds to wait for a free conn
    pool_recycle=3600,             # close+reopen conns hourly (avoids "MySQL has gone away")
    pool_pre_ping=True,            # ping before reuse — survives restarts/failovers
)
```

### 10.2 Sizing

Rule of thumb: `pool_size = (workers × peak concurrent queries per worker) + headroom`. For a 4-worker FastAPI app doing one query per request, `pool_size=8, max_overflow=10` is reasonable.

**The cardinal mistake.** Setting `pool_size=200`. Every connection holds DB-side memory and a socket. The DB will tip over before you exhaust the pool.

### 10.3 PgBouncer / ProxySQL (for big traffic)

For high-traffic apps with many app servers, use a dedicated connection pooler in front of the DB:
- **PgBouncer** (PostgreSQL).
- **ProxySQL** (MySQL).

These multiplex thousands of client connections onto far fewer DB-side connections. App-side pools then size to a few connections each.

---

## 11. Async database access

For FastAPI / asyncio code (Module 4), use **async drivers** so DB I/O doesn't block the event loop.

### 11.1 SQLAlchemy async

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

engine = create_async_engine(
    "mysql+aiomysql://user:pass@localhost/myapp?charset=utf8mb4",
    pool_size=10, max_overflow=20, pool_pre_ping=True,
)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_user(user_id: int) -> User | None:
    async with SessionLocal() as session:
        return await session.get(User, user_id)

async def list_recent(limit: int = 10) -> list[User]:
    async with SessionLocal() as session:
        result = await session.scalars(
            select(User).order_by(User.created_at.desc()).limit(limit)
        )
        return list(result)
```

### 11.2 The async driver picks

| DB | Async driver | URL prefix |
|---|---|---|
| PostgreSQL | `asyncpg` | `postgresql+asyncpg://` |
| MySQL | `aiomysql` or `asyncmy` | `mysql+aiomysql://` |
| SQLite | `aiosqlite` | `sqlite+aiosqlite://` |

`asyncpg` is the fastest of the three by a large margin.

### 11.3 The "don't mix sync and async" rule

Never call a sync DB driver from an async function. It blocks the event loop and freezes the entire process. Use `asyncio.to_thread(...)` if you absolutely must call a sync function:

```python
result = await asyncio.to_thread(sync_query_function, arg1, arg2)
```

---

## 12. Redis — the in-memory data structure server

Redis is not just a cache. It's an in-memory data structure server — strings, lists, hashes, sets, sorted sets, streams, geo, pub/sub. Master a few patterns and you'll reach for it constantly.

### 12.1 The basics

```python
import redis

# sync client
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

r.set("greeting", "hello")
r.get("greeting")                             # 'hello'
r.set("counter", 0)
r.incr("counter")                              # atomic +1 → 1
r.expire("greeting", 60)                       # TTL 60s

# delete / check
r.delete("greeting")
r.exists("counter")                            # 1 or 0
```

### 12.2 The data structures (and their use cases)

```python
# STRING — counters, simple key/value, JSON blobs
r.set("user:1", '{"name":"ada"}')

# HASH — fielded objects (better than parsing JSON every time)
r.hset("user:1", mapping={"name": "Ada", "age": 30, "country": "US"})
r.hget("user:1", "name")                       # 'Ada'
r.hgetall("user:1")                            # {'name':'Ada','age':'30',...}

# LIST — queues, stacks, capped feeds
r.rpush("tasks", "a", "b", "c")               # push right
r.lpop("tasks")                                # pop left → FIFO queue
r.lrange("tasks", 0, -1)                       # all
r.ltrim("tasks", -100, -1)                     # cap at last 100

# SET — uniqueness, membership, intersections
r.sadd("online_users", "u1", "u2", "u3")
r.sismember("online_users", "u1")             # True
r.sinter("online_users", "premium_users")     # intersection

# SORTED SET — leaderboards, time-ordered indices
r.zadd("leaderboard", {"alice": 100, "bob": 90, "cal": 200})
r.zrevrange("leaderboard", 0, 9, withscores=True)    # top 10
r.zincrby("leaderboard", 10, "alice")          # +10 to alice's score
r.zrangebyscore("leaderboard", 50, 150)        # range query

# STREAM — append-only log, like Kafka-lite
r.xadd("events", {"type": "click", "user": "u1"})
r.xrange("events", "-", "+")                   # all messages

# PUB/SUB — fire-and-forget messaging
pub = r.pubsub()
r.publish("notifications", "hello")
```

### 12.3 The five caching patterns to know

#### Pattern 1 — Cache-aside (look-aside)

The default. Application reads cache; on miss, reads DB and populates cache.

```python
def get_user(user_id: int) -> dict | None:
    key = f"user:{user_id}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)
    user = db_get_user(user_id)
    if user:
        r.setex(key, 300, json.dumps(user))    # cache for 5 min
    return user
```

**When to use:** read-heavy, tolerant of slight staleness. Most apps.

#### Pattern 2 — Write-through

On write, update DB then update cache. Stronger consistency, slower writes.

#### Pattern 3 — Write-behind

App writes to cache; cache asynchronously persists to DB. Risky on crashes; rarely worth it.

#### Pattern 4 — Refresh-ahead

Eagerly refresh hot keys before they expire. Add a "soft TTL" your code checks; refresh asynchronously when crossed.

#### Pattern 5 — Cache stampede protection

When a popular key expires, every concurrent request misses simultaneously and slams the DB. Two fixes:

```python
# (a) per-key lock
def get_with_lock(key, fetch_fn, ttl=300, lock_ttl=10):
    cached = r.get(key)
    if cached: return json.loads(cached)
    lock_key = f"lock:{key}"
    if r.set(lock_key, "1", nx=True, ex=lock_ttl):    # SETNX with TTL
        try:
            value = fetch_fn()
            r.setex(key, ttl, json.dumps(value))
            return value
        finally:
            r.delete(lock_key)
    else:
        time.sleep(0.05)
        return get_with_lock(key, fetch_fn, ttl, lock_ttl)

# (b) probabilistic early refresh — XFetch algorithm — is the elegant solution
```

### 12.4 Distributed rate limiting with Redis

```python
def allow_request(user_id: str, limit: int = 100, window_s: int = 60) -> bool:
    key = f"rate:{user_id}:{int(time.time()) // window_s}"
    n = r.incr(key)
    if n == 1: r.expire(key, window_s)
    return n <= limit
```

Fixed-window. For sliding windows, use a sorted set keyed by timestamp and trim old entries.

### 12.5 Distributed locks — and the warning

`SET key value NX EX 30` looks like a lock. It is, *but* with major caveats:
- TTL must be longer than the longest critical section, or the lock auto-releases mid-work.
- A second client can now run while the first is still holding — race condition.
- The first client's "release" can accidentally release the second's lock — store a unique value and check on release.

For real distributed locks, use **Redlock** carefully or, better, a system designed for it (etcd, Zookeeper, Postgres advisory locks).

### 12.6 Persistence

Redis has two persistence modes: **RDB** (point-in-time snapshots) and **AOF** (append-only file). Use both. For pure cache use cases, you can disable persistence and treat Redis as ephemeral — losing state on restart is fine.

---

## 13. NoSQL — a brief, honest tour

You should know one document store. **MongoDB** is the most common; the API generalizes.

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["myapp"]
users = db["users"]

users.insert_one({"name": "Ada", "email": "a@x", "tags": ["beta", "premium"]})
users.find_one({"email": "a@x"})
users.update_one({"_id": user_id}, {"$set": {"name": "Adelle"}, "$inc": {"login_count": 1}})
users.create_index("email", unique=True)

for u in users.find({"tags": "premium"}).limit(10):
    print(u)

# aggregation pipeline (the equivalent of SQL GROUP BY)
pipeline = [
    {"$match": {"country": "US"}},
    {"$group": {"_id": "$tier", "n": {"$sum": 1}, "total": {"$sum": "$revenue"}}},
    {"$sort": {"total": -1}},
]
for doc in users.aggregate(pipeline):
    print(doc)
```

**When MongoDB is the right call:**
- Schema genuinely varies between documents (heterogeneous events).
- Hierarchical / nested data you'd otherwise normalize across many tables.
- High write throughput on log/event-shaped data.

**When it isn't:**
- Multi-document transactions across collections (Mongo supports them, but they're slower than relational equivalents).
- Strong relational constraints (use SQL).
- Aggregation queries you'd write naturally in SQL.

The 2026 reality: most teams that picked MongoDB in 2015 wish they'd picked Postgres with `JSONB`.

---

## 14. Database performance — indexes and EXPLAIN

### 14.1 Indexes — the 80/20

An index is a separate structure (usually a B-tree) that maps column values → row locations. Reads on indexed columns become O(log n); writes pay a small cost to update the index.

**Rules of thumb:**
- **Index foreign keys.** Always.
- **Index columns used in WHERE, JOIN, ORDER BY, GROUP BY** — but only those with selective filters.
- **Composite indexes follow leftmost prefix rule.** `INDEX(a, b, c)` helps queries filtering by `a`, `(a, b)`, `(a, b, c)` — but NOT just `b` or just `c`.
- **Don't over-index.** Each index slows writes and consumes disk. >5 indexes per table is usually a smell.
- **Covering indexes** include all columns the query needs, so the DB never reads the row. Fast.

```sql
-- bad query: full scan if no index
SELECT * FROM orders WHERE status = 'pending' AND created_at > '2026-01-01';

-- helpful index
CREATE INDEX idx_orders_status_created ON orders(status, created_at);

-- the leftmost prefix rule: this index also helps
SELECT * FROM orders WHERE status = 'pending';
-- but NOT
SELECT * FROM orders WHERE created_at > '2026-01-01';   -- no leading status, won't use it
```

### 14.2 EXPLAIN — the only way to know

```sql
-- MySQL
EXPLAIN SELECT * FROM orders WHERE user_id = 1 AND created_at > '2026-01-01';
EXPLAIN ANALYZE SELECT ...;     -- actually executes and reports timings

-- PostgreSQL
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;

-- SQLite
EXPLAIN QUERY PLAN SELECT ...;
```

What to look for:
- **`type: ALL`** in MySQL = full table scan. Bad on big tables.
- **`Using filesort`** = sorting wasn't satisfied by index. Add an index covering the sort.
- **`Using temporary`** = creating a temp table. GROUP BY without index, common cause.
- **Row count estimates wildly off?** Run `ANALYZE TABLE` to refresh statistics.

### 14.3 The seven slow-query causes (in order of frequency)

1. Missing index on a `WHERE`/`JOIN` column.
2. **N+1 queries** from an ORM (§6.4).
3. Function on the indexed column: `WHERE LOWER(email) = ?` defeats the index. Store lowercased; use a functional index; or compare without the function.
4. Implicit type coercion: `WHERE varchar_col = 123` — converts the column, defeats the index.
5. Selecting too many columns (`SELECT *` over big rows). Specify columns.
6. `OFFSET` on huge tables — pagination by ID range is O(log n); by offset is O(n).
7. Lock waits — long transactions hold row locks; other transactions block.

### 14.4 Pagination — keyset > offset

```sql
-- Slow on big tables: skips O(N) rows
SELECT * FROM events ORDER BY id DESC LIMIT 20 OFFSET 100000;

-- Fast: uses index, O(log N) seek
SELECT * FROM events WHERE id < :last_seen_id ORDER BY id DESC LIMIT 20;
```

The client tracks the last seen ID and passes it back as `:last_seen_id`. This is "cursor pagination" or "keyset pagination" — what every API at scale uses.

---

## 15. Database anti-patterns

| Anti-pattern | Right way |
|---|---|
| f-string user input into SQL | Bind parameters every time |
| Storing money as `FLOAT` | `DECIMAL(p, s)` or integer cents |
| Storing datetimes without timezone | `TIMESTAMPTZ` (Postgres) / `DATETIME` UTC + app-side TZ |
| `SELECT *` in production code | Specify columns |
| `OFFSET` pagination on huge tables | Keyset pagination |
| One huge transaction wrapping many requests | Short transactions; commit frequently |
| Nullable FKs everywhere | NOT NULL where the relationship is mandatory |
| Soft-delete via NULL `deleted_at` then forget to filter | Use views or RLS to enforce filters |
| `MySQL utf8` charset | `utf8mb4` always |
| Unbounded `pool_size` | Size to actual concurrency |
| `pickle` blobs in a column | JSON, or normalize, or a key-value store |
| Sequential UUID primary keys | Auto-increment integers OR sortable UUIDs (UUIDv7) |
| ORM's `query()` (1.x style) | `select()` (2.x) |
| Skipping migrations, editing schema in prod | Alembic for everything |
| Caching with no invalidation strategy | TTL + version stamp on writes |

---


## 16. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 10 SQL fundamentals (P1–P10), 4 SQLite (P11–P14), 10 SQLAlchemy (P15–P24), 5 Transactions/Concurrency (P25–P29), 5 Redis (P30–P34), 2 Migrations (P35–P36).

---

### Problem 1 — Top customers by revenue (with name)

**Statement.** Tables `customers(id, name)` and `orders(id, customer_id, amount, created_at)`. Return the top 10 customers by total revenue in 2026, with their name and order count.

**Brute force.** Two queries: get totals, then get names per ID. N+1 prone.

**Optimized.**
```sql
SELECT c.id, c.name,
       COUNT(o.id) AS n_orders,
       SUM(o.amount) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.created_at >= '2026-01-01' AND o.created_at < '2027-01-01'
GROUP BY c.id, c.name
ORDER BY revenue DESC
LIMIT 10;
```

**Complexity.** O(orders_in_range) with an index on `orders(created_at)` or `orders(customer_id, created_at)`.

**Edge cases.** Customer with no orders in range → excluded by INNER JOIN (correct here). Tied revenues — append a tiebreaker (`ORDER BY revenue DESC, c.id`).

**Real-world.** Every BI dashboard. Pre-aggregation into a daily summary table is standard for high-traffic dashboards.

**Follow-ups.** Top 10 *per country*. Add `LEFT JOIN` if you want zero-revenue customers too. Year-over-year comparison.

---

### Problem 2 — Customers who haven't ordered in 90 days

**Solution (anti-join via NOT EXISTS).**
```sql
SELECT c.id, c.name, c.email
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.id
      AND o.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
);
```

**Why `NOT EXISTS` over `LEFT JOIN ... WHERE NULL`.** Both work; `NOT EXISTS` is clearer and handles NULL in the join column correctly. `NOT IN` is buggy with NULLs — avoid.

**Real-world.** Churn-at-risk segmentation, re-engagement campaigns.

**Follow-ups.** Same as Postgres `NOT EXISTS` (identical). Add window: also no orders in any prior 90-day period vs ever-customers.

---

### Problem 3 — Running total of revenue per customer

**Solution (window function).**
```sql
SELECT customer_id, created_at, amount,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY created_at
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM orders
ORDER BY customer_id, created_at;
```

**Real-world.** Customer-lifetime-value charts, account ledgers, billing systems.

**Follow-ups.** Reset per year (`PARTITION BY customer_id, YEAR(created_at)`). Trailing 30-day total instead of cumulative — change `ROWS` to `RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND CURRENT ROW` (Postgres) or use a CTE with self-join in MySQL.

---

### Problem 4 — Top 3 products per category

**Solution.**
```sql
WITH ranked AS (
    SELECT category_id, product_id, total_sold,
           ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY total_sold DESC) AS rn
    FROM product_sales_summary
)
SELECT category_id, product_id, total_sold
FROM ranked
WHERE rn <= 3;
```

**Why `ROW_NUMBER` and not `RANK`.** `ROW_NUMBER` gives exactly 3 rows even with ties. `RANK` could give >3 with ties. Pick based on requirements.

**Real-world.** Recommendation feeds, leaderboards, category-page layouts.

**Follow-ups.** Top 3 per category *per month*. With ties (`DENSE_RANK <= 3`).

---

### Problem 5 — Pivot: monthly revenue per category as columns

**Solution (conditional aggregation — works in every dialect).**
```sql
SELECT
    DATE_FORMAT(created_at, '%Y-%m') AS month,
    SUM(CASE WHEN category = 'A' THEN amount ELSE 0 END) AS cat_a,
    SUM(CASE WHEN category = 'B' THEN amount ELSE 0 END) AS cat_b,
    SUM(CASE WHEN category = 'C' THEN amount ELSE 0 END) AS cat_c
FROM orders
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY month;
```

**Real-world.** When the analyst wants the columns to be categories. Note: pivots with dynamic columns (unknown categories) require app-level pivot — pandas `pivot_table` is the right tool.

**Follow-ups.** Use Postgres `crosstab` extension or DuckDB's `PIVOT` for cleaner syntax.

---

### Problem 6 — Median order amount (by group)

**Statement.** MySQL doesn't have a built-in median. Compute median order amount per customer.

**Solution (Postgres / SQLite 3.45+ / DuckDB).**
```sql
SELECT customer_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median
FROM orders GROUP BY customer_id;
```

**MySQL solution (no PERCENTILE_CONT — use window).**
```sql
WITH ordered AS (
    SELECT customer_id, amount,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount) AS rn,
           COUNT(*)    OVER (PARTITION BY customer_id)                    AS n
    FROM orders
)
SELECT customer_id, AVG(amount) AS median
FROM ordered
WHERE rn IN ((n+1)/2, (n+2)/2)         -- middle 1 or 2 rows
GROUP BY customer_id;
```

**Real-world.** Robust statistics on skewed data (revenue, latency). Median is far more useful than mean for these.

**Follow-ups.** P95 / P99 (change `0.5` → `0.95` / `0.99`). Approximate medians on huge tables — use t-digest in extensions.

---

### Problem 7 — Find duplicates by composite key, keep latest

**Solution.**
```sql
DELETE FROM events
WHERE id NOT IN (
    SELECT keep_id FROM (
        SELECT MAX(id) AS keep_id
        FROM events
        GROUP BY user_id, event_type, day
    ) t
);
```

**MySQL warning:** in older versions, MySQL forbids referencing the same table in a subquery + DELETE. Wrap in another subquery or use a join syntax.

**Better, idempotent solution using window function:**
```sql
DELETE FROM events
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id, event_type, day ORDER BY id DESC) AS rn
        FROM events
    ) t WHERE rn > 1
);
```

**Real-world.** Data cleanup after a job that double-inserted; deduplication of analytics events.

**Follow-ups.** Mark instead of delete (set `is_duplicate=1`). Soft-delete with audit trail. Doing this in batches (`LIMIT 10000`) on huge tables to avoid long transactions.

---

### Problem 8 — Self-join: hierarchical org chart

**Statement.** `employees(id, name, manager_id)`. List each employee with their manager's name.

**Solution.**
```sql
SELECT e.id, e.name AS employee, COALESCE(m.name, '(no manager)') AS manager
FROM employees e
LEFT JOIN employees m ON m.id = e.manager_id
ORDER BY e.name;
```

**Recursive CTE for full hierarchy depth:**
```sql
WITH RECURSIVE chain AS (
    SELECT id, name, manager_id, 1 AS depth, CAST(name AS CHAR(500)) AS path
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, c.depth + 1, CONCAT(c.path, ' > ', e.name)
    FROM employees e JOIN chain c ON e.manager_id = c.id
)
SELECT * FROM chain ORDER BY path;
```

**Real-world.** Org charts, comment threads, file system trees, BOMs (bills of materials).

**Follow-ups.** Detect cycles (limit depth, check visited set in app code). All descendants of a given manager. Aggregate counts down the tree.

---

### Problem 9 — Find gaps in a sequence (ID gaps)

**Statement.** Find missing IDs in `orders.id` (gaps where rows were deleted).

**Solution.**
```sql
SELECT id + 1 AS gap_start,
       next_id - 1 AS gap_end
FROM (
    SELECT id, LEAD(id) OVER (ORDER BY id) AS next_id
    FROM orders
) t
WHERE next_id - id > 1;
```

**Real-world.** Detecting deleted rows; confirming an export was complete; auditing.

**Follow-ups.** Gaps in time series (sensor readings missing). Find date gaps with `generate_series` (Postgres) or a calendar table.

---

### Problem 10 — Anti-join: orders with no matching shipment

**Solution.**
```sql
-- Method 1: NOT EXISTS — preferred
SELECT * FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.order_id = o.id);

-- Method 2: LEFT JOIN ... IS NULL
SELECT o.*
FROM orders o
LEFT JOIN shipments s ON s.order_id = o.id
WHERE s.id IS NULL;
```

Both are correct; `NOT EXISTS` is usually faster on Postgres/MySQL. `NOT IN` would be wrong if the subquery can return NULL.

**Real-world.** Operational dashboards ("orders awaiting shipment"), data quality checks.

**Follow-ups.** Antijoin with time predicate ("not shipped in 24h after order").

---

### Problem 11 — SQLite: full-text search on documents

**Solution.**
```python
import sqlite3
conn = sqlite3.connect(":memory:")
conn.executescript("""
    CREATE VIRTUAL TABLE docs USING fts5(title, body);
    INSERT INTO docs(title, body) VALUES
        ('Python tips', 'Use comprehensions over loops'),
        ('SQL basics', 'Always parameterize queries'),
        ('Async Python', 'Avoid blocking the event loop with sync calls');
""")
for row in conn.execute("SELECT title FROM docs WHERE docs MATCH 'python OR sql'"):
    print(row)
# ('Python tips',)
# ('SQL basics',)
# ('Async Python',)
```

**Real-world.** Local CLI tools with search. Hard-to-beat for offline/desktop apps.

**Follow-ups.** Phrase search (`MATCH '"event loop"'`). Ranking (`bm25(docs)`). Highlighting matched snippets (`snippet()` function).

---

### Problem 12 — SQLite: idempotent UPSERT

**Statement.** Insert a user; if email exists, update name.

**Solution.**
```python
conn.execute(
    """
    INSERT INTO users(email, name, login_count)
    VALUES (?, ?, 1)
    ON CONFLICT(email) DO UPDATE SET
        name = excluded.name,
        login_count = login_count + 1
    """,
    ("ada@x", "Ada"),
)
```

`excluded` refers to the row that *would have been* inserted. Same syntax in Postgres.

**Real-world.** Idempotent ingest pipelines, "upsert on conflict" patterns. Webhook processors. The `ON CONFLICT` clause is one of the most useful SQL features.

**Follow-ups.** `DO NOTHING` for "insert if not exists." Multi-column constraint. MySQL equivalent is `ON DUPLICATE KEY UPDATE` with a different syntax.

---

### Problem 13 — SQLite: WAL mode with concurrent readers

**Statement.** Demonstrate that with WAL mode, a long-running write doesn't block readers.

**Solution (concept).**
```python
import sqlite3, threading, time

conn = sqlite3.connect("test.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")        # WAL-safe, faster

def writer():
    c = sqlite3.connect("test.db")
    c.execute("BEGIN")
    c.execute("INSERT INTO logs(msg) VALUES (?)", ("slow",))
    time.sleep(2)
    c.commit(); c.close()

def reader():
    c = sqlite3.connect("test.db")
    print(c.execute("SELECT COUNT(*) FROM logs").fetchone())
    c.close()

# In default journal mode, the reader would BLOCK until the writer commits.
# In WAL mode, the reader sees the pre-write snapshot immediately.
```

**Real-world.** Local web servers using SQLite (FastAPI + SQLite is viable for surprisingly large apps with WAL). Mobile-app sync.

**Follow-ups.** Tune `wal_autocheckpoint`. Multi-process writers — SQLite serializes them but WAL keeps it tolerable.

---

### Problem 14 — SQLite: bulk insert performance

**Statement.** Insert 1M rows. Naive loop takes minutes; do it right.

**Solution.**
```python
import sqlite3, time

def fast_bulk_insert(rows):
    conn = sqlite3.connect("bulk.db")
    conn.execute("CREATE TABLE IF NOT EXISTS k(id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("PRAGMA synchronous=OFF")          # don't wait for fsync (only OK on bulk loads)
    conn.execute("PRAGMA journal_mode=MEMORY")
    with conn:                                       # one transaction, not 1M
        conn.executemany("INSERT INTO k(v) VALUES (?)", rows)
    conn.close()

t = time.time()
fast_bulk_insert([(f"row{i}",) for i in range(1_000_000)])
print(time.time() - t, "s")     # typically <5s for 1M rows
```

**Why this works.** Default sqlite commits each insert (durability). Wrapping in one transaction avoids 1M fsyncs. `synchronous=OFF` is acceptable for one-time bulk loads where you can re-run on failure.

**Real-world.** Loading reference data, seeding tests.

**Follow-ups.** `executemany` vs prepared statements. Even faster: dump to CSV and use `.import` from sqlite3 CLI.

---

### Problem 15 — SQLAlchemy: minimal model + CRUD

**Solution.**
```python
from sqlalchemy import create_engine, String, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

class Base(DeclarativeBase): pass

class Post(Base):
    __tablename__ = "posts"
    id:    Mapped[int]  = mapped_column(primary_key=True)
    title: Mapped[str]  = mapped_column(String(200))

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)

with Session(engine) as session:
    session.add_all([Post(title="A"), Post(title="B")])
    session.commit()
    posts = session.scalars(select(Post).order_by(Post.id)).all()
    print([p.title for p in posts])      # ['A', 'B']
```

**Real-world.** This is the smallest viable persistent storage layer for a Python app.

**Follow-ups.** Add timestamps via `mapped_column(DateTime, default=datetime.utcnow)`. Add `__repr__`. Build a small repository class.

---

### Problem 16 — SQLAlchemy: many-to-many relationship

**Statement.** Posts and tags, with an association table.

**Solution.**
```python
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import relationship

post_tag = Table(
    "post_tag", Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id",  ForeignKey("tags.id"),  primary_key=True),
)

class Post(Base):
    __tablename__ = "posts"
    id:    Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    tags:  Mapped[list["Tag"]] = relationship(secondary=post_tag, back_populates="posts")

class Tag(Base):
    __tablename__ = "tags"
    id:    Mapped[int] = mapped_column(primary_key=True)
    name:  Mapped[str] = mapped_column(unique=True)
    posts: Mapped[list[Post]] = relationship(secondary=post_tag, back_populates="tags")
```

**Real-world.** Tags, roles, permissions, attendees of events. The most common relational pattern after one-to-many.

**Follow-ups.** Add an attribute to the association (e.g. `created_at` on the link). For that you'd promote `post_tag` to a full mapped class — "association object" pattern.

---

### Problem 17 — SQLAlchemy: detect and prevent N+1

**Statement.** A loop over users prints their order count. Show the N+1 query, then fix it.

**Solution (the bad version).**
```python
for u in session.scalars(select(User)).all():
    print(u.name, len(u.orders))     # one extra SELECT per user
```

**Fixed.**
```python
from sqlalchemy.orm import selectinload

for u in session.scalars(select(User).options(selectinload(User.orders))):
    print(u.name, len(u.orders))     # 2 queries total, regardless of N
```

**Test it.** Set `engine = create_engine(URL, echo=True)` to see emitted SQL counts. In tests, count queries with the `event.listens_for(engine, "before_cursor_execute")` hook.

**Real-world.** This single bug pattern accounts for half of "ORM is slow" complaints. Tooling: `sqltap`, `sqlcommenter`, or write a tiny query-counter as a fixture.

**Follow-ups.** Use `joinedload` for one-to-one, `selectinload` for one-to-many. `raiseload` to **enforce** eager loading and fail loud on lazy access.

---

### Problem 18 — SQLAlchemy: bulk insert efficiently

**Solution.**
```python
# Way 1: ORM bulk save (still emits N statements but in batches)
session.add_all([User(name=f"u{i}", email=f"u{i}@x") for i in range(10_000)])
session.commit()

# Way 2: Core insert — much faster, no ORM overhead
from sqlalchemy import insert
with engine.begin() as conn:
    conn.execute(insert(User), [{"name": f"u{i}", "email": f"u{i}@x"} for i in range(10_000)])

# Way 3: For huge data — bypass entirely, use COPY (Postgres) or LOAD DATA (MySQL)
```

**Rule.** ORM is for transactional CRUD with relationships. For bulk loads, drop to Core or use the DB's native bulk loader.

**Real-world.** Seed scripts, ETL, data migrations.

**Follow-ups.** Postgres `COPY FROM STDIN` via psycopg. MySQL `LOAD DATA LOCAL INFILE`. Server-side `INSERT ... SELECT` from a staging table.

---

### Problem 19 — SQLAlchemy: filter + paginate with keyset

**Solution.**
```python
def page(session: Session, after_id: int | None = None, limit: int = 20):
    stmt = select(User).order_by(User.id).limit(limit)
    if after_id is not None:
        stmt = stmt.where(User.id > after_id)
    rows = session.scalars(stmt).all()
    next_cursor = rows[-1].id if rows else None
    return rows, next_cursor
```

**Real-world.** API pagination. Always keyset, never `OFFSET`, on tables that grow.

**Follow-ups.** Compound cursor for sort by `created_at, id` (need both for stability). Bidirectional cursors. Encode cursors as opaque base64 to discourage clients from constructing them.

---

### Problem 20 — SQLAlchemy: soft-delete pattern

**Solution.**
```python
class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

class User(SoftDeleteMixin, Base):
    __tablename__ = "users"
    id:    Mapped[int] = mapped_column(primary_key=True)
    name:  Mapped[str]

# Helpful query helper that filters by default
def active_users(session):
    return session.scalars(select(User).where(User.deleted_at.is_(None)))

# Soft-delete
def soft_delete(session, user):
    user.deleted_at = datetime.utcnow()
    session.commit()
```

**Real-world warning.** Soft-delete is appealing but has gotchas: unique-constraint violations on undelete, unindexed `deleted_at IS NULL` filters scanning entire tables, and developers forgetting to filter. Use views or row-level security where supported.

**Follow-ups.** Use a single-column `is_active` boolean (smaller, easier to index). Audit table for hard deletes. GDPR-compliant true deletion.

---

### Problem 21 — SQLAlchemy: optimistic locking with version column

**Solution.**
```python
class Account(Base):
    __tablename__ = "accounts"
    id:      Mapped[int] = mapped_column(primary_key=True)
    balance: Mapped[int]
    version: Mapped[int] = mapped_column(default=0)
    __mapper_args__ = {"version_id_col": version}

# On UPDATE, SA will check version_id and bump it. If another process
# updated in between, SA raises StaleDataError on commit.
```

**Real-world.** Anywhere conflict resolution beats locking — webapp form edits, inventory adjustments, document updates.

**Follow-ups.** Hand-rolled version pattern with retry. Compare-and-swap via `UPDATE ... WHERE version = ?`. Postgres `xmin` system column.

---

### Problem 22 — SQLAlchemy: hybrid property for computed fields

**Solution.**
```python
from sqlalchemy.ext.hybrid import hybrid_property

class User(Base):
    __tablename__ = "users"
    id:    Mapped[int] = mapped_column(primary_key=True)
    first: Mapped[str]
    last:  Mapped[str]

    @hybrid_property
    def full_name(self):
        return f"{self.first} {self.last}"

    @full_name.expression
    def full_name(cls):
        return func.concat(cls.first, " ", cls.last)

# Works in Python AND SQL:
user.full_name                                  # "Ada Lovelace"
session.scalars(select(User).where(User.full_name == "Ada Lovelace"))
```

**Real-world.** Avoiding duplication between Python logic and SQL — same formula in both.

**Follow-ups.** Generated columns at the DB level (Postgres `GENERATED ALWAYS AS`). Hybrid methods (with arguments).

---

### Problem 23 — SQLAlchemy: connection pool sizing experiment

**Statement.** Demonstrate `QueuePool` behavior under load.

**Solution.**
```python
from sqlalchemy import create_engine, text
from concurrent.futures import ThreadPoolExecutor
import time

engine = create_engine(
    "sqlite:///:memory:",
    pool_size=2, max_overflow=0,
    pool_timeout=2,                              # wait at most 2s
)

def slow_query(_):
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        time.sleep(1)

with ThreadPoolExecutor(max_workers=4) as ex:
    futs = list(ex.map(slow_query, range(4)))
# Two threads will succeed quickly, two will wait, possibly time out.
```

**Real-world.** Pool exhaustion is the #2 cause of "site is slow but DB is idle" — your app is queueing on connections, not DB work.

**Follow-ups.** Watch `engine.pool.status()`. Add APM tracing of pool waits. Switch to async + asyncpg when concurrency is high.

---

### Problem 24 — SQLAlchemy: async engine for FastAPI

**Solution.**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///app.db", echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# In a FastAPI route:
# from fastapi import Depends
# @app.get("/users/{id}")
# async def get_user(id: int, session: AsyncSession = Depends(get_session)):
#     return await session.get(User, id)
```

**Real-world.** Standard FastAPI + DB pattern. `expire_on_commit=False` avoids accidental lazy-loads after commit (which would deadlock the loop).

**Follow-ups.** `async with session.begin():` for transactions. Pool tuning for async — fewer connections needed because the loop multiplexes.

---

### Problem 25 — Transaction: implementing a money transfer correctly

**Statement.** Move `amount` from account A to account B atomically. Survive crashes; reject overdrafts.

**Solution.**
```python
from sqlalchemy.exc import OperationalError

def transfer(session, from_id: int, to_id: int, amount: int):
    if amount <= 0: raise ValueError("amount must be positive")
    # always lock in deterministic order to prevent deadlocks
    a, b = sorted([from_id, to_id])
    src_id, dst_id = (a, b) if from_id < to_id else (b, a)
    src = session.get(Account, from_id, with_for_update=True)
    dst = session.get(Account, to_id,   with_for_update=True)
    if src.balance < amount: raise ValueError("insufficient funds")
    src.balance -= amount
    dst.balance += amount

# Caller wraps in a transaction
def safe_transfer(engine, *args, **kwargs):
    for attempt in range(5):
        try:
            with Session(engine) as s, s.begin():
                return transfer(s, *args, **kwargs)
        except OperationalError as e:
            if "deadlock" in str(e).lower() and attempt < 4:
                time.sleep(0.05 * (2**attempt))
                continue
            raise
```

**Why the order trick.** If thread 1 does (A → B) and thread 2 does (B → A) and they both `SELECT FOR UPDATE` in caller order, they deadlock. Sorting IDs and locking in fixed order prevents this.

**Real-world.** Banking, points/coins systems, inventory adjustments.

**Follow-ups.** Idempotency key (so retries don't double-transfer). Audit log table (insert before commit). Two-phase / saga for cross-service transfers.

---

### Problem 26 — Idempotent operations with a unique key

**Statement.** Ensure that re-processing a webhook (e.g., Stripe sends the same event twice) doesn't double-apply.

**Solution.**
```sql
CREATE TABLE webhook_events (
    event_id VARCHAR(64) PRIMARY KEY,
    received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

```python
def process_webhook(event_id, payload):
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO webhook_events(event_id) VALUES (:id)"), {"id": event_id})
            apply_business_logic(conn, payload)
    except IntegrityError:
        return                          # already processed; skip silently
```

The PK violation is the *signal* that this event was already handled. Both inserts fail atomically — your business logic only runs once.

**Real-world.** Every webhook integration. Payment processors retry aggressively; idempotency is non-negotiable.

**Follow-ups.** Idempotency-Key HTTP header pattern for client retries. Time-bounded uniqueness (e.g. one transfer per (user, day, amount) window).

---

### Problem 27 — Detecting and avoiding lost updates

**Statement.** Two threads read account balance 100, both add 10, both write 110. Final balance: 110, not 120. Demonstrate and fix.

**Solution (atomic update).**
```python
# WRONG — lost update
def add_to_balance_bad(session, account_id, amount):
    a = session.get(Account, account_id)
    a.balance += amount
    session.commit()

# RIGHT — let the DB add, atomically
def add_to_balance(engine, account_id, amount):
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE accounts SET balance = balance + :a WHERE id = :id"),
            {"a": amount, "id": account_id},
        )
```

The DB executes the increment under a row lock — concurrent UPDATEs serialize correctly.

**Real-world.** Counters, vote tallies, stock decrements. The "read-modify-write" anti-pattern is widespread; UPDATE-with-expression is the fix.

**Follow-ups.** Optimistic locking with version. Compare-and-swap in SQL. Postgres `RETURNING` clause to get the new value.

---

### Problem 28 — Choosing isolation level

**Statement.** A reporting query takes 30 seconds and reads 10M rows. Concurrent OLTP transactions deadlock against it. What isolation level / approach reduces conflict?

**Discussion.** Default REPEATABLE READ (MySQL) takes range locks that block writes in the read region. Drop the report to READ COMMITTED for less locking. Better: use a read replica for reporting.

```python
with Session(engine, isolation_level="READ COMMITTED") as session:
    run_long_report(session)
```

**Real-world.** Always separate OLTP and analytical workloads. Read replicas, materialized views, or columnar stores (BigQuery / ClickHouse — Module 5).

**Follow-ups.** Postgres `REPEATABLE READ` is MVCC-based — much less locking than MySQL. Snapshot isolation. `SET TRANSACTION READ ONLY` for safety.

---

### Problem 29 — Handle "MySQL has gone away"

**Statement.** Long-running worker processes a queue. After idle period, queries fail with "server has gone away."

**Solution.**
```python
engine = create_engine(
    URL,
    pool_pre_ping=True,                     # ping each conn before use
    pool_recycle=1800,                      # cycle conns every 30 min
    pool_size=10, max_overflow=20,
)
```

`pool_pre_ping` issues a cheap `SELECT 1` before handing out a conn. If it fails, the pool transparently reconnects. `pool_recycle` proactively retires conns older than the window — must be less than MySQL's `wait_timeout` (default 8 hours, but often lowered).

**Real-world.** Every workplace runs into this. Set both options on day one of any new project.

**Follow-ups.** Same options on aiomysql. Heartbeat queries from a worker. Drain + reconnect on `OperationalError`.

---

### Problem 30 — Redis: cache-aside with stampede protection

**Solution.**
```python
import redis, json, time, random

r = redis.Redis(decode_responses=True)
LOCK_TTL_S = 10

def get_user(user_id: int) -> dict | None:
    key = f"user:{user_id}"
    cached = r.get(key)
    if cached: return json.loads(cached)

    lock_key = f"lock:{key}"
    if r.set(lock_key, "1", nx=True, ex=LOCK_TTL_S):
        try:
            user = db_get_user(user_id)               # actual DB call
            if user:
                r.setex(key, 300, json.dumps(user))
            return user
        finally:
            r.delete(lock_key)
    else:
        # someone else is fetching; small backoff and retry
        time.sleep(0.05 + random.random() * 0.05)
        return get_user(user_id)
```

**Real-world.** Defends against thundering herd when a popular key expires. The recursive retry is fine because the lock TTL bounds the depth.

**Follow-ups.** XFetch (probabilistic early refresh). Caching negative results ("user not found") with a shorter TTL. Background refresh worker.

---

### Problem 31 — Redis: rate limiter, sliding window

**Solution (sorted-set timestamp log).**
```python
import time
def allow(user_id: str, limit: int = 100, window_s: int = 60) -> bool:
    key = f"rl:{user_id}"
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_s)    # drop old
    pipe.zcard(key)                                   # count remaining
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window_s)
    _, count, _, _ = pipe.execute()
    return count < limit
```

**Why a pipeline.** The four ops are sent as one round-trip — atomic at the connection level (though for true atomicity, use a Lua script).

**Real-world.** API rate limits, login attempt throttling, scraping politeness.

**Follow-ups.** Atomic Lua script (avoids the count/add race). Token bucket implementation (smoother). Per-IP and per-user limits combined.

---

### Problem 32 — Redis: simple job queue

**Solution.**
```python
# producer
def enqueue(job: dict):
    r.lpush("jobs", json.dumps(job))

# consumer
def consume():
    while True:
        # blocking pop with 5s timeout
        item = r.brpop("jobs", timeout=5)
        if item is None: continue
        _, payload = item
        job = json.loads(payload)
        try:
            handle(job)
        except Exception:
            r.lpush("jobs:dead", payload)            # DLQ
            raise
```

`BRPOP` blocks the consumer until a job arrives — no busy-polling. LPUSH/RPOP gives FIFO.

**Real-world.** Lightweight job queues. For features like retries, scheduling, and idempotency, use **RQ**, **Celery**, or **Dramatiq**. Don't roll your own beyond toy scale.

**Follow-ups.** Reliable queue with `RPOPLPUSH` (atomic move to "in-flight" list) so a crash doesn't lose jobs. Stream-based queue with `XREADGROUP` consumer groups (modern, Kafka-like).

---

### Problem 33 — Redis: leaderboard with pagination

**Solution.**
```python
# update score
r.zincrby("leaderboard:weekly", 10, "alice")

# top 10 with scores
top10 = r.zrevrange("leaderboard:weekly", 0, 9, withscores=True)

# user's rank (1-based)
rank = r.zrevrank("leaderboard:weekly", "alice")
print(rank + 1 if rank is not None else "unranked")

# pagination by rank
def page(start_rank: int, n: int):
    return r.zrevrange("leaderboard:weekly", start_rank, start_rank + n - 1, withscores=True)

# expire weekly board on Sundays — set TTL when first incremented
```

**Real-world.** Game leaderboards, top spenders, trending content. Sorted sets are O(log n) — fast enough for millions of entries.

**Follow-ups.** Per-time-window boards (hourly/daily/weekly) with rollups. Score updates batched via Lua. Approximate top-K (Redis-Bloom CMS).

---

### Problem 34 — Redis: distributed lock — and its caveats

**Solution.**
```python
import uuid

def acquire_lock(key: str, ttl_s: int = 10) -> str | None:
    token = str(uuid.uuid4())
    if r.set(f"lock:{key}", token, nx=True, ex=ttl_s):
        return token
    return None

# release only if WE hold it (Lua script for atomicity)
RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""
def release_lock(key: str, token: str) -> bool:
    return bool(r.eval(RELEASE_LUA, 1, f"lock:{key}", token))
```

**Why the token + Lua.** Without a unique token, you might delete a lock that has timed out and been reacquired by another process. Without the Lua script, GET-then-DEL is a race.

**Caveats (Martin Kleppmann's "How to do distributed locking" is required reading).** Network partitions, GC pauses, clock skew can all cause two clients to think they hold the lock simultaneously. For correctness-critical use cases, use systems with fencing tokens (etcd, Zookeeper, Postgres advisory locks) — not Redis alone.

**Real-world.** OK for "best effort" mutual exclusion (cron deduping, cache stampede). Not OK as the only barrier to a payment being processed twice.

**Follow-ups.** Redlock algorithm. Fencing tokens. Pessimistic vs optimistic in distributed systems.

---

### Problem 35 — Alembic: zero-downtime column rename

**Statement.** Rename `users.fullname` to `users.full_name` without downtime.

**Solution (multi-step deploy).**

Migration 1 (deploy first, code still uses `fullname`):
```python
def upgrade():
    op.add_column("users", sa.Column("full_name", sa.String(200), nullable=True))
    op.execute("UPDATE users SET full_name = fullname")
    # backfill new writes with a trigger OR app-level dual-write
```

App release A: writes go to **both** `fullname` and `full_name`. Reads still come from `fullname`.

App release B: reads switch to `full_name`. Writes still dual.

App release C: writes drop `fullname`.

Migration 2 (after release C is fully deployed):
```python
def upgrade():
    op.drop_column("users", "fullname")
```

**Real-world.** This dance is annoying but unavoidable on production systems serving real traffic. Skip steps and your next deploy goes down.

**Follow-ups.** Tools like `gh-ost` and `pt-online-schema-change` for schema changes on huge MySQL tables. Postgres has built-in `ALTER TABLE` that's mostly online for many operations.

---

### Problem 36 — Alembic: detecting drift between models and DB

**Statement.** Write a CI check that fails if the DB schema diverges from the SQLAlchemy models.

**Solution.**
```bash
# Generate a fresh autogen migration. If it's empty, models match DB.
alembic revision --autogenerate -m "drift-check"
# Inspect the generated file: should be all `pass` in upgrade()/downgrade().
```

```python
# As a Python check (rough sketch)
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

with engine.connect() as conn:
    mc = MigrationContext.configure(conn)
    diff = compare_metadata(mc, target_metadata)
    if diff:
        print("DRIFT:", diff)
        sys.exit(1)
```

Run this in CI on a freshly-migrated test DB.

**Real-world.** Without it, developers will edit models and forget to generate migrations, leading to "works on my machine, breaks in staging." Catch it at PR time.

**Follow-ups.** Linting migrations themselves (e.g., banning destructive ops without explicit approval). Tracking migration runtime in CI.

---

## 17. Three mini-projects

### Mini-project A — A small accounting ledger
Build SQLite + SQLAlchemy ORM models for `accounts` and `entries` (double-entry bookkeeping: every transaction has equal debit and credit entries). Implement `transfer`, `balance(account)`, and `history(account)`. Add Alembic. Add tests that include concurrent transfers (using threads) to verify no money is created or destroyed.

**Skills exercised:** ORM, transactions, `with_for_update`, version columns, Alembic, testing concurrency.

### Mini-project B — A URL shortener with Redis + MySQL
Short URL → long URL mapping. MySQL stores the canonical mapping. Redis caches lookups with a 1-day TTL. Track click counts in Redis (`INCR`) and flush to MySQL hourly. Implement: `create(long_url)`, `resolve(short)`, `top_links(n)`. Use FastAPI for the API (Module 4 preview).

**Skills exercised:** caching strategy, MySQL + Redis dual-store, periodic flush, idempotent ID generation.

### Mini-project C — Schema migration drill
Take any open-source schema (or invent one with 5 tables) and walk through these scenarios end-to-end with Alembic:
- Adding a NOT NULL column with backfill (via two migrations).
- Splitting one column into two.
- Renaming a table while live.
- Adding a unique constraint that retroactively violates existing data.

**Skills exercised:** the multi-release dance §8.3 lays out. This is the most underrated production skill in this module.

---

## 18. Real-world usage map

| Concept | Where it returns later |
|---|---|
| Parameterized queries | Every API route in Module 4 |
| SQLAlchemy 2.x ORM | Module 4 (FastAPI), Module 12 (MLOps metadata stores) |
| SQLModel | Module 4 — easier API + DB integration |
| Alembic | Every deploy in Module 12 (MLOps) |
| Connection pooling | FastAPI under load; LLM apps that hit DBs |
| Async DB | FastAPI async routes; agent tools (Module 11) that read from DB |
| Redis cache-aside | LLM response caching (Module 13 LLMOps); session stores |
| Redis rate limiter | API quota enforcement (Module 13); LLM cost control |
| Redis distributed lock | Cron deduplication; agent loop coordination |
| Redis pub/sub / streams | Real-time agent updates; SSE/WebSocket fan-out |
| Window functions (SQL) | Feature engineering in BigQuery (Module 5); analytics |
| EXPLAIN / indexes | Anywhere a query gets slow — every module |
| Optimistic locking | High-concurrency UI updates; collaborative agents |

---

## 19. Interview pitfalls — what NOT to say

- **"I'll just put it in a NoSQL DB."** Without justifying *why*, this signals weak relational fluency. Most apps want SQL.
- **"I'll add an index to be safe."** Indexes have write cost. State the query and the cardinality first.
- **"I'd query in a loop."** N+1 alarm. Show the JOIN or `WHERE id IN (...)` version.
- **"I'd use `SELECT *`."** Specify columns; be conscious of row width.
- **"`OFFSET` is fine for pagination."** Not on big tables. State keyset.
- **"NULL is just empty."** It's *unknown*. Talk about three-valued logic.
- **"I'd use floats for currency."** No. `DECIMAL` or integer cents.
- **"I'd cache everything."** Articulate invalidation strategy. "TTL of 5 min" is a real answer; "I'd cache it" alone is not.
- **"REPEATABLE READ is the safest level."** Postgres SERIALIZABLE is — and REPEATABLE READ in MySQL has unusual locking that often *increases* deadlocks.
- **"`session.commit()` everywhere."** Demonstrate one transactional boundary per logical unit of work, not per row.
- **"I'd use Redis for the primary store."** Redis is in-memory; persistence is best-effort. Use it for cache/derived data, not the source of truth (with rare exceptions).

**How to communicate.** When given a "design a database" question, narrate in this order: (1) entities and relationships, (2) PK choice and its tradeoffs, (3) indexes you'd add for the stated queries, (4) consistency/availability tradeoffs, (5) growth projection — when does this break?

---

## 20. Cheatsheet

```text
SQL CORE
  SELECT cols FROM t [JOIN ... ON ...]
    WHERE p GROUP BY k HAVING q ORDER BY o LIMIT n OFFSET m
  evaluation order: FROM JOIN WHERE GROUP HAVING SELECT ORDER LIMIT
  joins: INNER LEFT RIGHT FULL CROSS
  semi/anti: WHERE EXISTS / WHERE NOT EXISTS
  CTE: WITH x AS (...) SELECT ... FROM x
  recursive: WITH RECURSIVE x AS (base UNION ALL recur)
  windows: f() OVER (PARTITION BY k ORDER BY o ROWS BETWEEN ...)
    ROW_NUMBER RANK DENSE_RANK NTILE LAG LEAD FIRST_VALUE LAST_VALUE
  NULL-safe: IS NULL  IS NOT NULL  COALESCE  NULLIF
  COUNT(*) counts NULLs; AVG/SUM ignore NULLs

DDL
  CREATE TABLE t(... PRIMARY KEY, ... NOT NULL, FOREIGN KEY (..) REFERENCES ..)
  CREATE INDEX ix ON t(a, b)        composite, leftmost-prefix rule
  ALTER TABLE t ADD COLUMN c TYPE [DEFAULT v]
  CREATE UNIQUE INDEX, CHECK (...)

SQLITE (built-in sqlite3)
  conn = sqlite3.connect("f.db")
  conn.row_factory = sqlite3.Row
  PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL
  conn.execute("?, ?", (a,b))     parameterize!
  conn.executemany(sql, rows)
  with conn: ...                   txn (auto commit/rollback)

MYSQL (PyMySQL)
  pymysql.connect(host=, charset='utf8mb4', cursorclass=DictCursor)
  cur.execute("WHERE x=%s", (v,))   ← %s placeholder
  always: ENGINE=InnoDB, charset=utf8mb4

SQLALCHEMY 2.x — CORE
  engine = create_engine(URL,
      pool_size=10, max_overflow=20,
      pool_pre_ping=True, pool_recycle=3600)
  with engine.begin() as c:        # txn block
      c.execute(stmt, {"a":1})
  text("SELECT :p"), insert(t).values(...)
  select(t.c.a).join(...).where(...).group_by(...)
  on_duplicate_key_update (mysql), on_conflict_do_update (postgres)

SQLALCHEMY 2.x — ORM
  class Base(DeclarativeBase): pass
  class M(Base):
      id: Mapped[int] = mapped_column(primary_key=True)
      name: Mapped[str]
      x: Mapped[Optional[int]]    # nullable
      orders: Mapped[list["Order"]] = relationship(back_populates=...)
  with Session(engine) as s:
      s.add(obj); s.commit()
      s.scalars(select(M).where(M.x==1)).all()
      s.execute(select(M.a, func.sum(M.b)))
      s.get(M, pk)
  loaders: selectinload (default) | joinedload | raiseload
  N+1: USE SELECTINLOAD on relationships you'll access in loops

ALEMBIC
  alembic init alembic
  alembic revision --autogenerate -m "msg"
  alembic upgrade head | downgrade -1
  rules: backward-compat across deploys; never edit applied migrations

TRANSACTIONS / LOCKS
  isolation: READ UNCOMMITTED < READ COMMITTED < REPEATABLE READ < SERIALIZABLE
  MySQL InnoDB default: REPEATABLE READ (gap locks)
  Postgres default: READ COMMITTED
  pessimistic: SELECT ... FOR UPDATE   /   FOR SHARE
  optimistic: WHERE version=? then version+1
  deadlocks: lock in same order; retry with backoff
  lost-update fix: UPDATE x SET v = v + ? (atomic)

CONNECTION POOL
  pool_size: ~ (workers × peak concurrent queries) + headroom
  pool_pre_ping=True   : avoid stale conns
  pool_recycle < server wait_timeout
  proxy: PgBouncer (PG), ProxySQL (MySQL)

ASYNC DB
  postgres: postgresql+asyncpg://      (fastest)
  mysql:    mysql+aiomysql://          mysql+asyncmy://
  sqlite:   sqlite+aiosqlite://
  never sync DB calls in async funcs   (use asyncio.to_thread if you must)

REDIS
  STRING:  set/get/incr/setex/setnx
  HASH:    hset/hget/hgetall/hincrby
  LIST:    lpush/rpush/lpop/rpop/blpop/brpop/lrange/ltrim
  SET:     sadd/sismember/sinter/sunion/sdiff
  ZSET:    zadd/zrange/zrevrange/zincrby/zrangebyscore/zrank/zrevrank
  STREAM:  xadd/xrange/xreadgroup
  PUBSUB:  publish/subscribe
  TTL:     expire/ttl/persist
  pipeline: r.pipeline().cmd().cmd().execute()
  Lua:     r.eval(script, n_keys, *args)

CACHING PATTERNS
  cache-aside (default), write-through, write-behind, refresh-ahead
  stampede: per-key SETNX lock OR XFetch probabilistic refresh
  always TTL; consider negative caching (404s)

INDEXES (rules)
  index FK columns
  index WHERE/JOIN/ORDER/GROUP cols (selective)
  composite: leftmost-prefix matters
  EXPLAIN before adding
  function on column kills index (LOWER(email)); store normalized
  type coercion kills index (varchar = int)
  > 5 indexes per table = smell

PAGINATION
  keyset: WHERE id > :last ORDER BY id LIMIT n     (always)
  offset: OFFSET n LIMIT m   (small tables only)

SECURITY
  parameterize 100% of values
  allow-list dynamic identifiers (col/table names)
  least-priv DB users; never root in app
  TLS to DB; never plaintext over network
  passwords: hash with bcrypt/argon2 — never store plaintext or md5/sha256

ANTI-PATTERNS
  utf8 (use utf8mb4); FLOAT for money (DECIMAL or cents int)
  SELECT * in prod; OFFSET on huge tables; SetWithCopy in pandas of databases
  N+1 in ORM; one-massive-transaction; bare except; pickle blob columns
  ad-hoc schema edits in prod; missing migrations
```

---

## 21. Prerequisites & next steps

**Prerequisites covered? You can:**
- Write JOINs, GROUP BY, window functions, and CTEs by hand.
- Decide between SQLite, MySQL/Postgres, Redis, and Mongo for a given problem.
- Use SQLAlchemy 2.x ORM and Core; spot and fix N+1; size a pool.
- Generate, review, and safely apply Alembic migrations.
- Reason about isolation levels, deadlocks, and locking; implement money-safe transfers.
- Use Redis for cache-aside, rate limiting, leaderboards, and queues — and know when it's the wrong tool.
- Read EXPLAIN output and add (or refuse to add) indexes with reason.

**Next steps in the bible:**
- **Module 4 — FastAPI.** This is where DB sessions become per-request, async, and tested. The async SA pattern from §11 is the spine of any modern Python service.
- **Module 5 — BigQuery & warehousing.** Same SQL, columnar storage, petabyte scale.
- **Module 12 — MLOps.** Models, runs, datasets, and metrics — all metadata going into Postgres/MySQL.

**External study (only if you want depth):**
- *Designing Data-Intensive Applications* (Kleppmann). The book on databases. Read it once; revisit forever.
- *Use the Index, Luke!* (free online) — the clearest treatment of indexes anywhere.
- *PostgreSQL Documentation* — exceptional even if you use MySQL. The SQL chapters teach SQL.
- The SQLAlchemy 2.x docs — they're a tutorial, not just reference.

---

*End of Module 3. Module 4 covers FastAPI 0.115+, Pydantic 2, async, dependency injection, auth, testing, and deployment — same structure, 35+ problems.*
