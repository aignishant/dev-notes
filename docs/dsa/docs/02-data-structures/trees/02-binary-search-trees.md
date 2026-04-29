# Binary Search Trees

> The data structure that turns "find this value" into a `O(log n)` walk — when you keep it balanced.

<span class="phase-status phase-done">Phase 2 — Data Structures</span>

---

!!! abstract "What this chapter is"
    A **Binary Search Tree (BST)** is a binary tree where every node obeys an ordering invariant. That single rule unlocks `O(log n)` search, insert, and delete — *if* the tree stays balanced. This page covers the invariant, the three classic operations (with delete's three sub-cases), the validation off-by-one trap, and the five interview problems that show up over and over.

    **Prereqs:** [Tree basics](01-tree-basics.md), [How to think recursively](../../01-foundations/how-to-think-recursively.md).

---

## 1. The BST invariant

> For every node `n`: every value in the **left subtree** is **strictly less than** `n.val`, and every value in the **right subtree** is **strictly greater than** `n.val`. Recursively. All the way down.

```
              (8)
             /   \
          (3)     (10)
         /   \       \
      (1)   (6)      (14)
            / \      /
          (4) (7) (13)
```

!!! warning "The 'no duplicates' assumption"
    Most interview problems assume **all values are distinct**. If duplicates are allowed, you need to pick a side (always left, or always right) and stick with it — and the strict `<` / `>` becomes `<=` / `<` (or `<` / `<=`). **Always clarify with the interviewer.** The default in this chapter is "no duplicates".

??? question "Why this invariant matters"
    Because at each node you can **discard half the tree** in one comparison. That's the entire reason BSTs exist. If `target < node.val`, the right subtree cannot contain it — gone. If `target > node.val`, left subtree gone. Each step halves the search space, which is the definition of `O(log n)` (when the tree is balanced).

---

## 2. The node type

```python linenums="1"
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class TreeNode:
    val: int
    left: TreeNode | None = None
    right: TreeNode | None = None
```

---

## 3. Search — `O(h)`

> Walk down. Go left if `target < node.val`, right if `target > node.val`, return when equal.

=== "Recursive"

    ```python linenums="1"
    def search(root: TreeNode | None, target: int) -> TreeNode | None:
        if root is None or root.val == target:
            return root
        if target < root.val:
            return search(root.left, target)
        return search(root.right, target)
    ```

=== "Iterative"

    ```python linenums="1"
    def search(root: TreeNode | None, target: int) -> TreeNode | None:
        node = root
        while node is not None and node.val != target:
            node = node.left if target < node.val else node.right
        return node
    ```

The **iterative form is preferred in interviews** — same complexity, no recursion budget, and easier to reason about.

---

## 4. Insert — `O(h)`

> Search for the value. When you fall off (hit `None`), attach a new node there.

```python linenums="1"
def insert(root: TreeNode | None, val: int) -> TreeNode:
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert(root.left, val)
    elif val > root.val:
        root.right = insert(root.right, val)
    # val == root.val: no-op (no duplicates)
    return root
```

!!! tip "Always return `root`"
    The pattern `root.left = insert(root.left, val)` lets the recursion handle the `None` case without special-casing the parent. Memorize this idiom — it shows up in delete too.

---

## 5. Delete — the three cases

This is **the** BST interview question. Memorize the three cases.

### 5a. Find the node first
Walk down like search until you land on the target.

### 5b. The three cases

<div class="grid cards" markdown>

-   :material-leaf:{ .lg .middle } &nbsp; **Case 1 — Leaf**

    No children. Just remove it: parent's pointer becomes `None`. Trivial.

-   :material-source-branch:{ .lg .middle } &nbsp; **Case 2 — One child**

    Splice it out: replace the node with its only child. The child takes the node's place; the BST invariant is preserved because the child's whole subtree was already on the correct side of the deleted node's parent.

-   :material-call-split:{ .lg .middle } &nbsp; **Case 3 — Two children**

    The interesting one. Find the **inorder successor** (smallest value in the right subtree — i.e. leftmost node of `node.right`). Copy its value into the node being deleted, then recursively delete the successor from the right subtree. The successor itself has at most a right child (it's the leftmost), so its deletion is Case 1 or Case 2.

</div>

```python linenums="1"
def delete(root: TreeNode | None, val: int) -> TreeNode | None:
    if root is None:
        return None
    if val < root.val:
        root.left = delete(root.left, val)
    elif val > root.val:
        root.right = delete(root.right, val)
    else:
        # found the node to delete
        if root.left is None:        # case 1 (leaf) or case 2 (only right)
            return root.right
        if root.right is None:       # case 2 (only left)
            return root.left
        # case 3: two children — replace with inorder successor
        succ = root.right
        while succ.left is not None:
            succ = succ.left
        root.val = succ.val
        root.right = delete(root.right, succ.val)
    return root
```

??? question "Why inorder successor and not just any descendant?"
    Because the successor is the **smallest value still greater than the node's value** — meaning every value in the left subtree is still less than it, and every remaining value in the right subtree is still greater. The invariant survives. (You can equivalently use the inorder **predecessor** — largest in the left subtree. Pick one and be consistent.)

---

## 6. Validation — the off-by-one trap

> "Given a binary tree, return whether it's a valid BST."

The naive attempt that **everyone gets wrong on the first try**:

```python linenums="1"
# WRONG — checks only immediate children, not the whole subtree
def is_bst_wrong(root: TreeNode | None) -> bool:
    if root is None:
        return True
    if root.left and root.left.val >= root.val:
        return False
    if root.right and root.right.val <= root.val:
        return False
    return is_bst_wrong(root.left) and is_bst_wrong(root.right)
```

It fails on this tree:

```
        (5)
       /   \
     (3)   (8)
           / \
         (4) (9)   ← 4 < 5! invariant broken, but local check passes
```

The local check at node `8` only sees that `4 < 8` and `9 > 8` — both fine locally. But `4` lives in `5`'s right subtree, which is illegal.

### The correct approach — pass `min/max` bounds

```python linenums="1"
def is_valid_bst(root: TreeNode | None) -> bool:
    def check(node: TreeNode | None, lo: float, hi: float) -> bool:
        if node is None:
            return True
        if not (lo < node.val < hi):
            return False
        return check(node.left, lo, node.val) and check(node.right, node.val, hi)
    return check(root, float("-inf"), float("inf"))
```

Each recursive call **tightens the bounds**: going left, the new upper bound is the parent's value; going right, the new lower bound is the parent's value. A node is valid iff its value lies strictly inside its inherited window.

??? tip "Alternative — inorder traversal"
    A BST's inorder traversal is **strictly increasing**. So: do an inorder walk, track the previous value, return False if the current value is `<=` previous. Same `O(n)` time, slightly cleaner if you've already memorized iterative inorder.

    ```python linenums="1"
    def is_valid_bst(root: TreeNode | None) -> bool:
        prev = float("-inf")
        stack: list[TreeNode] = []
        node = root
        while node or stack:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if node.val <= prev:
                return False
            prev = node.val
            node = node.right
        return True
    ```

---

## 7. Inorder traversal yields a sorted sequence

This is the **single most useful BST fact** for interviews:

> An inorder traversal of a BST visits nodes in **strictly increasing** order.

Why: by definition, all of left subtree `< node < ` all of right subtree. Inorder is left → node → right, so the values come out sorted.

**Consequences you'll exploit:**

- Validate BST in `O(n)` (previous section).
- Find the kth smallest in `O(h + k)` with iterative inorder + early exit.
- Recover BST (two swapped nodes) by spotting the two inversions in the inorder sequence.
- Convert BST → sorted doubly linked list in one pass.

---

## 8. Balanced vs unbalanced — the `O(n)` trap

The whole `O(log n)` story assumes the tree is **balanced** — height is `O(log n)`. A naively built BST can be **completely skewed**:

```
Insert in sorted order: 1, 2, 3, 4, 5
    (1)
       \
        (2)
           \
            (3)
               \
                (4)
                   \
                    (5)
```

This is a linked list. Search, insert, delete are all `O(n)`. Worst case **defeats the entire point** of the data structure.

### The fix: self-balancing BSTs
- **AVL trees** — strictly balanced (heights of children differ by ≤ 1). More rotations, faster lookups.
- **Red-Black trees** — looser balance. Fewer rotations on insert/delete. What `std::map`, `TreeMap`, and the Linux scheduler use.
- Both guarantee `O(log n)` for all operations. Both rotate on insert/delete to maintain balance.

In Python practice, reach for `sortedcontainers.SortedList` (a skip list under the hood) — see [Treaps & Skip Lists](../../05-advanced/08-treaps-skip-lists.md).

### Python doesn't give you a BST

Python's standard library has **no balanced BST**. Your two practical replacements:

<div class="grid cards" markdown>

-   :material-vector-arrange-below:{ .lg .middle } &nbsp; **`bisect` + sorted list**

    `O(log n)` search via binary search, but `O(n)` insert/delete because the underlying list shifts. Fine for a few thousand elements.

-   :material-package-variant:{ .lg .middle } &nbsp; **`sortedcontainers.SortedList`**

    Third-party, ships with most competitive-programming environments. `O(log n)` for everything in practice (uses a list-of-lists trick, not a tree). The pragmatic answer to "I need a BST in Python".

</div>

```python linenums="1"
from sortedcontainers import SortedList

sl = SortedList()
sl.add(5); sl.add(2); sl.add(8); sl.add(1)
print(sl)            # SortedList([1, 2, 5, 8])
print(sl[0])         # 1   — kth smallest in O(log n)
print(sl.bisect_left(5))  # 2 — index of 5
sl.remove(2)
```

---

## 9. Kth smallest via inorder

> "Return the kth smallest value in a BST" — `O(h + k)`.

Iterative inorder, decrement a counter, return when it hits zero.

```python linenums="1"
def kth_smallest(root: TreeNode, k: int) -> int:
    stack: list[TreeNode] = []
    node = root
    while node or stack:
        while node:                  # walk down the left spine
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right
    raise ValueError("k larger than tree size")
```

The **early exit** is what makes it `O(h + k)` instead of `O(n)` — you never visit nodes past the kth.

??? tip "Follow-up: frequent inserts/deletes"
    If the tree is modified often and you need the kth smallest repeatedly, **augment each node with a `size` field** (size of its subtree). Then kth smallest is `O(h)` — at each node compare `k` to `left.size + 1`. This is "order statistic tree" territory.

---

## 10. Interview problems

### 10.1 Validate BST
Already shown — bounds approach or inorder approach. Both `O(n)` time, `O(h)` space.

### 10.2 Lowest Common Ancestor of a BST
> Given two nodes `p` and `q`, return their LCA.

In a **general** binary tree, LCA needs a full DFS. In a **BST**, the ordering gives you `O(h)`: the LCA is the first node whose value lies between `p.val` and `q.val` (inclusive).

```python linenums="1"
def lca_bst(root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode:
    lo, hi = min(p.val, q.val), max(p.val, q.val)
    node = root
    while node:
        if node.val < lo:
            node = node.right
        elif node.val > hi:
            node = node.left
        else:
            return node       # split point — this is the LCA
    raise ValueError("p or q not in tree")
```

### 10.3 Kth Smallest in BST
Section 9 above. Iterative inorder + early exit.

### 10.4 Recover BST (two nodes swapped)
> Exactly two nodes of a BST were swapped. Recover the tree without changing structure.

Inorder a valid BST is strictly increasing. After the swap, you'll see **one or two "drops"** (where `prev > current`). Track first and second drops:

- First drop: the **first** offender is `prev`, tentatively the **second** is `current`.
- Second drop (if any): update the **second** offender to `current`.
- Swap their values. Done. `O(n)` time, `O(h)` space (or `O(1)` with Morris).

```python linenums="1"
def recover_tree(root: TreeNode) -> None:
    first: TreeNode | None = None
    second: TreeNode | None = None
    prev: TreeNode | None = None

    def inorder(node: TreeNode | None) -> None:
        nonlocal first, second, prev
        if node is None:
            return
        inorder(node.left)
        if prev and prev.val > node.val:
            if first is None:
                first = prev
            second = node
        prev = node
        inorder(node.right)

    inorder(root)
    assert first and second
    first.val, second.val = second.val, first.val
```

??? question "Why two drops max?"
    If the swapped pair is **adjacent** in the inorder sequence, you see exactly one inversion. If they're **non-adjacent**, you see two. Either way the first drop's `prev` and the last drop's `current` are the swapped nodes.

### 10.5 Convert BST to sorted doubly linked list
> Rewire the tree in place so `left` becomes "previous" and `right` becomes "next", in sorted (inorder) order, and circularly link head and tail.

```python linenums="1"
def bst_to_dll(root: TreeNode | None) -> TreeNode | None:
    if root is None:
        return None
    head: TreeNode | None = None
    prev: TreeNode | None = None

    def inorder(node: TreeNode | None) -> None:
        nonlocal head, prev
        if node is None:
            return
        inorder(node.left)
        if prev is None:
            head = node                  # leftmost = head
        else:
            prev.right = node
            node.left = prev
        prev = node
        inorder(node.right)

    inorder(root)
    # circular link
    head.left = prev
    prev.right = head
    return head
```

Inorder traversal is the trick — it visits nodes in sorted order, and at each visit you splice the current node onto the tail of the list you're building.

---

## 🃏 Cheatsheet

| Operation | Balanced | Skewed (worst) | Notes |
|---|---|---|---|
| Search | `O(log n)` | `O(n)` | iterative preferred |
| Insert | `O(log n)` | `O(n)` | `root.left = insert(root.left, v)` idiom |
| Delete | `O(log n)` | `O(n)` | three cases: leaf / one child / two children |
| Min / Max | `O(log n)` | `O(n)` | walk leftmost / rightmost |
| Inorder | `O(n)` | `O(n)` | yields sorted sequence |
| Validate | `O(n)` | `O(n)` | pass `(lo, hi)` bounds, **not** local checks |
| kth smallest | `O(h + k)` | `O(n)` | iterative inorder + early exit |
| LCA (BST) | `O(h)` | `O(n)` | first node whose value splits `p` and `q` |

**Mental model:** a BST is a recursive halving structure. Every node says "everything smaller is on my left, everything bigger is on my right" — recursively, all the way down. The interview traps are (1) the validation off-by-one, (2) delete's two-children case, and (3) forgetting that "balanced" is an assumption, not a guarantee.

**In Python:** there is no built-in BST. Reach for `bisect` (small data) or `sortedcontainers.SortedList` (anything bigger). Implement a real BST only when the question demands tree mechanics — LCA, validation, recover, traversal-based problems.
