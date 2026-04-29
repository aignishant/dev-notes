# Trees — common across all companies

> The recursion playground. If you can post-order, you can interview.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Trees show up in **every** loop — phone screen, on-site, system-design follow-ups. The good news: ~80% of tree problems collapse to one of four moves — recurse on `left`/`right`, BFS by level, post-order with a global accumulator, or build-from-traversal. Master those, and the only remaining variable is whether the tree is a BST.

## Pattern frequency

| Pattern | Frequency | Typical signal |
|---|---|---|
| DFS recursion (pre/in/post) | ⭐⭐⭐⭐⭐ | "depth", "diameter", "path sum", "LCA" |
| BFS level-order | ⭐⭐⭐⭐ | "level", "right view", "zig-zag" |
| Post-order with global | ⭐⭐⭐⭐ | "max path", "diameter" — return one thing, update another |
| BST in-order | ⭐⭐⭐ | "kth smallest", "validate BST" |
| Build from traversals | ⭐⭐⭐ | preorder+inorder / inorder+postorder |
| Serialize / deserialize | ⭐⭐ | encode tree to string and back |

## Problem set

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Maximum Depth of Binary Tree | Easy | DFS | 104 |
| 2 | Same Tree | Easy | DFS pair | 100 |
| 3 | Symmetric Tree | Easy | DFS mirror | 101 |
| 4 | Invert Binary Tree | Easy | DFS swap | 226 |
| 5 | Diameter of Binary Tree | Easy | Post-order + global | 543 |
| 6 | Path Sum | Easy | DFS | 112 |
| 7 | Path Sum II | Medium | DFS + backtrack | 113 |
| 8 | Path Sum III | Medium | Prefix-sum on tree | 437 |
| 9 | Lowest Common Ancestor (BT) | Medium | DFS | 236 |
| 10 | Lowest Common Ancestor (BST) | Easy | BST property | 235 |
| 11 | Validate BST | Medium | In-order / bounds | 98 |
| 12 | Binary Tree Level Order Traversal | Medium | BFS | 102 |
| 13 | Right Side View | Medium | BFS last-of-level | 199 |
| 14 | Serialize and Deserialize Binary Tree | Hard | DFS preorder | 297 |
| 15 | Construct Tree from Preorder + Inorder | Medium | Recursion + map | 105 |
| 16 | Kth Smallest in BST | Medium | In-order | 230 |
| 17 | Binary Tree Maximum Path Sum | Hard | Post-order + global | 124 |
| 18 | Flatten Binary Tree to Linked List | Medium | Reverse post-order | 114 |

---

## Deep-dive 1 — Lowest Common Ancestor of a Binary Tree (LC 236)

??? question "Why this is *the* tree-recursion question"
    Asked by Google, Meta, Amazon, Bloomberg. Tests one idea: **trust the recursion**. The answer is six lines if you believe in your function. Most candidates over-think it and write 30.

The contract:

- Find the lowest node that has both `p` and `q` in its subtree.
- Both `p` and `q` are guaranteed to exist.

The recursive insight:

- If `root` is `None` → return `None`.
- If `root` is `p` or `q` → return `root` (it's a candidate; bubble it up).
- Recurse on `left` and `right`.
- If **both** sides return non-null, `root` is the split point — it's the LCA.
- Otherwise return whichever side is non-null (the candidate found below).

```python linenums="1"
from __future__ import annotations


class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def lowestCommonAncestor(
        self,
        root: TreeNode | None,
        p: TreeNode,
        q: TreeNode,
    ) -> TreeNode | None:
        # Base: empty subtree, or we hit one of the targets.
        if root is None or root is p or root is q:
            return root

        left = self.lowestCommonAncestor(root.left, p, q)   # (1)
        right = self.lowestCommonAncestor(root.right, p, q)

        # Both subtrees returned a non-null target → root is the LCA.
        if left and right:
            return root

        # Only one side has a target → bubble that candidate up.
        return left if left else right
```

1. Each recursive call returns "did you see `p` or `q` in your subtree, and if so, what's the highest such node?"

??? note "Complexity"
    - Time **O(n)** — each node visited once.
    - Space **O(h)** recursion stack, `h = log n` balanced, `n` skewed.

??? tip "BST variant (LC 235)"
    For a BST, exploit ordering:
    ```python linenums="1"
    while root:
        if p.val < root.val and q.val < root.val:
            root = root.left
        elif p.val > root.val and q.val > root.val:
            root = root.right
        else:
            return root  # split point
    ```
    O(h) time, O(1) space.

---

## Deep-dive 2 — Binary Tree Maximum Path Sum (LC 124)

??? question "Why interviewers love this"
    It's the cleanest test of "return one thing, update another." If you can articulate that pattern, you've shown post-order maturity. Asked at Meta, Google, Microsoft, Uber.

The path can start and end at *any* nodes and bend through any node — but a path can use **at most one** child arm of any given node (otherwise it'd revisit the parent).

So at every node, two different numbers matter:

- **`gain(node)`** — the best straight-line sum *starting at `node`* and going down one arm. This is what we **return** to the parent (parent can extend it).
- **`best`** — the best full path's sum seen anywhere. This includes "bend" paths `left + node + right`. We **don't** return it; we update a `nonlocal` running max.

The trick: if a child's gain is negative, **drop it** (use `0` instead) — we'd rather the path skip that arm.

```python linenums="1"
from __future__ import annotations
import math


class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def maxPathSum(self, root: TreeNode | None) -> int:
        best = -math.inf  # can be negative — single-node tree may have a negative root.

        def gain(node: TreeNode | None) -> int:
            nonlocal best
            if node is None:
                return 0

            # Recurse first; clamp negative arms to 0 (skip them).
            left_gain = max(gain(node.left), 0)   # (1)
            right_gain = max(gain(node.right), 0)

            # "Bend" path through this node — uses BOTH arms.
            bend = node.val + left_gain + right_gain
            best = max(best, bend)                # (2)

            # Return the best straight arm — parent can only extend ONE side.
            return node.val + max(left_gain, right_gain)  # (3)

        gain(root)
        return int(best)
```

1. Negative gain ⇒ skip that arm. This is what makes the algorithm work for negative values.
2. Update the global with the bend (both arms used). The bend path can't be returned to the parent.
3. Return only the best single arm — anything else would create a non-simple path for the parent.

??? note "Complexity"
    - Time **O(n)** — one post-order pass.
    - Space **O(h)** recursion.

??? tip "Same shape, different problem"
    Diameter of Binary Tree (LC 543) is the *exact* same template — just track the count of edges instead of a sum:
    ```python linenums="1"
    diameter = 0
    def depth(node):
        nonlocal diameter
        if not node: return 0
        l, r = depth(node.left), depth(node.right)
        diameter = max(diameter, l + r)
        return 1 + max(l, r)
    ```

---

## Common gotchas

!!! warning "Things that bite people"
    - **Single-node negative tree** for max path sum — initialise `best = -inf`, not `0`.
    - **LCA** — don't confuse "ancestor" with "parent." A node is its own ancestor.
    - **Validate BST** — comparing `node.val > node.left.val` is wrong. Use `(low, high)` bounds passed down.
    - **Level order** — use `len(queue)` snapshot at the start of each level; don't loop "while queue" naively.
    - **Build from preorder + inorder** — without a hash map of `inorder` indices, you'll be O(n²).

## 🃏 Cheatsheet

| Move | When | Skeleton |
|---|---|---|
| Plain DFS | depth, same-tree, invert | `def dfs(node): if not node: return …; dfs(left); dfs(right)` |
| Post-order + global | diameter, max path | `nonlocal best; ... best = max(best, l + r)` |
| BFS level | level order, right view | `q = deque([root]); while q: for _ in range(len(q)): …` |
| BST in-order | kth smallest, validate | `inorder` is sorted ⇒ kth is the kth visit |
| Build from traversals | preorder + inorder | hash inorder once; preorder pointer + slice bounds |
| Serialize | encode/decode | preorder DFS with `#` for null; deserialize via iterator |

??? tip "Mental checklist before you code"
    1. Is it a BST? If yes, in-order is sorted — use it.
    2. Does the answer involve a *path* that can bend? Post-order + nonlocal global.
    3. Does the answer depend on *level*? BFS, snapshot `len(queue)`.
    4. Building from traversals? Hash the inorder indices first.
    5. Two-target search (LCA)? Trust the recursion — return the candidate.
