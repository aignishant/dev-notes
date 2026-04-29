# Binary search — common across all companies

> Halve the search space, double the salary. Master `bisect_left` semantics and "search on the answer" and you'll solve a dozen distinct interview problems with one template.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

## 📖 Why binary search is "everywhere"

Two reasons. First, **vanilla binary search on a sorted array** is the litmus test interviewers use to probe whether you can write off-by-one-free code under pressure (TCS / ISRO written tests, Amazon OAs). Second, **binary search on the answer** — the technique where the search space is *not* an array but a numerical range — turns a class of optimisation problems (Koko, Capacity to Ship, Split Array) into 20-line solutions, and Google / Meta interviewers love them.

A candidate who's comfortable with both styles is genuinely rare; this page makes you that candidate.

---

## 🧩 Patterns that drive these 14

| Pattern | Frequency | Problems on this page |
|---|---|---|
| **Vanilla binary search** | ⭐⭐⭐⭐⭐ | Binary Search, Search Insert, Sqrt(x) |
| **Lower / upper bound (`bisect`)** | ⭐⭐⭐⭐⭐ | First/Last Position, Find K Closest |
| **Rotated sorted array — "one half is sorted"** | ⭐⭐⭐⭐⭐ | Search Rotated I/II, Find Min Rotated |
| **Peak / unimodal** | ⭐⭐⭐⭐ | Find Peak Element, Single Element in Sorted |
| **2D binary search** | ⭐⭐⭐ | Search 2D Matrix I/II |
| **Binary search on the answer** | ⭐⭐⭐⭐⭐ | Koko, Ship Packages, Split Array, Median of Two |

---

## 📋 The 14 questions

Difficulty pills: <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Binary Search | <span class="diff-easy">Easy</span> | Vanilla | 704 |
| 2 | Search Insert Position | <span class="diff-easy">Easy</span> | Lower bound | 35 |
| 3 | First and Last Position of Element | <span class="diff-medium">Medium</span> | Lower + upper bound | 34 |
| 4 | Sqrt(x) | <span class="diff-easy">Easy</span> | Numeric BS | 69 |
| 5 | Find Peak Element | <span class="diff-medium">Medium</span> | Slope direction | 162 |
| 6 | Single Element in Sorted Array | <span class="diff-medium">Medium</span> | Pair-index parity | 540 |
| 7 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | One half sorted | 33 |
| 8 | Search in Rotated Sorted Array II | <span class="diff-medium">Medium</span> | Same + dup-skip | 81 |
| 9 | Find Minimum in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Compare to right | 153 |
| 10 | Search a 2D Matrix (I and II) | <span class="diff-medium">Medium</span> | Flat-index / staircase | 74 / 240 |
| 11 | Find K Closest Elements | <span class="diff-medium">Medium</span> | Window via lower bound | 658 |
| 12 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | Partition BS | 4 |
| 13 | Koko Eating Bananas | <span class="diff-medium">Medium</span> | BS on answer | 875 |
| 14 | Capacity to Ship Packages | <span class="diff-medium">Medium</span> | BS on answer | 1011 |
| 15 | Split Array Largest Sum | <span class="diff-hard">Hard</span> | BS on answer | 410 |

---

## 🔬 Deep-dive 1 — Search in Rotated Sorted Array (LC 33)

> *A sorted array was rotated at some unknown pivot. Find `target` in `O(log n)`.*

The trick: at every step, **at least one half is sorted**. Decide which half by comparing `nums[mid]` to `nums[lo]`. Then check if `target` lies in the sorted half — if yes, recurse into it; otherwise, recurse into the other half (which contains the rotation).

??? question "Full solution — `search_rotated`"

    ```python linenums="1"
    from __future__ import annotations

    def search_rotated(nums: list[int], target: int) -> int:
        """Index of target in rotated sorted array, or -1.

        Time: O(log n)   Space: O(1)
        Assumes nums has no duplicates (LC 33).
        """
        lo, hi = 0, len(nums) - 1

        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid

            # Decide which half is sorted.
            if nums[lo] <= nums[mid]:
                # Left half [lo..mid] is sorted.
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:
                # Right half [mid..hi] is sorted.
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1

        return -1
    ```

??? tip "The decision tree"
    ```
    nums[lo] <= nums[mid] ?
       yes  -> left is sorted
              target in [nums[lo], nums[mid]) ?  go left  : go right
       no   -> right is sorted
              target in (nums[mid], nums[hi]] ?  go right : go left
    ```

    The bracket directions matter — left half uses `[lo, mid)` (open at mid because we already checked `nums[mid]`), and right uses `(mid, hi]`. Get this wrong and you'll either infinite-loop or skip the answer.

!!! warning "Duplicates change the rules (LC 81)"
    With duplicates, `nums[lo] == nums[mid]` no longer tells you which half is sorted. The fix: when `nums[lo] == nums[mid] == nums[hi]`, increment `lo` and decrement `hi` (worst-case `O(n)`), then resume binary search. The `O(log n)` worst case is lost.

For **Find Minimum in Rotated Sorted Array** (LC 153) the comparison flips: compare `nums[mid]` to `nums[hi]`. If `nums[mid] > nums[hi]`, the minimum is in `(mid, hi]`; else in `[lo, mid]`.

---

## 🔬 Deep-dive 2 — Koko Eating Bananas (LC 875)

> *Koko eats bananas at speed `k` per hour. Given pile sizes and a deadline `h` hours, find the minimum integer speed `k` to finish all piles in time.*

This is the **search on the answer** template. The search space is `k ∈ [1, max(piles)]`. The predicate `can_finish(k)` is monotone: if `k` works, every larger `k` also works. So we binary-search for the smallest `k` where `can_finish(k)` is true.

??? question "Full solution — `min_eating_speed`"

    ```python linenums="1"
    from __future__ import annotations
    from math import ceil

    def min_eating_speed(piles: list[int], h: int) -> int:
        """Smallest integer speed k so that all piles finish within h hours.

        Time: O(n log m)  where m = max(piles)
        Space: O(1)
        """

        def can_finish(k: int) -> bool:
            hours = 0
            for p in piles:
                # Each pile takes ceil(p / k) hours; finishing one pile early
                # doesn't carry over to the next.
                hours += (p + k - 1) // k
                if hours > h:
                    return False
            return True

        lo, hi = 1, max(piles)
        while lo < hi:
            mid = (lo + hi) // 2
            if can_finish(mid):
                hi = mid       # mid might be the answer; don't exclude it.
            else:
                lo = mid + 1   # mid is too slow; answer is strictly larger.

        return lo
    ```

??? note "Why this template generalises"
    The shape never changes:
    1. **Identify the answer range** `[lo, hi]` — usually `[min, max]` of inputs or `[1, sum]`.
    2. **Write `feasible(x)`** — does answer `x` satisfy the constraint?
    3. **Confirm monotonicity** — `feasible(x) => feasible(x + 1)` (or the reverse). This is the load-bearing invariant.
    4. **Binary search for the boundary** — smallest `x` where `feasible` flips from `False` to `True`.

    Same template, different `feasible`:

    | Problem | `feasible(x)` |
    |---|---|
    | Koko Eating Bananas | "speed `x` finishes within `h` hours" |
    | Capacity to Ship Packages | "capacity `x` ships within `D` days" |
    | Split Array Largest Sum | "max-subarray-sum `x` is achievable with ≤ `m` splits" |
    | Minimise Max Distance to Gas Station | "max gap `x` is achievable with `K` new stations" |

!!! tip "The `lo < hi` vs `lo <= hi` choice"
    For "find the boundary", use `while lo < hi` and update `hi = mid` / `lo = mid + 1`. This converges to the boundary index without overshoot.

    For "find an exact match in an array", use `while lo <= hi` and update `hi = mid - 1` / `lo = mid + 1`. This stops when the search space is empty.

    Mixing the two is the #1 source of binary-search bugs.

---

## 🃏 Cheatsheet

- **Two templates, learn both** — exact match (`lo <= hi`, `mid ± 1`) and boundary (`lo < hi`, `hi = mid`).
- **Overflow-safe mid** — `mid = lo + (hi - lo) // 2`. In Python it doesn't matter, but interviewers in C++/Java land care.
- **`bisect_left` vs `bisect_right`** — `bisect_left([1,2,2,3], 2) == 1`, `bisect_right(..., 2) == 3`. First/last position is `bl(x)` and `br(x) - 1`.
- **Rotated array decision** — `nums[lo] <= nums[mid]` ⇒ left half sorted; else right half sorted. Then check if `target` lies in the sorted half.
- **Search on answer recipe** — define range, write `feasible(x)`, confirm monotone, binary-search the boundary.
- **2D matrix (sorted rows + sorted columns)** — staircase from top-right; each comparison eliminates a row or column. `O(m + n)`.
- **2D matrix (fully sorted, flattened)** — treat as 1D of length `m·n`; `(r, c) = divmod(idx, cols)`. `O(log(m·n))`.
- **Peak element** — compare `nums[mid]` to `nums[mid + 1]`; go toward the rising slope.
- **Median of two sorted** — partition both arrays so left halves total `(m + n + 1) // 2`. Binary-search the partition of the *shorter* array.
- **Find K closest elements** — binary-search the *left edge* of the window in `[0, n - k]`; compare `x - arr[mid]` vs `arr[mid + k] - x`.
- **Sqrt(x)** — boundary template on `[0, x]`, predicate `mid * mid <= x`.
- **Single element in sorted (LC 540)** — pair-index trick: every full pair starts at an even index; binary-search where that breaks.
- **Edge cases**: empty array, single element, target smaller than min / larger than max, all duplicates, target at boundary.
- **When binary search fails**: predicate not monotone, or you can't define an `O(1)` / `O(n)` `feasible`. Most common slip — using BS on an unsorted array because "it's `log n`, must be faster". It's not; it's wrong.
