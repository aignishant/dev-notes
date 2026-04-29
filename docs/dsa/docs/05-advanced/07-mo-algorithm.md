# Mo's Algorithm

> The trick that turns "**q range queries on a static array**" into a sequence of **incremental window adjustments**, by reordering the queries cleverly so the window endpoints only ever move `O((n + q) √n)` times **in total**. Each query becomes "add/remove a few elements from the current window," which is far cheaper than recomputing from scratch. Net: **O((n + q) √n)** offline range queries with cheap insert/delete.

<span class="phase-status phase-done">Phase 6 — Advanced</span>

---

## 📖 What is Mo's algorithm?

You have a static array of `n` elements and `q` offline range queries `(l, r)` asking some aggregate over `arr[l..r]` — for example, "how many distinct values?" or "sum of squares of frequencies?" The aggregate has **no easy associative merge** (otherwise you'd reach for a segment tree or BIT) but it **does** support cheap incremental updates: add one element to the window in O(1) (or O(log n)), remove one in the same.

Mo's algorithm processes the queries in a non-obvious order so that across all `q` queries, the **total number of window-endpoint moves is O((n + q) √n)**. With O(1) add/remove, total work is O((n + q) √n).

The reorder: bucket queries by `l // √n`. Inside a bucket, sort by `r` (alternate ascending/descending in odd/even buckets — the "Hilbert" variant). Then sweep two pointers `cur_l, cur_r` over the queries in this order, adjusting the window one element at a time and recording the answer per query.

The mental model: queries are points `(l, r)` in 2D; the naive order traces a chaotic path of total length up to O(qn). Mo's reorder traces a path of length O((n + q) √n) — the optimal trade-off between bucket width (`r` movement within a bucket) and bucket count (`l` movement across buckets).

!!! tip "The signal — when to reach for Mo's"
    Reach for it when:

    - The array is **static** (no updates in the query stream — or use Mo-with-updates).
    - All queries are **available offline** — you can read them all before answering.
    - The aggregate has a **cheap add/remove** (O(1) or O(log n)) but no clean associative merge.
    - The query count is large (`q ≥ √n`) and you can afford O((n + q) √n).
    - The aggregate involves **counts/frequencies/distinct values/mode** — classic Mo territory.

    Don't reach for it when:

    - The aggregate has an associative merge (sum, min, max, gcd) — segment tree wins.
    - Queries arrive online (you must answer each before seeing the next) — Mo's needs all queries upfront.
    - `q` is tiny (`q << √n`) — naive recompute is faster.
    - Updates are interleaved with queries — vanilla Mo's breaks; reach for Mo-with-updates (O(n^(5/3))).

---

## 🧩 The four flavors

### Flavor 1: Vanilla Mo's — sqrt-bucket sort

The textbook form. Each query is `(l, r, idx)`; sort by `(l // B, r)` where `B = √n`. Sweep two pointers, calling `add` / `remove` on each step.

```python
def mo_algorithm(arr: list[int], queries: list[tuple[int, int]]) -> list[int]:
    """Process q range queries on a static array with O(1) add/remove."""
    n = len(arr)
    block = max(1, int(n ** 0.5))                                 # bucket width B = √n
    q = len(queries)
    indexed = sorted(
        range(q),
        key=lambda i: (queries[i][0] // block, queries[i][1])     # bucket by l, sort by r within bucket
    )

    cur_l, cur_r = 0, -1                                          # window is currently empty: arr[0..-1]
    freq = [0] * (max(arr) + 1)                                   # state: frequency table
    distinct = 0                                                  # the running aggregate (e.g. # distinct)

    def add(x: int) -> None:
        nonlocal distinct
        if freq[x] == 0:
            distinct += 1
        freq[x] += 1

    def remove(x: int) -> None:
        nonlocal distinct
        freq[x] -= 1
        if freq[x] == 0:
            distinct -= 1

    ans = [0] * q
    for i in indexed:
        l, r = queries[i]
        while cur_r < r: cur_r += 1; add(arr[cur_r])              # extend right
        while cur_l > l: cur_l -= 1; add(arr[cur_l])              # extend left
        while cur_r > r: remove(arr[cur_r]); cur_r -= 1           # shrink right
        while cur_l < l: remove(arr[cur_l]); cur_l += 1           # shrink left
        ans[i] = distinct
    return ans
```

The four `while` loops **must be in the right order**: extend before shrink, otherwise you may temporarily make `cur_l > cur_r + 1` and the `freq` decrement would underflow. Extending first guarantees the window stays non-empty during the transition.

### Flavor 2: Even/odd snake sort (the hidden constant-factor win)

Sorting strictly by `(bucket, r)` makes `cur_r` jump from the right edge back to the left of the next bucket — a wasted sweep. Sort by `(bucket, r if bucket % 2 == 0 else -r)` so `cur_r` snakes back and forth, halving the average `r` movement in practice.

```python
indexed = sorted(
    range(q),
    key=lambda i: (
        queries[i][0] // block,
        queries[i][1] if (queries[i][0] // block) % 2 == 0 else -queries[i][1],
    )
)
```

Same asymptotic O((n + q) √n), but typically **2× faster** in practice. Always use this in contests.

### Flavor 3: Mo's with updates (the time dimension)

When updates are interleaved with queries, add a **time dimension**: each query carries the count of updates that happened before it. Bucket by `(l // n^(2/3), r // n^(2/3), t)` and sort. Sweep `cur_l`, `cur_r`, *and* `cur_t`; rolling `cur_t` forward applies an update, rolling back undoes it. Total complexity: **O(n^(5/3))**.

```python
def mo_with_updates(arr: list[int], queries: list[tuple], updates: list[tuple]) -> list[int]:
    """queries[i] = (l, r, t, idx) where t = updates seen before this query.
       updates[j] = (pos, new_val) — apply to a copy of arr, with rollback support."""
    n = len(arr)
    block = max(1, int(n ** (2/3)))                               # bucket width n^(2/3)
    arr = arr[:]                                                  # mutate a copy
    indexed = sorted(
        range(len(queries)),
        key=lambda i: (queries[i][0] // block, queries[i][1] // block, queries[i][2])
    )
    cur_l, cur_r, cur_t = 0, -1, 0
    # ... add / remove / apply_update / rollback_update on cur_t crossing ...
```

Used in Codeforces problems like *"DZY Loves Fibonacci with point updates"*. Much heavier — only reach for it when no online structure works.

### Flavor 4: Mo's on tree (path queries via Euler tour)

Path queries on a static tree become a 1D Mo's problem if you flatten via the **Euler tour with first/last occurrence** trick. Each node appears twice in the tour (entry + exit). A path query `(u, v)` becomes a window query on the tour: include nodes appearing exactly once (those are on the path), exclude nodes appearing twice. Then run vanilla Mo's on the flattened sequence with a custom add/remove that toggles inclusion.

```python
# Pseudocode sketch — full implementation is ~80 lines
def mo_on_tree(n: int, adj: list[list[int]], values: list[int], queries: list[tuple[int, int]]):
    tour, first, last = euler_tour_with_lca(adj, root=0)          # length 2n
    on = [False] * n
    def toggle(node: int) -> None:
        if on[node]: remove(values[node])
        else: add(values[node])
        on[node] = not on[node]
    # Map (u, v) → (l, r) on tour, run Mo's with `toggle` instead of add/remove.
```

Used for "distinct colors on path between u and v" — there's no segment-tree-friendly merge for distinct counts on tree paths.

---

## 🔍 Sub-pattern at-a-glance

| # | Variant                | Bucket width         | Total moves         | When to use                                           |
|---|------------------------|----------------------|----------------------|-------------------------------------------------------|
| 1 | Vanilla Mo's           | `√n`                 | `O((n + q) √n)`      | Static array, offline queries, cheap add/remove       |
| 2 | Even/odd snake sort    | `√n`                 | Same — better const  | Always. Free 2× speedup over vanilla                  |
| 3 | Mo's with updates      | `n^(2/3)`            | `O(n^(5/3))`         | Interleaved point updates between queries             |
| 4 | Mo's on tree           | `√(2n)` on Euler tour| `O((n + q) √n)`      | Path queries with no associative merge                |
| 5 | Hilbert-curve Mo's     | implicit             | Similar              | Theoretical optimal; rarely needed in practice        |
| 6 | Mo's with rollback     | `√n`                 | `O((n + q) √n)`      | Aggregates that have add but no easy remove (only L↑) |

---

## 📚 20 problems where Mo's is the canonical answer

| #  | Source / ID    | Problem                                       | Difficulty | Key insight                                                         |
|----|----------------|-----------------------------------------------|------------|---------------------------------------------------------------------|
| 1  | SPOJ DQUERY    | Distinct values in subarray `[l, r]`          | Easy       | The textbook Mo's example. Frequency table + distinct counter.      |
| 2  | CF 86D         | "Powerful Array" — sum of `cnt²·v` per range  | Medium     | Add: `delta = (2·cnt+1)·v`; remove: `delta = -(2·cnt-1)·v`.         |
| 3  | SPOJ FREQUENT  | Most frequent value in `[l, r]`               | Hard       | Maintain reverse-index "count → set of values" for O(√n) mode.      |
| 4  | CF 220B        | "Funny Numbers" — count `arr[i] == cnt[arr[i]]` | Medium   | Add: check post-add; remove: check post-remove against new count.   |
| 5  | LC 327         | Count of range sum in `[low, high]`           | Hard       | Prefix sums + Mo's on the prefix-sum array via offset queries.      |
| 6  | LC 992         | Subarrays with K different integers           | Hard       | Two-pointer sliding wins, but Mo's also solves it cleanly.          |
| 7  | CF 617E        | XOR-prefix queries, count pairs with XOR = k  | Hard       | Frequency table on prefix XOR; add xors `cnt[p ^ k]`.               |
| 8  | SPOJ KATHTHI   | "Kth smallest in range"                       | Hard       | Mo's + Fenwick over compressed values for O(n √n log n).            |
| 9  | CF 375D        | "Tree and Queries" — count colors with cnt ≥ k| Hard       | Mo's on tree (Euler tour) + bucket by frequency value.              |
| 10 | CF 191F        | "Anti-cheating system" — distinct counts      | Medium     | Standard Mo's distinct count.                                       |
| 11 | SPOJ ADAUNCLE  | Pairs `(i, j)` in range with `arr[i] = arr[j]`| Medium     | Add: `delta = cnt[v]`; remove: `delta = -(cnt[v]-1)`.               |
| 12 | CF 940F        | "Machine Learning" — mex of frequencies       | Hard       | Mo's with updates (n^(5/3)). Track frequency-of-frequencies.        |
| 13 | CF 351D        | "Jeff and Removing Periodicity" — XOR queries | Hard       | Mo's on a compressed XOR-prefix array.                              |
| 14 | LightOJ 1188   | Distinct values in `[l, r]`                   | Easy       | Same as DQUERY. Good warmup.                                        |
| 15 | CF 633H        | "Fibonacci-ish" — minimum number to add       | Hard       | Mo's with mathematical post-processing per query.                   |
| 16 | SPOJ COT2      | Count distinct on tree path `(u, v)`          | Hard       | Mo's on tree — the canonical path-distinct problem.                 |
| 17 | CF 86D variant | Sum of cubes of frequencies                   | Medium     | Same template as #2; extend the delta formula.                      |
| 18 | CSES 1734      | "Distinct Values Queries"                     | Easy       | Persistent seg tree wins, but Mo's is a clean alternate.            |
| 19 | CF 803F        | "Coprime Subsequences" — gcd-related queries  | Hard       | Mo's + Mobius / inclusion-exclusion. Classic hybrid.                |
| 20 | CF 786C        | "Till I Collapse" — segment counts            | Hard       | Mo's-style amortisation with binary search per partition.           |

---

## 🔬 Deep-dive 1 — Why bucket width `√n` is optimal

This is the question every interviewer asks: *"Where does the √n come from?"*

Let bucket width be `B`. There are `n / B` buckets. Inside one bucket:

- All queries share the same bucket for `l`, so `cur_l` moves **at most B per query** (within-bucket l-movement).
- Queries are sorted by `r`, so `cur_r` increases monotonically — **at most n total per bucket**.

Across `q` queries:

- **`cur_l` total movement:** `q · B` (each query contributes at most B of l-movement, possibly more across bucket boundaries — see below).
- **`cur_r` total movement:** `(n / B) · n = n² / B` (n per bucket × n / B buckets in the worst case).
- **Bucket boundary `cur_l` jumps:** at each bucket boundary `cur_l` may jump by up to n. There are n / B boundaries, contributing at most `n · n / B = n² / B` extra l-movement.

Total: **`q·B + n²/B`**. Minimise over `B`: take derivative w.r.t. `B`, set to zero → `q = n²/B²` → **`B = n / √q`**. When `q ≈ n`, this collapses to **`B = √n`**.

Plugging back in: total moves `= q · √n + n² / √n = q√n + n√n = (n + q) √n`. **That's the bound.**

The trade-off is **physical**: smaller buckets mean less l-movement per query but more bucket boundaries (more r-rewinds); larger buckets mean fewer boundaries but more l-movement per query. The sweet spot is exactly when the two costs balance.

??? tip "Why not just sort by `(l, r)` directly?"
    Sorting by `(l, r)` lexicographically gives O(n) movement on `cur_l` total but O(qn) on `cur_r` worst case (each query may move `cur_r` from 0 to n if `l` increased by 1). The bucket trick deliberately *gives up* perfect `cur_l` ordering to bound `cur_r` per-bucket — total cost goes from O(qn) to O((n + q)√n).

??? tip "What if `q` and `n` are very different?"
    Use `B = n / √q` instead of `√n`. For `q << n` this gives larger buckets (less l-movement per query is irrelevant when q is small); for `q >> n` it gives smaller buckets. Most contest writeups use `B = √n` as a "good enough" default — the optimum changes the constant, not the asymptotic.

---

## 🔬 Deep-dive 2 — SPOJ DQUERY full walkthrough

**Problem:** array of `n ≤ 30000` elements, `q ≤ 200000` queries asking *"how many distinct values in `arr[l..r]`?"*

**Why Mo's:** "distinct count" has no associative merge — segment tree won't help. But add (one element) is O(1): if `freq[x] == 0` before, distinct goes up. Remove is O(1) symmetrically. Perfect Mo's setup.

Concrete trace on `arr = [1, 1, 2, 1, 3, 2, 4]`, `n = 7`, `B = √7 ≈ 2`:

| Query | (l, r) | Bucket of l | Sort key      |
|-------|--------|-------------|---------------|
| Q0    | (0, 4) | 0           | (0, 4)        |
| Q1    | (1, 1) | 0           | (0, 1)        |
| Q2    | (2, 6) | 1           | (1, 6)        |
| Q3    | (5, 6) | 2           | (2, 6)        |
| Q4    | (0, 6) | 0           | (0, 6)        |

Sort by key: Q1(0,1), Q0(0,4), Q4(0,6), Q2(2,6), Q3(5,6).

Sweep:

1. **Q1 (0,1):** start `cur_l=0, cur_r=-1`. Extend right to 1: add `arr[0]=1` (distinct=1), add `arr[1]=1` (no change, distinct=1). **ans[1] = 1.**
2. **Q0 (0,4):** extend right to 4: add `arr[2]=2` (distinct=2), add `arr[3]=1` (no change), add `arr[4]=3` (distinct=3). **ans[0] = 3.**
3. **Q4 (0,6):** extend right to 6: add `arr[5]=2` (no change), add `arr[6]=4` (distinct=4). **ans[4] = 4.**
4. **Q2 (2,6):** shrink left to 2: remove `arr[0]=1` (freq[1] 3→2, no change), remove `arr[1]=1` (freq[1] 2→1, no change). **ans[2] = 4.**
5. **Q3 (5,6):** shrink left to 5: remove `arr[2]=2` (freq[2] 2→1), remove `arr[3]=1` (freq[1] 1→0, distinct=3), remove `arr[4]=3` (freq[3] 1→0, distinct=2). **ans[3] = 2.**

Total `cur_l` movements: 0 + 0 + 0 + 2 + 3 = 5. Total `cur_r` movements: 2 + 3 + 2 + 0 + 0 = 7. Sum = 12 ≈ (7+5)√7 ≈ 32 (loose upper bound). Each move was O(1). Total work: O((n + q) √n).

The key invariant: at every moment, `freq` and `distinct` describe **exactly** the current window `arr[cur_l..cur_r]`. Mo's just amortises *how much you move the window*.

---

## 🔬 Deep-dive 3 — CF 86D "Powerful Array": sum of cnt²·v

**Problem:** for each query `(l, r)`, compute `Σ (count of v in arr[l..r])² · v` over all distinct values v.

The aggregate is **not** distinct-count — but it has a beautiful incremental update:

Let `S = Σ cnt[v]² · v`. When we **add** an element `x`, `cnt[x]` goes from `c` to `c+1`. The contribution from `x` changes from `c² · x` to `(c+1)² · x`. **Delta:** `((c+1)² - c²) · x = (2c + 1) · x`.

Similarly, **remove** `x`: `cnt[x]` from `c` to `c-1`. Delta: `((c-1)² - c²) · x = -(2c - 1) · x = (1 - 2c) · x`.

```python
def powerful_array(arr: list[int], queries: list[tuple[int, int]]) -> list[int]:
    n, q = len(arr), len(queries)
    block = max(1, int(n ** 0.5))
    indexed = sorted(
        range(q),
        key=lambda i: (queries[i][0] // block,
                       queries[i][1] if (queries[i][0] // block) % 2 == 0 else -queries[i][1])
    )
    freq = [0] * (max(arr) + 1)
    cur_l, cur_r, S = 0, -1, 0

    def add(x: int) -> None:
        nonlocal S
        S += (2 * freq[x] + 1) * x                                # (c+1)² - c² = 2c + 1
        freq[x] += 1

    def remove(x: int) -> None:
        nonlocal S
        freq[x] -= 1
        S -= (2 * freq[x] + 1) * x                                # symmetric — note freq is post-decrement

    ans = [0] * q
    for i in indexed:
        l, r = queries[i]
        while cur_r < r: cur_r += 1; add(arr[cur_r])
        while cur_l > l: cur_l -= 1; add(arr[cur_l])
        while cur_r > r: remove(arr[cur_r]); cur_r -= 1
        while cur_l < l: remove(arr[cur_l]); cur_l += 1
        ans[i] = S
    return ans
```

**The pattern:** any aggregate of the form `Σ f(cnt[v], v)` where `f` admits a closed-form delta on `cnt[v] ± 1` is a Mo's candidate. Sum of squares, cubes, `cnt · v`, `cnt · log(v)`, even `Σ v / cnt[v]` — all reduce to the same skeleton with a different `delta` formula in `add` / `remove`.

This is *the* general lesson of Mo's: **find the closed-form delta, then plug into the template.**

---

## 🐛 Common bugs

1. **Wrong loop order in the four `while`s.** Extend (grow window) before shrink (shrink window). Otherwise you can underflow `freq` mid-transition (the window briefly becomes inverted).
2. **`cur_r` initialised to `0` instead of `-1`.** Empty window is `[cur_l, cur_r]` with `cur_r = cur_l - 1`. Starting at `cur_r = 0` means the window already includes `arr[0]` — your first `add` double-counts it.
3. **Forgetting the snake (even/odd) sort.** Loses ~2× constant factor; can TLE in tight problems even though asymptotically fine.
4. **Bucket width B = 0 when `n = 1`.** Always `B = max(1, int(n ** 0.5))`. Division-by-zero in `l // B` otherwise.
5. **Add / remove asymmetry in delta formula.** `add` increments *after* computing delta with old count; `remove` decrements *before* computing delta with new count. Mixing the two orderings introduces off-by-one errors in S.
6. **Indexing the original query order to write `ans`.** Easy to forget — the indexed list shuffles queries; you must write `ans[i] = ...` where `i` is the **original index**, not the sweep position.
7. **Calling `add` / `remove` outside the window's actual arr indices.** When `cur_l > cur_r` (empty window), the four loops should produce zero net calls. Edge case: a query with `l > r` (shouldn't happen but guard if input might have it).
8. **Not pre-allocating `freq`.** Using a `dict` instead of `list` slows by 5–10× in Python. For values up to 10⁶, a list is essential.

---

## 🗣️ Interviewer phrasings to recognize

- "**Q range queries on a static array**, the operation has no obvious merge but it's cheap to update incrementally" → Mo's.
- "**Distinct values** / **mode** / **frequency-of-frequency** in a range" → classic Mo's territory.
- "**Sum of squares** (or cubes) **of frequencies**" → Mo's with closed-form delta in add/remove.
- "**Path queries** on a tree where the operation is *count distinct* or *mode*" → Mo's on tree.
- "Online updates between queries, **no obvious data structure** works" → Mo's with updates (n^(5/3)).
- "Can we afford O(n √n)?" — when an interviewer asks this, they're hinting Mo's.

---

## 🧭 Connections to other patterns

- **[Sliding Window](../04-patterns/01-sliding-window.md)** — Mo's is "sliding window with reordered queries." Same add/remove primitives, just driven by a query order instead of a single sweep.
- **[Segment Trees](03-segment-trees.md)** — the alternative when the operation has an associative merge. Segment tree wins for sum/min/max; Mo's wins for distinct/mode/frequency-of-frequency.
- **[Fenwick Tree (BIT)](04-fenwick-bit.md)** — sometimes used **inside** Mo's: `add` / `remove` updates a BIT and the answer-extraction queries it (Mo's + BIT for "kth smallest in range" → O(n √n log n)).
- **Coordinate compression** — values up to 10⁹ won't fit a `freq` array; compress first.
- **[Heavy-Light Decomposition](06-heavy-light-decomposition.md)** — solves *online* tree path queries with associative merges. Mo's-on-tree solves *offline* tree path queries without an associative merge — the two are complementary, not competitors.
- **Sqrt decomposition (general)** — Mo's is *one specific* application of the √n idea. Other applications: bucketed range updates (precomputed bucket sums + lazy patches), heavy/light point queries, and sqrt-tree.

---

## ✅ Self-check — 8 questions

??? question "1. Where does the `√n` bucket width come from — derive it."
    Total work = `q·B` (l-movement per query) + `n²/B` (r-rewinds across n/B buckets, each up to n long). Minimise w.r.t. B: derivative gives `B = n/√q`. When `q ≈ n`, `B = √n`. Plugging back: total = `(n + q)√n`.

??? question "2. Why does Mo's require all queries to be available offline?"
    The reorder needs to know all `(l, r)` pairs at once to bucket-sort them. If queries arrived online, you couldn't reorder — and the amortised bound only holds for the specific sorted order.

??? question "3. What's the right order of the four `while` loops, and why?"
    Extend before shrink: `cur_r < r` (extend right), `cur_l > l` (extend left), `cur_r > r` (shrink right), `cur_l < l` (shrink left). Extending first prevents the window from briefly inverting during transitions, which would underflow your frequency table.

??? question "4. Why does the snake sort (even/odd reverse on r) help even though it's the same asymptotic?"
    Without snake: at every bucket boundary, `cur_r` may rewind from the right end of the array back to the start of the next bucket — wasted O(n) per boundary. With snake: `cur_r` continues from where it ended, halving average `r`-movement. Still O((n+q)√n), just a 2× constant-factor win.

??? question "5. When does Mo's *fail* and you should reach for something else?"
    (a) When the operation has an associative merge — segment tree is asymptotically better. (b) When queries are online. (c) When `q << √n` — naive O(qn) is faster. (d) When updates are interleaved — vanilla Mo's breaks; use Mo's with updates (n^(5/3)) or an online structure.

??? question "6. How does Mo's with updates achieve O(n^(5/3))?"
    Three dimensions (l, r, t). Bucket width B = n^(2/3). Across n/B² query-buckets and n updates, total movements work out to n^(5/3). Same minimisation argument as 1D Mo's, just over a 3D path.

??? question "7. Why use a list instead of a dict for the frequency table in Python?"
    Python dict access is ~5–10× slower than list indexing due to hashing overhead and pointer chasing. Mo's does O((n + q) √n) add/remove operations — the constant matters. If values are up to ~10⁶, a list of that size is fine.

??? question "8. What's the trick that flattens a tree into a 1D Mo's sequence?"
    Euler tour with first/last occurrence. Each node appears twice in the tour (entry + exit). For path query (u, v), nodes appearing exactly once in the corresponding tour interval are on the path; nodes appearing twice are not. The `add`/`remove` callback toggles each node's "on path" status, and the inner aggregate works as on a 1D sequence.

---

> **Up next in Advanced:** Treaps & Skip Lists — randomised balanced BSTs from scratch, supporting order-statistics, split/merge, and persistent variants.
