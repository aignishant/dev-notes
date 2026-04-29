# Dynamic programming — common across all companies

> One pattern, many faces — overlapping subproblems plus optimal substructure beat brute-force exponential blow-ups.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Dynamic programming questions dominate every onsite loop because they test recursion, state design, and complexity reasoning in one shot. The bar at FAANG is to articulate the **state**, the **transition**, and a **base case** within the first 60 seconds — then either memoize a recursion or build a bottom-up table. This page is the canonical "must-have-solved" DP set: linear DPs (Climbing Stairs, House Robber), 1-D knapsack (Coin Change, Partition Subset), 2-D grid DPs (Edit Distance, LCS), interval DPs (Burst Balloons, Palindrome Partitioning II), and stock series. Internalize the templates here and most novel DP variants reduce to "rename the state."

## Patterns at a glance

| Pattern | Frequency | Signal phrase | Typical state |
|---|---|---|---|
| Linear 1-D DP | Very high | "ways to reach", "max so far" | `dp[i]` |
| 0/1 Knapsack | High | "subset with sum", "exact target" | `dp[i][w]` |
| Unbounded Knapsack | High | "unlimited supply", "fewest coins" | `dp[amount]` |
| 2-D Grid / String DP | Very high | "edit", "LCS", "paths in grid" | `dp[i][j]` |
| Interval DP | Medium | "merge stones", "burst balloons" | `dp[l][r]` |
| Stock / state-machine | High | "buy/sell with constraint" | `dp[i][k][holding]` |
| Bitmask DP | Medium | n ≤ 20, "visit all" | `dp[mask][i]` |
| Decision DP (rob/skip) | High | "non-adjacent", "cooldown" | `dp[i]` (take/skip) |

## Problem list

| # | Problem | Pattern | Difficulty | Companies |
|---|---|---|---|---|
| 1 | Climbing Stairs | Linear DP | Easy | Google, Amazon |
| 2 | House Robber I / II / III | Decision DP | Med | Meta, Amazon |
| 3 | Coin Change I / II | Unbounded knapsack | Med | Google, Meta |
| 4 | Longest Increasing Subsequence | Linear / patience | Med | Google, Microsoft |
| 5 | Longest Common Subsequence | 2-D string DP | Med | Amazon, Google |
| 6 | Edit Distance | 2-D string DP | Hard | Google, Meta |
| 7 | Word Break | Linear DP + set | Med | Meta, Amazon |
| 8 | Decode Ways | Linear DP | Med | Meta, Uber |
| 9 | Unique Paths I / II | Grid DP | Med | Amazon, Bloomberg |
| 10 | Min Path Sum | Grid DP | Med | Amazon |
| 11 | Maximum Subarray (Kadane) | Linear DP | Easy | Amazon, Google |
| 12 | Best Time to Buy/Sell I-IV + Cooldown | State machine | Med-Hard | Google, Meta |
| 13 | Partition Equal Subset Sum | 0/1 knapsack | Med | Amazon |
| 14 | Target Sum | 0/1 knapsack | Med | Meta |
| 15 | Palindrome Partitioning II | Interval + linear | Hard | Google |
| 16 | Regular Expression Matching | 2-D DP | Hard | Meta, Google |
| 17 | Wildcard Matching | 2-D DP | Hard | Meta |
| 18 | Burst Balloons | Interval DP | Hard | Google |

??? tip "How to pick the state in 30 seconds"
    Ask: "What is the smallest piece of input I can answer for, and what info from earlier do I carry?" If the answer involves an index, use `dp[i]`; if two cursors (two strings, or l/r in an interval), `dp[i][j]`; if a budget or capacity, add a dimension; if a binary choice (holding/not), add a flag.

---

## Deep-dive 1 — Coin Change (bottom-up unbounded knapsack)

> Given coins of unlimited supply and a target `amount`, return the **fewest** coins that sum to `amount`, or `-1` if impossible.

The recursion is `f(a) = 1 + min(f(a - c) for c in coins if c <= a)` with `f(0) = 0`. Since subproblems collide heavily (every amount is reused), we tabulate.

### State, transition, base

- **State:** `dp[a]` = min coins to make amount `a`.
- **Transition:** `dp[a] = min(dp[a], dp[a - c] + 1)` for every coin `c <= a`.
- **Base:** `dp[0] = 0`. Initialize the rest to `amount + 1` (a sentinel larger than any feasible answer) so `min` works without special-casing.

### Solution

```python linenums="1"
from __future__ import annotations


def coin_change(coins: list[int], amount: int) -> int:
    """Return the fewest coins summing to ``amount``, or -1 if impossible.

    Args:
        coins: Available coin denominations (positive ints, unlimited supply).
        amount: Non-negative target sum.

    Returns:
        Minimum number of coins, or -1 if no combination reaches ``amount``.
    """
    INF = amount + 1  # (1) sentinel — any real answer is <= amount
    dp = [INF] * (amount + 1)
    dp[0] = 0

    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:  # (2) relax
                dp[a] = dp[a - c] + 1

    return dp[amount] if dp[amount] != INF else -1
```

1. Using `amount + 1` (rather than `math.inf`) keeps the array as plain ints — slightly faster and avoids float comparisons.
2. Order matters: iterate `a` outer, `c` inner. Because each `dp[a - c]` is *already finalized* under min when we read it, this naturally allows reusing the same coin many times — the **unbounded** knapsack ordering.

### Complexity

| Metric | Cost |
|---|---|
| Time | `O(amount × len(coins))` |
| Space | `O(amount)` |

??? question "Why does this NOT work greedily?"
    Greedy ("always take the largest coin ≤ remaining") fails for `coins=[1,3,4], amount=6`: greedy picks `4+1+1 = 3` coins; optimum is `3+3 = 2`. DP enumerates all transitions so it's safe regardless of denomination structure.

??? question "Variant — Coin Change II (count of ways)"
    Swap min-cost for count-of-ways and **flip loop order** to avoid double-counting:
    ```python linenums="1"
    def change(amount: int, coins: list[int]) -> int:
        dp = [0] * (amount + 1)
        dp[0] = 1
        for c in coins:               # coin outer
            for a in range(c, amount + 1):
                dp[a] += dp[a - c]
        return dp[amount]
    ```
    Coin-outer ensures each combination is counted once (subsets, not permutations).

---

## Deep-dive 2 — Longest Increasing Subsequence (two solutions)

> Given an array `nums`, return the length of the longest strictly increasing subsequence.

LIS shows up everywhere — patience-sort variant is the textbook FAANG follow-up after the O(n²) DP. Know **both**.

### Approach A — O(n²) DP

- **State:** `dp[i]` = length of LIS ending **at** index `i`.
- **Transition:** `dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i], default=0)`.
- **Answer:** `max(dp)`.

```python linenums="1"
from __future__ import annotations


def length_of_lis_dp(nums: list[int]) -> int:
    """O(n^2) DP — clear, easy to extend (e.g. reconstruct the LIS).

    Args:
        nums: Input integer sequence.

    Returns:
        Length of the longest strictly increasing subsequence.
    """
    if not nums:
        return 0
    n = len(nums)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
    return max(dp)
```

### Approach B — O(n log n) patience sort with `bisect_left`

Maintain `tails`, where `tails[k]` is the **smallest possible tail** of any increasing subsequence of length `k + 1` seen so far. For each `x`:

1. Find the leftmost index `i` in `tails` with `tails[i] >= x` (via `bisect_left`).
2. If `i == len(tails)`, `x` extends the longest run — append.
3. Otherwise overwrite `tails[i] = x` (we found a smaller tail for length `i + 1` — never hurts future appends).

`tails` is **not** the LIS itself, but its length is the LIS length.

```python linenums="1"
from __future__ import annotations
from bisect import bisect_left


def length_of_lis_patience(nums: list[int]) -> int:
    """O(n log n) patience-sort LIS using ``bisect_left`` for strict increase.

    Args:
        nums: Input integer sequence.

    Returns:
        Length of the longest strictly increasing subsequence.
    """
    tails: list[int] = []
    for x in nums:
        i = bisect_left(tails, x)  # (1) strict: replace duplicates
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
```

1. For **non-strict** (≤), use `bisect_right` instead — that lets equal values extend the run.

### Complexity

| Approach | Time | Space | When to use |
|---|---|---|---|
| O(n²) DP | `O(n²)` | `O(n)` | n ≤ 2500, or you must reconstruct the subsequence with parent pointers |
| Patience O(n log n) | `O(n log n)` | `O(n)` | n is large (10⁵+); only the **length** is required |

??? warning "Common bug — strict vs non-strict"
    Interviewers love to flip "strictly increasing" to "non-decreasing." Strict ⇒ `bisect_left`, non-decreasing ⇒ `bisect_right`. Get this wrong and your function silently returns the wrong number on duplicates.

??? question "Reconstructing the LIS"
    Patience sort alone cannot reconstruct — `tails` is overwritten. Either fall back to the O(n²) DP with parent pointers, or augment patience sort with a parallel `prev` array recording, for each appended/replaced position, the index of the current tail at length `i - 1`.

---

## 🃏 Cheatsheet

| Trick | When |
|---|---|
| Top-down `@cache` recursion | Sketch first, convert to bottom-up only if needed |
| `dp[0] = 1` for "ways" | Empty selection counts as one way |
| Sentinel `INF = amount + 1` | Avoid `math.inf` arithmetic |
| Coin-outer vs amount-outer | Combinations vs permutations in Coin Change II |
| `bisect_left` strict / `bisect_right` non-strict | LIS variants |
| Rolling 1-D array | Drop a dimension when only previous row matters |
| 0/1 knapsack — iterate weight **descending** | Prevents reusing an item |
| Unbounded — iterate weight **ascending** | Allows reuse |
| Stock state machine | `hold[i] = max(hold[i-1], cash[i-1] - p)` / `cash[i] = max(cash[i-1], hold[i-1] + p)` |
| Interval DP loop order | Length outer, left endpoint inner |

??? tip "30-second DP framework"
    1. Define `dp[...]` in one English sentence.
    2. Write the recurrence — ignore base cases.
    3. Now write base cases.
    4. Decide direction (top-down memo vs bottom-up table).
    5. State complexity. If states × transitions exceeds budget, look for a smarter state.

??? note "Edge cases checklist"
    - Empty input — does `dp` of size 0 break `max()`?
    - Single element — many DPs default to `1`, not `0`.
    - All-equal elements — strict-vs-non-strict trips here.
    - `amount = 0` in Coin Change — return `0`, not `-1`.
    - Negative numbers — Kadane allows them; subset-sum DPs typically don't.
