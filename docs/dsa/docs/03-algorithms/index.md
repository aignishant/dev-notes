# ⚙️ Algorithms

> The recipes that work on the boxes from [Data Structures](../02-data-structures/index.md).

<span class="phase-status phase-done">Phase 4 — Ten chapters live</span>

Algorithms are the *how*. Data structures are the *what*. This section covers every recipe you'll need: from O(n²) baselines you must beat, to the polynomial-time tricks that show up under pressure, to the bitmask DP that wins the hard rounds.

---

## 🧮 Core families

<div class="grid cards" markdown>

-   :material-sort: **[Sorting](01-sorting.md)**

    ---

    Bubble → insertion → merge → quick (Lomuto + Hoare) → heap → counting → radix → bucket. Stability, in-place, when each wins. Timsort internals, custom keys, external sort.

-   :material-magnify: **[Searching](02-searching.md)**

    ---

    Linear, binary (3 invariants — exact, leftmost, rightmost), ternary, exponential, interpolation. The "binary search on the answer" template. Five footguns to avoid.

-   :material-rotate-3d-variant: **[Recursion](03-recursion.md)**

    ---

    Stack frames, base case, recursion tree. Why Python skips TCO. Converting recursion to iteration with an explicit stack. Five common pitfalls.

-   :material-call-split: **[Divide & Conquer](04-divide-and-conquer.md)**

    ---

    The divide / conquer / combine recipe. Master Theorem with worked cases. Merge sort, quickselect, max subarray, closest pair, count inversions, fast exponentiation.

</div>

---

## 🧠 Optimisation paradigms

<div class="grid cards" markdown>

-   :material-table-large: **[Dynamic Programming](05-dynamic-programming.md)**

    ---

    The 5 DP shapes — 1D linear, 2D grid, interval, knapsack, string. Top-down (`@cache`) vs bottom-up vs space-optimised. State definition rule. Coin Change, LIS (O(n log n)), Edit Distance, House Robber II.

-   :material-medal: **[Greedy](06-greedy.md)**

    ---

    Greedy choice + optimal substructure. Exchange-argument proofs. Activity selection, fractional knapsack, Huffman, Jump Game, Gas Station, Task Scheduler. When greedy fails — and the counter-examples that prove it.

</div>

---

## 🌐 Specialised algorithms

<div class="grid cards" markdown>

-   :material-graph: **[Graph algorithms](07-graph-algorithms.md)**

    ---

    BFS, DFS, topological sort (Kahn + DFS), Dijkstra, Bellman-Ford, Floyd-Warshall, A\*, Prim, Kruskal, Tarjan SCC, bridges, articulation points. Plus 4 worked interview problems.

-   :material-format-letter-matches: **[String algorithms](08-string-algorithms.md)**

    ---

    Naive baseline, KMP (with failure-function derivation), Rabin-Karp (rolling hash), Z-algorithm, suffix arrays, Aho-Corasick (multi-pattern), Manacher's. The decision tree for which to use.

-   :material-calculator-variant: **[Math algorithms](09-math-algorithms.md)**

    ---

    GCD + extended Euclid, modular arithmetic + inverse, fast exponentiation, Sieve of Eratosthenes, primality (Miller-Rabin), factorisation, nCr mod p, Catalan, matrix exponentiation for linear recurrences.

-   :material-numeric-1-box-multiple: **[Bit manipulation](10-bit-manipulation.md)**

    ---

    The bit-tricks table. XOR applications. Bitmask subset iteration. Bitmask DP (TSP, subset-sum). Python-specific gotchas (arbitrary precision, `& 0xFFFFFFFF` for 32-bit emulation).

</div>

---

## ⚡ The fastest tour

If you only have an evening:

1. Skim **Sorting** for the comparison table — you should be able to recite it cold.
2. Master the 3 binary-search invariants in **Searching** — they show up in 30% of mediums.
3. Read the 5 DP shapes in **Dynamic Programming** — recognise the shape, the code follows.
4. Memorise BFS/DFS/Dijkstra/topo-sort templates from **Graph algorithms**.

Everything else rewards depth over speed.
