# Advanced DP

> The chapter where DP stops being "1D / 2D table" and becomes a **language**: state design as a craft, transitions as algebra, optimisations as theorems. Four flavors carry the weight of every "DP-tier-hard" problem you'll meet: **digit DP** for "count integers in `[L, R]` satisfying property P", **bitmask DP** for "assign / visit / partition over a small universe (n ≤ 20)", **DP on trees with rerooting** for "compute f(v) for every root v in `O(n)` not `O(n²)`", and **SOS / Knuth-style optimisations** that drop a quadratic to `O(n · 2ⁿ)` or `O(n²)` to `O(n log n)`. Master the four and you've covered the long tail of contest-grade DP.

<span class="phase-status phase-done">Phase 7 — Ultra-Advanced</span>

---

## 📖 What makes DP "advanced"?

Standard DP teaches you to find a **state** `dp[i][j]` whose value depends on smaller subproblems. Advanced DP keeps that skeleton but adds three twists:

1. **The state is a structured object, not a number.** A bitmask, a tight digit-by-digit walk over `N`, a (vertex, parent) pair on a tree.
2. **The transition is itself an algorithm.** Subset enumeration over a bitmask, "tight" carry-propagation in digit DP, rerooting via a difference identity on a tree.
3. **The optimisation theorem matters.** Knuth's optimality (`opt[i][j-1] ≤ opt[i][j] ≤ opt[i+1][j]`) drops `O(n³)` matrix-chain-style DPs to `O(n²)`. SOS aggregates over `2ⁿ` subsets in `O(n · 2ⁿ)` instead of `O(3ⁿ)`. Convex-hull-trick / Li-Chao tree handle "min over linear functions" transitions in `O(log n)`.

The mental model: **state design is about identifying the smallest sufficient summary**, transitions are about **enumerating all "previous moves" cheaply**, and optimisations exploit **monotonicity / convexity / set-algebra** properties of the transition.

!!! tip "The signal — when to reach for advanced DP"
    Reach for it when:

    - The problem says "count / find numbers in `[L, R]` such that..." → **digit DP**.
    - `n ≤ 20` and the problem is "visit all / partition / assign" → **bitmask DP** (the `n ≤ 20` ceiling is the giveaway).
    - The problem is on a tree and asks for `f(v)` **for every vertex `v`** → **rerooting**.
    - "Sum / max over all subsets `S ⊆ T`" — and `T` is a bitmask of size `≤ 20` → **SOS DP**.
    - You have an `O(n²)` DP `dp[i][j] = min_k (dp[i][k] + cost(k, j))` and `cost` satisfies the **quadrangle inequality** → **Knuth optimisation** to `O(n²)`.
    - Transitions are `dp[i] = min_j (dp[j] + b[j] · x[i] + c[j])` with monotone slopes → **convex-hull trick / Li-Chao tree**.

    Don't reach for it when:

    - `n ≤ 20` but the structure is graph-flow / matching → max-flow may be cleaner.
    - The state space is `2ⁿ` and `n > 22` — switch to meet-in-the-middle or a different formulation.
    - "Counting" smells like generating functions or matrix exponentiation — those are different tools.

---

## 🧩 The four flavors

### Flavor 1: Digit DP — counting in `[L, R]` with constraints

The skeleton: walk `N` digit-by-digit, carrying a **`tight`** flag (am I still constrained to be ≤ `N`'s digits so far?) plus whatever state the property requires (last digit, current digit-sum mod m, has-leading-zero, mask of used digits).

```python
from functools import lru_cache

def count_le(N: int) -> int:
    """Count integers in [0, N] with at most k=3 distinct nonzero digits."""
    digits = list(map(int, str(N)))                                   # (1)
    n = len(digits)

    @lru_cache(maxsize=None)
    def go(i: int, mask: int, tight: bool, leading: bool) -> int:     # (2)
        if i == n:
            return 1 if bin(mask).count("1") <= 3 else 0
        upper = digits[i] if tight else 9                             # (3)
        total = 0
        for d in range(0, upper + 1):
            new_mask = mask if (leading and d == 0) else mask | (1 << d)
            total += go(i + 1, new_mask, tight and d == upper, leading and d == 0)
        return total

    return go(0, 0, True, True)
```

1. Convert `N` to its digit list — fixes the digit-by-digit walk order.
2. **State**: position `i`, used-digits `mask`, `tight` (still bounded by `N`), `leading` (haven't placed a nonzero digit yet — distinguishes `00007` from `00010`).
3. **Tight propagation**: if I was tight and pick exactly the matching digit, I stay tight; otherwise I go free for all subsequent positions.

Use `count_le(R) - count_le(L - 1)` for ranges.

### Flavor 2: Bitmask DP — `2ⁿ` states for `n ≤ 20`

When the input has `n ≤ 20` "items" and you must consider every subset — TSP-style ("visit every city"), assignment ("each task to one worker"), or partition ("split into groups summing to S") — `dp[mask]` (or `dp[mask][last]` for path-flavoured) is canonical.

```python
def tsp(dist: list[list[int]]) -> int:
    """Travelling salesman: shortest tour starting and ending at city 0."""
    n = len(dist)
    INF = float("inf")
    dp = [[INF] * n for _ in range(1 << n)]                           # (1)
    dp[1][0] = 0                                                      # (2)
    for mask in range(1 << n):
        for u in range(n):
            if dp[mask][u] == INF or not (mask >> u) & 1:
                continue
            for v in range(n):                                         # (3)
                if (mask >> v) & 1:
                    continue
                new_mask = mask | (1 << v)
                if dp[new_mask][v] > dp[mask][u] + dist[u][v]:
                    dp[new_mask][v] = dp[mask][u] + dist[u][v]
        # close the tour from any u in the full mask
    full = (1 << n) - 1
    return min(dp[full][u] + dist[u][0] for u in range(1, n))
```

1. `dp[mask][u]` = shortest path that visits exactly `mask`'s set bits and ends at `u`.
2. Start: visited only `{0}`, currently at `0`, cost `0`.
3. Try every "next city" `v` not yet in `mask`. `O(2ⁿ · n²)` total — `n=20` is the practical ceiling (~10⁸ ops with cheap inner work).

**Sub-pattern: enumerate subsets of a mask.** `s = (s - 1) & mask` walks all submasks of `mask` in `O(3ⁿ)` total over all masks — the right complexity bound when each submask of each mask is visited once.

```python
s = mask
while s > 0:
    # process subset s
    s = (s - 1) & mask
# don't forget s = 0 if needed
```

### Flavor 3: Tree DP with rerooting — `f(v)` for every root in `O(n)`

Standard tree DP picks an arbitrary root, computes `down[v]` = answer for `v`'s subtree, in one DFS. Rerooting computes `f(v)` = "answer if `v` were the root" for **every** `v`, by combining `down[v]` with a second pass that propagates the **`up[v]`** contribution from outside `v`'s subtree.

```python
import sys
sys.setrecursionlimit(10**6)

def sum_of_distances(n: int, edges: list[tuple[int, int]]) -> list[int]:
    """LC 834: sum of distances from each node to all others."""
    g: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v)
        g[v].append(u)

    size = [1] * n
    down = [0] * n                                                    # sum of distances within subtree

    def dfs1(u: int, parent: int) -> None:                            # (1)
        for v in g[u]:
            if v == parent: continue
            dfs1(v, u)
            size[u] += size[v]
            down[u] += down[v] + size[v]

    ans = [0] * n
    def dfs2(u: int, parent: int, up: int) -> None:                   # (2)
        ans[u] = down[u] + up
        for v in g[u]:
            if v == parent: continue
            # contribution to v from "outside v's subtree" =
            #     ans[u] (full answer at u) − (down[v] + size[v]) (v's subtree contribution to u)
            #     + (n − size[v])              (everyone outside v moves 1 step closer)
            new_up = (ans[u] - (down[v] + size[v])) + (n - size[v])
            dfs2(v, u, new_up - down[v])                              # (3)

    dfs1(0, -1)
    dfs2(0, -1, 0)
    return ans
```

1. **First pass (post-order):** compute subtree size and `down[u]` = `Σ d(u, w)` for `w` in `u`'s subtree.
2. **Second pass (pre-order):** for each child `v`, derive its `up` contribution from the parent's full answer minus what `v`'s subtree contributed.
3. The identity `ans[v] = down[v] + up[v]` is what makes rerooting work — every advanced rerooting problem is a different `combine` function on top of this skeleton.

### Flavor 4: SOS DP — sum over subsets in `O(n · 2ⁿ)`

Compute, for every mask `S`, the sum `f(S) = Σ_{T ⊆ S} a[T]` where `a` is given. The naive enumeration of submasks is `O(3ⁿ)`. SOS does it in `O(n · 2ⁿ)` via a **dimension-by-dimension** roll-up — the same idea as multi-dimensional prefix sums.

```python
def sos(a: list[int]) -> list[int]:
    """f[S] = sum of a[T] over all T subset-of-equal S."""
    n = (len(a) - 1).bit_length()
    f = a[:]
    for i in range(n):                                                # (1)
        for mask in range(1 << n):
            if (mask >> i) & 1:
                f[mask] += f[mask ^ (1 << i)]                         # (2)
    return f
```

1. For each bit-position `i`, treat that bit as a "dimension."
2. If bit `i` is set in `mask`, add the value of the same mask with bit `i` cleared. After the `i`-th pass, `f[mask]` = sum over all `T ⊆ mask` that match `mask` on bits `> i`.

**Inverse SOS** (mobius / superset sum) just flips the condition `if not (mask >> i) & 1:` — useful for "sum over supersets."

---

## 🔍 Sub-pattern at-a-glance

| # | Sub-pattern                          | Trigger                                        | State                                             | Complexity     |
|---|--------------------------------------|------------------------------------------------|---------------------------------------------------|----------------|
| 1 | Digit DP (basic)                     | "Count in [L, R] with property"                | `(pos, tight, leading, ...prop_state)`            | O(D · S · 10)  |
| 2 | Digit DP on pairs                    | "Pairs (a, b) with a + b = N and ..."          | Two-tape walk with shared tight                   | O(D · S · 100) |
| 3 | Bitmask TSP / Hamiltonian            | n ≤ 20, visit all                              | `dp[mask][last]`                                  | O(2ⁿ · n²)     |
| 4 | Bitmask partition / cover            | n ≤ 16, "minimum groups"                       | `dp[mask]` + submask enumeration                  | O(3ⁿ)          |
| 5 | Bitmask profile DP (broken profile)  | Tile a grid, n ≤ 12 in one dim                 | `dp[row][profile_mask]`                           | O(rows · 2ⁿ · 2ⁿ) |
| 6 | Tree DP (single root)                | "Subtree property"                             | `dp[v][...optional_state]`                        | O(n)           |
| 7 | Rerooting tree DP                    | "Answer for each vertex as root"               | `down[v]` + `up[v]` two-pass                      | O(n)           |
| 8 | SOS / superset DP                    | "Sum over subsets of mask"                     | `f[mask]` rolled bit-by-bit                       | O(n · 2ⁿ)      |
| 9 | Knuth optimisation                   | `dp[i][j] = min_k dp[i][k] + dp[k][j] + w(i,j)` with quadrangle ineq. | `opt[i][j]` monotone | O(n²)          |
| 10| Convex hull trick / Li-Chao          | `dp[i] = min_j (dp[j] + m_j · x_i + c_j)`       | Lower envelope of lines                           | O(n log n)     |

---

## 📚 20 problems where advanced DP is the canonical answer

| #  | Source        | Problem                                               | Difficulty | Pattern                     | Key insight                                                                       |
|----|---------------|-------------------------------------------------------|------------|-----------------------------|-----------------------------------------------------------------------------------|
| 1  | LC 233        | Number of Digit One                                   | Hard       | Digit DP                    | Count `1`s digit by digit; or closed-form for each position.                     |
| 2  | LC 600        | Non-negative integers without consecutive ones         | Hard       | Digit DP                    | State = (pos, last_bit, tight); count binary digits.                             |
| 3  | LC 902        | Numbers At Most N Given Digit Set                      | Hard       | Digit DP                    | Tight walk over `N`; restrict each digit to the given set.                       |
| 4  | LC 1012       | Numbers With Repeated Digits                           | Hard       | Digit DP                    | Complement: count without repeats with a 10-bit `used` mask, subtract from N.    |
| 5  | LC 1397       | Find All Good Strings                                  | Hard       | Digit DP × KMP              | Walk the string with two tight flags + KMP automaton state.                      |
| 6  | CF Round 1036 | Counting Triangles (digit-DP-flavoured)                | Hard       | Digit DP                    | State = (pos, tight, current_sum_mod_3).                                         |
| 7  | LC 943        | Find the Shortest Superstring                          | Hard       | Bitmask DP                  | `dp[mask][last]` over which strings used; transitions add `overlap(last, j)`.    |
| 8  | LC 847        | Shortest Path Visiting All Nodes                       | Hard       | Bitmask DP + BFS            | BFS on `(node, mask)`; same skeleton as TSP.                                     |
| 9  | LC 1125       | Smallest Sufficient Team                               | Hard       | Bitmask DP                  | Skill-mask state; minimise team size to cover all skills.                        |
| 10 | LC 1494       | Parallel Courses II                                    | Hard       | Bitmask DP                  | `dp[taken_mask]` = min semesters; transitions enumerate ≤ k feasible new courses.|
| 11 | LC 1659       | Maximize Grid Happiness                                | Hard       | Profile / bitmask DP        | Row-by-row state encodes the previous row's people-types in ternary.             |
| 12 | LC 1799       | Maximize Score After N Operations                      | Hard       | Bitmask DP                  | `dp[mask]` = max score after pairing some elements; transitions pick a pair.     |
| 13 | LC 1986       | Minimum Number of Work Sessions                        | Medium     | Bitmask DP                  | `dp[mask]` = (sessions, used_in_last); careful tuple ordering.                   |
| 14 | LC 834        | Sum of Distances in Tree                               | Hard       | Rerooting                   | Two-pass DFS with `down[v]` then `up[v]` rolling identity.                       |
| 15 | LC 1372       | Longest ZigZag Path in a Binary Tree                   | Medium     | Tree DP                     | `dp[v][0/1]` = longest zigzag ending at `v` going left/right.                    |
| 16 | LC 968        | Binary Tree Cameras                                    | Hard       | Tree DP                     | Three states per node: covered-with-camera, covered-no-camera, uncovered.        |
| 17 | LC 337        | House Robber III                                       | Medium     | Tree DP                     | `dp[v]` = (rob_v, skip_v); standard "two-state" tree DP.                         |
| 18 | CF EDU SOS    | Sum over subsets — official problem set                | Medium     | SOS                         | Roll dimension-by-dimension; classic O(n · 2ⁿ).                                  |
| 19 | LC 1681       | Minimum Incompatibility                                | Hard       | Bitmask DP + SOS-style cost | Pre-compute valid-subset costs by submask enumeration, then `dp[mask]` over partitions. |
| 20 | LC 879        | Profitable Schemes                                     | Hard       | 3D DP                       | `dp[i][members][profit_floor]`; profit caps at `minProfit`. Multi-dim state.     |

---

## 🔬 Deep-dive 1 — Digit DP, fully traced

**Problem:** count integers in `[1, N]` with **at most one repeated digit** (LC 1012 backwards).

**N = 234, walk:** digits = `[2, 3, 4]`, `n = 3`.

State: `(pos, used_mask, tight, leading)`. We'll trace `go(0, 0, True, True)`:

- `pos=0, mask=0, tight=True`: `upper = 2`. Try `d ∈ {0, 1, 2}`.
  - `d=0`: `leading=True` → `new_mask = 0`; recurse `(1, 0, False, True)`.
  - `d=1`: `leading` becomes False; `new_mask = 1<<1 = 2`; recurse `(1, 2, False, False)`.
  - `d=2`: `tight` stays True; `new_mask = 4`; recurse `(1, 4, True, False)`.

Take the `d=2` branch:

- `pos=1, mask=4, tight=True`: `upper = 3`. Try `d ∈ {0..3}`.
  - `d=2`: bit `2` already in mask → repeat allowed (we're "at most one repeat"). Update repeat-count state.
  - `d=3`: `tight` stays True (matches `digits[1]`); `new_mask = 4 | 8 = 12`; recurse `(2, 12, True, False)`.

Take that branch:

- `pos=2, mask=12, tight=True`: `upper = 4`. `d ∈ {0..4}`.
  - For each `d`, check `bit d` against `mask`; if already set, increment repeat-count.

The point of the trace: **the only "magic" in digit DP is the tight propagation.** Everything else is a normal recursive count. Memoising on `(pos, mask, leading)` (dropping `tight` because tight states are visited at most once) keeps it `O(D · 2¹⁰)`.

**Why memoise drops `tight`:** at any given `(pos, mask, leading)`, there's at most one tight branch (the one that matched digits exactly so far). All other branches reaching that `(pos, mask, leading)` are non-tight and identical — memoise on the non-tight version, recompute the tight branch live each time.

---

## 🔬 Deep-dive 2 — TSP traced on n=4

**Cities `0,1,2,3`** with symmetric distances:

```
      0   1   2   3
  0   0  10  15  20
  1  10   0  35  25
  2  15  35   0  30
  3  20  25  30   0
```

**Initial:** `dp[0001][0] = 0`, all others ∞.

**mask = 0001 (just {0})**, `u=0`, `dp[0001][0] = 0`. Try `v ∈ {1, 2, 3}`:
- `v=1`: `dp[0011][1] = 0 + 10 = 10`.
- `v=2`: `dp[0101][2] = 0 + 15 = 15`.
- `v=3`: `dp[1001][3] = 0 + 20 = 20`.

**mask = 0011 ({0,1})**, `u=1`, `dp[0011][1]=10`. Try `v ∈ {2, 3}`:
- `v=2`: `dp[0111][2] = 10 + 35 = 45`.
- `v=3`: `dp[1011][3] = 10 + 25 = 35`.

**mask = 0101 ({0,2})**, `u=2`, `dp[0101][2]=15`:
- `v=1`: `dp[0111][1] = 15 + 35 = 50`.
- `v=3`: `dp[1101][3] = 15 + 30 = 45`.

**mask = 1001 ({0,3})**, `u=3`, `dp[1001][3]=20`:
- `v=1`: `dp[1011][1] = 20 + 25 = 45`. Worse than 35? No — different last-vertex slot, both stored.
- `v=2`: `dp[1101][2] = 20 + 30 = 50`.

(Continue through masks 0111, 1011, 1101, 1110, 1111…)

**Final:** for `mask = 1111`, take `min over u of dp[1111][u] + dist[u][0]` to close the tour. Optimum here is `0 → 1 → 3 → 2 → 0` of length `10 + 25 + 30 + 15 = 80`.

Note how `dp[mask][u]` stores **one entry per (subset, current vertex)** — the `last` axis is the price you pay so the next transition knows where to depart from.

---

## 🔬 Deep-dive 3 — Why rerooting works (the difference identity)

Given a tree rooted at `r`, define `S(r) = Σ_v d(r, v)` (sum of distances). The first DFS computes `S(0)` along with `down[v]` = sum of distances from `v` to its subtree.

When we **reroot** from parent `u` to child `v`:

- Every vertex in `v`'s subtree gets **1 closer** to the root → `−size[v]` contribution.
- Every vertex *outside* `v`'s subtree gets **1 farther** → `+(n − size[v])` contribution.

So `S(v) = S(u) − size[v] + (n − size[v]) = S(u) + n − 2 · size[v]`.

That's the entire trick. **One DFS sets up `S(0)`; one more pass propagates by the identity `S(child) = S(parent) + n − 2 · size[child]`.**

Generalised: any rerooting DP needs a **`combine`** function such that `f(child) = combine(f(parent), Δ_v)` where `Δ_v` depends only on the edge `parent → child`. If you can write that identity, rerooting works.

---

## 🐛 Common bugs

1. **Forgetting `leading` in digit DP.** Without it, you double-count `0007 = 7` because `0` is treated as a "used digit". Always carry `leading` until the first nonzero digit appears.
2. **Memoising on `tight` in digit DP.** Memoising the tight branch is wrong because it depends on the prefix matching `N`'s prefix exactly; only memoise non-tight states.
3. **Bitmask DP off-by-one in mask iteration.** `for mask in range(1 << n)` includes `0` (empty set) and `(1 << n) - 1` (full set). If your transition assumes "at least one bit set," guard `dp[0]` carefully.
4. **Submask enumeration missing the empty submask.** `s = (s - 1) & mask` walks `s` down to `0` exclusive. If you need `s = 0`, handle it separately or change the loop to `do { ... } while (s > 0)`.
5. **Bitmask DP confusing "items used" with "items remaining."** Both encodings work; pick one and stick with it. Mixing causes silent off-by-one bugs.
6. **Rerooting not subtracting the child contribution.** `up[v] = combine(ans[u] − contribution_of_v_to_u, ...)` — forgetting the subtraction adds child's subtree twice.
7. **Tree DP recursion overflow on path graphs.** Python's default 1000-frame limit blows up on `n = 10⁴`. Bump `sys.setrecursionlimit` or convert to an iterative post-order.
8. **SOS direction wrong.** Subset sums (sum over `T ⊆ S`) and superset sums (sum over `T ⊇ S`) flip the `if (mask >> i) & 1` check. Pick the direction matching your problem.
9. **Knuth optimisation applied without checking the quadrangle inequality.** It's `cost(a, c) + cost(b, d) ≤ cost(a, d) + cost(b, c)` for `a ≤ b ≤ c ≤ d`. Without it, the `opt[i][j]` monotonicity fails and you get wrong answers, not just slow ones.
10. **Profile DP confusing rows vs columns.** Profile masks the **smaller** dimension; if `rows ≤ 12` flip the grid before iterating.

---

## 🗣️ Interviewer phrasings to recognize

- "How many integers in `[1, N]` satisfy ..." / "Count numbers with property P up to 10¹⁸" → **digit DP**.
- "n ≤ 20", "visit all", "shortest tour", "assign each task" → **bitmask DP**.
- "For each node, compute ..." (on a tree) → **rerooting**.
- "Sum over all subsets of mask" / "for each mask, count supersets" → **SOS DP**.
- "Place `n` items in `k` bins minimising X" with `n ≤ 16` → **bitmask partition DP**.
- "Tile a grid with dominoes / L-shapes" → **profile DP**.
- "Cost is `dp[i][k] + dp[k][j] + w(i, j)`" → check **Knuth optimisation**.
- "Minimum cost over piecewise-linear functions" → **convex hull trick**.

---

## 🧭 Connections to other patterns

- **[Tries](../05-advanced/01-tries.md)** — digit DP can be reframed as DP on a (binary or decimal) trie of `[0, N]`.
- **[Heavy-Light Decomposition](../05-advanced/06-heavy-light-decomposition.md)** — rerooting is the "answer-everywhere" cousin of HLD's "path query" worldview.
- **[Persistent Data Structures](01-persistent-data-structures.md)** — persistent segment trees on rerooting let you "freeze" subtree contributions for offline queries.
- **[Max-Flow / Min-Cut](02-max-flow-min-cut.md)** — some bitmask DPs (e.g. LC 1494 Parallel Courses II) have flow formulations; bitmask wins when `n` is small.
- **Matrix exponentiation** — when transitions are linear and the state space is small, raise the transition matrix to the `n`-th power for `O(s³ log n)`.
- **Generating functions** — counting DPs with multiplicative structure often have closed-form polynomial-multiplication solutions.

---

## ✅ Self-check — 8 questions

??? question "1. In digit DP, why do we usually memoise on `(pos, ...state)` and NOT on `tight`?"
    Because along any root-to-leaf walk in the digit-by-digit recursion there's at most **one** tight path (the one matching `N` exactly so far). All non-tight paths reaching a given `(pos, state)` are interchangeable — they share the same future. Memoising treats only the non-tight states; the tight branch is recomputed live each time, which is fine because it's traversed once per top-level call.

??? question "2. Why is `n ≤ 20` the practical ceiling for bitmask DP?"
    `2²⁰ ≈ 10⁶` masks; with an `O(n)` transition that's ~`10⁷` ops — fine. `2²⁵ ≈ 3·10⁷` masks with `n=25` factor pushes past `10⁹`. For `n > 20` you usually need meet-in-the-middle, structure-specific pruning, or a different algorithm entirely.

??? question "3. State the rerooting identity and explain in one sentence why it's `O(n)` not `O(n²)`."
    `f(child) = combine(f(parent), Δ_edge)` — once `f(root)` is computed, every other vertex's answer is one constant-time update from its parent's answer, so two DFS passes (one bottom-up to set up subtree contributions, one top-down to propagate `up[v]`) suffice.

??? question "4. Trace why SOS runs in `O(n · 2ⁿ)` and not `O(3ⁿ)`."
    Naively summing over `T ⊆ S` for every `S` visits each `(S, T)` pair with `T ⊆ S` — there are `3ⁿ` such pairs total. SOS instead does `n` passes, each pass aggregating one bit-position over all `2ⁿ` masks: `n · 2ⁿ = 20 · 10⁶ ≈ 2·10⁷` for `n=20`, vs `3²⁰ ≈ 3.5·10⁹`.

??? question "5. What property must `cost(i, j)` satisfy for Knuth optimisation, and what monotonicity does it imply?"
    The **quadrangle inequality**: `cost(a, c) + cost(b, d) ≤ cost(a, d) + cost(b, c)` for `a ≤ b ≤ c ≤ d`. This implies `opt[i][j-1] ≤ opt[i][j] ≤ opt[i+1][j]`, so when computing `dp[i][j]`'s minimising `k`, you only check `k ∈ [opt[i][j-1], opt[i+1][j]]`. The total work telescopes to `O(n²)`.

??? question "6. In bitmask TSP, why is the state `dp[mask][last]` and not just `dp[mask]`?"
    Because the next transition appends a new city `v` and must add `dist[last][v]` — without `last` in the state, you don't know where to depart from. Adding `last` multiplies state by `n` and gives `O(2ⁿ · n²)` total.

??? question "7. What's the difference between subset SOS and superset SOS, and how do you flip the direction?"
    Subset SOS: `f[S] = Σ_{T ⊆ S} a[T]`. The bit-i pass adds `f[mask ^ (1<<i)]` when bit i **is** set. Superset SOS: `f[S] = Σ_{T ⊇ S} a[T]`. Same loop, but add `f[mask | (1<<i)]` when bit i **is not** set. They're symmetric under bit-complement.

??? question "8. When does bitmask profile DP beat plain bitmask DP?"
    When the problem is on a 2D grid where one dimension `m` is small (typically `m ≤ 12`) but the other dimension `n` can be large (10³+). The state `dp[row][profile]` is `O(n · 2^m)` instead of `O(2^(n·m))` — practical for grids where the row-wise state captures the "interface" between processed and unprocessed cells.

---

> **Up next in Ultra-Advanced:** Online algorithms & sketches — sliding-window median, Count-Min sketch for heavy-hitters, HyperLogLog for cardinality estimation, and Reservoir sampling for streaming.
