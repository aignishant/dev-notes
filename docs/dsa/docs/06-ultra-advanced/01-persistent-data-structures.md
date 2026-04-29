# Persistent Data Structures

> Data structures where **every modification returns a new version** without mutating the old one — and yet each modification still costs only `O(log n)` time and memory by **sharing all the unchanged subtree** with the previous version. The trick: **path-copying.** Clone the root-to-modified-leaf spine, point the clone's untouched children at the *old* nodes. Now both old and new versions are valid roots; navigating from each gives you the structure as it was at that version. Net: **kth-element-as-of-version-v in `O(log n)`**, with `O(log n)` extra memory per version.

<span class="phase-status phase-done">Phase 7 — Ultra-Advanced</span>

---

## 📖 What are persistent data structures?

A data structure is **persistent** if old versions remain accessible after modifications. Three flavors of "persistent":

- **Partial persistence** — old versions are read-only; only the latest can be modified.
- **Full persistence** — any version can be modified, producing a new branching version.
- **Confluent persistence** — versions can be merged (very rare in interview practice).

The standard technique is **path-copying**: when you modify a node, clone it; recurse to clone the path back up to the root. The clones form a *new spine*; everything **off** the spine is shared with the previous version. So the new version uses only `O(log n)` extra nodes.

The mental model: imagine a forest of root pointers, one per version. Each root is the entry point into that version's view of the data. Many of the deep subtrees are **physically the same memory** — they were untouched by recent modifications. Only the spine differs.

This works for any tree-shaped data structure: arrays via balanced trees, segment trees, treaps, tries, hash array mapped tries (HAMTs — used by Clojure's immutable maps).

!!! tip "The signal — when to reach for persistence"
    Reach for it when:

    - You need to **answer queries about historical state** (e.g., "what was `arr[i]` after the kth update?").
    - You need **versioned undo / redo** with O(1) version switching.
    - You need to **process queries offline in a different order** but need each query's "view" of state.
    - You're building a **functional / immutable** language's collections (Clojure, Scala, Haskell).
    - You're solving **kth smallest in subarray `[l, r]`** — the textbook persistent segment tree problem.

    Don't reach for it when:

    - You only need the latest state — non-persistent is faster (no clone overhead).
    - Memory is critically tight — even O(log n) per version multiplied by q versions is `O(q log n)` total.
    - The problem allows offline reordering (Mo's, sqrt decomposition) — those are usually simpler.

---

## 🧩 The four flavors

### Flavor 1: Persistent segment tree (the workhorse)

The single most useful persistent structure in competitive programming. A standard recursive segment tree, but every modification returns a **new root**, sharing all unchanged subtrees with the old root.

```python
class Node:
    __slots__ = ("val", "left", "right")
    def __init__(self, val: int = 0, left: "Node | None" = None, right: "Node | None" = None) -> None:
        self.val = val
        self.left = left
        self.right = right

def build(l: int, r: int) -> Node:
    if l == r:
        return Node(0)
    mid = (l + r) // 2
    return Node(0, build(l, mid), build(mid + 1, r))

def update(prev: Node, l: int, r: int, idx: int, delta: int) -> Node:
    """Returns a NEW root reflecting `prev` with arr[idx] += delta."""
    if l == r:
        return Node(prev.val + delta)                             # leaf clone
    mid = (l + r) // 2
    if idx <= mid:
        new_left = update(prev.left, l, mid, idx, delta)
        return Node(prev.val + delta, new_left, prev.right)       # share right subtree
    else:
        new_right = update(prev.right, mid + 1, r, idx, delta)
        return Node(prev.val + delta, prev.left, new_right)       # share left subtree

def query(node: Node, l: int, r: int, ql: int, qr: int) -> int:
    if qr < l or r < ql: return 0
    if ql <= l and r <= qr: return node.val
    mid = (l + r) // 2
    return query(node.left, l, mid, ql, qr) + query(node.right, mid + 1, r, ql, qr)
```

After `n` updates, you have `n` roots in `versions[0..n-1]`. Each `versions[v]` *is* the segment tree as of version `v`. Total memory: `O(n log n)`.

### Flavor 2: Kth smallest in subarray (the killer application)

Given a static array and many queries `(l, r, k)`: "kth smallest in `arr[l..r]`." Build a persistent segment tree **on the value domain** (after coord compression). `versions[i]` = segment tree where every position's value count up to `arr[i]` is reflected. To answer `(l, r, k)`: descend `versions[r]` minus `versions[l-1]` simultaneously, choosing left or right based on the count diff.

```python
def kth_in_range(versions: list[Node], l: int, r: int, k: int, lo: int, hi: int) -> int:
    """Returns the kth smallest value in arr[l..r] (1-indexed k)."""
    u, v = versions[l - 1], versions[r]                           # versions[r] - versions[l-1]
    while lo < hi:
        left_count = v.left.val - u.left.val                      # how many values fall in left half
        mid = (lo + hi) // 2
        if k <= left_count:
            u, v = u.left, v.left
            hi = mid
        else:
            k -= left_count
            u, v = u.right, v.right
            lo = mid + 1
    return lo                                                     # the value (or its compressed index)
```

`O(log V)` per query where `V` is the compressed value domain. **No segment tree on the original array needed** — the persistence does the heavy lifting.

### Flavor 3: Persistent array (logarithmic-time clone)

A persistent array via a balanced binary tree of leaves. `set(i, x)` returns a new array root sharing everything except the spine to leaf `i`. Used in functional languages (Clojure's vectors are HAMTs with branching factor 32).

```python
class ArrNode:
    __slots__ = ("val", "left", "right")
    def __init__(self, val: int = 0, left=None, right=None) -> None:
        self.val, self.left, self.right = val, left, right

def parr_build(arr: list[int], l: int, r: int) -> ArrNode:
    if l == r: return ArrNode(arr[l])
    m = (l + r) // 2
    return ArrNode(0, parr_build(arr, l, m), parr_build(arr, m + 1, r))

def parr_set(node: ArrNode, l: int, r: int, idx: int, val: int) -> ArrNode:
    if l == r: return ArrNode(val)
    m = (l + r) // 2
    if idx <= m:
        return ArrNode(0, parr_set(node.left, l, m, idx, val), node.right)
    return ArrNode(0, node.left, parr_set(node.right, m + 1, r, idx, val))

def parr_get(node: ArrNode, l: int, r: int, idx: int) -> int:
    if l == r: return node.val
    m = (l + r) // 2
    return parr_get(node.left, l, m, idx) if idx <= m else parr_get(node.right, m + 1, r, idx)
```

Get/set are both `O(log n)`. With branching factor 32 (HAMT-style), `log_32 n` is ~4 for n = 10^6 — almost O(1) in practice.

### Flavor 4: Persistent trie (versioned set of keys)

A trie where insert returns a new root sharing untouched subtrees. Useful for problems like "max XOR of `arr[i]` with any value inserted in `arr[..j]`" — each version is a trie of values inserted up to index `j`, and you walk the trie greedily to maximise XOR with `arr[i]`.

```python
class TrieNode:
    __slots__ = ("count", "left", "right")
    def __init__(self, count: int = 0, left=None, right=None) -> None:
        self.count, self.left, self.right = count, left, right

def ptrie_insert(prev: TrieNode | None, value: int, bit: int = 30) -> TrieNode:
    new = TrieNode(
        count=(prev.count if prev else 0) + 1,
        left=prev.left if prev else None,
        right=prev.right if prev else None,
    )
    if bit < 0: return new
    if (value >> bit) & 1:
        new.right = ptrie_insert(prev.right if prev else None, value, bit - 1)
    else:
        new.left = ptrie_insert(prev.left if prev else None, value, bit - 1)
    return new

def max_xor_in_window(versions: list[TrieNode], l: int, r: int, value: int, bit: int = 30) -> int:
    """Max XOR of `value` with any insertion between versions[l-1] and versions[r]."""
    u, v = versions[l - 1], versions[r]
    result = 0
    for b in range(bit, -1, -1):
        want = 1 - ((value >> b) & 1)                             # we want the opposite bit
        u_child = (u.right if u else None) if want else (u.left if u else None)
        v_child = v.right if want else v.left
        cnt_u = u_child.count if u_child else 0
        cnt_v = v_child.count if v_child else 0
        if cnt_v - cnt_u > 0:
            result |= (1 << b)
            u, v = u_child, v_child
        else:
            other = 1 - want
            u = (u.right if u else None) if other else (u.left if u else None)
            v = v.right if other else v.left
    return result
```

The same trick as kth smallest: subtract counts in two versions to see how many fit in a sub-range.

---

## 🔍 Sub-pattern at-a-glance

| # | Variant                       | Killer use case                                     | Cost per op            |
|---|-------------------------------|-----------------------------------------------------|------------------------|
| 1 | Persistent segment tree       | Kth smallest in `[l, r]`, count-in-range queries    | O(log V) per query     |
| 2 | Persistent array (HAMT)       | Functional-language collections, immutable arrays   | O(log_b n)             |
| 3 | Persistent trie (binary)      | Max-XOR / bit queries over a window of inserts      | O(B) where B = bits    |
| 4 | Persistent treap              | Versioned ordered sets with split/merge             | O(log n) per op        |
| 5 | Path-copying for any tree     | General persistence template                        | O(depth) per op        |
| 6 | Fat-node / fat-edge           | Theoretical full persistence with O(1) overhead     | Rarely used in practice|

---

## 📚 20 problems where persistent structures shine

| #  | Source         | Problem                                            | Difficulty | Key insight                                                       |
|----|----------------|----------------------------------------------------|------------|-------------------------------------------------------------------|
| 1  | SPOJ MKTHNUM   | Kth smallest in `arr[l..r]`                        | Hard       | Textbook persistent segment tree on value domain.                 |
| 2  | LC 1742        | Maximum number of balls in a box                   | Easy       | Trivial — just shows freq counting; persistence is overkill here. |
| 3  | CF 813E        | Army Creation (count occurrences in window)        | Hard       | Persistent seg tree of "previous occurrence index ≤ l".           |
| 4  | LC 327         | Count of range sum                                 | Hard       | Persistent BIT or merge-sort-with-counting wins.                  |
| 5  | SPOJ COT       | Count distinct on tree path (Sack of Tricks)       | Hard       | Persistent seg tree on Euler tour + LCA combine.                  |
| 6  | CF 484E        | Sign on Fence (max contiguous ≥ k in `[l, r]`)     | Hard       | Persistent seg tree of "1 if value ≥ threshold" sorted by value.  |
| 7  | LC 421         | Maximum XOR of two numbers in array                | Medium     | Plain trie suffices; persistent variant handles range version.    |
| 8  | CF 100632F     | Persistent set with rollback                       | Hard       | Persistent treap by version index.                                |
| 9  | UVa 12538      | Version-based text editor                          | Medium     | Persistent rope (path-copying treap or implicit segment tree).    |
| 10 | CF 707D        | Persistent bookcase (matrix toggles)               | Hard       | Persistent segment tree of rows; row toggle = lazy flag.          |
| 11 | LC 715         | Range Module                                       | Hard       | Could use persistent treap if we needed undo across calls.        |
| 12 | CSES 2358      | Range distinct values                              | Hard       | Persistent seg tree of "next occurrence" indicators.              |
| 13 | CF 893F        | Subtree min on a versioned tree                    | Hard       | Persistent seg tree on Euler tour + path-copy on insertion.       |
| 14 | SPOJ DISQUERY  | Distance between two nodes (offline)               | Medium     | Persistent LCA via binary lifting on snapshots.                   |
| 15 | CF 484E        | Same as #6 — repeat to internalize the pattern     | Hard       | Threshold-binary-search inside the persistent tree.               |
| 16 | CF 464E        | The Classic Problem (graph with 2^L weights)       | Very Hard  | Persistent seg tree of bits as Dijkstra's priority key.           |
| 17 | LC 295         | Find median from data stream                       | Hard       | Two heaps wins; persistent BIT also solves it with version stamps.|
| 18 | CSES 2206      | Counting paths (versioned tree updates)            | Hard       | Persistent BIT on Euler tour.                                     |
| 19 | CF 372C        | Watching Fireworks (offline)                       | Hard       | Persistent monotonic deque per version.                           |
| 20 | LC 731         | My Calendar II (overlapping intervals)             | Medium     | Persistent interval tree allows historical "what was my schedule?"|

---

## 🔬 Deep-dive 1 — Persistent segment tree memory analysis

The classic worry: "doesn't path-copying blow up to O(n²) memory?"

**Claim:** after `n` updates on a segment tree of size `n`, total memory is `O(n log n)`.

**Proof:** the initial `build` allocates `2n - 1` nodes (the full tree). Each `update` clones exactly the path from root to a leaf — that's `⌈log₂ n⌉ + 1 ≈ log₂ n` new nodes. After `n` updates, total: `2n - 1 + n · log₂ n ≈ n log₂ n`.

For `n = 10⁵` and `log₂ n ≈ 17`, that's ~1.7 million nodes. Each node has 3 fields (val, left, right). With Python's overhead per object, that's ~150 bytes/node → ~250 MB. **Memory is the real constraint of persistent structures in Python.**

In C++, with packed structs (24 bytes/node), the same is ~40 MB — comfortably within typical 256 MB limits.

??? tip "What about persistent updates that touch the *same* leaf many times?"
    Each clone still adds a fresh `log n` spine; the old spine for that leaf in the previous version is still there. Memory grows linearly in the number of operations, not the number of distinct leaves touched.

??? tip "Garbage collection of old versions?"
    If you no longer hold a reference to an old root, all nodes uniquely owned by that version's spine are GC'd (in Python). Shared subtrees stay alive as long as *some* version still references them. In contest code, you usually keep all versions, so memory grows monotonically.

---

## 🔬 Deep-dive 2 — Kth smallest in `arr[l..r]` step-by-step

**The setup.** Given `arr = [1, 5, 2, 6, 3, 7, 4]` (n=7), preprocess so we can answer "kth smallest in `arr[l..r]`" in `O(log V)` per query.

**Step 1 — coord compress** (already sorted distinct: `[1,2,3,4,5,6,7]`, indexes `0..6`).

**Step 2 — build versions.** `versions[0]` = empty seg tree on value indexes `[0..6]`. For each `i = 1..n`, `versions[i] = update(versions[i-1], 0, 6, compressed[arr[i-1]], +1)` — increment the count at that value.

After all 7 updates, `versions[i]` is a segment tree where leaf `j` holds the count of value-index `j` in `arr[..i-1]`.

**Step 3 — query.** For query `(l=2, r=6, k=3)` ("3rd smallest in `arr[2..6] = [2,6,3,7,4]`"):

Walk `versions[6]` and `versions[1]` simultaneously. At each internal node, `left_count = v.left.val - u.left.val` = count of values in left half within `arr[2..6]`.

- Root covers `[0..6]`. Left = `[0..3]` (values 1,2,3,4). v.left.val - u.left.val = (count of values 1..4 in arr[..6]) - (count of values 1..4 in arr[..1]) = 4 - 1 = 3. Since k=3 ≤ 3, go left.
- Now at `[0..3]`. Left = `[0..1]` (values 1,2). diff = 2 - 1 = 1. k=3 > 1 → go right with k = 3 - 1 = 2.
- Now at `[2..3]` (values 3,4). Left = `[2..2]` (value 3). diff = 1 - 0 = 1. k=2 > 1 → go right with k = 1.
- Now at `[3..3]` (value 4). Leaf. Answer: value-index 3 = original value `4`.

Sanity check: `arr[2..6]` sorted = `[2, 3, 4, 6, 7]`. 3rd smallest = `4`. ✅

The whole query touched `log V = 3` levels, doing O(1) work each. **No "redo the segment tree per query" — the persistence makes the difference free.**

---

## 🔬 Deep-dive 3 — Why persistent ≠ "just keep all versions in a list"

Naïve "keep the entire structure per version" is O(n) per version → O(n²) total. The whole point of persistence is **structural sharing**: we don't keep n copies; we keep n roots that share everything they can.

The deep insight: a balanced tree's update touches only `O(log n)` nodes. So if we **clone exactly those `O(log n)` nodes** and reuse pointers to the rest, the new version is "complete" in the sense that navigating from its root gives the correct view, **without copying any subtree off the modified path**.

This is **only possible** because the data structure is **tree-shaped**. For a doubly-linked list, every node points to its neighbours, so changing one node forces changing pointers in adjacent nodes — and that propagates all the way through. For a tree, the parent points to the child but not vice-versa, so cloning the parent doesn't force cloning the sibling.

??? tip "What about persistent hash tables?"
    Hash tables aren't tree-shaped, but **HAMTs (Hash Array Mapped Tries)** are: hash the key, treat the hash as a path through a 32-ary trie. Then path-copying gives persistence. Clojure's `PersistentHashMap` is exactly this — and `assoc` runs in `O(log_32 n) ≈ O(1)` for practical sizes.

??? tip "Can we do persistent arrays without trees?"
    **Confluent persistence with O(1) overhead** is possible via the *fat-node* technique: each modification appends to a per-node version log, and lookup binary-searches the log. Theoretically beautiful, practically rare — the constants are big and the code is fragile. Trees are the lingua franca of persistence.

The big takeaway: **persistence demands a tree backbone**. If your structure has cycles or back-edges, persistence is much harder.

---

## 🐛 Common bugs

1. **Mutating `prev` in `update`.** The whole point is to leave `prev` unchanged. Any `prev.val += ...` instead of returning a new node breaks all earlier versions.
2. **Sharing children incorrectly when both subtrees changed.** Each `update` only descends into ONE side; the other side's pointer is reused **as-is**. Clone exactly the path you walked.
3. **Coordinate compression off-by-one.** When indexing the value domain, `bisect_left` on the sorted distinct array gives 0-indexed positions; the segment tree is built on `[0, V-1]`. Mixing 1-indexed and 0-indexed conventions silently corrupts results.
4. **Forgetting that `versions[r] - versions[l-1]` requires l ≥ 1.** For l=0, you need a "version -1" which is just the initial empty root.
5. **Building a recursive segment tree in Python with deep recursion.** For n = 10⁵, `build` recurses ~17 deep — fine. For n = 10⁶, ~20 deep — also fine. But avoid the **iterative** segtree for persistence: iterative form needs different indexing per version, breaking sharing.
6. **Memory blowup from too many versions.** Each version costs `O(log n)` nodes. For 10⁶ versions and n = 10⁵, that's 10⁶ · 17 = 17M nodes. In Python, easily 1.5 GB. Either compress versions or move to a non-persistent online structure.
7. **Persistent trie max-XOR walking the wrong child.** Greedy max-XOR wants the **opposite** bit; check `cnt_v - cnt_u > 0` for the opposite child first, fall back to the same-bit child.
8. **Not freeing intermediate `versions[]` when only the latest matters.** If you don't actually need all versions, persistence is wasteful — just mutate.

---

## 🗣️ Interviewer phrasings to recognize

- "**Kth smallest** in `arr[l..r]` for q queries" → persistent segment tree.
- "**Count of values in range** `[a, b]` within `arr[l..r]`" → persistent BIT or persistent seg tree.
- "After applying the **first k updates** to the array, what's the value of `arr[i]`?" → persistent array.
- "**Versioned database** — each transaction sees a snapshot" → persistence is the data-structures-textbook answer.
- "**Functional / immutable** language collections" → HAMT, persistent vector, persistent map.
- "Undo / redo with **O(1) version switching**" → keep all roots, swap pointers.

---

## 🧭 Connections to other patterns

- **[Segment Trees](../05-advanced/03-segment-trees.md)** — the underlying structure most often made persistent.
- **[Fenwick Tree (BIT)](../05-advanced/04-fenwick-bit.md)** — also persistable, though the bit-trick form is awkward; the explicit-tree form is cleaner.
- **[Treaps & Skip Lists](../05-advanced/08-treaps-skip-lists.md)** — treaps go persistent very naturally via path-copying.
- **[Tries](../05-advanced/01-tries.md)** — persistent binary tries handle XOR-in-window queries.
- **[Mo's Algorithm](../05-advanced/07-mo-algorithm.md)** — the alternative when offline reordering is OK and persistence is overkill. Mo's loses for true online queries.
- **Functional programming** — Clojure, Scala, Haskell, Elm all use persistent collections by default; understanding persistence makes you a better functional programmer.

---

## ✅ Self-check — 8 questions

??? question "1. Why does path-copying give O(log n) memory per modification, not O(n)?"
    A modification on a balanced tree only touches the root-to-leaf path — `O(log n)` nodes. Path-copying clones exactly those nodes; everything off the path is reused via shared pointers. Total new memory per update: O(log n).

??? question "2. How does kth-smallest-in-range work with persistent segment trees?"
    Build a persistent seg tree on the value domain. `versions[i]` reflects values inserted up to position i. To answer (l, r, k): walk `versions[r]` and `versions[l-1]` together; at each internal node, `left_count = v.left - u.left.val` tells how many values fall in the left half. Descend left if k ≤ left_count, else descend right with k -= left_count. O(log V) per query.

??? question "3. Why don't persistent linked lists give O(log n) per update?"
    Linked lists aren't tree-shaped — modifying a node requires updating its predecessor's `next` pointer, which requires updating *its* predecessor, all the way to the head. The 'spine' you must clone is the entire prefix, giving O(n) per update.

??? question "4. What's structural sharing, and why does it require immutability?"
    Two structures share a subtree by holding the same physical pointer to it. If either could mutate the shared subtree, they'd corrupt each other's view. Immutability ensures sharing is safe — once a node exists, it never changes, so any number of versions can point to it.

??? question "5. When does persistence beat Mo's algorithm for offline range queries?"
    Mo's wins when the operation has a cheap incremental add/remove and queries can be batched. Persistence wins when queries arrive **online** (must be answered immediately) or when you need to "look back at version v" mid-stream. Persistence also wins when the operation has no clean add/remove but does have a clean `apply / unapply` pair.

??? question "6. How does HAMT achieve effectively-O(1) persistent map operations?"
    Hash Array Mapped Trie: hash the key, treat the hash as a path through a 32-ary trie (5 bits per level). For practical sizes (n ≤ 10⁹), depth is ≤ 6 — effectively constant. Clojure's PersistentHashMap is HAMT.

??? question "7. What's the memory cost of n updates on an n-element persistent segment tree?"
    Initial build: 2n - 1 nodes. Each update: log₂ n new nodes. After n updates: ≈ n log n total. For n = 10⁵, log n ≈ 17 → ~1.7M nodes. Python's per-object overhead makes this expensive; C++ packed structs are much more compact.

??? question "8. Can persistent structures support range updates (not just point updates)?"
    Yes, with **persistent lazy propagation**. Each lazy push must clone the affected children (since the lazy bit was 'attached' to a previous version's node and we shouldn't mutate that). It's noticeably harder than vanilla persistence — but doable, and used in problems like CF 484E.

---

> **Up next in Ultra-Advanced:** Max-Flow / Min-Cut — Dinic's algorithm in O(V²E), Ford-Fulkerson, the min-cut/max-flow duality, and bipartite matching as max-flow on a unit-capacity graph.
