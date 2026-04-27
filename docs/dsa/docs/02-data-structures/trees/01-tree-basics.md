# Trees — the basics

!!! abstract "What this chapter is"
    The structure that **launches more interview questions than any other**. Once you can think recursively about a tree, you can think recursively about anything — graphs, DPs, divide-and-conquer, even file systems and DOMs. Trees are where most candidates' "I can do recursion" claim is actually tested.

    **Reading time:** 4–5 hours cover-to-cover; 30–45 minutes per problem.

    **Prereqs:** [How to think recursively](../../01-foundations/how-to-think-recursively.md), [Linked Lists](../linked-lists/01-linked-list-basics.md) (a tree is a generalized linked list), [Stacks & Queues](../stacks-and-queues/01-stacks-and-queues-basics.md) (used for iterative traversals), and the [Python crash course](../../01-foundations/python-crash-course-for-dsa.md).

---

## Chapter map

<div class="grid cards" markdown>

-   :material-numeric-1-circle:{ .lg .middle } &nbsp; **What is a tree?**

    Plain English + family-tree analogy. The vocabulary you'll see on every problem.

-   :material-numeric-2-circle:{ .lg .middle } &nbsp; **Why we need them**

    Hierarchies, sorted lookup in O(log n), prefix queries, expression trees, decision trees.

-   :material-numeric-3-circle:{ .lg .middle } &nbsp; **How they work internally**

    Node-and-pointer model, array embedding, parent pointers, children lists.

-   :material-numeric-4-circle:{ .lg .middle } &nbsp; **Python implementations from scratch**

    `TreeNode`, `BinaryTree`, `BST`, plus the four canonical traversals — recursive **and** iterative.

-   :material-numeric-5-circle:{ .lg .middle } &nbsp; **Time & space complexity**

    The "balanced vs skewed" gap and why it matters for every BST claim.

-   :material-numeric-6-circle:{ .lg .middle } &nbsp; **Built-in Python tools**

    `bisect`, `sortedcontainers.SortedList`, `heapq`, and what Python *doesn't* give you (no built-in BST).

-   :material-numeric-7-circle:{ .lg .middle } &nbsp; **When to use vs not use**

    Tree vs hash map vs sorted list vs heap vs trie.

-   :material-numeric-8-circle:{ .lg .middle } &nbsp; **Common mistakes & gotchas**

    The 12 pitfalls — including the "BST is sorted" myth and the off-by-one in height.

-   :material-numeric-9-circle:{ .lg .middle } &nbsp; **Patterns this connects to**

    Top-down vs bottom-up recursion, DFS vs BFS, divide-and-conquer, tree DP, LCA, serialize/deserialize.

-   :material-numeric-10-circle:{ .lg .middle } &nbsp; **Practice problems (40)**

    Each in 5-layer progressive format with follow-ups.

-   :fontawesome-solid-microphone:{ .lg .middle } &nbsp; **How interviewers ask this**

    The phrasings, the "draw it on the whiteboard" expectation, and the recursion tell.

-   :material-clipboard-check:{ .lg .middle } &nbsp; **Self-check quiz**

    20 questions. If you can answer 18, you've mastered tree basics.

</div>

---

## 1. What is a tree?

> **Plain English:** a tree is a collection of "nodes" connected by edges, with **one root** at the top and **no cycles**. Each node holds a value and points to zero or more **children**. From any node, there is exactly one path back to the root.

The everyday analogy is a **family tree**, but flipped: the **root** is the oldest ancestor at the top, the **leaves** are the youngest descendants at the bottom. Each person has one parent (except the root) and any number of children.

```
                  (1)        ← root
                 /   \
              (2)     (3)
             /   \      \
          (4)    (5)    (6)  ← leaves are 4, 5, 6
```

Compared to a linked list, a tree is just "a linked list where each node has *more than one* `next` pointer." That single change unlocks an enormous design space — **and** is why every tree algorithm is recursion-shaped.

### 1.1 The vocabulary you must know

You will see these words in **every** tree problem:

| Term | Meaning | Example in the picture above |
|---|---|---|
| **Node** | A unit storing a value | (1), (2), … (6) |
| **Edge** | A connection between two nodes | (1)–(2), (2)–(4), … |
| **Root** | The single node with no parent | (1) |
| **Leaf** | A node with no children | (4), (5), (6) |
| **Internal node** | A non-leaf, non-root node | (2), (3) |
| **Parent** | The node directly above another | (2) is parent of (4) |
| **Child** | The node directly below another | (4) is child of (2) |
| **Sibling** | Two nodes with the same parent | (4) and (5) |
| **Ancestor** | Any node on the path up to the root | (2) and (1) are ancestors of (4) |
| **Descendant** | Any node on the path down from a node | (4), (5) are descendants of (2) |
| **Depth (of a node)** | Number of edges from root to that node | depth((4)) = 2 |
| **Height (of a node)** | Number of edges on the longest path *down* | height((1)) = 2, height((4)) = 0 |
| **Height (of a tree)** | Height of the root | 2 in the picture |
| **Level** | Set of nodes at the same depth | level 0 = {(1)}, level 1 = {(2),(3)} |
| **Subtree** | A node + all its descendants | subtree at (2) = {(2),(4),(5)} |
| **Degree** | Number of children of a node | deg((2)) = 2, deg((1)) = 2 |
| **Path** | Sequence of edges between two nodes | (4) → (2) → (1) → (3) |

!!! warning "Depth vs height — the off-by-one trap"
    **Depth counts down from the root, height counts up from the leaves.** The two go in opposite directions, but for the *same* node they need not be equal. They're *only* equal for the root and only when the tree is a single chain.

    A common bug: returning `1 + max(depth(left), depth(right))` when the question asked for **height** — they happen to share a recurrence, but **a single empty tree has height -1, not 0**, and it's easy to flip the base case.

### 1.2 Types of trees you'll meet

Don't memorize all of these — just know the names so you recognize them:

| Type | Defining property |
|---|---|
| **Binary tree** | Every node has at most 2 children (`left`, `right`). |
| **Full binary tree** | Every node has either 0 or 2 children — never 1. |
| **Complete binary tree** | All levels filled except possibly the last; last level fills left-to-right. |
| **Perfect binary tree** | All internal nodes have 2 children **and** all leaves are at the same level. |
| **Balanced binary tree** | For every node, `\|height(left) - height(right)\| ≤ 1`. |
| **Binary search tree (BST)** | For every node: all keys in left subtree `<` node `<` all keys in right subtree. |
| **Heap** | A complete binary tree with the heap order property (min or max at root). |
| **N-ary tree** | Each node can have any number of children, stored in a list. |
| **Trie (prefix tree)** | N-ary tree where edges are characters; words live on the paths. |
| **Segment tree / BIT** | Augmented binary tree for range queries — covered in the [advanced section](../../05-advanced/index.md). |

!!! info "The two definitions you'll actually use 90% of the time"
    For interviews, when someone says "tree" without qualification, they almost always mean **binary tree**. When they say "balanced tree," they mean **AVL or Red-Black** internally and **balanced binary tree** externally — the distinction rarely matters for problem-solving.

### 1.3 What a tree is *not*

- **Not a graph** — well, it *is* a graph, but with two extra rules: no cycles, and every node has exactly one parent (except the root). Every tree is a graph; not every graph is a tree.
- **Not always sorted** — a generic binary tree has *no* ordering. Only a **BST** is sorted, and only with respect to its specific ordering invariant.
- **Not always balanced** — without explicit rebalancing (AVL, Red-Black), a BST can degenerate into a linked list and lose its O(log n) guarantee.

---

## 2. Why we need trees

The pure abstraction looks simple. The patterns that fall out of it are what carry weight.

### 2.1 Hierarchies are everywhere

The DOM. The file system. JSON. XML. Org charts. Outline structures. Decision trees. Game move trees. Abstract syntax trees in compilers. **Anything that has a "contains" relationship is a tree** — and tree algorithms transfer wholesale to all of them.

### 2.2 Sorted lookup, insert, and delete in O(log n)

A **balanced BST** gives you all three in O(log n). That's better than a sorted array (O(n) insert) and better than a linked list (O(n) lookup). It's the main reason `std::map` in C++ and `TreeMap` in Java exist. (Python's standard library skips this — see §6.)

### 2.3 Range queries

"Sum of all values in [l, r]," "min of all values in [l, r]," "k-th smallest" — these are all O(log n) on the right tree. Segment trees and BITs are tree variants built specifically for this.

### 2.4 Prefix queries

A **trie** lets you find all words with a given prefix in time proportional to the *prefix length*, not the dictionary size. That's how autocompletes work.

### 2.5 Expression trees and parsing

`(3 + 4) * 5` becomes a tree where leaves are numbers and internal nodes are operators. Evaluating an expression is a postorder walk. Compilers, calculators, and SQL planners all do this.

### 2.6 Divide-and-conquer's natural shape

Many recursive algorithms — merge sort, quicksort, "build tree from preorder + inorder" — are *implicitly* operating on a tree of subproblems. Once you've internalised tree recursion, divide-and-conquer is the same skill in different clothes.

### 2.7 Tree DP — a huge interview category

"Find the diameter of the tree." "Find the path with maximum sum." "Maximum independent set on a tree." These are dynamic-programming-on-trees problems, and they're everywhere in product-company interviews.

---

## 3. How they work internally

### 3.1 The node-and-pointer model (the default)

Each node is a small struct holding a value and pointers to its children. Edges are not stored explicitly — they live as pointers.

```
class TreeNode:
    val:   <data>
    left:  TreeNode | None
    right: TreeNode | None
```

That's it. The whole tree is reachable from a single `root` reference. To "build" a tree you just allocate nodes and wire them up.

```
       (1)               TreeNode(1)
      /   \                /        \
   (2)    (3)        TreeNode(2)   TreeNode(3)
                         left=None right=None …
```

### 3.2 The array embedding (heap-style)

If the tree is **complete** (no gaps — see §1.2), you can pack it into an array and skip the pointers entirely.

The rule: for the node at index `i`,

- left child is at `2*i + 1`
- right child is at `2*i + 2`
- parent is at `(i - 1) // 2`

```
         (A)                          index 0
        /   \                          A
     (B)    (C)         array  →     [A, B, C, D, E, F]
     / \   /                            0  1  2  3  4  5
   (D)(E)(F)
```

This is the trick that makes `heapq` work. Pros: cache-friendly, no allocation per insert. Cons: only works for *complete* trees — gaps waste space.

### 3.3 Parent pointers (sometimes useful)

Add a `parent` pointer to each node and you can walk *upwards*. Costs an extra pointer per node, but lets you do things like "find lowest common ancestor without the root in hand." Many interview problems specifically *forbid* parent pointers to force the recursive solution.

### 3.4 The children-list model (n-ary trees)

For trees where the branching factor isn't 2:

```
class NaryNode:
    val:      <data>
    children: list[NaryNode]
```

A binary tree is just an n-ary tree restricted to `len(children) ≤ 2`. The traversal patterns are identical — substitute `for child in node.children:` for the explicit `node.left`/`node.right`.

### 3.5 Memory layout — why pointer-chasing is "slow"

Each `TreeNode` is a heap allocation. Walking a tree of 10 million nodes is 10 million potential cache misses. For most algorithmic problems we don't care, but in production you'll see **tree flatteners**, **B-trees** (one node per disk page, branching factor of hundreds), and **arena allocators** (all nodes in one contiguous slab) precisely to fix this.

### 3.6 The empty tree

By convention, an empty tree is `None`. Almost every tree algorithm has an `if not node: return ...` line as its base case. Forgetting it is the #1 source of `AttributeError: 'NoneType' object has no attribute 'left'` bugs.

---

## 4. Python implementations from scratch

### 4.1 `TreeNode` — the universal building block

The exact class LeetCode and most interviews use:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterator

@dataclass
class TreeNode:
    """A binary-tree node holding a value and up to two children.

    Attributes:
        val: The payload at this node. Any hashable type for BST work.
        left: Left child, or None.
        right: Right child, or None.
    """
    val: Any
    left:  TreeNode | None = None
    right: TreeNode | None = None
```

That's the entire data structure. Every algorithm in this chapter operates on it.

### 4.2 Building a tree from a level-order list (the LeetCode format)

LeetCode encodes trees as a level-order list with `None` for missing children — e.g. `[1, 2, 3, None, 4]` is

```
       1
      / \
     2   3
      \
       4
```

The decoder:

```python
from collections import deque

def build_tree(values: list[Any]) -> TreeNode | None:
    """Build a binary tree from a level-order list with None for gaps.

    >>> root = build_tree([1, 2, 3, None, 4])
    >>> root.val, root.left.val, root.left.right.val
    (1, 2, 4)
    """
    if not values or values[0] is None:
        return None

    root = TreeNode(values[0])
    queue: deque[TreeNode] = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        # Left child
        if i < len(values) and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        # Right child
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root
```

You'll use this in every test you write.

### 4.3 The four traversals — recursive

A traversal **visits every node exactly once**. The four canonical orders:

| Name | Order | Mnemonic |
|---|---|---|
| **Preorder** | Node → Left → Right | "the root comes first" |
| **Inorder** | Left → Node → Right | "in the middle" — gives sorted order on a BST |
| **Postorder** | Left → Right → Node | "the root comes last" — needed for "compute on subtrees first" |
| **Level-order** | Top to bottom, left to right | a.k.a. BFS |

```python
def preorder(node: TreeNode | None, out: list[Any]) -> None:
    """Preorder traversal: node, left, right."""
    if node is None:
        return
    out.append(node.val)         # visit
    preorder(node.left, out)     # recurse left
    preorder(node.right, out)    # recurse right


def inorder(node: TreeNode | None, out: list[Any]) -> None:
    """Inorder traversal: left, node, right.

    On a BST this yields keys in sorted order — a fact you'll use a lot.
    """
    if node is None:
        return
    inorder(node.left, out)
    out.append(node.val)
    inorder(node.right, out)


def postorder(node: TreeNode | None, out: list[Any]) -> None:
    """Postorder traversal: left, right, node.

    The shape of every "compute something from subtree results" algorithm.
    """
    if node is None:
        return
    postorder(node.left, out)
    postorder(node.right, out)
    out.append(node.val)
```

The structure of all three is **identical** — only the position of `out.append(node.val)` changes. That single line decides whether you're doing top-down, in-between, or bottom-up work.

!!! tip "The mental model that unlocks 90% of tree problems"
    - **Preorder** = "do work, then recurse" → top-down, **passing info down** (e.g. building a path from root).
    - **Postorder** = "recurse, then combine" → bottom-up, **collecting info up** (e.g. height, size, diameter).
    - **Inorder** = "recurse, visit, recurse" → only meaningful on BSTs, where it produces sorted order.

    When you see a new tree problem, the first question is: **does this need information from above (preorder) or from below (postorder)?**

### 4.4 The four traversals — iterative

Every recursive traversal can be rewritten with an explicit stack or queue. You should know these by heart — interviewers ask "now do it without recursion."

#### 4.4.1 Iterative preorder — the easy one

```python
def preorder_iter(root: TreeNode | None) -> list[Any]:
    """Iterative preorder using an explicit stack.

    Trick: push right first so left pops next (LIFO).
    """
    if root is None:
        return []
    out: list[Any] = []
    stack: list[TreeNode] = [root]
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right:                 # (1) push right FIRST
            stack.append(node.right)
        if node.left:                  # (2) push left LAST → pops first
            stack.append(node.left)
    return out
```

1. We want to visit `left` before `right`, but a stack is LIFO — so we push them in reverse.
2. The whole loop is `pop, visit, push children` — the canonical DFS shape.

#### 4.4.2 Iterative inorder — the sneaky one

```python
def inorder_iter(root: TreeNode | None) -> list[Any]:
    """Iterative inorder: walk left, then visit, then walk right's subtree."""
    out: list[Any] = []
    stack: list[TreeNode] = []
    node = root
    while node is not None or stack:
        # 1. Walk all the way left, pushing every ancestor.
        while node is not None:
            stack.append(node)
            node = node.left
        # 2. Pop the deepest unvisited ancestor, visit it.
        node = stack.pop()
        out.append(node.val)
        # 3. Move to its right subtree (which we'll then walk-left into).
        node = node.right
    return out
```

This pattern — the **two-loop walk** — is the prototype for many BST algorithms (validate BST, kth smallest, two-sum on BST).

#### 4.4.3 Iterative postorder — the hard one

```python
def postorder_iter(root: TreeNode | None) -> list[Any]:
    """Iterative postorder via the 'reversed preorder' trick.

    Strategy: do a preorder that visits node, RIGHT, LEFT — then reverse the output.
    That gives left-right-node order, which is postorder.
    """
    if root is None:
        return []
    out: list[Any] = []
    stack: list[TreeNode] = [root]
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.left:                  # left first → pops AFTER right
            stack.append(node.left)
        if node.right:                 # right first → pops first → giving "node, right, left"
            stack.append(node.right)
    out.reverse()                      # node-right-left → left-right-node
    return out
```

There's a "true" two-stack version that doesn't cheat with reverse, but in interviews this trick is fine and faster to code.

#### 4.4.4 Level-order (BFS)

```python
from collections import deque

def level_order(root: TreeNode | None) -> list[list[Any]]:
    """BFS — return a list of lists, one per level.

    Returns:
        [[level 0 vals], [level 1 vals], ...]
    """
    if root is None:
        return []
    out: list[list[Any]] = []
    q: deque[TreeNode] = deque([root])
    while q:
        level_size = len(q)            # snapshot — the loop must not see the kids we add this round
        level: list[Any] = []
        for _ in range(level_size):
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        out.append(level)
    return out
```

The `level_size = len(q)` snapshot is the single most important line in iterative BFS over trees. Without it, "for each level, do X" problems won't work.

### 4.5 A full `BinaryTree` class

Putting traversals on a class for ergonomic use:

```python
class BinaryTree:
    """A thin wrapper around a root TreeNode, exposing the four traversals."""

    def __init__(self, root: TreeNode | None = None) -> None:
        self.root = root

    @classmethod
    def from_list(cls, values: list[Any]) -> BinaryTree:
        return cls(build_tree(values))

    def preorder(self) -> list[Any]:
        out: list[Any] = []
        preorder(self.root, out)
        return out

    def inorder(self) -> list[Any]:
        out: list[Any] = []
        inorder(self.root, out)
        return out

    def postorder(self) -> list[Any]:
        out: list[Any] = []
        postorder(self.root, out)
        return out

    def level_order(self) -> list[list[Any]]:
        return level_order(self.root)

    def height(self) -> int:
        """Height in edges. Empty tree = -1, single node = 0."""
        def h(n: TreeNode | None) -> int:
            if n is None: return -1
            return 1 + max(h(n.left), h(n.right))
        return h(self.root)

    def size(self) -> int:
        def s(n: TreeNode | None) -> int:
            if n is None: return 0
            return 1 + s(n.left) + s(n.right)
        return s(self.root)
```

### 4.6 A `BST` from scratch (insert, search, delete)

A binary tree where the **BST invariant** holds: for every node, all left descendants are smaller and all right descendants are larger.

```python
class BST:
    """Unbalanced binary search tree — supports insert, search, delete.

    Note: with adversarial input (already-sorted insertions), this degenerates
    to a linked list and ops become O(n). Use sortedcontainers.SortedList in
    production. This class exists for educational and interview purposes.
    """

    def __init__(self) -> None:
        self.root: TreeNode | None = None

    # ---------- search ----------
    def search(self, key: Any) -> TreeNode | None:
        node = self.root
        while node is not None:
            if key == node.val:
                return node
            node = node.left if key < node.val else node.right
        return None

    # ---------- insert ----------
    def insert(self, key: Any) -> None:
        self.root = self._insert(self.root, key)

    def _insert(self, node: TreeNode | None, key: Any) -> TreeNode:
        if node is None:
            return TreeNode(key)
        if key < node.val:
            node.left = self._insert(node.left, key)
        elif key > node.val:
            node.right = self._insert(node.right, key)
        # key == node.val → no-op (we ignore duplicates here; some BSTs allow them)
        return node

    # ---------- delete (the tricky one) ----------
    def delete(self, key: Any) -> None:
        self.root = self._delete(self.root, key)

    def _delete(self, node: TreeNode | None, key: Any) -> TreeNode | None:
        if node is None:
            return None
        if key < node.val:
            node.left = self._delete(node.left, key)
        elif key > node.val:
            node.right = self._delete(node.right, key)
        else:
            # Found it. Three cases:
            if node.left is None:                  # (1) 0 or 1 child — splice
                return node.right
            if node.right is None:                 # (2) 1 child (other side) — splice
                return node.left
            # (3) 2 children — replace with in-order successor (smallest in right subtree).
            succ = node.right
            while succ.left is not None:
                succ = succ.left
            node.val = succ.val
            node.right = self._delete(node.right, succ.val)
        return node

    def inorder(self) -> list[Any]:
        out: list[Any] = []
        inorder(self.root, out)
        return out
```

The delete operation has three cases — leaf, one child, two children — and the two-child case is the only one that's interesting. The "in-order successor" trick (find the smallest key in the right subtree, copy it up, then delete it from the right subtree) preserves the BST invariant.

!!! warning "Why this BST is *unbalanced*"
    Insert `[1, 2, 3, 4, 5]` into a fresh BST and you get a right-leaning chain — every operation is O(n). Real BSTs (AVL, Red-Black) self-rebalance to keep height O(log n). Self-balancing trees are out of scope for this chapter — see the [Advanced section](../../05-advanced/index.md) once you're comfortable with the basics.

### 4.7 Pretty-printing a tree (for debugging)

You'll thank yourself later:

```python
def pretty_print(root: TreeNode | None) -> str:
    """Render a small binary tree as ASCII, for sanity checks."""
    if root is None:
        return "<empty>"

    def lines(node: TreeNode | None) -> tuple[list[str], int, int, int]:
        # Returns: (text-lines, total-width, root-position, height)
        if node is None:
            return [], 0, 0, 0
        label = str(node.val)
        L, lw, lp, lh = lines(node.left)
        R, rw, rp, rh = lines(node.right)
        # Width of this node's label
        sw = len(label)
        # First two lines: label and the / \
        first = " " * lp + " " * max(0, lw - lp) + label + " " * max(0, rp) + " " * (rw - rp)
        # ... full implementation is fiddly; this is enough to convey the idea.
        merged = []
        max_h = max(lh, rh)
        # (Simplified for brevity — production version aligns properly.)
        merged.append(label)
        for i in range(max_h):
            li = L[i] if i < len(L) else " " * lw
            ri = R[i] if i < len(R) else " " * rw
            merged.append(li + "  " + ri)
        return merged, lw + sw + rw + 2, lw + sw // 2, max_h + 1

    out, _, _, _ = lines(root)
    return "\n".join(out)
```

A nicer production-grade printer fits an entire blog post on its own. For most debugging, just `print(tree.level_order())` is enough.

---

## 5. Time & space complexity

The most important table in this chapter:

| Operation | Balanced binary tree | Skewed binary tree (worst case) | Notes |
|---|---|---|---|
| Search (general binary tree) | O(n) | O(n) | No order to exploit — must scan |
| Search (BST) | **O(log n)** | **O(n)** | The whole point of a BST — but only when balanced |
| Insert (BST) | O(log n) | O(n) | Same |
| Delete (BST) | O(log n) | O(n) | Same |
| Min / Max (BST) | O(log n) | O(n) | Walk all the way left / right |
| Inorder traversal | O(n) | O(n) | Always — every node once |
| Preorder / Postorder / BFS | O(n) | O(n) | Always |
| Build from sorted list (BST) | O(n) | — | If you build it balanced; see Problem 21 |
| Lowest Common Ancestor | O(n) | O(n) | O(log n) on a BST with the BST trick |

### 5.1 Why "balanced" matters so much

A balanced tree of n nodes has height O(log n). A skewed tree of n nodes has height O(n). Every BST operation is **O(height)** — so the difference is the difference between 20 ops and 1,000,000 ops on a million-element tree.

```
Balanced (height ≈ log n)        Skewed (height = n - 1)

         5                         1
       /   \                        \
      3     8                        2
     / \   / \                        \
    1   4 7   9                        3
                                        \
                                         4
                                          \
                                           5
```

A plain BST does **not** stay balanced on its own. AVL and Red-Black trees pay a small constant-factor overhead on insert/delete to guarantee log-n height forever. Most production "tree maps" are one of these two.

### 5.2 Space complexity

| Quantity | Value |
|---|---|
| Storing the tree itself | O(n) — one node per element |
| Recursive traversal stack | **O(h)** — the call stack is one frame per ancestor |
| Iterative traversal (DFS, explicit stack) | O(h) |
| Iterative traversal (BFS, queue) | O(w) where w is the **max width** of the tree |

`h` ranges from `log n` (balanced) to `n` (skewed). `w` ranges from `1` (skewed) to `n/2` (perfect tree's bottom level).

!!! info "BFS vs DFS — the space tradeoff"
    On a tall, thin tree, **DFS uses less memory** (h is small relative to w). On a wide, shallow tree, **BFS uses less memory** (w is small relative to h). For a fully balanced tree they're the same order — h ≈ log n, w ≈ n/2 — but BFS has the larger constant.

### 5.3 The recursion-depth trap (Python-specific)

Python's default recursion limit is **1000**. A skewed tree of 10000 nodes will crash a recursive traversal with `RecursionError`. Two fixes:

1. `sys.setrecursionlimit(10**6)` — quick and works in interviews.
2. Convert to iterative — what they actually want to see for "this needs to be production-grade."

---

## 6. Built-in Python tools

Python's standard library is **deliberately tree-poor**. There is *no built-in BST*. You're expected to use these:

### 6.1 `bisect` — sorted list as a poor-man's BST

If you only need ordered insert + lookup and don't care about iterator stability, `bisect.insort` on a list gives you O(log n) lookup and O(n) insert (because of the shift):

```python
import bisect

a: list[int] = []
bisect.insort(a, 5)        # O(n) insert
bisect.insort(a, 3)
bisect.insort(a, 7)
i = bisect.bisect_left(a, 5)   # O(log n) — index of first element ≥ 5
```

OK for ≤ 10⁴ elements. Above that, switch to `sortedcontainers`.

### 6.2 `sortedcontainers.SortedList` — the actual BST replacement

Third-party but widely available; the *de facto* "TreeMap" for Python interviews.

```python
from sortedcontainers import SortedList

sl = SortedList([5, 3, 7])
sl.add(4)                  # O(log n)
sl.remove(3)               # O(log n)
sl.bisect_left(5)          # O(log n)
sl[0]                      # smallest, O(log n)
sl[-1]                     # largest
```

Internally it's a list of lists (a B-tree-ish structure), not a binary tree, but the API matches BST expectations and the constants are excellent.

### 6.3 `heapq` — array-embedded min-heap

A heap is a tree (see §3.2). Python ships a min-heap on a list:

```python
import heapq

h: list[int] = []
heapq.heappush(h, 5)
heapq.heappush(h, 3)
heapq.heappop(h)           # returns 3 — the min
```

For max-heap: push negatives. For "k smallest / largest in stream": `heapq.nsmallest`, `heapq.nlargest`.

### 6.4 `xml.etree.ElementTree` and `html.parser` — real-world n-ary trees

Used for parsing XML/HTML. They're full n-ary trees with parent links and named children. Not interview material — but if you ever need to walk a real-world tree in Python, look here first.

### 6.5 What Python does *not* give you

| Want | Built-in? | Use instead |
|---|---|---|
| Self-balancing BST (TreeMap) | **No** | `sortedcontainers.SortedList` / `SortedDict` |
| Trie | No | Roll your own (Problem 38, or [Tries chapter](../../05-advanced/index.md)) |
| Segment tree / BIT | No | Roll your own |
| `BinaryTree` / `TreeNode` | No | Define a class — that's what we did in §4 |

The lack of a built-in BST is one of Python's most-felt absences for competitive coders coming from C++/Java.

---

## 7. When to use vs not use

The decision tree:

```
Need ordered traversal / range queries?
├─ Yes → BST / SortedList / SortedDict
│        (or segment tree if range *aggregates*)
└─ No
   ├─ Need O(1) point lookup by key?
   │  ├─ Yes → hash map (dict)
   │  └─ No
   │     ├─ Need top-k / smallest / priority order?
   │     │  └─ Yes → heap
   │     └─ Need prefix queries on strings?
   │        └─ Yes → trie
   └─ Have a hierarchical relationship?
      └─ Yes → tree (binary, n-ary, or general)
```

| Use a tree when… | Use something else when… |
|---|---|
| You need ordered iteration | You only need point lookups → **hash map** |
| Keys arrive in random order, ranges matter | Keys are dense small integers → **array** |
| The data is hierarchical by nature (DOM, FS) | The data is flat → list |
| Range queries (sum, min, max in [l, r]) | Single-key queries → hash map |
| Prefix queries / autocomplete | Substring match → KMP, suffix arrays |
| Top-k / streaming priority | Random access by index → list |

A practical rule: **if you find yourself reaching for a tree for "fast lookup," check if a hash map works first.** Hash maps win on every benchmark for point queries. Trees only beat them on *order-aware* operations.

---

## 8. Common mistakes & gotchas

### 8.1 Forgetting the `None` base case

```python
def height(node: TreeNode) -> int:
    return 1 + max(height(node.left), height(node.right))   # ❌ AttributeError on leaves
```

The fix is one line: `if node is None: return -1` (or `0`, depending on whether you measure in edges or nodes — be consistent).

### 8.2 Off-by-one on height vs depth

Pick a convention and stick to it. The two reasonable choices:

- **In edges**: empty tree = -1, single node = 0, two-level tree = 1.
- **In nodes**: empty tree = 0, single node = 1, two-level tree = 2.

LeetCode usually uses the *node* convention. Most textbooks use the *edge* convention. **Read the problem carefully.**

### 8.3 The "BST is sorted" fallacy

A BST is **not sorted in any traversal except inorder**. Pre/post/level orders give you *unsorted* sequences. If a problem says "validate BST given preorder," you need a different algorithm than "validate BST given inorder."

### 8.4 The "left.val < node.val" trap when validating a BST

```python
def is_bst(node: TreeNode | None) -> bool:
    if node is None:
        return True
    if node.left and node.left.val >= node.val:    # ❌ only checks immediate child
        return False
    if node.right and node.right.val <= node.val:
        return False
    return is_bst(node.left) and is_bst(node.right)
```

This passes a tree like `[5, 1, 8, None, None, 3, 9]` because `3 < 8`. But 3 is in the *right subtree of 5*, so it must be `> 5`. The fix: pass `(low, high)` bounds down (Problem 18).

### 8.5 Recursing into a sibling branch unnecessarily

The classic "Lowest Common Ancestor" mistake: continuing to recurse into the right subtree after both targets were found in the left. Use early returns.

### 8.6 BFS that loses the level boundary

```python
while q:
    node = q.popleft()
    if node.left:  q.append(node.left)
    if node.right: q.append(node.right)
```

This is BFS, but you can't tell which level any given node was on. To preserve levels, snapshot `len(q)` *before* the inner loop (see §4.4.4).

### 8.7 Using `list.pop(0)` for BFS

```python
q = [root]
while q:
    node = q.pop(0)         # ❌ O(n) per pop
```

Use `collections.deque`. `pop(0)` on a list is O(n) and silently turns your O(n) BFS into O(n²).

### 8.8 Mutating the tree during traversal

If you delete nodes while walking, you'll either re-visit nodes or skip them. Either traverse first into a list and then mutate, or use postorder so children are visited before their (about-to-be-mutated) parent.

### 8.9 Confusing "balanced" with "complete"

- **Complete**: every level full except possibly the last, which fills left-to-right. Heap shape.
- **Balanced**: heights of left/right subtrees differ by at most 1, recursively.
- **Perfect**: complete *and* full at the last level.

A complete tree is balanced. A balanced tree need not be complete. A perfect tree is both.

### 8.10 The "parent pointer" assumption

Most LeetCode `TreeNode` definitions do **not** include a parent pointer. If your algorithm needs one, either build a `child → parent` dict in a first pass, or restructure to avoid needing it.

### 8.11 Returning the wrong thing from helper recursion

A frequent bug: the outer function wants "the maximum path sum" but the recursive helper returns "the maximum path *ending at this node*." These are different. Use a closure variable (or `nonlocal`) to track the global answer while the helper returns the local one.

```python
def max_path_sum(root: TreeNode) -> int:
    best = float('-inf')

    def gain(n: TreeNode | None) -> int:
        nonlocal best
        if n is None:
            return 0
        L = max(0, gain(n.left))
        R = max(0, gain(n.right))
        best = max(best, n.val + L + R)     # path THROUGH n
        return n.val + max(L, R)            # path ENDING AT n

    gain(root)
    return best
```

### 8.12 Forgetting that two `TreeNode` objects with the same value are not equal

```python
TreeNode(5) == TreeNode(5)   # False — default __eq__ is identity
```

If you need value-equality, override `__eq__` and `__hash__`, or compare `node.val` directly.

---

## 9. Patterns this connects to

Trees are the unifying structure behind a huge slice of patterns. The big ones:

### 9.1 Top-down (preorder) recursion

You pass information **down** from parent to children. Examples: "all root-to-leaf paths," "path sum equals target," "build the path string as you go."

```python
def helper(node, info_from_above):
    if node is None: return
    info_here = combine(info_from_above, node.val)
    helper(node.left,  info_here)
    helper(node.right, info_here)
```

### 9.2 Bottom-up (postorder) recursion

You collect information **up** from children to parent. Examples: height, size, diameter, balanced-tree check, max path sum.

```python
def helper(node) -> SomeInfo:
    if node is None: return BASE_CASE
    L = helper(node.left)
    R = helper(node.right)
    return combine(L, R, node.val)
```

This is the more powerful of the two patterns and the one interviewers most love.

### 9.3 BFS / level-order

When the problem is "per level" (right-side view, level averages, zigzag, level minimum), BFS is the right hammer. The `len(q)` snapshot is non-negotiable.

### 9.4 Two-pointer / two-traversal

Some problems become trivial if you traverse the tree twice — once for setup, once for the answer. Examples: "find LCA without parent pointers" (one pass to compute parent, second to walk up), "diameter via two BFS" on n-ary trees.

### 9.5 Tree DP

Trees are a strict generalization of arrays for DP. The recurrence usually looks like

```
dp[node] = f(node.val, dp[left], dp[right])
```

Examples: house robber III, max path sum, longest path with constraints, count subtrees with property X.

### 9.6 Serialize / deserialize

Tree → string and back. Two common encodings: preorder with `null` sentinels, level-order with `null` sentinels. The "preorder with bounds" trick is also used for `is_valid_bst` and `recover BST from preorder`.

### 9.7 The "pass two values up" trick

When a single bottom-up return value isn't enough, return a **tuple**: `(local_answer, info_for_parent)`. The "is balanced" problem is the canonical example — you return `(is_balanced, height)` together.

### 9.8 LCA — three flavors

- **Generic binary tree**: postorder, return the node that "sees" both targets.
- **BST**: walk down once; the LCA is the first node whose value is between the two.
- **Tree with parent pointers**: jump up from both targets to a common depth, then walk together.

### 9.9 Morris traversal (O(1) space inorder)

A truly O(1) extra-space inorder using temporary "thread" pointers between predecessor and successor. Rarely needed in interviews but a beautiful trick worth knowing about — it's the only way to traverse without recursion *and* without an explicit stack.

---

## 10. Practice problems (40)

Each problem is presented in **5 layers**: brute force → cleaner → optimal → "what if?" follow-ups → real-world usage. Difficulty: 🟢 easy, 🟡 medium, 🔴 hard.

### Easy (1–10) — recursion warm-ups

#### Problem 1 — Maximum Depth of a Binary Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Apple</span> <span class="company-tag">Adobe</span>

> Given the root of a binary tree, return its maximum depth — the number of nodes on the longest root-to-leaf path.

##### 📖 Story Mode

You're standing at the founder of a family tree. You ask each of your children, *"how deep does your branch go?"* They each ask their own children the same question. When the youngest descendant — a leaf — is asked, they say `0`. Every ancestor adds **one** for themselves and reports back the **maximum** depth they got from any child. The number that bubbles up to you is the answer.

That recursion — *ask your children, take the max, add one* — is the canonical "postorder" pattern, and it solves a third of all tree problems.

##### 🌍 Real-World Usage

- **DOM rendering** — browsers compute the depth of the DOM tree to bound how expensive a selector match (`querySelectorAll(".x .y .z")`) can get.
- **JSON parsing** — `json.loads` raises `RecursionError` if a document is too deeply nested; libraries like `orjson` document a hard depth limit.
- **File systems** — `find -maxdepth N` literally implements this traversal to bound disk-walk cost.
- **Compiler ASTs** — many static analyzers reject ASTs deeper than some threshold to prevent stack-overflow attacks via crafted source files.

##### 🧠 Thinking Process

**Brute force:** BFS level by level, count the levels you see.

```
depth = 0
queue = [root]
while queue:
    depth += 1
    for each node currently in queue:
        replace it with its children
return depth
```

That's correct, but a tree problem usually has a cleaner *recursive* shape if the answer for a node is computable from the answers of its children. Here it is:

> `depth(node) = 1 + max(depth(left), depth(right))`, with `depth(None) = 0`.

That's a one-liner. The recursion *is* the algorithm.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force (BFS)"

    ```python
    from collections import deque

    def max_depth_bfs(root: TreeNode | None) -> int:
        if root is None:
            return 0
        q: deque[TreeNode] = deque([root])
        depth = 0
        while q:
            depth += 1
            for _ in range(len(q)):     # snapshot the level
                n = q.popleft()
                if n.left:  q.append(n.left)
                if n.right: q.append(n.right)
        return depth
    ```

    - **O(n) time**, **O(w) space** where w = max width of the tree.
    - Always works. Not the recursion-canonical answer, but the safest under "what if the tree has a million nodes and the recursion limit is too shallow?" follow-ups.

=== "Layer 2 — Recursive postorder"

    ```python
    def max_depth(root: TreeNode | None) -> int:
        if root is None:
            return 0
        return 1 + max(max_depth(root.left), max_depth(root.right))
    ```

    - **O(n) time**, **O(h) recursion stack** where h is the tree height.
    - This is what interviewers expect to see.

=== "Layer 3 — Edge-case-hardened"

    ```python
    def max_depth(root: TreeNode | None) -> int:
        if root is None:
            return 0
        # Short-circuit leaves explicitly — no extra recursive calls into None.
        if root.left is None and root.right is None:
            return 1
        return 1 + max(max_depth(root.left), max_depth(root.right))
    ```

    Functionally equivalent to Layer 2; the leaf check makes it ~2× faster on bushy trees by skipping two `max_depth(None)` calls per leaf.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def max_depth(root: TreeNode | None) -> int:
        """Return the maximum depth (number of nodes on longest root-to-leaf path).

        Args:
            root: The root of a binary tree, or None.

        Returns:
            0 if the tree is empty, otherwise the depth in nodes.

        Time:  O(n).  Each node is visited exactly once.
        Space: O(h).  Recursion stack; h ranges from log n (balanced) to n (skewed).

        Example:
            >>> root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4)))
            >>> max_depth(root)
            3
        """
        if root is None:
            return 0
        return 1 + max(max_depth(root.left), max_depth(root.right))
    ```

=== "Layer 5 — Iterative DFS (when recursion is unsafe)"

    ```python
    def max_depth_iter(root: TreeNode | None) -> int:
        if root is None:
            return 0
        stack: list[tuple[TreeNode, int]] = [(root, 1)]
        best = 0
        while stack:
            node, d = stack.pop()
            best = max(best, d)
            if node.left:  stack.append((node.left,  d + 1))
            if node.right: stack.append((node.right, d + 1))
        return best
    ```

    Use this when n is large enough that Python's default recursion limit (1000) would overflow on a skewed tree. **O(n)** time, **O(h)** explicit-stack space.

##### 🔍 Dry Run

Tree:

```
        1
       / \
      2   3
     /     \
    4       5
```

Recursion trace (Layer 2):

| call | left result | right result | returns |
|------|-------------|--------------|---------|
| `max_depth(4)` | 0 | 0 | 1 |
| `max_depth(2)` | 1 | 0 | 2 |
| `max_depth(5)` | 0 | 0 | 1 |
| `max_depth(3)` | 0 | 1 | 2 |
| `max_depth(1)` | 2 | 2 | **3** ✅ |

##### ⏱️ Complexity

- **Time: O(n)** — every node is visited once, constant work per node.
- **Space: O(h)** — recursion stack. Best case (balanced) `O(log n)`; worst case (skewed chain) `O(n)`.

##### 🎯 Pattern Used

**Postorder bottom-up recursion.** The shape: `f(node) = combine(f(left), f(right), node.val)`. Owns about a third of all tree problems — diameter, balanced check, height, max path sum, lowest common ancestor.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if you can't use recursion (Python stack limit)?"
    Use the iterative DFS in Layer 5, or BFS in Layer 1. Both are O(n) time and avoid Python's recursion limit. For very large inputs, BFS uses O(w) memory while DFS uses O(h) — pick whichever you expect to be smaller.

??? question "Follow-up 2 — What if the tree is n-ary instead of binary?"
    Replace `max(max_depth(left), max_depth(right))` with `max((max_depth(c) for c in node.children), default=0)`. Same O(n) cost.

??? question "Follow-up 3 — Return the *minimum* depth instead."
    See Problem 10 — there's a one-child trap that makes `min` non-symmetric with `max`.

??? question "Follow-up 4 — Return the deepest *leaf's value*, not the depth."
    Track a `(depth, value)` tuple from each subtree; pick the larger by depth, tie-break by left-most.

??? question "Follow-up 5 — Streaming: depth of an arbitrarily large tree on disk."
    Iterative DFS with depth on the stack — works in constant additional memory beyond the tree itself. Or do it as a single linear pass over a serialized preorder: depth = max running stack height.

##### 🐛 Common Bugs

1. **Returning `1` for `None`.** A null node contributes 0, not 1. Off-by-one on every result.
2. **Using `+` instead of `max`.** Returns the *number of nodes*, not the depth.
3. **Counting edges instead of nodes** when the spec asks for nodes (or vice versa). Read the problem twice.
4. **Hitting Python's recursion limit on a million-node skewed tree.** Switch to iterative DFS in Layer 5.
5. **Recursing into `None` then immediately returning** — fine, but doubles the function-call count. The Layer 3 leaf shortcut avoids this.

##### ✅ Edge Cases Checklist

- [ ] Empty tree (`root is None`) → `0`
- [ ] Single node → `1`
- [ ] Skewed left chain of n nodes → `n`
- [ ] Perfectly balanced tree of n nodes → `⌈log₂(n+1)⌉`
- [ ] Tree with only one child at every internal node → still `n`
- [ ] Negative values (irrelevant — depth is shape, not values)

##### 🏢 Sample Interviewer Quote

> *"Given a binary tree, return its maximum depth. Walk me through your approach."*

Your opener: *"Postorder recursion — the depth of a node is one plus the larger of its two children's depths, base case `None → 0`. O(n) time, O(h) stack. If h could be n, I'd switch to iterative DFS to dodge the Python recursion limit."*

---

#### Problem 2 — Same Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">LinkedIn</span>

> Given the roots `p` and `q` of two binary trees, return True if and only if they are **structurally identical** and the corresponding nodes have **equal values**.

##### 📖 Story Mode

You and a friend each draw a family tree. You want to know whether you drew **the same tree** — not just the same set of names, but the same shape, the same root, the same left-vs-right placement at every node. The simplest check: walk both trees in lockstep. At every step, if both pointers are null, fine. If one is null and the other isn't, they differ. If both have a node, the values must match and you must recurse into both pairs of children.

##### 🌍 Real-World Usage

- **React reconciliation** — when a component re-renders, React diffs the previous virtual DOM against the new one; the leaf check is essentially `same_tree`.
- **AST equality in compilers / linters** — two expressions are interchangeable iff their parse trees are identical (modulo positions).
- **Configuration drift detection** — comparing two snapshots of a config tree (Kubernetes manifests, JSON profiles) for byte-equivalent equality.
- **Deterministic build verification** — comparing two protobuf message trees built from different inputs to verify reproducibility.

##### 🧠 Thinking Process

The recurrence writes itself:

> `same(p, q)` is True iff `(p == q == None)`, **or** both are non-null **and** `p.val == q.val` **and** `same(p.left, q.left)` **and** `same(p.right, q.right)`.

The two `None` cases must be handled in this order — the `both None` short-circuit before the `one None` mismatch — otherwise you'll dereference a null.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Recursive (canonical)"

    ```python
    def same_tree(p: TreeNode | None, q: TreeNode | None) -> bool:
        if p is None and q is None:
            return True
        if p is None or q is None:
            return False
        return (p.val == q.val
                and same_tree(p.left,  q.left)
                and same_tree(p.right, q.right))
    ```

    - **O(n)** time (n = size of the smaller tree before mismatch), **O(h)** stack.
    - The first mismatch short-circuits the rest of the walk.

=== "Layer 2 — Iterative BFS lockstep"

    ```python
    from collections import deque

    def same_tree_bfs(p: TreeNode | None, q: TreeNode | None) -> bool:
        q_pairs: deque[tuple[TreeNode | None, TreeNode | None]] = deque([(p, q)])
        while q_pairs:
            a, b = q_pairs.popleft()
            if a is None and b is None:
                continue
            if a is None or b is None or a.val != b.val:
                return False
            q_pairs.append((a.left,  b.left))
            q_pairs.append((a.right, b.right))
        return True
    ```

    Same O(n)/O(w). Good fallback when recursion depth is dangerous.

=== "Layer 3 — Hash-based fast inequality"

    ```python
    def serialize(n: TreeNode | None) -> tuple:
        if n is None:
            return ()
        return (n.val, serialize(n.left), serialize(n.right))

    def same_tree_hash(p: TreeNode | None, q: TreeNode | None) -> bool:
        return serialize(p) == serialize(q)
    ```

    Same complexity, but **two passes** and tuple-allocation overhead. Useful in test harnesses where the serialized form is itself useful (golden-file comparisons). Don't bring this to an interview unless asked — Layer 1 is faster and shorter.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def same_tree(p: TreeNode | None, q: TreeNode | None) -> bool:
        """Return True iff two binary trees are structurally and value-wise identical.

        Args:
            p: Root of the first tree (may be None).
            q: Root of the second tree (may be None).

        Returns:
            True iff the trees have the same shape and the same values at every
            corresponding position.

        Time:  O(min(n_p, n_q)) on a mismatch, O(n) when equal.
        Space: O(h) recursion stack.
        """
        if p is None and q is None:
            return True
        if p is None or q is None:
            return False
        return (p.val == q.val
                and same_tree(p.left,  q.left)
                and same_tree(p.right, q.right))
    ```

=== "Layer 5 — Variants"

    **Variant A — same set of values, ignoring structure:** sort the inorder traversals and compare lists. **O(n log n)**, **O(n)** space.

    **Variant B — `same_tree` modulo a tolerance** (for floats): replace `p.val == q.val` with `abs(p.val - q.val) < eps`.

    **Variant C — `same_tree` modulo subtree swaps** (i.e., is one tree obtainable from the other by mirroring some subtrees?): at each node, accept either `(L↔L, R↔R)` or `(L↔R, R↔L)` as a match. See Problem 3 (Symmetric Tree) for the same-tree-against-its-own-mirror version.

##### 🔍 Dry Run

Trees:

```
   p:  1            q:  1
      / \              / \
     2   3            2   4   ← differs at right child
```

| call | check | result |
|------|-------|--------|
| `same_tree(p, q)` | both non-null, vals match (1 == 1) | recurse |
| `same_tree(p.left=2, q.left=2)` | both non-null, vals match | recurse |
| `same_tree(None, None)` × 2 | base | True |
| → returns True for left subtree |  |  |
| `same_tree(p.right=3, q.right=4)` | vals differ (3 ≠ 4) | **False** |
| → propagates up | → | **False** ✅ |

##### ⏱️ Complexity

- **Time: O(n)** at worst (full match); on a mismatch the walk short-circuits to O(depth-of-first-mismatch).
- **Space: O(h)** recursion stack.

##### 🎯 Pattern Used

**Lockstep recursion on two trees.** Same shape as `merge`, `is_subtree`, and `flip-equivalent trees`. The trick is the **two null cases** — both null is success, exactly one null is failure — and the `and` chain that short-circuits on the first false.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Iterative version (no recursion)."
    See Layer 2: BFS with a queue of pairs `(a, b)`.

??? question "Follow-up 2 — Are these two trees equal as multi-sets of values?"
    Compare sorted inorders. **O(n log n)**. Different problem — structure no longer matters.

??? question "Follow-up 3 — Is one tree a *subtree* of the other?"
    For each node `n` in the larger tree, check `same_tree(n, smaller.root)`. Naive O(n × m); can be sped up to O(n + m) by serializing both with null markers and using KMP / Z-function on the strings.

??? question "Follow-up 4 — Two trees with extra parent pointers — does that help?"
    No — equality doesn't need parent pointers. They'd help for *path-from-leaf* problems, not this one.

??? question "Follow-up 5 — How do you compare two trees stored on different machines?"
    Serialize both (preorder with null markers) and hash. If the hashes match, they're equal with overwhelming probability. To be sure, exchange and compare the serializations directly.

##### 🐛 Common Bugs

1. **Forgetting one of the null cases** — if you only check `p is None and q is None`, then `same_tree(None, node)` will dereference `q.val` and crash.
2. **Using `==` on the nodes themselves** — Python's default `==` compares by identity, not values, so two trees built independently always compare unequal.
3. **`or` instead of `and`** in the recursive return — produces "any matching subtree" semantics.
4. **Returning `True` early on first match** instead of *all* matches.
5. **Mutating one tree during traversal** in an attempt to mark visited nodes — unnecessary and breaks idempotency.

##### ✅ Edge Cases Checklist

- [ ] Both empty → `True`
- [ ] One empty, one with nodes → `False`
- [ ] Both single-node, same value → `True`
- [ ] Both single-node, different values → `False`
- [ ] Mirror images (same values, swapped left/right) → `False` (this is Problem 3, not 2)
- [ ] Same shape, different values at exactly one leaf → `False`
- [ ] Trees with `None` values in nodes (where allowed) — treat `None == None` as match, not as missing-node

##### 🏢 Sample Interviewer Quote

> *"Determine if two binary trees are the same."*

Your opener: *"Lockstep recursion. If both nodes are null, match. If exactly one is null, mismatch. Otherwise compare values and recurse on left and right pairs. O(n), O(h)."*

---

#### Problem 3 — Symmetric Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree, return True if it is a mirror of itself — its left subtree is a mirror image of its right subtree.

##### 📖 Story Mode

Picture the tree on a sheet of paper, then fold the paper down the middle along the root's vertical axis. If every node on the left lands exactly on a node of the same value on the right, the tree is symmetric. The check is the **two-pointer "lockstep"** version of Problem 2, but the *cross-recursion* changes: compare `left.left ↔ right.right` and `left.right ↔ right.left`.

##### 🌍 Real-World Usage

- **Layout engines** — checking if a UI tree is mirror-symmetric to apply RTL transformations.
- **Bioinformatics** — palindromic structure detection in branched RNA / DNA fold-back patterns.
- **Compiler equality of mirrored expressions** — `(a + b) * c` vs `c * (b + a)` modulo commutativity.
- **Game state symmetry pruning** — chess/Go endgame solvers detect symmetric board positions to halve the search space.

##### 🧠 Thinking Process

Symmetry is a relation between **two pointers** walking the tree in mirror directions. Define:

> `mirror(a, b)` ⇔ same null-ness; same value if both non-null; **and** `mirror(a.left, b.right)` and `mirror(a.right, b.left)`.

Then `is_symmetric(root) = root is None or mirror(root.left, root.right)`.

Notice the cross-pairing — that's the only difference from Problem 2.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Mirror-and-compare (naïve)"

    ```python
    def is_symmetric_naive(root: TreeNode | None) -> bool:
        def clone_mirror(n: TreeNode | None) -> TreeNode | None:
            if n is None:
                return None
            return TreeNode(n.val, clone_mirror(n.right), clone_mirror(n.left))

        return same_tree(root, clone_mirror(root))
    ```

    Correct, but allocates a full mirror tree. **O(n)** time, **O(n)** extra space. Don't ship — but mention it as the "obvious" approach in an interview.

=== "Layer 2 — Cross-recursion (canonical)"

    ```python
    def is_symmetric(root: TreeNode | None) -> bool:
        def mirror(a: TreeNode | None, b: TreeNode | None) -> bool:
            if a is None and b is None:
                return True
            if a is None or b is None:
                return False
            return (a.val == b.val
                    and mirror(a.left,  b.right)
                    and mirror(a.right, b.left))

        return root is None or mirror(root.left, root.right)
    ```

    **O(n)**, **O(h)**. The interview answer.

=== "Layer 3 — Iterative BFS with paired queue"

    ```python
    from collections import deque

    def is_symmetric_bfs(root: TreeNode | None) -> bool:
        if root is None:
            return True
        q: deque[tuple[TreeNode | None, TreeNode | None]] = deque(
            [(root.left, root.right)]
        )
        while q:
            a, b = q.popleft()
            if a is None and b is None:
                continue
            if a is None or b is None or a.val != b.val:
                return False
            q.append((a.left,  b.right))
            q.append((a.right, b.left))
        return True
    ```

    Same complexity, dodges Python's recursion limit. Note the **mirrored append order**.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def is_symmetric(root: TreeNode | None) -> bool:
        """Return True iff the binary tree is mirror-symmetric.

        Args:
            root: Root of the tree (or None).

        Returns:
            True if the left and right subtrees are mirror images.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        if root is None:
            return True

        def mirror(a: TreeNode | None, b: TreeNode | None) -> bool:
            if a is None and b is None:
                return True
            if a is None or b is None:
                return False
            return (a.val == b.val
                    and mirror(a.left,  b.right)
                    and mirror(a.right, b.left))

        return mirror(root.left, root.right)
    ```

=== "Layer 5 — Variants"

    **Variant A — flip-equivalent trees:** two trees are "flip-equivalent" if you can flip any number of subtree pairs to make them equal. At each node accept either same-side or cross-side match. See LeetCode 951.

    **Variant B — "is the tree symmetric ignoring values, only shape?"** Drop the `a.val == b.val` clause.

    **Variant C — symmetric n-ary tree** with children list — a node's children list, reversed, must equal the partner's children list (then recurse pairwise).

##### 🔍 Dry Run

Tree:

```
        1
       / \
      2   2
     / \ / \
    3  4 4  3
```

| call | a, b | check | recurse |
|------|------|-------|---------|
| `mirror(2, 2)` | both non-null, 2 == 2 | proceed | `(3, 3)` and `(4, 4)` |
| `mirror(3, 3)` | match leaves | True | — |
| `mirror(4, 4)` | match leaves | True | — |
| `is_symmetric` returns | | | **True** ✅ |

Asymmetric counter-example:

```
        1
       / \
      2   2
       \   \
        3   3   ← left has right-only child, right also right-only — not mirror
```

`mirror(2.left=None, 2.right=3)` → one is null, one isn't → **False**.

##### ⏱️ Complexity

- **Time: O(n)** — every node visited once across both subtrees.
- **Space: O(h)** recursion stack.

##### 🎯 Pattern Used

**Two-pointer cross-recursion.** Whenever a problem says "mirror," "reflection," or "flip the orientation," the answer is `recurse(a.left, b.right)` paired with `recurse(a.right, b.left)`.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Iterative?"
    Layer 3. Mirror-paired queue.

??? question "Follow-up 2 — Symmetric *modulo* values (only shape)?"
    Drop the value comparison; keep the structural check.

??? question "Follow-up 3 — Symmetric across an *arbitrary* axis (some internal node)?"
    Run `mirror(node.left, node.right)` at every node and OR the results. **O(n²)** naive; can be cut with hashing of subtree shapes.

??? question "Follow-up 4 — Largest mirror-symmetric subtree?"
    Postorder, return `(is_mirror, size)`; track best size globally.

??? question "Follow-up 5 — Why is the recursion `mirror(a.left, b.right)` and not `mirror(a.left, b.left)`?"
    Because we're comparing one tree's left to the other tree's *right*. Same-side comparison is for the `same_tree` problem; cross-side is what makes this *mirror*.

##### 🐛 Common Bugs

1. **Calling `same_tree(root.left, root.right)` instead of `mirror(...)`** — gets `[1, 2, 3, 4, 4, 3]` wrong because that tree has same-shape subtrees but they're not *mirror* images.
2. **Iterative version with non-mirrored append order** — `q.append((a.left, b.left)); q.append((a.right, b.right))` checks same-tree, not symmetry.
3. **Forgetting the empty-tree case** — `mirror(root.left, root.right)` would crash on `root is None`.
4. **Pre-mutation:** if you reverse one subtree in place to "make the comparison easier," you've modified the input — bad form, and dangerous if the tree is shared.
5. **Comparing `repr(left) == repr(right_reversed)`** — shapes can collide.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `True`
- [ ] Single node → `True`
- [ ] Two nodes (root + left only) → `False`
- [ ] Mirror leaves with equal values → `True`
- [ ] Mirror shape but unequal values somewhere → `False`
- [ ] Skewed tree of depth h, single side only → `False`
- [ ] Tree where every internal node has the *same* value (e.g., all 1s) — symmetry depends purely on shape

##### 🏢 Sample Interviewer Quote

> *"Given the root of a binary tree, check whether it is a mirror of itself."*

Your opener: *"Define `mirror(a, b)`: same null-ness; same value; recurse on the cross-paired children — `a.left ↔ b.right` and `a.right ↔ b.left`. Call `mirror(root.left, root.right)`. O(n), O(h). I can also give you the iterative BFS variant with a paired queue."*

---

#### Problem 4 — Invert Binary Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Apple</span>

> Given the root of a binary tree, mirror it: swap the left and right children at every node, then return the root.

##### 📖 Story Mode

You're holding the tree by the root and you flip every horizontal "fork" so the children swap sides. Recursively. This problem is famous because **Max Howell** — author of Homebrew — was once rejected by Google after struggling to invert a binary tree on the whiteboard. He tweeted about it; the tweet went viral; and now this problem is permanently the meme that says, *"Yes, you actually do need to know recursion."*

The actual algorithm is two lines.

##### 🌍 Real-World Usage

- **RTL UI rendering** — flipping a layout tree for right-to-left languages is exactly this.
- **Game state symmetry** — chess engines invert positions to reuse evaluation tables for white-to-move vs black-to-move.
- **Differentiable trees** in ML — gradient flow through tree-structured networks sometimes requires walking children in reversed order.
- **AST refactoring** — swapping `if-else` branches when negating a condition is `invert` of a 2-child node.

##### 🧠 Thinking Process

The recurrence is trivial:

> `invert(node) = swap(invert(left), invert(right))`, base case `invert(None) = None`.

You can also invert via BFS — pop a node from the queue, swap its children, push them. Same complexity. The recursive version is so short it's almost a koan.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Recursive (postorder swap)"

    ```python
    def invert(root: TreeNode | None) -> TreeNode | None:
        if root is None:
            return None
        root.left, root.right = invert(root.right), invert(root.left)
        return root
    ```

    - **O(n) time**, **O(h) stack**.
    - Mutates the input. Tuple-assignment matters: `root.left = invert(root.right)` followed by `root.right = invert(root.left)` would be wrong because the second call sees the *already-overwritten* `root.left`.

=== "Layer 2 — Pre-order swap (also valid)"

    ```python
    def invert(root: TreeNode | None) -> TreeNode | None:
        if root is None:
            return None
        root.left, root.right = root.right, root.left
        invert(root.left)
        invert(root.right)
        return root
    ```

    Functionally equivalent. Some interviewers prefer this because the swap happens "on entry," making the order of recursive calls obviously irrelevant.

=== "Layer 3 — Iterative BFS"

    ```python
    from collections import deque

    def invert_bfs(root: TreeNode | None) -> TreeNode | None:
        if root is None:
            return None
        q: deque[TreeNode] = deque([root])
        while q:
            n = q.popleft()
            n.left, n.right = n.right, n.left
            if n.left:  q.append(n.left)
            if n.right: q.append(n.right)
        return root
    ```

    Pull this out when asked "what if recursion would overflow on a million-deep skewed tree?"

=== "Layer 4 — Production-ready (no mutation)"

    ```python
    from __future__ import annotations


    def inverted(root: TreeNode | None) -> TreeNode | None:
        """Return a *new* tree that is the mirror image of `root`.

        The input is not mutated.

        Args:
            root: Root of the source tree.

        Returns:
            Root of a freshly allocated mirror tree, or None if the input is None.

        Time:  O(n).
        Space: O(n) — every node is duplicated.
        """
        if root is None:
            return None
        return TreeNode(root.val, inverted(root.right), inverted(root.left))
    ```

    Use this in a context where the caller still holds the original — tests, undo stacks, audit logs.

=== "Layer 5 — N-ary variant"

    ```python
    def invert_nary(root: NaryNode | None) -> NaryNode | None:
        if root is None:
            return None
        root.children = [invert_nary(c) for c in reversed(root.children)]
        return root
    ```

    Same shape, generalized children list.

##### 🔍 Dry Run

Tree:

```
   Before:        After:
       4              4
      / \            / \
     2   7          7   2
    / \ / \        / \ / \
   1  3 6  9      9  6 3  1
```

Recursion (Layer 1):

| call | left was | right was | after swap |
|------|----------|-----------|------------|
| `invert(2)` returns subtree | (1, 3) | swapped to (3, 1) |
| `invert(7)` returns subtree | (6, 9) | swapped to (9, 6) |
| `invert(4)` swaps `(2-subtree, 7-subtree)` | (now-2, now-7) | becomes `(now-7, now-2)` |
| return root |  |  | mirrored ✅ |

##### ⏱️ Complexity

- **Time: O(n)** — every node is visited and its two pointers swapped.
- **Space: O(h)** for recursion (or **O(w)** for the BFS variant).

##### 🎯 Pattern Used

**In-place tree mutation via recursion.** The "swap then recurse" / "recurse then swap" duality applies to many in-place tree transforms (e.g., serialize-modify-deserialize pipelines).

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Without mutating the input."
    Layer 4: allocate new nodes. O(n) extra space.

??? question "Follow-up 2 — Iterative."
    Layer 3: BFS or a DFS stack.

??? question "Follow-up 3 — On an n-ary tree."
    Layer 5: reverse the children list.

??? question "Follow-up 4 — What's the relationship between `invert` and `is_symmetric`?"
    A tree is symmetric iff `same_tree(root, invert(clone(root)))`. They're dual problems.

??? question "Follow-up 5 — Inverse of `invert`?"
    `invert` is its own inverse — applying it twice yields the original. (It's an involution.)

##### 🐛 Common Bugs

1. **Sequential assignment instead of tuple-swap** — `root.left = invert(root.right); root.right = invert(root.left)` walks the *new* `root.left` (which is the old right), inverting it again, ending with both children equal to a doubly-inverted subtree. Tuple-swap captures both values before either is written.
2. **Returning `None` after mutating in place** — caller loses the root.
3. **Recursing only on the left after swap** — half the tree never gets inverted.
4. **Treating `invert` as `clone` accidentally** — allocating new nodes unnecessarily.
5. **Inverting a BST and expecting it to remain a BST** — no, the inverted tree breaks the BST invariant entirely.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → returns `None`
- [ ] Single node → returns the same node, unchanged
- [ ] Tree with only left children → becomes a right-only chain
- [ ] Tree with only right children → becomes a left-only chain
- [ ] Already symmetric tree → still symmetric after inversion
- [ ] Tree shared with another caller — mutation surprise (use Layer 4 instead)

##### 🏢 Sample Interviewer Quote

> *"Invert a binary tree."*

Your opener: *"Two-line recursion: swap children, recurse on both. O(n), O(h). The tuple-assignment matters — sequential writes would clobber the second swap. I can also do iterative BFS if recursion is risky, or a non-mutating clone-and-mirror if the input must stay intact."*

---

#### Problem 5 — Diameter of Binary Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Uber</span>

> Given the root of a binary tree, return the length of the longest path between any two nodes — the **diameter**, measured in **edges**. The path may or may not pass through the root.

##### 📖 Story Mode

Imagine you're tracing the longest possible "walk" through the tree, allowed to go up and over but never visiting any edge twice. For every node `n`, the longest walk that passes through `n` has length `height(n.left) + height(n.right)` — go down one side as far as possible, return through `n`, and go down the other side. The diameter is the **maximum** of that over every node.

The trap: there are two things to compute at each node — the *height* (returned to the parent) and the *diameter through me* (a global maximum). One recursion, two values.

##### 🌍 Real-World Usage

- **Build graphs** — longest dependency chain in a Bazel/Make graph determines the *critical path* of a build.
- **Forum threading** — longest reply chain in a comment tree (the Reddit/Hacker News "deepest thread") is essentially a diameter on a tree of replies.
- **Network topology** — longest shortest-path between any two routers in a tree-shaped network defines the **diameter of the network**.
- **Phylogenetic distance** — the maximum evolutionary distance between two species in a phylogenetic tree.

##### 🧠 Thinking Process

**Brute force:** at every node compute `height(left) + height(right)`, take the max. But `height` recurses fully each time, so it's **O(n²)**.

**The insight:** while computing `height(n)` postorder, we already know `height(n.left)` and `height(n.right)` — for free. Track the running best as a side effect of the height computation.

**Pattern:** "**postorder with a side-channel maximum.**" Used everywhere: max path sum, longest univalue path, longest ZigZag path.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force"

    ```python
    def diameter_brute(root: TreeNode | None) -> int:
        def height(n: TreeNode | None) -> int:
            if n is None:
                return 0
            return 1 + max(height(n.left), height(n.right))

        if root is None:
            return 0

        best = 0
        # Walk every node and compute the through-diameter.
        def walk(n: TreeNode | None) -> None:
            nonlocal best
            if n is None:
                return
            best = max(best, height(n.left) + height(n.right))
            walk(n.left)
            walk(n.right)

        walk(root)
        return best
    ```

    **O(n²)** time (height re-computed at every node), **O(h)** stack.

=== "Layer 2 — Single pass with closure"

    ```python
    def diameter(root: TreeNode | None) -> int:
        best = 0

        def height(n: TreeNode | None) -> int:
            nonlocal best
            if n is None:
                return 0
            L = height(n.left)
            R = height(n.right)
            best = max(best, L + R)        # diameter THROUGH n (in edges)
            return 1 + max(L, R)           # height of n (in nodes)

        height(root)
        return best
    ```

    **O(n)**, **O(h)**. The interview answer.

=== "Layer 3 — Edge-case-hardened"

    ```python
    def diameter(root: TreeNode | None) -> int:
        if root is None:
            return 0

        best = [0]   # use a list to avoid `nonlocal` if you prefer

        def height(n: TreeNode | None) -> int:
            if n is None:
                return 0
            L = height(n.left)
            R = height(n.right)
            if L + R > best[0]:
                best[0] = L + R
            return 1 + max(L, R)

        height(root)
        return best[0]
    ```

    Same complexity. The list-trick avoids `nonlocal` if you're tutoring someone unfamiliar with closures, or in environments where `nonlocal` is unavailable.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def diameter(root: TreeNode | None) -> int:
        """Length of the longest path (in edges) between any two nodes.

        Args:
            root: Root of the binary tree.

        Returns:
            0 for the empty tree or a single node, otherwise the count of
            edges on the longest path.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        best = 0

        def height(n: TreeNode | None) -> int:
            nonlocal best
            if n is None:
                return 0
            L = height(n.left)
            R = height(n.right)
            best = max(best, L + R)
            return 1 + max(L, R)

        height(root)
        return best
    ```

=== "Layer 5 — Variants"

    **Variant A — return the path itself**, not just the length: each `height` call returns `(depth, deepest_node)`; track `(left_deepest, right_deepest)` whenever a new best is found. The diameter path is `left_deepest → … → n → … → right_deepest`.

    **Variant B — weighted edges:** add the edge weights into the height return: `return weight(n, child) + height(child)`. The diameter is `L + R` where each is a *weighted* depth.

    **Variant C — n-ary tree:** the through-diameter is the **sum of the two largest** child heights. Use a small heap or a running top-2.

    **Variant D — diameter of an arbitrary undirected graph:** if the graph is a tree, run BFS from any node to find the farthest node `u`, then BFS from `u` to find the farthest node `v`. `dist(u, v)` is the diameter. **O(n)**.

##### 🔍 Dry Run

Tree:

```
        1
       / \
      2   3
     / \
    4   5
```

| node | L | R | L+R (through-diameter) | best after | returns height |
|------|---|---|------------------------|-----------|---------------|
| 4 | 0 | 0 | 0 | 0 | 1 |
| 5 | 0 | 0 | 0 | 0 | 1 |
| 2 | 1 | 1 | 2 | 2 | 2 |
| 3 | 0 | 0 | 0 | 2 | 1 |
| 1 | 2 | 1 | 3 | **3** | 3 |

Answer: **3** (path: 4 → 2 → 1 → 3 or 5 → 2 → 1 → 3, both 3 edges) ✅

##### ⏱️ Complexity

- **Time: O(n)** — each node touched once.
- **Space: O(h)** recursion stack.

##### 🎯 Pattern Used

**Postorder with side-channel maximum.** Whenever a problem asks for "the best [thing] over all nodes" but each node's contribution is computable from its children's heights/sums/lengths, this is the shape:

```
def helper(n):
    if not n: return 0
    L = helper(n.left)
    R = helper(n.right)
    update(global_best, combine_through_n(L, R))
    return upward_value(L, R, n)
```

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why does the answer involve `L + R` not `1 + L + R`?"
    The diameter is in **edges**, not nodes. `L` is the height of the left subtree in nodes (counting the children, not the root edge); the edge from root-to-left and root-to-right are counted *inside* `L` and `R`. Some textbooks define diameter in nodes — read the spec.

??? question "Follow-up 2 — Why doesn't the diameter need to pass through the root?"
    Because the longest path might lie entirely in one subtree (e.g., a tree where the left subtree is a long chain and the right is a leaf). The recursion handles this because we update `best` at *every* node, not just at the root.

??? question "Follow-up 3 — Diameter of a general (cyclic) graph?"
    NP-hard for general graphs (it's the longest path problem). On trees, it's O(n) via two BFS passes.

??? question "Follow-up 4 — Print the actual diameter path."
    Variant A above: return the deepest node along with the depth, then reconstruct.

??? question "Follow-up 5 — What if the tree is enormous and recursion overflows?"
    Use an explicit stack and emulate postorder. Each node's two child heights become available in the postorder visit; update best then.

##### 🐛 Common Bugs

1. **Returning `1 + L + R`** — that's the *number of nodes* on the path, off by one from edges.
2. **Updating `best` only at the root** — misses any diameter that doesn't pass through the root.
3. **Forgetting the empty-tree case** — `diameter(None)` should be 0, not error.
4. **Recomputing `height` per node (Layer 1)** — accidentally O(n²). Always combine with the postorder.
5. **Confusing `max(L, R)` (height) with `L + R` (through-diameter)** — the recursive return is `1 + max(L, R)`; the global update is `L + R`.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0
- [ ] Single node → 0 (no edges)
- [ ] Two nodes (root + one child) → 1
- [ ] Linear chain of n nodes → n − 1
- [ ] Balanced perfect tree of height h → 2 × h
- [ ] Diameter entirely in one subtree (no through-root case) — handled by per-node update

##### 🏢 Sample Interviewer Quote

> *"Find the diameter of a binary tree."*

Your opener: *"Postorder. At each node, recursive `height(left)` and `height(right)`, update a running max with `L + R` for the diameter through this node, then return `1 + max(L, R)` upward as my own height. O(n), O(h). I'll use a closure for the running max."*

---

#### Problem 6 — Balanced Binary Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Meta</span> <span class="company-tag">Apple</span>

> Given a binary tree, determine if it is **height-balanced**: for every node, the heights of the two subtrees differ by at most 1.

##### 📖 Story Mode

Imagine a Jenga tower where each block sits on the previous one. If at any node, one side of the tower is far taller than the other, the whole structure tilts — and worse, BST operations on it degenerate to O(n). Self-balancing trees (AVL, Red-Black, B-trees) all enforce this exact "no level differs by more than 1" property at every node.

##### 🌍 Real-World Usage

- **AVL trees** — balance factor at every node is in `{-1, 0, +1}`; rotations restore it.
- **Database indexes** — B-tree balance is *the* reason a billion-row index lookup is fast.
- **Filesystem trees** — balanced directory structures keep `lookup` constant in practice.
- **Spatial trees (k-d, R-trees)** — re-balance on insert/delete to preserve query performance.

##### 🧠 Thinking Process

The brute force is "for every node, compute height of left and right, compare." That's **O(n²)** — height is recomputed at every level.

**The insight:** while computing the height of a subtree, we already know whether *its* subtrees are balanced. Combine the height computation with a balanced-flag — return `(height, is_balanced)` from each recursive call. **O(n)**.

A neater encoding: use `-1` as a sentinel for "this subtree is unbalanced." Any non-negative return is the height. The recursion bails early once it sees `-1`.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force"

    ```python
    def is_balanced_brute(root: TreeNode | None) -> bool:
        def height(n: TreeNode | None) -> int:
            if n is None:
                return 0
            return 1 + max(height(n.left), height(n.right))

        if root is None:
            return True
        if abs(height(root.left) - height(root.right)) > 1:
            return False
        return is_balanced_brute(root.left) and is_balanced_brute(root.right)
    ```

    **O(n²)**. Correct, but heights are recomputed.

=== "Layer 2 — Tuple return (height, balanced)"

    ```python
    def is_balanced(root: TreeNode | None) -> bool:
        def check(n: TreeNode | None) -> tuple[bool, int]:
            if n is None:
                return True, 0
            ok_l, hL = check(n.left)
            if not ok_l:
                return False, 0
            ok_r, hR = check(n.right)
            if not ok_r:
                return False, 0
            return abs(hL - hR) <= 1, 1 + max(hL, hR)

        return check(root)[0]
    ```

    **O(n)**, **O(h)**. Clean and explicit.

=== "Layer 3 — Sentinel −1 trick"

    ```python
    def is_balanced(root: TreeNode | None) -> bool:
        def height_or_neg1(n: TreeNode | None) -> int:
            if n is None:
                return 0
            L = height_or_neg1(n.left)
            if L == -1:
                return -1
            R = height_or_neg1(n.right)
            if R == -1 or abs(L - R) > 1:
                return -1
            return 1 + max(L, R)

        return height_or_neg1(root) != -1
    ```

    Same complexity, single-value return. Reads as "height, but signaling failure." Common idiom in C/C++ tree code.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def is_balanced(root: TreeNode | None) -> bool:
        """Return True iff the tree is height-balanced.

        A tree is height-balanced if, for every node, the heights of its left
        and right subtrees differ by at most 1.

        Args:
            root: Root of the tree (may be None).

        Returns:
            True for an empty tree, otherwise the balance check.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        def check(n: TreeNode | None) -> int:
            """Return height, or -1 if any subtree is unbalanced."""
            if n is None:
                return 0
            L = check(n.left)
            if L == -1:
                return -1
            R = check(n.right)
            if R == -1 or abs(L - R) > 1:
                return -1
            return 1 + max(L, R)

        return check(root) != -1
    ```

=== "Layer 5 — Variants"

    **Variant A — return the imbalance factor**: the maximum `|hL − hR|` over all nodes. Useful for "how unbalanced is this tree?" telemetry.

    **Variant B — strict balance (perfect tree)**: every internal node has two children, all leaves at the same depth. Different (stricter) recurrence.

    **Variant C — weight balance (size-balanced)**: subtree *node counts*, not heights, must differ by ≤ a factor (e.g., 2× as in scapegoat trees). Replace heights with sizes.

    **Variant D — list the offending nodes**: collect the nodes where the imbalance is detected; useful for debugging or visualizing tree health.

##### 🔍 Dry Run

Balanced tree:

```
        3
       / \
      9   20
         /  \
        15   7
```

| node | L (height) | R | abs(L−R) | balanced? | returns |
|------|------------|---|----------|-----------|---------|
| 9 | 0 | 0 | 0 | ✓ | (T, 1) |
| 15 | 0 | 0 | 0 | ✓ | (T, 1) |
| 7 | 0 | 0 | 0 | ✓ | (T, 1) |
| 20 | 1 | 1 | 0 | ✓ | (T, 2) |
| 3 | 1 | 2 | 1 | ✓ | (T, 3) |

Answer: **True** ✅

Unbalanced tree:

```
       1
      /
     2
    /
   3
```

`check(2)` returns `(True, 2)` (L=0, R=0, but recursion gives left=1, right=0). `check(1)`: L=2, R=0, abs=2 > 1 → returns `(False, ...)` — propagates. Answer: **False**.

##### ⏱️ Complexity

- **Time: O(n)** for Layers 2–4; **O(n²)** for Layer 1.
- **Space: O(h)** recursion stack.

##### 🎯 Pattern Used

**Postorder return-tuple.** Same shape as Diameter: each recursive call returns a per-node summary (height + flag), the caller combines and short-circuits on failure.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why is the brute O(n²)?"
    `height` is called at every node, and each `height` call is O(subtree-size). Summed over a balanced tree, that's `n + n/2 × 2 + n/4 × 4 + ... = n log n`. On a skewed tree, it's quadratic.

??? question "Follow-up 2 — How does AVL maintain this property?"
    On every insert/delete, the affected ancestors are checked; rotations (single-left, single-right, double) restore the balance factor without rebuilding the tree.

??? question "Follow-up 3 — Is balance the same as 'BST-ness'?"
    No. Balance is a *shape* property (heights). BST-ness is a *value* property (left ≤ node ≤ right). A tree can be balanced and not a BST, BST and not balanced, both, or neither.

??? question "Follow-up 4 — What if the tree has 10 million nodes and is a chain?"
    Recursion overflows. Use an iterative postorder with a stack — same algorithm, no stack frames.

??? question "Follow-up 5 — Strict balance (perfect tree)?"
    Every internal node has two non-null children, all leaves at the same depth. Recurrence: `is_perfect(n) ⇔ is_perfect(L) and is_perfect(R) and height(L) == height(R)`.

##### 🐛 Common Bugs

1. **Returning the height when you should return False** — the tuple/sentinel handling matters.
2. **Calling `is_balanced(left) and is_balanced(right)` plus separate height checks** — accidental O(n²) (Layer 1).
3. **Off-by-one on `abs(L − R) > 1`** vs `> 0` — strict balance vs balance.
4. **Forgetting the early return** in the sentinel approach — you'll pay full cost on huge unbalanced trees.
5. **Wrong base case**: `check(None) → (True, 0)`. If you return `(True, -1)` or similar, your heights propagate wrong.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `True`
- [ ] Single node → `True`
- [ ] Linear chain of 2 nodes → `True` (heights 0 and 1, diff 1)
- [ ] Linear chain of 3 nodes → `False` (heights 0 and 2 at the root)
- [ ] Perfectly balanced full binary tree → `True`
- [ ] One subtree heavily skewed but the tree is shallow enough that the global is balanced — careful: the *every node* check, not just the root

##### 🏢 Sample Interviewer Quote

> *"Determine if a binary tree is height-balanced."*

Your opener: *"Postorder, return both the height and a balanced flag — or use −1 as a 'failed' sentinel. O(n), O(h). Brute force would be O(n²) because height gets recomputed."*

---

#### Problem 7 — Path Sum (root-to-leaf equals target)

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Adobe</span>

> Given the root of a binary tree and an integer `target`, return True if and only if there exists a **root-to-leaf** path whose node values sum to exactly `target`.

##### 📖 Story Mode

Picture each node as carrying a numeric "weight." You walk from the root to a leaf; along the way, you accumulate the weights. At a leaf, you check: "did I hit the target?" If yes, return True; if not, try another root-to-leaf path. The recursion shape: **subtract as you go**, and the leaf check decides the verdict.

The classic trap: don't check `target == 0` at `None`. If you do, a node with only one child gets credit for a phantom "leaf" on the missing side.

##### 🌍 Real-World Usage

- **Budget propagation** — does any spending path through a tree of departments hit the cap?
- **Decision-tree classifiers** — does any path of features lead to a target probability score?
- **Game-tree min-max with prune** — early-stop on paths whose accumulated heuristic score exceeds the bound.
- **Network routing cost** — is there a route from source to a leaf node within budget?

##### 🧠 Thinking Process

> `has_path_sum(node, target)` is True iff `node` is a **leaf** and `node.val == target`, or one of `node`'s children has a path summing to `target − node.val`.

That's the recursive structure. Termination: leaves return T/F; non-leaves OR-combine the two recursive calls.

The *leaf* test is `node.left is None and node.right is None` — both children null. The naive `node is None: return target == 0` is **wrong**: it makes a single-child node match if `target == sum of the only path`, even though the missing-child side is also "checked" and treated as a free hit.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Recursive (subtract as you go)"

    ```python
    def has_path_sum(root: TreeNode | None, target: int) -> bool:
        if root is None:
            return False
        if root.left is None and root.right is None:
            return target == root.val
        rem = target - root.val
        return (has_path_sum(root.left,  rem)
                or has_path_sum(root.right, rem))
    ```

    **O(n)**, **O(h)**.

=== "Layer 2 — Iterative DFS (explicit stack)"

    ```python
    def has_path_sum_iter(root: TreeNode | None, target: int) -> bool:
        if root is None:
            return False
        stack: list[tuple[TreeNode, int]] = [(root, target - root.val)]
        while stack:
            n, rem = stack.pop()
            if n.left is None and n.right is None and rem == 0:
                return True
            if n.right:
                stack.append((n.right, rem - n.right.val))
            if n.left:
                stack.append((n.left,  rem - n.left.val))
        return False
    ```

    Same complexity, no recursion limit.

=== "Layer 3 — BFS variant"

    ```python
    from collections import deque

    def has_path_sum_bfs(root: TreeNode | None, target: int) -> bool:
        if root is None:
            return False
        q: deque[tuple[TreeNode, int]] = deque([(root, target - root.val)])
        while q:
            n, rem = q.popleft()
            if n.left is None and n.right is None and rem == 0:
                return True
            if n.left:  q.append((n.left,  rem - n.left.val))
            if n.right: q.append((n.right, rem - n.right.val))
        return False
    ```

    Useful if you also want to find the *shortest* root-to-leaf path that sums to target — BFS gives you depth order for free.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def has_path_sum(root: TreeNode | None, target: int) -> bool:
        """Return True iff there is a root-to-leaf path summing to `target`.

        Args:
            root: Root of the tree (may be None).
            target: Required sum.

        Returns:
            False for an empty tree, otherwise the existence check.

        Time:  O(n).
        Space: O(h) recursion stack.

        Example:
            >>> # tree:    5
            >>> #         / \
            >>> #        4   8
            >>> #       /
            >>> #      11
            >>> #     /  \
            >>> #    7    2
            >>> # has_path_sum(root, 22)  →  True   (5+4+11+2)
        """
        if root is None:
            return False
        if root.left is None and root.right is None:
            return target == root.val
        rem = target - root.val
        return (has_path_sum(root.left,  rem)
                or has_path_sum(root.right, rem))
    ```

=== "Layer 5 — Variants"

    **Variant A — return *all* root-to-leaf paths summing to target** (LC 113). Track the running path on a stack and append a copy when a leaf hits target. **O(n × L)** where L is the longest path (because of the copy).

    **Variant B — count root-to-any-node paths summing to target** (LC 437, "Path Sum III"). Use prefix-sums-on-the-recursion-stack: a hash map of `running_sum → count` looks up `running_sum − target` in O(1). **O(n)**.

    **Variant C — max sum root-to-leaf**: replace OR-combine with `max`, drop the target.

    **Variant D — minimum-cost path with non-leaf termination allowed**: BFS by cost (Dijkstra on a tree).

##### 🔍 Dry Run

Tree (target = 22):

```
            5
           / \
          4   8
         /   / \
        11  13  4
       /  \      \
      7    2      1
```

| call | (node, target) | rem | leaf? | result |
|------|----------------|-----|-------|--------|
| `has(5, 22)` | rem=17 | no | recurse | |
| `has(4, 17)` | rem=13 | no | recurse left only | |
| `has(11, 13)` | rem=2 | no | recurse | |
| `has(7, 2)` | leaf | 2 == 7? no | False | |
| `has(2, 2)` | leaf | 2 == 2? **yes** | **True** ✅ | propagates up |

##### ⏱️ Complexity

- **Time: O(n)** — each node visited at most once.
- **Space: O(h)** stack.

##### 🎯 Pattern Used

**Top-down accumulation.** Pass the running state (here: remaining target) *down* the recursion. Sibling pattern of "postorder bottom-up" — preorder top-down is for problems where the answer depends on the path so far, not on subtree summaries.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — All such paths, not just existence."
    Variant A. Backtrack with a list; deepcopy on hit.

??? question "Follow-up 2 — Path between any two nodes (not just root-to-leaf)."
    Different problem (Path Sum III). Prefix-sum hash on the recursion stack.

??? question "Follow-up 3 — Negative or zero values?"
    The recursion handles them — the `rem` can go negative or back up to target. Don't prune on `rem < 0` unless all values are positive.

??? question "Follow-up 4 — Why not check `target == 0` at `None`?"
    A node with only one child would call into both `None` and the actual child. The `None` arm would succeed if `running_sum == target` — but that's the *parent's* path, with no leaf. False positives.

??? question "Follow-up 5 — Streaming: tree is too large for memory."
    Iterative DFS with `(node_id, rem)` on disk-backed stack. Or recompute paths via tree serialization replayed lazily.

##### 🐛 Common Bugs

1. **Wrong base case** — `if root is None: return target == 0`. Off by one at single-child nodes.
2. **Forgetting to subtract `root.val` before recursing** — passes the wrong remaining target.
3. **Returning `True` only if *both* sides hit target** — should be `or`, not `and`.
4. **Mutating `target` in place** — fine for one branch, but the second sibling sees the wrong value if you didn't restore.
5. **Considering an internal node a leaf** — `if not (root.left or root.right)` is the canonical leaf test.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `False` (no paths exist)
- [ ] Single node, val == target → `True`
- [ ] Single node, val ≠ target → `False`
- [ ] Tree with one root-to-leaf path matching, others not → `True`
- [ ] Negative values present → recursion still correct
- [ ] Target unreachable on every leaf → `False`

##### 🏢 Sample Interviewer Quote

> *"Given a binary tree and a sum, determine if it has a root-to-leaf path with that sum."*

Your opener: *"Top-down recursion subtracting `target` by each node's value. At a leaf, check `target == node.val`. The leaf check matters — `None` is not a leaf, otherwise single-child nodes get false positives. O(n), O(h)."*

---

#### Problem 8 — Convert Sorted Array to BST (height-balanced)

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Airbnb</span> <span class="company-tag">Bloomberg</span>

> Given a sorted (ascending) integer array `nums`, build a **height-balanced** BST: a tree where the depths of the two subtrees of every node differ by at most 1.

##### 📖 Story Mode

A sorted array is already an inorder traversal of *some* BST. To make it height-balanced, pick the **middle** as the root — that splits the remaining elements equally — and recurse on the halves. The result is the optimal balanced BST: every level is filled left-to-right and the height is `⌈log₂(n+1)⌉`.

##### 🌍 Real-World Usage

- **Database bulk load** — building a BBST index from a sorted file gives O(log n) lookups afterward in one pass.
- **Cache warm-up** — pre-populating a sorted dataset into an in-memory tree without per-insert rebalancing.
- **Read-only analytics** — building once, querying many times; balanced shape gives predictable latency.
- **Snapshot trees** — git-style history snapshots where the chronological order is the inorder.

##### 🧠 Thinking Process

> Build(lo, hi): if `lo > hi` return None; mid = (lo + hi) // 2; root = nums[mid]; left = Build(lo, mid - 1); right = Build(mid + 1, hi).

Two reasons to pass `(lo, hi)` instead of slicing:

1. **Memory:** slicing allocates O(n log n) cumulative space across recursion.
2. **Clarity:** the indices are tied to the original array.

The choice of "middle" is `(lo + hi) // 2`, but for arrays of even length you could also pick `(lo + hi + 1) // 2` — different but equally valid balanced shapes.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Slicing (simple)"

    ```python
    def sorted_array_to_bst_slice(nums: list[int]) -> TreeNode | None:
        if not nums:
            return None
        mid = len(nums) // 2
        return TreeNode(nums[mid],
                        sorted_array_to_bst_slice(nums[:mid]),
                        sorted_array_to_bst_slice(nums[mid + 1:]))
    ```

    Easy to read; **O(n log n)** total memory because of the slices.

=== "Layer 2 — Index-based (canonical)"

    ```python
    def sorted_array_to_bst(nums: list[int]) -> TreeNode | None:
        def build(lo: int, hi: int) -> TreeNode | None:
            if lo > hi:
                return None
            mid = (lo + hi) // 2
            return TreeNode(nums[mid],
                            build(lo, mid - 1),
                            build(mid + 1, hi))

        return build(0, len(nums) - 1)
    ```

    **O(n) time**, **O(log n) stack** (because the tree is balanced). The interview answer.

=== "Layer 3 — Pick the upper-middle (alternative balance)"

    ```python
    def sorted_array_to_bst_upper(nums: list[int]) -> TreeNode | None:
        def build(lo: int, hi: int) -> TreeNode | None:
            if lo > hi:
                return None
            mid = (lo + hi + 1) // 2          # bias right on even lengths
            return TreeNode(nums[mid],
                            build(lo, mid - 1),
                            build(mid + 1, hi))

        return build(0, len(nums) - 1)
    ```

    Produces a different but equally balanced tree. LeetCode accepts both.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def sorted_array_to_bst(nums: list[int]) -> TreeNode | None:
        """Build a height-balanced BST from a sorted ascending array.

        Args:
            nums: Sorted (non-decreasing) list of integers. Duplicates allowed —
                  the resulting tree will not be a strict BST in that case;
                  see Variant A for the deduplicated build.

        Returns:
            Root of a height-balanced BST whose inorder traversal is `nums`.

        Time:  O(n).
        Space: O(log n) recursion stack (balanced tree).
        """
        def build(lo: int, hi: int) -> TreeNode | None:
            if lo > hi:
                return None
            mid = (lo + hi) // 2
            return TreeNode(nums[mid],
                            build(lo, mid - 1),
                            build(mid + 1, hi))

        return build(0, len(nums) - 1)
    ```

=== "Layer 5 — Linked-list input variant (LC 109)"

    ```python
    def sorted_list_to_bst(head: ListNode | None) -> TreeNode | None:
        # First pass: count nodes
        count = 0
        cur = head
        while cur:
            count += 1
            cur = cur.next

        ptr = head

        def build(n: int) -> TreeNode | None:
            nonlocal ptr
            if n <= 0:
                return None
            left = build(n // 2)
            node = TreeNode(ptr.val)
            ptr = ptr.next
            node.left = left
            node.right = build(n - n // 2 - 1)
            return node

        return build(count)
    ```

    **O(n) time**, **O(log n) stack**. Uses the *inorder* simulation: build the left subtree, consume one element for the root, build the right subtree. No need to convert the linked list to an array.

##### 🔍 Dry Run

`nums = [-10, -3, 0, 5, 9]`

| call | lo | hi | mid | val | left call | right call |
|------|----|----|-----|-----|-----------|------------|
| build(0,4) | 0 | 4 | 2 | 0 | build(0,1) | build(3,4) |
| build(0,1) | 0 | 1 | 0 | -10 | build(0,-1)=None | build(1,1) |
| build(1,1) | 1 | 1 | 1 | -3 | build(1,0)=None | build(2,1)=None |
| build(3,4) | 3 | 4 | 3 | 5 | build(3,2)=None | build(4,4) |
| build(4,4) | 4 | 4 | 4 | 9 | None | None |

Resulting tree:

```
        0
       / \
     -10   5
       \    \
       -3    9
```

Height = 2, balanced ✅.

##### ⏱️ Complexity

- **Time: O(n)** — each element becomes a node exactly once.
- **Space: O(log n)** recursion stack (balanced); plus O(n) for the output tree itself.

##### 🎯 Pattern Used

**Divide-and-conquer on a sorted sequence.** Same shape as merge-sort, binary search, "build a tree from preorder + inorder," and "build a fenwick tree from a sorted array."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why is the result a valid BST?"
    Inorder of the resulting tree visits left-subtree (range `[lo..mid-1]`), root (`nums[mid]`), right-subtree (`[mid+1..hi]`) in ascending order. Since `nums` is sorted, BST invariant holds.

??? question "Follow-up 2 — Why is it height-balanced?"
    Each recursive level halves the range, so the tree's height is `⌈log₂(n+1)⌉`. Heights of left and right subtrees differ by at most 1.

??? question "Follow-up 3 — What if the input is a sorted *linked list* (no random access)?"
    Layer 5: simulate inorder construction with a moving pointer. **O(n) time**, **O(log n) space**. Avoid the naive O(n²) "convert to array first" approach.

??? question "Follow-up 4 — Duplicates in the input?"
    The straightforward build duplicates them as nodes. If you want a *strict* BST (no duplicates), dedupe with `nums = sorted(set(nums))` first, or store counts in nodes.

??? question "Follow-up 5 — Maintain perfect height (all leaves at same depth)?"
    Only possible if `n = 2^k − 1`. Otherwise pad / skip; the problem usually accepts merely *height-balanced*.

##### 🐛 Common Bugs

1. **Off-by-one on `hi`** — `build(0, len(nums))` and then comparing `lo >= hi` is also valid, but mixing the two conventions causes bugs. Pick exclusive *or* inclusive and stick to it.
2. **`mid = lo + (hi - lo) // 2` if used wrong** — fine, but ensure overflow-safety (irrelevant in Python; matters in Java/C++).
3. **Slicing with `nums[mid:]` instead of `nums[mid+1:]`** — duplicates the root in the right subtree.
4. **Building the right subtree first** in the linked-list variant — pointer would already be past the root.
5. **Forgetting that the input must be sorted** — if not, the result is not a BST.

##### ✅ Edge Cases Checklist

- [ ] Empty array → `None`
- [ ] Single element → single-node tree
- [ ] Two elements → 2-node tree of height 1
- [ ] Three elements → balanced (root = middle)
- [ ] Even length array → either left-mid or right-mid choice; both balanced
- [ ] Already-sorted with duplicates — handle per spec
- [ ] Negative numbers — irrelevant, BST works on any total order

##### 🏢 Sample Interviewer Quote

> *"Convert a sorted array to a height-balanced BST."*

Your opener: *"Pick the middle as the root, recurse on the left and right halves. Index-based build to avoid slicing — O(n) time, O(log n) stack. If the input is a sorted linked list, I'd use the inorder-simulation trick to avoid converting to an array."*

---

#### Problem 9 — Merge Two Binary Trees

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span>

> Given two binary trees `t1` and `t2`, "overlay" one onto the other. Where both have a node at the same position, the merged node's value is the sum. Where only one has a node, that node (and its entire subtree) is kept.

##### 📖 Story Mode

You and a friend each drew a binary tree on transparent paper. You stack them. Where the two papers overlap with nodes, you write down their sum; where only one paper has a node, you keep it as-is. The merged tree is the result.

The recurrence is one of the prettiest in the chapter — both the null-cases collapse cleanly:

> `merge(a, b)` = `b` if `a` is None; `a` if `b` is None; otherwise a new node whose value is `a.val + b.val` and whose children are `merge(a.left, b.left)` and `merge(a.right, b.right)`.

##### 🌍 Real-World Usage

- **Configuration overlays** — merging a "default" config tree with an "override" tree (with sum or last-write semantics).
- **Sparse tensor merging** — combining two sparse tree-structured updates in differentiable computation.
- **Quad-tree image overlays** — merging two compressed images at the leaf level.
- **Game state composition** — combining two snapshots of a hierarchical state with additive deltas.

##### 🧠 Thinking Process

This is the **two-pointer lockstep** pattern from Problems 2 and 3, but with a third action — *combine* — at every paired non-null position.

Two design choices:

1. **Allocate new nodes** (clean, non-mutating). O(min(n, m)) extra space for the new tree.
2. **Mutate `t1` in place** (less allocation, but destroys `t1`).

Pick (1) by default; switch to (2) when the caller is OK with mutation and wants minimal allocations.

##### 🐍 5 Layers of Solution

=== "Layer 1 — New-allocation recursive"

    ```python
    def merge_trees(a: TreeNode | None, b: TreeNode | None) -> TreeNode | None:
        if a is None:
            return b
        if b is None:
            return a
        return TreeNode(
            a.val + b.val,
            merge_trees(a.left,  b.left),
            merge_trees(a.right, b.right),
        )
    ```

    **O(min(n_a, n_b))** time, **O(h)** stack. Note: when only one tree has a subtree, we return the *original* (not a copy) — the merged tree shares structure with the input. Document this if mutation downstream would surprise the caller.

=== "Layer 2 — Pure (no shared structure)"

    ```python
    def merge_trees_pure(a: TreeNode | None, b: TreeNode | None) -> TreeNode | None:
        def clone(n: TreeNode | None) -> TreeNode | None:
            if n is None:
                return None
            return TreeNode(n.val, clone(n.left), clone(n.right))

        if a is None:
            return clone(b)
        if b is None:
            return clone(a)
        return TreeNode(
            a.val + b.val,
            merge_trees_pure(a.left,  b.left),
            merge_trees_pure(a.right, b.right),
        )
    ```

    Same complexity, but the result owns all its nodes — safe to mutate.

=== "Layer 3 — In-place (mutate `a`)"

    ```python
    def merge_trees_inplace(a: TreeNode | None, b: TreeNode | None) -> TreeNode | None:
        if a is None:
            return b
        if b is None:
            return a
        a.val += b.val
        a.left  = merge_trees_inplace(a.left,  b.left)
        a.right = merge_trees_inplace(a.right, b.right)
        return a
    ```

    **Half the allocations**; `a` is destroyed. Use when `a` is a temporary anyway.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def merge_trees(a: TreeNode | None, b: TreeNode | None) -> TreeNode | None:
        """Overlay two binary trees, summing values at coincident positions.

        The returned tree may share structure with the inputs where one side
        is None. Use `merge_trees_pure` for a fully owned copy.

        Args:
            a: Root of the first tree.
            b: Root of the second tree.

        Returns:
            Root of the merged tree, or None if both inputs are None.

        Time:  O(min(n_a, n_b)).  Beyond the overlap, we attach existing subtrees.
        Space: O(h) recursion stack.
        """
        if a is None:
            return b
        if b is None:
            return a
        return TreeNode(
            a.val + b.val,
            merge_trees(a.left,  b.left),
            merge_trees(a.right, b.right),
        )
    ```

=== "Layer 5 — Iterative BFS in-place"

    ```python
    from collections import deque

    def merge_trees_bfs(a: TreeNode | None, b: TreeNode | None) -> TreeNode | None:
        if a is None:
            return b
        if b is None:
            return a
        q: deque[tuple[TreeNode, TreeNode]] = deque([(a, b)])
        while q:
            x, y = q.popleft()
            x.val += y.val
            if x.left and y.left:
                q.append((x.left, y.left))
            elif x.left is None:
                x.left = y.left
            if x.right and y.right:
                q.append((x.right, y.right))
            elif x.right is None:
                x.right = y.right
        return a
    ```

    Avoids recursion. Mutates `a` like Layer 3.

##### 🔍 Dry Run

```
   t1:  1            t2:  2
       / \              / \
      3   2            1   3
     /                  \   \
    5                    4   7
```

| call | a.val + b.val (or fallback) | left recursion | right recursion |
|------|-----------------------------|---------------|-----------------|
| merge(1, 2) | 3 | merge(3, 1) | merge(2, 3) |
| merge(3, 1) | 4 | merge(5, None)=5 | merge(None, 4)=4 |
| merge(2, 3) | 5 | merge(None, None)=None | merge(None, 7)=7 |

Result:

```
        3
       / \
      4   5
     / \   \
    5   4   7
```

✅

##### ⏱️ Complexity

- **Time: O(min(n_a, n_b))** — once one side is None, we attach the other's subtree wholesale (constant work).
- **Space: O(h)** for the stack, plus the result tree itself if you allocate fresh nodes.

##### 🎯 Pattern Used

**Two-tree lockstep with combine.** Generalizes `same_tree`: instead of returning a bool, *do something* at each matched position. Same shape applies to "diff two trees," "merge two AVL trees," "compose two functorial trees."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Iterative version."
    Layer 5: BFS with a queue of paired nodes.

??? question "Follow-up 2 — Without mutating inputs and without sharing structure."
    Layer 2: deep-clone the orphan side.

??? question "Follow-up 3 — What if the merge function isn't `+` but, say, `max`?"
    Replace `a.val + b.val` with `max(a.val, b.val)`. Or pass a callback `merge_fn(a.val, b.val)`. The structural recursion is unchanged — this is the "monoid" generalization.

??? question "Follow-up 4 — Two BSTs — does the merged tree remain a BST?"
    No — the sum can violate the BST invariant. Different problem (LC 1305: "All Elements in Two BSTs"), solved by inorder-merging the two streams.

??? question "Follow-up 5 — Three or more trees?"
    Fold left: `merge_trees(merge_trees(t1, t2), t3)`. **O(total node count)**.

##### 🐛 Common Bugs

1. **Returning `a` always when `b` is None and vice versa, but forgetting to clone** — caller may mutate the returned tree and accidentally clobber an input.
2. **Allocating a new node when one side is None** — wastes time; the existing subtree is fine to attach (or clone if you want purity).
3. **Mutating `a.val` *and* allocating a new TreeNode** — mixed-mode contract; pick one.
4. **Using `a.val + b.val` when the spec says "max" or "min"** — read the problem.
5. **Treating two structurally identical empty subtrees as a None hit** — fine, but make sure the recursion bottoms out cleanly.

##### ✅ Edge Cases Checklist

- [ ] Both empty → `None`
- [ ] One empty → return the other (cloned or shared per contract)
- [ ] Identical trees → values doubled, structure preserved
- [ ] Disjoint shapes (e.g., `t1` left-only, `t2` right-only) → result has both subtrees
- [ ] Negative values → still works (just additive overlay)
- [ ] One tree massively larger than the other → only the overlap region is "touched"

##### 🏢 Sample Interviewer Quote

> *"Merge two binary trees by summing overlapping nodes."*

Your opener: *"Lockstep recursion. If one side is null, return the other; otherwise allocate a new node with summed value and recurse on the children. O(min(n, m)) time, O(h) stack. I can also mutate `t1` in place to halve the allocations if the caller's OK losing it."*

---

#### Problem 10 — Minimum Depth of a Binary Tree

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Adobe</span>

> Given the root of a binary tree, return its **minimum depth** — the number of nodes on the shortest path from the root **to a leaf**. A leaf is a node with no children.

##### 📖 Story Mode

The opposite of Problem 1 — but with a sneaky asymmetry. Naive `1 + min(min_depth(left), min_depth(right))` is wrong when a node has only one child. Why? `min_depth(None) = 0`, so a one-child node would say "my min depth is `1 + 0 = 1`," even though there's no leaf on the null side.

The fix: a leaf must have **both children null**. If only one is null, the path must go through the other side.

##### 🌍 Real-World Usage

- **Decision trees** — depth of the shallowest "leaf decision" tells you the fastest classification path.
- **Game trees** — minimum moves to reach a terminal state in a game with forced moves.
- **Filesystem search** — shortest path from a root directory to the *first* file (no further subdirectories).
- **BFS shortest path** in tree-shaped state machines (e.g., dependency resolution to first leaf).

##### 🧠 Thinking Process

The recursion has **three cases**:

1. `root` is None → 0.
2. `root` is a leaf (`left is None and right is None`) → 1.
3. `root` has at least one child → `1 + min(depth of *non-null* children)`.

Or: BFS level-by-level and return the depth of the first leaf seen. **BFS wins on average** because it stops at the first leaf, whereas DFS may explore an entire long subtree before finding the shallow one.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Naive (wrong)"

    ```python
    def min_depth_naive(root: TreeNode | None) -> int:
        if root is None:
            return 0
        return 1 + min(min_depth_naive(root.left),
                       min_depth_naive(root.right))   # ❌ wrong
    ```

    On a tree like `1 → 2` (root with single left child), this returns `1 + min(1, 0) = 1`. But the only leaf is at depth 2. **Off by one whenever there's a one-child node.**

=== "Layer 2 — Recursive (correct)"

    ```python
    def min_depth(root: TreeNode | None) -> int:
        if root is None:
            return 0
        if root.left is None and root.right is None:
            return 1
        if root.left is None:
            return 1 + min_depth(root.right)
        if root.right is None:
            return 1 + min_depth(root.left)
        return 1 + min(min_depth(root.left), min_depth(root.right))
    ```

    **O(n)**, **O(h)**.

=== "Layer 3 — BFS (early-stop on first leaf)"

    ```python
    from collections import deque

    def min_depth_bfs(root: TreeNode | None) -> int:
        if root is None:
            return 0
        q: deque[tuple[TreeNode, int]] = deque([(root, 1)])
        while q:
            n, d = q.popleft()
            if n.left is None and n.right is None:
                return d
            if n.left:  q.append((n.left,  d + 1))
            if n.right: q.append((n.right, d + 1))
        return 0   # unreachable when root is non-null
    ```

    Returns as soon as the first leaf is dequeued. **O(n) worst case** (skewed tree), but typically far less.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations
    from collections import deque


    def min_depth(root: TreeNode | None) -> int:
        """Return the minimum depth: nodes on the shortest root-to-leaf path.

        Uses BFS so the answer is the depth of the first leaf reached, which
        terminates much earlier than DFS on highly unbalanced trees.

        Args:
            root: Root of the tree (may be None).

        Returns:
            0 for an empty tree, otherwise the count of nodes on the shortest
            root-to-leaf path.

        Time:  O(n) worst case, often less due to early termination.
        Space: O(w) BFS queue, where w is the maximum width.
        """
        if root is None:
            return 0
        q: deque[tuple[TreeNode, int]] = deque([(root, 1)])
        while q:
            n, d = q.popleft()
            if n.left is None and n.right is None:
                return d
            if n.left:
                q.append((n.left, d + 1))
            if n.right:
                q.append((n.right, d + 1))
        return 0
    ```

=== "Layer 5 — Variants"

    **Variant A — weighted edges:** Dijkstra on a tree. Min-heap of `(cost, node)`; pop the cheapest leaf.

    **Variant B — depth to *any node satisfying a predicate*** (not just a leaf): same BFS, replacing the leaf check with the predicate.

    **Variant C — n-ary tree:** the leaf check becomes `not n.children`; recursion uses `min(min_depth(c) for c in n.children, default=0)` — but **default=0** would re-introduce the one-child trap; use `1 + min(min_depth(c) for c in n.children)` and the leaf base case explicitly.

##### 🔍 Dry Run

Tree:

```
        2
         \
          3
           \
            4
             \
              5
```

Naive (Layer 1) returns `1 + min(min(0), 1+1+1+1) = 1` — wrong.

Layer 2 trace:
- `min_depth(2)`: left is None, return `1 + min_depth(3)` = `1 + min_depth(3)`
- `min_depth(3)`: left is None, return `1 + min_depth(4)`
- `min_depth(4)`: left is None, return `1 + min_depth(5)`
- `min_depth(5)`: leaf → 1
- back-propagate: 1 → 2 → 3 → **4** ✅

BFS (Layer 3):
| dequeue | depth | leaf? | enqueued |
|---------|-------|-------|----------|
| (2, 1) | 1 | no (right child) | (3, 2) |
| (3, 2) | 2 | no | (4, 3) |
| (4, 3) | 3 | no | (5, 4) |
| (5, 4) | 4 | **yes** → return **4** ✅

##### ⏱️ Complexity

- **Time: O(n)** worst case for both DFS and BFS; BFS often much less due to early termination.
- **Space: O(h)** for DFS, **O(w)** for BFS.

##### 🎯 Pattern Used

**BFS for shortest-path on a tree.** Same shape as "shortest path in unweighted graph" — first leaf dequeued wins. The DFS variant is the more familiar recursion, but the BFS variant is the cleaner answer when interviewers say "we want the *first* leaf."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why is naive `1 + min(min_depth(L), min_depth(R))` wrong?"
    `min_depth(None) = 0` makes a one-child node return `1`, claiming a non-existent leaf on the null side. Trick question that catches half the candidates.

??? question "Follow-up 2 — Iterative DFS — does it work?"
    Yes, but it visits the entire tree before knowing the minimum, since each branch could surprise you. BFS is asymptotically the same in the worst case but typically much better.

??? question "Follow-up 3 — What's the right base case for a true leaf?"
    `node.left is None and node.right is None` returns 1. That's the "I am a leaf, depth-from-here is 1 node" base.

??? question "Follow-up 4 — Min depth where some leaves are forbidden (e.g., must satisfy a value condition)?"
    Replace the leaf check with `is_leaf(n) and predicate(n)`. BFS handles this without restructure.

??? question "Follow-up 5 — Streaming / generator-style?"
    Convert BFS to a generator that `yield`s `(node, depth)` in BFS order; the consumer takes the first leaf and stops. Same complexity, lazier.

##### 🐛 Common Bugs

1. **The naive recursion** (Layer 1) — most common bug for this problem. The asymmetry between `max` and `min` is the lesson.
2. **Forgetting the empty-tree case** — must return 0 (no leaves), not 1.
3. **Treating internal nodes as leaves** — careful: `not (node.left or node.right)` is the leaf check.
4. **DFS that doesn't propagate Inf for None subtrees** — if you go DFS, return `inf` for the null side and then take `min(left, right) + 1`. Easy to mess up.
5. **Mutating depth in place across recursion** — pass it as a parameter, don't share via global.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0
- [ ] Single node → 1
- [ ] Skewed left-only chain of n nodes → n (only path is to the deepest leaf)
- [ ] Balanced full tree → `⌈log₂(n+1)⌉`
- [ ] Tree with a one-child root and a deep right subtree → must walk the deep side; naive returns 1 incorrectly
- [ ] All internal nodes have one child only — equivalent to a chain, depth = n

##### 🏢 Sample Interviewer Quote

> *"Find the minimum depth of a binary tree."*

Your opener: *"BFS — the first leaf dequeued is at the minimum depth, so we stop early. Worst case O(n) but typically much faster than DFS. The DFS recursion has a trap: a node with one child isn't a leaf, so naive `1 + min(left, right)` is wrong; the correct recurrence handles single-child nodes by recursing only on the non-null side."*

---

### Medium (11–25) — the bulk of interview questions

#### Problem 11 — Binary Tree Level Order Traversal

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">LinkedIn</span>

> Given the root of a binary tree, return its level-order traversal — the values of the nodes level by level, from top to bottom and left to right, as a list of lists.

##### 📖 Story Mode

You're standing at the root and you announce, "Everyone on level 0, raise your hand!" The root raises. "Level 1, raise!" Its children raise. "Level 2, raise!" Their children raise. You walk along each level left-to-right writing down what you see. **That's BFS.**

The trick that separates a clean solution from a buggy one is *snapshotting* the queue size before draining a level. Otherwise you'd accidentally process children together with their parents.

##### 🌍 Real-World Usage

- **UI rendering** — DOM/React layout passes work top-down level by level.
- **Network broadcast** — flood-fill from a router hop by hop is BFS.
- **Game AI** — ply-by-ply evaluation in min-max search ("explore one move ahead, then two, then three").
- **Build systems** — topological levels: build all the things with no missing deps, then everything that depends on them, etc.

##### 🧠 Thinking Process

The standard BFS shape:

```
queue ← [root]
while queue not empty:
    snapshot the size of the queue (= number of nodes at this level)
    for that many iterations:
        pop, record, enqueue children
    flush the level into the output
```

The snapshot is the keystone. Without `for _ in range(len(q))`, the inner loop would also process the next level.

##### 🐍 5 Layers of Solution

=== "Layer 1 — BFS with level snapshot (canonical)"

    ```python
    from collections import deque

    def level_order(root: TreeNode | None) -> list[list[int]]:
        if root is None:
            return []
        out: list[list[int]] = []
        q: deque[TreeNode] = deque([root])
        while q:
            level: list[int] = []
            for _ in range(len(q)):
                n = q.popleft()
                level.append(n.val)
                if n.left:  q.append(n.left)
                if n.right: q.append(n.right)
            out.append(level)
        return out
    ```

    **O(n) time**, **O(w) space** where w is the maximum width.

=== "Layer 2 — DFS with depth index"

    ```python
    def level_order_dfs(root: TreeNode | None) -> list[list[int]]:
        out: list[list[int]] = []

        def go(n: TreeNode | None, depth: int) -> None:
            if n is None:
                return
            if depth == len(out):
                out.append([])
            out[depth].append(n.val)
            go(n.left,  depth + 1)
            go(n.right, depth + 1)

        go(root, 0)
        return out
    ```

    Same complexity, but uses **O(h)** stack instead of **O(w)** queue. Useful when w >> h (bushy tree, deep recursion is fine).

=== "Layer 3 — BFS with `(node, depth)` tuples"

    ```python
    def level_order_tuples(root: TreeNode | None) -> list[list[int]]:
        if root is None:
            return []
        out: list[list[int]] = []
        q: deque[tuple[TreeNode, int]] = deque([(root, 0)])
        while q:
            n, d = q.popleft()
            if d == len(out):
                out.append([])
            out[d].append(n.val)
            if n.left:  q.append((n.left,  d + 1))
            if n.right: q.append((n.right, d + 1))
        return out
    ```

    Equivalent. Some prefer this when they need depth-aware logic per node.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations
    from collections import deque


    def level_order(root: TreeNode | None) -> list[list[int]]:
        """Return the values of the tree in BFS / level-order.

        Args:
            root: Root of the binary tree (may be None).

        Returns:
            A list of levels; each level is a list of node values left-to-right.
            Empty list for an empty tree.

        Time:  O(n).
        Space: O(w) where w is the maximum width of the tree.
        """
        if root is None:
            return []

        result: list[list[int]] = []
        q: deque[TreeNode] = deque([root])

        while q:
            level_size = len(q)            # snapshot before draining
            level_values: list[int] = []

            for _ in range(level_size):
                node = q.popleft()
                level_values.append(node.val)
                if node.left  is not None: q.append(node.left)
                if node.right is not None: q.append(node.right)

            result.append(level_values)

        return result
    ```

=== "Layer 5 — Variants"

    **Variant A — Bottom-up (LC 107):**

    ```python
    def level_order_bottom(root: TreeNode | None) -> list[list[int]]:
        return list(reversed(level_order(root)))
    ```

    **Variant B — Zigzag (LC 103):** flip every other level.

    ```python
    def zigzag(root: TreeNode | None) -> list[list[int]]:
        out = level_order(root)
        for i in range(1, len(out), 2):
            out[i].reverse()
        return out
    ```

    **Variant C — N-ary tree:** replace `if n.left/right` with `for c in n.children: q.append(c)`.

    **Variant D — Average of each level (LC 637):** swap `level.append(...)` for a running sum and divide by `level_size`.

##### 🔍 Dry Run

```
        3
       / \
      9   20
         /  \
        15   7
```

| iteration | q before | level_size | level | q after |
|-----------|----------|-----------|-------|---------|
| 1 | [3] | 1 | [3] | [9, 20] |
| 2 | [9, 20] | 2 | [9, 20] | [15, 7] |
| 3 | [15, 7] | 2 | [15, 7] | [] |

Output: `[[3], [9, 20], [15, 7]]` ✅

##### ⏱️ Complexity

- **Time: O(n)** — each node is enqueued and dequeued exactly once.
- **Space: O(w)** for the queue (peak ~ n/2 at the widest level of a perfect tree); plus O(n) for the output.

##### 🎯 Pattern Used

**BFS with level boundary.** The "snapshot the queue size" idiom is the bedrock of dozens of tree problems: right-side view, level averages, level minimums, zigzag, populating next-right-pointers. Memorize it.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Bottom-up (last level first)."
    Variant A: reverse the output. **O(n).**

??? question "Follow-up 2 — Zigzag order (alternate left↔right per level)."
    Variant B: reverse every other level after the standard BFS. Or build with a deque per level and append-left on odd levels.

??? question "Follow-up 3 — Right-side view (only the last node per level)."
    See Problem 15. Take `level[-1]` after each level.

??? question "Follow-up 4 — Maximum value per level (LC 515)."
    Replace `level.append(n.val)` with a running max; output a list of maxes.

??? question "Follow-up 5 — N-ary tree."
    Swap `n.left / n.right` for `for c in n.children`.

##### 🐛 Common Bugs

1. **Forgetting to snapshot `len(q)`** — the inner loop bleeds into the next level.
2. **Using `list.pop(0)` instead of `deque.popleft()`** — `list.pop(0)` is O(n); the whole BFS becomes O(n²).
3. **Returning `[[]]` for an empty tree** instead of `[]`.
4. **Recursive DFS that uses a global `depth` counter without resetting** between calls.
5. **Appending to `out[d]` before checking `d == len(out)`** — index error on first node of each new depth.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `[]`
- [ ] Single node → `[[val]]`
- [ ] Skewed left chain → one element per level
- [ ] Perfect balanced tree → `2^k` elements at level k
- [ ] Tree with only one child at every level — still one element per level

##### 🏢 Sample Interviewer Quote

> *"Return a binary tree's level-order traversal."*

Your opener: *"BFS with the queue-size snapshot. Standard template. O(n), O(w). I can adapt it to bottom-up, zigzag, right-side view, level averages, etc. — each is one line of difference from the canonical loop."*

---

#### Problem 12 — Validate Binary Search Tree

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> Given the root of a binary tree, determine if it is a valid Binary Search Tree (BST). For each node, every value in its left subtree must be **strictly less than** the node's value, and every value in its right subtree must be **strictly greater**.

##### 📖 Story Mode

You'd think the BST check is "for each node, left.val < node.val < right.val." That's the **§8.4 trap**, and it's wrong:

```
       5
      / \
     3   8
        / \
       2   9     ← 2 < 8, but 2 < 5 fails the BST invariant globally
```

A valid BST needs every node to lie within a **range** inherited from its ancestors — not just compared with its immediate children. Two clean ways to do this: (1) **pass bounds down** during recursion, or (2) **inorder traversal must be strictly increasing**.

##### 🌍 Real-World Usage

- **Database integrity audits** — every B-tree index periodically validates this invariant during fsck/REINDEX.
- **Custom BSTs** — testing that your own AVL/RB-tree implementation hasn't violated invariants after a tricky rotation.
- **Binary serialization formats** — verifying the ordering invariant after a partial replay.
- **Compiler symbol tables** — when a sorted-name lookup tree is rebuilt, this is the validation.

##### 🧠 Thinking Process

Two correct approaches:

1. **Bounds passed down (top-down):** every recursion carries `(lo, hi)`, the open interval the node must lie in. The root starts with `(-∞, +∞)`. Going left tightens `hi` to `node.val`; going right tightens `lo` to `node.val`.
2. **Inorder is sorted:** a valid BST's **inorder** traversal yields values in strictly increasing order. Walk inorder, check `prev < node.val` at every step.

Both are O(n). The bounds approach short-circuits earlier on the wrong tree; the inorder approach uses less stack on a balanced tree.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Wrong (the §8.4 trap)"

    ```python
    def is_valid_bst_wrong(root: TreeNode | None) -> bool:
        if root is None:
            return True
        if root.left and root.left.val >= root.val:
            return False
        if root.right and root.right.val <= root.val:
            return False
        return is_valid_bst_wrong(root.left) and is_valid_bst_wrong(root.right)
    ```

    Misses the global ordering: a deep descendant on the right of a left subtree can violate the root's bound while satisfying every parent-child check.

=== "Layer 2 — Bounds (the right answer)"

    ```python
    import math

    def is_valid_bst(root: TreeNode | None) -> bool:
        def go(n: TreeNode | None, lo: float, hi: float) -> bool:
            if n is None:
                return True
            if not (lo < n.val < hi):
                return False
            return (go(n.left,  lo,     n.val)
                    and go(n.right, n.val, hi))

        return go(root, -math.inf, math.inf)
    ```

    **O(n)**, **O(h)**.

=== "Layer 3 — Inorder must be strictly increasing"

    ```python
    import math

    def is_valid_bst_inorder(root: TreeNode | None) -> bool:
        prev: float = -math.inf
        stack: list[TreeNode] = []
        node = root
        while node is not None or stack:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if node.val <= prev:
                return False
            prev = node.val
            node = node.right
        return True
    ```

    Iterative inorder, **O(n)**, **O(h)**. Stops at first violation.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations
    import math


    def is_valid_bst(root: TreeNode | None) -> bool:
        """Return True iff the tree obeys the BST ordering invariant.

        For every node n:
            all values in n.left subtree  < n.val
            all values in n.right subtree > n.val

        Uses bounds-down recursion. Equivalent to checking that an inorder
        walk yields strictly increasing values.

        Args:
            root: Root of the tree (may be None).

        Returns:
            True iff valid BST.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        def check(n: TreeNode | None, lo: float, hi: float) -> bool:
            if n is None:
                return True
            if not (lo < n.val < hi):
                return False
            return (check(n.left,  lo,     n.val)
                    and check(n.right, n.val, hi))

        return check(root, -math.inf, math.inf)
    ```

=== "Layer 5 — Variants"

    **Variant A — Duplicates allowed on one side** (e.g., "left ≤ root < right"): change `<` to `<=` consistently on the chosen side.

    **Variant B — Recover a BST with two swapped nodes** (LC 99): walk inorder, find the two adjacent pairs out of order, swap their values. **O(n) / O(h).**

    **Variant C — Largest BST subtree** (LC 333): postorder, return `(min, max, size, is_bst)` per subtree; track global max size.

    **Variant D — Number of valid BSTs of size n** (LC 96, "Catalan numbers"): DP, not validation, but sibling problem.

##### 🔍 Dry Run (bounds version)

Tree:

```
       5
      / \
     1   4
        / \
       3   6
```

| call | n | lo | hi | check | result |
|------|---|------|------|-------|--------|
| go(5) | 5 | -∞ | +∞ | OK | recurse |
| go(1) | 1 | -∞ | 5 | OK | leaf, True |
| go(4) | 4 | 5 | +∞ | **4 < 5 violates lo=5** | **False** ✅ |

##### ⏱️ Complexity

- **Time: O(n)** — each node visited once.
- **Space: O(h)** — recursion or explicit stack.

##### 🎯 Pattern Used

**Bounds passed down** (top-down preorder) — used wherever a node's local check depends on the *ancestor* values, not the children. Same shape: "valid binary search tree," "max ancestor diff," "good nodes count," "all valid path sums under bound."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why isn't the local left/right check enough?"
    A right-subtree node can be smaller than the **grandparent** even if it's bigger than its parent. The bounds capture every ancestor's constraint at once.

??? question "Follow-up 2 — What if values are 32-bit ints and the bounds need real ±∞?"
    Use Python's `math.inf` (free) or pass `lo, hi` as `Optional[int]` and treat None as unconstrained. Avoid `INT_MIN / INT_MAX` constants that could legitimately appear as node values.

??? question "Follow-up 3 — Inorder approach — why does it work?"
    Because inorder visits left → node → right, and on a BST those values are strictly increasing. One inequality break ⇒ invalid.

??? question "Follow-up 4 — Recover a BST that has two swapped values."
    Variant B. Inorder walk; find the **two** dips; swap their `.val`. **O(n)**.

??? question "Follow-up 5 — How would you parallelize the check on a million-node tree?"
    Bounds-down recursion is naturally parallel: split at the root, validate the two subtrees independently. **O(n / p)** with p workers.

##### 🐛 Common Bugs

1. **Local-only check** (Layer 1) — most common. Misses the grandparent constraint.
2. **Allowing duplicates accidentally** by using `<=` somewhere — silently passes invalid trees.
3. **Forgetting to update `prev` after the violation check** in inorder — infinite loop or wrong reject.
4. **Using `INT_MIN`/`INT_MAX` literals** that collide with legitimate node values.
5. **Mixing bounds and inorder approaches halfway through** — pick one and stick.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `True` (vacuously)
- [ ] Single node → `True`
- [ ] Two nodes in violation (e.g., left.val > root.val) → `False`
- [ ] Duplicates in tree (depending on spec) — choose `<` vs `<=` carefully
- [ ] Tree with values at `INT_MIN` / `INT_MAX` boundaries
- [ ] Deeply skewed valid BST (e.g., 1 → 2 → 3 → ... right-only) → `True`
- [ ] Deep descendant violates an ancestor's bound — must be caught

##### 🏢 Sample Interviewer Quote

> *"Validate that a binary tree is a BST."*

Your opener: *"Bounds-down recursion: pass `(lo, hi)` from the root with `(-∞, +∞)`; tighten when going left or right. Equivalent to checking inorder yields strictly increasing values. The naive `left.val < root.val < right.val` is wrong because it misses ancestor constraints. O(n), O(h)."*

---

#### Problem 13 — Path Sum II (return all root-to-leaf paths summing to target)

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Meta</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree and an integer `target`, return all **root-to-leaf** paths whose values sum to `target`. Each path is a list of node values in order from root to leaf.

##### 📖 Story Mode

This is Path Sum I (Problem 7) with two upgrades:

1. Find **all** matching paths, not just one.
2. Return the actual paths as lists of values, not just `True/False`.

The natural shape is **backtracking**: maintain a running "current path" stack; on a match at a leaf, **deepcopy** the path into the result; always **pop** when leaving a node so siblings see the right state.

##### 🌍 Real-World Usage

- **Penetration tests on permission trees** — find every permission chain that grants a target capability.
- **Game tree solvers** — every winning sequence from a given state.
- **Dependency reasoning** — every chain of requires/imports leading to a target package.
- **Decision-tree interpretability** — list every classification path leading to a given outcome.

##### 🧠 Thinking Process

Backtracking on trees has a 3-line skeleton:

```
push current node onto path
if leaf and target reached → save a copy of path
else → recurse into children
pop (restore state)
```

**The two non-obvious lines:**

- `path.copy()` (or `list(path)`) — without it, every "saved" path is a reference to the *same* list, which is later mutated.
- `path.pop()` — without the pop, the path accumulates across sibling subtrees, leaking values.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Pass the path as an argument (no shared state)"

    ```python
    def path_sum_ii_pass(root: TreeNode | None, target: int) -> list[list[int]]:
        out: list[list[int]] = []

        def go(n: TreeNode | None, rem: int, path: list[int]) -> None:
            if n is None:
                return
            new_path = path + [n.val]            # allocates each call
            if n.left is None and n.right is None and rem == n.val:
                out.append(new_path)
                return
            go(n.left,  rem - n.val, new_path)
            go(n.right, rem - n.val, new_path)

        go(root, target, [])
        return out
    ```

    Correct, but allocates a new list at every node — **O(n × h)** total memory.

=== "Layer 2 — Backtracking with a shared list"

    ```python
    def path_sum_ii(root: TreeNode | None, target: int) -> list[list[int]]:
        out: list[list[int]] = []
        path: list[int] = []

        def go(n: TreeNode | None, rem: int) -> None:
            if n is None:
                return
            path.append(n.val)
            if n.left is None and n.right is None and rem == n.val:
                out.append(path.copy())          # snapshot
            else:
                go(n.left,  rem - n.val)
                go(n.right, rem - n.val)
            path.pop()                           # backtrack

        go(root, target)
        return out
    ```

    **O(n) time** (per node), **O(h)** stack and path. The `out` itself can be O(n × h) in the worst case (every leaf is a hit on a balanced tree).

=== "Layer 3 — Iterative DFS with explicit (node, rem, path) stack"

    ```python
    def path_sum_ii_iter(root: TreeNode | None, target: int) -> list[list[int]]:
        if root is None:
            return []
        out: list[list[int]] = []
        stack: list[tuple[TreeNode, int, list[int]]] = [(root, target - root.val, [root.val])]

        while stack:
            n, rem, path = stack.pop()
            if n.left is None and n.right is None and rem == 0:
                out.append(path)
            if n.right is not None:
                stack.append((n.right, rem - n.right.val, path + [n.right.val]))
            if n.left  is not None:
                stack.append((n.left,  rem - n.left.val,  path + [n.left.val]))
        return out
    ```

    Avoids recursion. Same complexity caveats as Layer 1 (allocates per branch).

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def path_sum_ii(root: TreeNode | None, target: int) -> list[list[int]]:
        """Return all root-to-leaf paths whose values sum to `target`.

        Args:
            root: Root of the tree (may be None).
            target: Required sum.

        Returns:
            List of paths; each path is a list of values from root to leaf.

        Time:  O(n) per node, plus O(h) per emitted path for the snapshot.
        Space: O(h) recursion + path; O(n × h) worst-case output.
        """
        results: list[list[int]] = []
        running: list[int] = []

        def backtrack(node: TreeNode | None, remaining: int) -> None:
            if node is None:
                return
            running.append(node.val)
            is_leaf = node.left is None and node.right is None

            if is_leaf and remaining == node.val:
                results.append(running.copy())
            else:
                backtrack(node.left,  remaining - node.val)
                backtrack(node.right, remaining - node.val)

            running.pop()    # MUST happen on every return path

        backtrack(root, target)
        return results
    ```

=== "Layer 5 — Variants"

    **Variant A — Path sums *between any two nodes*** (Path Sum III, LC 437): not just root-to-leaf. Use a prefix-sum hash on the recursion stack.

    **Variant B — Maximum-sum root-to-leaf path:** drop the target, track `max(sum)` and the corresponding path.

    **Variant C — Number of paths summing to target** (without listing them): count with the same recursion; **O(n)**.

    **Variant D — Lexicographically smallest path summing to target:** BFS by depth; tie-break on value; first hit wins.

##### 🔍 Dry Run

Tree (target = 22):

```
            5
           / \
          4   8
         /   / \
        11  13  4
       /  \    / \
      7    2  5   1
```

| step | path before | n | rem | leaf? | match? | snapshot |
|------|-------------|---|-----|-------|--------|----------|
| 1 | [] | 5 | 22 | no | — | — |
| 2 | [5] | 4 | 17 | no | — | — |
| 3 | [5,4] | 11 | 13 | no | — | — |
| 4 | [5,4,11] | 7 | 2 | yes | 2 ≠ 7 | — |
| 5 | [5,4,11] | 2 | 2 | yes | 2 == 2 | **[5,4,11,2]** ✅ |
| 6 | [5] | 8 | 17 | no | — | — |
| 7 | [5,8] | 4 | 9 | no | — | — |
| 8 | [5,8,4] | 5 | 5 | yes | 5 == 5 | **[5,8,4,5]** ✅ |
| 9 | [5,8,4] | 1 | 5 | yes | 5 ≠ 1 | — |

Result: `[[5, 4, 11, 2], [5, 8, 4, 5]]`

##### ⏱️ Complexity

- **Time: O(n²)** worst case (every leaf produces an O(n) path snapshot).
- **Space: O(h)** for the running path plus O(total-path-length) for the output.

##### 🎯 Pattern Used

**Backtracking on trees.** The three-line skeleton (push, recurse, pop) generalizes to any tree-shaped enumeration: word search, all root-to-leaf strings, all binary tree paths, all subset-on-path-with-constraint problems.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why `path.copy()` not just `path`?"
    `path` is a *single shared list*. Without copying, every appended "path" in `out` is the same object — the next pop mutates it.

??? question "Follow-up 2 — Why `path.pop()` after the children?"
    Because the next sibling subtree must not see this branch's leftovers. The pop "unwinds" the push.

??? question "Follow-up 3 — Memory if many paths match?"
    Output dominates: O(p × h) for p matching paths each of average length h. Sometimes interviewers ask for an iterator instead of a list — yield each match with `yield path.copy()`.

??? question "Follow-up 4 — All paths between *any two* nodes summing to target?"
    Different problem (Path Sum III). Prefix-sum-hashing on the recursion stack: O(n).

??? question "Follow-up 5 — Negative values?"
    No special handling — the recursion still works. Don't prune on `rem < 0`; valid paths can dip below zero and recover.

##### 🐛 Common Bugs

1. **Forgetting `path.copy()`** — the most common bug. All saved paths end up identical (and usually empty after backtracking).
2. **Forgetting `path.pop()`** — leftovers leak into siblings.
3. **Returning early after a match** — misses other matches under the same parent.
4. **Treating internal nodes as leaves** — use the strict leaf check `n.left is None and n.right is None`.
5. **Mutating the input tree** during traversal to "mark visited."

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `[]`
- [ ] Single node, val == target → `[[val]]`
- [ ] Single node, val ≠ target → `[]`
- [ ] No leaf hits target → `[]`
- [ ] Multiple matching paths through different leaves
- [ ] Negative values present — paths still valid
- [ ] All values zero, target zero — every leaf path matches

##### 🏢 Sample Interviewer Quote

> *"Return all root-to-leaf paths summing to target."*

Your opener: *"Backtracking. Push, check at leaves, snapshot if match, recurse on children, pop. The two gotchas: copy the path before saving, and pop on every return so sibling subtrees aren't polluted. O(n²) worst case (output dominates), O(h) stack."*

---

#### Problem 14 — Construct Binary Tree from Preorder + Inorder

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Meta</span> <span class="company-tag">Bloomberg</span>

> Given two arrays `preorder` and `inorder` of the same length, where each holds the corresponding traversal of a binary tree with **unique values**, reconstruct and return the tree.

##### 📖 Story Mode

A single traversal isn't enough to reconstruct a binary tree (preorder alone, for example, has many possible matching trees). But **two carefully chosen** traversals are. The classic combo is **preorder + inorder**:

- Preorder gives you the **root** (it's always the first element).
- Inorder, given that root, splits cleanly into "everything to the left" (the left subtree) and "everything to the right" (the right subtree).

Recurse on each half. The shape *is* the algorithm.

##### 🌍 Real-World Usage

- **Deserializers** — JSON/YAML/Protobuf libraries reconstruct nested structures from a serialized stream this way.
- **Tree-shaped database snapshots** — restoring a B-tree from a sorted dump + structural metadata.
- **AST reconstruction** — parsers reconstructing syntax trees from token streams (preorder is essentially the recursive-descent path).
- **Reversible compression** — Huffman codes are decoded by walking a reconstructed binary tree.

##### 🧠 Thinking Process

> `build(preorder, inorder)`: if both empty, return None. Otherwise root = preorder[0]; find root in inorder at position `m`; the next `m` elements of preorder belong to the left subtree, the rest to the right.

Naive: `inorder.index(root_val)` is O(n), and slicing is O(n) — total O(n²) on a balanced tree, O(n²) on a chain. Speed it up by:

1. **Hashing inorder positions** (one pass, O(n)).
2. **Using indices instead of slices** to avoid array allocation.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Slicing (O(n²))"

    ```python
    def build_naive(preorder: list[int], inorder: list[int]) -> TreeNode | None:
        if not preorder:
            return None
        root_val = preorder[0]
        i = inorder.index(root_val)
        return TreeNode(
            root_val,
            build_naive(preorder[1:1 + i], inorder[:i]),
            build_naive(preorder[1 + i:],  inorder[i + 1:]),
        )
    ```

    Easy to understand, **O(n²)** time, **O(n²)** memory (slicing).

=== "Layer 2 — Index map + bounds"

    ```python
    def build_tree(preorder: list[int], inorder: list[int]) -> TreeNode | None:
        idx = {v: i for i, v in enumerate(inorder)}
        pre_i = 0

        def go(lo: int, hi: int) -> TreeNode | None:
            nonlocal pre_i
            if lo > hi:
                return None
            root_val = preorder[pre_i]
            pre_i += 1
            m = idx[root_val]
            node = TreeNode(root_val)
            node.left  = go(lo, m - 1)        # left FIRST so pre_i advances right
            node.right = go(m + 1, hi)
            return node

        return go(0, len(inorder) - 1)
    ```

    **O(n)**, **O(n)** for the hash map plus **O(h)** stack.

=== "Layer 3 — Iterative (Morris-style)"

    ```python
    def build_tree_iter(preorder: list[int], inorder: list[int]) -> TreeNode | None:
        if not preorder:
            return None
        root = TreeNode(preorder[0])
        stack: list[TreeNode] = [root]
        in_i = 0

        for v in preorder[1:]:
            node = stack[-1]
            if node.val != inorder[in_i]:
                # next preorder value is the *left* child of the top node
                node.left = TreeNode(v)
                stack.append(node.left)
            else:
                # we've hit the inorder pivot — pop until we find the right-subtree root
                while stack and stack[-1].val == inorder[in_i]:
                    node = stack.pop()
                    in_i += 1
                node.right = TreeNode(v)
                stack.append(node.right)
        return root
    ```

    **O(n)**, **O(h)** stack. No recursion. Trickier to derive — only show this if pushed.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def build_tree(preorder: list[int], inorder: list[int]) -> TreeNode | None:
        """Reconstruct a binary tree from its preorder and inorder traversals.

        All values must be distinct. Both traversals must come from the same tree.

        Args:
            preorder: Preorder traversal (root, left, right).
            inorder:  Inorder traversal  (left, root, right).

        Returns:
            Root of the reconstructed tree, or None if both inputs are empty.

        Raises:
            KeyError: if `preorder` and `inorder` are inconsistent (a value in
                      preorder is missing from inorder).

        Time:  O(n).
        Space: O(n) for the index map plus O(h) recursion stack.
        """
        if not preorder or not inorder:
            return None

        position = {value: i for i, value in enumerate(inorder)}
        pre_idx = 0

        def build(lo: int, hi: int) -> TreeNode | None:
            nonlocal pre_idx
            if lo > hi:
                return None
            root_val = preorder[pre_idx]
            pre_idx += 1
            mid = position[root_val]
            node = TreeNode(root_val)
            node.left  = build(lo, mid - 1)   # must go left first
            node.right = build(mid + 1, hi)
            return node

        return build(0, len(inorder) - 1)
    ```

=== "Layer 5 — Variants"

    **Variant A — Postorder + Inorder** (LC 106): symmetric. Postorder's *last* element is the root; consume from the end and build **right** subtree first.

    **Variant B — Preorder + Postorder** (LC 889): underdetermined unless the tree is full (every node has 0 or 2 children). Multiple valid trees match; spec usually says "any one is fine."

    **Variant C — Level-order + Inorder:** rare but doable; identify root from level-order's first, split inorder, then partition the level-order tail by membership in each side.

    **Variant D — Reconstruct an *n-ary* tree:** preorder + the children-counts at each node, or preorder + a "depth tag" stream.

##### 🔍 Dry Run

`preorder = [3, 9, 20, 15, 7]`, `inorder = [9, 3, 15, 20, 7]`

| step | pre_i | root_val | mid in inorder | left range | right range |
|------|-------|----------|----------------|------------|-------------|
| 1 | 0 | 3 | 1 | (0, 0) | (2, 4) |
| 2 (left) | 1 | 9 | 0 | (0, -1) None | (1, 0) None |
| 3 (right of 3) | 2 | 20 | 3 | (2, 2) | (4, 4) |
| 4 (left of 20) | 3 | 15 | 2 | None | None |
| 5 (right of 20) | 4 | 7 | 4 | None | None |

Tree:

```
        3
       / \
      9   20
         /  \
        15   7
```

✅

##### ⏱️ Complexity

- **Time: O(n)** for Layer 2; O(n²) for Layer 1.
- **Space: O(n)** for the index map; O(h) for stack.

##### 🎯 Pattern Used

**Divide-and-conquer driven by structural traversals.** "Pick the root from one traversal, partition the other, recurse." Same shape: build from preorder + postorder, build a BST from preorder, build a Cartesian tree.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why is preorder + inorder enough but preorder alone isn't?"
    Preorder gives the order in which nodes were *visited*. Without inorder, you can't tell where each subtree boundary is. Inorder pinpoints the boundary because the root sits between left-subtree and right-subtree.

??? question "Follow-up 2 — Postorder + Inorder?"
    Variant A. Symmetric. Postorder's *last* element is the root; build **right** subtree first to consume the postorder pointer correctly.

??? question "Follow-up 3 — What about preorder + postorder?"
    Underdetermined — unless the tree is full (every internal node has both children). Spec usually accepts any valid tree.

??? question "Follow-up 4 — Duplicates in values?"
    The position lookup becomes ambiguous. You need an external disambiguator (e.g., index identifiers per node) — the canonical problem assumes uniqueness.

??? question "Follow-up 5 — Streaming inputs?"
    Iterative Morris-style (Layer 3) processes preorder in one pass without rewinding. Inorder still needs an index lookup.

##### 🐛 Common Bugs

1. **Building the right subtree before the left** — `pre_idx` advances in the wrong order; tree gets mirrored.
2. **Re-scanning inorder with `index()` every recursion** — accidentally O(n²).
3. **Using slicing in production code** — O(n²) memory.
4. **Forgetting to `pre_idx += 1`** — infinite recursion.
5. **Off-by-one on `(lo, hi)`** — confusing inclusive vs exclusive bounds. Pick one and stick.

##### ✅ Edge Cases Checklist

- [ ] Empty inputs → `None`
- [ ] Single-node tree → just `TreeNode(preorder[0])`
- [ ] Skewed left chain (preorder == inorder reversed) → tall left tree
- [ ] Skewed right chain (preorder == inorder) → tall right tree
- [ ] Balanced tree → recursion depth O(log n)
- [ ] Negative values, zeros — handled by hash; values just need to be distinct

##### 🏢 Sample Interviewer Quote

> *"Reconstruct a binary tree from its preorder and inorder traversals."*

Your opener: *"The first preorder element is the root. Hash inorder positions for O(1) split lookup. Recurse: take next preorder element, split inorder around it, build left subtree first so the preorder pointer advances correctly. O(n), O(n) space."*

---

#### Problem 15 — Binary Tree Right Side View

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> Given the root of a binary tree, imagine yourself standing on the **right side** of it. Return the values of the nodes you can see from top to bottom.

##### 📖 Story Mode

You're physically to the right of the tree, looking through its silhouette. The closest node at each depth blocks the ones behind it. The visible "skyline" is one node per level — the **rightmost** at each depth.

Two clean approaches:

1. **BFS:** the **last** node dequeued from each level is the rightmost.
2. **DFS preferring right:** the **first** node seen at each new depth is the rightmost (because we always go right before left).

Both are O(n).

##### 🌍 Real-World Usage

- **UI overflow** — what's the "rightmost" element in each row of a tree-laid-out menu? Useful for ellipsis/truncation logic.
- **Game engines** — in shadow casting on a tree-shaped scene graph, the rightmost (or any-side) silhouette is the cast contour.
- **Org-chart visuals** — "show only the most recently promoted person at each level" is structurally identical.
- **Render-tree culling** — visible-from-side checks for occlusion in 2D layouts.

##### 🧠 Thinking Process

The BFS version writes itself: `level[-1]` per level. The DFS version is more elegant: visit right first, only append on the *first* visit at a depth.

The DFS formulation is "right-side visible" reduced to a one-line invariant: `if depth == len(out): out.append(n.val)`. Same complexity, no queue.

##### 🐍 5 Layers of Solution

=== "Layer 1 — BFS, last of each level"

    ```python
    from collections import deque

    def right_view(root: TreeNode | None) -> list[int]:
        if root is None:
            return []
        out: list[int] = []
        q: deque[TreeNode] = deque([root])
        while q:
            last = q[-1].val            # rightmost at this level (peek)
            for _ in range(len(q)):
                n = q.popleft()
                if n.left:  q.append(n.left)
                if n.right: q.append(n.right)
            out.append(last)
        return out
    ```

    **O(n)** time, **O(w)** space.

=== "Layer 2 — DFS preferring right"

    ```python
    def right_view_dfs(root: TreeNode | None) -> list[int]:
        out: list[int] = []

        def go(n: TreeNode | None, depth: int) -> None:
            if n is None:
                return
            if depth == len(out):
                out.append(n.val)        # first time we hit this depth → it's the rightmost
            go(n.right, depth + 1)
            go(n.left,  depth + 1)

        go(root, 0)
        return out
    ```

    **O(n)**, **O(h)** stack.

=== "Layer 3 — BFS overwriting per level"

    ```python
    def right_view_overwrite(root: TreeNode | None) -> list[int]:
        if root is None:
            return []
        out: list[int] = []
        q: deque[tuple[TreeNode, int]] = deque([(root, 0)])
        while q:
            n, d = q.popleft()
            if d == len(out):
                out.append(n.val)
            else:
                out[d] = n.val            # overwrite — last write wins for the level
            if n.left:  q.append((n.left,  d + 1))
            if n.right: q.append((n.right, d + 1))
        return out
    ```

    Same complexity. Reads a little less cleanly but extends naturally to "average per level," "max per level," etc.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def right_side_view(root: TreeNode | None) -> list[int]:
        """Return the values visible from the right side of the binary tree.

        Each level contributes its rightmost node's value.

        Args:
            root: Root of the tree (may be None).

        Returns:
            List of rightmost values, level by level top to bottom.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        out: list[int] = []

        def visit(node: TreeNode | None, depth: int) -> None:
            if node is None:
                return
            if depth == len(out):
                out.append(node.val)
            visit(node.right, depth + 1)
            visit(node.left,  depth + 1)

        visit(root, 0)
        return out
    ```

=== "Layer 5 — Variants"

    **Variant A — Left side view:** swap the recursion order to `left` first. Or use BFS with `level[0]` instead of `level[-1]`.

    **Variant B — Top view (LC: top view of binary tree):** for each *horizontal distance* from the root, take the first (topmost) node. BFS keyed by `(depth, hd)`; group by `hd`, take the one with the smallest depth.

    **Variant C — Bottom view:** same as top view but take the *last* node per `hd`.

    **Variant D — Boundary of binary tree (LC 545):** combines left view, leaves, and reversed right view.

##### 🔍 Dry Run

```
        1
       / \
      2   3
       \   \
        5   4
```

DFS visits in order: 1 (depth 0 → append 1), 3 (depth 1 → append 3), 4 (depth 2 → append 4), 2 (depth 1 → already filled, skip), 5 (depth 2 → already filled, skip).

Output: `[1, 3, 4]` ✅

BFS:
- Level 0: [1] → last = 1
- Level 1: [2, 3] → last = 3
- Level 2: [5, 4] → last = 4

Output: `[1, 3, 4]` ✅

##### ⏱️ Complexity

- **Time: O(n)** — every node visited once.
- **Space: O(h)** for DFS, **O(w)** for BFS, plus O(h) for the output (one entry per level).

##### 🎯 Pattern Used

**"First seen at depth"** — visit children in priority order; append only when entering a new depth. Works for many "leftmost / rightmost / topmost / bottommost" tree problems.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Left side view."
    Variant A — recurse left first; or BFS with `level[0]`.

??? question "Follow-up 2 — Why does DFS-right-first work?"
    Because the **first** node we encounter at each new depth is the rightmost we'll ever see at that depth (subsequent visits there go through left subtrees).

??? question "Follow-up 3 — Top view of a binary tree?"
    Different: use **horizontal distance** keyed BFS. The first node seen at each `hd` is the top-view node.

??? question "Follow-up 4 — Both left and right views together?"
    BFS once, append both `level[0]` and `level[-1]` per level. (Deduplicate when the level has only one node.)

??? question "Follow-up 5 — Streaming the result?"
    Generator-style DFS: `yield node.val` when entering a new depth. Caller can stop early.

##### 🐛 Common Bugs

1. **DFS that visits left first** — captures the *leftmost* per depth, not the rightmost.
2. **Using `level[len(level) - 1]`** when `level` is a deque — fine, but if you `pop` everything first, `level` may already be empty.
3. **Returning all rightmost children** — no, only one per depth, even if a level has many "rightmost branches."
4. **Confusing right-side with right-children** — a right-side view value can be a left child if the right side is missing at that depth.
5. **Empty tree returning `[None]`** instead of `[]`.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `[]`
- [ ] Single node → `[val]`
- [ ] Right-only chain → all node values
- [ ] Left-only chain → all node values (left child is the only / rightmost at each depth)
- [ ] Tree where right subtree is shallower than left — left children "fill in" at the bottom levels
- [ ] Deeply unbalanced tree

##### 🏢 Sample Interviewer Quote

> *"Return the right-side view of a binary tree."*

Your opener: *"DFS, right-first; on first visit to each depth, append the node value. O(n), O(h). Or BFS where I take `level[-1]` per level — same complexity. The DFS version is shorter."*

---

#### Problem 16 — Lowest Common Ancestor (binary tree)

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Meta</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">LinkedIn</span> <span class="company-tag">Apple</span>

> Given the root of a binary tree and two nodes `p` and `q` in the tree, return their **lowest common ancestor (LCA)** — the *deepest* node that has both `p` and `q` as descendants. A node is considered a descendant of itself.

##### 📖 Story Mode

In a family tree, the LCA of two cousins is their nearest shared grandparent. In a git commit DAG, the LCA of two branches is the **merge base** — the most recent common commit. The recursion that finds it is one of the most elegant in the chapter:

> Walk postorder. At each node, check both subtrees. If both come back with a hit (one for each target), **this** node is the LCA — neither subtree alone contained both. Otherwise, propagate up whichever subtree had the hit.

##### 🌍 Real-World Usage

- **Git merge-base** (`git merge-base A B`) — the LCA of two branches on the commit DAG.
- **File-system "common parent directory"** — for two paths.
- **Class hierarchy** — least specific common base class for multiple inheritance lookups.
- **Phylogenetics** — most recent common ancestor of two species.

##### 🧠 Thinking Process

The trick is the **postorder return value**:

- `None` if the subtree contains neither p nor q.
- `p` (or `q`) if the subtree contains exactly one of them.
- A common ancestor (the LCA so far) if the subtree contains both.

The recursion combines the two children's returns:

- Both non-null → this node is the split point → return `self`.
- One non-null → propagate it up.
- Both null → return None.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Postorder recursive (canonical)"

    ```python
    def lca(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
        if root is None or root is p or root is q:
            return root
        left  = lca(root.left,  p, q)
        right = lca(root.right, p, q)
        if left and right:
            return root              # found p in one subtree, q in the other
        return left if left else right
    ```

    **O(n)**, **O(h)**.

=== "Layer 2 — Iterative with parent pointers"

    ```python
    def lca_iter(root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode | None:
        # 1) BFS to build a parent map.
        parent: dict[TreeNode, TreeNode | None] = {root: None}
        stack: list[TreeNode] = [root]
        while p not in parent or q not in parent:
            n = stack.pop()
            if n.left:
                parent[n.left]  = n
                stack.append(n.left)
            if n.right:
                parent[n.right] = n
                stack.append(n.right)

        # 2) Walk p's ancestors into a set; then walk q's ancestors and find the first hit.
        ancestors: set[TreeNode] = set()
        node: TreeNode | None = p
        while node is not None:
            ancestors.add(node)
            node = parent[node]
        node = q
        while node not in ancestors:
            node = parent[node]
        return node
    ```

    **O(n)** time and space. Useful when `p` and `q` aren't pointers but identifiers.

=== "Layer 3 — Path-from-root approach"

    ```python
    def lca_path(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
        def find_path(n: TreeNode | None, target: TreeNode, path: list[TreeNode]) -> bool:
            if n is None:
                return False
            path.append(n)
            if n is target:
                return True
            if find_path(n.left, target, path) or find_path(n.right, target, path):
                return True
            path.pop()
            return False

        path_p: list[TreeNode] = []
        path_q: list[TreeNode] = []
        find_path(root, p, path_p)
        find_path(root, q, path_q)

        last: TreeNode | None = None
        for a, b in zip(path_p, path_q):
            if a is b:
                last = a
            else:
                break
        return last
    ```

    Conceptually clean (compute paths, walk both until they diverge), but **O(n)** with two passes plus path memory. Use Layer 1 in interviews.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def lowest_common_ancestor(
        root: TreeNode | None,
        p: TreeNode,
        q: TreeNode,
    ) -> TreeNode | None:
        """Return the lowest common ancestor of `p` and `q` in the binary tree.

        A node is its own ancestor — if `p` is an ancestor of `q`, the answer is `p`.

        Args:
            root: Root of the tree.
            p: First target node (must be present in the tree).
            q: Second target node (must be present in the tree).

        Returns:
            The deepest node that has both `p` and `q` as descendants.
            None if either target is not in the tree.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        if root is None:
            return None
        if root is p or root is q:
            return root

        left  = lowest_common_ancestor(root.left,  p, q)
        right = lowest_common_ancestor(root.right, p, q)

        if left is not None and right is not None:
            return root
        return left if left is not None else right
    ```

=== "Layer 5 — Variants"

    **Variant A — LCA on a BST** (Problem 17): walk down using value comparisons. **O(h)**.

    **Variant B — LCA with parent pointers and no root** — given just `p` and `q`, walk up from both, equalize depths, then walk in lockstep until equal. **O(h)**.

    **Variant C — k-LCA** (lowest common ancestor of *k* nodes): generalize the postorder; return the count of targets seen; the first node with count == k is the answer.

    **Variant D — Online LCA** with many queries: preprocess in O(n) with Tarjan's offline LCA or sparse-table-based Euler-tour LCA for O(1) per query.

##### 🔍 Dry Run

Tree:

```
        3
       / \
      5   1
     / \  / \
    6  2 0   8
      / \
     7   4
```

Find LCA of 5 and 1:

| call | root | left | right | returns |
|------|------|------|-------|---------|
| lca(3) | left=lca(5)→5 | right=lca(1)→1 | both non-null | **3** ✅ |

Find LCA of 5 and 4:

| call | root | left | right | returns |
|------|------|------|-------|---------|
| lca(2) | left=lca(7)→None | right=lca(4)→4 | only right | 4 |
| lca(5) | hit 5 itself | — | — | **5** (5 is ancestor of 4) ✅ |

##### ⏱️ Complexity

- **Time: O(n)** — every node visited at most once.
- **Space: O(h)** stack.

##### 🎯 Pattern Used

**Postorder propagation with split detection.** The "first node where both sides return non-null" idiom appears in: largest BST subtree, max path sum, k-th ancestor, lowest common ancestor of multiple nodes.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if `p` or `q` isn't in the tree?"
    The plain recursion may return a non-null node (the one that *is* in the tree). To detect missing targets, return `(node, p_seen, q_seen)` from each recursion and verify both flags at the root.

??? question "Follow-up 2 — LCA on a BST?"
    Problem 17. Walk down using values: first node between `p.val` and `q.val` is the LCA. O(h), O(1) extra.

??? question "Follow-up 3 — Many LCA queries on the same tree?"
    Preprocess with Euler-tour + sparse-table RMQ → O(1) per query. Or use Tarjan's offline algorithm if all queries are known up front.

??? question "Follow-up 4 — LCA without root, only with parent pointers?"
    Climb from both nodes; equalize depths; lockstep walk until equal. **O(h)**.

??? question "Follow-up 5 — LCA of k nodes?"
    Generalize the postorder: return the count of targets contained; the deepest node whose count == k is the LCA.

##### 🐛 Common Bugs

1. **Returning early when `root is p or root is q`** — that's correct *only* if you accept that `p` (or `q`) can be the LCA when it's an ancestor of the other.
2. **Comparing values instead of identity** when nodes can have duplicate values — use `is`, not `==`.
3. **Confusing "split" detection with "found one"** — `if left and right` means split → return self; otherwise propagate.
4. **Treating it like a BST** when it's not — value-based descent only works on a BST.
5. **Failing to handle a missing target silently** — see Follow-up 1.

##### ✅ Edge Cases Checklist

- [ ] `p == q` → returns `p`
- [ ] One is the ancestor of the other → returns the ancestor
- [ ] Both are leaves → their first common ancestor walking up
- [ ] Tree with a single node → that node (if it's the target)
- [ ] `p` not in tree → see Follow-up 1
- [ ] Both targets in the same subtree → LCA is inside that subtree, not the root

##### 🏢 Sample Interviewer Quote

> *"Find the lowest common ancestor of two nodes in a binary tree."*

Your opener: *"Postorder recursion. Return self when I see p or q; recurse on both subtrees. If both children return non-null, I'm the split point — return self. Otherwise propagate the non-null one. O(n), O(h). I can adapt this to a BST for O(h), or with parent pointers for O(h) without the tree root."*

---

#### Problem 17 — Lowest Common Ancestor on a BST

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> Given the root of a Binary Search Tree (BST) and two nodes `p` and `q` in the tree (`p.val ≠ q.val`), return their lowest common ancestor.

##### 📖 Story Mode

On a BST, the LCA is dramatically cheaper than on a generic binary tree. The reason: **values themselves tell you where to go**. If both targets are smaller than the current node, descend left; if both are larger, descend right; otherwise, this node *is* the LCA — the targets diverge here.

This is the cleanest LCA algorithm in any tree variant. **O(h)**, **O(1)** extra space, no recursion needed.

##### 🌍 Real-World Usage

- **B-tree directories** — finding the common parent of two index keys.
- **Range index probes** — the "split point" of a range query is the LCA of its endpoints.
- **DNS lookup trees** — the LCA of two DNS labels in a hierarchical zone tree.
- **Geo-tries / k-d trees** — the bounding region containing two points.

##### 🧠 Thinking Process

The BST invariant `left < node < right` lets you decide direction by comparing values:

- If `node.val < lo` → both targets are larger → go right.
- If `node.val > hi` → both targets are smaller → go left.
- Otherwise → `lo ≤ node.val ≤ hi` → split point → return.

`lo` and `hi` are `min(p.val, q.val)` and `max(p.val, q.val)`.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Iterative (canonical for BST)"

    ```python
    def lca_bst(root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode | None:
        lo, hi = min(p.val, q.val), max(p.val, q.val)
        node: TreeNode | None = root
        while node is not None:
            if node.val < lo:
                node = node.right
            elif node.val > hi:
                node = node.left
            else:
                return node
        return None    # unreachable if p, q are both in the tree
    ```

    **O(h)** time, **O(1)** extra. The interview gold standard.

=== "Layer 2 — Recursive"

    ```python
    def lca_bst_rec(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
        if root is None:
            return None
        if p.val < root.val and q.val < root.val:
            return lca_bst_rec(root.left, p, q)
        if p.val > root.val and q.val > root.val:
            return lca_bst_rec(root.right, p, q)
        return root
    ```

    **O(h)** time, **O(h)** stack. Equivalent semantics; many interviewers prefer Layer 1 because it's tail-recursive in disguise.

=== "Layer 3 — Treat as a generic binary tree (Problem 16)"

    ```python
    def lca_generic(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
        if root is None or root is p or root is q:
            return root
        L = lca_generic(root.left,  p, q)
        R = lca_generic(root.right, p, q)
        if L and R:
            return root
        return L if L else R
    ```

    Works on any tree, but **O(n)** instead of O(h). Avoid on BSTs unless you can't trust the BST property.

=== "Layer 4 — Production-ready"

    ```python
    from __future__ import annotations


    def lowest_common_ancestor_bst(
        root: TreeNode,
        p: TreeNode,
        q: TreeNode,
    ) -> TreeNode | None:
        """Return the LCA of `p` and `q` in a BST.

        Walks down from the root using value comparisons. The first node whose
        value falls between p.val and q.val (inclusive) is the LCA.

        Args:
            root: Root of a non-empty BST.
            p: First target (must be in the tree).
            q: Second target (must be in the tree).

        Returns:
            The deepest node that is an ancestor of both p and q.
            None if the tree is empty.

        Time:  O(h).
        Space: O(1).
        """
        lo, hi = (p.val, q.val) if p.val < q.val else (q.val, p.val)

        node: TreeNode | None = root
        while node is not None:
            if node.val < lo:
                node = node.right
            elif node.val > hi:
                node = node.left
            else:
                return node
        return None
    ```

=== "Layer 5 — Variants"

    **Variant A — Range count (LC 938 "Range Sum of BST"):** start at the LCA of `(lo, hi)` and sum from there.

    **Variant B — k-LCA on a BST:** find `min(targets)` and `max(targets)`, then the LCA-of-range walk. Same O(h).

    **Variant C — When `p` or `q` may not be in the tree:** verify both exist before/after.

    **Variant D — LCA on a *self-balancing* BST under updates:** O(log n) per query as the tree height stays log n.

##### 🔍 Dry Run

```
            6
           / \
          2   8
         / \ / \
        0  4 7  9
          / \
         3   5
```

LCA of 2 and 8: lo=2, hi=8.
- root=6 → 2 ≤ 6 ≤ 8 → return 6 ✅

LCA of 2 and 4: lo=2, hi=4.
- root=6 → 6 > 4 → go left.
- node=2 → 2 ≤ 2 ≤ 4 → return 2 ✅

LCA of 3 and 5: lo=3, hi=5.
- root=6 → 6 > 5 → go left.
- node=2 → 2 < 3 → go right.
- node=4 → 3 ≤ 4 ≤ 5 → return 4 ✅

##### ⏱️ Complexity

- **Time: O(h)** — at worst the height of the tree (log n on a balanced BST, n on a skewed one).
- **Space: O(1)** for Layer 1.

##### 🎯 Pattern Used

**Top-down value-driven descent.** The BST property turns "search for a structural property" into "compare and branch." Same shape as: insert, search, delete, range sum, kth-smallest (with subtree-size augmentation).

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why does this work?"
    On a BST, every value in `node.left` is `< node.val` and every value in `node.right` is `> node.val`. If both targets are smaller, both lie in the left subtree → recurse left. If both larger → right. Otherwise the targets straddle this node → split point.

??? question "Follow-up 2 — What if `p` and `q` aren't in the tree but you're given just their *values*?"
    Same algorithm. The LCA of two values is well-defined by the BST shape — it's the deepest node whose value is in `[lo, hi]`.

??? question "Follow-up 3 — What if the BST is augmented with subtree sizes?"
    The LCA descent still costs O(h), but now you can count nodes in the range `[lo, hi]` along the way in the same walk.

??? question "Follow-up 4 — What if the tree is *not* actually a BST but the spec says it is?"
    Trust-but-verify: if you're paranoid, run a `is_valid_bst` check first. If it fails, fall back to Problem 16's O(n) algorithm.

??? question "Follow-up 5 — LCA on a BST stored on disk (each node access is expensive)?"
    The single root-to-LCA path is the *minimum* number of disk reads possible: O(h). No algorithm can beat that.

##### 🐛 Common Bugs

1. **Forgetting to swap `p.val` and `q.val`** so that `lo ≤ hi` — otherwise comparisons are inverted.
2. **Using strict `<` / `>`** when a target equals `node.val` — that target *is* the LCA. Use `< lo` and `> hi`, treat the boundary as "split."
3. **Recursing in both directions** — defeats the BST advantage; reverts to O(n).
4. **Treating the tree as a BST when it isn't** — silent wrong answers.
5. **Forgetting the empty-tree case** — `None` input should return `None`.

##### ✅ Edge Cases Checklist

- [ ] `p` or `q` is the root → root is the LCA
- [ ] `p` is an ancestor of `q` → `p` is the LCA
- [ ] `p == q` (same node) → that node
- [ ] Both leaves on the same side → walk down that side
- [ ] Targets straddle the root → root is the LCA
- [ ] Skewed BST (chain) → still O(h) = O(n) here

##### 🏢 Sample Interviewer Quote

> *"Find the LCA in a BST."*

Your opener: *"Walk down from the root. If both targets are smaller than the current node, go left; if both are larger, go right; otherwise this node is the LCA. O(h), O(1) extra. The BST invariant gives us the cheapest LCA in any tree variant."*

---

#### Problem 18 — Kth Smallest Element in a BST

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Uber</span>

> Given the root of a Binary Search Tree (BST) and an integer `k`, return the **k-th smallest** value in the tree (1-indexed).

##### 📖 Story Mode

A BST's **inorder traversal** visits values in sorted order. So the k-th smallest is just "the k-th value yielded by an inorder walk" — and we can stop as soon as we've yielded k.

If the tree is small, this is O(h + k). If the tree is large but k is, say, 1, we're done in O(h). And if you need to support frequent kth-smallest queries on a tree that's also being modified, you augment each node with the **subtree size** — then each query is O(h).

##### 🌍 Real-World Usage

- **Database "k-th percentile"** queries on an indexed column.
- **Order-statistic trees** — augmented BSTs are the standard solution to "find the median of a stream while supporting updates" (alongside two-heaps).
- **Leaderboard rank** queries — "give me the player at rank k."
- **Quantile queries on histograms** — augmented BSTs support `select(k)` and `rank(value)` in O(log n).

##### 🧠 Thinking Process

Inorder traversal yields BST values in ascending order. So:

> `kth_smallest = the kth value yielded by inorder(root)`.

Iterative inorder is the cleanest implementation — we can stop early. Recursive inorder also works but you'd need a `nonlocal` counter and an early-exit signal.

For repeated queries on a mutating tree, **augment** each node with `size = 1 + size(left) + size(right)`. Then the lookup walks down: compare `k` to `size(node.left) + 1`; recurse appropriately. **O(h) per query**, **O(log n) per insert/delete** to update sizes.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Recursive inorder, full traversal"

    ```python
    def kth_smallest_full(root: TreeNode | None, k: int) -> int:
        out: list[int] = []

        def inorder(n: TreeNode | None) -> None:
            if n is None:
                return
            inorder(n.left)
            out.append(n.val)
            inorder(n.right)

        inorder(root)
        return out[k - 1]
    ```

    **O(n)** time, **O(n)** space. Fine for small trees, wasteful for large ones.

=== "Layer 2 — Iterative inorder with early stop"

    ```python
    def kth_smallest(root: TreeNode | None, k: int) -> int:
        stack: list[TreeNode] = []
        node = root
        while node is not None or stack:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            k -= 1
            if k == 0:
                return node.val
            node = node.right
        raise ValueError("k out of range")
    ```

    **O(h + k)** time, **O(h)** space. The standard answer.

=== "Layer 3 — Recursive with early-exit closure"

    ```python
    def kth_smallest_rec(root: TreeNode | None, k: int) -> int:
        result: int | None = None
        count = 0

        def go(n: TreeNode | None) -> None:
            nonlocal count, result
            if n is None or result is not None:
                return
            go(n.left)
            count += 1
            if count == k:
                result = n.val
                return
            go(n.right)

        go(root)
        if result is None:
            raise ValueError("k out of range")
        return result
    ```

    Same complexity, slightly more boilerplate.

=== "Layer 4 — Order-statistic tree (augmented with size)"

    ```python
    @dataclass
    class StatNode:
        val: int
        left:  "StatNode | None" = None
        right: "StatNode | None" = None
        size:  int = 1   # 1 + size(left) + size(right)


    def kth_smallest_os(root: StatNode | None, k: int) -> int:
        node = root
        while node is not None:
            left_size = node.left.size if node.left else 0
            if k == left_size + 1:
                return node.val
            if k <= left_size:
                node = node.left
            else:
                k -= left_size + 1
                node = node.right
        raise ValueError("k out of range")
    ```

    **O(h) per query**. Maintain `size` on insert/delete (also O(h)). The standard "order statistic tree" pattern.

=== "Layer 5 — Production-ready (Layer 2 with edge cases)"

    ```python
    from __future__ import annotations


    def kth_smallest(root: TreeNode | None, k: int) -> int:
        """Return the k-th smallest value in a BST (1-indexed).

        Args:
            root: Root of the BST.
            k:    Rank to retrieve (1 ≤ k ≤ size of tree).

        Returns:
            The k-th smallest value.

        Raises:
            ValueError: if `k` is out of range or the tree is empty.

        Time:  O(h + k).
        Space: O(h).
        """
        if root is None or k < 1:
            raise ValueError("Empty tree or k < 1")

        stack: list[TreeNode] = []
        node = root
        remaining = k
        while node is not None or stack:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            remaining -= 1
            if remaining == 0:
                return node.val
            node = node.right

        raise ValueError("k out of range")
    ```

##### 🔍 Dry Run

```
        5
       / \
      3   6
     / \
    2   4
   /
  1
```

`k = 3`. Inorder visits `1, 2, 3, 4, 5, 6`. After 3 yields, we stop at `3`.

| step | stack | node | remaining | yield |
|------|-------|------|-----------|-------|
| 1 | [5] | 5 | 3 | — |
| 2 | [5, 3] | 3 | 3 | — |
| 3 | [5, 3, 2] | 2 | 3 | — |
| 4 | [5, 3, 2, 1] | 1 | 3 | — |
| 5 | [5, 3, 2] | None (popped 1) | 2 | yielded 1 |
| 6 | [5, 3] | None | 1 | yielded 2 |
| 7 | [5] | 4 (3.right) | 1 | yielded 3 |
| 8 | [5, 4] | None | 0 | yielded 4? wait — recompute |

Let me redo: after yielding 1, remaining=2; after yielding 2, remaining=1; after yielding 3, remaining=0 → return **3** ✅.

##### ⏱️ Complexity

- **Time: O(h + k)** for Layer 2; **O(n)** for Layer 1; **O(h)** for the augmented tree.
- **Space: O(h)** for the iterative stack.

##### 🎯 Pattern Used

**Iterative inorder with early stop** — same pattern as "next inorder successor" and "iterator over BST." The augmented variant is the **order-statistic tree** pattern from advanced data structures.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if the BST is modified often and k-th queries are frequent?"
    Augment with subtree sizes (Layer 4). Each query is O(h); each insert/delete updates sizes along the affected path, also O(h). On a balanced BST (AVL/RB), all operations are O(log n).

??? question "Follow-up 2 — Kth largest?"
    Reverse inorder (right → node → left), or compute `n - k + 1` smallest.

??? question "Follow-up 3 — Stream of values, find k-th smallest at any time?"
    Two-heap median trick generalized: a max-heap of the smallest k values gives you O(log k) per insert and O(1) for the k-th smallest.

??? question "Follow-up 4 — All k smallest values?"
    Same iterative inorder; collect into a list of length k.

??? question "Follow-up 5 — Approximate k-th in a giant tree?"
    Reservoir-sample or use a quantile sketch (t-digest, Greenwald-Khanna). Trades exactness for memory.

##### 🐛 Common Bugs

1. **0-indexing vs 1-indexing** — the spec usually says 1-indexed; make sure your loop matches.
2. **Forgetting to push the right child** — yields a wrong inorder.
3. **Using a recursive inorder without early exit** — silent O(n) when O(h+k) is achievable.
4. **Decrementing `k` in the wrong place** — must be after popping a node, not when pushing.
5. **Using `list.pop(0)` for a queue-like access** — not relevant here, but a common trap in similar problems.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → raise / return error
- [ ] k = 1 → return the leftmost (smallest)
- [ ] k = size → return the rightmost (largest)
- [ ] k > size → raise / return error
- [ ] Skewed left chain → kth smallest is the kth from the bottom
- [ ] Skewed right chain → kth smallest is the kth from the top
- [ ] Duplicates allowed (depends on spec) — handle via `<= ` semantics consistently

##### 🏢 Sample Interviewer Quote

> *"Find the k-th smallest element in a BST."*

Your opener: *"Iterative inorder, decrement k as we pop; stop when k hits zero. O(h + k), O(h). If we expect frequent queries with mutations, I'd augment each node with a subtree size — every query then becomes O(h)."*

---

#### Problem 19 — Serialize and Deserialize a Binary Tree

<span class="diff-hard">Hard</span> <span class="company-tag">LinkedIn</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Meta</span>

> Design an algorithm to **serialize** a binary tree to a string and **deserialize** the string back to the original tree. The serialized form can be any string; round-tripping must reconstruct the tree exactly.

##### 📖 Story Mode

Imagine you have an in-memory tree on machine A and need to ship it to machine B. Pointers can't cross the wire — only **bytes** can. Serialization converts the tree to a flat string; deserialization rebuilds it on the other side.

The classic trick: a single **preorder traversal with `null` sentinels** uniquely identifies the structure. No need to ship inorder + preorder separately. The sentinels mark every empty child, so the parser knows exactly where each subtree ends.

##### 🌍 Real-World Usage

- **Distributed systems** — shipping ASTs, DOM snapshots, decision trees, or game-state trees between processes.
- **Caching** — Redis stores serialized blobs; when you fetch, you must rebuild the structure.
- **Persistent storage** — saving a tree to a file and loading it back later.
- **Network protocols** — gRPC/Thrift use schema-driven serialization but the round-trip property is the same.
- **Snapshot/replay debugging** — capture a tree state, ship it to your laptop, replay locally.

##### 🧠 Thinking Process

Two questions to answer:

1. **Which traversal order?** Preorder (root → left → right) is easiest because it reconstructs top-down — you build the parent before its children.
2. **How to mark empty subtrees?** A sentinel like `#` or `null`. Without sentinels, you can't recover the shape (e.g. is "1,2,3" a left-only chain or a balanced tree?).

> **Why preorder works alone:** the very first token is always the root. Then the next tokens are the entire left subtree (recursively), then the right subtree. The `null` sentinels ensure each recursive call knows when to stop.

For inorder alone, the root's position is ambiguous. For postorder alone, you'd build bottom-up — fine, but mirror of preorder.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Preorder with null sentinels (recursive)"

    ```python
    NULL = "#"
    SEP  = ","


    def serialize(root: TreeNode | None) -> str:
        parts: list[str] = []

        def go(n: TreeNode | None) -> None:
            if n is None:
                parts.append(NULL)
                return
            parts.append(str(n.val))
            go(n.left)
            go(n.right)

        go(root)
        return SEP.join(parts)


    def deserialize(data: str) -> TreeNode | None:
        it = iter(data.split(SEP))

        def go() -> TreeNode | None:
            tok = next(it)
            if tok == NULL:
                return None
            node = TreeNode(int(tok))
            node.left  = go()
            node.right = go()
            return node

        return go()
    ```

    **O(n)** time and space. The cleanest solution.

=== "Layer 2 — Iterative preorder serialize"

    ```python
    def serialize_iter(root: TreeNode | None) -> str:
        if root is None:
            return NULL
        parts: list[str] = []
        stack: list[TreeNode | None] = [root]
        while stack:
            n = stack.pop()
            if n is None:
                parts.append(NULL)
                continue
            parts.append(str(n.val))
            # push right first so left is processed first
            stack.append(n.right)
            stack.append(n.left)
        return SEP.join(parts)
    ```

    Useful when recursion depth is a concern (a 10⁶-node skewed tree blows the stack).

=== "Layer 3 — BFS / level-order with sentinels"

    ```python
    from collections import deque


    def serialize_bfs(root: TreeNode | None) -> str:
        if root is None:
            return ""
        parts: list[str] = []
        q: deque[TreeNode | None] = deque([root])
        while q:
            n = q.popleft()
            if n is None:
                parts.append(NULL)
                continue
            parts.append(str(n.val))
            q.append(n.left)
            q.append(n.right)
        return SEP.join(parts)


    def deserialize_bfs(data: str) -> TreeNode | None:
        if not data:
            return None
        toks = data.split(SEP)
        root = TreeNode(int(toks[0]))
        q: deque[TreeNode] = deque([root])
        i = 1
        while q and i < len(toks):
            parent = q.popleft()
            if toks[i] != NULL:
                parent.left = TreeNode(int(toks[i]))
                q.append(parent.left)
            i += 1
            if i < len(toks) and toks[i] != NULL:
                parent.right = TreeNode(int(toks[i]))
                q.append(parent.right)
            i += 1
        return root
    ```

    Matches LeetCode's display format. Friendlier for humans, slightly more code.

=== "Layer 4 — Compact (postorder + binary)"

    ```python
    # When values fit in 4 bytes, pack them with struct for a tighter wire format.
    import struct


    def serialize_bin(root: TreeNode | None) -> bytes:
        out = bytearray()

        def go(n: TreeNode | None) -> None:
            if n is None:
                out.append(0)              # 1-byte sentinel
                return
            out.append(1)
            out.extend(struct.pack(">i", n.val))   # 4-byte big-endian int
            go(n.left)
            go(n.right)

        go(root)
        return bytes(out)
    ```

    Useful for network protocols where every byte counts. Inorder tradeoff: not human-readable.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    class Codec:
        """Serialize and deserialize a binary tree.

        The format is a comma-separated preorder traversal with `#` for nulls.
        Round-trip is guaranteed to reconstruct an identical tree.

        Time:  O(n) for both directions.
        Space: O(n) for the output string and the recursion stack.
        """

        NULL = "#"
        SEP  = ","

        def serialize(self, root: TreeNode | None) -> str:
            parts: list[str] = []

            def preorder(n: TreeNode | None) -> None:
                if n is None:
                    parts.append(self.NULL)
                    return
                parts.append(str(n.val))
                preorder(n.left)
                preorder(n.right)

            preorder(root)
            return self.SEP.join(parts)

        def deserialize(self, data: str) -> TreeNode | None:
            if not data:
                return None
            it = iter(data.split(self.SEP))

            def build() -> TreeNode | None:
                tok = next(it, None)
                if tok is None or tok == self.NULL:
                    return None
                node = TreeNode(int(tok))
                node.left  = build()
                node.right = build()
                return node

            return build()
    ```

##### 🔍 Dry Run

```
    1
   / \
  2   3
     / \
    4   5
```

**Serialize (preorder + null sentinels):**

| step | visit | parts |
|------|-------|-------|
| 1 | 1 | `[1]` |
| 2 | 2 | `[1, 2]` |
| 3 | 2.left null | `[1, 2, #]` |
| 4 | 2.right null | `[1, 2, #, #]` |
| 5 | 3 | `[1, 2, #, #, 3]` |
| 6 | 4 | `[1, 2, #, #, 3, 4]` |
| 7-8 | 4's nulls | `[1, 2, #, #, 3, 4, #, #]` |
| 9 | 5 | `[..., 5]` |
| 10-11 | 5's nulls | `[..., 5, #, #]` |

Output: `"1,2,#,#,3,4,#,#,5,#,#"`.

**Deserialize:** consumes tokens left-to-right, building each subtree before moving on.

##### ⏱️ Complexity

- **Time: O(n)** for both serialize and deserialize — each node visited once.
- **Space: O(n)** for the output string + **O(h)** for the recursion stack.

##### 🎯 Pattern Used

**Preorder traversal with null sentinels** — the canonical "uniquely identify tree shape" technique. Generalizes to N-ary trees by also recording each node's child count.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Can you do it with a non-recursive serialize?"
    Yes — use an explicit stack as in Layer 2. Push right before left so left is processed first.

??? question "Follow-up 2 — What if the tree is a BST?"
    You can drop the null sentinels: a preorder of a BST uniquely identifies its shape because BST ordering disambiguates left vs right. **O(n)** to serialize, **O(n)** to deserialize using the "next greater" trick.

??? question "Follow-up 3 — N-ary tree?"
    Two options: (a) preorder with a child-count token before each node's children; (b) preorder with `null` between siblings. LeetCode 428 walks through both.

??? question "Follow-up 4 — Optimize the wire size?"
    Layer 4's binary packing. Or run-length encode long null runs. Or use a tag-length-value format like Protocol Buffers.

??? question "Follow-up 5 — How would you handle very deep trees?"
    Recursion can blow the stack. Switch to the iterative version (Layer 2). For Python, also bump `sys.setrecursionlimit()` as a quick workaround.

??? question "Follow-up 6 — Serialize across endian-different machines?"
    For text formats (Layer 1-3) it doesn't matter. For binary (Layer 4), pin the byte order with `struct.pack(">i", ...)` (`>` = big-endian).

##### 🐛 Common Bugs

1. **Forgetting null sentinels** — `"1,2,3"` is ambiguous (left-only chain vs. balanced).
2. **Using `' '` as separator** — values can contain spaces in some languages; pick a separator that values can't contain (or escape).
3. **Not handling empty tree** — `serialize(None)` should still round-trip cleanly. Most clean: `""` or `"#"`.
4. **Recursive deserialize without iterator state** — using an index `int` doesn't carry mutations; pass an iterator or a list with `idx[0]`.
5. **`int(tok)` on `#`** — guard against the sentinel before parsing.
6. **Stack overflow on deep trees** — Layer 1 recursion fails for n > ~10⁵ in Python without raising the recursion limit.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → serialize to `""` or `"#"`, deserialize back to `None`
- [ ] Single node → `"42,#,#"` round-trips
- [ ] Skewed left chain → all right children are `#`
- [ ] Skewed right chain → symmetric
- [ ] Negative values → `"-7"` parses fine
- [ ] Duplicate values → fine; nodes are independent
- [ ] Very deep tree → use iterative variant
- [ ] Values with the separator character → escape or pick a different separator

##### 🏢 Sample Interviewer Quote

> *"Design an algorithm to serialize and deserialize a binary tree."*

Your opener: *"Preorder traversal with `null` sentinels — that's enough to uniquely encode the tree. Comma-separated string. Serialize is a recursive preorder; deserialize is a recursive build that consumes tokens in order. O(n) time and space both ways."*

---

#### Problem 20 — Flatten Binary Tree to Linked List

<span class="diff-medium">Medium</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Amazon</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree, **flatten it in-place** into a right-only linked list. The "list" should follow the **preorder** traversal of the original tree. Every node's `left` becomes `None` and `right` points to the next node in preorder.

##### 📖 Story Mode

Picture rotating the tree so all the left arms swing down to become tails of right chains. The flattened result reads exactly like the preorder traversal — root first, then everything from the left subtree, then everything from the right subtree.

The cleanest formulation: for each node, **splice the entire left subtree between the node and its right subtree**, then null out the left pointer. Do that recursively (or iteratively with Morris) and the tree collapses into a right-only spine.

##### 🌍 Real-World Usage

- **Tree-to-stream conversion** — flattening a parse tree for serialization or pretty-printing.
- **In-place transformations on persistent data structures** — saves memory.
- **DOM linearization** — converting a nested DOM into a flat reading-order list for accessibility tools.
- **Compiler IR passes** — flattening expression trees into single-successor block lists.

##### 🧠 Thinking Process

The desired order is **preorder**: `node, left subtree (preorder), right subtree (preorder)`. Three approaches, increasing in elegance:

1. **Capture preorder into a list, rewire pointers in a second pass.** Easy but uses O(n) extra memory.
2. **Recursive splice** — for each node, recursively flatten left + right, then splice the left chain in. O(h) recursion, O(1) extra besides the stack.
3. **Morris-style iterative** — no recursion at all. For each node with a left child, find the **rightmost** node of the left subtree (its preorder predecessor of `cur.right`), point that node's `right` to `cur.right`, then move `cur.left` to `cur.right`. Walk down the right chain.

> **Key insight (Morris):** the right tip of a left subtree is exactly the predecessor of the original right child in preorder. So inserting the right subtree after that tip preserves preorder.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Collect preorder, then rewire"

    ```python
    def flatten_collect(root: TreeNode | None) -> None:
        if root is None:
            return
        order: list[TreeNode] = []

        def pre(n: TreeNode | None) -> None:
            if n is None:
                return
            order.append(n)
            pre(n.left)
            pre(n.right)

        pre(root)
        for i in range(len(order) - 1):
            order[i].left  = None
            order[i].right = order[i + 1]
        order[-1].left = order[-1].right = None
    ```

    **O(n)** time, **O(n)** space. Easy to reason about; uses extra memory.

=== "Layer 2 — Recursive splice (returns tail)"

    ```python
    def flatten_rec(root: TreeNode | None) -> None:
        def go(n: TreeNode | None) -> TreeNode | None:
            """Flatten the subtree rooted at n; return its tail (last node)."""
            if n is None:
                return None
            l_tail = go(n.left)
            r_tail = go(n.right)
            if n.left is not None:
                # Splice the left chain between n and its original right.
                (l_tail or n.left).right = n.right
                n.right = n.left
                n.left  = None
            return r_tail or l_tail or n

        go(root)
    ```

    **O(n)** time, **O(h)** stack space. Very clean once you trust the contract.

=== "Layer 3 — Reverse-postorder one-pointer"

    ```python
    def flatten_revpost(root: TreeNode | None) -> None:
        prev: TreeNode | None = None

        def go(n: TreeNode | None) -> None:
            nonlocal prev
            if n is None:
                return
            go(n.right)
            go(n.left)
            n.right = prev
            n.left  = None
            prev = n

        go(root)
    ```

    Walks **right → left → root** (reverse of preorder) and threads each node onto a growing chain via `prev`. Elegant.

=== "Layer 4 — Morris-style iterative, O(1) extra space"

    ```python
    def flatten_morris(root: TreeNode | None) -> None:
        cur = root
        while cur is not None:
            if cur.left is not None:
                # Find the rightmost in the left subtree (preorder predecessor of cur.right).
                pred = cur.left
                while pred.right is not None:
                    pred = pred.right
                pred.right = cur.right
                cur.right  = cur.left
                cur.left   = None
            cur = cur.right
    ```

    **O(n)** time (each edge traversed at most twice), **O(1)** extra space. The interview-favorite answer.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def flatten(root: TreeNode | None) -> None:
        """Flatten a binary tree in-place to a right-only preorder list.

        Args:
            root: Root of the binary tree (mutated in place).

        Time:  O(n) — each node's left subtree contributes at most twice.
        Space: O(1) extra.
        """
        cur = root
        while cur is not None:
            if cur.left is not None:
                pred = cur.left
                while pred.right is not None:
                    pred = pred.right
                pred.right = cur.right
                cur.right  = cur.left
                cur.left   = None
            cur = cur.right
    ```

##### 🔍 Dry Run

```
input:           after flatten:
    1                1
   / \                \
  2   5                2
 / \   \                \
3   4   6                3
                          \
                           4
                            \
                             5
                              \
                               6
```

Morris walk:

| cur | left? | rightmost of left | action |
|-----|-------|-------------------|--------|
| 1 | yes (2) | 4 | `4.right = 5`; `1.right = 2`; `1.left = None` |
| 2 | yes (3) | 3 | `3.right = 4`; `2.right = 3`; `2.left = None` |
| 3 | no | — | move to `3.right` (= 4) |
| 4 | no | — | move to `4.right` (= 5) |
| 5 | no | — | move to `5.right` (= 6) |
| 6 | no | — | move to `6.right` (= None) → done |

Final right-only chain: `1 → 2 → 3 → 4 → 5 → 6` ✅.

##### ⏱️ Complexity

- **Time: O(n)** — each edge is traversed at most twice in Morris.
- **Space: O(1)** extra for Morris, **O(h)** for recursive variants, **O(n)** for the collect-and-rewire approach.

##### 🎯 Pattern Used

**In-place tree rewiring + preorder predecessor splice (Morris)** — the same idea used to do iterative inorder without a stack. Reverse-postorder threading (Layer 3) is the dual of "build the chain from the tail."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What's the order — preorder, inorder, or postorder?"
    Preorder. The problem states it explicitly; verify by tracing the small example.

??? question "Follow-up 2 — In-place vs returning a new structure?"
    In-place is the asked variant. Returning a new linked list of values is trivial: just do a preorder into a list.

??? question "Follow-up 3 — Can you do it without recursion AND without extra space?"
    Yes — Morris (Layer 4). Each node's left subtree is "rotated" to the right of `cur` exactly once.

??? question "Follow-up 4 — What if you must preserve the original tree?"
    Build a deep copy first, then flatten the copy. Or build a separate linked-list structure of the values.

??? question "Follow-up 5 — Flatten to follow inorder instead of preorder?"
    Same idea but use the **predecessor** of `cur` (= rightmost of left subtree) and rewire so left subtree becomes the prefix. Or just collect inorder into a list and rewire.

##### 🐛 Common Bugs

1. **Recursing on `n.left` and `n.right` *after* you've already overwritten `n.right`** — always recurse first, then splice.
2. **Forgetting to null out `n.left`** — the result must be a right-only list, but tests often only check `right`-chain so this can go unnoticed in dev.
3. **Not handling the empty tree** — Morris loop's `while cur is not None` covers it for free; the recursive variant needs `if n is None: return`.
4. **Walking the rightmost via `pred.right`** but stopping one too early — the loop condition is `while pred.right is not None`, not `while pred is not None`.
5. **Using a global `prev`** without resetting it between calls — wrap it in a closure or class.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → no-op
- [ ] Single node → unchanged (left/right both None)
- [ ] Already right-skewed → effectively a no-op
- [ ] Left-skewed chain → becomes right-skewed
- [ ] Tree with a single leaf at depth 1 left → splices correctly
- [ ] Balanced tree → standard case
- [ ] Tree with only left children → fully rotated

##### 🏢 Sample Interviewer Quote

> *"Flatten this binary tree in-place into a right-only linked list following preorder."*

Your opener: *"Morris-style: for each node with a left child, find the rightmost of that left subtree, hook the right subtree onto it, move left to right, null the left. Walk down the right chain. O(n) time, O(1) extra space."*

---

#### Problem 21 — Convert Sorted List to BST

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span>

> Given the head of a singly linked list whose elements are sorted in ascending order, convert it into a **height-balanced** binary search tree.

##### 📖 Story Mode

This is **Problem 8 (Sorted Array → BST)** with one twist: the input is a linked list, not an array. Linked lists have no random access — `arr[mid]` is now a walk. The naive fix is to dump everything into an array first; the elegant fix is to **simulate inorder traversal** while building the tree, advancing the head pointer one step each time we visit a node.

The "build inorder" trick is one of the prettiest tree algorithms. The key realization: if we know the **size** `n`, the BST shape is fixed — left subtree has `n // 2` nodes, root, right subtree has `n - n//2 - 1`. So we can build the left subtree first (which exhausts the leftmost `n//2` list nodes), then take the next list node as the root, then build the right subtree. The list is consumed in inorder — exactly the order our BST stores values.

##### 🌍 Real-World Usage

- **Skip list / linked-list-backed sorted collections** to balanced trees — for example, when transitioning from a streaming insert phase to a query phase.
- **External sorts** producing a sorted run that needs to support range/predecessor queries — convert once, query many.
- **Persistent data structure conversions** — sorted log → balanced index.
- **Database index rebuilds** — a sorted file scan → B-tree-like in-memory index for warm caches.

##### 🧠 Thinking Process

Three approaches:

1. **Materialize to array, recurse on indices.** Easiest but uses O(n) extra space.
2. **Find the middle by slow/fast pointers, recurse on the two halves.** No extra array but each level walks to the middle — `O(n log n)` total.
3. **Inorder simulation:** count first to get `n`, then a recursive function builds the left subtree, "consumes" the current list node as the root, builds the right subtree. **O(n)** time, **O(log n)** stack space. Optimal.

> **Insight:** the BST you'd build is determined entirely by the size `n` (since the list is sorted). Inorder traversal of that BST visits values in sorted order. So if we *build* the BST in inorder, we just need to consume the list one node at a time, in order.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Materialize to array"

    ```python
    def sorted_list_to_bst_array(head: ListNode | None) -> TreeNode | None:
        vals: list[int] = []
        while head is not None:
            vals.append(head.val)
            head = head.next

        def build(lo: int, hi: int) -> TreeNode | None:
            if lo > hi:
                return None
            mid = (lo + hi) // 2
            node = TreeNode(vals[mid])
            node.left  = build(lo, mid - 1)
            node.right = build(mid + 1, hi)
            return node

        return build(0, len(vals) - 1)
    ```

    **O(n)** time, **O(n)** extra. The straightforward translation of Problem 8.

=== "Layer 2 — Slow/fast middle, recurse"

    ```python
    def sorted_list_to_bst_slowfast(head: ListNode | None) -> TreeNode | None:
        if head is None:
            return None
        if head.next is None:
            return TreeNode(head.val)

        # Find middle (and the predecessor of middle so we can split).
        prev: ListNode | None = None
        slow, fast = head, head
        while fast is not None and fast.next is not None:
            prev = slow
            slow = slow.next
            fast = fast.next.next

        # Split.
        if prev is not None:
            prev.next = None

        node = TreeNode(slow.val)
        node.left  = sorted_list_to_bst_slowfast(head if prev is not None else None)
        node.right = sorted_list_to_bst_slowfast(slow.next)
        return node
    ```

    **O(n log n)** time, **O(log n)** stack space. Each recursion walks half the list to find its midpoint.

=== "Layer 3 — Inorder simulation (optimal)"

    ```python
    def sorted_list_to_bst(head: ListNode | None) -> TreeNode | None:
        # First pass: count.
        n, p = 0, head
        while p is not None:
            n += 1
            p = p.next

        cur = [head]   # mutable wrapper so the closure can advance it

        def build(size: int) -> TreeNode | None:
            if size <= 0:
                return None
            left = build(size // 2)
            node = TreeNode(cur[0].val)
            cur[0] = cur[0].next
            node.left  = left
            node.right = build(size - size // 2 - 1)
            return node

        return build(n)
    ```

    **O(n)** time, **O(log n)** stack space. The list is consumed in a single sweep — magical.

=== "Layer 4 — Iterative-ish using inorder generator"

    ```python
    def sorted_list_to_bst_gen(head: ListNode | None) -> TreeNode | None:
        n, p = 0, head
        while p is not None:
            n += 1
            p = p.next

        node_iter = iter(_walk(head))

        def build(size: int) -> TreeNode | None:
            if size <= 0:
                return None
            left = build(size // 2)
            node = TreeNode(next(node_iter))
            node.left  = left
            node.right = build(size - size // 2 - 1)
            return node

        return build(n)


    def _walk(head: ListNode | None):
        while head is not None:
            yield head.val
            head = head.next
    ```

    Same complexity, decouples list-walking from tree-building. Easier to test.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def sorted_list_to_bst(head: ListNode | None) -> TreeNode | None:
        """Convert a sorted singly linked list to a height-balanced BST.

        Args:
            head: Head of a list sorted in non-decreasing order.

        Returns:
            Root of a height-balanced BST containing all list values.

        Time:  O(n).
        Space: O(log n) recursion stack.
        """
        n = 0
        p = head
        while p is not None:
            n += 1
            p = p.next

        state = {"node": head}

        def build(size: int) -> TreeNode | None:
            if size <= 0:
                return None
            left = build(size // 2)
            assert state["node"] is not None
            root = TreeNode(state["node"].val)
            state["node"] = state["node"].next
            root.left  = left
            root.right = build(size - size // 2 - 1)
            return root

        return build(n)
    ```

##### 🔍 Dry Run

List: `1 → 2 → 3 → 4 → 5 → 6 → 7`. n = 7.

`build(7)` → `build(3)` for left, then root, then `build(3)` for right.

`build(3)` (left side):

- `build(1)` → consumes `1` → leaf `1`.
- root = `2`, advance.
- `build(1)` → consumes `3` → leaf `3`. So returns subtree `2(1, 3)`.

Back at top: root = `4`, advance.

`build(3)` (right side):

- `build(1)` → consumes `5` → leaf `5`.
- root = `6`, advance.
- `build(1)` → consumes `7` → leaf `7`. Returns `6(5, 7)`.

Final tree:

```
        4
       / \
      2   6
     / \ / \
    1  3 5  7
```

##### ⏱️ Complexity

- **Time: O(n)** for Layer 3 (inorder simulation); **O(n)** for Layer 1; **O(n log n)** for Layer 2.
- **Space: O(log n)** stack for Layer 3; **O(n)** for Layer 1.

##### 🎯 Pattern Used

**Inorder construction with a mutable list pointer** — the same trick used to "build a BST from a sorted iterator." Generalizes to: any time you need to consume a sorted source and produce a balanced tree, build inorder.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if you can't count first (streaming list, unknown length)?"
    Buffer chunks: read up to N values at a time and build subtrees, then stitch them together. Or fall back to materializing if the dataset fits.

??? question "Follow-up 2 — What if duplicates are present?"
    The same algorithm works; duplicates land in adjacent inorder positions, fine for a BST that allows duplicates.

??? question "Follow-up 3 — Doubly linked list input?"
    Same algorithm. The `next` pointer advance is identical.

??? question "Follow-up 4 — Sorted descending?"
    Reverse the list first (O(n)), then run the algorithm.

??? question "Follow-up 5 — Why is the inorder simulation O(n) and not O(n log n)?"
    Because each list node is consumed exactly once. The recursion just structures *when* each consumption happens.

##### 🐛 Common Bugs

1. **Recursing on `head` directly without an external mutable pointer** — Python's pass-by-reference for objects doesn't help here; you need a list or class wrapper.
2. **Building right subtree before reading the root value** — wrecks ordering. Order matters: left → root → right.
3. **Off-by-one in the size split** — `size // 2` for left, `size - size//2 - 1` for right. Verify with size=2 case: left=1, right=0 (root is the second node).
4. **Returning the same node twice** — forgetting to advance `cur[0]`.
5. **Slow-fast variant: not breaking the list before recursing** — the left half's tail still points to the right half, causing infinite loops.

##### ✅ Edge Cases Checklist

- [ ] Empty list → return `None`
- [ ] Single node → leaf
- [ ] Two nodes → either `2(1, None)` or `2(None, 1)` depending on the split convention
- [ ] All equal values → fine
- [ ] Negative values → fine
- [ ] Very long list (10⁶) — Layer 3's iteration depth is `O(log n)`, safe
- [ ] List length is a power of 2 minus 1 (perfect tree result)

##### 🏢 Sample Interviewer Quote

> *"Convert this sorted linked list to a height-balanced BST."*

Your opener: *"Inorder construction. Count once for the size, then a recursive `build(size)` that builds the left subtree of size `size//2`, consumes the next list node as the root, then builds the right subtree. O(n) time, O(log n) stack — the list is consumed in a single sweep."*

---

#### Problem 22 — Binary Tree Maximum Path Sum

<span class="diff-hard">Hard</span> <span class="company-tag">Meta</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> A **path** in a binary tree is any sequence of nodes connected by parent-child edges. Each node appears at most once. The path does **not** need to pass through the root. Return the maximum sum of node values along any path.

##### 📖 Story Mode

This problem is the canonical example of the **"two values per recursion"** pattern: at each node we need two distinct quantities — the **best path that ends at this node** (which can be extended by the parent) and the **best path that passes through this node** (which can't be extended further because it uses both children).

Classic interviewer favorite at Meta and Google. The aha moment: a path can either go up-and-stop (extends to parent) or peak-here (uses both subtrees). We track both, but only the first is "returnable."

##### 🌍 Real-World Usage

- **Network throughput along a chain of nodes** — find the highest-throughput path.
- **DAG longest path** with node weights — same pattern in a DAG.
- **Decision trees with payoff scoring** — find the sequence of decisions with the highest expected value.
- **Game trees** — minimax-style "best path through state space."
- **Compilers (cost models)** — finding the most expensive evaluation path through an expression tree.

##### 🧠 Thinking Process

For each node `n`, define:

- `gain(n)` = best path-sum that **ends at `n`**, going strictly upward (so `n` connects to at most one of its children).
  - `gain(n) = n.val + max(0, max(gain(n.left), gain(n.right)))` — we drop subtrees whose contribution is negative.
- The best path that **peaks at `n`** = `n.val + max(0, gain(n.left)) + max(0, gain(n.right))`.

> **Key insight:** the global answer = max over all nodes of "path peaking at this node."

So we postorder the tree, compute `gain` for each child, update the global max with the "peak-at-n" candidate, then return `gain(n)` upward.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force: try every (u, v) pair"

    ```python
    def max_path_sum_brute(root: TreeNode | None) -> int:
        if root is None:
            return 0

        nodes: list[TreeNode] = []
        def collect(n: TreeNode | None) -> None:
            if n is None:
                return
            nodes.append(n)
            collect(n.left)
            collect(n.right)
        collect(root)

        # For each pair, find their path sum (LCA-based). O(n³) worst case.
        ...
    ```

    O(n³). Pedagogical only.

=== "Layer 2 — Postorder with two values (the classic)"

    ```python
    def max_path_sum(root: TreeNode) -> int:
        best = float("-inf")

        def gain(n: TreeNode | None) -> int:
            nonlocal best
            if n is None:
                return 0
            L = max(0, gain(n.left))
            R = max(0, gain(n.right))
            best = max(best, n.val + L + R)   # peak at n
            return n.val + max(L, R)          # extend through n

        gain(root)
        return best
    ```

    **O(n)** time, **O(h)** stack. The standard answer.

=== "Layer 3 — Iterative postorder (no recursion)"

    ```python
    def max_path_sum_iter(root: TreeNode) -> int:
        if root is None:
            raise ValueError("Empty tree")

        best = float("-inf")
        gain: dict[int, int] = {}
        stack: list[tuple[TreeNode, bool]] = [(root, False)]
        while stack:
            n, processed = stack.pop()
            if not processed:
                stack.append((n, True))
                if n.right is not None: stack.append((n.right, False))
                if n.left  is not None: stack.append((n.left,  False))
            else:
                L = max(0, gain.get(id(n.left),  0))
                R = max(0, gain.get(id(n.right), 0))
                best = max(best, n.val + L + R)
                gain[id(n)] = n.val + max(L, R)
        return best
    ```

    Same complexity, deeper-tree-safe.

=== "Layer 4 — Track endpoints (return path, not just sum)"

    ```python
    def max_path_with_path(root: TreeNode) -> tuple[int, list[int]]:
        best_sum = float("-inf")
        best_path: list[int] = []

        def go(n: TreeNode | None) -> tuple[int, list[int]]:
            nonlocal best_sum, best_path
            if n is None:
                return 0, []
            ls, lp = go(n.left)
            rs, rp = go(n.right)
            ls, lp = (ls, lp) if ls > 0 else (0, [])
            rs, rp = (rs, rp) if rs > 0 else (0, [])
            peak_sum  = n.val + ls + rs
            peak_path = list(reversed(lp)) + [n.val] + rp
            if peak_sum > best_sum:
                best_sum, best_path = peak_sum, peak_path
            if ls >= rs:
                return n.val + ls, lp + [n.val]
            return n.val + rs, rp + [n.val]

        go(root)
        return best_sum, best_path
    ```

    Useful when interviewers ask "and what's the path?" Slightly more bookkeeping.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def max_path_sum(root: TreeNode | None) -> int:
        """Maximum path sum in a binary tree.

        A path is any sequence of nodes connected by parent-child edges,
        with each node appearing at most once. The path need not pass
        through the root.

        Args:
            root: Root of the binary tree (must be non-empty).

        Returns:
            The maximum path sum.

        Raises:
            ValueError: if the tree is empty.

        Time:  O(n).
        Space: O(h) for the recursion stack.
        """
        if root is None:
            raise ValueError("Tree must have at least one node")

        best = root.val

        def gain(n: TreeNode | None) -> int:
            nonlocal best
            if n is None:
                return 0
            left  = max(0, gain(n.left))
            right = max(0, gain(n.right))
            best = max(best, n.val + left + right)
            return n.val + max(left, right)

        gain(root)
        return best
    ```

##### 🔍 Dry Run

```
       -10
       / \
      9  20
         / \
        15  7
```

Postorder visits:

| node | gain | peak | best |
|------|------|------|------|
| 9    | 9    | 9     | 9    |
| 15   | 15   | 15    | 15   |
| 7    | 7    | 7     | 15   |
| 20   | 20 + max(15, 7) = 35 | 20 + 15 + 7 = 42 | 42 |
| -10  | -10 + max(9, 35) = 25 | -10 + 9 + 35 = 34 | 42 |

Answer: **42** (path 15 → 20 → 7).

##### ⏱️ Complexity

- **Time: O(n)** — each node visited once.
- **Space: O(h)** for the recursion stack.

##### 🎯 Pattern Used

**Tree DP with two values per recursion** — return the "extendable" answer, but update a global with the "non-extendable" answer. Same pattern: Diameter (Problem 5), House Robber III (Problem 32), Longest Univalue Path.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if all values are negative?"
    Initialize `best = root.val` (or `-inf`). Don't clip the root itself with `max(0, …)`; only clip *child contributions*. The Layer 2 code handles this correctly because the peak update uses raw `n.val + L + R`.

??? question "Follow-up 2 — Return the actual path, not just the sum?"
    Layer 4 — track endpoints alongside the sum. Adds O(n) extra memory.

??? question "Follow-up 3 — What if the path must pass through the root?"
    Then it's just `gain(root.left) + root.val + gain(root.right)` (with the same clipping). O(n).

??? question "Follow-up 4 — Path must have at least k nodes?"
    Add a length parameter to the recursion. Trickier; you'd track multiple `(length, max_sum)` pairs per node and combine on the way up.

??? question "Follow-up 5 — N-ary tree?"
    Same idea, but the "peak-at-n" path uses the **top two** child gains: `n.val + top1 + top2`. The "extendable" gain returns `n.val + top1`.

##### 🐛 Common Bugs

1. **Clipping `n.val` itself with `max(0, n.val + ...)`** — wrong. You can clip child *contributions*, not the node itself. A negative root in a single-node tree is still the answer.
2. **Returning `n.val + L + R` upward** — this is the "peak" path, not extendable. Parent can only attach to one side.
3. **Initializing `best = 0`** — fails on all-negative trees.
4. **Forgetting `nonlocal best`** — in Python.
5. **Using `>=` vs `>` in path-tracking variant** — usually doesn't change correctness, but document your choice.
6. **Treating leaf as base case** — works, but the simpler base case is `None → 0`.

##### ✅ Edge Cases Checklist

- [ ] Single node (positive or negative) → returns `n.val`
- [ ] All negative values → returns the largest single value
- [ ] Linear chain → standard DP
- [ ] Path that doesn't pass through root → tested by the dry-run
- [ ] Very deep tree → use iterative variant
- [ ] Two-node tree → `max(root.val, root.val + child.val, child.val)`
- [ ] Mixed signs → ensure `max(0, …)` only clips children, not the node

##### 🏢 Sample Interviewer Quote

> *"Find the maximum path sum in a binary tree. The path doesn't have to pass through the root."*

Your opener: *"Tree DP. At each node I compute `gain(n)` = best one-sided path ending at n; clip negative children to zero. Globally I update best with `n.val + L + R` — the path that peaks here. O(n), O(h)."*

---

#### Problem 23 — Path Sum III

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Quora</span>

> Given the root of a binary tree and a `target` sum, return the **number of paths** whose values sum to `target`. The path must go **downward** (from a parent to a child), but need not start at the root or end at a leaf.

##### 📖 Story Mode

This is "Two Sum on a tree." If we record the **running prefix sum** along the root-to-current path, then any contiguous downward sub-path's sum equals `current_prefix - earlier_prefix`. So the question "how many sub-paths ending at the current node sum to `target`?" becomes "how many earlier prefix sums equal `current - target`?" — a hash-map lookup.

The catch: prefixes recorded along one branch must be **forgotten** when we backtrack to a sibling. That's why we increment on the way down and decrement on the way back up — pure backtracking on a counter map.

##### 🌍 Real-World Usage

- **Subarray sum equals K (LeetCode 560)** — exact same trick, applied to a 1D array.
- **Tree-based payment auditing** — count paths in an organizational tree whose total expense equals a budget.
- **Phylogenetic trees** — count lineages with a target mutation count.
- **Decision trees with rewards** — count branches summing to a target reward.

##### 🧠 Thinking Process

Three approaches, by complexity:

1. **Brute force:** for each starting node, DFS to count downward paths summing to target. **O(n²)**.
2. **Prefix sum + hash map (the elegant fix):** run a DFS, maintain a counter `seen[prefix_sum]`. At each node, answer at this node = `seen[current - target]`. Add `current` to `seen`, recurse into children, then remove `current` on the way back. **O(n)**.
3. **Negative-numbers gotcha:** since values can be negative, we cannot prune branches on running sum overshooting target — every branch must be explored fully. The hash-map approach is robust to negatives.

> **Why backtracking?** A prefix recorded on the left branch is **invalid** for the right branch — they're different root-to-node paths. So we have to undo the increment.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force: every node as a start"

    ```python
    def path_sum_iii_brute(root: TreeNode | None, target: int) -> int:
        if root is None:
            return 0

        def from_node(n: TreeNode | None, remaining: int) -> int:
            if n is None:
                return 0
            count = 1 if n.val == remaining else 0
            count += from_node(n.left,  remaining - n.val)
            count += from_node(n.right, remaining - n.val)
            return count

        def go(n: TreeNode | None) -> int:
            if n is None:
                return 0
            return from_node(n, target) + go(n.left) + go(n.right)

        return go(root)
    ```

    **O(n²)** worst case. Acceptable for small inputs.

=== "Layer 2 — Prefix sum + hash map"

    ```python
    def path_sum_iii(root: TreeNode | None, target: int) -> int:
        count = 0
        seen: dict[int, int] = {0: 1}   # empty-prefix base case

        def go(n: TreeNode | None, run_sum: int) -> None:
            nonlocal count
            if n is None:
                return
            run_sum += n.val
            count += seen.get(run_sum - target, 0)
            seen[run_sum] = seen.get(run_sum, 0) + 1
            go(n.left,  run_sum)
            go(n.right, run_sum)
            seen[run_sum] -= 1            # backtrack — sibling branches don't share this prefix

        go(root, 0)
        return count
    ```

    **O(n)** time, **O(h)** stack + **O(n)** hash-map space.

=== "Layer 3 — Iterative DFS with explicit stack"

    ```python
    def path_sum_iii_iter(root: TreeNode | None, target: int) -> int:
        if root is None:
            return 0
        count = 0
        seen: dict[int, int] = {0: 1}

        # Stack carries (node, run_sum, processed_flag)
        stack: list[tuple[TreeNode, int, bool]] = [(root, 0, False)]
        while stack:
            n, parent_sum, processed = stack.pop()
            run_sum = parent_sum + n.val
            if not processed:
                count += seen.get(run_sum - target, 0)
                seen[run_sum] = seen.get(run_sum, 0) + 1
                stack.append((n, parent_sum, True))   # post-visit cleanup
                if n.right is not None: stack.append((n.right, run_sum, False))
                if n.left  is not None: stack.append((n.left,  run_sum, False))
            else:
                seen[run_sum] -= 1
        return count
    ```

    Same asymptotic, deep-tree-safe.

=== "Layer 4 — Reusable on N-ary trees"

    ```python
    def path_sum_nary(root: NaryNode | None, target: int) -> int:
        count = 0
        seen: dict[int, int] = {0: 1}

        def go(n: NaryNode | None, run_sum: int) -> None:
            nonlocal count
            if n is None:
                return
            run_sum += n.val
            count += seen.get(run_sum - target, 0)
            seen[run_sum] = seen.get(run_sum, 0) + 1
            for child in n.children:
                go(child, run_sum)
            seen[run_sum] -= 1

        go(root, 0)
        return count
    ```

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations
    from collections import defaultdict


    def path_sum_iii(root: TreeNode | None, target: int) -> int:
        """Count downward paths summing to `target`.

        A "downward path" is any sequence of parent→child edges; it need
        not start at the root or end at a leaf.

        Args:
            root:   Root of the binary tree.
            target: Target sum.

        Returns:
            Number of paths summing to `target`.

        Time:  O(n).
        Space: O(n) for the prefix-sum counter + O(h) recursion stack.
        """
        count = 0
        seen: dict[int, int] = defaultdict(int)
        seen[0] = 1   # empty prefix

        def dfs(node: TreeNode | None, run_sum: int) -> None:
            nonlocal count
            if node is None:
                return
            run_sum += node.val
            count += seen[run_sum - target]
            seen[run_sum] += 1
            dfs(node.left,  run_sum)
            dfs(node.right, run_sum)
            seen[run_sum] -= 1

        dfs(root, 0)
        return count
    ```

##### 🔍 Dry Run

```
        10
       /  \
      5   -3
     / \    \
    3   2   11
   / \   \
  3  -2   1
```

Target = 8. Visit `10 → 5 → 3 → 3` with prefix sums `10, 15, 18, 21`.

At node `3` (leaf): run_sum = 21, look up `21 - 8 = 13`; not in `seen`. seen has `{0:1, 10:1, 15:1, 18:1}`.

Backtrack to `3` (interior, val=3): seen has `{0:1, 10:1, 15:1, 18:1}` after decrement of 21. Visit right child `-2`: run_sum = 16; lookup `16 - 8 = 8` → not present.

Continue to node `2` (sibling of `3` interior): run_sum = 17. Visit `1` (its right): run_sum = 18; lookup `18 - 8 = 10` → seen has 10 once → +1.

Continue to `-3 → 11`: run_sum = `10 + (-3) + 11 = 18`; lookup `18 - 8 = 10` → seen has 10 once → +1.

Also at `5 → 2 → 1`: run_sum = 18 (matches `5+2+1=8` from node `5`'s subtree)... actually `5 + 2 + 1 = 8` is itself a path; that's counted via `seen[run_sum - target] = seen[18 - 8] = seen[10]`. ✓.

Answer: **3** valid paths.

##### ⏱️ Complexity

- **Time: O(n)** — each node visited once; each lookup/update is O(1) average.
- **Space: O(n)** for the hash map + **O(h)** recursion.

##### 🎯 Pattern Used

**Prefix sum + hash map** (the "Two Sum trick"), applied to a tree via **DFS backtracking on the counter**. The same trick generalizes to subarray problems on 1D arrays.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What about negative numbers?"
    Already handled. The hash-map approach works regardless of sign because we don't prune; we just count. Brute force also works.

??? question "Follow-up 2 — Return the paths, not the count?"
    Augment the DFS to track the current path as a list and, on each match, record `path[len(path) - matched_length : len(path)]`. You'd also need to know the matched_length, which means storing prefix-sum positions, not just counts. **O(n)** time still, but **O(n²)** worst-case output size.

??? question "Follow-up 3 — Path can go in any direction (not just downward)?"
    That's the "Diameter / Max Path Sum" pattern (Problems 5 & 22) — different problem, two-values-per-recursion.

??? question "Follow-up 4 — What if the tree has 10⁷ nodes and target is 0 with a very wide range of values?"
    Hash map size is bounded by `n` (one entry per distinct prefix). The DFS stack is the bottleneck; switch to iterative.

??? question "Follow-up 5 — Online / streaming tree traversal?"
    The same algorithm works as you walk down a single path. The hash-map "decrement on backtrack" requires DFS — for a streaming root-to-leaf walk, just maintain the running counter without backtracking.

##### 🐛 Common Bugs

1. **Forgetting `seen[0] = 1`** — paths starting at the root won't be counted.
2. **Forgetting to decrement on backtrack** — counts paths that span sibling branches, which don't actually exist as a single downward path.
3. **Using a global mutable state without resetting it between test runs** — wrap in a closure or class.
4. **Comparing `run_sum == target` only** — counts only root-prefix paths, missing all paths that don't start at root.
5. **Off-by-one with `seen[run_sum] += 1` placement** — must happen *after* the lookup, *before* recursing into children.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0
- [ ] Single node, value = target → 1
- [ ] Single node, value ≠ target → 0
- [ ] Multiple paths through the same node → all counted
- [ ] target = 0 → must include all "empty zero" sub-paths? No — paths must contain ≥ 1 node
- [ ] Negative values present → algorithm still correct
- [ ] All values 0, target 0 → quadratic in node count? No — linear paths only
- [ ] Very deep tree → iterative DFS

##### 🏢 Sample Interviewer Quote

> *"Count downward paths in a binary tree whose values sum to a target."*

Your opener: *"Two Sum on a tree. Prefix sum DFS, hash-map counter; at each node the answer is `seen[run_sum - target]`. Increment on the way down, decrement on backtrack so sibling branches don't pollute each other. O(n)."*

---

#### Problem 24 — Populating Next Right Pointers

<span class="diff-medium">Medium</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Amazon</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span> <span class="company-tag">Oracle</span>

> You are given a **perfect binary tree** where each node has an additional `next` pointer (initially `None`). Populate each `next` to point to its right neighbor on the same level. The rightmost node on each level should point to `None`. Use **O(1) extra space** (the recursion stack and the tree itself don't count).

##### 📖 Story Mode

A perfect binary tree's structure makes this elegant. Once we've connected level `k`, every node on level `k` has a working `next` — and we can use those `next` pointers to weave level `k+1`'s nodes together without any queue.

For each parent on level `k`:

- `parent.left.next = parent.right` (siblings under the same parent).
- `parent.right.next = parent.next.left` if `parent.next` exists (cousins under adjacent parents).

After we've processed all parents on level `k`, level `k+1` is fully threaded. Move down to `leftmost.left` and repeat.

##### 🌍 Real-World Usage

- **Game-tree level-by-level processing** without the queue overhead.
- **Hierarchical caches** (CPU caches, web tiers) — finding "neighbors at the same level."
- **Layered neural networks** — peer-to-peer connections within a layer.
- **Skip lists** at each level — neighbors must point sideways.

##### 🧠 Thinking Process

The naive approach uses BFS with a queue: O(n) time, O(w) space (where w = max width = n/2 for a perfect tree). Acceptable but not the asked-for "O(1) extra space."

The trick: **use the `next` pointers from level k to traverse it horizontally** while connecting level k+1.

> **The two connection rules per parent on level k:**
>
> 1. **Same-parent siblings:** `parent.left.next = parent.right`.
> 2. **Cousins:** `parent.right.next = parent.next.left` (if `parent.next` exists).

Walk left-to-right on the current level using `next`; do these two assignments per node; drop down via `leftmost.left` once you've finished.

##### 🐍 5 Layers of Solution

=== "Layer 1 — BFS with queue"

    ```python
    from collections import deque


    def connect_bfs(root):
        if root is None:
            return None
        q = deque([root])
        while q:
            level_size = len(q)
            prev = None
            for _ in range(level_size):
                node = q.popleft()
                if prev is not None:
                    prev.next = node
                prev = node
                if node.left  is not None: q.append(node.left)
                if node.right is not None: q.append(node.right)
        return root
    ```

    **O(n)** time, **O(n/2) = O(n)** space. Works for any tree, not just perfect.

=== "Layer 2 — Two pointers, O(1) space (the asked solution)"

    ```python
    def connect(root):
        leftmost = root
        while leftmost is not None and leftmost.left is not None:
            head = leftmost
            while head is not None:
                head.left.next = head.right          # rule 1: siblings
                if head.next is not None:
                    head.right.next = head.next.left # rule 2: cousins
                head = head.next                     # walk the current level
            leftmost = leftmost.left                 # drop one level
        return root
    ```

    **O(n)** time, **O(1)** extra space. The standard answer.

=== "Layer 3 — Recursive (DFS)"

    ```python
    def connect_rec(root):
        if root is None or root.left is None:
            return root
        root.left.next = root.right
        if root.next is not None:
            root.right.next = root.next.left
        connect_rec(root.left)
        connect_rec(root.right)
        return root
    ```

    O(n) time, **O(log n)** stack. Cleaner but technically not O(1) space.

=== "Layer 4 — Generalize to any binary tree (LeetCode 117)"

    ```python
    def connect_any(root):
        cur = root
        while cur is not None:
            dummy = type(cur)(0)   # head of the next level
            tail = dummy
            while cur is not None:
                if cur.left is not None:
                    tail.next = cur.left
                    tail = tail.next
                if cur.right is not None:
                    tail.next = cur.right
                    tail = tail.next
                cur = cur.next
            cur = dummy.next
        return root
    ```

    Uses a `dummy` head per level so we don't depend on `parent.right` always existing. O(n) time, O(1) extra.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def connect(root: Node | None) -> Node | None:
        """Populate next pointers on a perfect binary tree.

        Each node's next points to its right neighbor on the same level,
        or None if it's the rightmost node on its level.

        Args:
            root: Root of a perfect binary tree (every parent has 0 or 2 children
                and every leaf is at the same depth).

        Returns:
            The (mutated) root.

        Time:  O(n).
        Space: O(1) extra.
        """
        leftmost = root
        while leftmost is not None and leftmost.left is not None:
            head = leftmost
            while head is not None:
                head.left.next = head.right
                if head.next is not None:
                    head.right.next = head.next.left
                head = head.next
            leftmost = leftmost.left
        return root
    ```

##### 🔍 Dry Run

```
       1
      / \
     2   3
    /|   |\
   4 5   6 7
```

Initial: all `next = None`.

**Level 0 (`leftmost = 1`):** outer loop enters because `1.left = 2` exists.

- `head = 1`: `1.left.next = 1.right` → `2.next = 3`. `1.next` is None, so no cousin link.
- `head = 1.next = None` → inner loop ends.
- `leftmost = 1.left = 2`.

**Level 1 (`leftmost = 2`):** outer loop enters because `2.left = 4` exists.

- `head = 2`: `2.left.next = 2.right` → `4.next = 5`. `2.next = 3`, so `2.right.next = 3.left` → `5.next = 6`.
- `head = 3`: `3.left.next = 3.right` → `6.next = 7`. `3.next = None`, no cousin link.
- `head = None` → inner loop ends.
- `leftmost = 2.left = 4`.

**Level 2 (`leftmost = 4`):** `4.left = None` → outer loop exits.

Final next-chains:

- Level 0: `1 → None`
- Level 1: `2 → 3 → None`
- Level 2: `4 → 5 → 6 → 7 → None` ✓.

##### ⏱️ Complexity

- **Time: O(n)** — each node's two `next` writes happen exactly once.
- **Space: O(1)** extra (Layer 2). Recursive variant uses **O(log n)** stack.

##### 🎯 Pattern Used

**Level-by-level traversal using established neighbor pointers** — same idea as "linked-list level traversal." The key abstraction: once a level is connected, the level itself becomes a singly linked list you can walk in O(width).

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if the tree isn't perfect?"
    LeetCode 117 (Populating Next Right Pointers II). Use Layer 4: maintain a `dummy → tail` pointer pair per level so missing children don't break the chain.

??? question "Follow-up 2 — Can you do it recursively in O(1) extra (not counting stack)?"
    Recursive in Layer 3 uses O(log n) stack. To get truly O(1) extra you must iterate.

??? question "Follow-up 3 — What if `next` already had values you must preserve?"
    Save them first or rebuild from scratch — depends on the spec. The standard problem assumes initial `next = None`.

??? question "Follow-up 4 — How do you connect a tree with arbitrary `parent` pointers but no `next`?"
    Use parent pointers to walk to the right neighbor: at each node, walk up to LCA with the right-side cousin, then down. More complex but doable in O(1) extra.

??? question "Follow-up 5 — Verify the result?"
    For each level, walk the linked list via `next` and check size == 2^level for a perfect tree.

##### 🐛 Common Bugs

1. **Forgetting the cousin link** — `head.right.next = head.next.left`. Without this, levels become a series of disconnected sibling pairs.
2. **Off-by-one on `leftmost.left is not None`** — leaves have no children; entering the inner loop at the leaf level would crash.
3. **Recursing on the right child before processing the parent's `next`** — in the recursive variant, we *must* set `root.right.next` before recursing, because `root.next` is already set by the parent.
4. **Treating `cur.next` as a queue and `popleft`-ing** — there's no popleft; `next` is a **read-only** chain at the current level until you finish the level.
5. **Mutating `next` and then trying to read it as the original tree shape** — once set, `next` is the level chain.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → return `None`
- [ ] Single node → `next = None`, return it
- [ ] Two-level tree → only one inner-loop iteration
- [ ] Three-level perfect → matches the dry run
- [ ] Non-perfect tree → Layer 2 fails on missing children; use Layer 4
- [ ] All values equal → algorithm doesn't read values, fine
- [ ] Verify O(1) extra space — no auxiliary list/queue/dict

##### 🏢 Sample Interviewer Quote

> *"Populate the next right pointers in this perfect binary tree, in O(1) extra space."*

Your opener: *"Once level k is connected, I walk it via `next` and connect level k+1 via two rules per parent: `left.next = right` and `right.next = next.left` if next exists. Drop to `leftmost.left`. O(n) time, O(1) extra."*

---

#### Problem 25 — Count Complete Tree Nodes

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Apple</span> <span class="company-tag">Bloomberg</span>

> Given the root of a **complete** binary tree, return the number of nodes. Design an algorithm that runs in better than **O(n)** time.

##### 📖 Story Mode

A **complete** binary tree is one where every level is fully filled except possibly the last, and the last level's nodes are pushed as far left as possible. That structure gives us a powerful invariant: at every node, **at least one** of its two subtrees is **perfect** (i.e. fully filled to the same depth on both sides).

We exploit this: at each node, measure leftmost-depth and rightmost-depth. If they're equal, the subtree is perfect → `2^d - 1` nodes by formula. Otherwise recurse on both children. Each recursive call splits into one "deep" branch (the imperfect one) and one "shallow" branch (where the leftmost == rightmost early-outs immediately). The result: `O(log² n)`.

##### 🌍 Real-World Usage

- **Heap implementations** rooted on arrays — when you need to query "size of the heap" without scanning.
- **Cache-oblivious B-trees** that maintain near-perfect filling.
- **Memory pool with binary buddies** — track filled blocks via complete-tree counting.
- **Persistent functional data structures** that grow level-by-level — fast size queries.

##### 🧠 Thinking Process

The naive count is O(n): traverse every node. For a complete tree we can do much better.

> **Lemma:** for any complete tree, at *any* node, the left subtree is complete OR the right subtree is complete (in fact, at least one is **perfect** — fully filled).

So at each node we measure:

- `dL` = depth of the **leftmost** chain (always going left).
- `dR` = depth of the **rightmost** chain (always going right).

If `dL == dR`, the entire subtree is perfect → `(1 << dL) - 1` nodes (subtract 1 because depth = number of edges + 1, but our formula counts nodes... we treat dL as the *count of nodes on the leftmost chain*, so the formula is `(1 << dL) - 1`).

Otherwise, recurse: `1 + count(left) + count(right)`. The **single-branch-deep** property of complete trees ensures the recursion is `O(log n)` deep and each level does `O(log n)` work → **O(log² n)**.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Naive O(n) traversal"

    ```python
    def count_nodes_naive(root: TreeNode | None) -> int:
        if root is None:
            return 0
        return 1 + count_nodes_naive(root.left) + count_nodes_naive(root.right)
    ```

    O(n) — the easy fallback.

=== "Layer 2 — Left-depth vs right-depth recursion"

    ```python
    def count_nodes(root: TreeNode | None) -> int:
        if root is None:
            return 0

        dL = 0
        n = root
        while n is not None:
            dL += 1
            n = n.left

        dR = 0
        n = root
        while n is not None:
            dR += 1
            n = n.right

        if dL == dR:
            return (1 << dL) - 1   # perfect subtree

        return 1 + count_nodes(root.left) + count_nodes(root.right)
    ```

    **O(log² n)** time, **O(log n)** stack.

=== "Layer 3 — Binary search on the last level"

    ```python
    def count_nodes_bs(root: TreeNode | None) -> int:
        if root is None:
            return 0

        # Tree height (depth of leftmost chain).
        depth = 0
        n = root
        while n.left is not None:
            depth += 1
            n = n.left

        if depth == 0:
            return 1

        # The last level can hold up to 2^depth nodes (indexed 0 .. 2^depth - 1).
        # Binary search the largest index whose node exists.
        def exists(idx: int) -> bool:
            lo, hi = 0, (1 << depth) - 1
            n = root
            for _ in range(depth):
                mid = (lo + hi) // 2
                if idx <= mid:
                    n = n.left
                    hi = mid
                else:
                    n = n.right
                    lo = mid + 1
            return n is not None

        lo, hi = 0, (1 << depth) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if exists(mid):
                lo = mid
            else:
                hi = mid - 1

        return (1 << depth) - 1 + lo + 1
    ```

    **O(log² n)** time, **O(1)** extra. Slightly faster constant than Layer 2 in some cases; same asymptotic.

=== "Layer 4 — Iterative left/right depth"

    ```python
    def count_nodes_iter(root: TreeNode | None) -> int:
        total = 0
        while root is not None:
            dL = _left_depth(root)
            dR = _right_depth(root)
            if dL == dR:
                return total + (1 << dL) - 1
            # Walk down: count the side that's perfect, recurse on the other.
            left_left = _left_depth(root.left)
            if left_left + 1 == dL:
                # left subtree depth == dL - 1 perfect; right subtree handled implicitly
                total += (1 << (dL - 1))   # left perfect: 2^(dL-1) - 1 nodes + the root
                root = root.right
            else:
                total += (1 << (dL - 2))   # right perfect of depth dL-2
                root = root.left
            total += 0   # placeholder; handle inside branches above
        return total


    def _left_depth(n):
        d = 0
        while n is not None: d += 1; n = n.left
        return d


    def _right_depth(n):
        d = 0
        while n is not None: d += 1; n = n.right
        return d
    ```

    Iterative variant — eliminates the recursion stack but is fiddly.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def count_nodes(root: TreeNode | None) -> int:
        """Count nodes in a complete binary tree in O(log² n).

        Args:
            root: Root of a complete binary tree.

        Returns:
            Total node count.

        Time:  O(log² n).
        Space: O(log n) recursion stack.
        """
        if root is None:
            return 0

        dL = _depth_left(root)
        dR = _depth_right(root)

        if dL == dR:
            return (1 << dL) - 1

        return 1 + count_nodes(root.left) + count_nodes(root.right)


    def _depth_left(node: TreeNode | None) -> int:
        d = 0
        while node is not None:
            d += 1
            node = node.left
        return d


    def _depth_right(node: TreeNode | None) -> int:
        d = 0
        while node is not None:
            d += 1
            node = node.right
        return d
    ```

##### 🔍 Dry Run

```
        1
       / \
      2   3
     / \ /
    4  5 6
```

Total node count: 6.

`count_nodes(1)`: `dL` walks `1 → 2 → 4` = 3. `dR` walks `1 → 3 → 6`? Wait — `3.right` is None. So `dR` = walks `1 → 3` then `3.right` is None → `dR = 2`. `dL ≠ dR`, so recurse: `1 + count_nodes(2) + count_nodes(3)`.

`count_nodes(2)`: `dL = 2 → 4`, then `4.left = None` so `dL = 2`. `dR = 2 → 5`, then `5.right = None` so `dR = 2`. Perfect! → `(1 << 2) - 1 = 3`.

`count_nodes(3)`: `dL = 3 → 6` = 2. `dR = 3` (since `3.right = None`) = 1. Not equal → recurse: `1 + count_nodes(6) + count_nodes(None)`. → `1 + 1 + 0 = 2`.

Total: `1 + 3 + 2 = 6` ✓.

##### ⏱️ Complexity

- **Time: O(log² n)** — at each of `O(log n)` recursion levels we do `O(log n)` work to measure depths.
- **Space: O(log n)** for the recursion stack.

##### 🎯 Pattern Used

**Exploit structural invariants for sub-linear counting.** The complete-tree property guarantees that at every node, one of the two subtrees is perfect — letting us short-circuit one branch with a closed-form count.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why log² and not log?"
    Each call along the recursion spine measures depths in O(log n). The recursion is O(log n) deep because each step recurses into only the "imperfect" subtree. log * log = log².

??? question "Follow-up 2 — Can it be done in O(log n)?"
    Yes — Layer 3's binary-search-on-last-level achieves O(log² n) but with a tighter constant. True O(log n) would require additional structural metadata (e.g. each node knowing its subtree size).

??? question "Follow-up 3 — What if the tree isn't complete?"
    Fall back to O(n) traversal — Layer 1.

??? question "Follow-up 4 — Verify completeness?"
    BFS, and after seeing the first `None` child, every subsequent child must be `None` too. O(n).

??? question "Follow-up 5 — Augmented complete tree (each node stores its subtree size)?"
    Then count is O(1) per query. Updates are O(log n).

##### 🐛 Common Bugs

1. **Mixing up `depth` (edges) vs `node count along chain`** — be consistent. The Layer 2 code treats `dL` as node-count.
2. **Using `2**dL - 1` vs `(1 << dL) - 1`** — same thing, but bit-shift is faster for big trees.
3. **Forgetting the `None` base case** — infinite recursion.
4. **Computing `dL` and `dR` from the wrong starting node** — always from `root` of the current call.
5. **Off-by-one in binary search** — boundary conditions on the last level are notoriously easy to mess up.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0
- [ ] Single node → 1
- [ ] Perfect tree → returns 2^h - 1 immediately
- [ ] Last level half-full → returns count correctly
- [ ] Last level one node → smallest possible imperfect case
- [ ] Last level missing exactly one node (rightmost) → recurses into right
- [ ] Very deep tree → O(log² n) is small even for n = 10⁹
- [ ] Tree NOT actually complete → Layer 2 may return incorrect; pre-validate or fall back

##### 🏢 Sample Interviewer Quote

> *"Count the nodes in this complete binary tree faster than O(n)."*

Your opener: *"At each node, compare leftmost depth vs rightmost depth. If equal → perfect subtree, return `(1 << d) - 1`. Otherwise recurse on both children. The complete-tree invariant guarantees one branch always early-exits, so we get O(log² n)."*

---

### Hard (26–35) — the ones that separate signals

#### Problem 26 — Recover Binary Search Tree

<span class="diff-medium">Medium</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Amazon</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> You are given the root of a binary search tree where exactly **two** nodes have had their values swapped by mistake. **Recover** the tree without changing its structure. Try to do it with constant extra space.

##### 📖 Story Mode

A BST's inorder walk yields a strictly increasing sequence. If exactly two nodes were swapped, the inorder walk has either **one** or **two** "violations" — places where `current.val < prev.val`.

- **Two adjacent nodes swapped** (rare case): one violation. The two offenders are the pair around it.
- **Two non-adjacent nodes swapped** (common case): two violations. The first offender is the **higher** of the first violation; the second offender is the **lower** of the second violation.

Once we identify the two offending nodes, swap their `val` fields. Done. We never touch any pointers — we only fix the values that drifted.

##### 🌍 Real-World Usage

- **Database recovery** after a corrupt update: detect and repair invariants.
- **Configuration management** — detecting two transposed config keys.
- **Genome sequencing pipelines** — detecting and fixing transposed adjacent nucleotides.
- **Financial reconciliation** — detecting two swapped ledger entries that violate ordering invariants.
- **Self-healing data structures** — invariant checkers that auto-repair single perturbations.

##### 🧠 Thinking Process

We need three pointers as we walk inorder:

- `prev`: previous-in-inorder node.
- `first`: first offender (set on first violation).
- `second`: second offender (set on every violation; if there's only one, `first` and `second` come from the same violation).

> **Detection rule:** at each comparison, if `prev.val > cur.val`:
> - If `first is None`: `first = prev` (the higher of the first violation), and `second = cur` (in case this is the only violation).
> - Else: `second = cur` (we found a second violation; the second offender is `cur`).

After the walk, swap `first.val` and `second.val`. **O(n)** time. With a recursive inorder, **O(h)** stack. With Morris, **O(1)** extra.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Collect inorder, find swap, restore"

    ```python
    def recover_collect(root: TreeNode) -> None:
        nodes: list[TreeNode] = []
        def inorder(n: TreeNode | None) -> None:
            if n is None: return
            inorder(n.left); nodes.append(n); inorder(n.right)
        inorder(root)

        sorted_vals = sorted(node.val for node in nodes)
        for node, v in zip(nodes, sorted_vals):
            node.val = v
    ```

    **O(n log n)** time, **O(n)** space. Robust but heavy-handed.

=== "Layer 2 — Inorder with two-violation tracking"

    ```python
    def recover(root: TreeNode) -> None:
        first: TreeNode | None = None
        second: TreeNode | None = None
        prev: TreeNode | None = None

        def inorder(n: TreeNode | None) -> None:
            nonlocal first, second, prev
            if n is None: return
            inorder(n.left)
            if prev is not None and prev.val > n.val:
                if first is None:
                    first = prev
                second = n
            prev = n
            inorder(n.right)

        inorder(root)
        if first is not None and second is not None:
            first.val, second.val = second.val, first.val
    ```

    **O(n)** time, **O(h)** stack.

=== "Layer 3 — Iterative inorder"

    ```python
    def recover_iter(root: TreeNode) -> None:
        first = second = prev = None
        stack: list[TreeNode] = []
        node = root
        while node is not None or stack:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if prev is not None and prev.val > node.val:
                if first is None:
                    first = prev
                second = node
            prev = node
            node = node.right
        if first is not None and second is not None:
            first.val, second.val = second.val, first.val
    ```

    Same complexity, recursion-stack-free.

=== "Layer 4 — Morris inorder, O(1) extra space"

    ```python
    def recover_morris(root: TreeNode) -> None:
        first = second = prev = None
        cur = root
        while cur is not None:
            if cur.left is None:
                if prev is not None and prev.val > cur.val:
                    if first is None: first = prev
                    second = cur
                prev = cur
                cur = cur.right
            else:
                # find inorder predecessor in left subtree
                pred = cur.left
                while pred.right is not None and pred.right is not cur:
                    pred = pred.right
                if pred.right is None:
                    pred.right = cur            # thread
                    cur = cur.left
                else:
                    pred.right = None           # un-thread
                    if prev is not None and prev.val > cur.val:
                        if first is None: first = prev
                        second = cur
                    prev = cur
                    cur = cur.right
        if first is not None and second is not None:
            first.val, second.val = second.val, first.val
    ```

    **O(n)** time, **O(1)** extra space. The "constant space" answer.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def recover_tree(root: TreeNode | None) -> None:
        """Recover a BST in which two nodes were swapped.

        Walks inorder; finds at most two "out-of-order" violations. Swaps the
        values of the two offending nodes in place.

        Args:
            root: Root of a BST with exactly two swapped values.

        Time:  O(n).
        Space: O(h) for the recursive variant.
        """
        if root is None:
            return

        first: TreeNode | None = None
        second: TreeNode | None = None
        prev: TreeNode | None = None

        def inorder(node: TreeNode | None) -> None:
            nonlocal first, second, prev
            if node is None:
                return
            inorder(node.left)
            if prev is not None and prev.val > node.val:
                if first is None:
                    first = prev
                second = node
            prev = node
            inorder(node.right)

        inorder(root)
        if first is not None and second is not None:
            first.val, second.val = second.val, first.val
    ```

##### 🔍 Dry Run

BST as drawn (with two values swapped):

```
        3
       / \
      1   4
         /
        2
```

Inorder walk yields values: `1, 3, 4, 2`. Sorted should be `1, 2, 3, 4`. **The 3 and 2 were swapped.**

| step | node | prev | violation? | first | second |
|------|------|------|------------|-------|--------|
| 1 | 1 | None | — | None | None |
| 2 | 3 | 1 | 1<3 OK | None | None |
| 3 | 4 | 3 | 3<4 OK | None | None |
| 4 | 2 | 4 | 4>2 ✓ | 4 (= prev) | 2 |

Swap `first.val=4` and `second.val=2`. Tree becomes `1, 2, 3, 4` inorder ✓.

##### ⏱️ Complexity

- **Time: O(n)** — single inorder pass.
- **Space: O(h)** stack (recursive/iterative); **O(1)** for Morris.

##### 🎯 Pattern Used

**Inorder traversal as a sortedness oracle on a BST** + **single-pass invariant repair**. The two-violation detection is the canonical pattern for "exactly K elements out of place."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — What if K nodes were swapped instead of 2?"
    Collect all violation pairs; you'll have up to K violations. Solve with collect-and-resort (Layer 1) for general K.

??? question "Follow-up 2 — Achieve O(1) extra space?"
    Morris traversal (Layer 4). The recursion stack would otherwise dominate.

??? question "Follow-up 3 — Why not swap pointers instead of values?"
    Pointer-swap requires re-parenting and is much messier. Value-swap preserves structure trivially. The problem says "without changing structure" — exactly what we want.

??? question "Follow-up 4 — How do you detect that no swap occurred (already valid BST)?"
    `first` remains `None` after the walk; skip the swap.

??? question "Follow-up 5 — What if the two swapped nodes are adjacent in inorder?"
    Only one violation. The handler `if first is None: first = prev; second = n` covers it: `first` and `second` are set during the same comparison.

##### 🐛 Common Bugs

1. **Updating `second` only on a "second" violation** — wrong; if only one violation exists, you'd never set `second`. Always set `second = n` on any violation.
2. **Overwriting `first` on the second violation** — must guard with `if first is None`.
3. **Forgetting `nonlocal`** in Python.
4. **Comparing `prev.val >= n.val`** — strictly greater than is the correct invariant for a BST without duplicates. With duplicates, the algorithm needs more care.
5. **Swapping pointers instead of values** — the problem forbids structure changes.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → no-op
- [ ] Single node → no-op
- [ ] Two-node tree with values swapped → handled (one violation case)
- [ ] Adjacent-in-inorder swap → one violation
- [ ] Non-adjacent swap → two violations
- [ ] Already valid BST → first remains None, no swap
- [ ] Skewed tree → still O(n) and Morris-safe
- [ ] Duplicate values in original tree (rare) → algorithm assumes strict BST

##### 🏢 Sample Interviewer Quote

> *"This BST has two nodes with their values swapped — recover it without modifying the structure."*

Your opener: *"Inorder walk; track violations. The first violation's prev is `first`; every violation's current is `second`. After the walk, swap their values. O(n), O(h). With Morris, O(1) extra."*

---

#### Problem 27 — Binary Tree Cameras

<span class="diff-hard">Hard</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span>

> You are given the root of a binary tree. Each **camera** at a node monitors **its parent, itself, and its immediate children**. Calculate the **minimum number of cameras** needed to monitor every node in the tree.

##### 📖 Story Mode

Place too few cameras and some node is unwatched. Place too many and you've wasted budget. The optimal placement is rarely intuitive — yet it boils down to a beautiful greedy fact: **leaves should never have cameras** (a camera on a leaf only watches itself + its parent; a camera on the leaf's parent watches itself + the leaf + the leaf's grandparent — strictly better).

So the right strategy is to push cameras **as high as possible** while still covering every leaf. Postorder lets us decide bottom-up: each node returns one of three states to its parent — `NEEDS_CAMERA` (uncovered, parent must cover us), `HAS_CAMERA` (we placed one), or `COVERED` (a child has a camera that covers us).

##### 🌍 Real-World Usage

- **Surveillance/IoT camera placement** — minimize monitoring devices in a hierarchical site.
- **Data-center hot-spare placement** — minimum spare nodes to cover any single failure.
- **Network monitoring agents** — minimum agents that observe all nodes in a tree topology.
- **Vertex cover variants** in graph theory.
- **Sensor networks** with hierarchical coverage relationships.

##### 🧠 Thinking Process

Three states per node:

- **0 (NEEDS_CAMERA)**: this node is uncovered; its parent must place a camera.
- **1 (HAS_CAMERA)**: we placed a camera here.
- **2 (COVERED)**: at least one child has a camera, so we're covered without one ourselves.

Postorder rules — at each node, given child states `(L, R)`:

1. If either child is `0` (uncovered) → **place a camera here** (state 1).
2. Else if either child is `1` (has a camera) → we're covered (state 2).
3. Else (both children are `2`) → **we're uncovered** (state 0); parent's problem.

Base case: `None → 2 (COVERED)`. This is critical — a leaf's null children are "covered" so the leaf reports `0` (needs cam). The leaf's parent then must place a camera (state 1). The parent's parent sees state 1 and reports state 2.

> **Greedy correctness:** any valid placement that puts a camera on a leaf can be moved to the leaf's parent without losing coverage. Therefore an optimal placement never has a camera at a leaf — exactly what our rules enforce.

After processing the root, if the root reports `0` (uncovered) we add **one more camera** for it.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute-force every subset"

    ```python
    # Pedagogical only: try every subset of nodes as camera placements.
    # 2^n — infeasible for n > ~25.
    ```

    Won't work in interview.

=== "Layer 2 — Postorder with three states"

    ```python
    NEEDS, HAS, COVERED = 0, 1, 2

    def min_camera_cover(root: TreeNode | None) -> int:
        cameras = 0

        def go(n: TreeNode | None) -> int:
            nonlocal cameras
            if n is None:
                return COVERED
            L = go(n.left)
            R = go(n.right)
            if L == NEEDS or R == NEEDS:
                cameras += 1
                return HAS
            if L == HAS or R == HAS:
                return COVERED
            return NEEDS

        if go(root) == NEEDS:
            cameras += 1
        return cameras
    ```

    **O(n)** time, **O(h)** stack.

=== "Layer 3 — DP with explicit state vectors"

    ```python
    INF = float("inf")

    def min_camera_dp(root: TreeNode | None) -> int:
        # Returns (with_cam, covered_no_cam, uncovered) - min cameras for each state of n.
        def go(n: TreeNode | None) -> tuple[int, int, int]:
            if n is None:
                return INF, 0, 0   # null can't have cam; null is "covered" for free
            l_with, l_cov, l_un = go(n.left)
            r_with, r_cov, r_un = go(n.right)

            # If n has a camera: children can be in any of the 3 states.
            with_cam = 1 + min(l_with, l_cov, l_un) + min(r_with, r_cov, r_un)
            # If n is covered without a camera: at least one child has a camera.
            covered = min(l_with + min(r_with, r_cov), l_cov + r_with)
            # If n is uncovered: both children must be covered (not uncovered).
            uncovered = min(l_cov, l_with) + min(r_cov, r_with)
            return with_cam, covered, uncovered

        with_cam, covered, _ = go(root)   # root cannot remain uncovered
        return min(with_cam, covered)
    ```

    Same O(n) but more explicit; pairs naturally with the proof.

=== "Layer 4 — Greedy + visited-set (alternative formulation)"

    ```python
    def min_camera_greedy(root: TreeNode | None) -> int:
        # DFS; if a leaf's parent isn't already a camera, install one.
        cameras = set()
        def dfs(n: TreeNode | None, parent: TreeNode | None, depth: int) -> None:
            if n is None: return
            dfs(n.left, n, depth + 1)
            dfs(n.right, n, depth + 1)
            if (parent is None and n not in cameras
                    and not (n.left in cameras or n.right in cameras)):
                cameras.add(n)
            elif (n.left and n.left not in cameras and not _covered(n.left, cameras)):
                cameras.add(n)
            ...
        dfs(root, None, 0)
        return len(cameras)
    ```

    Conceptually equivalent but messier; the postorder state machine is cleaner.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations
    from enum import IntEnum


    class CamState(IntEnum):
        NEEDS = 0
        HAS = 1
        COVERED = 2


    def min_camera_cover(root: TreeNode | None) -> int:
        """Minimum cameras to cover every node in the tree.

        A camera at node N monitors N's parent, N itself, and N's children.

        Args:
            root: Root of the tree.

        Returns:
            Minimum camera count.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        cameras = 0

        def post(n: TreeNode | None) -> CamState:
            nonlocal cameras
            if n is None:
                return CamState.COVERED
            left = post(n.left)
            right = post(n.right)
            if left == CamState.NEEDS or right == CamState.NEEDS:
                cameras += 1
                return CamState.HAS
            if left == CamState.HAS or right == CamState.HAS:
                return CamState.COVERED
            return CamState.NEEDS

        if post(root) == CamState.NEEDS:
            cameras += 1
        return cameras
    ```

##### 🔍 Dry Run

```
        0
       / \
      0   0
         / \
        0   0
```

(values don't matter; just structure)

Postorder:

| node | left state | right state | rule | this state | cams |
|------|-----------|-------------|------|------------|------|
| left-leaf (under root.left) | COVERED | COVERED | both covered → NEEDS | NEEDS | 0 |
| root.left | child=NEEDS | (no child) | NEEDS triggered → HAS, +1 cam | HAS | 1 |
| left-leaf (under root.right.left) | COVERED | COVERED | NEEDS | NEEDS | 1 |
| right-leaf (under root.right.right) | COVERED | COVERED | NEEDS | NEEDS | 1 |
| root.right | NEEDS, NEEDS | NEEDS triggered → HAS, +1 cam | HAS | 2 |
| root | HAS, HAS | both HAS → COVERED | COVERED | 2 |

Final root is COVERED, no extra. Total cameras = **2** ✓.

##### ⏱️ Complexity

- **Time: O(n)** — single postorder pass.
- **Space: O(h)** for the recursion stack.

##### 🎯 Pattern Used

**Tree DP with a small-state machine** (3 states). This is the canonical pattern for "minimum vertex cover on a tree" and its variants. Generalizes to: "place watchers on a tree to cover all nodes/edges with minimum count."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Prove the greedy is optimal."
    Suppose an optimal placement has a camera on a leaf. Move it to the leaf's parent: the parent gains coverage (was NEEDS or COVERED; now HAS), the grandparent is now also covered (was NEEDS now COVERED). So the move never loses coverage and reduces "wasted coverage." By exchange argument, an optimal placement exists with no leaf cameras.

??? question "Follow-up 2 — What if a camera also covered grandchildren?"
    The state machine grows. You'd need 5+ states to track "covered by deep child" vs "covered by direct child." DP still O(n) but with larger constant.

??? question "Follow-up 3 — Edges instead of nodes need monitoring?"
    Different problem (minimum edge cover on a tree). Solved by matching: pair each edge greedily with its parent's edge.

??? question "Follow-up 4 — N-ary tree?"
    Same logic. NEEDS triggers if any child is NEEDS; COVERED if any child is HAS; otherwise NEEDS.

??? question "Follow-up 5 — What if cameras are weighted (placement cost varies)?"
    Generalizes to weighted vertex-cover-on-tree DP — Layer 3's vector DP, with `with_cam = weight(n) + …`. Still O(n).

##### 🐛 Common Bugs

1. **Returning COVERED for a leaf** — wrong. A leaf's null children are COVERED, so the leaf's two children are both COVERED → leaf returns NEEDS (rule 3).
2. **Returning HAS for None** — wrong. Null children must be COVERED so leaves return NEEDS.
3. **Forgetting to count the root if it returns NEEDS** — most common bug. After the postorder, check root's state.
4. **Using `or` for both directions when both children matter** — careful with the precedence of NEEDS over HAS over COVERED.
5. **Treating "parent has camera" as covering us** — yes, but parent's state is unknown when we return; the postorder formulation handles this by making the parent's decision based on our state.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0 cameras
- [ ] Single node → 1 camera (it's NEEDS after post; root-uncovered branch adds 1)
- [ ] Two-node tree (root + one child) → 1 camera (on root or child? — on root, by greedy)
- [ ] Linear chain → roughly n/3 cameras
- [ ] Balanced perfect tree → cameras at the second-to-last level
- [ ] Skewed left → still works
- [ ] Tree where every internal node has only left children → correctness check

##### 🏢 Sample Interviewer Quote

> *"Place the minimum number of cameras to monitor every node in this binary tree. Each camera watches itself, its parent, and its direct children."*

Your opener: *"Tree DP. Three states per node: NEEDS (parent must cover me), HAS (I have a camera), COVERED (a child has one). Postorder. Null children are COVERED. If any child is NEEDS, place a camera here. If any child has one, I'm COVERED. Else NEEDS. Sum the cameras + 1 if root ends NEEDS."*

---

#### Problem 28 — All Nodes Distance K from Target

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Meta</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree, a target node, and an integer `k`, return a list of values of all nodes at **distance exactly k** from the target.

##### 📖 Story Mode

Distance in a tree means edges, and a tree-as-tree is **directional** (parent → child only). But distance is symmetric: a node `k` away from the target could be in the target's subtree, or k − ... hops up + down somewhere else.

The trick: temporarily treat the tree as an **undirected graph** by computing each node's `parent` pointer. Then BFS from the target until we reach exactly k layers. Every node at the kth layer is the answer.

##### 🌍 Real-World Usage

- **"People you may know" within k hops** in social graphs.
- **Service-mesh blast-radius analysis** — services exactly k hops away from a faulty one.
- **Game pathfinding** — squares reachable in exactly k moves.
- **Genealogy** — relatives exactly k generations from a target ancestor.
- **DOM traversal with arbitrary direction** — find elements k siblings/parents/children away.

##### 🧠 Thinking Process

Two main approaches:

1. **Parent map + BFS:** First DFS to compute `parent[node] = parent_node`. Then BFS from `target` over the implicit undirected graph (children + parent neighbors), tracking visited. After exactly k BFS layers, the queue holds the answer.
2. **DFS with subtree distance:** Walk from root; when we hit the target, recurse downward to collect "subtree distance k" nodes. Then walk back up via parent pointers, collecting nodes at distance `k - depth_above_target`. Trickier but doesn't need a parent map.

> **Why parent + BFS?** Symmetric distance + a unique source = textbook BFS. The parent map "completes" the tree into an undirected graph in O(n).

##### 🐍 5 Layers of Solution

=== "Layer 1 — Parent map + BFS"

    ```python
    from collections import deque


    def distance_k(root: TreeNode, target: TreeNode, k: int) -> list[int]:
        if root is None or target is None:
            return []

        parent: dict[int, TreeNode | None] = {}

        def map_parents(n: TreeNode | None, p: TreeNode | None) -> None:
            if n is None: return
            parent[id(n)] = p
            map_parents(n.left, n)
            map_parents(n.right, n)

        map_parents(root, None)

        visited: set[int] = {id(target)}
        q: deque[TreeNode] = deque([target])
        for _ in range(k):
            if not q: return []
            for _ in range(len(q)):
                n = q.popleft()
                for nb in (n.left, n.right, parent[id(n)]):
                    if nb is not None and id(nb) not in visited:
                        visited.add(id(nb))
                        q.append(nb)
        return [n.val for n in q]
    ```

    **O(n)** time, **O(n)** space. The standard answer.

=== "Layer 2 — DFS without parent map"

    ```python
    def distance_k_dfs(root: TreeNode, target: TreeNode, k: int) -> list[int]:
        ans: list[int] = []

        def collect_subtree(n: TreeNode | None, dist: int) -> None:
            if n is None or dist < 0: return
            if dist == 0:
                ans.append(n.val); return
            collect_subtree(n.left, dist - 1)
            collect_subtree(n.right, dist - 1)

        def go(n: TreeNode | None) -> int:
            """Returns -1 if target not in subtree, else distance from n to target."""
            if n is None: return -1
            if n is target:
                collect_subtree(n, k)
                return 0
            l = go(n.left)
            if l != -1:
                if l + 1 == k:
                    ans.append(n.val)
                else:
                    collect_subtree(n.right, k - l - 2)
                return l + 1
            r = go(n.right)
            if r != -1:
                if r + 1 == k:
                    ans.append(n.val)
                else:
                    collect_subtree(n.left, k - r - 2)
                return r + 1
            return -1

        go(root)
        return ans
    ```

    **O(n)** time, **O(h)** stack. No parent map but trickier to get right.

=== "Layer 3 — Convert to adjacency list, BFS"

    ```python
    from collections import defaultdict, deque


    def distance_k_graph(root: TreeNode, target: TreeNode, k: int) -> list[int]:
        adj: dict[int, list[TreeNode]] = defaultdict(list)

        def build(n: TreeNode | None, p: TreeNode | None) -> None:
            if n is None: return
            if p is not None:
                adj[id(n)].append(p)
                adj[id(p)].append(n)
            build(n.left, n); build(n.right, n)

        build(root, None)

        visited: set[int] = {id(target)}
        q: deque[TreeNode] = deque([target])
        for _ in range(k):
            for _ in range(len(q)):
                n = q.popleft()
                for nb in adj[id(n)]:
                    if id(nb) not in visited:
                        visited.add(id(nb))
                        q.append(nb)
            if not q: return []
        return [n.val for n in q]
    ```

    Equivalent but explicit graph — easier to extend.

=== "Layer 4 — Iterative DFS distance from root variant"

    Useful when the target is given by value, not reference. Walk down to target while tracking the path; then BFS or backtrack with the path stack. Same O(n).

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations
    from collections import deque


    def distance_k(root: TreeNode | None, target: TreeNode | None, k: int) -> list[int]:
        """Find all nodes exactly k edges away from `target`.

        Args:
            root:   Root of the tree.
            target: Target node (must be a node within the tree).
            k:      Non-negative distance.

        Returns:
            List of values at distance exactly k. Order is unspecified.

        Time:  O(n).
        Space: O(n).
        """
        if root is None or target is None or k < 0:
            return []

        parent: dict[int, TreeNode | None] = {}

        def link_parents(node: TreeNode | None, par: TreeNode | None) -> None:
            if node is None:
                return
            parent[id(node)] = par
            link_parents(node.left, node)
            link_parents(node.right, node)

        link_parents(root, None)

        visited: set[int] = {id(target)}
        frontier: deque[TreeNode] = deque([target])

        for _ in range(k):
            if not frontier:
                return []
            for _ in range(len(frontier)):
                node = frontier.popleft()
                for neighbor in (node.left, node.right, parent[id(node)]):
                    if neighbor is not None and id(neighbor) not in visited:
                        visited.add(id(neighbor))
                        frontier.append(neighbor)

        return [n.val for n in frontier]
    ```

##### 🔍 Dry Run

```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
       / \
      7   4
```

target = node `5`, k = 2.

Parent map links every node up. BFS from `5`:

- Layer 0: `{5}`.
- Layer 1: neighbors of 5 = `[6, 2, 3]` (children + parent). Visited adds them.
- Layer 2 (k = 2 — answer): from `6`: parent `5` visited, no children. From `2`: children `[7, 4]`, parent `5` visited. From `3`: parent None, child `1` (other side). Layer 2 frontier = `[7, 4, 1]`.

Answer values: `[7, 4, 1]` ✓.

##### ⏱️ Complexity

- **Time: O(n)** — DFS for parent map + BFS visits each node ≤ once.
- **Space: O(n)** for parent map, visited set, and queue.

##### 🎯 Pattern Used

**Tree-as-undirected-graph + BFS layer counting.** Common idiom for "distance" questions on trees because trees by default have only downward edges.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — k = 0?"
    Return `[target.val]` only.

??? question "Follow-up 2 — k larger than tree diameter?"
    BFS empties out before reaching k layers; return `[]`.

??? question "Follow-up 3 — What if target is given by value (not by node reference)?"
    First DFS to find the node, then run the algorithm. O(n) in total.

??? question "Follow-up 4 — Avoid the parent map (memory-constrained)?"
    Layer 2's DFS approach: when you "find" the target, do an explicit "subtree-distance" collection, then on the way back up, switch to "the other subtree at distance k - depth_above."

??? question "Follow-up 5 — N-ary tree?"
    Same parent map; iterate over `node.children + [parent]`.

##### 🐛 Common Bugs

1. **Forgetting to mark target as visited** — BFS revisits its parent → infinite loop.
2. **Using node values as visited keys** when values aren't unique — use `id(node)` or a `set` of node references.
3. **Looping `k+1` times** instead of `k` — gives nodes at distance k+1.
4. **Returning early when queue empty before reaching k** — must return `[]`.
5. **Using DFS with depth check `if dist == k`** but missing the "switch sides at LCA" cases.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `[]`
- [ ] target = root → standard BFS
- [ ] k = 0 → `[target.val]`
- [ ] k larger than tree → `[]`
- [ ] target is a leaf → BFS goes through parent
- [ ] k = 1 → just immediate neighbors (children + parent)
- [ ] Skewed tree → parent map still works
- [ ] Duplicate values → use node identity, not value

##### 🏢 Sample Interviewer Quote

> *"Find all nodes at distance exactly k from this target node."*

Your opener: *"Build a parent map first, treating the tree as an undirected graph. Then BFS from the target for exactly k layers; the final layer's values are the answer. O(n) time and space."*

---

#### Problem 29 — Vertical Order Traversal

<span class="diff-hard">Hard</span> <span class="company-tag">Meta</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree, return the **vertical order** traversal. Assign each node coordinates: root is at `(0, 0)`; the left child of a node at `(x, y)` is at `(x − 1, y + 1)`, the right child is at `(x + 1, y + 1)`. Group nodes by `x` (column), and within each column **sort by `y`** (top-down), breaking ties by **value**.

##### 📖 Story Mode

Imagine the tree drawn with each level offset diagonally. We're slicing it into vertical "columns" by the x-coordinate. The output is a list of columns from leftmost to rightmost. Within each column, top-of-the-tree first; ties broken by value (so two nodes with the same `(x, y)` come out in sorted order).

Three layers of grouping/sorting: by column → by row within column → by value within `(column, row)`. The cleanest implementation: collect all `(x, y, val)` triples in a single DFS, then sort.

##### 🌍 Real-World Usage

- **DOM/UI layout** — render order based on visual columns/rows.
- **Visual diff tools** for tree-structured data — column-aligned views.
- **GIS** — bucketing points into vertical columns.
- **Game-board view of an isometric map** — column-by-column rendering.
- **CAD/architecture** — vertical slicing of hierarchical structural elements.

##### 🧠 Thinking Process

The output is a `list[list[int]]` where each inner list is one column from leftmost to rightmost.

> **Tie-breaking matters:** LeetCode 987 (the "Hard" version) requires `(x, y, val)` triple sort. The earlier "Medium" version (314) only used BFS column ordering with no value tie-break. Both interview variants exist; ask which one.

Standard approach: DFS or BFS to compute `(x, y)` for each node, store `(x, y, val)`. After collecting, sort by `(x, y, val)` and group by `x`.

##### 🐍 5 Layers of Solution

=== "Layer 1 — DFS collect, sort triples"

    ```python
    def vertical_order_dfs(root: TreeNode | None) -> list[list[int]]:
        triples: list[tuple[int, int, int]] = []   # (x, y, val)

        def go(n: TreeNode | None, x: int, y: int) -> None:
            if n is None: return
            triples.append((x, y, n.val))
            go(n.left,  x - 1, y + 1)
            go(n.right, x + 1, y + 1)

        go(root, 0, 0)
        triples.sort()

        out: list[list[int]] = []
        prev_x: int | None = None
        for x, _, val in triples:
            if x != prev_x:
                out.append([])
                prev_x = x
            out[-1].append(val)
        return out
    ```

    **O(n log n)** time, **O(n)** space.

=== "Layer 2 — BFS with column dict (314 variant)"

    ```python
    from collections import defaultdict, deque


    def vertical_order_bfs(root: TreeNode | None) -> list[list[int]]:
        """LeetCode 314: BFS preserves natural top-to-bottom, left-to-right order
        within a column — no extra sort needed for ties."""
        if root is None:
            return []
        cols: dict[int, list[int]] = defaultdict(list)
        q: deque[tuple[TreeNode, int]] = deque([(root, 0)])
        while q:
            n, x = q.popleft()
            cols[x].append(n.val)
            if n.left:  q.append((n.left,  x - 1))
            if n.right: q.append((n.right, x + 1))
        return [cols[x] for x in sorted(cols)]
    ```

    **O(n log n)** for the final `sorted`, **O(n)** otherwise. **Doesn't sort by value within (x, y)** — only correct for 314, not 987.

=== "Layer 3 — Bucket by (x, y) then sort values"

    ```python
    from collections import defaultdict


    def vertical_order_bucket(root: TreeNode | None) -> list[list[int]]:
        buckets: dict[tuple[int, int], list[int]] = defaultdict(list)

        def go(n: TreeNode | None, x: int, y: int) -> None:
            if n is None: return
            buckets[(x, y)].append(n.val)
            go(n.left,  x - 1, y + 1)
            go(n.right, x + 1, y + 1)

        go(root, 0, 0)

        cols_by_x: dict[int, list[int]] = defaultdict(list)
        for (x, y), vals in sorted(buckets.items()):
            for v in sorted(vals):
                cols_by_x[x].append(v)
        return [cols_by_x[x] for x in sorted(cols_by_x)]
    ```

    Same complexity, more readable.

=== "Layer 4 — Two-pass: find x bounds, then DFS"

    ```python
    def vertical_order_2pass(root: TreeNode | None) -> list[list[int]]:
        if root is None:
            return []
        # Pass 1: find min/max x to size the array.
        lo, hi = 0, 0
        def find_bounds(n: TreeNode | None, x: int) -> None:
            nonlocal lo, hi
            if n is None: return
            lo = min(lo, x); hi = max(hi, x)
            find_bounds(n.left,  x - 1)
            find_bounds(n.right, x + 1)
        find_bounds(root, 0)

        # Pass 2: BFS collect into array indexed by (x - lo).
        from collections import deque
        cols: list[list[int]] = [[] for _ in range(hi - lo + 1)]
        q = deque([(root, 0)])
        while q:
            n, x = q.popleft()
            cols[x - lo].append(n.val)
            if n.left:  q.append((n.left,  x - 1))
            if n.right: q.append((n.right, x + 1))
        return cols
    ```

    Avoids the dict overhead. Same asymptotics, smaller constant.

=== "Layer 5 — Production-ready (LC 987 — full tie-break)"

    ```python
    from __future__ import annotations
    from itertools import groupby


    def vertical_order(root: TreeNode | None) -> list[list[int]]:
        """Vertical-order traversal with full tie-break by (x, y, val).

        Args:
            root: Root of the binary tree.

        Returns:
            Columns from leftmost to rightmost; within each column, ordered
            by depth then by value.

        Time:  O(n log n).
        Space: O(n).
        """
        triples: list[tuple[int, int, int]] = []

        def dfs(node: TreeNode | None, x: int, y: int) -> None:
            if node is None:
                return
            triples.append((x, y, node.val))
            dfs(node.left,  x - 1, y + 1)
            dfs(node.right, x + 1, y + 1)

        dfs(root, 0, 0)
        triples.sort()
        return [
            [val for _, _, val in group]
            for _, group in groupby(triples, key=lambda t: t[0])
        ]
    ```

##### 🔍 Dry Run

```
        3
       / \
      9   20
         /  \
        15   7
```

Coords: `3 → (0, 0)`, `9 → (-1, 1)`, `20 → (1, 1)`, `15 → (0, 2)`, `7 → (2, 2)`.

Triples sorted: `(-1, 1, 9), (0, 0, 3), (0, 2, 15), (1, 1, 20), (2, 2, 7)`.

Groupby x:

- x=-1: `[9]`
- x=0: `[3, 15]`
- x=1: `[20]`
- x=2: `[7]`

Output: `[[9], [3, 15], [20], [7]]` ✓.

##### ⏱️ Complexity

- **Time: O(n log n)** dominated by the sort.
- **Space: O(n)** for the triples + recursion stack O(h).

##### 🎯 Pattern Used

**Coordinate-tagging during traversal + global sort.** Common pattern when the desired output depends on a derived ordering not naturally produced by traversal.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Without the value tie-break (LC 314)?"
    BFS naturally orders nodes top-down and left-to-right within a column — no value sort needed. Simpler O(n log n) (only the column sort).

??? question "Follow-up 2 — Avoid the global sort?"
    Bucket by `x` first (with the offset trick from Layer 4), then sort each bucket's `(y, val)` independently. Slightly faster in practice if columns are short.

??? question "Follow-up 3 — Output the count of columns instead of the values?"
    Track only `min_x`, `max_x` — return `max_x - min_x + 1`. O(n) time.

??? question "Follow-up 4 — Memory-bounded streaming variant?"
    Two passes: first finds min/max x; second does a per-column extraction. Each column is O(column-size) extra.

??? question "Follow-up 5 — N-ary tree with the same coordinate convention?"
    Children offsets need a redefinition (e.g., spread evenly). Same algorithm once you've defined the offsets.

##### 🐛 Common Bugs

1. **Using BFS without value-sort for LC 987** — BFS gives FIFO within `(x, y)` ties, but the spec asks for value-sorted ties.
2. **Sorting by `(x, y, val)` lexicographically** — works because tuple compare goes left-to-right. Don't write a custom comparator.
3. **Forgetting `defaultdict`** when bucketing → KeyError.
4. **Off-by-one with x deltas** — left = x − 1, right = x + 1. Test with a 2-level tree.
5. **Returning columns in dict insertion order** — must explicitly `sorted(keys)`.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `[]`
- [ ] Single node → `[[root.val]]`
- [ ] Left-skewed → columns are 0, -1, -2, … each with 1 node
- [ ] Two nodes at same `(x, y)` → sorted by value
- [ ] Negative values → fine
- [ ] Large tree (10⁵ nodes) → O(n log n) is fast
- [ ] Deep recursion → consider iterative DFS

##### 🏢 Sample Interviewer Quote

> *"Return the vertical order traversal of this tree, where ties are broken by row then by value."*

Your opener: *"Tag every node with `(x, y)` during DFS, collect `(x, y, val)` triples, sort lexicographically, group by x. O(n log n) time, O(n) space."*

---

#### Problem 30 — Serialize and Deserialize an N-ary Tree

<span class="diff-hard">Hard</span> <span class="company-tag">LinkedIn</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span>

> Design an algorithm to **serialize** an N-ary tree (each node may have any number of children) to a string, and **deserialize** the string back to the original tree.

##### 📖 Story Mode

Problem 19 worked because each binary node had a fixed shape: left subtree + right subtree. With **N children** per node, "preorder + null sentinels" alone is ambiguous — we don't know when one node's child list ends and the next sibling begins.

The fix: serialize each node as **`val,child_count`** before its children, or use a **child-list terminator**. The first format makes deserialize simple (read val, read count, recurse exactly count times); the second mirrors Problem 19 but with end-of-children markers.

##### 🌍 Real-World Usage

- **Filesystem snapshots** — directory trees with arbitrary fan-out.
- **HTML / DOM serialization** — nodes have variable children.
- **AST serialization** — function bodies are lists of statements.
- **Org-charts and category trees** — arbitrary fan-out.
- **Trie persistence** — a trie node has up to 26 children.

##### 🧠 Thinking Process

Two clean encodings:

1. **`val,count` preorder** — for each node, emit its value + child count, then recursively serialize each child. Deserialize: read val, read count, call self `count` times.
2. **`val,#` after children** — for each node, emit value, recursively serialize each child, then emit a sentinel `#` to mark "end of children." Slightly more bytes but simpler to extend (e.g. variable values).

Both are **O(n)**. Choose based on which is easier to debug; (1) is the textbook choice.

> **Anti-pattern: don't try to serialize as level-order.** It works but requires more bookkeeping (you'd need a per-level child count too).

##### 🐍 5 Layers of Solution

=== "Layer 1 — Preorder with child count"

    ```python
    SEP = ","


    def serialize(root: NaryNode | None) -> str:
        if root is None:
            return ""
        parts: list[str] = []

        def go(n: NaryNode) -> None:
            parts.append(str(n.val))
            parts.append(str(len(n.children)))
            for c in n.children:
                go(c)

        go(root)
        return SEP.join(parts)


    def deserialize(data: str) -> NaryNode | None:
        if not data:
            return None
        it = iter(data.split(SEP))

        def go() -> NaryNode:
            val = int(next(it))
            count = int(next(it))
            node = NaryNode(val, [])
            for _ in range(count):
                node.children.append(go())
            return node

        return go()
    ```

    **O(n)** time and space. The standard answer.

=== "Layer 2 — Preorder with end-of-children sentinel"

    ```python
    NULL = "#"


    def serialize_eoc(root: NaryNode | None) -> str:
        if root is None: return ""
        parts: list[str] = []

        def go(n: NaryNode) -> None:
            parts.append(str(n.val))
            for c in n.children:
                go(c)
            parts.append(NULL)

        go(root)
        return SEP.join(parts)


    def deserialize_eoc(data: str) -> NaryNode | None:
        if not data: return None
        it = iter(data.split(SEP))

        def go() -> NaryNode:
            val = int(next(it))
            node = NaryNode(val, [])
            while True:
                tok = next(it)
                if tok == NULL: break
                # Push back: rebuild iter or track via lookahead.
                ...
            return node

        return go()
    ```

    Slightly trickier because we'd need a peek operation. Layer 1 is preferable.

=== "Layer 3 — Level-order (BFS) with child counts"

    ```python
    from collections import deque


    def serialize_bfs(root: NaryNode | None) -> str:
        if root is None: return ""
        parts: list[str] = [str(root.val), str(len(root.children))]
        q: deque[NaryNode] = deque([root])
        while q:
            n = q.popleft()
            for c in n.children:
                parts.append(str(c.val))
                parts.append(str(len(c.children)))
                q.append(c)
        return SEP.join(parts)


    def deserialize_bfs(data: str) -> NaryNode | None:
        if not data: return None
        toks = data.split(SEP)
        i = 0
        root = NaryNode(int(toks[i]), [])
        cnt = int(toks[i + 1])
        i += 2
        q: deque[tuple[NaryNode, int]] = deque([(root, cnt)])
        while q:
            parent, remaining = q.popleft()
            for _ in range(remaining):
                child = NaryNode(int(toks[i]), [])
                child_cnt = int(toks[i + 1])
                i += 2
                parent.children.append(child)
                q.append((child, child_cnt))
        return root
    ```

    Same complexity, useful when you need a level-by-level wire format.

=== "Layer 4 — JSON-based"

    ```python
    import json


    def to_dict(n: NaryNode | None) -> dict | None:
        if n is None: return None
        return {"val": n.val, "children": [to_dict(c) for c in n.children]}


    def serialize_json(root: NaryNode | None) -> str:
        return json.dumps(to_dict(root))


    def from_dict(d: dict | None) -> NaryNode | None:
        if d is None: return None
        return NaryNode(d["val"], [from_dict(c) for c in d["children"]])


    def deserialize_json(data: str) -> NaryNode | None:
        return from_dict(json.loads(data))
    ```

    Most readable; larger wire size; relies on the JSON library.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    class NaryCodec:
        """Serialize and deserialize an N-ary tree.

        Format: comma-separated preorder traversal where each node is encoded
        as `<val>,<child_count>` followed by its children.

        Time:  O(n) for both directions.
        Space: O(n) for the output string + O(h) recursion stack.
        """

        SEP = ","

        def serialize(self, root: NaryNode | None) -> str:
            if root is None:
                return ""
            parts: list[str] = []

            def encode(node: NaryNode) -> None:
                parts.append(str(node.val))
                parts.append(str(len(node.children)))
                for child in node.children:
                    encode(child)

            encode(root)
            return self.SEP.join(parts)

        def deserialize(self, data: str) -> NaryNode | None:
            if not data:
                return None
            tokens = iter(data.split(self.SEP))

            def decode() -> NaryNode:
                val = int(next(tokens))
                count = int(next(tokens))
                node = NaryNode(val, [])
                for _ in range(count):
                    node.children.append(decode())
                return node

            return decode()
    ```

##### 🔍 Dry Run

N-ary tree:

```
        1
      / | \
     3  2  4
    / \
   5   6
```

Preorder + counts emits: `1,3,3,2,5,0,6,0,2,0,4,0`.

| step | emit | reason |
|------|------|--------|
| 1 | `1` | val |
| 2 | `3` | 1 has 3 children |
| 3 | `3` | val |
| 4 | `2` | 3 has 2 children |
| 5 | `5` | val |
| 6 | `0` | 5 has 0 children |
| 7 | `6` | val |
| 8 | `0` | 6 has 0 children |
| 9 | `2` | back to 1's level; val |
| 10 | `0` | 2 has 0 children |
| 11 | `4` | val |
| 12 | `0` | 4 has 0 children |

Deserialize reads: val=1 → count=3 → recurse 3×: builds 3-subtree, then 2 leaf, then 4 leaf. ✓

##### ⏱️ Complexity

- **Time: O(n)** for both directions.
- **Space: O(n)** output + **O(h)** recursion.

##### 🎯 Pattern Used

**Preorder with structural metadata.** The "child count" turns each node into a self-contained header — the deserializer always knows exactly how many children to consume.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why not just use Problem 19's preorder + null sentinels?"
    Ambiguous for N-ary: how do you know "two siblings" vs "one sibling with one grandchild"? You need either a child count or end-of-children sentinel.

??? question "Follow-up 2 — Bandwidth-bounded — minimize bytes?"
    Use a binary format: variable-length integers (varint) for val and count. Or run-length encode common counts (0 is most common in deep trees).

??? question "Follow-up 3 — Streaming deserialize (don't load the whole string)?"
    Read tokens from a stream instead of a list. The recursive `decode()` works as long as `next()` can stream.

??? question "Follow-up 4 — Cycles or DAG?"
    Trees by definition have no cycles. For DAGs, assign each node an ID; emit `(id, val, [child_ids])`.

??? question "Follow-up 5 — How do you handle string values containing the separator?"
    Escape them, or pick a separator the data can't contain (e.g. `\x01`). Or use a binary length-prefix format.

##### 🐛 Common Bugs

1. **Forgetting to emit child count for leaves** — must emit `0`.
2. **Off-by-one in the recursion count** — must call recurse exactly `count` times.
3. **Using a global iterator without resetting** — wrap in a closure.
4. **Treating empty string and `None` differently** — pick one convention; document it.
5. **Mixing serialization formats** — don't use `null` sentinels and child counts in the same format.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `""` round-trips to `None`
- [ ] Single node → `"42,0"`
- [ ] All leaves at one level → fine
- [ ] Linear chain (each node has exactly one child) → child counts all 1
- [ ] Wide tree (root has 100 children) → counts encode correctly
- [ ] Deep tree → recursion depth O(h)
- [ ] Negative values → encode normally
- [ ] Values containing the separator → escape or change separator

##### 🏢 Sample Interviewer Quote

> *"Serialize and deserialize an N-ary tree."*

Your opener: *"Preorder, encoding each node as `val,count` followed by the children. Deserialize reads val, reads count, recurses count times. O(n) both ways. The child count removes the binary-tree ambiguity that null sentinels alone can't resolve for arbitrary fan-out."*

---

#### Problem 31 — Find Duplicate Subtrees

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree, return all **duplicate subtrees** — subtrees with identical structure and node values. Return one representative root per duplicate group.

##### 📖 Story Mode

Two subtrees are "the same" iff their structure and values match exactly. We need a way to **canonically identify** each subtree so that two structurally-equal subtrees produce the same key.

The natural canonical form is the **postorder serialization** of the subtree (with null sentinels). For a leaf-3, it's `"3,#,#"`. For `1(2(3, null), null)` it's `"1,2,3,#,#,#,#"`. Hash these strings and we have our equality check.

Naive implementation: O(n²) due to string concatenation. The trick to get true O(n) is **string interning**: assign each unique subtree string an integer ID; then the canonical form for parent uses **child IDs**, not their full strings.

##### 🌍 Real-World Usage

- **Compiler common subexpression elimination (CSE)** — same subtree of an AST = compute once.
- **Cached query plans** — recognize identical subqueries.
- **Decision trees** — duplicate decision branches can be merged for compactness.
- **Filesystem dedup** — duplicate directory subtrees can share storage.
- **HTML/DOM optimization** — repeated subcomponent trees can be hoisted.

##### 🧠 Thinking Process

1. **Postorder DFS, build a serialization string per subtree.** O(n²) worst case (each string is O(n)).
2. **String interning**: a `dict[str, int]` maps full serializations to small IDs. The serialization for a node becomes `"val,left_id,right_id"` — fixed-length **independent of subtree size**. Now hashing/storing each is O(1) and total time is O(n).
3. **Counter to detect duplicates**: increment count per ID; on second occurrence, append the node to the answer.

> **Why postorder?** We need children's serializations *before* we can serialize ourselves.

##### 🐍 5 Layers of Solution

=== "Layer 1 — String serialization (O(n²))"

    ```python
    from collections import defaultdict


    def find_duplicate_subtrees_str(root: TreeNode | None) -> list[TreeNode]:
        seen: dict[str, int] = defaultdict(int)
        result: list[TreeNode] = []

        def post(n: TreeNode | None) -> str:
            if n is None:
                return "#"
            sig = f"{n.val},{post(n.left)},{post(n.right)}"
            seen[sig] += 1
            if seen[sig] == 2:
                result.append(n)
            return sig

        post(root)
        return result
    ```

    **O(n²)** time worst case, O(n²) space. Easy to write, fails for very deep trees.

=== "Layer 2 — String interning (O(n))"

    ```python
    from collections import defaultdict


    def find_duplicate_subtrees(root: TreeNode | None) -> list[TreeNode]:
        ids: dict[tuple[int, int, int], int] = {}
        count: dict[int, int] = defaultdict(int)
        result: list[TreeNode] = []
        next_id = 1
        NULL = 0

        def post(n: TreeNode | None) -> int:
            nonlocal next_id
            if n is None:
                return NULL
            l = post(n.left)
            r = post(n.right)
            key = (n.val, l, r)
            if key in ids:
                uid = ids[key]
            else:
                uid = next_id
                ids[key] = uid
                next_id += 1
            count[uid] += 1
            if count[uid] == 2:
                result.append(n)
            return uid

        post(root)
        return result
    ```

    **O(n)** time, **O(n)** space. The interview-quality answer.

=== "Layer 3 — Tuple-as-key recursion (concise)"

    ```python
    from collections import defaultdict


    def find_duplicate_subtrees_tuple(root: TreeNode | None) -> list[TreeNode]:
        seen: dict = defaultdict(list)

        def post(n: TreeNode | None):
            if n is None: return None
            key = (n.val, post(n.left), post(n.right))
            seen[key].append(n)
            return key

        post(root)
        return [nodes[0] for nodes in seen.values() if len(nodes) > 1]
    ```

    Same complexity as Layer 2. Tuples are hashable so this works directly.

=== "Layer 4 — Iterative postorder (deep-tree-safe)"

    ```python
    def find_duplicate_subtrees_iter(root: TreeNode | None) -> list[TreeNode]:
        if root is None: return []
        ids: dict[tuple[int, int, int], int] = {}
        count: dict[int, int] = defaultdict(int)
        node_id: dict[int, int] = {}
        result: list[TreeNode] = []
        next_id = 1

        stack: list[tuple[TreeNode, bool]] = [(root, False)]
        while stack:
            n, processed = stack.pop()
            if not processed:
                stack.append((n, True))
                if n.right: stack.append((n.right, False))
                if n.left:  stack.append((n.left,  False))
            else:
                l = node_id.get(id(n.left), 0)
                r = node_id.get(id(n.right), 0)
                key = (n.val, l, r)
                if key in ids:
                    uid = ids[key]
                else:
                    uid = next_id
                    ids[key] = uid
                    next_id += 1
                node_id[id(n)] = uid
                count[uid] += 1
                if count[uid] == 2:
                    result.append(n)
        return result
    ```

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations
    from collections import defaultdict


    def find_duplicate_subtrees(root: TreeNode | None) -> list[TreeNode]:
        """Find all duplicate subtrees (one representative per group).

        Two subtrees are duplicates iff they have identical structure and
        node values. Uses string interning for O(n) total time.

        Args:
            root: Root of the tree.

        Returns:
            List of one representative root per duplicate subtree class.

        Time:  O(n).
        Space: O(n).
        """
        unique_id: dict[tuple[int, int, int], int] = {}
        count: dict[int, int] = defaultdict(int)
        duplicates: list[TreeNode] = []
        next_id = 1
        NULL_ID = 0

        def serialize(node: TreeNode | None) -> int:
            nonlocal next_id
            if node is None:
                return NULL_ID
            triple = (node.val, serialize(node.left), serialize(node.right))
            uid = unique_id.get(triple)
            if uid is None:
                uid = next_id
                unique_id[triple] = uid
                next_id += 1
            count[uid] += 1
            if count[uid] == 2:
                duplicates.append(node)
            return uid

        serialize(root)
        return duplicates
    ```

##### 🔍 Dry Run

```
        1
       / \
      2   3
     /   / \
    4   2   4
       /
      4
```

Postorder visit order: leaves first.

| node | left_id | right_id | triple | id |
|------|---------|----------|--------|-----|
| 4 (under 2 left of 1) | 0 | 0 | (4, 0, 0) | 1 |
| 2 (left of 1) | 1 | 0 | (2, 1, 0) | 2 |
| 4 (under 2 left of 3) | 0 | 0 | (4, 0, 0) | 1 (count=2 → **append**) |
| 2 (under 3) | 1 | 0 | (2, 1, 0) | 2 (count=2 → **append**) |
| 4 (right of 3) | 0 | 0 | (4, 0, 0) | 1 (count=3) |
| 3 | 2 | 1 | (3, 2, 1) | 3 |
| 1 | 2 | 3 | (1, 2, 3) | 4 |

Duplicates: the leaf `4` and the subtree `2(4)` ✓.

##### ⏱️ Complexity

- **Time: O(n)** with interning.
- **Space: O(n)** for the maps.

##### 🎯 Pattern Used

**Postorder canonical fingerprinting + string interning.** The same idea powers compiler CSE, AST hash-consing, and persistent-data-structure equality.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why is the naive string version O(n²)?"
    Each subtree's serialization is up to O(n) long; total work over n subtrees is O(n²). Interning replaces O(n)-length strings with O(1) integer IDs.

??? question "Follow-up 2 — What if values are arbitrary objects?"
    Use `id()`-keys via a hash map: `vid = obj_to_id[node.val]`. Same algorithm.

??? question "Follow-up 3 — Could you use Merkle hashing instead?"
    Yes — hash `(val, left_hash, right_hash)` recursively. Collisions are theoretically possible; in practice with a 64-bit hash they're rare enough to ignore for interview purposes.

??? question "Follow-up 4 — Return ALL duplicates, not just one per group?"
    Track every node per group and return all `(group_size > 1)` lists.

??? question "Follow-up 5 — Streaming variant — tree built incrementally, query duplicates online?"
    Maintain the maps as you build. Each insert is O(h) for the path of recomputations.

##### 🐛 Common Bugs

1. **Using `f"{val},{l},{r}"` with Python int keys** — works but quadratic for large trees.
2. **Forgetting to skip groups with count 1** when reporting — only multi-occurrence subtrees are duplicates.
3. **Comparing only structure, not values** — wrong; the problem says identical subtrees, including values.
4. **Returning every duplicate node, not one per group** — the spec says one representative.
5. **Treating null as a non-canonical token** — must always serialize null subtrees the same way.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → `[]`
- [ ] Single node → no duplicates → `[]`
- [ ] Two identical leaves → one duplicate (leaf shape)
- [ ] Identical subtrees at different depths → still duplicates
- [ ] All nodes equal value → many duplicates expected
- [ ] No duplicates → `[]`
- [ ] Negative values → fine
- [ ] Very deep tree → use iterative variant

##### 🏢 Sample Interviewer Quote

> *"Find every duplicate subtree in this binary tree."*

Your opener: *"Postorder; assign each unique subtree an integer ID via string interning. The triple `(val, left_id, right_id)` is the canonical key. Track count per ID; second occurrence is a duplicate. O(n) time and space."*

---

#### Problem 32 — House Robber III

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span>

> A thief is going to rob houses arranged as a **binary tree**. The constraint: he can't rob **directly connected** houses (parent and child). Return the **maximum amount** he can steal without alerting the police.

##### 📖 Story Mode

The classic House Robber problem on a 1D street has a clean DP: at each house decide rob-or-skip; rob → skip the next; skip → consider the next freely. On a tree, "next" branches into two children — but the same idea applies recursively.

**Two states per node:**

- `rob_this`: max loot if we rob this node (then **skip** both children).
- `skip_this`: max loot if we skip this node (free choice for each child).

The genius of the tuple-return is that we never need to store an exponential set of choices — each subtree summarizes itself in two numbers.

##### 🌍 Real-World Usage

- **Independent set on trees** — exact same structure (max-weight independent set is the generic version).
- **Resource scheduling on hierarchical grids** — pick non-adjacent nodes for events to avoid conflicts.
- **Cache-line evictions** in a tree-shaped cache hierarchy — avoid evicting parent + child simultaneously.
- **Network packet scheduling** — adjacent routers can't transmit at once.

##### 🧠 Thinking Process

For each node, returning a single number (max loot in this subtree) isn't enough — the parent needs to know *whether the child was robbed* to make its own decision.

Return a **tuple `(rob, skip)`**:

- `rob = n.val + left.skip + right.skip` (we robbed this; children must skip).
- `skip = max(left.rob, left.skip) + max(right.rob, right.skip)` (free choice).

Final answer is `max(root.rob, root.skip)`.

> **Two-state tree DP** is one of the four canonical tree DP shapes:
>
> 1. Single value (height, count).
> 2. Tuple of values (rob/skip, deepest/answer).
> 3. List of values (per-depth state).
> 4. State machine (Cameras' 3-state).

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force with memoization on `(node, parent_robbed)`"

    ```python
    def rob_memo(root: TreeNode | None) -> int:
        memo: dict[tuple[int, bool], int] = {}

        def go(n: TreeNode | None, parent_robbed: bool) -> int:
            if n is None: return 0
            key = (id(n), parent_robbed)
            if key in memo: return memo[key]

            skip = go(n.left, False) + go(n.right, False)
            if parent_robbed:
                memo[key] = skip
                return skip

            rob = n.val + go(n.left, True) + go(n.right, True)
            memo[key] = max(rob, skip)
            return memo[key]

        return go(root, False)
    ```

    O(n) time, O(n) memo. Two cache entries per node.

=== "Layer 2 — Tuple-return tree DP (the elegant solution)"

    ```python
    def rob(root: TreeNode | None) -> int:
        def go(n: TreeNode | None) -> tuple[int, int]:
            """Returns (rob_this, skip_this)."""
            if n is None: return (0, 0)
            l_rob, l_skip = go(n.left)
            r_rob, r_skip = go(n.right)
            rob_this  = n.val + l_skip + r_skip
            skip_this = max(l_rob, l_skip) + max(r_rob, r_skip)
            return (rob_this, skip_this)

        return max(go(root))
    ```

    **O(n)** time, **O(h)** stack. The interview answer.

=== "Layer 3 — Iterative postorder"

    ```python
    def rob_iter(root: TreeNode | None) -> int:
        if root is None: return 0
        # Build postorder; compute (rob, skip) for each.
        stack: list[tuple[TreeNode, bool]] = [(root, False)]
        rob_skip: dict[int, tuple[int, int]] = {}
        while stack:
            n, processed = stack.pop()
            if not processed:
                stack.append((n, True))
                if n.right: stack.append((n.right, False))
                if n.left:  stack.append((n.left,  False))
            else:
                l = rob_skip.get(id(n.left),  (0, 0))
                r = rob_skip.get(id(n.right), (0, 0))
                rob_this  = n.val + l[1] + r[1]
                skip_this = max(l) + max(r)
                rob_skip[id(n)] = (rob_this, skip_this)
        return max(rob_skip[id(root)])
    ```

=== "Layer 4 — N-ary tree generalization"

    ```python
    def rob_nary(root: NaryNode | None) -> int:
        def go(n: NaryNode | None) -> tuple[int, int]:
            if n is None: return (0, 0)
            rob_this, skip_this = n.val, 0
            for c in n.children:
                cr, cs = go(c)
                rob_this  += cs
                skip_this += max(cr, cs)
            return (rob_this, skip_this)
        return max(go(root))
    ```

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def rob(root: TreeNode | None) -> int:
        """Maximum loot from a binary-tree house arrangement.

        Adjacent nodes (parent-child) cannot both be robbed.

        Args:
            root: Root of the binary tree.

        Returns:
            Maximum total loot.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        def post(node: TreeNode | None) -> tuple[int, int]:
            if node is None:
                return (0, 0)
            left_rob, left_skip = post(node.left)
            right_rob, right_skip = post(node.right)
            rob_node  = node.val + left_skip + right_skip
            skip_node = max(left_rob, left_skip) + max(right_rob, right_skip)
            return (rob_node, skip_node)

        return max(post(root))
    ```

##### 🔍 Dry Run

```
        3
       / \
      2   3
       \   \
        3   1
```

Postorder:

| node | (rob, skip) | reasoning |
|------|-------------|-----------|
| leaf 3 (under 2) | (3, 0) | rob: 3; skip: 0 |
| 2 | (2 + 0 = 2, max(3, 0) = 3) | (2, 3) |
| leaf 1 (under right 3) | (1, 0) | |
| right 3 | (3 + 0 = 3, max(1, 0) = 1) | (3, 1) |
| root 3 | (3 + 3 + 1 = 7, max(2,3) + max(3,1) = 6) | (7, 6) |

Answer: max(7, 6) = **7** ✓.

##### ⏱️ Complexity

- **Time: O(n)** — each node visited once.
- **Space: O(h)** for the recursion stack.

##### 🎯 Pattern Used

**Two-value tuple-return tree DP.** The same shape as "Diameter" (Problem 5) and "Max Path Sum" (Problem 22) — return a **summary tuple** that lets the parent make optimal decisions.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Linear House Robber on an array (1D version)?"
    Same DP collapsed to 1D: `dp[i] = max(dp[i-1], dp[i-2] + a[i])`. The tree version generalizes by having two "branches" instead of one predecessor.

??? question "Follow-up 2 — Ternary tree?"
    Same logic; sum `skip` of all children for the rob case; sum `max(c.rob, c.skip)` of all children for skip.

??? question "Follow-up 3 — Recover the chosen houses?"
    Track decisions via a parallel structure mapping each subtree to "robbed_root_set." More memory but doable.

??? question "Follow-up 4 — What if some nodes have negative values?"
    Treat them as "skip-only" by checking `max(0, ...)` in the rob branch — except the original problem usually assumes non-negative.

??? question "Follow-up 5 — Constrained: must rob at least k houses?"
    State explosion: track `(robs_remaining, parent_state)` per node. Polynomial in k.

##### 🐛 Common Bugs

1. **Returning only the max** — loses information needed by the parent.
2. **Confusing the tuple ordering** — `(rob, skip)` vs `(skip, rob)`. Pick one and document.
3. **Adding `n.val` to skip** — wrong; skip means we don't take this node.
4. **Recursing only on left, forgetting right child** — silent wrong answer.
5. **Using `max(go(n.left))` instead of unpacking** — `max((a, b))` returns max of the two; works but obscures the intent.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0
- [ ] Single node → `n.val`
- [ ] Single node with negative value → max(0, val) — but standard problem says non-negative
- [ ] Linear chain → DP equivalent to 1D HouseRobber
- [ ] Skewed → still O(n)
- [ ] Balanced → straightforward
- [ ] Two-level only → trivially correct
- [ ] All zeros → 0

##### 🏢 Sample Interviewer Quote

> *"Houses are arranged as a binary tree. You can't rob both a parent and a child. Maximum loot?"*

Your opener: *"Tree DP. Each node returns `(rob_this, skip_this)`. rob: take this + both children's skip. skip: max of children's rob/skip. Final answer is max of root's tuple. O(n)."*

---

#### Problem 33 — Maximum Width of Binary Tree

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span>

> Given the root of a binary tree, return the **maximum width** among all levels. The width of a level is the **distance between the leftmost and rightmost non-null nodes** on that level, counting **null intermediate nodes** in between (as if the tree were a complete binary tree).

##### 📖 Story Mode

This isn't "count the nodes per level" — it's "as if we drew the tree with the gaps preserved, how wide is the widest level?" That's why nulls between the leftmost and rightmost nodes count.

The trick is **positional indexing**: assign the root index 1; for a node at index `p`, its left child is `2p` and right child is `2p + 1`. This is the **heap array** indexing. The width of any level = `max_index − min_index + 1` over the non-null nodes on that level.

> **Watch out:** indices grow like `2^depth`, so for a tree of depth 60 you've got astronomical indices. Reset (subtract `min_index` per level) to keep numbers manageable.

##### 🌍 Real-World Usage

- **Memory-allocation simulation** for binary heaps — visualize how wide an arena you'd need.
- **Tree-shaped layout / rendering** — knowing max width tells you canvas width.
- **Competition rounds and tournament brackets** — maximum simultaneous matches per round.
- **Layered network throughput** — busiest layer in a hierarchical service map.

##### 🧠 Thinking Process

1. **BFS** by levels, carrying `(node, index)` tuples.
2. At each level, compute width = last_index − first_index + 1.
3. Track the global max.

To avoid overflow with deep skewed trees, **subtract the minimum index** of the level from every index when pushing children — the *width* is invariant under translation.

##### 🐍 5 Layers of Solution

=== "Layer 1 — BFS with absolute indices"

    ```python
    from collections import deque


    def width_of_binary_tree(root: TreeNode | None) -> int:
        if root is None:
            return 0
        q: deque[tuple[TreeNode, int]] = deque([(root, 1)])
        best = 0
        while q:
            level_size = len(q)
            _, first_idx = q[0]
            last_idx = first_idx
            for _ in range(level_size):
                n, idx = q.popleft()
                last_idx = idx
                if n.left:  q.append((n.left,  2 * idx))
                if n.right: q.append((n.right, 2 * idx + 1))
            best = max(best, last_idx - first_idx + 1)
        return best
    ```

    **O(n)** time, **O(w)** space. Indices may grow huge — Python handles big ints, but other languages would overflow.

=== "Layer 2 — BFS with normalized indices"

    ```python
    def width_normalized(root: TreeNode | None) -> int:
        if root is None: return 0
        q: deque[tuple[TreeNode, int]] = deque([(root, 0)])
        best = 0
        while q:
            level_size = len(q)
            min_idx = q[0][1]
            first = min_idx
            last = first
            for _ in range(level_size):
                n, idx = q.popleft()
                idx -= min_idx       # normalize
                last = idx
                if n.left:  q.append((n.left,  2 * idx))
                if n.right: q.append((n.right, 2 * idx + 1))
            best = max(best, last - first + 1)
        return best
    ```

    Same complexity but indices stay small.

=== "Layer 3 — DFS with leftmost-per-depth"

    ```python
    def width_dfs(root: TreeNode | None) -> int:
        if root is None: return 0
        leftmost: dict[int, int] = {}
        best = 0

        def go(n: TreeNode | None, depth: int, idx: int) -> None:
            nonlocal best
            if n is None: return
            if depth not in leftmost:
                leftmost[depth] = idx
            best = max(best, idx - leftmost[depth] + 1)
            go(n.left,  depth + 1, 2 * idx)
            go(n.right, depth + 1, 2 * idx + 1)

        go(root, 0, 0)
        return best
    ```

    **O(n)** time, **O(h)** stack. Avoids the queue entirely.

=== "Layer 4 — Hybrid: BFS-by-level with running max"

    Same as Layer 2 but compute `last - first + 1` per dequeue, not after the level — slightly more bookkeeping, no benefit. Skip.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations
    from collections import deque


    def width_of_binary_tree(root: TreeNode | None) -> int:
        """Maximum level width counting null gaps as if the tree were complete.

        Args:
            root: Root of the binary tree.

        Returns:
            Maximum width of any level (1 if single node, 0 if empty).

        Time:  O(n).
        Space: O(w) where w = max width.
        """
        if root is None:
            return 0

        queue: deque[tuple[TreeNode, int]] = deque([(root, 0)])
        max_width = 0

        while queue:
            level_size = len(queue)
            base = queue[0][1]
            first = last = 0
            for i in range(level_size):
                node, idx = queue.popleft()
                norm = idx - base
                if i == 0:
                    first = norm
                last = norm
                if node.left:
                    queue.append((node.left,  2 * norm))
                if node.right:
                    queue.append((node.right, 2 * norm + 1))
            max_width = max(max_width, last - first + 1)

        return max_width
    ```

##### 🔍 Dry Run

```
        1
       / \
      3   2
     /     \
    5       9
   / \    /
  6   7  8
```

BFS with normalized indices:

| level | items (norm idx) | width |
|-------|-----------|-------|
| 0 | 1@0 | 1 |
| 1 | 3@0, 2@1 | 2 |
| 2 | 5@0, 9@3 | 4 |
| 3 | 6@0, 7@1, 8@6 | 7 |

Max width = **7** ✓.

(Level 3: 5's children are at idx 0,1; 9's left child is at idx 6 (= 2 * 3 = 6). 6 - 0 + 1 = 7.)

##### ⏱️ Complexity

- **Time: O(n)** — each node enqueued/dequeued once.
- **Space: O(w)** queue, **O(d)** for the per-depth `leftmost` map in the DFS variant.

##### 🎯 Pattern Used

**Heap-array positional indexing on a tree.** The same indexing converts arbitrary trees into "complete-tree-like" arrays for analysis. Useful in competitive programming.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why not just count nodes per level?"
    Counts ignore null gaps. The problem explicitly counts gaps as if the tree were complete: `width = right_idx - left_idx + 1`.

??? question "Follow-up 2 — How to avoid huge indices in deep trees?"
    Normalize per level (Layer 2): subtract `min_index` of the level from every index.

??? question "Follow-up 3 — DFS or BFS — which is better?"
    Both are O(n). DFS uses O(h) recursion stack; BFS uses O(w) queue. Pick based on shape.

??? question "Follow-up 4 — N-ary tree?"
    Indexing changes: child k of a node at index p is at `n*p + k` for n-ary. Same width formula.

??? question "Follow-up 5 — What if values can be `null`?"
    The problem distinguishes between null **nodes** and node **values**. Null nodes are gaps; null values just behave as normal nodes.

##### 🐛 Common Bugs

1. **Counting nodes** instead of indices → wrong on sparse levels.
2. **Forgetting to normalize** → on deep trees, indices grow as 2^depth.
3. **Off-by-one in width formula** — `last - first + 1`, not `last - first`.
4. **Using `level_size` after enqueueing children** — must snapshot it via `len(queue)` before the inner loop (the §10 BFS pattern).
5. **Treating empty tree → return 1** — should return 0.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → 0
- [ ] Single node → 1
- [ ] Skewed left → 1 every level
- [ ] Skewed right → 1 every level
- [ ] Deep tree where last level has only the leftmost and rightmost → wide level
- [ ] Two-level perfect tree → 2
- [ ] Three-level perfect tree → 4
- [ ] Tree depth ~60 → normalize to avoid arithmetic blow-up

##### 🏢 Sample Interviewer Quote

> *"Maximum width of this binary tree, counting null gaps."*

Your opener: *"BFS with positional indexing: root=0, left child = 2p, right = 2p+1. Per level, width = last_idx - first_idx + 1. Normalize indices each level so they stay small. O(n)."*

---

#### Problem 34 — Smallest Subtree with All Deepest Nodes

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Apple</span>

> Given the root of a binary tree, return the **smallest subtree** that contains all the **deepest** nodes (i.e. nodes at the maximum depth in the original tree).

##### 📖 Story Mode

The "smallest subtree containing the deepest nodes" is the **LCA of the deepest leaves**. If there's only one deepest leaf, the answer is that leaf. If there are multiple, it's their lowest common ancestor.

A single postorder DFS computes this elegantly: each subtree returns `(depth_of_deepest_leaf_in_this_subtree, lca_of_those_leaves)`. At each node, if the left and right subtrees report the same depth, the current node is their LCA; otherwise the answer for this subtree is whichever side reported the larger depth.

##### 🌍 Real-World Usage

- **DOM "deepest common ancestor"** — find the smallest container that encloses all deepest leaf elements.
- **Phylogenetic trees** — find the most recent common ancestor of all "leaf" species at the deepest evolutionary depth.
- **Decision trees** — find the smallest sub-problem whose leaves are the deepest decision points.
- **File-system queries** — smallest folder that contains all deepest files (deepest = most-nested).

##### 🧠 Thinking Process

The recursive contract: `dfs(node) → (depth, subtree_root)` where:

- `depth` = depth of deepest leaf in `node`'s subtree (counting from the *root*, or from `node`; either works as long as it's consistent).
- `subtree_root` = root of the smallest subtree that contains all deepest leaves of `node`'s subtree.

Then at each node:

- Recurse on both children.
- If `left_depth == right_depth`, the answer is `node` itself (LCA of left's deepest and right's deepest).
- If `left_depth > right_depth`, the answer is `left_subtree_root`.
- Else the answer is `right_subtree_root`.

Return `(max(left_depth, right_depth) + 1, computed_subtree_root)`.

> **Why this works:** the LCA of any two leaves in a tree is the lowest node from which paths to both leaves diverge. By bubbling up "deepest depth + lca-so-far," we find that split point exactly when both children report equal max depth.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Two-pass: find max depth, then LCA"

    ```python
    def subtree_with_deepest_two_pass(root: TreeNode | None) -> TreeNode | None:
        if root is None: return None

        max_depth = 0
        def find_depth(n: TreeNode | None, d: int) -> None:
            nonlocal max_depth
            if n is None: return
            max_depth = max(max_depth, d)
            find_depth(n.left, d + 1)
            find_depth(n.right, d + 1)
        find_depth(root, 0)

        def lca(n: TreeNode | None, d: int) -> TreeNode | None:
            if n is None: return None
            if d == max_depth: return n
            l = lca(n.left,  d + 1)
            r = lca(n.right, d + 1)
            if l and r: return n
            return l or r

        return lca(root, 0)
    ```

    Two O(n) passes.

=== "Layer 2 — Single postorder returning (depth, lca)"

    ```python
    def subtree_with_deepest(root: TreeNode | None) -> TreeNode | None:
        def go(n: TreeNode | None) -> tuple[int, TreeNode | None]:
            if n is None: return (0, None)
            ld, ln = go(n.left)
            rd, rn = go(n.right)
            if ld == rd: return (ld + 1, n)
            if ld > rd:  return (ld + 1, ln)
            return (rd + 1, rn)
        return go(root)[1]
    ```

    **O(n)** time, **O(h)** stack. The clean answer.

=== "Layer 3 — Iterative variant"

    Same shape but with explicit postorder stack; useful for very deep trees.

=== "Layer 4 — N-ary generalization"

    ```python
    def subtree_with_deepest_nary(root: NaryNode | None) -> NaryNode | None:
        def go(n: NaryNode | None) -> tuple[int, NaryNode | None]:
            if n is None: return (0, None)
            best_depth = 0
            best_nodes: list[NaryNode] = []
            for c in n.children:
                d, sub = go(c)
                if d > best_depth:
                    best_depth = d
                    best_nodes = [sub]
                elif d == best_depth:
                    best_nodes.append(sub)
            if best_depth == 0: return (1, n)
            if len(best_nodes) == 1: return (best_depth + 1, best_nodes[0])
            return (best_depth + 1, n)
        return go(root)[1]
    ```

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def subtree_with_all_deepest(root: TreeNode | None) -> TreeNode | None:
        """Smallest subtree containing every deepest leaf.

        Args:
            root: Root of the binary tree.

        Returns:
            Root of the smallest subtree, or None if the tree is empty.

        Time:  O(n).
        Space: O(h) recursion stack.
        """
        def post(node: TreeNode | None) -> tuple[int, TreeNode | None]:
            """Return (deepest_depth, lca_of_deepest_in_this_subtree)."""
            if node is None:
                return (0, None)
            left_depth, left_lca = post(node.left)
            right_depth, right_lca = post(node.right)
            if left_depth == right_depth:
                return (left_depth + 1, node)
            if left_depth > right_depth:
                return (left_depth + 1, left_lca)
            return (right_depth + 1, right_lca)

        return post(root)[1]
    ```

##### 🔍 Dry Run

```
         3
        / \
       5   1
      / \ / \
     6  2 0  8
       / \
      7   4
```

Postorder visits:

| node | left (d, lca) | right (d, lca) | result |
|------|---------------|----------------|--------|
| 6 | (0, None) | (0, None) | (1, 6) |
| 7 | (0, None) | (0, None) | (1, 7) |
| 4 | (0, None) | (0, None) | (1, 4) |
| 2 | (1, 7) | (1, 4) | left==right=1 → (2, 2) |
| 5 | (1, 6) | (2, 2) | right>left → (3, 2) |
| 0 | (0, None) | (0, None) | (1, 0) |
| 8 | (0, None) | (0, None) | (1, 8) |
| 1 | (1, 0) | (1, 8) | equal → (2, 1) |
| 3 (root) | (3, 2) | (2, 1) | left>right → (4, 2) |

Answer: subtree rooted at **2** ✓.

##### ⏱️ Complexity

- **Time: O(n)** — each node visited once.
- **Space: O(h)** for the recursion stack.

##### 🎯 Pattern Used

**Postorder returning a tuple** that simultaneously summarizes "depth seen" and "the answer subtree." Same pattern as Diameter (Problem 5) and LCA (Problem 16).

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Single deepest leaf?"
    The algorithm returns it (the leaf is its own subtree).

??? question "Follow-up 2 — All leaves at the same depth (perfect tree)?"
    The answer is the root.

??? question "Follow-up 3 — How is this different from LCA (Problem 16)?"
    LCA takes two specified nodes. Here, the "two nodes" are implicitly all the deepest leaves. The algorithm computes them on the fly.

??? question "Follow-up 4 — Depth-tagged variant: subtree containing all leaves at exactly depth k?"
    Same idea but compare equality with `k` instead of returning max depth.

??? question "Follow-up 5 — N-ary tree?"
    Layer 4 — when 2+ children share max depth, the current node is the LCA.

##### 🐛 Common Bugs

1. **Returning the LCA of `(left_lca, right_lca)` always** — wrong; only when depths match. If one side is deeper, it dominates.
2. **Comparing `n.left.depth` directly** — `None` doesn't have a depth; the recursion's `(0, None)` handles the base case.
3. **Off-by-one in depth** — pick "depth from root" or "depth from node" consistently; `+1` increments per recursion level.
4. **Using values to compare leaves** — leaves are compared by depth, not by value.
5. **Two-pass approach forgetting the LCA aggregation rule** — `if l and r: return n; else l or r`.

##### ✅ Edge Cases Checklist

- [ ] Empty tree → None
- [ ] Single node → that node
- [ ] Two-leaf tree (root with two leaves) → root
- [ ] Skewed tree → the only leaf
- [ ] Multiple deepest leaves under same parent → that parent
- [ ] Multiple deepest leaves under different parents → their LCA
- [ ] Perfect tree → root
- [ ] Deep tree → recursion stack manageable

##### 🏢 Sample Interviewer Quote

> *"Find the smallest subtree that contains all the deepest leaves of this binary tree."*

Your opener: *"Postorder; each call returns `(deepest_depth, current_lca)`. If left and right depths match, current node is the LCA. Otherwise, the deeper side's lca propagates up. O(n)."*

---

#### Problem 35 — Verify Preorder Serialization of a Binary Tree

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">LinkedIn</span> <span class="company-tag">Microsoft</span>

> Given a comma-separated string representing the **preorder traversal** of a binary tree where `#` denotes a null node, verify whether it is a **valid** serialization. You must do this **without** reconstructing the tree.

##### 📖 Story Mode

A valid preorder string fills out the tree by always consuming the next available "slot." The root takes one slot and produces two new ones (its children). Each non-null node takes one slot and produces two; each `#` takes one and produces zero.

So we maintain a **slot counter**: start at 1. For each token:

- `#`: slot − 1.
- non-null: slot − 1 + 2 = slot + 1.

The string is valid iff slots **never go negative** and ends at exactly **0**.

There's also an elegant graph-theoretic argument: in a valid binary tree with `n` nodes and `m` nulls, **edges = n + m − 1** (counting null leaves) but each non-null contributes 2 edges (to children, real or null) and the root contributes one in-edge. Setting these equal gives the slot equation.

##### 🌍 Real-World Usage

- **Network protocol validators** — confirm the wire format is well-formed without parsing into objects.
- **Compiler / linter** — quickly check serialized AST validity before deserializing.
- **Database export validators** — sanity-check tree exports.
- **Static analyzers** for tree-typed config files.
- **Streaming input — fail fast** if invalid input arrives early.

##### 🧠 Thinking Process

The slot trick is the canonical approach. An alternative: count `2 * non_null + 1 - null`; valid iff this equals 0 at the end **and** non-negative throughout.

Both approaches are O(n) single-pass.

> **Slot counter formulation:**
>
> 1. Initialize `slots = 1`.
> 2. For each token, decrement by 1. If slots < 0 → invalid.
> 3. If token is non-null, increment by 2.
> 4. At end, valid iff slots == 0.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Slot counter"

    ```python
    def is_valid_preorder(preorder: str) -> bool:
        slots = 1
        for tok in preorder.split(","):
            if slots == 0:
                return False
            slots -= 1
            if tok != "#":
                slots += 2
        return slots == 0
    ```

    **O(n)** time, **O(1)** extra (after split). Cleanest answer.

=== "Layer 2 — Stack-collapse"

    ```python
    def is_valid_preorder_stack(preorder: str) -> bool:
        stack: list[str] = []
        for tok in preorder.split(","):
            stack.append(tok)
            # Collapse "X,#,#" → "#" repeatedly.
            while len(stack) >= 3 and stack[-1] == "#" and stack[-2] == "#" and stack[-3] != "#":
                stack.pop(); stack.pop(); stack.pop()
                stack.append("#")
        return stack == ["#"]
    ```

    Mimics recursive deserialization: every "node, null, null" pattern collapses to a null. **O(n)** amortized.

=== "Layer 3 — Two-counter (in-edges vs out-edges)"

    ```python
    def is_valid_preorder_edges(preorder: str) -> bool:
        in_deg = 1   # the root needs one in-edge
        out_deg = 0
        for tok in preorder.split(","):
            in_deg -= 1                # arriving at this node consumes 1 in-edge
            if in_deg < 0: return False
            if tok != "#":
                in_deg += 2            # node's two children need in-edges
        return in_deg == 0
    ```

    Identical math, framed as edge counting. Helpful for the "prove it" follow-up.

=== "Layer 4 — Streaming validation"

    ```python
    from typing import Iterable


    def is_valid_preorder_stream(tokens: Iterable[str]) -> bool:
        slots = 1
        for tok in tokens:
            if slots == 0: return False
            slots -= 1
            if tok != "#": slots += 2
        return slots == 0
    ```

    Same complexity, doesn't materialize the full token list — useful for very large input.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def is_valid_preorder(preorder: str) -> bool:
        """Validate a preorder serialization with `#` for null.

        Uses the slot-counting argument: starting with 1 slot, each token
        consumes 1; non-null tokens add 2. Slots must stay non-negative and
        end at 0.

        Args:
            preorder: Comma-separated tokens (e.g. ``"9,3,4,#,#,1,#,#,2,#,6,#,#"``).

        Returns:
            True iff the string is a valid preorder serialization.

        Time:  O(n).
        Space: O(1) extra after split.
        """
        slots = 1
        for token in preorder.split(","):
            if slots == 0:
                return False
            slots -= 1
            if token != "#":
                slots += 2
        return slots == 0
    ```

##### 🔍 Dry Run

`"9,3,4,#,#,1,#,#,2,#,6,#,#"` (a valid preorder):

| token | slots before | slots after |
|-------|--------------|-------------|
| 9 | 1 | 0+2 = 2 |
| 3 | 2 | 1+2 = 3 |
| 4 | 3 | 2+2 = 4 |
| # | 4 | 3 |
| # | 3 | 2 |
| 1 | 2 | 1+2 = 3 |
| # | 3 | 2 |
| # | 2 | 1 |
| 2 | 1 | 0+2 = 2 |
| # | 2 | 1 |
| 6 | 1 | 0+2 = 2 |
| # | 2 | 1 |
| # | 1 | 0 |

End: slots = 0 → **valid** ✓.

`"1,#"` (invalid):

| token | slots before | slots after |
|-------|--------------|-------------|
| 1 | 1 | 0+2 = 2 |
| # | 2 | 1 |

End: slots = 1 ≠ 0 → **invalid** ✓.

##### ⏱️ Complexity

- **Time: O(n)** — single pass over tokens.
- **Space: O(1)** beyond the split.

##### 🎯 Pattern Used

**Capacity / slot accounting** — a common technique for validating tree-structured streams. The same "in-degree vs out-degree" argument validates DAG topological sorts.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why does the slot trick work?"
    Each node consumes a slot (the place where it lives in its parent's tree) and adds two new slots (its two child positions, real or null). At the start there's one slot (the root). At a valid end, all slots must be filled.

??? question "Follow-up 2 — Without splitting the string?"
    Iterate character-by-character; track whether you're inside a token. Same O(n).

??? question "Follow-up 3 — Validate inorder or postorder serialization?"
    Postorder: same trick but iterate in reverse and the rules flip. Inorder: ambiguous — can't validate without extra info.

??? question "Follow-up 4 — Validate AND deserialize in one pass?"
    Combine: same slot logic but materialize a node on each non-null token. If you ever fail validation, abort.

??? question "Follow-up 5 — What if the input has extra whitespace?"
    Strip each token before comparing.

##### 🐛 Common Bugs

1. **Forgetting to check `slots == 0` before decrementing** — early returning false on a valid input that uses up its last slot.
2. **Returning true when `slots > 0` at end** — only `== 0` is valid.
3. **Treating `#` and a numeric `0` differently** — the spec says `#` for null; numeric values can include `0`.
4. **Off-by-one initial value** — `slots = 1` (root takes one), not `slots = 0`.
5. **Using stack collapse but not the right comparator** — the third element from top must be a non-null number for the collapse to apply.

##### ✅ Edge Cases Checklist

- [ ] `"#"` → valid (just the null root)
- [ ] `""` → invalid (empty)
- [ ] `"1"` → invalid (root present but no nulls for its children)
- [ ] `"1,#,#"` → valid (root + two null children)
- [ ] `"1,#,#,#"` → invalid (extra token)
- [ ] Negative numbers like `"-1,#,#"` → valid (token isn't `#`)
- [ ] Very long valid serialization → O(n) handles
- [ ] Stack approach: triple-equal-#s case

##### 🏢 Sample Interviewer Quote

> *"Validate this preorder serialization without building the tree."*

Your opener: *"Slot counter. Start at 1. Each token consumes 1; non-null tokens add 2. Valid iff slots stay non-negative throughout and end at 0. O(n) time, O(1) extra."*

---

### Bonus (36–40) — design and edge-case rounds

#### Problem 36 — Design a Trie (Prefix Tree)

<span class="diff-medium">Medium</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Meta</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> Implement a **Trie** with the following methods: `insert(word)`, `search(word)` (exact-word match), and `startsWith(prefix)` (any word with this prefix exists).

##### 📖 Story Mode

A Trie ("retrieval tree") is the canonical data structure for **prefix-keyed** lookups. Each node represents a prefix; each edge is labeled by a single character. Walking from root to a marked node spells out a stored word.

Where a hash map gives you O(L) average lookup but no notion of prefix neighborhoods, a Trie gives you O(L) for both lookup AND prefix iteration — and shares storage among words with common prefixes.

##### 🌍 Real-World Usage

- **Autocomplete** — type-ahead suggestions on search engines and IDEs.
- **Spell-checkers** — "did you mean" suggestions via prefix exploration + edit distance.
- **IP routing tables** — longest-prefix-match on binary tries.
- **Genome sequence indexing** — generalized suffix tries, FM-indexes.
- **DNS resolvers** — domain name prefix matching.
- **Word games** — Boggle, Scrabble dictionaries.
- **Chrome's URL omnibox** — prefix-based history search.

##### 🧠 Thinking Process

Each node stores:

- A mapping of next character → child node (`dict[str, Node]` for general; `list[Node | None]` of size 26 for fixed alphabet).
- A boolean `is_word` marking that "the path from root to this node spells a stored word."

`insert(word)`: walk character-by-character, creating children on demand; mark the final node `is_word`.

`search(word)`: walk; if missing a child mid-path, return False; at end, return `is_word`.

`startsWith(prefix)`: same walk; at end, just return True (don't check `is_word`).

> **Key distinction:** `search` requires `is_word = True` at the end. `startsWith` doesn't care — any node reachable along the path means the prefix has at least one word.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Dict-based children"

    ```python
    class Trie:
        def __init__(self) -> None:
            self.children: dict[str, "Trie"] = {}
            self.is_word: bool = False

        def insert(self, word: str) -> None:
            node = self
            for ch in word:
                if ch not in node.children:
                    node.children[ch] = Trie()
                node = node.children[ch]
            node.is_word = True

        def search(self, word: str) -> bool:
            node = self._walk(word)
            return node is not None and node.is_word

        def starts_with(self, prefix: str) -> bool:
            return self._walk(prefix) is not None

        def _walk(self, s: str) -> "Trie | None":
            node = self
            for ch in s:
                if ch not in node.children:
                    return None
                node = node.children[ch]
            return node
    ```

    **O(L)** per operation; **O(total characters inserted)** space.

=== "Layer 2 — Array-of-26 children (faster, fixed alphabet)"

    ```python
    class TrieArr:
        __slots__ = ("children", "is_word")

        def __init__(self) -> None:
            self.children: list["TrieArr | None"] = [None] * 26
            self.is_word = False

        def insert(self, word: str) -> None:
            node = self
            for ch in word:
                idx = ord(ch) - ord("a")
                if node.children[idx] is None:
                    node.children[idx] = TrieArr()
                node = node.children[idx]
            node.is_word = True

        def search(self, word: str) -> bool:
            node = self
            for ch in word:
                node = node.children[ord(ch) - ord("a")]
                if node is None:
                    return False
            return node.is_word

        def starts_with(self, prefix: str) -> bool:
            node = self
            for ch in prefix:
                node = node.children[ord(ch) - ord("a")]
                if node is None:
                    return False
            return True
    ```

    Faster constant due to no dict overhead. **O(L)** per op; **O(26 × total nodes)** space.

=== "Layer 3 — Compressed (radix tree)"

    Each edge stores a string instead of a single character. Saves space when many nodes have a single child. Implementation is more complex; covered in Advanced.

=== "Layer 4 — Trie with deletion"

    ```python
    class TrieDel(Trie):
        def delete(self, word: str) -> bool:
            def _del(node: "Trie", word: str, depth: int) -> bool:
                """Returns True if the current node should be deleted."""
                if depth == len(word):
                    if not node.is_word:
                        return False
                    node.is_word = False
                    return not node.children
                ch = word[depth]
                child = node.children.get(ch)
                if child is None:
                    return False
                if _del(child, word, depth + 1):
                    del node.children[ch]
                    return not node.is_word and not node.children
                return False

            return _del(self, word, 0)
    ```

    Removes a word; prunes empty branches. O(L).

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    class Trie:
        """Prefix tree (trie).

        Supports insertion, exact-word search, and prefix existence checks
        in O(L) time per operation, where L is the length of the word/prefix.
        """

        __slots__ = ("children", "is_word")

        def __init__(self) -> None:
            self.children: dict[str, Trie] = {}
            self.is_word: bool = False

        def insert(self, word: str) -> None:
            """Insert `word` into the trie."""
            node = self
            for ch in word:
                child = node.children.get(ch)
                if child is None:
                    child = Trie()
                    node.children[ch] = child
                node = child
            node.is_word = True

        def search(self, word: str) -> bool:
            """Return True iff `word` is in the trie as a complete word."""
            node = self._traverse(word)
            return node is not None and node.is_word

        def starts_with(self, prefix: str) -> bool:
            """Return True iff any inserted word begins with `prefix`."""
            return self._traverse(prefix) is not None

        def _traverse(self, s: str) -> Trie | None:
            node: Trie | None = self
            for ch in s:
                if node is None:
                    return None
                node = node.children.get(ch)
            return node
    ```

##### 🔍 Dry Run

Insert `"apple"`, `"app"`, `"apt"`. Then search and prefix-check.

```
After insert("apple"):
  root → a → p → p → l → e (is_word=True)

After insert("app"):
  root → a → p → p (is_word=True) → l → e (is_word=True)

After insert("apt"):
  root → a → p → ┬→ p (is_word=True) → l → e (is_word=True)
                 └→ t (is_word=True)
```

`search("app")` → walk root→a→p→p; final is_word=True → **True** ✓
`search("appl")` → walk root→a→p→p→l; final is_word=False → **False** ✓
`starts_with("ap")` → walk root→a→p exists → **True** ✓
`starts_with("apz")` → at p, no z child → **False** ✓

##### ⏱️ Complexity

- **Time: O(L)** per `insert` / `search` / `startsWith`.
- **Space: O(N × L)** where N = number of inserted words, L = average length. Common prefixes share storage.

##### 🎯 Pattern Used

**Prefix-shared tree storage.** The same idea generalizes to **suffix tries**, **Aho-Corasick**, and **patricia/radix tries** for IP routing.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — How do you delete a word?"
    Mark `is_word = False` at the terminal node. If that node has no children, prune it; recurse upward removing empty branches. Layer 4 covers it.

??? question "Follow-up 2 — Wildcard search (`a.c` matches `abc` and `azc`)?"
    DFS at each node when you see `.`, branching into all 26 children. O(26^L) worst case but usually fast.

??? question "Follow-up 3 — Memory optimization?"
    Use the array-of-26 layout, or `__slots__`, or compress single-child chains into edges (radix tree).

??? question "Follow-up 4 — Persistent / immutable trie?"
    Each insert returns a new root with structural sharing. Useful in functional languages and version-controlled data.

??? question "Follow-up 5 — Top-K autocomplete?"
    At each node, store the top-K most-popular words in its subtree (heap). Insert/search update the heap. Used in production search bars.

##### 🐛 Common Bugs

1. **Forgetting `is_word`** — `search("ap")` returns True if you only check "node exists."
2. **Sharing default-mutable children**: `children: dict = {}` at class level → all instances share the same dict.
3. **Case sensitivity** — decide upfront and document.
4. **Unicode** — array-of-26 fails for non-ASCII. Use dict.
5. **Inserting empty string** — should mark root's `is_word = True`. Edge case.

##### ✅ Edge Cases Checklist

- [ ] Empty trie → `search` and `starts_with` return False
- [ ] Insert empty string → `search("")` returns True
- [ ] Insert duplicate word → idempotent
- [ ] Search prefix that's also a word
- [ ] Search prefix that isn't a stored word
- [ ] Words with the same prefix share nodes
- [ ] Very long words (10⁵ chars) → O(L) per op
- [ ] Unicode words → use dict, not array-of-26

##### 🏢 Sample Interviewer Quote

> *"Design a Trie. Implement insert, search, and startsWith."*

Your opener: *"Each node has a children dict and an is_word boolean. Insert walks creating children on demand; search walks then checks is_word; startsWith walks and returns True. All O(L)."*



#### Problem 37 — Word Search II (Trie + DFS over a board)

<span class="diff-hard">Hard</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> Given an `m × n` board of characters and a list of `words`, return all words that can be formed by sequentially adjacent (horizontally/vertically) cells, where the same cell may not be used more than once per word.

##### 📖 Story Mode

The naive approach: for each word, run a Word Search I (single-word DFS) — `O(W · m · n · 4^L)` where W is the number of words and L is max word length. For W = 10⁴ words, this is millions of independent searches that mostly retrace the same cell paths.

The Trie unlocks the elegant fix: **load all words into a Trie first**, then DFS the board *once*, walking the Trie in lockstep with the board. At each cell we descend into the Trie if the letter is a child of the current Trie node; if not, we prune. Every step prunes work for **every word** that doesn't pass through this cell.

##### 🌍 Real-World Usage

- **Boggle / Scrabble solvers** — find all valid words on a letter grid.
- **Kindle dictionary search** — efficient prefix-aware search.
- **Crossword puzzle generation / solving** — Trie pruning for fitted word lists.
- **OCR post-processing** — confirm that a candidate string forms valid dictionary words.
- **DNA / protein motif search** — multi-pattern matching on a sequence grid.

##### 🧠 Thinking Process

1. **Build a Trie** of all the words. Mark the terminal node of each word with the word itself (a small optimization — saves us assembling the path during DFS).
2. **DFS each board cell** as a starting point. Pass the Trie node along.
3. At each step:
   - If the cell's letter isn't in the current Trie node's children → prune.
   - If the child is a terminal → record the word, set its terminal to None to dedupe.
   - Recurse into 4 neighbors (mark current cell visited via a sentinel).
4. **Optional optimization:** prune dead branches of the Trie as words are found — once a node has no children and isn't terminal, splice it out of its parent.

> **Why Trie wins:** every prefix of every word is shared. The DFS visits each board path **at most once per Trie node**, not once per matching word.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Naive: word-by-word DFS"

    ```python
    def find_words_naive(board: list[list[str]], words: list[str]) -> list[str]:
        m, n = len(board), len(board[0])
        result: list[str] = []

        def dfs(r: int, c: int, w: str, idx: int) -> bool:
            if idx == len(w): return True
            if not (0 <= r < m and 0 <= c < n): return False
            if board[r][c] != w[idx]: return False
            ch = board[r][c]
            board[r][c] = "#"
            ok = (dfs(r+1,c,w,idx+1) or dfs(r-1,c,w,idx+1)
                  or dfs(r,c+1,w,idx+1) or dfs(r,c-1,w,idx+1))
            board[r][c] = ch
            return ok

        for w in words:
            if any(dfs(r, c, w, 0) for r in range(m) for c in range(n)):
                result.append(w)
        return result
    ```

    O(W × m × n × 4^L). Too slow for large W.

=== "Layer 2 — Trie + single board DFS"

    ```python
    def find_words(board: list[list[str]], words: list[str]) -> list[str]:
        # Build trie.
        root: dict = {}
        for w in words:
            node = root
            for ch in w:
                node = node.setdefault(ch, {})
            node["$"] = w   # terminal marker = the word

        m, n = len(board), len(board[0])
        result: list[str] = []

        def dfs(r: int, c: int, node: dict) -> None:
            ch = board[r][c]
            child = node.get(ch)
            if child is None: return
            if "$" in child:
                result.append(child["$"])
                del child["$"]   # dedupe
            board[r][c] = "#"
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r+dr, c+dc
                if 0 <= rr < m and 0 <= cc < n and board[rr][cc] != "#":
                    dfs(rr, cc, child)
            board[r][c] = ch
            # Prune dead branch.
            if not child:
                del node[ch]

        for r in range(m):
            for c in range(n):
                dfs(r, c, root)
        return result
    ```

    O(m × n × 4^L) — the canonical answer.

=== "Layer 3 — Class-based Trie"

    ```python
    class TrieNode:
        __slots__ = ("children", "word")
        def __init__(self) -> None:
            self.children: dict[str, TrieNode] = {}
            self.word: str | None = None


    def find_words_oo(board: list[list[str]], words: list[str]) -> list[str]:
        root = TrieNode()
        for w in words:
            node = root
            for ch in w:
                node = node.children.setdefault(ch, TrieNode())
            node.word = w

        m, n = len(board), len(board[0])
        result: list[str] = []

        def dfs(r: int, c: int, node: TrieNode) -> None:
            ch = board[r][c]
            child = node.children.get(ch)
            if child is None: return
            if child.word is not None:
                result.append(child.word)
                child.word = None
            board[r][c] = "#"
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r+dr, c+dc
                if 0 <= rr < m and 0 <= cc < n and board[rr][cc] != "#":
                    dfs(rr, cc, child)
            board[r][c] = ch
            if not child.children:
                del node.children[ch]

        for r in range(m):
            for c in range(n):
                dfs(r, c, root)
        return result
    ```

=== "Layer 4 — Pre-filter words by board frequency"

    Count letter frequencies on the board; skip any word whose required letter counts exceed the board's. Cheap pre-pass that often prunes 50%+ of the input dictionary.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    class _Node:
        __slots__ = ("children", "word")

        def __init__(self) -> None:
            self.children: dict[str, _Node] = {}
            self.word: str | None = None


    def find_words(board: list[list[str]], words: list[str]) -> list[str]:
        """Return every word from `words` that appears on `board`.

        Uses a trie + single board DFS with branch pruning.

        Time:  O(m * n * 4^L) where L is the longest word.
        Space: O(total characters in `words`) for the trie.
        """
        root = _Node()
        for w in words:
            node = root
            for ch in w:
                node = node.children.setdefault(ch, _Node())
            node.word = w

        m, n = len(board), len(board[0])
        found: list[str] = []
        VISITED = "#"

        def dfs(r: int, c: int, parent: _Node) -> None:
            letter = board[r][c]
            child = parent.children.get(letter)
            if child is None:
                return
            if child.word is not None:
                found.append(child.word)
                child.word = None      # dedupe

            board[r][c] = VISITED
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < m and 0 <= cc < n and board[rr][cc] != VISITED:
                    dfs(rr, cc, child)
            board[r][c] = letter

            if not child.children:
                del parent.children[letter]

        for r in range(m):
            for c in range(n):
                dfs(r, c, root)

        return found
    ```

##### 🔍 Dry Run

Board:
```
o a a n
e t a e
i h k r
i f l v
```

Words: `["oath", "pea", "eat", "rain"]`.

Trie (after build):
```
root
├─ o → a → t → h ($oath)
├─ p → e → a ($pea)
├─ e → a → t ($eat)
└─ r → a → i → n ($rain)
```

DFS from `(0,0)='o'`: trie root has 'o' → walk. Then `(0,1)='a'` → trie has 'o→a'. Then `(1,1)='t'` → 'o→a→t'. Then `(2,1)='h'` → terminal `$oath` → append. Backtrack.

DFS later from `(1,0)='e'`: trie has 'e'. Then neighbor `(0,0)='o'` → no 'o' under 'e', prune. Try `(2,0)='i'` → no 'i' under 'e', prune. Try `(1,1)='t'` → no 't' under 'e', prune. Etc.

DFS from `(0,2)='a'` reaches 'eat' indirectly... actually 'eat' starts with 'e', so search starts from cells with 'e': `(1,0)` and `(1,3)`. From `(1,3)='e'` → `(0,3)='n'`? no. Note `(1,3)→(1,2)='a'→(0,2)='a'`? Wait — 'eat' = e, a, t. From `(1,3)` neighbor `(0,3)='n'` no; `(2,3)='r'` no; `(1,2)='a'` yes → `(0,2)='a'`? we need 'a' then 't'. `(1,2)='a'` then neighbor `(1,1)='t'` → reach terminal `$eat` → append.

Final result: `["oath", "eat"]` (no `pea`, no `rain` on the given board) ✓.

##### ⏱️ Complexity

- **Time: O(m × n × 4^L)** where L is the max word length. The Trie pruning cuts the constant dramatically in practice.
- **Space: O(total characters in `words`)** for the Trie + O(L) recursion stack.

##### 🎯 Pattern Used

**Multi-pattern matching via Trie + grid DFS with in-place visited marker.** A textbook composition of "load patterns into a prefix structure, then walk the input alongside the structure."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why is single-DFS-on-Trie better than multiple DFS-per-word?"
    A single board DFS visits every cell at most O(4^L) times **regardless of word count**. Per-word DFS multiplies by W, the number of words.

??? question "Follow-up 2 — Optimize when most words don't appear?"
    Pre-filter by letter frequency (Layer 4). Also prune Trie branches as words are found.

??? question "Follow-up 3 — Diagonal moves allowed?"
    Add 4 more deltas (diagonal directions). Same algorithm.

??? question "Follow-up 4 — Same word can be returned multiple times?"
    Don't `del child.word` after the first match.

??? question "Follow-up 5 — How would you make this work on a streaming board (cells revealed over time)?"
    Maintain only the active DFS frontiers; advance whenever a new neighbor is revealed.

##### 🐛 Common Bugs

1. **Forgetting to mark cells visited** — same cell used twice in one path.
2. **Forgetting to restore the cell after recursion** — lasting damage from one starting cell.
3. **Using the assembled path string** at terminal to record the word — slow; better to store the word at the terminal node.
4. **Not deduping** — the same word can be matched from different starting cells.
5. **Not pruning the Trie** — wastes time on dead branches.

##### ✅ Edge Cases Checklist

- [ ] Empty board → `[]`
- [ ] Empty words → `[]`
- [ ] Single-letter words → match if letter on board
- [ ] Word longer than board cell count → can't match
- [ ] Word with repeated letters → cells can't be reused; carefully track visited
- [ ] Same word given twice in input → return once
- [ ] Board with all the same letter → many false matches at first; Trie prunes quickly
- [ ] 12 × 12 board with 10⁵ words → Trie pruning critical

##### 🏢 Sample Interviewer Quote

> *"Find every word from this list that can be formed on the board."*

Your opener: *"Build a Trie of the words. DFS each board cell once, walking the Trie alongside. Prune missing branches; record matches by storing the word at the terminal node. Mark visited via in-place sentinel; restore on backtrack. O(m·n·4^L)."*



#### Problem 38 — Implement an LRU Cache

<span class="diff-medium">Medium</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Google</span> <span class="company-tag">Meta</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span> <span class="company-tag">Uber</span>

> Design a data structure that supports `get(key)` and `put(key, value)` in **O(1)** average time. The cache has a fixed capacity; on `put` when full, evict the **least recently used** entry.

##### 📖 Story Mode

Not technically a tree — but the doubly-linked list inside an LRU is "a tree of degree 1 with parent pointers," and the structural intuition transfers cleanly.

The key insight: **hash map + doubly linked list**. The hash map gives O(1) lookup; the linked list maintains MRU-to-LRU order. On `get`, move the node to the head (MRU). On `put`, insert at head; if over capacity, evict from the tail (LRU).

##### 🌍 Real-World Usage

- **OS page cache** — keep recently-accessed pages in RAM.
- **CPU caches** with LRU replacement (or pseudo-LRU for hardware efficiency).
- **CDN caching** — recently-served content stays near edge.
- **Database query result caching** — Redis, Memcached.
- **HTTP request caching** in browsers.
- **Memoization in recommender systems** — recently-queried users.

##### 🧠 Thinking Process

We need two things:

1. **O(1) lookup by key** — hash map keyed by the original key, valued at the linked-list node.
2. **O(1) reorder + eviction** — doubly linked list so we can remove a node in the middle (given the node) in O(1) and maintain head/tail pointers.

Use sentinel **head** and **tail** dummy nodes to avoid edge cases on insertion/removal. Each real node holds `(key, value)` (we need the key on eviction to remove from the map).

> **Why not Python's OrderedDict?** It's actually built on the same scheme. Production code can use `OrderedDict` directly via `move_to_end` and `popitem(last=False)`; interview problems usually want the hand-built version.

##### 🐍 5 Layers of Solution

=== "Layer 1 — OrderedDict (cheating, but elegant)"

    ```python
    from collections import OrderedDict


    class LRUCache:
        def __init__(self, capacity: int) -> None:
            self.cap = capacity
            self.cache: OrderedDict[int, int] = OrderedDict()

        def get(self, key: int) -> int:
            if key not in self.cache:
                return -1
            self.cache.move_to_end(key)
            return self.cache[key]

        def put(self, key: int, value: int) -> None:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.cap:
                self.cache.popitem(last=False)
    ```

    O(1) per op. Production-ready as-is.

=== "Layer 2 — Hand-built doubly linked list + dict"

    ```python
    class _DNode:
        __slots__ = ("key", "val", "prev", "next")
        def __init__(self, key: int = 0, val: int = 0) -> None:
            self.key = key
            self.val = val
            self.prev: _DNode | None = None
            self.next: _DNode | None = None


    class LRUCache:
        def __init__(self, capacity: int) -> None:
            self.cap = capacity
            self.map: dict[int, _DNode] = {}
            self.head = _DNode()        # dummy head (MRU side)
            self.tail = _DNode()        # dummy tail (LRU side)
            self.head.next = self.tail
            self.tail.prev = self.head

        def _remove(self, node: _DNode) -> None:
            node.prev.next = node.next
            node.next.prev = node.prev

        def _insert_front(self, node: _DNode) -> None:
            node.next = self.head.next
            node.prev = self.head
            self.head.next.prev = node
            self.head.next = node

        def get(self, key: int) -> int:
            node = self.map.get(key)
            if node is None:
                return -1
            self._remove(node)
            self._insert_front(node)
            return node.val

        def put(self, key: int, value: int) -> None:
            node = self.map.get(key)
            if node is not None:
                node.val = value
                self._remove(node)
                self._insert_front(node)
                return
            if len(self.map) >= self.cap:
                lru = self.tail.prev
                self._remove(lru)
                del self.map[lru.key]
            new_node = _DNode(key, value)
            self.map[key] = new_node
            self._insert_front(new_node)
    ```

    The interview-quality answer.

=== "Layer 3 — With expiration / TTL"

    Wrap each entry with an absolute expiry time; on `get`, check expiry and lazy-delete if expired. Common in production caches.

=== "Layer 4 — Thread-safe"

    Wrap operations in a lock. For high-throughput, use sharded LRUs (one per hash bucket).

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    class _Node:
        __slots__ = ("key", "val", "prev", "next")

        def __init__(self, key: int = 0, val: int = 0) -> None:
            self.key = key
            self.val = val
            self.prev: _Node | None = None
            self.next: _Node | None = None


    class LRUCache:
        """Least-recently-used cache with O(1) get and put.

        Args:
            capacity: Maximum number of entries.

        Time:  O(1) average per op.
        Space: O(capacity).
        """

        def __init__(self, capacity: int) -> None:
            if capacity <= 0:
                raise ValueError("capacity must be positive")
            self._cap = capacity
            self._map: dict[int, _Node] = {}
            self._head = _Node()
            self._tail = _Node()
            self._head.next = self._tail
            self._tail.prev = self._head

        def get(self, key: int) -> int:
            node = self._map.get(key)
            if node is None:
                return -1
            self._move_to_front(node)
            return node.val

        def put(self, key: int, value: int) -> None:
            existing = self._map.get(key)
            if existing is not None:
                existing.val = value
                self._move_to_front(existing)
                return

            if len(self._map) >= self._cap:
                lru = self._tail.prev
                assert lru is not self._head
                self._unlink(lru)
                del self._map[lru.key]

            node = _Node(key, value)
            self._link_front(node)
            self._map[key] = node

        def _unlink(self, node: _Node) -> None:
            node.prev.next = node.next
            node.next.prev = node.prev

        def _link_front(self, node: _Node) -> None:
            node.next = self._head.next
            node.prev = self._head
            self._head.next.prev = node
            self._head.next = node

        def _move_to_front(self, node: _Node) -> None:
            self._unlink(node)
            self._link_front(node)
    ```

##### 🔍 Dry Run

`LRUCache(2)`. Then: `put(1, 1)`, `put(2, 2)`, `get(1)`, `put(3, 3)`, `get(2)`, `put(4, 4)`, `get(1)`, `get(3)`, `get(4)`.

| op | state (head → ... → tail) | return |
|----|---------------------------|--------|
| put(1,1) | 1 | — |
| put(2,2) | 2, 1 | — |
| get(1) | 1, 2 | 1 |
| put(3,3) | 3, 1 (evicted 2) | — |
| get(2) | 3, 1 | -1 |
| put(4,4) | 4, 3 (evicted 1) | — |
| get(1) | 4, 3 | -1 |
| get(3) | 3, 4 | 3 |
| get(4) | 4, 3 | 4 |

✓.

##### ⏱️ Complexity

- **Time: O(1)** per `get` and `put`.
- **Space: O(capacity)**.

##### 🎯 Pattern Used

**Hash map + doubly linked list** for O(1) ordered membership. The same combo backs `OrderedDict`, `LinkedHashMap` (Java), and most production LRU implementations.

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — How does this differ from LFU (Least Frequently Used)?"
    LFU evicts the least-accessed entry. Implementation: dict + min-frequency tracker + per-frequency doubly linked list. Still O(1) per op but more involved.

??? question "Follow-up 2 — Why use a doubly linked list, not singly?"
    Singly LL needs the predecessor when removing a known node — that's O(n) without back-pointers. Doubly LL gives O(1) removal of any node.

??? question "Follow-up 3 — How does Python's `OrderedDict.move_to_end` achieve O(1)?"
    Same internal structure: a dict pointing to nodes in a doubly linked list of insertion order.

??? question "Follow-up 4 — What if values are large objects?"
    The cache holds references; eviction frees them (assuming no external references). Memory limits → use `cap` based on bytes, not entry count.

??? question "Follow-up 5 — Distributed LRU?"
    Consistent-hash partition keys to nodes; each node runs its own LRU. Eviction is local. Tricky if cache lookups must hit "any node."

##### 🐛 Common Bugs

1. **Forgetting to evict from the dict** when removing the LRU node — silent memory leak.
2. **Not using sentinel head/tail** — boundary conditions explode.
3. **Storing only value in the linked list** — can't recover the key during eviction.
4. **Updating value but not moving to front** on `put` of an existing key.
5. **Using a singly linked list** — O(n) removal of arbitrary nodes.

##### ✅ Edge Cases Checklist

- [ ] capacity = 0 → reject in constructor
- [ ] capacity = 1 → put + put → first eviction
- [ ] get on missing key → return -1
- [ ] put existing key → update value + move to front, no eviction
- [ ] Repeated gets on same key → no-op for the linked list (effectively)
- [ ] Multiple evictions in a sequence → handled
- [ ] Negative keys/values → fine
- [ ] Very large capacity (10⁶) → O(1) per op still

##### 🏢 Sample Interviewer Quote

> *"Implement an LRU cache with O(1) get and put."*

Your opener: *"Hash map keyed by user-key, valued at a doubly-linked-list node. Sentinel head/tail. Get: lookup, move to front, return val. Put: lookup; if exists, update + move; else create + link to front; if over capacity, unlink tail.prev and remove from map."*



#### Problem 39 — Closest Binary Search Tree Value

<span class="diff-easy">Easy</span> <span class="company-tag">Google</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Amazon</span> <span class="company-tag">Bloomberg</span>

> Given the root of a BST and a `target` (real number), return the **value in the BST closest to** `target`.

##### 📖 Story Mode

A BST's defining property is that smaller values are on the left, larger on the right. When searching for a target, we make a binary-search-style walk:

- If `target < node.val`, the closest value (or a closer one) might be in the left subtree.
- If `target > node.val`, look right.

Whether or not we descend, **the current node is a candidate for "closest seen so far."** Track it; update when something closer appears.

The walk terminates at a null. Best running candidate wins. **O(h)**.

##### 🌍 Real-World Usage

- **Approximate-match queries** in indexed databases.
- **Snap-to-nearest-grid** in CAD or graphics.
- **Continuous-value classifiers** — find the nearest training point.
- **Time-series quantization** — bucket a timestamp to the nearest indexed sample.
- **Auction matching** — find the bid closest to a target price.

##### 🧠 Thinking Process

A BST is a balanced search structure for `<=` queries. Its `find_closest` walk is a textbook one-pass:

1. Track `best = root.val`.
2. Walk the tree. At each node, if `|node.val - target| < |best - target|`, update `best`.
3. Descend `node.left` if `target < node.val`, else `node.right`. Stop at null.

> **Why we don't need to descend both sides:** because the BST property means the closest value is either the current node OR somewhere along the descent path. The walk converges to the value just below or above the target; both are guaranteed to be considered as we pass through.

##### 🐍 5 Layers of Solution

=== "Layer 1 — Inorder + linear scan"

    ```python
    def closest_inorder(root: TreeNode | None, target: float) -> int:
        vals: list[int] = []
        def inorder(n: TreeNode | None) -> None:
            if n is None: return
            inorder(n.left); vals.append(n.val); inorder(n.right)
        inorder(root)
        return min(vals, key=lambda v: abs(v - target))
    ```

    O(n) — fine if you don't have the BST property to exploit.

=== "Layer 2 — One-pass walk"

    ```python
    def closest_value(root: TreeNode, target: float) -> int:
        best = root.val
        node: TreeNode | None = root
        while node is not None:
            if abs(node.val - target) < abs(best - target):
                best = node.val
            node = node.left if target < node.val else node.right
        return best
    ```

    **O(h)** — the BST-aware answer.

=== "Layer 3 — Recursive"

    ```python
    def closest_value_rec(root: TreeNode, target: float) -> int:
        def go(n: TreeNode | None, best: int) -> int:
            if n is None: return best
            if abs(n.val - target) < abs(best - target):
                best = n.val
            nxt = n.left if target < n.val else n.right
            return go(nxt, best)
        return go(root, root.val)
    ```

    Same complexity, recursive flavor.

=== "Layer 4 — Closest K values (LC 272)"

    ```python
    from heapq import heappush, heappop


    def closest_k(root: TreeNode | None, target: float, k: int) -> list[int]:
        # Max-heap of size k: store (-distance, val).
        heap: list[tuple[float, int]] = []
        def inorder(n: TreeNode | None) -> None:
            if n is None: return
            inorder(n.left)
            d = abs(n.val - target)
            if len(heap) < k:
                heappush(heap, (-d, n.val))
            elif -heap[0][0] > d:
                heappop(heap); heappush(heap, (-d, n.val))
            inorder(n.right)
        inorder(root)
        return [v for _, v in heap]
    ```

    O(n log k). Generalization beyond Closest 1.

=== "Layer 5 — Production-ready"

    ```python
    from __future__ import annotations


    def closest_value(root: TreeNode, target: float) -> int:
        """Return the BST value closest to `target`.

        If two values are equidistant, returns the one encountered first
        on the descent path (BST search order).

        Args:
            root:   Root of a non-empty BST.
            target: Target value.

        Returns:
            The closest stored integer value.

        Time:  O(h).
        Space: O(1).
        """
        best = root.val
        node: TreeNode | None = root
        while node is not None:
            if abs(node.val - target) < abs(best - target):
                best = node.val
            node = node.left if target < node.val else node.right
        return best
    ```

##### 🔍 Dry Run

```
        4
       / \
      2   5
     / \
    1   3
```

target = 3.714.

| step | node | best | new node |
|------|------|------|----------|
| 0 | 4 | 4 | target < 4 → left = 2 |
| 1 | 2 | best stays 4 (|2-3.714|=1.714 vs |4-3.714|=0.286) | target > 2 → right = 3 |
| 2 | 3 | best = 3? |3-3.714|=0.714 vs 0.286 → no, best stays 4 | target > 3 → right = None |
| 3 | None | done |

Hmm — best ends at 4, but 3 is also a candidate; |4 - 3.714| = 0.286 < |3 - 3.714| = 0.714, so 4 is correct.

Try target = 3.0: descent goes 4 → 2 → 3. Best transitions: 4 → 2 (|2-3|=1<|4-3|=1? equal — no update, best stays 4) → 3 (|3-3|=0 → best=3). Answer 3 ✓.

##### ⏱️ Complexity

- **Time: O(h)** — single root-to-leaf walk.
- **Space: O(1)** for iterative; O(h) stack for recursive.

##### 🎯 Pattern Used

**Iterative BST search with a running "best so far" tracker.** Same structure as "find predecessor / successor" and "BST insert."

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Closest K values?"
    Layer 4 — inorder traversal + max-heap of size k. O(n log k). For balanced BSTs there's a trickier O(k + log n) using stacks of predecessor/successor — interview classic.

??? question "Follow-up 2 — Tree isn't balanced?"
    Worst case O(n) due to skewed depth. Same algorithm correctness; just slower.

??? question "Follow-up 3 — Multiple values equidistant?"
    Tie-break by smallest, largest, or first-encountered — depends on spec. Document it.

??? question "Follow-up 4 — target outside the range of all stored values?"
    Algorithm returns the min or max value; both are extremes of the descent path.

??? question "Follow-up 5 — Make the BST self-update with each query?"
    Splay tree: rotate the closest-found node to the root. Future queries near the same target are O(log n) amortized.

##### 🐛 Common Bugs

1. **Comparing `abs(diff) <=` instead of `<`** — affects tie-breaking.
2. **Initializing `best = float('inf')`** — fine for distance, but the answer must be an actual node value, not the sentinel.
3. **Descending both sides** — wasteful; BST guarantees the closer side covers the answer.
4. **Computing `abs(node.val - target)` repeatedly** — cache it.
5. **Returning early without updating `best`** when target == node.val — should still update.

##### ✅ Edge Cases Checklist

- [ ] Single-node tree → that value
- [ ] target equal to a stored value → return it
- [ ] target < smallest value → return smallest
- [ ] target > largest value → return largest
- [ ] Skewed tree → O(n) walk
- [ ] target between two equidistant values → spec-dependent tie-break
- [ ] target is a float, values are int → fine
- [ ] Large BST → O(h) is fast even for deep trees

##### 🏢 Sample Interviewer Quote

> *"Find the value in this BST closest to a given target."*

Your opener: *"One-pass BST walk: at each node, update `best` if closer; descend left if target < node.val, else right. Stop at None. O(h)."*



#### Problem 40 — Count Smaller Numbers After Self

<span class="diff-hard">Hard</span> <span class="company-tag">Google</span> <span class="company-tag">Amazon</span> <span class="company-tag">Microsoft</span> <span class="company-tag">Bloomberg</span> <span class="company-tag">Apple</span>

> Given an integer array `nums`, return an array `counts` where `counts[i]` is the number of smaller elements **to the right** of `nums[i]`.

##### 📖 Story Mode

The brute-force O(n²) is obvious; the interesting version is O(n log n) — and there are **three** standard approaches:

1. **Merge sort with index tracking.** During each merge, when an element from the right half is placed before remaining elements from the left, every left-element already passed contributes to a count. Track via index arrays.
2. **Binary indexed tree (Fenwick tree)** keyed by value rank. Walk right-to-left; for each element, query "how many already-seen are smaller" then update.
3. **Balanced BST** with subtree-size augmentation (or `SortedList`). Insert each element right-to-left; on insert, the count of inserted nodes less than the new element = inserted-on-left.

We'll show all three. The BIT version is the textbook "tree" answer.

##### 🌍 Real-World Usage

- **Inversions counting** — same algorithmic shape; measures "sortedness" of a sequence.
- **Sales analytics** — for each item, how many later sales were below its price?
- **Time-series anomaly detection** — count "regressions" relative to a measurement.
- **Genome rearrangement studies** — measuring distance from a sorted reference.
- **Sports rankings** — number of "upsets" each team caused.

##### 🧠 Thinking Process

For each `i`, we want `count(nums[j] < nums[i] for j > i)`. Right-to-left iteration makes "j > i" automatic ("already seen").

> **BIT/Fenwick approach:**
>
> 1. Compress values to a small rank range `[1..k]`.
> 2. Walk right-to-left. For each element of rank `r`, query `sum(BIT[1..r-1])` (count of smaller already-seen). Append to result. Then BIT.update(r, +1).
>
> O(n log k).

> **Merge-sort approach:**
>
> 1. Pair each value with its original index: `(val, idx)`.
> 2. Mergesort by value; on each merge, when a right-half element is placed, increment `counts[idx]` by `(left elements still pending)` for each pending left element... actually the cleaner formulation: when placing a left-half element, increment its count by the number of right-half elements already placed.
>
> O(n log n).

##### 🐍 5 Layers of Solution

=== "Layer 1 — Brute force"

    ```python
    def count_smaller_brute(nums: list[int]) -> list[int]:
        n = len(nums)
        out = [0] * n
        for i in range(n):
            for j in range(i + 1, n):
                if nums[j] < nums[i]:
                    out[i] += 1
        return out
    ```

    O(n²). Pedagogical.

=== "Layer 2 — Binary Indexed Tree (Fenwick)"

    ```python
    def count_smaller_bit(nums: list[int]) -> list[int]:
        # Coordinate compression.
        sorted_vals = sorted(set(nums))
        rank = {v: i + 1 for i, v in enumerate(sorted_vals)}   # 1-indexed
        size = len(sorted_vals)

        bit = [0] * (size + 1)
        def update(i: int, x: int = 1) -> None:
            while i <= size:
                bit[i] += x
                i += i & -i
        def query(i: int) -> int:
            s = 0
            while i > 0:
                s += bit[i]
                i -= i & -i
            return s

        n = len(nums)
        out = [0] * n
        for i in range(n - 1, -1, -1):
            r = rank[nums[i]]
            out[i] = query(r - 1)
            update(r)
        return out
    ```

    **O(n log n)** time and **O(n)** space.

=== "Layer 3 — Merge sort with index tracking"

    ```python
    def count_smaller_merge(nums: list[int]) -> list[int]:
        n = len(nums)
        out = [0] * n
        idxs = list(range(n))

        def merge_sort(lo: int, hi: int) -> None:
            if hi - lo <= 1: return
            mid = (lo + hi) // 2
            merge_sort(lo, mid); merge_sort(mid, hi)
            # Merge.
            tmp: list[int] = []
            i, j = lo, mid
            right_count = 0
            while i < mid and j < hi:
                if nums[idxs[j]] < nums[idxs[i]]:
                    tmp.append(idxs[j]); j += 1; right_count += 1
                else:
                    out[idxs[i]] += right_count
                    tmp.append(idxs[i]); i += 1
            while i < mid:
                out[idxs[i]] += right_count
                tmp.append(idxs[i]); i += 1
            while j < hi:
                tmp.append(idxs[j]); j += 1
            idxs[lo:hi] = tmp

        merge_sort(0, n)
        return out
    ```

    **O(n log n)** time and space.

=== "Layer 4 — SortedList (sortedcontainers)"

    ```python
    from sortedcontainers import SortedList


    def count_smaller_sl(nums: list[int]) -> list[int]:
        sl = SortedList()
        out: list[int] = []
        for v in reversed(nums):
            out.append(sl.bisect_left(v))
            sl.add(v)
        return out[::-1]
    ```

    **O(n log n)** amortized. Tersest correct solution if `sortedcontainers` is available.

=== "Layer 5 — Production-ready (BIT)"

    ```python
    from __future__ import annotations


    class _Fenwick:
        __slots__ = ("size", "tree")

        def __init__(self, size: int) -> None:
            self.size = size
            self.tree = [0] * (size + 1)

        def update(self, i: int, delta: int = 1) -> None:
            while i <= self.size:
                self.tree[i] += delta
                i += i & -i

        def prefix(self, i: int) -> int:
            s = 0
            while i > 0:
                s += self.tree[i]
                i -= i & -i
            return s


    def count_smaller(nums: list[int]) -> list[int]:
        """For each index, count smaller numbers to its right.

        Time:  O(n log n).
        Space: O(n).
        """
        if not nums:
            return []

        unique_sorted = sorted(set(nums))
        rank = {v: i + 1 for i, v in enumerate(unique_sorted)}
        bit = _Fenwick(len(unique_sorted))

        result = [0] * len(nums)
        for i in range(len(nums) - 1, -1, -1):
            r = rank[nums[i]]
            result[i] = bit.prefix(r - 1)
            bit.update(r)
        return result
    ```

##### 🔍 Dry Run

`nums = [5, 2, 6, 1]`. Compressed ranks: `{1:1, 2:2, 5:3, 6:4}`.

Walk right-to-left:

| i | nums[i] | rank | prefix(rank-1) | result[i] | BIT after update |
|---|---------|------|----------------|-----------|------------------|
| 3 | 1 | 1 | 0 | 0 | {1:1} |
| 2 | 6 | 4 | 1 (rank 1 already seen) | 1 | {1:1, 4:1} |
| 1 | 2 | 2 | 1 (rank 1) | 1 | {1:1, 2:1, 4:1} |
| 0 | 5 | 3 | 2 (ranks 1, 2) | 2 | {1:1, 2:1, 3:1, 4:1} |

Result: `[2, 1, 1, 0]` ✓.

##### ⏱️ Complexity

- **Time: O(n log n)**.
- **Space: O(n)** for the BIT/SortedList/index arrays.

##### 🎯 Pattern Used

**Coordinate compression + Fenwick tree** for "count of values in a range" queries on a stream. The same pattern appears in **inversion counting**, **range-sum queries**, and **2D-rectangle counts** (with 2D BIT).

##### 🔄 Interviewer Follow-ups

??? question "Follow-up 1 — Why not segment tree?"
    Equivalent O(n log n). BIT is shorter and faster constants for this prefix-only query.

??? question "Follow-up 2 — What if values are floats?"
    Coordinate compression still works — sort uniques, map to ranks.

??? question "Follow-up 3 — Inversions instead of counts?"
    Sum the result array → total inversions of the original sequence.

??? question "Follow-up 4 — Online / streaming version (values arrive over time)?"
    BIT works as long as you know value range up front. If values are unbounded reals, use a balanced BST (e.g. `SortedList`).

??? question "Follow-up 5 — Memory-bounded?"
    BIT uses O(distinct values) memory. For 10⁹ distinct values, switch to a balanced BST or compressed sketch (e.g. count-min for approximate).

##### 🐛 Common Bugs

1. **Forgetting coordinate compression** — BIT size = max value, can be huge.
2. **Off-by-one in `prefix(rank - 1)`** — must be strict less-than count.
3. **Walking left-to-right** instead of right-to-left → counts elements to the left.
4. **Mergesort version: incrementing the wrong index** — must be the original index, not the merged-array index.
5. **Coordinate compression forgetting `set()`** — duplicates give incorrect rank assignments.

##### ✅ Edge Cases Checklist

- [ ] Empty array → []
- [ ] Single element → [0]
- [ ] Already sorted descending → [n-1, n-2, …, 0]
- [ ] Already sorted ascending → all zeros
- [ ] All duplicates → all zeros (no strictly smaller)
- [ ] Negative values → coordinate compression handles
- [ ] Very large value range with few distinct values → compression saves memory
- [ ] 10⁵ elements → O(n log n) is fast

##### 🏢 Sample Interviewer Quote

> *"For each index, count the number of smaller elements to its right."*

Your opener: *"Coordinate-compress values to small ranks. Walk right-to-left with a Fenwick tree of presence counts: at each step, query prefix(rank-1) = count of smaller seen, then update(rank). O(n log n)."*



---

## How interviewers ask this

A few specific phrasings to listen for:

| Phrasing | What they want to see |
|---|---|
| "Walk me through how you'd traverse this tree." | Pre/in/post + when each is appropriate. |
| "Do it without recursion." | Explicit stack version. |
| "Now do it in O(1) extra space." | Morris traversal — but only on inorder/preorder. |
| "What's the time complexity? In the worst case?" | "O(n) for traversal, O(h) recursion depth, h ranges from log n to n." |
| "Is the tree balanced? Does it matter for your solution?" | Acknowledge the gap between best and worst case. |
| "What if the tree has 10⁷ nodes?" | Recursion depth — switch to iterative or raise the limit. |
| "What if values can be duplicates?" | Make `<` / `<=` choices explicit. |
| "Now do this on an n-ary tree." | Generalize children list. |
| "What if I only have parent pointers?" | The "two-pointer ancestor walk" pattern. |

The "use a hash map" tell for hash-table problems has a tree analogue: the **"draw it on the whiteboard"** tell. If the interviewer asks you to draw the tree before coding, they want to see you reason about edges, traversal order, and base cases visually before writing a single line of Python. Take the offer.

The two recursive patterns (preorder = pass info down, postorder = collect info up) are what they're checking. If you announce *which* one applies before coding, you've already passed half the bar.

---

## Self-check quiz

Try to answer all 20 without scrolling back. If you get 18 right, you've earned the next chapter.

1. Define the height and depth of a node. Are they the same for the root? For a leaf?
2. Why is **inorder** special on a BST?
3. What is the recurrence for the height of a binary tree (in edges)? In nodes?
4. Why is iterative inorder hard but iterative preorder easy?
5. How does the postorder iterative trick using "reversed preorder" work?
6. What's the difference between a complete, balanced, and perfect binary tree?
7. What is the worst-case height of a BST built from a sorted insert sequence?
8. Why does Python's standard library not include a self-balancing BST? What do you use instead?
9. State the BST validation invariant correctly (avoid the §8.4 trap).
10. Why is `len(q)` snapshotted before the inner loop in BFS over levels?
11. In the "max path sum" problem, why do we `max(0, gain(child))`?
12. What does a postorder helper return when it needs to track a global maximum?
13. How does the "in-order successor" delete work in a BST?
14. Time complexity of `bisect.insort`? `sortedcontainers.SortedList.add`?
15. What's the trick for counting nodes of a complete binary tree in O(log² n)?
16. State the LCA postorder algorithm in one sentence.
17. What's the LCA shortcut on a BST?
18. Morris traversal — why is it O(1) extra space?
19. How do you serialize a tree with null markers, and why does it work?
20. When does BFS use less memory than DFS? When does DFS use less?

??? success "Answer hints"
    1. Height = edges to deepest leaf. Depth = edges from root. Same for root only when measured the same way; for a leaf, depth varies, height = 0.
    2. Inorder visits left then node then right; on a BST that order is monotonically increasing.
    3. Edges: `1 + max(h(L), h(R))`; base `h(None) = -1`. Nodes: `1 + max(h(L), h(R))`; base `h(None) = 0`.
    4. Preorder visits the node *before* descending — straightforward `pop, visit, push children`. Inorder must descend left fully *first*, then visit, then go right — needs a two-loop walk.
    5. A preorder that visits node-right-left, when reversed, gives left-right-node = postorder.
    6. Complete: filled level-by-level left-to-right. Balanced: subtree heights differ by ≤ 1. Perfect: all internal nodes have 2 children and all leaves at the same depth.
    7. O(n) — degenerates to a chain.
    8. Adding one would have been a real maintenance burden and most use cases are covered by `dict` (unordered) and `bisect` / `sortedcontainers` (ordered). Use `SortedList`/`SortedDict`.
    9. Pass `(low, high)` bounds down: at every node, `low < node.val < high`, then recurse with updated bounds.
    10. So the inner loop only processes nodes already in the queue from the *previous* level, not the children we're appending now.
    11. To skip a subtree whose best contribution would be negative — using 0 means "don't extend the path that way."
    12. A `nonlocal` (or closure) variable that the helper updates as a side effect, while it returns the local "best path ending here."
    13. Replace the deleted node's value with the smallest value in its right subtree, then delete that smallest value (which has at most one child, so easy).
    14. `bisect.insort`: O(log n) to find, O(n) to shift; `SortedList.add`: O(log n) amortized.
    15. Measure leftmost and rightmost depths; if equal, perfect → use formula; else recurse on both subtrees.
    16. Postorder; return non-null when subtree contains either target; the first node that gets non-null from *both* children is the LCA.
    17. Walk down; the first node whose value is between p and q is the LCA.
    18. It threads the right pointers of in-order predecessors back to their successors, eliminating the need for a stack — and unthreads them as it goes.
    19. Preorder with a `null` sentinel for missing children. Deserialization consumes the tokens in the same order; on `null` it returns None, otherwise constructs a node and recursively deserializes left then right.
    20. BFS uses less when h is large but w is small (skewed). DFS uses less when w is large but h is small (perfect/balanced). Recursive DFS uses O(h) stack; iterative BFS uses O(w) queue.

---

!!! tip "Where to go next"
    - **Binary Search Trees in depth** (forthcoming) — AVL, Red-Black, augmented BSTs.
    - **Tries** (in [Advanced](../../05-advanced/index.md)) — string-keyed trees for prefix queries.
    - **Heaps** — the array-embedded complete tree.
    - **Segment Trees & BITs** — augmented trees for range queries.
    - **Patterns: DFS / BFS** in the [Patterns](../../04-patterns/index.md) section — the cross-cutting versions of the recursion templates you just learned.

You've now mastered the foundation that supports every other tree topic. **The recursion patterns from §9 transfer to graphs, DP, and divide-and-conquer wholesale** — practice them until they feel automatic.
