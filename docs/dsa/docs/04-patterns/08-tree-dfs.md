# Tree DFS

> Recursion's home turf. Walk the tree along one branch all the way down, then back up. The pattern that solves "max depth," "diameter," "path sum," "validate BST," "lowest common ancestor," "serialize/deserialize," and most "tree-shaped" interview questions. Two recursion shapes — **top-down** (carry info from parent) and **bottom-up** (each subtree returns info to its parent) — and one iterative stack flavor for when recursion depth is a worry.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is tree DFS?

Imagine you're a courier who has to ring every doorbell in an apartment block. BFS = "knock on every door on floor 1, then floor 2, then floor 3." DFS = "go all the way up the left staircase to the top, ring every doorbell on the way, come back down, take the right staircase up, do the same."

DFS in a binary tree is the literal reading of recursion: visit the current node, recurse on the left subtree, recurse on the right subtree. Three orderings name the three places you can put the visit:

- **Pre-order** — visit *before* recursing: `root, left, right`. Good for "copy / serialize."
- **In-order** — recurse left, visit, recurse right: `left, root, right`. For BSTs this returns sorted values.
- **Post-order** — recurse first, visit *after*: `left, right, root`. Used when a parent's answer depends on children's answers (diameter, height, "did this subtree contain p or q?").

Tree DFS isn't a single algorithm — it's a *family of recursion shapes*. The questions to ask before writing code:

1. **Does the parent need information from below?** → bottom-up (post-order, return values).
2. **Do children need information from above?** → top-down (pre-order, parameter passing).
3. **Both?** → both. Pass state down as parameters; combine results from below in the parent.

!!! tip "The signal — when to reach for tree DFS"
    Reach for it when:

    - The answer is about a **subtree** (max depth, count of nodes, "is this a valid BST?").
    - The answer is about **paths from root to leaf** (path sum, all root-to-leaf paths).
    - The answer is about **a relationship between two nodes** (LCA, distance).
    - You need ordering **within a subtree** (in-order traversal of a BST).

    If you instead need ordering **across siblings** (level by level), use [Tree BFS](07-tree-bfs.md).

---

## 🧩 The three flavors

### Flavor 1: Bottom-up (post-order, return-value driven)

The most common interview shape. Each call returns a small piece of information about its subtree; the parent combines.

```python
class TreeNode:
    def __init__(
        self,
        val: int = 0,
        left: "TreeNode | None" = None,
        right: "TreeNode | None" = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right


def max_depth(root: TreeNode | None) -> int:
    if root is None:
        return 0                                        # (1) base
    left = max_depth(root.left)                         # (2) recurse first
    right = max_depth(root.right)
    return 1 + max(left, right)                         # (3) combine, return up
```

1. The base case is the *empty* subtree, not a leaf. Always check `None` first.
2. **Recurse before doing the work**: post-order = children-first.
3. The parent's answer is a function of the children's answers + a constant.

**Examples:** Max Depth (LC 104), Diameter of Binary Tree (LC 543), Balanced Binary Tree (LC 110), Lowest Common Ancestor (LC 236), Count Univalue Subtrees (LC 250).

### Flavor 2: Top-down (pre-order, parameter passing)

Each call gets context from its ancestors as parameters. The work happens *on the way down*; results are collected via a closure or a list parameter.

```python
def all_root_to_leaf_paths(root: TreeNode | None) -> list[list[int]]:
    out: list[list[int]] = []

    def dfs(node: TreeNode | None, path: list[int]) -> None:
        if node is None:
            return
        path.append(node.val)                           # (1) extend before recursing
        if node.left is None and node.right is None:    # (2) leaf — record
            out.append(path.copy())                     # (3) snapshot, not reference
        else:
            dfs(node.left, path)
            dfs(node.right, path)
        path.pop()                                      # (4) backtrack

    dfs(root, [])
    return out
```

1. Push state on the way down.
2. Record at leaves only — internal nodes don't represent complete paths.
3. **Always copy when storing** a list that you continue to mutate. Reference bugs here are the #1 source of "why is the answer all the same path?" confusion.
4. Pop on the way up — classic backtracking.

**Examples:** Path Sum II (LC 113), Sum of Root-to-Leaf Numbers (LC 129), Binary Tree Paths (LC 257), Smallest String Starting from Leaf (LC 988).

### Flavor 3: Iterative DFS (explicit stack)

When recursion depth could blow the stack (LC's max tree depth is 10⁴ — Python's default recursion limit is 1000), or when an interviewer asks for an iterator, use an explicit stack.

```python
def inorder_iterative(root: TreeNode | None) -> list[int]:
    out: list[int] = []
    stack: list[TreeNode] = []
    node = root
    while node is not None or stack:
        while node is not None:
            stack.append(node)
            node = node.left                            # (1) drill left
        node = stack.pop()
        out.append(node.val)                            # (2) visit on the way back up
        node = node.right                               # (3) then go right
    return out
```

The "drill-left, visit-on-pop, go-right" idiom mimics what recursion does on the call stack — but you control the stack explicitly.

**Examples:** Binary Search Tree Iterator (LC 173), Inorder Traversal Iterative (LC 94), N-ary Tree Postorder Iterative (LC 590).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Subtree summary | Each node returns one value about its subtree | Max Depth (LC 104) | Bottom-up + base case `None → 0` |
| 2 | Two-piece return | Return a tuple per subtree | Balanced BT (LC 110) | `(is_balanced, height)` per call |
| 3 | Path-from-root | Carry path / sum down as parameter | Path Sum (LC 112) | Subtract from target; check at leaf |
| 4 | Path collector | Same, but accumulate all valid paths | Path Sum II (LC 113) | Backtrack with `path.append/pop` |
| 5 | Bounded recursion | Pass `(min, max)` allowed values down | Validate BST (LC 98) | Update bounds at each step |
| 6 | "Bubble up" search | Find a node, propagate result upward | LCA (LC 236) | Return `node` if found in subtree |
| 7 | Side-effect via closure | Maintain a class-scope answer; return helper info | Diameter (LC 543) | `nonlocal best` updated mid-recursion |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Maximum Depth of Binary Tree | 104 | <span class="diff-easy">Easy</span> | Subtree summary | 📝 |
| 2 | Same Tree | 100 | <span class="diff-easy">Easy</span> | Pairwise DFS | 📝 |
| 3 | Symmetric Tree | 101 | <span class="diff-easy">Easy</span> | Pairwise DFS | 📝 |
| 4 | Invert Binary Tree | 226 | <span class="diff-easy">Easy</span> | Subtree summary (post-order) | 📝 |
| 5 | Path Sum | 112 | <span class="diff-easy">Easy</span> | Path-from-root | 📝 |
| 6 | Path Sum II | 113 | <span class="diff-medium">Medium</span> | Path collector | 📝 |
| 7 | Path Sum III | 437 | <span class="diff-medium">Medium</span> | Path collector + prefix-sum hash | 📝 |
| 8 | Sum Root to Leaf Numbers | 129 | <span class="diff-medium">Medium</span> | Path-from-root | 📝 |
| 9 | Binary Tree Paths | 257 | <span class="diff-easy">Easy</span> | Path collector | 📝 |
| 10 | Lowest Common Ancestor of Binary Tree | 236 | <span class="diff-medium">Medium</span> | Bubble-up search | 📝 |
| 11 | LCA of BST | 235 | <span class="diff-medium">Medium</span> | Bounded descent | 📝 |
| 12 | Diameter of Binary Tree | 543 | <span class="diff-easy">Easy</span> | Side-effect via closure | 📝 |
| 13 | Binary Tree Maximum Path Sum | 124 | <span class="diff-hard">Hard</span> | Side-effect via closure | 📝 |
| 14 | Validate Binary Search Tree | 98 | <span class="diff-medium">Medium</span> | Bounded recursion | 📝 |
| 15 | Recover Binary Search Tree | 99 | <span class="diff-medium">Medium</span> | In-order detect-pair | 📝 |
| 16 | Convert Sorted Array to BST | 108 | <span class="diff-easy">Easy</span> | Build-by-bisection | 📝 |
| 17 | Serialize and Deserialize Binary Tree | 297 | <span class="diff-hard">Hard</span> | Pre-order with sentinel | 📝 |
| 18 | Flatten Binary Tree to Linked List | 114 | <span class="diff-medium">Medium</span> | Post-order relink | 📝 |
| 19 | Count Good Nodes in Binary Tree | 1448 | <span class="diff-medium">Medium</span> | Path-from-root (max so far) | 📝 |
| 20 | House Robber III | 337 | <span class="diff-medium">Medium</span> | Two-piece return (rob/skip) | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Path Sum II (LC 113)

> Given a binary tree and a target sum, return **all** root-to-leaf paths whose node values add up to `target`.

This is the textbook example of **top-down DFS with backtracking**. The cleanest, most idiomatic Python here uses an inner helper plus a closure-captured `out` list.

#### Code

```python
def path_sum(root: TreeNode | None, target: int) -> list[list[int]]:
    out: list[list[int]] = []
    path: list[int] = []

    def dfs(node: TreeNode | None, remaining: int) -> None:
        if node is None:
            return
        path.append(node.val)                          # (1) extend
        remaining -= node.val
        if node.left is None and node.right is None and remaining == 0:
            out.append(path.copy())                    # (2) snapshot at leaf
        else:
            dfs(node.left, remaining)
            dfs(node.right, remaining)
        path.pop()                                     # (3) backtrack

    dfs(root, target)
    return out
```

1. Push `node.val` onto the path before recursing — children see their ancestor chain.
2. **`path.copy()` is mandatory.** If you append `path` itself, every entry in `out` aliases the same list, which keeps mutating as you backtrack. By the end, `out` is `n` references to an empty list.
3. Pop after recursing — the path returns to its parent's state.

#### Dry run on

```
        5
       / \
      4   8
     /   / \
    11  13  4
   / \      / \
  7   2    5   1
```

target = 22. Expected: `[[5,4,11,2], [5,8,4,5]]`.

The DFS does 6 root-to-leaf walks. Tracing the two that succeed:

| Step | Action | `path` | `remaining` |
|------|--------|--------|-------------|
| Start at 5 | append, sub | `[5]` | 17 |
| → 4 | append, sub | `[5,4]` | 13 |
| → 11 | append, sub | `[5,4,11]` | 2 |
| → 7 (leaf, 2 ≠ 0) | append, sub, no record | `[5,4,11,7]` | -5 |
| ← pop 7 | | `[5,4,11]` | 2 |
| → 2 (leaf, 2 = 2 ✓) | **record** `[5,4,11,2]` | `[5,4,11,2]` | 0 |
| ← unwind to 5 | … | … | … |
| → 8 | … | `[5,8]` | 9 |
| → 13 (leaf, 9-13 ≠ 0) | record nothing | `[5,8,13]` | -4 |
| → 4 → 5 (leaf, 9-4-5 = 0 ✓) | **record** `[5,8,4,5]` | `[5,8,4,5]` | 0 |
| → 4 → 1 (leaf, 9-4-1 ≠ 0) | nothing | `[5,8,4,1]` | 4 |

Final `out`: `[[5,4,11,2], [5,8,4,5]]` ✓.

#### Why subtract from target instead of accumulating?

Same number of operations either way, but `remaining == 0` at a leaf is one comparison; `path_sum == target` would require either a running sum or `sum(path)` (O(depth) per leaf, blowing up to O(n·depth)). The subtract idiom is O(1) per leaf check.

#### Complexity

- **Time:** O(n²) worst case — n leaves × O(n) `path.copy()`. For balanced trees, O(n log n).
- **Space:** O(h) for the recursion stack + O(answer size).

---

### Deep-dive 2 — Diameter of Binary Tree (LC 543)

> The diameter of a binary tree is the length (in edges) of the longest path between any two nodes. The path may or may not pass through the root.

The interview-classic that teaches **"return one thing, store another."** Each subtree returns its **height** to its parent, but the *answer* (the diameter) is updated as a side effect inside the function.

#### Code

```python
def diameter_of_binary_tree(root: TreeNode | None) -> int:
    best = 0

    def height(node: TreeNode | None) -> int:
        nonlocal best
        if node is None:
            return 0
        left = height(node.left)
        right = height(node.right)
        # (1) The longest path *through* `node` has `left + right` edges.
        best = max(best, left + right)
        # (2) But the parent only cares about the deeper branch + 1 edge to `node`.
        return 1 + max(left, right)

    height(root)
    return best
```

1. The diameter could pass through *any* node — so at every node, we ask: "if this node is the apex of the longest path, what's the answer?" That's `left_height + right_height` (the path goes down-left then down-right).
2. The **return value** is what the *parent* needs: the deeper branch plus the edge from parent to this node.

The mismatch — return value ≠ answer — is what makes this pattern interview-worthy. Many candidates try to return both pieces and tangle themselves up.

#### Dry run on

```
        1
       / \
      2   3
     / \
    4   5
```

| Call | left | right | `best` after | returns (height) |
|------|------|-------|--------------|------------------|
| height(4) | 0 | 0 | max(0, 0) = 0 | 1 |
| height(5) | 0 | 0 | 0 | 1 |
| height(2) | 1 | 1 | max(0, 1+1) = **2** | 1+max(1,1) = 2 |
| height(3) | 0 | 0 | 2 | 1 |
| height(1) | 2 | 1 | max(2, 2+1) = **3** | 1+max(2,1) = 3 |

Answer: `best = 3`. The path `4 → 2 → 1 → 3` has 3 edges. ✓

#### Why we count edges, not nodes

LeetCode 543 specifically defines diameter as edges. If you accidentally return `1 + left + right` and `1 + max(left, right)` you'd be counting nodes, off-by-one. Read the problem.

#### Variant: Binary Tree Maximum Path Sum (LC 124)

Replace heights with sums and clamp negatives to zero (a negative branch contributes nothing — just don't take it):

```python
left = max(0, max_gain(node.left))
right = max(0, max_gain(node.right))
best = max(best, node.val + left + right)
return node.val + max(left, right)
```

Same skeleton, three semantic tweaks. Hard problem, easy code once you've internalised diameter.

#### Complexity

- **Time:** O(n) — one recursive call per node.
- **Space:** O(h) recursion stack.

---

### Deep-dive 3 — Validate Binary Search Tree (LC 98)

> Given the root of a binary tree, decide whether it is a valid BST. A valid BST has every node strictly greater than all values in its left subtree and strictly less than all values in its right subtree.

The candidate trap: comparing each node only to its immediate children. That's wrong — a value in the right subtree of root must beat *every* ancestor on the way down, not just root.

#### Approach A — Bounded recursion (top-down)

Pass the allowed `(low, high)` range down. Each step tightens the bound for the relevant child.

```python
def is_valid_bst(root: TreeNode | None) -> bool:
    def check(
        node: TreeNode | None, low: float, high: float
    ) -> bool:
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return (
            check(node.left, low, node.val) and        # (1) right bound shrinks
            check(node.right, node.val, high)          # (2) left bound shrinks
        )

    return check(root, float("-inf"), float("inf"))
```

1. Every node in the left subtree must be < `node.val` and > `low`.
2. Every node in the right subtree must be > `node.val` and < `high`.

This is **Flavor 2** (top-down, parameter passing) — the bounds are the carried context.

#### Approach B — In-order traversal (bottom-up via side effect)

A valid BST's in-order traversal is strictly increasing. Walk in-order; at each visit, compare to the previous value.

```python
def is_valid_bst_inorder(root: TreeNode | None) -> bool:
    prev: float = float("-inf")
    valid = True

    def inorder(node: TreeNode | None) -> None:
        nonlocal prev, valid
        if node is None or not valid:
            return
        inorder(node.left)
        if node.val <= prev:
            valid = False
            return
        prev = node.val
        inorder(node.right)

    inorder(root)
    return valid
```

#### Dry run for Approach A on

```
        5
       / \
      1   4
         / \
        3   6
```

Note: 5's right child is 4, but 4 < 5 — already a violation. But the *real* trap is at node 3: 3 is greater than 1 (its left-subtree's only ancestor going through the right subtree), but 3 is less than 5 (the original root). Naive parent-only check: 3 < 4 ✓, 3 < 6 ✓ — passes. Bounded check: at node 3, the bounds are `(5, 4)` — meaning value must be > 5 AND < 4, which is impossible. The bounded check correctly rejects.

| Call | Bounds | `node.val` | Pass? |
|------|--------|------------|-------|
| check(5) | (-∞, ∞) | 5 | ✓, recurse |
| check(1) (left of 5) | (-∞, 5) | 1 | ✓, no children, return True |
| check(4) (right of 5) | (5, ∞) | 4 | **fail** (`4 > 5` false) → return False |

Output: `False` ✓.

#### Why Approach A is the recommended interview answer

Approach B's in-order trick is elegant but has a gotcha: if you forget to short-circuit (`if not valid: return`), you keep recursing after a violation and might overwrite `valid = True` incorrectly… actually you can't, but the bookkeeping is fiddly. Approach A's bound-passing is direct and self-documenting.

#### Complexity (both)

- **Time:** O(n).
- **Space:** O(h) recursion stack.

---

## 🐛 Common bugs

1. **Storing `path` itself instead of `path.copy()`** in the path-collector pattern. Every entry in `out` aliases the same backing list and ends up empty after backtracking.
2. **Returning the answer from a "compute and bubble up" function.** In Diameter / Max Path Sum, the *return* is the value the parent needs, not the answer. Use a closure / `nonlocal` for the answer.
3. **Validate BST with parent-only checks.** Bounds must shrink down the tree; the immediate parent isn't enough.
4. **Off-by-one in edge-count vs node-count problems.** Re-read whether the answer is in nodes or edges.
5. **Hitting Python's default recursion limit (1000) on a deep tree.** Use the iterative stack flavor or `sys.setrecursionlimit(...)` (interviewer-dependent).
6. **Confusing "leaf" with "nullable child."** A leaf has both children `None`. A node with one child is *not* a leaf.
7. **Mutating the tree by accident.** Some "flatten" / "invert" problems return a new shape *in-place* — be deliberate.
8. **Stale closure variable.** Common when copy-pasting two helper functions inside the same outer scope; make sure each closure captures the correct `nonlocal`.

---

## 🗣️ Interviewer phrasings to recognize

- "Find the maximum depth / sum / count in the tree." → bottom-up subtree summary.
- "Find all root-to-leaf paths that …" → top-down with backtracking.
- "Find the lowest common ancestor of `p` and `q`." → bubble-up search (return the node if `p` or `q` was found in this subtree).
- "Is the tree a valid BST?" → bounded recursion.
- "Find the longest path in the tree." → diameter pattern (return height, update answer).
- "Serialize / deserialize the tree." → pre-order with `null` sentinels.
- "Flatten the tree." → post-order relink.

---

## 🧭 Connections to other patterns

- **Tree BFS** ([07-tree-bfs.md](07-tree-bfs.md)) — when you need ordering across siblings.
- **Backtracking** — DFS *is* backtracking when you push state on the way down and pop on the way back up.
- **Divide and Conquer** — Convert Sorted Array to BST (LC 108) is DFS that builds a tree, not walks it.
- **Dynamic Programming on Trees** — House Robber III (LC 337) returns a 2-tuple per subtree representing "rob this node" vs "skip it"; same recursion shape, more state.
- **In-place Linked List Reversal** ([06-in-place-linked-list-reversal.md](06-in-place-linked-list-reversal.md)) — Flatten Binary Tree to Linked List (LC 114) uses a post-order relink that's structurally similar to LL reversal.

---

## ✅ Self-check — 8 questions

??? question "1. When do you choose top-down vs bottom-up?"
    Top-down when children need information *from* their ancestors (path sums, bounds, accumulated values). Bottom-up when parents need information *from* their children (heights, sums, "did the subtree contain x?"). When both, parameters carry the down-info, return values carry the up-info.

??? question "2. Why is the base case `if node is None: return`, not `if node is leaf`?"
    Every recursion must terminate at the boundary of the data structure. The structural boundary of a tree is `None` (the absence of a node), not a leaf. Treating leaves as the base case forces special-handling of single-child nodes — confusing and bug-prone.

??? question "3. Why do we always copy the path before storing it in path-collector problems?"
    `out.append(path)` stores a reference. Subsequent `path.pop()` calls will mutate the list you just stored. By the end, every entry in `out` aliases the same (now-empty) list. `path.copy()` snapshots the current state.

??? question "4. Why does Diameter need a closure / `nonlocal` variable?"
    Because each recursive call must *return* one piece of information (height) to its parent, but the answer (longest path through any node) is computed *during* the recursion, not at any single call site. Closures let you maintain the answer alongside the return value.

??? question "5. Why is parent-only comparison wrong for Validate BST?"
    A right-subtree value must beat every ancestor on the *path from root*, not just its direct parent. A node whose value is between its parent and grandparent looks fine locally but breaks the global BST property. Bounds shrinking down the tree captures the global constraint.

??? question "6. What's the recursion depth of a balanced tree with n nodes?"
    O(log n). For a skewed tree (every node has only one child), recursion depth is O(n), which is what blows Python's default limit at ~1000.

??? question "7. How do you turn a recursive in-order traversal into an iterator?"
    Use Flavor 3 (explicit stack). The iterator stores a stack of "left-spines" and yields one node per `next()` call by popping, recording, and pushing the right child's left-spine. See LC 173 for the full pattern.

??? question "8. Outline the LCA algorithm and why it works."
    `lca(node, p, q)`: if `node is None or node is p or node is q`, return `node`. Recurse on both children. If both calls return non-None, this node is the LCA (one target found in each subtree). If only one returned non-None, that's the LCA (or the only one of `p`/`q` found so far). The reason it works: the LCA is the deepest node where the search "splits" between left and right.

---

> **Next pattern up:** Two Heaps — the median-of-stream pattern using a max-heap of small-half + min-heap of large-half, plus IPO/k-pairs variants (page coming next).
