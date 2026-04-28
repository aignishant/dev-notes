# Two Pointers

> The most general two-index technique in interviews. You maintain two indices that walk through the input under some discipline — towards each other, in the same direction at different speeds, or as a partition boundary — and decide their next step based on what you observe. **Sliding window is a special case** of two pointers; this page covers the rest.

---

## 📖 What is two pointers?

You have an array (or string, or linked list) and two indices `i` and `j`. Instead of nesting two loops to consider every `(i, j)` pair (O(n²)), you exploit some structure — usually the input being **sorted** or having a **monotonic property** — to advance one or both pointers each step. **Each pointer moves at most n times → O(n) total.**

The pattern reduces "look at every pair" problems from O(n²) to O(n) when the input has the right shape.

!!! tip "The signal — when to reach for two pointers"
    Reach for it when:

    - The input is **sorted** (or you can sort it cheaply) and you're searching for a pair / triple with a sum / difference property.
    - You need to **partition** an array in-place (Dutch National Flag, move zeros, remove duplicates).
    - The problem is on a **palindrome** or **mirror property** — you walk inward from both ends.
    - You need to **merge two sorted streams** without extra memory beyond the output.
    - You see "in-place," "without extra space," or "linear time on a sorted array."

    If the input is unsorted and you need order-aware traversal, sliding window or sort-first-then-two-pointers usually wins over hash maps.

---

## 🧩 The four flavors

Every two-pointer problem is one of these four shapes. Once you can name the flavor, the template falls out.

### Flavor 1: Opposite ends — converging

`left` starts at 0, `right` at `n - 1`. They walk towards each other based on a comparison. Used when the input is **sorted** and you want a pair with a target relationship.

```python
def opposite_ends(arr: list[int], target: int) -> tuple[int, int] | None:
    """Find indices (i, j) with arr[i] + arr[j] == target. arr must be sorted."""
    left, right = 0, len(arr) - 1
    while left < right:
        s = arr[left] + arr[right]
        if s == target:
            return (left, right)
        if s < target:
            left += 1                    # need larger sum → grow the small side
        else:
            right -= 1                   # need smaller sum → shrink the large side
    return None
```

**Examples:** Two Sum II (sorted), 3Sum, Container With Most Water, Trapping Rain Water, Valid Palindrome, Reverse String.

### Flavor 2: Same direction — different speeds

Both pointers start at the same end and move forward. One advances faster or under different rules. **Sliding window is this flavor**, but so are partition-style problems where `slow` lags `fast` to mark a boundary.

```python
def remove_value_inplace(arr: list[int], val: int) -> int:
    """Move all elements != val to the front; return the new length."""
    slow = 0
    for fast in range(len(arr)):
        if arr[fast] != val:
            arr[slow] = arr[fast]
            slow += 1
    return slow
```

**Examples:** Move Zeroes, Remove Duplicates from Sorted Array, Remove Element, Sort Colors (3-way partition), Partition List.

### Flavor 3: Two arrays — merge / compare

Each pointer indexes a *different* array. They advance based on a comparison between current elements.

```python
def merge_sorted(a: list[int], b: list[int]) -> list[int]:
    """Merge two sorted arrays into one sorted output."""
    out: list[int] = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:]); out.extend(b[j:])
    return out
```

**Examples:** Merge Sorted Array (LC 88), Intersection of Two Arrays II, Merge Two Sorted Lists, Is Subsequence, Backspace String Compare.

### Flavor 4: Fast & slow — same array, different speeds (cycle / midpoint)

Both pointers start at the head; `fast` moves 2 steps per `slow`'s 1. Used for cycle detection (Floyd's) and finding the midpoint of a linked list. Important enough to get its own [pattern page](03-fast-slow-pointers.md) — listed here for completeness.

```python
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

---

## ⚡ Why is this O(n)?

In Flavors 1 and 2, **each pointer moves at most n times** and never goes backward. Total advances: ≤ 2n → O(n). The decision per step is O(1).

In Flavor 3, the loop runs at most `len(a) + len(b)` times — each iteration advances exactly one pointer.

In Flavor 4, `fast` runs at most n/2 iterations before either reaching the end or meeting `slow` inside a cycle.

The trade-off: you need either a sorted input or a structural invariant (cycle, mirror) to know which pointer to advance. **Two pointers buys you O(n) at the cost of O(n log n) sorting** if the input wasn't sorted to begin with — still a huge win over O(n²) for n ≥ 1000.

!!! warning "Common confusion"
    Two pointers vs sliding window:
    
    - **Sliding window**: both pointers move *forward only*, and you maintain "window state" (sum, count, hash map). The window represents a *contiguous subarray*.
    - **Two pointers (general)**: pointers can move *toward each other*, or be in *different arrays*, or have *no concept of a window*.
    
    Every sliding window is a two-pointer; not every two-pointer is a sliding window.

---

## 🔬 The 7 sub-patterns

Every two-pointer problem reduces to one of these:

| # | Sub-pattern | Pointer discipline | Example problem |
|---|---|---|---|
| 1 | **Pair-sum on sorted array** | Opposite ends, sum-compare-and-step | Two Sum II, 3Sum |
| 2 | **Container / volume** | Opposite ends, take min × width | Container With Most Water |
| 3 | **In-place partition** | Slow/fast, slow marks boundary | Move Zeroes, Sort Colors |
| 4 | **Mirror / palindrome** | Opposite ends, equality check | Valid Palindrome, Reverse |
| 5 | **Merge / compare two arrays** | Two indices, advance smaller | Merge Sorted Array, Is Subsequence |
| 6 | **Trim from both ends** | Opposite ends, conditional shrink | Trapping Rain Water |
| 7 | **K-tuple via fixed-pivot** | Outer fix one, inner two-pointer | 3Sum, 4Sum |

Master these 7 mechanisms and you've solved every interview two-pointer problem.

---

## 📋 The 20 problems

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 5 (full v3 solutions for every pattern problem)

### Opposite ends — pair / triple sums (5)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum II — Input Sorted | <span class="diff-medium">Medium</span> | Pair-sum sorted | [📝](#deep-dive-1-two-sum-ii-input-sorted) |
| 2 | 3Sum | <span class="diff-medium">Medium</span> | Fix-pivot + two-pointer | [✅](../02-data-structures/arrays/01-array-basics.md#problem-12-3sum) |
| 3 | 3Sum Closest | <span class="diff-medium">Medium</span> | Fix-pivot + two-pointer | 🚧 |
| 4 | 4Sum | <span class="diff-medium">Medium</span> | Two fixed pivots + two-pointer | 🚧 |
| 5 | Valid Triangle Number | <span class="diff-medium">Medium</span> | Pair-sum sorted, count | 🚧 |

### Container / area — opposite ends (3)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 6 | Container With Most Water | <span class="diff-medium">Medium</span> | Container | [✅](../02-data-structures/arrays/01-array-basics.md#problem-11-container-with-most-water) |
| 7 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Trim from both ends | [📝](#deep-dive-2-trapping-rain-water) |
| 8 | Boats to Save People | <span class="diff-medium">Medium</span> | Container, greedy | 🚧 |

### Mirror / palindrome (3)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 9 | Valid Palindrome | <span class="diff-easy">Easy</span> | Mirror | [✅](../02-data-structures/strings/01-string-basics.md#problem-3-valid-palindrome) |
| 10 | Valid Palindrome II (one-delete) | <span class="diff-easy">Easy</span> | Mirror with one skip | 🚧 |
| 11 | Reverse String / Reverse Vowels | <span class="diff-easy">Easy</span> | Mirror, swap | [✅](../02-data-structures/strings/01-string-basics.md#problem-2-reverse-string) |

### In-place partition — slow/fast (5)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 12 | Move Zeroes | <span class="diff-easy">Easy</span> | Partition | [✅](../02-data-structures/arrays/01-array-basics.md#problem-3-move-zeroes) |
| 13 | Remove Duplicates from Sorted Array | <span class="diff-easy">Easy</span> | Partition | [✅](../02-data-structures/arrays/01-array-basics.md#problem-5-remove-duplicates-from-sorted-array) |
| 14 | Remove Element | <span class="diff-easy">Easy</span> | Partition | 🚧 |
| 15 | Sort Colors (Dutch Flag) | <span class="diff-medium">Medium</span> | 3-way partition | [✅](../02-data-structures/arrays/01-array-basics.md#problem-16-sort-colors-dutch-national-flag) |
| 16 | Partition List (linked list) | <span class="diff-medium">Medium</span> | Partition | [✅](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-21-partition-list) |

### Two arrays — merge / compare (4)

| # | Problem | Difficulty | Sub-pattern | Status |
|---|---|---|---|---|
| 17 | Merge Sorted Array (in-place) | <span class="diff-easy">Easy</span> | Merge from back | [📝](#deep-dive-3-merge-sorted-array-in-place) |
| 18 | Is Subsequence | <span class="diff-easy">Easy</span> | Two-array compare | 🚧 |
| 19 | Intersection of Two Arrays II | <span class="diff-easy">Easy</span> | Merge sorted | 🚧 |
| 20 | Backspace String Compare (O(1) space) | <span class="diff-medium">Medium</span> | Two-string back-walk | 🚧 |

---

## 🔬 Deep-dives — 3 templates that cover everything

Picked because:

- **#1 Two Sum II** demonstrates the **opposite-ends sorted** flavor (the simplest and most-asked).
- **#2 Trapping Rain Water** demonstrates the **trim-from-both-ends with state** flavor — the canonical "hard" two-pointer.
- **#3 Merge Sorted Array** demonstrates **two-array merge with the "fill from the back" trick** — the most common in-place merge.

Master these three skeletons and you can solve every problem in the table above by adapting the comparison and what you record.

Format: thinking process → optimal solution → dry run → complexity → variants.

---

### Deep-dive 1: Two Sum II — input sorted

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Everyone</span>

> Given a **sorted** array of integers and a target, find the *1-indexed* pair of indices whose values sum to the target. Exactly one solution exists. (LeetCode 167.)

Example: `numbers = [2, 7, 11, 15]`, `target = 9` → `[1, 2]` (because `numbers[0] + numbers[1] = 9`).

#### 📖 Story mode

A sorted ledger of donations. You need to find two donors whose contributions sum to a specific number. Walking from both ends inward gets you there in one pass.

#### 🧠 Thinking process

- **Brute force**: nested loops over all pairs. O(n²).
- **Hash map**: walk once, look up `target − x`. O(n) time, O(n) space — but ignores that the input is sorted.
- **Insight (two pointers)**: with a sorted array, start at both ends. If sum is too small, advance left (gain). If too large, retract right (lose). Each pointer moves at most n times → O(n) time, **O(1) space**.

The interviewer specifically gives you a sorted array because they want the O(1)-space solution.

#### 🐍 Optimal solution

```python
def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    """1-indexed pair of indices that sum to target. Input is sorted."""
    left, right = 0, len(numbers) - 1
    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            return [left + 1, right + 1]   # 1-indexed
        if s < target:
            left += 1
        else:
            right -= 1
    return []                              # spec guarantees a solution
```

The decision is monotonic: once `left` advances, all smaller pairs `(left', right)` with `left' < left` are already eliminated. Same for `right`.

#### 🔍 Dry run on `numbers = [2, 7, 11, 15]`, `target = 9`

| left | right | numbers[left] | numbers[right] | sum | action |
|---|---|---|---|---|---|
| 0 | 3 | 2 | 15 | 17 | sum > target, right-- |
| 0 | 2 | 2 | 11 | 13 | sum > target, right-- |
| 0 | 1 | 2 | 7 | 9 | **match → return [1, 2]** |

Three iterations on n=4. Brute force would have done 6 iterations (`C(4,2)`).

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Brute force | O(n²) | O(1) |
| Hash map | O(n) | O(n) |
| **Two pointers** | **O(n)** | **O(1)** |

#### 🔄 Variants you might be asked

??? question "What if the array isn't sorted?"
    Sort first → O(n log n) total, still beats hash-map for memory-constrained environments. Or use a hash map (LC 1, Two Sum) → O(n) time, O(n) space. Pick based on whether interviewer cares more about time or space.

??? question "Find all unique pairs that sum to target (no duplicates)."
    Same loop, but on a match advance *both* pointers, and skip subsequent equal values to avoid re-emitting the same pair. Pattern continues into 3Sum.

??? question "3Sum — find all unique triples summing to 0."
    Sort, then for each `i` from 0 to n-3, run two-pointer on the remainder for `target = -nums[i]`. Skip duplicate `i` values and duplicates within the inner loop. O(n²).

??? question "Closest pair — sum closest to target."
    Track `best_diff = min over the loop of |sum - target|` and the corresponding pair. Same pointer discipline.

??? question "Pair with smallest absolute difference."
    Return `numbers[left+1] - numbers[left]` minimum across consecutive pairs in a sorted array. Single pass, no two pointers needed — but worth mentioning the relationship.

#### 🐛 Common bugs

- Returning **0-indexed** when the spec asks for **1-indexed** — read carefully.
- `while left <= right` instead of `<` — you'd consider `(i, i)` which the spec disallows.
- Advancing both pointers on equal mismatches — the comparison must be `<` or `>`, not just `!=`.
- Forgetting that the input is *sorted* and reaching for a hash map — wastes the structure.

---

### Deep-dive 2: Trapping Rain Water

<span class="diff-hard">Hard</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Meta</span>

> Given `n` non-negative integers representing an elevation map where each bar has width 1, compute how much water it can trap after raining. (LeetCode 42.)

Example: `height = [0,1,0,2,1,0,1,3,2,1,2,1]` → `6`.

```
    │
█   ██  █
█ ████ ██
████████████
```

The water trapped at index `i` is `min(maxLeft[i], maxRight[i]) - height[i]` (clamped to ≥ 0).

#### 📖 Story mode

A 1D landscape after rain. Where water pools depends on the *minimum* of the maximum walls on each side. Walking inward from both ends with two pointers, the side with the *smaller* current wall is always the limiting factor — so we advance it.

#### 🧠 Thinking process

- **Brute force**: at each `i`, scan left and right for max walls. O(n²).
- **Precompute arrays**: `maxLeft[i]` and `maxRight[i]` in two passes. Then sum the formula. O(n) time, **O(n) space**.
- **Insight (two pointers)**: the water at `i` is bounded by `min(maxLeft, maxRight)`. If we know `maxLeft < maxRight` so far, then `i` is bounded by `maxLeft` — we don't need to know the exact `maxRight`. Walk inward from the side whose current max is smaller. **O(n) time, O(1) space.**

This is the canonical "trim from both ends with state" template.

#### 🐍 Optimal solution

```python
def trap(height: list[int]) -> int:
    """Total water trapped. Two-pointer O(n) time, O(1) space."""
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            # left side is the binding constraint
            if height[left] >= left_max:
                left_max = height[left]            # raise the wall
            else:
                water += left_max - height[left]   # trap above this column
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
    return water
```

The invariant: at every step, the *smaller* of `height[left]` and `height[right]` is below or equal to *some* wall on the other side (because we haven't crossed yet). So that side's `*_max` is a valid bound on water at the current pointer.

#### 🔍 Dry run on `height = [0,1,0,2,1,0,1,3,2,1,2,1]`

| left | right | height[L] | height[R] | left_max | right_max | water | action |
|---|---|---|---|---|---|---|---|
| 0 | 11 | 0 | 1 | 0 | 0 | 0 | L<R, raise left_max=0, L++ |
| 1 | 11 | 1 | 1 | 0→1 | 0 | 0 | R<=L, raise right_max=1, R-- |
| 1 | 10 | 1 | 2 | 1 | 1 | 0 | L<R, no raise (h≥lm), L++ |
| 2 | 10 | 0 | 2 | 1 | 1 | 0+1=1 | L<R, water += 1-0=1, L++ |
| 3 | 10 | 2 | 2 | 1→2 | 1 | 1 | R<=L, raise right_max=2, R-- |
| 3 | 9 | 2 | 1 | 2 | 2 | 1 | R<L, no raise, water += 2-1=2, R-- |
| 3 | 8 | 2 | 2 | 2 | 2 | 2 | R<=L, no raise (h≥rm), R-- |
| 3 | 7 | 2 | 3 | 2 | 2 | 2 | L<R, no raise, L++ |
| 4 | 7 | 1 | 3 | 2 | 2 | 2+1=3 | L<R, water += 2-1=1, L++ |
| 5 | 7 | 0 | 3 | 2 | 2 | 3+2=5 | L<R, water += 2-0=2, L++ |
| 6 | 7 | 1 | 3 | 2 | 2 | 5+1=6 | L<R, water += 2-1=1, L++ |
| 7 | 7 | — | — | — | — | 6 | L<R fails, exit |

Answer: 6.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Brute force | O(n²) | O(1) |
| Precomputed maxes | O(n) | O(n) |
| **Two pointers** | **O(n)** | **O(1)** |
| Monotonic stack | O(n) | O(n) |

#### 🔄 Variants you might be asked

??? question "Trapping Rain Water II (2D / LC 407)."
    Doesn't reduce to two pointers — needs a min-heap that always processes the *lowest border cell first*. Mention immediately if the interviewer goes 2D.

??? question "What if heights can be negative?"
    Spec disallows it (rain pools above ground, not below). Two-pointer still works mathematically but the "water level" interpretation breaks.

??? question "Return *where* the maximum pool of water sits, not just the total."
    Track `(left, right, depth)` of the largest contiguous water span. Same loop structure with extra bookkeeping.

??? question "Streaming heights — water as new bars are added on the right."
    Pre-compute prefix max from the left, post-compute suffix max from the right. As new bars arrive on the right, update suffix max in O(1) and recompute the affected range. Or accept O(n) per query — depends on rate.

#### 🐛 Common bugs

- Updating `*_max` *after* the comparison instead of *before* — water is computed against an outdated max.
- Using `<=` in `height[left] < height[right]` — when equal, you need a deterministic tie-break (this code picks "advance left").
- Off-by-one in `while left < right` — getting it wrong skips the last column.
- Confusing this with the **monotonic stack** solution — both work; two-pointer is harder to derive but uses O(1) space.

---

### Deep-dive 3: Merge Sorted Array (in-place)

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Microsoft</span>

> You're given two sorted arrays `nums1` (size `m + n`, with the last `n` slots empty / placeholder) and `nums2` (size `n`). Merge `nums2` into `nums1` in sorted order, **in place** in `nums1`. (LeetCode 88.)

Example: `nums1 = [1, 2, 3, 0, 0, 0]`, `m = 3`, `nums2 = [2, 5, 6]`, `n = 3` → `nums1` becomes `[1, 2, 2, 3, 5, 6]`.

#### 📖 Story mode

Two sorted lists of timestamped events; one has trailing slots reserved. You need the merged stream in the larger array, without allocating temporary memory.

#### 🧠 Thinking process

- **Brute force**: copy `nums2` into `nums1[m:]`, then sort `nums1`. O((m+n) log (m+n)).
- **Front-to-back two-pointer**: would clobber unread `nums1` values. You'd need a temp array → O(m+n) space.
- **Insight (back-to-front)**: write from the *end* of `nums1` backward. The trailing slots are empty, so you never overwrite an unread value. **O(m+n) time, O(1) space.**

The "fill from the back" trick is the entire lesson here.

#### 🐍 Optimal solution

```python
def merge_in_place(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    """In-place merge of nums2 into nums1. Both inputs are sorted."""
    i, j, k = m - 1, n - 1, m + n - 1     # last real, last in nums2, last slot
    while i >= 0 and j >= 0:
        if nums1[i] > nums2[j]:
            nums1[k] = nums1[i]; i -= 1
        else:
            nums1[k] = nums2[j]; j -= 1
        k -= 1
    # Drain leftover nums2 (nums1 leftovers are already in place)
    while j >= 0:
        nums1[k] = nums2[j]; j -= 1; k -= 1
```

We never overwrite an `i`-position because `k > i` is the invariant — the write head is always to the right of (or at) the read head in `nums1`.

#### 🔍 Dry run on `nums1 = [1, 2, 3, 0, 0, 0]`, `m = 3`, `nums2 = [2, 5, 6]`, `n = 3`

| i | j | k | nums1[i] | nums2[j] | write | nums1 after |
|---|---|---|---|---|---|---|
| 2 | 2 | 5 | 3 | 6 | 6 to slot 5 | `[1,2,3,0,0,6]` |
| 2 | 1 | 4 | 3 | 5 | 5 to slot 4 | `[1,2,3,0,5,6]` |
| 2 | 0 | 3 | 3 | 2 | 3 to slot 3 | `[1,2,3,3,5,6]` |
| 1 | 0 | 2 | 2 | 2 | 2 to slot 2 | `[1,2,2,3,5,6]` |
| 1 | -1 | 1 | — | — | exit while | `[1,2,2,3,5,6]` |

The drain loop doesn't run because `j` hit -1. `nums1`'s prefix `[1, 2]` is already correctly placed.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| Concat + sort | O((m+n) log (m+n)) | O(1) |
| Front-merge with temp | O(m+n) | O(m) |
| **Back-merge in place** | **O(m+n)** | **O(1)** |

#### 🔄 Variants you might be asked

??? question "Merge two sorted linked lists."
    Different storage, same idea — but you don't need the back-to-front trick because you can rewire pointers without overwriting. See [LL P2 — Merge Two Sorted Lists](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-2-merge-two-sorted-lists).

??? question "Merge K sorted arrays."
    K-way merge with a min-heap — heap of `(value, array_id, index)` tuples. O(N log k) where N = total elements. See [LL P27 — Merge K Sorted Lists](../02-data-structures/linked-lists/01-linked-list-basics.md#problem-27-merge-k-sorted-lists).

??? question "What if `nums1` doesn't have trailing slots? You're given two arrays the same size."
    The back-to-front trick still works *if* you can overwrite `nums1` from the back — provided the merged result fits and you've allocated extra space. Otherwise, two-pointer with a temp array.

??? question "Streaming merge — both arrays arrive as iterators."
    Use `heapq.merge(a, b)` (Python stdlib). It's a generator that yields one element at a time using exactly this two-pointer logic. O(m+n) total, O(1) space (lazy).

#### 🐛 Common bugs

- Filling from the **front** without a temp array — overwrites unread `nums1` values.
- Forgetting the drain loop for leftover `nums2` — if `nums1`'s smallest is smaller than all of `nums2`, you exit the main loop with `j ≥ 0`.
- Using `m + n` instead of `m + n - 1` for the initial `k` — off-by-one writes past the end.
- Not noticing leftover `nums1` is already in place — adding a redundant drain loop for `i` is harmless but wasteful.

---

## 🐛 Common bugs across all two-pointer problems

| Bug | Symptom | Fix |
|---|---|---|
| Advancing the wrong pointer on equal values | Misses pairs / triples | Decide tie-break upfront; advance both for "all unique" |
| Forgetting to skip duplicates in 3Sum-style | Repeated triples in output | After a match, skip while `nums[i] == nums[i-1]` |
| Off-by-one in `while left < right` | Misses last comparison or considers `(i, i)` | Use `<` for distinct pairs, `<=` only when same-index allowed |
| Updating window state in the wrong order | Wrong answer | Compute decision *before* mutating pointers |
| Applying two-pointers to unsorted input | Wrong answer | Sort first, or switch to hash map |
| Front-merge that overwrites unread values | Data loss | Merge from the back |

---

## 🎯 How interviewers ask two-pointer problems

### Common phrasings

| What they say | What it means |
|---|---|
| *"Sorted array, find a pair that sums to X"* | Opposite-ends, sum-compare |
| *"In place, O(1) space"* | Slow/fast partition |
| *"Two sorted arrays, merge / find common"* | Two-array compare |
| *"Palindrome", "mirror", "reverse"* | Opposite-ends, equality check |
| *"Container", "trap", "area"* | Opposite-ends with state |
| *"K-tuple summing to target"* | Outer-fix + inner two-pointer |

### What they're testing

1. **Pattern recognition** — do you spot the sortedness or the symmetry?
2. **Pointer discipline** — can you state the invariant and prove the loop terminates?
3. **Decision rule** — given the comparison, which pointer moves and why?
4. **In-place reasoning** — can you mutate without clobbering unread data?
5. **Why O(n)** — can you explain the linearity argument?

### The 4-step interview flow

1. **Recognize** the structure: sorted? symmetric? two arrays? cycle?
2. **Pick the flavor** (opposite ends / same direction / two arrays / fast-slow).
3. **State the invariant** out loud — what's true at every iteration?
4. **Decide the comparison rule** — which pointer advances based on what observation?

### Red flags

- Solving with a hash map when the input is **sorted** — you missed the structural hint.
- Front-merging an in-place problem and asking for a temp array — you missed the back-to-front trick.
- Writing nested loops for sorted-array pair-sum — you missed the pattern entirely.

---

## 🔗 How two pointers connects to other patterns

| Pattern | Connection |
|---|---|
| **Sliding window** | Sliding window is two-pointer where both indices move forward only and you maintain window state. |
| **Fast & slow pointers** | A specialization where pointers move at different speeds in the same array (cycle / midpoint). [Dedicated page](03-fast-slow-pointers.md). |
| **Binary search** | Binary search is *one* pointer collapsing a range; two pointers is *two* pointers each making local decisions. Both exploit sortedness. |
| **Sorting** | Sorting is the price you pay to enable two-pointer when the input isn't already sorted. O(n log n) sort + O(n) two-pointer beats O(n²) brute. |
| **Merge sort** | The merge step is exactly Flavor 3 (two-array merge). |
| **Monotonic stack** | An alternative to two-pointer for "trim both ends with state" problems like Trapping Rain Water — same answer, different mechanism. |
| **Greedy** | Many two-pointer decisions are greedy (always advance the smaller side). The pattern formalizes a class of greedy choices. |

---

## ✅ Self-check — 8 questions

??? question "1. What's the difference between two pointers and sliding window?"
    Sliding window is a *special case* where both pointers move forward only and you track window state (sum, count, hash map). Two pointers is general — they may move toward each other (palindrome), in different arrays (merge), or at different speeds (cycle).

??? question "2. Why does opposite-ends two-pointer require a sorted input?"
    Because the decision rule (advance the side that makes the sum / area / score better) only converges when the underlying values are monotonic. On unsorted input you can't tell which side is "binding."

??? question "3. In Trapping Rain Water two-pointer, why is the smaller side always the binding constraint?"
    Because the side with the smaller max-so-far is *guaranteed* to be the lower wall of the bound at the current column — you can't have water higher than the smaller of the two bounding walls.

??? question "4. Why merge from the back in LC 88?"
    To avoid overwriting unread values in `nums1`. The trailing slots are empty, so writing to position `m+n-1, m+n-2, …` is always safe.

??? question "5. When solving 3Sum, why do you skip duplicates?"
    To avoid emitting the same triple twice. After finding `(a, b, c)`, advance past all positions with the same `b` (and the same `a` for the outer loop) before resuming.

??? question "6. Can two pointers handle negative numbers?"
    Yes — what matters is sortedness, not sign. The shrink-when-valid logic from sliding window breaks on negatives, but the converging-from-ends logic does not.

??? question "7. What's the loop invariant in opposite-ends two-pointer?"
    "Every pair `(i, j)` with `i < left` or `j > right` has been considered and rejected based on its comparison with the target." That's why neither pointer needs to backtrack.

??? question "8. The give-away that a problem is two-pointer (not sliding window)?"
    Sortedness, symmetry, or two distinct sequences. If you see "sorted array + pair / triple" or "palindrome" or "merge two arrays," reach for two pointers. Sliding window kicks in for "longest / shortest contiguous subarray."

---

## 🔁 Where to go from here

- **Next pattern**: [Fast & Slow Pointers](03-fast-slow-pointers.md) — the specialization for cycle detection and midpoints.
- **Apply it**: every problem in the table above. Start with Two Sum II → 3Sum → Trapping Rain Water as the canonical progression.
- **Cross-reference**: Arrays chapter problems P3, P5, P11, P12, P13, P16; Strings P2, P3; Linked Lists P21.
