# 07 — Python Concurrency & Async Programming
## Complete Interview Questions with Examples

---

## 7.1 Asyncio

### Q1: Explain asyncio and how async/await works.

**Answer:**

```python
import asyncio
import time

# ═══════════════════════════════════════
# Basic async/await
# ═══════════════════════════════════════
async def fetch_data(url, delay):
    """Simulate async I/O operation."""
    print(f"Fetching {url}...")
    await asyncio.sleep(delay)    # Non-blocking sleep (yields control)
    print(f"Done fetching {url}")
    return f"Data from {url}"

async def main():
    # Sequential — 3 seconds total
    result1 = await fetch_data("url1", 1)
    result2 = await fetch_data("url2", 2)

    # Concurrent — 2 seconds total (max of individual times)
    results = await asyncio.gather(
        fetch_data("url1", 1),
        fetch_data("url2", 2),
        fetch_data("url3", 1),
    )
    print(results)

asyncio.run(main())

# ═══════════════════════════════════════
# Key asyncio patterns
# ═══════════════════════════════════════

# 1. gather — run coroutines concurrently, collect all results
async def fetch_all(urls):
    tasks = [fetch_data(url, 1) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)

# 2. create_task — schedule coroutine without waiting
async def background_job():
    task = asyncio.create_task(fetch_data("bg", 5))
    # ... do other work ...
    result = await task    # Wait when needed

# 3. TaskGroup (Python 3.11+) — structured concurrency
async def structured():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_data("a", 1))
        task2 = tg.create_task(fetch_data("b", 2))
    # Both tasks guaranteed complete here
    print(task1.result(), task2.result())

# 4. as_completed — process results as they arrive
async def process_as_ready(urls):
    tasks = [asyncio.create_task(fetch_data(url, i))
             for i, url in enumerate(urls)]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        print(f"Got result: {result}")

# 5. Timeout
async def with_timeout():
    try:
        result = await asyncio.wait_for(
            fetch_data("slow", 10),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        print("Timed out!")

# 6. Semaphore — limit concurrency
async def rate_limited_fetch(urls, max_concurrent=5):
    sem = asyncio.Semaphore(max_concurrent)

    async def bounded_fetch(url):
        async with sem:    # Only 5 concurrent fetches
            return await fetch_data(url, 1)

    return await asyncio.gather(*(bounded_fetch(url) for url in urls))

# 7. Queue — producer/consumer pattern
async def producer_consumer():
    queue = asyncio.Queue(maxsize=10)

    async def producer():
        for i in range(20):
            await queue.put(f"item_{i}")
            await asyncio.sleep(0.1)
        await queue.put(None)  # Sentinel

    async def consumer(name):
        while True:
            item = await queue.get()
            if item is None:
                await queue.put(None)  # Signal other consumers
                break
            print(f"{name} processing {item}")
            await asyncio.sleep(0.2)
            queue.task_done()

    await asyncio.gather(
        producer(),
        consumer("Worker-1"),
        consumer("Worker-2"),
    )
```

---

### Q2: Threading vs Multiprocessing vs Asyncio — when to use which?

**Answer:**

```python
"""
┌────────────────┬──────────────┬───────────────┬──────────────┐
│                │  Threading   │Multiprocessing│   Asyncio    │
├────────────────┼──────────────┼───────────────┼──────────────┤
│ Best for       │ I/O-bound    │ CPU-bound     │ I/O-bound    │
│ Parallelism    │ Concurrent   │ True parallel │ Concurrent   │
│ GIL impact     │ Limited by   │ Bypasses GIL  │ Single thread│
│ Memory         │ Shared       │ Separate      │ Shared       │
│ Overhead       │ Low          │ High (process)│ Very low     │
│ Scaling        │ ~100 threads │ ~CPU cores    │ ~10K+ tasks  │
│ Complexity     │ Medium       │ Medium-High   │ Medium       │
│ Communication  │ Shared vars  │ IPC (pipes)   │ Shared vars  │
│ Debugging      │ Hard (races) │ Medium        │ Easier       │
└────────────────┴──────────────┴───────────────┴──────────────┘

Decision Guide:
  - Network requests, file I/O, web scraping → asyncio
  - Legacy blocking libraries, simple I/O    → threading
  - CPU-heavy (ML training, data processing) → multiprocessing
  - Mix of CPU + I/O                         → multiprocessing + asyncio
"""

# ═══════════════════════════════════════
# Threading example
# ═══════════════════════════════════════
import threading

class SafeCounter:
    """Thread-safe counter using Lock."""
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:           # Acquire/release lock automatically
            self._count += 1

    @property
    def value(self):
        return self._count

counter = SafeCounter()
threads = [threading.Thread(target=counter.increment) for _ in range(1000)]
for t in threads: t.start()
for t in threads: t.join()
print(counter.value)  # 1000 (guaranteed with lock)

# ═══════════════════════════════════════
# Thread synchronization primitives
# ═══════════════════════════════════════
lock = threading.Lock()           # Basic mutual exclusion
rlock = threading.RLock()         # Reentrant lock (can acquire multiple times)
event = threading.Event()         # Signal between threads
sem = threading.Semaphore(5)      # Limit concurrent access
barrier = threading.Barrier(3)    # Wait for N threads to reach a point
condition = threading.Condition() # Wait for a condition to be true

# ═══════════════════════════════════════
# Multiprocessing example
# ═══════════════════════════════════════
from multiprocessing import Pool, Process, Queue, Manager

def cpu_work(n):
    return sum(i * i for i in range(n))

# Pool — simple parallel map
with Pool(processes=4) as pool:
    results = pool.map(cpu_work, [10**6] * 8)

# Shared state between processes
with Manager() as manager:
    shared_list = manager.list()
    shared_dict = manager.dict()

    def worker(shared_list, i):
        shared_list.append(i)

    processes = [Process(target=worker, args=(shared_list, i)) for i in range(5)]
    for p in processes: p.start()
    for p in processes: p.join()
    print(list(shared_list))

# Inter-process communication with Queue
def producer(q):
    for i in range(10):
        q.put(i)
    q.put(None)

def consumer(q):
    while (item := q.get()) is not None:
        print(f"Got: {item}")

q = Queue()
Process(target=producer, args=(q,)).start()
Process(target=consumer, args=(q,)).start()
```

---

### Q3: Explain async context managers and async iterators.

**Answer:**

```python
# Async Context Manager
class AsyncDBConnection:
    async def __aenter__(self):
        self.conn = await create_connection()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()

# async with AsyncDBConnection() as conn:
#     result = await conn.execute("SELECT 1")

# Using contextlib
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_timer(label):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.4f}s")

# async with async_timer("DB query"):
#     await db.execute("SELECT * FROM users")

# Async Iterator
class AsyncRange:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def __aiter__(self):
        self.current = self.start
        return self

    async def __anext__(self):
        if self.current >= self.stop:
            raise StopAsyncIteration
        await asyncio.sleep(0.1)  # Simulate async work
        value = self.current
        self.current += 1
        return value

# async for num in AsyncRange(0, 5):
#     print(num)

# Async Generator
async def async_fetch_pages(urls):
    for url in urls:
        data = await fetch_data(url, 0.5)
        yield data   # Produces values asynchronously

# async for page in async_fetch_pages(urls):
#     process(page)
```

---
