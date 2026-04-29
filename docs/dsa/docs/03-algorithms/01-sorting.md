# Sorting

> Nine algorithms, one decision tree, and the answer to "why is Python's `sort()` so fast?"

<span class="phase-status phase-done">Phase 4 — Algorithms</span>

---

## Why sorting still matters in interviews

Sorting itself is rarely the *whole* answer in 2026 — `list.sort()` is one line. But the *idea* of sorting is the foundation of:

- Two-pointer / sweep-line problems (intervals, meeting rooms, skyline).
- Greedy proofs ("sort by deadline, then…").
- Order statistics (k-th element, median of medians).
- External processing of files larger than RAM.

If you can't reason about *why* quicksort is `O(n log n)` average and `O(n²)` worst, you can't reason about most greedy algorithms either.

---

## The comparison table

| Algorithm     | Best       | Average    | Worst      | Space     | Stable | In-place | Use it when…                                  |
|---------------|------------|------------|------------|-----------|--------|----------|-----------------------------------------------|
| Bubble        | O(n)       | O(n²)      | O(n²)      | O(1)      | yes    | yes      | Never. Teaching only.                          |
| Insertion     | O(n)       | O(n²)      | O(n²)      | O(1)      | yes    | yes      | Tiny inputs (n ≤ ~16) or nearly sorted data.   |
| Selection     | O(n²)      | O(n²)      | O(n²)      | O(1)      | no     | yes      | You care about *minimising writes* (e.g. flash). |
| Merge         | O(n log n) | O(n log n) | O(n log n) | O(n)      | yes    | no       | Stable sort, linked lists, external sort.      |
| Quicksort     | O(n log n) | O(n log n) | O(n²)      | O(log n)  | no     | yes      | Default in-memory sort; cache-friendly.        |
| Heapsort      | O(n log n) | O(n log n) | O(n log n) | O(1)      | no     | yes      | Hard worst-case guarantee, no extra memory.    |
| Counting      | O(n + k)   | O(n + k)   | O(n + k)   | O(n + k)  | yes    | no       | Small integer range `k` (e.g. ages, bytes).    |
| Radix (LSD)   | O(d·(n+b)) | O(d·(n+b)) | O(d·(n+b)) | O(n + b)  | yes    | no       | Fixed-width keys (ints, strings of equal len). |
| Bucket        | O(n + k)   | O(n + k)   | O(n²)      | O(n + k)  | yes    | no       | Uniformly distributed floats in `[0, 1)`.      |

Where `n` is item count, `k` is the value range, `d` is digits, `b` is the radix base.

---

## The slow trio (n²)

All three sort by repeatedly making local fixes. They're rarely the right choice but interviewers love asking "explain insertion sort" because it tests whether you really understand invariants.

### Bubble sort

```python linenums="1"
def bubble_sort(a: list[int]) -> None:
    """In-place bubble sort. Stable, O(n²) worst, O(n) on already-sorted."""
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):  # (1)
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:  # (2)
            return
```

1. After pass `i`, the largest `i+1` elements are at the end — no need to re-scan them.
2. Early-exit makes it `O(n)` on sorted input — the only reason this algorithm is mentioned at all.

### Insertion sort

The one slow sort that *is* used in practice — Python's Timsort falls back to it for runs ≤ 32 elements, because the constant factor is tiny.

```python linenums="1"
def insertion_sort(a: list[int]) -> None:
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:  # shift right
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
```

**Invariant**: after iteration `i`, `a[0..i]` is sorted.

### Selection sort

```python linenums="1"
def selection_sort(a: list[int]) -> None:
    for i in range(len(a)):
        min_idx = i
        for j in range(i + 1, len(a)):
            if a[j] < a[min_idx]:
                min_idx = j
        a[i], a[min_idx] = a[min_idx], a[i]
```

Useful trivia: selection sort makes at most `n - 1` swaps, the *fewest* of any comparison sort. If a swap is enormously expensive (think: rearranging 1 GB rows on disk) it's actually the right tool.

---

## Merge sort — the divide-and-conquer baseline

```python linenums="1"
def merge_sort(a: list[int]) -> list[int]:
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left = merge_sort(a[:mid])
    right = merge_sort(a[mid:])
    return _merge(left, right)


def _merge(left: list[int], right: list[int]) -> list[int]:
    out: list[int] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:  # `<=` keeps it stable
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out
```

??? question "Why is merge sort stable?"
    Equal elements: we always take from the *left* half first (`<=`). Since the left half came from earlier indices, equal items keep their original order.

??? tip "Merge sort on linked lists is `O(1)` extra space"
    Splitting a linked list (slow/fast pointer) and merging in-place by re-pointing `.next` doesn't allocate. That's why every "sort a linked list in `O(n log n)` and `O(1) space`" problem is merge sort.

---

## Quicksort — Lomuto vs Hoare partition

Quicksort's Achilles' heel is the partition. Get the partition right, get the sort right.

### Lomuto partition (interview favourite — easier to write)

```python linenums="1"
def quicksort_lomuto(a: list[int], lo: int = 0, hi: int | None = None) -> None:
    if hi is None:
        hi = len(a) - 1
    if lo >= hi:
        return
    p = _lomuto(a, lo, hi)
    quicksort_lomuto(a, lo, p - 1)
    quicksort_lomuto(a, p + 1, hi)


def _lomuto(a: list[int], lo: int, hi: int) -> int:
    pivot = a[hi]
    i = lo - 1
    for j in range(lo, hi):
        if a[j] <= pivot:
            i += 1
            a[i], a[j] = a[j], a[i]
    a[i + 1], a[hi] = a[hi], a[i + 1]
    return i + 1
```

### Hoare partition (faster, fewer swaps)

```python linenums="1"
def quicksort_hoare(a: list[int], lo: int = 0, hi: int | None = None) -> None:
    if hi is None:
        hi = len(a) - 1
    if lo >= hi:
        return
    p = _hoare(a, lo, hi)
    quicksort_hoare(a, lo, p)       # note: include p
    quicksort_hoare(a, p + 1, hi)


def _hoare(a: list[int], lo: int, hi: int) -> int:
    pivot = a[(lo + hi) // 2]
    i, j = lo - 1, hi + 1
    while True:
        i += 1
        while a[i] < pivot: i += 1
        j -= 1
        while a[j] > pivot: j -= 1
        if i >= j:
            return j
        a[i], a[j] = a[j], a[i]
```

!!! warning "The classic quicksort bug"
    Always pick a *good* pivot. `a[lo]` or `a[hi]` is `O(n²)` on already-sorted input — a real footgun. Use median-of-three or `random.choice`. Production sorts (introsort, pdqsort) detect bad recursion depth and switch to heapsort.

---

## Heapsort

`O(n log n)` worst-case with `O(1)` extra space — the only comparison sort that has both.

```python linenums="1"
def heapsort(a: list[int]) -> None:
    n = len(a)
    # 1) build max-heap, bottom-up
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(a, i, n)
    # 2) extract max, place at end
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        _sift_down(a, 0, end)


def _sift_down(a: list[int], i: int, n: int) -> None:
    while True:
        l, r = 2 * i + 1, 2 * i + 2
        largest = i
        if l < n and a[l] > a[largest]: largest = l
        if r < n and a[r] > a[largest]: largest = r
        if largest == i: return
        a[i], a[largest] = a[largest], a[i]
        i = largest
```

Heapsort is *not* stable. It's also slower in practice than quicksort because of poor cache locality (jumps around the array), but its tight worst case makes it the fallback inside introsort.

---

## The non-comparison family

Comparison sorts are bounded by `Ω(n log n)` (proof: decision-tree height). If you have *more structure* — small integer range, fixed-width keys, uniform distribution — you can break that bound.

### Counting sort

```python linenums="1"
def counting_sort(a: list[int], k: int) -> list[int]:
    """Sort values in [0, k). Stable, O(n + k)."""
    count = [0] * k
    for x in a: count[x] += 1
    # prefix sums = "where does this value start in the output?"
    for i in range(1, k):
        count[i] += count[i - 1]
    out = [0] * len(a)
    for x in reversed(a):  # reversed → stable
        count[x] -= 1
        out[count[x]] = x
    return out
```

### Radix sort (LSD)

```python linenums="1"
def radix_sort(a: list[int]) -> list[int]:
    if not a:
        return a
    out = list(a)
    exp = 1
    mx = max(a)
    while mx // exp > 0:
        out = _counting_pass(out, exp)
        exp *= 10
    return out


def _counting_pass(a: list[int], exp: int) -> list[int]:
    count = [0] * 10
    for x in a: count[(x // exp) % 10] += 1
    for i in range(1, 10): count[i] += count[i - 1]
    out = [0] * len(a)
    for x in reversed(a):
        d = (x // exp) % 10
        count[d] -= 1
        out[count[d]] = x
    return out
```

### Bucket sort

```python linenums="1"
def bucket_sort(a: list[float], n_buckets: int = 10) -> list[float]:
    """Assumes input in [0.0, 1.0)."""
    buckets: list[list[float]] = [[] for _ in range(n_buckets)]
    for x in a:
        buckets[int(x * n_buckets)].append(x)
    out: list[float] = []
    for b in buckets:
        b.sort()  # insertion sort in real impls; n is small per bucket
        out.extend(b)
    return out
```

---

## Python's Timsort — what it actually is

`list.sort()` and `sorted()` use **Timsort**, designed by Tim Peters in 2002. It's:

1. A **hybrid**: merge sort for the big picture, *binary* insertion sort for small runs (≤ 32 elements).
2. **Run-aware**: it scans the input for naturally-occurring sorted runs (ascending or strictly descending) and merges them, instead of pretending the input is random.
3. **Stable**, **adaptive** (`O(n)` on already-sorted), **galloping** during merges (jumps ahead when one run dominates).
4. Worst case `O(n log n)`, best case `O(n)`.

**Interview soundbite**: "Python uses Timsort, which is merge sort tuned for real-world data — it exploits existing order, falls back to insertion on small runs, and gallops during merges."

---

## Sorting custom objects with `key=`

```python linenums="1"
from dataclasses import dataclass

@dataclass
class Interval:
    start: int
    end: int

xs = [Interval(3, 5), Interval(1, 4), Interval(1, 2)]

# By start, then by end (lexicographic on tuple)
xs.sort(key=lambda iv: (iv.start, iv.end))

# Descending by length, ties broken by start
xs.sort(key=lambda iv: (-(iv.end - iv.start), iv.start))
```

!!! tip "Why `key=` beats `cmp=`"
    Python 3 removed `cmp=`. The `key` function is called once per element (cached), then comparisons use the cached keys. `cmp` would be called `O(n log n)` times — slower and harder to reason about.

### Stability lets you compose sorts

If you need to sort by *primary* then *secondary* key, sort by the *secondary* key first, then *primary*. Stable sort preserves the secondary order within each primary group. Useful when the keys are computed by separate logic and you don't want to build a tuple.

---

## External sort — bigger than RAM

Files of 100 GB, RAM of 8 GB. You can't load it. The classic solution:

1. **Run generation**: read chunks that fit in RAM, sort each in memory (Timsort), write each sorted chunk to a temp file.
2. **k-way merge**: open all chunk files, use a min-heap of `(value, file_id)` to merge them with `O(n log k)` total work.

`heapq.merge(*iters)` does this for you in Python — it returns a lazy iterator that does k-way merge from any number of sorted inputs.

```python linenums="1"
import heapq, tempfile, os

def external_sort(input_path: str, output_path: str, chunk_size: int = 1_000_000) -> None:
    chunks: list[str] = []
    with open(input_path) as f:
        buf: list[int] = []
        for line in f:
            buf.append(int(line))
            if len(buf) >= chunk_size:
                chunks.append(_flush(buf))
                buf.clear()
        if buf:
            chunks.append(_flush(buf))

    files = [open(p) for p in chunks]
    iters = ((int(line) for line in fp) for fp in files)
    with open(output_path, "w") as out:
        for v in heapq.merge(*iters):
            out.write(f"{v}\n")
    for fp in files: fp.close()
    for p in chunks: os.unlink(p)


def _flush(buf: list[int]) -> str:
    buf.sort()
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "w") as fp:
        for v in buf: fp.write(f"{v}\n")
    return path
```

---

## Interview problems that are really sorting in disguise

### 1. Merge intervals (LeetCode 56)

```python linenums="1"
def merge(intervals: list[list[int]]) -> list[list[int]]:
    intervals.sort(key=lambda x: x[0])
    out: list[list[int]] = []
    for s, e in intervals:
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
```

The whole problem is "sort by start, then sweep". Without sorting it's `O(n²)`; with it, `O(n log n)`.

### 2. K closest points to origin (LeetCode 973)

Three solutions ranked by interviewer impressed-ness:

- **Sort by distance, take first k** — `O(n log n)`. Works, fine.
- **Max-heap of size k** — `O(n log k)`. Better when `k ≪ n`.
- **Quickselect partition** — `O(n)` average. The "wow" answer.

### 3. Sort colors (LeetCode 75) — Dutch national flag

Three values (0, 1, 2), one pass, in place. Use three pointers.

```python linenums="1"
def sort_colors(a: list[int]) -> None:
    lo, mid, hi = 0, 0, len(a) - 1
    while mid <= hi:
        if a[mid] == 0:
            a[lo], a[mid] = a[mid], a[lo]; lo += 1; mid += 1
        elif a[mid] == 2:
            a[mid], a[hi] = a[hi], a[mid]; hi -= 1
        else:
            mid += 1
```

This is a 3-way partition — exactly what pdqsort uses to handle duplicates efficiently.

---

## Common gotchas

!!! warning "Sorting bugs that fail interviews"
    - **Comparing strings as numbers**: `"10" < "2"` is `True` lexicographically. Pass `key=int`.
    - **NaN**: any comparison with `float('nan')` is false; `sort()` may produce surprising orders. Filter NaNs first.
    - **Mutating during sort**: `list.sort()` is in place; if you iterate while sorting, undefined behaviour.
    - **Forgetting stability**: if you re-sort by a new key, you *lose* the previous order *only if* the new sort isn't stable (Timsort is, so you're fine in Python).
    - **Quicksort on sorted input**: pick a random pivot.
    - **Recursion depth on quicksort**: Python's default recursion limit is 1000. Use iterative quicksort or shuffle first.

---

## 🃏 Cheatsheet

- **Default to `list.sort()` / `sorted()`** — Timsort is stable, adaptive, and `O(n log n)`.
- **`key=` over `cmp=`**. Build tuples for multi-key sorts.
- **Stable + repeated sorts** = composable multi-key ordering.
- **Quicksort**: random pivot, Lomuto for clarity, Hoare for speed.
- **Heapsort** when you need worst-case `O(n log n)` and `O(1)` extra space.
- **Counting / radix / bucket** when keys have structure (small range, fixed width, uniform).
- **External sort** = sort chunks → `heapq.merge` them.
- **Interview hot-takes**: merge intervals, k closest points, Dutch flag — all sort-then-sweep.
