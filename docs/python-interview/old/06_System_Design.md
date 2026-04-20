# 06 — System Design Interview
## Complete Questions with Python-Centric Examples

---

## 6.1 System Design Fundamentals

### Q1: Explain key concepts every system design interview covers.

**Answer:**

**Scalability:**
- Vertical scaling: Bigger machine (more CPU/RAM)
- Horizontal scaling: More machines (distributed)

**Load Balancing:**
```
Client → Load Balancer → [Server 1, Server 2, Server 3]
Algorithms: Round-robin, Least connections, IP hash, Weighted
Tools: Nginx, HAProxy, AWS ALB
```

**Caching:**
```
Client → Cache (Redis/Memcached) → Database
Strategies:
  - Cache-aside:   App checks cache first, loads from DB on miss
  - Write-through: Write to cache AND DB simultaneously
  - Write-behind:  Write to cache, async flush to DB
  - TTL:           Time-based expiration
```

**Database:**
```
SQL (PostgreSQL, MySQL):
  - ACID transactions, joins, structured data
  - Vertical scaling, read replicas

NoSQL (MongoDB, DynamoDB, Cassandra):
  - Flexible schema, horizontal scaling
  - Types: Document, Key-Value, Column-family, Graph

CAP Theorem: Pick 2 of 3:
  - Consistency: All nodes see same data
  - Availability: Every request gets a response
  - Partition tolerance: System works despite network failures
```

**Message Queues:**
```
Producer → Queue (Kafka/RabbitMQ/SQS) → Consumer
Use for: Async processing, decoupling, buffering spikes
```

**API Design:**
```
REST: Resource-based URLs, HTTP methods (GET, POST, PUT, DELETE)
GraphQL: Single endpoint, client specifies exact data needed
gRPC: Binary protocol, strongly typed, high performance
```

---

### Q2: Design a URL Shortener (like bit.ly)

**Answer:**

```python
"""
Requirements:
- Shorten long URLs → 7-char short code
- Redirect short URL to original
- Analytics (click count)
- Scale: 100M URLs, 1B redirects/month

Architecture:
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Client   │────▶│ Load Balancer │────▶│ App Servers│
└──────────┘     └──────────────┘     └─────┬──────┘
                                            │
                          ┌─────────────────┼─────────────┐
                          ▼                 ▼             ▼
                    ┌──────────┐     ┌──────────┐   ┌─────────┐
                    │  Redis    │     │PostgreSQL│   │Analytics │
                    │  Cache    │     │  (URLs)  │   │ (Kafka)  │
                    └──────────┘     └──────────┘   └─────────┘
"""

import hashlib
import string
import time
from dataclasses import dataclass

# Base62 encoding for short codes
CHARS = string.ascii_letters + string.digits  # 62 chars

def encode_base62(num: int) -> str:
    """Convert integer to base62 string."""
    if num == 0:
        return CHARS[0]
    result = []
    while num > 0:
        result.append(CHARS[num % 62])
        num //= 62
    return ''.join(reversed(result))

def generate_short_code(url: str, counter: int) -> str:
    """Generate unique 7-char short code."""
    # Method 1: Counter-based (guaranteed unique)
    return encode_base62(counter).zfill(7)

    # Method 2: Hash-based (check for collisions)
    # hash_val = hashlib.md5(url.encode()).hexdigest()[:7]

# Database Schema
"""
CREATE TABLE urls (
    id BIGSERIAL PRIMARY KEY,
    short_code VARCHAR(7) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    click_count BIGINT DEFAULT 0,
    expires_at TIMESTAMP
);
CREATE INDEX idx_short_code ON urls(short_code);
"""

# API Design
"""
POST /api/shorten
  Body: {"url": "https://very-long-url.com/page/article/123"}
  Response: {"short_url": "https://short.ly/abc1234", "expires": "2025-01-01"}

GET /:short_code
  → 301 Redirect to original URL
  → Background: increment click count via Kafka

GET /api/stats/:short_code
  Response: {"clicks": 1523, "created": "2024-01-01", "original_url": "..."}
"""

# Caching strategy:
# - Cache hot URLs in Redis (read-through cache)
# - 80/20 rule: 20% of URLs get 80% of traffic
# - TTL: 24 hours for cache entries
# - Cache: short_code → original_url

# Scale estimations:
# 100M URLs × 500 bytes avg = ~50 GB → fits in one PostgreSQL instance
# 1B redirects/month = ~400 reads/sec → Redis handles easily
# Write: 100M/month = ~40 writes/sec → PostgreSQL handles easily
```

---

### Q3: Design a Rate Limiter

**Answer:**

```python
"""
Requirements:
- Limit API requests per user/IP
- Configurable: 100 requests/minute
- Distributed (works across multiple servers)

Algorithms:
1. Fixed Window Counter
2. Sliding Window Log
3. Sliding Window Counter
4. Token Bucket ← Most common
5. Leaky Bucket
"""

import time
import threading
from collections import defaultdict

# ═══════════════════════════════════════
# Token Bucket Algorithm
# ═══════════════════════════════════════
class TokenBucket:
    """
    Tokens are added at a fixed rate.
    Each request consumes one token.
    If no tokens available → request rejected.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity          # Max tokens
        self.refill_rate = refill_rate    # Tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

# Usage
limiter = TokenBucket(capacity=10, refill_rate=1)  # 10 burst, 1/sec sustained

# ═══════════════════════════════════════
# Sliding Window Counter (Redis-based)
# ═══════════════════════════════════════
"""
Redis implementation for distributed rate limiting:

def is_allowed(user_id, limit=100, window=60):
    key = f"rate:{user_id}:{int(time.time()) // window}"
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    count = pipe.execute()[0]
    return count <= limit

# Or using sorted sets for precise sliding window:
def is_allowed_precise(user_id, limit=100, window=60):
    key = f"rate:{user_id}"
    now = time.time()
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)  # Remove old entries
    pipe.zadd(key, {str(now): now})               # Add current request
    pipe.zcard(key)                                # Count requests in window
    pipe.expire(key, window)                       # Auto-cleanup
    _, _, count, _ = pipe.execute()
    return count <= limit
"""

# ═══════════════════════════════════════
# Decorator for rate limiting in Python apps
# ═══════════════════════════════════════
class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = defaultdict(list)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = args[0] if args else "default"  # Use first arg as key
            now = time.time()
            # Remove old timestamps
            self.calls[key] = [t for t in self.calls[key] if now - t < self.period]
            if len(self.calls[key]) >= self.max_calls:
                raise Exception("Rate limit exceeded")
            self.calls[key].append(now)
            return func(*args, **kwargs)
        return wrapper

import functools

@RateLimiter(max_calls=5, period=60)
def api_call(user_id, data):
    return f"Processing {data} for {user_id}"
```

---

### Q4: Design a Task Queue System (like Celery)

**Answer:**

```python
"""
Components:
┌──────────┐     ┌──────────────┐     ┌──────────┐
│ Producer  │────▶│ Message Broker│────▶│  Worker   │
│ (Web App) │     │ (Redis/RabbitMQ)│   │ (Consumer)│
└──────────┘     └──────────────┘     └─────┬──────┘
                                            │
                                     ┌──────▼──────┐
                                     │Result Backend│
                                     │  (Redis/DB)  │
                                     └─────────────┘

Key Design Decisions:
- At-least-once delivery (with idempotency)
- Retry with exponential backoff
- Dead letter queue for failed tasks
- Priority queues
- Task routing (different queues for different task types)
- Horizontal scaling (add more workers)
"""

# Celery example — the standard Python task queue
"""
# tasks.py
from celery import Celery

app = Celery('myapp', broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/1')

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_order(self, order_id):
    try:
        order = fetch_order(order_id)
        charge_payment(order)
        send_confirmation(order)
        return {"status": "completed", "order_id": order_id}
    except PaymentError as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)

@app.task
def send_email(to, subject, body):
    # ... send email
    pass

# Usage
result = process_order.delay(order_id=123)       # Async
result = process_order.apply_async(
    args=[123],
    countdown=60,           # Delay 60 seconds
    queue='high-priority'
)
print(result.get(timeout=30))   # Wait for result

# Chaining tasks
from celery import chain, group, chord

# Sequential: A → B → C
workflow = chain(
    fetch_data.s(url),
    process_data.s(),
    store_results.s()
)
workflow.apply_async()

# Parallel: A, B, C all at once
job = group([
    process_chunk.s(chunk) for chunk in chunks
])
results = job.apply_async()

# Parallel then aggregate: (A, B, C) → D
workflow = chord(
    [process_chunk.s(c) for c in chunks],
    aggregate_results.s()
)
"""
```

---

### Q5: Design a Chat Application.

**Answer:**

```python
"""
Requirements:
- 1-to-1 and group messaging
- Online/offline status
- Message history
- Real-time delivery
- Read receipts
- File sharing

Architecture:
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client   │◄──▶│  WebSocket   │◄───▶│  Message      │
│  (React)  │    │  Gateway     │     │  Service      │
└──────────┘    └──────────────┘     └───────┬────────┘
                                             │
                    ┌────────────────────────┼───────────────┐
                    ▼                        ▼               ▼
              ┌──────────┐          ┌──────────────┐  ┌──────────┐
              │  Redis    │          │  Cassandra   │  │  S3      │
              │  PubSub   │          │  (Messages)  │  │  (Files) │
              │  + Presence│         └──────────────┘  └──────────┘
              └──────────┘

Data Model:
  messages: message_id, conversation_id, sender_id, content,
            timestamp, type (text/image/file), status

  conversations: conversation_id, participants[], type (1-1/group),
                 last_message_at

  user_status: user_id, status (online/offline), last_seen

Key Decisions:
  - WebSockets for real-time (not polling)
  - Cassandra for messages (write-heavy, time-series data)
  - Redis PubSub for cross-server message routing
  - Partition messages by conversation_id
  - Message ordering: server-assigned timestamps
  - Offline delivery: store and forward on reconnect

Scale:
  - 10M users, 1M concurrent
  - 1B messages/day = ~12K writes/sec → Cassandra handles easily
  - WebSocket connections: ~100K per server → 10 gateway servers
"""

# FastAPI + WebSocket example
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active[user_id] = ws

    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)

    async def send_to_user(self, user_id: str, message: dict):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(message)
        else:
            # User offline — store for later delivery
            store_offline_message(user_id, message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Route message to recipient
            await manager.send_to_user(
                data["to"],
                {"from": user_id, "content": data["content"],
                 "timestamp": time.time()}
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id)
"""
```

---

### Q6: How to handle database scaling?

**Answer:**

```
Read Replicas:
  Primary (writes) → Replica 1 (reads) → Replica 2 (reads)
  Use for: Read-heavy workloads (95% reads)

Sharding (Horizontal Partitioning):
  Shard 1: Users A-M    Shard 2: Users N-Z
  Strategies:
    - Hash-based:  shard = hash(user_id) % num_shards
    - Range-based: shard by date range or ID range
    - Directory:   lookup table maps key → shard

  Challenges:
    - Cross-shard queries (joins across shards)
    - Rebalancing when adding shards
    - Hotspots (uneven distribution)

Connection Pooling:
  App → Pool (10-20 connections) → Database
  Tools: PgBouncer (PostgreSQL), SQLAlchemy pool

Caching Layers:
  L1: Application cache (in-memory)
  L2: Distributed cache (Redis)
  L3: Database query cache

Indexing Strategy:
  - B-tree: Default, good for range queries
  - Hash: Exact match only, O(1)
  - GIN/GiST: Full-text search, JSON, arrays
  - Partial index: Index subset of rows
  - Composite index: Multi-column, order matters

  Rule: Index columns used in WHERE, JOIN, ORDER BY
  Tradeoff: Faster reads, slower writes, more storage
```

---

### Q7: Explain microservices vs monolith.

**Answer:**

```
Monolith:
  ┌─────────────────────────────────────┐
  │  Single Deployable Unit             │
  │  ┌─────┐ ┌──────┐ ┌────────────┐  │
  │  │Users│ │Orders│ │Notifications│  │
  │  └─────┘ └──────┘ └────────────┘  │
  │  Shared Database                    │
  └─────────────────────────────────────┘
  ✅ Simple deployment, easier debugging
  ✅ No network overhead between modules
  ❌ Hard to scale individual components
  ❌ Single point of failure
  ❌ Technology lock-in

Microservices:
  ┌──────┐   ┌───────┐   ┌──────────────┐
  │User  │   │Order  │   │Notification  │
  │Service│  │Service│   │Service       │
  │PostgreSQL│ │MongoDB│  │Redis+Kafka   │
  └──────┘   └───────┘   └──────────────┘
       ↕ API Gateway / Service Mesh ↕
  ✅ Independent scaling, deployment, technology
  ✅ Fault isolation
  ✅ Team autonomy
  ❌ Network complexity, latency
  ❌ Data consistency challenges
  ❌ Operational overhead (monitoring, logging, tracing)

Communication:
  Synchronous: REST, gRPC (request/response)
  Asynchronous: Kafka, RabbitMQ (event-driven)

Python Frameworks for Microservices:
  - FastAPI: High-performance REST APIs
  - gRPC: google.protobuf + grpcio
  - Celery + Kafka: Async task processing
  - Nameko: Python microservices framework
```

---
