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

#### Problem 3 🟢 — Symmetric Tree

> Determine if a binary tree is a mirror of itself.

**Layer 1 — naive:** mirror the tree, then check `same_tree`.

**Layer 2 — direct recursion:** check left and right recursively, comparing left.left with right.right and left.right with right.left.

```python
def is_symmetric(root: TreeNode | None) -> bool:
    def mirror(a: TreeNode | None, b: TreeNode | None) -> bool:
        if a is None and b is None: return True
        if a is None or b is None:  return False
        return (a.val == b.val
                and mirror(a.left,  b.right)
                and mirror(a.right, b.left))
    return root is None or mirror(root.left, root.right)
```

**Layer 3 — optimal:** O(n), O(h).

**Layer 4:** *iterative?* BFS pairs; on each pop, compare values, push (a.left, b.right) and (a.right, b.left).

**Layer 5:** detecting palindromic structure in any tree-shaped data — used in compiler optimizations and data-structure equality checks.

---

#### Problem 4 🟢 — Invert Binary Tree

> Swap left and right at every node.

**Layer 2 — recursive postorder:**

```python
def invert(root: TreeNode | None) -> TreeNode | None:
    if root is None: return None
    root.left, root.right = invert(root.right), invert(root.left)
    return root
```

**Layer 4 — follow-ups:**

- *Without mutation?* Allocate new nodes; same shape, swapped children.
- *On an n-ary tree?* `node.children.reverse()` plus recursion.

**Layer 5 — Max Howell's tweet:** *"Google: 90 % of our engineers use the software you wrote (Homebrew), but you can't invert a binary tree on a whiteboard so go fuck yourself."* Yes, this problem is famous for that.

---

#### Problem 5 🟢 — Diameter of Binary Tree

> Length of the longest path between any two nodes (measured in edges). The path may or may not pass through the root.

**Layer 1 — brute force:** for every node, compute height of left and right; the diameter through that node is `hL + hR`. Take the max. **O(n²)** because `height` is recomputed.

**Layer 2 — single-pass postorder with closure:**

```python
def diameter(root: TreeNode | None) -> int:
    best = 0
    def height(n: TreeNode | None) -> int:
        nonlocal best
        if n is None: return 0
        L = height(n.left)
        R = height(n.right)
        best = max(best, L + R)        # diameter THROUGH n
        return 1 + max(L, R)           # height of n
    height(root)
    return best
```

**Layer 3 — that's optimal:** O(n), O(h).

**Layer 4 — follow-ups:**

- *Diameter weighted by edge weights?* Same recurrence, but use `L + edge_to_left + R + edge_to_right` for the through-cost.
- *Print the actual path?* Store the deepest node in each subtree as you go.

**Layer 5 — real world:** longest dependency chain in a build graph, longest discussion thread in a forum tree.

---

#### Problem 6 🟢 — Balanced Binary Tree

> Return True if the tree is balanced (every node's two subtrees differ in height by at most 1).

**Layer 1 — naive:** for every node, compute heights of both subtrees, compare. O(n²).

**Layer 2 — single pass returning a tuple:**

```python
def is_balanced(root: TreeNode | None) -> bool:
    def check(n: TreeNode | None) -> tuple[bool, int]:
        if n is None: return True, 0
        ok_l, hL = check(n.left)
        if not ok_l: return False, 0
        ok_r, hR = check(n.right)
        if not ok_r: return False, 0
        return abs(hL - hR) <= 1, 1 + max(hL, hR)
    return check(root)[0]
```

**Layer 3 — sentinel-style alternative:** return `-1` to mean "unbalanced," any non-negative number is the height. Single-value return, same complexity.

**Layer 4 — follow-ups:**

- *Strictly balanced (red-black definition)?* Different recurrence — but the same shape.
- *Compute the imbalance factor?* Track `max(|hL − hR|)` as you go.

**Layer 5 — AVL/Red-Black trees enforce this property continuously to keep operations O(log n).**

---

#### Problem 7 🟢 — Path Sum (root-to-leaf equals target)

> Return True if any root-to-leaf path's values sum to `target`.

**Layer 2 — preorder recursion subtracting as you go:**

```python
def has_path_sum(root: TreeNode | None, target: int) -> bool:
    if root is None: return False
    if root.left is None and root.right is None:   # leaf
        return target == root.val
    rem = target - root.val
    return has_path_sum(root.left, rem) or has_path_sum(root.right, rem)
```

The `if leaf` check is critical: don't return `target == 0` at `None`, because a single-child node would falsely succeed.

**Layer 4:**

- *All paths summing to target?* Backtrack — see Problem 13.
- *Any path (not just root-to-leaf) summing to target?* See Problem 23 (path sum III).

**Layer 5 — used in budget propagation: does any spending path through a tree of departments hit the cap?**

---

#### Problem 8 🟢 — Convert Sorted Array to BST (height-balanced)

> Given a sorted array, build a height-balanced BST.

**Layer 2 — pick the middle as the root, recurse on halves:**

```python
def sorted_array_to_bst(nums: list[int]) -> TreeNode | None:
    if not nums: return None
    mid = len(nums) // 2
    return TreeNode(nums[mid],
                    sorted_array_to_bst(nums[:mid]),
                    sorted_array_to_bst(nums[mid+1:]))
```

**Layer 3 — avoid slicing (O(n) extra):** pass `(lo, hi)` indices.

```python
def sorted_array_to_bst(nums: list[int]) -> TreeNode | None:
    def build(lo: int, hi: int) -> TreeNode | None:
        if lo > hi: return None
        mid = (lo + hi) // 2
        return TreeNode(nums[mid], build(lo, mid - 1), build(mid + 1, hi))
    return build(0, len(nums) - 1)
```

**Layer 4 — sorted *linked list* instead of array?** Use the inorder simulation trick — O(n) without converting to a list.

**Layer 5 — real-world:** building a BBST from a sorted dump (a database "load" operation that wants O(log n) lookups afterwards).

---

#### Problem 9 🟢 — Merge Two Binary Trees

> Overlay two binary trees: where both have nodes, sum them; where only one has, keep it.

**Layer 2 — recursive:**

```python
def merge(a: TreeNode | None, b: TreeNode | None) -> TreeNode | None:
    if a is None: return b
    if b is None: return a
    return TreeNode(a.val + b.val, merge(a.left, b.left), merge(a.right, b.right))
```

**Layer 4 — in-place (mutating `a`)?** Same recurrence but assign back into `a.left`, `a.right`. Halves the allocations.

**Layer 5 — used in monoid-merging operations on trees, e.g. combining two configuration trees with override semantics.**

---

#### Problem 10 🟢 — Minimum Depth of a Binary Tree

> Length of the shortest root-to-leaf path. **Watch the trap:** a node with only one child is *not* a leaf.

**Layer 1 — naive recursion:**

```python
def min_depth_naive(root: TreeNode | None) -> int:
    if root is None: return 0
    return 1 + min(min_depth_naive(root.left), min_depth_naive(root.right))   # ❌ wrong on one-child nodes
```

**Layer 2 — handle the one-child case:**

```python
def min_depth(root: TreeNode | None) -> int:
    if root is None: return 0
    if root.left is None:  return 1 + min_depth(root.right)
    if root.right is None: return 1 + min_depth(root.left)
    return 1 + min(min_depth(root.left), min_depth(root.right))
```

**Layer 3 — BFS is actually faster on average** because the answer is the depth of the *first* leaf seen; you stop early.

**Layer 4 — generalize to weighted edges?** Then it's Dijkstra on a tree, which collapses to a DFS with priority.

**Layer 5 — used in decision trees: depth of the shallowest "leaf decision."**

---

### Medium (11–25) — the bulk of interview questions

#### Problem 11 🟡 — Binary Tree Level Order Traversal

> Return the values level by level, top to bottom, left to right.

**Solution:** the BFS template from §4.4.4.

```python
from collections import deque

def level_order(root: TreeNode | None) -> list[list[int]]:
    if root is None: return []
    out, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            n = q.popleft()
            level.append(n.val)
            if n.left:  q.append(n.left)
            if n.right: q.append(n.right)
        out.append(level)
    return out
```

**Follow-ups:**

- *Bottom-up* (last level first)? Reverse the output.
- *Zigzag?* Track a `left_to_right` boolean; reverse alternate levels (or use a deque per level, append-left on odd levels).
- *Right-side view?* Append the *last* element of each level.

---

#### Problem 12 🟡 — Validate Binary Search Tree

> Determine if a tree is a valid BST.

**Layer 1 — incorrect** (the trap from §8.4): comparing only with immediate children.

**Layer 2 — bounds passed down (the right answer):**

```python
def is_valid_bst(root: TreeNode | None) -> bool:
    def go(n: TreeNode | None, lo: float, hi: float) -> bool:
        if n is None: return True
        if not (lo < n.val < hi): return False
        return go(n.left, lo, n.val) and go(n.right, n.val, hi)
    return go(root, float('-inf'), float('inf'))
```

**Layer 3 — inorder traversal must be strictly increasing:**

```python
def is_valid_bst_inorder(root: TreeNode | None) -> bool:
    prev = float('-inf')
    stack: list[TreeNode] = []
    node = root
    while node is not None or stack:
        while node is not None:
            stack.append(node); node = node.left
        node = stack.pop()
        if node.val <= prev: return False
        prev = node.val
        node = node.right
    return True
```

**Layer 4 — duplicates allowed?** Replace `<` with `<=` (or vice versa) consistently.

**Layer 5 — every B-tree-based database performs essentially this check during integrity audits.**

---

#### Problem 13 🟡 — Path Sum II (return all paths summing to target)

> All root-to-leaf paths whose sum equals `target`.

**Layer 2 — backtracking preorder:**

```python
def path_sum_ii(root: TreeNode | None, target: int) -> list[list[int]]:
    out: list[list[int]] = []
    path: list[int] = []
    def go(n: TreeNode | None, rem: int) -> None:
        if n is None: return
        path.append(n.val)
        if n.left is None and n.right is None and rem == n.val:
            out.append(path.copy())            # snapshot
        else:
            go(n.left,  rem - n.val)
            go(n.right, rem - n.val)
        path.pop()                              # backtrack
    go(root, target)
    return out
```

**The two non-obvious lines:** `path.copy()` (without it, all "paths" share the same mutated list) and `path.pop()` (without it, leftovers leak into sibling subtrees).

---

#### Problem 14 🟡 — Construct Binary Tree from Preorder + Inorder

> Given preorder and inorder traversals of a tree with unique values, reconstruct it.

**Insight:** preorder's first element is the root. Find it in inorder; everything to its left is the left subtree, everything to its right is the right subtree. Recurse.

**Layer 1 — slicing (O(n²) due to repeated `index` and slicing):**

```python
def build_naive(preorder: list[int], inorder: list[int]) -> TreeNode | None:
    if not preorder: return None
    root_val = preorder[0]
    i = inorder.index(root_val)
    return TreeNode(root_val,
                    build_naive(preorder[1:1+i], inorder[:i]),
                    build_naive(preorder[1+i:],  inorder[i+1:]))
```

**Layer 3 — index map + bounds (O(n)):**

```python
def build_tree(preorder: list[int], inorder: list[int]) -> TreeNode | None:
    idx = {v: i for i, v in enumerate(inorder)}
    pre_i = 0
    def go(lo: int, hi: int) -> TreeNode | None:
        nonlocal pre_i
        if lo > hi: return None
        root_val = preorder[pre_i]; pre_i += 1
        m = idx[root_val]
        node = TreeNode(root_val)
        node.left  = go(lo, m - 1)             # build left FIRST so pre_i advances correctly
        node.right = go(m + 1, hi)
        return node
    return go(0, len(inorder) - 1)
```

**Layer 4:**

- *Postorder + Inorder?* Same idea — postorder's last element is the root; consume from the end and build right first.
- *Preorder + Postorder?* Underdetermined (multiple trees match) unless tree is full.

**Layer 5 — this is essentially what JSON/YAML deserializers do for nested objects.**

---

#### Problem 15 🟡 — Binary Tree Right Side View

> List of values visible from the right side, top to bottom.

**Solution — BFS, take last of each level:**

```python
def right_view(root: TreeNode | None) -> list[int]:
    if root is None: return []
    out, q = [], deque([root])
    while q:
        last = None
        for _ in range(len(q)):
            n = q.popleft()
            last = n.val
            if n.left:  q.append(n.left)
            if n.right: q.append(n.right)
        out.append(last)
    return out
```

**Alternative — DFS preferring right:**

```python
def right_view_dfs(root: TreeNode | None) -> list[int]:
    out: list[int] = []
    def go(n: TreeNode | None, depth: int) -> None:
        if n is None: return
        if depth == len(out): out.append(n.val)    # first node we see at this depth (going right-first)
        go(n.right, depth + 1)
        go(n.left,  depth + 1)
    go(root, 0)
    return out
```

**Follow-up:** *Left side view?* Mirror — reverse the recursion order (or use the BFS version with first-of-level).

---

#### Problem 16 🟡 — Lowest Common Ancestor (binary tree)

> Given two nodes p and q in a binary tree, return their LCA — the deepest node that has both as descendants.

**Layer 2 — postorder, return non-null when subtree contains a target:**

```python
def lca(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
    if root is None or root is p or root is q:
        return root
    L = lca(root.left,  p, q)
    R = lca(root.right, p, q)
    if L and R: return root      # split here → root is the LCA
    return L if L else R
```

**Layer 3 — already O(n).**

**Layer 4 — BST?** Walk down once: the first node whose value is between `p.val` and `q.val` is the LCA. O(h).

**Layer 5 — version control: in git, `merge-base` is exactly this on the commit DAG.**

---

#### Problem 17 🟡 — LCA on a BST

```python
def lca_bst(root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode:
    lo, hi = min(p.val, q.val), max(p.val, q.val)
    node = root
    while node is not None:
        if node.val < lo:    node = node.right
        elif node.val > hi:  node = node.left
        else:                return node
    return None  # unreachable if p and q are guaranteed in the tree
```

O(h), O(1) extra. The cleanest LCA in any tree variant.

---

#### Problem 18 🟡 — Kth Smallest in BST

> Find the k-th smallest element.

**Layer 2 — inorder traversal, stop at the k-th yield:**

```python
def kth_smallest(root: TreeNode | None, k: int) -> int:
    stack: list[TreeNode] = []
    node = root
    while node is not None or stack:
        while node is not None:
            stack.append(node); node = node.left
        node = stack.pop()
        k -= 1
        if k == 0: return node.val
        node = node.right
    raise ValueError("k out of range")
```

**Layer 4 — frequent insertions/deletions?** Augment each node with a `size` count of its subtree; then kth-smallest is O(h). This is the standard trick for "order statistic trees."

---

#### Problem 19 🟡 — Serialize and Deserialize a Binary Tree

> Encode the tree as a string and decode it back.

**Layer 2 — preorder with `null` sentinels:**

```python
def serialize(root: TreeNode | None) -> str:
    out: list[str] = []
    def go(n: TreeNode | None) -> None:
        if n is None: out.append("#"); return
        out.append(str(n.val))
        go(n.left); go(n.right)
    go(root)
    return ",".join(out)


def deserialize(s: str) -> TreeNode | None:
    it = iter(s.split(","))
    def go() -> TreeNode | None:
        v = next(it)
        if v == "#": return None
        n = TreeNode(int(v))
        n.left  = go()
        n.right = go()
        return n
    return go()
```

**Follow-up — level-order serialization (LeetCode's display format):** uses a BFS encoding with `null` sentinels; trickier to deserialize but the round-trip preserves structure equally.

---

#### Problem 20 🟡 — Flatten Binary Tree to Linked List (in place)

> Rearrange the tree into a right-only "linked list" matching preorder.

**Layer 2 — recursive, returning the tail:**

```python
def flatten(root: TreeNode | None) -> None:
    def go(n: TreeNode | None) -> TreeNode | None:
        # Returns the tail of the flattened list rooted at n.
        if n is None: return None
        l_tail = go(n.left)
        r_tail = go(n.right)
        if n.left is not None:
            # splice left chain between n and what was n.right
            (l_tail or n.left).right = n.right
            n.right = n.left
            n.left = None
        return r_tail or l_tail or n
    go(root)
```

**Layer 3 — Morris-style iterative O(1) extra:**

```python
def flatten_iter(root: TreeNode | None) -> None:
    cur = root
    while cur is not None:
        if cur.left is not None:
            # find rightmost in left subtree
            pred = cur.left
            while pred.right is not None:
                pred = pred.right
            pred.right = cur.right
            cur.right = cur.left
            cur.left = None
        cur = cur.right
```

---

#### Problem 21 🟡 — Convert Sorted List to BST

> Same as Problem 8 but the input is a singly linked list (no random access).

**Layer 2 — convert to array, then Problem 8:** O(n) time, O(n) extra.

**Layer 3 — inorder simulation:** walk the list "as if" doing inorder traversal of the BST you're about to build. O(n) time, O(log n) extra.

```python
def sorted_list_to_bst(head):
    # First pass: count
    n, p = 0, head
    while p is not None: n += 1; p = p.next
    cur = [head]   # mutable wrapper
    def build(size: int) -> TreeNode | None:
        if size <= 0: return None
        left = build(size // 2)
        node = TreeNode(cur[0].val)
        cur[0] = cur[0].next
        node.left = left
        node.right = build(size - size // 2 - 1)
        return node
    return build(n)
```

This is one of the prettiest tree algorithms; understanding why it works is genuinely educational.

---

#### Problem 22 🟡 — Binary Tree Maximum Path Sum

> Find the path with the largest sum of node values. The path can start and end at any nodes; it must be connected.

**Solution — postorder, two values per recursion (the §8.11 pattern):**

```python
def max_path_sum(root: TreeNode) -> int:
    best = float('-inf')
    def gain(n: TreeNode | None) -> int:
        nonlocal best
        if n is None: return 0
        L = max(0, gain(n.left))
        R = max(0, gain(n.right))
        best = max(best, n.val + L + R)        # path THROUGH n
        return n.val + max(L, R)               # path ENDING AT n
    gain(root)
    return best
```

The `max(0, …)` is what allows skipping a subtree whose contribution would be negative.

---

#### Problem 23 🟡 — Path Sum III (any path summing to target)

> Count paths whose values sum to `target`. Path must go top-down (parent → child) but need not start at root or end at leaf.

**Layer 1 — for every node, run "subtree path sum" rooted there:** O(n²).

**Layer 3 — prefix-sum + hash map (the Two Sum trick, on a tree):** keep a running prefix sum from root to current node; the answer at each node is the count of earlier prefix sums equal to `current - target`.

```python
def path_sum_iii(root: TreeNode | None, target: int) -> int:
    count = 0
    seen: dict[int, int] = {0: 1}
    def go(n: TreeNode | None, run_sum: int) -> None:
        nonlocal count
        if n is None: return
        run_sum += n.val
        count += seen.get(run_sum - target, 0)
        seen[run_sum] = seen.get(run_sum, 0) + 1
        go(n.left, run_sum); go(n.right, run_sum)
        seen[run_sum] -= 1                    # backtrack — sibling branches don't share this prefix
    go(root, 0)
    return count
```

The single bug interviewers watch for: forgetting to *decrement* on the way back up.

---

#### Problem 24 🟡 — Populating Next Right Pointers (perfect binary tree)

> Each node has an extra `next` pointer; connect it to the node immediately to its right on the same level (or `None` for rightmost).

**Layer 2 — BFS:** O(n) time, O(w) space.

**Layer 3 — O(1) extra space using established `next` pointers from the previous level:**

```python
def connect(root):
    leftmost = root
    while leftmost is not None and leftmost.left is not None:
        head = leftmost
        while head is not None:
            head.left.next = head.right
            if head.next is not None:
                head.right.next = head.next.left
            head = head.next
        leftmost = leftmost.left
```

---

#### Problem 25 🟡 — Count Complete Tree Nodes (in O(log² n))

> Given a complete binary tree, count its nodes — but better than O(n).

**Insight:** measure the leftmost depth `dL` and rightmost depth `dR`. If `dL == dR`, the tree is *perfect*: 2^dL − 1 nodes. Otherwise recurse.

```python
def count_nodes(root):
    if root is None: return 0
    dL, dR = 0, 0
    n = root
    while n is not None: dL += 1; n = n.left
    n = root
    while n is not None: dR += 1; n = n.right
    if dL == dR:
        return (1 << dL) - 1                  # perfect
    return 1 + count_nodes(root.left) + count_nodes(root.right)
```

Each level the recursion goes into exactly one of the two subtrees deeply; the other resolves with the perfect-tree formula. **O(log² n)** total.

---

### Hard (26–35) — the ones that separate signals

#### Problem 26 🔴 — Recover Binary Search Tree

> Two nodes of a BST were swapped by mistake. Recover the tree without changing its structure.

**Insight:** an inorder walk yields a sorted sequence. With two swapped, you see two "violations" — a place where current < previous. Track the first such pair's *higher* element and the second pair's *lower* element; swap them at the end. O(n), O(h) extra.

---

#### Problem 27 🔴 — Binary Tree Cameras

> Place cameras at nodes; each camera covers itself, its parent, and its direct children. Minimum cameras to cover the whole tree.

**Solution — postorder with three states per node** (NEEDS_CAMERA, HAS_CAMERA, COVERED) and a closure counter. A classical tree DP — work it out by hand on small examples first.

---

#### Problem 28 🔴 — All Nodes Distance K from Target

> Given a target node, list all nodes at exactly distance K.

**Solution — convert tree to undirected graph (parent map), then BFS from target K levels.** O(n), O(n).

---

#### Problem 29 🔴 — Vertical Order Traversal

> Group nodes by their "x-coordinate" (root is 0; left child is x−1; right child is x+1). Within an x-column, sort by y, then by value.

**Solution — DFS collecting `(x, y, val)` triples; sort. O(n log n).**

---

#### Problem 30 🔴 — Serialize and Deserialize an N-ary Tree

> Same as Problem 19 but for an n-ary tree.

**Solution — preorder with a "child count" sentinel after each node**, so the deserializer knows when a sibling list ends. O(n).

---

#### Problem 31 🔴 — Find Duplicate Subtrees

> Return one root for every subtree shape (including values) that appears more than once.

**Solution — postorder canonical-string + hash map.** Each subtree's signature is `f"{val},{left_sig},{right_sig}"`. The first time we see a sig: record it. The second time: report the node. **O(n²)** worst case due to string concat; use an interner (sig → integer id) for true O(n).

---

#### Problem 32 🔴 — House Robber III (tree DP)

> A robber can't rob two adjacent houses (parent and child). The houses form a binary tree. Max loot.

**Solution — postorder returning a tuple `(rob_this, skip_this)`:**

```python
def rob(root):
    def go(n):
        if n is None: return (0, 0)
        l_rob, l_skip = go(n.left)
        r_rob, r_skip = go(n.right)
        rob_this  = n.val + l_skip + r_skip
        skip_this = max(l_rob, l_skip) + max(r_rob, r_skip)
        return (rob_this, skip_this)
    return max(go(root))
```

---

#### Problem 33 🔴 — Maximum Width of Binary Tree

> Width of a level = distance between leftmost and rightmost non-null nodes on that level (counting null gaps in between).

**Solution — BFS with positional indexing:** for a node at position `p`, its left child is at `2p`, right at `2p+1`. Per level, `max(positions) - min(positions) + 1`. Reset positions per level to avoid overflow on deep trees.

---

#### Problem 34 🔴 — Smallest Subtree with All Deepest Nodes

> Find the smallest subtree containing every deepest leaf.

**Solution — postorder returning `(deepest_depth, lca)` per subtree.** If left and right have equal max depth, current node is the LCA; otherwise propagate the deeper side up.

---

#### Problem 35 🔴 — Verify Preorder Serialization of a Binary Tree

> Given a comma-separated preorder serialization with `#` for null, verify it without building the tree.

**Solution — track "available slots":** start with 1 slot. Each `#` consumes 1 slot. Each non-null consumes 1 and produces 2 (its two children). Slots must never go negative; must be exactly 0 at the end. O(n).

---

### Bonus (36–40) — design and edge-case rounds

#### Problem 36 🟡 — Design a Trie (Prefix Tree)

Implement `insert(word)`, `search(word)`, `startsWith(prefix)`. Each node has 26 children (or a `dict[str, Node]`). Insert/search/prefix all O(L) where L is the word length.

#### Problem 37 🔴 — Word Search II (Trie + DFS over a board)

Given a board of letters and a list of words, find all words on the board. Build a Trie of the words, DFS the board pruning at each step using the Trie. Cuts the runtime from O(W·N²) to roughly O(N² · L) for L = max word length.

#### Problem 38 🔴 — Implement an LRU Cache (doubly linked list + hash map)

Not technically a tree, but the doubly linked list is "a tree of degree 1 with reversed parent pointers." Useful contrast.

#### Problem 39 🔴 — Closest Binary Search Tree Value

Given a BST and a target real number, return the value closest to it. Walk down once, tracking the running closest. O(h).

#### Problem 40 🔴 — Count Smaller Numbers After Self (BIT or merge sort tree)

Given an array, for each index `i` count how many later elements are smaller. Solvable with a Binary Indexed Tree or by a merge-sort-with-counts. The BIT solution is the standard "tree" answer; it generalises to range queries.

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
