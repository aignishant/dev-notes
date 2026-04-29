# 🧠 Ultra-Advanced

> The "you probably won't be asked this, but if you are, you'll be the only candidate who can solve it" topics.

<span class="phase-status phase-inprogress">Phase 7 — building out the ultra-advanced chapter</span>

Each page in this section follows the **same shape** as [Advanced](../05-advanced/index.md): plain-English signal → multiple flavors → sub-patterns table → 20-problem table → three deep-dives → bugs → interviewer phrasings → connections → 8 self-checks.

---

## ✅ Available now

<div class="grid cards" markdown>

-   :material-history: **[Persistent Data Structures](01-persistent-data-structures.md)**

    ---

    Path-copying for `O(log n)` versioned updates. Persistent segment tree for kth-smallest in `arr[l..r]` (SPOJ MKTHNUM), persistent trie for max-XOR in window, persistent arrays via HAMT, persistent treap. The backbone of immutable functional collections.

-   :material-water-pump: **[Max-Flow / Min-Cut](02-max-flow-min-cut.md)**

    ---

    Edmonds-Karp `O(VE²)`, Dinic's `O(V²E)` (and `O(E √V)` on unit caps for bipartite matching). Reverse-edge trick, max-flow / min-cut duality, project-selection closure problem, vertex-disjoint paths via vertex splitting. Solves dozens of seemingly-unrelated problems by reduction.

-   :material-vector-triangle: **[Computational Geometry](03-computational-geometry.md)**

    ---

    Cross-product orientation tests, Andrew's monotone-chain convex hull `O(n log n)`, Bentley-Ottmann segment-intersection sweep, closest-pair sweep, ray-casting point-in-polygon, shoelace area, KD-tree nearest-neighbour. The toolkit for every 2D-coordinate interview problem — robust integer primitives plus sweep-line thinking.

-   :material-table-large: **[Advanced DP](04-advanced-dp.md)**

    ---

    Digit DP for "count integers in `[L, R]` with property P", bitmask DP for `n ≤ 20` visit/assign/partition problems, rerooting tree DP for "answer at every vertex" in `O(n)`, SOS DP for `Σ_{T ⊆ S} a[T]` in `O(n · 2ⁿ)`, plus Knuth and convex-hull-trick optimisations. The DP-tier-hard toolkit.

-   :material-waveform: **[Online Algorithms & Sketches](05-online-sketches.md)**

    ---

    Two-heap sliding-window median (`O(log k)` exact), Reservoir sampling for uniform stream samples, Count-Min sketch for approximate frequencies (`ε · ||a||₁` additive error), HyperLogLog for cardinality at ~`1.04/√m` standard error in 16 KB, Bloom filter for set-membership with one-sided FPR, Misra-Gries heavy hitters. The streaming-systems toolkit.

-   :material-dice-multiple: **[Randomised Algorithms](06-randomised-algorithms.md)**

    ---

    Las Vegas (random runtime, exact output) vs Monte Carlo (fixed runtime, bounded-error output). Randomised quickselect `O(n)` expected, Miller-Rabin primality with `4^(−k)` failure, Karger min-cut via random edge contraction with `2/(n(n−1))` per-trial success bound, Schwartz-Zippel polynomial identity testing, the probabilistic method, and Fisher-Yates. The "coin flips beat cleverness" toolkit.

</div>

---

## 🚧 Coming next

The remaining ultra-advanced topics:

7. **Game theory & alpha-beta** — Sprague-Grundy, minimax pruning, game-tree search

Each will follow the canonical shape pioneered by [Persistent Data Structures](01-persistent-data-structures.md).
