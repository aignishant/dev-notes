# How to think recursively

> The mindset, the templates, the common bugs. After this page, recursion stops feeling like magic.

---

## What recursion actually is

A **recursive function calls itself** to solve a smaller version of the same problem.

Real-world analogy: you're stuck in a queue. You ask the person in front, "How many people are ahead of you?" They ask the next person. Eventually someone at the front says "zero." The answer ripples back: 0 → 1 → 2 → 3 → ... → you.

That's recursion. Each step:
1. Asks a smaller version of the same question.
2. Trusts the smaller version returns the right answer.
3. Combines that answer with its own state.

```python
def count_ahead(person):
    if person.is_first:
        return 0
    return 1 + count_ahead(person.in_front)
```

---

## The two parts of every recursive function

### 1. Base case — when to stop

If you don't have a base case, the function calls itself forever. Stack overflow. Crash.

The base case is the **smallest** version of the problem you can answer **without** further recursion.

| Problem | Base case |
|---|---|
| Factorial | `n == 0` → return 1 |
| Sum of list | empty list → return 0 |
| Tree depth | node is `None` → return 0 |
| Reverse string | length ≤ 1 → return string |
| Fibonacci | n < 2 → return n |

### 2. Recursive case — make the problem smaller

Reduce the problem by **one step** and call yourself with the smaller input.

```python
def factorial(n):
    if n == 0:           # base case
        return 1
    return n * factorial(n - 1)    # recursive case
```

Each call reduces `n` by 1. Eventually we hit `n == 0`. The chain unwinds back up.

---

## The "trust the recursion" mindset

This is the single most important shift for thinking recursively.

**Don't try to trace every recursive call in your head.** You'll lose your mind.

Instead, **assume the recursive call works**. Treat it like a black box that returns the right answer for a smaller input. Then ask: how do I combine that answer with my current state?

### Example — sum of a list

```python
def sum_list(arr):
    if not arr:
        return 0
    return arr[0] + sum_list(arr[1:])
```

Mental model:
- `sum_list([1, 2, 3, 4])` — I don't know the answer.
- But I trust `sum_list([2, 3, 4])` returns 9 (somehow).
- So my answer is `1 + 9 = 10`. Done.

That's it. Don't think deeper. The recursion handles itself.

### Example — reverse a string

```python
def reverse(s):
    if len(s) <= 1:
        return s
    return reverse(s[1:]) + s[0]
```

Mental model:
- `reverse("hello")` — I trust `reverse("ello")` returns `"olle"`.
- I append `s[0]` (= `"h"`) to the end → `"olleh"`. Done.

---

## The three-step recursive recipe

Use this template for every recursive function:

```python
def f(input):
    # 1. Base case
    if <smallest version>:
        return <known answer>

    # 2. Recursive call(s) on smaller input
    smaller_answer = f(<reduced input>)

    # 3. Combine with current state and return
    return <combined>
```

Examples:

| Function | Base | Recursive call | Combine |
|---|---|---|---|
| `factorial(n)` | `n==0 → 1` | `factorial(n-1)` | `n * smaller` |
| `sum_list(arr)` | `[] → 0` | `sum_list(arr[1:])` | `arr[0] + smaller` |
| `reverse(s)` | `len≤1 → s` | `reverse(s[1:])` | `smaller + s[0]` |
| `tree_depth(root)` | `None → 0` | `depth(left), depth(right)` | `1 + max(L, R)` |
| `fib(n)` | `n<2 → n` | `fib(n-1), fib(n-2)` | `a + b` |

---

## The call stack — what's actually happening

When `f` calls itself, Python stacks the calls.

```python
factorial(3)
  → factorial(2)
    → factorial(1)
      → factorial(0)         # base case, returns 1
      ← returns 1
    ← returns 1 * 1 = 1
  ← returns 2 * 1 = 2
← returns 3 * 2 = 6
```

The stack grows on the way down, then unwinds on the way up. Each frame keeps its own local variables.

**Implication:** recursion uses memory. For input n, the stack peaks at n frames. → O(n) extra space.

---

## Drawing the recursion tree

For multi-recursive functions (two or more recursive calls), draw the tree.

```python
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

```
                fib(4)
              /        \
          fib(3)      fib(2)
          /    \      /    \
      fib(2)  fib(1) fib(1) fib(0)
      /    \
   fib(1)  fib(0)
```

The tree has 2ⁿ leaves → O(2ⁿ) time. That's why naive recursive Fibonacci is exponentially slow.

**Memoization** cuts the tree by remembering already-computed answers:

```python
from functools import cache

@cache
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

Each `fib(k)` is now computed once. Total work: O(n).

---

## Common patterns

### Pattern 1 — single recursion, accumulating result

Walk through input, build an answer.

```python
def length(s):
    if not s: return 0
    return 1 + length(s[1:])
```

### Pattern 2 — two recursive calls (divide & conquer)

Tree recursion or split-the-problem-in-half.

```python
def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
```

### Pattern 3 — recursion with helper / accumulator

Sometimes the cleanest recursion needs an extra parameter.

```python
def reverse(arr):
    def helper(i, j):
        if i >= j: return
        arr[i], arr[j] = arr[j], arr[i]
        helper(i+1, j-1)
    helper(0, len(arr)-1)
```

### Pattern 4 — backtracking

Try a choice, recurse, undo if it doesn't pan out.

```python
def permutations(arr):
    result = []
    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        for i, x in enumerate(remaining):
            path.append(x)
            backtrack(path, remaining[:i] + remaining[i+1:])
            path.pop()                          # undo
    backtrack([], arr)
    return result
```

(Backtracking is a whole topic of its own — covered later. For now, just notice the **try → recurse → undo** shape.)

### Pattern 5 — recursion on trees

The natural fit for recursion. Same shape every time:

```python
def f(node):
    if node is None: return <base>
    left = f(node.left)
    right = f(node.right)
    return <combine left, right, node.val>
```

Every tree problem you'll face starts here.

---

## Worked examples

### Tree depth

```python
def max_depth(root):
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

Trust: `max_depth(root.left)` returns the depth of the left subtree. Same for right. My answer = 1 (for myself) + the deeper of the two.

### Count nodes in a tree

```python
def count(root):
    if root is None: return 0
    return 1 + count(root.left) + count(root.right)
```

### Path from root to a target value

```python
def find_path(root, target):
    if root is None:
        return None
    if root.val == target:
        return [root.val]

    left = find_path(root.left, target)
    if left is not None:
        return [root.val] + left

    right = find_path(root.right, target)
    if right is not None:
        return [root.val] + right

    return None
```

### Generate all subsets (backtracking)

```python
def subsets(arr):
    result = []
    def backtrack(i, path):
        if i == len(arr):
            result.append(path[:])
            return
        # exclude arr[i]
        backtrack(i+1, path)
        # include arr[i]
        path.append(arr[i])
        backtrack(i+1, path)
        path.pop()
    backtrack(0, [])
    return result
```

For each element, two choices: include or exclude. → 2ⁿ subsets.

---

## Common bugs

### Bug 1 — missing base case

```python
def f(n):
    return n + f(n-1)        # 💥 RecursionError
```

Always check: "what's the smallest input, and what should I return?"

### Bug 2 — base case unreachable

```python
def f(n):
    if n == 0: return 0
    return 1 + f(n+1)        # n grows! never reaches 0 💥
```

Each recursive call must move **toward** the base case.

### Bug 3 — forgot to return

```python
def sum_list(arr):
    if not arr: return 0
    arr[0] + sum_list(arr[1:])   # ❌ missing `return`
```

The function returns `None`. Easy to miss in long functions.

### Bug 4 — mutating shared state

```python
def subsets(arr, path=[]):       # ❌ shared default!
    ...
```

Mutable default arguments are shared across calls. Use `path=None` and create inside, or pass explicitly.

### Bug 5 — exponential recomputation

Naive Fibonacci recomputes `fib(2)` 5 times for `fib(6)`. Solution: **memoize**.

```python
from functools import cache

@cache
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

### Bug 6 — Python's recursion limit

Default limit is 1000. For deep recursion (linked list of length 10⁴, deep tree):

```python
import sys
sys.setrecursionlimit(10**6)
```

Or convert to iterative + explicit stack.

---

## Recursion vs iteration

Most recursive functions can be rewritten iteratively. Sometimes recursion is cleaner; sometimes iteration is.

| Problem | Better as |
|---|---|
| Tree traversal | Recursion (matches the data shape) |
| Linear iteration over a list | Iteration |
| Backtracking | Recursion (the undo step is natural) |
| DP on subsequences | Either (memoized recursion ↔ tabulation) |
| Linked-list reversal | Iteration (simple, O(1) space) |

Rule of thumb: **if the data is recursive (tree, nested), use recursion. If the data is linear, prefer iteration.**

---

## Converting recursion to iteration

If you hit recursion-depth issues, convert with an explicit stack.

**Recursive:**
```python
def dfs(node):
    if node is None: return
    print(node.val)
    dfs(node.left)
    dfs(node.right)
```

**Iterative with stack:**
```python
def dfs(root):
    if root is None: return
    stack = [root]
    while stack:
        node = stack.pop()
        print(node.val)
        if node.right: stack.append(node.right)
        if node.left:  stack.append(node.left)
```

The stack replaces the call stack. Push children, pop the next node, repeat.

---

## When to use recursion in interviews

✅ **Use recursion when:**
- The data is recursive (trees, nested structures)
- The problem decomposes into smaller versions of itself (DP, divide & conquer)
- You need backtracking (try → undo)
- The iterative version would be much messier

❌ **Avoid recursion when:**
- Linear iteration over a flat structure
- Recursion depth might exceed 1000 without a clear way to bump the limit
- Tail recursion would help — Python doesn't optimize it

---

## Self-check

Without peeking, write recursive functions for:

1. Compute the length of a string.
2. Compute the maximum value in a list.
3. Reverse a list (returning a new list).
4. Check if a string is a palindrome.
5. Compute the n-th Fibonacci number with memoization.
6. Count leaves in a binary tree.
7. Generate all permutations of a list.

If you can do all 7 in 5 minutes each, you've internalized recursion.

---

## Up next

→ [Input/output handling](input-output-handling.md) — read fast, print clean.
