# Unbounded Knapsack DP

> Same recurrence as 0/1 knapsack, **one character of difference**: you iterate `w` **left-to-right** instead of right-to-left. That single change lets each item be reused unlimited times. Coin Change (min coins, count ways), Rod Cutting, Combination Sum IV, and Perfect Squares all live here. The "what's the iteration order?" question is the entire interview signal — get it right, every variant follows.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is unbounded knapsack DP?

You have items, each with a weight and value, and a capacity `W`. Pick items — **each usable any number of times** — to maximise value (or minimise cost, count combinations, etc.) without exceeding `W`.

The state and recurrence are the same shape as 0/1: `dp[i][w]` = best value using items `0..i-1` with budget `w`. The recurrence: skip item `i` (`dp[i-1][w]`), or take **one more copy** of item `i` (`dp[i][w - wi] + vi`). Note the second branch reads `dp[i][·]`, not `dp[i-1][·]` — *that's* the unbounded twist.

When you collapse to 1D, the consequence is that `dp[w - wi]` should be the **already-updated** value (post-item-i), not the previous row. So you iterate `w` **left-to-right** — exactly the opposite of 0/1 knapsack.

The mental model: imagine an infinite supply of each item. The DP at column `w` "remembers" how many of each item you've used along the way; the left-to-right scan lets earlier positions feed forward into later positions, propagating multiple uses.

!!! tip "The signal — when to reach for unbounded knapsack"
    Reach for it when:

    - "Each item / coin / piece can be used **any number of times**."
    - "Min coins to make change," "max value rod-cutting," "count ways to make sum."
    - The problem mentions **infinite supply**, **unlimited use**, or items that don't deplete.

    Don't reach for it when:

    - Items are limited to one use → that's 0/1 knapsack ([15-01-knapsack-dp.md](15-01-knapsack-dp.md)).
    - Items have a *bounded* count (use 3 times, etc.) → bounded knapsack (binary-decomposition trick).
    - Order of selection matters as a permutation → that's a different DP (Combination Sum IV is the famous trap).

---

## 🧩 The three flavors

### Flavor 1: Maximise value (rod cutting / classic unbounded)

Same recurrence as 0/1, but `dp[w - wi]` reads the *current row* (post-item-i):

```python
def unbounded_knapsack(weights: list[int], values: list[int], W: int) -> int:
    dp = [0] * (W + 1)
    for w in range(1, W + 1):
        for wi, vi in zip(weights, values):
            if w >= wi:
                dp[w] = max(dp[w], dp[w - wi] + vi)               # (1) reads "this row"
    return dp[W]
```

1. The outer loop is over `w`, the inner is over items. Either order works for max/min variants — but for *counting* variants, the loop order **matters** (see Flavor 3).

Equivalent and more common framing — outer items, inner weights:

```python
def unbounded_knapsack_v2(weights: list[int], values: list[int], W: int) -> int:
    dp = [0] * (W + 1)
    for wi, vi in zip(weights, values):
        for w in range(wi, W + 1):                                # (2) left-to-right
            dp[w] = max(dp[w], dp[w - wi] + vi)
    return dp[W]
```

2. Compare with 0/1's `range(W, wi - 1, -1)`. **Left-to-right** here lets the same item be reused via `dp[w - wi]`.

**Examples:** Rod Cutting (classic), Coin Change Maximum (variant where you want the highest value reachable).

### Flavor 2: Minimise count (Coin Change "min coins")

```python
def coin_change(coins: list[int], amount: int) -> int:
    """LC 322 — fewest coins to make amount; -1 if impossible."""
    INF = amount + 1                                              # (1) sentinel
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for w in range(1, amount + 1):
        for c in coins:
            if w >= c:
                dp[w] = min(dp[w], dp[w - c] + 1)
    return dp[amount] if dp[amount] != INF else -1
```

1. `INF = amount + 1` is a safe sentinel: no valid solution can use more than `amount` coins (since coins are ≥ 1). Avoids overflow concerns of `float('inf')`.

**Examples:** Coin Change (LC 322), Perfect Squares (LC 279 — items are `1², 2², 3²…`), Minimum Cost For Tickets (LC 983 — items are 1-day, 7-day, 30-day passes).

### Flavor 3: Count combinations vs. count permutations — *the* loop-order trap

For counting problems, the **outer/inner loop order matters** — and gets it wrong on the first try almost universally.

```python
def coin_change_2(amount: int, coins: list[int]) -> int:
    """LC 518 — number of distinct combinations of coins summing to amount.
    {1, 2} and {2, 1} count as the same combination, not two."""
    dp = [0] * (amount + 1)
    dp[0] = 1                                                     # (1) empty combination
    for c in coins:                                               # (2) outer: coins
        for w in range(c, amount + 1):                            # (3) inner: amounts (left-to-right)
            dp[w] += dp[w - c]
    return dp[amount]


def combination_sum_iv(nums: list[int], target: int) -> int:
    """LC 377 — number of ordered sequences (permutations) summing to target.
    [1, 2] and [2, 1] count as TWO sequences."""
    dp = [0] * (target + 1)
    dp[0] = 1
    for w in range(1, target + 1):                                # (4) outer: target
        for x in nums:                                            # (5) inner: items
            if w >= x:
                dp[w] += dp[w - x]
    return dp[target]
```

1. Base: there's exactly one way to make sum 0 — the empty selection.
2. **Outer = items** ⇒ each item is "considered once" globally; combinations are unique up to order.
3. The classic combinations DP shape. Left-to-right inner loop.
4. **Outer = target** ⇒ at every target, all items are reconsidered; the same multiset can appear in different orders.
5. This produces *permutations*, which is what LC 377 actually wants despite its misleading name.

**The rule:**
- **Outer = items, inner = weights** → counts **combinations** (unordered).
- **Outer = weights, inner = items** → counts **permutations** (ordered).

**Examples:** Coin Change 2 (LC 518), Combination Sum IV (LC 377), Number of Dice Rolls With Target Sum (LC 1155 — bounded variant).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Max value (unlimited supply) | Rod cutting | Rod Cutting (classic) | Left-to-right inner loop |
| 2 | Min count to reach target | Fewest coins | Coin Change (LC 322) | `dp[w] = min(dp[w], dp[w-c] + 1)` |
| 3 | Count combinations (unordered) | Number of multisets | Coin Change 2 (LC 518) | Outer = items, inner = w |
| 4 | Count permutations (ordered) | Number of sequences | Combination Sum IV (LC 377) | Outer = w, inner = items |
| 5 | Reachability with reuse | Can sum reach target? | Word Break (LC 139) | Boolean DP, items = words |
| 6 | Min/max sum-of-squares | Square decomposition | Perfect Squares (LC 279) | Items are `1, 4, 9, 16, …` |
| 7 | Bounded reuse (≤ k copies) | Item with cap | Bounded knapsack | Binary-decompose into 0/1 |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Coin Change | 322 | <span class="diff-medium">Medium</span> | Min count | 📝 |
| 2 | Coin Change 2 | 518 | <span class="diff-medium">Medium</span> | Combinations | 📝 |
| 3 | Combination Sum IV | 377 | <span class="diff-medium">Medium</span> | Permutations | 📝 |
| 4 | Perfect Squares | 279 | <span class="diff-medium">Medium</span> | Min count | 📝 |
| 5 | Minimum Cost For Tickets | 983 | <span class="diff-medium">Medium</span> | Min cost (calendar) | 📝 |
| 6 | Word Break | 139 | <span class="diff-medium">Medium</span> | Reachability | 📝 |
| 7 | Word Break II | 140 | <span class="diff-hard">Hard</span> | Reconstruct (DP + backtrack) | 📝 |
| 8 | Rod Cutting | (classic) | <span class="diff-medium">Medium</span> | Max value | 📝 |
| 9 | Maximum Number of Achievable Transfer Requests | 1601 | <span class="diff-hard">Hard</span> | Bitmask / DP (cousin) | 📝 |
| 10 | Number of Dice Rolls With Target Sum | 1155 | <span class="diff-medium">Medium</span> | Bounded count | 📝 |
| 11 | Integer Break | 343 | <span class="diff-medium">Medium</span> | Decompose-and-product | 📝 |
| 12 | Stone Game IV | 1510 | <span class="diff-hard">Hard</span> | Win/lose DP | 📝 |
| 13 | Minimum Number of Refuelling Stops | 871 | <span class="diff-hard">Hard</span> | Heap / DP | 📝 |
| 14 | Climbing Stairs (k steps) | 70 generalised | <span class="diff-easy">Easy</span> | Permutations (Fibonacci cousin) | ✅ |
| 15 | Decode Ways | 91 | <span class="diff-medium">Medium</span> | Linear count (Fibonacci cousin) | 📝 |
| 16 | Number of Subarrays With Bounded Maximum | 795 | <span class="diff-medium">Medium</span> | Sliding count (cousin) | 📝 |
| 17 | Bounded Knapsack (≤ k copies) | (classic) | <span class="diff-medium">Medium</span> | Binary decomposition | 📝 |
| 18 | Maximum Earnings From Taxi | 2008 | <span class="diff-medium">Medium</span> | DP variant | 📝 |
| 19 | Concatenated Words | 472 | <span class="diff-hard">Hard</span> | Word Break + filter | 📝 |
| 20 | Minimum Coins for Watermelon (classic) | (classic) | <span class="diff-easy">Easy</span> | Min count | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Coin Change (LC 322)

> Given an array of coin denominations and an amount, return the **fewest coins** needed to make the amount, or `-1` if impossible. Coins can be reused.

The textbook unbounded knapsack with `min` aggregation.

#### Code

```python
def coin_change(coins: list[int], amount: int) -> int:
    INF = amount + 1
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for w in range(1, amount + 1):
        for c in coins:
            if w >= c:
                dp[w] = min(dp[w], dp[w - c] + 1)
    return dp[amount] if dp[amount] != INF else -1
```

#### Dry run on `coins = [1, 2, 5]`, `amount = 11`

| `w` | considered (c, dp[w-c]+1) | `dp[w]` |
|-----|---------------------------|---------|
| 0 | base | 0 |
| 1 | (1, dp[0]+1=1) | 1 |
| 2 | (1, dp[1]+1=2), (2, dp[0]+1=1) | 1 |
| 3 | (1, dp[2]+1=2), (2, dp[1]+1=2) | 2 |
| 4 | (1, 3), (2, 2) | 2 |
| 5 | (1, 3), (2, 3), (5, 1) | 1 |
| 6 | (1, 2), (2, 3), (5, 2) | 2 |
| 7 | (1, 3), (2, 2), (5, 3) | 2 |
| 8 | (1, 3), (2, 3), (5, 3) | 3 |
| 9 | (1, 4), (2, 3), (5, 3) | 3 |
| 10 | (1, 4), (2, 4), (5, 2) | 2 |
| 11 | (1, 3), (2, 3), (5, 4) | 3 |

Output: `dp[11] = 3` (e.g., 5 + 5 + 1). ✓

#### Why greedy fails

Greedy "always take the largest coin that fits" works for some currency systems (US: `[1, 5, 10, 25]`) but fails in general. Counterexample: `coins = [1, 3, 4]`, `amount = 6`. Greedy picks `4 + 1 + 1 = 3 coins`. DP picks `3 + 3 = 2 coins`. The DP is necessary for unrestricted coin sets.

#### Why `INF = amount + 1` is a safe sentinel

The maximum number of coins is bounded by `amount` (each coin is ≥ 1). So `amount + 1` is strictly greater than any valid count — comparing it with `min(...)` always loses. Avoids the float-`inf` trap (which can introduce subtle issues in mixed arithmetic).

#### Complexity

- **Time:** O(amount · |coins|).
- **Space:** O(amount).

---

### Deep-dive 2 — Coin Change 2 vs Combination Sum IV (LC 518 vs 377)

> The two near-identical problems that *aren't* identical. Coin Change 2 counts **combinations** (multisets); Combination Sum IV counts **permutations** (ordered sequences).

#### LC 518 — Coin Change 2

> Given coins and amount, return the number of distinct combinations summing to amount.

```python
def change(amount: int, coins: list[int]) -> int:
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:                                               # outer: coins
        for w in range(c, amount + 1):
            dp[w] += dp[w - c]
    return dp[amount]
```

#### LC 377 — Combination Sum IV

> Given an array of distinct positive integers and a target, return the number of *ordered* combinations that add up to target. Order matters: `[1, 2]` and `[2, 1]` are distinct.

```python
def combination_sum_iv(nums: list[int], target: int) -> int:
    dp = [0] * (target + 1)
    dp[0] = 1
    for w in range(1, target + 1):                                # outer: target
        for x in nums:
            if w >= x:
                dp[w] += dp[w - x]
    return dp[target]
```

#### The crucial difference, in one diagram

For `coins = [1, 2]`, `amount = 3`:

**LC 518** (outer coins):

| Step | After processing | dp |
|------|-----------------|-----|
| start | — | `[1, 0, 0, 0]` |
| coin 1 | every w gets `+= dp[w-1]` | `[1, 1, 1, 1]` |
| coin 2 | `dp[2] += dp[0]`, `dp[3] += dp[1]` | `[1, 1, 2, 2]` |

`dp[3] = 2`: combinations `{1,1,1}` and `{1,2}`. Two combinations. ✓

**LC 377** (outer target):

| Step | dp before | After computing dp[w] |
|------|-----------|------------------------|
| w=1 | `[1, 0, 0, 0]` | `dp[1] = dp[0] = 1` → `[1, 1, 0, 0]` |
| w=2 | `[1, 1, 0, 0]` | `dp[2] = dp[1] + dp[0] = 2` → `[1, 1, 2, 0]` |
| w=3 | `[1, 1, 2, 0]` | `dp[3] = dp[2] + dp[1] = 3` → `[1, 1, 2, 3]` |

`dp[3] = 3`: permutations `[1,1,1]`, `[1,2]`, `[2,1]`. Three permutations. ✓

#### Why the loop order causes this

**LC 518's** outer-coin loop fixes a "left-to-right" notion of items. Once we move past coin 1, no `dp[w]` update will use coin 1 *again from scratch* — it can only chain forward via `dp[w - 2]`. So multisets are counted once.

**LC 377's** outer-target loop reconsiders all items at every `w`. So `[1, 2]` (use 1, then 2) and `[2, 1]` (use 2, then 1) are reached by *different paths* in the recurrence — counted separately.

This loop-order rule generalises beyond knapsack to many counting DPs. **When the count "feels" wrong, swap the loops.**

#### Complexity

Both: **Time** O(n · target). **Space** O(target).

---

### Deep-dive 3 — Word Break (LC 139)

> Given a string `s` and a dictionary of words, return `True` if `s` can be segmented into a sequence of dictionary words. Words can be reused.

This is unbounded "items" (the dictionary words) with a one-dimensional capacity (the prefix of `s`) — and the recurrence is the same shape, just *over string positions* instead of integer weights.

#### Code

```python
def word_break(s: str, word_dict: list[str]) -> bool:
    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True                                                  # (1) empty prefix
    for w in range(1, n + 1):
        for word in word_set:
            wl = len(word)
            if w >= wl and s[w - wl:w] == word and dp[w - wl]:    # (2) suffix matches and prefix is breakable
                dp[w] = True
                break
    return dp[n]
```

1. The empty string is trivially "breakable" (zero-segment decomposition). This is the base case that lets recursion bottom out.
2. To break `s[:w]`, find any dictionary word that's a suffix of length `wl` such that `s[:w - wl]` is breakable.

#### Dry run on `s = "leetcode"`, `wordDict = ["leet", "code"]`

`n = 8`, initial `dp = [T, F, F, F, F, F, F, F, F]`.

| `w` | Check suffixes | Set? |
|-----|----------------|------|
| 1 | "l" — no match | — |
| 2 | "le", "el" — no match | — |
| 3 | "lee", "eet", "tco" — no match | — |
| 4 | "leet" matches; `dp[0] = True` | `dp[4] = T` |
| 5 | "tcod", "leet" (not at 5)… no | — |
| 6 | "etco" etc. — no | — |
| 7 | "tcode" — no | — |
| 8 | "code" matches; `dp[4] = True` | `dp[8] = T` |

Output: `dp[8] = True`. ✓ ("leet" + "code".)

#### A subtlety — iterating over substring lengths is faster

A typical optimisation: instead of looping over the whole word set (which can be expensive), loop over `j` from 0 to `w-1`, check if `s[j:w] in word_set` and `dp[j]`. This is O(n²) string slicing in the worst case, but **with a maximum word length cap**, it's O(n · max_word_len), which is faster than O(n · |dict|) when `|dict|` is large but words are short.

```python
def word_break_optimised(s: str, word_dict: list[str]) -> bool:
    word_set = set(word_dict)
    max_len = max((len(w) for w in word_set), default=0)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for w in range(1, n + 1):
        for j in range(max(0, w - max_len), w):                   # only meaningful j
            if dp[j] and s[j:w] in word_set:
                dp[w] = True
                break
    return dp[n]
```

#### Why this isn't 0/1

The same word can appear multiple times in the segmentation: `s = "aaa"`, `wordDict = ["a"]` is breakable (three uses of "a"). 0/1 logic would forbid that. The unbounded structure — which lets a word be reused — is exactly what's needed.

#### Complexity

- **Time:** O(n² · max_word_len) for substring matching with the optimised loop.
- **Space:** O(n) for `dp` plus O(|dict|) for the word set.

---

## 🐛 Common bugs

1. **Iterating right-to-left in the 1D form.** Silently turns unbounded into 0/1 — items are no longer reused. Left-to-right is mandatory.
2. **Wrong loop order in counting variants.** Outer-items / inner-target gives combinations; outer-target / inner-items gives permutations. Pick based on the problem's wording.
3. **`INF = float('inf')` for min-coins.** Works in Python but adds floats to integer arithmetic; can produce subtle float-comparison issues. Use `amount + 1` (a sentinel that's strictly larger than any valid count).
4. **Coin Change confused with Coin Change 2.** Different problems entirely — the first asks for *fewest coins*, the second for *number of combinations*. Different recurrences (`min` vs sum), different aggregations.
5. **Not handling `amount = 0` separately.** `dp[0] = 0` for min-count problems and `dp[0] = 1` for counting problems — set the base case explicitly before the main loop.
6. **Reading the problem as "exactly one of each item" when it's actually unbounded.** Re-read: "you may use any coin any number of times" → unbounded. Missing this single line wastes the next 20 minutes.
7. **Using DFS+memo for Combination Sum IV with no termination check.** If a non-positive number is in `nums`, the recursion never bottoms out. The DP form is safer (target strictly decreases).
8. **Word Break: substring comparison inside a tight loop.** Python string slicing is O(k); doing it n × |dict| times can be slow. Cache `max_len` and limit `j` to `[w - max_len, w)`.

---

## 🗣️ Interviewer phrasings to recognize

- "Each coin / piece can be used **any number of times**." → Unbounded knapsack.
- "Number of **ways** / **combinations** to make sum X." → Counting variant; choose loop order based on whether order matters.
- "**Fewest** coins / smallest pieces / minimum cost." → Min-count variant.
- "Can the string be **segmented**?" → Word Break (one-dimensional unbounded).
- "How many sequences (order matters) sum to X?" → Combination Sum IV (outer = target).
- "Cut a rod into pieces to maximise revenue." → Rod Cutting (max-value flavor).

---

## 🧭 Connections to other patterns

- **0/1 Knapsack DP** ([15-01-knapsack-dp.md](15-01-knapsack-dp.md)) — same recurrence, opposite iteration order; the right-vs-left rule is the only structural difference.
- **Fibonacci Numbers DP** ([17-fibonacci-numbers-dp.md](17-fibonacci-numbers-dp.md)) — Climbing Stairs is essentially Combination Sum IV with `nums = [1, 2]`. Many "linear count" DPs are unbounded knapsacks in disguise.
- **Subsets & Backtracking** ([10-subsets-backtracking.md](10-subsets-backtracking.md)) — backtracking *enumerates*; DP *counts/aggregates*. Combination Sum (LC 39) is an explicit-listing variant of unbounded knapsack.
- **Greedy** — Greedy works for *canonical* coin systems (USD, EUR) but fails in general. DP is the correct fallback.
- **BFS** — Coin Change can be reformulated as shortest path in a graph where nodes are amounts and edges are coin denominations. Same complexity, different framing.

---

## ✅ Self-check — 8 questions

??? question "1. What's the single-character difference between 0/1 and unbounded knapsack in 1D code?"
    The inner loop direction. 0/1: `for w in range(W, wi - 1, -1)` (right-to-left). Unbounded: `for w in range(wi, W + 1)` (left-to-right). Going left-to-right lets `dp[w - wi]` be the just-updated current-row value, allowing item reuse.

??? question "2. Why is the loop order different for Coin Change 2 vs Combination Sum IV?"
    Coin Change 2 counts unordered combinations: outer = items, inner = target — each item is fixed in a slot of the loop nesting, so the same multiset isn't counted twice. Combination Sum IV counts ordered sequences: outer = target, inner = items — at every target we reconsider all items, generating all orderings.

??? question "3. Why does `INF = amount + 1` work as a sentinel in Coin Change?"
    The minimum number of coins to make a positive amount with positive coins is at most `amount` (using all 1-coins, if available). So `amount + 1` is strictly larger than any valid count; it's a valid sentinel that loses every `min` comparison and stays in unreachable cells.

??? question "4. When can greedy beat DP for coin change?"
    Greedy works iff the coin system is **canonical** — coins like USD `[1, 5, 10, 25]` are. Many real currencies are. For arbitrary coin sets (e.g., `[1, 3, 4]`), greedy can give wrong answers (`6 = 4 + 1 + 1` greedy vs `3 + 3` DP). A theorem characterises canonical coin systems (Pearson 2005); for interview, default to DP.

??? question "5. How would you handle a 'use this item at most k times' variant (bounded knapsack)?"
    Decompose item with count `k` into items with counts `1, 2, 4, …, 2^t, k - (2^(t+1) - 1)` (binary decomposition). Each chunk is treated as a single 0/1 item. Total log(k) items per original item; overall O(n · W · log k_max). Cleaner than naive O(n · W · k).

??? question "6. Why is Word Break unbounded, not 0/1?"
    The same word can appear in the segmentation many times (`"aaa"` with `wordDict = ["a"]`). 0/1 would treat each dictionary word as usable at most once, breaking the natural definition.

??? question "7. How does Perfect Squares (LC 279) fit this template?"
    The "items" are the squares `1, 4, 9, 16, …, ⌊√n⌋²`. The capacity is the integer `n`. Min-count recurrence: `dp[w] = min(dp[w], dp[w - k²] + 1)` for each k². Lagrange's four-square theorem gives an O(1) characterisation, but the DP is the standard interview answer.

??? question "8. How would you reconstruct the actual coins used in Coin Change?"
    Keep a parent array alongside `dp`: `parent[w]` records which coin was used to reach `dp[w]`. When `dp[w]` is updated by `dp[w - c] + 1`, set `parent[w] = c`. To recover the coins, walk from `parent[amount]` down to 0, emitting each `parent[w]` and jumping to `w - parent[w]`.

---

> **Next pattern up:** Fibonacci Numbers DP — the simplest 1D linear-recurrence DP, covering Climbing Stairs, House Robber, Decode Ways, and the recurrences whose state is the last 1–2 values (page coming next).
