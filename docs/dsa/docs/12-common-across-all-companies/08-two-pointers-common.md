# Two pointers — common across all companies

> Two indices, one array, one invariant. The cheapest `O(n)` trick in interview prep, and the one most likely to surprise you with how far it stretches.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

## 📖 Why two pointers is "everywhere"

When the input is **sorted** (or can be sorted cheaply), or when you have **two sequences to compare**, or when you need **in-place rearrangement without extra memory** — the answer is almost always two pointers. The pattern is interview-loved because it forces candidates to articulate an *invariant* and prove forward progress, both of which are exactly what hiring panels score on.

These 14 problems span easy warm-ups (TCS / ISRO favourites) through `O(n)` trap-rain-water style brain-twisters (Google / Meta gateposts).

---

## 🧩 Patterns that drive these 14

| Pattern | Frequency | Problems on this page |
|---|---|---|
| **Opposite-ends converging** | ⭐⭐⭐⭐⭐ | Two Sum II, Container Water, Valid Palindrome, Reverse String, Trapping Rain Water |
| **Read / write (in-place compaction)** | ⭐⭐⭐⭐⭐ | Move Zeroes, Remove Duplicates I/II, Sort Colors |
| **Sort + outer-loop + inner two-pointer** | ⭐⭐⭐⭐ | 3Sum, 3Sum Closest, 4Sum |
| **Squared / merge-style scan** | ⭐⭐⭐ | Squares of Sorted Array, Backspace Compare |
| **Expand-from-centre** | ⭐⭐⭐ | Longest Mountain |
| **Skip-duplicates after move** | ⭐⭐⭐⭐ | 3Sum, 4Sum |

---

## 📋 The 14 questions

Difficulty pills: <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Two Sum II — sorted input | <span class="diff-medium">Medium</span> | Opposite ends | 167 |
| 2 | 3Sum | <span class="diff-medium">Medium</span> | Sort + fixed + 2P | 15 |
| 3 | 3Sum Closest | <span class="diff-medium">Medium</span> | Sort + fixed + 2P | 16 |
| 4 | 4Sum | <span class="diff-medium">Medium</span> | Sort + 2 fixed + 2P | 18 |
| 5 | Container With Most Water | <span class="diff-medium">Medium</span> | Opposite ends + greedy shrink | 11 |
| 6 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Opposite ends + max invariant | 42 |
| 7 | Remove Duplicates from Sorted Array | <span class="diff-easy">Easy</span> | Read / write | 26 |
| 8 | Remove Duplicates from Sorted Array II | <span class="diff-medium">Medium</span> | Read / write with count | 80 |
| 9 | Move Zeroes | <span class="diff-easy">Easy</span> | Read / write | 283 |
| 10 | Sort Colors (Dutch flag) | <span class="diff-medium">Medium</span> | Three pointers | 75 |
| 11 | Valid Palindrome (I and II) | <span class="diff-easy">Easy</span> | Opposite ends + 1-skip | 125 / 680 |
| 12 | Reverse String | <span class="diff-easy">Easy</span> | Opposite ends | 344 |
| 13 | Squares of a Sorted Array | <span class="diff-easy">Easy</span> | Opposite ends + reverse fill | 977 |
| 14 | Backspace String Compare | <span class="diff-easy">Easy</span> | Reverse two pointers | 844 |
| 15 | Longest Mountain in Array | <span class="diff-medium">Medium</span> | Expand-from-centre | 845 |

---

## 🔬 Deep-dive 1 — 3Sum (LC 15)

> *Find all unique triplets `(a, b, c)` in `nums` such that `a + b + c == 0`.*

Sort first. For each fixed `nums[i]`, the remaining problem is "find two numbers in a sorted array summing to `-nums[i]`" — pure two-pointer. The hard part isn't the algorithm; it's **deduplicating without a `set`**.

??? question "Full solution — `three_sum`"

    ```python linenums="1"
    from __future__ import annotations

    def three_sum(nums: list[int]) -> list[list[int]]:
        """All unique triplets summing to zero.

        Time: O(n^2)   Space: O(1) extra (excluding output)
        """
        nums.sort()
        n = len(nums)
        out: list[list[int]] = []

        for i in range(n - 2):
            # Early exit: if smallest possible triplet > 0, done.
            if nums[i] > 0:
                break
            # Skip duplicate anchors.
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            target = -nums[i]
            l, r = i + 1, n - 1

            while l < r:
                s = nums[l] + nums[r]
                if s == target:
                    out.append([nums[i], nums[l], nums[r]])
                    l += 1
                    r -= 1
                    # Skip duplicate left and right.
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
                    while l < r and nums[r] == nums[r + 1]:
                        r -= 1
                elif s < target:
                    l += 1
                else:
                    r -= 1

        return out
    ```

??? tip "The three dedup gates"
    1. **Anchor dedup** — `if i > 0 and nums[i] == nums[i - 1]: continue`. Prevents the same outer triplet from being constructed twice.
    2. **Left dedup** — only after a hit, advance `l` past the duplicate value just used.
    3. **Right dedup** — symmetric, advance `r` past the duplicate value just used.

    Skipping duplicates on `s < target` / `s > target` branches is **wrong** — you'll miss valid triplets. Only dedup *after a successful match*.

The same skeleton extends to **4Sum** (one extra outer loop, `O(n³)`), **k-Sum** in general (recursive), and **3Sum Closest** (track the minimum `|s − target|` instead of looking for equality).

---

## 🔬 Deep-dive 2 — Trapping Rain Water (LC 42)

> *Given non-negative heights, compute total water trapped after rain.*

The classic `O(n)` two-pointer with `O(1)` space. The clever bit: at each step, you trap water for the **shorter side** because the taller side already guarantees the boundary.

??? question "Full solution — `trap`"

    ```python linenums="1"
    from __future__ import annotations

    def trap(height: list[int]) -> int:
        """Total water trapped between bars.

        Time: O(n)   Space: O(1)
        """
        if not height:
            return 0

        l, r = 0, len(height) - 1
        max_left = max_right = 0
        water = 0

        while l < r:
            if height[l] < height[r]:
                # Left side is the bottleneck for water at index l.
                if height[l] >= max_left:
                    max_left = height[l]
                else:
                    water += max_left - height[l]
                l += 1
            else:
                # Right side is the bottleneck for water at index r.
                if height[r] >= max_right:
                    max_right = height[r]
                else:
                    water += max_right - height[r]
                r -= 1

        return water
    ```

??? note "Why it's correct — the invariant"
    Water trapped at index `i` is `min(max_to_left[i], max_to_right[i]) − height[i]`.

    **Claim:** when `height[l] < height[r]`, we already know that `max_to_right[l] ≥ height[r] > height[l] ≥ max_left`. So `min(max_left, max_to_right[l]) == max_left`, and we can compute water at `l` using only `max_left`.

    The symmetric argument holds for the other branch. We never need the *true* `max_to_right[l]`; we only need a lower bound that still dominates `max_left`, and `height[r]` provides exactly that.

!!! warning "Don't use `<=`"
    The branch must be strict `<`. With `<=`, on `height[l] == height[r]` you'd advance `l` while the invariant `max_to_right[l] ≥ height[r]` is still merely *equal* — fine here, but causes off-by-one confusion when you try to generalise. Use `<` and let the equal case fall to the `else`.

The same technique solves **Container With Most Water** (LC 11) — there you want `max area = (r − l) × min(h[l], h[r])`, and you always advance the **shorter side** for the same reason: advancing the taller side can only shrink area.

---

## 🃏 Cheatsheet

- **Choose your variant first** — opposite-ends? read/write? sort + outer + 2P? expand-from-centre? Naming the variant locks the template.
- **Sort is fair game** unless the problem says "preserve original order". Sorting unlocks 3Sum, 4Sum, 3Sum Closest, dedup tricks.
- **Dedup only after a hit** — never on the `<` / `>` branches. Three gates: anchor, left-after-hit, right-after-hit.
- **In-place compaction** — write pointer `w` lags read pointer `r`; `w` only advances when you commit a value to `nums[w]`.
- **Three-way partition (Dutch flag)** — `lo, mid, hi`. Swap-and-advance on 0, advance-only on 1, swap-and-shrink on 2. Don't advance `mid` when swapping with `hi`.
- **Squares of sorted array** — fill `out` from the back; whichever absolute value is bigger wins.
- **Trapping water invariant** — the shorter side is the bottleneck, so you can resolve it now and move on.
- **Container with Most Water** — always advance the shorter wall; equal walls, advance either (doesn't matter for the answer).
- **Backspace compare** — walk both strings *from the right*, skipping over `#` runs. Forward direction needs a stack.
- **Palindrome with one delete** — on mismatch, try `s[l+1..r]` and `s[l..r-1]`; if either is a palindrome, return true.
- **Edge cases**: empty array, length 1, all duplicates, all the same value, already sorted descending.
- **When two pointers fails**: the relation between left and right pointers must be **monotone**. If moving `l` right could ever require also moving `r` right (rather than left), you need a different tool — usually hashing or binary search.
