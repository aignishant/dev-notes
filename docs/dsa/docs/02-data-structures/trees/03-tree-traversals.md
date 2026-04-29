# Tree traversals

> Four orders, two implementations each, one constant-space trick — and the problems that test all of them.

<span class="phase-status phase-done">Phase 2 — Data Structures</span>

---

!!! abstract "What this chapter is"
    Tree problems almost always reduce to "visit every node in a specific order". This page covers the **four canonical orders** (preorder, inorder, postorder, level-order), both **recursive** and **iterative** implementations, **Morris traversal** for `O(1)` space, and the construction/serialization problems that come up constantly.

    **Prereqs:** [Tree basics](01-tree-basics.md), [BSTs](02-binary-search-trees.md), [Stacks & Queues](../stacks-and-queues/01-stacks-and-queues-basics.md).

---

## 1. The four orders

For each non-empty subtree rooted at `node`, with children `L` and `R`:

| Order | Visit pattern | Mnemonic | Typical use |
|---|---|---|---|
| **Preorder** | `node, L, R` | "root first" | clone tree, serialize, top-down DP |
| **Inorder** | `L, node, R` | "root middle" | BST sorted output, recover BST |
| **Postorder** | `L, R, node` | "root last" | bottom-up DP (heights, max path sum), delete tree |
| **Level-order** | breadth-first | "row by row" | shortest path, right-side view, zigzag |

```
        (1)
       /   \
     (2)   (3)
     / \
   (4) (5)

Preorder:    1 2 4 5 3
Inorder:     4 2 5 1 3
Postorder:   4 5 2 3 1
Level-order: 1 2 3 4 5
```

---

## 2. Recursive — the easy ones

```python linenums="1"
from __future__ import annotations
from collections import deque

def preorder(node, out: list[int]) -> None:
    if node is None: return
    out.append(node.val)
    preorder(node.left, out)
    preorder(node.right, out)

def inorder(node, out: list[int]) -> None:
    if node is None: return
    inorder(node.left, out)
    out.append(node.val)
    inorder(node.right, out)

def postorder(node, out: list[int]) -> None:
    if node is None: return
    postorder(node.left, out)
    postorder(node.right, out)
    out.append(node.val)
```

All `O(n)` time, `O(h)` space (recursion stack). Skewed tree → `O(n)` space and you risk Python's default recursion limit (~1000) — that's why interviewers sometimes ask for the iterative form.

---

## 3. Iterative inorder — the canonical pattern

> The "push the entire left spine, pop, visit, jump right" trick. **Memorize this** — it's the basis for `kth smallest`, `validate BST`, and `BST iterator`.

```python linenums="1"
def inorder_iter(root) -> list[int]:
    out: list[int] = []
    stack: list = []
    node = root
    while node or stack:
        while node:                  # 1. push the entire left spine
            stack.append(node)
            node = node.left
        node = stack.pop()           # 2. pop the leftmost unvisited
        out.append(node.val)         # 3. visit it
        node = node.right            # 4. jump to its right child; repeat
    return out
```

The two nested loops feel weird at first. Read them as:

1. *Inner `while`* — descend leftward, stacking everything as you go.
2. *Pop* — the leftmost unvisited node is on top.
3. *Visit it.*
4. *Move right* — and the outer loop will descend that subtree's left spine next.

The stack holds at most `h` nodes — `O(h)` space, `O(n)` time.

---

## 4. Iterative preorder — easy

Push right child first so left is processed first.

```python linenums="1"
def preorder_iter(root) -> list[int]:
    if root is None: return []
    out: list[int] = []
    stack = [root]
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right: stack.append(node.right)
        if node.left:  stack.append(node.left)
    return out
```

---

## 5. Iterative postorder — the tricky one

Postorder is `L, R, node`. There are **two standard approaches**.

=== "Two stacks (easier to remember)"

    Push root onto stack 1. Pop, push to stack 2, then push left then right onto stack 1 (so right is popped first → reversed). At the end stack 2 holds the postorder.

    ```python linenums="1"
    def postorder_iter(root) -> list[int]:
        if root is None: return []
        s1, s2 = [root], []
        while s1:
            node = s1.pop()
            s2.append(node)
            if node.left:  s1.append(node.left)
            if node.right: s1.append(node.right)
        return [n.val for n in reversed(s2)]
    ```

    **Why this works**: stack 1 produces a **modified preorder** (`node, R, L`). Reversing that gives `L, R, node` — postorder. Clean and short.

=== "Mark-visited (one stack)"

    Push each node twice — once "to visit", once "to expand" — distinguished by a flag. Visit only when we see the flagged copy.

    ```python linenums="1"
    def postorder_iter(root) -> list[int]:
        out: list[int] = []
        if root is None: return out
        stack: list[tuple] = [(root, False)]
        while stack:
            node, visited = stack.pop()
            if visited:
                out.append(node.val)
            else:
                stack.append((node, True))           # push self for visit later
                if node.right: stack.append((node.right, False))
                if node.left:  stack.append((node.left, False))
        return out
    ```

    Slightly more memory but generalizes to **any** order — swap the three pushes' order to get pre/in/post with the same skeleton.

---

## 6. Level-order (BFS)

> Visit nodes row by row using a queue. The bedrock of "shortest path in unweighted graph" too.

```python linenums="1"
def level_order(root) -> list[list[int]]:
    if root is None: return []
    out: list[list[int]] = []
    q: deque = deque([root])
    while q:
        level_size = len(q)              # snapshot — only nodes from THIS level
        level: list[int] = []
        for _ in range(level_size):
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        out.append(level)
    return out
```

!!! tip "The `level_size = len(q)` trick"
    The queue mixes nodes from the current level (being popped) and the next level (being pushed). Snapshotting the length **at the start of each iteration** locks in how many to pop for the current level. Without this you can't tell where one level ends.

### Right-side view — one-line variant

For each level, take the **last** value:

```python linenums="1"
def right_side_view(root) -> list[int]:
    if root is None: return []
    out: list[int] = []
    q: deque = deque([root])
    while q:
        n = len(q)
        for i in range(n):
            node = q.popleft()
            if i == n - 1:               # last node of this level
                out.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
    return out
```

??? tip "DFS variant of right-side view"
    Preorder visiting **right before left**, tracking depth — the first node you see at each new depth is the rightmost. `O(n)` time, `O(h)` space.

---

## 7. Morris traversal — `O(1)` space inorder

> The "no stack, no recursion" inorder walk. The trick: temporarily **thread** each node's predecessor's right pointer to point to it, walk, then **unthread** to restore the tree.

The algorithm:

1. Start at `root`. Loop while current is not `None`.
2. If current has **no left child**: visit it, move to `current.right`.
3. Otherwise find the **inorder predecessor** = rightmost node of the left subtree.
    - If predecessor's `right` is `None`: thread it (`pred.right = current`), move to `current.left`.
    - If predecessor's `right` is `current` (we've been here before): **unthread** (`pred.right = None`), visit current, move to `current.right`.

```python linenums="1"
def morris_inorder(root) -> list[int]:
    out: list[int] = []
    curr = root
    while curr is not None:
        if curr.left is None:
            out.append(curr.val)             # no left subtree → visit
            curr = curr.right
        else:
            # find inorder predecessor (rightmost in left subtree)
            pred = curr.left
            while pred.right is not None and pred.right is not curr:
                pred = pred.right

            if pred.right is None:           # first visit — create thread
                pred.right = curr
                curr = curr.left
            else:                            # second visit — thread exists
                pred.right = None            # UNTHREAD: restore the tree
                out.append(curr.val)
                curr = curr.right
    return out
```

!!! warning "Don't skip the unthread step"
    If you forget `pred.right = None` you leave the tree mutated — the next call sees cycles and loops forever. The whole **point** of Morris is that the tree returns to its original state.

**Trade-off:** `O(1)` extra space but ~`2n` traversals (each edge visited twice). Constant factor is ~2× the recursive version. Only choose it when the interviewer **specifically asks for `O(1)` space**.

---

## 8. Construct binary tree from preorder + inorder

> Classic divide-and-conquer.

**Key insight:**

- The **first** element of preorder is the root.
- Find that root in the inorder array — everything to its **left** is the left subtree's inorder, everything to its **right** is the right subtree's inorder.
- The size of the left subtree tells you how to slice the preorder array for the recursive calls.

Naive implementation slices arrays → `O(n²)`. Optimal version uses a **hashmap of inorder index** plus index pointers → `O(n)`.

```python linenums="1"
def build_tree(preorder: list[int], inorder: list[int]):
    idx = {v: i for i, v in enumerate(inorder)}     # O(1) lookup
    pre_iter = iter(preorder)

    def build(in_lo: int, in_hi: int):
        if in_lo > in_hi:
            return None
        root_val = next(pre_iter)
        root = TreeNode(root_val)
        mid = idx[root_val]
        root.left  = build(in_lo, mid - 1)          # left first — preorder demands it
        root.right = build(mid + 1, in_hi)
        return root

    return build(0, len(inorder) - 1)
```

??? question "Why must we recurse left before right?"
    Because we're consuming preorder **in order**. After taking the root, the next preorder element is the root of the **left** subtree (preorder = root, left, right). Recursing right first would consume the wrong elements. The `iter(preorder)` + `next()` pattern is what enforces this — there's no index to pass around because the iterator is the index.

---

## 9. Serialize & deserialize a binary tree

> "Encode a binary tree to a string, decode it back. Tree shape is arbitrary — not a BST."

The cleanest interview answer is **preorder with explicit null markers**.

```python linenums="1"
NULL = "#"
SEP = ","

def serialize(root) -> str:
    parts: list[str] = []
    def dfs(node):
        if node is None:
            parts.append(NULL)
            return
        parts.append(str(node.val))
        dfs(node.left)
        dfs(node.right)
    dfs(root)
    return SEP.join(parts)

def deserialize(data: str):
    tokens = iter(data.split(SEP))
    def build():
        tok = next(tokens)
        if tok == NULL:
            return None
        node = TreeNode(int(tok))
        node.left  = build()
        node.right = build()
        return node
    return build()
```

**Why null markers?** Without them, you can't distinguish "left child of value X" from "right child of value X" in a non-BST. The nulls disambiguate the shape.

??? tip "Alternative: level-order with nulls"
    Another common encoding (LeetCode uses this) — BFS, emit `#` for missing children, **omit trailing nulls**. Slightly trickier to deserialize because you process pairs of children per parent in queue order.

---

## 10. Interview problems

### 10.1 Binary Tree Level Order Traversal
Section 6 — BFS with `level_size` snapshot.

### 10.2 Binary Tree Right Side View
Section 6 — last node of each BFS level, or DFS visiting right-before-left and recording first node at each depth.

### 10.3 Construct Binary Tree from Preorder and Inorder
Section 8 — hashmap of inorder index, recurse with index bounds, `O(n)`.

### 10.4 Serialize and Deserialize Binary Tree
Section 9 — preorder + null markers, `O(n)` both directions.

### 10.5 Binary Tree Maximum Path Sum
> A path is any sequence of connected nodes (start and end can be **anywhere**, the path doesn't have to go through the root). Return the maximum sum.

This is **postorder DP** — the canonical interview question for "bottom-up tree thinking". At each node, two quantities matter:

- **Gain** to return to my parent = `node.val + max(0, max(left_gain, right_gain))`. The parent can only extend the path through one child (otherwise the "path" branches).
- **Best path through me** = `node.val + max(0, left_gain) + max(0, right_gain)`. Both children can contribute *here*, because the path can turn at this node.

Track the global max while returning the linear gain.

```python linenums="1"
import math

def max_path_sum(root) -> int:
    best = -math.inf

    def gain(node) -> int:
        nonlocal best
        if node is None:
            return 0
        left  = max(gain(node.left),  0)         # ignore negative subtrees
        right = max(gain(node.right), 0)
        best  = max(best, node.val + left + right)   # path *through* this node
        return node.val + max(left, right)            # path *via* this node to parent

    gain(root)
    return best
```

??? question "Why `max(..., 0)`?"
    Negative subtree contributions can only hurt the path sum — drop them by treating their gain as 0 (i.e. don't extend the path that way).

`O(n)` time, `O(h)` space. The pattern — return one number to the parent, track another globally — recurs in **diameter of binary tree**, **longest univalue path**, and many tree DP problems.

---

## 🃏 Cheatsheet

| Traversal | Recursive | Iterative | Space | Use case |
|---|---|---|---|---|
| Preorder | trivial | one stack, push right then left | `O(h)` | clone, serialize |
| Inorder | trivial | left-spine stack | `O(h)` | BST sorted output |
| Postorder | trivial | two stacks **or** mark-visited | `O(h)` | bottom-up DP, delete |
| Level-order | n/a | BFS with `deque`, snapshot length | `O(w)` | shortest path, views |
| Morris inorder | n/a | threading + unthread | `O(1)` | space-constrained |

**Patterns to memorize:**

- **Iterative inorder** — left spine push, pop, visit, jump right. Basis for kth-smallest, BST iterator, validate-BST.
- **Level-order with `level_size = len(q)`** — basis for right-side view, zigzag, level averages, level sums.
- **Postorder return-vs-track** — return a *linear* value to your parent; track the *branching* value globally. Basis for max path sum, diameter, longest univalue path.
- **Preorder + null markers** — basis for serialize/deserialize, clone with reference equality.

**Recursion limit warning (Python):** the default is ~1000. Skewed trees of 10⁴+ nodes overflow. Use `sys.setrecursionlimit(10**6)` for competitive code, or **always go iterative** in production.

**Choosing the order:**

- Need parent info before children → **preorder**.
- Need children info before parent (sums, heights, validation) → **postorder**.
- BST and want sorted output → **inorder**.
- Shortest path / level-by-level / "first occurrence at depth d" → **level-order**.
