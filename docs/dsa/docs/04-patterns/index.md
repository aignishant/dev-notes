# 🎯 Patterns

> 20 patterns that solve 90% of LeetCode and 95% of interview problems.

<span class="phase-status phase-done">Phase 5 — all 20 canonical pattern pages complete ✅</span>

Each pattern page in this section follows the **same five-part shape**:

1. **What the pattern looks like** (plain-English signal: *"if you see X, try this"*)
2. **The template code** in Python (fixed and variable flavors where applicable)
3. **The sub-patterns** — every flavor of the pattern in one place
4. **20+ problems** that fit the pattern, with difficulty + sub-pattern + status
5. **3 deep-dive walkthroughs** demonstrating the canonical templates

---

## ✅ Available now

<div class="grid cards" markdown>

-   :material-window-restore: **[Sliding Window](01-sliding-window.md)**

    ---

    Fixed vs variable windows. The 7 sub-patterns. Longest-substring-without-repeats, Min-window-substring, Sliding-window-maximum.

-   :material-arrow-left-right-bold: **[Two Pointers](02-two-pointers.md)**

    ---

    Opposite-ends, same-direction, merge-two-arrays, fast-and-slow. Trapping rain water, merge sorted array in-place, two-sum sorted.

-   :material-run-fast: **[Fast & Slow Pointers](03-fast-slow-pointers.md)**

    ---

    Floyd's tortoise & hare. Cycle detection, cycle entry algebra (`T = (k−1)·C + (C−M)`), happy number, find-middle.

-   :material-table-merge-cells: **[Merge Intervals](04-merge-intervals.md)**

    ---

    Sort + sweep. Sweep-line events. Insert-into-sorted. Meeting Rooms II, Insert Interval, Employee Free Time.

-   :material-sort-numeric-ascending: **[Cyclic Sort](05-cyclic-sort.md)**

    ---

    Place each value at its home index in O(n)/O(1). Missing Number, Find Duplicates, First Missing Positive (LC 41).

-   :material-link-variant: **[In-Place Linked List Reversal](06-in-place-linked-list-reversal.md)**

    ---

    Three-pointer relink in O(n)/O(1). Full reversal, sublist (LC 92), k-group (LC 25), palindrome, reorder, rotate.

-   :material-graph-outline: **[Tree BFS](07-tree-bfs.md)**

    ---

    Queue + level-snapshot trick. Level order, zigzag, right side view, minimum depth, LC 117 next-pointers in O(1) space.

-   :material-file-tree: **[Tree DFS](08-tree-dfs.md)**

    ---

    Top-down vs bottom-up vs iterative-stack. Path Sum II, Diameter (LC 543), Validate BST, LCA, Max Path Sum (LC 124).

-   :material-chart-bell-curve: **[Two Heaps](09-two-heaps.md)**

    ---

    Max-heap of small half + min-heap of large half. Median of stream (LC 295), Sliding Window Median (LC 480), IPO (LC 502).

-   :material-source-branch: **[Subsets & Backtracking](10-subsets-backtracking.md)**

    ---

    Choose / recurse / un-choose. Subsets, Permutations II with duplicate-skip, Palindrome Partitioning, N-Queens, Sudoku.

-   :material-magnify-scan: **[Modified Binary Search](11-modified-binary-search.md)**

    ---

    Lower/upper bound, rotated arrays (pick-the-sorted-half), and binary search on the answer space (Koko, ship packages).

-   :material-podium: **[Top-K Elements](12-top-k-elements.md)**

    ---

    Min-heap of size k for top-k largest, max-heap-via-negation for smallest, QuickSelect average O(n). Kth Largest (LC 215), K Closest Points (LC 973), Top K Frequent (LC 347 with bucket sort).

-   :material-call-merge: **[K-way Merge](13-k-way-merge.md)**

    ---

    Heap of `k` sorted-source cursors. Merge k Sorted Lists (LC 23), Smallest Range Covering K Lists (LC 632), Find K Pairs with Smallest Sums (LC 373).

-   :material-graph: **[Topological Sort](14-topological-sort.md)**

    ---

    Kahn's BFS (in-degree zero peel) and DFS post-order with three-colour cycle detection. Course Schedule (LC 207/210), Alien Dictionary (LC 269), Minimum Height Trees (LC 310).

-   :material-bag-personal: **[0/1 Knapsack DP](15-01-knapsack-dp.md)**

    ---

    The mother subset-DP. 2D `dp[i][w]` table → 1D rolling with right-to-left iteration. Partition Equal Subset (LC 416), Target Sum (LC 494), Last Stone Weight II (LC 1049).

-   :material-bag-personal-plus: **[Unbounded Knapsack DP](16-unbounded-knapsack-dp.md)**

    ---

    Items reusable. The single-character difference: iterate left-to-right. Coin Change (LC 322), Coin Change 2 (LC 518), Combination Sum IV (LC 377), Word Break (LC 139).

-   :material-numeric: **[Fibonacci Numbers DP](17-fibonacci-numbers-dp.md)**

    ---

    Linear 1D DP with constant lookback — collapses to O(1) space via two rolling variables. Climbing Stairs (LC 70), House Robber (LC 198/213), Decode Ways (LC 91).

-   :material-mirror: **[Palindromic Subsequence DP](18-palindromic-subsequence-dp.md)**

    ---

    Interval DP with diagonal-sweep fill order. Longest Palindromic Subsequence (LC 516), Longest Palindromic Substring (LC 5), Min Insertions to Palindrome (LC 1312), Min Cuts (LC 132).

-   :material-vector-link: **[Longest Common Subsequence DP](19-longest-common-subsequence-dp.md)**

    ---

    Canonical 2D two-sequence DP. LCS (LC 1143), Edit Distance (LC 72), Distinct Subsequences (LC 115), Shortest Common Supersequence (LC 1092), Interleaving String (LC 97), LIS-as-LCS (LC 300).

-   :material-xor: **[Bitwise XOR](20-bitwise-xor.md)**

    ---

    `x ^ x = 0` and the bit-tricks playbook. Single Number (LC 136/137/260), Missing Number (LC 268), Maximum XOR via bitwise trie (LC 421), Sum without `+` (LC 371), `n & (n-1)`, `n & -n`.

</div>

---

## 🎉 Bible complete

All 20 canonical patterns are now written. Every page follows the same five-part shape, pioneered by [Sliding Window](01-sliding-window.md). From here the journey continues with the [Advanced](../05-advanced/index.md), [Ultra-Advanced](../06-ultra-advanced/index.md), and [System Design](../08-system-design/index.md) sections.
