# Two Heaps

> Two priority queues running back-to-back, each guarding one half of the data. The textbook trick for "running median of a stream," and the secret weapon for "schedule projects greedily by capital then profit" (IPO), "sliding-window median," and "earliest-possible-day-to-finish-tasks." A pattern your interviewer will reach for the moment you say *"running statistics on a stream."*

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 20)</span>

---

## 📖 What is the two-heaps pattern?

Imagine a librarian sorting incoming books by reading level. She keeps two carts: an **easy cart** (max-heap by difficulty — the "hardest of the easy" books float to the top) and a **hard cart** (min-heap — the "easiest of the hard" books float to the top). Whenever a new book arrives, she drops it into the appropriate cart and rebalances so neither cart has more than one extra book. Now she can answer "what's the median reading level?" instantly: it's the top of the larger cart, or the average of the two tops if the carts are equal-sized.

That's the two-heaps trick distilled. **A max-heap holds the smaller half; a min-heap holds the larger half.** Each push: O(log n). Median query: O(1). For a stream of `n` numbers that's O(n log n) total — beating the obvious O(n²) sort-each-time.

The pattern generalises beyond medians: **whenever you can split your data into two halves where you only care about the *boundary* between them**, two heaps is the move. Examples:

- **Median of stream** — boundary = where small ends and big begins.
- **IPO project scheduler** — boundary = "which projects can I afford right now?"
- **Sliding-window median** — same as median, but the window slides (lazy deletion).
- **Earliest day to finish tasks with prerequisites** — boundary = "which tasks are unlocked?"

!!! tip "The signal — when to reach for two heaps"
    Reach for it when:

    - You need the **median**, the **k-th element**, or **boundary statistics** over a *stream* (not a fixed array).
    - You're doing a **greedy schedule** that filters items by one criterion (capital, deadline, time available) and ranks the survivors by another (profit, value).
    - The brute force is "sort the array every step" → O(n² log n) and you need to do better.

    Cousins:

    - **Single heap (top-K)** — when you only care about *one* tail of the data, not both halves.
    - **Sliding window** ([01-sliding-window.md](01-sliding-window.md)) — fixed-size median problems can also be solved with a sorted-list bisect (`SortedList`), trade-off: O(log n) per move vs O(log n) heap + cleanup overhead.

---

## 🧩 The three flavors

### Flavor 1: Balanced halves (the median primitive)

A max-heap `low` holds the smaller half. A min-heap `high` holds the larger half. Maintain two invariants after every insertion:

1. **Order**: every value in `low` ≤ every value in `high`.
2. **Size**: `len(low) == len(high)` *or* `len(low) == len(high) + 1`. (Lefty bias: `low` is allowed to be one element larger.)

```python
import heapq
from typing import Final


class MedianFinder:
    """Online median tracker for a stream of numbers."""

    def __init__(self) -> None:
        self._low: list[float] = []     # max-heap (negated values)
        self._high: list[float] = []    # min-heap

    def add_num(self, num: float) -> None:
        # (1) Route the new number through `low` (negate for max-heap behavior).
        heapq.heappush(self._low, -num)
        # (2) Move the largest of `low` to `high` to enforce the order invariant.
        heapq.heappush(self._high, -heapq.heappop(self._low))
        # (3) If `high` got too big, give one back to `low`.
        if len(self._high) > len(self._low):
            heapq.heappush(self._low, -heapq.heappop(self._high))

    def find_median(self) -> float:
        if len(self._low) > len(self._high):
            return -self._low[0]                              # odd count
        return (-self._low[0] + self._high[0]) / 2.0          # even count
```

The "push-through-low-then-rebalance" routine is more lines than a naive insert-into-the-right-heap, but **eliminates branching** on which heap should receive the value. It also self-corrects if the input value should have gone to `high` — it gets shuffled there for free.

**Examples:** Find Median from Data Stream (LC 295), Sliding Window Median (LC 480 with lazy deletion).

### Flavor 2: Filter-and-pick (IPO-style scheduler)

A min-heap of "items not yet available" (sorted by entry threshold), and a max-heap of "available items" (sorted by reward). Each round:

1. Move every item whose threshold ≤ current state from the min-heap to the max-heap.
2. Pop the best-reward item from the max-heap.
3. Update state with the reward.

```python
import heapq

def find_maximized_capital(
    k: int, w: int, profits: list[int], capital: list[int]
) -> int:
    # (1) Pair (capital, profit) and sort by capital ascending — or use a min-heap.
    pending: list[tuple[int, int]] = list(zip(capital, profits))
    heapq.heapify(pending)
    available: list[int] = []           # max-heap of profits (negate)

    for _ in range(k):
        # (2) Move every project we can afford into the available pool.
        while pending and pending[0][0] <= w:
            _, profit = heapq.heappop(pending)
            heapq.heappush(available, -profit)
        if not available:
            break                       # nothing is affordable → stop early
        # (3) Take the highest-profit affordable project.
        w += -heapq.heappop(available)

    return w
```

**Examples:** IPO (LC 502), Find Maximized Capital, Maximum Performance of a Team (LC 1383 — variant).

### Flavor 3: Lazy deletion (sliding-window heap)

Heaps don't support O(log n) random removal — only `pop` from the top. When the window slides and the leaving element isn't on top, you can't actually remove it. The fix: **mark it as "ghost" and ignore it the next time it surfaces.**

```python
import heapq

class SlidingWindowMedian:
    """Median of every k-element window in a stream."""

    def __init__(self) -> None:
        self._low: list[tuple[float, int]] = []     # max-heap of (-val, index)
        self._high: list[tuple[float, int]] = []    # min-heap of (val, index)
        self._invalid_low = 0
        self._invalid_high = 0

    def _prune(self, heap: list[tuple[float, int]], invalid: int, *, lo: int) -> int:
        # Pop ghosts from the top; return new invalid count.
        while heap and heap[0][1] < lo:
            heapq.heappop(heap)
            invalid -= 1
        return invalid

    # ... see Deep-dive 2 for the full add/remove/median walkthrough.
```

The two-counter approach `_invalid_low / _invalid_high` keeps the heap sizes interpretable (`real_size = len(heap) - invalid`).

**Examples:** Sliding Window Median (LC 480), Maximum Subsequence Score (LC 2542 — heap + counter), Process Tasks Using Servers (LC 1882).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Running median | Median of a growing stream | LC 295 | Balanced halves; lefty bias |
| 2 | Sliding median | Median of every k-window | LC 480 | Lazy deletion via ghost counters |
| 3 | Greedy two-tier | Filter by threshold A, pick by reward B | IPO (LC 502) | Min-heap pending + max-heap available |
| 4 | Server scheduling | Earliest free server, then earliest weight | LC 1882 | Free-heap + busy-heap by `(free_time, idx)` |
| 5 | k-th element of stream | Maintain top-k forever | LC 703 | Single min-heap of size k (degenerate "two heaps" — small heap is full set) |
| 6 | Difference balancing | Boundary between two ranked groups | Maximum Performance of a Team (LC 1383) | Sort by one key, heap by another |
| 7 | Earliest deadline first | "Always do the most urgent now" | Course Schedule III (LC 630) | Max-heap of times; pop biggest if total exceeds deadline |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Find Median from Data Stream | 295 | <span class="diff-hard">Hard</span> | Running median | 📝 |
| 2 | Sliding Window Median | 480 | <span class="diff-hard">Hard</span> | Sliding median | 📝 |
| 3 | IPO | 502 | <span class="diff-hard">Hard</span> | Greedy two-tier | 📝 |
| 4 | Maximum Performance of a Team | 1383 | <span class="diff-hard">Hard</span> | Difference balancing | 📝 |
| 5 | Course Schedule III | 630 | <span class="diff-hard">Hard</span> | Earliest deadline first | 📝 |
| 6 | Find Right Interval | 436 | <span class="diff-medium">Medium</span> | Boundary lookup | 📝 |
| 7 | Process Tasks Using Servers | 1882 | <span class="diff-medium">Medium</span> | Server scheduling | 📝 |
| 8 | Single-Threaded CPU | 1834 | <span class="diff-medium">Medium</span> | Earliest available task | 📝 |
| 9 | Reorganize String | 767 | <span class="diff-medium">Medium</span> | Most-frequent-first heap | 📝 |
| 10 | Task Scheduler | 621 | <span class="diff-medium">Medium</span> | Cooldown heap | 📝 |
| 11 | Kth Largest Element in a Stream | 703 | <span class="diff-easy">Easy</span> | k-th element of stream | 📝 |
| 12 | Connect Sticks | 1167 | <span class="diff-medium">Medium</span> | Min-heap merge | 📝 |
| 13 | Last Stone Weight | 1046 | <span class="diff-easy">Easy</span> | Max-heap collide | 📝 |
| 14 | Maximize Capital | LC 502 var | <span class="diff-hard">Hard</span> | Greedy two-tier | 📝 |
| 15 | Minimum Cost to Hire K Workers | 857 | <span class="diff-hard">Hard</span> | Sort+heap-of-quality | 📝 |
| 16 | Minimum Number of Refueling Stops | 871 | <span class="diff-hard">Hard</span> | Greedy-fuel max-heap | 📝 |
| 17 | Earliest Possible Day to Solve All Tasks | — | <span class="diff-medium">Medium</span> | Greedy two-tier | 📝 |
| 18 | Smallest Range Covering Elements from K Lists | 632 | <span class="diff-hard">Hard</span> | k-pointer min-heap | 📝 |
| 19 | Find K Pairs with Smallest Sums | 373 | <span class="diff-medium">Medium</span> | Pair-frontier min-heap | 📝 |
| 20 | Median of Two Sorted Arrays (heap version) | 4 | <span class="diff-hard">Hard</span> | Running median | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Find Median from Data Stream (LC 295)

> Design a class that supports `add_num(int)` and `find_median()`. Find the median of all numbers seen so far. Both should run in O(log n) and O(1) respectively.

#### Code (re-stated)

```python
import heapq

class MedianFinder:
    def __init__(self) -> None:
        self._low: list[float] = []     # max-heap via negation
        self._high: list[float] = []    # min-heap

    def add_num(self, num: float) -> None:
        heapq.heappush(self._low, -num)
        heapq.heappush(self._high, -heapq.heappop(self._low))
        if len(self._high) > len(self._low):
            heapq.heappush(self._low, -heapq.heappop(self._high))

    def find_median(self) -> float:
        if len(self._low) > len(self._high):
            return -self._low[0]
        return (-self._low[0] + self._high[0]) / 2.0
```

#### Dry run on stream `1, 2, 3, 4, 5`

| Op | Step-by-step (after the 3-line `add_num`) | `low` (sorted desc, conceptually) | `high` (sorted asc) | `median()` |
|----|--------------------------------------------|-----------------------------------|--------------------|----------|
| add(1) | push 1 to low → [1]; pop 1, push to high → low=[], high=[1]; high>low → pop 1, push to low | [1] | [] | 1.0 |
| add(2) | push 2 to low → [2,1]; pop 2, push to high → low=[1], high=[2] | [1] | [2] | 1.5 |
| add(3) | push 3 to low → [3,1]; pop 3, push to high → low=[1], high=[2,3]; high>low → pop 2, push to low → low=[2,1], high=[3] | [2,1] | [3] | 2.0 |
| add(4) | push 4 to low → [4,2,1]; pop 4, push to high → low=[2,1], high=[3,4] | [2,1] | [3,4] | 2.5 |
| add(5) | push 5 to low → [5,2,1]; pop 5, push to high → low=[2,1], high=[3,4,5]; high>low → pop 3, push to low → low=[3,2,1], high=[4,5] | [3,2,1] | [4,5] | 3.0 |

Each median query is O(1) — read the top(s). Each insert is O(log n).

#### The lefty-bias choice

We chose to allow `len(low) == len(high) + 1`. The opposite (`high` larger) is symmetric — the choice just decides which top is the median when the count is odd. **Pick one and stay consistent**, otherwise the comparisons in `find_median` get tangled.

#### Why route through `low` first instead of comparing?

The 3-line insert is **branch-free**:

```python
heapq.heappush(self._low, -num)             # always
heapq.heappush(self._high, -heapq.heappop(self._low))   # always
if len(self._high) > len(self._low):
    heapq.heappush(self._low, -heapq.heappop(self._high))
```

A branched alternative would compare `num` against `low[0]` to decide which heap. Both are O(log n) — the branchless version reads cleaner under interview pressure and is harder to off-by-one.

#### Complexity

- **Time:** `add_num` O(log n); `find_median` O(1).
- **Space:** O(n).

---

### Deep-dive 2 — Sliding Window Median (LC 480)

> Given an array `nums` and an integer `k`, return the median of every contiguous window of length `k`.

The challenge: when the window slides, the *leaving* element might be deep inside one of the heaps. Heaps can't remove from the middle in O(log n). The trick: **lazy deletion**.

#### The approach

Tag every heap entry with its **index**. When sliding, mark the leaving index as a "ghost"; whenever a ghost surfaces at a heap top, pop it. Maintain `effective_size` = `len(heap) - ghosts`.

#### Code

```python
import heapq

def median_sliding_window(nums: list[int], k: int) -> list[float]:
    low: list[tuple[int, int]] = []                # max-heap of (-val, idx)
    high: list[tuple[int, int]] = []               # min-heap of (val, idx)
    invalid_low = 0
    invalid_high = 0
    out: list[float] = []

    def prune_low() -> None:
        nonlocal invalid_low
        while low and low[0][1] <= leaving_idx:
            heapq.heappop(low)
            invalid_low -= 1

    def prune_high() -> None:
        nonlocal invalid_high
        while high and high[0][1] <= leaving_idx:
            heapq.heappop(high)
            invalid_high -= 1

    leaving_idx = -1
    for i, x in enumerate(nums):
        # Insert via the routed path.
        heapq.heappush(low, (-x, i))
        heapq.heappush(high, (-low[0][0], low[0][1]))
        heapq.heappop(low)

        # If we've grown past the window, shrink by marking the outgoing ghost.
        if i >= k:
            leaving_idx = i - k
            # The leaving element is in exactly one of the heaps.
            # Mark it as ghost; the prune helpers will remove ghosts at the top.
            # (We use a simple trick: lazy bookkeeping via counters + `prune_*`.)
            real_low = sum(1 for (_, j) in low if j > leaving_idx)
            real_high = sum(1 for (_, j) in high if j > leaving_idx)
            # Recover invalid counts the cheap way for clarity:
            invalid_low = len(low) - real_low
            invalid_high = len(high) - real_high
            prune_low()
            prune_high()

        # Rebalance using *real* sizes (len - invalid).
        real_low = len(low) - invalid_low
        real_high = len(high) - invalid_high
        if real_low > real_high + 1:
            heapq.heappush(high, (-low[0][0], low[0][1]))
            heapq.heappop(low)
            prune_high()
        elif real_high > real_low:
            heapq.heappush(low, (-high[0][0], high[0][1]))
            heapq.heappop(high)
            prune_low()

        if i >= k - 1:
            real_low = len(low) - invalid_low
            real_high = len(high) - invalid_high
            if real_low > real_high:
                out.append(float(-low[0][0]))
            else:
                out.append((-low[0][0] + high[0][0]) / 2.0)

    return out
```

The code is gnarlier than Flavor 1 — **welcome to lazy deletion**. The simpler pedagogical implementation uses Python's `SortedList` (from `sortedcontainers`):

```python
from sortedcontainers import SortedList

def median_sliding_window_sorted(nums: list[int], k: int) -> list[float]:
    window: SortedList[int] = SortedList()
    out: list[float] = []
    for i, x in enumerate(nums):
        window.add(x)
        if len(window) > k:
            window.remove(nums[i - k])
        if len(window) == k:
            if k % 2:
                out.append(float(window[k // 2]))
            else:
                out.append((window[k // 2 - 1] + window[k // 2]) / 2.0)
    return out
```

`SortedList` gives O(log k) add/remove/index. In an interview, **always** mention both approaches: heap+lazy-deletion is the textbook two-heaps pattern; `SortedList` is the pragmatic answer.

#### Dry run on `nums = [1, 3, -1, -3, 5, 3, 6, 7]`, `k = 3`

Window snapshots and medians:

| Window | Sorted | Median |
|--------|--------|--------|
| [1, 3, -1] | [-1, 1, 3] | 1 |
| [3, -1, -3] | [-3, -1, 3] | -1 |
| [-1, -3, 5] | [-3, -1, 5] | -1 |
| [-3, 5, 3] | [-3, 3, 5] | 3 |
| [5, 3, 6] | [3, 5, 6] | 5 |
| [3, 6, 7] | [3, 6, 7] | 6 |

Output: `[1, -1, -1, 3, 5, 6]` ✓.

#### Complexity

- **Time:** O(n log k) with either approach.
- **Space:** O(k).

---

### Deep-dive 3 — IPO (LC 502)

> You have `k` rounds of investment. In each round you can pick one project. Each project has a `capital` requirement and a `profit`. You start with `w` capital. After picking a project, your capital becomes `w + profit`. Maximize your final capital.

A two-stage greedy:

1. Among projects you can afford right now, pick the most profitable. (max-heap of profits)
2. As capital grows, more projects become affordable. (min-heap of capital, drained as `w` grows)

#### Code (re-stated)

```python
import heapq

def find_maximized_capital(
    k: int, w: int, profits: list[int], capital: list[int]
) -> int:
    pending = list(zip(capital, profits))
    heapq.heapify(pending)              # min-heap by capital
    available: list[int] = []           # max-heap of profits (negated)

    for _ in range(k):
        while pending and pending[0][0] <= w:
            _, p = heapq.heappop(pending)
            heapq.heappush(available, -p)
        if not available:
            break
        w += -heapq.heappop(available)
    return w
```

#### Dry run on `k = 2, w = 0, profits = [1, 2, 3], capital = [0, 1, 1]`

| Round | `w` start | Move from `pending` to `available` | Pop best from `available` | `w` end |
|-------|-----------|-----------------------------------|---------------------------|---------|
| 1 | 0 | (0, 1) → -1 (only this is affordable) | profit=1 | 1 |
| 2 | 1 | (1, 2), (1, 3) → -2, -3 | profit=3 | 4 |

Output: 4. ✓

The greedy "always take the highest-profit affordable" is provably optimal here because every project costs the same (one round), so the greedy choice never closes off a better option.

#### Why two heaps and not one?

You **could** sort `pending` by capital and use a single max-heap of profits — drain `pending` into the max-heap as `w` grows. That's actually what the code does (the min-heap on `pending` is used only for "pop next-cheapest" semantics; pre-sorting and using an index pointer is identical complexity). The two-heap framing is the conceptual trick: **one heap for filtering by criterion A, the other for ranking by criterion B**.

#### Complexity

- **Time:** O((n + k) log n).
- **Space:** O(n).

---

## 🐛 Common bugs

1. **Forgetting to negate for max-heap.** Python's `heapq` is min-heap only. Either negate values or use `(-priority, payload)` tuples.
2. **Off-by-one in the median balance condition.** `len(low) > len(high) + 1` and `len(high) > len(low)` (lefty bias) — *not* both `> +1`. Pick a side.
3. **Lazy deletion: counting heap length as the "real" size.** It includes ghosts. Maintain a separate `valid_count` or compare `len - ghosts` everywhere.
4. **IPO: comparing `pending[0][0] < w` instead of `<= w`.** A project with capital exactly equal to your current capital is affordable.
5. **Tied projects with equal capital but different profits — using a single key.** Always store tuples; tie-break by index or by the secondary criterion.
6. **Heappush of mutable objects.** Heap re-orderings call `<` on stored items. If the items are dicts or unsortable types, you'll get `TypeError`. Wrap in `(key, idx, payload)` tuples — `idx` breaks ties.
7. **Sliding-window median: prune *only* when ghost is at the top.** Pruning anywhere else is O(n).
8. **Median over integers that you average — integer division by accident.** Cast to float (`/ 2.0`) or you'll quietly drop the .5.

---

## 🗣️ Interviewer phrasings to recognize

- "Find the running median as numbers stream in." → Flavor 1.
- "Median of every k-window." → Flavor 3 (lazy deletion) or `SortedList`.
- "Pick at most k projects to maximize capital." → Flavor 2 (IPO).
- "Each item has two attributes; sort by one, weight by the other." → Difference balancing (LC 1383).
- "Earliest day to finish all tasks given prerequisites and durations." → Earliest-deadline-first heap.
- "K closest points / k smallest sums." → Boundary heap (single-heap or two-heap variants).

---

## 🧭 Connections to other patterns

- **Top-K elements (single heap)** — degenerate two-heaps where one heap is empty / fixed-size.
- **Sliding Window** ([01-sliding-window.md](01-sliding-window.md)) — sliding median is a window problem; some prefer `SortedList` over two-heaps for clarity.
- **Greedy + sort** — Flavor 2 (IPO) is "sort then heap"; many greedy-schedule problems share this skeleton.
- **K-way Merge** — Smallest Range Covering K Lists (LC 632) uses k-pointer heap, a generalisation of the running-min idea.
- **Two Pointers** ([02-two-pointers.md](02-two-pointers.md)) — fixed-size two-heap balancing has a "pointer" feel where the boundary index between halves is implicit.

---

## ✅ Self-check — 8 questions

??? question "1. Why use two heaps instead of a single sorted list?"
    Insertion into a Python `list` to keep it sorted is O(n) per move. Two heaps give O(log n) per move and O(1) median. `sortedcontainers.SortedList` is O(log n) too and is sometimes preferred for clarity, but `heapq` is in the stdlib.

??? question "2. Why is the routed insertion (`push to low, pop from low, push to high, maybe rebalance`) preferred over branching on `num < low[0]`?"
    Branchless code is harder to off-by-one and reads cleaner. Both are O(log n). The routed form also self-corrects the order invariant for free.

??? question "3. What goes wrong if you allow `len(low) - len(high)` to exceed 1 in absolute value?"
    The median computation breaks. Odd count: median is `low[0]` only if `low` has more elements; if `high` has more, the median is `high[0]`. Even count: average the two tops. Without the size invariant you can't tell which case you're in.

??? question "4. In IPO, why is greedy correct?"
    Every round you must pick exactly one project, and projects don't expire. Among affordable projects, picking the most profitable can never hurt — it raises your capital the most, unlocking the most future projects. Exchange argument: any "wait and pick later" strategy can be improved by swapping in the better project now.

??? question "5. How does lazy deletion compare to maintaining two heaps with `dict` lookup for removal?"
    A `dict` of value → heap-index lets you remove in O(log n), but Python's `heapq` doesn't expose internal positions, so you'd implement a custom heap. Lazy deletion uses stdlib heaps and amortizes the cleanup cost. Same Big-O, much less code.

??? question "6. Why doesn't `SortedList` make two-heaps obsolete?"
    Heap operations are constant-factor faster for very large streams, and `sortedcontainers` is third-party. Interviews that allow only stdlib insist on heaps.

??? question "7. How would you adapt two-heaps to track the running 90th percentile?"
    Generalise to two heaps with sizes proportional to the percentile. For 90% you'd keep `low` at 9× the size of `high`; the boundary value is the percentile. Rebalance after every insert. Extends to any quantile.

??? question "8. Outline how to handle a stream where elements can also be *deleted*."
    Use lazy deletion: keep a `removed: dict[value, count]` map. When popping a heap top, check the map; if marked removed, decrement and pop again. Maintain the order invariant by routing every insert/delete through the rebalance routine. Same Big-O, more bookkeeping.

---

> **Next pattern up:** Subsets / Backtracking — the recursive "include/exclude" tree, permutations, combinations, palindrome partitioning, and the master template for every "generate all valid X" problem (page coming next).
