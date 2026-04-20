# 23 — Enhanced Questions: Database, System Design & Microservices
## Most Important Missing Questions for Files 06, 08, 16, 17, 18

---

## 23.1 DATABASE ADDITIONS

### Q1: What is Database Normalization? Explain 1NF, 2NF, 3NF.

```
1NF (First Normal Form):
  ✅ Each column has atomic (indivisible) values
  ✅ No repeating groups
  ❌ Bad:  |Name|Phones         |
           |Alice|123-456, 789-012|   ← Multiple values in one cell
  ✅ Good: |Name|Phone   |
           |Alice|123-456|
           |Alice|789-012|

2NF (Second Normal Form):
  ✅ Is in 1NF
  ✅ Every non-key column depends on the ENTIRE primary key
  ❌ Bad: Table(student_id, course_id, student_name, grade)
          student_name depends only on student_id, not the full key
  ✅ Fix: Split into Students(student_id, student_name) and
          Enrollments(student_id, course_id, grade)

3NF (Third Normal Form):
  ✅ Is in 2NF
  ✅ No transitive dependencies (non-key depends on non-key)
  ❌ Bad: Employee(id, department_id, department_name)
          department_name depends on department_id, not on employee id
  ✅ Fix: Employee(id, department_id) and Department(department_id, name)

Denormalization — intentionally breaking normalization for performance:
  - Read-heavy systems (analytics, dashboards)
  - Avoid expensive JOINs
  - Example: Store order_total in orders table instead of computing SUM(items)
```

### Q2: Explain ACID vs BASE.

```
ACID (SQL databases — strong consistency):
  Atomicity:    All or nothing
  Consistency:  Valid state to valid state
  Isolation:    Concurrent transactions don't interfere
  Durability:   Committed data persists

BASE (NoSQL databases — eventual consistency):
  Basically Available: System always responds (may be stale)
  Soft state:         State may change over time without input
  Eventually consistent: System will become consistent given time

When to choose:
  ACID → Banking, inventory, e-commerce orders (data integrity critical)
  BASE → Social media feeds, analytics, caching (can tolerate staleness)
```

### Q3: What is a Deadlock in databases? How to prevent it?

```sql
-- Deadlock scenario:
-- Transaction 1: UPDATE accounts SET balance=100 WHERE id=1; (locks row 1)
--                UPDATE accounts SET balance=200 WHERE id=2; (waits for row 2)
-- Transaction 2: UPDATE accounts SET balance=300 WHERE id=2; (locks row 2)
--                UPDATE accounts SET balance=400 WHERE id=1; (waits for row 1)
-- → DEADLOCK! Both waiting for each other.

-- Prevention:
-- 1. Always lock resources in the same order
-- 2. Use timeouts
-- 3. Keep transactions short
-- 4. Use SELECT FOR UPDATE NOWAIT

BEGIN;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE NOWAIT;
-- If row is locked, raises error immediately instead of waiting
```

### Q4: What are Views, Stored Procedures, and Triggers?

```sql
-- VIEW: Virtual table (saved query)
CREATE VIEW active_users AS
SELECT id, name, email FROM users WHERE status = 'active';
-- Usage: SELECT * FROM active_users;
-- Benefits: Simplify complex queries, security (restrict column access)

-- MATERIALIZED VIEW: Cached result (faster reads, needs refresh)
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT DATE_TRUNC('month', order_date) AS month, SUM(total) AS revenue
FROM orders GROUP BY month;
-- REFRESH MATERIALIZED VIEW monthly_revenue;

-- STORED PROCEDURE: Server-side logic
CREATE FUNCTION transfer_funds(from_id INT, to_id INT, amount DECIMAL)
RETURNS VOID AS $$
BEGIN
    UPDATE accounts SET balance = balance - amount WHERE id = from_id;
    UPDATE accounts SET balance = balance + amount WHERE id = to_id;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: Automatic action on data change
CREATE TRIGGER update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
```

### Q5: Explain query optimization — how to read EXPLAIN ANALYZE.

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_email = 'test@example.com';

-- Key things to look for:
-- 1. Seq Scan → BAD for large tables (reads every row)
-- 2. Index Scan → GOOD (uses index)
-- 3. Actual time → Real execution time
-- 4. Rows → How many rows scanned vs returned

-- OPTIMIZATION CHECKLIST:
-- ✅ Add index on columns in WHERE, JOIN, ORDER BY
-- ✅ Use LIMIT for pagination
-- ✅ Avoid SELECT * — select only needed columns
-- ✅ Use EXISTS instead of IN for subqueries
-- ✅ Avoid functions on indexed columns: WHERE YEAR(date) = 2024 → BAD
--    Use: WHERE date >= '2024-01-01' AND date < '2025-01-01' → GOOD
-- ✅ Use EXPLAIN ANALYZE to verify index usage
-- ✅ Consider partial indexes for filtered queries
-- ✅ Batch INSERT/UPDATE instead of row-by-row
```

### Q6: What is Connection Pooling? Why is it important?

```python
"""
Without pooling:
  Each request → Open new connection → Execute query → Close connection
  Problem: Opening a connection takes ~50ms! Multiply by 1000 requests/sec...

With pooling:
  App → Pool of 20 pre-opened connections → Reuse connections
  Each request borrows a connection, uses it, returns it to pool.

SQLAlchemy pool configuration:
"""
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,          # Steady-state connections
    max_overflow=20,       # Extra connections under load
    pool_timeout=30,       # Wait time for connection
    pool_recycle=1800,     # Recycle connections after 30 min
    pool_pre_ping=True,    # Test connection before using
)

# Total max connections = pool_size + max_overflow = 30
```

---

## 23.2 SYSTEM DESIGN ADDITIONS

### Q7: Design a Social Media News Feed (like Twitter/Facebook).

```
Requirements:
  - User posts content
  - User sees posts from people they follow
  - Sorted by time (latest first)
  - Scale: 100M users, 10K posts/sec

Two approaches:

1. PULL MODEL (Fan-out on read):
   User opens feed → Query all followed users' posts → Merge & sort
   ✅ Simple to implement
   ❌ Slow for users following 1000+ people
   ❌ High read cost

2. PUSH MODEL (Fan-out on write): ← Preferred
   User posts → Push post to ALL followers' feed caches
   ✅ Fast reads (feed is pre-computed)
   ❌ Expensive writes for celebrities (10M followers)
   ❌ Wasted work for inactive users

3. HYBRID (Best approach):
   - Regular users: Push model (write to followers' caches)
   - Celebrities (>100K followers): Pull model (merge at read time)

Architecture:
  Post Service → Kafka → Fan-out Service → Redis (per-user feed)
  Read: User → Redis (pre-computed feed) + merge celebrity posts
  
  Feed Cache (Redis): Sorted Set per user
    Key: feed:{user_id}
    Value: Sorted set of {post_id: timestamp}
    ZREVRANGE feed:123 0 20  → Get latest 20 posts
```

### Q8: Design a Notification System.

```
Requirements:
  - Push, email, SMS, in-app
  - Priority levels
  - User preferences (opt-out)
  - Scale: 1M notifications/hour

Architecture:
  Event → Notification Service → Priority Queue → Channel Workers
                                    ↓
                              Template Engine
                                    ↓
                        ┌───────────┼───────────┐
                        ▼           ▼           ▼
                    Email Worker  SMS Worker  Push Worker
                    (SendGrid)   (Twilio)    (Firebase)

Key Design Decisions:
  1. Message queue (Kafka/SQS) for reliability and rate control
  2. Priority queues: urgent (immediate), high (minutes), low (batch)
  3. User preferences table: check before sending
  4. Template system: avoid hardcoded content
  5. Deduplication: Don't send same notification twice
  6. Rate limiting: Max 10 emails/hour per user
  7. Dead letter queue: Failed notifications for retry/investigation
```

### Q9: Explain CAP Theorem with real examples.

```
CAP Theorem: In a distributed system, you can only guarantee 2 of 3:
  C (Consistency): Every read gets the most recent write
  A (Availability): Every request gets a response
  P (Partition tolerance): System works despite network failures

Since network partitions ALWAYS happen in distributed systems,
the real choice is: CP or AP

CP (Consistency + Partition tolerance):
  → Some requests may fail during partition
  → Examples: PostgreSQL, MongoDB (default), Redis Cluster, HBase
  → Use for: Banking, inventory, elections — correctness matters

AP (Availability + Partition tolerance):
  → Every request gets a response (may be stale)
  → Examples: Cassandra, DynamoDB, CouchDB
  → Use for: Social media feeds, product catalog, DNS

Real-world: Most systems are "tunable"
  - DynamoDB: Configure read consistency (strong vs eventual)
  - MongoDB: Configure read/write concern
  - Cassandra: Tune consistency level per query
```

---

## 23.3 FASTAPI & API ADDITIONS

### Q10: REST API design best practices — most asked.

```
URL Design:
  ✅ Use nouns, not verbs: /users, /orders
  ❌ Bad: /getUsers, /createOrder
  
  ✅ Use plural: /users/123, /users/123/orders
  ❌ Bad: /user/123
  
  ✅ Use HTTP methods for actions:
     GET /users       → List users
     POST /users      → Create user
     GET /users/123   → Get specific user
     PUT /users/123   → Replace user
     PATCH /users/123 → Partial update
     DELETE /users/123 → Delete user

Status Codes:
  200 OK            → Successful GET/PUT/PATCH
  201 Created       → Successful POST
  204 No Content    → Successful DELETE
  400 Bad Request   → Invalid input
  401 Unauthorized  → Not authenticated
  403 Forbidden     → Authenticated but no permission
  404 Not Found     → Resource doesn't exist
  409 Conflict      → Duplicate resource
  422 Unprocessable → Validation error (FastAPI default)
  429 Too Many Req  → Rate limited
  500 Internal Error → Server bug

Pagination:
  GET /users?page=2&per_page=20
  Response: { "data": [...], "total": 150, "page": 2, "per_page": 20 }
  
  Or cursor-based (better for large datasets):
  GET /users?cursor=abc123&limit=20
  Response: { "data": [...], "next_cursor": "def456" }

Versioning:
  URL: /api/v1/users (most common)
  Header: Accept: application/vnd.myapi.v2+json

Filtering & Sorting:
  GET /products?category=electronics&sort=-price&min_price=100
```

### Q11: What is OAuth2? How does JWT authentication work?

```python
"""
OAuth2 Flow (simplified):
  1. User clicks "Login with Google"
  2. Redirect to Google's auth page
  3. User authorizes your app
  4. Google redirects back with authorization code
  5. Your server exchanges code for access token
  6. Use access token to get user info from Google

JWT (JSON Web Token):
  Header.Payload.Signature (base64 encoded, dot-separated)
  
  Header:  {"alg": "HS256", "typ": "JWT"}
  Payload: {"sub": "user123", "name": "Alice", "exp": 1234567890}
  Signature: HMACSHA256(header + "." + payload, secret_key)
  
  Stateless: Server doesn't need to store session. Token contains all info.
  Verify: Server checks signature with secret key.
"""

from jose import jwt
from datetime import datetime, timedelta

SECRET = "your-secret-key"
ALGORITHM = "HS256"

def create_token(user_id: int, expires_hours: int = 24) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")
```

---

## 23.4 MICROSERVICES ADDITIONS

### Q12: Explain Event-Driven Architecture in detail.

```python
"""
Event-Driven Architecture:
  Services communicate by publishing and subscribing to events.
  No direct service-to-service calls for async operations.

Event Types:
  1. Domain Event:  "OrderPlaced", "UserRegistered"
  2. Integration Event: Cross-service event published to message bus
  3. Command Event:  "ProcessPayment", "SendEmail" (directed at specific service)

Benefits:
  ✅ Loose coupling — services don't know about each other
  ✅ Scalability — add consumers independently
  ✅ Resilience — publisher doesn't care if consumer is down
  ✅ Audit trail — events are a log of what happened

Challenges:
  ❌ Eventual consistency
  ❌ Event ordering
  ❌ Debugging across services
  ❌ Idempotency required (same event processed twice)
"""

# Event schema example
"""
{
    "event_id": "uuid-123",
    "event_type": "order.placed",
    "timestamp": "2024-03-15T10:30:00Z",
    "version": "1.0",
    "source": "order-service",
    "data": {
        "order_id": 456,
        "user_id": 789,
        "items": [...],
        "total": 99.99
    },
    "metadata": {
        "correlation_id": "req-abc-123",
        "causation_id": "evt-xyz-789"
    }
}
"""

# Idempotent consumer pattern
"""
class OrderEventHandler:
    def __init__(self, db, processed_events_cache):
        self.db = db
        self.cache = processed_events_cache
    
    async def handle(self, event):
        # Check if already processed (idempotency)
        if await self.cache.exists(event['event_id']):
            logger.info(f"Event {event['event_id']} already processed, skipping")
            return
        
        # Process event
        await self.process_order(event['data'])
        
        # Mark as processed
        await self.cache.set(event['event_id'], '1', ttl=86400)
"""
```

### Q13: What is Service Mesh? Explain Istio/Linkerd.

```
Service Mesh: Infrastructure layer that handles service-to-service communication.

Without Service Mesh:
  Each service handles: retries, circuit breaking, TLS, tracing, load balancing
  → Code duplication, inconsistency, complex libraries

With Service Mesh:
  Sidecar proxy (Envoy) runs alongside each service
  Handles ALL networking concerns transparently

┌─────────────────────────────────┐
│         Service A               │
│  ┌──────┐    ┌──────────────┐   │
│  │ App  │←──→│ Sidecar Proxy│   │
│  └──────┘    └──────┬───────┘   │
└─────────────────────┼───────────┘
                      │ (encrypted, load-balanced, traced)
┌─────────────────────┼───────────┐
│         Service B   │           │
│  ┌──────┐    ┌──────┴───────┐   │
│  │ App  │←──→│ Sidecar Proxy│   │
│  └──────┘    └──────────────┘   │
└─────────────────────────────────┘

Features:
  - mTLS encryption (zero-trust security)
  - Automatic retries and circuit breaking
  - Load balancing (round-robin, least connections)
  - Distributed tracing (Jaeger/Zipkin integration)
  - Traffic management (canary deployments, A/B testing)
  - Rate limiting

When to use: Large deployments (50+ microservices)
When NOT to use: Small teams, few services (adds operational complexity)
```

### Q14: Explain the Outbox Pattern for reliable event publishing.

```python
"""
Problem: How to update database AND publish event atomically?

❌ Naive approach:
    1. Save order to database
    2. Publish "order.created" to Kafka
    → If step 2 fails, database has order but no event was published!

✅ Outbox Pattern:
    1. Save order + event to SAME database (in one transaction)
    2. Separate process reads outbox table and publishes to Kafka
    3. Mark as published

    This guarantees: If order is saved, event will eventually be published.
"""

# Step 1: Write to DB + Outbox in one transaction
"""
BEGIN;
    INSERT INTO orders (id, user_id, total) VALUES (1, 42, 99.99);
    
    INSERT INTO outbox (
        id, event_type, payload, created_at, published
    ) VALUES (
        'uuid-123', 'order.created',
        '{"order_id": 1, "user_id": 42, "total": 99.99}',
        NOW(), false
    );
COMMIT;
"""

# Step 2: Background worker publishes events
"""
async def outbox_publisher():
    while True:
        events = await db.fetch(
            "SELECT * FROM outbox WHERE published = false ORDER BY created_at LIMIT 100"
        )
        for event in events:
            try:
                await kafka.publish(event['event_type'], event['payload'])
                await db.execute(
                    "UPDATE outbox SET published = true WHERE id = $1", event['id']
                )
            except Exception as e:
                logger.error(f"Failed to publish event {event['id']}: {e}")
        
        await asyncio.sleep(1)  # Poll interval
"""
```

---

## 23.5 TESTING ADDITIONS

### Q15: What is the difference between Unit, Integration, and E2E tests?

```python
"""
Testing Pyramid:
         /  E2E   \         ← Few, slow, expensive
        / Integration\      ← Some, medium speed
       /    Unit Tests \    ← Many, fast, cheap

Unit Test:
  - Tests ONE function/method in isolation
  - Mocks all dependencies
  - Fast (milliseconds)
  - Example: test_calculate_discount()

Integration Test:
  - Tests interaction between components
  - Uses real database/cache (test instance)
  - Medium speed (seconds)
  - Example: test_create_user_saves_to_db()

E2E Test:
  - Tests entire user flow
  - Uses real browser/API client
  - Slow (seconds-minutes)
  - Example: test_user_signup_to_purchase_flow()
"""

# Unit test example
def test_calculate_discount():
    assert calculate_discount(100, 0.2) == 80
    assert calculate_discount(50, 0) == 50
    assert calculate_discount(0, 0.5) == 0

# Integration test example
def test_create_user_in_database(db_session):
    user = UserService(db_session).create(name="Alice", email="a@test.com")
    
    saved = db_session.query(User).filter(User.email == "a@test.com").first()
    assert saved is not None
    assert saved.name == "Alice"

# What to test at 9 years experience level:
# - Edge cases (empty input, None, boundaries)
# - Error paths (exceptions, invalid input)
# - Concurrency issues
# - Performance characteristics
# - Security (SQL injection, XSS)
```

---
