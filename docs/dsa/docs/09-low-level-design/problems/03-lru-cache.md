# Design an LRU Cache

> A cache that evicts the *least recently used* entry when full. The most-asked LLD problem because it crosses both DS (DLL + hash map) and OOP cleanly.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design a cache with a fixed maximum capacity. Support `get(key)` and `put(key, value)` in O(1). When capacity is reached, evict the least-recently-used entry."*

LeetCode 146 in coding form. As an LLD interview, expect:

1. **Clarifying questions** (concurrency? expiration? value type?).
2. **Pick a data structure** with explicit O(1) reasoning.
3. **Production extensions**: thread-safety, TTL, write-through, stats.

---

## ❓ Clarifying questions

1. **Capacity?** Fixed at construction or resizable?
2. **Concurrency?** Single-threaded or thread-safe?
3. **TTL?** Should entries expire in addition to LRU eviction?
4. **Persistence?** In-memory only?
5. **Value type?** Generic? Bytes? Hashable?
6. **Eviction callback?** Notify when an entry is evicted?
7. **Stats?** Hit/miss counters?

**Default assumptions**:

- Fixed capacity at construction.
- Generic key/value (`K`, `V`).
- Single-threaded for the core; mention how to make it thread-safe.
- No TTL in v1; add as extension.

---

## 🏛️ Data structure

**O(1) requires hash map + doubly-linked list.**

| Operation | Hash map alone | DLL alone | Hash map + DLL |
|---|---|---|---|
| Lookup | O(1) | O(n) | O(1) |
| Move-to-front | O(n) | O(1) given node | O(1) |
| Evict tail | O(n) | O(1) | O(1) |

The hash map maps `key → DLL node`. The DLL keeps usage order: head = most recent, tail = least recent.

```
HEAD <-> A <-> B <-> C <-> TAIL
        most               least
        recent            recent
```

---

## 🔧 Code

### Core implementation

```python
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class _Node(Generic[K, V]):
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: K, value: V):
        self.key = key
        self.value = value
        self.prev: "_Node[K, V] | None" = None
        self.next: "_Node[K, V] | None" = None


class LRUCache(Generic[K, V]):
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._map: dict[K, _Node[K, V]] = {}
        # Sentinels — avoids None checks at boundaries
        self._head: _Node[K, V] = _Node(None, None)   # type: ignore[arg-type]
        self._tail: _Node[K, V] = _Node(None, None)   # type: ignore[arg-type]
        self._head.next = self._tail
        self._tail.prev = self._head

    # --- public API ---

    def get(self, key: K) -> V | None:
        node = self._map.get(key)
        if node is None:
            return None
        self._move_to_front(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        node = self._map.get(key)
        if node is not None:
            node.value = value
            self._move_to_front(node)
            return

        if len(self._map) >= self.capacity:
            self._evict_lru()

        new_node = _Node(key, value)
        self._add_to_front(new_node)
        self._map[key] = new_node

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key: K) -> bool:
        return key in self._map

    # --- internals ---

    def _add_to_front(self, node: _Node[K, V]) -> None:
        nxt = self._head.next
        node.prev = self._head
        node.next = nxt
        self._head.next = node
        nxt.prev = node                                 # type: ignore[union-attr]

    def _remove(self, node: _Node[K, V]) -> None:
        node.prev.next = node.next                      # type: ignore[union-attr]
        node.next.prev = node.prev                      # type: ignore[union-attr]

    def _move_to_front(self, node: _Node[K, V]) -> None:
        self._remove(node)
        self._add_to_front(node)

    def _evict_lru(self) -> None:
        lru = self._tail.prev
        if lru is None or lru is self._head:
            return
        self._remove(lru)
        del self._map[lru.key]
```

### Walkthrough

```python
c = LRUCache[int, str](capacity=2)
c.put(1, "a")           # cache: {1:a}
c.put(2, "b")           # cache: {1:a, 2:b}
c.get(1)                # → "a"; 1 moves to front. order: 1, 2
c.put(3, "c")           # capacity hit; evict LRU (2). cache: {1:a, 3:c}
c.get(2)                # → None
c.get(1)                # → "a"
```

---

## 🐍 Pythonic alternative — `OrderedDict`

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache: OrderedDict = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)        # pop oldest
```

`OrderedDict` is internally a hash map + DLL. **In an interview, write the explicit DLL version first** — that's what the interviewer wants to see. Mention `OrderedDict` as the production-ready alternative.

---

## 🎯 OOP design notes

| Decision | Rationale |
|---|---|
| `_Node` is internal (leading `_`) | Hidden implementation detail. |
| Sentinels `_head` and `_tail` | Eliminate None-handling at list boundaries. |
| `__slots__` on `_Node` | Saves memory at scale (millions of entries). |
| Generic over `K`, `V` | Type-safe usage. |
| `__len__`, `__contains__` | Pythonic; integrate with `len()` and `in`. |

---

## 🚀 Extensions

### Thread safety

Wrap public methods in a lock:

```python
import threading

class ThreadSafeLRUCache(LRUCache[K, V]):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            return super().get(key)

    def put(self, key, value):
        with self._lock:
            super().put(key, value)
```

For high-contention production caches, prefer **shard-by-key** locking: N internal LRUs, each with its own lock. Reduces contention by N×.

### TTL (time-based expiry)

Add `expires_at` to each `_Node`. On `get`, check expiry; if expired, evict + return `None`. Periodically sweep expired entries.

```python
@dataclass
class TTLNode(_Node):
    expires_at: float        # unix epoch sec

def get(self, key):
    node = self._map.get(key)
    if node is None: return None
    if time.time() >= node.expires_at:
        self._evict(node)
        return None
    self._move_to_front(node)
    return node.value
```

### Eviction callback

Pass a callable to constructor; invoke on eviction. Useful for write-through caches:

```python
class LRUCache(Generic[K, V]):
    def __init__(self, capacity, on_evict=None):
        ...
        self._on_evict = on_evict

    def _evict_lru(self):
        lru = ...
        if self._on_evict:
            self._on_evict(lru.key, lru.value)
        ...
```

### Stats (Observer-light)

Track hits, misses, evictions:

```python
class CacheStats:
    def __init__(self):
        self.hits = self.misses = self.evictions = 0

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0
```

Wire into `LRUCache.get` / `_evict_lru`. Expose via `cache.stats()`.

### Other eviction policies

LRU isn't always the right choice. Same skeleton; swap policy:

| Policy | When |
|---|---|
| LRU | Recency dominates (most workloads) |
| LFU | Frequency matters (popular videos) |
| FIFO | Fairness; no recency signal |
| TinyLFU / Window-TinyLFU | Modern best-in-class (Caffeine) |
| ARC | Adaptive between LRU and LFU |

---

## 🪤 Common mistakes

??? warning "Singly-linked list"

    Removing arbitrary nodes is O(n). Need doubly-linked.

??? warning "No sentinels"

    Code becomes a forest of `if node.prev is None: ...` checks. Sentinels eliminate boundaries.

??? warning "Forgetting to delete from map on eviction"

    Eviction must update **both** structures. Otherwise hash map grows unbounded.

??? warning "Using a list instead of DLL"

    Python `list` does O(n) for arbitrary remove/insert. Defeats the O(1) goal.

??? warning "Reaching for `OrderedDict` first"

    Interviewers want to see you can build it. `OrderedDict` is the punchline.

---

## ⏱️ Pacing

| Minute | What |
|---|---|
| 0–2 | Clarifying questions. |
| 2–5 | Pick DS: hash map + DLL. Justify O(1). |
| 5–25 | Code. Sentinel-based DLL, with tests. |
| 25–35 | Extensions (thread safety / TTL / stats). |
| 35–45 | Q&A. |

---

## ➡️ Where this connects

- [Hash table basics](../../02-data-structures/hash-tables/01-hash-table-basics.md) — the map half.
- [Linked list basics](../../02-data-structures/linked-lists/01-linked-list-basics.md) — the DLL half.
- [OOP fundamentals](../01-oop-fundamentals.md) — encapsulation + slots.
- Other LLD: [Parking Lot](01-parking-lot.md), [Elevator](02-elevator-system.md), [Vending Machine](04-vending-machine.md).
