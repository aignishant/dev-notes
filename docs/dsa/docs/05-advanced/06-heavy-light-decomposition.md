# Heavy-Light Decomposition (HLD)

> The trick that turns "**path queries on a tree**" into "**range queries on an array**." Decompose the tree into a small number of vertex-disjoint **chains** such that any root-to-leaf path crosses at most `O(log n)` chains. Lay each chain contiguously in an array; answer path queries by stitching together `O(log n)` range queries on a segment tree (or BIT). Net: **O(log² n) per path query / update** on a tree of n nodes.

<span class="phase-status phase-inprogress">Phase 6 — Advanced topic (Batch 37)</span>

---

## 📖 What is heavy-light decomposition?

Given a rooted tree, classify each non-leaf node's edge to its **heaviest child** (the child whose subtree has the most nodes) as a **heavy edge**; every other edge to a child is a **light edge**. Heavy edges chain together to form **heavy paths**; light edges connect different heavy paths.

**Key property (the magic):** any root-to-leaf path crosses **at most `log n` light edges**, and therefore at most `log n + 1` heavy chains. Why? Each light edge climbs from a subtree of size `s` to a subtree of size `> 2s` (because the heavy child got picked instead) — so subtree size at least doubles each light edge climbed.

Once chains are identified, lay them out in a flat array using a DFS order that visits each chain contiguously. Build a segment tree on this array. Now any path query splits into `O(log n)` chain segments, each a range query on the array — `O(log² n)` total.

The mental model: heavy chains are **highways** through the tree; light edges are **off-ramps**. Climbing from any node to the root uses the highway whenever possible and only takes off-ramps when crossing chains.

!!! tip "The signal — when to reach for HLD"
    Reach for it when:

    - The tree is **rooted with weighted nodes or edges** and you need **path queries** (sum/min/max on a u-v path).
    - **Point updates** to nodes and **path queries** interleave.
    - You'd reach for an Euler tour but the operation isn't *subtree* — it's *path*.
    - LCA is a sub-routine — HLD gives O(log n) LCA implicitly.

    Don't reach for it when:

    - **Subtree queries only** (sum / max in subtree of v) — Euler tour + segment tree is simpler.
    - **Static tree, batch path queries** — Tarjan offline LCA + auxiliary work is often cleaner.
    - **Tree is a path** — HLD degenerates to a single chain; just use a segment tree directly.
    - The tree is small (n ≤ 1000) — brute force with LCA is faster to write and run.

---

## 🧩 The two flavors

### Flavor 1: Vertex-weighted HLD with segment tree

The standard form. Weights live on nodes; path queries aggregate node values.

```python
class HLD:
    """Vertex-weighted HLD. Build once; supports path query/update via segment tree."""
    def __init__(self, n: int, adj: list[list[int]], weights: list[int], root: int = 0) -> None:
        self.n = n
        self.adj = adj
        self.parent = [-1] * n
        self.depth = [0] * n
        self.size = [0] * n
        self.heavy = [-1] * n                                     # heavy[v] = v's heavy child, -1 if leaf
        self.head = [0] * n                                       # head[v] = top of v's heavy chain
        self.pos = [0] * n                                        # pos[v] = v's index in the flat array
        self._dfs_size(root, -1)
        self._dfs_decompose(root, root, -1)

        flat = [0] * n
        for v in range(n):
            flat[self.pos[v]] = weights[v]
        self.seg = SegTree(flat)                                  # any range-sum seg tree

    def _dfs_size(self, v: int, p: int) -> None:
        self.parent[v] = p
        self.size[v] = 1
        max_child_size = 0
        for u in self.adj[v]:
            if u == p:
                continue
            self.depth[u] = self.depth[v] + 1
            self._dfs_size(u, v)
            self.size[v] += self.size[u]
            if self.size[u] > max_child_size:                     # (1) heaviest child
                max_child_size = self.size[u]
                self.heavy[v] = u

    _dfs_pos = 0

    def _dfs_decompose(self, v: int, h: int, p: int) -> None:
        self.head[v] = h
        self.pos[v] = HLD._dfs_pos
        HLD._dfs_pos += 1
        if self.heavy[v] != -1:                                   # (2) extend heavy chain first
            self._dfs_decompose(self.heavy[v], h, v)
        for u in self.adj[v]:
            if u == p or u == self.heavy[v]:
                continue
            self._dfs_decompose(u, u, v)                          # (3) start a new chain at u

    def update_node(self, v: int, val: int) -> None:
        self.seg.update(self.pos[v], val)

    def path_query(self, u: int, v: int) -> int:
        res = 0
        while self.head[u] != self.head[v]:                       # (4) climb until both on same chain
            if self.depth[self.head[u]] < self.depth[self.head[v]]:
                u, v = v, u                                        # ensure head[u] is the deeper chain head
            res += self.seg.range_sum(self.pos[self.head[u]], self.pos[u])
            u = self.parent[self.head[u]]                         # (5) jump to parent of chain head
        if self.depth[u] > self.depth[v]:
            u, v = v, u
        res += self.seg.range_sum(self.pos[u], self.pos[v])       # (6) final segment within shared chain
        return res
```

1. The "heaviest child" rule: pick the child with the largest subtree.
2. **Heavy first** in the decompose DFS — this puts heavy-chain nodes at consecutive positions in the flat array.
3. Each non-heavy child starts a new chain (its own head).
4. Path query: climb both `u` and `v` until they share a chain head.
5. After collecting one chain segment, jump to the parent of that chain's head — this crosses one light edge.
6. When both are on the same chain, the remaining path is one range query.

**Examples:** SPOJ QTREE, CF problems where you sum / max along tree paths under updates.

### Flavor 2: Edge-weighted HLD

When weights live on edges, not nodes. Trick: assign each edge to the **deeper endpoint**'s position in the flat array, and skip the LCA in the final range query.

The structural code is identical; only the path-query final step changes:

```python
def path_query_edge_weighted(self, u: int, v: int) -> int:
    res = 0
    while self.head[u] != self.head[v]:
        if self.depth[self.head[u]] < self.depth[self.head[v]]:
            u, v = v, u
        res += self.seg.range_sum(self.pos[self.head[u]], self.pos[u])
        u = self.parent[self.head[u]]
    if self.depth[u] > self.depth[v]:
        u, v = v, u
    if u != v:                                                    # (1) skip the LCA's "edge" (it doesn't exist)
        res += self.seg.range_sum(self.pos[u] + 1, self.pos[v])
    return res
```

1. The LCA's slot in the array represents the edge from the LCA to **its** parent — that edge isn't on the u-v path, so skip it.

---

## 🎒 The five sub-patterns

| # | Sub-pattern | Plain English | Canonical use | Trick |
|---|-------------|---------------|----------------|-------|
| 1 | Path sum + node update | Aggregate weights along u-v | Node-weighted HLD | Heavy-first DFS for contiguous chains |
| 2 | Path max/min + node update | Same shape, different combine | Node-weighted HLD + max seg | Identity = ±∞ |
| 3 | Path update + path query | Range-add along path, range-query along path | HLD + lazy seg tree | Lazy propagation inside the seg tree |
| 4 | Edge-weighted path | Weights on edges | Edge-weighted HLD | Assign edge to deeper endpoint; skip LCA in query |
| 5 | LCA via HLD | Just the chain-climb without seg tree | LCA on weighted trees | Climb until same chain → shallower of (u, v) is LCA |

---

## 📋 Twenty problems on HLD

| # | Problem | Source | Difficulty | Sub-pattern | Status |
|---|---------|--------|------------|-------------|--------|
| 1 | Path Queries (sum) | CSES | <span class="diff-hard">Hard</span> | Node-weighted | 📝 |
| 2 | Path Queries II (max) | CSES | <span class="diff-hard">Hard</span> | Path max | 📝 |
| 3 | QTREE | SPOJ | <span class="diff-hard">Hard</span> | Edge-weighted | 📝 |
| 4 | QTREE 2 (LCA + dist) | SPOJ | <span class="diff-hard">Hard</span> | Distance via HLD | 📝 |
| 5 | QTREE 3 (color) | SPOJ | <span class="diff-hard">Hard</span> | Black/white path query | 📝 |
| 6 | QTREE 4 (subtree) | SPOJ | <span class="diff-hard">Hard</span> | HLD + centroid hybrid | 📝 |
| 7 | LCA via HLD | CSES | <span class="diff-medium">Medium</span> | LCA only | 📝 |
| 8 | Tree Path Queries | various OI | <span class="diff-hard">Hard</span> | Path sum / max | 📝 |
| 9 | Subtree of Path | rare | <span class="diff-hard">Hard</span> | HLD + Euler tour combined | 📝 |
| 10 | Lowest Common Ancestor of Deepest Leaves | LC 1123 | <span class="diff-medium">Medium</span> | LCA cousin (DFS works too) | 📝 |
| 11 | Smallest Common Region | LC 1257 | <span class="diff-medium">Medium</span> | LCA cousin | 📝 |
| 12 | Sum of Distances in Tree | LC 834 | <span class="diff-hard">Hard</span> | Re-root DP (HLD overkill) | 📝 |
| 13 | Path In Zigzag Labelled Binary Tree | LC 1104 | <span class="diff-medium">Medium</span> | Implicit tree path | 📝 |
| 14 | Path With Maximum Probability | LC 1514 | <span class="diff-medium">Medium</span> | Dijkstra (HLD not needed) | 📝 |
| 15 | Number of Good Paths | LC 2421 | <span class="diff-hard">Hard</span> | DSU on values (HLD alt) | 📝 |
| 16 | Travelling Salesman in Tree | rare | <span class="diff-hard">Hard</span> | Path queries + DP | 📝 |
| 17 | Path XOR Queries | CF | <span class="diff-hard">Hard</span> | XOR aggregate on path | 📝 |
| 18 | Min Edge on Path Between Two Nodes | UVa | <span class="diff-hard">Hard</span> | Edge-weighted min | 📝 |
| 19 | Path Add + Subtree Sum | rare | <span class="diff-hard">Hard</span> | HLD path-add + Euler subtree-sum hybrid | 📝 |
| 20 | Auction Path | CF | <span class="diff-hard">Hard</span> | Path queries with sorted updates | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Why log n light edges per root-to-leaf path

The whole O(log² n) bound rests on this lemma. Let's prove it.

**Lemma.** Any root-to-leaf path traverses at most `log₂(n)` light edges.

**Proof.** Suppose we walk from a leaf up to the root. Consider one light-edge step from node `v` to its parent `p`. Because the light edge from `p` to `v` exists, **`v` is *not* the heaviest child of `p`** — some sibling `w` of `v` satisfies `size(w) ≥ size(v)`. The subtree rooted at `p` contains both `v` and `w` (and `p` itself), so `size(p) ≥ size(v) + size(w) + 1 ≥ 2 · size(v) + 1 > 2 · size(v)`.

So **every light-edge step at least doubles the subtree size**. Starting from a leaf (size 1) and reaching the root (size n), the number of doublings is at most `log₂(n)`. ∎

That's the entire algorithmic bound. Heavy edges can be many in a row — they form a chain — but a chain is a contiguous range in the flat array, so all the heavy steps in a chain combine into **one** range query. The total number of range queries per path operation is at most one per heavy chain, which is at most `log n + 1`.

### Deep-dive 2 — Building HLD on a small tree

Let's walk through the build on this rooted tree (root = 0):

```
            0
          / | \
         1  2  3
        /|     |
       4 5     6
              /|
             7 8
```

Adjacency list (omitting parent pointers):

```
0: [1, 2, 3]
1: [4, 5]
2: []
3: [6]
6: [7, 8]
```

#### Step 1: `_dfs_size` — compute subtree sizes and heavy children

| node | size | children sizes | heavy child |
|------|------|----------------|-------------|
| 4 | 1 | — | -1 |
| 5 | 1 | — | -1 |
| 1 | 3 | 4:1, 5:1 | 4 (tie — pick first) |
| 2 | 1 | — | -1 |
| 7 | 1 | — | -1 |
| 8 | 1 | — | -1 |
| 6 | 3 | 7:1, 8:1 | 7 |
| 3 | 4 | 6:3 | 6 |
| 0 | 9 | 1:3, 2:1, 3:4 | 3 |

#### Step 2: `_dfs_decompose` — assign chain heads and flat-array positions

DFS from 0, **heavy child first**:

| step | node | head | pos |
|------|------|------|-----|
| 1 | 0 | 0 | 0 |
| 2 | 3 (heavy of 0) | 0 | 1 |
| 3 | 6 (heavy of 3) | 0 | 2 |
| 4 | 7 (heavy of 6) | 0 | 3 |
| 5 | 8 (light child of 6) | 8 | 4 |
| 6 | 1 (light child of 0) | 1 | 5 |
| 7 | 4 (heavy of 1) | 1 | 6 |
| 8 | 5 (light child of 1) | 5 | 7 |
| 9 | 2 (light child of 0) | 2 | 8 |

Flat array layout (indices 0..8):

```
index: 0  1  2  3  4  5  6  7  8
node:  0  3  6  7  8  1  4  5  2
chain: A  A  A  A  B  C  C  D  E
```

Five chains: A=[0,3,6,7], B=[8], C=[1,4], D=[5], E=[2]. The longest path (root to leaf 8) crosses chains A and B — two chains, one light edge. Path 0→1→5 crosses A, C, D — three chains, two light edges. Both bounded by log₂(9) ≈ 3.

#### Step 3: Path query example — `path_query(7, 8)`

Both leaves of node 6.

- `head[7] = 0`, `head[8] = 8`. Different chains.
- `depth[head[7]] = 0`, `depth[head[8]] = 3`. Pick `u = 8` (deeper head).
- Range query on chain B: `pos[head[8]] = 4`, `pos[8] = 4`. Sum `flat[4..4]`. Adds `weights[8]` to result.
- Climb: `u = parent[head[8]] = parent[8] = 6`. So now `u = 6`, `v = 7`.
- `head[6] = 0`, `head[7] = 0`. Same chain.
- `depth[6] = 2`, `depth[7] = 3`. Pick `u = 6` (shallower).
- Range query on chain A: `pos[6] = 2`, `pos[7] = 3`. Sum `flat[2..3]`. Adds `weights[6] + weights[7]`.

Result: `weights[6] + weights[7] + weights[8]`. ✓ The three nodes on the 7-to-8 path (LCA = 6).

Two range queries; one light-edge climb. **O(log² n)** per path query.

### Deep-dive 3 — When HLD overkills the problem

HLD is gorgeous but heavy. Several common path-query problems have lighter-weight solutions that you should reach for first:

**Static path sum on a weighted tree (no updates):** precompute `dist[v]` = sum from root to `v`. Then `sum(u, v) = dist[u] + dist[v] - 2 · dist[lca(u, v)]`. LCA via binary lifting is O(log n), no seg tree needed.

**Subtree queries:** Euler tour flattens each subtree to a contiguous range. Then it's just a 1D seg tree, no HLD.

**Tree distance queries:** binary lifting gives LCA in O(log n) and distance in O(log n) — no need for HLD's machinery.

**Path queries on a tree that's actually a path (n-node line graph):** HLD's chain is the whole graph. Just use a segment tree directly.

**LC 2421 (Number of Good Paths):** the official solution is **DSU sorted by node value** in O(n α(n)) — much shorter and faster than HLD's O(n log² n).

**The HLD discriminator:** updates AND path-query AND the operation isn't trivially decomposable (sum/dist) AND the tree is large. If any of those is missing, prefer a lighter tool.

---

## 🐛 Common bugs

1. **Forgetting heavy-first in `_dfs_decompose`.** If you decompose any-child-first, heavy-chain nodes won't sit contiguously, breaking the range-query optimisation.
2. **Wrong direction in path query.** Always climb the side with the **deeper chain head**. Reversing the order breaks correctness — the climb may overshoot the LCA.
3. **Off-by-one on the final segment.** The shared-chain query is `seg.range_sum(pos[u], pos[v])` where `u` is the *shallower* of the two — easy to flip.
4. **Edge-weighted HLD without skipping the LCA's slot.** Each node's slot represents the edge to its parent; the LCA's slot represents an edge *not on the path*. Use `pos[u] + 1` instead of `pos[u]` in the final query for edge-weighted variants.
5. **Class-level `_dfs_pos` static counter.** Convenient but bites if you build multiple HLDs in the same process. Use an instance attribute or a closure.
6. **Recursion depth on long paths.** Python's default recursion limit is ~1000. For a path-shaped tree with `n = 10^5` you'll blow the stack — bump `sys.setrecursionlimit(...)` or convert to iterative DFS.
7. **Lazy-propagation interaction.** Range update + range query over paths needs the underlying seg tree to support lazy. Vanilla seg tree breaks for HLD path-add.
8. **LCA returned wrong sign.** When using HLD purely for LCA: after climbing until same chain, the **shallower** of the two is the LCA — not always `u`, depends on which side you climbed last.

---

## 🗣️ Interviewer phrasings to recognize

- "**Sum / min / max along the path** between two nodes." → HLD with the corresponding seg tree.
- "**Update a node** and **query a path** mixed online." → HLD's bread and butter.
- "**Distance** between two nodes" with edge updates — HLD with edge weights.
- "**LCA** with weighted edges" — HLD gives both LCA and the path aggregate in one pass.
- "Tree where queries are on **subtrees**, not paths." → not HLD; Euler tour + seg tree.
- "Path query with **DSU-like** structure" — sometimes DSU-on-tree (small-to-large) replaces HLD. LC 2421 is the textbook example.

---

## 🧭 Connections to other patterns

- **[Segment Trees](03-segment-trees.md)** — HLD's underlying data structure. The chain-flatten makes the tree look 1D so seg trees apply.
- **[Tree DFS](../04-patterns/08-tree-dfs.md)** — HLD's two DFSes (size + decompose) are textbook tree DFSes; the cleverness is the *order* of recursion.
- **[Union-Find / DSU](02-union-find.md)** — for problems involving "merge subtrees as values rise," DSU-on-tree often replaces HLD with smaller constants.
- **Binary Lifting (LCA)** — alternative for pure LCA queries. O(n log n) preprocessing, O(log n) per query, no path-aggregate machinery.
- **Euler Tour** — flattens a tree for *subtree* queries (range = contiguous Euler-tour interval). HLD flattens for *path* queries; the two flatten differently for different question types.

---

## ✅ Self-check — 8 questions

??? question "1. Why are there at most log n light edges on any root-to-leaf path?"
    Each light-edge step climbs from a child whose subtree is *not* the heaviest. The parent's subtree contains the child plus the heaviest sibling, so the parent's subtree is at least twice the child's. From a leaf (size 1) to the root (size n), at most log₂(n) doublings happen.

??? question "2. Why does HLD lay heavy chains contiguously in the flat array?"
    The decompose DFS recurses into the heavy child *first*, then the light children. Heavy-chain nodes get consecutive positions, so a "climb up a heavy chain" maps to a contiguous range query.

??? question "3. What's the per-operation cost of HLD-with-segment-tree, and where does each log come from?"
    O(log² n). One log from the path crossing O(log n) chains; another log from each chain segment being a O(log n) seg-tree range query.

??? question "4. How do you adapt HLD for edge weights instead of node weights?"
    Assign each edge to the **deeper endpoint**'s slot in the flat array. Path queries proceed identically until the final shared-chain segment, where you skip the LCA's slot (`pos[u] + 1` instead of `pos[u]`) because that slot represents an edge not on the path.

??? question "5. When is HLD overkill?"
    Subtree queries → Euler tour. Static path sums → distance via LCA. Pure LCA → binary lifting. Tree-as-path → segment tree directly. If updates aren't part of the problem, HLD is rarely the cleanest choice.

??? question "6. How does HLD give you LCA for free?"
    During the chain-climb in `path_query`, when both nodes finally land on the same chain, the **shallower** of the two *is* the LCA. No additional preprocessing needed beyond the HLD structure.

??? question "7. Can HLD support range updates along a path?"
    Yes — but the underlying seg tree must support lazy propagation. The chain-climb framework is the same; each contiguous chain segment becomes a lazy range update instead of a range query.

??? question "8. What's DSU-on-tree (small-to-large) and when does it replace HLD?"
    DSU-on-tree merges subtree information by recursing into all children, keeping only the heaviest child's data and re-adding the others. Each node is added O(log n) times across all merges — O(n log n) total. Often shorter than HLD for offline subtree-property problems where you don't need point updates after build.

---

> **Up next in Advanced:** Mo's Algorithm — offline range queries reordered by √n-bucket to amortise to O((n + q) √n).
