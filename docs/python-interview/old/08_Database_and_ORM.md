# 08 — Database & ORM Interview Questions
## Complete Questions with Python Examples

---

## 8.1 SQL Fundamentals

### Q1: Essential SQL queries every Python developer must know.

```sql
-- JOINS
-- Inner join: only matching rows from both tables
SELECT u.name, o.total FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- Left join: all rows from left table + matching from right
SELECT u.name, COALESCE(COUNT(o.id), 0) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.name;

-- AGGREGATION
SELECT
    department,
    COUNT(*) as emp_count,
    AVG(salary) as avg_salary,
    MAX(salary) as max_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 50000    -- Filter AFTER grouping (WHERE filters BEFORE)
ORDER BY avg_salary DESC;

-- WINDOW FUNCTIONS (critical for senior interviews)
SELECT
    name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank,
    salary - AVG(salary) OVER (PARTITION BY department) as diff_from_avg,
    SUM(salary) OVER (ORDER BY hire_date) as running_total
FROM employees;

-- SUBQUERIES
-- Find users who spent more than average
SELECT name, total_spent
FROM (
    SELECT u.name, SUM(o.total) as total_spent
    FROM users u JOIN orders o ON u.id = o.user_id
    GROUP BY u.name
) sub
WHERE total_spent > (SELECT AVG(total) FROM orders);

-- CTE (Common Table Expression) — cleaner subqueries
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', order_date) as month,
        SUM(total) as revenue
    FROM orders
    GROUP BY month
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month) as prev_month,
       revenue - LAG(revenue) OVER (ORDER BY month) as growth
FROM monthly_sales;

-- INDEXES
CREATE INDEX idx_users_email ON users(email);              -- B-tree (default)
CREATE INDEX idx_orders_date ON orders(order_date DESC);   -- Descending
CREATE INDEX idx_composite ON orders(user_id, order_date); -- Composite
CREATE INDEX idx_partial ON orders(total) WHERE status = 'completed'; -- Partial

-- EXPLAIN ANALYZE — understand query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';
-- Seq Scan vs Index Scan — Index Scan is what you want for selective queries
```

---

### Q2: Explain N+1 query problem and how to solve it.

**Answer:**

```python
# ═══════════════════════════════════════
# N+1 Problem — the silent performance killer
# ═══════════════════════════════════════

# ❌ N+1 queries — 1 query for users + N queries for orders
"""
users = User.query.all()          # 1 query: SELECT * FROM users
for user in users:                # N iterations
    print(user.orders)            # N queries: SELECT * FROM orders WHERE user_id = ?
# Total: N+1 queries!
"""

# ✅ Fix 1: Eager loading (SQLAlchemy)
"""
# joinedload — single JOIN query
users = session.query(User).options(joinedload(User.orders)).all()
# SELECT users.*, orders.* FROM users LEFT JOIN orders ON ...

# subqueryload — 2 queries (better for large result sets)
users = session.query(User).options(subqueryload(User.orders)).all()
# Query 1: SELECT * FROM users
# Query 2: SELECT * FROM orders WHERE user_id IN (1, 2, 3, ...)

# selectinload (recommended for collections)
users = session.query(User).options(selectinload(User.orders)).all()
"""

# ✅ Fix 2: Django — select_related / prefetch_related
"""
# select_related — single JOIN (for ForeignKey, OneToOne)
posts = Post.objects.select_related('author').all()

# prefetch_related — separate query + Python-side join (for ManyToMany, reverse FK)
authors = Author.objects.prefetch_related('books').all()
"""
```

---

## 8.2 SQLAlchemy

### Q3: SQLAlchemy ORM essentials.

```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship, Session, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, index=True)

    # Relationship — lazy loading by default
    orders = relationship("Order", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"<User(name={self.name})>"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    total = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship("User", back_populates="orders")

# Engine & Session
engine = create_engine("postgresql://user:pass@localhost/mydb", echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# CRUD Operations
def create_user(session: Session, name: str, email: str) -> User:
    user = User(name=name, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_users_with_orders(session: Session, min_total: float):
    """Complex query with join and filter."""
    from sqlalchemy import func
    return (
        session.query(User, func.sum(Order.total).label("total_spent"))
        .join(Order)
        .group_by(User.id)
        .having(func.sum(Order.total) > min_total)
        .order_by(func.sum(Order.total).desc())
        .all()
    )

# Transaction handling
def transfer_funds(session, from_id, to_id, amount):
    try:
        from_acc = session.query(Account).get(from_id)
        to_acc = session.query(Account).get(to_id)

        if from_acc.balance < amount:
            raise ValueError("Insufficient funds")

        from_acc.balance -= amount
        to_acc.balance += amount
        session.commit()
    except Exception:
        session.rollback()
        raise

# SQLAlchemy 2.0 style (modern)
from sqlalchemy import select

stmt = select(User).where(User.name == "Alice").order_by(User.id)
result = session.execute(stmt).scalars().all()
```

---

## 8.3 Redis

### Q4: Redis patterns for Python applications.

```python
"""
Redis Data Structures & Use Cases:
  String:     Caching, counters, rate limiting
  Hash:       User profiles, session data
  List:       Message queues, recent items
  Set:        Tags, unique visitors, mutual friends
  Sorted Set: Leaderboards, priority queues
  Stream:     Event sourcing, log aggregation
"""

# Example patterns with redis-py
"""
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 1. Caching with TTL
def get_user_cached(user_id):
    cache_key = f"user:{user_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    user = db.query(User).get(user_id)
    r.setex(cache_key, 3600, json.dumps(user.to_dict()))  # 1 hour TTL
    return user.to_dict()

# 2. Distributed Lock
def with_lock(lock_name, timeout=10):
    lock = r.lock(lock_name, timeout=timeout)
    if lock.acquire(blocking=True, blocking_timeout=5):
        try:
            # Critical section
            pass
        finally:
            lock.release()

# 3. Leaderboard (Sorted Set)
r.zadd("leaderboard", {"alice": 100, "bob": 85, "charlie": 92})
top_3 = r.zrevrange("leaderboard", 0, 2, withscores=True)
# [('alice', 100), ('charlie', 92), ('bob', 85)]
rank = r.zrevrank("leaderboard", "bob")  # 2 (0-indexed)

# 4. Pub/Sub
def publisher():
    r.publish("notifications", json.dumps({"type": "new_message", "user": "alice"}))

def subscriber():
    pubsub = r.pubsub()
    pubsub.subscribe("notifications")
    for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            handle_notification(data)

# 5. Session Storage (Hash)
r.hset("session:abc123", mapping={
    "user_id": "42",
    "username": "alice",
    "role": "admin"
})
r.expire("session:abc123", 3600)
session = r.hgetall("session:abc123")
"""
```

---

## 8.4 Database Transactions

### Q5: Explain ACID properties and isolation levels.

**Answer:**

```
ACID:
  Atomicity:    All-or-nothing (transaction fully completes or fully rolls back)
  Consistency:  Database moves from one valid state to another
  Isolation:    Concurrent transactions don't interfere
  Durability:   Committed data survives system failures

Isolation Levels (weakest → strongest):
  READ UNCOMMITTED:  Can read uncommitted changes (dirty reads)
  READ COMMITTED:    Only reads committed data (default in PostgreSQL)
  REPEATABLE READ:   Consistent reads within a transaction
  SERIALIZABLE:      Full isolation (as if transactions ran sequentially)

  Higher isolation = more safety but less concurrency

Common Issues:
  Dirty Read:       Reading uncommitted data
  Non-repeatable Read: Same query returns different results in one transaction
  Phantom Read:     New rows appear between two identical queries

Python/SQLAlchemy:
  session.begin()
  session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
  # ... operations ...
  session.commit()
```

---
