# Pattern Templates

> Copy-paste-ready code skeletons for every interview pattern. Memorise the *shape*; fill in the body.

<span class="phase-status phase-done">Phase 14 — Resources</span>

---

## Two pointers

### Same direction (sliding window / fast-slow)

```python
def template(arr):
    left = 0
    for right in range(len(arr)):
        # extend window with arr[right]
        while window_invalid():
            # shrink from left
            left += 1
        # update answer with [left, right]
    return answer
```

### Opposite direction

```python
def template(arr):
    left, right = 0, len(arr) - 1
    while left < right:
        if condition(arr[left], arr[right]):
            # process
            left += 1
        else:
            right -= 1
    return answer
```

---

## Sliding window

### Fixed-size window of K

```python
def fixed_window(arr, k):
    window_sum = sum(arr[:k])
    best = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        best = max(best, window_sum)
    return best
```

### Variable-size window (longest with property)

```python
def longest_with_property(arr):
    counts = {}
    left = 0
    best = 0
    for right, x in enumerate(arr):
        counts[x] = counts.get(x, 0) + 1
        while violates(counts):
            counts[arr[left]] -= 1
            if counts[arr[left]] == 0:
                del counts[arr[left]]
            left += 1
        best = max(best, right - left + 1)
    return best
```

---

## Binary search

### Standard (find target)

```python
def search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

### Lower bound (first index where pred is True)

```python
def lower_bound(arr, pred):
    """Find leftmost i where pred(arr[i]) is True."""
    lo, hi = 0, len(arr)        # half-open
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(arr[mid]):
            hi = mid
        else:
            lo = mid + 1
    return lo                    # may equal len(arr) if no such i
```

### Binary search on answer (parametric)

```python
def min_capacity(weights, days):
    def feasible(cap):
        d, cur = 1, 0
        for w in weights:
            if cur + w > cap:
                d += 1; cur = 0
            cur += w
        return d <= days

    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid): hi = mid
        else:             lo = mid + 1
    return lo
```

---

## BFS

### Grid

```python
from collections import deque

def bfs_grid(grid, start):
    m, n = len(grid), len(grid[0])
    q = deque([(*start, 0)])
    seen = {start}
    while q:
        r, c, d = q.popleft()
        if is_target(r, c):
            return d
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < m and 0 <= nc < n and (nr,nc) not in seen and not blocked(grid, nr, nc):
                seen.add((nr, nc))
                q.append((nr, nc, d+1))
    return -1
```

### Multi-source BFS (rotting oranges, walls and gates)

```python
def multi_source(grid):
    q = deque()
    for r, c in starting_cells(grid):
        q.append((r, c, 0))
    seen = set(starting_cells(grid))
    while q:
        r, c, d = q.popleft()
        # ... same as BFS
```

### Level-by-level BFS

```python
def level_bfs(root):
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        # process level
```

---

## DFS

### Recursive (with seen set)

```python
def dfs(node, seen):
    if node in seen:
        return
    seen.add(node)
    process(node)
    for nb in neighbors(node):
        dfs(nb, seen)
```

### Iterative with stack

```python
def dfs_iter(start):
    stack = [start]
    seen = {start}
    while stack:
        node = stack.pop()
        process(node)
        for nb in neighbors(node):
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
```

### Topological sort (Kahn's BFS)

```python
def topo(adj, n):
    indeg = [0] * n
    for u in range(n):
        for v in adj[u]: indeg[v] += 1
    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)
    return order if len(order) == n else []   # cycle detection
```

---

## Backtracking

### General template

```python
def backtrack(state, choices):
    if is_solution(state):
        results.append(snapshot(state))
        return
    for choice in choices(state):
        if not is_valid(state, choice):
            continue
        apply(state, choice)
        backtrack(state, choices)
        undo(state, choice)
```

### Permutations

```python
def permutations(nums):
    res = []
    def bt(path, used):
        if len(path) == len(nums):
            res.append(path[:])
            return
        for i, x in enumerate(nums):
            if used[i]: continue
            used[i] = True; path.append(x)
            bt(path, used)
            used[i] = False; path.pop()
    bt([], [False] * len(nums))
    return res
```

### Combinations

```python
def combinations(nums, k):
    res = []
    def bt(start, path):
        if len(path) == k:
            res.append(path[:]); return
        for i in range(start, len(nums)):
            path.append(nums[i])
            bt(i + 1, path)
            path.pop()
    bt(0, [])
    return res
```

### Subsets

```python
def subsets(nums):
    res = [[]]
    for x in nums:
        res += [s + [x] for s in res]
    return res
```

---

## Dynamic programming

### 1D bottom-up

```python
def fib(n):
    if n < 2: return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b
```

### 2D bottom-up

```python
def edit_distance(s, t):
    m, n = len(s), len(t)
    dp = [[0] * (n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]
```

### Top-down memoised

```python
from functools import cache

def coin_change(coins, amount):
    @cache
    def best(rem):
        if rem < 0: return float("inf")
        if rem == 0: return 0
        return min(best(rem - c) for c in coins) + 1
    ans = best(amount)
    return ans if ans != float("inf") else -1
```

### Knapsack 0/1

```python
def knapsack(weights, values, W):
    n = len(weights)
    dp = [0] * (W + 1)
    for i in range(n):
        for w in range(W, weights[i] - 1, -1):   # reverse to avoid reuse
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[W]
```

---

## Union-Find (DSU)

```python
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path compression
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return False
        if self.rank[ra] < self.rank[rb]: ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]: self.rank[ra] += 1
        return True
```

---

## Trie

```python
class Trie:
    def __init__(self):
        self.children = {}
        self.end = False

    def insert(self, word):
        node = self
        for c in word:
            node = node.children.setdefault(c, Trie())
        node.end = True

    def search(self, word, prefix=False):
        node = self
        for c in word:
            if c not in node.children: return False
            node = node.children[c]
        return prefix or node.end
```

---

## Heap patterns

### K largest

```python
import heapq

def k_largest(arr, k):
    return heapq.nlargest(k, arr)            # O(N log K) for typical K << N
```

### Top-K with streaming

```python
class TopK:
    def __init__(self, k):
        self.k, self.h = k, []
    def add(self, x):
        if len(self.h) < self.k:
            heapq.heappush(self.h, x)
        elif x > self.h[0]:
            heapq.heapreplace(self.h, x)
```

### Median of stream

```python
class MedianFinder:
    def __init__(self):
        self.lo = []           # max-heap (negate)
        self.hi = []           # min-heap

    def add(self, x):
        heapq.heappush(self.lo, -heapq.heappushpop(self.hi, x))
        if len(self.lo) > len(self.hi):
            heapq.heappush(self.hi, -heapq.heappop(self.lo))

    def median(self):
        if len(self.hi) > len(self.lo):
            return self.hi[0]
        return (self.hi[0] - self.lo[0]) / 2
```

---

## Linked list

### Reverse

```python
def reverse(head):
    prev = None
    while head:
        nxt = head.next
        head.next = prev
        prev = head
        head = nxt
    return prev
```

### Floyd's cycle detect

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast: return True
    return False
```

### Find middle

```python
def middle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow
```

---

## Tree

### DFS recursive

```python
def dfs(node):
    if not node: return
    process(node)               # preorder
    dfs(node.left)
    # process(node) for inorder
    dfs(node.right)
    # process(node) for postorder
```

### Iterative inorder

```python
def inorder(root):
    out, stack, node = [], [], root
    while node or stack:
        while node:
            stack.append(node); node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out
```

### LCA in BST

```python
def lca_bst(root, p, q):
    while root:
        if p.val < root.val and q.val < root.val:
            root = root.left
        elif p.val > root.val and q.val > root.val:
            root = root.right
        else:
            return root
```

---

## Sorting tricks

```python
# Sort by multiple keys
arr.sort(key=lambda x: (x.a, -x.b, x.c))

# Group consecutive equals
from itertools import groupby
for key, group in groupby(sorted(arr), key=lambda x: x.field):
    print(key, list(group))

# Custom comparator
from functools import cmp_to_key
arr.sort(key=cmp_to_key(lambda a, b: -1 if my_less(a, b) else 1))
```

---

## Bit tricks

```python
x & (x - 1)         # clear lowest set bit
x & -x              # isolate lowest set bit
bin(x).count("1")   # popcount
x ^ y               # toggle / find difference
1 << k              # 2^k
x | (1 << k)        # set bit k
x & ~(1 << k)       # clear bit k
(x >> k) & 1        # check bit k
~x                  # bitwise not
```
