# Topological Sort

> An ordering of vertices in a **directed acyclic graph** such that every edge `u → v` puts `u` before `v` in the output. The two canonical algorithms — **Kahn's BFS** (peel off in-degree-zero nodes) and **DFS post-order with reverse** — also double as **cycle detectors**: if you can't produce a topological order, the graph has a cycle. Course schedules, build systems, task dependency graphs, alien dictionaries — anything with "do A before B" lives here.

<span class="phase-status phase-inprogress">Phase 5 — pattern page (Batch 25)</span>

---

## 📖 What is topological sort?

A topological order of a directed graph is a linear ordering of its vertices where, for every directed edge `u → v`, vertex `u` comes before `v`. Such an ordering exists **if and only if the graph is a DAG** (directed *acyclic* graph). If there's a cycle, no ordering can satisfy every edge — and the algorithms below detect this.

Two equivalent algorithms:

1. **Kahn's algorithm (BFS):** repeatedly remove a vertex with in-degree 0, append it to the output, and decrement the in-degrees of its neighbours. Continue until the graph is empty (success) or no in-degree-0 vertex remains (cycle).
2. **DFS post-order:** run DFS from any unvisited vertex, push each vertex onto a stack *after* its DFS recursion returns (post-order). Reverse the stack to get a topological order. Cycles show up as a back-edge during DFS.

The mental model: in Kahn's, you "build the order from the start" (sources first); in DFS, you "build it from the end" (sinks last, then reverse). Both run in **O(V + E)**.

!!! tip "The signal — when to reach for topological sort"
    Reach for it when you see:

    - "Tasks have **dependencies**; produce a valid order to do them all." (Course Schedule, Build Order)
    - "Given a list of dependent items, can they all be completed?" → cycle detection.
    - "Reconstruct the alphabet / partial order from these examples." (Alien Dictionary, LC 269)
    - Anything mentioning **prerequisites**, **dependencies**, **must come before**, or **DAG**.

    Don't reach for it when:

    - The graph is undirected — topological sort doesn't make sense without direction.
    - You need *all* topological orders, not one. (That's a separate problem; backtracking territory.)
    - The constraint isn't "before" but "near" or "shortest path" — that's BFS / Dijkstra, not topo.

---

## 🧩 The three flavors

### Flavor 1: Kahn's algorithm (BFS, in-degree zero peel)

The most interview-friendly. Compute in-degrees, seed a queue with all in-degree-0 vertices, and pop-and-decrement. The order in which you pop is a valid topological order.

```python
from collections import deque

def topo_sort_kahn(n: int, edges: list[list[int]]) -> list[int] | None:
    """Return a topo order, or None if a cycle exists. Vertices are 0..n-1."""
    graph: list[list[int]] = [[] for _ in range(n)]
    in_deg = [0] * n
    for u, v in edges:                                # edge u → v
        graph[u].append(v)
        in_deg[v] += 1

    queue: deque[int] = deque(i for i in range(n) if in_deg[i] == 0)  # (1) seed
    order: list[int] = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:                             # (2) decrement neighbours
            in_deg[v] -= 1
            if in_deg[v] == 0:
                queue.append(v)

    return order if len(order) == n else None          # (3) cycle iff fewer than n nodes emitted
```

1. Seed with **every** in-degree-0 vertex; there can be many. Order among them doesn't matter — any tie-breaking gives a valid topo order.
2. After "removing" `u` from the graph, decrement the in-degree of each of its successors. When a successor's in-degree hits 0, it's now ready.
3. The cycle test is elegant: if any vertex is part of a cycle, its in-degree never drops to 0, so it never enters the queue. Number of emitted vertices < `n` ⇒ cycle.

**Examples:** Course Schedule (LC 207 — just need to know if order *exists*), Course Schedule II (LC 210 — return the order), Alien Dictionary (LC 269 — derive edges from word pairs, then topo).

### Flavor 2: DFS post-order

Run DFS from each unvisited vertex; on the way back up the recursion (post-order), push the vertex onto a stack. The reverse of that stack is a topological order.

```python
def topo_sort_dfs(n: int, edges: list[list[int]]) -> list[int] | None:
    graph: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)

    WHITE, GRAY, BLACK = 0, 1, 2                      # (1) tri-state for cycle detection
    color = [WHITE] * n
    order: list[int] = []
    has_cycle = False

    def dfs(u: int) -> None:
        nonlocal has_cycle
        color[u] = GRAY                                # (2) currently in recursion stack
        for v in graph[u]:
            if color[v] == GRAY:                       # (3) back-edge → cycle
                has_cycle = True
                return
            if color[v] == WHITE:
                dfs(v)
                if has_cycle:
                    return
        color[u] = BLACK                               # (4) done; safe to record
        order.append(u)

    for u in range(n):
        if color[u] == WHITE:
            dfs(u)
            if has_cycle:
                return None

    return order[::-1]                                 # (5) reverse the post-order
```

1. **WHITE** = unvisited, **GRAY** = visiting (in current recursion stack), **BLACK** = finished. The three colours are the standard cycle-detection idiom.
2. On entering `u`, paint it GRAY.
3. If during DFS you hit a GRAY neighbour, that's a back-edge — `u` reached an ancestor of itself, so there's a cycle.
4. After all neighbours are done, paint `u` BLACK and record it (post-order).
5. Reversing the post-order gives a topological sort: `u` finishes *after* all its descendants, so reversing puts `u` *before* them.

**Why two colours aren't enough.** With just visited / unvisited, a node visited via two different paths in a DAG looks identical to a back-edge in a graph with a cycle. The GRAY state distinguishes "still being explored" from "fully done."

**Examples:** Same problem set as Kahn's. DFS is sometimes preferable when you also need to do other DFS bookkeeping (SCCs, articulation points).

### Flavor 3: Lexicographically smallest topo order (priority queue)

Sometimes the problem asks for the topo order that's lexicographically smallest among all valid orders. Replace Kahn's queue with a **min-heap**: always pop the smallest-id ready vertex.

```python
import heapq

def topo_sort_lex_smallest(n: int, edges: list[list[int]]) -> list[int] | None:
    graph: list[list[int]] = [[] for _ in range(n)]
    in_deg = [0] * n
    for u, v in edges:
        graph[u].append(v)
        in_deg[v] += 1

    heap: list[int] = [i for i in range(n) if in_deg[i] == 0]
    heapq.heapify(heap)
    order: list[int] = []
    while heap:
        u = heapq.heappop(heap)                        # (1) smallest ready vertex
        order.append(u)
        for v in graph[u]:
            in_deg[v] -= 1
            if in_deg[v] == 0:
                heapq.heappush(heap, v)

    return order if len(order) == n else None
```

1. The heap costs an extra log factor: **O((V + E) log V)** total. Use only when ordering matters; default to Kahn's plain BFS otherwise.

**Examples:** "Smallest lexicographic course order," LC 1203 Sort Items by Groups (a layered topo where lex smallest matters within a group).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | "Can all tasks finish?" | DAG-ness check | Course Schedule (LC 207) | Run Kahn's; check if `len(order) == n` |
| 2 | "Give me the order" | Produce a valid topo order | Course Schedule II (LC 210) | Same Kahn's; return `order` |
| 3 | Lex smallest order | Min-id ready vertex first | (Variant) | Replace queue with min-heap |
| 4 | Derive order from examples | Edges implicit in input | Alien Dictionary (LC 269) | Compare adjacent words to extract edges |
| 5 | All possible orders | Output every valid topo order | (Variant) | Backtracking on Kahn's frontier |
| 6 | Min-height trees | Trim leaves layer-by-layer | Minimum Height Trees (LC 310) | Topo on undirected (degree-1 peel) |
| 7 | Layered / parallel topo | Group items in independent batches | Build dependency graph | BFS by levels (size-snapshot trick) |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Course Schedule | 207 | <span class="diff-medium">Medium</span> | Cycle check | 📝 |
| 2 | Course Schedule II | 210 | <span class="diff-medium">Medium</span> | Topo order | 📝 |
| 3 | Course Schedule III | 630 | <span class="diff-hard">Hard</span> | Greedy + heap (cousin) | 📝 |
| 4 | Course Schedule IV | 1462 | <span class="diff-medium">Medium</span> | Reachability over DAG | 📝 |
| 5 | Alien Dictionary | 269 | <span class="diff-hard">Hard</span> | Derive edges | 📝 |
| 6 | Minimum Height Trees | 310 | <span class="diff-medium">Medium</span> | Trim leaves | 📝 |
| 7 | Find Eventual Safe States | 802 | <span class="diff-medium">Medium</span> | Reverse-graph topo | 📝 |
| 8 | Sort Items by Groups Respecting Dependencies | 1203 | <span class="diff-hard">Hard</span> | Two-level topo | 📝 |
| 9 | Parallel Courses | 1136 | <span class="diff-medium">Medium</span> | Layered topo (semesters) | 📝 |
| 10 | Parallel Courses II | 1494 | <span class="diff-hard">Medium</span> | Bitmask DP (cousin) | 📝 |
| 11 | Parallel Courses III | 2050 | <span class="diff-hard">Hard</span> | Topo + longest path | 📝 |
| 12 | Loud and Rich | 851 | <span class="diff-medium">Medium</span> | Topo + propagation | 📝 |
| 13 | Reconstruct Itinerary | 332 | <span class="diff-hard">Hard</span> | Hierholzer (cousin) | 📝 |
| 14 | All Ancestors of a Node in a DAG | 2192 | <span class="diff-medium">Medium</span> | Topo + set propagation | 📝 |
| 15 | Largest Color Value in a Directed Graph | 1857 | <span class="diff-hard">Hard</span> | Topo + DP on counts | 📝 |
| 16 | Build a Matrix With Conditions | 2392 | <span class="diff-hard">Hard</span> | Two independent topos | 📝 |
| 17 | Find All Possible Recipes | 2115 | <span class="diff-medium">Medium</span> | Topo with supplies | 📝 |
| 18 | Sequence Reconstruction | 444 | <span class="diff-medium">Medium</span> | Unique topo order check | 📝 |
| 19 | Longest Increasing Path in a Matrix | 329 | <span class="diff-hard">Hard</span> | Implicit DAG + DFS DP | 📝 |
| 20 | Minimum Time to Complete All Tasks | 1834 | <span class="diff-medium">Medium</span> | Scheduling (cousin) | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Course Schedule II (LC 210)

> There are `numCourses` courses labelled `0..numCourses-1`. `prerequisites[i] = [a, b]` means you must take course `b` before course `a`. Return any valid order, or `[]` if impossible.

The clearest example of Kahn's algorithm. Two-step recipe: build graph + in-degree array, then BFS the in-degree-0 frontier.

#### Code

```python
from collections import deque

def find_order(num_courses: int, prerequisites: list[list[int]]) -> list[int]:
    graph: list[list[int]] = [[] for _ in range(num_courses)]
    in_deg = [0] * num_courses
    for course, pre in prerequisites:                  # (1) edge: pre → course
        graph[pre].append(course)
        in_deg[course] += 1

    queue: deque[int] = deque(i for i in range(num_courses) if in_deg[i] == 0)
    order: list[int] = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:
            in_deg[v] -= 1
            if in_deg[v] == 0:
                queue.append(v)

    return order if len(order) == num_courses else []
```

1. **Read the edge direction carefully.** LC 210's `[a, b]` means "to take `a`, finish `b` first" — i.e., `b → a`. Inverting this gives wrong answers silently (you'd produce an order where prerequisites come last).

#### Dry run on `numCourses = 4`, `prerequisites = [[1, 0], [2, 0], [3, 1], [3, 2]]`

Graph & in-degrees after building:

```
0 → 1, 2
1 → 3
2 → 3
in_deg: [0, 1, 1, 2]
```

Initial queue: `[0]` (only 0 has in-deg 0).

| Step | Pop | Order | Decrement → New in_deg | Push |
|------|-----|-------|------------------------|------|
| 1 | 0 | `[0]` | in_deg[1]=0, in_deg[2]=0 | 1, 2 |
| 2 | 1 | `[0, 1]` | in_deg[3]=1 | (none) |
| 3 | 2 | `[0, 1, 2]` | in_deg[3]=0 | 3 |
| 4 | 3 | `[0, 1, 2, 3]` | (no neighbours) | (none) |

Output: `[0, 1, 2, 3]`. ✓ (Other valid orders: `[0, 2, 1, 3]`.)

#### What does a cycle look like?

Add prerequisite `[0, 3]` (now 3 → 0 too): the cycle is `0 → 1 → 3 → 0`. Initial queue is empty (every vertex has in-degree ≥ 1). The while loop terminates immediately with `order = []`, length 0 ≠ 4 → return `[]`.

#### Why Kahn's terminates with the right answer

**Loop invariant:** at the start of each iteration, the queue contains every vertex with in-degree 0 in the *current residual graph*. Removing a queue front decrements its successors' in-degrees, possibly creating new in-degree-0 vertices that get appended. Since each edge is decremented exactly once, the loop processes all `E` edges in total time. The order's length equals `n` iff the original graph was a DAG — because in a DAG every vertex eventually becomes in-degree-0; in a cyclic graph, the cycle vertices never drop to 0.

#### Complexity

- **Time:** O(V + E). Each vertex enters the queue once; each edge contributes one decrement.
- **Space:** O(V + E) for graph + in-degree + queue.

---

### Deep-dive 2 — Alien Dictionary (LC 269)

> Given a sorted list of words from an alien alphabet, derive the order of letters in that alphabet. Return any valid order, or `""` if impossible (cycle, or invalid prefix order like `["abc", "ab"]`).

Two-step problem: **build the graph from word comparisons**, then run topo. The graph-building is the trickier half.

#### Building the graph from word pairs

For each adjacent word pair, scan both words character-by-character. The **first differing character** gives one edge. If no differing character exists and the longer word comes first (`["abc", "ab"]`), the input is invalid — there's no way to sort that lexicographically.

```python
from collections import defaultdict, deque

def alien_order(words: list[str]) -> str:
    graph: dict[str, set[str]] = defaultdict(set)
    in_deg: dict[str, int] = {c: 0 for word in words for c in word}    # (1) seed all letters

    for w1, w2 in zip(words, words[1:]):                                # (2) adjacent pairs
        if len(w1) > len(w2) and w1.startswith(w2):                     # (3) invalid prefix
            return ""
        for c1, c2 in zip(w1, w2):
            if c1 != c2:
                if c2 not in graph[c1]:
                    graph[c1].add(c2)
                    in_deg[c2] += 1
                break                                                   # only the first diff yields an edge

    queue: deque[str] = deque(c for c in in_deg if in_deg[c] == 0)
    order: list[str] = []
    while queue:
        c = queue.popleft()
        order.append(c)
        for nb in graph[c]:
            in_deg[nb] -= 1
            if in_deg[nb] == 0:
                queue.append(nb)

    return "".join(order) if len(order) == len(in_deg) else ""
```

1. **Seed every letter that appears anywhere**, even those without edges — they still need to appear in the output.
2. Compare consecutive words only — transitivity comes for free from topo.
3. The trap case: `["abc", "ab"]`. There's no first-differing character (one is a prefix of the other) and `w1` is longer than `w2`, so `w2` should sort *before* `w1` in any prefix order — contradiction. Return `""`.

#### Dry run on `words = ["wrt", "wrf", "er", "ett", "rftt"]`

Pair-by-pair edge extraction:

| Pair | Find first diff | Edge | Cumulative graph |
|------|------------------|------|-------------------|
| `wrt`, `wrf` | `t` vs `f` (index 2) | `t → f` | `t → f` |
| `wrf`, `er` | `w` vs `e` (index 0) | `w → e` | `t → f`, `w → e` |
| `er`, `ett` | `r` vs `t` (index 1) | `r → t` | `t → f`, `w → e`, `r → t` |
| `ett`, `rftt` | `e` vs `r` (index 0) | `e → r` | `t → f`, `w → e`, `r → t`, `e → r` |

Letters seen: `{w, r, t, f, e}`. In-degrees:
- `w`: 0
- `r`: 1 (from `e`)
- `t`: 1 (from `r`)
- `f`: 1 (from `t`)
- `e`: 1 (from `w`)

Kahn's:

| Step | Pop | Decrement → in_deg now | Order |
|------|-----|-------------------------|-------|
| 1 | `w` | `e` → 0 | `w` |
| 2 | `e` | `r` → 0 | `we` |
| 3 | `r` | `t` → 0 | `wer` |
| 4 | `t` | `f` → 0 | `wert` |
| 5 | `f` | (no neighbours) | `wertf` |

Output: `"wertf"`. ✓

#### Why "first differing character" is the only edge

Lexicographic comparison stops at the first difference. The characters *after* the first difference can be anything — they don't constrain the alphabet order. So extracting any later character would give a spurious edge. One edge per pair is correct.

#### Subtle invariant: the alphabet might have multiple valid orders

For `words = ["z", "x"]`, the only edge is `z → x`. Any order putting `z` before `x` works. The problem says "return any valid order," so the natural Kahn's output suffices.

#### Complexity

- **Time:** O(C) where C = total characters across all words. Each character contributes O(1) to comparison; topo is O(V + E) ≤ O(26 + edges).
- **Space:** O(V + E) ≤ O(26 + 26²).

---

### Deep-dive 3 — Minimum Height Trees (LC 310)

> Given an undirected tree (n nodes, n-1 edges), find every root that produces a tree of minimum height. Return the list of such roots.

The trick: **the answer is always 1 or 2 nodes**, located at the "centre" of the tree. Find them by repeatedly trimming leaves (degree-1 vertices) — the last 1 or 2 to fall are the centroids.

This isn't a directed-graph topo — it's the *undirected* analogue: peel **degree-1** vertices instead of in-degree-0.

#### Why ≤ 2 centroids?

A tree has a "longest path" called its **diameter**. The midpoint of the diameter minimises the maximum distance to any other node. If the diameter has odd length, the midpoint is a single vertex; if even, two adjacent vertices share the role. Either way, ≤ 2 candidates.

#### Code

```python
from collections import deque

def find_min_height_trees(n: int, edges: list[list[int]]) -> list[int]:
    if n == 1:
        return [0]                                                      # (1) trivial
    if n == 2:
        return [0, 1]

    graph: list[set[int]] = [set() for _ in range(n)]
    for u, v in edges:
        graph[u].add(v)
        graph[v].add(u)

    leaves: deque[int] = deque(i for i in range(n) if len(graph[i]) == 1)
    remaining = n
    while remaining > 2:                                                 # (2) trim until ≤ 2 left
        layer_size = len(leaves)
        remaining -= layer_size
        for _ in range(layer_size):
            leaf = leaves.popleft()
            (nb,) = graph[leaf]                                          # (3) only one neighbour
            graph[nb].remove(leaf)
            if len(graph[nb]) == 1:                                      # (4) became a leaf
                leaves.append(nb)
    return list(leaves)
```

1. Edge cases: n=1 has only one vertex (the answer); n=2 means both vertices are equivalent.
2. **Layer-by-layer trimming**, like BFS levels. After each layer is removed, fewer vertices remain.
3. Tuple unpacking `(nb,) = graph[leaf]` enforces "leaf has exactly one neighbour" — defensive correctness.
4. After removal, the neighbour might itself become a leaf — push it for the next layer.

#### Dry run on `n = 6`, `edges = [[0,3],[1,3],[2,3],[4,3],[5,4]]`

Adjacency:
```
0: {3}
1: {3}
2: {3}
3: {0, 1, 2, 4}
4: {3, 5}
5: {4}
```

Initial leaves (degree 1): `[0, 1, 2, 5]`. `remaining = 6`.

**Iteration 1:** layer_size = 4, remaining → 2. Pop each leaf, remove edge, check neighbour:
- Pop 0 → remove from 3's set → `3: {1, 2, 4}` (still degree 3)
- Pop 1 → `3: {2, 4}` (degree 2)
- Pop 2 → `3: {4}` (degree 1) — append 3 to leaves
- Pop 5 → `4: {3}` (degree 1) — append 4 to leaves

After iteration: leaves = `[3, 4]`, remaining = 2. Loop condition `remaining > 2` is false → exit.

Output: `[3, 4]`. ✓

#### Why "layer by layer" not "one leaf at a time"

If you trim one leaf at a time, you might over-trim — by the time you finish a "layer," some neighbours are already past being a leaf. The layer-snapshot trick (`layer_size = len(leaves)` before the inner loop, exactly like Tree BFS) ensures each layer represents one synchronous round of leaf removal.

#### Complexity

- **Time:** O(n). Each edge is touched exactly twice (once per endpoint) across all iterations.
- **Space:** O(n) for adjacency + queue.

---

## 🐛 Common bugs

1. **Edge direction inverted.** `prerequisites[i] = [a, b]` in LC 210 means `b → a`. Building edges as `a → b` produces silently-wrong topo orders that "work" on examples without cycles.
2. **Forgetting isolated vertices.** A graph with vertex 5 but no edges to/from it still needs 5 in the output. Initialise `in_deg` with **every** vertex, not just those that appear in edges.
3. **DFS topo: two-colour cycle detection.** Marking only "visited / unvisited" misclassifies cross-edges in a DAG as cycles. Use the three-colour (WHITE/GRAY/BLACK) approach.
4. **Reversing the wrong list in DFS topo.** The post-order *itself* is a reverse topo order — reverse it once at the end. Reversing inside the recursion or forgetting to reverse at all both produce wrong orders.
5. **Alien Dictionary: missing the prefix-trap case.** `["abc", "ab"]` has no first-differing character; if `w1` is longer than `w2`, the input is invalid. Return early.
6. **Minimum Height Trees: trimming one leaf at a time.** You can over-trim into the centre. Use the layer-snapshot pattern.
7. **Lex-smallest topo: using a set instead of a min-heap.** Sets aren't ordered; you'd pop arbitrary elements. Use `heapq`.
8. **Counting `len(order) == n`** to detect cycles but not initialising vertices not appearing in edges. Same bug as #2 in disguise.

---

## 🗣️ Interviewer phrasings to recognize

- "Tasks **A depends on** B." → directed edge `B → A`; topo sort.
- "Can you **finish all** courses?" → cycle check; Kahn's, return `len(order) == n`.
- "Return **any valid** order." → standard Kahn's or DFS post-order.
- "Return the **lexicographically smallest** order." → Kahn's with a min-heap.
- "All **possible** orders." → backtracking on Kahn's frontier (each step picks any in-deg-0 vertex).
- "Find the **root** that minimises height." → undirected topo (degree-1 peel), aka tree centroid.
- "Reconstruct the **alphabet** from these examples." → derive edges from word pairs, then topo.

---

## 🧭 Connections to other patterns

- **Tree BFS** ([07-tree-bfs.md](07-tree-bfs.md)) — Kahn's algorithm is BFS, and "Min Height Trees" uses the level-snapshot trick.
- **Tree DFS** ([08-tree-dfs.md](08-tree-dfs.md)) — DFS topo uses the same post-order recursion pattern; cycle detection's GRAY state is the same idea as detecting back-edges.
- **Top-K Elements** ([12-top-k-elements.md](12-top-k-elements.md)) — lex-smallest topo replaces the BFS queue with a min-heap.
- **K-way Merge** ([13-k-way-merge.md](13-k-way-merge.md)) — both use heaps over multiple "sources" but for different purposes.
- **DP on DAG** — many longest-path / counting problems on DAGs run in topological order to enable bottom-up DP.
- **Strongly Connected Components** — Tarjan / Kosaraju condense cycles into a DAG, then topo-sort the condensation.

---

## ✅ Self-check — 8 questions

??? question "1. What's the difference between Kahn's algorithm and DFS topological sort?"
    Kahn's is BFS-based: maintain in-degrees, repeatedly dequeue an in-degree-0 vertex, decrement neighbours. Builds the order **front-to-back** (sources first). DFS post-order: run DFS, push each vertex on a stack after recursion returns, then reverse. Builds the order **back-to-front** (sinks last). Both run in O(V + E); cycle detection is `len(order) == n` for Kahn's, GRAY-on-revisit for DFS.

??? question "2. Why three colours (WHITE/GRAY/BLACK) instead of two for DFS cycle detection?"
    With only two colours (visited/unvisited), a vertex visited via two different paths in a DAG looks identical to a back-edge in a cyclic graph. The GRAY state — "currently on the recursion stack" — distinguishes "we're still exploring through here" from "we've finished here," allowing precise back-edge detection.

??? question "3. How does Kahn's algorithm detect a cycle?"
    A cycle's vertices never have in-degree 0 (each one has at least one predecessor inside the cycle). They never enter the queue, so they never appear in `order`. After the loop, `len(order) < n` ⇒ cycle.

??? question "4. In Alien Dictionary, why do we only extract one edge per word pair?"
    Lexicographic comparison stops at the first differing character. Characters after that don't constrain the alphabet. Extracting later characters as edges would produce false constraints (and wrong outputs). Always break out of the inner loop on the first differing pair.

??? question "5. For Minimum Height Trees, why is the answer always at most 2 nodes?"
    The diameter of a tree (longest path) has a unique midpoint when its length is even — that's the centroid. When odd, two adjacent vertices share the role. Any non-centroid root has greater max-eccentricity, so it can't be a min-height root.

??? question "6. How do you produce *all* possible topological orders?"
    Backtracking on Kahn's frontier: at each step, the queue is a set of in-degree-0 vertices; choose any one to emit, recurse, then put it back. The branching factor at each step equals the number of currently in-degree-0 vertices. Time is exponential in the worst case.

??? question "7. What's the minimum semesters to finish all courses (LC 1136)?"
    Layered Kahn's with the level-snapshot trick: each iteration of the outer loop = one semester; pop *all* currently in-degree-0 courses in that round, decrement neighbours, count semesters. If you exit with leftover vertices, the prerequisite graph has a cycle.

??? question "8. When does the topological order need to be unique (LC 444)?"
    The topo order is unique iff Kahn's queue **never has more than one element at a time**. If at any iteration the queue holds ≥ 2 in-degree-0 vertices, there's ambiguity — you could emit either one first. This gives an O(V + E) check for "is the order forced by the constraints."

---

> **Next pattern up:** 0/1 Knapsack DP — the canonical "pick a subset under a capacity constraint" template, with the unbounded variant and the space-optimised 1D rolling array (page coming next).
