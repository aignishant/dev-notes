# Max-Flow / Min-Cut

> The single most powerful **graph reduction** in algorithms. Dozens of seemingly-unrelated problems — bipartite matching, edge-disjoint paths, project selection, image segmentation, baseball-elimination — collapse to "send the most flow you can from a source `s` to a sink `t` in a directed graph with edge capacities." Solve it once with Dinic's algorithm in `O(V² E)` (or `O(E √V)` on unit-capacity graphs), and a whole world of problems opens up. The duality theorem **max-flow = min-cut** lets you read the bottleneck off the saturated edges for free.

<span class="phase-status phase-done">Phase 7 — Ultra-Advanced</span>

---

## 📖 What are max-flow and min-cut?

Given a directed graph `G = (V, E)` with non-negative integer **capacities** `c(u, v)` on each edge, a **source** `s`, and a **sink** `t`. A **flow** is a function `f(u, v) ≥ 0` on edges satisfying:

1. **Capacity:** `f(u, v) ≤ c(u, v)` for every edge.
2. **Conservation:** for every vertex `v ≠ s, t`, total in-flow = total out-flow.

The **value** of the flow is the total flow leaving `s` (= total flow entering `t`). **Max-flow** asks for the flow of maximum value.

A **cut** partitions `V` into `(S, T)` with `s ∈ S` and `t ∈ T`. The cut's **capacity** is the sum of capacities of edges from `S` to `T`. **Min-cut** asks for the cut of minimum capacity.

**Max-flow / min-cut theorem (the duality):** the value of the max-flow equals the capacity of the min-cut. After running max-flow, the min-cut is exactly the edges saturated by the flow that lie on the boundary between vertices reachable from `s` in the residual graph and the rest.

The algorithmic approach is **augmenting paths**: repeatedly find a path from `s` to `t` in the **residual graph** (edges with remaining capacity), push flow equal to the path's bottleneck, and iterate until no augmenting path exists. Cleverness in choosing *which* path leads to the runtime classes:

- **Ford-Fulkerson (any path):** can be `O(E · max_flow)` — pathological with irrational capacities.
- **Edmonds-Karp (shortest path / BFS):** `O(V · E²)`.
- **Dinic's (level graph + DFS-blocking-flow):** `O(V² E)` general, `O(E √V)` for unit-capacity bipartite matching.

The mental model: think of the graph as a network of **pipes** with given capacities. You're filling water from `s` and asking how much can reach `t`. The min-cut is the bottleneck — the narrowest "throat" in the pipe network.

!!! tip "The signal — when to reach for max-flow"
    Reach for it when:

    - **Bipartite matching** — left and right vertex sets, find max-cardinality matching.
    - **Edge-disjoint / vertex-disjoint paths** between two nodes.
    - **Project selection** — choose projects with prerequisites to maximise net profit.
    - **Image segmentation** — foreground/background pixel cut with smoothness penalties.
    - **Baseball elimination** — can a team still win the division?
    - "Find the **minimum number of edges to remove** to disconnect `s` from `t`."
    - "Find a **min-cut** that separates two sets" — directly the dual.

    Don't reach for it when:

    - The graph is a **DAG** with simple flow conservation — topological-DP often suffices.
    - The capacities are all 1 and the graph is undirected — BFS or Hopcroft-Karp specialised.
    - It's a **min-cost flow** problem — different algorithm (SSP / cycle-canceling).
    - The problem has a **greedy** or **flow-free** combinatorial structure (matroid, Hall's theorem direct).

---

## 🧩 The four flavors

### Flavor 1: Edmonds-Karp (BFS-augmenting paths)

The simplest correct max-flow. Find shortest augmenting paths via BFS in the residual graph; push flow equal to the bottleneck. Runs in `O(V · E²)` because each edge can become saturated at most O(V) times along a shortest path.

```python
from collections import defaultdict, deque

class MaxFlow:
    def __init__(self, n: int) -> None:
        self.n = n
        self.cap: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    def add_edge(self, u: int, v: int, c: int) -> None:
        self.cap[u][v] += c                                       # forward capacity
        # backward edge starts at 0 — created lazily by defaultdict on access

    def _bfs(self, s: int, t: int, parent: dict[int, int]) -> bool:
        seen = {s}
        q = deque([s])
        while q:
            u = q.popleft()
            for v, c in self.cap[u].items():
                if c > 0 and v not in seen:
                    seen.add(v)
                    parent[v] = u
                    if v == t: return True
                    q.append(v)
        return False

    def edmonds_karp(self, s: int, t: int) -> int:
        flow = 0
        while True:
            parent: dict[int, int] = {}
            if not self._bfs(s, t, parent): break
            # Find bottleneck along path
            bottleneck = float("inf")
            v = t
            while v != s:
                u = parent[v]
                bottleneck = min(bottleneck, self.cap[u][v])
                v = u
            # Push flow: subtract from forward, add to backward
            v = t
            while v != s:
                u = parent[v]
                self.cap[u][v] -= bottleneck
                self.cap[v][u] += bottleneck                      # reverse edge gets capacity
                v = u
            flow += bottleneck
        return flow
```

The **reverse edge trick** is the key insight: when you push flow along `u → v`, you also create a "permission to undo" by adding `bottleneck` to `cap[v][u]`. Future augmenting paths can route through `v → u` to re-route earlier choices.

### Flavor 2: Dinic's algorithm (level graph + blocking flow)

The standard fast max-flow. Each phase: BFS from `s` to label every vertex with its distance from `s` in the residual graph (level graph). Then DFS to find a *blocking flow* — saturate paths that strictly descend in level. Repeat until `t` is unreachable. Phases ≤ `V`; each phase is `O(VE)` in dense graphs and `O(E)` per augmenting path in sparse cases. Total: `O(V² E)`.

```python
class Dinic:
    def __init__(self, n: int) -> None:
        self.n = n
        self.graph: list[list[int]] = [[] for _ in range(n)]      # graph[u] = list of edge indices
        self.edges: list[list[int]] = []                          # each edge = [to, cap]

    def add_edge(self, u: int, v: int, c: int) -> None:
        self.graph[u].append(len(self.edges))
        self.edges.append([v, c])
        self.graph[v].append(len(self.edges))
        self.edges.append([u, 0])                                 # reverse edge with 0 capacity

    def _bfs(self, s: int, t: int) -> bool:
        self.level = [-1] * self.n
        self.level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for eid in self.graph[u]:
                v, c = self.edges[eid]
                if c > 0 and self.level[v] < 0:
                    self.level[v] = self.level[u] + 1
                    q.append(v)
        return self.level[t] >= 0

    def _dfs(self, u: int, t: int, pushed: int) -> int:
        if u == t: return pushed
        while self.it[u] < len(self.graph[u]):
            eid = self.graph[u][self.it[u]]
            v, c = self.edges[eid]
            if c > 0 and self.level[v] == self.level[u] + 1:
                d = self._dfs(v, t, min(pushed, c))
                if d > 0:
                    self.edges[eid][1] -= d
                    self.edges[eid ^ 1][1] += d                   # XOR 1 toggles to reverse edge
                    return d
            self.it[u] += 1                                       # current arc dead
        return 0

    def max_flow(self, s: int, t: int) -> int:
        flow = 0
        while self._bfs(s, t):
            self.it = [0] * self.n                                # current-arc heuristic
            while (pushed := self._dfs(s, t, float("inf"))) > 0:
                flow += pushed
        return flow
```

The **current-arc heuristic** (`self.it[u]`) is critical: once an outgoing edge from `u` is exhausted at the current level, mark it dead — never re-scan it within the phase. Without it, Dinic's degrades to `O(V²E²)`.

### Flavor 3: Bipartite matching as max-flow

Maximum bipartite matching in a graph with `L ∪ R` vertices: add source `s` connected to every `L` with capacity 1; every original edge `L → R` with capacity 1; every `R → t` with capacity 1. Max flow = max matching. With Dinic's on unit-capacity bipartite, runtime is `O(E √V)` (Hopcroft-Karp).

```python
def max_bipartite_matching(left: int, right: int, edges: list[tuple[int, int]]) -> int:
    """L vertices: 0..left-1; R vertices: left..left+right-1; source = left+right; sink = left+right+1."""
    s, t = left + right, left + right + 1
    g = Dinic(left + right + 2)
    for u in range(left): g.add_edge(s, u, 1)
    for u, v in edges:    g.add_edge(u, left + v, 1)
    for v in range(right): g.add_edge(left + v, t, 1)
    return g.max_flow(s, t)
```

The reduction is mechanical, but the insight is profound: **matching = flow with capacities = 1**. Hall's marriage theorem and König's theorem fall out of max-flow / min-cut applied to this setup.

### Flavor 4: Project selection / closure problem

You have `n` projects. Each project `p` has a profit `π(p)` (possibly negative — these are the *costs*). Some projects depend on others — to do `p` you must also do its prerequisites. Pick a set `S` of projects (closed under dependencies) maximising `Σ π(p)`.

**Reduction to min-cut:**

- Source `s` connects to each profitable project `p` with capacity `π(p)`.
- Each cost project `p` (negative profit) connects to sink `t` with capacity `|π(p)|`.
- Each dependency `p → q` (you need `q` to do `p`) becomes an edge `p → q` with capacity `+∞`.

The min `s-t` cut corresponds to the optimal closed set: vertices on the `s` side are picked, vertices on the `t` side are skipped. The infinite-capacity dependency edges ensure no min-cut violates a dependency.

**Max profit = (sum of positive profits) − min cut.**

```python
def project_selection(profits: list[int], deps: list[tuple[int, int]]) -> int:
    """profits[i] = profit of project i (can be negative). deps = (p, q) means p depends on q."""
    n = len(profits)
    s, t = n, n + 1
    g = Dinic(n + 2)
    pos_sum = 0
    for i, p in enumerate(profits):
        if p > 0:
            g.add_edge(s, i, p)
            pos_sum += p
        elif p < 0:
            g.add_edge(i, t, -p)
    for p, q in deps:
        g.add_edge(p, q, 10**18)                                  # infinity
    return pos_sum - g.max_flow(s, t)
```

This template solves an enormous class of "select with prerequisites" optimisation problems.

---

## 🔍 Sub-pattern at-a-glance

| # | Problem class                       | Reduction                                                | Complexity            |
|---|-------------------------------------|----------------------------------------------------------|-----------------------|
| 1 | Generic max-flow                    | Direct                                                   | O(V² E) Dinic         |
| 2 | Bipartite matching                  | Source→L→R→sink, all caps 1                              | O(E √V) on unit caps  |
| 3 | Vertex-disjoint paths               | Split each vertex `v` into `v_in → v_out` with cap 1     | O(V² E)               |
| 4 | Edge-disjoint paths                 | Set every edge cap to 1                                  | O(V² E)               |
| 5 | Project selection (closure)         | Source→profit→cost→sink + ∞ dep edges                    | O(V² E)               |
| 6 | Min-vertex-cover (bipartite)        | König: min-vertex-cover = max-matching                   | O(E √V)               |
| 7 | Image segmentation                  | Source=fg, sink=bg, smoothness penalties on neighbours   | O(V² E)               |
| 8 | Baseball elimination                | Construct game-graph, max-flow saturates iff team alive  | O(V² E) per team      |

---

## 📚 20 problems where max-flow / min-cut is the canonical answer

| #  | Source      | Problem                                          | Difficulty | Key insight                                                       |
|----|-------------|--------------------------------------------------|------------|-------------------------------------------------------------------|
| 1  | LC 1349     | Maximum students taking exam (no-cheat seating)  | Hard       | Bipartite matching on a chess-board parity graph.                 |
| 2  | LC 1494     | Parallel courses II                              | Hard       | Bitmask DP wins; max-flow is overkill but works.                  |
| 3  | LC 1947     | Maximum compatibility score sum                  | Medium     | Direct bipartite-matching-by-weight via min-cost flow.            |
| 4  | LC 1820     | Maximum number of accepted invitations           | Medium     | Textbook bipartite matching.                                      |
| 5  | UVa 820     | Internet bandwidth (multi-edge max-flow)         | Medium     | Sum capacities on multi-edges; standard Dinic's.                  |
| 6  | SPOJ FASTFLOW | Maximum flow                                   | Medium     | The textbook Dinic's stress test.                                 |
| 7  | CF 1184E1   | Daleks' Invasion (min-cut on tree)               | Hard       | Tree min-cut = max edge on path; Kruskal-DSU solves directly.     |
| 8  | UVa 11380   | Down Went the Titanic (escape via flow)          | Hard       | Grid → flow network with capacities for jumping-off points.       |
| 9  | LC 2092     | Find all people with secret (offline matching)   | Hard       | Process meetings sorted by time; DSU wins, but flow also works.   |
| 10 | CF 277E     | Binary Tree on plane                             | Hard       | Min-cost flow with each node having ≤ 2 outgoing children.        |
| 11 | UVa 1660    | Cable TV Network (vertex connectivity)           | Hard       | Vertex split + min-cut for k-vertex connectivity.                 |
| 12 | LC 765      | Couples holding hands                            | Hard       | DSU is canonical, but matching-flow gives the same answer.        |
| 13 | CSES 1694   | Download Speed                                   | Easy       | Vanilla Dinic's max-flow.                                         |
| 14 | CSES 1696   | Police Chase (min-cut)                           | Medium     | Set all edges cap 1; min-cut = min edges to disconnect.           |
| 15 | CSES 1711   | Distinct Routes (edge-disjoint paths)            | Medium     | Edge-cap 1 max-flow; reconstruct paths via DFS on saturated edges.|
| 16 | UVa 11045   | My T-shirt suits me (size matching)              | Medium     | Bipartite matching: sizes ↔ players.                              |
| 17 | UVa 10092   | The Problem with the Problem Setter              | Medium     | Bipartite matching: problems ↔ categories with capacity > 1.      |
| 18 | UVa 753     | Plug for UNIX                                    | Medium     | Multi-source bipartite matching with adapter chains.              |
| 19 | LC 1820     | Same as #4                                       | Medium     | Reinforces the bipartite-matching template.                       |
| 20 | UVa 11248   | Frequency Hopping (min-cut increase)             | Hard       | Run max-flow, then on each edge ask "does increasing it help?"    |

---

## 🔬 Deep-dive 1 — Why the reverse-edge trick works (and the duality theorem)

The single most non-obvious step in max-flow: when you push flow along `u → v`, you **add capacity to `v → u`**.

**Why:** subsequent augmenting paths can use the reverse edge to **cancel** earlier flow. Imagine you greedily push flow along `s → a → b → t`, but the optimal solution sends flow `s → a → t` and `s → b → t`. Without reverse edges, you're stuck. *With* reverse edges, a path `s → b → a → t` exists in the residual graph: pushing 1 unit along it cancels the `a → b` choice (reverse edge has capacity 1) and re-routes through `b → t` and `a → t` — giving total flow 2 instead of 1.

**The duality theorem (max-flow = min-cut):** at termination, no augmenting path exists in the residual graph. Let `S` = set of vertices reachable from `s` in the residual graph; `T` = the rest. Then `t ∈ T` (otherwise an augmenting path would exist). Every edge `u → v` from `S` to `T` must be saturated (else `v` would be reachable). So the cut `(S, T)` has capacity = current flow value. Since *any* cut has capacity ≥ max flow (each unit of flow crosses the cut at least once), our found cut is the **minimum** cut.

**Reading the min-cut after running max-flow:**

```python
def find_min_cut(g: Dinic, s: int) -> tuple[set[int], list[tuple[int, int]]]:
    # BFS in residual graph from s
    seen = {s}
    q = deque([s])
    while q:
        u = q.popleft()
        for eid in g.graph[u]:
            v, c = g.edges[eid]
            if c > 0 and v not in seen:
                seen.add(v)
                q.append(v)
    cut_edges = []
    for u in seen:
        for eid in g.graph[u]:
            v, _ = g.edges[eid]
            if v not in seen and (eid % 2 == 0):                  # forward edge from S to T
                cut_edges.append((u, v))
    return seen, cut_edges
```

The `seen` set is `S`; edges from `S` to outside are the min-cut.

---

## 🔬 Deep-dive 2 — Bipartite matching: small example traced through

**Problem:** Match 3 candidates `A, B, C` to 3 jobs `1, 2, 3`. Compatibility:

- `A` can do `{1, 2}`
- `B` can do `{1}`
- `C` can do `{2, 3}`

**Construction:** source `s = 6`, sink `t = 7`. Vertices 0..2 = candidates, 3..5 = jobs.

Edges (all capacity 1):
- `s → A, s → B, s → C` (i.e., `6→0, 6→1, 6→2`)
- `A → 1, A → 2, B → 1, C → 2, C → 3` (i.e., `0→3, 0→4, 1→3, 2→4, 2→5`)
- `1 → t, 2 → t, 3 → t` (i.e., `3→7, 4→7, 5→7`)

**Dinic's run, phase 1:**
- BFS levels: `s=0, A=B=C=1, jobs=2, t=3`.
- DFS from `s`: try `s → A → 1 → t`. Push 1.
- DFS from `s`: try `s → B → 1`. `1 → t` saturated; backtrack. `B`'s only edge dead; backtrack to `s`.
- DFS from `s`: try `s → C → 2 → t`. Push 1. Total flow so far: 2.

**Dinic's run, phase 2:**
- Residual: `s → B → 1 → A → 2 → C → 3 → t` is reachable (1→A and 2→C are reverse edges).
- BFS levels in residual: `s=0, B=1, 1=2, A=3, 2=4, C=5, 3=6, t=7`.
- DFS: `s → B → 1 → A → 2 → C → 3 → t`. Push 1. Total flow: 3.

**Result:** max flow = 3 = perfect matching. Reading off forward-edge saturation:
- `A → 2` is saturated (matched to job 2).
- `B → 1` is saturated (matched to job 1).
- `C → 3` is saturated (matched to job 3).

The augmenting path in phase 2 *re-routed* `A` from job 1 to job 2, freeing job 1 for `B`. **This is exactly what the reverse-edge trick enables.** Without it, the greedy matching `A→1, C→2` would leave `B` and `3` unmatched at flow value 2.

---

## 🔬 Deep-dive 3 — Project selection step-by-step

**Problem:** 4 projects with profits `[10, -5, -8, 6]`. Dependencies: project 0 needs project 1 (`0 → 1`); project 3 needs projects 1 and 2 (`3 → 1, 3 → 2`).

**Construction:**

- Sum of positive profits: `10 + 6 = 16`.
- `s → 0` cap 10 (profit).
- `s → 3` cap 6.
- `1 → t` cap 5 (cost = -profit).
- `2 → t` cap 8.
- `0 → 1` cap ∞.
- `3 → 1` cap ∞.
- `3 → 2` cap ∞.

**Question:** what's the optimal subset?

Running Dinic's:
- Path `s → 0 → 1 → t` with bottleneck `min(10, ∞, 5) = 5`. Push 5. Flow = 5.
- Path `s → 3 → 2 → t` with bottleneck `min(6, ∞, 8) = 6`. Push 6. Flow = 11.
- Path `s → 3 → 1 → t`? `3 → 1` is ∞, but `1 → t` has 0 residual. Try via reverse `1 → 0`: `s → 3 → 1 → 0` — but `0 → s` reverse goes only back to source, dead end. No more augmenting paths.

**Min-cut value: 11.** **Max profit: 16 − 11 = 5.**

**Reading the cut:** BFS from `s` in residual: `s` and `3` are reachable (the edge `s → 3` has 0 residual? No — capacity 6, pushed 6, residual 0. Hmm, so `3` is NOT directly reachable. Let me reconsider — what about reverse edges? `3` is reachable via `s → 0 → ... `? `s → 0` has residual 5 (pushed 5 of 10). Yes, `0` is reachable. From `0`, reverse edge `0 ← 1` doesn't help for forward reach. `s → 3`? residual 0, blocked. Actually `3` is unreachable.

**S = {s, 0}, T = {1, 2, 3, t}.** The cut: `s → 3` (saturated, cap 6), `0 → 1` (∞, but pushed 5 — hmm — wait, `0 → 1` has cap ∞ so residual is huge, so 1 IS reachable from 0!).

Let me redo: `s → 0 → 1` reaches 1 (residual cap on `0 → 1` is `∞ - 5`). Then `1 → t` saturated → blocked. `1 → 3` reverse? `3 → 1` was ∞, pushed 0 actual flow on it (we tried but couldn't), so reverse `1 → 3` has 0 residual. So `3` and `2` and `t` aren't reachable.

**Final S = {s, 0, 1}, T = {2, 3, t}.** Cut edges from S to T: `1 → t` (cap 5, saturated) and `s → 3` (cap 6, saturated). Cut value = 5 + 6 = 11. ✓

**Selected projects (S minus s): {0, 1}.** Net profit: `10 - 5 = 5`. ✓

So we pick projects 0 and 1 (skipping 2 and 3) for net profit 5. Project 3 is unprofitable because it needs project 2's cost (-8), and 6 - 8 < 0.

The min-cut gave the optimal selection **automatically** — no DP, no enumeration.

---

## 🐛 Common bugs

1. **Forgetting reverse edges.** The whole algorithm depends on them. Without reverse edges, max-flow gives only a "greedy" approximation of the true max.
2. **Adding reverse edge with capacity equal to forward cap.** Reverse starts at **0** capacity; only flow-pushing increases it. Setting both to `c` would let you push flow in both directions freely — wrong.
3. **For undirected edges, treat as two directed edges of capacity c each** (not one with cap c). And both get reverse edges of cap 0.
4. **Source or sink chosen wrong in bipartite matching.** Always `s → L → R → t`; never the other way around.
5. **Missing the current-arc heuristic in Dinic's.** Without it, repeated rescanning of dead arcs in DFS pushes the runtime to O(V²E²) — TLE on any non-trivial test.
6. **`graph[u]` storing edges instead of edge indices.** You need indices to update the underlying `edges` array, and the XOR-1 trick requires consecutive forward/reverse pairs.
7. **Integer overflow on capacities.** Use 10**18 (not float inf) for ∞ to avoid float comparison issues with integers.
8. **Vertex-capacity problems (e.g. vertex-disjoint paths) without splitting.** Each vertex `v` must be split into `v_in → v_out` with capacity equal to the vertex's capacity; all in-edges go to `v_in`, out-edges leave `v_out`. Forgetting this gives wrong answers on vertex-constraint problems.

---

## 🗣️ Interviewer phrasings to recognize

- "Maximum **bipartite matching**" → max-flow on unit caps, or Hopcroft-Karp for the same complexity bound.
- "**Minimum number of edges to remove** to disconnect `s` from `t`" → set all edge caps to 1 → min-cut = answer.
- "**Project / task selection** with prerequisites and profits" → project-selection min-cut.
- "**Image segmentation** with foreground/background and smoothness" → Boykov-Kolmogorov, but the problem is min-cut at heart.
- "How many **disjoint paths** between two nodes?" → max-flow with unit caps.
- "**Network reliability** — min number of links to fail" → min-cut.
- "Can `team X` still **win the division**?" → baseball elimination via max-flow.

---

## 🧭 Connections to other patterns

- **[Topological Sort](../04-patterns/14-topological-sort.md)** — DAG problems sometimes look like flow but can be solved via topological DP without the flow machinery.
- **[Union-Find / DSU](../05-advanced/02-union-find.md)** — for tree min-cut or "minimum edge to disconnect," DSU often replaces flow.
- **Bipartite matching specialised algorithms** — Hopcroft-Karp matches Dinic's `O(E √V)` exactly. Hungarian algorithm for assignment with weights.
- **Min-cost max-flow** — extends max-flow to "send max flow at minimum cost." Used in transportation, assignment with weights, and Codeforces-tier problems.
- **Linear programming duality** — max-flow / min-cut is the canonical example of LP duality. Once you see it here, LP duality starts to make sense everywhere.

---

## ✅ Self-check — 8 questions

??? question "1. Why does the reverse-edge trick work?"
    It allows future augmenting paths to **cancel** earlier flow choices. Without reverse edges, a greedy push along `s → a → b → t` blocks better solutions; with reverse edges, a path `s → b → a → t` in the residual graph re-routes optimally.

??? question "2. State the max-flow / min-cut duality theorem and why the proof works."
    Max-flow value = min-cut capacity. After max-flow terminates, let S = vertices reachable from s in the residual graph. Every edge from S to V\S must be saturated (else V\S would be reachable). So the cut (S, V\S) has capacity = flow value. Any cut has capacity ≥ max flow, so this cut is min.

??? question "3. What's the runtime of Dinic's on a unit-capacity bipartite graph, and why is it different from the general bound?"
    O(E √V) — much better than the general O(V²E). On unit caps, the number of BFS phases is bounded by O(√V) because after √V phases the current flow is within √V of optimal (by a level-graph length argument), and each remaining augmentation pushes 1 unit.

??? question "4. How is bipartite matching reduced to max-flow?"
    Add source s connected to every left vertex with cap 1; original edges L→R with cap 1; every right vertex to sink t with cap 1. Max-flow value = max matching size. Saturated L→R edges are the matching pairs.

??? question "5. What's the project-selection / closure reduction?"
    Source connects to profitable projects (cap = profit); cost projects connect to sink (cap = |profit|); dependencies are ∞-capacity edges. Min-cut = unrealised profit. Max profit = total positive profits − min-cut.

??? question "6. What's the current-arc heuristic, and why is Dinic's much slower without it?"
    During DFS, once an outgoing edge from u can no longer push flow at the current level, advance u's pointer past it permanently within the phase. Without this, every DFS rescans dead arcs from the start, giving O(V²E²) instead of O(V²E).

??? question "7. How do you reduce vertex-disjoint paths to max-flow?"
    Split each vertex v into v_in → v_out with capacity 1. All in-edges go to v_in; out-edges leave v_out. Then standard edge-disjoint max-flow on the split graph gives max vertex-disjoint paths.

??? question "8. When should you NOT use max-flow even though the problem looks like it?"
    When the graph is a DAG and flow conservation isn't actually constrained — topological DP suffices. When the problem reduces to a matroid intersection with greedy. When capacities are huge but flow value is small — Ford-Fulkerson with capacity scaling or min-cost flow may be more natural.

---

> **Up next in Ultra-Advanced:** Computational Geometry — convex hull (Graham scan, Andrew's monotone chain), line sweep for closest-pair-in-plane, point-in-polygon, and KD-trees for spatial queries.
