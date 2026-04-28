# K-way Merge

> Merging two sorted lists is a warm-up; merging **k** of them is the same idea with one twist — a min-heap of `k` "front-row tickets," one per list, that re-fills as you advance. The technique generalises beyond literal lists: any time you have `k` monotone sources and want them streamed in global order, this is the pattern. The Smallest Range Covering Elements from K Lists trick (LC 632) is the same heap viewed from a different angle.

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 24)</span>

---

## 📖 What is k-way merge?

Two-way merge (the merge step of merge-sort) walks two sorted arrays in lock-step, picking the smaller front element each time — O(n + m) total work. Generalising to **k** sorted sources, the natural data structure is a **min-heap of size k** holding "the next unread element from each source." Each output step pops the global minimum (O(log k)) and pushes the popped source's *next* element. Total work to emit N elements is **O(N log k)**.

The mental model: imagine k vertical columns, each already sorted top-to-bottom. The heap holds **one cursor per column**, always pointing at that column's current head. The smallest cursor wins each round. When a column is exhausted, its cursor leaves the heap.

This generalises to any monotone source — sorted arrays, sorted linked lists, sorted streams, even cross-products like "sums of pairs from two sorted arrays" (LC 373) where the implicit order is `a[i] + b[j]`.

The smallest-range trick (LC 632) flips the question: keep the heap of cursors, *and* track the running maximum across cursors. The window `[min, max]` always covers at least one element from every list — pop-and-advance the min to shrink it.

!!! tip "The signal — when to reach for k-way merge"
    Reach for it when:

    - You have **k sorted sources** and need them emitted/consumed in global order.
    - You're asked for the **kth smallest from k sorted sources** (LC 378 Sorted Matrix, LC 373 Smallest Pairs).
    - The phrasing involves "**range covering elements from each of k lists**" — that's LC 632 directly.

    The two-line tell:

    - The inputs are individually sorted.
    - You need a global ordering, but only the front of each source matters at any moment.

    Don't reach for it when:

    - The sources aren't sorted — sort them first or use top-K instead.
    - k = 2 — just use two-pointer merge, log(2) overhead is silly.

---

## 🧩 The three flavors

### Flavor 1: Heap of `(value, list_id, idx)` for sorted-array merge

The canonical shape. Push the head of each list into a min-heap. Pop the global minimum, emit it, push the next element from the same list (if any). Repeat until heap empty.

```python
import heapq

def merge_k_sorted(lists: list[list[int]]) -> list[int]:
    heap: list[tuple[int, int, int]] = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))      # (1) seed: head of each list
    out: list[int] = []
    while heap:
        val, list_id, idx = heapq.heappop(heap)
        out.append(val)
        if idx + 1 < len(lists[list_id]):             # (2) advance this list's cursor
            nxt = lists[list_id][idx + 1]
            heapq.heappush(heap, (nxt, list_id, idx + 1))
    return out
```

1. The seed phase puts `k` items into the heap. Each `(value, list_id, idx)` tuple uniquely identifies "I came from list `list_id` and was at position `idx`."
2. After emitting one value, push only the *next* element from the same list. The heap stays at size ≤ k throughout.

**Why the `list_id` field?** Two purposes: (a) it tells you which list to advance after a pop; (b) it breaks ties when two lists have equal values, since `int` and tuples are orderable but two `int`s alone with `list` payload would crash on tie. The integer `list_id` is a clean, free tiebreaker.

**Examples:** Merge k Sorted Lists (LC 23), Merge k Sorted Arrays (classical), Smallest Range Covering Elements from K Lists (LC 632 — same skeleton, different question).

### Flavor 2: Heap of ListNode pointers (linked-list merge)

For linked lists, the heap holds the **head node** of each list. Pop the smallest, splice it onto the output tail, push the popped node's `.next` if non-null. Same O(N log k), but no array-index bookkeeping.

```python
import heapq
from dataclasses import dataclass, field

@dataclass(order=True)
class HeapItem:
    val: int
    list_id: int
    node: "ListNode" = field(compare=False)           # (1) skip node in compare

def merge_k_lists(lists: list["ListNode"]) -> "ListNode":
    heap: list[HeapItem] = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, HeapItem(head.val, i, head))
    dummy = ListNode(0)
    tail = dummy
    while heap:
        item = heapq.heappop(heap)
        tail.next = item.node                         # (2) splice in
        tail = tail.next
        if item.node.next:
            nxt = item.node.next
            heapq.heappush(heap, HeapItem(nxt.val, item.list_id, nxt))
    tail.next = None                                  # (3) clean terminator
    return dummy.next
```

1. `field(compare=False)` keeps the heap from comparing `ListNode` objects (which aren't orderable). The `(val, list_id)` prefix is enough to break ties.
2. Splice the actual node — no allocation, the original nodes get re-linked.
3. Critical: nodes you splice in still carry their old `.next` pointers; sever the tail explicitly or you might emit stale tails.

**Examples:** Merge k Sorted Lists (LC 23 — the canonical linked-list version), interview variants asking for "in-place" k-way merge of LL inputs.

### Flavor 3: The "covering window" variant — Smallest Range (LC 632)

Same heap of cursors, but maintain the running **maximum across cursors** alongside. The window `[min, max]` (where `min` is the heap root) always covers at least one element from each list. Each step: record window if better, pop the min and advance that list's cursor (which updates the max if the new value is larger).

```python
import heapq

def smallest_range(lists: list[list[int]]) -> list[int]:
    heap: list[tuple[int, int, int]] = []
    cur_max = -10**18
    for i, lst in enumerate(lists):
        heapq.heappush(heap, (lst[0], i, 0))
        cur_max = max(cur_max, lst[0])

    best_lo, best_hi = -10**9, 10**9                  # (1) sentinel "infinitely wide"
    while True:
        cur_min, list_id, idx = heapq.heappop(heap)
        if cur_max - cur_min < best_hi - best_lo:     # (2) tighter window
            best_lo, best_hi = cur_min, cur_max
        if idx + 1 == len(lists[list_id]):            # (3) one list exhausted → stop
            break
        nxt = lists[list_id][idx + 1]
        cur_max = max(cur_max, nxt)
        heapq.heappush(heap, (nxt, list_id, idx + 1))

    return [best_lo, best_hi]
```

1. Use any sentinel wider than the input range. Safe values: `[-10**9, 10**9]` for LC 632's input bounds.
2. The min lives at the heap root; the max is tracked by hand. Both update O(1) per step (advance is O(log k)).
3. The first list to run out is when you must stop — you can no longer cover all k lists. Whatever window was best up to then is the answer.

**Examples:** Smallest Range Covering Elements from K Lists (LC 632), variants where the cost function uses both endpoints of the cursor window.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Merge k sorted arrays | one global sorted output | Merge k Sorted Arrays | Heap of `(val, list_id, idx)` |
| 2 | Merge k sorted linked lists | LL splice-in version | Merge k Sorted Lists (LC 23) | Heap of `(val, list_id, node)` |
| 3 | Smallest range covering k lists | tightest `[lo, hi]` covering one from each | Smallest Range (LC 632) | Heap of cursors + tracked max |
| 4 | Kth smallest in sorted matrix | matrix as k sorted rows/columns | Kth Smallest in Sorted Matrix (LC 378) | Heap of row heads, pop k times |
| 5 | K smallest pairs | sums of pairs across two sorted arrays | Find K Pairs with Smallest Sums (LC 373) | Heap seeded with `(a[i] + b[0], i, 0)` |
| 6 | Top-k from streams | streaming variant of merge | (interview) | Heap that admits new elements as they arrive |
| 7 | Sorted matrix flatten | row-by-row k-way merge | Smallest Number in Multiplication Table (LC 668 alt) | Same heap; different bookkeeping |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Merge k Sorted Lists | 23 | <span class="diff-hard">Hard</span> | Merge k LL | 📝 |
| 2 | Smallest Range Covering Elements from K Lists | 632 | <span class="diff-hard">Hard</span> | Smallest range | 📝 |
| 3 | Find K Pairs with Smallest Sums | 373 | <span class="diff-medium">Medium</span> | K smallest pairs | 📝 |
| 4 | Kth Smallest Element in a Sorted Matrix | 378 | <span class="diff-medium">Medium</span> | Sorted matrix kth | 📝 |
| 5 | Merge Two Sorted Lists | 21 | <span class="diff-easy">Easy</span> | Two-way warm-up | 📝 |
| 6 | Ugly Number II | 264 | <span class="diff-medium">Medium</span> | Three-pointer (cousin) | 📝 |
| 7 | Super Ugly Number | 313 | <span class="diff-medium">Medium</span> | k-pointer (cousin) | 📝 |
| 8 | Find K-th Smallest Pair Distance | 719 | <span class="diff-hard">Hard</span> | Bsearch on answer (cousin) | 📝 |
| 9 | Kth Smallest Number in Multiplication Table | 668 | <span class="diff-hard">Hard</span> | Bsearch on answer (cousin) | 📝 |
| 10 | Sliding Window Median | 480 | <span class="diff-hard">Hard</span> | Two heaps (cousin) | ✅ |
| 11 | The Skyline Problem | 218 | <span class="diff-hard">Hard</span> | Heap with lazy deletion | 📝 |
| 12 | Meeting Rooms II | 253 | <span class="diff-medium">Medium</span> | Min-heap of end times | ✅ |
| 13 | Reorganize String | 767 | <span class="diff-medium">Medium</span> | Heap (cousin) | 📝 |
| 14 | Task Scheduler | 621 | <span class="diff-medium">Medium</span> | Heap (cousin) | 📝 |
| 15 | Find Median from Data Stream | 295 | <span class="diff-hard">Hard</span> | Two heaps (cousin) | ✅ |
| 16 | Top K Frequent Elements | 347 | <span class="diff-medium">Medium</span> | Top-k (cousin) | ✅ |
| 17 | Kth Largest Element in an Array | 215 | <span class="diff-medium">Medium</span> | Top-k (cousin) | ✅ |
| 18 | Sort a nearly sorted (k-sorted) array | (classic) | <span class="diff-medium">Medium</span> | Heap of size k+1 | 📝 |
| 19 | Merge Sorted Array | 88 | <span class="diff-easy">Easy</span> | Two-pointer (cousin) | ✅ |
| 20 | Smallest Number Range II | 910 | <span class="diff-medium">Medium</span> | Sort + sweep (cousin) | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Merge k Sorted Lists (LC 23)

> Merge `k` sorted linked lists into one sorted linked list. Return its head.

The canonical example. Three legitimate approaches; know all three.

#### Approach A — Heap of nodes

```python
import heapq
from dataclasses import dataclass, field

@dataclass(order=True)
class HeapItem:
    val: int
    list_id: int
    node: "ListNode" = field(compare=False)

def merge_k_lists(lists: list["ListNode"]) -> "ListNode":
    heap: list[HeapItem] = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, HeapItem(head.val, i, head))
    dummy = ListNode(0)
    tail = dummy
    while heap:
        item = heapq.heappop(heap)
        tail.next = item.node
        tail = tail.next
        if item.node.next:
            nxt = item.node.next
            heapq.heappush(heap, HeapItem(nxt.val, item.list_id, nxt))
    tail.next = None
    return dummy.next
```

**Time:** O(N log k) — N total nodes, each push/pop is O(log k). **Space:** O(k) for the heap.

#### Approach B — Pairwise merge (divide & conquer)

Repeatedly merge pairs of lists. After ⌈log k⌉ rounds, you have one merged list.

```python
def merge_two(a: "ListNode", b: "ListNode") -> "ListNode":
    dummy = ListNode(0)
    tail = dummy
    while a and b:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a else b
    return dummy.next

def merge_k_lists_dc(lists: list["ListNode"]) -> "ListNode":
    if not lists:
        return None
    while len(lists) > 1:
        merged = []
        for i in range(0, len(lists), 2):
            a = lists[i]
            b = lists[i + 1] if i + 1 < len(lists) else None
            merged.append(merge_two(a, b))
        lists = merged
    return lists[0]
```

**Time:** O(N log k) — same as heap. **Space:** O(1) extra (no heap, but the recursion-like outer loop). Often *faster in practice* because it has no heap-overhead constant factor.

#### Approach C — Naive concatenate-and-sort

Concatenate values, sort, rebuild list. O(N log N), worse than the others. Mention it for completeness; never the right answer.

#### Dry run on `lists = [[1, 4, 5], [1, 3, 4], [2, 6]]` (heap approach)

Initial heap: `[(1, 0, 1→4→5), (1, 1, 1→3→4), (2, 2, 2→6)]`.

| Step | Pop `(val, list_id)` | Output so far | Heap after push of next |
|------|----------------------|---------------|--------------------------|
| 1 | (1, 0) | `1` | `[(1, 1, 1→3→4), (2, 2, 2→6), (4, 0, 4→5)]` |
| 2 | (1, 1) | `1, 1` | `[(2, 2, 2→6), (4, 0, 4→5), (3, 1, 3→4)]` |
| 3 | (2, 2) | `1, 1, 2` | `[(3, 1, 3→4), (4, 0, 4→5), (6, 2, 6)]` |
| 4 | (3, 1) | `1, 1, 2, 3` | `[(4, 0, 4→5), (6, 2, 6), (4, 1, 4)]` |
| 5 | (4, 0) | `1, 1, 2, 3, 4` | `[(4, 1, 4), (6, 2, 6), (5, 0, 5)]` |
| 6 | (4, 1) | `1, 1, 2, 3, 4, 4` | `[(5, 0, 5), (6, 2, 6)]` (list 1 exhausted) |
| 7 | (5, 0) | `1, 1, 2, 3, 4, 4, 5` | `[(6, 2, 6)]` (list 0 exhausted) |
| 8 | (6, 2) | `1, 1, 2, 3, 4, 4, 5, 6` | `[]` (list 2 exhausted) |

Output: `1 → 1 → 2 → 3 → 4 → 4 → 5 → 6`. ✓

#### Why O(log k) per step matters

For k = 10⁴ and N = 10⁶, each step is ≈ 13 comparisons → 1.3·10⁷ total. The naive "scan all k heads each time" approach would be 10¹⁰. Five orders of magnitude. The heap is the entire performance story.

---

### Deep-dive 2 — Smallest Range Covering Elements from K Lists (LC 632)

> Given `k` sorted lists, find the smallest range `[lo, hi]` such that at least one element from each list falls in `[lo, hi]`. If multiple smallest exist, return the one with smaller `lo`.

The trick that confuses everyone first time: this is **the same algorithm as merge-k-sorted**, but you read off the answer at every step rather than producing an output sequence.

#### The invariant

Maintain a heap of `k` cursors (one per list). At any moment, `heap_root.val = cur_min` is the smallest value across cursors, and `cur_max` (tracked by hand) is the largest. The window `[cur_min, cur_max]` covers exactly one element from each list. To shrink: advance the minimum's cursor (the only direction that *could* tighten the window).

When any list is exhausted, you can no longer cover all k lists — stop. The best window seen so far is the answer.

#### Code (re-stated)

```python
import heapq

def smallest_range(lists: list[list[int]]) -> list[int]:
    heap: list[tuple[int, int, int]] = []
    cur_max = -10**18
    for i, lst in enumerate(lists):
        heapq.heappush(heap, (lst[0], i, 0))
        cur_max = max(cur_max, lst[0])

    best_lo, best_hi = -10**9, 10**9
    while True:
        cur_min, list_id, idx = heapq.heappop(heap)
        if cur_max - cur_min < best_hi - best_lo:
            best_lo, best_hi = cur_min, cur_max
        if idx + 1 == len(lists[list_id]):
            break
        nxt = lists[list_id][idx + 1]
        cur_max = max(cur_max, nxt)
        heapq.heappush(heap, (nxt, list_id, idx + 1))

    return [best_lo, best_hi]
```

#### Dry run on `lists = [[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]`

Initial heap: `[(0, 1, 0), (4, 0, 0), (5, 2, 0)]`. `cur_max = 5`.

| Step | Pop `(min, list, idx)` | Window | Best (so far) | Advance: push next from list | New `cur_max` |
|------|-------------------------|--------|---------------|------------------------------|----------------|
| 1 | (0, 1, 0) | [0, 5] (width 5) | [0, 5] | (9, 1, 1) | 9 |
| 2 | (4, 0, 0) | [4, 9] (width 5) | [0, 5] (tie, keep earlier) | (10, 0, 1) | 10 |
| 3 | (5, 2, 0) | [5, 10] (width 5) | [0, 5] | (18, 2, 1) | 18 |
| 4 | (9, 1, 1) | [9, 18] (width 9) | [0, 5] | (12, 1, 2) | 18 |
| 5 | (10, 0, 1) | [10, 18] (width 8) | [0, 5] | (15, 0, 2) | 18 |
| 6 | (12, 1, 2) | [12, 18] (width 6) | [0, 5] | (20, 1, 3) | 20 |
| 7 | (15, 0, 2) | [15, 20] (width 5) | [0, 5] (tie) | (24, 0, 3) | 24 |
| 8 | (18, 2, 1) | [18, 24] (width 6) | [0, 5] | (22, 2, 2) | 24 |
| 9 | (20, 1, 3) | [20, 24] (width 4) | **[20, 24]** | list 1 exhausted (was idx 3, len 4) → break | — |

Output: `[20, 24]`. ✓

Note step 1's `[0, 5]` had width 5 and so does step 9's `[20, 24]`'s computed width 4 — wait, step 9's width is 24-20 = 4 < 5. So `[20, 24]` is the actual winner.

#### Why advance only the *min*?

If you advanced the max, the new value would be ≥ `cur_max` (because the source is sorted), so `cur_max` doesn't shrink. The window only widens. Advancing the min, on the other hand, may bring the new front-of-list above the old min — which is the only way to get tighter.

#### Why stop the moment any list runs out?

You need *at least one* element from every list. Once one list has no more, no future window can cover it (its cursor is past the end). The current best is final.

#### Complexity

- **Time:** O(N log k) where N is the total element count across lists.
- **Space:** O(k) for the heap.

---

### Deep-dive 3 — Find K Pairs with Smallest Sums (LC 373)

> Given two sorted arrays `nums1`, `nums2` and integer `k`, find the `k` pairs `(u, v)` with the smallest sums where `u ∈ nums1`, `v ∈ nums2`.

This is a sneaky k-way merge. The "k sorted lists" are *implicit* — for each `i ∈ nums1`, the sequence `[(nums1[i], nums2[0]), (nums1[i], nums2[1]), …]` is sorted (because `nums2` is sorted). So we have `len(nums1)` sorted lists; we need the k smallest values across all of them.

#### Naive baseline

Compute all `len(nums1) · len(nums2)` pairs, sort by sum, take the first k. O(n·m log(n·m)) time, O(n·m) memory. Too slow when n,m large and k small.

#### The k-way-merge insight

Seed a min-heap with `(nums1[i] + nums2[0], i, 0)` for `i = 0 .. min(k, len(nums1)) - 1`. (No need to seed more than k cursors — they can't contribute to top-k.) Pop k times; each pop emits the next-smallest pair, then pushes `(nums1[i] + nums2[j+1], i, j+1)` if available.

```python
import heapq

def k_smallest_pairs(nums1: list[int], nums2: list[int], k: int) -> list[list[int]]:
    if not nums1 or not nums2:
        return []
    heap: list[tuple[int, int, int]] = []
    for i in range(min(k, len(nums1))):                # (1) seed at most k cursors
        heapq.heappush(heap, (nums1[i] + nums2[0], i, 0))
    out: list[list[int]] = []
    while heap and len(out) < k:
        s, i, j = heapq.heappop(heap)
        out.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return out
```

1. Seeding only k cursors is the optimisation that turns this into O(k log k) instead of O((n + k) log n). The first `min(k, n)` cursors give every possible smallest-pair candidate.

#### Dry run on `nums1 = [1, 7, 11]`, `nums2 = [2, 4, 6]`, `k = 3`

Initial heap (seed all 3 since k ≥ len(nums1)):

`[(1+2=3, 0, 0), (7+2=9, 1, 0), (11+2=13, 2, 0)]`.

| Step | Pop `(sum, i, j)` | Pair emitted | Push (if j+1 < len2) |
|------|-------------------|--------------|----------------------|
| 1 | (3, 0, 0) | `[1, 2]` | (1+4=5, 0, 1) |
| 2 | (5, 0, 1) | `[1, 4]` | (1+6=7, 0, 2) |
| 3 | (7, 0, 2) | `[1, 6]` | none (j+1 == len2) |

Output: `[[1,2], [1,4], [1,6]]`. ✓

#### Why is this correct?

Claim: at any point, the smallest unemitted pair is in the heap.

Proof sketch: the heap holds, for each *active* `i`, the smallest unemitted pair from row `i`. Any unemitted pair lives in some row; that row's smallest unemitted pair sits in the heap (or was never seeded — but unseeded rows `i ≥ k` have head-pair sum ≥ heap minimum since we seeded the k smallest heads). The heap root is the global smallest unemitted pair. ✓

#### Complexity

- **Time:** O(k log k) — k pops, each O(log k) (heap stays at size ≤ min(n, k)).
- **Space:** O(min(n, k)) for the heap.

---

## 🐛 Common bugs

1. **Forgetting the `list_id` tiebreaker.** When two values tie, the heap then compares the third tuple field — which is often a `list` or `ListNode`, neither orderable. Add a unique integer field as the second component.
2. **Pushing all elements upfront.** Defeats the size-k bound. The pattern is "seed k, then push one-per-pop." Heap should never exceed k.
3. **Confusing "push next from same list" with "push next globally."** Only the popped list advances. Pushing from another list desyncs the cursors.
4. **Smallest-range: stopping too late.** As soon as the first list exhausts, you must stop. Continuing past that point compares against a list that can no longer contribute, producing wrong windows.
5. **Smallest-range: forgetting `cur_max` updates on push.** The push updates `cur_max`; the pop does **not** (the popped value isn't a max-side change). Easy to invert.
6. **Pairwise merge: forgetting to terminate the merged list.** When one of the two inputs runs out, splice the remaining tail (`tail.next = a if a else b`). Forgetting this gives an infinite list traversal in tests.
7. **Heap-of-pairs: seeding all `n` rows when k is small.** Wastes time and memory. Seed only `min(k, n)` rows.
8. **Sorted-matrix kth: using a heap of size n×n instead of size n.** The heap should hold one cursor per *row* (or *column*) — not every cell.

---

## 🗣️ Interviewer phrasings to recognize

- "Merge **k** sorted lists / arrays / streams." → Heap of k cursors.
- "Smallest range that covers at least one element from each of these k lists." → LC 632 directly.
- "Kth smallest in a sorted matrix" → Heap of row heads (or binary-search-on-answer).
- "Find k pairs with the smallest sum" → Implicit k-way merge across rows of pairs.
- "Continuous stream of sorted batches; emit globally sorted." → Same heap, online.
- "Sort an array where each element is at most k positions from its sorted position" (k-sorted array) → Heap of size k+1.

---

## 🧭 Connections to other patterns

- **Top-K Elements** ([12-top-k-elements.md](12-top-k-elements.md)) — the heap-of-size-k is the same data structure; top-K *evicts* the worst, k-way merge *advances* the popped source. Same heap, different policies.
- **Two Pointers** ([02-two-pointers.md](02-two-pointers.md)) — k = 2 reduces to two-pointer merge. The heap-based k-way merge generalises that idea.
- **Modified Binary Search** ([11-modified-binary-search.md](11-modified-binary-search.md)) — Kth Smallest in Sorted Matrix and Find K-th Smallest Pair Distance are solvable both ways; binary-search-on-answer often beats the heap when the answer space is bounded.
- **Two Heaps** ([09-two-heaps.md](09-two-heaps.md)) — sliding-window median is "two heaps" but the merge-and-balance step is structurally similar.
- **Greedy** — the "always advance the smallest cursor" rule is a one-step greedy, and its correctness comes from the monotonicity of each list.

---

## ✅ Self-check — 8 questions

??? question "1. Why does k-way merge cost O(N log k) and not O(N log N)?"
    The heap holds only k items at any time (one cursor per list). Each push/pop is O(log k). N total emissions ⇒ O(N log k). Sorting all N elements would be O(N log N), losing the structure of the inputs.

??? question "2. Why include a `list_id` (or insertion counter) in the heap tuple?"
    Two reasons: (a) you need to know which list to advance after a pop; (b) when two values tie, the heap then compares the next tuple field — which is often unorderable (`list`, `ListNode`, etc.). The integer `list_id` gives a clean tiebreaker that prevents `TypeError`.

??? question "3. In smallest-range (LC 632), why advance only the minimum cursor?"
    Advancing the max can only make the window wider (the new value is ≥ the old max). Advancing the min is the only move that could push the bottom up, potentially shrinking the window. Greedy correctness follows from this monotonicity.

??? question "4. When does pairwise merge beat heap-based merge in practice?"
    Same big-O (both O(N log k)), but pairwise has lower constant factors — no heap overhead, and the inner two-way merge has very tight memory access patterns. For linked lists especially, pairwise often wins on benchmarks.

??? question "5. For Kth Smallest in Sorted Matrix (LC 378), how does k-way merge apply?"
    Each row is a sorted list. Push the head of each row (O(n)), then pop k-1 times advancing within the row. The kth pop is the answer. O(k log n) total. (Binary-search-on-answer is also valid and typically faster in practice for large k.)

??? question "6. In LC 373 (k smallest pairs), why is seeding only `min(k, n)` rows enough?"
    Each row's smallest pair is `(nums1[i], nums2[0])`. The k-th smallest sum overall must use one of these row-heads (and successors via column-advance). Rows with index ≥ k can never contribute earlier than the first k row-heads, so they're irrelevant.

??? question "7. What's the symmetric trick for 'merge k sorted DESCENDING lists'?"
    Use a max-heap (negate values on push and pop in Python's `heapq`). Everything else is identical: pop the global max, advance the popped list's cursor, push the next negated value.

??? question "8. Why doesn't k-way merge solve 'merge k UNSORTED lists'?"
    The whole correctness argument depends on each list being individually sorted: the front element of a list is the smallest from that source. If the inputs aren't sorted, the heap-of-cursors invariant fails. Sort each list first (O(N log(N/k)) total) or fall back to a single global sort.
