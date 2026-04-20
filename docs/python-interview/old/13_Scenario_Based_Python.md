# 13 — Scenario-Based Python Questions (Basic to Advanced)
## Real Interview Scenarios with Solutions

> **Cross-reference:** For foundational concepts used in these scenarios, see Files 01–03.

---

## 13.1 Basic Scenarios

### Scenario 1: The Mysterious List Bug

**Interviewer:** "A junior developer wrote this function. Users report that adding items to one shopping cart affects another user's cart. Find and fix the bug."

```python
# ❌ BUGGY CODE
class ShoppingCart:
    def __init__(self, items=[]):
        self.items = items

    def add_item(self, item):
        self.items.append(item)
        return self.items

# Reproduction
cart1 = ShoppingCart()
cart1.add_item("Laptop")
print(cart1.items)            # ['Laptop']

cart2 = ShoppingCart()
print(cart2.items)            # ['Laptop'] ← BUG! cart2 already has cart1's item!
cart2.add_item("Phone")
print(cart1.items)            # ['Laptop', 'Phone'] ← BUG! cart1 got cart2's item!
```

**Root Cause:** Mutable default argument `items=[]` is shared across ALL instances. The list is created ONCE when the function is defined, not per call. *(See File 01, Q2 — mutable vs immutable)*

```python
# ✅ FIXED CODE
class ShoppingCart:
    def __init__(self, items=None):
        self.items = items if items is not None else []

    def add_item(self, item):
        self.items.append(item)
        return self.items

# Now works correctly
cart1 = ShoppingCart()
cart1.add_item("Laptop")
cart2 = ShoppingCart()
print(cart2.items)    # [] ← Correct! Independent list
```

**Follow-up question:** "Why did we use `items if items is not None` instead of `items or []`?"

```python
# Because `or` treats empty list as falsy!
items = []
result = items or []   # Returns NEW empty list — ignores the passed empty list!

# `is not None` correctly handles empty lists
items = []
result = items if items is not None else []   # Returns the SAME empty list — correct!
```

---

### Scenario 2: Dictionary Key Confusion

**Interviewer:** "A developer stores configuration using tuples as keys. This works fine, but when they switched to lists, it broke. Why?"

```python
# ✅ Works — tuples are hashable (immutable)
config = {}
config[(1920, 1080)] = "Full HD"
config[(3840, 2160)] = "4K"
print(config[(1920, 1080)])    # "Full HD"

# ❌ Fails — lists are NOT hashable (mutable)
config[[1920, 1080]] = "Full HD"
# TypeError: unhashable type: 'list'
```

**Explanation:** Dictionary keys must be hashable. Hashability requires immutability because if a key's value changed after insertion, it would be in the wrong hash bucket and become unfindable. *(See File 01, Q2)*

**Follow-up:** "How would you make a custom class usable as a dict key?"

```python
class Resolution:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __hash__(self):
        return hash((self.width, self.height))

    def __eq__(self, other):
        return isinstance(other, Resolution) and \
               self.width == other.width and self.height == other.height

config = {}
config[Resolution(1920, 1080)] = "Full HD"
print(config[Resolution(1920, 1080)])   # "Full HD"
```

---

### Scenario 3: The Silent Data Loss

**Interviewer:** "This function processes a CSV and should return the total revenue. It returns 0 for some files. Debug it."

```python
# ❌ BUGGY CODE
def calculate_revenue(filepath):
    total = 0
    with open(filepath) as f:
        for line in f:
            parts = line.strip().split(",")
            price = parts[2]
            quantity = parts[3]
            total += price * quantity      # Bug is here!
    return total

# CSV: product,category,price,quantity
# Widget,Electronics,29.99,5
```

**Root cause:** `price` and `quantity` are STRINGS (from CSV parsing). `"29.99" * "5"` raises `TypeError`, but if quantity is an integer string like `"5"`, then `price * quantity` does string repetition: `"29.99" * 5 = "29.9929.9929.9929.9929.99"`. The `+=` then concatenates strings to `total` (which starts as `int 0`, causing a `TypeError`).

```python
# ✅ FIXED CODE
def calculate_revenue(filepath):
    total = 0.0
    with open(filepath) as f:
        next(f)    # Skip header row!
        for line_num, line in enumerate(f, start=2):
            parts = line.strip().split(",")
            try:
                price = float(parts[2])
                quantity = int(parts[3])
                total += price * quantity
            except (ValueError, IndexError) as e:
                print(f"Skipping malformed line {line_num}: {e}")
    return total

# Even better — use the csv module
import csv

def calculate_revenue_v2(filepath):
    total = 0.0
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                total += float(row['price']) * int(row['quantity'])
            except (ValueError, KeyError) as e:
                print(f"Skipping row: {e}")
    return total
```

---

### Scenario 4: Why is My Loop Skipping Items?

**Interviewer:** "We need to remove all negative numbers from a list. This code misses some. Why?"

```python
# ❌ BUGGY — modifying list during iteration
numbers = [1, -2, -3, 4, -5, -6, 7]

for i in range(len(numbers)):
    if numbers[i] < 0:
        numbers.pop(i)     # Shifts all elements, index now points to next-next item

# Result: [1, -3, 4, -6, 7] — missed -3 and -6!
```

**Root cause:** When you `pop(i)`, all elements after index `i` shift left. The loop index `i` then advances, skipping the element that slid into position `i`.

```python
# ✅ FIX 1: List comprehension (most Pythonic)
numbers = [1, -2, -3, 4, -5, -6, 7]
numbers = [n for n in numbers if n >= 0]
# [1, 4, 7]

# ✅ FIX 2: Iterate backwards (if you must modify in-place)
numbers = [1, -2, -3, 4, -5, -6, 7]
for i in range(len(numbers) - 1, -1, -1):
    if numbers[i] < 0:
        numbers.pop(i)
# [1, 4, 7]

# ✅ FIX 3: Filter
numbers = list(filter(lambda x: x >= 0, numbers))

# ✅ FIX 4: Slice assignment (in-place, same list object)
numbers[:] = [n for n in numbers if n >= 0]
```

---

### Scenario 5: The Unpredictable Sort

**Interviewer:** "We're sorting employee records by salary, but employees with the same salary appear in random order each run. The product team wants stable ordering — same salary should be alphabetical by name."

```python
employees = [
    {"name": "Charlie", "salary": 75000},
    {"name": "Alice", "salary": 90000},
    {"name": "Bob", "salary": 75000},
    {"name": "Diana", "salary": 90000},
]

# ❌ Inconsistent — only sorts by salary
sorted_emps = sorted(employees, key=lambda e: e["salary"], reverse=True)
# Alice/Diana order is unpredictable (same salary)

# ✅ Multi-key sort — salary desc, then name asc
sorted_emps = sorted(employees, key=lambda e: (-e["salary"], e["name"]))
# [{'name': 'Alice', 'salary': 90000},
#  {'name': 'Diana', 'salary': 90000},
#  {'name': 'Bob', 'salary': 75000},
#  {'name': 'Charlie', 'salary': 75000}]

# Note: Python's sort IS stable (Timsort) — equal elements preserve original order
# But "original order" depends on data source, so always use explicit multi-key sort
```

---

## 13.2 Intermediate Scenarios

### Scenario 6: Memory Explosion in Production

**Interviewer:** "Our data pipeline reads a 10GB log file and processes each line. The server runs out of memory. The developer loads the entire file into memory. Fix it."

```python
# ❌ MEMORY EXPLOSION — loads entire file into memory
def process_logs_bad(filepath):
    with open(filepath) as f:
        lines = f.readlines()           # 10GB in memory!
    results = []
    for line in lines:
        if "ERROR" in line:
            results.append(parse_error(line))
    return results                       # Another large list in memory!

# ✅ FIX: Generator pipeline — constant memory
def process_logs_good(filepath):
    def read_lines(path):
        with open(path) as f:
            for line in f:              # File iterator — one line at a time
                yield line.strip()

    def filter_errors(lines):
        for line in lines:
            if "ERROR" in line:
                yield line

    def parse_lines(lines):
        for line in lines:
            yield parse_error(line)

    # Pipeline — each stage processes one item at a time
    lines = read_lines(filepath)
    errors = filter_errors(lines)
    parsed = parse_lines(errors)

    # Write results instead of collecting in memory
    with open("errors.json", "w") as out:
        for record in parsed:
            out.write(json.dumps(record) + "\n")

# ✅ ALTERNATIVE: Using itertools
from itertools import islice

def process_in_batches(filepath, batch_size=10000):
    with open(filepath) as f:
        while True:
            batch = list(islice(f, batch_size))
            if not batch:
                break
            process_batch(batch)
```

*(See File 01, Q13–Q14 for generators and memory efficiency)*

---

### Scenario 7: Race Condition in Concurrent Counter

**Interviewer:** "Our web app counts page views using threads. After 1 million requests, the counter shows only 950,000. What happened?"

```python
# ❌ RACE CONDITION — not thread-safe
import threading

counter = 0

def increment():
    global counter
    for _ in range(100_000):
        counter += 1     # NOT atomic! Read → Increment → Write can interleave

threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)    # Expected: 1,000,000 | Actual: ~950,000 (varies!)
```

**Root cause:** `counter += 1` is NOT atomic. It involves: (1) read `counter`, (2) add 1, (3) write back. Two threads can read the same value, both add 1, and write the same result — losing one increment.

```python
# ✅ FIX 1: Threading Lock
import threading

counter = 0
lock = threading.Lock()

def increment_safe():
    global counter
    for _ in range(100_000):
        with lock:            # Only one thread at a time
            counter += 1

# ✅ FIX 2: Atomic operations with queue
from queue import Queue

def increment_with_queue():
    q = Queue()
    def worker():
        for _ in range(100_000):
            q.put(1)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    return q.qsize()

# ✅ FIX 3: In production — use Redis INCR (atomic)
# redis_client.incr("page_views")

# ✅ FIX 4: concurrent.futures for cleaner code
from concurrent.futures import ThreadPoolExecutor
import threading

class AtomicCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self, n=1):
        with self._lock:
            self._value += n
            return self._value

    @property
    def value(self):
        return self._value
```

*(See File 03, Q5 — GIL, and File 07, Q2 — threading)*

---

### Scenario 8: Circular Import Hell

**Interviewer:** "Our project has `models.py` importing from `services.py` and `services.py` importing from `models.py`. We get `ImportError`. How do you fix it?"

```python
# ❌ CIRCULAR IMPORT
# models.py
from services import validate_user    # Imports services

class User:
    def __init__(self, name):
        self.name = name
        validate_user(self)

# services.py
from models import User              # Imports models → CIRCULAR!

def validate_user(user):
    if not isinstance(user, User):
        raise TypeError("Not a User")

# ImportError: cannot import name 'User' from partially initialized module
```

**Fixes:**

```python
# ✅ FIX 1: Import inside function (lazy import)
# services.py
def validate_user(user):
    from models import User           # Import when needed, not at module level
    if not isinstance(user, User):
        raise TypeError("Not a User")

# ✅ FIX 2: Restructure — extract shared code
# interfaces.py (new file — no dependencies)
from abc import ABC, abstractmethod
class Validatable(ABC):
    @abstractmethod
    def validate(self): pass

# models.py
from interfaces import Validatable
class User(Validatable):
    def validate(self):
        return bool(self.name)

# services.py
from interfaces import Validatable
def validate_user(user: Validatable):
    return user.validate()

# ✅ FIX 3: Use TYPE_CHECKING for type hints only
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import User    # Only imported during type checking, not at runtime

def validate_user(user: "User"):
    pass

# ✅ FIX 4: Dependency injection
class UserService:
    def __init__(self, validator):
        self.validator = validator

    def create_user(self, name):
        user = User(name)
        self.validator(user)
        return user
```

---

## 13.3 Advanced Scenarios

### Scenario 9: Debugging a Memory Leak in Long-Running Service

**Interviewer:** "Our FastAPI service's memory usage grows continuously over days until it crashes. How would you diagnose and fix it?"

```python
# ═══════════════════════════════════════
# Step 1: Identify the leak — use tracemalloc
# ═══════════════════════════════════════
import tracemalloc

tracemalloc.start()

# ... run the app for a while ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
print("[ Top 10 memory consumers ]")
for stat in top_stats[:10]:
    print(stat)

# ═══════════════════════════════════════
# Common causes & fixes
# ═══════════════════════════════════════

# CAUSE 1: Unbounded cache
# ❌ Cache grows forever
_cache = {}
def get_user(user_id):
    if user_id not in _cache:
        _cache[user_id] = db.query(user_id)
    return _cache[user_id]

# ✅ Fix: Use LRU cache with max size
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user(user_id):
    return db.query(user_id)

# ✅ Or use TTL cache
from cachetools import TTLCache
_cache = TTLCache(maxsize=1000, ttl=300)   # 5 minute TTL


# CAUSE 2: Event listeners / callbacks never removed
# ❌ Listeners accumulate
class EventBus:
    listeners = []     # Class variable — persists across requests!

    def subscribe(self, callback):
        self.listeners.append(callback)

# ✅ Fix: Use weak references
import weakref
class EventBus:
    def __init__(self):
        self._listeners = []

    def subscribe(self, callback):
        self._listeners.append(weakref.ref(callback))

    def emit(self, event):
        self._listeners = [ref for ref in self._listeners if ref() is not None]
        for ref in self._listeners:
            callback = ref()
            if callback:
                callback(event)


# CAUSE 3: Circular references preventing GC
# ❌ Circular reference
class Node:
    def __init__(self):
        self.parent = None
        self.children = []

    def add_child(self, child):
        child.parent = self        # child → self, self.children → child = CYCLE
        self.children.append(child)

# ✅ Fix: Use weakref for back-references
class Node:
    def __init__(self):
        self._parent = None
        self.children = []

    @property
    def parent(self):
        return self._parent() if self._parent else None

    def add_child(self, child):
        child._parent = weakref.ref(self)
        self.children.append(child)


# CAUSE 4: Database sessions not closed
# ❌ Session leak
def get_data():
    session = Session()
    return session.query(User).all()
    # Session never closed!

# ✅ Fix: Use context manager
def get_data():
    with Session() as session:
        return session.query(User).all()
```

---

### Scenario 10: Designing a Retry Mechanism with Exponential Backoff

**Interviewer:** "Our payment gateway is flaky. Design a production-grade retry mechanism."

```python
import time
import random
import logging
from functools import wraps
from typing import Tuple, Type

logger = logging.getLogger(__name__)

def retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    backoff_max: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry=None,
):
    """
    Production-grade retry decorator with exponential backoff.

    Features:
    - Exponential backoff: 1s, 2s, 4s, 8s, ...
    - Jitter: Random delay to prevent thundering herd
    - Max backoff cap: Don't wait forever
    - Configurable retryable exceptions
    - Callback on retry for logging/metrics
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Exponential backoff with optional jitter
                    delay = min(backoff_base * (2 ** (attempt - 1)), backoff_max)
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )

                    if on_retry:
                        on_retry(attempt, e, delay)

                    time.sleep(delay)

            raise last_exception
        return wrapper
    return decorator


# Usage
@retry(
    max_attempts=5,
    backoff_base=1.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
    on_retry=lambda attempt, err, delay: metrics.increment("payment.retry")
)
def process_payment(order_id: str, amount: float) -> dict:
    response = payment_gateway.charge(order_id, amount)
    if response.status_code == 429:
        raise ConnectionError("Rate limited")
    if response.status_code >= 500:
        raise ConnectionError(f"Server error: {response.status_code}")
    return response.json()


# ═══════════════════════════════════════
# Async version for asyncio
# ═══════════════════════════════════════
import asyncio

def async_retry(max_attempts=3, backoff_base=1.0, retryable_exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    if attempt == max_attempts:
                        raise
                    delay = backoff_base * (2 ** (attempt - 1)) * (0.5 + random.random())
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@async_retry(max_attempts=3, retryable_exceptions=(ConnectionError,))
async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

*(See File 03, Q1 for decorator patterns)*

---

### Scenario 11: Fixing a Deadlock

**Interviewer:** "Two services transfer money between accounts. Occasionally, the system freezes. Diagnose."

```python
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()

# ❌ DEADLOCK — Thread 1 holds A, waits for B. Thread 2 holds B, waits for A.
def transfer_1_to_2():
    with lock_a:                   # Acquires A
        time.sleep(0.1)
        with lock_b:               # Waits for B ← BLOCKED (Thread 2 has B)
            print("Transfer 1→2")

def transfer_2_to_1():
    with lock_b:                   # Acquires B
        time.sleep(0.1)
        with lock_a:               # Waits for A ← BLOCKED (Thread 1 has A)
            print("Transfer 2→1")

# Both threads freeze forever — DEADLOCK!

# ✅ FIX: Always acquire locks in the same order
def transfer(from_acc, to_acc, amount):
    # Sort by ID to ensure consistent ordering
    first, second = sorted([from_acc, to_acc], key=lambda a: a.id)

    with first.lock:
        with second.lock:
            from_acc.balance -= amount
            to_acc.balance += amount

# ✅ FIX 2: Use timeout
def transfer_safe(from_acc, to_acc, amount):
    while True:
        if from_acc.lock.acquire(timeout=1):
            try:
                if to_acc.lock.acquire(timeout=1):
                    try:
                        from_acc.balance -= amount
                        to_acc.balance += amount
                        return True
                    finally:
                        to_acc.lock.release()
            finally:
                from_acc.lock.release()
        time.sleep(random.uniform(0, 0.1))   # Random backoff
```

---

### Scenario 12: Optimizing a Slow API Endpoint

**Interviewer:** "This endpoint takes 8 seconds to respond. Optimize it."

```python
# ❌ SLOW — 8 seconds
async def get_dashboard(user_id: int):
    user = await db.get_user(user_id)              # 200ms
    orders = await db.get_orders(user_id)           # 2000ms
    recommendations = await ml_service.recommend(user_id)  # 3000ms
    notifications = await notification_service.get(user_id) # 1500ms
    analytics = await analytics_service.get(user_id)        # 1300ms
    # Total: ~8000ms (sequential)

    return {
        "user": user,
        "orders": orders,
        "recommendations": recommendations,
        "notifications": notifications,
        "analytics": analytics,
    }

# ✅ FAST — 3 seconds (concurrent)
async def get_dashboard_fast(user_id: int):
    # Gather independent calls concurrently
    user, (orders, recommendations, notifications, analytics) = await asyncio.gather(
        db.get_user(user_id),                           # Still needed first? No.
        asyncio.gather(
            db.get_orders(user_id),
            ml_service.recommend(user_id),
            notification_service.get(user_id),
            analytics_service.get(user_id),
        )
    )
    # Total: ~max(200, 2000, 3000, 1500, 1300) = ~3000ms

    return {
        "user": user,
        "orders": orders,
        "recommendations": recommendations,
        "notifications": notifications,
        "analytics": analytics,
    }

# ✅ EVEN FASTER — add caching
from functools import lru_cache
import redis

cache = redis.Redis()

async def get_dashboard_cached(user_id: int):
    cache_key = f"dashboard:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)          # <1ms from cache

    result = await get_dashboard_fast(user_id)
    cache.setex(cache_key, 60, json.dumps(result))   # Cache 60 seconds
    return result
```

*(See File 07, Q1 — asyncio patterns)*

---
