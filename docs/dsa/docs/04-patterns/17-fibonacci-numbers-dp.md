# Fibonacci Numbers DP

> The simplest 1D DP family. State at position `i` depends on a tiny constant-size window of the previous states — usually just `i-1` and `i-2`. Climbing Stairs, House Robber, Decode Ways, Min Cost Climbing Stairs, and most "linear array, scalar transition" DPs all live here. The signature optimisation: **drop the array entirely and keep just two rolling variables** — O(1) space without losing the recurrence.

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 28)</span>

---

## 📖 What is Fibonacci-style DP?

A linear DP where `dp[i]` depends on a **bounded constant number of earlier values** — most often `dp[i-1]` and `dp[i-2]`, occasionally back to `dp[i-3]` or `dp[i-k]` for small fixed `k`.

The textbook example is the Fibonacci sequence itself: `f(n) = f(n-1) + f(n-2)`. The DP shape is identical to a dozen interview problems — the only thing that changes is *what* the recurrence sums or maximises.

**State definition** (always 1D over a single index `i`):

- Climbing Stairs: `dp[i] = ways to reach step i`
- House Robber: `dp[i] = max money robbing houses 0..i with no two adjacent`
- Decode Ways: `dp[i] = number of decodings of s[:i]`
- Min Cost Climbing Stairs: `dp[i] = min cost to reach step i`

**The shape:** linear scan, constant work per cell, constant lookback. **The optimisation:** since you only read `dp[i-1]` and `dp[i-2]`, store just two scalars — overwrite as you go. O(1) space.

The mental model: imagine walking along an array left-to-right with **two cards in your hand** representing the last two answers. At each step, peek at both cards, compute the new answer, slide one card off, slide the new answer into the other slot.

!!! tip "The signal — when to reach for Fibonacci-style DP"
    Reach for it when:

    - The state is a **single 1D index** (a position, a step, a day, a string prefix).
    - The transition reads only **a constant number of earlier states** — typically `i-1` and `i-2`.
    - The problem is "ways to do X" / "min cost to reach X" / "max value ending at X."

    Don't reach for it when:

    - The transition reads an unbounded prefix (LIS / LCS / many-to-one) — that's a different DP.
    - The state is multi-dimensional (knapsack, grid DP) — different patterns.
    - The recurrence has a *condition* (e.g., "only if A[i] is even") — still works, but think carefully about the base cases.

---

## 🧩 The three flavors

### Flavor 1: Two-variable rolling form (the canonical shape)

The textbook 1D Fibonacci DP. `prev2` and `prev1` track the two most recent answers; one assignment per step.

```python
def fib(n: int) -> int:
    if n < 2:
        return n
    prev2, prev1 = 0, 1                                          # (1) f(0), f(1)
    for _ in range(2, n + 1):
        prev2, prev1 = prev1, prev2 + prev1                      # (2) shift forward
    return prev1
```

1. Initialise `prev2 = f(i-2)` and `prev1 = f(i-1)` for the first iteration's `i = 2`.
2. Python's tuple-assign is the cleanest way to do the swap — both reads happen before either write. In other languages, use a temp variable.

**Why O(1) space matters here.** For a problem like Climbing Stairs with `n` up to 45, the difference is negligible. But the *habit* generalises to memory-constrained interview problems and to embedded contexts where every byte counts.

**Examples:** Fibonacci Number (LC 509), Climbing Stairs (LC 70), House Robber (LC 198), Min Cost Climbing Stairs (LC 746).

### Flavor 2: Array form (for clarity or reconstruction)

When you need to inspect the full DP for debugging or reconstruction, keep the array:

```python
def climb_stairs(n: int) -> int:
    """LC 70 — number of distinct ways to climb n steps taking 1 or 2 at a time."""
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[0], dp[1] = 1, 1                                          # (1) 1 way to be at step 0 (do nothing)
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]
```

1. **Climbing Stairs uses `dp[0] = 1`**, not 0 — there's exactly one way to "be at the start" (do nothing). Using `dp[0] = 0` would shift every subsequent count down by one. This is a classic interview gotcha.

**Examples:** Same problems; use the array form when you need to explain, debug, or reconstruct.

### Flavor 3: Multi-state per index (House Robber, Decode Ways)

Sometimes a single scalar per index isn't enough — you need 2–3 states (e.g., "did I rob house i or not"). Same structure, slightly wider state.

```python
def rob(nums: list[int]) -> int:
    """LC 198 — max money without robbing two adjacent houses."""
    rob_prev, skip_prev = 0, 0                                   # (1) two states
    for x in nums:
        rob_curr = skip_prev + x                                 # (2) rob this house: must skip last
        skip_curr = max(rob_prev, skip_prev)                     # (3) skip this house: free choice last
        rob_prev, skip_prev = rob_curr, skip_curr
    return max(rob_prev, skip_prev)
```

1. `rob_prev` = max with last house robbed; `skip_prev` = max with last house skipped.
2. To rob *this* house, the previous one must have been skipped.
3. To skip this house, you keep whichever was better previously.

The **same idea condensed** uses only one variable: `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`, where `dp[i-1]` represents "skip house i" and `dp[i-2] + nums[i]` represents "rob house i." Both forms are correct; the explicit two-state version is easier to extend (e.g., House Robber II with circular constraint).

**Examples:** House Robber (LC 198), House Robber II (LC 213), Delete and Earn (LC 740 — reduces to House Robber after value-frequency reduction), Stock with Cooldown (LC 309 — three states).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Count ways (1+2 step) | Number of paths | Climbing Stairs (LC 70) | `dp[i] = dp[i-1] + dp[i-2]` |
| 2 | Min cost to reach n | Cumulative min | Min Cost Climbing Stairs (LC 746) | `dp[i] = min(dp[i-1], dp[i-2]) + cost[i]` |
| 3 | Max with adjacency rule | "No two adjacent" | House Robber (LC 198) | `dp[i] = max(dp[i-1], dp[i-2] + a[i])` |
| 4 | Decode-ways count | Conditional Fibonacci | Decode Ways (LC 91) | `dp[i] += dp[i-1] if 1 ≤ d ≤ 9; dp[i] += dp[i-2] if 10 ≤ dd ≤ 26` |
| 5 | Tiling a 2×n board | Geometric variant | Domino Tilings (classic) | Same Fibonacci shape with 2 base cases |
| 6 | Circular DP | Wrap-around constraint | House Robber II (LC 213) | Run twice: `nums[:-1]` and `nums[1:]`; max |
| 7 | Generalised k-step | Step sizes 1..k | Climbing Stairs k-step | `dp[i] = sum(dp[i-1..i-k])` (sliding window for O(n)) |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Fibonacci Number | 509 | <span class="diff-easy">Easy</span> | Pure Fibonacci | 📝 |
| 2 | Climbing Stairs | 70 | <span class="diff-easy">Easy</span> | Count ways | 📝 |
| 3 | Min Cost Climbing Stairs | 746 | <span class="diff-easy">Easy</span> | Min cost | 📝 |
| 4 | House Robber | 198 | <span class="diff-medium">Medium</span> | Adjacency rule | 📝 |
| 5 | House Robber II | 213 | <span class="diff-medium">Medium</span> | Circular | 📝 |
| 6 | House Robber III | 337 | <span class="diff-medium">Medium</span> | Tree DP (cousin) | 📝 |
| 7 | Decode Ways | 91 | <span class="diff-medium">Medium</span> | Conditional Fibonacci | 📝 |
| 8 | Decode Ways II | 639 | <span class="diff-hard">Hard</span> | Wildcards in conditional | 📝 |
| 9 | Delete and Earn | 740 | <span class="diff-medium">Medium</span> | Reduce to House Robber | 📝 |
| 10 | Best Time to Buy and Sell Stock | 121 | <span class="diff-easy">Easy</span> | Linear scan (cousin) | 📝 |
| 11 | Best Time to Buy and Sell Stock with Cooldown | 309 | <span class="diff-medium">Medium</span> | 3-state DP | 📝 |
| 12 | Maximum Subarray (Kadane) | 53 | <span class="diff-medium">Medium</span> | 1D DP (cousin) | 📝 |
| 13 | Number of Tilings of 2 × n | 790 | <span class="diff-medium">Medium</span> | Tiling | 📝 |
| 14 | Tribonacci | 1137 | <span class="diff-easy">Easy</span> | Three-value lookback | 📝 |
| 15 | Paint House | 256 | <span class="diff-medium">Medium</span> | Multi-state Fibonacci | 📝 |
| 16 | Paint Fence | 276 | <span class="diff-medium">Medium</span> | Two-state count | 📝 |
| 17 | Domino and Tromino Tiling | 790 | <span class="diff-medium">Medium</span> | Tiling variant | 📝 |
| 18 | Count Number of Texts | 2266 | <span class="diff-medium">Medium</span> | k-step Fibonacci | 📝 |
| 19 | Coin Change (cousin — different pattern) | 322 | <span class="diff-medium">Medium</span> | Unbounded knapsack | ✅ |
| 20 | Climbing Stairs (k step variant) | 70 generalised | <span class="diff-easy">Easy</span> | k-step Fibonacci | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Climbing Stairs (LC 70)

> You're climbing a staircase. It takes `n` steps to reach the top. Each time you can climb 1 or 2 steps. How many distinct ways can you climb to the top?

The cleanest exposition of why this is Fibonacci — and the most common interview question that immediately reveals whether the candidate sees the pattern.

#### Code

```python
def climb_stairs(n: int) -> int:
    if n <= 2:
        return n
    prev2, prev1 = 1, 2                                          # (1) ways to reach step 1, step 2
    for _ in range(3, n + 1):
        prev2, prev1 = prev1, prev1 + prev2
    return prev1
```

1. Base cases: 1 way to reach step 1 (just take step 1), 2 ways to reach step 2 (1+1, or 2). Notice these are *the right base cases*; using `(0, 1)` is the indexed-from-0 alternative when you also count "be at start."

#### Why the recurrence is Fibonacci

To reach step `i`, the last move was either a **+1 step from `i-1`** or a **+2 step from `i-2`**. The two source positions are disjoint (you can't reach step `i` both ways simultaneously *with the same prior path*, because the prior paths are different). So:

`ways(i) = ways(i-1) + ways(i-2)`

That's literally Fibonacci (with shifted base cases).

#### Dry run for `n = 5`

| Step | prev2 (was) | prev1 (was) | new = prev1 + prev2 | After |
|------|-------------|-------------|----------------------|-------|
| start | — | — | — | prev2=1, prev1=2 |
| i=3 | 1 | 2 | 3 | prev2=2, prev1=3 |
| i=4 | 2 | 3 | 5 | prev2=3, prev1=5 |
| i=5 | 3 | 5 | 8 | prev2=5, prev1=8 |

Output: 8.

Sanity check by enumeration: `1+1+1+1+1`, `1+1+1+2`, `1+1+2+1`, `1+2+1+1`, `2+1+1+1`, `1+2+2`, `2+1+2`, `2+2+1`. Eight ways. ✓

#### Variant — k step sizes

Generalising "1 or 2" to "1, 2, …, k":

```python
def climb_stairs_k(n: int, k: int) -> int:
    dp = [0] * (n + 1)
    dp[0] = 1
    window_sum = 1                                               # (1) running window
    for i in range(1, n + 1):
        dp[i] = window_sum
        window_sum += dp[i]
        if i >= k:
            window_sum -= dp[i - k]                              # (2) drop oldest
    return dp[n]
```

1. The recurrence is `dp[i] = sum(dp[i-1] + dp[i-2] + … + dp[i-k])`. Naively O(n·k). With a rolling window sum, O(n).
2. Sliding-window optimisation, exactly like Pattern 1.

#### Complexity

- **Time:** O(n).
- **Space:** O(1) for the rolling form, O(n) for the array form.

---

### Deep-dive 2 — House Robber (LC 198)

> A row of houses, each with some money. You can't rob two adjacent houses (the alarms connect them). What's the maximum you can rob?

The recurrence is one of the cleanest "max with constraint" examples in DP.

#### Code (rolling form)

```python
def rob(nums: list[int]) -> int:
    prev2, prev1 = 0, 0                                          # (1) money before any houses
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)              # (2) skip vs rob
    return prev1
```

1. Two virtual base cases: zero money before house 0 and before house -1.
2. At each house: either skip (`prev1`) or rob (must have skipped previous, so `prev2 + x`). Take the max.

#### Dry run on `nums = [2, 7, 9, 3, 1]`

| House (x) | prev2 (was) | prev1 (was) | rob = prev2 + x | skip = prev1 | new prev1 = max(skip, rob) |
|-----------|-------------|-------------|------------------|---------------|----------------------------|
| start | — | — | — | — | prev2=0, prev1=0 |
| 2 | 0 | 0 | 2 | 0 | 2; (prev2=0, prev1=2) |
| 7 | 0 | 2 | 7 | 2 | 7; (prev2=2, prev1=7) |
| 9 | 2 | 7 | 11 | 7 | 11; (prev2=7, prev1=11) |
| 3 | 7 | 11 | 10 | 11 | 11; (prev2=11, prev1=11) |
| 1 | 11 | 11 | 12 | 11 | 12; (prev2=11, prev1=12) |

Output: 12 (rob houses 0, 2, 4: 2 + 9 + 1 = 12). ✓

#### Variant — House Robber II (LC 213, circular)

If houses are in a *circle*, house 0 and house n-1 are adjacent. The trick: split into **two linear sub-problems** — one excludes house 0, the other excludes house n-1 — and take the max. Either subproblem is a plain House Robber.

```python
def rob_circle(nums: list[int]) -> int:
    if len(nums) == 1:
        return nums[0]
    return max(rob(nums[:-1]), rob(nums[1:]))
```

The crucial insight: at most one of the two endpoints can be robbed in any optimal solution. The two cases (rob 0 / don't rob 0) exhaust the possibilities.

#### The two-variable form is enough for this problem

Why no third variable? Because the constraint only reaches 1 back. If the constraint were "no three adjacent," you'd need three variables. The number of variables = the lookback depth.

#### Complexity

- **Time:** O(n).
- **Space:** O(1) for the rolling form.

---

### Deep-dive 3 — Decode Ways (LC 91)

> A string `s` of digits encodes letters via `'A'=1, 'B'=2, …, 'Z'=26`. Return the number of ways to decode `s`. Leading zeros and standalone zeros aren't valid letters.

A **conditional Fibonacci** — the recurrence is `dp[i] = dp[i-1] + dp[i-2]`, but each term contributes only if its letter is valid. Edge cases around `'0'` are the entire interview signal.

#### Code

```python
def num_decodings(s: str) -> int:
    if not s or s[0] == "0":
        return 0
    n = len(s)
    prev2, prev1 = 1, 1                                          # (1) base: 1 way for empty / 1-char prefix
    for i in range(2, n + 1):
        curr = 0
        one = int(s[i - 1])
        two = int(s[i - 2:i])
        if 1 <= one <= 9:                                        # (2) single-digit decode
            curr += prev1
        if 10 <= two <= 26:                                      # (3) two-digit decode
            curr += prev2
        prev2, prev1 = prev1, curr
    return prev1
```

1. `dp[0] = 1` (empty string has one decoding — the empty one). `dp[1] = 1` if `s[0] != '0'` (one decoding) — handled by the early return.
2. The single-digit term contributes when the *current* digit is `1..9` (not `0`).
3. The two-digit term contributes when the *previous* two digits form `10..26`.

#### Dry run on `s = "226"`

`n = 3`. Initial `prev2 = 1, prev1 = 1`.

**i = 2** (digits `s[0:2] = "22"`):
- one = `s[1]` = 2 ⇒ valid ⇒ curr += prev1 = 1.
- two = `s[0:2]` = 22 ⇒ valid (10..26) ⇒ curr += prev2 = 1+1 = 2.
- `(prev2, prev1) = (1, 2)`.

**i = 3** (digits `s[1:3] = "26"`):
- one = `s[2]` = 6 ⇒ valid ⇒ curr += 2.
- two = `s[1:3]` = 26 ⇒ valid ⇒ curr += 1, total 3.
- `(prev2, prev1) = (2, 3)`.

Output: 3. The three decodings: `"BBF"` (2-2-6), `"BZ"` (2-26), `"VF"` (22-6). ✓

#### The `'0'` edge cases — the bug magnet

Three `'0'`-related traps:

1. **Leading zero (`"012"`)** — invalid, return 0. The early check handles this.
2. **Standalone zero (`"30"`)** — `s[1] = '0'` means the single-digit term doesn't contribute; the two-digit term doesn't contribute either (`30 > 26`). `curr` stays 0; total decodings is 0.
3. **Zero following 1 or 2 (`"10"`, `"20"`)** — single-digit term doesn't contribute (`'0'` invalid alone), but two-digit term contributes (`10` and `20` are valid). Correct count: 1 decoding.

The recurrence handles all three correctly because each branch has its own validity check.

#### Why this is still Fibonacci-shape

The structural recurrence `dp[i] = dp[i-1] + dp[i-2]` is intact — both terms are present, each gated by a digit-validity check. It's "Fibonacci with conditional contributions." The O(1)-space rolling form drops out of the structure exactly as in Climbing Stairs.

#### Complexity

- **Time:** O(n).
- **Space:** O(1).

---

## 🐛 Common bugs

1. **Wrong base cases for Climbing Stairs.** `dp[0] = 1`, `dp[1] = 1` (or `dp[1] = 1, dp[2] = 2` if 1-indexed) — every off-by-one shifts the whole sequence.
2. **Tuple-assign forgotten in Python.** Writing `prev2 = prev1; prev1 = prev1 + prev2` leaves `prev2` already changed when computing the second line. Use `prev2, prev1 = prev1, prev2 + prev1` so both reads happen before either write.
3. **House Robber: confusing "rob this" and "skip this" indexing.** The recurrence `dp[i] = max(dp[i-1], dp[i-2] + nums[i])` reads `dp[i-2]` for "rob" — not `dp[i-1]`. Inverting these is a common silent error.
4. **House Robber II: forgetting to handle `n=1`.** The split-and-recur approach needs an explicit guard for `len(nums) == 1` because slicing into two empty arrays would produce a degenerate result.
5. **Decode Ways: using `s[i-2] in '12'` instead of full integer comparison.** This works for English-letter range up to 26 but breaks for any extension; checking `10 <= int(s[i-2:i]) <= 26` is unambiguous.
6. **Climbing Stairs k-step: O(n·k) when O(n) is reachable.** Use a rolling window sum to get O(n).
7. **Forgetting that the rolling form loses reconstruction.** If the problem asks "show me the actual path" (steps taken, houses robbed), keep the array.
8. **Negative or zero `n` in Fibonacci.** `n < 0` is undefined; the spec usually says `n ≥ 0`. Don't assume — check the constraints and handle edge cases explicitly.

---

## 🗣️ Interviewer phrasings to recognize

- "Number of **ways** to climb / hop / reach step n with step sizes {1, 2}." → Climbing Stairs.
- "Maximum sum / value with **no two adjacent**." → House Robber.
- "Decode this **digit string**." → Decode Ways.
- "Buy and sell with a **cooldown** day." → Stock-with-cooldown three-state DP.
- "Tile a 2×n board with dominos." → Tiling Fibonacci.
- "Tribonacci / k-th sequence." → Same recurrence with wider lookback.

---

## 🧭 Connections to other patterns

- **Unbounded Knapsack DP** ([16-unbounded-knapsack-dp.md](16-unbounded-knapsack-dp.md)) — Climbing Stairs is Combination Sum IV with `nums = [1, 2]`. The "outer-target / inner-items" loop order maps to Fibonacci.
- **0/1 Knapsack DP** ([15-01-knapsack-dp.md](15-01-knapsack-dp.md)) — both are 1D rolling DPs; knapsack adds a capacity axis, Fibonacci has just the index.
- **Sliding Window** ([01-sliding-window.md](01-sliding-window.md)) — k-step Fibonacci uses a rolling sum to keep O(n).
- **Tree DFS** ([08-tree-dfs.md](08-tree-dfs.md)) — House Robber III is the tree-shaped variant; the same "rob-this-or-not" two-state idea, computed bottom-up.
- **Greedy** — Greedy fails for House Robber (counterexample: `[2, 1, 1, 2]` — greedy picks one 2 then must skip both 1s and the other 2; DP picks both 2s for 4). DP is required.

---

## ✅ Self-check — 8 questions

??? question "1. Why does Fibonacci-style DP collapse to O(1) space?"
    The recurrence reads only the last 1–2 (or, more generally, a constant number of) earlier states. You can keep just those scalars and overwrite as you scan, dropping the array entirely. Time stays O(n); space drops from O(n) to O(1).

??? question "2. What's the right tuple-assign for the Fibonacci step in Python?"
    `prev2, prev1 = prev1, prev2 + prev1`. Both right-hand-side expressions evaluate before any assignment, so the old `prev2` is still readable when computing `prev2 + prev1`. Using two sequential assignments (`prev2 = prev1; prev1 = prev2 + prev1`) gives the wrong answer because the second line reads the *new* `prev2`.

??? question "3. How does House Robber II (circular) reduce to plain House Robber?"
    In a circle, the first and last houses are adjacent. Any optimal solution either skips the first house, in which case the rest is a plain House Robber on `nums[1:]`, or skips the last, leaving a plain problem on `nums[:-1]`. Take the max of the two reductions.

??? question "4. Why does Decode Ways need separate validity checks for 1-digit and 2-digit terms?"
    Each branch has its own constraints: 1-digit valid iff the digit is `1..9`; 2-digit valid iff the pair is `10..26`. They're independent — `"30"` is decodable as `30 = ?` (no, `30 > 26`) and `'0'` (invalid alone), so the answer is 0. Mixing checks misses these subtleties.

??? question "5. What's the lookback depth for Tribonacci, and how does that change the rolling form?"
    Tribonacci's recurrence is `T(n) = T(n-1) + T(n-2) + T(n-3)`. The rolling form keeps **three** scalars — `prev3, prev2, prev1` — and shifts them forward each step. The pattern generalises: `k`-bonacci needs `k` rolling variables.

??? question "6. When is the array form preferable to the rolling form?"
    Three cases: (a) you need to **reconstruct** the actual decisions (path, set, etc.), which requires history; (b) you're **debugging** and want to inspect the table; (c) the recurrence has a non-trivial *non-constant* lookback (e.g., reads `dp[i - k]` where `k` varies) — the rolling form might still apply but the array is clearer.

??? question "7. Why doesn't greedy work for House Robber?"
    Greedy "rob largest, skip neighbours, repeat" fails on inputs where two smaller values together beat a single large one. Counter: `[2, 1, 1, 2]` — greedy robs the first 2, must skip the 1, must skip the next 1, can rob the last 2: total 4. But that *is* what DP finds. Counter that breaks greedy: `[2, 7, 9, 3, 1]` — DP finds 12 (2+9+1) but greedy that picks 9 first then can't see 2+1 cleanly without backtracking.

??? question "8. How would you compute Fibonacci in O(log n)?"
    Matrix exponentiation: `[[F(n+1)], [F(n)]] = [[1,1],[1,0]]^n · [[1],[0]]`. Compute the matrix power via fast exponentiation in O(log n) matrix multiplications, each O(1) on a fixed 2×2. Useful only for huge n where the linear DP becomes a bottleneck — interview-noteworthy but rarely interview-required.

---

> **Next pattern up:** Palindromic Subsequence DP — interval DP over a string, with the diagonal-sweep recurrence that's the foundation of LCS, Edit Distance, and Matrix Chain Multiplication (page coming next).
