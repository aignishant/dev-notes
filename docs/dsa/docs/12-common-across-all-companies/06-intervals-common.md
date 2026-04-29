# Intervals — common across all companies

> Sort by start, sweep with a heap. Two ideas, a dozen problems, every company.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Interval problems are deceptively shallow: ~95% of them reduce to *sort the intervals by start time, then either sweep with a running end-pointer or maintain a min-heap of end times*. Once you've internalised those two patterns, the only thing left is recognising which one applies. The 13 problems below are the ones that show up across **every** company's onsite — particularly Amazon, Google, and operations-heavy startups.

## Patterns that drive these problems

| Pattern | Frequency | Where it shows up |
|---|---|---|
| Sort + sweep | ★★★★★ | Merge, Insert, Non-overlapping, Free Time |
| Min-heap of end times | ★★★★★ | Meeting Rooms II, Max CPU Load |
| Sweep line / events | ★★★★☆ | Car Pooling, Min Platforms, My Calendar III |
| Greedy by end time | ★★★★☆ | Min Arrows, Non-overlapping Intervals |
| Two-pointer merge | ★★★☆☆ | Interval List Intersections |
| Balanced BST / sorted set | ★★★☆☆ | My Calendar I/II |

## The list (13 problems)

| # | Problem | Difficulty | Pattern | LC# |
|---|---|---|---|---|
| 1 | Merge Intervals | Medium | Sort + sweep | 56 |
| 2 | Insert Interval | Medium | Linear scan | 57 |
| 3 | Non-overlapping Intervals | Medium | Greedy by end | 435 |
| 4 | Meeting Rooms | Easy | Sort + adjacent check | 252 |
| 5 | Meeting Rooms II | Medium | Min-heap of ends | 253 |
| 6 | Minimum Number of Arrows | Medium | Greedy by end | 452 |
| 7 | Interval List Intersections | Medium | Two-pointer | 986 |
| 8 | Employee Free Time | Hard | Heap merge / flatten | 759 |
| 9 | Car Pooling | Medium | Sweep line | 1094 |
| 10 | My Calendar I | Medium | Sorted set / TreeMap | 729 |
| 11 | My Calendar II | Medium | Two interval lists | 731 |
| 12 | My Calendar III | Hard | Sweep line / count map | 732 |
| 13 | Minimum Number of Platforms | Medium | Sweep line / heap | (GfG) |
| 14 | Maximum CPU Load | Medium | Heap of end times | (Educative) |
| 15 | Find Right Interval | Medium | Sort + binary search | 436 |

---

## Deep-dive 1 — Merge Intervals

The reference problem for the entire family. Sort by start; sweep, extending the current merged interval whenever the next one overlaps, otherwise pushing it onto the result.

??? question "Why sort by start time, not end time?"
    Sorting by start guarantees that when we look at interval `i`, every earlier interval has already been considered for merging into the current run. After sorting by start, **two intervals overlap iff `next.start <= current.end`** — a single comparison.

??? question "What about touching intervals like `[1,3]` and `[3,5]`?"
    Convention varies. The standard LeetCode rule is **closed intervals merge** (so `[1,3]` and `[3,5]` -> `[1,5]`). Use `next.start <= curr_end`. If the problem says half-open, switch to `<`.

```python linenums="1"
from __future__ import annotations


def merge(intervals: list[list[int]]) -> list[list[int]]:
    """Merge all overlapping intervals.

    Time:  O(n log n)  — dominated by the sort
    Space: O(n)        — output list (O(1) excluding output)
    """
    if not intervals:
        return []
    intervals.sort(key=lambda iv: iv[0])
    merged: list[list[int]] = [intervals[0][:]]
    for start, end in intervals[1:]:
        last = merged[-1]
        if start <= last[1]:           # overlap -> extend
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged


# Trace: [[1,3],[2,6],[8,10],[15,18]]
# sorted: same
# start with [1,3]
# [2,6]:  2 <= 3 -> extend -> [1,6]
# [8,10]: 8 > 6  -> push   -> [1,6], [8,10]
# [15,18]:15>10  -> push   -> [1,6], [8,10], [15,18]
```

!!! tip "Mutate the last interval in place"
    `merged[-1][1] = max(...)` is cleaner and faster than popping and re-pushing. Interviewers notice the small wins.

---

## Deep-dive 2 — Meeting Rooms II

The canonical resource-allocation problem. *How many rooms are needed if every meeting must run uninterrupted?* Equivalently: at any instant, what's the maximum number of overlapping intervals?

The trick: sort by start, and use a **min-heap of end times**. The heap top is "the room that frees up earliest". For each new meeting:

- If the earliest-freeing room is already free (`heap[0] <= start`), reuse it: pop and push the new end.
- Otherwise, allocate a new room: push the new end without popping.

The heap size at any moment = rooms in use. The answer is the heap's max size, which equals its final size if you never shrink it — but here we *do* pop-and-push when reusing, so the answer is `len(heap)` at the end (since unused rooms stay popped).

??? question "Why does the heap size at the end equal the answer?"
    Every push is "I just started a meeting in some room"; every pop is "I freed a room before starting a new meeting". A room that's reused contributes one pop and one push (net 0). A brand-new room contributes one push (net +1). So `len(heap)` at the end = number of distinct rooms ever opened = peak concurrent meetings = answer.

??? question "When would I prefer the sweep-line / event variant?"
    When the input is huge and you don't need the heap structure — emit `(start, +1)` and `(end, -1)` events, sort, sweep, track the max running sum. Same O(n log n), simpler code, but doesn't generalise to "max CPU load" where each meeting carries a weight.

```python linenums="1"
from __future__ import annotations
import heapq


def min_meeting_rooms(intervals: list[list[int]]) -> int:
    """Minimum number of conference rooms required.

    Sort by start; maintain a min-heap of end times. For each
    incoming meeting, reuse the earliest-freeing room if possible,
    otherwise open a new one.

    Time:  O(n log n)
    Space: O(n)
    """
    if not intervals:
        return 0
    intervals.sort(key=lambda iv: iv[0])
    heap: list[int] = []                   # end times of busy rooms
    for start, end in intervals:
        if heap and heap[0] <= start:
            heapq.heapreplace(heap, end)   # reuse: pop + push in one op
        else:
            heapq.heappush(heap, end)      # open a new room
    return len(heap)


# Trace: [[0,30],[5,10],[15,20]]
# [0,30]:  heap empty           -> push 30          heap=[30]
# [5,10]:  heap[0]=30 > 5       -> push 10          heap=[10,30]
# [15,20]: heap[0]=10 <= 15     -> heapreplace 20   heap=[20,30]
# answer = 2
```

!!! warning "Sort comparator: tie-break carefully"
    For pure Meeting Rooms II, sorting by `start` alone works. For variants like *Maximum CPU Load* (weighted intervals) or *Employee Free Time* (merging multiple sorted streams), sort by `(start, end)` to keep the algorithm deterministic across ties.

---

## 🃏 Cheatsheet

- **Sort by start, then sweep** — this solves Merge, Insert, Non-overlapping, Free Time, and half the rest.
- **Min-heap of end times** for "minimum resources" / "max concurrency" problems (Meeting Rooms II, Max CPU Load, Min Platforms).
- **Greedy by end time** for Min Arrows and Non-overlapping Intervals — pick the interval that frees up earliest, skip everything that conflicts with it.
- **Sweep line** = events `(time, +1/-1)`, sort, scan, track running sum max. Cleanest model for Car Pooling, My Calendar III.
- **Two-pointer merge** for Interval List Intersections — both lists sorted, advance the one whose end is smaller.
- **Touching vs overlapping**: `[1,3]` and `[3,5]` — read the problem's exact wording. Default to closed (`<=`).
- **Insert Interval** can be O(n) without re-sorting — three phases: before, merge-with, after.
- **My Calendar I** = sorted set / `SortedList` and binary search; My Calendar II = two layers (single + double); III = sweep line.
- **`heapq` is min-heap only.** For max-end-time tricks, push `-end` and negate on pop.
- **Empty-input guard** at the top of every interval function. Sort on an empty list is fine, but indexing `intervals[0]` is not.
