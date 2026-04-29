# Randomised Algorithms

> The chapter where coin flips beat cleverness. Random pivot in quicksort makes adversarial input impossible. Random edge contraction in Karger's algorithm finds a min-cut in `O(V²)` per trial — repeat `O(V² log V)` times and you beat the deterministic `O(V³)` Stoer-Wagner with embarrassingly parallel code. Miller-Rabin tests primality of a 1024-bit integer in milliseconds where deterministic AKS would take hours. The four flavors here are **Las Vegas** (always correct, randomized runtime), **Monte Carlo** (fixed runtime, randomized correctness), **fingerprinting** (compare big things by comparing small hashes), and **the probabilistic method** (prove an object exists by showing a random one works with positive probability). Net: randomization is not a workaround — it is *the* technique that powers modern crypto, distributed consensus, and most lower-bound proofs.

<span class="phase-status phase-inprogress">Phase 7 — Ultra-Advanced topic 6 of 7</span>

---

## 📖 What is a randomised algorithm?

An algorithm that makes **internal coin flips** as part of its execution. The output (or runtime) depends on the random choices, not just the input. Two flavors:

- **Las Vegas:** the output is **always correct**; the *runtime* is a random variable. Example: randomised quicksort. Worst-case `O(n²)`, but expected `O(n log n)` for any input.
- **Monte Carlo:** the *runtime* is fixed (or bounded); the **output may be wrong** with bounded probability `p`. Example: Miller-Rabin primality. Always returns in `O(k log³ n)` time, but a composite may slip through with probability `≤ 4^(−k)`.

You can convert **Monte Carlo → Las Vegas** if you have a cheap verifier: run Monte Carlo, verify the output, and re-run on failure. You can convert **Las Vegas → Monte Carlo** by capping the runtime and returning a default on timeout.

The third pillar is **fingerprinting**: replace a heavy comparison ("are these two trees equal?", "do these polynomials match?") with a hash comparison, accepting a tiny false-match probability. This underlies Rabin-Karp, polynomial identity testing (Schwartz-Zippel), and Merkle-tree-based diff in Git.

The fourth is the **probabilistic method** (Erdős): to show some combinatorial object exists, define a probability distribution over candidates and show the desired property holds with probability `> 0`. Constructive variants (Lovász Local Lemma + algorithmic LLL) actually find the object in expected polynomial time.

The mental model: **randomness is a free oracle** that, in exchange for negligible failure probability, breaks adversarial inputs, eliminates worst-case bias, and makes parallelism trivial.

!!! tip "The signal — when to reach for randomization"
    Reach for it when:

    - The deterministic worst case is bad and there's a **symmetry** that random choice breaks (quicksort pivot, hash table key, treap priority).
    - The problem has a **cheap verifier** but a hard search (Las Vegas: random search → verify).
    - You need a **distributed/parallel** algorithm with no coordination (random sampling, Karger's repetitions, leader election).
    - **Approximate counting** — random sampling gives `1 ± ε` answers in `O(log(1/δ) / ε²)` samples.
    - **Cryptography or crypto-hash** primitives — randomness is the foundation of security.
    - You need a **lower bound proof via the probabilistic method** (prove existence, not construction).

    Don't reach for it when:

    - The deterministic algorithm is already optimal (sort small arrays with insertion sort, not quicksort with hash-based pivot).
    - The application is **safety-critical** with no acceptable failure probability — use deterministic alternatives or run multiple seeds in parallel and quorum.
    - The "random" source is **predictable** (avoid `random.random()` for cryptographic uses; use `secrets`).

---

## 🧩 The four flavors

### Flavor 1: Las Vegas — randomised quickselect (`O(n)` expected)

Find the `k`-th smallest in an unsorted array. Deterministic median-of-medians is `O(n)` worst case but heavy-constant; randomised pivot is `O(n)` *expected*, with tiny constants.

```python
import random

def quickselect(arr: list[int], k: int) -> int:
    """Return the k-th smallest (0-indexed) via Hoare partition."""
    a = arr[:]                                                        # don't mutate caller
    lo, hi = 0, len(a) - 1
    while lo < hi:
        pivot = a[random.randint(lo, hi)]                             # (1) random pivot
        i, j = lo, hi
        while i <= j:
            while a[i] < pivot: i += 1
            while a[j] > pivot: j -= 1
            if i <= j:
                a[i], a[j] = a[j], a[i]
                i += 1; j -= 1
        if k <= j:                                                    # (2) recurse one side
            hi = j
        elif k >= i:
            lo = i
        else:
            return a[k]
    return a[k]
```

1. **Random pivot** is the entire trick. Adversarial inputs (sorted, reverse-sorted, all-equal) are no longer worst-case for *this* particular run.
2. Quickselect recurses on **one side only** — the side containing the target `k`. Expected work: `T(n) = T(3n/4) + O(n)` → `O(n)` (the `3/4` comes from the pivot landing in the middle 50% of ranks half the time).

**Expected `O(n)`, worst `O(n²)`.** No input forces worst case — only the random sequence does.

### Flavor 2: Monte Carlo — Miller-Rabin primality

Test if `n` is prime in `O(k log³ n)` for `k` rounds, with composite-misclassification probability `≤ 4^(−k)`. For `k = 20`, that's `< 10⁻¹²` — far below cosmic-ray bit-flip rates.

```python
import random

def miller_rabin(n: int, k: int = 20) -> bool:
    if n < 2: return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0: return n == p
    # Write n - 1 = 2^s · d with d odd
    s, d = 0, n - 1
    while d % 2 == 0:
        s += 1; d //= 2
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)                                              # (1) fast modular exp
        if x == 1 or x == n - 1:
            continue                                                  # passes this round
        for _ in range(s - 1):                                        # (2) try squaring s-1 times
            x = (x * x) % n
            if x == n - 1: break
        else:
            return False                                              # composite witness found
    return True                                                       # probable prime
```

1. The Fermat-style check `a^(n−1) ≡ 1 (mod n)` is the starting point. Miller-Rabin strengthens it by inspecting the *square-root chain*.
2. **Witness:** if no element of the chain `a^d, a^(2d), a^(4d), ..., a^(2^(s−1) · d)` equals `n − 1` *and* `a^d ≠ 1`, then `n` is definitely composite. Each random `a` catches at least 3/4 of composites; `k` rounds give `4^(−k)` failure.

**Las Vegas variant:** if you suspect `n` is prime and the Miller-Rabin output matters, use deterministic witnesses for `n < 3.3 · 10²⁴` (a fixed set of 12 witnesses suffices) — this is a rare case where Monte Carlo upgrades to certain-correctness given input bounds.

### Flavor 3: Karger's min-cut — random edge contraction

Find the **global min-cut** of an undirected graph (the minimum number of edges to remove to disconnect the graph). Deterministic Stoer-Wagner is `O(V³)`; Karger's contracts random edges until 2 supernodes remain and outputs the count of edges between them.

```python
import random
from collections import defaultdict

def karger_once(n: int, edges: list[tuple[int, int]]) -> int:
    """One trial; returns a cut value (≥ true min-cut)."""
    parent = list(range(n))
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    pool = edges[:]
    random.shuffle(pool)                                              # (1)
    super_count = n
    for u, v in pool:
        if super_count == 2: break
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv                                           # (2) contract
            super_count -= 1
    cut = sum(1 for u, v in edges if find(u) != find(v))              # (3)
    return cut

def karger_min_cut(n: int, edges: list[tuple[int, int]]) -> int:
    trials = max(1, n * n * (n.bit_length()))                         # (4) O(V² log V)
    return min(karger_once(n, edges) for _ in range(trials))
```

1. Random edge order is the only randomization needed.
2. Contracting an edge merges its endpoints into a single supernode (DSU does it for us in near-`O(α(n))` per op).
3. After all but 2 supernodes remain, count original edges still crossing the supernode boundary.
4. **Probability one trial finds the min-cut:** `≥ 2 / (n · (n − 1)) ≈ 2/n²`. Repeat `O(n² log n)` times → success probability `≥ 1 − 1/n`.

The runtime per trial is `O(E α(V)) ≈ O(E)`. Total: `O(E · V² log V)` — slower than Stoer-Wagner asymptotically, but each trial is independent and embarrassingly parallel.

### Flavor 4: Schwartz-Zippel & polynomial identity testing

**Question:** are two polynomials `P(x₁, …, xₙ)` and `Q(x₁, …, xₙ)` identical? Symbolic comparison is exponential. Schwartz-Zippel: evaluate at a random point in a large field. If they differ, the random point detects it with probability `≥ 1 − d/|S|` where `d` is degree and `S` is the sample set.

```python
def polys_equal(P, Q, num_vars: int, degree: int, trials: int = 30) -> bool:
    """P, Q are functions taking a tuple of `num_vars` ints; check if P ≡ Q."""
    field_size = 10 ** 18 + 9                                          # large prime
    for _ in range(trials):
        pt = tuple(random.randint(0, field_size - 1) for _ in range(num_vars))
        if P(*pt) % field_size != Q(*pt) % field_size:
            return False                                              # certificate of inequality
    return True                                                       # probably equal
```

**Why it works:** a non-zero polynomial of total degree `d` has at most `d · |S|^(n−1)` zeros in `S^n`. With `|S| = 10¹⁸`, a single random evaluation finds a difference with overwhelming probability. `trials = 30` over a field of size `10¹⁸` gives essentially `2^(−500)` failure.

Used in: **bipartite matching via Tutte matrix determinant**, **edit-distance via polynomial multiplication**, **string equality via polynomial fingerprints (Rabin-Karp)**, **Merkle-tree diff in Git** (a hash *is* a fingerprint).

---

## 🔍 Sub-pattern at-a-glance

| # | Algorithm                       | Type           | Runtime                     | Failure prob               | Key idea                                          |
|---|---------------------------------|----------------|-----------------------------|----------------------------|---------------------------------------------------|
| 1 | Randomised quicksort/select     | Las Vegas      | O(n log n) / O(n) expected  | 0 (correctness)            | Random pivot breaks adversarial inputs            |
| 2 | Treaps                          | Las Vegas      | O(log n) expected per op    | 0                          | Random priority = expected balance                |
| 3 | Skip lists                      | Las Vegas      | O(log n) expected           | 0                          | Random level = expected balance                   |
| 4 | Karger / Karger-Stein min-cut   | Monte Carlo    | O(V² log³ V) (Karger-Stein) | 1/V (boost by repeating)   | Random edge contraction                           |
| 5 | Miller-Rabin primality          | Monte Carlo    | O(k log³ n)                 | 4^(−k)                     | Witness via square-root chain                     |
| 6 | Schwartz-Zippel / fingerprinting| Monte Carlo    | O(d) per eval               | d / \|S\|                  | Polynomial zeros are rare in a big field          |
| 7 | Reservoir / random sample       | Las Vegas      | O(n)                        | 0 (uniformity exact)       | Per-step probability `k/n`                        |
| 8 | Random projection / JL lemma    | Monte Carlo    | O(n d k)                    | δ                          | Distance-preserving dim reduction                 |
| 9 | Probabilistic method            | Existence proof| —                           | —                          | `E[X] > 0 ⇒ ∃ instance with X > 0`              |
| 10| Algorithmic Lovász Local Lemma  | Las Vegas      | Expected poly               | 0                          | Resampling fixes bad events independently         |

---

## 📚 20 problems where randomization is the canonical answer

| #  | Source        | Problem                                              | Difficulty | Pattern                  | Key insight                                                            |
|----|---------------|------------------------------------------------------|------------|--------------------------|------------------------------------------------------------------------|
| 1  | LC 215        | Kth Largest Element                                  | Medium     | Quickselect              | Random pivot Hoare partition, recurse one side.                        |
| 2  | LC 973        | K Closest Points to Origin                           | Medium     | Quickselect              | Same skeleton on a comparator over distance.                           |
| 3  | LC 384        | Shuffle an Array                                     | Medium     | Fisher-Yates             | `swap(i, randint(0, i))` produces uniform permutations.                |
| 4  | LC 528        | Random Pick with Weight                              | Medium     | Prefix sums + binary search | `bisect_left` on cumulative weights with `random()`.               |
| 5  | LC 470        | Implement Rand10 from Rand7                          | Medium     | Rejection sampling       | Generate uniform in a range; reject overflow region.                   |
| 6  | LC 398        | Random Pick Index                                    | Medium     | Reservoir sampling       | Single-pass sampling without storing positions.                        |
| 7  | LC 380        | Insert Delete GetRandom O(1)                         | Medium     | Hash + dynamic array     | Index-keyed hashmap to allow O(1) random access.                       |
| 8  | LC 381        | Insert Delete GetRandom O(1) — Duplicates allowed    | Hard       | Hash of sets + array     | Same trick with multiset of indices per value.                         |
| 9  | LC 382        | Linked List Random Node                              | Medium     | Reservoir sampling       | Stream over the list with k=1 reservoir.                               |
| 10 | LC 519        | Random Flip Matrix                                   | Medium     | Lazy Fisher-Yates        | Map index → value with hashmap; emulate shuffled array.                |
| 11 | LC 710        | Random Pick with Blacklist                           | Hard       | Lazy Fisher-Yates        | Remap blacklisted slots to whitelisted suffix.                         |
| 12 | LC 478        | Generate Random Point in a Circle                    | Medium     | Rejection sampling       | Sample uniform in bounding square; reject outside circle.              |
| 13 | LC 528        | Random Pick with Weight (variant)                    | Medium     | CDF                      | Cumulative-distribution + binary search.                               |
| 14 | LC 1117       | Building H2O (concurrency, but uses randomization)   | Medium     | Coordination             | Sometimes randomization replaces locks (lock-free skip lists).         |
| 15 | Industry      | Bloom-filter hash family                              | —          | Universal hashing        | `(a*x + b) mod p mod m` with random a, b is 2-universal.               |
| 16 | Industry      | Consistent hashing (Karger-style)                    | —          | Random ring              | Hash nodes and keys to a ring; random placement = balanced load.       |
| 17 | Industry      | Dynamic perfect hashing (Cuckoo)                     | —          | Random hash + retry      | Two hash functions; on collision evict and re-insert; rebuild on cycle.|
| 18 | Industry      | RSA / DSA key generation                              | —          | Miller-Rabin             | Generate random `b`-bit candidate; test primality; retry.              |
| 19 | Industry      | Distributed leader election (Bully / Paxos)          | —          | Random tie-breaks        | Random IDs avoid livelock when nodes have equal priority.              |
| 20 | LC 1206       | Design Skiplist                                      | Hard       | Skip list                | Random level for each node; expected `O(log n)` ops without rotations. |

---

## 🔬 Deep-dive 1 — Why random pivot makes quicksort `O(n log n)` expected

Let `T(n)` be the expected running time of randomised quicksort on `n` distinct elements. The pivot is uniform among the `n` elements; it lands at rank `r ∈ {1, …, n}` with probability `1/n`. The two recursive calls handle ranks `{1, …, r−1}` and `{r+1, …, n}`. So:

`T(n) = n + (1/n) · Σ_{r=1}^{n} (T(r − 1) + T(n − r))`
     `= n + (2/n) · Σ_{r=0}^{n−1} T(r)`.

**Solving this recurrence** (multiply both sides by `n`, subtract the `n−1` version, and divide):

`n · T(n) − (n−1) · T(n−1) = n² − (n−1)² + 2 · T(n−1)`
`⇒ T(n) / (n+1) − T(n−1) / n = 2 · (2n − 1) / (n(n+1))`.

This telescopes — `T(n) / (n+1) = Σ_{k=2}^{n} 2(2k−1)/(k(k+1)) ≈ 2 · ln n`. Hence `T(n) ≈ 2(n+1) ln n = O(n log n)`.

**Variance:** also `O(n log n)` by similar analysis. So with high probability the actual runtime is within a constant factor of expected — pathological inputs are exponentially rare.

---

## 🔬 Deep-dive 2 — Karger's success probability bound

**Claim:** the probability that one trial of Karger's contracts the min-cut down to the final 2 supernodes is `≥ 2 / (n(n−1))`.

**Proof sketch:** Let `C` be a fixed min-cut of size `k`. The graph has `n` vertices and at least `nk/2` edges (every vertex has degree `≥ k`, else there's a smaller cut). The probability that the *first* random edge contracted is **not** in `C`:

`P(first edge ∉ C) ≥ 1 − k / (nk/2) = 1 − 2/n`.

After one safe contraction, the graph has `n − 1` supernodes and the min-cut is still `k`. By induction:

`P(no C-edge contracted in `n−2` rounds) ≥ ∏_{i=0}^{n−3} (1 − 2/(n − i)) = 2 / (n(n−1))`.

**Boosting:** repeat `T = c · n(n−1)/2 · ln n` times. Probability all trials fail: `(1 − 2/(n(n−1)))^T ≤ e^(−c ln n) = 1/n^c`. With `c = 2`, success probability `≥ 1 − 1/n²`.

This is the **canonical example** of converting a low-probability single-trial Monte Carlo into a high-probability one by repetition. The trick is that `O(V² log V)` independent trials parallelise perfectly across `V²` cores → `O(E log V)` wall-clock.

**Karger-Stein** speeds this up to `O(V² log³ V)` total by recursively halving the graph at carefully chosen sizes — a textbook divide-and-conquer-on-randomized-recursion result.

---

## 🔬 Deep-dive 3 — The probabilistic method on edge-colourings

**Theorem (Erdős):** every graph with `m` edges has a 2-edge-colouring with at least `m/2` "bichromatic" triangles… no, let's pick a cleaner one.

**Theorem (Erdős):** for every `n ≥ 3`, there exists a tournament on `n` vertices with no Hamiltonian path of monochromatic edges in a 2-colouring of size `o(2^n / n)`. (Tournaments are complete graphs with directed edges — used in election theory and game theory.)

**Cleaner classic — `R(k, k) > 2^(k/2)`**: the Ramsey number `R(k, k)` is at least `2^(k/2)`, meaning there exists a 2-edge-colouring of `K_n` with `n = ⌊2^(k/2)⌋` containing **no monochromatic `K_k`**.

**Proof:** colour each edge of `K_n` red or blue independently with probability 1/2. Fix any `k`-vertex subset. The probability that *all* `C(k, 2)` edges among it are the same colour is `2 · 2^(−C(k,2))`. By union bound, the probability that *some* `k`-subset is monochromatic is at most:

`C(n, k) · 2^(1 − C(k, 2)) ≤ n^k / k! · 2^(1 − k(k−1)/2)`.

For `n = 2^(k/2)` and `k ≥ 3`, this is `< 1`. So with positive probability, the random colouring has **no** monochromatic `K_k` — hence such a colouring exists.

**Why this matters algorithmically:** the bound is tight up to lower-order factors, but no *constructive* proof gets close — finding such a colouring deterministically is open. The probabilistic method *proves existence* and bounds quantities; making it constructive is a research programme (Lovász Local Lemma, derandomization via conditional expectation).

The pattern: **define a random object, compute the expected value of an indicator, use Markov/union bound to show the desired event has positive probability.**

---

## 🐛 Common bugs

1. **Quickselect using `<` instead of `≤` in the partition.** With duplicates, strict comparison loops forever on all-equal arrays. Use Hoare's careful `while a[i] < pivot: i += 1` and `while a[j] > pivot: j -= 1` (strict on both sides), then swap.
2. **Random pivot taken with `random.randint(lo, hi)` but **then** used as an index instead of a value.** Pick the value `a[random.randint(lo, hi)]`; the index moves during partition.
3. **Miller-Rabin with `k = 1`.** Single round catches `≥ 75%` of composites — Carmichael-like numbers can fool a single `a`. Always `k ≥ 20`.
4. **Karger's not deduplicating contracted self-loops.** When you contract `u-v`, edges between `u`-and-its-neighbours and `v`-and-its-neighbours that connect to the same neighbour become **parallel edges**. Keep them — that's how min-cut detection works. But `u-v` itself becomes a self-loop; remove it.
5. **Schwartz-Zippel using too small a field.** `random.randint(0, 100)` for polynomials of degree 50 has failure probability up to 50%. Use a field of size `≥ 100 d`, ideally a 60-bit prime.
6. **Rabin-Karp using non-prime modulus or fixed seed.** Adversaries who know your modulus can craft hash collisions. Use random `base` and prime `modulus`, or two independent hashes.
7. **Reservoir sampling using `randint(1, i)` instead of `randint(0, i)`.** Off-by-one — must include 0.
8. **`random.shuffle()` for security.** Python's `random` is Mersenne Twister — predictable from a few outputs. Use `secrets.SystemRandom()` for crypto.
9. **Fisher-Yates implemented as `swap(randint(0, n-1), randint(0, n-1))` repeatedly.** Wrong. The correct loop is `for i in range(n-1, 0, -1): swap(a[i], a[randint(0, i)])` — only `n − 1` swaps and uniform output.
10. **Treaps / skip lists with non-uniform random priorities.** If priorities are biased, expected height drifts away from `O(log n)`. Use uniform `random.random()` floats or 64-bit ints.

---

## 🗣️ Interviewer phrasings to recognize

- "Find the median / kth element in `O(n)`" → **quickselect** (random pivot).
- "Generate primes for RSA" → **Miller-Rabin**.
- "Find the minimum number of edges to disconnect this graph" → **Karger** (or Stoer-Wagner / max-flow).
- "Are these two polynomials / strings / trees equivalent?" → **fingerprinting / Schwartz-Zippel**.
- "Sample a random row from a billion-row table" → **reservoir** or block sampling.
- "Shuffle this array uniformly" → **Fisher-Yates**.
- "Build a balanced BST without rebalancing logic" → **treap** (random priorities).
- "Distribute keys across nodes evenly with no coordination" → **consistent hashing**.

---

## 🧭 Connections to other patterns

- **[Treaps & Skip Lists](../05-advanced/08-treaps-skip-lists.md)** — both rely on randomization for expected balance. Treaps use random priorities; skip lists use random levels.
- **[Online Algorithms & Sketches](05-online-sketches.md)** — Bloom filters, Count-Min, and HyperLogLog are all Monte Carlo data structures.
- **[Hash Tables](../02-data-structures/hash-tables/01-hash-table-basics.md)** — universal hashing uses randomization to defeat adversarial keys.
- **[Computational Geometry](03-computational-geometry.md)** — random incremental construction (RIC) for convex hull, Delaunay triangulation, and half-plane intersection achieves expected `O(n log n)` with simple code.
- **[Max-Flow / Min-Cut](02-max-flow-min-cut.md)** — Karger / Karger-Stein give *unweighted, undirected* min-cut directly without flow machinery.
- **Cryptography** — most modern crypto (RSA, ElGamal, ECDSA, AES nonces) uses Monte Carlo primitives (Miller-Rabin, randomized padding, IVs).

---

## ✅ Self-check — 8 questions

??? question "1. State the difference between Las Vegas and Monte Carlo with one canonical example each."
    Las Vegas: output is always correct, runtime is random. Example: randomised quicksort — sorts correctly always, expected `O(n log n)` runtime. Monte Carlo: runtime is bounded, output may be wrong with bounded probability. Example: Miller-Rabin — fixed `O(k log³ n)` runtime, may declare a composite "prime" with probability `≤ 4^(−k)`.

??? question "2. Why is randomised quicksort `O(n log n)` expected even though worst-case is `O(n²)`?"
    The expected runtime recurrence `T(n) = n + (2/n) · Σ T(r)` solves to `T(n) ≈ 2(n+1) ln n`. Crucially, the "worst-case input" doesn't trigger worst-case runtime — only the random pivot sequence does, and the probability of consistently bad pivots is exponentially small. There is no input that an adversary can craft to make randomised quicksort slow (without learning the seed).

??? question "3. Walk through one Miller-Rabin round on `n = 561`."
    `n − 1 = 560 = 2^4 · 35`, so `s = 4, d = 35`. Pick `a = 2`. Compute `2^35 mod 561`. (`2^35 = 34359738368`; `34359738368 mod 561 = 263`.) `263 ≠ 1` and `263 ≠ 560`. Square: `263² mod 561 = 166`. Not 560. Square: `166² mod 561 = 67`. Not 560. Square: `67² mod 561 = 1`. Not 560 — and we squared from a non-(±1) and got 1, witnessing a non-trivial sqrt of 1, so 561 is composite. (561 = 3 · 11 · 17, a Carmichael number — fools Fermat but not Miller-Rabin.)

??? question "4. Why does Karger's contract random edges instead of, say, the lowest-degree edge?"
    Because the *deterministic* choice (lowest-degree, etc.) can be fooled by adversarial graphs. The probability bound `2/(n(n−1))` requires uniform random selection — any deterministic rule would have adversarial inputs where every choice is bad. Karger-Stein refines: contract random edges *for early steps* (cheap), then recurse on smaller graphs for the late ones (where mistakes are more costly).

??? question "5. What's the failure probability of polynomial identity testing with `n` variables, degree `d`, evaluated at one random point in a field of size `|S|`?"
    By Schwartz-Zippel, a non-zero polynomial of total degree `d` has at most `d · |S|^(n−1)` zeros in `S^n`, so a random point in `S^n` is a zero with probability `≤ d/|S|`. Independent of `n`. With `|S| = 10¹⁸` and `d = 1000`, failure is `≤ 10⁻¹⁵` per test.

??? question "6. Why is the probabilistic method *not* a constructive proof, and when does that matter?"
    It proves "an object with property P exists" by showing `Pr[random object has P] > 0`, but doesn't provide an algorithm to find one. In practice it matters when (a) you need an explicit construction for use in a larger algorithm, and (b) when failure probability is low but not zero — a random sample might miss. The Lovász Local Lemma's algorithmic version (Moser-Tardos resampling) makes some probabilistic-method proofs constructive in expected polynomial time.

??? question "7. How do you turn a Monte Carlo with success probability `p` into one with success probability `1 − δ`?"
    Repeat `k = ⌈log(1/δ) / log(1/(1−p))⌉` independent trials; output success if any trial succeeds (for one-sided tests) or majority (for two-sided). For `p = 1/2`, `k = log₂(1/δ)` trials suffice. This is **probability amplification** — each independent trial multiplies failure probability.

??? question "8. Why does Fisher-Yates require `randint(0, i)` (inclusive of i) and not `randint(0, i-1)`?"
    Because we want each of `i+1` items to be the survivor at position `i` with equal probability `1/(i+1)`. The shuffled item at position `i` after the swap should be one of `a[0..i]` uniformly. `randint(0, i-1)` would never pick `a[i]` to stay — biased toward replacement.

---

> **Up next in Ultra-Advanced:** Game theory & alpha-beta — Sprague-Grundy theorem, Nim, minimax, alpha-beta pruning, and game-tree search foundations of chess engines.
