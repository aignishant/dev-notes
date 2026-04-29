# Heap & priority queue — common across all companies

> When the problem says "top K", "median of stream", or "merge K", reach for a heap before anything else.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

A heap is a comparison structure that exposes the min (or max) in O(log n). Python's `heapq` is a **min-heap**; for a max-heap, push negatives. Three patterns dominate interviews: "top K via size-K heap", "merge K sorted things via heap of pointers", and "two heaps balanced for the median." Get those three reflexive and you'll fly through this section.

## Pattern frequency

| Pattern | Frequency | Typical signal |
|---|---|---|
| Top-K with size-K heap | ⭐⭐⭐⭐⭐ | "top K", "K largest", "K closest" |
| Merge K sorted | ⭐⭐⭐⭐ | "merge K lists/arrays" |
| Two heaps (median) | ⭐⭐⭐⭐ | "median of stream", "sliding median" |
| Greedy with heap | ⭐⭐⭐ | task scheduler, reorganize string |
| Heap + lazy deletion | ⭐⭐ | sliding window median |

## Problem set

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Kth Largest Element in Array | Medium | Quickselect / size-K heap | 215 |
| 2 | Kth Largest Element in Stream | Easy | Size-K min-heap | 703 |
| 3 | Top K Frequent Elements | Medium | Counter + heap / bucket | 347 |
| 4 | Top K Frequent Words | Medium | Heap with custom key | 692 |
| 5 | Merge K Sorted Lists | Hard | Heap of head pointers | 23 |
| 6 | K Closest Points to Origin | Medium | Size-K max-heap | 973 |
| 7 | Find Median from Data Stream | Hard | Two heaps | 295 |
| 8 | Sliding Window Median | Hard | Two heaps + lazy delete | 480 |
| 9 | Find K Closest Elements | Medium | Binary search / heap | 658 |
| 10 | Reorganize String | Medium | Greedy max-heap | 767 |
| 11 | Task Scheduler | Medium | Greedy max-heap + cooldown | 621 |
| 12 | Last Stone Weight | Easy | Max-heap | 1046 |
| 13 | Furthest Building You Can Reach | Medium | Heap of climbs | 1642 |
| 14 | Maximum Subsequence Score | Medium | Sort + size-K min-heap | 2542 |
| 15 | Smallest Range Covering K Lists | Hard | K-way merge with heap | 632 |

---

## Deep-dive 1 — Find Median from Data Stream (LC 295)

??? question "Why two heaps?"
    The median lives in the middle of a sorted list. We don't need *all* the data sorted — only the boundary between the small half and the large half. A max-heap on the small half + a min-heap on the large half gives O(1) median, O(log n) insert. Asked at Google, Amazon, Bloomberg, Microsoft.

The invariants:

- `small` is a **max-heap** holding the smaller half.
- `large` is a **min-heap** holding the larger half.
- `len(small) == len(large)` or `len(small) == len(large) + 1` (small can be one bigger when count is odd).
- Every element in `small` ≤ every element in `large`.

The dance on `addNum(num)`:

1. Push to `small` (max-heap, so push `-num`).
2. Move `small`'s top to `large` (it might belong on the right).
3. If `large` got bigger than `small`, move `large`'s top back to `small` (we want `small` ≥ `large` in size).

```python linenums="1"
from __future__ import annotations
import heapq


class MedianFinder:
    """Two-heap balanced median tracker.

    small: max-heap (negated) of the lower half.
    large: min-heap of the upper half.
    Invariant: 0 <= len(small) - len(large) <= 1.
    """

    def __init__(self) -> None:
        self.small: list[int] = []   # max-heap (store as -value)
        self.large: list[int] = []   # min-heap

    def addNum(self, num: int) -> None:
        # Step 1: provisionally place into small.
        heapq.heappush(self.small, -num)

        # Step 2: rebalance ordering — small's top might belong in large.
        heapq.heappush(self.large, -heapq.heappop(self.small))   # (1)

        # Step 3: rebalance sizes — small must be >= large in size.
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))  # (2)

    def findMedian(self) -> float:
        if len(self.small) > len(self.large):
            return float(-self.small[0])                            # (3)
        return (-self.small[0] + self.large[0]) / 2.0               # (4)
```

1. Always push the small-top into large — guarantees the ordering invariant in one move.
2. After step 2, sizes might be wrong; pull one back if needed.
3. Odd count ⇒ small has the extra element ⇒ its max is the median.
4. Even count ⇒ average the two middles.

??? note "Complexity"
    - `addNum` **O(log n)** — three heap ops.
    - `findMedian` **O(1)**.
    - Space **O(n)**.

??? tip "Sliding window variant (LC 480)"
    Same two-heap idea, but you also need to *remove* the element leaving the window. Use **lazy deletion**: keep a `to_remove` counter dict, only purge from the top when the top has been marked. Re-balance after every step.

---

## Deep-dive 2 — Merge K Sorted Lists (LC 23)

??? question "Why a heap and not divide-and-conquer?"
    Both work — divide-and-conquer pairs lists in O(N log K). The heap approach is more **online**: you can interleave reads from many streams without collecting them all first. Plus the heap gives a clean template for any K-way merge.

The plan:

- Push the **head node** of each non-empty list into a min-heap, keyed by `node.val`.
- Pop the smallest, attach to result, push its `.next` if any.
- Repeat until empty.

The wrinkle: Python's `heapq` compares whole tuples, so if two nodes share a value it tries to compare `ListNode` objects directly — which raises. Two fixes: include a tiebreaker counter, or define `__lt__` on `ListNode`. The class-based approach is cleaner.

```python linenums="1"
from __future__ import annotations
import heapq


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None) -> None:
        self.val = val
        self.next = next

    # Tiebreaker so heapq can compare nodes with equal vals.
    def __lt__(self, other: "ListNode") -> bool:    # (1)
        return self.val < other.val


class Solution:
    def mergeKLists(self, lists: list[ListNode | None]) -> ListNode | None:
        heap: list[ListNode] = []

        # Seed: one node per list.
        for head in lists:
            if head is not None:
                heapq.heappush(heap, head)          # (2)

        dummy = ListNode()
        tail = dummy

        while heap:
            node = heapq.heappop(heap)              # smallest current head
            tail.next = node
            tail = node
            if node.next is not None:
                heapq.heappush(heap, node.next)     # (3) feed next of that list

        return dummy.next
```

1. Without `__lt__`, `heapq` raises `TypeError: '<' not supported between instances of 'ListNode'` on val ties.
2. Heap holds at most K nodes at any time — one per active list.
3. The "next of the popped one" is the only new candidate — one push per pop.

??? note "Complexity"
    Let `N` = total nodes, `K` = number of lists.

    - Time **O(N log K)** — each node is pushed and popped once; heap size is at most K.
    - Space **O(K)** for the heap (output list reuses input nodes).

??? tip "Alternative: tuple with counter (no class change)"
    If you can't modify `ListNode`, push `(node.val, idx, node)` where `idx` is a monotonically-increasing counter — Python compares the int `idx` instead of falling through to `node`.
    ```python linenums="1"
    counter = itertools.count()
    heapq.heappush(heap, (node.val, next(counter), node))
    ```

---

## Common gotchas

!!! warning "Things that bite people"
    - **Max-heap** — Python only ships min-heap. Push `-x`, pop and negate. Don't forget the negate on read.
    - **Top K** — keep a heap of size K, not size N. For "K largest" use a **min-heap** of size K (pop the smallest when size > K) — counter-intuitive but correct.
    - **Custom comparator** — `heapq` has no `key=` parameter. Either push tuples `(priority, item)` or wrap items in a class with `__lt__`.
    - **Top K Frequent Words** — ties go to lexicographic order. Push `(-count, word)` so words sort ascending on equal counts.
    - **Sliding window median** — naive remove is O(n). Use lazy deletion or a sorted container (`sortedcontainers.SortedList`).

## 🃏 Cheatsheet

| Move | When | Skeleton |
|---|---|---|
| Size-K min-heap | top K largest | push, pop if `len > K` ⇒ heap holds the K largest |
| Size-K max-heap | top K smallest | push `-x`, pop if `len > K` |
| Merge K | K sorted streams | seed heap with head of each, pop+advance |
| Two heaps | running median | small max-heap, large min-heap, balance |
| Greedy heap | scheduler, reorganize | pop most-frequent, hold in cooldown bucket |
| Lazy delete | sliding window heap | `to_remove` dict, purge top opportunistically |

??? tip "Heap operation reference (Python)"
    ```python linenums="1"
    import heapq
    h: list[int] = []
    heapq.heappush(h, x)            # O(log n)
    smallest = heapq.heappop(h)     # O(log n)
    smallest = h[0]                 # O(1) peek
    heapq.heappushpop(h, x)         # push then pop (cheaper than two ops)
    heapq.heapreplace(h, x)         # pop then push
    heapq.nlargest(k, iterable)     # O(n log k) — convenient for top-K one-shot
    heapq.nsmallest(k, iterable)
    heapq.heapify(lst)              # O(n) in-place
    ```
