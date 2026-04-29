# Merge Intervals

> Sort by start, sweep once, merge overlaps. The pattern that solves every "calendar / range / scheduling" problem you'll ever see in an interview. Feels obvious after one demo and yet half of candidates botch the boundary check.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is the merge-intervals pattern?

You're given a bunch of intervals — ranges with a `[start, end)` (or `[start, end]`) shape. The natural way to think about them is as line segments on a number line, or as boxes on a calendar. Almost every interview question in this family reduces to one of:

- **Merge overlaps** — collapse `[1,3], [2,6]` into `[1,6]`.
- **Detect overlaps** — "could this person attend all meetings?"
- **Insert into sorted intervals** — "given a non-overlapping list, insert a new one and re-merge."
- **Count concurrent events** — "minimum number of meeting rooms."

In every case the key move is the same: **sort the intervals by `start`, then sweep left-to-right with a single pointer comparing each new interval against the previous one.** O(n log n) sort dominates; the sweep is O(n).

!!! tip "The signal — when to reach for merge-intervals"
    Reach for it when you see:

    - Inputs shaped like `[[s, e], [s, e], …]` — pairs of numbers that mean "from … to …".
    - Words like *meeting*, *interval*, *range*, *appointment*, *segment*, *overlap*, *busy slots*, *calendar conflict*.
    - The answer involves either **merging**, **counting concurrent**, or **whether all fit**.
    - Brute force is O(n²) "compare each pair."

    Two close cousins:

    - **Sweep line / events** — when starts and ends carry different meaning (ticket goes up at start, down at end). Useful for "minimum rooms" / "max overlap."
    - **Interval scheduling (greedy)** — pick maximum non-overlapping subset. Sort by **end**, not by start.

---

## 🧩 The four flavors

### Flavor 1: Sort + sweep merge

The canonical move. Sort by start, walk through; if the next interval starts before the previous one ends, merge by extending the previous interval's end to the max.

```python
def merge(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []

    intervals.sort(key=lambda iv: iv[0])             # (1) O(n log n)
    merged: list[list[int]] = [intervals[0][:]]      # (2) seed with copy

    for start, end in intervals[1:]:
        last = merged[-1]
        if start <= last[1]:                         # (3) overlap
            last[1] = max(last[1], end)              # (4) extend
        else:
            merged.append([start, end])              # (5) disjoint — new bucket

    return merged
```

1. Sort is the only step that costs more than O(n).
2. Copy the first interval so we don't mutate the caller's input.
3. `<=` means "touching counts as overlap." Use `<` if `[1,2]` and `[2,3]` should stay separate.
4. **Crucial bug** — extend by `max(last[1], end)`, not by `end`. The new interval might be *fully contained* inside the previous one.
5. No overlap → a fresh bucket starts here.

**Examples:** Merge Intervals (LC 56), Insert Interval (LC 57), Employee Free Time (LC 759), Interval List Intersections (LC 986 — sweep two arrays).

### Flavor 2: Sweep-line / event sorting

Treat each interval as **two events** — a `+1` at `start` and a `−1` at `end` — sort all events together, sweep counting concurrent ranges. This decouples starts from ends entirely.

```python
def min_meeting_rooms(intervals: list[list[int]]) -> int:
    events: list[tuple[int, int]] = []
    for s, e in intervals:
        events.append((s, +1))   # door opens
        events.append((e, -1))   # door closes

    # Tie-breaker: -1 before +1 if same time → a meeting that ends
    # at t=10 frees the room *before* a meeting that starts at t=10.
    events.sort()

    rooms = max_rooms = 0
    for _, delta in events:
        rooms += delta
        max_rooms = max(max_rooms, rooms)
    return max_rooms
```

**Why sort `(time, delta)` works:** Python sorts tuples lexicographically; `−1 < +1`, so simultaneous "close" events fire before "open" events. That matches the "meetings touching at endpoints don't conflict" convention.

**Examples:** Meeting Rooms II (LC 253), Car Pooling (LC 1094), My Calendar III (LC 732), Skyline (LC 218 — multi-keyed events).

### Flavor 3: Min-heap of end times

A sweep-line variant that's nicer to derive from scratch in an interview, especially when an interviewer steers you toward heaps. Sort by start, push each interval's end onto a min-heap; if the smallest end ≤ current start, that room frees up — pop it.

```python
import heapq

def min_meeting_rooms_heap(intervals: list[list[int]]) -> int:
    intervals.sort(key=lambda iv: iv[0])
    free_when: list[int] = []                # min-heap of end times
    for s, e in intervals:
        if free_when and free_when[0] <= s:  # smallest-end room is free
            heapq.heappop(free_when)
        heapq.heappush(free_when, e)
    return len(free_when)                    # peak heap size = peak rooms
```

**Examples:** Task Scheduler (heap variant), CPU job scheduling, conference rooms.

### Flavor 4: Insert-into-sorted (no full re-sort)

When the existing list is *already* non-overlapping and sorted, you don't need a full sort to insert a new interval — slice into three parts in one pass.

```python
def insert(intervals: list[list[int]], new: list[int]) -> list[list[int]]:
    res: list[list[int]] = []
    i, n = 0, len(intervals)
    s, e = new

    # (1) Pour through everything strictly to the left of `new`.
    while i < n and intervals[i][1] < s:
        res.append(intervals[i])
        i += 1

    # (2) Absorb everything that overlaps `new` into one big interval.
    while i < n and intervals[i][0] <= e:
        s = min(s, intervals[i][0])
        e = max(e, intervals[i][1])
        i += 1
    res.append([s, e])

    # (3) Pour the rest.
    while i < n:
        res.append(intervals[i])
        i += 1

    return res
```

**Why this is a win:** O(n), not O(n log n). It's the right move when the data is curated (e.g., a calendar app maintaining sorted state).

**Examples:** Insert Interval (LC 57), Range Module (LC 715), Add Bold Tag (LC 616 with merging).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Merge overlapping | Collapse adjacent overlaps | Merge Intervals | Sort by start, `last[1] = max(last[1], e)` |
| 2 | Insert + merge | New interval into sorted list | Insert Interval | Three-pass slice |
| 3 | Concurrent count | Max overlap at any time | Meeting Rooms II | Events `(t, ±1)` sorted |
| 4 | All-fit feasibility | "Can this person attend all?" | Meeting Rooms (LC 252) | Sort by start; check `s_i ≥ e_{i-1}` |
| 5 | Two-list intersection | Intersect sorted A vs B | Interval List Intersections | Walk two pointers, `[max(s), min(e)]` |
| 6 | Free-time / gaps | Holes between busy windows | Employee Free Time | Merge all → invert |
| 7 | Greedy non-overlap | Max disjoint subset | Non-overlapping Intervals | Sort by **end**, greedy keep-earliest-end |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Merge Intervals | 56 | Medium | Merge overlapping | 📝 |
| 2 | Insert Interval | 57 | Medium | Insert + merge | 📝 |
| 3 | Meeting Rooms | 252 | Easy | All-fit feasibility | 📝 |
| 4 | Meeting Rooms II | 253 | Medium | Concurrent count | 📝 |
| 5 | Interval List Intersections | 986 | Medium | Two-list intersection | 📝 |
| 6 | Non-overlapping Intervals | 435 | Medium | Greedy non-overlap | 📝 |
| 7 | Min Arrows to Burst Balloons | 452 | Medium | Greedy non-overlap | 📝 |
| 8 | Employee Free Time | 759 | Hard | Free-time / gaps | 📝 |
| 9 | Car Pooling | 1094 | Medium | Concurrent count | 📝 |
| 10 | My Calendar I | 729 | Medium | All-fit (online) | 📝 |
| 11 | My Calendar II | 731 | Medium | Concurrent count | 📝 |
| 12 | My Calendar III | 732 | Hard | Concurrent count | 📝 |
| 13 | Range Module | 715 | Hard | Insert + merge + delete | 📝 |
| 14 | Data Stream as Disjoint Intervals | 352 | Hard | Insert + merge | 📝 |
| 15 | Add Bold Tag in String | 616 | Medium | Insert + merge | 📝 |
| 16 | Remove Covered Intervals | 1288 | Medium | Sort + sweep | 📝 |
| 17 | The Skyline Problem | 218 | Hard | Sweep-line (multi-key) | 📝 |
| 18 | Maximum Sum of Two Non-Overlapping Subarrays | 1031 | Medium | Adjacent-window dp | 📝 |
| 19 | Number of Flowers in Full Bloom | 2251 | Hard | Sweep-line + offline | 📝 |
| 20 | Minimum Number of Taps to Open to Water a Garden | 1326 | Hard | Greedy interval cover | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Merge Intervals (LC 56)

> Given an array of intervals, merge all overlapping ones and return the disjoint result.

**Input:** `[[1,3], [2,6], [8,10], [15,18]]`
**Output:** `[[1,6], [8,10], [15,18]]`

#### Code

```python
def merge(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    intervals.sort(key=lambda iv: iv[0])
    merged: list[list[int]] = [intervals[0][:]]
    for s, e in intervals[1:]:
        last = merged[-1]
        if s <= last[1]:
            last[1] = max(last[1], e)
        else:
            merged.append([s, e])
    return merged
```

#### Dry run on `[[1,3], [2,6], [8,10], [15,18]]`

| Step | Current `(s,e)` | `merged[-1]` before | Overlap? | `merged` after |
|------|-----------------|---------------------|----------|----------------|
| Init | —               | —                   | —        | `[[1,3]]`      |
| 1    | `(2,6)`         | `[1,3]`             | `2 ≤ 3` ✓ | `[[1,6]]`      |
| 2    | `(8,10)`        | `[1,6]`             | `8 ≤ 6` ✗ | `[[1,6],[8,10]]` |
| 3    | `(15,18)`       | `[8,10]`            | `15 ≤ 10` ✗ | `[[1,6],[8,10],[15,18]]` |

Output `[[1,6],[8,10],[15,18]]` ✓.

#### Why containment doesn't break it

Try `[[1,10], [2,3]]`. After sort it's already in order. Step 1: `s=2, last=[1,10]`, overlap (`2 ≤ 10`). Update `last[1] = max(10, 3) = 10`. **Without the `max`** we'd shrink the merged interval to `[1,3]` — that's the #1 bug in this pattern.

#### Complexity

- **Time:** O(n log n) for the sort + O(n) sweep = O(n log n).
- **Space:** O(n) for the output (in-place is possible by reading and writing on the same array; rarely worth it in interviews).

---

### Deep-dive 2 — Meeting Rooms II (LC 253)

> Given `intervals[i] = [start, end]` for n meetings, return the minimum number of conference rooms needed.

This is the canonical "max number of overlapping intervals at any point" question. We'll use the **events / sweep-line** flavor (Flavor 2) — it's the cleanest derivation.

**Input:** `[[0,30], [5,10], [15,20]]`
**Output:** `2`

#### Code

```python
def min_meeting_rooms(intervals: list[list[int]]) -> int:
    events: list[tuple[int, int]] = []
    for s, e in intervals:
        events.append((s, +1))
        events.append((e, -1))
    events.sort()                        # ties: -1 before +1
    rooms = peak = 0
    for _, delta in events:
        rooms += delta
        peak = max(peak, rooms)
    return peak
```

#### Dry run on `[[0,30], [5,10], [15,20]]`

Build events (already sorted alphabetically because tuples sort `(time, delta)`):

```
(0, +1)   meeting A opens
(5, +1)   meeting B opens
(10, -1)  meeting B closes
(15, +1)  meeting C opens
(20, -1)  meeting C closes
(30, -1)  meeting A closes
```

Sweep:

| Event       | `rooms` after | `peak` |
|-------------|---------------|--------|
| `(0, +1)`   | 1             | 1      |
| `(5, +1)`   | 2             | **2**  |
| `(10, -1)`  | 1             | 2      |
| `(15, +1)`  | 2             | 2      |
| `(20, -1)`  | 1             | 2      |
| `(30, -1)`  | 0             | 2      |

Answer = 2. ✓

#### Why the tie-break matters

Suppose meetings `[10, 15]` and `[15, 20]`. Without the `−1 before +1` order, you'd see `(15, +1)` first → rooms=2 → wrong. The convention "a meeting that ends at t frees the room *before* a new one starting at t needs it" requires `−1` events to fire first at the same `t`. Sorting tuples gives this for free because `(15, -1) < (15, +1)`.

If the interview convention says "touching means conflict" (closed intervals), flip to `(15, +1) < (15, -1)` by negating the tie-breaker — `events.sort(key=lambda x: (x[0], -x[1]))`.

#### Complexity

- **Time:** O(n log n) — 2n events, O(2n log 2n) sort.
- **Space:** O(n) for the events array.

---

### Deep-dive 3 — Insert Interval (LC 57)

> Given a sorted, non-overlapping list of intervals, insert `new = [s, e]` and return the result, still sorted and non-overlapping.

This is the "no full re-sort" flavor (Flavor 4). Useful interview discriminator: a strong candidate notices the input *invariant* (already sorted, already disjoint) and refuses to throw it away with another `O(n log n)` sort.

**Input:** `intervals = [[1,3], [6,9]]`, `new = [2,5]`
**Output:** `[[1,5], [6,9]]`

#### Code

```python
def insert(intervals: list[list[int]], new: list[int]) -> list[list[int]]:
    res: list[list[int]] = []
    i, n = 0, len(intervals)
    s, e = new

    while i < n and intervals[i][1] < s:    # (1) left of new
        res.append(intervals[i])
        i += 1

    while i < n and intervals[i][0] <= e:   # (2) overlapping cluster
        s = min(s, intervals[i][0])
        e = max(e, intervals[i][1])
        i += 1
    res.append([s, e])

    while i < n:                            # (3) right of new
        res.append(intervals[i])
        i += 1

    return res
```

#### Dry run on `intervals = [[1,2], [3,5], [6,7], [8,10], [12,16]]`, `new = [4,8]`

**Phase 1 — left of new** (`intervals[i][1] < 4`):

| `i` | `intervals[i]` | `intervals[i][1] < 4`? | Action       | `res`             |
|-----|----------------|------------------------|--------------|-------------------|
| 0   | `[1,2]`        | `2 < 4` ✓              | append, i++  | `[[1,2]]`         |
| 1   | `[3,5]`        | `5 < 4` ✗              | exit phase 1 | `[[1,2]]`         |

**Phase 2 — overlap cluster** (`intervals[i][0] <= 8`, with `(s,e)` evolving):

| `i` | `intervals[i]` | `intervals[i][0] <= e`? | New `(s,e)` |
|-----|----------------|-------------------------|-------------|
| 1   | `[3,5]`        | `3 ≤ 8` ✓               | `(3,8)`     |
| 2   | `[6,7]`        | `6 ≤ 8` ✓               | `(3,8)`     |
| 3   | `[8,10]`       | `8 ≤ 8` ✓               | `(3,10)`    |
| 4   | `[12,16]`      | `12 ≤ 10` ✗             | exit phase 2 |

Append `[3,10]` → `res = [[1,2], [3,10]]`.

**Phase 3 — right of new:**

| `i` | `intervals[i]` | Action       | `res`                        |
|-----|----------------|--------------|------------------------------|
| 4   | `[12,16]`      | append, i++  | `[[1,2], [3,10], [12,16]]`   |

Output `[[1,2], [3,10], [12,16]]` ✓.

#### Why O(n)?

Each interval is touched **at most once** across the three phases — the index `i` only advances. No sort. This is a real win when n is large (e.g., a billion-event calendar service).

#### Complexity

- **Time:** O(n).
- **Space:** O(n) for the result.

---

## 🐛 Common bugs

1. **Forgetting `max(last[1], end)` on merge.** A fully contained interval (`[1,10]` swallowing `[2,3]`) shrinks the answer.
2. **Wrong overlap test.** `start <= last[1]` vs `start < last[1]` flips the "touching = overlap" semantics. Pick consciously and state it.
3. **Sorting by end when you needed start (or vice versa).** Greedy non-overlapping wants **end** sort; merging wants **start**. Mixing them silently produces nonsense.
4. **Sweep-line tie-break.** Forgetting that closes must precede opens at the same time → off-by-one peak count.
5. **Mutating input on first append.** `merged = [intervals[0]]` instead of `merged = [intervals[0][:]]` — later `last[1] = …` mutates the caller's list. Defensive copy.
6. **Heap variant: comparing wrong field.** `heap[0]` is the smallest **end**; comparing it to a new **start** is the right move. Comparing two ends gives the wrong question.
7. **Insert Interval: using `<=` in phase 1.** Phase 1's check is `intervals[i][1] < s`; using `<=` swallows a touching interval and then double-merges in phase 2.

---

## 🗣️ Interviewer phrasings to recognize

- "Given a list of meeting times, can the person attend them all?" → Flavor 1, all-fit (sort by start, check adjacency).
- "How many rooms are needed?" → Flavor 2 or 3 (events or heap).
- "A user adds an event — does it conflict?" → My Calendar series; balanced BST or sorted list + binary search.
- "Burst all balloons with the fewest arrows" → greedy by end (Flavor: non-overlap subset).
- "Find when *everyone* is free." → merge all busy slots → invert.

---

## 🧭 Connections to other patterns

- **Sliding window** is the *contiguous-array* cousin; merge-intervals operates on already-bounded ranges, not raw indices.
- **Sweep-line** is a generalization — once you have events with multiple kinds (open/close/query), you've left "merge intervals" and entered general computational geometry.
- **Greedy** (sort-by-end) shows up in problem 6 (LC 435) and 7 (LC 452) — a subtle shift from "merge" to "skip."
- **Heaps / priority queues** appear in Flavor 3 — and dominate when intervals stream in (online).
- **Segment trees / Range Module (LC 715)** is the production answer to "many adds and deletes."

---

## ✅ Self-check — 8 questions

??? question "1. Why sort by `start` for merging but by `end` for greedy non-overlap?"
    Merging needs adjacent comparisons of endpoints, easiest done in start-order so the "previous end" is meaningful. Greedy non-overlap wants to leave the earliest-ending interval picked first to maximize room for the rest — a classic exchange argument. They're different problems.

??? question "2. Why `start <= last[1]` and not `start < last[1]`?"
    Convention. `[1,2]` and `[2,3]` *touching* — do they merge? With `<=`, yes. With `<`, no. The interviewer should specify; if not, ask.

??? question "3. Why does the sweep-line tie-breaker matter?"
    At the same time `t`, processing `−1` first means a meeting that ends at `t` releases its room *before* a meeting starting at `t` claims one — so they share a room. If you process `+1` first you double-count. `(t, -1) < (t, +1)` falls out of tuple sorting for free."

??? question "4. When is the heap flavor strictly better than events?"
    When intervals arrive **online** (one at a time) and you must answer "rooms used so far" after each. The heap is incremental; the events array would have to be re-sorted on every insert.

??? question "5. Why is Insert Interval O(n) but Merge Intervals O(n log n)?"
    Insert Interval *uses* the precondition that the input is already sorted and disjoint — that information was bought elsewhere. Merge Intervals starts cold.

??? question "6. How do you handle floats / non-integer times?"
    Same algorithms work on any totally-ordered type. Watch for floating-point precision when comparing equality at boundaries — prefer multiplying everything to integer milliseconds.

??? question "7. What changes for half-open `[start, end)` vs closed `[start, end]`?"
    Just the overlap predicate. Half-open: overlap iff `s_a < e_b and s_b < e_a` (strict). Closed: overlap iff `s_a <= e_b and s_b <= e_a`. Pick one and stay consistent.

??? question "8. How do you delete or split intervals?"
    "Remove [a, b) from the disjoint list" → walk the list, for each overlapping interval emit up to two slices (`[s, a)` and `[b, e)`) for the parts outside the cut. This is what `Range Module (LC 715)` is built around.

---

> **Next pattern up:** Cyclic Sort — the trick for "find the missing/duplicate number in `[1..n]` in O(1) space" (page coming next).
