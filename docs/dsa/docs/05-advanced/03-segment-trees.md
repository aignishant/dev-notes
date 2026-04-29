# Segment Trees

> The Swiss army knife of **range queries with point or range updates**. Build a balanced binary tree where each leaf holds one array element and each internal node holds the **aggregate** (sum, min, max, gcd, …) of its subtree's range. Both query and update run in **O(log n)**. Add **lazy propagation** and you can update an entire range in O(log n) too — this is the data structure that powers competitive programming's hardest range problems.

<span class="phase-status phase-inprogress">Phase 6 — Advanced topic (Batch 34)</span>

---

## 📖 What is a segment tree?

A complete (or near-complete) binary tree built on an array of size `n`:

- Each **leaf** corresponds to one element of the input array.
- Each **internal node** stores the aggregate (sum, min, max, …) of the elements in its subtree's range.
- The root covers the entire array `[0, n-1]`.

The tree's structure is fixed by `n`. A node covering `[l, r]` has:

- Left child covering `[l, mid]` where `mid = (l + r) / 2`.
- Right child covering `[mid+1, r]`.

Two core operations:

- **`update(i, val)`** — change `arr[i]` to `val`. Walk from the root to the leaf for index `i`, updating aggregates on the way back up. **O(log n)**.
- **`query(ql, qr)`** — return the aggregate over `arr[ql..qr]`. Recurse from the root, taking each node's stored value when its range is **fully inside** `[ql, qr]`, recursing into children when **partially overlapping**, returning the identity element (0 for sum, +∞ for min, …) when **disjoint**. **O(log n)**.

The mental model: a **divide-and-conquer cache for range queries**. Every range query decomposes into O(log n) precomputed pieces — the segments that exactly tile the query range.

**Lazy propagation** extends update to entire ranges. Instead of touching every leaf in the range, mark internal nodes with a "pending update" tag and apply it when (and only when) you next visit children. Range updates become O(log n) too.

!!! tip "The signal — when to reach for a segment tree"
    Reach for it when:

    - "Range query (sum / min / max / gcd / xor) **with point updates**." → vanilla segment tree.
    - "**Range update** (add / set / multiply) **and range query**." → segment tree with **lazy propagation**.
    - The aggregate is **associative** (sum, min, max, gcd, xor, matrix product, polynomial). Non-associative aggregates don't fit.
    - Queries and updates **interleave** — pure batch problems often have simpler solutions (prefix sums, sweep).
    - "**Kth smallest in a range**" / "count elements ≤ x in range" → merge-sort tree or persistent segment tree (variants).

    Don't reach for it when:

    - Only point queries — an array is enough.
    - Only range queries on a static array — prefix sums (or sparse table for min/max) is simpler and faster constant-factor.
    - Only **prefix** range updates and **point** queries — Fenwick tree is half the code.
    - The aggregate isn't associative — no segment tree saves you.

---

## 🧩 The four flavors

### Flavor 1: Recursive segment tree (the textbook form)

The most readable, easiest to derive, easiest to extend. Slightly more memory than the iterative form.

```python
class SegTree:
    """Range sum, point update."""
    def __init__(self, arr: list[int]) -> None:
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)                            # (1) safe upper bound on tree size
        if self.n:
            self._build(arr, 1, 0, self.n - 1)

    def _build(self, arr: list[int], node: int, l: int, r: int) -> None:
        if l == r:
            self.tree[node] = arr[l]
            return
        mid = (l + r) // 2
        self._build(arr, 2 * node, l, mid)
        self._build(arr, 2 * node + 1, mid + 1, r)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def update(self, i: int, val: int) -> None:
        self._update(1, 0, self.n - 1, i, val)

    def _update(self, node: int, l: int, r: int, i: int, val: int) -> None:
        if l == r:
            self.tree[node] = val
            return
        mid = (l + r) // 2
        if i <= mid:
            self._update(2 * node, l, mid, i, val)
        else:
            self._update(2 * node + 1, mid + 1, r, i, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def query(self, ql: int, qr: int) -> int:
        return self._query(1, 0, self.n - 1, ql, qr)

    def _query(self, node: int, l: int, r: int, ql: int, qr: int) -> int:
        if qr < l or r < ql:                                      # (2) disjoint — return identity (0 for sum)
            return 0
        if ql <= l and r <= qr:                                   # (3) fully inside — return stored
            return self.tree[node]
        mid = (l + r) // 2
        return self._query(2 * node, l, mid, ql, qr) + self._query(2 * node + 1, mid + 1, r, ql, qr)
```

1. The tree array is sized `4n` to safely accommodate any non-power-of-2 `n`. Tighter bound is `2 * next_pow2(n)`, but `4n` is the bullet-proof default.
2. **Disjoint case**: the node's range and the query range don't overlap. Contribute the identity element (0 for sum, ∞ for min, -∞ for max).
3. **Fully-contained case**: the node's range is entirely within the query range. Return the precomputed aggregate.

For partial overlap, recurse into both children and combine.

**Examples:** Range Sum Query - Mutable (LC 307), Count of Smaller Numbers After Self (LC 315).

### Flavor 2: Iterative segment tree (a.k.a. "non-recursive segment tree")

Half the code, slightly less intuitive, no recursion overhead. Common in competitive programming.

```python
class SegTreeIter:
    """Range sum, point update — iterative."""
    def __init__(self, arr: list[int]) -> None:
        self.n = len(arr)
        self.tree = [0] * (2 * self.n)
        for i, x in enumerate(arr):
            self.tree[self.n + i] = x                             # (1) leaves go in the second half
        for i in range(self.n - 1, 0, -1):
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]

    def update(self, i: int, val: int) -> None:
        i += self.n
        self.tree[i] = val
        i //= 2
        while i:
            self.tree[i] = self.tree[2 * i] + self.tree[2 * i + 1]
            i //= 2

    def query(self, ql: int, qr: int) -> int:
        """Inclusive [ql, qr]."""
        res = 0
        ql += self.n
        qr += self.n + 1                                          # (2) convert to half-open [ql, qr)
        while ql < qr:
            if ql & 1:                                            # (3) ql is a right child — take and move right
                res += self.tree[ql]
                ql += 1
            if qr & 1:                                            # (4) qr is a right child — exclusive, move left and take
                qr -= 1
                res += self.tree[qr]
            ql //= 2
            qr //= 2
        return res
```

1. The tree is laid out so leaves sit at indices `[n, 2n)` and internal node `i` has children `2i, 2i+1`. No padding to power-of-2 needed.
2. Convert closed interval to half-open to make the loop conditions clean.
3. If `ql` is odd, it's a *right* child — its parent's range extends below the query, so take this node's value directly and move to the next sibling.
4. Mirror logic for `qr`. Decrement first because `qr` is exclusive.

**Why use it:** ~2× faster constant factor, half the code, but harder to extend to lazy propagation.

### Flavor 3: Lazy propagation (range update + range query)

The killer feature. Range updates in O(log n) by deferring work.

```python
class SegTreeLazy:
    """Range add + range sum, recursive."""
    def __init__(self, n: int) -> None:
        self.n = n
        self.tree = [0] * (4 * n)
        self.lazy = [0] * (4 * n)                                 # (1) pending "add x to all in this range"

    def _push(self, node: int, l: int, r: int) -> None:
        if self.lazy[node]:
            mid = (l + r) // 2
            left, right = 2 * node, 2 * node + 1
            add = self.lazy[node]
            self.tree[left] += add * (mid - l + 1)                # (2) push to children: update their aggregates
            self.lazy[left] += add
            self.tree[right] += add * (r - mid)
            self.lazy[right] += add
            self.lazy[node] = 0                                   # (3) cleared at this level

    def update_range(self, ql: int, qr: int, val: int) -> None:
        self._update(1, 0, self.n - 1, ql, qr, val)

    def _update(self, node: int, l: int, r: int, ql: int, qr: int, val: int) -> None:
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self.tree[node] += val * (r - l + 1)
            self.lazy[node] += val                                # (4) defer the per-child update
            return
        self._push(node, l, r)
        mid = (l + r) // 2
        self._update(2 * node, l, mid, ql, qr, val)
        self._update(2 * node + 1, mid + 1, r, ql, qr, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def query_range(self, ql: int, qr: int) -> int:
        return self._query(1, 0, self.n - 1, ql, qr)

    def _query(self, node: int, l: int, r: int, ql: int, qr: int) -> int:
        if qr < l or r < ql:
            return 0
        if ql <= l and r <= qr:
            return self.tree[node]
        self._push(node, l, r)
        mid = (l + r) // 2
        return self._query(2 * node, l, mid, ql, qr) + self._query(2 * node + 1, mid + 1, r, ql, qr)
```

1. `lazy[node]` stores the **pending add** — "every element in this node's range still needs `lazy[node]` added, but I haven't propagated it down yet."
2. When pushing, the child's aggregate is the *number of elements* in its range times the add.
3. After pushing once, this node's `lazy` is zeroed.
4. When the node's range is fully contained in the update range, apply the update *to this node's aggregate* and **defer** the rest by adding to `lazy`. The push happens later, only when forced by a descent.

**Examples:** Range Sum + Range Add (LC 1109 reframed), My Calendar III (LC 732, with coordinate compression).

### Flavor 4: Coordinate compression + segment tree

When indices are sparse but bounded by `10^9`, you can't allocate a tree of size 10^9. Compress to dense indices first.

```python
def compress(values: list[int]) -> dict[int, int]:
    """Return a mapping from each unique value to its rank."""
    return {v: i for i, v in enumerate(sorted(set(values)))}
```

Then build a segment tree over the rank space (size = number of unique values, ≤ number of operations). Most "intervals on the number line" problems use this trick (LC 218 Skyline, LC 732 My Calendar III, LC 850 Rectangle Area II).

---

## 🎒 The eight sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Range sum + point update | The textbook seg tree | LC 307 | Build, update, query each O(log n) |
| 2 | Range min/max + point update | Same shape, different aggregate | LC 239 (with seg-tree solution) | `combine = min` / `max`; identity = ±∞ |
| 3 | Range gcd / xor + point update | Other associative aggregates | LC 1521-style | gcd / xor as the combine |
| 4 | Range update + range query (lazy) | The lazy-propagation flagship | LC 732 / 715 | Push pending updates only on descent |
| 5 | Range assign + range query | "Set this range to v" semantics | LC 715 Range Module | Lazy stores `set` flag, not add |
| 6 | Count smaller / inversions | Order-statistic trick | LC 315, LC 327, LC 493 | Merge-sort tree / Fenwick alt |
| 7 | Coordinate compression | Sparse keys, dense tree | LC 218 Skyline (alt), LC 850 | Map values → ranks before build |
| 8 | Persistent segment tree | Versioned snapshots | LC 1206-flavour | Path-copy on update for k-th-smallest queries |

---

## 📋 Twenty problems on segment trees

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Range Sum Query - Mutable | 307 | <span class="diff-medium">Medium</span> | Range sum + point update | 📝 |
| 2 | Range Sum Query 2D - Mutable | 308 | <span class="diff-hard">Hard</span> | 2D seg tree | 📝 |
| 3 | Count of Smaller Numbers After Self | 315 | <span class="diff-hard">Hard</span> | Count smaller | 📝 |
| 4 | Reverse Pairs | 493 | <span class="diff-hard">Hard</span> | Count inversions w/ doubled | 📝 |
| 5 | Count of Range Sum | 327 | <span class="diff-hard">Hard</span> | Range sum + count | 📝 |
| 6 | The Skyline Problem | 218 | <span class="diff-hard">Hard</span> | Sweep + max-seg | 📝 |
| 7 | My Calendar III | 732 | <span class="diff-hard">Hard</span> | Lazy + max | 📝 |
| 8 | Range Module | 715 | <span class="diff-hard">Hard</span> | Range assign | 📝 |
| 9 | Falling Squares | 699 | <span class="diff-hard">Hard</span> | Lazy max + compression | 📝 |
| 10 | Rectangle Area II | 850 | <span class="diff-hard">Hard</span> | Sweep + interval seg | 📝 |
| 11 | Number of Longest Increasing Subseq | 673 | <span class="diff-medium">Medium</span> | Seg tree alt to DP | 📝 |
| 12 | Longest Substring of One Repeating Character | 2213 | <span class="diff-hard">Hard</span> | Seg tree storing 5-tuples per node | 📝 |
| 13 | Longest Increasing Subsequence II | 2407 | <span class="diff-hard">Hard</span> | Seg tree on value space | 📝 |
| 14 | Booking Concert Tickets in Groups | 2286 | <span class="diff-hard">Hard</span> | Lazy + descent search | 📝 |
| 15 | Range Frequency Queries | 2080 | <span class="diff-medium">Medium</span> | Per-leaf hash, no real seg tree (cousin) | 📝 |
| 16 | Handling Sum Queries After Update | 2569 | <span class="diff-hard">Hard</span> | Lazy XOR-style flip | 📝 |
| 17 | Maximum Sum BIT (cousin) | 1109 | <span class="diff-medium">Medium</span> | Lazy-add range / point query | 📝 |
| 18 | Distance to Add Queries | — (CF) | <span class="diff-medium">Medium</span> | Persistence | 📝 |
| 19 | K-th Smallest in Subarray | — (CF / OI) | <span class="diff-hard">Hard</span> | Merge-sort tree / persistent | 📝 |
| 20 | Maximum Frequency After Subarray | 2382-style | <span class="diff-hard">Hard</span> | Seg tree + frequency | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Range Sum Query Mutable (LC 307)

> Implement `update(i, val)` and `sumRange(l, r)` on an array, both in O(log n).

#### Code (re-stated, recursive form)

```python
class NumArray:
    def __init__(self, nums: list[int]) -> None:
        self.n = len(nums)
        self.tree = [0] * (4 * self.n)
        if self.n:
            self._build(nums, 1, 0, self.n - 1)

    def _build(self, nums, node, l, r):
        if l == r:
            self.tree[node] = nums[l]
            return
        mid = (l + r) // 2
        self._build(nums, 2 * node, l, mid)
        self._build(nums, 2 * node + 1, mid + 1, r)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def update(self, i: int, val: int) -> None:
        self._update(1, 0, self.n - 1, i, val)

    def _update(self, node, l, r, i, val):
        if l == r:
            self.tree[node] = val
            return
        mid = (l + r) // 2
        if i <= mid:
            self._update(2 * node, l, mid, i, val)
        else:
            self._update(2 * node + 1, mid + 1, r, i, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def sumRange(self, l: int, r: int) -> int:
        return self._query(1, 0, self.n - 1, l, r)

    def _query(self, node, l, r, ql, qr):
        if qr < l or r < ql:
            return 0
        if ql <= l and r <= qr:
            return self.tree[node]
        mid = (l + r) // 2
        return self._query(2 * node, l, mid, ql, qr) + self._query(2 * node + 1, mid + 1, r, ql, qr)
```

#### Tree layout for `nums = [1, 3, 5, 7, 9, 11]` (`n = 6`)

The tree array is sized `4 × 6 = 24`. The root (node 1) covers `[0, 5]`.

```
                        node 1: [0,5] sum=36
                  /                              \
        node 2: [0,2] sum=9                  node 3: [3,5] sum=27
        /              \                      /              \
  node 4: [0,1] sum=4   node 5: [2,2]=5  node 6: [3,4] sum=16  node 7: [5,5]=11
   /            \                          /            \
 node 8=1   node 9=3                  node 12=7    node 13=9
```

Internal node ids follow the standard `2*node`, `2*node + 1` convention; leaves are wherever the recursion terminates.

#### Query `sumRange(1, 4)` walked

Start at node 1 covering `[0, 5]`, query `[1, 4]`:

- Partial overlap → recurse into both children.
  - Node 2 covers `[0, 2]`, query `[1, 4]`. Partial overlap.
    - Node 4 covers `[0, 1]`, query `[1, 4]`. Partial overlap.
      - Node 8 covers `[0, 0]`, query `[1, 4]`. **Disjoint** → return 0.
      - Node 9 covers `[1, 1]`, query `[1, 4]`. **Fully contained** → return 3.
      - Combine: 3.
    - Node 5 covers `[2, 2]`, query `[1, 4]`. **Fully contained** → return 5.
    - Combine: 3 + 5 = 8.
  - Node 3 covers `[3, 5]`, query `[1, 4]`. Partial overlap.
    - Node 6 covers `[3, 4]`, query `[1, 4]`. **Fully contained** → return 16.
    - Node 7 covers `[5, 5]`, query `[1, 4]`. **Disjoint** → return 0.
    - Combine: 16.
  - Combine: 8 + 16 = 24.

Output: 24 = 3 + 5 + 7 + 9. ✓

The query touched 5 leaves out of 6, but only 4 *internal* "fully-contained" stops were made. In general, a query of length `k` touches O(log n) fully-contained nodes plus O(log n) recursion overhead.

#### Update `update(3, 10)` (change `nums[3]` from 7 to 10)

Walk from root to leaf 12:

- Node 1 `[0, 5]`: `i=3 > mid=2`, go right.
- Node 3 `[3, 5]`: `i=3 ≤ mid=4`, go left.
- Node 6 `[3, 4]`: `i=3 ≤ mid=3`, go left.
- Node 12 `[3, 3]`: leaf. Set `tree[12] = 10`.

Then unwind, recomputing each parent's aggregate:

- Node 6: `tree[12] + tree[13] = 10 + 9 = 19`.
- Node 3: `tree[6] + tree[7] = 19 + 11 = 30`.
- Node 1: `tree[2] + tree[3] = 9 + 30 = 39`.

Total work: O(log n) = ~3 cells updated.

#### Why `4 × n` for the tree array

For arbitrary `n`, the recursion can produce up to `2 × next_pow2(n)` nodes. `next_pow2(n)` ≤ `2n`, so `2 × 2n = 4n` is a safe over-allocation. Tighter bounds are possible (`2 × next_pow2(n) - 1`) but `4n` is the bullet-proof rule of thumb everyone uses.

#### Complexity

- **Time:** O(n) build, O(log n) update, O(log n) query.
- **Space:** O(n) (tree array is 4n at most).

---

### Deep-dive 2 — Lazy Propagation: Range Add + Range Sum

> Maintain an array supporting `add(l, r, x)` (add `x` to every element in `[l, r]`) and `sum(l, r)` (sum of `[l, r]`). Both in O(log n).

This is the canonical lazy-propagation problem. Without lazy, range add would be O(n).

#### The lazy idea, in one sentence

When an update fully covers a node's range, **don't recurse into children** — apply the update to the node's aggregate and store the pending update in a `lazy[node]` tag. Only push the tag to children when you next descend into them.

#### Code (re-stated)

```python
class SegTreeLazy:
    def __init__(self, n: int) -> None:
        self.n = n
        self.tree = [0] * (4 * n)
        self.lazy = [0] * (4 * n)

    def _push(self, node: int, l: int, r: int) -> None:
        if self.lazy[node]:
            mid = (l + r) // 2
            add = self.lazy[node]
            left, right = 2 * node, 2 * node + 1
            self.tree[left] += add * (mid - l + 1)
            self.lazy[left] += add
            self.tree[right] += add * (r - mid)
            self.lazy[right] += add
            self.lazy[node] = 0

    def update_range(self, ql: int, qr: int, val: int) -> None:
        self._update(1, 0, self.n - 1, ql, qr, val)

    def _update(self, node, l, r, ql, qr, val):
        if qr < l or r < ql:
            return
        if ql <= l and r <= qr:
            self.tree[node] += val * (r - l + 1)
            self.lazy[node] += val
            return
        self._push(node, l, r)
        mid = (l + r) // 2
        self._update(2 * node, l, mid, ql, qr, val)
        self._update(2 * node + 1, mid + 1, r, ql, qr, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def query_range(self, ql: int, qr: int) -> int:
        return self._query(1, 0, self.n - 1, ql, qr)

    def _query(self, node, l, r, ql, qr):
        if qr < l or r < ql:
            return 0
        if ql <= l and r <= qr:
            return self.tree[node]
        self._push(node, l, r)
        mid = (l + r) // 2
        return self._query(2 * node, l, mid, ql, qr) + self._query(2 * node + 1, mid + 1, r, ql, qr)
```

#### Walking through a small lazy example

Start: array `[0, 0, 0, 0, 0, 0, 0, 0]`, `n = 8`. Tree and lazy both all zeros.

**Update 1:** `add(0, 3, 5)`.

- Node 1 `[0, 7]`: partial overlap, push (lazy is 0, no work), recurse.
  - Node 2 `[0, 3]`: **fully contained** → `tree[2] += 5 * 4 = 20`, `lazy[2] += 5`.
  - Node 3 `[4, 7]`: disjoint → return 0.
- Combine: `tree[1] = tree[2] + tree[3] = 20 + 0 = 20`.

State: `tree[1]=20, tree[2]=20`, `lazy[2]=5`. Children of node 2 still hold zeros — the work is **deferred**.

**Query 1:** `sum(2, 5)`.

- Node 1 `[0, 7]`: partial, push (lazy=0, nothing). Recurse.
  - Node 2 `[0, 3]`: partial. **Push**: `lazy[2]=5` propagates → `tree[4] += 5*2=10, lazy[4]+=5; tree[5] += 5*2=10, lazy[5]+=5; lazy[2]=0`. Recurse.
    - Node 4 `[0, 1]`: disjoint → 0.
    - Node 5 `[2, 3]`: fully contained → return `tree[5] = 10`.
    - Combine: 10.
  - Node 3 `[4, 7]`: partial, push (lazy=0). Recurse.
    - Node 6 `[4, 5]`: fully contained → return `tree[6] = 0`.
    - Node 7 `[6, 7]`: disjoint → 0.
    - Combine: 0.
- Combine: 10 + 0 = 10.

Output: 10 = 5 + 5 (positions 2 and 3). ✓ Position 4 and 5 still hold 0.

#### Why the per-child contribution is `add × range_size`

When you push `add` down to a child, that child's range has `range_size` elements, each gaining `add`. The aggregate (sum) gains `add × range_size`. Forgetting the multiplier is the most common lazy-prop bug.

For range-min or range-max with range-add, the multiplier is just `add` (the min/max shifts uniformly). The multiplier rule is **aggregate-specific**.

#### Complexity

- **Time:** O(log n) per update and query (each touches O(log n) nodes).
- **Space:** O(n) tree + O(n) lazy.

---

### Deep-dive 3 — Count of Smaller Numbers After Self (LC 315)

> For each `nums[i]`, count how many `nums[j]` with `j > i` are smaller. Return the array of counts.

A textbook "order-statistics over a range" problem. Three good solutions: merge-sort with counting, Fenwick tree on compressed values, **segment tree on compressed values** (this section).

#### The plan

1. **Compress** the input to ranks (e.g., `[5, 2, 6, 1] → [2, 1, 3, 0]`).
2. Build a segment tree over the rank space, all zeros, where `tree[i]` will store "how many times rank `i` has been seen so far."
3. **Iterate from right to left.** For each element `nums[i]` (rank `r`):
   - Query the count of values in `[0, r-1]` (number of smaller values seen so far → that's the count for index `i`).
   - Update: increment the count at rank `r`.

#### Code

```python
def count_smaller(nums: list[int]) -> list[int]:
    """LC 315."""
    if not nums:
        return []

    # 1. Compress
    rank = {v: i for i, v in enumerate(sorted(set(nums)))}
    m = len(rank)

    # 2. Segment tree over rank space
    tree = [0] * (4 * m)

    def update(node: int, l: int, r: int, i: int) -> None:
        if l == r:
            tree[node] += 1
            return
        mid = (l + r) // 2
        if i <= mid:
            update(2 * node, l, mid, i)
        else:
            update(2 * node + 1, mid + 1, r, i)
        tree[node] = tree[2 * node] + tree[2 * node + 1]

    def query(node: int, l: int, r: int, ql: int, qr: int) -> int:
        if qr < l or r < ql or ql > qr:
            return 0
        if ql <= l and r <= qr:
            return tree[node]
        mid = (l + r) // 2
        return query(2 * node, l, mid, ql, qr) + query(2 * node + 1, mid + 1, r, ql, qr)

    # 3. Right-to-left scan
    result = [0] * len(nums)
    for i in range(len(nums) - 1, -1, -1):
        r = rank[nums[i]]
        result[i] = query(1, 0, m - 1, 0, r - 1)
        update(1, 0, m - 1, r)
    return result
```

#### Walking `nums = [5, 2, 6, 1]`

Compression: `{1: 0, 2: 1, 5: 2, 6: 3}`. `m = 4`.

Right-to-left:

- `i = 3`: `nums[3] = 1`, rank 0. Query `[0, -1]` → empty range → 0. Update rank 0. `result = [_,_,_,0]`.
- `i = 2`: `nums[2] = 6`, rank 3. Query `[0, 2]` → 1 (only rank 0 is set). Update rank 3. `result = [_,_,1,0]`.
- `i = 1`: `nums[1] = 2`, rank 1. Query `[0, 0]` → 1 (only rank 0 is set). Update rank 1. `result = [_,1,1,0]`.
- `i = 0`: `nums[0] = 5`, rank 2. Query `[0, 1]` → 2 (rank 0 and rank 1 are set). Update rank 2. `result = [2,1,1,0]`.

Output: `[2, 1, 1, 0]`. ✓

#### Why a segment tree over the value space?

The natural impulse is "segment tree over the array indices." That doesn't work — we need to count *how many values smaller than `x`*, not "what's in this index range." So the tree's index axis is the **compressed value space** instead.

A Fenwick tree solves this same problem in fewer lines of code. The segment-tree form generalises better when the aggregate becomes more complex (e.g., "max value with rank ≤ k", "sum of squares", etc.).

#### Complexity

- **Time:** O(n log n). Sort for compression + O(n) scan, each step O(log n).
- **Space:** O(n) for the tree + O(n) for the rank map.

---

## 🐛 Common bugs

1. **Allocating tree size `2n`.** The tree needs `4n` worst-case (for the recursive form). `2n` only works in the iterative layout where the array is laid out flat.
2. **Forgetting the lazy multiplier for range-sum.** When pushing `add` down, the child's sum gains `add × range_size`, not just `add`. Range-min/max gains `add` flat. Aggregate-specific.
3. **Pushing lazy to children that don't exist.** When the node is a leaf (`l == r`), there are no children to push to. Either skip the push at leaves or guard `_push` with `if l < r`.
4. **Using `combine = max` with identity 0.** If values can be negative, `max(0, …)` silently inflates the answer. Identity for max is `-∞`. Identity for min is `+∞`. Identity for sum is 0. Identity for gcd is 0. Identity for xor is 0. Pick deliberately.
5. **Mutating during iteration.** When walking the tree array iteratively, don't recompute `mid` from outdated `l, r` — pass them in or recompute at every recursion level.
6. **Forgetting that lazy "set" and lazy "add" don't compose trivially.** If you support both range-add and range-set (assign), the lazy tag needs two fields (or a tag type) and the `combine_lazy` logic gets fiddly. Most LC problems pick one.
7. **Coordinate-compressing without preserving boundary semantics.** For interval problems on the number line, the segment tree's "leaves" usually represent **gaps between consecutive distinct values**, not the values themselves. LC 850 Rectangle Area II is the trap.
8. **Recursion depth blowing up Python's stack.** `n = 10^5` builds a tree of depth ~17 — fine. `n = 10^7` is also fine. But adversarial inputs in lazy + nested recursion can exceed defaults; bump `sys.setrecursionlimit(...)` defensively.
9. **`mid = (l + r) // 2` in languages with overflow.** Python is fine. C++/Java need `mid = l + (r - l) // 2` to avoid integer overflow on huge `l + r`.

---

## 🗣️ Interviewer phrasings to recognize

- "**Mutable** range sum / min / max." → vanilla seg tree.
- "**Range update** + range query." → lazy propagation.
- "**Count smaller / inversions**." → seg tree over value space (or merge-sort, or Fenwick).
- "**Skyline** / merging intervals with timestamps." → seg tree on coordinate-compressed range + sweep.
- "**Range frequency** of a target." → seg tree per leaf storing a hash, or per-leaf list with binary search.
- "**Booking concert tickets**." → lazy + descent search (find leftmost leaf satisfying a constraint).
- "**Range XOR-flip** + range sum of bits." → lazy boolean flip propagating sum-of-zeros / sum-of-ones swap.

---

## 🧭 Connections to other patterns

- **Fenwick (Binary Indexed Tree)** — half the code, same O(log n), but only supports prefix queries and point updates natively. Range-add + point-query and range-add + range-sum are achievable with two Fenwick trees, but anything more exotic pushes you back to seg trees.
- **[Merge Intervals](../04-patterns/04-merge-intervals.md)** — sweep-line with seg tree handles "intervals that change over time" (skyline, calendars).
- **[Modified Binary Search](../04-patterns/11-modified-binary-search.md)** — seg-tree descent search ("leftmost leaf with property P") is binary search on a tree instead of an array.
- **[Tries](01-tries.md)** — both are tree DSes, but tries index by characters (per-string), seg trees index by array positions (per-range).
- **Persistent segment tree** — every update creates a *new version* by path-copying the affected log(n) nodes. Powers k-th smallest in a range and historical queries. Ultra-advanced.

---

## ✅ Self-check — 8 questions

??? question "1. Why is the tree array sized 4n in the recursive form?"
    The tree needs at most `2 × next_pow2(n)` nodes; `next_pow2(n) ≤ 2n`, so `4n` is the safe bullet-proof upper bound. Tighter bounds work but `4n` is the universal default.

??? question "2. What's the difference between point-update + range-query (vanilla) and range-update + range-query (lazy)?"
    Vanilla: each update touches one leaf and re-aggregates O(log n) ancestors. Lazy: range updates avoid descending past nodes that are fully contained — instead they update the node's aggregate and store a pending tag (`lazy[node]`). The tag is pushed to children only when those children are next visited. Both query types stay O(log n).

??? question "3. Why does the lazy push for range-sum multiply by `range_size`, but range-max doesn't?"
    Range-sum's aggregate is the sum of all elements in the range. Adding `x` to each element adds `x × range_size` to the sum. Range-max's aggregate is one element; adding `x` to every element shifts the max by exactly `x`. The multiplier rule is aggregate-specific.

??? question "4. When does a Fenwick tree beat a segment tree?"
    When you only need point-update + prefix-query (or its O(log²n) range-update variants). Fenwick is half the code, ~2× faster constant factor, and uses one array instead of two. Seg trees win when the operation is too complex for Fenwick (range-min/max, lazy assign, custom merge-tuples).

??? question "5. How does Count of Smaller Numbers After Self use a seg tree on the value space, not the index space?"
    The query is "count of values smaller than `x`," which is naturally a range query on the *value* axis. Compress values to ranks, then build a seg tree over rank space; `tree[r]` accumulates "how many times rank `r` has been seen." Right-to-left iteration gives "values seen so far" = "values to the right of the current position."

??? question "6. Why does a non-recursive (iterative) seg tree need only `2n` slots while the recursive one needs `4n`?"
    The iterative form lays leaves at indices `[n, 2n)` and internal nodes at `[1, n)` — exactly `2n` slots, no padding to power-of-2 needed for sum/min/max with the standard half-open query loop. The recursive form's `4n` accommodates uneven splits at every level safely.

??? question "7. What's the right identity element for each common aggregate?"
    Sum: 0. Min: `+∞` (or `INT_MAX`). Max: `-∞` (or `INT_MIN`). GCD: 0 (since `gcd(x, 0) = x`). XOR: 0. Multiplication: 1. Boolean AND: True. Boolean OR: False. Pick deliberately — the wrong identity silently corrupts results.

??? question "8. What does 'persistent segment tree' add beyond a normal one?"
    Every update creates a *new version* of the tree by copying only the log(n) nodes on the affected path; old versions remain queryable. Enables "what was the array at time T?" queries, k-th smallest in any subarray (Bryan Chan's wavelet-trie-like trick), and other historical-query problems. Used in competitive programming, rare in interviews.

---

> **Up next in Advanced:** Fenwick (Binary Indexed Tree) — half the code, same asymptotics for prefix-style problems. Then suffix arrays, HLD, Mo's algorithm, and treaps.
