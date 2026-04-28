# 🎯 Patterns

> 20 patterns that solve 90% of LeetCode and 95% of interview problems.

<span class="phase-status phase-inprogress">Phase 5 — building out the canonical pattern pages</span>

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

</div>

---

## 🚧 Coming next

The remaining 11 patterns:

10. Subsets / Backtracking
11. Modified Binary Search
12. Top-K Elements
13. K-way Merge
14. Topological Sort
15. 0/1 Knapsack DP
16. Unbounded Knapsack DP
17. Fibonacci Numbers DP
18. Palindromic Subsequence DP
19. Longest Common Subsequence DP
20. Bitwise XOR

Every page follows the canonical shape pioneered by [Sliding Window](01-sliding-window.md).
