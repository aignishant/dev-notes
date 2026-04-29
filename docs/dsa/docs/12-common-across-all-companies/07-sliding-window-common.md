# Sliding window — common across all companies

> The window slides; the invariant holds. Master the "expand-right, shrink-left" rhythm and half of the medium-tier interview pool falls.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

## 📖 Why sliding window is "everywhere"

Every interviewer — product, service, or PSU — has at least one window problem in their bank because the technique compresses an `O(n²)` brute-force scan into `O(n)` using a single invariant: *the window always satisfies condition X*. Once you internalise the **expand-then-shrink** loop, the only thing that changes between problems is what you store inside the window (a counter, a deque, a frequency map, a sum).

This page covers 14 problems that have appeared in **at least three of the five tracked tracks** (Google, Meta, Amazon, TCS, ISRO) over the last 5 hiring cycles.

---

## 🧩 Patterns that drive these 14

| Pattern | Frequency | Problems on this page |
|---|---|---|
| **Fixed-size window** | ⭐⭐⭐⭐⭐ | Max Sum K, Anagrams, Permutation in String |
| **Variable-size window (shrink on violation)** | ⭐⭐⭐⭐⭐ | Longest Substring No Repeat, Min Window Substring, Longest Repeating Char Replacement |
| **At-most-K trick (`atMost(k) - atMost(k-1)`)** | ⭐⭐⭐⭐ | Subarrays K Distinct, Number of Nice Subarrays, Bounded Maximum |
| **Monotonic deque** | ⭐⭐⭐⭐ | Sliding Window Maximum |
| **Kadane / running sum** | ⭐⭐⭐⭐ | Maximum Subarray, Best Time Buy/Sell |
| **Two-counter "have/need"** | ⭐⭐⭐⭐ | Min Window Substring, Permutation in String |

---

## 📋 The 14 questions

Difficulty pills: <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Maximum Subarray (Kadane) | <span class="diff-medium">Medium</span> | Running sum / DP | 53 |
| 2 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | 121 |
| 3 | Maximum Sum of K Consecutive Elements | <span class="diff-easy">Easy</span> | Fixed window | 643 |
| 4 | Longest Substring Without Repeating Chars | <span class="diff-medium">Medium</span> | Variable window + set | 3 |
| 5 | Longest Repeating Character Replacement | <span class="diff-medium">Medium</span> | Variable window + max-freq | 424 |
| 6 | Longest Substring with At Most K Distinct | <span class="diff-medium">Medium</span> | Variable window + counter | 340 |
| 7 | Fruit Into Baskets | <span class="diff-medium">Medium</span> | At-most-2 window | 904 |
| 8 | Find All Anagrams in a String | <span class="diff-medium">Medium</span> | Fixed window + counter | 438 |
| 9 | Permutation in String | <span class="diff-medium">Medium</span> | Fixed window + counter | 567 |
| 10 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Variable window + have/need | 76 |
| 11 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 239 |
| 12 | Subarrays with K Different Integers | <span class="diff-hard">Hard</span> | At-most(k) − At-most(k−1) | 992 |
| 13 | Number of Subarrays with Bounded Maximum | <span class="diff-medium">Medium</span> | At-most-trick | 795 |
| 14 | Count Number of Nice Subarrays | <span class="diff-medium">Medium</span> | At-most-trick on parity | 1248 |

---

## 🔬 Deep-dive 1 — Minimum Window Substring (LC 76)

> *Given strings `s` and `t`, return the smallest window of `s` that contains every character of `t` (with multiplicity).*

The canonical "have/need" template. We track **how many distinct characters of `t` are currently satisfied** in the window — *not* total characters — using a single integer `have` against a target `need`.

??? question "Full solution — `min_window`"

    ```python linenums="1"
    from __future__ import annotations
    from collections import Counter

    def min_window(s: str, t: str) -> str:
        """Smallest substring of s containing all chars of t (with multiplicity).

        Time: O(|s| + |t|)   Space: O(|t|)
        """
        if not t or not s:
            return ""

        need: dict[str, int] = Counter(t)
        window: dict[str, int] = {}
        required = len(need)        # distinct chars we must satisfy
        have = 0                    # how many distinct chars are currently satisfied

        best_len = float("inf")
        best_l = 0
        l = 0

        for r, ch in enumerate(s):
            window[ch] = window.get(ch, 0) + 1
            if ch in need and window[ch] == need[ch]:
                have += 1

            # Shrink while window is valid — try to find a smaller one.
            while have == required:
                if r - l + 1 < best_len:
                    best_len = r - l + 1
                    best_l = l

                left_ch = s[l]
                window[left_ch] -= 1
                if left_ch in need and window[left_ch] < need[left_ch]:
                    have -= 1
                l += 1

        return "" if best_len == float("inf") else s[best_l : best_l + best_len]
    ```

**Why it's `O(n)`:** every character is added once (right pointer) and removed at most once (left pointer), so total work is `2n`.

??? tip "The mental model"
    - `need[c]` is fixed — it's the *demand*.
    - `window[c]` is the *current supply*.
    - `have` increments only at the **exact tipping point** `window[c] == need[c]`. Going from 2 → 3 of a char that's already satisfied does **not** bump `have`.
    - Symmetrically, `have` decrements only when we drop *below* `need[c]`.

This is the same skeleton you'll reuse for **Permutation in String**, **Find All Anagrams**, and **Smallest Substring Containing All Characters of Another String** — only the success condition differs.

---

## 🔬 Deep-dive 2 — Sliding Window Maximum (LC 239)

> *Given `nums` and window size `k`, return the maximum of every length-`k` window.*

Naive: `O(n·k)`. The trick is a **monotonic decreasing deque** of indices. The front always holds the index of the current window's maximum.

??? question "Full solution — `max_sliding_window`"

    ```python linenums="1"
    from __future__ import annotations
    from collections import deque

    def max_sliding_window(nums: list[int], k: int) -> list[int]:
        """Maximum of every length-k window in nums.

        Time: O(n)   Space: O(k)
        """
        if k == 0 or not nums:
            return []

        dq: deque[int] = deque()   # indices, values nums[dq] strictly decreasing
        out: list[int] = []

        for i, x in enumerate(nums):
            # 1. Drop indices that have fallen out of the window on the left.
            if dq and dq[0] <= i - k:
                dq.popleft()

            # 2. Maintain decreasing invariant: pop smaller-or-equal tails.
            while dq and nums[dq[-1]] <= x:
                dq.pop()

            dq.append(i)

            # 3. Once the first full window is formed, record the front.
            if i >= k - 1:
                out.append(nums[dq[0]])

        return out
    ```

**Why it's `O(n)`:** every index is appended once and popped at most once across the whole run — amortised `O(1)` per step.

??? note "The two invariants"
    1. **Window invariant:** `dq[0] >= i - k + 1` (front is inside the current window).
    2. **Monotone invariant:** `nums[dq]` is strictly decreasing front-to-back. So the front is always the maximum, and any element smaller than the current `x` in the tail is *useless* — it can never be the max of any future window that also contains `x`.

!!! warning "Common bug"
    Use `<=` (not `<`) when popping the tail. If you allow equal values to pile up, the deque grows unboundedly when the input has long runs of equal numbers, and your average-case complexity quietly degrades.

The same monotonic-deque pattern solves **Shortest Subarray with Sum at Least K** (LC 862, monotonic on prefix sums) and **Constrained Subsequence Sum** (LC 1425, monotonic on DP states).

---

## 🃏 Cheatsheet

- **Template skeleton** — `for r in range(n): expand; while invariant_violated: shrink l; record`.
- **Have/need** — count *distinct satisfied chars*, not total chars. Increment `have` only at the tipping point.
- **At-most-k trick** — to count subarrays with *exactly* k of something, compute `atMost(k) − atMost(k − 1)`. Works for distinct elements, parity counts, sum bounds.
- **Monotonic deque** — store **indices**, not values, so you can detect window expiry. Decreasing for max, increasing for min.
- **Fixed window** — initialise the first window outside the main loop, or use `if i >= k - 1` inside it.
- **Variable window** — left pointer monotonically increases. Total pointer movement is `2n`, hence `O(n)`.
- **Don't store `set` in the window** when you also need counts — use `Counter`. Sets break on duplicates.
- **Kadane is a window** — `max(nums[i], running + nums[i])` is "shrink to just `i` if running becomes harmful".
- **Edge cases to test**: empty input, `k = 0`, `k > n`, all-same elements, all-distinct elements, single element.
- **When sliding window doesn't apply**: the metric must be **monotone** as the window grows — adding an element can't *decrease* it. Counterexample: "longest subarray with sum ≤ K" with negative numbers — adding a negative can make a previously invalid window valid again. Use prefix-sum + deque instead.
