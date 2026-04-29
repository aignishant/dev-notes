# Databricks — 50 most-asked questions

> The 50 problems Databricks (Unity Catalog, Delta Lake, MLflow, Mosaic AI) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Databricks</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Databricks is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background. |
| **Tech phone screen** | 60 min | Coding (medium / hard). |
| **OA / take-home** | 4-8 hr | Real-feeling project (e.g., a mini query engine). |
| **Onsite — coding ×2** | 60 min each | Algorithms + DS, often Spark / SQL flavored. |
| **Onsite — system design** | 60 min | Big-data: storage formats, query engines, ML serving. |
| **Onsite — manager / architecture** | 45 min | Project deep-dive, architecture critique. |

**Databricks style**: research-heavy, ex-Spark / Berkeley DNA, Scala / Python heavy. Take-home is real engineering work — they grade on tests, README, design choices. Hard problems and ambiguity tolerated more than at FAANG. Bar is **high**, especially for staff+.

---

## 🎯 What Databricks tests

| Signal | Where | How to show |
|---|---|---|
| Engineering depth | Take-home + onsite | Tests, structure, trade-off notes. |
| Big-data fluency | Design | Parquet, Delta, predicate pushdown, shuffles. |
| ML systems thinking | Some teams | Feature stores, online inference, drift. |
| Long-form thinking | Take-home | They grade architecture choices, not just correctness. |

---

## 🧩 Patterns Databricks loves

| Pattern | Frequency | Why |
|---|---|---|
| **DP** | ⭐⭐⭐⭐ | Cost-based optimiser. |
| **Hash + sliding window** | ⭐⭐⭐⭐⭐ | Standard. |
| **Heap + K-way merge** | ⭐⭐⭐⭐ | Sort-merge join, top-K. |
| **Trie + DFS** | ⭐⭐⭐ | Catalog browsing, autocomplete. |
| **Graph DAG / topo** | ⭐⭐⭐⭐ | Spark task DAG, query plans. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash | 🚧 |
| 4 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 5 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix + hash | 🚧 |
| 6 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 🚧 |
| 8 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 9 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand center | 🚧 |
| 10 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 15 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 16 | Serialize / Deserialize | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 17 | Inorder Traversal Iterative | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 18 | Recover BST | <span class="diff-medium">Medium</span> | Inorder + swap | 🚧 |

### Graphs (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 19 | Number of Islands | <span class="diff-medium">Medium</span> | DFS | 🚧 |
| 20 | Course Schedule II | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 21 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |
| 22 | Cheapest Flights K Stops | <span class="diff-medium">Medium</span> | Bellman-Ford | 🚧 |
| 23 | Spark DAG Scheduling | <span class="diff-hard">Hard</span> | Topo + critical path | 📝 |
| 24 | Find Bridges (Tarjan) | <span class="diff-hard">Hard</span> | Bridge finding | 📝 (see [ByteDance 50](bytedance-50.md)) |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 25 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 26 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 27 | Skyline Problem | <span class="diff-hard">Hard</span> | Sweep + heap | 🚧 |
| 28 | External Sort | <span class="diff-hard">Hard</span> | K-way merge | 📝 (see [Snowflake 50](snowflake-50.md)) |

### Backtracking (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | Subsets | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 30 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |

### DP (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 32 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 33 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |
| 34 | Word Break | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 35 | Burst Balloons | <span class="diff-hard">Hard</span> | Interval DP | 🚧 |
| 36 | Partition Equal Subset Sum | <span class="diff-medium">Medium</span> | 0/1 knapsack | 🚧 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 38 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | BS partition | 🚧 |
| 39 | Sort an Array (Merge) | <span class="diff-medium">Medium</span> | Merge sort | 🚧 |

### Concurrency (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Bounded Blocking Queue | <span class="diff-medium">Medium</span> | Lock + cond var | 🚧 |
| 41 | Reader-Writer Lock | <span class="diff-medium">Medium</span> | Counter + cond var | 🚧 |

### Design (9)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Design Mini Spark | <span class="diff-hard">Hard</span> | RDD + DAG | 📝 |
| 43 | Design Delta Lake | <span class="diff-hard">Hard</span> | Append-only log + Parquet | 📝 |
| 44 | Design ML Feature Store | <span class="diff-hard">Hard</span> | Online + offline split | 🚧 |
| 45 | Design Catalog | <span class="diff-hard">Hard</span> | Versioned tree | 🚧 |
| 46 | Design Job Scheduler | <span class="diff-hard">Hard</span> | Priority queue + DAG | 🚧 |
| 47 | Design Streaming Window Join | <span class="diff-hard">Hard</span> | Watermark + state | 🚧 |
| 48 | Design Notebook Service | <span class="diff-medium">Medium</span> | Cell exec + state | 🚧 |
| 49 | Design Cluster Auto-Scaler | <span class="diff-hard">Hard</span> | Pool + signals | 🚧 |
| 50 | Design Audit + Lineage | <span class="diff-hard">Hard</span> | DAG of (table, op) | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Spark DAG Scheduling

??? question "Story: a Spark job decomposes into stages. Stages with no dependencies can run in parallel. Schedule them."

    Build the DAG of stages, run topological sort, then within each "wave" of ready stages, dispatch concurrently.

```python
from collections import defaultdict, deque

def schedule_stages(deps: list[tuple[int, int]], n_stages: int) -> list[list[int]]:
    """deps = list of (predecessor, successor). Returns a list of waves."""
    indeg = [0] * n_stages
    out: dict[int, list[int]] = defaultdict(list)
    for u, v in deps:
        out[u].append(v)
        indeg[v] += 1

    ready = deque([i for i in range(n_stages) if indeg[i] == 0])
    waves: list[list[int]] = []
    while ready:
        wave = list(ready)
        waves.append(wave)
        ready = deque()
        for u in wave:
            for v in out[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    ready.append(v)
    return waves
```

??? abstract "Complexity"

    O(V + E) — same as Kahn's topo sort. Output is the wave structure, not just an order.

??? tip "Databricks follow-up: 'now consider stage durations — minimise total wall time'"

    Critical-path scheduling: longest path through the DAG = minimum makespan with infinite workers. With finite workers, this becomes NP-hard (job-shop); use list scheduling with "longest remaining work" heuristic.

---

### Deep-dive 2 — Mini Spark RDD

??? question "Story: implement a tiny RDD with `map` / `filter` / `collect`. Show lazy evaluation."

    Each transformation builds a new RDD whose `compute()` calls its parent's `compute()`. Nothing executes until `collect()`.

```python
from typing import Callable, Iterator, Any

class RDD:
    def __init__(self, source: Callable[[], Iterator[Any]]):
        self._source = source

    @classmethod
    def from_iter(cls, it):
        data = list(it)
        return cls(lambda: iter(data))

    def map(self, f: Callable[[Any], Any]) -> "RDD":
        return RDD(lambda: (f(x) for x in self._source()))

    def filter(self, pred: Callable[[Any], bool]) -> "RDD":
        return RDD(lambda: (x for x in self._source() if pred(x)))

    def collect(self) -> list:
        return list(self._source())

# Example: only ints > 100, doubled
rdd = RDD.from_iter(range(200)).filter(lambda x: x > 100).map(lambda x: x * 2)
# Nothing has run yet
print(rdd.collect()[:3])  # [202, 204, 206]
```

??? abstract "Complexity"

    Each transformation O(1) construction. Compute is O(N) on collect.

??? tip "Databricks follow-up: 'add `groupByKey`'"

    `groupByKey` is a *shuffle* — partition by key, then within partition, accumulate values per key. Real Spark does this on an external hash map (spilling to disk), making it the most expensive primitive in the framework.

---

### Deep-dive 3 — Delta Lake (append-only log)

??? question "Story: ACID on top of Parquet files in S3. How does Delta achieve atomic commits without locking?"

    Each commit writes a new JSON file in `_delta_log/000000N.json` describing **adds** (new data files) and **removes** (logical deletes). Atomic put-if-absent of `N.json` IS the commit. Reading the table = scanning the log to compute the active file set.

```python
from dataclasses import dataclass, field
from typing import Literal
import json

@dataclass
class LogEntry:
    op: Literal["add", "remove"]
    path: str

@dataclass
class Commit:
    version: int
    entries: list[LogEntry]

class DeltaTable:
    def __init__(self):
        self.commits: list[Commit] = []

    def commit(self, entries: list[LogEntry]) -> int:
        # ATOMIC put-if-absent in real impl
        version = len(self.commits)
        self.commits.append(Commit(version, entries))
        return version

    def active_files(self, at_version: int | None = None) -> set[str]:
        end = len(self.commits) if at_version is None else at_version + 1
        files: set[str] = set()
        for c in self.commits[:end]:
            for e in c.entries:
                if e.op == "add":
                    files.add(e.path)
                else:
                    files.discard(e.path)
        return files
```

??? abstract "Complexity"

    `active_files` O(V · E) over V versions. Real impl periodically writes a **checkpoint** (snapshot of active files) so reads only replay log since the last checkpoint.

??? tip "Databricks follow-up: 'two writers commit at the same version — what happens?'"

    The store's atomic put-if-absent on `N.json` causes one to fail with `FileAlreadyExists`. The loser **rebases**: re-reads the log up to N+1, checks for conflicts (e.g., did the winner remove a file I'm modifying?), and retries with version N+1 if safe. This is optimistic concurrency control.

---

## 🛡️ Day-of tips

- **Take-home grading**: tests + README + a "design notes" doc beat clever code. Spend 30% of time on writeup.
- **Mention Spark internals where natural**: shuffle, broadcast join, narrow vs wide dependencies. Don't force it.
- **Architecture critique round**: be ready to draw + critique your own past project. They want self-awareness.
- **Big-data vocabulary**: predicate pushdown, columnar projection, partition pruning, watermarks, exactly-once.
