# Treaps & Skip Lists

> Two **randomised** balanced data structures that you can write **from scratch in under 100 lines** — without ever touching the rotation gymnastics of red-black or AVL trees. Both give you `O(log n)` expected ordered-set operations: insert, delete, lookup, kth-element, range-split. Treaps add **split / merge** as primitive operations, which unlocks order-statistics, range-flip, and persistent variants. Skip lists add **probabilistic levels** that map cleanly to lock-free concurrent variants. Together: the two practical "I need a balanced BST and I want to write it myself" answers.

<span class="phase-status phase-done">Phase 6 — Advanced topic 8 of 8</span>

---

## 📖 What are treaps and skip lists?

A **treap** is a binary search tree where every node carries two keys: the **key** (BST-ordered) and a **priority** (heap-ordered, randomly chosen at insert time). The tree is simultaneously a BST on keys *and* a max-heap on priorities. Because the priorities are random, the tree's expected height is `O(log n)`.

A **skip list** is a sorted linked list with **multiple express lanes** stacked on top — each higher lane skips over more elements. A node's height is sampled geometrically at insert time (50% chance of being one level taller). Searching descends from the top lane, jumping forward as far as possible at each level. Expected height: `O(log n)`. Expected search cost: `O(log n)`.

Both are **simpler to implement** than AVL or red-black trees because the balancing is **probabilistic** — no rotations, no recolouring. The price: worst case is `O(n)` (with vanishingly small probability for random priorities / heights).

The mental model: instead of *forcing* balance by tracking heights and rotating, **roll a die at insert time** so the structure is balanced *in expectation*. The randomness is your friend — an adversary can't construct a worst-case input unless they see your random seed.

!!! tip "The signal — when to reach for treaps or skip lists"
    Reach for them when:

    - You need a **balanced BST** and don't want to write 400 lines of red-black code.
    - You need **order-statistics** (kth element, rank of x) and `SortedList` isn't available.
    - You need **range operations** like split-by-key, merge two trees, reverse a range — treap's split/merge handles these in `O(log n)`.
    - You're building a **persistent / immutable** ordered set — treaps clone naturally with path-copying.
    - You're building a **concurrent / lock-free** ordered set — skip lists are the classic answer (Java's `ConcurrentSkipListMap`).

    Don't reach for them when:

    - Python's `sortedcontainers.SortedList` exists and you can use it — it's a B-tree-of-arrays and beats both in practice.
    - You only need a hash set / hash map — those are `O(1)` expected, both are `O(log n)`.
    - You're in an interview where the only point is "do you know how to balance a BST" — you may need AVL or red-black.

---

## 🧩 The four flavors

### Flavor 1: Treap with insert / delete / search

The standard form. Each node is `(key, priority, left, right)`. Insert: BST-insert by key, then rotate up while the new node's priority exceeds its parent's. Delete: rotate the node downward (towards the lower-priority child) until it's a leaf, then snip.

```python
import random

class TreapNode:
    __slots__ = ("key", "priority", "left", "right")
    def __init__(self, key: int) -> None:
        self.key = key
        self.priority = random.random()                           # uniform in [0, 1)
        self.left: TreapNode | None = None
        self.right: TreapNode | None = None

def rotate_right(p: TreapNode) -> TreapNode:                      # left child becomes parent
    l = p.left
    p.left, l.right = l.right, p
    return l

def rotate_left(p: TreapNode) -> TreapNode:                       # right child becomes parent
    r = p.right
    p.right, r.left = r.left, p
    return r

def insert(root: TreapNode | None, key: int) -> TreapNode:
    if root is None:
        return TreapNode(key)
    if key < root.key:
        root.left = insert(root.left, key)
        if root.left.priority > root.priority:                    # heap violation → fix it
            root = rotate_right(root)
    elif key > root.key:
        root.right = insert(root.right, key)
        if root.right.priority > root.priority:
            root = rotate_left(root)
    return root                                                   # duplicate keys ignored

def delete(root: TreapNode | None, key: int) -> TreapNode | None:
    if root is None:
        return None
    if key < root.key:
        root.left = delete(root.left, key)
    elif key > root.key:
        root.right = delete(root.right, key)
    else:                                                         # found — rotate down
        if root.left is None: return root.right
        if root.right is None: return root.left
        if root.left.priority > root.right.priority:
            root = rotate_right(root)
            root.right = delete(root.right, key)
        else:
            root = rotate_left(root)
            root.left = delete(root.left, key)
    return root
```

### Flavor 2: Implicit treap (split / merge — the killer feature)

Instead of explicit keys, an **implicit treap** uses subtree size as the implicit "key" — the node's position in an in-order traversal. Then `split(root, k)` divides the tree into the first `k` and the rest in `O(log n)`; `merge(left, right)` glues two treaps where every key in `left < every key in right`. With these two primitives, you get **range operations**: reverse, sum, min, lazy add — all by splitting out the range, operating, and merging back.

```python
class ImpTreap:
    __slots__ = ("priority", "value", "size", "left", "right")
    def __init__(self, value: int) -> None:
        self.priority = random.random()
        self.value = value
        self.size = 1
        self.left: ImpTreap | None = None
        self.right: ImpTreap | None = None

def _size(t: ImpTreap | None) -> int:
    return t.size if t else 0

def _update(t: ImpTreap) -> None:
    t.size = 1 + _size(t.left) + _size(t.right)

def merge(a: ImpTreap | None, b: ImpTreap | None) -> ImpTreap | None:
    if not a or not b: return a or b
    if a.priority > b.priority:
        a.right = merge(a.right, b)
        _update(a)
        return a
    else:
        b.left = merge(a, b.left)
        _update(b)
        return b

def split(t: ImpTreap | None, k: int) -> tuple[ImpTreap | None, ImpTreap | None]:
    """Split into first k and the rest."""
    if not t: return (None, None)
    if _size(t.left) >= k:
        left, t.left = split(t.left, k)
        _update(t)
        return (left, t)
    else:
        t.right, right = split(t.right, k - _size(t.left) - 1)
        _update(t)
        return (t, right)

# Usage: insert v at index i  →  l, r = split(root, i); root = merge(merge(l, ImpTreap(v)), r)
# Reverse range [l, r)        →  a, bc = split(root, l); b, c = split(bc, r - l); apply lazy reverse to b; root = merge(merge(a, b), c)
```

This is **the** reason competitive programmers reach for treaps over AVL/RB: split/merge make "range surgery" trivial.

### Flavor 3: Skip list (probabilistic levels)

Each node is sampled to a height; a node of height `h` participates in lanes `0..h-1`. Search descends from the top lane, advancing forward as long as the next node's key < target.

```python
import random

MAX_LEVEL = 16                                                    # supports ~2^16 elements

class SkipNode:
    __slots__ = ("key", "next")
    def __init__(self, key: int, level: int) -> None:
        self.key = key
        self.next: list[SkipNode | None] = [None] * level         # one pointer per level

class SkipList:
    def __init__(self) -> None:
        self.head = SkipNode(float("-inf"), MAX_LEVEL)            # sentinel at every level
        self.level = 1                                            # current top occupied level

    def _random_level(self) -> int:
        lvl = 1
        while random.random() < 0.5 and lvl < MAX_LEVEL:          # geometric distribution, p=0.5
            lvl += 1
        return lvl

    def search(self, key: int) -> bool:
        cur = self.head
        for i in range(self.level - 1, -1, -1):
            while cur.next[i] and cur.next[i].key < key:
                cur = cur.next[i]
        cur = cur.next[0]
        return cur is not None and cur.key == key

    def insert(self, key: int) -> None:
        update = [self.head] * MAX_LEVEL                          # predecessor at each level
        cur = self.head
        for i in range(self.level - 1, -1, -1):
            while cur.next[i] and cur.next[i].key < key:
                cur = cur.next[i]
            update[i] = cur

        lvl = self._random_level()
        if lvl > self.level:
            self.level = lvl
        node = SkipNode(key, lvl)
        for i in range(lvl):
            node.next[i] = update[i].next[i]
            update[i].next[i] = node

    def delete(self, key: int) -> bool:
        update = [self.head] * MAX_LEVEL
        cur = self.head
        for i in range(self.level - 1, -1, -1):
            while cur.next[i] and cur.next[i].key < key:
                cur = cur.next[i]
            update[i] = cur
        cur = cur.next[0]
        if cur is None or cur.key != key:
            return False
        for i in range(self.level):
            if update[i].next[i] is cur:
                update[i].next[i] = cur.next[i]
        while self.level > 1 and self.head.next[self.level - 1] is None:
            self.level -= 1
        return True
```

The geometric height distribution gives expected height `log₂ n` and expected search cost `O(log n)`. The constant factor is roughly `2 log n` comparisons.

### Flavor 4: Persistent treap (path-copying for immutability)

Every modifying operation **clones the path from root to the modified node**, leaving the rest of the tree shared. The old root remains a valid version of the structure; the new root is the updated version. Each modification costs `O(log n)` time **and** `O(log n)` extra memory (the cloned spine).

```python
def persistent_insert(root: TreapNode | None, key: int) -> TreapNode:
    if root is None:
        return TreapNode(key)
    new = TreapNode(root.key)                                     # clone this node
    new.priority = root.priority
    new.left, new.right = root.left, root.right
    if key < root.key:
        new.left = persistent_insert(root.left, key)
        if new.left.priority > new.priority:
            new = rotate_right(new)
    elif key > root.key:
        new.right = persistent_insert(root.right, key)
        if new.right.priority > new.priority:
            new = rotate_left(new)
    return new
# `root` is unchanged — `new` is the next version. Keep both in a `versions: list[TreapNode]` array.
```

This is how persistent ordered sets / segment trees are built. The same technique applies to skip lists, but the multi-pointer per level makes it bulkier.

---

## 🔍 Sub-pattern at-a-glance

| # | Variant                         | Where it shines                                                | Cost                  |
|---|---------------------------------|----------------------------------------------------------------|-----------------------|
| 1 | Treap (key-ordered)             | Generic balanced BST — replacement for `set` / `map`           | O(log n) expected     |
| 2 | Implicit treap (split/merge)    | Range reverse, range insert, rope-like editor buffers          | O(log n) per op       |
| 3 | Skip list                       | Concurrent / lock-free ordered map; simpler than treap         | O(log n) expected     |
| 4 | Persistent treap                | Versioned ordered sets, immutable data structures              | O(log n) per version  |
| 5 | Cartesian tree                  | Treap of array values keyed by index — RMQ in O(n) build       | O(n) build, O(1) RMQ  |
| 6 | Indexed skip list               | Skip list with subtree counts at each level → kth-element      | O(log n)              |

---

## 📚 20 problems where a treap or skip list shines

| #  | Source         | Problem                                            | Difficulty | Key insight                                                      |
|----|----------------|----------------------------------------------------|------------|------------------------------------------------------------------|
| 1  | LC 1409        | Queries on a permutation with key                  | Medium     | Implicit treap of indices — split-and-front-prepend in O(log n). |
| 2  | LC 715         | Range Module                                       | Hard       | Treap of intervals; split/merge handles overlap naturally.       |
| 3  | LC 729         | My Calendar I                                      | Medium     | Sorted intervals; treap or skip list both work as `SortedList`.  |
| 4  | LC 855         | Exam Room                                          | Medium     | Treap by gap size + lookup by seat — two structures linked.      |
| 5  | LC 218         | The Skyline Problem                                | Hard       | Multiset of heights → treap; alternatives are heap-with-lazy.    |
| 6  | CF 702F        | T-shirts (sorted by price/quality)                 | Hard       | Implicit treap to delete-by-budget then walk in order.           |
| 7  | SPOJ ORDERSET  | Order-statistic set (insert/delete/kth/rank)       | Medium     | Textbook treap with subtree-size augmentation.                   |
| 8  | CF 13E         | Holes (interval-jump game)                         | Hard       | Treap with parent pointers for jump compression.                 |
| 9  | CF 899F        | Letters Removing                                   | Hard       | Implicit treap on positions; lazy delete via split.              |
| 10 | LC 327         | Count of range sum                                 | Hard       | BIT / merge-sort wins, but indexed skip list also solves it.     |
| 11 | LC 493         | Reverse pairs                                      | Hard       | Same — Fenwick is canonical, skip list-of-counts is alternative. |
| 12 | LC 1825        | Finding MK Average                                 | Hard       | Three SortedLists — under the hood: skip-list-or-treap forest.   |
| 13 | CF 455D        | Serega and Fun (cyclic shift on segment)           | Hard       | Implicit treap: `split, split, merge in different order`.        |
| 14 | LC 480         | Sliding window median                              | Hard       | Two heaps wins, but `SortedList` (skip-list-like) is one-liner.  |
| 15 | CF 1041F       | Ray in numeric maze                                | Hard       | Coordinate-compressed treap of active rays.                      |
| 16 | CF 70E         | Information Reform (cost graph)                    | Hard       | Persistent treap for "what was the min cost up through year y?"  |
| 17 | LC 715         | Range Module (revisit)                             | Hard       | Implicit treap of (start, end) pairs with merge-on-overlap.      |
| 18 | UVa 11512      | GATTACA (suffix DS)                                | Medium     | Cartesian tree on LCP array → RMQ → longest repeated substring.  |
| 19 | CF 366E        | Captains Mode (game tree DP + skiplist for kth)    | Hard       | Skip list to maintain sorted heroes by score with O(log) kth.    |
| 20 | LC 1622        | Fancy Sequence (lazy add/mul)                      | Hard       | Implicit treap with lazy `(a, b) → ax + b` propagation.          |

---

## 🔬 Deep-dive 1 — Why random priorities give expected `O(log n)` height

This is the question that *separates* treap users from treap *implementers*.

**Claim:** for a treap on `n` keys with priorities chosen uniformly at random, the expected depth of any node is `O(log n)`.

**Proof sketch (the elegant probabilistic argument):**

Fix two nodes `i` and `j` in the in-order sequence with `i < j`. Node `i` is an **ancestor** of node `j` if and only if `i` has the **maximum priority** among nodes `i, i+1, ..., j`. Why? Walk down from the root. The first node in `[i..j]` that we hit (in the BST descent for `j`) is whoever has the highest priority in that range — because the priorities form a heap. If that node is `i`, then `i` is an ancestor of `j`; otherwise, `i` and `j` get split into different subtrees by some node strictly between them, and `i` cannot be `j`'s ancestor.

So `Pr[i is ancestor of j] = 1 / (|j - i| + 1)` (each node in the range is equally likely to have the max priority).

**Depth of `j`** = number of ancestors of `j` = `Σ_{i ≠ j} Pr[i is ancestor of j]`.

`= Σ_{i=1}^{j-1} 1/(j - i + 1) + Σ_{i=j+1}^{n} 1/(i - j + 1)`

`≈ H_j + H_{n-j} ≤ 2 H_n ≈ 2 ln n ≈ 1.39 log₂ n`.

So **expected depth ≤ 1.39 log₂ n** for every node. The maximum depth is also `O(log n)` whp by a Chernoff bound.

??? tip "What if priorities collide (e.g., float underflow)?"
    For `n ≤ 10^7` and 53-bit IEEE doubles, collision probability is ~n²/2^54 ≈ 10⁻¹. To be safe, use `random.random()` (53-bit) or even `random.randrange(2**62)`. In contest practice, `random.random()` is plenty.

??? tip "Why doesn't an adversary just choose the inputs to break us?"
    The priorities are chosen *server-side* at insert time, not derived from the keys. The adversary controls keys, not priorities. Without seeing your random seed, the input order is irrelevant — the priorities determine the tree shape.

---

## 🔬 Deep-dive 2 — Implicit treap rope: insert, reverse, sum a substring in O(log n)

The killer application of implicit treaps is the **rope** — a string that supports:

- `insert(i, s)`: insert string `s` at position `i` — O(|s| log n)
- `delete(i, j)`: delete substring `s[i:j]` — O(log n)
- `reverse(i, j)`: reverse substring — O(log n)
- `sum(i, j)`: aggregate (e.g., sum of character codes) over a substring — O(log n)

The structure: each character is a node in an implicit treap. Position = in-order rank. Subtree augmentations: `size`, `sum`, `lazy_reverse`.

```python
class RopeNode:
    __slots__ = ("priority", "char", "size", "sum", "lazy_rev", "left", "right")
    def __init__(self, c: str) -> None:
        self.priority = random.random()
        self.char = c
        self.size = 1
        self.sum = ord(c)
        self.lazy_rev = False
        self.left: RopeNode | None = None
        self.right: RopeNode | None = None

def _push(t: RopeNode) -> None:
    if t.lazy_rev:
        t.left, t.right = t.right, t.left
        if t.left: t.left.lazy_rev ^= True
        if t.right: t.right.lazy_rev ^= True
        t.lazy_rev = False

def _update(t: RopeNode) -> None:
    t.size = 1 + (t.left.size if t.left else 0) + (t.right.size if t.right else 0)
    t.sum = ord(t.char) + (t.left.sum if t.left else 0) + (t.right.sum if t.right else 0)

# split / merge: identical to ImpTreap above but with _push at the start of each call

def reverse_range(root: RopeNode, l: int, r: int) -> RopeNode:
    a, bc = split(root, l)
    b, c = split(bc, r - l)
    b.lazy_rev ^= True
    return merge(merge(a, b), c)

def sum_range(root: RopeNode, l: int, r: int) -> int:
    a, bc = split(root, l)
    b, c = split(bc, r - l)
    s = b.sum
    return s, merge(merge(a, b), c)                               # restore tree
```

**Why this is impossible with AVL/RB without massive engineering:** AVL/RB are keyed on a key, not an implicit position. To maintain "implicit position" in those, you'd need to track subtree sizes (fine) *and* propagate lazy reverse through rotations (very fine — but the rotation logic is already complex). Treaps, by contrast, have **only two operations**: split and merge. Lazy propagation hooks in cleanly at the top of each.

In Sublime Text, Atom, and other editor implementations, the text buffer is literally a **rope of this exact form**. Cursor movement is rank-of-position, edit is split-merge, undo is persistent versioning.

---

## 🔬 Deep-dive 3 — Skip list `level` choice and the `p = 0.5` constant

Why height `log₂ n` and probability `p = 0.5`?

**Expected number of levels:** if each node is promoted with probability `p`, the expected height is `log_{1/p} n`. For `p = 0.5`, that's `log₂ n`.

**Expected search cost:** at each level, the search does a constant expected number of forward steps (geometric variable with mean `1/p`). Across `log_{1/p} n` levels, total expected comparisons = `(1/p) · log_{1/p} n`.

For `p = 0.5`: `2 · log₂ n` comparisons.
For `p = 0.25`: `4 · log_4 n = 4 · (log₂ n / 2) = 2 · log₂ n` — same!
For `p = 0.5` *is* the minimum of `(1/p) · ln(n) / ln(1/p)` over `p ∈ (0, 1)`; it minimises at `p = 1/e ≈ 0.37`.

So `p = 0.5` is **near-optimal** and delightfully implementable with a single coin flip per level.

**Memory cost:** expected pointers per node = `1 / (1 - p) = 2` for `p = 0.5`. So memory is ~2× a sorted linked list — quite cheap.

**Pathological height:** the maximum level used can spike. For `p = 0.5` and `n = 10^6`, max height is concentrated around `log₂(10^6) ≈ 20`, but with non-trivial probability of 25 or so. That's why `MAX_LEVEL = 16` works for `n ≤ 65536`; bump to `MAX_LEVEL = 24` for `n ≤ 16M`.

??? tip "Java's `ConcurrentSkipListMap` uses skip lists. Why not a concurrent BST?"
    Concurrent BSTs require complex tree-rotation locking (or seqlocks, or hand-over-hand). Skip lists have **no rotations** — each node is independent — so lock-free CAS-based insertion is straightforward: CAS-link your node into each level bottom-up. This is the entire reason `ConcurrentSkipListMap` exists.

---

## 🐛 Common bugs

1. **Forgetting `_push` in implicit treap before split/merge.** Lazy values need to flow into children before the structure changes shape — otherwise the lazy bit is lost.
2. **Forgetting `_update` after split/merge.** Subtree sizes must be recomputed at every node whose children changed. Skip an update and `split(t, k)` returns garbage.
3. **Using `random.seed(0)` in tests then expecting `O(log n)` per op.** Fixed seeds produce deterministic priorities — an adversary (or unlucky test) can hit `O(n)` chains. Re-seed only when reproducibility is essential.
4. **Skip list's MAX_LEVEL too small.** For `n = 10^7`, `MAX_LEVEL = 16` may overflow. Use `int(log2(n)) + 4` to be safe.
5. **Skip list's `update[]` array size.** Allocate `MAX_LEVEL` even though `self.level` may be smaller — otherwise inserting at a new top level has no predecessor to splice into.
6. **Treap delete with both children present but priorities equal.** Edge case from collisions — break ties deterministically (e.g. always rotate left).
7. **Persistent treap mutating `priority` on the cloned node.** Clone with the **original** priority, not a new random — otherwise the heap property breaks across versions.
8. **Implicit treap mixing key-ordered and position-ordered indices.** With implicit treaps, there's no `key` field — `split(t, k)` is by **position**, not by value. Confusing the two leads to silent wrong answers.

---

## 🗣️ Interviewer phrasings to recognize

- "**Insert / delete / kth element**, all in `O(log n)`" → treap, skip list, or `SortedList`.
- "**Reverse a range** in a string / array, then keep doing more operations" → implicit treap rope.
- "**Persistent ordered set** — keep all historical versions" → persistent treap or segment tree on indices.
- "**Concurrent ordered map** — multiple threads inserting / scanning" → skip list.
- "Build a **balanced BST without rotations**" → treap (priorities) or skip list (levels).
- "**Cartesian tree** of an array" → treap built bottom-up where priorities are the array values.

---

## 🧭 Connections to other patterns

- **[Segment Trees](03-segment-trees.md)** — the index-keyed alternative. Faster constants for fixed-size arrays; treap wins for *resizing* arrays (insert/delete at any position).
- **[Fenwick Tree (BIT)](04-fenwick-bit.md)** — order-statistics on small value ranges (after coord compression). Treap wins when values come from a huge or unbounded domain.
- **[Heavy-Light Decomposition](06-heavy-light-decomposition.md)** — treaps can replace the underlying segment tree if you need split/merge of paths (link-cut trees use them).
- **Persistent data structures** (next page) — path-copying treaps are the textbook persistent ordered set.
- **`sortedcontainers.SortedList`** — Python's de-facto skip-list-like container. In interviews, mention you'd use it; in implementation rounds, build a treap.
- **Link-cut trees / Splay trees** — when treaps aren't enough (need amortised O(log n) per *forest* operation, not per tree).

---

## ✅ Self-check — 8 questions

??? question "1. Why does a random-priority treap have expected height O(log n)?"
    For any two in-order nodes `i < j`, `i` is an ancestor of `j` iff `i` has the max priority in the contiguous range `[i..j]` — probability `1/(j-i+1)`. Summing over all `i ≠ j` gives expected depth ≤ 2H_n ≈ 1.39 log₂ n.

??? question "2. What are the *only* two operations an implicit treap exposes, and why is that powerful?"
    `split(t, k)` and `merge(a, b)`. Every other operation (insert at i, delete range, reverse range, lazy add) is built from these by splitting out the affected segment, mutating it, and merging back.

??? question "3. Why is `p = 0.5` the typical skip-list level probability?"
    It minimises memory (~2 pointers per node) and gives `2 log₂ n` expected comparisons per search — close to the theoretical optimum at `p = 1/e ≈ 0.37`. And it's implementable with a single coin flip.

??? question "4. Compare red-black tree vs treap for production code."
    Red-black: deterministic O(log n) worst case, ~2× constant factor smaller than treap, but ~400 lines to implement correctly. Treap: O(log n) expected, ~80 lines, randomised so adversary-proof, supports split/merge as primitives. Production libraries (`std::map`, `TreeMap`) use red-black for the worst-case guarantee; competitive programmers and rope-style editors use treap for the simplicity and split/merge.

??? question "5. How do you make a persistent treap?"
    Path-copying: every modifying operation clones the root-to-modified-node path, leaving everything else shared. Each modification costs O(log n) extra memory and time; old versions remain valid.

??? question "6. Why are skip lists the standard for concurrent ordered maps (e.g. Java's ConcurrentSkipListMap)?"
    No rotations — each node's structure is independent. Lock-free insertion is just CAS-linking the new node at each level bottom-up. Concurrent BSTs require much heavier locking or complex non-blocking algorithms.

??? question "7. When should you NOT use a treap or skip list, even if you know how?"
    When `sortedcontainers.SortedList` is available — its B-tree-of-arrays beats both in practice. When you only need a hash set/map. When the interviewer specifically wants AVL/RB rotations.

??? question "8. What's a Cartesian tree, and how is it related to treaps?"
    A Cartesian tree of an array A is the tree where root is `argmax(A)`, left subtree is the Cartesian tree of A[..root], right subtree is the Cartesian tree of A[root+1..]. It's the unique treap with priorities = A's values and keys = array indices. Built in O(n) using a monotonic stack — used for O(n) RMQ preprocessing.

---

> **Phase 6 closes here — that's all 8 advanced data structures.** Up next in 🧠 Ultra-Advanced: **Persistent Data Structures** — versioned segment trees, persistent arrays, and immutable functional data structures, with `O(log n)` operations and `O(log n)` extra memory per version.
