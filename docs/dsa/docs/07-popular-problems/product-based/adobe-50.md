# Adobe — 50 most-asked questions

> The 50 problems Adobe (Creative Cloud, Document Cloud, Experience Cloud) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Adobe</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Adobe is like

| Round | Length | Focus |
|---|---|---|
| **OA / hackerrank** | 90 min | 2 medium coding problems. |
| **Phone screen** | 45 min | One coding + one OOP design question. |
| **Onsite — coding ×2** | 60 min each | Algorithms + DS, often graphics-flavored. |
| **Onsite — OOP / system design** | 60 min | "Design a layer system for Photoshop." |
| **Onsite — manager / culture** | 45 min | Behavioral. |

**Adobe style**: friendlier than FAANG, *more domain-flavored* (image processing, PDF parsing, vector graphics). Strong OOP-design emphasis. Bias toward seeing your reasoning over speed.

---

## 🎯 What Adobe tests

| Signal | Where | How to show |
|---|---|---|
| Coding correctness | Coding rounds | Working code + tests in 30 min. |
| OOP design | Phone screen, onsite | Class hierarchies, interfaces, SOLID. |
| Domain familiarity | Specific teams | Image filters, PDF formats, color spaces, layers. |
| Communication | Every round | Walk through approach + tradeoffs. |

---

## 🧩 Patterns Adobe loves

| Pattern | Frequency | Why |
|---|---|---|
| **OOP / class design** | ⭐⭐⭐⭐⭐ | Adobe's primary signal. |
| **Trees / recursion** | ⭐⭐⭐⭐ | Layer trees, document object models. |
| **Hash + heap** | ⭐⭐⭐⭐ | Standard medium fluency. |
| **Graph BFS / DFS** | ⭐⭐⭐ | Image flood-fill, layer dependencies. |
| **DP** | ⭐⭐⭐ | Less than Google, but seam-carving comes up. |
| **Sliding window** | ⭐⭐⭐ | String / log problems. |
| **Bit manipulation** | ⭐⭐⭐ | Color packing (RGBA). |

---

## 📋 The 50 questions

Status: ✅ = full v3 &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 4 | Spiral Matrix | <span class="diff-medium">Medium</span> | Layer-by-layer | 🚧 |
| 5 | Set Matrix Zeroes | <span class="diff-medium">Medium</span> | In-place markers | 🚧 |
| 6 | Rotate Image | <span class="diff-medium">Medium</span> | Transpose + reverse | 🚧 |
| 7 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 8 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand-around-center | 🚧 |
| 9 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 10 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |

### Linked lists (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 13 | Linked List Cycle | <span class="diff-easy">Easy</span> | Floyd's | 🚧 |
| 14 | Copy List with Random Pointer | <span class="diff-medium">Medium</span> | Hash / interleave | 🚧 |

### Trees (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 15 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 16 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 17 | LCA (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 18 | Symmetric Tree | <span class="diff-easy">Easy</span> | Recursive mirror | 🚧 |
| 19 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | DFS post-order | 🚧 |
| 20 | Maximum Depth of Binary Tree | <span class="diff-easy">Easy</span> | DFS | 🚧 |
| 21 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |
| 22 | Construct Tree from Preorder + Inorder | <span class="diff-medium">Medium</span> | Recursive partition | 🚧 |

### Graphs (5) — graphics-flavored

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 23 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 24 | Flood Fill | <span class="diff-easy">Easy</span> | Grid DFS / BFS | [📝](#deep-dive-1-flood-fill) |
| 25 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 26 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |
| 27 | Pacific Atlantic Water Flow | <span class="diff-medium">Medium</span> | Multi-source BFS | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 28 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 29 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 30 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |
| 31 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 32 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |

### Stacks (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 34 | Min Stack | <span class="diff-medium">Medium</span> | Two stacks | 🚧 |
| 35 | Largest Rectangle in Histogram | <span class="diff-hard">Hard</span> | Monotonic stack | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 36 | Permutations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 37 | Subsets | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 38 | Word Search | <span class="diff-medium">Medium</span> | Grid DFS + backtrack | 🚧 |

### Heap & Top-K (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 39 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 40 | K Closest Points to Origin | <span class="diff-medium">Medium</span> | Heap / quickselect | 🚧 |
| 41 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |

### Bit / math (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 42 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |
| 43 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |
| 44 | Number of 1 Bits | <span class="diff-easy">Easy</span> | n & (n-1) | 🚧 |

### OOP / design (6) — **Adobe specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 45 | Design a Layer System (Photoshop) | <span class="diff-medium">Medium</span> | OOP + composite | [📝](#deep-dive-3-photoshop-layers) |
| 46 | Image Smoother | <span class="diff-easy">Easy</span> | 2D convolution | [📝](#deep-dive-2-image-smoother) |
| 47 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 48 | Implement Trie | <span class="diff-medium">Medium</span> | Trie | [✅](../../05-advanced/01-tries.md) |
| 49 | Implement strStr | <span class="diff-easy">Easy</span> | KMP / Rabin-Karp | 🚧 |
| 50 | Tic-Tac-Toe Game | <span class="diff-medium">Medium</span> | Row/col counters | 🚧 |

---

## 🔬 Deep-dives — 3 Adobe-style walkthroughs

### Deep-dive 1: Flood Fill

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Adobe</span>

> Given a 2D image, a starting pixel `(sr, sc)`, and a `new_color`, replace the connected region of same-color pixels with `new_color`. Photoshop's paint-bucket tool.

#### 🐍 Optimal solution (DFS)

```python
def flood_fill(image: list[list[int]], sr: int, sc: int, new_color: int) -> list[list[int]]:
    rows, cols = len(image), len(image[0])
    target = image[sr][sc]
    if target == new_color:
        return image                            # no-op short-circuit

    def dfs(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or image[r][c] != target:
            return
        image[r][c] = new_color
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            dfs(r + dr, c + dc)

    dfs(sr, sc)
    return image
```

**Why the no-op check?** Without it, painting "white" over a white pixel triggers infinite recursion (we never mark progress).

#### 🔄 Adobe's classic follow-ups

??? question "How would you handle 32-bit RGBA pixels with anti-aliased edges?"
    Use a **tolerance threshold**: `|pixel - target| ≤ tol`. Real Photoshop uses this.

??? question "What if the image is 50000 × 50000 — DFS blows the stack?"
    Iterative BFS with explicit deque.

??? question "How do you parallelize this?"
    Region-grow per thread; merge at boundaries. Or process tiles independently and merge at tile borders.

---

### Deep-dive 2: Image Smoother

<span class="diff-easy">Easy</span> &nbsp; <span class="company-tag">Adobe</span>

> Given a 2D `image`, return a smoothed image where each pixel = floor average of itself + 8 neighbors (clamped at edges).

#### 🐍 Optimal solution

```python
def image_smoother(img: list[list[int]]) -> list[list[int]]:
    rows, cols = len(img), len(img[0])
    out = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            s, n = 0, 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        s += img[nr][nc]
                        n += 1
            out[r][c] = s // n
    return out
```

#### 🔄 Adobe's classic follow-ups

??? question "Generalize to a K×K kernel with arbitrary weights (Gaussian blur)."
    Same loop with a 2D weight matrix. For separable kernels (Gaussian *is* separable), apply 1D row-pass then 1D col-pass — O(K) per pixel instead of O(K²).

??? question "Make this in-place to save memory."
    Process row-by-row, keep one extra row of the *original* values. O(cols) extra memory.

??? question "What about FFT-based convolution?"
    For very large kernels, O(rows · cols · log(rows · cols)) via FFT beats O(rows · cols · K²). Adobe's actual filters use it.

---

### Deep-dive 3: Photoshop Layers

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Adobe</span>

> Design a layer system: `add_layer(name, content, parent=None)`, `move(name, new_parent)`, `delete(name)`, `render()` (returns flat output applying parent → child order).

#### 🐍 Optimal solution sketch

```python
class Layer:
    def __init__(self, name: str, content: object, parent: "Layer | None" = None):
        self.name = name
        self.content = content
        self.parent = parent
        self.children: list["Layer"] = []

class LayerSystem:
    def __init__(self) -> None:
        self.root = Layer("__root__", None)
        self.index: dict[str, Layer] = {self.root.name: self.root}

    def add_layer(self, name: str, content: object, parent_name: str = "__root__") -> None:
        if name in self.index:
            raise KeyError(name)
        parent = self.index[parent_name]
        layer = Layer(name, content, parent)
        parent.children.append(layer)
        self.index[name] = layer

    def move(self, name: str, new_parent_name: str) -> None:
        layer, new_parent = self.index[name], self.index[new_parent_name]
        layer.parent.children.remove(layer)
        layer.parent = new_parent
        new_parent.children.append(layer)

    def delete(self, name: str) -> None:
        layer = self.index.pop(name)
        layer.parent.children.remove(layer)
        # optionally cascade-delete children, or reparent to root

    def render(self) -> list[object]:
        out: list[object] = []
        def walk(node: Layer) -> None:
            for c in node.children:                # children rendered after parent
                if c.content is not None:
                    out.append(c.content)
                walk(c)
        walk(self.root)
        return out
```

#### 🔄 Adobe's classic follow-ups

??? question "Add blend modes per layer (multiply, screen, overlay)."
    Each layer carries a `blend_mode`. `render()` composites bottom-up, applying the blend function to combine the running buffer with the new layer.

??? question "Make undo/redo work."
    Command pattern: every mutation is a `Command` with `do/undo`. Push to `undo_stack`. Or persistent data structures (path-copying tree) — O(log n) per snapshot.

??? question "How to handle very deep nesting efficiently?"
    Use iterative traversal. Cache rendered subtrees keyed by `(subtree_hash, blend_mode)` for redraw speed.

---

## 🗓️ Day-of tips

!!! tip "Adobe checklist"
    1. **Be ready for OOP-design follow-ups** on every coding problem.
    2. **Know your domain** (graphics / PDF / cloud — depends on team).
    3. **Talk through tradeoffs** — Adobe values reasoning more than speed.
    4. **One easy + one OOP-design** warm-up.

### Red & green flags

- 🚩 Skipping the OOP design extension to a coding problem.
- 🚩 No domain awareness if applying to a graphics team.
- 🟢 Naming a design pattern (composite, strategy, visitor) when it fits.
- 🟢 Asking about real Adobe products you'd be working on.

---

## 🔁 Where to go from here

- [Top 100 by Pattern](../top-100-by-pattern.md), [LLD](../../09-low-level-design/index.md), [System Design](../../08-system-design/index.md).

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md).
