# 🚀 Advanced

> Topics that show up in senior interviews, ICPC-style rounds, and Google L5+ loops.

<span class="phase-status phase-done">Phase 6 — Complete (8 of 8 advanced data structures)</span>

Each page in this section follows the **same shape** pioneered by the [pattern bible](../04-patterns/index.md):

1. **What it is** (plain-English signal: *"if you see X, try this"*)
2. **Implementation(s)** in Python (multiple flavors where applicable)
3. **Sub-patterns** — every flavor in one place
4. **20 problems** that fit the structure
5. **Three deep-dive walkthroughs** demonstrating the canonical templates

---

## ✅ Available now

<div class="grid cards" markdown>

-   :material-file-tree-outline: **[Tries (Prefix Trees)](01-tries.md)**

    ---

    Dict-of-dicts vs TrieNode vs array-backed. Implement Trie (LC 208), Wildcard search (LC 211), Word Search II (LC 212), Bitwise trie for max XOR (LC 421).

-   :material-vector-union: **[Union-Find / DSU](02-union-find.md)**

    ---

    Path compression + union-by-rank in O(α(n)). Connected components (LC 547), Redundant Connection (LC 684), Accounts Merge (LC 721), Kruskal's MST, weighted DSU for LC 399 / 990.

-   :material-tree: **[Segment Trees](03-segment-trees.md)**

    ---

    Range query + point/range update in O(log n). Recursive vs iterative form, lazy propagation, coordinate compression. LC 307, LC 315, LC 732, LC 850.

-   :material-binary: **[Fenwick Tree (BIT)](04-fenwick-bit.md)**

    ---

    Eight-line BIT for point-update + prefix-sum in O(log n). The `i & -i` trick, range-update via difference arrays, two-BIT range-add + range-sum, and 2D BIT. LC 307, LC 315, LC 493.

-   :material-format-letter-matches: **[Suffix Arrays & Suffix Automata](05-suffix-arrays.md)**

    ---

    SA via doubling in O(n log² n), Kasai's LCP in O(n), and SAM as the all-substring automaton. Longest duplicate substring (LC 1044), longest common substring of k strings, all-distinct-substring count.

-   :material-graph-outline: **[Heavy-Light Decomposition](06-heavy-light-decomposition.md)**

    ---

    Decompose a tree into O(log n) heavy chains, lay them flat, answer path queries via segment tree in O(log² n). Vertex- vs edge-weighted, lazy-prop interaction, when DSU-on-tree replaces it.

-   :material-sigma: **[Mo's Algorithm](07-mo-algorithm.md)**

    ---

    Reorder offline range queries by `√n` buckets to amortise to O((n + q) √n). Vanilla, even/odd snake sort, Mo's with updates (n^(5/3)), Mo's on tree via Euler tour. SPOJ DQUERY, CF 86D Powerful Array.

-   :material-shuffle-variant: **[Treaps & Skip Lists](08-treaps-skip-lists.md)**

    ---

    Randomised balanced BSTs in <100 lines: priority-driven treap, implicit treap with split/merge for range surgery, geometric-level skip list for concurrent ordered maps, persistent treap via path-copying. The "I want a balanced BST without 400 lines of red-black" answer.

</div>

---

## 🎉 Phase 6 complete

All 8 advanced data structures are written. Continue with **🧠 [Ultra-Advanced](../06-ultra-advanced/index.md)** for the next chapter — persistent data structures, max-flow / min-cut, computational geometry, advanced DP, sketches, randomised algorithms, and game theory.
