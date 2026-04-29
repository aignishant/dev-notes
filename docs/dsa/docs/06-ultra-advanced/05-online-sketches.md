# Online Algorithms & Sketches

> The chapter where you can't keep the data. A trillion events stream past, you have a few megabytes of RAM, and the interviewer wants the median, the heavy hitters, the count of distinct items, and a uniform random sample — *exactly* if possible, *approximately* with a tunable error if not. The four flavors here cover that space: **two-heap sliding median** (exact, online, `O(log n)`), **Reservoir sampling** (exact uniform sample with `O(1)` memory), **Count-Min / Misra-Gries** (approximate frequency / heavy hitters with `ε`-additive error), and **HyperLogLog** (approximate cardinality with ~1.04/√m relative error). One Bloom filter at the end for set-membership. Net: the streaming-systems toolkit that powers Cloudflare, Splunk, Druid, and every analytics database.

<span class="phase-status phase-done">Phase 7 — Ultra-Advanced</span>

---

## 📖 What is "online"? What is a "sketch"?

**Online** means the algorithm sees inputs **one at a time**, processes each, and *cannot rewind*. Contrast with **offline**, where you have the whole input in memory or on disk and can sort, scan multiple times, etc.

**Sketches** are sub-linear-memory data structures that answer queries **approximately**. The trade-off is governed by two parameters:

- `ε` — the approximation error (additive or multiplicative).
- `δ` — the failure probability (the chance the answer is outside the `ε` window).

Sketches typically use `O((1/ε) · log(1/δ))` space and `O(log(1/δ))` time per update. **You buy precision with bits.**

The mental model: every sketch is a **random projection** of the data into a small fixed-size summary. Hash functions are the projection; clever aggregation (min, sum, max-of-leading-zeros) is the readout.

Three reasons sketches matter beyond "saving memory":

1. **Mergeability.** Two sketches built on different streams can be combined to get the sketch of the union, in time proportional to sketch size — not data size. This is what makes them work in distributed settings (per-shard sketches → reduce step).
2. **Stable across runs.** Same hash seeds → same sketch, same answer. Useful for deduplication and incremental builds.
3. **Constant memory regardless of stream length.** A HyperLogLog with `m = 16384` registers uses ~`16 KB` to estimate cardinalities up to ~`10⁹` with 0.8% standard error. The same memory works whether the stream is 10⁶ or 10¹².

!!! tip "The signal — when to reach for online / sketch algorithms"
    Reach for it when:

    - "Stream of N events, can't store them" — pick the right sketch by query type.
    - "Find top-k frequent items" → **Misra-Gries** or **Count-Min + heap**.
    - "Estimate distinct count" → **HyperLogLog**.
    - "Random sample of size k from a stream of unknown length" → **Reservoir sampling**.
    - "Median over the last k events" → **two-heap sliding window**.
    - "Has X been seen before?" with false-positive tolerance → **Bloom filter**.
    - "Approximate quantiles over a stream" → **t-digest / KLL sketch**.

    Don't reach for it when:

    - The stream fits in RAM and you can afford O(n log n) sort — just sort.
    - You need **exact** answers and the universe is small — count-arrays beat sketches.
    - The query type doesn't match a known sketch (no sketch is universal).

---

## 🧩 The five flavors

### Flavor 1: Two-heap sliding-window median

Maintain a max-heap `lo` (lower half) and a min-heap `hi` (upper half) with `|lo| − |hi| ∈ {0, 1}`. Median = top of `lo` if odd-size, else mean of tops. **Lazy deletion** handles "drop the element that left the window."

```python
import heapq
from collections import defaultdict

def sliding_median(nums: list[int], k: int) -> list[float]:
    lo: list[int] = []                                                # (1) max-heap (negated)
    hi: list[int] = []                                                # min-heap
    to_remove: dict[int, int] = defaultdict(int)
    lo_size = hi_size = 0

    def prune(heap: list[int]) -> None:                               # (2)
        sign = -1 if heap is lo else 1
        while heap and to_remove[sign * heap[0]] > 0:
            to_remove[sign * heap[0]] -= 1
            heapq.heappop(heap)

    def add(x: int) -> None:
        nonlocal lo_size, hi_size
        if not lo or x <= -lo[0]:
            heapq.heappush(lo, -x); lo_size += 1
        else:
            heapq.heappush(hi, x); hi_size += 1
        # rebalance to invariant lo_size − hi_size ∈ {0, 1}
        if lo_size > hi_size + 1:
            heapq.heappush(hi, -heapq.heappop(lo)); lo_size -= 1; hi_size += 1
        elif lo_size < hi_size:
            heapq.heappush(lo, -heapq.heappop(hi)); hi_size -= 1; lo_size += 1
        prune(lo); prune(hi)

    def remove(x: int) -> None:                                       # (3) lazy
        nonlocal lo_size, hi_size
        to_remove[x] += 1
        if x <= -lo[0]: lo_size -= 1
        else:           hi_size -= 1
        prune(lo); prune(hi)

    out: list[float] = []
    for i, x in enumerate(nums):
        add(x)
        if i >= k:
            remove(nums[i - k])
        if i >= k - 1:
            out.append(-lo[0] if k % 2 else (-lo[0] + hi[0]) / 2)
    return out
```

1. Python `heapq` is a min-heap; negate values for the max-heap half.
2. **Lazy prune** at the heap tops. Mid-heap stale elements are fine — they float around until they bubble up.
3. We can't `remove` from a binary heap in `O(log n)` arbitrarily; the lazy-deletion pattern with a counter is the canonical workaround. Net `O(log k)` amortised per update.

### Flavor 2: Reservoir sampling — uniform sample of size `k`

You see items one at a time; total length is unknown; you want a uniform random sample of `k` items at the end. Memory: `O(k)`.

```python
import random

def reservoir(stream, k: int) -> list:
    sample: list = []
    for i, x in enumerate(stream):
        if i < k:
            sample.append(x)                                          # (1)
        else:
            j = random.randint(0, i)                                  # (2) inclusive
            if j < k:
                sample[j] = x
    return sample
```

1. Fill the reservoir with the first `k` items unconditionally.
2. For item `i ≥ k`, replace a random reservoir slot with probability `k / (i + 1)`. **Why uniform:** by induction on `i`, every item seen so far is in the reservoir with probability `k / (i + 1)`. After `n` items, that's `k / n` per item — uniform.

For weighted reservoir sampling, see **A-Res** (Efraimidis-Spirakis): generate `key_i = u_i^(1/w_i)` and keep the `k` largest keys via a min-heap.

### Flavor 3: Count-Min sketch — approximate frequency

A `d × w` table of counters, with `d` independent hash functions. **Update:** for each row, hash the item to a column and increment. **Query:** `count(x) = min over rows of table[row][hash_row(x)]`. The min trick removes upward bias from collisions.

```python
import hashlib

class CountMin:
    def __init__(self, w: int = 2048, d: int = 5):                    # (1)
        self.w, self.d = w, d
        self.table = [[0] * w for _ in range(d)]
        self.seeds = list(range(d))

    def _hashes(self, x: bytes) -> list[int]:
        return [int(hashlib.blake2b(x, digest_size=8, salt=str(s).encode().ljust(16, b"\0")).hexdigest(), 16) % self.w
                for s in self.seeds]

    def add(self, x: bytes, c: int = 1) -> None:
        for r, h in enumerate(self._hashes(x)):
            self.table[r][h] += c

    def count(self, x: bytes) -> int:                                 # (2)
        return min(self.table[r][h] for r, h in enumerate(self._hashes(x)))
```

1. With `w = ⌈e / ε⌉` and `d = ⌈ln(1/δ)⌉`, the estimate is at most `true + ε · ||a||₁` with probability `≥ 1 − δ`. ε=0.001 and δ=0.01 → w ≈ 2719, d ≈ 5 → ~14 KB.
2. Always an **over**-estimate — collisions only inflate counts. The `min` across rows minimises the inflation.

### Flavor 4: HyperLogLog — approximate cardinality

Stream over items; estimate `|distinct(items)|` with ~`1.04/√m` standard error using `m = 2^p` registers (each holds a small int — 5 or 6 bits is enough for streams up to ~`10⁹`).

```python
import hashlib, math

class HLL:
    def __init__(self, p: int = 14):                                  # (1)
        self.p = p
        self.m = 1 << p
        self.regs = [0] * self.m
        self.alpha = {4: 0.673, 5: 0.697, 6: 0.709}.get(self.m,
                     0.7213 / (1 + 1.079 / self.m))                   # (2)

    def add(self, x: bytes) -> None:
        h = int(hashlib.blake2b(x, digest_size=8).hexdigest(), 16)
        idx = h & (self.m - 1)                                        # bucket index
        rho = ((h >> self.p) | (1 << (64 - self.p))).bit_length()
        rho = 64 - self.p - rho.bit_length() + 1                      # (3) leading-zeros + 1
        # Equivalent simple form:
        bits = (h >> self.p)
        rho = 1
        while bits & 1 == 0 and rho < 64 - self.p:
            rho += 1; bits >>= 1
        self.regs[idx] = max(self.regs[idx], rho)

    def cardinality(self) -> float:
        Z = 1.0 / sum(2.0 ** -r for r in self.regs)
        E = self.alpha * self.m * self.m * Z                          # (4) raw estimate
        if E <= 2.5 * self.m:                                          # small-range correction
            zeros = self.regs.count(0)
            if zeros: E = self.m * math.log(self.m / zeros)
        return E
```

1. `p = 14` → `m = 16384` registers, ~16 KB, standard error ~0.81%.
2. The `α` constant corrects bias from the harmonic-mean-of-2^reg estimator.
3. `ρ` = position of the leftmost 1-bit in the **rest** of the hash. The intuition: in a uniform stream, the maximum `ρ` seen scales like `log₂(distinct count)`. Each register watches one partition.
4. The estimator is the `α`-corrected harmonic mean of `2^reg`, scaled by `m²`. Small-range and large-range corrections handle the tails.

**Mergeability:** `merge(A, B).regs[i] = max(A.regs[i], B.regs[i])`. This is what makes HLL essential in distributed analytics.

### Flavor 5: Bloom filter — approximate set membership

Bit array of size `m` + `k` independent hash functions. **Add:** set `k` bits. **Query:** all `k` bits set → "maybe in set"; any zero → "definitely not in set." Tunable false-positive rate, **never** false negatives.

```python
class Bloom:
    def __init__(self, m: int = 1 << 20, k: int = 7):                 # (1)
        self.m, self.k = m, k
        self.bits = bytearray(m // 8)

    def _hashes(self, x: bytes) -> list[int]:
        h = int(hashlib.blake2b(x, digest_size=16).hexdigest(), 16)
        h1, h2 = h & ((1 << 64) - 1), h >> 64                         # (2) double-hashing
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, x: bytes) -> None:
        for h in self._hashes(x):
            self.bits[h >> 3] |= 1 << (h & 7)

    def __contains__(self, x: bytes) -> bool:
        return all(self.bits[h >> 3] & (1 << (h & 7)) for h in self._hashes(x))
```

1. Optimal `k = (m / n) · ln 2` for `n` expected insertions; FPR `≈ (1 − e^(−kn/m))^k`.
2. The "double hashing" trick — derive `k` hashes from two independent ones — is a Kirsch-Mitzenmacher result giving same FPR as `k` truly independent hashes.

---

## 🔍 Sub-pattern at-a-glance

| # | Sketch / algorithm     | Query                                    | Memory          | Error                              | Mergeable |
|---|------------------------|------------------------------------------|-----------------|------------------------------------|-----------|
| 1 | Two-heap sliding median| Median of last `k`                       | O(k)            | Exact                              | No (windowed) |
| 2 | Reservoir sampling     | Uniform sample of size k                 | O(k)            | Exact (probabilistic uniformity)   | No (sequential) |
| 3 | Count-Min sketch       | freq(x) approx, top-k                    | O((1/ε)·log(1/δ)) | additive `ε · ||a||₁`            | Yes (sum)  |
| 4 | Misra-Gries            | Heavy hitters > n/k                      | O(k)            | Misses items with freq ≤ n/k       | Yes        |
| 5 | HyperLogLog            | Approx distinct count                    | O(2^p)          | ~1.04/√m relative                  | Yes (max)  |
| 6 | Bloom filter           | "Possibly in set"                        | O(m)            | One-sided FPR                      | Yes (OR)   |
| 7 | t-digest / KLL         | Approx quantile                          | O(1/ε)          | rank error `ε · n`                 | Yes        |
| 8 | Boyer-Moore vote       | Strict majority element                  | O(1)            | Exact (when majority exists)       | No         |

---

## 📚 20 problems where streaming / sketch thinking is the canonical answer

| #  | Source       | Problem                                              | Difficulty | Pattern                | Key insight                                                            |
|----|--------------|------------------------------------------------------|------------|------------------------|------------------------------------------------------------------------|
| 1  | LC 295       | Find Median from Data Stream                         | Hard       | Two-heap                | The two-heap balance is the canonical formulation.                    |
| 2  | LC 480       | Sliding Window Median                                | Hard       | Two-heap + lazy delete  | Add `to_remove` map; prune at heap tops only.                         |
| 3  | LC 169       | Majority Element (> n/2)                             | Easy       | Boyer-Moore vote        | Single-pass O(1) memory.                                              |
| 4  | LC 229       | Majority Element II (> n/3)                          | Medium     | Misra-Gries (k=2)       | Two candidates + verification pass.                                   |
| 5  | LC 692       | Top K Frequent Words                                 | Medium     | Count-Min + heap        | When stream doesn't fit in RAM, swap exact dict for Count-Min.        |
| 6  | LC 703       | Kth Largest Element in a Stream                      | Easy       | Min-heap of size k      | Trivial but the streaming setup matters.                              |
| 7  | LC 1396      | Design Underground System                            | Medium     | Two-dict streaming      | One dict for active checkins, one for averages.                       |
| 8  | LC 362       | Design Hit Counter                                   | Medium     | Circular buffer / queue | 5-minute window over hits; deque or bucketed counts.                  |
| 9  | LC 359       | Logger Rate Limiter                                  | Easy       | Hash + recent-window    | Keep `last_seen[msg]`; reject if within window.                       |
| 10 | LC 642       | Design Search Autocomplete System                    | Hard       | Trie + streaming-top-k  | Streaming top-k per prefix.                                           |
| 11 | LC 1845      | Seat Reservation Manager                             | Medium     | Min-heap                | Lazy availability.                                                    |
| 12 | LC 2102      | Sequentially Ordinal Rank Tracker                    | Hard       | Two heaps               | Variant of the median two-heap idea on ordinal ranks.                 |
| 13 | LC 716       | Max Stack                                            | Easy       | Two-stack streaming     | Companion stack for running max.                                      |
| 14 | LC 1825      | Finding MK Average                                   | Hard       | Three sorted multisets  | Maintain low/mid/hi partitions over a sliding window.                 |
| 15 | LC 239       | Sliding Window Maximum                               | Hard       | Monotonic deque         | Streaming max in O(n) over the window.                                |
| 16 | CTCI 17.20   | Continuous Median (book)                             | Hard       | Two-heap                | Same as LC 295.                                                       |
| 17 | Industry     | "Distinct visitors per day" at scale                  | Hard       | HyperLogLog             | Per-shard HLL → daily merge → 0.8% error at 16 KB.                    |
| 18 | Industry     | "Has this URL been crawled?"                         | Hard       | Bloom filter            | One-sided FPR; recheck on hit if needed.                              |
| 19 | Industry     | "Top-100 hot keys" in an in-memory cache             | Hard       | Count-Min + min-heap    | CM sketch + heap of top-100 candidates with stored est. counts.       |
| 20 | LC 384       | Shuffle an Array                                     | Medium     | Fisher-Yates online     | Same primitive as reservoir sampling for k = n.                       |

---

## 🔬 Deep-dive 1 — Why reservoir sampling is uniform, by induction

**Claim:** after seeing `n` items, every item is in the reservoir with probability exactly `k / n`.

**Base case (n = k):** the first `k` items fill the reservoir unconditionally. Probability `k / k = 1` for each. ✓

**Inductive step:** assume the claim for `n − 1`. The `n`-th item is added with probability `k / n` (we draw `j ∈ [0, n)` and replace if `j < k`).

For an item `x` already in the reservoir at step `n − 1` (probability `k / (n − 1)`):
- It survives step `n` if either (a) the new item is rejected (prob `(n − k) / n`), or (b) the new item replaces a *different* slot (prob `(k − 1) / n`).
- Total survival probability: `(n − k) / n + (k − 1) / n = (n − 1) / n`.
- So `P(x in reservoir at step n) = k / (n − 1) · (n − 1) / n = k / n`. ✓

The new item: in with probability `k / n` directly. ✓

The induction holds, so the algorithm produces a uniform sample of size `k`. The key insight: **the per-step replacement probability `k / n` exactly cancels the "I survived all prior steps" probability**, keeping the marginal at `k / n` for every item.

---

## 🔬 Deep-dive 2 — Count-Min error bound, intuitively

CM with `d` rows and `w` columns. The estimator for `x` is `f̂(x) = min_r table[r][hash_r(x)]`.

**Each row's estimate is `f(x) + collisions_r`**, where collisions are mass from items hashing to the same column. By linearity of expectation, `E[collisions_r] ≤ ||a||₁ / w` (every other item contributes its weight scaled by `1/w`, the collision probability).

**Markov:** `P(collisions_r > e · ||a||₁ / w) ≤ 1/e`.

Setting `w = ⌈e / ε⌉`, the per-row "bad event" `collisions_r > ε · ||a||₁` has probability `≤ 1/e`. Across `d` independent rows, all rows being bad has probability `≤ (1/e)^d = e^(−d)`. Set `d = ⌈ln(1/δ)⌉` and the failure probability drops to `δ`.

**The min trick is what makes the bound multiplicative across rows**: the estimate is wrong only if *every* row collides badly. Independent hashes make these events independent.

This is also why CM is **biased upward but never below true frequency** — the readout is `f(x) + min_r collisions_r ≥ f(x)`. For "is X frequent?" queries, false positives are the concern, never false negatives.

---

## 🔬 Deep-dive 3 — HyperLogLog from first principles

**The setup:** hash each item to a uniform 64-bit integer. Use the first `p` bits as a **register index** (so we have `m = 2^p` registers); use the remaining bits as the value. For each register, track the **maximum** "leading-1 position" `ρ` ever seen — i.e., the position of the leftmost 1-bit in the value.

**Why `ρ` ≈ log₂(n)`:** if you draw `n` uniform values, the max leading-1-position is `~log₂ n` on average — the same intuition as "longest run of heads in `n` coin flips." Each register watches `n / m` items (in expectation), so its `ρ` predicts `log₂(n / m)`.

**The estimator:** combine all registers via the harmonic mean of `2^ρ_i`:

`E = α_m · m² / Σᵢ 2^(−ρᵢ)`

The harmonic mean is robust to outliers (unlike arithmetic mean of `2^ρ`, which has high variance from a single big register).

**Why not Linear Counting?** For tiny streams (fewer items than `m`), HLL undercounts — most registers are zero. The "small-range correction" `m · ln(m / zeros)` is the Linear Counting estimator: count the empty registers and back out an MLE for cardinality. Standard implementations switch between them at `n ≈ 2.5m`.

**Standard error:** `1.04 / √m`. With `p = 14`, that's 0.81%. To halve the error, quadruple `m` (one more bit of `p`). The space cost is `m · 6 bits ≈ 12 KB` for `p = 14`.

The whole machinery comes from one tiny idea: **the running-maximum of leading-zero counts is a sublinear-memory cardinality estimator**, and the rest is just statistics to squeeze the variance down.

---

## 🐛 Common bugs

1. **Two-heap median: rebalancing without lazy-prune.** `prune` at heap tops must run after every operation, not just before reading the median — the rebalance step itself can move stale elements to the top.
2. **Reservoir sampling using `randint(1, i)` instead of `randint(0, i)`.** Off-by-one; `j` must include `0`.
3. **Count-Min using correlated hashes.** Python's `hash()` on the same item gives the same value across the rows; use seeded BLAKE2b or a family like `hashlib.shake_128(item, seed)` to get genuine independence.
4. **HyperLogLog mixing buckets across versions.** Two HLL instances are mergeable only if they have the same `p` and the same hash family. Versioning/serialisation must include both.
5. **Bloom filter resized after inserts.** Bloom filters are not resizable — the bit positions depend on the modulus. Use a "scalable Bloom filter" (cascade of growing filters) if you need dynamic sizing.
6. **Misra-Gries forgetting the verification pass.** Misra-Gries finds *candidates* for items with frequency `> n/k`. The actual frequencies must be verified in a second pass — it doesn't prove they're heavy, only that nothing else *could* be.
7. **Boyer-Moore vote without verification.** Same trap: BM finds the candidate; you must scan again to confirm it's actually a majority. If no majority exists, BM still returns *something*.
8. **Sliding-window median computing mean of `lo` and `hi` for odd `k`.** Median is `lo[0]` for odd-size; means is wrong by `0.5` typically.
9. **HLL ignoring `bit_length()` overflow.** If the rest of the hash is all-zero, `ρ = 64 − p + 1`. Forgetting this case underestimates `ρ`'s ceiling.

---

## 🗣️ Interviewer phrasings to recognize

- "Stream of N events, find the median continuously" → **two-heap**.
- "Pick a random tweet uniformly from a Firehose" → **reservoir sampling**.
- "How many unique users visited today?" → **HyperLogLog** (or exact set if it fits).
- "Top-100 most frequent search queries last hour" → **Count-Min + heap**.
- "Has this URL been crawled before?" → **Bloom filter**.
- "Find the element appearing more than n/3 times" → **Misra-Gries / Boyer-Moore generalised**.
- "Approximate p99 latency over a stream" → **t-digest / KLL**.
- "Random sample for A/B test analysis on a 1B-row table" → **reservoir** at ingest time.

---

## 🧭 Connections to other patterns

- **[Top-K Elements](../04-patterns/12-top-k-elements.md)** — top-k is exact when memory permits; CM-sketch + heap is the streaming version.
- **[Sliding Window](../04-patterns/01-sliding-window.md)** — two-heap median, monotonic deque max, and Misra-Gries are all sliding-window flavours.
- **[Hash Tables](../02-data-structures/hash-tables/01-hash-table-basics.md)** — sketches are hash tables with **lossy aggregation**: trade exactness for sub-linear memory.
- **[Persistent Data Structures](01-persistent-data-structures.md)** — when you need a sketch *as of timestamp T*, persistent CM-sketch is one approach (though usually a per-window sketch is simpler).
- **[Computational Geometry](03-computational-geometry.md)** — geometric sketches (ε-coresets, ε-nets) are the spatial analog: small subsets that approximate the full set on all queries from a class.
- **MinHash / SimHash** — sketches for set similarity (Jaccard) and document-similarity, respectively. Same flavour as HLL.

---

## ✅ Self-check — 8 questions

??? question "1. Why does the two-heap structure give O(log k) median over a sliding window, and what's the role of lazy deletion?"
    Two heaps balanced to within 1 element keep the median at the top of `lo` (or the average of both tops). Insertion is O(log k). Removing an arbitrary element from a heap would be O(k) — but lazy deletion (mark for removal, prune at the top when it bubbles up) gives O(log k) amortised. Stale elements deeper in the heap never affect the median because the median is always at the top.

??? question "2. Prove uniform-sample correctness of reservoir sampling in one paragraph."
    By induction: the first `k` items are in the reservoir with probability 1. For step `n > k`, an existing item survives with probability `(n−1)/n` (replacement happens with prob `k/n` and targets a uniformly random slot, missing this item with prob `(k−1)/k`). So `P(in at step n) = k/(n−1) · (n−1)/n = k/n`. The new item enters with prob `k/n`. By induction, every item has marginal `k/n` after `n` items. QED.

??? question "3. How does a Count-Min sketch upper-bound query error, and why is the bias always positive?"
    Each row gives `f(x) + collisions_r` where `collisions_r ≤ ε · ||a||₁` with prob `≥ 1 − 1/e`. Across `d` independent rows, all rows simultaneously bad has prob `≤ e^(−d)`. The min across rows takes the smallest collision sum, giving `f̂(x) ≤ f(x) + ε · ||a||₁` with prob `≥ 1 − δ`. Bias is positive because collisions only add — every row's estimate is `≥ f(x)`, so the min is too.

??? question "4. Why does HyperLogLog use the harmonic mean of `2^ρ` and not the arithmetic mean?"
    `2^ρ` has very high variance — a single register that happened to see a big leading-zero count would dominate an arithmetic mean. The harmonic mean is robust to outliers because it weights small values more, capping the contribution of any one register. The α correction compensates for the harmonic mean's known bias.

??? question "5. What's the difference between a Bloom filter false positive and false negative, and which can a vanilla Bloom produce?"
    Bloom filters can have false positives (claim "in set" when it's not) but never false negatives (claim "not in set" when it is). Adding an item only sets bits to 1; querying never resets them. So if `x ∈ S`, all `k` bits are set when `x` was added, and `contains(x)` returns True. False positives arise when *other* insertions happened to set the same bits.

??? question "6. Why is Misra-Gries guaranteed to find every item with frequency > n/k, but may also return non-heavy items?"
    Misra-Gries maintains `k − 1` (item, count) slots. When a new item arrives that's not tracked and all slots are full, every count is decremented. Each decrement consumes `k` items from the stream (the new one and `k − 1` decrements). So an item with frequency > n/k must end up tracked: it can be decremented at most `n/k` times. Conversely, items below the threshold may *also* be tracked if they appear at the right moments — hence the verification pass.

??? question "7. Why is mergeability so important for sketches in distributed systems?"
    A distributed system shards a stream across N workers. Each worker maintains its sketch independently. At query time, the coordinator merges them and answers. Without mergeability, you'd have to ship raw data — defeating the purpose of sketches. The merge operations (Count-Min: sum tables; HLL: max registers; Bloom: OR bits) are O(sketch size), independent of stream length.

??? question "8. When does a streaming approach lose to an offline algorithm — name two scenarios."
    1. **Need exact answers, small data:** if the data fits in RAM, sort + scan beats any sketch on accuracy and is comparable in time. 2. **Queries don't match a sketch:** "median of items with property P" — no streaming sketch supports arbitrary predicate filtering. You either pre-filter (and lose generality) or fall back to offline. Sketches are great when query types are known up-front and the stream is huge.

---

> **Up next in Ultra-Advanced:** Randomised algorithms — Karger's min-cut, Las Vegas vs Monte Carlo, randomised quicksort/select, treaps' randomisation revisited, and the probabilistic method.
