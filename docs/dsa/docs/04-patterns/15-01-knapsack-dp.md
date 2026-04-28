# 0/1 Knapsack DP

> The mother of all subset-selection DPs. Given a list of items, each with a *weight* and *value*, pick a subset that maximises value under a capacity budget. The "0/1" half of the name says **each item is either taken or not — no halves, no duplicates.** Once you internalise the 2D `dp[i][w]` table and the rolling-array trick that compresses it to 1D (with the **right-to-left** iteration order), Subset Sum, Partition Equal Subset Sum, Target Sum, Last Stone Weight II, and a dozen others all collapse to template substitutions.

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 26)</span>

---

## 📖 What is 0/1 knapsack DP?

You have `n` items, each with a weight `w[i]` and value `v[i]`. You also have a capacity `W`. Pick a subset of items whose total weight is ≤ `W` and whose total value is maximised. The "0/1" constraint: each item used **at most once**.

The DP definition that solves it: `dp[i][w]` = "maximum value using a subset of items `0..i-1` whose total weight is exactly `w` (or ≤ `w` for the standard form)." The recurrence has two branches per item: skip it (`dp[i-1][w]`) or take it (`dp[i-1][w - weight[i-1]] + value[i-1]`, only if `w ≥ weight[i-1]`).

The mental model: picture a `(n+1) × (W+1)` grid. The answer at `dp[i][w]` looks **only** at the row above (`dp[i-1][·]`) at column `w` and column `w - weight[i-1]`. Because of that local dependency, you can roll the table down to a single 1D array of size `W+1` — but **iterating `w` right-to-left** preserves the "previous row" semantics. Iterating left-to-right would silently turn it into the *unbounded* knapsack.

This is the fundamental "pick a subset that satisfies some additive constraint" template. Most variants are 5-line edits — flip max to min, replace value with 1 (counting), or replace `<= W` with `== W` (exact).

!!! tip "The signal — when to reach for 0/1 knapsack"
    Reach for it when:

    - "Pick a **subset** of these items maximising / minimising / counting some additive quantity."
    - "Can a subset sum to **exactly** target?" (Subset Sum, Partition Equal Subset Sum)
    - "Each item can be used **at most once**." (the 0/1 distinguishes from unbounded)
    - The constraint is a sum that fits in a manageable integer bound (typically ≤ 10⁴ or ≤ 10⁵).

    Don't reach for it when:

    - Items can be taken any number of times → that's *unbounded* knapsack ([16-unbounded-knapsack-dp.md](16-unbounded-knapsack-dp.md)).
    - The constraint isn't an additive sum (max, count of distinct, etc.) — different DP.
    - The budget is larger than ~10⁷ — DP table too big; consider meet-in-the-middle or a different approach.

---

## 🧩 The three flavors

### Flavor 1: 2D `dp[i][w]` table — the readable form

The textbook definition. `dp[i][w]` = max value using items `0..i-1` with weight budget `w`.

```python
def knapsack_2d(weights: list[int], values: list[int], W: int) -> int:
    n = len(weights)
    dp = [[0] * (W + 1) for _ in range(n + 1)]                    # (1) +1 row, +1 col

    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]                               # (2) skip item i
            if w >= wi:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - wi] + vi)  # (3) take item i

    return dp[n][W]
```

1. The `+1`s give a clean base row of all zeros: zero items ⇒ zero value at any capacity.
2. Skipping is always legal and gives `dp[i-1][w]`.
3. Taking is conditional on capacity. If allowed, the value is "previous row at the residual capacity, plus this item's value."

The 2D form is **always correct** and the easiest to debug. Use it in interviews if you have any doubt.

**Examples:** Classic 0/1 Knapsack (no LC#, but appears constantly), Partition Equal Subset Sum (LC 416), Last Stone Weight II (LC 1049).

### Flavor 2: 1D rolling array — the space-optimised form

Because `dp[i][w]` only reads `dp[i-1][·]`, you can keep just one row. The catch: when updating in place, **iterate `w` right-to-left** so that the value at `w - wi` is still from the previous row when you read it.

```python
def knapsack_1d(weights: list[int], values: list[int], W: int) -> int:
    dp = [0] * (W + 1)
    for wi, vi in zip(weights, values):
        for w in range(W, wi - 1, -1):                            # (1) right-to-left
            dp[w] = max(dp[w], dp[w - wi] + vi)                   # (2) reads "previous row"
    return dp[W]
```

1. The `range(W, wi - 1, -1)` walks from `W` down to `wi`. Below `wi` the item can't fit.
2. Going right-to-left, `dp[w - wi]` hasn't been updated *this iteration* yet — it still holds the previous-row value. Going left-to-right would let an item be picked multiple times, silently turning this into unbounded knapsack.

**The right-to-left rule is the single most-tested detail of this pattern.** Internalise it.

**Examples:** Same problem set as Flavor 1; 1D form is the production answer once you've validated the recurrence in 2D.

### Flavor 3: Counting / boolean variants

Same template, but the cell value isn't "max value" — it's "is this sum reachable" (boolean) or "how many subsets sum to this" (count). Two single-line edits.

```python
def can_partition(nums: list[int]) -> bool:
    """LC 416 — split nums into two equal-sum halves."""
    s = sum(nums)
    if s % 2:
        return False
    target = s // 2
    dp = [False] * (target + 1)
    dp[0] = True                                                  # (1) zero is always reachable
    for x in nums:
        for w in range(target, x - 1, -1):
            dp[w] = dp[w] or dp[w - x]                            # (2) reachability OR
    return dp[target]


def count_subsets_with_sum(nums: list[int], target: int) -> int:
    dp = [0] * (target + 1)
    dp[0] = 1                                                     # (1) one way to make 0 — empty subset
    for x in nums:
        for w in range(target, x - 1, -1):
            dp[w] += dp[w - x]                                    # (3) count add
    return dp[target]
```

1. Base case `dp[0] = True / 1`. The empty subset always sums to zero.
2. Boolean variant: take the OR of "didn't use this item" with "did use it."
3. Counting variant: add the two counts. Same recurrence; different aggregation.

**Examples:** Subset Sum (canonical), Partition Equal Subset Sum (LC 416), Target Sum (LC 494 — count subsets with a given signed sum, reduced to count-with-sum), Ones and Zeroes (LC 474 — 2D capacity: zeros and ones).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Maximise value | Classic knapsack | 0/1 Knapsack | `dp[w] = max(dp[w], dp[w-wi]+vi)` |
| 2 | Minimise value | Min coins / weight | Last Stone Weight II (LC 1049) | Same recurrence; `min` instead of `max` |
| 3 | Reachability | Can sum reach target? | Partition Equal Subset (LC 416) | `dp[w] or dp[w - x]`, base `dp[0]=True` |
| 4 | Count subsets | How many subsets sum to target? | Target Sum (LC 494) | `dp[w] += dp[w - x]`, base `dp[0]=1` |
| 5 | Two-dim capacity | Capacity is a tuple | Ones and Zeroes (LC 474) | `dp[i][j]` rolling 2D, both axes right-to-left |
| 6 | Equal partition | Split into two equal halves | Partition Equal Subset (LC 416) | Reduce to subset-sum to `total / 2` |
| 7 | Reconstruct items | Recover the chosen subset | (Variant) | Keep the 2D table; backtrack from `dp[n][W]` |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Partition Equal Subset Sum | 416 | <span class="diff-medium">Medium</span> | Reachability | 📝 |
| 2 | Target Sum | 494 | <span class="diff-medium">Medium</span> | Count subsets | 📝 |
| 3 | Last Stone Weight II | 1049 | <span class="diff-medium">Medium</span> | Min difference | 📝 |
| 4 | Ones and Zeroes | 474 | <span class="diff-medium">Medium</span> | 2D capacity | 📝 |
| 5 | Profitable Schemes | 879 | <span class="diff-hard">Hard</span> | 2D capacity + count | 📝 |
| 6 | Tallest Billboard | 956 | <span class="diff-hard">Hard</span> | Difference DP | 📝 |
| 7 | Closest Subsequence Sum | 1755 | <span class="diff-hard">Hard</span> | Meet-in-the-middle (cousin) | 📝 |
| 8 | Best Sightseeing Pair | 1014 | <span class="diff-medium">Medium</span> | Pair max DP (cousin) | 📝 |
| 9 | Maximum Earnings From Taxi | 2008 | <span class="diff-medium">Medium</span> | Job scheduling DP | 📝 |
| 10 | Maximum Profit in Job Scheduling | 1235 | <span class="diff-hard">Hard</span> | Bsearch + DP | 📝 |
| 11 | Best Time to Buy and Sell Stock IV | 188 | <span class="diff-hard">Hard</span> | k-transactions DP | 📝 |
| 12 | Number of Subsets With Equal Sum | (classic) | <span class="diff-medium">Medium</span> | Count subsets | 📝 |
| 13 | Subset Sum (decision) | (classic) | <span class="diff-medium">Medium</span> | Reachability | 📝 |
| 14 | Equal Sum Partition | (classic) | <span class="diff-medium">Medium</span> | Equal partition | 📝 |
| 15 | Min Subset Sum Difference | (classic) | <span class="diff-medium">Medium</span> | Min difference | 📝 |
| 16 | Count of Subsets with given diff | (classic) | <span class="diff-medium">Medium</span> | Diff → sum reduction | 📝 |
| 17 | Combination Sum (subset variant) | 39-derived | <span class="diff-medium">Medium</span> | Backtracking variant | 📝 |
| 18 | Largest Sum Subset with sum ≤ K | (classic) | <span class="diff-medium">Medium</span> | Max with bound | 📝 |
| 19 | Partition Array Into Two Arrays To Minimize Sum Difference | 2035 | <span class="diff-hard">Hard</span> | Meet-in-the-middle | 📝 |
| 20 | Last Stone Weight (variant — heap) | 1046 | <span class="diff-easy">Easy</span> | Heap (cousin) | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Classic 0/1 Knapsack

> `weights = [1, 3, 4, 5]`, `values = [1, 4, 5, 7]`, `W = 7`. Max value?

The original problem; the table makes the recurrence concrete.

#### Code (2D form)

```python
def knapsack(weights: list[int], values: list[int], W: int) -> int:
    n = len(weights)
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]
            if w >= wi:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - wi] + vi)
    return dp[n][W]
```

#### The full table for the example

Items in order: `(1,1), (3,4), (4,5), (5,7)`. Columns are weights `0..7`.

| `i` \ `w` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|-----------|---|---|---|---|---|---|---|---|
| 0 (no items) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 (`w=1, v=1`) | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 (`w=3, v=4`) | 0 | 1 | 1 | 4 | 5 | 5 | 5 | 5 |
| 3 (`w=4, v=5`) | 0 | 1 | 1 | 4 | 5 | 6 | 6 | 9 |
| 4 (`w=5, v=7`) | 0 | 1 | 1 | 4 | 5 | 7 | 8 | 9 |

**Example cell — `dp[3][7]`:**
- Skip item 3: `dp[2][7] = 5`.
- Take item 3 (weight 4, value 5): `dp[2][7-4] + 5 = dp[2][3] + 5 = 4 + 5 = 9`.
- Max → `9`.

**Final answer:** `dp[4][7] = 9` (take items 1 and 3: weights 1+4=5 ≤ 7, values 1+5=6 — wait, that's 6, not 9).

Re-tracing for 9: items 2 and 3 give weights 3+4=7, values 4+5=9. ✓

#### 1D rolling form for the same example

After processing each item:

| Item | dp = | Notes |
|------|------|-------|
| start | `[0, 0, 0, 0, 0, 0, 0, 0]` | base |
| 1 (`w=1, v=1`) | `[0, 1, 1, 1, 1, 1, 1, 1]` | every position ≥ 1 gains 1 |
| 2 (`w=3, v=4`) | `[0, 1, 1, 4, 5, 5, 5, 5]` | take item 2 wherever it fits |
| 3 (`w=4, v=5`) | `[0, 1, 1, 4, 5, 6, 6, 9]` | best is items {2,3} at w=7 |
| 4 (`w=5, v=7`) | `[0, 1, 1, 4, 5, 7, 8, 9]` | item 4 alone wins at w=5,6 |

Same final answer at `dp[7] = 9`.

#### Why right-to-left in the 1D form?

Walk `dp[w]` from high `w` to low. When computing `dp[w] = max(dp[w], dp[w - wi] + vi)`, you read `dp[w - wi]`. Going right-to-left, indices smaller than `w` haven't been updated *this iteration* yet — `dp[w - wi]` still holds the *previous-row* value. That's exactly what the 2D recurrence reads.

Going left-to-right, `dp[w - wi]` would already be the *current* row's updated value — meaning item `i` has been "used" in `dp[w - wi]` and is being used again at `dp[w]`. That's the unbounded variant — correct for [Pattern 16](16-unbounded-knapsack-dp.md), wrong here.

#### Complexity

- **Time:** O(n · W).
- **Space:** O(n · W) for 2D, **O(W)** for 1D rolling.

---

### Deep-dive 2 — Partition Equal Subset Sum (LC 416)

> Given an array of positive integers, can it be partitioned into two subsets with equal sums?

The reduction: if the total is `S`, you need a subset summing to **exactly** `S/2`. If `S` is odd, impossible. Otherwise, run subset-sum reachability.

#### Code

```python
def can_partition(nums: list[int]) -> bool:
    s = sum(nums)
    if s % 2:
        return False
    target = s // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for x in nums:
        for w in range(target, x - 1, -1):
            dp[w] = dp[w] or dp[w - x]
            if dp[target]:                                        # (1) early exit
                return True
    return dp[target]
```

1. Optional optimisation: once `dp[target]` flips to True, you're done.

#### Dry run on `nums = [1, 5, 11, 5]`

`sum = 22`, `target = 11`. Initial `dp = [T, F, F, F, F, F, F, F, F, F, F, F]`.

After **1**: process `x=1`. Right-to-left, only `dp[1] = dp[1] or dp[0] = T`.
`dp = [T, T, F, F, F, F, F, F, F, F, F, F]`.

After **5**: process `x=5`. Right-to-left from 11 to 5:
- `dp[6] = dp[6] or dp[1] = T`
- `dp[5] = dp[5] or dp[0] = T`

`dp = [T, T, F, F, F, T, T, F, F, F, F, F]`.

After **11**: process `x=11`. Only `dp[11] = dp[11] or dp[0] = T`.

`dp = [T, T, F, F, F, T, T, F, F, F, F, T]`. Early-exit returns `True`.

#### What if we'd iterated left-to-right?

Process `x = 5` going left-to-right, starting at `w = 5`:
- `dp[5] = dp[5] or dp[0] = T`
- `dp[6] = dp[6] or dp[1] = T`
- `dp[10] = dp[10] or dp[5] = T` — **but `dp[5]` was set this iteration**, so we're using item 5 *twice* to reach 10.

That's wrong for 0/1 (we don't have two 5s). Right-to-left is mandatory.

#### Complexity

- **Time:** O(n · S/2). Acceptable for `n, S ≤ ~10⁴`.
- **Space:** O(S/2) with the 1D form.

---

### Deep-dive 3 — Target Sum (LC 494)

> Given `nums` and integer `target`, count the number of ways to assign `+` or `-` to each element such that the signed sum equals `target`.

The trick: rewrite the problem as **"count subsets with a specific sum."** Let `P` be the set with `+` and `N` be the set with `-`. Then `sum(P) - sum(N) = target` and `sum(P) + sum(N) = total`. Adding: `2 · sum(P) = target + total`, so `sum(P) = (target + total) / 2`.

If `target + total` is odd or `(target + total) / 2 < 0`, the answer is 0. Otherwise, count subsets summing to `(target + total) / 2`.

#### Code

```python
def find_target_sum_ways(nums: list[int], target: int) -> int:
    total = sum(nums)
    if abs(target) > total or (target + total) % 2:               # (1) feasibility
        return 0
    s = (target + total) // 2
    dp = [0] * (s + 1)
    dp[0] = 1                                                     # (2) one empty subset
    for x in nums:
        for w in range(s, x - 1, -1):
            dp[w] += dp[w - x]                                    # (3) count add
    return dp[s]
```

1. Two infeasibility cases bundled. `abs(target) > total` is unreachable; `(target + total) % 2` makes `s` non-integer.
2. The empty subset is the unique way to make sum 0.
3. `dp[w] += dp[w - x]` says "ways to make `w` = ways to make it without using `x` + ways to make `w - x` and then add `x`."

#### Dry run on `nums = [1, 1, 1, 1, 1]`, `target = 3`

`total = 5`, `s = (3 + 5) / 2 = 4`. Want subsets summing to 4.

| Item | dp |
|------|-----|
| start | `[1, 0, 0, 0, 0]` |
| 1 | `[1, 1, 0, 0, 0]` (add 1 to dp[1]) |
| 1 | `[1, 2, 1, 0, 0]` |
| 1 | `[1, 3, 3, 1, 0]` |
| 1 | `[1, 4, 6, 4, 1]` |
| 1 | `[1, 5, 10, 10, 5]` |

`dp[4] = 5`. ✓ (The 5 ways: choose any 4 of the 5 ones to be `+`, the remaining one is `-`. C(5,4)=5.)

#### Why the `target + total` reduction is beautiful

It turns a *signed-sum count* into a *subset-sum count*. The latter has a clean DP. Without this transformation, you'd be doing a much messier 2D DP over signed partial sums (with negative indices). The reduction is the entire interview signal — recognising it earns most of the credit.

#### Complexity

- **Time:** O(n · s) where `s = (target + total) / 2`.
- **Space:** O(s).

---

## 🐛 Common bugs

1. **Iterating left-to-right in the 1D form.** Silently turns 0/1 into unbounded — items get reused. Right-to-left is mandatory.
2. **Off-by-one on the DP table size.** `dp[n+1][W+1]` (with the zero row/column for "no items / no capacity"). Using `dp[n][W]` gives a confusing recurrence with edge cases everywhere.
3. **Initialising `dp[0] = 1` for max-value problems.** Wrong — for max-value, the base is `dp[w] = 0` for all `w`. The `dp[0] = 1` initialisation is for *counting* problems.
4. **Forgetting the `if w >= wi` guard.** Negative indexing in Python doesn't error but reads from the wrong end of the array — gives garbage answers.
5. **Target Sum: not checking `(target + total)` parity.** If odd, no integer subset-sum target exists; the answer is 0.
6. **Counting variant overflow in non-Python languages.** Counts can exceed 32-bit. In Python, irrelevant; in C++/Java, use `long long` or take a modulus.
7. **Reconstructing items from a 1D rolling table.** You can't — the rolling form discards the per-item history. Keep the 2D table when you need the chosen subset.
8. **Treating "0/1" as "either skip or take any quantity."** That's unbounded knapsack. The defining feature of 0/1 is *at most once per item*.

---

## 🗣️ Interviewer phrasings to recognize

- "Pick a **subset** to maximise / minimise some additive quantity." → Max/min knapsack.
- "Can you reach this **exact sum**?" → Reachability variant.
- "How many ways to **assign signs** / **choose items** to hit a sum?" → Counting variant.
- "Partition into two **equal halves**." → Reduce to subset-sum to `total / 2`.
- "Two capacities (zeros and ones, time and money)." → 2D 0/1 knapsack.
- "Each item used **at most once**." → 0/1 (vs. unbounded).

---

## 🧭 Connections to other patterns

- **Unbounded Knapsack DP** ([16-unbounded-knapsack-dp.md](16-unbounded-knapsack-dp.md)) — same recurrence shape but iterate left-to-right (each item can be reused).
- **Subsets & Backtracking** ([10-subsets-backtracking.md](10-subsets-backtracking.md)) — explicit enumeration of subsets; DP gives the *count* or *best* without listing them.
- **LCS DP** (page coming next) — the structural cousin (2D DP, two-axis 1D rolling).
- **Sliding Window** ([01-sliding-window.md](01-sliding-window.md)) — when items have **contiguity** constraints, knapsack often reduces to sliding window or prefix sums.
- **Greedy** — fractional knapsack is greedy (sort by value/weight); 0/1 is *not* — you need DP.

---

## ✅ Self-check — 8 questions

??? question "1. Why does the 1D rolling form require right-to-left iteration?"
    `dp[w]` reads `dp[w - wi]`. Going right-to-left, smaller indices haven't been updated this iteration, so `dp[w - wi]` is the previous-row value — exactly what the 2D recurrence wants. Going left-to-right, `dp[w - wi]` has already been updated, meaning the item is being reused — that's unbounded knapsack.

??? question "2. What's the time-and-space complexity of 0/1 knapsack?"
    Time is O(n · W). Space is O(n · W) for the 2D table or O(W) for the 1D rolling array. The rolling form loses the ability to reconstruct the chosen subset.

??? question "3. How do you adapt the template for 'minimum sum' instead of 'maximum'?"
    Initialise `dp[w] = ∞` for `w > 0` and `dp[0] = 0`, then use `min` instead of `max`. Last Stone Weight II is the canonical example, after a clever reduction to subset-sum.

??? question "4. How does Target Sum (LC 494) reduce to a subset-sum problem?"
    Let P = positively-signed subset, N = negatively-signed. `sum(P) - sum(N) = target`, `sum(P) + sum(N) = total`. Adding: `sum(P) = (target + total) / 2`. Counting subsets summing to that value gives the answer. Infeasible if `target + total` is odd or `|target| > total`.

??? question "5. When does 0/1 knapsack fail to fit in memory?"
    When `n · W` exceeds memory. For large `W` and small `n`, **meet-in-the-middle** (split into two halves of n/2, enumerate sums of each, combine with two-pointer or bsearch) gives O(2^(n/2)) — better than O(n · W) for `W ≫ 2^(n/2)`. For specific structures, polynomial approximation schemes apply.

??? question "6. How do you reconstruct the chosen subset?"
    Keep the 2D table. Walk backwards from `dp[n][W]`: if `dp[i][w] != dp[i-1][w]`, item `i` was taken — record it and move to `dp[i-1][w - weights[i-1]]`. Otherwise move to `dp[i-1][w]`. Continue until `i = 0`.

??? question "7. Why is dp[0] = 1 for counting and dp[0] = True for reachability?"
    Empty subset has sum 0, and there's exactly one empty subset (counting) and it's a valid way to reach 0 (reachability). For max-value, the empty subset has value 0, so `dp[0] = 0`.

??? question "8. What changes if items have a 2D capacity (Ones and Zeroes)?"
    The state becomes `dp[i][zeros][ones]`, and the rolling form is 2D: iterate **both** zeros and ones right-to-left in nested loops. Recurrence is the same shape: skip vs. take.

---

> **Next pattern up:** Unbounded Knapsack DP — same shape but each item can be reused. The signature edit: iterate left-to-right (page coming next).
