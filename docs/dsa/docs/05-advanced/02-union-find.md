# Union-Find / Disjoint Set Union (DSU)

> The data structure for **dynamic connectivity**. You have a set of elements partitioned into disjoint groups, and you support two operations: `find(x)` (which group is `x` in?) and `union(x, y)` (merge the groups of `x` and `y`). Both operations run in **near-constant amortised time** — `O(α(n))`, the inverse Ackermann function, indistinguishable from O(1) for any input that fits in a galaxy. Powers Kruskal's MST, cycle detection in undirected graphs, friend-circle / island problems with **online** edge additions, and the offline Tarjan LCA algorithm.

<span class="phase-status phase-done">Phase 6 — Advanced</span>

---

## 📖 What is Union-Find?

A partition of `{0, 1, …, n-1}` into disjoint sets, with two operations:

- **`find(x)`** → a *representative* element of the set containing `x`. Two elements are in the same set iff their representatives are equal.
- **`union(x, y)`** → merge the sets containing `x` and `y` into one.

The standard implementation is a **forest of trees**. Each set is a tree; each element points to its parent; the root is the representative. `find` walks parent pointers to the root; `union` makes one root point to the other.

Without optimisation, find/union are O(n) worst case (a degenerate chain). Two tricks together push that to amortised O(α(n)):

1. **Path compression** in `find`: as you walk to the root, re-point every visited node directly at the root. Future `find`s on those nodes are O(1).
2. **Union by rank (or size)**: when merging, hang the smaller tree under the larger. Keeps trees shallow.

The mental model: imagine each element as a person, parent as "who I report to," and the root as the manager of the team. `find` walks up the org chart to find the manager. With path compression, after one walk everyone you passed reports directly to the manager — flattening the org chart on every query.

!!! tip "The signal — when to reach for Union-Find"
    Reach for it when:

    - **Edges arrive online** and you need to ask "are u and v connected?" repeatedly.
    - "**Number of connected components**" / "minimum operations to merge" / "friend circles."
    - **Cycle detection in an undirected graph** — adding edge `(u, v)`; cycle iff already in same set.
    - **Kruskal's MST** — sort edges, add if endpoints are in different sets.
    - **Equation / equivalence problems** — `a == b`, `b == c` ⇒ `a == c`. (LC 990, LC 399 cousin.)
    - "**Accounts merge**" / "**redundant connection**" / "**string similarity groups.**"

    Don't reach for it when:

    - The graph is **fully known up front** and you want components — plain BFS/DFS is simpler.
    - You need to **delete** edges or split sets — basic DSU doesn't support deletion. (Special variants exist: link-cut trees, offline rollback DSU.)
    - The query is "shortest path" / "weighted distance" / a per-edge metric — DSU only tracks set membership, not distances.

---

## 🧩 The four flavors

### Flavor 1: Path compression + union by rank (the canonical form)

```python
class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))                              # (1) every element is its own root
        self.rank = [0] * n                                       # (2) tree depth upper bound
        self.components = n                                       # (3) running count of components

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:                          # (4) walk to the root
            root = self.parent[root]
        while self.parent[x] != root:                             # (5) path compression — second pass
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False                                          # (6) already merged
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx                                       # (7) ensure rx has the larger rank
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1                                    # (8) ranks tied — bumping one increments depth
        self.components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)
```

1. The disjoint forest starts as `n` singleton trees, each its own parent.
2. Rank is a *bound* on tree depth, not the actual depth (path compression breaks that). Initialise to 0.
3. `components` is the running count — decrement on every successful union.
4. First pass: walk parent pointers up to the root.
5. Second pass: re-walk and re-point every visited node directly at the root. The two-pass form is the cleanest path compression that doesn't recurse.
6. Already in the same set — no work, return false to signal "no merge happened" (useful for cycle detection).
7. Hang the smaller-rank tree under the larger. Smaller subtrees absorbed by larger.
8. Equal ranks: hanging one under the other increments the new root's rank by 1.

### Flavor 2: Recursive path compression (one-line find)

```python
def find(self, x: int) -> int:
    if self.parent[x] != x:
        self.parent[x] = self.find(self.parent[x])                # (1) compress on the way back
    return self.parent[x]
```

1. The cleanest expression of path compression: recurse to the root, and as the call stack unwinds, every node's parent is rewritten to the root. Same complexity, smaller code, but blows up the call stack for deep chains. Bound to recursion-limit-friendly inputs.

### Flavor 3: Union by size (instead of rank)

```python
class UnionFindSize:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]          # (1) path-halving
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.size[rx] < self.size[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        self.size[rx] += self.size[ry]                            # (2) accumulate component size
        return True
```

1. **Path halving** (Tarjan's variant): every visited node's parent is rewritten to its grandparent. One pass, single traversal, asymptotically equivalent to full compression.
2. The `size` array doubles as "size of the component containing this root" — useful when problems ask for the largest component / size queries.

### Flavor 4: Weighted DSU (with offsets — LC 399 / LC 990)

```python
class WeightedUnionFind:
    """For 'equivalence with weights': a / b = w."""
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n
        self.weight = [1.0] * n                                   # (1) weight[x] = ratio x / parent[x]

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            orig_parent = self.parent[x]
            root = self.find(orig_parent)
            self.weight[x] *= self.weight[orig_parent]            # (2) update on the way up
            self.parent[x] = root
        return self.parent[x]

    def union(self, x: int, y: int, w: float) -> None:
        """Record x / y = w."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return                                                # (3) skip if already related — could verify consistency
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
            x, y = y, x
            w = 1 / w
        self.parent[ry] = rx
        self.weight[ry] = self.weight[x] * w / self.weight[y]     # (4) maintain ratio invariant
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
```

1. Each node carries the ratio between itself and its parent. The product along the path to the root gives the ratio between the node and the root.
2. Recursive find updates weights as it compresses. After one find, `weight[x]` = ratio `x / root`.
3. For LC 990 you'd verify `x / y == w` here and report contradiction if not.
4. After merging, the new edge from `ry` to `rx` carries a weight that preserves the existing ratios.

**Examples:** LC 399 Evaluate Division, LC 990 Satisfiability of Equality Equations.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Connected components | Count groups | LC 547, LC 323 | Union all edges; count `parent[i] == i` |
| 2 | Cycle detection (undirected) | Adding an edge that closes a cycle | LC 684 | `union` returns false → cycle |
| 3 | Kruskal's MST | Min-weight spanning tree | LC 1135 | Sort edges, add iff different sets |
| 4 | Online / streaming connectivity | Edges arrive over time | LC 305 (Number of Islands II) | Process events sequentially |
| 5 | Equivalence with weights | `a / b = w` chains | LC 399, LC 990 | Weighted DSU, propagate ratios |
| 6 | Largest component query | Max size after each union | LC 952 | Track `size[]`; `max` on the fly |
| 7 | Offline grouping | Bulk merges then bulk queries | LC 1202, LC 1632 | Build all edges, do all unions, batch find |

---

## 📋 Twenty problems on Union-Find

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Number of Provinces | 547 | <span class="diff-medium">Medium</span> | Components | 📝 |
| 2 | Number of Connected Components in an Undirected Graph | 323 | <span class="diff-medium">Medium</span> | Components | 📝 |
| 3 | Redundant Connection | 684 | <span class="diff-medium">Medium</span> | Cycle detection | 📝 |
| 4 | Redundant Connection II | 685 | <span class="diff-hard">Hard</span> | Cycle + directed-edge twist | 📝 |
| 5 | Accounts Merge | 721 | <span class="diff-medium">Medium</span> | Components | 📝 |
| 6 | Most Stones Removed With Same Row or Col | 947 | <span class="diff-medium">Medium</span> | Bipartite-flavoured DSU | 📝 |
| 7 | Number of Islands II | 305 | <span class="diff-hard">Hard</span> | Online connectivity | 📝 |
| 8 | Evaluate Division | 399 | <span class="diff-medium">Medium</span> | Weighted DSU | 📝 |
| 9 | Satisfiability of Equality Equations | 990 | <span class="diff-medium">Medium</span> | Equivalence | 📝 |
| 10 | Smallest String With Swaps | 1202 | <span class="diff-medium">Medium</span> | Group + sort | 📝 |
| 11 | Min Cost to Connect All Points | 1584 | <span class="diff-medium">Medium</span> | Kruskal | 📝 |
| 12 | Connecting Cities With Minimum Cost | 1135 | <span class="diff-medium">Medium</span> | Kruskal | 📝 |
| 13 | Earliest Moment When Everyone Becomes Friends | 1101 | <span class="diff-medium">Medium</span> | Online merge until 1 component | 📝 |
| 14 | Largest Component Size by Common Factor | 952 | <span class="diff-hard">Hard</span> | DSU on factor classes | 📝 |
| 15 | Swim in Rising Water | 778 | <span class="diff-hard">Hard</span> | DSU + sorted timestamps | 📝 |
| 16 | Bricks Falling When Hit | 803 | <span class="diff-hard">Hard</span> | Reverse-time DSU | 📝 |
| 17 | Regions Cut by Slashes | 959 | <span class="diff-medium">Medium</span> | Cell-split DSU | 📝 |
| 18 | Rank Transform of a Matrix | 1632 | <span class="diff-hard">Hard</span> | DSU per rank class | 📝 |
| 19 | Process Restricted Friend Requests | 2076 | <span class="diff-hard">Hard</span> | DSU + restriction sets | 📝 |
| 20 | Graph Connectivity With Threshold | 1627 | <span class="diff-hard">Hard</span> | DSU on factor sieve | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Number of Provinces (LC 547)

> Given an `n × n` matrix `isConnected` where `isConnected[i][j] == 1` means cities `i` and `j` are directly connected, return the total number of provinces (a province = a connected component of cities).

The textbook DSU problem. Two solutions: BFS/DFS or DSU. The DSU form is one line of logic.

#### Code

```python
def find_circle_num(is_connected: list[list[int]]) -> int:
    """LC 547."""
    n = len(is_connected)
    uf = UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):                                 # (1) upper triangle only — matrix is symmetric
            if is_connected[i][j]:
                uf.union(i, j)
    return uf.components                                          # (2) running count maintained inside DSU
```

1. The matrix is symmetric. Iterate only the upper triangle to avoid doing every union twice.
2. We track `components` inside `UnionFind` so this is O(1). If the DSU didn't track it, count `sum(1 for i in range(n) if uf.find(i) == i)`.

#### Dry run on a small example

```
is_connected = [[1, 1, 0],
                [1, 1, 0],
                [0, 0, 1]]
```

Initial: `parent = [0, 1, 2]`, `rank = [0, 0, 0]`, `components = 3`.

- `(i, j) = (0, 1)`: `is_connected[0][1] = 1`. `union(0, 1)`. Both rank 0, ties; make 0 the new root, bump its rank. `parent = [0, 0, 2]`, `rank = [1, 0, 0]`, `components = 2`.
- `(i, j) = (0, 2)`: `is_connected[0][2] = 0`. Skip.
- `(i, j) = (1, 2)`: `is_connected[1][2] = 0`. Skip.

Output: `components = 2`. ✓ ({0, 1} and {2}.)

#### Why DSU here over BFS/DFS

BFS/DFS is O(n²) too (you must visit every cell of the matrix). DSU is no faster asymptotically. The win is:

- **Online edges**: if the problem becomes "edges arrive one at a time, query components after each," DSU does O(α(n)) per event; rebuilding BFS/DFS would be O(n + edges) per event.
- **Composability**: DSU plays nicely with subsequent operations (Kruskal, accounts merge, etc.).

For pure batch components on a static matrix, BFS/DFS is fine — DSU is the right tool when the problem signals dynamism or composes with other DSU-based steps.

#### Complexity

- **Time:** O(n² · α(n)) — n² edges, each union is α(n).
- **Space:** O(n) for the DSU.

---

### Deep-dive 2 — Redundant Connection (LC 684)

> Given a graph that started as a tree (n nodes, n-1 edges) and had **one extra edge** added, return the redundant edge. If multiple, return the last one in the input.

DSU's signature use case: **detect the edge that closes a cycle**.

#### Code

```python
def find_redundant_connection(edges: list[list[int]]) -> list[int]:
    """LC 684."""
    n = len(edges)
    uf = UnionFind(n + 1)                                         # (1) nodes are 1-indexed
    for u, v in edges:
        if not uf.union(u, v):                                    # (2) union returned False → already same set → cycle
            return [u, v]
    return []
```

1. LC's nodes are 1-indexed. Sizing `n + 1` avoids off-by-one (waste 1 slot).
2. `union` returns `False` when both endpoints are already in the same set — that means adding this edge closes a cycle. Return it.

#### Dry run on `edges = [[1,2],[1,3],[2,3]]`

Initial: `parent = [0, 1, 2, 3]`, all separate.

- `(1, 2)`: `find(1) = 1`, `find(2) = 2`. Different. Union → `parent[2] = 1`. Returns True.
- `(1, 3)`: `find(1) = 1`, `find(3) = 3`. Different. Union → `parent[3] = 1`. Returns True.
- `(2, 3)`: `find(2) = 1`, `find(3) = 1`. Same! Union returns False. **Redundant** — return `[2, 3]`. ✓

#### Why DSU is the right tool

- Detecting cycles in a **directed** graph is best done with DFS + a "currently in stack" flag (3-colour).
- Detecting cycles in an **undirected** graph as edges arrive is a perfect DSU job. Adding edge (u, v) closes a cycle iff u and v are already connected. One `find` per endpoint, O(α(n)) total.

#### Variant: LC 685 (Redundant Connection II)

The graph started as a **rooted tree** with directed edges, then had one extra directed edge added. Now the redundancy might be:

- A node with two parents (no cycle).
- A cycle (no two-parent node).
- Both.

Solve in three cases. DSU still finds the cycle; the two-parent node is detected by an indegree scan first. The combined logic is fiddly but the DSU primitive is identical.

#### Complexity

- **Time:** O(n · α(n)) ≈ O(n).
- **Space:** O(n).

---

### Deep-dive 3 — Accounts Merge (LC 721)

> Given a list of accounts where `accounts[i] = [name, email1, email2, ...]`, merge accounts that share *any* email. Return the merged accounts with sorted emails.

A two-stage problem. Stage 1: which accounts share an email → DSU. Stage 2: collect emails per merged group, sort, output.

#### Code

```python
from collections import defaultdict

def accounts_merge(accounts: list[list[str]]) -> list[list[str]]:
    """LC 721."""
    n = len(accounts)
    uf = UnionFind(n)

    email_to_account: dict[str, int] = {}
    for i, acc in enumerate(accounts):
        for email in acc[1:]:
            if email in email_to_account:
                uf.union(i, email_to_account[email])              # (1) merge accounts that share this email
            else:
                email_to_account[email] = i

    groups: defaultdict[int, set[str]] = defaultdict(set)
    for email, idx in email_to_account.items():
        groups[uf.find(idx)].add(email)                           # (2) bucket emails by component root

    return [[accounts[root][0]] + sorted(emails) for root, emails in groups.items()]
```

1. The clever bit: as we scan emails, the **first time** we see an email we record which account it belongs to. The **second time** we see it, we union the two accounts. This sweeps in O(total_emails · α(n)).
2. After all unions, every email maps to its account's root. Bucket emails by root, prepend the account's name (any account in the group has it — they're the same person), sort the emails.

#### Why DSU shines here

The naive approach: build a graph where accounts are nodes and shared-email is an edge, run BFS. That's O(n² · avg_emails²) just to build the edges (compare every pair of accounts). The DSU approach scans emails linearly with a hash, doing O(1) work per unique email and one union per repeat.

#### Dry run sketch on a tiny input

```
accounts = [
    ["John", "john@a.com", "j2@b.com"],
    ["John", "john@a.com", "j3@c.com"],
    ["Mary", "mary@a.com"],
]
```

- Account 0's emails: `john@a.com → 0`, `j2@b.com → 0`.
- Account 1's emails: `john@a.com` already in map (→ 0), `union(1, 0)`. `j3@c.com → 1` (but find(1) = 0).
- Account 2's emails: `mary@a.com → 2`.

After unions: roots are 0 (covers accounts 0, 1) and 2 (covers account 2).

Bucket: 0 → {john@a.com, j2@b.com, j3@c.com}; 2 → {mary@a.com}.

Output:
```
[["John", "j2@b.com", "j3@c.com", "john@a.com"],
 ["Mary", "mary@a.com"]]
```

#### Complexity

- **Time:** O(N · K · α(N) + N · K log(N · K)), where N = number of accounts, K = avg emails per account. The log factor is the per-group sort.
- **Space:** O(N · K) for the email map and groups.

---

## 🐛 Common bugs

1. **No path compression.** Without it, find can be O(n) on adversarial inputs. The "I'll add it later if needed" plan never survives a stress test.
2. **Path compression that recurses too deep.** Recursive find blows the Python recursion limit (~1000 by default) on chains of length > 1000. Use the iterative two-pass form for large n, or `sys.setrecursionlimit(...)`.
3. **Union by rank but `union(x, y)` leaves rank stale.** When ranks tie, you must increment the new root's rank. Forgetting that bump degrades to O(log n) trees instead of α(n).
4. **Confusing rank with size.** Rank is depth-bound; size is element count. They're not interchangeable. Pick one and stick with it.
5. **Returning `True` from union when already merged.** The convention is: union returns whether a real merge happened. False on already-same-set is essential for cycle detection (LC 684).
6. **Forgetting to size DSU for 1-indexed nodes.** Many LC graphs are 1..n. Allocate `n + 1` slots and waste index 0.
7. **Forgetting the symmetric edges in adjacency-matrix problems.** Iterating both upper and lower triangles is harmless but slow; iterate only the upper triangle for symmetric inputs.
8. **DSU on something that isn't an `int`.** Map your strings/cells/coordinates to integer ids first. `(r, c) → r * cols + c` is the standard 2D-cell trick.
9. **Trying to support union *and split*.** Standard DSU has no `split` or `delete`. If you need to "remove an edge," reverse the timeline: start from the final state, and add edges in reverse order. (LC 803 Bricks Falling is the textbook reverse-time DSU problem.)

---

## 🗣️ Interviewer phrasings to recognize

- "Number of **connected components** / **provinces** / **friend circles**." → LC 547, LC 323, basic union per edge.
- "Edge that **completes a cycle**." → LC 684, `union` returns False.
- "**Minimum spanning tree** / minimum cost to connect." → Kruskal: sort edges, union if different.
- "**Online** edges; query components after each." → LC 305, DSU is purpose-built.
- "Equation chains: a == b, b == c → a == c." → LC 990, basic DSU. Add ratios → LC 399.
- "Merge **accounts** / addresses / aliases." → LC 721, hash + DSU.
- "**Largest component** after each merge." → LC 952, track size on union.
- "Reverse-time problem (e.g., bricks fall when hit)." → process events in reverse with DSU adds.

---

## 🧭 Connections to other patterns

- **[Topological Sort](../04-patterns/14-topological-sort.md)** — both work on graphs but for different questions: topo for ordering on DAGs, DSU for connectivity on undirected.
- **[Tree BFS](../04-patterns/07-tree-bfs.md) / [Tree DFS](../04-patterns/08-tree-dfs.md)** — BFS/DFS gives connected components on a static graph; DSU wins when edges are dynamic.
- **Tries** ([01-tries.md](01-tries.md)) — different DS, but both share the "advanced senior interview" flavour.
- **Kruskal's MST** — DSU is the engine. Sort edges by weight, add each iff endpoints are in different sets.
- **Tarjan offline LCA** — old-school algorithm that uses DSU to answer LCA queries on a tree in O((n + q) α(n)).

---

## ✅ Self-check — 8 questions

??? question "1. Why is the amortised cost of find/union α(n) and not log n?"
    Path compression flattens trees aggressively — every find call shortens the path of all visited nodes. Combined with union-by-rank (or size) keeping trees balanced when merged, the amortised cost over m operations on n elements is O(m · α(n)), where α is the inverse Ackermann function. α(n) ≤ 4 for any n ≤ 2^65536, so it's effectively a constant.

??? question "2. What does `union` returning `False` mean?"
    Both endpoints are already in the same set — no real merge happened. This is the cycle-detection signal: in an undirected graph, adding an edge between two already-connected nodes closes a cycle. LC 684 is the textbook use.

??? question "3. Why use rank instead of plain depth?"
    Path compression invalidates true depth (it shortens after every find). Rank is a *bound* on depth that's cheap to maintain — only updated when two trees of equal rank merge. The bound is enough to guarantee α(n) amortised cost.

??? question "4. When would you pick union-by-size over union-by-rank?"
    When you need the **size of the component** as part of the answer (largest island, minimum-friend-circles, etc.). Union-by-size lets you read `size[find(x)]` directly. They're asymptotically identical; pick whichever the problem rewards.

??? question "5. Can you delete edges or split sets with DSU?"
    Not the standard DSU. Two workarounds: (a) **reverse-time** processing — if the timeline of operations is fixed, run them backwards so deletions become additions (LC 803). (b) **Link-cut trees** — a dynamic-tree data structure (Tarjan) that supports both link and cut in O(log n) per op. Far more complex.

??? question "6. How do you adapt DSU to non-integer keys (strings, coordinates)?"
    Map them to integers first. Coordinates: `id = r * cols + c`. Strings: a `dict[str, int]` assigning a fresh id per first-seen string. The DSU array is then sized to the number of unique keys.

??? question "7. How does Kruskal's MST use DSU?"
    Sort edges by weight ascending. For each edge `(u, v, w)`, if `find(u) != find(v)`, take the edge (it doesn't form a cycle) and union them. Stop when n-1 edges are taken. DSU's role is the cycle-check in O(α(n)) per edge.

??? question "8. Why does LC 399 (Evaluate Division) need *weighted* DSU instead of plain?"
    The problem isn't just "are a and b in the same group?" — it's "what's the ratio a / b given a chain of known ratios?" Each parent pointer needs to carry a multiplicative weight so that the product along the path to the root gives the ratio between the node and the root. Two nodes' ratio is `weight[a] / weight[b]` once they share a root.

---

> **Up next in Advanced:** Segment Trees — range queries (sum, min, max) and lazy propagation for range updates in O(log n). Then Fenwick trees (BIT), suffix arrays, HLD, and Mo's.
