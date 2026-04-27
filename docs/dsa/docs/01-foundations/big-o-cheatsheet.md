# Big-O cheatsheet

> One-page reference. Bookmark this. Re-skim before every interview.

---

## Growth class hierarchy

From fastest to slowest:

```
O(1) < O(log n) < O(√n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)
```

For input size **n = 10⁶**:
| Big-O | Operations | Real-world feel |
|---|---|---|
| O(1) | 1 | instant |
| O(log n) | ~20 | instant |
| O(√n) | ~1,000 | instant |
| O(n) | 10⁶ | ~10 ms |
| O(n log n) | ~2 × 10⁷ | ~200 ms |
| O(n²) | 10¹² | hours (TLE) |
| O(2ⁿ) | not computable | astronomical |

---

## Python data structure cheat table

### `list`

| Operation | Time | Notes |
|---|---|---|
| `arr[i]` | O(1) | |
| `arr[i] = x` | O(1) | |
| `arr.append(x)` | O(1) amortized | |
| `arr.pop()` | O(1) | |
| `arr.pop(0)` | **O(n)** | use `deque.popleft()` |
| `arr.insert(0, x)` | **O(n)** | use `deque.appendleft()` |
| `arr.insert(i, x)` | O(n) | |
| `arr.remove(x)` | O(n) | |
| `x in arr` | O(n) | |
| `arr[i:j]` (slice) | O(j-i) | makes a copy |
| `len(arr)` | O(1) | |
| `arr.sort()` | O(n log n) | Timsort, in-place |
| `sorted(arr)` | O(n log n) | new list |
| `arr.count(x)` | O(n) | |
| `arr + other` | O(n + m) | |
| `arr * k` | O(n × k) | |

### `dict` / `set` (hash table)

| Operation | Time |
|---|---|
| `d[k]` (read) | O(1) avg, O(n) worst |
| `d[k] = v` | O(1) avg |
| `del d[k]` | O(1) avg |
| `k in d` | O(1) avg |
| `len(d)` | O(1) |
| Iteration | O(n) |

For interviews, always say **O(1)** for hash ops.

### `str`

Strings are immutable. Most ops produce a new string.

| Operation | Time |
|---|---|
| `s[i]` | O(1) |
| `s + t` | O(\|s\| + \|t\|) |
| `s += ch` in loop | **O(n²)** total — use `"".join(list)` |
| `sub in s` | O(\|s\| × \|sub\|) worst |
| `s.find(sub)` | O(\|s\| × \|sub\|) worst |
| `s.replace(a, b)` | O(\|s\|) |
| `s.split(sep)` | O(\|s\|) |
| `"".join(strs)` | O(total length) |
| `s.lower()` / `.upper()` | O(\|s\|) |

### `tuple`

Same as `list` for read; immutable so no add/remove.

### `collections.deque`

| Operation | Time |
|---|---|
| `d.append(x)` | O(1) |
| `d.appendleft(x)` | O(1) |
| `d.pop()` | O(1) |
| `d.popleft()` | O(1) |
| `d[i]` (random access) | **O(n)** |

Deque trades O(1) end-ops for O(n) middle access. Don't index a deque if you can avoid it.

### `heapq` (operates on a list)

| Operation | Time |
|---|---|
| `heappush(h, x)` | O(log n) |
| `heappop(h)` | O(log n) |
| `h[0]` (peek) | O(1) |
| `heapify(arr)` | **O(n)** |
| `nlargest(k, iter)` | O(n log k) |
| `nsmallest(k, iter)` | O(n log k) |

---

## Algorithm cheat table

### Sorting

| Algorithm | Time (avg) | Time (worst) | Space | Stable |
|---|---|---|---|---|
| **Timsort** (Python's) | O(n log n) | O(n log n) | O(n) | ✅ |
| Quicksort | O(n log n) | O(n²) | O(log n) | ❌ |
| Mergesort | O(n log n) | O(n log n) | O(n) | ✅ |
| Heapsort | O(n log n) | O(n log n) | O(1) | ❌ |
| Insertion sort | O(n²) | O(n²) | O(1) | ✅ |
| Bubble sort | O(n²) | O(n²) | O(1) | ✅ |
| Counting sort | O(n + k) | O(n + k) | O(n + k) | ✅ |
| Radix sort | O(n × d) | O(n × d) | O(n + b) | ✅ |

Python's `arr.sort()` is Timsort — best-of-most-worlds.

### Searching

| Algorithm | Input | Time | Space |
|---|---|---|---|
| Linear search | unsorted | O(n) | O(1) |
| Binary search | sorted | O(log n) | O(1) |
| Hash lookup | hashable key | O(1) avg | O(n) build |

### Tree operations (BST, balanced)

| Operation | Time |
|---|---|
| Search | O(log n) |
| Insert | O(log n) |
| Delete | O(log n) |
| In-order traversal | O(n) |

(Worst case for unbalanced BST is O(n).)

### Graph algorithms

| Algorithm | Time | Space |
|---|---|---|
| BFS | O(V + E) | O(V) |
| DFS | O(V + E) | O(V) for recursion stack |
| Topological sort | O(V + E) | O(V) |
| Dijkstra (with min-heap) | O((V + E) log V) | O(V) |
| Bellman-Ford | O(V × E) | O(V) |
| Floyd-Warshall | O(V³) | O(V²) |
| Prim's MST | O(E log V) | O(V) |
| Kruskal's MST | O(E log E) | O(V) |

V = vertices, E = edges.

### Common DP problems

| Problem | Time | Space (naïve) | Space (optimized) |
|---|---|---|---|
| Climb stairs / Fibonacci | O(n) | O(n) | O(1) |
| House robber | O(n) | O(n) | O(1) |
| Coin change | O(n × amount) | O(amount) | O(amount) |
| Longest Common Subsequence | O(m × n) | O(m × n) | O(min(m, n)) |
| Edit distance | O(m × n) | O(m × n) | O(min(m, n)) |
| 0/1 Knapsack | O(n × W) | O(n × W) | O(W) |
| LIS (length only) | O(n log n) | O(n) | O(n) |
| Matrix path counting | O(m × n) | O(m × n) | O(min(m, n)) |

---

## Pattern → Complexity mapping (memorize)

| Pattern | Typical time | Typical space |
|---|---|---|
| Two pointers | O(n) | O(1) |
| Sliding window | O(n) | O(k) for window |
| Hash map for complement | O(n) | O(n) |
| Binary search | O(log n) | O(1) |
| Merge intervals | O(n log n) | O(n) |
| BFS / DFS on graph | O(V + E) | O(V) |
| Backtracking | O(2ⁿ) or O(n!) | O(n) recursion |
| 1D DP | O(n) | O(n) or O(1) |
| 2D DP | O(m × n) | O(m × n) or O(min) |
| Top-K with heap | O(n log k) | O(k) |
| K-way merge with heap | O(n log k) | O(k) |
| Divide and conquer | O(n log n) | O(log n) |
| Trie | O(L) per op (L = key length) | O(N × L) |
| Union-Find with path compression | O(α(n)) ≈ O(1) | O(n) |

---

## Math identities you should know

```
log₂(n × m)  =  log₂(n) + log₂(m)
log₂(n / m)  =  log₂(n) − log₂(m)
log₂(n^k)    =  k × log₂(n)

n × log₂(n)  >  n × log₁₀(n)   but Big-O drops constant base
                                so we just write O(n log n)

2^k = n   ⟺   k = log₂(n)
                                "halving k times to reach 1"
                                = log₂(n) iterations
```

---

## Time-budget table (for "n=?" hint reading)

When the problem says **n ≤ X**, the expected complexity is roughly:

| n | Expected complexity |
|---|---|
| ≤ 10 | O(n!) or O(2ⁿ) acceptable |
| ≤ 20 | O(2ⁿ) acceptable |
| ≤ 100 | O(n³) or O(n² × log n) acceptable |
| ≤ 1,000 | O(n²) acceptable |
| ≤ 10⁵ | O(n log n) or O(n × √n) |
| ≤ 10⁶ | O(n) or O(n log n) |
| ≤ 10⁸ | O(n) only |
| ≤ 10¹⁸ | O(log n) only |

Use this as a *signal*. If problem says n=10⁵ and you propose O(n²), you're missing a faster solution.

---

## The Π / Σ trick — average over n loops

When loop bodies vary in length, use **amortized analysis**:

```python
seen = set()
left = 0
for right in range(n):
    while s[right] in seen:
        seen.remove(s[left])
        left += 1
    seen.add(s[right])
```

Looks like O(n²) (nested loop). But: `left` only ever moves right. Across the whole outer loop, `while`'s total iterations are at most n. So total work = O(n) outer + O(n) inner = **O(n)**.

This is the **sliding window** insight. The inner loop's amortized cost is O(1) per outer step.

---

## Quick rules of thumb

- **Sorted input + O(log n) → binary search**
- **"Find pair / triplet that sums to X" → hash map or two pointers**
- **"Subarray with property P" → sliding window or prefix sums**
- **"Count ways / minimum cost" → DP**
- **"All combinations / permutations" → backtracking**
- **"Top-K / Median in stream" → heap (one or two)**
- **"Connected components / shortest path unweighted" → BFS**
- **"Topological order / cycle in directed graph" → DFS or Kahn's**

---

## What to memorize cold

If you can recite this table, your interview complexity analysis will be flawless:

- `dict / set` lookups: **O(1) avg**
- `list` append: **O(1) amortized**, `pop(0)`: **O(n)**
- `string +=`: **O(n²) total**, use `"".join()`: **O(n)**
- `heappush / heappop`: **O(log n)**, `heapify`: **O(n)**
- `bisect_left / bisect_right`: **O(log n)** on a sorted list
- Sorting: **O(n log n)**
- BFS / DFS on graph: **O(V + E)**
- Recursion stack: **O(depth)**

---

## Up next

→ [How to think recursively](how-to-think-recursively.md) — the mindset, the templates, the bugs.
