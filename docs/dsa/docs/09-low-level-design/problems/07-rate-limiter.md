# Design a Rate Limiter

> Cap requests per client per window. The LLD problem that doubles as a systems-design conversation. Asked at any company with an API gateway.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design a rate limiter. Given a client identifier, decide if a request should be allowed or rejected based on a configured limit (e.g. 100 req / minute). Discuss algorithm trade-offs and distributed deployment."*

A 30-45 minute LLD round. Interviewer expects:

1. **Clarifying questions** (per-client? distributed? burst tolerance?).
2. **Multiple algorithms** discussed: fixed window / sliding window / leaky bucket / token bucket.
3. **Code** for at least one (token bucket is the canonical pick).
4. **Distributed extension**: how to scale across N gateways.

---

## ❓ Clarifying questions

1. **Granularity?** Per-IP? Per-user? Per-API-key?
2. **Limits?** 100/min global, or per-endpoint?
3. **Bursts allowed?** Token bucket lets bursts up to capacity; sliding window doesn't.
4. **Distributed?** Single gateway or many behind a load balancer?
5. **Latency budget?** ≤1ms? Affects whether we use Redis or local memory.
6. **Failure mode?** Fail-open (let traffic through) or fail-closed (reject)?

**Default assumptions**:

- Per-client (API key); 100 req/min per client.
- Token bucket (allows bursts, smooth refill).
- Distributed via Redis with atomic ops.
- Fail-open on Redis outage (we'd rather over-serve than 503-storm).

---

## 🏛️ Algorithm comparison

| Algorithm | Pros | Cons | Memory / client |
|---|---|---|---|
| **Fixed window** | Simplest | Boundary spike (200 req at second 59→01) | 1 counter |
| **Sliding log** | Exact | O(N) memory + log purge | All timestamps |
| **Sliding window counter** | Smooth, cheap | Approximation only | 2 counters |
| **Leaky bucket** | Constant rate out | No burst tolerance | 1 counter + rate |
| **Token bucket** | Bursts allowed up to capacity | More state | 2 floats (tokens + last_ts) |

**Recommendation**: **token bucket** for general APIs (the standard at AWS, Stripe, Cloudflare).

---

## 🔧 Code — Strategy pattern over algorithms

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections import defaultdict, deque
import time
import threading


class RateLimitStrategy(ABC):
    @abstractmethod
    def allow(self, client_id: str) -> bool: ...
```

### Fixed window

```python
class FixedWindowLimiter(RateLimitStrategy):
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.counts: dict[str, tuple[int, int]] = {}     # client → (window_start, count)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = int(time.time())
        bucket = now // self.window
        with self._lock:
            ws, count = self.counts.get(client_id, (bucket, 0))
            if ws != bucket:
                ws, count = bucket, 0
            if count >= self.limit:
                self.counts[client_id] = (ws, count)
                return False
            self.counts[client_id] = (ws, count + 1)
            return True
```

### Sliding window log (exact, expensive)

```python
class SlidingLogLimiter(RateLimitStrategy):
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.logs: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        with self._lock:
            log = self.logs[client_id]
            while log and log[0] < cutoff:
                log.popleft()
            if len(log) >= self.limit:
                return False
            log.append(now)
            return True
```

### Token bucket — the canonical pick

```python
@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class TokenBucketLimiter(RateLimitStrategy):
    """capacity = max burst; refill_rate = tokens/sec."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = time.time()
        with self._lock:
            b = self.buckets.get(client_id)
            if b is None:
                b = _Bucket(tokens=self.capacity, last_refill=now)
                self.buckets[client_id] = b

            # Lazy refill — only when checked
            elapsed = now - b.last_refill
            b.tokens = min(self.capacity, b.tokens + elapsed * self.refill_rate)
            b.last_refill = now

            if b.tokens >= 1:
                b.tokens -= 1
                return True
            return False
```

??? note "Why lazy refill?"

    A background thread refilling every bucket every tick wastes CPU and doesn't scale. **Refill on read** is O(1) per request, exact, and scales linearly with active clients.

### Leaky bucket

```python
class LeakyBucketLimiter(RateLimitStrategy):
    """Constant outflow rate; rejects if bucket would overflow."""

    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.buckets: dict[str, _Bucket] = {}    # tokens here = current fill
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = time.time()
        with self._lock:
            b = self.buckets.get(client_id) or _Bucket(0.0, now)
            elapsed = now - b.last_refill
            b.tokens = max(0.0, b.tokens - elapsed * self.leak_rate)
            b.last_refill = now
            if b.tokens + 1 > self.capacity:
                self.buckets[client_id] = b
                return False
            b.tokens += 1
            self.buckets[client_id] = b
            return True
```

### The gateway (Facade)

```python
class RateLimiter:
    """Top-level service; one strategy, configurable per route."""

    def __init__(self, strategy: RateLimitStrategy):
        self.strategy = strategy

    def check(self, client_id: str) -> bool:
        return self.strategy.allow(client_id)
```

---

## 🌐 Distributed rate limiting

A single gateway is easy. **Multiple gateways behind a load balancer** is the real interview question.

### Approach 1: Redis with atomic operations

Token bucket in Redis using a **Lua script** for atomicity:

```python
LUA_TOKEN_BUCKET = """
local key       = KEYS[1]
local now       = tonumber(ARGV[1])
local capacity  = tonumber(ARGV[2])
local refill    = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last   = tonumber(bucket[2]) or now

local elapsed = now - last
tokens = math.min(capacity, tokens + elapsed * refill)

local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, 3600)
return allowed
"""
```

The `EVAL` is **single-threaded inside Redis** → atomic without distributed locks.

### Approach 2: Local + global hybrid

- Each gateway gets a **local quota** = `total_limit / N_gateways`.
- Local check is hot-path (sub-ms).
- A **slow drift sync** every few seconds rebalances if some gateways under-use.
- Trade-off: slight overshoot (each gateway drains its share independently).

### Approach 3: Sticky routing

Route all requests for a client to the same gateway via consistent hashing. Each gateway then does local rate limiting. Simpler than #1 but loses on rebalances.

---

## 🧪 Walkthrough

```python
limiter = RateLimiter(TokenBucketLimiter(capacity=10, refill_rate=1.0))
# 10 burst, refills 1/sec → steady-state 60/min

# 10 quick requests succeed (drains bucket)
for _ in range(10):
    assert limiter.check("client-A")
# 11th immediately → False
assert not limiter.check("client-A")
# Wait 2 seconds → 2 tokens regenerated
time.sleep(2)
assert limiter.check("client-A")
assert limiter.check("client-A")
assert not limiter.check("client-A")
```

---

## 🎯 Patterns + SOLID applied

| Decision | Pattern / principle |
|---|---|
| `RateLimitStrategy` ABC + 4 impls | **Strategy** + OCP — swap algorithm without touching gateway |
| Lazy refill | Pull-based; no scheduler thread |
| `RateLimiter` is a thin facade | **Facade** |
| Atomic Lua in distributed mode | Avoids the read-modify-write race |
| `_Bucket` dataclass | DRY across token + leaky |

---

## 🚀 Extensions

??? question "Per-endpoint vs per-client limits?"

    Compose two limiters: `key = f\"{endpoint}:{client_id}\"` for endpoint-specific limits *and* `key = client_id` for global. Reject if either denies.

??? question "Tiered limits (free / paid / enterprise)?"

    `Limiter` factory keyed on plan: `get_limiter(plan).check(client_id)`. Configuration-driven so ops can tune without deploys.

??? question "What if Redis is down?"

    Two paths: **fail-open** (let traffic through, log alert) or **fail-closed** (reject all). Most APIs choose fail-open. Use a circuit breaker so we don't hammer Redis during the outage.

??? question "How do you tell a client they're being limited?"

    HTTP `429 Too Many Requests` + `Retry-After: <seconds>` header + `X-RateLimit-Remaining: 0`. Stripe-style headers earn the senior signal.

??? question "What about millions of clients — memory blow-up?"

    Local: LRU-evict idle buckets. Redis: TTL on each key (1h ≫ window). Don't keep state for clients you haven't seen recently.

??? question "Smooth rolling window without log-storage?"

    **Sliding window counter approximation**: `count = current_count + previous_count * (1 - elapsed_in_current/window)`. Two counters per client; ~99% accurate; constant memory. Cloudflare's published approach.

---

## ⏱️ Pacing

| Minute | What |
|---|---|
| 0–3   | Clarifying questions. |
| 3–8   | Algorithm comparison table on whiteboard. Pick one. |
| 8–25  | Code token bucket + Strategy ABC. |
| 25–35 | Distributed: Redis Lua sketch. |
| 35–45 | Q&A; failure modes, headers. |

---

## 🪤 Common mistakes

??? warning "Refilling tokens via background thread"

    O(N) cost per tick. Use lazy refill on read. `tokens += elapsed * rate`.

??? warning "Race between `read tokens / decrement / write` in distributed mode"

    Without atomicity, two gateways both see 1 token, both decrement, both allow. Use Redis Lua / `INCR` / DynamoDB conditional writes.

??? warning "Stringly-typed strategy selection"

    `if algo == \"token_bucket\": ...` is OCP-violating. Use the ABC.

??? warning "Forgetting to free bucket entries for inactive clients"

    Unbounded growth. LRU + TTL.

??? warning "Treating fixed-window as good enough"

    The boundary spike (2× limit at the boundary) is a real production bug. Acknowledge it; pick sliding window or token bucket.

---

## ➡️ Where this connects

- [Hash table basics](../../02-data-structures/hash-tables/01-hash-table-basics.md) — bucket maps.
- [Design patterns](../03-design-patterns.md) — Strategy, Facade.
- [System Design overview](../../08-system-design/index.md) — rate limiting is a recurring SD building block.
- Other LLD: [LRU Cache](03-lru-cache.md) (similar lazy-eviction trick).
