# Top-K Elements

> "Give me the **k** largest / smallest / closest / most-frequent." Heaps were *invented* for this. The trick that separates juniors from seniors: use a heap of **size k**, not size n. Then the right answer to "what's the time complexity?" is **O(n log k)**, not O(n log n) — and for k ≪ n that gap is the difference between passing and not. The QuickSelect alternative trades worst-case guarantees for an average O(n) that's usually faster in practice.

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 23)</span>

---

## 📖 What is the top-K pattern?

Whenever a problem asks for "the k largest / smallest / closest / most-frequent / kth-something," you almost never need the full sorted order. You need just enough order to know **which k elements survive and what the boundary value is**. That's exactly what a heap maintains in O(log k) per insertion.

The mental shift is this: a heap of size **k** isn't a sorted list — it's a *cutoff line*. You walk through n elements; for each one you ask "should this displace the current worst-of-the-best?" If yes, swap it in. The heap's root is always the *threshold* — the easiest one to evict. After one pass through n items you have your top-k for O(n log k) total work, and you only ever held k items in memory.

There's also a lower-bound algorithm here — **QuickSelect** — which doesn't even maintain a heap. It uses partition-and-recurse to find the kth element in average O(n) time (worst case O(n²) without good pivoting). It's the algorithm of choice when you don't need the top-k *sorted*, just *separated*.

!!! tip "The signal — when to reach for top-K"
    Reach for it when you see:

    - "Find the **k** largest / smallest / closest / most-frequent."
    - "Return the **k**th X." (kth largest, kth smallest, kth closest)
    - "Top **k** rows / points / words / words-by-frequency."
    - A streaming problem: "as items arrive, maintain the top-k so far."

    The two-line tell:

    - You don't need the full sorted output, just the top slice.
    - k is much smaller than n (otherwise just sort: O(n log n) wins).

    Don't reach for it when:

    - You need *all* elements in sorted order — just sort.
    - The data has special structure (bounded range, frequency, etc.) — bucket sort or counting sort can hit O(n).

---

## 🧩 The three flavors

### Flavor 1: Min-heap of size k for top-k *largest*

Walk through every element. Push it onto a min-heap. If the heap exceeds size k, pop the smallest. After processing all n elements, the heap holds the k largest, and its root is the kth largest.

```python
import heapq

def k_largest(nums: list[int], k: int) -> list[int]:
    heap: list[int] = []                              # (1) min-heap; root is current threshold
    for x in nums:
        heapq.heappush(heap, x)                       # (2) O(log k)
        if len(heap) > k:
            heapq.heappop(heap)                       # (3) evict the worst-of-the-best
    return heap                                       # (4) unsorted, but contains the top k
```

1. Python's `heapq` is a **min-heap** — that's what we want for top-k *largest* (the root is the easiest to displace).
2. Push first, *then* check size. Avoids comparing-against-root nuance.
3. After the pop, the heap holds exactly k elements — the largest seen so far.
4. The result is the top-k but **not sorted**. If the problem asks for sorted order, do `sorted(heap, reverse=True)` at the end (O(k log k), negligible compared to the O(n log k) main pass).

**Examples:** Kth Largest Element in Array (LC 215), Kth Largest Element in Stream (LC 703 — same heap maintained across calls), K Closest Points to Origin (LC 973 with negated distance).

### Flavor 2: Max-heap of size k for top-k *smallest*

Symmetric. Walk through elements, push the **negation** (Python's `heapq` only does min-heaps), pop when the size exceeds k. The root holds the largest of the small ones — the easiest to displace.

```python
import heapq

def k_smallest(nums: list[int], k: int) -> list[int]:
    heap: list[int] = []                              # max-heap simulated via negation
    for x in nums:
        heapq.heappush(heap, -x)                      # (1) negate on insert
        if len(heap) > k:
            heapq.heappop(heap)                       # pops the most-negative = largest x
    return [-y for y in heap]                         # (2) un-negate at the end
```

1. The negate-on-insert / negate-on-read trick is the standard Python max-heap idiom. Internalise it; you'll write it a hundred times.
2. For tuples (e.g., `(distance, point)`), negate just the comparison key: `(-dist, point)`.

**Examples:** K Closest Points to Origin (LC 973), Find K Closest Elements (LC 658 — though two-pointers wins here).

### Flavor 3: QuickSelect — partition without sorting

When you only need the top-k as an **unordered set**, partition-based selection is faster on average. Pick a pivot, partition the array so smaller-than-pivot elements are on one side and larger on the other, then recurse into the side that contains the kth boundary.

```python
import random

def quickselect_kth_largest(nums: list[int], k: int) -> int:
    """Return the kth largest element. k is 1-indexed."""

    def partition(lo: int, hi: int, pivot_idx: int) -> int:
        pivot = nums[pivot_idx]
        nums[pivot_idx], nums[hi] = nums[hi], nums[pivot_idx]   # (1) move pivot to end
        store = lo
        for i in range(lo, hi):
            if nums[i] > pivot:                                  # (2) "greater first" for kth largest
                nums[store], nums[i] = nums[i], nums[store]
                store += 1
        nums[store], nums[hi] = nums[hi], nums[store]            # (3) put pivot back at boundary
        return store

    def select(lo: int, hi: int, k_idx: int) -> int:
        if lo == hi:
            return nums[lo]
        pivot_idx = random.randint(lo, hi)                       # (4) randomise to avoid O(n²)
        pivot_idx = partition(lo, hi, pivot_idx)
        if k_idx == pivot_idx:
            return nums[k_idx]
        elif k_idx < pivot_idx:
            return select(lo, pivot_idx - 1, k_idx)
        else:
            return select(pivot_idx + 1, hi, k_idx)

    return select(0, len(nums) - 1, k - 1)                       # k - 1 because 0-indexed target
```

1. Standard Lomuto partition: stash pivot at `hi`, partition the prefix, swap pivot back at the end.
2. For *kth largest*, count elements **greater than** the pivot first (left side gets the larger values).
3. After the loop, `store` is the boundary — every index < `store` holds something `> pivot`.
4. **Random pivoting is critical.** Without it, sorted/adversarial input produces O(n²). With it, expected O(n).

**Examples:** Kth Largest Element in Array (LC 215, the canonical example), Wiggle Sort II (LC 324, partition into halves), median-of-medians problems.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Top-k largest (heap) | k biggest elements | Kth Largest in Array (LC 215) | Min-heap of size k |
| 2 | Top-k smallest (heap) | k smallest elements | K Closest Points (LC 973) | Max-heap of size k (negate) |
| 3 | Streaming kth | kth largest as data arrives | Kth Largest in Stream (LC 703) | Persistent heap; constant size k |
| 4 | Top-k closest | k items nearest to a target value | Find K Closest Elements (LC 658) | Heap on distance, or two-pointer window |
| 5 | Top-k frequent | k items with highest count | Top K Frequent (LC 347) | Counter + heap, or **bucket sort O(n)** |
| 6 | QuickSelect | kth-something, unordered output | Kth Largest in Array (LC 215) | Partition + random pivot |
| 7 | Top-k from N sorted lists | merging top-k across sources | (Cousin of K-way Merge) | Heap of `(value, list_id, idx)` |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Kth Largest Element in an Array | 215 | <span class="diff-medium">Medium</span> | Top-k largest / QuickSelect | 📝 |
| 2 | Kth Largest Element in a Stream | 703 | <span class="diff-easy">Easy</span> | Streaming kth | 📝 |
| 3 | K Closest Points to Origin | 973 | <span class="diff-medium">Medium</span> | Top-k smallest | 📝 |
| 4 | Top K Frequent Elements | 347 | <span class="diff-medium">Medium</span> | Top-k frequent | 📝 |
| 5 | Top K Frequent Words | 692 | <span class="diff-medium">Medium</span> | Top-k frequent + tiebreak | 📝 |
| 6 | Sort Characters By Frequency | 451 | <span class="diff-medium">Medium</span> | Top-k frequent (full output) | 📝 |
| 7 | Find K Closest Elements | 658 | <span class="diff-medium">Medium</span> | Top-k closest | 📝 |
| 8 | Last Stone Weight | 1046 | <span class="diff-easy">Easy</span> | Repeated max-extract | 📝 |
| 9 | Reorganize String | 767 | <span class="diff-medium">Medium</span> | Top-k frequent + scheduling | 📝 |
| 10 | Task Scheduler | 621 | <span class="diff-medium">Medium</span> | Top-k frequent + cooldown | 📝 |
| 11 | Kth Smallest Element in a Sorted Matrix | 378 | <span class="diff-medium">Medium</span> | Heap on matrix / bsearch | 📝 |
| 12 | Find K Pairs with Smallest Sums | 373 | <span class="diff-medium">Medium</span> | Heap of pairs | 📝 |
| 13 | The Skyline Problem | 218 | <span class="diff-hard">Hard</span> | Max-heap with lazy deletion | 📝 |
| 14 | Find Median from Data Stream | 295 | <span class="diff-hard">Hard</span> | Two heaps (cousin pattern) | ✅ |
| 15 | Frequency of the Most Frequent Element | 1838 | <span class="diff-medium">Medium</span> | Sliding window (cousin) | 📝 |
| 16 | Maximum Subsequence Score | 2542 | <span class="diff-medium">Medium</span> | Sort + min-heap of size k | 📝 |
| 17 | Minimum Cost to Hire K Workers | 857 | <span class="diff-hard">Hard</span> | Sort + max-heap of size k | 📝 |
| 18 | Find the Kth Largest Integer in the Array | 1985 | <span class="diff-medium">Medium</span> | Top-k largest (string compare) | 📝 |
| 19 | Kth Smallest Prime Fraction | 786 | <span class="diff-hard">Hard</span> | Heap of fraction pairs | 📝 |
| 20 | Kth Largest Sum in a Binary Tree | 2583 | <span class="diff-medium">Medium</span> | BFS + top-k largest | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Kth Largest Element in an Array (LC 215)

> Given an unsorted array `nums` and integer `k`, return the kth largest element. (Not the kth distinct — duplicates count.)

The litmus test for this whole pattern. There are three reasonable approaches: full sort, heap of size k, QuickSelect. Know all three; pick by context.

#### Approach A — Sort (the trivial baseline)

```python
def find_kth_largest_sort(nums: list[int], k: int) -> int:
    return sorted(nums)[-k]
```

O(n log n) time, O(1)-ish extra space (depending on sort impl). Always works; never the right interview answer if a better one exists.

#### Approach B — Heap of size k (the canonical answer)

```python
import heapq

def find_kth_largest_heap(nums: list[int], k: int) -> int:
    heap: list[int] = []
    for x in nums:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]                                   # (1) root = kth largest
```

1. After the loop, the heap holds the k largest. The min-heap root is the smallest of those, i.e., the kth largest overall.

O(n log k) time, O(k) space. **The default answer.** It's also the only one that handles streaming naturally (LC 703).

A one-liner using `heapq.nlargest`:

```python
def find_kth_largest_nlargest(nums: list[int], k: int) -> int:
    return heapq.nlargest(k, nums)[-1]
```

Same complexity; cleanest production code.

#### Approach C — QuickSelect (the "show off" answer)

(See Flavor 3's full code above.) Average O(n), worst O(n²) without good pivots. Beats heap when k is large (close to n/2) — at that point the heap-of-size-k argument loses force.

#### Dry run on `nums = [3, 2, 1, 5, 6, 4]`, `k = 2`

Heap-of-size-k pass:

| Step | Element pushed | Heap (after push) | Action | Heap (after step) |
|------|----------------|-------------------|--------|--------------------|
| 1 | 3 | `[3]` | size ≤ k, keep | `[3]` |
| 2 | 2 | `[2, 3]` | size ≤ k, keep | `[2, 3]` |
| 3 | 1 | `[1, 3, 2]` | size > k, pop 1 | `[2, 3]` |
| 4 | 5 | `[2, 3, 5]` | size > k, pop 2 | `[3, 5]` |
| 5 | 6 | `[3, 5, 6]` | size > k, pop 3 | `[5, 6]` |
| 6 | 4 | `[4, 6, 5]` | size > k, pop 4 | `[5, 6]` |

Final heap `[5, 6]`, root = 5. Output: **5** ✓ (the 2nd largest is 5).

#### Why heap beats sort for k ≪ n

For n = 10⁶, k = 10:

- Sort: ~20 · 10⁶ ≈ 2·10⁷ comparisons.
- Heap: ~3.3 · 10⁶ comparisons (`log₂ 10 ≈ 3.3`).

Six-fold speed-up, *and* the heap version uses O(k) memory while sort might use O(n).

#### Complexity summary

| Approach | Time | Space | When to use |
|----------|------|-------|-------------|
| Sort | O(n log n) | O(n) or O(1) | Baseline; clean code |
| Heap of size k | O(n log k) | O(k) | k ≪ n; streaming |
| QuickSelect | O(n) avg, O(n²) worst | O(1) in-place | Large k; one-shot |

---

### Deep-dive 2 — Top K Frequent Elements (LC 347)

> Given an array of integers and `k`, return the k most frequent elements (any order).

The interesting twist: **bucket sort** beats heap for this specific problem because frequencies are bounded by `n`.

#### Approach A — Heap on a Counter

```python
import heapq
from collections import Counter

def top_k_frequent_heap(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)                            # O(n)
    return heapq.nlargest(k, counts.keys(), key=counts.get)
```

Internally `nlargest` runs a heap of size k on the unique values. Time: O(n + u log k) where `u` is the number of unique elements. Memory: O(u + k).

Hand-rolled equivalent:

```python
def top_k_frequent_heap_manual(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    heap: list[tuple[int, int]] = []                  # (count, value)
    for value, count in counts.items():
        heapq.heappush(heap, (count, value))
        if len(heap) > k:
            heapq.heappop(heap)
    return [value for count, value in heap]
```

#### Approach B — Bucket sort (the O(n) win)

Frequencies live in `[1..n]`. Make `n+1` buckets indexed by frequency; drop each value into the bucket matching its count; walk the buckets from high to low and collect the first k.

```python
from collections import Counter

def top_k_frequent_bucket(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    n = len(nums)
    buckets: list[list[int]] = [[] for _ in range(n + 1)]
    for value, count in counts.items():
        buckets[count].append(value)
    result: list[int] = []
    for freq in range(n, 0, -1):                      # walk high → low
        result.extend(buckets[freq])
        if len(result) >= k:
            return result[:k]
    return result
```

O(n) time, O(n) space. Beats heap whenever k is non-trivial.

#### Dry run on `nums = [1, 1, 1, 2, 2, 3]`, `k = 2`

`Counter` → `{1: 3, 2: 2, 3: 1}`.

Bucket version. n = 6, so 7 buckets:

| Freq | Bucket |
|------|--------|
| 0 | `[]` |
| 1 | `[3]` |
| 2 | `[2]` |
| 3 | `[1]` |
| 4–6 | `[]` |

Walk from 6 down: bucket 3 → result = `[1]`. Bucket 2 → result = `[1, 2]`. Length ≥ k, return `[1, 2]`. ✓

Heap version. `heapq.nlargest(2, {1, 2, 3}, key=counts.get)` keeps a min-heap of size 2:

| Step | Item (val, count) | Heap (min-heap on count) | Action |
|------|-------------------|---------------------------|--------|
| 1 | (1, 3) | `[(3, 1)]` | push |
| 2 | (2, 2) | `[(2, 2), (3, 1)]` | push |
| 3 | (3, 1) | `[(2, 2), (3, 1), (1, 3)]` | push, then pop the smallest count → pop (1, 3) |
| End | — | `[(2, 2), (3, 1)]` | extract values |

Output: `[1, 2]` (order may differ). ✓

#### Choosing between them

- **Bucket sort** for "find k most frequent among n elements where freq ≤ n." Always O(n).
- **Heap** when frequencies aren't bounded (e.g., counting from a stream of unknown length, or sorting by a non-integer key like a float score).

Be ready to discuss both in interviews — the bucket sort answer often impresses.

---

### Deep-dive 3 — K Closest Points to Origin (LC 973)

> Given a list of points and integer `k`, return the k points closest to the origin (Euclidean distance).

The natural fit for **max-heap of size k** in Python via negation.

#### Approach — Max-heap of size k

```python
import heapq

def k_closest(points: list[list[int]], k: int) -> list[list[int]]:
    heap: list[tuple[int, list[int]]] = []
    for x, y in points:
        d2 = x * x + y * y                           # (1) squared distance — no sqrt
        heapq.heappush(heap, (-d2, [x, y]))          # (2) negate for max-heap
        if len(heap) > k:
            heapq.heappop(heap)                      # pops the most-negative = farthest
    return [point for _, point in heap]
```

1. **Squared distance is enough.** `sqrt` is monotone, so the top-k by `d²` matches the top-k by `d`. Skipping `sqrt` saves time and avoids float precision quirks.
2. The negation trick makes Python's min-heap behave as a max-heap. The "worst" survivor (the farthest point) sits at the root — easiest to evict.

#### Why max-heap (not min-heap) here?

We want the k *closest*. The "boundary" is the **kth-closest** point — i.e., the **farthest** of those still in the running. The heap should pop the *worst surviving candidate* whenever we exceed size k, so the root must be the *farthest*. That's a max-heap.

Inverting the rule: top-k *largest* needs the easiest-to-evict to be the *smallest* survivor — i.e., a min-heap. Same pattern, opposite polarity.

#### Dry run on `points = [[1, 3], [-2, 2], [5, 8], [0, 1]]`, `k = 2`

Squared distances: `(1, 3) → 10`, `(-2, 2) → 8`, `(5, 8) → 89`, `(0, 1) → 1`.

| Step | Push | Heap (`-d²` view) | Size > k? | After |
|------|------|--------------------|-----------|-------|
| 1 | `(-10, [1, 3])` | `[(-10, [1, 3])]` | no | `[(-10, …)]` |
| 2 | `(-8, [-2, 2])` | `[(-10, [1, 3]), (-8, [-2, 2])]` | no | both stay |
| 3 | `(-89, [5, 8])` | `[(-89, …), (-8, …), (-10, …)]` | yes — pop `(-89, [5, 8])` | `[(-10, [1, 3]), (-8, [-2, 2])]` |
| 4 | `(-1, [0, 1])` | `[(-10, [1, 3]), (-8, [-2, 2]), (-1, [0, 1])]` | yes — pop `(-10, [1, 3])` | `[(-8, [-2, 2]), (-1, [0, 1])]` |

Final heap: `[(-8, [-2, 2]), (-1, [0, 1])]`. Output: `[[-2, 2], [0, 1]]` ✓ (these are the two closest).

#### Alternative — QuickSelect partition

Same template as LC 215: partition by squared distance, recurse into the side that contains the kth boundary, return `points[:k]`. Average O(n), but in-place mutation.

#### Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort by `d²` | O(n log n) | O(n) | Cleanest code |
| Max-heap of size k | O(n log k) | O(k) | Best when k ≪ n |
| QuickSelect | O(n) avg | O(1) | Best for large k; in-place |

---

## 🐛 Common bugs

1. **Wrong heap polarity.** "Top-k largest" wants a *min-heap* (root = easiest to evict = smallest survivor). "Top-k smallest" wants a *max-heap*. Getting this backwards keeps the wrong elements.
2. **Forgetting Python's `heapq` is min-only.** Negate on push, negate on pop. For tuple keys, negate just the comparison field.
3. **Pushing tuples that contain unhashable / unorderable secondaries.** A tuple `(count, list)` errors when two counts tie because lists aren't orderable. Add a tiebreaker — typically a unique counter or `id()` — or wrap in a `dataclass(order=True)` with `field(compare=False)` on the unorderable field.
4. **Sorting first, then heap.** Defeats the entire purpose. The `O(n log k)` win comes from streaming the input *into* the heap in one pass.
5. **Using `heapq.heapify` then trying to keep size k.** `heapify` is O(n) but produces a heap of size n. Either use `nlargest`/`nsmallest` (which already use the size-k trick) or push one-at-a-time with a size guard.
6. **QuickSelect without random pivots.** Sorted/adversarial input → O(n²). Always randomize or use median-of-three.
7. **Computing `sqrt` for distance comparisons.** Squared distance preserves order. `sqrt` is slow and adds float noise.
8. **Returning the heap when the problem asks for a sorted list.** A heap is not a sorted array — only the root is guaranteed at the boundary. Sort the result if order matters.

---

## 🗣️ Interviewer phrasings to recognize

- "Find the **k** largest / smallest / closest." → Heap of size k (or QuickSelect).
- "Top **k** most frequent." → Counter + heap, *or* bucket sort for O(n).
- "Find the kth X." → QuickSelect for one-shot O(n) average; heap for streaming.
- "As elements arrive, …" → Streaming flavor; heap that's persistent across queries.
- "Return them sorted." → Heap then sort the final k elements (cheap: O(k log k)).
- "Memory is constrained / data doesn't fit in RAM." → Heap of size k explicitly; only k elements held at once.

---

## 🧭 Connections to other patterns

- **Two Heaps** ([09-two-heaps.md](09-two-heaps.md)) — running median = balanced top-half / bottom-half. The "size k" idea generalises to "size n/2 each."
- **K-way Merge** (page coming next) — heap of n list-heads is structurally identical to "top-k from N sorted lists."
- **Sliding Window** ([01-sliding-window.md](01-sliding-window.md)) — sliding window median / max combine windows with a heap or a deque.
- **Modified Binary Search** ([11-modified-binary-search.md](11-modified-binary-search.md)) — Kth Smallest in Sorted Matrix (LC 378) is solvable by both heap-of-rows *and* binary-search-on-the-answer.
- **Greedy** — "schedule the most-frequent task next" (Reorganize String, Task Scheduler) is greedy *driven* by a top-k frequent heap.

---

## ✅ Self-check — 8 questions

??? question "1. Why is heap of size k O(n log k) instead of O(n log n)?"
    Each of the n insertions costs O(log k) because the heap never grows beyond k. The pop-after-push enforces that bound. Compare with sorting-then-slicing, which is O(n log n) regardless of k. For k ≪ n the gap is huge.

??? question "2. For top-k *largest*, why a *min*-heap?"
    The heap's root is the element you're most willing to evict. In top-k-largest, the easiest-to-evict survivor is the *smallest* of the current top-k — that's a min-heap root. New incoming values larger than the root displace it; values smaller stay out.

??? question "3. When does QuickSelect beat heap-of-size-k?"
    When k is large (close to n/2 or larger) — the heap loses its size advantage. QuickSelect's expected O(n) becomes the clear winner. Also when the problem allows in-place mutation of the input and unsorted output, since QuickSelect is O(1) extra space.

??? question "4. Why is bucket sort sometimes better than heap for top-k frequent?"
    Frequencies are bounded by `n`, so you can index `n+1` buckets directly. Walking buckets from high to low collects the top-k in O(n). The heap version is O(n + u log k) where `u` is the unique count — usually slower, never faster.

??? question "5. How do you handle ties in `(count, value)` tuples when value isn't orderable?"
    Add a unique tiebreaker — usually an incrementing counter, `id(value)`, or a stable insertion index. The heap then never compares the unorderable third field. For Python lists/dicts as values, this is essential or you'll hit `TypeError: '<' not supported`.

??? question "6. Why does k-closest-points use squared distance instead of Euclidean?"
    `sqrt` is a monotone increasing function on non-negative inputs, so ranking by `d²` is identical to ranking by `d`. `sqrt` is slower and introduces float-precision noise. Skip it.

??? question "7. How do you maintain top-k as a stream evolves (LC 703)?"
    Keep the size-k heap as instance state. Each new element: push, then pop if size > k. The root is always the kth largest seen so far. Per-update cost is O(log k); space is O(k).

??? question "8. What's a common interview trap when the problem says 'return the k elements sorted'?"
    Returning the heap directly. A heap is partially ordered — only the root is guaranteed. After collecting the top-k via heap, sort the output explicitly (`sorted(heap, reverse=True)` for descending). The extra sort is O(k log k), negligible vs. the main pass.

---

> **Next pattern up:** K-way Merge — using a heap to merge N sorted lists, smallest-range problems, and the "top-k from N sources" generalisation (page coming next).
