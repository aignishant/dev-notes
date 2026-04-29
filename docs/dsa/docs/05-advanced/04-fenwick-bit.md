# Fenwick Tree (Binary Indexed Tree)

> **Half the code of a segment tree, same O(log n) for prefix problems.** A Fenwick tree (a.k.a. BIT) is the cleanest data structure for "point update + prefix-sum query" — and with the right framing it stretches to range update + point query, range update + range query, and 2D versions. The whole algorithm fits in **eight lines** of Python and the only non-obvious mechanic is the `i & -i` trick (which we already met in [Bitwise XOR](../04-patterns/20-bitwise-xor.md)).

<span class="phase-status phase-done">Phase 6 — Advanced</span>

---

## 📖 What is a Fenwick tree?

A 1-indexed array `bit[1..n]` where `bit[i]` stores the **partial sum** of a specific range ending at index `i`. The range size is determined by the **lowest set bit** of `i`:

- `i = 1 (0b001)` → covers `[1, 1]` (length 1)
- `i = 2 (0b010)` → covers `[1, 2]` (length 2)
- `i = 3 (0b011)` → covers `[3, 3]` (length 1)
- `i = 4 (0b100)` → covers `[1, 4]` (length 4)
- `i = 6 (0b110)` → covers `[5, 6]` (length 2)
- `i = 8 (0b1000)` → covers `[1, 8]` (length 8)

The pattern: `bit[i]` covers `[i - lowbit(i) + 1, i]` where `lowbit(i) = i & -i`. That's the entire structural rule.

Two operations:

- **`prefix_sum(i)`** — sum of `arr[1..i]`. Walk down: `i, i - lowbit(i), …` until 0, summing `bit[*]` at each stop. **O(log n)**.
- **`update(i, delta)`** — add `delta` to `arr[i]`. Walk up: `i, i + lowbit(i), …` until > n, adding `delta` to `bit[*]` at each stop. **O(log n)**.

Range sum `[l, r]` = `prefix_sum(r) - prefix_sum(l - 1)`.

The mental model: imagine the bit-positions of `i` as **levels of detail**. The lowest set bit decides how big a chunk this cell covers. Walking down by clearing the lowest set bit (`i -= i & -i`) decomposes any prefix into ≤ log₂(i) disjoint chunks. Walking up by adding the lowest set bit (`i += i & -i`) propagates an update to every chunk that contains index i.

!!! tip "The signal — when to reach for a Fenwick tree"
    Reach for it when:

    - "**Point update** + **prefix sum / range sum**." → vanilla BIT.
    - "**Count smaller / inversions / 2-sum-after**." → BIT on compressed value space (same as the seg-tree trick, half the code).
    - "Range add + point query" or "range add + range sum" — achievable with one or two BITs and the standard difference-array reframing.
    - You'd reach for a seg tree but the operation is **just sum** (or just XOR). BIT is faster and shorter.

    Don't reach for it when:

    - The aggregate isn't a **group operation** (has an inverse). Sum, XOR, count: yes. Min, max, gcd: no — use a seg tree.
    - You need range-update + range-min/max — the two-BIT difference trick only works for sum.
    - Operations are 2D *and* the data is sparse and huge — 2D BIT is great when dense, painful when sparse (use 2D seg tree or hash + 1D BIT).

---

## 🧩 The four flavors

### Flavor 1: Standard BIT — point update, prefix sum query

The eight-line workhorse.

```python
class Fenwick:
    """1-indexed. bit[0] is unused."""
    def __init__(self, n: int) -> None:
        self.n = n
        self.bit = [0] * (n + 1)                                  # (1) 1-indexed; size n+1

    def update(self, i: int, delta: int) -> None:
        """Add delta to arr[i]. 1-indexed."""
        while i <= self.n:
            self.bit[i] += delta
            i += i & -i                                           # (2) jump up by lowest set bit

    def prefix_sum(self, i: int) -> int:
        """Sum of arr[1..i]. 1-indexed."""
        s = 0
        while i > 0:
            s += self.bit[i]
            i -= i & -i                                           # (3) jump down by lowest set bit
        return s

    def range_sum(self, l: int, r: int) -> int:
        """Sum of arr[l..r]. 1-indexed inclusive."""
        return self.prefix_sum(r) - self.prefix_sum(l - 1)
```

1. **1-indexing is mandatory** — the `i & -i` recurrence depends on `i ≥ 1`. Index 0 is wasted.
2. Update walks up: `i → i + lowbit(i)`. Each step jumps to the next BIT cell whose covered range includes `i`.
3. Query walks down: `i → i - lowbit(i)`. Each step takes one chunk and jumps to the next non-overlapping chunk to its left.

**Examples:** Range Sum Query - Mutable (LC 307), Count of Smaller Numbers After Self (LC 315 via value-space BIT), Reverse Pairs (LC 493).

### Flavor 2: Range update + point query (difference BIT)

The trick: instead of storing the array itself, store the **difference array** `d[i] = arr[i] - arr[i-1]`. Then `arr[i] = sum(d[1..i])` — a prefix sum on the difference array.

```python
class FenwickRangeAdd:
    """Range-add + point-query, via a difference BIT."""
    def __init__(self, n: int) -> None:
        self.bit = Fenwick(n)

    def range_add(self, l: int, r: int, delta: int) -> None:
        """Add delta to arr[l..r]."""
        self.bit.update(l, delta)                                 # (1) +delta at start
        self.bit.update(r + 1, -delta)                            # (2) -delta after end

    def point_query(self, i: int) -> int:
        """Current value of arr[i]."""
        return self.bit.prefix_sum(i)
```

1. Adding `delta` at position `l` in the difference array adds `delta` to `arr[i]` for every `i ≥ l`.
2. Subtracting `delta` at position `r+1` cancels the addition for every `i > r`. Net effect: `+delta` exactly on `[l, r]`.

**Why it works:** the difference array's prefix sum is the original array. So a "single update at index l of the difference array" is a "range update from l to ∞ in the original array."

**Examples:** Online range-add with point queries on a stream of intervals.

### Flavor 3: Range update + range query (two BITs)

Same difference-array idea, but to support range *queries* we need two BITs.

```python
class FenwickRangeRange:
    """Range-add + range-sum via two BITs."""
    def __init__(self, n: int) -> None:
        self.n = n
        self.b1 = Fenwick(n)
        self.b2 = Fenwick(n)

    def _update(self, i: int, delta: int) -> None:
        self.b1.update(i, delta)
        self.b2.update(i, delta * (i - 1))

    def range_add(self, l: int, r: int, delta: int) -> None:
        self._update(l, delta)
        self._update(r + 1, -delta)

    def _prefix_sum(self, i: int) -> int:
        return self.b1.prefix_sum(i) * i - self.b2.prefix_sum(i)

    def range_sum(self, l: int, r: int) -> int:
        return self._prefix_sum(r) - self._prefix_sum(l - 1)
```

The math: derive `arr[k] = sum_{j ≤ k} d[j]` (where `d` is the difference array). Then

```
sum_{k=1..i} arr[k]
  = sum_{k=1..i} sum_{j ≤ k} d[j]
  = sum_{j=1..i} d[j] * (i - j + 1)
  = (i + 1) * sum d[j] − sum j * d[j]
```

So `prefix_sum(i)` = `b1.prefix_sum(i) * (i + 1) - b2.prefix_sum(i)` where `b1` tracks `d` and `b2` tracks `j * d[j]`. (My code stores `delta * (i - 1)` and computes `b1·i - b2`, which is the equivalent algebraic shuffle — pick whichever derivation you remember.)

This is the only "real" math in the BIT family. Most interviews don't push past Flavor 1 + 2.

### Flavor 4: 2D BIT

The natural extension to grids: `bit[i][j]` covers a rectangle `[i - lowbit(i) + 1..i] × [j - lowbit(j) + 1..j]`. Both axes use the same `i & -i` walk.

```python
class Fenwick2D:
    def __init__(self, rows: int, cols: int) -> None:
        self.rows, self.cols = rows, cols
        self.bit = [[0] * (cols + 1) for _ in range(rows + 1)]

    def update(self, r: int, c: int, delta: int) -> None:
        i = r
        while i <= self.rows:
            j = c
            while j <= self.cols:
                self.bit[i][j] += delta
                j += j & -j
            i += i & -i

    def prefix_sum(self, r: int, c: int) -> int:
        s = 0
        i = r
        while i > 0:
            j = c
            while j > 0:
                s += self.bit[i][j]
                j -= j & -j
            i -= i & -i
        return s

    def rect_sum(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle [r1, r2] × [c1, c2]. 1-indexed."""
        return (
            self.prefix_sum(r2, c2)
            - self.prefix_sum(r1 - 1, c2)
            - self.prefix_sum(r2, c1 - 1)
            + self.prefix_sum(r1 - 1, c1 - 1)
        )
```

Update is O(log r · log c). Query is O(log r · log c). The rectangle sum uses 2D inclusion-exclusion on four prefix rectangles.

**Examples:** Range Sum Query 2D - Mutable (LC 308).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Point update + prefix sum | Vanilla BIT | LC 307 | `i & -i` walk up / down |
| 2 | Count smaller / inversions | Order statistics on values | LC 315 | BIT on compressed value space, scan right-to-left |
| 3 | Range add + point query | Difference-array BIT | offline RMQ-style | One BIT, store deltas |
| 4 | Range add + range sum | Two BITs trick | LC 1109-style | b1 stores `d`, b2 stores `j·d` |
| 5 | XOR-prefix queries | Same shape, XOR aggregate | LC 1310-style | XOR has an inverse — fits BIT |
| 6 | 2D rectangles | Grid sum + cell update | LC 308 | Nested `i & -i` walks |
| 7 | K-th smallest in BIT | Binary-search-on-tree | offline order statistics | Walk powers of 2 down; jump if `bit[*]` < k |

---

## 📋 Twenty problems on Fenwick / BIT

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Range Sum Query - Mutable | 307 | <span class="diff-medium">Medium</span> | Point + prefix | 📝 |
| 2 | Range Sum Query 2D - Mutable | 308 | <span class="diff-hard">Hard</span> | 2D BIT | 📝 |
| 3 | Count of Smaller Numbers After Self | 315 | <span class="diff-hard">Hard</span> | Count smaller | 📝 |
| 4 | Reverse Pairs | 493 | <span class="diff-hard">Hard</span> | Inversions w/ doubled | 📝 |
| 5 | Count of Range Sum | 327 | <span class="diff-hard">Hard</span> | BIT on prefix-sum ranks | 📝 |
| 6 | Create Sorted Array Through Instructions | 1649 | <span class="diff-hard">Hard</span> | Two BIT counts (smaller + larger) | 📝 |
| 7 | Queries on a Permutation With Key | 1409 | <span class="diff-medium">Medium</span> | BIT for moving-front simulation | 📝 |
| 8 | Number of Visible People in a Queue | 1944 | <span class="diff-hard">Hard</span> | Monotonic stack alt — BIT not needed but useful comparison | 📝 |
| 9 | Number of Pairs Satisfying Inequality | 2426 | <span class="diff-hard">Hard</span> | BIT on differences | 📝 |
| 10 | Minimum Possible Integer After at Most K Adjacent Swaps | 1505 | <span class="diff-hard">Hard</span> | BIT to track removed positions | 📝 |
| 11 | Constrained Subsequence Sum | 1425 | <span class="diff-hard">Hard</span> | DP + BIT alternative to monotonic deque | 📝 |
| 12 | Sum of Subarrays With Bounded Maximum | 795-style | <span class="diff-medium">Medium</span> | Counting via BIT | 📝 |
| 13 | Booking Concert Tickets in Groups | 2286 | <span class="diff-hard">Hard</span> | Seg tree preferred but BIT fits some sub-queries | 📝 |
| 14 | Process Tasks Using Servers | 1882 | <span class="diff-medium">Medium</span> | Heap problem — BIT for variant counting | 📝 |
| 15 | Number of Submatrices That Sum to Target | 1074 | <span class="diff-medium">Medium</span> | 2D prefix sums (cousin of 2D BIT) | 📝 |
| 16 | Maximum Sum of an Hourglass | 2428 | <span class="diff-medium">Medium</span> | 2D prefix cousin | 📝 |
| 17 | Find Median From Data Stream | 295 | <span class="diff-hard">Hard</span> | Heap-based — BIT alternative when values are bounded | 📝 |
| 18 | Range Sum of Sorted Subarray Sums | 1508 | <span class="diff-medium">Medium</span> | BIT optional sketch | 📝 |
| 19 | XOR Queries of a Subarray | 1310 | <span class="diff-medium">Medium</span> | Static prefix XOR (no BIT needed) | ✅ |
| 20 | Sum of Floored Pairs | 1862 | <span class="diff-hard">Hard</span> | BIT counting + harmonic | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — The `i & -i` walk, derived from scratch

The whole BIT depends on two recurrences: `i += i & -i` (update walk-up) and `i -= i & -i` (query walk-down). Why these specific walks?

#### Setup: what does `bit[i]` store?

`bit[i]` stores the sum of a **specific range ending at `i`**, of length `lowbit(i) = i & -i`. So `bit[i]` covers `arr[i - lowbit(i) + 1 .. i]`.

Examples for `n = 8`:

| i | binary | lowbit(i) | range covered |
|---|--------|-----------|---------------|
| 1 | 0001 | 1 | [1, 1] |
| 2 | 0010 | 2 | [1, 2] |
| 3 | 0011 | 1 | [3, 3] |
| 4 | 0100 | 4 | [1, 4] |
| 5 | 0101 | 1 | [5, 5] |
| 6 | 0110 | 2 | [5, 6] |
| 7 | 0111 | 1 | [7, 7] |
| 8 | 1000 | 8 | [1, 8] |

Visually, the ranges form a binary-tree-shaped tiling:

```
    [1.....8]
    [1.4][5.8]
    [1.2][3][5.6][7]
    [1][2][3][4][5][6][7][8]    ← original cells
```

(Each row's segments cover the row above. The BIT only stores certain rows: `bit[1]=[1], bit[2]=[1..2], bit[3]=[3], bit[4]=[1..4], bit[5]=[5], bit[6]=[5..6], bit[7]=[7], bit[8]=[1..8]`.)

#### Why the prefix walk is `i -= lowbit(i)`

To compute `prefix_sum(7)`:

- `bit[7]` covers `[7, 7]`. Take it.
- Need `[1, 6]`. Jump to `7 - lowbit(7) = 7 - 1 = 6`.
- `bit[6]` covers `[5, 6]`. Take it.
- Need `[1, 4]`. Jump to `6 - lowbit(6) = 6 - 2 = 4`.
- `bit[4]` covers `[1, 4]`. Take it.
- Done. `i = 4 - lowbit(4) = 0`, loop exits.

Total = `bit[7] + bit[6] + bit[4]`. Three reads for a prefix of length 7. In general, log₂(i) reads.

#### Why the update walk is `i += lowbit(i)`

To update `arr[3]` by `+δ`:

- `bit[3]` covers `[3, 3]`. Add δ.
- Need to update every BIT cell whose range *contains* index 3. The next such cell is the smallest index > 3 whose lowbit-range still includes 3. That's `3 + lowbit(3) = 4`.
- `bit[4]` covers `[1, 4]`. Add δ.
- Next: `4 + lowbit(4) = 8`. `bit[8]` covers `[1, 8]`. Add δ.
- `8 + 8 = 16 > n`. Stop.

Three writes for one update. In general, log₂(n − i) writes.

The recurrence `i += lowbit(i)` finds, by construction, the **next BIT cell whose range includes i**. The proof is a one-liner about how lowbit-aligned ranges partition the prefix [1..i].

#### Why 1-indexed and not 0-indexed

`lowbit(0) = 0 & 0 = 0`. The walk degenerates: `0 + 0 = 0`, infinite loop. 1-indexing avoids this. Most BIT bugs are off-by-one from forgetting this.

If your problem is 0-indexed, mentally add 1 inside the BIT class. Don't try to make a 0-indexed BIT — it's possible but not worth the cognitive cost.

#### Complexity

- **Time:** O(log n) per `update` and `prefix_sum`.
- **Space:** O(n).

---

### Deep-dive 2 — Count of Smaller Numbers After Self (LC 315)

> For each `nums[i]`, count `nums[j]` with `j > i` and `nums[j] < nums[i]`.

The same problem we solved with a [segment tree](03-segment-trees.md). With a Fenwick, the code is half the length.

#### Plan (identical to seg-tree)

1. Compress values to ranks.
2. BIT over rank space.
3. Iterate right-to-left. For each element of rank `r`: query the count of values with rank `< r` (`prefix_sum(r - 1)`), then increment the count at rank `r` (`update(r, 1)`).

#### Code

```python
def count_smaller(nums: list[int]) -> list[int]:
    """LC 315 with Fenwick."""
    if not nums:
        return []

    rank = {v: i + 1 for i, v in enumerate(sorted(set(nums)))}    # (1) 1-indexed!
    m = len(rank)
    bit = Fenwick(m)

    result = [0] * len(nums)
    for i in range(len(nums) - 1, -1, -1):
        r = rank[nums[i]]
        result[i] = bit.prefix_sum(r - 1)                         # (2) count with rank < r
        bit.update(r, 1)
    return result
```

1. The compression maps to **1-indexed** ranks because BIT is 1-indexed.
2. `prefix_sum(r - 1)` counts values strictly smaller. Edge case: `r = 1` → `prefix_sum(0) = 0`. The Fenwick handles this naturally because the loop condition `while i > 0` exits immediately.

#### Dry run on `nums = [5, 2, 6, 1]`

Ranks: `{1: 1, 2: 2, 5: 3, 6: 4}`. `m = 4`. BIT all zero.

Right-to-left:

| i | nums[i] | r | prefix_sum(r-1) | result | after update |
|---|---------|---|-----------------|--------|--------------|
| 3 | 1 | 1 | prefix_sum(0) = 0 | result[3] = 0 | bit: rank 1 += 1 |
| 2 | 6 | 4 | prefix_sum(3) = 1 (only rank 1 set) | result[2] = 1 | bit: rank 4 += 1 |
| 1 | 2 | 2 | prefix_sum(1) = 1 (rank 1 set) | result[1] = 1 | bit: rank 2 += 1 |
| 0 | 5 | 3 | prefix_sum(2) = 2 (ranks 1 and 2 set) | result[0] = 2 | bit: rank 3 += 1 |

Output: `[2, 1, 1, 0]`. ✓

Same result as the seg tree, half the surrounding code.

#### Why the seg tree was the wrong tool

For this exact problem, BIT wins on:

- **Code length** — 8 lines of BIT vs ~30 lines of seg tree.
- **Constant factor** — fewer cache misses.
- **Memory** — `4n` for seg tree vs `n+1` for BIT.

The seg tree wins when the operation is non-invertible (min/max instead of sum) or when you need lazy propagation. Order-statistics counting plays directly to BIT's strengths.

#### Complexity

- **Time:** O(n log n). Sort + n iterations of (query + update) at log m each.
- **Space:** O(n) for BIT and rank map.

---

### Deep-dive 3 — Reverse Pairs (LC 493)

> Count pairs `(i, j)` with `i < j` and `nums[i] > 2 * nums[j]`.

A "count smaller" twist with a multiplier. The BIT approach: scan right-to-left, but query for values `< nums[i] / 2` (strictly), then update.

The subtlety: the "smaller" value isn't a rank in the original space — it's a rank against a compressed space that includes both `nums[i]` and `2 * nums[j]`.

#### Code

```python
def reverse_pairs(nums: list[int]) -> int:
    """LC 493."""
    # 1. Build a value space that includes nums[i] and 2 * nums[i] for all i.
    vals = set(nums)
    for x in nums:
        vals.add(2 * x)
    rank = {v: i + 1 for i, v in enumerate(sorted(vals))}
    m = len(rank)

    bit = Fenwick(m)
    count = 0
    # 2. Scan right-to-left. For each nums[i], count how many seen values v satisfy v < nums[i] / 2,
    #    i.e. 2 * v < nums[i] — equivalently, the rank of (nums[i] - 1) // 2 etc.
    # Cleaner: query "how many seen with value v such that 2*v < nums[i]" by transforming the threshold.

    for i in range(len(nums) - 1, -1, -1):
        # We want to count seen nums[j] where nums[i] > 2 * nums[j], i.e. nums[j] < nums[i] / 2.
        # In integer terms: nums[j] < nums[i] / 2 → nums[j] ≤ ceil(nums[i] / 2) - 1.
        # Easier: query strictly less than nums[i] / 2 by using rank trick on the compressed space:
        # find rank of nums[i] (we need values in compressed space whose value is strictly less than nums[i] / 2).
        # We'll compute the largest rank r' whose value < nums[i] / 2.
        threshold = nums[i] / 2
        # Use bisect on the sorted unique vals.
        # (For brevity, use a precomputed sorted list)
        pass  # the full code below uses a cleaner approach
    return count
```

The above outlines the idea but the practical implementation cleans up by precomputing a sorted list. Here's the working form:

```python
from bisect import bisect_left

def reverse_pairs(nums: list[int]) -> int:
    sorted_vals = sorted(set(nums) | {2 * x for x in nums})
    rank = {v: i + 1 for i, v in enumerate(sorted_vals)}
    m = len(rank)
    bit = Fenwick(m)

    count = 0
    for x in reversed(nums):
        # Count of seen y with 2 * y < x, i.e. y < x / 2.
        # In the compressed space, find the rank of the largest value strictly less than x / 2.
        idx = bisect_left(sorted_vals, x / 2) - 1                 # (1) largest index with value < x/2
        if idx >= 0:
            count += bit.prefix_sum(idx + 1)                      # (2) +1 because BIT is 1-indexed
        bit.update(rank[x], 1)

    return count
```

1. `bisect_left(sorted_vals, x / 2)` returns the first index whose value is ≥ `x / 2`. Subtracting 1 gives the last index strictly less.
2. Convert 0-indexed `idx` to 1-indexed BIT position.

#### Walking `nums = [1, 3, 2, 3, 1]`

`sorted_vals = [1, 2, 3, 4, 6]` (unique union with doubles), ranks `{1:1, 2:2, 3:3, 4:4, 6:5}`.

Right-to-left:

| step | x | x/2 | bisect idx | prefix_sum | count delta | update |
|------|---|-----|------------|------------|-------------|--------|
| 1 | 1 | 0.5 | bisect(0.5)=0, idx=-1 | — | 0 | rank 1 += 1 |
| 2 | 3 | 1.5 | bisect(1.5)=1, idx=0 | prefix_sum(1)=1 | +1 | rank 3 += 1 |
| 3 | 2 | 1.0 | bisect(1.0)=0, idx=-1 | — | 0 | rank 2 += 1 |
| 4 | 3 | 1.5 | bisect(1.5)=1, idx=0 | prefix_sum(1)=1 | +1 | rank 3 += 1 |
| 5 | 1 | 0.5 | idx=-1 | — | 0 | rank 1 += 1 |

Total count = 2. ✓ The reverse pairs are `(3 at idx 1, 1 at idx 4)` and `(3 at idx 3, 1 at idx 4)`.

#### Why include `2 * nums[i]` in the value space?

The BIT indexes are ranks. To compare `2 * y < x` we need both `x` and `2 * y` to live in the same coordinate system. Including the doubles makes the bisect well-defined.

#### Why this isn't easier with a seg tree

It's not — both work, both are O(n log n). The seg-tree code is longer; the BIT code is shorter. Pick BIT when the operation is "count with prefix predicate."

#### Complexity

- **Time:** O(n log n).
- **Space:** O(n).

---

## 🐛 Common bugs

1. **0-indexing.** `lowbit(0) = 0`, so the walk-up loop never advances and the walk-down loop never enters. **1-index everything**, even if your input is 0-indexed (translate at the boundary).
2. **Off-by-one in `prefix_sum(0)`.** Treat as 0 — the loop `while i > 0` exits immediately. This is the right answer for "sum of empty prefix."
3. **Using BIT for non-invertible operations.** Sum, XOR, count: yes (subtraction / XOR is the inverse). Min, max, gcd: no — `range_sum(l, r) = prefix(r) - prefix(l-1)` requires an inverse. Use a seg tree.
4. **Forgetting to compress.** A BIT over `10^9` values would need `10^9` cells. Always compress to the unique values that actually appear.
5. **Two-BIT range-update-range-query getting the math wrong.** The derivation is `prefix_sum(i) = b1.prefix_sum(i) * (i + 1) - b2.prefix_sum(i)` — easy to flip a sign or off-by-one. Memorise the recurrence or derive it cleanly each time; don't half-remember.
6. **`update` past `n`.** If the input puts an index outside `[1, n]`, the loop `while i <= n` silently does nothing. Validate inputs.
7. **2D BIT confused with 2D prefix sums.** Static 2D prefix sum is O(rc) build + O(1) query; mutable use 2D BIT for O(log r · log c) per op. Don't reach for 2D BIT when the matrix never changes.
8. **Float precision in compression**, e.g. `bisect_left(sorted_vals, x / 2)` with integer doubles. Either sort with strict integer math (replace `/2` with multiplied comparisons) or accept that float inputs introduce wobble.
9. **Overflow on `delta * (i - 1)` in two-BIT range queries.** Python is fine; in C++ use `long long`.

---

## 🗣️ Interviewer phrasings to recognize

- "**Mutable** range sum array." → BIT for sum; seg tree if min/max.
- "**Count smaller / larger / between**." → BIT on compressed value space.
- "**Number of inversions**." → BIT or merge-sort. BIT is shorter; merge-sort more general.
- "**Range add, point query**." → Difference BIT.
- "**Range add, range sum**." → Two BITs (the fancy trick).
- "**2D mutable rectangle sum**." → 2D BIT (or 2D seg tree if more complex).
- "**XOR over a range, mutable**." → BIT (XOR is its own inverse).

---

## 🧭 Connections to other patterns

- **[Segment Trees](03-segment-trees.md)** — superset of BIT functionality. Use seg tree when BIT can't handle the aggregate (min/max) or when you need lazy propagation. BIT when the aggregate is sum/XOR and code length matters.
- **[Bitwise XOR](../04-patterns/20-bitwise-xor.md)** — the `i & -i` lowest-set-bit trick is shared. The BIT *is* an application of two's-complement bit-twiddling at the data-structure level.
- **Prefix sums** — static analogue. BIT becomes essential the moment updates appear; if the array never changes, plain prefix sums beat BIT.
- **Merge sort** — alternative for inversion counting. Doesn't need compression; uses O(n log n) with a divide-and-conquer pass that counts cross-pair inversions during merge.
- **[Modified Binary Search](../04-patterns/11-modified-binary-search.md)** — k-th smallest in a BIT is binary-search-on-tree: walk powers of 2 down from `next_pow2(n)` and step into a chunk if `bit[*]` < k.

---

## ✅ Self-check — 8 questions

??? question "1. Why must the BIT be 1-indexed?"
    `lowbit(0) = 0 & -0 = 0`. The update walk `i += lowbit(i)` and query walk `i -= lowbit(i)` both stall at `i = 0`. With 1-indexing, every walk strictly increases (update) or strictly decreases (query), guaranteeing termination in O(log n) steps.

??? question "2. What does `bit[i]` actually store?"
    The sum of `arr[i - lowbit(i) + 1 .. i]` — a chunk of length `lowbit(i)` ending at `i`. `bit[6]` (lowbit 2) stores `arr[5] + arr[6]`. `bit[8]` (lowbit 8) stores the entire `arr[1..8]`.

??? question "3. Why is `range_sum(l, r) = prefix_sum(r) - prefix_sum(l-1)` only valid for sum, not min?"
    Subtraction is the inverse of addition — it lets you recover a range sum from two prefix sums. There's no "subtract the min of [1..l-1] from the min of [1..r]" — minima don't have inverses. Range min/max requires a sparse table or segment tree.

??? question "4. How does the difference-array BIT support range-add + point-query in O(log n)?"
    Storing the *difference array* in the BIT means the prefix sum at index `i` is the original `arr[i]`. Range-add `[l, r] += delta` becomes two point updates on the difference array: `+delta` at `l`, `-delta` at `r+1`. Each update is one BIT update; each point query is one prefix-sum.

??? question "5. Why do you need *two* BITs for range-add + range-sum?"
    Decomposing `prefix_sum_arr(i) = sum_{k=1..i} arr[k]` after a range add yields `b1.prefix_sum(i) * (i+1) - b2.prefix_sum(i)`, where `b1` tracks the difference array and `b2` tracks `j * d[j]`. Both are needed; one tracks the additive component, the other corrects for the index-weighted component.

??? question "6. When does a Fenwick tree beat a segment tree?"
    For point-update + prefix-sum (or XOR): always — half the code, ~2× faster constant factor, and uses a single 1D array. For range-update + range-query of *sum*: also wins (two BITs). For min/max/gcd, lazy propagation, or custom merge tuples: seg tree.

??? question "7. How do you find the k-th smallest element using a Fenwick that counts occurrences?"
    Walk powers of 2 from `next_pow2(n)` down to 1. At each level, if jumping into a chunk (advancing `idx` by `step` and reading `bit[idx + step]`) doesn't exceed `k`, take the jump and subtract `bit[idx + step]` from `k`. After log n steps, `idx + 1` is the k-th smallest's rank. O(log n) per query.

??? question "8. Why does Reverse Pairs (LC 493) need to compress *both* `nums[i]` and `2 * nums[i]`?"
    The query is "count y with 2*y < x." For the compressed coordinate space to support that comparison, both `x` and `2y` (for every `y`) must be representable. The union ensures `bisect_left(sorted_vals, x/2)` lands at a meaningful position.

---

> **Up next in Advanced:** Suffix Arrays / Suffix Automata — the data structure for "many substrings of one long text." Then heavy-light decomposition, Mo's algorithm, and treaps to close out Phase 6.
