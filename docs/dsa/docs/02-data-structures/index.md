# 📦 Data Structures

> The boxes you put data into. Pick the right box, the algorithm is half-solved.

<span class="phase-status phase-done">Phase 2 — Linear / Hash / Tree / Heap / Graph chapters live</span>

Every algorithm in [the next chapter](../03-algorithms/index.md) is just a recipe applied to one of these boxes. Choosing the right structure is half the interview.

---

## 🧱 Linear

<div class="grid cards" markdown>

-   :material-numeric: **Arrays**

    ---

    - [Array basics](arrays/01-array-basics.md) — 40+ problems, the gold-standard sample chapter.
    - [Prefix sums & difference arrays](arrays/02-prefix-sum-difference.md) — 1D/2D prefix, range-update difference arrays, the prefix + hashmap idiom.

-   :material-format-quote-close: **Strings**

    ---

    - [String basics](strings/01-string-basics.md) — immutability, slicing, Python idioms.
    - [Pattern matching (KMP, Z, Rabin-Karp)](strings/02-string-pattern-matching.md) — substring search, the failure function.

-   :material-link-variant: **Linked Lists**

    ---

    - [Linked list basics](linked-lists/01-linked-list-basics.md) — singly linked, dummy heads, fast/slow pointers.
    - [Advanced linked lists](linked-lists/02-advanced-linked-lists.md) — DLL with sentinels, circular, skip list, random-pointer copy.

-   :material-stack-overflow: **Stacks & Queues**

    ---

    - [Stacks and queues basics](stacks-and-queues/01-stacks-and-queues-basics.md) — LIFO / FIFO / deque.
    - [Monotonic stack & queue](stacks-and-queues/02-monotonic-stack-queue.md) — next-greater patterns, sliding-window max, histogram.

</div>

---

## 🔑 Hash-based

<div class="grid cards" markdown>

-   :material-key-variant: **Hash Tables**

    ---

    - [Hash table basics](hash-tables/01-hash-table-basics.md) — dict / set, collision counting, idioms.
    - [Hash internals](hash-tables/02-hash-internals.md) — chaining vs open addressing, Robin Hood, cuckoo, consistent hashing.

</div>

---

## 🌳 Tree-based

<div class="grid cards" markdown>

-   :material-file-tree: **Trees**

    ---

    - [Tree basics](trees/01-tree-basics.md) — binary tree fundamentals, recursive thinking.
    - [Binary Search Trees](trees/02-binary-search-trees.md) — invariant, the 3 delete cases, validation, inorder.
    - [Tree traversals](trees/03-tree-traversals.md) — pre/in/post/level (recursive + iterative), Morris, serialize.

</div>

For balanced trees, segment trees, BIT, and tries see [Advanced](../05-advanced/index.md).

---

## ⛰️ Heap-based

<div class="grid cards" markdown>

-   :material-chart-arc: **Heaps**

    ---

    - [Heap basics](heaps/01-heap-basics.md) — heap property, `heapq`, max-heap via negation, top-K, two-heap median.

</div>

---

## 🌐 Graph-based

<div class="grid cards" markdown>

-   :material-graph-outline: **Graphs**

    ---

    - [Graph basics](graphs/01-graph-basics.md) — vocabulary, three representations, BFS/DFS, grid-as-graph, bipartite.

</div>

For BFS/DFS/Dijkstra/Bellman-Ford/Floyd-Warshall/A\*/MST/SCC depth see [Algorithms — Graph algorithms](../03-algorithms/07-graph-algorithms.md).

---

## ⚡ The fastest tour

If you only have an evening:

1. Read the **Arrays basics** sample — it's the template every other chapter follows.
2. Skim **Hash internals** — collision strategies show up in 30% of system-design rounds.
3. Read **Heap basics** — the API is small but the problems are everywhere.
4. Skim **Graph basics** — every graph problem starts here.

Everything else rewards depth over speed.
