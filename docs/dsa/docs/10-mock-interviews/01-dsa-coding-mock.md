# Mock 1 — DSA Coding Round (45 min)

> **Setup**: senior at FAANG-level company, mid-loop. Candidate is mid-level (3-5 YoE). Problem: LRU Cache. Read this top to bottom; the side commentary explains why each move worked or didn't.

<span class="phase-status phase-done">Phase 14 — Mock Interview</span>

---

## 🎬 Transcript

### Minute 0-2: introductions

> **Interviewer (I)**: Hi, I'm M—. I'm a staff engineer on the search infra team. We've got 45 minutes; I'll spend the last 5 on your questions. Sound good?
>
> **Candidate (C)**: Sounds great. Thanks for making time.
>
> **I**: Cool. Today's problem: implement an **LRU cache** with `get(key)` and `put(key, value)`, both in O(1). Capacity is fixed at construction.

??? tip "What just happened"

    Tight intro; no role pitch from the candidate. Good. Saved 90 s for the actual work.

### Minute 2-6: clarifying

> **C**: Couple of clarifications. Is the cache thread-safe?
>
> **I**: Single-threaded for now. Bring it up if it's relevant later.
>
> **C**: Got it. Are keys hashable / comparable for equality?
>
> **I**: Assume strings.
>
> **C**: And on `get`, do we count it as "use" — i.e., bump it to most-recently-used?
>
> **I**: Yes.
>
> **C**: One more: on `put` for an existing key, does it count as a "use"?
>
> **I**: Yes — same as a fresh put.

??? tip "What just happened"

    Four clarifying questions, all useful, none stalling. The thread-safety + recency-on-get + recency-on-update are the three traps. Candidate found all three.

### Minute 6-10: approach

> **C**: I'll think aloud. To get O(1) `get` I need a hash map. To get O(1) eviction of the least-recent I need either a queue with O(1) removal of arbitrary nodes, or a doubly-linked list. So: hash map → DLL nodes; DLL holds (key, value); head = most recent, tail = least recent.
>
> **I**: Why doubly-linked, specifically?
>
> **C**: Because on `get`, when I find the node via hash map, I need to detach it from its current position and move it to the head. Removal in a singly-linked list is O(N) without the prev pointer.
>
> **I**: Perfect. Go ahead and code it.

??? tip "What just happened"

    Strong "let me reason from constraints" rather than "I'll use OrderedDict." Either is fine, but reasoning out the data structure first is what gets staff-level signal.

### Minute 10-30: coding

```python
class _Node:
    __slots__ = ("key", "value", "prev", "next")
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self.cap = capacity
        self.map: dict[str, _Node] = {}
        # Sentinel head/tail to avoid edge cases on empty/single-element lists
        self.head = _Node(None, None)
        self.tail = _Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: str) -> int | None:
        node = self.map.get(key)
        if node is None:
            return None
        self._move_to_front(node)
        return node.value

    def put(self, key: str, value: int) -> None:
        node = self.map.get(key)
        if node is not None:
            node.value = value
            self._move_to_front(node)
            return
        if len(self.map) >= self.cap:
            self._evict_lru()
        new_node = _Node(key, value)
        self.map[key] = new_node
        self._insert_after_head(new_node)

    # --- DLL helpers ---
    def _detach(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_after_head(self, node: _Node) -> None:
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _move_to_front(self, node: _Node) -> None:
        self._detach(node)
        self._insert_after_head(node)

    def _evict_lru(self) -> None:
        lru = self.tail.prev
        self._detach(lru)
        del self.map[lru.key]
```

Halfway through, this exchange:

> **I**: Why the sentinel head and tail?
>
> **C**: It eliminates the "is this the first/last node?" branch in `_detach` and the insert helpers. Every node has real prev/next pointers, so the bookkeeping is the same regardless of position. Saves about 8 conditionals.

??? tip "What just happened"

    Sentinel pattern is a small thing but signals the candidate has written real linked-list code before. Interviewers love specific reasons for design choices.

### Minute 30-37: testing + edge cases

> **C**: Let me trace a quick example. Capacity 2.
> ```
> put("a", 1) → map={a}, list=[a]
> put("b", 2) → map={a,b}, list=[b,a]
> get("a")    → returns 1, list=[a,b]
> put("c", 3) → evicts b, list=[c,a]
> get("b")    → returns None ✓
> get("a")    → returns 1 ✓
> ```
> Edge cases I want to think about: capacity 1, capacity 0, calling get before any put, putting the same key twice with different values, putting the same key when at capacity (must NOT evict).
>
> **I**: Walk me through "putting the same key when at capacity."
>
> **C**: If key already exists, I update the value and move to front *before* checking eviction. My code does that — the `if node is not None` branch returns before reaching the eviction check.
>
> **I**: Good. What if capacity is 1 and I put two different keys?
>
> **C**: First put inserts. Second put: key not in map → len(map) == cap, so evict tail (which is the only real node) → insert new. List is now `[new]`. Map has only the new key.

??? tip "What just happened"

    Edge cases are scripted. Two things matter: (1) candidate proposed them unprompted, (2) candidate's *code* already handles them — they didn't need to patch.

### Minute 37-40: complexity + follow-up

> **I**: Time and space?
>
> **C**: Both `get` and `put` are O(1) amortised. Hash map ops are O(1) avg. DLL ops are O(1) worst case. Space is O(capacity) for the map plus the DLL nodes — also O(capacity).
>
> **I**: How would you make this thread-safe?
>
> **C**: Three options. (1) One coarse mutex around the entire cache — simplest, kills concurrency. (2) Per-bucket striping in the hash map plus a separate DLL lock — better but the DLL is the bottleneck. (3) Lock-free: doable with CAS but complex and easy to get wrong; usually not worth it. For most production caches I'd start with (1) and measure; if contention shows up, move to (2) and consider replacing the DLL with a probabilistic approximation like CLOCK or 2Q which doesn't need exact ordering.
>
> **I**: Nice — I like that you mentioned approximate algorithms. CLOCK is what we use in our buffer manager.

??? tip "What just happened"

    Not just "wrap a mutex around it." The candidate flagged that *the data structure itself* is the contention bottleneck — and proposed switching to an approximation. That's the staff-level move.

### Minute 40-45: candidate questions

> **C**: A couple. First: how does your team decide between strict LRU vs approximate? Second: what's a recent gnarly problem the team solved that you'd happily tell a stranger about?

??? tip "What just happened"

    Genuine. The second question is gold — it forces the interviewer to share something real, which both gives the candidate signal and makes the interaction memorable.

---

## 🟢 What was good

- Clarifying questions surfaced all three traps (thread safety, get-as-use, put-as-use).
- Reasoned the DLL+map combo from constraints, not pattern-matching.
- Sentinel nodes — small touch, big signal.
- Edge cases enumerated *before* tracing, then verified against the code.
- Thread-safety answer escalated from coarse → fine → approximate, with reasoning.

## 🟡 What was weak

- Didn't ask about expected operation mix (read-heavy vs write-heavy) — would matter for thread-safety choice.
- Didn't ask whether `value=None` is a legitimate value (would conflict with `get` returning `None` for "missing"). Real interview gotcha.
- Slightly slow on coding — 20 min for ~50 lines. Budget should be ~12-15 min, leaving buffer for follow-ups.

## 🔁 How to do it better

1. **Test names matter**. After tracing by hand, write 3-4 named tests (`test_evicts_lru`, `test_update_existing_key_does_not_evict`, `test_get_unknown_returns_none`). Even pseudo-pytest signals testing discipline.
2. **Distinguish "missing" from "value is None"**. Use a sentinel: `_MISSING = object()`; return `_MISSING` and let caller compare. Or change the API to raise `KeyError`. Mention this *before* the interviewer asks.
3. **Time-box coding**. If you're past 15 min still typing the helpers, you've over-engineered. Skip helper extraction; inline the DLL ops; refactor at the end if time permits.

---

## 🃏 Cheatsheet for this style of round

- 4 clarifications max in the first 5 min.
- State the data structure choice and *why* before coding.
- Sentinels eliminate branches in linked-list code.
- Trace one example by hand; enumerate edge cases; verify against code.
- For thread safety: coarse → striped → lock-free → approximate. Don't jump to lock-free.
- Always have 1-2 questions ready. The "tell me about a gnarly problem" question wins.
