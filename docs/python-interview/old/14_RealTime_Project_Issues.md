# 14 — Real-Time Project Issues & Debugging
## Production War Stories — Interview Scenarios

> **Cross-reference:** File 03 (GIL, Memory), File 07 (Concurrency), File 08 (DB), File 09 (DevOps)

---

## 14.1 Production Crashes

### Scenario 1: "The Server Dies Every Friday at 6 PM"

**Interviewer:** "Our Django app crashes every Friday evening with OOM (Out of Memory). It runs fine on other days. Diagnose."

**Investigation flow:**
```
1. What happens Friday 6 PM? → Weekly report email goes out
2. Report query? → SELECT * FROM orders WHERE created_at > last_week
3. How many rows? → ~500K orders/week
4. How is it processed? → Loaded ALL into memory, rendered as HTML
```

```python
# ❌ ROOT CAUSE — loads 500K rows into memory
def generate_weekly_report():
    orders = Order.objects.filter(
        created_at__gte=last_week
    ).all()                                    # 500K objects in memory!

    html = render_template("report.html", orders=orders)   # Another copy!
    send_email(to="team@company.com", body=html)

# ✅ FIX 1: Use iterator/chunked processing
def generate_weekly_report_fixed():
    # Django's iterator() loads in chunks
    orders = Order.objects.filter(
        created_at__gte=last_week
    ).iterator(chunk_size=1000)

    # Stream to file instead of building in memory
    with open("/tmp/report.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Order ID", "Customer", "Total", "Date"])
        for order in orders:
            writer.writerow([order.id, order.customer, order.total, order.date])

    send_email_with_attachment("team@company.com", "/tmp/report.csv")

# ✅ FIX 2: Use database-level aggregation
def generate_weekly_summary():
    summary = Order.objects.filter(
        created_at__gte=last_week
    ).aggregate(
        total_revenue=Sum('total'),
        order_count=Count('id'),
        avg_order=Avg('total'),
    )
    # Only ONE row returned — minimal memory!
    send_email(to="team@company.com", body=format_summary(summary))

# ✅ FIX 3: Offload to background task
@celery_app.task
def generate_weekly_report_async():
    """Run in Celery worker — doesn't affect web server memory."""
    # ... process in chunks ...
    pass

# Schedule with Celery Beat
app.conf.beat_schedule = {
    'weekly-report': {
        'task': 'tasks.generate_weekly_report_async',
        'schedule': crontab(day_of_week=5, hour=18, minute=0),
    },
}
```

---

### Scenario 2: "API Responses Are Sometimes Stale"

**Interviewer:** "Users see outdated data after updating their profile. Sometimes it's instant, sometimes stale for minutes."

```python
# ═══════════════════════════════════════
# ROOT CAUSE: Cache invalidation issue with read replicas
# ═══════════════════════════════════════

# Architecture:
# App → Cache (Redis) → Primary DB (writes)
#                      → Replica DB (reads) ← Replication lag!

# ❌ PROBLEM
def update_profile(user_id, data):
    db.primary.update(user_id, data)      # Writes to primary
    cache.delete(f"user:{user_id}")        # Invalidates cache

def get_profile(user_id):
    cached = cache.get(f"user:{user_id}")
    if cached:
        return cached
    user = db.replica.get(user_id)         # Reads from replica
    # Replica might not have the update yet! (replication lag = 1-5 seconds)
    cache.set(f"user:{user_id}", user, ttl=300)
    return user

# ✅ FIX 1: Read-after-write from primary
def get_profile_fixed(user_id, force_primary=False):
    cached = cache.get(f"user:{user_id}")
    if cached and not force_primary:
        return cached

    # Use primary for recently updated users
    if force_primary or was_recently_updated(user_id):
        user = db.primary.get(user_id)
    else:
        user = db.replica.get(user_id)

    cache.set(f"user:{user_id}", user, ttl=300)
    return user

def update_profile_fixed(user_id, data):
    db.primary.update(user_id, data)
    user = db.primary.get(user_id)     # Read back from primary
    cache.set(f"user:{user_id}", user, ttl=300)  # Update cache directly
    mark_recently_updated(user_id, ttl=10)  # Flag for 10 seconds

def was_recently_updated(user_id):
    return cache.get(f"updated:{user_id}") is not None

def mark_recently_updated(user_id, ttl=10):
    cache.set(f"updated:{user_id}", "1", ttl=ttl)

# ✅ FIX 2: Write-through cache
def update_profile_write_through(user_id, data):
    db.primary.update(user_id, data)
    updated_user = db.primary.get(user_id)
    cache.set(f"user:{user_id}", updated_user, ttl=300)
    # Cache always has latest data — no stale reads
```

---

### Scenario 3: "500 Errors Spike During Deployments"

**Interviewer:** "Every time we deploy, we see a burst of 500 errors for 30 seconds. Users complain."

```python
"""
ROOT CAUSE: Deployment kills old processes before new ones are ready.

Investigation:
  1. Deploy happens → old processes receive SIGTERM
  2. Old processes die immediately → in-flight requests fail
  3. New processes start → take 10-30s to warm up (load models, establish DB connections)
  4. During warmup → new requests fail too

═══════════════════════════════════════
FIX: Graceful shutdown + Rolling deployment
═══════════════════════════════════════
"""

# 1. Graceful shutdown — finish in-flight requests
import signal
import asyncio

class GracefulShutdown:
    def __init__(self):
        self.is_shutting_down = False
        self._active_requests = 0

    def start_shutdown(self, signum, frame):
        self.is_shutting_down = True
        print(f"Received {signum}, finishing {self._active_requests} requests...")

    async def wait_for_completion(self, timeout=30):
        for _ in range(timeout * 10):
            if self._active_requests == 0:
                return
            await asyncio.sleep(0.1)
        print(f"Timeout: {self._active_requests} requests still active")

# FastAPI with graceful shutdown
"""
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await warm_up_connections()
    await preload_ml_models()
    yield
    # Shutdown
    await finish_active_requests(timeout=30)
    await close_db_connections()

app = FastAPI(lifespan=lifespan)
"""

# 2. Health check endpoint
"""
@app.get("/health")
async def health_check():
    if shutdown_handler.is_shutting_down:
        raise HTTPException(status_code=503, detail="Shutting down")

    db_ok = await check_db_connection()
    cache_ok = await check_redis_connection()

    if not (db_ok and cache_ok):
        raise HTTPException(status_code=503, detail="Dependencies unhealthy")

    return {"status": "healthy"}
"""

# 3. Kubernetes rolling deployment config
"""
# deployment.yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # Add 1 new pod before removing old
      maxUnavailable: 0     # Never have fewer pods than desired
  template:
    spec:
      containers:
      - name: app
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        terminationGracePeriodSeconds: 60
"""
```

---

### Scenario 4: "Database Connection Pool Exhausted"

**Interviewer:** "We get `too many connections` errors during peak hours. We have connection pooling configured."

```python
# ═══════════════════════════════════════
# ROOT CAUSE: Connection leak — connections not returned to pool
# ═══════════════════════════════════════

# ❌ CONNECTION LEAK
async def get_user(user_id):
    conn = await pool.acquire()
    result = await conn.fetch("SELECT * FROM users WHERE id=$1", user_id)
    # If an exception occurs above, connection is NEVER released!
    await pool.release(conn)
    return result

# ✅ FIX: Use context manager — guarantees release
async def get_user_fixed(user_id):
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM users WHERE id=$1", user_id)
    # Connection automatically released, even on exception

# ✅ SQLAlchemy session management
from contextlib import contextmanager

@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()         # ALWAYS close — returns connection to pool

# FastAPI dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ═══════════════════════════════════════
# Connection pool configuration
# ═══════════════════════════════════════
"""
SQLAlchemy pool settings:
  pool_size=10         # Steady-state connections
  max_overflow=20      # Extra connections under load (total max = 30)
  pool_timeout=30      # Wait time for a connection before error
  pool_recycle=1800    # Recycle connections after 30 min (avoid stale)
  pool_pre_ping=True   # Test connection before using

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
"""
```

---

### Scenario 5: "Celery Tasks Silently Failing"

**Interviewer:** "We dispatch 10,000 tasks to Celery daily. Some silently disappear. No errors logged."

```python
# ═══════════════════════════════════════
# COMMON CAUSES
# ═══════════════════════════════════════

# CAUSE 1: Worker crashes during task (acknowledgment before completion)
# ❌ Default: task acknowledged when RECEIVED, not when COMPLETED
# If worker crashes mid-task → task lost forever

# ✅ FIX: Late acknowledgment
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
app.conf.task_reject_on_worker_lost = True   # Requeue if worker dies

# CAUSE 2: Serialization failures
# ❌ Sending non-serializable objects
@app.task
def process(data):
    pass

process.delay(datetime.now())    # datetime isn't JSON-serializable by default!

# ✅ FIX: Convert to serializable format
process.delay(datetime.now().isoformat())

# CAUSE 3: No error handling in tasks
# ❌ Exception raised → task marked as failed → no retry
@app.task
def risky_task(data):
    result = external_api.call(data)     # Might fail!
    return result

# ✅ FIX: Retry with error handling
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def risky_task_fixed(self, data):
    try:
        result = external_api.call(data)
        return result
    except ConnectionError as exc:
        logger.warning(f"Task {self.request.id} failed: {exc}. Retrying...")
        self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error(f"Task {self.request.id} permanently failed: {exc}")
        # Send to dead letter queue or alert
        send_to_dlq(self.request.id, data, str(exc))
        raise

# CAUSE 4: Task result expiration
# ✅ FIX: Configure result backend
app.conf.result_expires = 86400  # Keep results for 24 hours

# MONITORING
# ✅ Use Flower for Celery monitoring
# pip install flower
# celery -A myapp flower --port=5555
```

---

### Scenario 6: "Slow Database Queries in Production"

**Interviewer:** "Some API endpoints take 15+ seconds. How do you identify and fix slow queries?"

```python
# ═══════════════════════════════════════
# Step 1: Identify slow queries
# ═══════════════════════════════════════

# Django: django-debug-toolbar + query logging
"""
# settings.py
LOGGING = {
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',   # Logs ALL SQL queries with timing
        },
    },
}
"""

# SQLAlchemy: Enable echo
# engine = create_engine(url, echo=True)

# PostgreSQL: pg_stat_statements
"""
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
"""

# ═══════════════════════════════════════
# Step 2: Common fixes
# ═══════════════════════════════════════

# FIX 1: Add missing indexes
"""
-- Before: Seq Scan on orders (15 seconds)
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_email = 'alice@test.com';

-- After: Index Scan (2 milliseconds)
CREATE INDEX idx_orders_email ON orders(customer_email);
"""

# FIX 2: Fix N+1 queries (See File 08, Q2)
# Django
posts = Post.objects.select_related('author').prefetch_related('tags')

# FIX 3: Pagination instead of loading all
# ❌ Bad
all_users = User.objects.all()    # 1 million users in memory!

# ✅ Good — keyset pagination (cursor-based)
def get_users_page(last_id=0, limit=50):
    return User.objects.filter(id__gt=last_id).order_by('id')[:limit]

# FIX 4: Denormalization for read-heavy queries
"""
-- Instead of JOIN every time:
SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id;

-- Add a counter column updated on write:
ALTER TABLE users ADD COLUMN order_count INT DEFAULT 0;
-- Update on new order via trigger or application code
"""

# FIX 5: Database query result caching
from django.core.cache import cache

def get_popular_products():
    cache_key = "popular_products"
    result = cache.get(cache_key)
    if result is None:
        result = Product.objects.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')[:10]
        result = list(result)
        cache.set(cache_key, result, timeout=300)   # 5 min cache
    return result
```

---

## 14.2 Security Incidents

### Scenario 7: "SQL Injection Found by Security Audit"

**Interviewer:** "Security team found SQL injection in our codebase. Show the vulnerability and fix."

```python
# ❌ VULNERABLE — string formatting in SQL
def search_users(name):
    query = f"SELECT * FROM users WHERE name = '{name}'"
    cursor.execute(query)

# Attack: name = "'; DROP TABLE users; --"
# Executed: SELECT * FROM users WHERE name = ''; DROP TABLE users; --'

# ✅ FIX: Parameterized queries
def search_users_safe(name):
    cursor.execute("SELECT * FROM users WHERE name = %s", (name,))

# ✅ With SQLAlchemy (always safe)
session.query(User).filter(User.name == name)

# ✅ For complex dynamic queries
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE name = :name AND age > :age")
result = session.execute(stmt, {"name": name, "age": min_age})
```

---
