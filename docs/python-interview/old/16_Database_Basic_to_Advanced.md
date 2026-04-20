# 16 — Database Interview Questions (Basic to Advanced)
## Most Popular & Frequently Asked with Scenario-Based Problems

> **Cross-reference:** File 08 (ORM Basics), File 06 (System Design DB Scaling)

---

## 16.1 Basic SQL — Must Know

### Q1: What are different types of JOINs? Explain with example.

```sql
-- Sample Data
-- users:  (1, Alice), (2, Bob), (3, Charlie)
-- orders: (101, user_id=1, $50), (102, user_id=1, $30), (103, user_id=2, $70), (104, user_id=99, $20)

-- ═══════════════════════════════════════
-- INNER JOIN: Only rows that match in BOTH tables
-- ═══════════════════════════════════════
SELECT u.name, o.amount
FROM users u INNER JOIN orders o ON u.id = o.user_id;
-- Result:
-- Alice  | 50
-- Alice  | 30
-- Bob    | 70
-- (Charlie excluded — no orders. user_id=99 excluded — no matching user)

-- ═══════════════════════════════════════
-- LEFT JOIN: ALL rows from left + matching from right (NULL if no match)
-- ═══════════════════════════════════════
SELECT u.name, o.amount
FROM users u LEFT JOIN orders o ON u.id = o.user_id;
-- Result:
-- Alice   | 50
-- Alice   | 30
-- Bob     | 70
-- Charlie | NULL    ← included with NULL (no orders)

-- ═══════════════════════════════════════
-- RIGHT JOIN: ALL rows from right + matching from left
-- ═══════════════════════════════════════
SELECT u.name, o.amount
FROM users u RIGHT JOIN orders o ON u.id = o.user_id;
-- Result:
-- Alice | 50
-- Alice | 30
-- Bob   | 70
-- NULL  | 20       ← order with user_id=99 (no matching user)

-- ═══════════════════════════════════════
-- FULL OUTER JOIN: ALL rows from BOTH tables
-- ═══════════════════════════════════════
SELECT u.name, o.amount
FROM users u FULL OUTER JOIN orders o ON u.id = o.user_id;
-- Result: All of the above combined

-- ═══════════════════════════════════════
-- CROSS JOIN: Cartesian product (every row × every row)
-- ═══════════════════════════════════════
SELECT u.name, s.size
FROM users u CROSS JOIN sizes s;
-- If 3 users × 4 sizes = 12 rows

-- ═══════════════════════════════════════
-- SELF JOIN: Join table with itself
-- ═══════════════════════════════════════
-- Find employees who earn more than their manager
SELECT e.name AS employee, m.name AS manager, e.salary, m.salary
FROM employees e
JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```

---

### Q2: Explain GROUP BY, HAVING, and aggregate functions.

```sql
-- GROUP BY: Group rows that share a value, apply aggregate functions

-- Basic grouping
SELECT department, COUNT(*) AS emp_count, AVG(salary) AS avg_salary
FROM employees
GROUP BY department;

-- HAVING vs WHERE
-- WHERE:  Filters rows BEFORE grouping
-- HAVING: Filters groups AFTER grouping

-- Find departments with more than 5 employees AND average salary > 60K
SELECT department, COUNT(*) AS emp_count, AVG(salary) AS avg_salary
FROM employees
WHERE status = 'active'              -- Filter individual rows FIRST
GROUP BY department
HAVING COUNT(*) > 5                   -- Filter groups AFTER
   AND AVG(salary) > 60000
ORDER BY avg_salary DESC;

-- Aggregate functions
SELECT
    COUNT(*)              AS total_rows,
    COUNT(DISTINCT dept)  AS unique_depts,
    SUM(salary)           AS total_salary,
    AVG(salary)           AS avg_salary,
    MIN(salary)           AS min_salary,
    MAX(salary)           AS max_salary,
    STRING_AGG(name, ', ') AS all_names    -- PostgreSQL
FROM employees;
```

---

### Q3: What is the difference between WHERE and HAVING?

| Feature | WHERE | HAVING |
|---------|-------|--------|
| When applied | Before GROUP BY | After GROUP BY |
| Operates on | Individual rows | Grouped results |
| Can use aggregates? | No | Yes |
| Performance | Faster (filters early) | Slower (filters after grouping) |

```sql
-- ❌ WRONG — can't use aggregate in WHERE
SELECT department, AVG(salary) FROM employees
WHERE AVG(salary) > 50000      -- ERROR!
GROUP BY department;

-- ✅ CORRECT — use HAVING for aggregate conditions
SELECT department, AVG(salary) FROM employees
GROUP BY department
HAVING AVG(salary) > 50000;

-- ✅ Best practice — filter with WHERE first, then HAVING
SELECT department, AVG(salary) FROM employees
WHERE hire_date > '2020-01-01'    -- Reduce rows first (faster)
GROUP BY department
HAVING AVG(salary) > 50000;       -- Then filter groups
```

---

### Q4: Explain UNION vs UNION ALL vs INTERSECT vs EXCEPT.

```sql
-- UNION: Combine results, remove duplicates
SELECT name FROM customers
UNION
SELECT name FROM suppliers;

-- UNION ALL: Combine results, keep duplicates (faster — no dedup)
SELECT name FROM customers
UNION ALL
SELECT name FROM suppliers;

-- INTERSECT: Only rows in BOTH results
SELECT email FROM customers
INTERSECT
SELECT email FROM newsletter_subscribers;

-- EXCEPT: Rows in first result but NOT in second
SELECT email FROM customers
EXCEPT
SELECT email FROM unsubscribed;
```

---

## 16.2 Intermediate — Subqueries & CTEs

### Q5: Subquery vs CTE vs Temporary Table — when to use which?

```sql
-- ═══════════════════════════════════════
-- SUBQUERY: Inline, single-use
-- ═══════════════════════════════════════
-- Find users who spent above average
SELECT name, total_spent
FROM (
    SELECT u.name, SUM(o.amount) AS total_spent
    FROM users u JOIN orders o ON u.id = o.user_id
    GROUP BY u.name
) sub
WHERE total_spent > (SELECT AVG(amount) FROM orders);

-- ═══════════════════════════════════════
-- CTE (Common Table Expression): Named, reusable, readable
-- ═══════════════════════════════════════
WITH user_spending AS (
    SELECT u.id, u.name, SUM(o.amount) AS total_spent
    FROM users u JOIN orders o ON u.id = o.user_id
    GROUP BY u.id, u.name
),
avg_spending AS (
    SELECT AVG(total_spent) AS avg_spent FROM user_spending
)
SELECT us.name, us.total_spent, av.avg_spent
FROM user_spending us, avg_spending av
WHERE us.total_spent > av.avg_spent;

-- ═══════════════════════════════════════
-- Recursive CTE: Hierarchical data (org chart, categories)
-- ═══════════════════════════════════════
WITH RECURSIVE org_chart AS (
    -- Base case: CEO (no manager)
    SELECT id, name, manager_id, 1 AS level
    FROM employees WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: employees under previous level
    SELECT e.id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY level, name;

-- Use Cases:
-- Subquery:  Simple, one-off calculations
-- CTE:       Complex queries, multiple references, readability
-- Temp Table: Very large intermediate results, need indexes
```

---

## 16.3 Advanced — Window Functions

### Q6: Explain window functions — the most asked advanced SQL topic.

```sql
-- Window functions perform calculations ACROSS rows without collapsing them
-- Unlike GROUP BY, they keep all individual rows

-- ═══════════════════════════════════════
-- ROW_NUMBER, RANK, DENSE_RANK
-- ═══════════════════════════════════════
SELECT
    name, department, salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS row_num,
    RANK()       OVER (PARTITION BY department ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dense_rank
FROM employees;

-- Salary:      100K, 90K, 90K, 80K
-- ROW_NUMBER:  1,    2,   3,   4     (always unique)
-- RANK:        1,    2,   2,   4     (skips after tie)
-- DENSE_RANK:  1,    2,   2,   3     (no skip after tie)

-- ═══════════════════════════════════════
-- Practical: Top 3 earners per department
-- ═══════════════════════════════════════
WITH ranked AS (
    SELECT name, department, salary,
           ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rn
    FROM employees
)
SELECT * FROM ranked WHERE rn <= 3;

-- ═══════════════════════════════════════
-- LAG, LEAD: Access previous/next row
-- ═══════════════════════════════════════
SELECT
    month, revenue,
    LAG(revenue, 1) OVER (ORDER BY month)  AS prev_month,
    LEAD(revenue, 1) OVER (ORDER BY month) AS next_month,
    revenue - LAG(revenue, 1) OVER (ORDER BY month) AS month_over_month_growth,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / LAG(revenue) OVER (ORDER BY month), 2
    ) AS growth_percent
FROM monthly_sales;

-- ═══════════════════════════════════════
-- Running totals & moving averages
-- ═══════════════════════════════════════
SELECT
    order_date, amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total,
    AVG(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7day
FROM orders;

-- ═══════════════════════════════════════
-- NTILE: Divide into buckets
-- ═══════════════════════════════════════
SELECT name, salary,
    NTILE(4) OVER (ORDER BY salary) AS salary_quartile
FROM employees;
-- Divides employees into 4 equal groups by salary

-- ═══════════════════════════════════════
-- FIRST_VALUE, LAST_VALUE
-- ═══════════════════════════════════════
SELECT
    department, name, salary,
    FIRST_VALUE(name) OVER (
        PARTITION BY department ORDER BY salary DESC
    ) AS highest_paid_in_dept,
    salary - FIRST_VALUE(salary) OVER (
        PARTITION BY department ORDER BY salary DESC
    ) AS diff_from_top
FROM employees;
```

---

## 16.4 Indexes — Critical for Performance

### Q7: Explain indexes — types, when to use, when NOT to use.

```sql
-- ═══════════════════════════════════════
-- B-Tree Index (Default): Range queries, equality, sorting
-- ═══════════════════════════════════════
CREATE INDEX idx_users_email ON users(email);
-- Good for: WHERE email = '...', ORDER BY email, email LIKE 'abc%'
-- Bad for:  email LIKE '%abc' (leading wildcard)

-- ═══════════════════════════════════════
-- Composite Index: Multi-column (ORDER MATTERS!)
-- ═══════════════════════════════════════
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);
-- This index helps:
--   WHERE user_id = 5                         ✅ (leftmost column)
--   WHERE user_id = 5 AND created_at > '...'  ✅ (both columns)
--   WHERE user_id = 5 ORDER BY created_at DESC ✅
--
-- This index does NOT help:
--   WHERE created_at > '...'                   ❌ (skipped leftmost column!)

-- ═══════════════════════════════════════
-- Partial Index: Index only some rows
-- ═══════════════════════════════════════
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';
-- Smaller index, faster queries for active users only

-- ═══════════════════════════════════════
-- GIN Index: Full-text search, JSON, arrays
-- ═══════════════════════════════════════
CREATE INDEX idx_products_tags ON products USING GIN(tags);
-- For: WHERE tags @> ARRAY['electronics']

CREATE INDEX idx_data_json ON events USING GIN(metadata jsonb_path_ops);
-- For: WHERE metadata @> '{"type": "click"}'

-- ═══════════════════════════════════════
-- Unique Index: Enforce uniqueness
-- ═══════════════════════════════════════
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- ═══════════════════════════════════════
-- WHEN NOT TO INDEX
-- ═══════════════════════════════════════
-- Small tables (< 1000 rows) — full scan is faster
-- Columns with low cardinality (boolean, status with 3 values)
-- Tables with heavy writes and few reads
-- Columns rarely used in WHERE/JOIN/ORDER BY

-- EXPLAIN ANALYZE: Always verify your index is being used!
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
-- Look for "Index Scan" (good) vs "Seq Scan" (bad)
```

---

## 16.5 Transactions & Locking

### Q8: Explain database transactions and locking.

```sql
-- ═══════════════════════════════════════
-- Transaction: Group of operations that must all succeed or all fail
-- ═══════════════════════════════════════
BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
    -- If either fails, ROLLBACK undoes both
COMMIT;  -- Or ROLLBACK;

-- ═══════════════════════════════════════
-- Row-level locking: SELECT ... FOR UPDATE
-- ═══════════════════════════════════════
BEGIN;
    -- Lock the row — other transactions must wait
    SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;
    -- Now safely update
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- SKIP LOCKED: Process tasks without waiting (job queue pattern)
BEGIN;
    SELECT id, payload FROM tasks
    WHERE status = 'pending'
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED;     -- Skip rows locked by other workers!

    UPDATE tasks SET status = 'processing' WHERE id = ?;
COMMIT;
```

```python
# Python transaction example (SQLAlchemy)
from sqlalchemy.orm import Session

def transfer_money(session: Session, from_id: int, to_id: int, amount: float):
    """Atomic money transfer with proper locking."""
    try:
        # Lock rows in consistent order to prevent deadlocks
        accounts = (
            session.query(Account)
            .filter(Account.id.in_([from_id, to_id]))
            .order_by(Account.id)
            .with_for_update()        # SELECT ... FOR UPDATE
            .all()
        )

        from_acc = next(a for a in accounts if a.id == from_id)
        to_acc = next(a for a in accounts if a.id == to_id)

        if from_acc.balance < amount:
            raise ValueError("Insufficient funds")

        from_acc.balance -= amount
        to_acc.balance += amount

        session.commit()
    except Exception:
        session.rollback()
        raise
```

---

## 16.6 Scenario-Based Database Questions

### Scenario 1: "Design a schema for an e-commerce platform"

```sql
-- Users & Authentication
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Products with categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INT REFERENCES categories(id)   -- Hierarchical categories
);

CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_count INT NOT NULL DEFAULT 0,
    category_id INT REFERENCES categories(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_address JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,   -- Snapshot at time of order
    UNIQUE(order_id, product_id)
);

-- Indexes for common queries
CREATE INDEX idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status) WHERE status != 'delivered';
CREATE INDEX idx_products_category ON products(category_id) WHERE is_active;
CREATE INDEX idx_products_price ON products(price);
```

---

### Scenario 2: "Write a query to find customers who ordered every month in 2024"

```sql
WITH monthly_orders AS (
    SELECT
        user_id,
        DATE_TRUNC('month', created_at) AS order_month
    FROM orders
    WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
    GROUP BY user_id, DATE_TRUNC('month', created_at)
)
SELECT u.name, u.email, COUNT(DISTINCT mo.order_month) AS months_ordered
FROM users u
JOIN monthly_orders mo ON u.id = mo.user_id
GROUP BY u.id, u.name, u.email
HAVING COUNT(DISTINCT mo.order_month) = 12;   -- All 12 months
```

---

### Scenario 3: "Find the second highest salary in each department"

```sql
-- Using window function
WITH ranked AS (
    SELECT name, department, salary,
           DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rank
    FROM employees
)
SELECT name, department, salary
FROM ranked
WHERE rank = 2;

-- Without window function (older SQL)
SELECT e1.department, MAX(e1.salary) AS second_highest
FROM employees e1
WHERE e1.salary < (
    SELECT MAX(e2.salary) FROM employees e2
    WHERE e2.department = e1.department
)
GROUP BY e1.department;
```

---

## 16.7 SQL vs NoSQL — When to Use Which

```
SQL (PostgreSQL, MySQL):
  ✅ Structured, relational data
  ✅ ACID transactions (financial, critical)
  ✅ Complex queries with JOINs
  ✅ Data integrity (foreign keys, constraints)
  ❌ Schema changes are expensive
  ❌ Horizontal scaling is harder

NoSQL — Document (MongoDB):
  ✅ Flexible schema, rapid iteration
  ✅ Nested/hierarchical data
  ✅ Horizontal scaling (sharding)
  ❌ No JOINs (denormalize instead)
  ❌ Weaker consistency guarantees

NoSQL — Key-Value (Redis, DynamoDB):
  ✅ Extreme speed (in-memory)
  ✅ Caching, sessions, counters
  ✅ Simple access patterns
  ❌ No complex queries
  ❌ Limited data modeling

NoSQL — Column-Family (Cassandra):
  ✅ Massive write throughput
  ✅ Time-series data, IoT
  ✅ Multi-datacenter replication
  ❌ Complex to model
  ❌ Limited query flexibility

NoSQL — Graph (Neo4j):
  ✅ Relationships are first-class
  ✅ Social networks, recommendations
  ✅ Fraud detection, knowledge graphs
  ❌ Not for simple CRUD
  ❌ Smaller ecosystem

Decision: Start with PostgreSQL unless you have a specific reason not to.
PostgreSQL handles JSON (JSONB), full-text search, and scales well to
millions of rows. Add NoSQL for specific use cases.
```

---
