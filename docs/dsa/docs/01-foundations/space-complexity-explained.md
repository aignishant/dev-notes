# Space complexity explained

> What "in-place" means, why interviewers test for it, and how to count memory.

Space complexity asks: **how much extra memory does my algorithm use, as a function of input size?**

Same Big-O notation, same growth zoo (O(1), O(log n), O(n), O(n²)). Different question: not "how long?" but "how much?"

---

## The two kinds of space

When measuring space, we usually distinguish:

- **Input space** — the memory the input itself takes. We **don't** count this. The input is given; we didn't allocate it.
- **Auxiliary space** — extra memory we allocate to solve the problem. **This** is what Big-O measures.

So when we say "space complexity is O(1)," we mean **auxiliary** space, not "no memory at all."

---

## What "O(1) space" really means

O(1) space means a **constant** number of variables, regardless of input size. A few ints, a couple of pointers, a small fixed-size buffer.

```python
# O(1) space — uses only a few local vars
def has_pair_with_sum(arr, target):
    seen = set()                    # ❌ wait, this grows with input!
    for x in arr:
        if target - x in seen:
            return True
        seen.add(x)
    return False
```

Hmm — `seen` can hold up to n items. So this is **O(n) space**, not O(1). The vars `target`, `x`, the `seen` set itself — only `seen` grows.

A true O(1) example:

```python
# O(1) space — just two pointers
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

Two pointers. No extra arrays. Constant extra memory.

---

## "In-place" — the holy grail

"In-place" means the algorithm uses **O(1) extra space**, modifying the input directly instead of allocating a new structure.

### Example 1 — Reverse a list, in-place

```python
def reverse_in_place(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        arr[left], arr[right] = arr[right], arr[left]   # swap
        left += 1
        right -= 1
    return arr
```

vs. **not** in-place:

```python
def reverse_new(arr):
    return arr[::-1]    # creates a NEW list of length n → O(n) space
```

Both produce the right answer. The first uses O(1) space; the second uses O(n).

### Example 2 — Move zeros to end, in-place

```python
def move_zeros(nums):
    write = 0
    for read in range(len(nums)):
        if nums[read] != 0:
            nums[write], nums[read] = nums[read], nums[write]
            write += 1
```

In-place: O(1) extra space. The "write" and "read" pointers are constant.

### Why interviewers love in-place

- Saves memory in production (matters at scale)
- Often forces a deeper understanding of the data structure
- Common follow-up: "Can you do it without extra space?" — they're testing whether you know the in-place version

---

## The recursion / call-stack trap

Recursive functions use stack space — even if you don't allocate any data structures.

```python
def factorial(n):
    if n <= 1: return 1
    return n * factorial(n-1)
```

This looks like it uses no memory. **But every recursive call adds a frame to the call stack.** For input n, the stack has up to n frames at peak.

→ Space complexity: **O(n)**, not O(1).

A common interview trick is converting recursive to iterative, *specifically* to drop space from O(n) to O(1).

```python
def factorial_iter(n):
    result = 1
    for i in range(2, n+1):
        result *= i
    return result
```

Now O(1) space. The interviewer will note it.

---

## Recursion on a tree — what's the space?

Recursive tree traversal uses stack space proportional to the **depth** of the tree.

| Tree shape | Depth | Recursive space |
|---|---|---|
| Balanced (BST) | O(log n) | O(log n) |
| Skewed (linked-list shape) | O(n) | O(n) |

Worst case for a binary tree with n nodes is **O(n)** stack space (skewed). Best case (perfectly balanced) is **O(log n)**. Always state worst case unless you've proven the tree is balanced.

---

## DP — memoization vs tabulation memory

DP problems often have two solutions, both with the same time complexity but different space.

**Memoized (top-down):**
```python
@cache
def climb(n):
    if n <= 1: return 1
    return climb(n-1) + climb(n-2)
```

- Time: O(n)
- Space: O(n) for the cache + O(n) for the recursion stack = **O(n)**

**Tabulated (bottom-up):**
```python
def climb(n):
    if n <= 1: return 1
    dp = [0] * (n+1)
    dp[0] = dp[1] = 1
    for i in range(2, n+1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

- Time: O(n)
- Space: O(n) for `dp`

**Tabulated with rolling variables:**
```python
def climb(n):
    if n <= 1: return 1
    a, b = 1, 1
    for _ in range(n-1):
        a, b = b, a + b
    return b
```

- Time: O(n)
- Space: **O(1)** — only two vars

This O(1) space optimization is a classic interview follow-up: "Can you reduce the space?"

---

## Common space complexities

| Complexity | Example |
|---|---|
| O(1) | Two pointers, in-place reversal, rolling DP |
| O(log n) | Recursive binary search (call stack), balanced BST recursion |
| O(n) | Hash map of n items, tabulated DP, recursion on linear input |
| O(n) (skewed tree) | Tree recursion when tree is unbalanced |
| O(h) where h = tree height | Tree recursion (best stated this way) |
| O(n + m) | Hash map + queue, BFS on graph |
| O(n²) | 2D DP table, adjacency matrix for graph |
| O(2ⁿ) | All subsets stored explicitly |

---

## How to count space — three rules

### Rule 1 — Count auxiliary structures

Sum the sizes of *new* arrays, dicts, sets, queues, stacks you allocate.

```python
def f(arr):
    seen = set()      # up to O(n)
    counts = {}       # up to O(n)
    queue = deque()   # up to O(n)
    # → O(n) total (we drop the constant 3)
```

### Rule 2 — Count recursion depth

Each recursive call adds one frame to the stack.

```python
def dfs(node):
    if not node: return
    dfs(node.left)    # adds a frame
    dfs(node.right)   # but only after .left returns
```

Stack peak = max depth = O(h) for tree of height h.

### Rule 3 — Output doesn't count (unless they ask)

If the problem says "return all subsets," you must produce 2ⁿ subsets — that's output. We say "O(2ⁿ) output, O(n) auxiliary" if asked to be precise.

If the problem says "return the count of subsets meeting condition X," we don't allocate the subsets — output is O(1).

---

## Common interview follow-ups (memorize)

> 🔁 "Can you do it in-place?"
>
> 🔁 "Can you reduce the space to O(1)?"
>
> 🔁 "What if memory is constrained — say, 1 MB total?"
>
> 🔁 "Can you do it without recursion?" (testing if you know iterative + explicit stack)
>
> 🔁 "What if the input is a stream and you can't store it?"

Each of these is a space-optimization question. Knowing the rolling-variable trick, the in-place pattern, and explicit-stack-vs-recursion lets you answer them.

---

## When space matters more than time

In real systems, sometimes a **slightly slower, much smaller** algorithm wins. Examples:

- **Streaming data** — you have 1 TB of logs but 16 GB RAM. You need a streaming algorithm (Bloom filter, count-min sketch, reservoir sampling).
- **Embedded systems** — kilobytes of memory available. O(n) space is impossible for n=10⁶.
- **Cloud cost** — 4× memory = 4× the bill.

Senior interviews probe this. If asked "what if we have 100M users?", say:
- "What's our memory budget?"
- "Can we afford O(n) space, or do we need streaming?"
- "Could we use approximate data structures (Bloom filter, HyperLogLog)?"

---

## Common gotchas

### Gotcha 1 — Slicing creates copies

```python
arr = [1, 2, 3, 4, 5]
sub = arr[1:4]    # NEW list of 3 elements — O(n) space
```

In a recursion that slices, total space can blow up:

```python
def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])      # O(n) slice each level
    right = merge_sort(arr[mid:])
    return merge(left, right)
```

Total auxiliary space: O(n log n) due to slicing. Pass indices instead to drop to O(n).

### Gotcha 2 — `seen` set in DFS

```python
def dfs(node):
    visited = set()      # ❌ resets every call!
    ...
```

Move `visited` outside or pass as argument — otherwise it's wrong, not just inefficient.

### Gotcha 3 — DP table when 1 row would do

If your DP only needs the previous row to compute the current, you don't need the whole table:

```python
# O(rows × cols) space
dp = [[0] * cols for _ in range(rows)]

# O(cols) space — keep only current and previous row
prev = [0] * cols
curr = [0] * cols
for i in range(rows):
    for j in range(cols):
        curr[j] = ...   # uses prev[j-1], prev[j], curr[j-1]
    prev, curr = curr, prev
```

---

## Self-check

For each, what's the **auxiliary** space complexity?

1. Two-pointer palindrome check on a string of length n. → ?
2. Reversing a linked list iteratively. → ?
3. Recursive in-order traversal of a balanced BST with n nodes. → ?
4. Recursive in-order traversal of a skewed BST with n nodes. → ?
5. BFS on a graph with V nodes and E edges. → ?
6. Building an adjacency matrix for a graph with V nodes. → ?
7. Computing nth Fibonacci with rolling vars. → ?
8. Storing all subsets of an n-element set. → ?

(Answers: 1. O(1) 2. O(1) 3. O(log n) 4. O(n) 5. O(V) 6. O(V²) 7. O(1) 8. O(2ⁿ × n) for storage, or O(n) for recursion-only.)

---

## Up next

→ [Big-O cheatsheet](big-o-cheatsheet.md) — one page reference you'll keep open during practice.
