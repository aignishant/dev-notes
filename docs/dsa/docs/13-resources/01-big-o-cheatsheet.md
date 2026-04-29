# Big-O Cheatsheet

> Every data structure, every operation, average and worst case. The single page you skim the night before.

<span class="phase-status phase-done">Phase 14 — Resources</span>

---

## Common operations by data structure

| Data structure | Access | Search | Insert | Delete | Notes |
|---|---|---|---|---|---|
| **Array (fixed)** | O(1) | O(N) | — | — | Random access; can't grow |
| **Dynamic array / list** | O(1) | O(N) | O(1) amort end / O(N) middle | O(N) | Python `list`, Java `ArrayList` |
| **Linked list (singly)** | O(N) | O(N) | O(1) at head / O(N) tail | O(1) given node ref | Cache-unfriendly |
| **Linked list (doubly)** | O(N) | O(N) | O(1) given node ref | O(1) given node ref | LRU pattern |
| **Stack** | — | O(N) | O(1) | O(1) | LIFO |
| **Queue** | — | O(N) | O(1) | O(1) | FIFO; `collections.deque` |
| **Hash map / dict** | — | O(1) avg / O(N) worst | O(1) avg | O(1) avg | Worst case = collision storm |
| **Hash set** | — | O(1) avg | O(1) avg | O(1) avg | |
| **Binary search tree** | O(log N) avg / O(N) | O(log N) avg / O(N) | O(log N) avg / O(N) | O(log N) avg / O(N) | Worst when degenerate |
| **Balanced BST (AVL/RB)** | O(log N) | O(log N) | O(log N) | O(log N) | TreeMap / set in Java/C++ |
| **Heap (binary)** | — | O(N) | O(log N) | O(log N) min/max | `heapq` is min-heap |
| **Trie** | — | O(L) | O(L) | O(L) | L = key length |
| **Skip list** | — | O(log N) avg | O(log N) avg | O(log N) avg | Redis sorted sets |
| **Disjoint set (union-find)** | — | α(N) ≈ O(1) | α(N) | — | Path compression + rank |
| **B-tree / B+tree** | — | O(log N) | O(log N) | O(log N) | Disk-based DBs |
| **LSM tree** | — | O(log N) per level | O(1) memtable | O(log N) tombstone | Cassandra, RocksDB |
| **Bloom filter** | — | O(K) constant | O(K) | — | False positives only |
| **Count-min sketch** | — | O(K) | O(K) | — | Approximate counts |

---

## Sorting algorithms

| Algorithm | Best | Average | Worst | Space | Stable | Notes |
|---|---|---|---|---|---|---|
| **Bubble** | O(N) | O(N²) | O(N²) | O(1) | ✓ | Don't use |
| **Insertion** | O(N) | O(N²) | O(N²) | O(1) | ✓ | Best for nearly-sorted small N |
| **Selection** | O(N²) | O(N²) | O(N²) | O(1) | ✗ | Don't use |
| **Merge** | O(N log N) | O(N log N) | O(N log N) | O(N) | ✓ | Linked-list-friendly |
| **Quick** | O(N log N) | O(N log N) | O(N²) | O(log N) avg | ✗ | Pivot kills it on sorted input |
| **Heap** | O(N log N) | O(N log N) | O(N log N) | O(1) | ✗ | In-place; no recursion |
| **Counting** | O(N+K) | O(N+K) | O(N+K) | O(K) | ✓ | Integers in known range |
| **Radix** | O(NK) | O(NK) | O(NK) | O(N+K) | ✓ | Integers/strings; K = digit count |
| **Bucket** | O(N+K) | O(N+K) | O(N²) | O(N) | ✓ | Uniform distribution |
| **Tim** (Python `sort`) | O(N) | O(N log N) | O(N log N) | O(N) | ✓ | Real-world champion |

---

## Graph algorithms

| Algorithm | Time | Space | Use case |
|---|---|---|---|
| **BFS** | O(V + E) | O(V) | Unweighted shortest path; level order |
| **DFS** | O(V + E) | O(V) | Topological sort; cycle detect; SCC |
| **Dijkstra (heap)** | O((V+E) log V) | O(V) | Non-negative weights |
| **Bellman-Ford** | O(VE) | O(V) | Negative weights; cycle detect |
| **Floyd-Warshall** | O(V³) | O(V²) | All-pairs shortest path |
| **A\*** | O(E) best / exponential worst | O(V) | Heuristic-guided search |
| **Prim's MST** | O((V+E) log V) | O(V) | Min spanning tree (dense) |
| **Kruskal's MST** | O(E log E) | O(V) | Min spanning tree (sparse) |
| **Tarjan / Kosaraju SCC** | O(V + E) | O(V) | Strongly connected components |
| **Topological sort** | O(V + E) | O(V) | DAG ordering |
| **Edmonds-Karp (max flow)** | O(VE²) | O(V²) | Max flow / min cut |

---

## Common DP complexities

| Problem class | Typical complexity | Examples |
|---|---|---|
| **1D linear DP** | O(N) time, O(N) or O(1) space | Fibonacci, climb stairs, max subarray |
| **2D grid DP** | O(MN) | Edit distance, LCS, unique paths |
| **Knapsack** | O(NW) | 0/1 knapsack, partition equal subset |
| **Interval DP** | O(N³) | Matrix chain, burst balloons |
| **Bitmask DP** | O(N · 2^N) | TSP, assignment |
| **Tree DP** | O(N) | House robber III, max path sum |
| **Digit DP** | O(D · 10 · 2 · K) | Count numbers with property |

---

## String algorithms

| Algorithm | Time | Space | Use case |
|---|---|---|---|
| **Naive substring** | O(NM) | O(1) | Tiny inputs |
| **KMP** | O(N + M) | O(M) | Single pattern |
| **Boyer-Moore** | O(NM) worst, O(N/M) best | O(σ + M) | Long patterns, large alphabet |
| **Rabin-Karp** | O(N + M) avg | O(1) | Multiple patterns / rolling hash |
| **Z-algorithm** | O(N + M) | O(N + M) | Pattern matching, periods |
| **Aho-Corasick** | O(N + M + Z) | O(M·σ) | Multi-pattern dictionary |
| **Suffix array build** | O(N log N) | O(N) | Substring queries |
| **Suffix automaton** | O(N) | O(N·σ) | All distinct substrings |
| **Manacher** | O(N) | O(N) | All palindromic substrings |

---

## How to estimate the bound for a problem

| Input size N | Acceptable | Tight | Too slow |
|---|---|---|---|
| N ≤ 10 | O(N!) | O(2^N) | — |
| N ≤ 20 | O(2^N) | O(N · 2^N) | O(N!) |
| N ≤ 100 | O(N⁴) | O(N³) | O(2^N) |
| N ≤ 1000 | O(N³) | O(N²) | O(N⁴) |
| N ≤ 10⁵ | O(N²) | O(N log N) | O(N³) |
| N ≤ 10⁶ | O(N log N) | O(N) | O(N²) |
| N ≤ 10⁸ | O(N) | O(log N) / O(1) | O(N log N) |
| N ≤ 10¹² | O(√N) | O(log N) | O(N) |
| N ≤ 10¹⁸ | O(log N) | O(1) | O(√N) |

Rule of thumb: a modern CPU executes ~10⁸ simple operations / second. Your time budget × 10⁸ ≈ how many ops you can afford.

---

## Common gotchas

- **`O(N)` vs `O(N) amortised`**: Python `list.append` is amortised O(1). One specific append might be O(N) on resize.
- **Hash map worst case**: O(N) on collision storm. Don't rely on O(1) for adversarial input.
- **Recursive depth**: Python recursion limit ~1000. For deep recursion, convert to iterative or use `sys.setrecursionlimit`.
- **Sorting + binary search vs hash**: Sorting + binary search = O(N log N + log N). Hash = O(N + 1). Hash wins unless you need order.
- **Python `in` on list**: O(N). On set/dict: O(1) avg. Choose accordingly.
- **String concatenation in loop**: O(N²) in Python with `s += x`. Use `''.join(parts)` for O(N).
- **Slicing**: `arr[i:j]` is O(j-i) and copies. Use indices for in-place algorithms.

---

## Master Theorem (recurrence shortcuts)

For T(N) = a · T(N/b) + f(N):

| Case | Condition | Result |
|---|---|---|
| 1 | f(N) = O(N^c), c < log_b(a) | T(N) = Θ(N^log_b(a)) |
| 2 | f(N) = Θ(N^c · log^k N), c = log_b(a) | T(N) = Θ(N^c · log^(k+1) N) |
| 3 | f(N) = Ω(N^c), c > log_b(a) | T(N) = Θ(f(N)) |

Examples:
- Merge sort: T(N) = 2T(N/2) + N → case 2, k=0 → **Θ(N log N)**.
- Binary search: T(N) = T(N/2) + 1 → case 2 → **Θ(log N)**.
- Strassen: T(N) = 7T(N/2) + N² → case 1 → **Θ(N^log₂7) ≈ Θ(N^2.81)**.
