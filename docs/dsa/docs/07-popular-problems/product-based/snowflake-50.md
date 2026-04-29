# Snowflake — 50 most-asked questions

> The 50 problems Snowflake (Data Cloud, Snowpark, Snowpipe, native apps) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Snowflake</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Snowflake is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background. |
| **Tech phone screen** | 60 min | Coding (medium). |
| **OA / take-home** | 90 min | Sometimes a SQL + algo combo. |
| **Onsite — coding ×2** | 60 min each | Algorithms + data structures. |
| **Onsite — system design** | 60 min | Storage / query engine / metadata. |
| **Onsite — manager** | 45 min | Behavioral + project. |

**Snowflake style**: data-warehouse veteran, query-engine flavor (parsing, planning, costing). C++ background prized for kernel team. Bar is high — close to FAANG. Strong system-design lean toward storage + compute separation.

---

## 🎯 What Snowflake tests

| Signal | Where | How to show |
|---|---|---|
| Algorithms | Coding | Standard hard / medium fluency. |
| Database internals | System design | Buffers, columnar storage, vectorised execution. |
| SQL | OA | Window functions, joins, optimisation. |
| Concurrency | Coding | Multi-thread / lock-free — happens in kernel team. |

---

## 🧩 Patterns Snowflake loves

| Pattern | Frequency | Why |
|---|---|---|
| **Hash + sliding window** | ⭐⭐⭐⭐⭐ | Standard mediums. |
| **DP** | ⭐⭐⭐⭐ | Query optimiser cost models. |
| **Tree / interval** | ⭐⭐⭐⭐ | B+ tree, segment tree. |
| **Heap K-way merge** | ⭐⭐⭐⭐ | Merge sorted runs in sort operator. |
| **Bit / SIMD thinking** | ⭐⭐⭐ | Vectorised exec, bitmap indexes. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash | 🚧 |
| 4 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 5 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | BS partition | 🚧 |
| 6 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Sort Colors | <span class="diff-medium">Medium</span> | Dutch flag | 🚧 |
| 8 | Find Duplicate | <span class="diff-medium">Medium</span> | Floyd's | 🚧 |
| 9 | First Missing Positive | <span class="diff-hard">Hard</span> | Cyclic sort | 🚧 |
| 10 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix + hash | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 15 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 16 | Serialize / Deserialize | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 17 | Range Sum BST | <span class="diff-easy">Easy</span> | DFS + prune | 🚧 |
| 18 | Count Smaller Numbers After Self | <span class="diff-hard">Hard</span> | BIT | 🚧 |
| 19 | Binary Tree Inorder Traversal | <span class="diff-easy">Easy</span> | Iterative stack | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 20 | Number of Islands | <span class="diff-medium">Medium</span> | DFS | 🚧 |
| 21 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 22 | Cheapest Flights K Stops | <span class="diff-medium">Medium</span> | Bellman-Ford | 🚧 |
| 23 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |
| 24 | Critical Connections | <span class="diff-hard">Hard</span> | Tarjan | 📝 (see [ByteDance 50](bytedance-50.md)) |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 25 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 26 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 27 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 🚧 |
| 28 | External Merge Sort | <span class="diff-hard">Hard</span> | K-way merge + disk | 📝 |

### Backtracking (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | Subsets | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 30 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 32 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 33 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 34 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |
| 35 | Burst Balloons | <span class="diff-hard">Hard</span> | Interval DP | 🚧 |

### Search & sort (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 36 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 37 | Find Peak Element | <span class="diff-medium">Medium</span> | BS variant | 🚧 |
| 38 | Kth Smallest in Sorted Matrix | <span class="diff-medium">Medium</span> | BS or heap | 🚧 |
| 39 | Sort an Array (External) | <span class="diff-medium">Medium</span> | Merge | 🚧 |

### Concurrency (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Print in Order | <span class="diff-easy">Easy</span> | Semaphore chain | 📝 (see [Apple 50](apple-50.md)) |
| 41 | Reader-Writer Lock | <span class="diff-medium">Medium</span> | Counter + cond var | 🚧 |
| 42 | Bounded Blocking Queue | <span class="diff-medium">Medium</span> | Lock + cond var | 🚧 |

### Design (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 43 | Design Columnar Store | <span class="diff-hard">Hard</span> | Block + dictionary encode | 📝 |
| 44 | Design Query Optimiser | <span class="diff-hard">Hard</span> | Cost-based DP | 🚧 |
| 45 | Design Time-Travel Storage | <span class="diff-hard">Hard</span> | MVCC + immutable files | 🚧 |
| 46 | Design Streaming Aggregator | <span class="diff-hard">Hard</span> | Window + sketch | 🚧 |
| 47 | Design Auto-Scaling Warehouse | <span class="diff-hard">Hard</span> | Pool + warm cache | 🚧 |
| 48 | Design Metadata Catalog | <span class="diff-hard">Hard</span> | Versioned tree | 🚧 |
| 49 | Design Resource Manager | <span class="diff-hard">Hard</span> | Quota + queue | 🚧 |
| 50 | Design Cross-Region Replication | <span class="diff-hard">Hard</span> | Async log shipping | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — External Merge Sort

??? question "Story: sort a 1 TB file with only 16 GB RAM. Standard step in any data warehouse."

    **Two phases**: (1) split file into chunks that fit in RAM, sort each, write to disk → "sorted runs"; (2) K-way merge using a min-heap. The K-way merge is the heart of every sort operator in databases.

```python
import heapq
from typing import Iterator

def k_way_merge(runs: list[Iterator[int]]) -> Iterator[int]:
    heap: list[tuple[int, int, Iterator[int]]] = []
    for i, run in enumerate(runs):
        try:
            heap.append((next(run), i, run))
        except StopIteration:
            pass
    heapq.heapify(heap)

    while heap:
        val, i, run = heapq.heappop(heap)
        yield val
        try:
            heapq.heappush(heap, (next(run), i, run))
        except StopIteration:
            pass
```

??? abstract "Complexity"

    O(N log K) for N total records, K runs. With M memory and total size N, we have K = ⌈N/M⌉ runs.

??? tip "Snowflake follow-up: 'how do you avoid disk thrashing during merge?'"

    Each run reads in **buffered chunks** (e.g., 1 MB) instead of one record at a time. Sequential reads are 100× faster than random. The output is also buffered, with a backpressure check.

---

### Deep-dive 2 — Columnar Store with Dictionary Encoding

??? question "Story: store 1B rows of `(user_id, country, event)`. Country has 200 distinct values — encode it efficiently."

    Columnar stores keep each column together, then dictionary-encode low-cardinality columns: replace strings with small integer IDs. Decoding pulls from the dictionary at query time. This shrinks `country` from ~10 bytes/row to ~1 byte/row.

```python
class DictColumn:
    def __init__(self):
        self.dict: list[str] = []
        self.lookup: dict[str, int] = {}
        self.codes: list[int] = []

    def append(self, value: str) -> None:
        if value not in self.lookup:
            self.lookup[value] = len(self.dict)
            self.dict.append(value)
        self.codes.append(self.lookup[value])

    def get(self, i: int) -> str:
        return self.dict[self.codes[i]]

    def filter_eq(self, value: str) -> list[int]:
        if value not in self.lookup:
            return []
        target = self.lookup[value]
        return [i for i, c in enumerate(self.codes) if c == target]
```

??? abstract "Complexity"

    `append` O(1) amortised. `filter_eq` O(N) but cache-friendly + SIMD-able in real impl.

??? tip "Snowflake follow-up: 'now do range filter on a numeric column'"

    Use **min/max pruning** at the block level: each block stores its (min, max). For a range query, skip whole blocks whose range doesn't intersect. Snowflake calls these "micro-partitions".

---

### Deep-dive 3 — Time-Travel Storage (immutable files + MVCC)

??? question "Story: Snowflake supports `SELECT ... AT(TIMESTAMP => '2025-01-01')`. How?"

    Every write creates a new immutable file ("micro-partition"). The metadata tracks `(table_id, version, file)`. A query at time T reads the file set whose write time is ≤ T. Old versions get GC'd after the time-travel window expires.

```python
from dataclasses import dataclass
from bisect import bisect_right

@dataclass
class Snapshot:
    timestamp: float
    files: list[str]

class TimeTravelTable:
    def __init__(self):
        self.history: list[Snapshot] = []

    def append_version(self, ts: float, files: list[str]) -> None:
        # Files monotonically grow; we record full file sets per snapshot.
        self.history.append(Snapshot(ts, files))

    def files_at(self, ts: float) -> list[str]:
        timestamps = [s.timestamp for s in self.history]
        idx = bisect_right(timestamps, ts) - 1
        return [] if idx < 0 else self.history[idx].files

    def gc_before(self, cutoff_ts: float) -> None:
        # keep latest snapshot ≤ cutoff and everything after
        timestamps = [s.timestamp for s in self.history]
        idx = bisect_right(timestamps, cutoff_ts) - 1
        if idx > 0:
            self.history = self.history[idx:]
```

??? abstract "Complexity"

    `files_at` O(log V), V versions. `append_version` O(1) amortised. Storage is ~size of latest + delta of older versions.

??? tip "Snowflake follow-up: 'how do you avoid storing full file-set per snapshot?'"

    Store deltas (added / removed file IDs per version). Reconstruct the file set by replaying deltas from a baseline snapshot. Snowflake's "metadata service" works exactly this way.

---

## 🛡️ Day-of tips

- **Talk database internals**: even on coding rounds, a comment like "this is what an external merge does" helps.
- **SQL fluency matters**: window functions (`ROW_NUMBER OVER`, `LAG`), correlated subqueries, query plans.
- **Performance vocabulary**: cache lines, branch prediction, vectorised execution. Use them sparingly but accurately.
- **System design**: separate storage and compute first; everything follows.
