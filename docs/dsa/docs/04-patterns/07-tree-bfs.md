# Tree BFS

> Walk a tree level by level — root first, then all of root's children, then all the grandchildren. The pattern that solves "right side view," "zigzag," "level averages," "minimum depth," "rotting oranges in a grid" — basically every problem where the answer cares about distance-from-root or distance-from-source. One queue, one length-snapshot trick, twenty FAANG problems.

<span class="phase-status phase-done">Phase 5 — Patterns</span>

---

## 📖 What is tree BFS?

Imagine the tree as a stack of horizontal shelves: root on shelf 0, root's children on shelf 1, grandchildren on shelf 2, and so on. **BFS = "process all of shelf k before any of shelf k+1."** A queue is the natural data structure: dequeue from the front (oldest = current shelf) and enqueue children at the back (next shelf).

The single most-asked sub-pattern is "give me the answer **per level**" — a list of lists. The trick is to snapshot the queue size at the start of each level so you know exactly how many nodes belong to that level:

```python
size = len(queue)               # how many nodes are on this shelf
for _ in range(size):           # process exactly that many
    node = queue.popleft()
    ...
    queue.append(node.left); queue.append(node.right)
```

That `size = len(queue)` is the difference between an algorithm that knows where one level ends and a confused soup that processes everything at once.

!!! tip "The signal — when to reach for tree BFS"
    Reach for it when:

    - The answer cares about **levels / depth / shortest distance from root**.
    - The problem says **"per level"**, **"left/right side view"**, **"largest in each row"**, **"zigzag"**, **"minimum depth."**
    - You're walking a graph from a source and want **distance** (BFS on graph generalises this).
    - DFS recursion would work but is awkward because you need ordering across siblings, not within a subtree.

    Cousins:

    - **Tree DFS** (page coming next) — pre/in/postorder, path sums, subtree problems.
    - **Topological sort** — BFS variant on DAGs (Kahn's algorithm).
    - **0-1 BFS / Dijkstra** — generalisations to weighted graphs.

---

## 🧩 The three flavors

### Flavor 1: Level-snapshot BFS (the primitive)

```python
from collections import deque

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


def level_order(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []
    result: list[list[int]] = []
    queue: deque[TreeNode] = deque([root])

    while queue:
        size = len(queue)                       # (1) snapshot — *this* level's count
        level: list[int] = []
        for _ in range(size):                   # (2) drain exactly `size` nodes
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)                    # (3) one level done

    return result
```

1. The **snapshot** is the trick. After the for-loop runs, `len(queue)` is the count of the *next* level — no contamination.
2. We process exactly `size` nodes; their children went to the back of the queue but won't be touched in this iteration.
3. Append the level once; never inside the for-loop.

**Examples:** Level Order Traversal (LC 102), Average of Levels (LC 637), Largest Value in Each Row (LC 515).

### Flavor 2: Zigzag / direction-flipping

Same shape as Flavor 1 but every other level is collected right-to-left. The clean idiom: build the level normally, reverse it on odd levels.

```python
def zigzag_level_order(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []
    result: list[list[int]] = []
    queue: deque[TreeNode] = deque([root])
    left_to_right = True

    while queue:
        size = len(queue)
        level: list[int] = [0] * size
        for i in range(size):
            node = queue.popleft()
            # (1) Write into the correct slot directly — no .reverse() pass.
            idx = i if left_to_right else size - 1 - i
            level[idx] = node.val
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
        left_to_right = not left_to_right

    return result
```

The "write to the slot directly" detail saves a `level.reverse()` call per level — pure cosmetic O(n) → O(n) but interview-tier polish.

**Examples:** Binary Tree Zigzag Level Order Traversal (LC 103), Spiral Tree Traversal.

### Flavor 3: BFS with sibling chaining (O(1) space)

For trees where each node already has a `next` pointer (LC 116/117), you can walk level *k* horizontally using the `next` pointers you set up while processing level *k-1*. **No queue needed** — the tree itself is your queue.

```python
class Node:
    def __init__(
        self,
        val: int = 0,
        left: "Node | None" = None,
        right: "Node | None" = None,
        next: "Node | None" = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right
        self.next = next


def connect(root: Node | None) -> Node | None:
    """Populate `next` pointers so each node points to its right sibling."""
    leftmost = root
    while leftmost:
        # Build the *next* level's chain by walking the *current* level horizontally.
        dummy = Node(0)                  # sentinel head of next level
        tail = dummy
        node = leftmost
        while node:
            if node.left:
                tail.next = node.left
                tail = tail.next
            if node.right:
                tail.next = node.right
                tail = tail.next
            node = node.next             # use the chain we built last round
        leftmost = dummy.next            # head of next level
    return root
```

**Examples:** Populating Next Right Pointers I (LC 116), II (LC 117), Tree Boundary Traversal (cousin).

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Level grouping | "Per level" outputs | Level Order (LC 102) | `size = len(queue)` snapshot |
| 2 | Side view | First/last node per level | Right Side View (LC 199) | Take last in for-loop OR push `right` first |
| 3 | Aggregate per level | Sum, avg, max, min | Average of Levels (LC 637) | Reduce inside the for-loop |
| 4 | Direction flip | Zigzag / spiral | LC 103 | Write to slot `i` or `size-1-i` |
| 5 | Shortest distance | Min depth, min steps to target | Minimum Depth (LC 111) | Return `depth` on first leaf / first match |
| 6 | Multi-source BFS | Many start points simultaneously | Rotting Oranges (LC 994) | Initialize queue with **all** sources |
| 7 | Sibling chain | `next` pointers per level | LC 116/117 | Walk the chain you built last level |

---

## 📋 Twenty problems on this pattern

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Binary Tree Level Order Traversal | 102 | <span class="diff-medium">Medium</span> | Level grouping | 📝 |
| 2 | Binary Tree Level Order Traversal II (bottom-up) | 107 | <span class="diff-medium">Medium</span> | Level grouping + reverse | 📝 |
| 3 | Average of Levels | 637 | <span class="diff-easy">Easy</span> | Aggregate per level | 📝 |
| 4 | Largest Value in Each Tree Row | 515 | <span class="diff-medium">Medium</span> | Aggregate per level | 📝 |
| 5 | Binary Tree Right Side View | 199 | <span class="diff-medium">Medium</span> | Side view | 📝 |
| 6 | Binary Tree Left Side View | — | <span class="diff-medium">Medium</span> | Side view | 📝 |
| 7 | Binary Tree Zigzag Level Order | 103 | <span class="diff-medium">Medium</span> | Direction flip | 📝 |
| 8 | Minimum Depth of Binary Tree | 111 | <span class="diff-easy">Easy</span> | Shortest distance | 📝 |
| 9 | Maximum Depth of Binary Tree | 104 | <span class="diff-easy">Easy</span> | Level counting | 📝 |
| 10 | Cousins in Binary Tree | 993 | <span class="diff-easy">Easy</span> | Track parent + level | 📝 |
| 11 | Populating Next Right Pointers (perfect tree) | 116 | <span class="diff-medium">Medium</span> | Sibling chain | 📝 |
| 12 | Populating Next Right Pointers II | 117 | <span class="diff-medium">Medium</span> | Sibling chain (general) | 📝 |
| 13 | Find Bottom Left Tree Value | 513 | <span class="diff-medium">Medium</span> | Last level's first node | 📝 |
| 14 | N-ary Tree Level Order | 429 | <span class="diff-medium">Medium</span> | Level grouping | 📝 |
| 15 | Symmetric Tree (BFS variant) | 101 | <span class="diff-easy">Easy</span> | Pairwise compare per level | 📝 |
| 16 | Rotting Oranges (grid BFS) | 994 | <span class="diff-medium">Medium</span> | Multi-source BFS | 📝 |
| 17 | Walls and Gates | 286 | <span class="diff-medium">Medium</span> | Multi-source BFS | 📝 |
| 18 | Word Ladder | 127 | <span class="diff-hard">Hard</span> | Implicit graph BFS | 📝 |
| 19 | Open the Lock | 752 | <span class="diff-medium">Medium</span> | Implicit graph BFS | 📝 |
| 20 | Shortest Path in Binary Matrix | 1091 | <span class="diff-medium">Medium</span> | 8-direction grid BFS | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Binary Tree Level Order Traversal (LC 102)

> Given the root of a binary tree, return the level-order traversal of its nodes' values (each level as a separate list).

#### Code (re-stated)

```python
def level_order(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []
    result: list[list[int]] = []
    queue: deque[TreeNode] = deque([root])

    while queue:
        size = len(queue)
        level: list[int] = []
        for _ in range(size):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)

    return result
```

#### Dry run on the tree

```
        3
       / \
      9  20
         / \
        15  7
```

| Outer iter | `queue` at start | `size` | Inner iters → `level` | Children pushed | `result` after |
|------------|------------------|--------|------------------------|------------------|----------------|
| 1 | `[3]` | 1 | `[3]` | 9, 20 | `[[3]]` |
| 2 | `[9, 20]` | 2 | `[9, 20]` | 15, 7 (from 20; 9 has none) | `[[3], [9, 20]]` |
| 3 | `[15, 7]` | 2 | `[15, 7]` | (none) | `[[3], [9, 20], [15, 7]]` |
| 4 | `[]` | — | — | — | exit |

Output: `[[3], [9, 20], [15, 7]]` ✓.

#### Why the snapshot trick is necessary

Suppose you skipped the `size` snapshot and just looped while the queue was non-empty. You'd correctly visit every node — but you'd have no way to know when one level ended and the next began. All values would land in one flat list. The snapshot is what *partitions* the BFS sweep into level chunks.

#### Bottom-up variant (LC 107)

Either reverse `result` at the end (cleanest) or `result.insert(0, level)` inside the loop (looks slick but is O(n²) due to list shifting). Reverse at the end.

#### Complexity

- **Time:** O(n) — each node enqueued and dequeued once.
- **Space:** O(w) where `w` is the maximum level width. For a balanced tree, `w ≈ n/2` → O(n) worst case.

---

### Deep-dive 2 — Binary Tree Zigzag Level Order Traversal (LC 103)

> Same as LC 102 but odd-indexed levels (root is level 0) are collected right-to-left.

The interesting design choice: do you **build then reverse**, **use a deque and append left/right**, or **write directly to indexed slots**?

#### Three approaches compared

```python
# Approach A — build, then reverse on odd levels.
# Simple but allocates a fresh list and reverses it.
level.reverse()  # at the end of each odd iteration

# Approach B — collections.deque, appendleft on odd levels.
# Elegant but creates a deque per level.
from collections import deque as dq
level: dq[int] = dq()
if left_to_right:
    level.append(node.val)
else:
    level.appendleft(node.val)
result.append(list(level))   # convert at the end

# Approach C — preallocate + index directly. (Used in our Flavor 2 above.)
level: list[int] = [0] * size
idx = i if left_to_right else size - 1 - i
level[idx] = node.val
```

All three are O(n). Approach C is the candidate that the interviewer "remembers" because it shows you understand that **appending to the back and prepending to the front are equivalent if you compute the slot directly**.

#### Dry run on the same tree, expecting `[[3], [20, 9], [15, 7]]`

| Level | `left_to_right` at start | `size` | Inner writes | `level` final |
|-------|--------------------------|--------|--------------|---------------|
| 0 | True | 1 | `level[0] = 3` | `[3]` |
| 1 | False | 2 | i=0 → idx=1 → `level[1]=9`; i=1 → idx=0 → `level[0]=20` | `[20, 9]` |
| 2 | True | 2 | `level[0]=15; level[1]=7` | `[15, 7]` |

Output: `[[3], [20, 9], [15, 7]]` ✓.

#### Watch-out

Don't flip the **enqueue order** (e.g., push right before left on odd levels). That changes the order children are visited on the *next* level too, breaking the alternation invariant. Direction-flip belongs in the *output*, not the *traversal*.

#### Complexity

- **Time:** O(n).
- **Space:** O(w) for the queue, plus O(n) for the output.

---

### Deep-dive 3 — Populating Next Right Pointers II (LC 117)

> Each node has `left`, `right`, and `next`. Initially `next = None` everywhere. Set `next` to the node's right sibling on the same level (or `None` if it's the rightmost). Tree is **not** guaranteed to be perfect (LC 116 is the perfect version).

The naive solution uses a queue (Flavor 1) — O(n) time, O(w) space. The elegant solution uses Flavor 3 — **O(1) extra space**, exploiting the `next` pointers from the previous level.

#### The O(1)-space algorithm (Flavor 3)

```python
def connect(root: Node | None) -> Node | None:
    leftmost = root
    while leftmost:
        dummy = Node(0)
        tail = dummy
        node = leftmost
        # Walk this level using `next` pointers built last round.
        while node:
            if node.left:
                tail.next = node.left
                tail = tail.next
            if node.right:
                tail.next = node.right
                tail = tail.next
            node = node.next
        # `dummy.next` is the head of the level we just built.
        leftmost = dummy.next
    return root
```

#### Dry run on

```
        1
       / \
      2   3
     / \   \
    4   5   7
```

(LC 117 — node 6 absent because tree is "not perfect.")

**Iteration 1** — `leftmost = 1`. Inner walk visits node 1.
- 1.left = 2: `tail.next = 2`, `tail = 2`.
- 1.right = 3: `tail.next = 3`, `tail = 3`.
- 1.next = None → inner loop ends.
- `leftmost = dummy.next = 2`. Level 1 chain: `2 → 3`.

**Iteration 2** — `leftmost = 2`. Inner walk visits 2, then 3 (via 2.next we just set).
- At node 2: 2.left = 4 → chain `4`. 2.right = 5 → chain `4 → 5`.
- Advance via `2.next = 3`. At node 3: 3.left = None. 3.right = 7 → chain `4 → 5 → 7`.
- 3.next = None → inner loop ends.
- `leftmost = dummy.next = 4`. Level 2 chain: `4 → 5 → 7`.

**Iteration 3** — `leftmost = 4`. Inner walk visits 4, 5, 7. None has children.
- Inner loop runs but never extends the chain.
- `leftmost = dummy.next = None` → outer loop ends.

Final result: every node has its `next` set correctly, with O(1) extra space. ✓

#### Why the dummy?

`dummy` lets us treat "the next level's first node" uniformly. Without it, we'd need `if first_child_of_next_level is None: first_child_of_next_level = …` checks every time we add the first child, which is fiddly. The sentinel collapses that into a single rule: "always append at `tail`."

#### Complexity

- **Time:** O(n) — each node visited a constant number of times.
- **Space:** O(1) — the dummy node and three pointers, regardless of tree size.

---

## 🐛 Common bugs

1. **Calling `len(queue)` *inside* the for-loop.** It changes as you enqueue children. Snapshot it once before the for-loop.
2. **Pushing children before checking they exist.** `queue.append(node.left)` when `node.left is None` enqueues `None` and crashes on `node.val` next iteration. Always guard.
3. **Returning early on first leaf in "minimum depth" without checking `not node.left and not node.right`.** A node with only a right child is *not* a leaf in this problem.
4. **Zigzag: flipping enqueue order, not output order.** Breaks the next level's order. Output flips; traversal doesn't.
5. **LC 116/117 confusion.** LC 116 is perfect tree (every level full, can use `node.next = parent.next.left`). LC 117 is general (must use the dummy/tail idiom).
6. **Multi-source BFS: forgetting to enqueue *all* sources at the start.** "Start from every rotten orange simultaneously" means push all of them before the loop, not one at a time.
7. **Returning `len(result)` for max depth in an empty tree.** If `root is None`, `result` is `[]` and length is 0 ✓ — but if you initialise with `result = [[root.val]]` you'll crash. Guard early.
8. **Using `list` as the queue and `pop(0)` to dequeue.** `pop(0)` is O(n) → algorithm becomes O(n²). Use `collections.deque` and `popleft()`.

---

## 🗣️ Interviewer phrasings to recognize

- "Print the tree level by level." → Flavor 1.
- "Right-side view of a tree." → Flavor 1, take the **last** node of each level.
- "Zigzag / spiral level order." → Flavor 2.
- "Minimum number of moves / minimum depth." → Flavor 1, return depth at first match.
- "All rotten oranges spread simultaneously." → Multi-source BFS (Flavor 1 with many initial nodes).
- "Connect each node to its right sibling **without** extra space." → Flavor 3.
- "Find the leftmost / rightmost node on the deepest level." → Flavor 1; track per-level first/last.

---

## 🧭 Connections to other patterns

- **Tree DFS** (page coming next) — preorder/inorder/postorder problems where order *within* a subtree matters more than across siblings.
- **Topological Sort** — Kahn's algorithm = BFS over a DAG with in-degree tracking.
- **Graph BFS** — same algorithm, except you track a `visited` set because the graph may have cycles.
- **Two Pointers** ([02-two-pointers.md](02-two-pointers.md)) — the sibling-chain trick in Flavor 3 is two-pointer-flavored.
- **K-way Merge** — multi-source BFS resembles a k-way frontier expansion.

---

## ✅ Self-check — 8 questions

??? question "1. Why does the snapshot `size = len(queue)` work?"
    Children pushed during the inner loop go to the *back* of the queue — past the snapshot index. The for-loop only iterates `size` times, so it processes exactly the current level and never spills.

??? question "2. Right-side view in one line of change from level-order — how?"
    After the inner for-loop, append `node.val` of the **last** iteration (i.e., `result.append(level[-1])`). Or push `right` before `left` and take `level[0]`.

??? question "3. Why use `collections.deque` instead of `list`?"
    `list.pop(0)` is O(n) (shifts all elements left). `deque.popleft()` is O(1). With a list, the entire BFS becomes O(n²).

??? question "4. How does multi-source BFS differ from single-source?"
    You enqueue **all** sources before the main loop, each at distance 0. The first time the BFS reaches any other node, that distance is the *minimum* over all sources. Single sweep, optimal.

??? question "5. Can BFS produce a wrong answer for shortest-path on a weighted graph?"
    Yes. BFS minimises the **number of edges**, not the **sum of weights**. For weighted shortest paths, use Dijkstra (or 0-1 BFS for weights ∈ {0, 1}).

??? question "6. Why does the LC 117 O(1) solution work even when the tree is not perfect?"
    Because we walk this level's `next` chain rather than relying on parent geometry. Whatever shape the level has, the chain we built last round threads through every node on it. Missing children are skipped naturally because the inner loop just doesn't append them.

??? question "7. How would you adapt level-order to find the *deepest* leaf?"
    Track the depth as you go (`while queue: depth += 1; ...`). After the outer loop, `depth` is the tree's maximum depth and the *last* `level` array is the deepest level.

??? question "8. What if the tree is given as parent pointers instead of left/right?"
    Build a `dict[node, list[node]]` of children in one pass, then run standard BFS from the root. Total: O(n). Same algorithm, different graph representation.

---

> **Next pattern up:** Tree DFS — preorder/inorder/postorder, recursion patterns, path-sum questions, lowest common ancestor, and the divide-and-conquer template.
