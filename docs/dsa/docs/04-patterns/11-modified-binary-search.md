# Modified Binary Search

> Binary search beyond "find this value in this sorted array." Rotated arrays, infinite arrays, bitonic arrays, peak finding, and — the killer move — **binary searching the answer space itself** (Koko's eating speed, ship within D days, split array minimum sum). Once you stop thinking of binary search as "where is X?" and start thinking of it as "find the boundary between *no* and *yes*," half a textbook of medium/hard problems collapses to log-time templates.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is modified binary search?

Plain binary search has one job: find an element in a sorted array. The "modified" version generalises in two directions.

**Direction 1 — modified data:** the array isn't a clean sorted list. It's rotated, bitonic, 2D, infinite, or has duplicates. The trick is to figure out which half of the search space is *currently* well-ordered (and contains the target if it's anywhere) — then binary-search inside it.

**Direction 2 — modified question:** you're not looking for a value; you're looking for the **smallest `x` such that some predicate is true**. The "array" is the implicit range `[low..high]` of candidate answers; the "comparison" is "does `feasible(x)` hold?" If `feasible` is monotone — `feasible(x)` ⇒ `feasible(x+1)` — binary search finds the boundary in O(log range) calls.

The shared mental model: **binary search finds a boundary between two zones.** First-occurrence binary search finds the boundary between "smaller than target" and "≥ target." Rotated-array search finds the boundary between "in this half" and "in that half." Answer-space binary search finds the boundary between "infeasible" and "feasible."

!!! tip "The signal — when to reach for modified binary search"
    Reach for it when:

    - The data is sorted, **mostly** sorted, **rotated**, or **monotone in some way**.
    - The brute force is O(n) scan or O(n²) and the input is large.
    - The problem says **"in O(log n)"** explicitly.
    - The answer is a **numeric quantity** with a feasibility predicate that's monotone (typical phrasing: *"minimum k such that …"* or *"maximum k such that …"*).

    Don't reach for it when:

    - The array isn't sorted *and* there's no monotone predicate hiding inside the problem.
    - The "answer space" predicate isn't monotone (binary search will give wrong results, silently).

---

## 🧩 The three flavors

### Flavor 1: Lower bound / upper bound

The most useful primitive in the bunch. **Lower bound** = first index `i` where `arr[i] >= target`. **Upper bound** = first index where `arr[i] > target`. Together they bracket every occurrence of `target`.

```python
def lower_bound(arr: list[int], target: int) -> int:
    lo, hi = 0, len(arr)                          # (1) hi is len(arr), not len(arr)-1
    while lo < hi:                                # (2) strict less-than
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(arr: list[int], target: int) -> int:
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] <= target:                    # (3) the only diff vs lower_bound
            lo = mid + 1
        else:
            hi = mid
    return lo
```

1. `hi = len(arr)` is the **half-open** convention. The answer can equal `len(arr)` (target larger than everything).
2. The invariant: `arr[lo-1] < target ≤ arr[hi]` (with the boundary fictions). Loop ends when `lo == hi`.
3. The single-character difference between `<` and `<=` is what flips lower-bound to upper-bound. Internalise this.

Python's standard library (`bisect.bisect_left` = lower bound; `bisect.bisect_right` = upper bound) does exactly this. **Use it in production.** Hand-rolling these is interview-only.

**Examples:** Find First and Last Position (LC 34), Search Insert Position (LC 35), Count of an Element (LC 1351).

### Flavor 2: Pick-the-sorted-half (rotated arrays)

A rotated sorted array `[4, 5, 6, 7, 0, 1, 2]` has a *break point* somewhere. At any midpoint, **one of the two halves is contiguously sorted**. Identify which half, check whether `target` falls inside it, and binary-search there.

```python
def search_rotated(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        # (1) Left half [lo..mid] is sorted iff nums[lo] <= nums[mid]
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:    # (2) target in left half
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            # Right half [mid..hi] is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1
```

1. The "is this half sorted?" test is `nums[lo] <= nums[mid]`. If yes, the rotation pivot is in the right half (or doesn't exist in this view).
2. Inside the sorted half, you can do a normal range check.

**Examples:** Search in Rotated Sorted Array (LC 33), Find Minimum in Rotated Sorted Array (LC 153), Find Peak Element (LC 162 — same trick, different question).

### Flavor 3: Binary search on the answer space

The "answer" is a number `x` (eating speed, ship capacity, split-array threshold). The feasibility predicate `feasible(x)` is monotone. Binary search the smallest (or largest) `x` for which `feasible(x)` is true.

```python
def min_eating_speed(piles: list[int], h: int) -> int:
    """LC 875 — Koko eats `piles` over `h` hours; min speed?"""

    def hours_needed(speed: int) -> int:
        # Each pile takes ceil(p / speed) hours.
        return sum((p + speed - 1) // speed for p in piles)

    lo, hi = 1, max(piles)                        # (1) bracket the answer
    while lo < hi:
        mid = (lo + hi) // 2
        if hours_needed(mid) <= h:                # (2) feasible — try smaller
            hi = mid
        else:
            lo = mid + 1                          # (3) infeasible — must try larger
    return lo
```

1. **Bracketing matters.** `lo` = "trivially infeasible" (or 1 if any speed works), `hi` = "trivially feasible." Wrong brackets = wrong answer.
2. The *direction* of the boundary depends on whether you're minimising or maximising. For "min `x` such that feasible," `feasible(mid) → hi = mid`.
3. The skeleton is identical to lower-bound binary search — `feasible(mid)` plays the role of `arr[mid] >= target`.

**Examples:** Koko Eating Bananas (LC 875), Capacity to Ship Packages (LC 1011), Split Array Largest Sum (LC 410), Median of Two Sorted Arrays (LC 4 — bsearch the partition).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Exact target | Find the index of `x` | Binary Search (LC 704) | Standard `[lo, hi]` two-side closed |
| 2 | Lower / upper bound | First `≥` or first `>` | Find First and Last Position (LC 34) | `bisect_left` / `bisect_right` |
| 3 | Rotated sorted | One break point | Search Rotated (LC 33) | Pick the sorted half |
| 4 | Find min in rotated | Where's the break? | Find Min in Rotated (LC 153) | Compare `nums[mid]` with `nums[hi]` |
| 5 | Peak element | Local maximum | Peak Element (LC 162) | Step toward the higher neighbour |
| 6 | 2D matrix | Sorted by row + column | Search 2D Matrix II (LC 240) | Start top-right, shed row/column |
| 7 | Answer-space search | Binary search on a numeric answer | Koko (LC 875) | Define `feasible(x)`; ensure monotonicity |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Binary Search | 704 | <span class="diff-easy">Easy</span> | Exact target | 📝 |
| 2 | Search Insert Position | 35 | <span class="diff-easy">Easy</span> | Lower bound | 📝 |
| 3 | Find First and Last Position | 34 | <span class="diff-medium">Medium</span> | Lower / upper bound | 📝 |
| 4 | Search in Rotated Sorted Array | 33 | <span class="diff-medium">Medium</span> | Rotated sorted | 📝 |
| 5 | Search in Rotated Sorted Array II | 81 | <span class="diff-medium">Medium</span> | Rotated + duplicates | 📝 |
| 6 | Find Minimum in Rotated Sorted Array | 153 | <span class="diff-medium">Medium</span> | Find min in rotated | 📝 |
| 7 | Find Minimum in Rotated Sorted Array II | 154 | <span class="diff-hard">Hard</span> | Min + duplicates | 📝 |
| 8 | Find Peak Element | 162 | <span class="diff-medium">Medium</span> | Peak element | 📝 |
| 9 | Search a 2D Matrix | 74 | <span class="diff-medium">Medium</span> | Flat treat-as-1D | 📝 |
| 10 | Search a 2D Matrix II | 240 | <span class="diff-medium">Medium</span> | 2D matrix shed-row | 📝 |
| 11 | Sqrt(x) | 69 | <span class="diff-easy">Easy</span> | Answer-space search | 📝 |
| 12 | Valid Perfect Square | 367 | <span class="diff-easy">Easy</span> | Answer-space search | 📝 |
| 13 | Koko Eating Bananas | 875 | <span class="diff-medium">Medium</span> | Answer-space search | 📝 |
| 14 | Capacity to Ship Packages Within D Days | 1011 | <span class="diff-medium">Medium</span> | Answer-space search | 📝 |
| 15 | Split Array Largest Sum | 410 | <span class="diff-hard">Hard</span> | Answer-space search | 📝 |
| 16 | Median of Two Sorted Arrays | 4 | <span class="diff-hard">Hard</span> | Partition binary search | 📝 |
| 17 | Find K Closest Elements | 658 | <span class="diff-medium">Medium</span> | Lower bound + window | 📝 |
| 18 | Find Smallest Letter Greater Than Target | 744 | <span class="diff-easy">Easy</span> | Upper bound | 📝 |
| 19 | Search in a Sorted Array of Unknown Size | 702 | <span class="diff-medium">Medium</span> | Exponential bracketing | 📝 |
| 20 | Random Pick with Weight | 528 | <span class="diff-medium">Medium</span> | Lower bound on prefix sums | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Find First and Last Position of Element in Sorted Array (LC 34)

> Given a sorted array and a target, return `[first, last]` index of `target`. Return `[-1, -1]` if not found. Required: O(log n).

The textbook way to use lower-bound and upper-bound together.

#### Code

```python
from bisect import bisect_left, bisect_right

def search_range(nums: list[int], target: int) -> list[int]:
    lo = bisect_left(nums, target)
    if lo == len(nums) or nums[lo] != target:
        return [-1, -1]
    hi = bisect_right(nums, target) - 1
    return [lo, hi]
```

Or with hand-rolled bounds:

```python
def search_range_manual(nums: list[int], target: int) -> list[int]:
    def lower(target_: int) -> int:
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < target_:
                lo = mid + 1
            else:
                hi = mid
        return lo

    first = lower(target)
    if first == len(nums) or nums[first] != target:
        return [-1, -1]
    last = lower(target + 1) - 1                  # upper bound trick
    return [first, last]
```

The second version uses a **single helper** with the trick `upper_bound(target) == lower_bound(target + 1)`. Less code, fewer chances to off-by-one.

#### Dry run on `nums = [5, 7, 7, 8, 8, 10]`, `target = 8`

`bisect_left(nums, 8)`:

| Iter | `lo` | `hi` | `mid` | `nums[mid]` | Action |
|------|------|------|-------|-------------|--------|
| 1 | 0 | 6 | 3 | 8 | not `< 8` → `hi = 3` |
| 2 | 0 | 3 | 1 | 7 | `< 8` → `lo = 2` |
| 3 | 2 | 3 | 2 | 7 | `< 8` → `lo = 3` |
| stop | 3 | 3 | — | — | return 3 |

`bisect_right(nums, 8)` (i.e., `bisect_left(nums, 9)`):

| Iter | `lo` | `hi` | `mid` | `nums[mid]` | Action |
|------|------|------|-------|-------------|--------|
| 1 | 0 | 6 | 3 | 8 | `< 9` → `lo = 4` |
| 2 | 4 | 6 | 5 | 10 | not `< 9` → `hi = 5` |
| 3 | 4 | 5 | 4 | 8 | `< 9` → `lo = 5` |
| stop | 5 | 5 | — | — | return 5 |

So `first = 3`, `last = 5 - 1 = 4`. Output: `[3, 4]` ✓.

#### Why the half-open `[lo, hi)` convention pays off

In the half-open form, the answer can be `lo == len(nums)` (target larger than everything, "insertion point is at the end"). With the closed form `[lo, hi]` you'd need a sentinel or special case. Pick one and stick to it across all your binary searches; mixing causes off-by-one bugs.

#### Complexity

- **Time:** O(log n) — two binary searches, each log-time.
- **Space:** O(1).

---

### Deep-dive 2 — Search in Rotated Sorted Array (LC 33)

> A sorted array was rotated at an unknown pivot. Given the array and a target, find the target's index or return `-1`. O(log n).

The candidate-killer here is forgetting that **at any midpoint, one half is always sorted**. That observation is the entire algorithm.

#### Code (re-stated)

```python
def search_rotated(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:                 # left half sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:                                     # right half sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1
```

#### Dry run on `nums = [4, 5, 6, 7, 0, 1, 2]`, `target = 0`

| Iter | `lo` | `hi` | `mid` | `nums[mid]` | Sorted half | Target in sorted half? | Next |
|------|------|------|-------|-------------|-------------|------------------------|------|
| 1 | 0 | 6 | 3 | 7 | left ([4..7], `4 <= 7`) | `4 <= 0 < 7`? No | `lo = 4` |
| 2 | 4 | 6 | 5 | 1 | left ([0..1], `0 <= 1`) | `0 <= 0 < 1`? Yes | `hi = 4` |
| 3 | 4 | 4 | 4 | 0 | match! | — | return 4 |

Output: index 4 ✓.

#### Why `nums[lo] <= nums[mid]` (with `<=`)?

When `lo == mid` (single-element view), `nums[lo] == nums[mid]` — that should count as "left half is sorted" (a single element is trivially sorted). Using strict `<` would misclassify this case. The boundary `lo <= hi` (closed range) and the `<=` here go together.

#### What about duplicates (LC 81)?

Duplicates break the test. Consider `nums = [2, 2, 2, 0, 2]`, `lo=0, mid=2, hi=4`. `nums[lo]=2 <= nums[mid]=2` says left is sorted, but `0` (the rotation point) is in the left half. Fix: when `nums[lo] == nums[mid] == nums[hi]`, **shrink both ends by 1** (`lo += 1; hi -= 1`) — this is the only safe move. Worst-case becomes O(n) when the array is all duplicates.

#### Complexity

- **Time:** O(log n) for distinct values; O(n) worst case with duplicates.
- **Space:** O(1).

---

### Deep-dive 3 — Koko Eating Bananas (LC 875)

> Koko has piles of bananas and `h` hours before the guards return. She eats one pile at a time at speed `k` bananas per hour. She finishes a pile and rests for the rest of the hour. Find the *minimum* `k` such that she finishes all piles in `h` hours.

The answer is a number — Koko's eating speed. Brute force tries every speed from 1 upward (O(max(piles) · n)). Binary search the answer space: O(n log max(piles)).

#### The feasibility predicate

`feasible(k)` = "with speed `k`, can Koko finish all piles in ≤ `h` hours?" For a single pile of size `p`, time is `ceil(p / k)`. Total time is the sum.

`feasible(k)` is **monotone**: if speed `k` works, any speed > `k` also works. That monotonicity is what makes binary search valid.

#### Code (re-stated)

```python
def min_eating_speed(piles: list[int], h: int) -> int:
    def hours_needed(speed: int) -> int:
        return sum((p + speed - 1) // speed for p in piles)

    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if hours_needed(mid) <= h:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

#### Dry run on `piles = [3, 6, 7, 11]`, `h = 8`

`lo = 1, hi = 11`. Iterate:

| Iter | `lo` | `hi` | `mid` | `hours_needed(mid)` | Feasible? | Next |
|------|------|------|-------|----------------------|-----------|------|
| 1 | 1 | 11 | 6 | 1+1+2+2 = 6 | 6 ≤ 8 ✓ | `hi = 6` |
| 2 | 1 | 6 | 3 | 1+2+3+4 = 10 | 10 ≤ 8 ✗ | `lo = 4` |
| 3 | 4 | 6 | 5 | 1+2+2+3 = 8 | ✓ | `hi = 5` |
| 4 | 4 | 5 | 4 | 1+2+2+3 = 8 | ✓ | `hi = 4` |
| stop | 4 | 4 | — | — | — | return 4 |

Output: speed 4. ✓ (At speed 4: pile 3 → 1h, pile 6 → 2h, pile 7 → 2h, pile 11 → 3h, total 8h.)

#### The bracketing rule

- `lo = 1` — minimum speed (any positive integer is a valid candidate).
- `hi = max(piles)` — Koko can always finish in `n` hours by eating the biggest pile per hour.

For other answer-space problems, the bracketing logic is the same: `lo` = minimum trivially-infeasible (or 1), `hi` = some trivially-feasible. **Be deliberate about the brackets** — wrong brackets give silently wrong answers.

#### Why the `hi = mid` (not `mid - 1`) for "feasible"?

We're looking for the **smallest** feasible `k`. If `mid` is feasible, the answer is `mid` *or* something smaller — keep `mid` in the candidate set. The half-open update `hi = mid` does that. Pairing with strict `lo < hi` makes the loop terminate cleanly.

#### Complexity

- **Time:** O(n log max(piles)) — log iterations, each O(n) feasibility check.
- **Space:** O(1).

---

## 🐛 Common bugs

1. **Mixing `[lo, hi]` (closed) with `[lo, hi)` (half-open) conventions.** The closed form uses `while lo <= hi` and updates `mid ± 1`; the half-open uses `while lo < hi` and `hi = mid`. Pick one per problem; never mix.
2. **`mid = (lo + hi) // 2` overflow** — not in Python (arbitrary precision), but in C++/Java. The textbook fix `mid = lo + (hi - lo) // 2` is harmless in Python and good muscle memory.
3. **Forgetting to recheck `nums[first] == target`** in LC 34. `bisect_left` returns the *insertion point*, which can land on an index whose value isn't the target (or past the end).
4. **Rotated array with duplicates: assuming `nums[lo] <= nums[mid]` always works.** It fails when all three (`lo, mid, hi`) tie. Shrink both ends and continue.
5. **Answer-space binary search with non-monotone feasibility.** Will return *some* index but not the right one. Always *prove* monotonicity before using this template.
6. **Wrong bracket `hi`.** For Koko, `hi = sum(piles)` is too generous (correct but wasteful); `hi = max(piles)` is tighter and provably feasible. For Split Array Largest Sum, `lo = max(nums)` (each part must hold at least the largest single element) and `hi = sum(nums)` (one part holds everything).
7. **Returning `lo` vs `hi` when they meet.** They're equal at the end of half-open loops — return either. But if you exited an inner `if found: return`, you might return the wrong one in pathological cases.
8. **2D matrix LC 240: doing two nested binary searches.** The shed-row trick (start top-right, move left or down) is O(m + n) — strictly better than O(m log n) of the nested version.

---

## 🗣️ Interviewer phrasings to recognize

- "Find the position to insert / find the first occurrence / find the last occurrence." → Lower / upper bound.
- "Search a rotated sorted array." → Pick-the-sorted-half.
- "Find the minimum / peak / break point." → Comparing `nums[mid]` with `nums[hi]` (or neighbours).
- "Minimum / maximum k such that …" or "smallest x for which …" → Answer-space search; define `feasible(x)`.
- "O(log n) on a 2D matrix where rows and columns are sorted." → LC 74 flat (treat as 1D) or LC 240 shed-row.
- "Search in an infinite/unknown-size sorted array." → Exponential bracketing: double `hi` until `arr[hi] > target`, then binary-search.

---

## 🧭 Connections to other patterns

- **Two Pointers** ([02-two-pointers.md](02-two-pointers.md)) — when the data is sorted, two-pointer "shrink from both ends" is often a linear cousin of binary search.
- **Sliding Window** ([01-sliding-window.md](01-sliding-window.md)) — Find K Closest Elements (LC 658) combines lower-bound + window expansion.
- **Greedy** — the feasibility predicate in answer-space search is often a greedy simulation (Koko's `hours_needed`, Capacity to Ship's "fit one truck at a time").
- **Divide and Conquer** — Median of Two Sorted Arrays (LC 4) is binary-search-the-partition, which is a hybrid.
- **Heap-based top-K** — when you have streaming data (no random access), heaps replace binary search.

---

## ✅ Self-check — 8 questions

??? question "1. What's the difference between `bisect_left` and `bisect_right`?"
    `bisect_left(arr, x)` returns the *leftmost* index where `x` could be inserted to keep `arr` sorted — equivalently, the first index `i` with `arr[i] >= x`. `bisect_right` returns the *rightmost* such index — first `i` with `arr[i] > x`. For a sorted array containing `x` once, they differ by 1.

??? question "2. Why does `lo + (hi - lo) // 2` matter in non-Python languages?"
    `(lo + hi) // 2` can overflow when both are near INT_MAX. Subtracting first keeps the intermediate small. Python integers are arbitrary precision so it's unnecessary, but it's a defensive habit worth keeping.

??? question "3. In rotated array search, why is the test `nums[lo] <= nums[mid]` and not `<`?"
    When the search range has shrunk to `lo == mid`, the left half is a single element — trivially sorted. Strict `<` would call this case "right half sorted" incorrectly. The `<=` includes the degenerate single-element case.

??? question "4. How do you detect non-monotonicity in answer-space search?"
    Test `feasible(x)` and `feasible(x+1)` for several `x`. If you ever find `feasible(x)` true and `feasible(x+1)` false, the predicate is non-monotone. In an interview, *prove* monotonicity before coding (usually a one-line greedy argument).

??? question "5. How does the LC 240 shed-row search work?"
    Start at the top-right corner. If the value equals target, done. If it's larger, move left (column is dropped). If smaller, move down (row is dropped). Each step eliminates an entire row or column, so total steps ≤ m + n. Beats the naive m × log(n) and is *not* a binary search but is asked under the same "modified binary search" umbrella.

??? question "6. Why does duplicate-rotated-array search become O(n) worst case?"
    When `nums[lo] == nums[mid] == nums[hi]`, neither half can be confirmed sorted — the rotation pivot might be anywhere. The only safe move is to shrink the range by 1 from both ends. Pathological all-duplicate input forces n/2 such shrinks → O(n).

??? question "7. How would you binary search on an infinite array?"
    Exponential bracketing: start `lo = 0, hi = 1`. While `arr[hi] < target`, double `hi`. Once `arr[hi] >= target`, run a normal binary search on `[lo, hi]`. Total: O(log answer_index).

??? question "8. When should you reach for `bisect` over hand-rolled binary search?"
    Production code: always `bisect`. Interview code: `bisect` if the interviewer is okay with stdlib; otherwise hand-roll lower_bound/upper_bound and explain that they match `bisect_left` / `bisect_right` semantics.

---

> **Next pattern up:** Top-K Elements — heaps for "the k largest / smallest / closest / most-frequent," plus the QuickSelect alternative that runs in average O(n) (page coming next).
