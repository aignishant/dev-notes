# 24 — Advanced DSA: Hard Problems for FAANG
## Google/Meta Level Problems with Step-by-Step Solutions

---

## 24.1 Advanced Graph Problems

### Design Graph — Build from common patterns

```python
# ═══════════════════════════════════════
# Graph Representations — Know all three
# ═══════════════════════════════════════

# 1. Adjacency List (most common in interviews)
from collections import defaultdict
graph = defaultdict(list)
edges = [(0,1), (1,2), (2,0)]
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)    # Undirected

# 2. Adjacency Matrix (dense graphs)
n = 5
matrix = [[0]*n for _ in range(n)]
matrix[0][1] = 1    # Edge from 0 to 1

# 3. Edge List (union-find, Kruskal's)
edges = [(0, 1, 5), (1, 2, 3)]   # (from, to, weight)
```

### Shortest Path Algorithms Comparison

```python
"""
┌────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Algorithm          │ Use Case         │ Time             │ Handles Negative │
├────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ BFS                │ Unweighted       │ O(V + E)         │ N/A              │
│ Dijkstra           │ Non-negative wts │ O((V+E) log V)   │ No               │
│ Bellman-Ford       │ Negative weights │ O(V × E)         │ Yes              │
│ Floyd-Warshall     │ All pairs        │ O(V³)            │ Yes              │
│ A*                 │ Heuristic search │ O(E) best case   │ No               │
└────────────────────┴──────────────────┴──────────────────┴──────────────────┘
"""

# Bellman-Ford — Handles negative weights
def bellman_ford(n, edges, source):
    dist = [float('inf')] * n
    dist[source] = 0
    
    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    
    # Check for negative cycles
    for u, v, w in edges:
        if dist[u] != float('inf') and dist[u] + w < dist[v]:
            return None    # Negative cycle exists!
    return dist

# Floyd-Warshall — All pairs shortest paths O(V³)
def floyd_warshall(n, edges):
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = w
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    return dist

# Minimum Spanning Tree — Kruskal's O(E log E)
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py: return False
        if self.rank[px] < self.rank[py]: px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]: self.rank[px] += 1
        return True

def kruskal(n, edges):
    edges.sort(key=lambda e: e[2])   # Sort by weight
    uf = UnionFind(n)
    mst = []
    total = 0
    for u, v, w in edges:
        if uf.union(u, v):
            mst.append((u, v, w))
            total += w
    return total, mst
```

### Advanced: Detect Cycle in Directed Graph (DFS coloring)

```python
def has_cycle_directed(n, adj):
    """
    WHITE=0: unvisited, GRAY=1: in current path, BLACK=2: fully processed
    Cycle exists if we visit a GRAY node.
    """
    color = [0] * n
    
    def dfs(node):
        color[node] = 1   # GRAY — being processed
        for neighbor in adj[node]:
            if color[neighbor] == 1:   # Back edge → cycle!
                return True
            if color[neighbor] == 0 and dfs(neighbor):
                return True
        color[node] = 2   # BLACK — done
        return False
    
    return any(color[i] == 0 and dfs(i) for i in range(n))
```

---

## 24.2 Advanced Dynamic Programming

### 2D DP Problems

```python
# ═══════════════════════════════════════
# Longest Common Subsequence — O(m×n)
# ═══════════════════════════════════════
def lcs(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]

# ═══════════════════════════════════════
# 0/1 Knapsack — O(n × W)
# ═══════════════════════════════════════
def knapsack(weights, values, W):
    n = len(weights)
    dp = [0] * (W + 1)
    for i in range(n):
        for w in range(W, weights[i] - 1, -1):    # Reverse to avoid reusing item
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[W]

# ═══════════════════════════════════════
# Minimum Path Sum in Grid — O(m×n)
# ═══════════════════════════════════════
def min_path_sum(grid):
    m, n = len(grid), len(grid[0])
    for i in range(m):
        for j in range(n):
            if i == 0 and j == 0:
                continue
            elif i == 0:
                grid[i][j] += grid[i][j-1]
            elif j == 0:
                grid[i][j] += grid[i-1][j]
            else:
                grid[i][j] += min(grid[i-1][j], grid[i][j-1])
    return grid[m-1][n-1]

# ═══════════════════════════════════════
# Interleaving String — O(m×n) [HARD]
# ═══════════════════════════════════════
def is_interleave(s1, s2, s3):
    m, n = len(s1), len(s2)
    if m + n != len(s3):
        return False
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for i in range(m + 1):
        for j in range(n + 1):
            if i > 0 and s1[i-1] == s3[i+j-1]:
                dp[i][j] = dp[i][j] or dp[i-1][j]
            if j > 0 and s2[j-1] == s3[i+j-1]:
                dp[i][j] = dp[i][j] or dp[i][j-1]
    return dp[m][n]
```

### DP on Strings — Pattern

```python
# ═══════════════════════════════════════
# Regular Expression Matching — O(m×n) [HARD — Google classic]
# ═══════════════════════════════════════
def is_match(s, p):
    m, n = len(s), len(p)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    
    # Handle patterns like a*, a*b*, a*b*c* that can match empty string
    for j in range(2, n + 1):
        if p[j-1] == '*':
            dp[0][j] = dp[0][j-2]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j-1] == '.' or p[j-1] == s[i-1]:
                dp[i][j] = dp[i-1][j-1]
            elif p[j-1] == '*':
                dp[i][j] = dp[i][j-2]    # Zero occurrences
                if p[j-2] == '.' or p[j-2] == s[i-1]:
                    dp[i][j] = dp[i][j] or dp[i-1][j]    # One or more
    
    return dp[m][n]

# ═══════════════════════════════════════
# Palindrome Partitioning — Minimum Cuts — O(n²)
# ═══════════════════════════════════════
def min_cut(s):
    n = len(s)
    # is_pal[i][j] = True if s[i:j+1] is palindrome
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            if s[i] == s[j] and (j - i <= 2 or is_pal[i+1][j-1]):
                is_pal[i][j] = True
    
    dp = list(range(n))    # dp[i] = min cuts for s[0:i+1]
    for i in range(1, n):
        if is_pal[0][i]:
            dp[i] = 0
            continue
        for j in range(i):
            if is_pal[j+1][i]:
                dp[i] = min(dp[i], dp[j] + 1)
    return dp[n-1]
```

### DP on Trees

```python
# House Robber III — DP on binary tree — O(n)
def rob_tree(root):
    def dfs(node):
        if not node:
            return (0, 0)   # (rob_this, skip_this)
        left = dfs(node.left)
        right = dfs(node.right)
        
        rob_this = node.val + left[1] + right[1]    # Rob this + skip children
        skip_this = max(left) + max(right)            # Skip this, best of children
        
        return (rob_this, skip_this)
    
    return max(dfs(root))
```

---

## 24.3 Advanced Data Structures

### LRU Cache — HashMap + Doubly Linked List — O(1)

```python
class DLinkedNode:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    """O(1) get and put — implemented from scratch."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = DLinkedNode()   # Dummy head
        self.tail = DLinkedNode()   # Dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def _add_to_front(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
    
    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _move_to_front(self, node):
        self._remove(node)
        self._add_to_front(node)
    
    def get(self, key):
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._move_to_front(node)
        return node.val
    
    def put(self, key, value):
        if key in self.cache:
            node = self.cache[key]
            node.val = value
            self._move_to_front(node)
        else:
            if len(self.cache) >= self.capacity:
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]
            node = DLinkedNode(key, value)
            self.cache[key] = node
            self._add_to_front(node)
```

### Segment Tree — Range queries O(log n)

```python
class SegmentTree:
    """Range Sum Query with point updates — O(log n) per operation."""
    def __init__(self, nums):
        self.n = len(nums)
        self.tree = [0] * (4 * self.n)
        self._build(nums, 0, 0, self.n - 1)
    
    def _build(self, nums, node, start, end):
        if start == end:
            self.tree[node] = nums[start]
            return
        mid = (start + end) // 2
        self._build(nums, 2*node+1, start, mid)
        self._build(nums, 2*node+2, mid+1, end)
        self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]
    
    def update(self, idx, val, node=0, start=0, end=None):
        if end is None: end = self.n - 1
        if start == end:
            self.tree[node] = val
            return
        mid = (start + end) // 2
        if idx <= mid:
            self.update(idx, val, 2*node+1, start, mid)
        else:
            self.update(idx, val, 2*node+2, mid+1, end)
        self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]
    
    def query(self, l, r, node=0, start=0, end=None):
        if end is None: end = self.n - 1
        if l > end or r < start:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        mid = (start + end) // 2
        return (self.query(l, r, 2*node+1, start, mid) +
                self.query(l, r, 2*node+2, mid+1, end))
```

---

## 24.4 String Algorithms

```python
# KMP — Pattern matching O(n + m)
def kmp_search(text, pattern):
    def build_lps(pattern):
        lps = [0] * len(pattern)
        length = 0
        i = 1
        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            elif length:
                length = lps[length - 1]
            else:
                i += 1
        return lps
    
    lps = build_lps(pattern)
    i = j = 0
    results = []
    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == len(pattern):
            results.append(i - j)
            j = lps[j - 1]
        elif i < len(text) and text[i] != pattern[j]:
            if j:
                j = lps[j - 1]
            else:
                i += 1
    return results

# Rabin-Karp — Rolling hash pattern matching O(n + m) average
def rabin_karp(text, pattern):
    n, m = len(text), len(pattern)
    if m > n:
        return []
    
    BASE, MOD = 31, 10**9 + 7
    
    def hash_str(s):
        h = 0
        for c in s:
            h = (h * BASE + ord(c)) % MOD
        return h
    
    pat_hash = hash_str(pattern)
    txt_hash = hash_str(text[:m])
    power = pow(BASE, m - 1, MOD)
    results = []
    
    for i in range(n - m + 1):
        if txt_hash == pat_hash and text[i:i+m] == pattern:
            results.append(i)
        if i + m < n:
            txt_hash = (txt_hash - ord(text[i]) * power) * BASE + ord(text[i + m])
            txt_hash %= MOD
    return results
```

---

## 24.5 Problem-Solving Framework — How to Approach Unknown Problems

```
Step 1: CLARIFY (2 min)
  "Can the array be empty?"
  "Are values always positive?"
  "Is the input sorted?"
  "What's the size constraint?" (determines acceptable complexity)

Step 2: EXAMPLES (2 min)
  Walk through 2-3 examples including edge cases.
  Draw them out.

Step 3: BRUTE FORCE (1 min)
  Always state the naive solution first.
  "Brute force would be O(n²) using nested loops..."
  This shows you understand the problem.

Step 4: OPTIMIZE (3 min)
  Ask yourself:
  - "Can I sort and use binary search/two pointers?"
  - "Can I use a hash map to trade space for time?"
  - "Is there a sliding window/monotonic stack pattern?"
  - "Does this have optimal substructure → DP?"
  - "Can I reduce the problem size → divide and conquer?"

Step 5: CODE (15 min)
  Write clean, modular code.
  Use descriptive names.
  Handle edge cases at the top.

Step 6: TEST (3 min)
  Walk through your code with examples.
  Check edge cases: empty, single element, duplicates, negative.
  State complexity: "Time O(n log n), Space O(n)"

Common size → complexity mapping:
  n ≤ 10:      O(n!) — backtracking/brute force OK
  n ≤ 20:      O(2ⁿ) — subsets/bitmask DP
  n ≤ 500:     O(n³) — Floyd-Warshall, triple loop
  n ≤ 5000:    O(n²) — 2D DP, nested loops
  n ≤ 10⁶:     O(n log n) — sort-based, binary search
  n ≤ 10⁸:     O(n) — single pass, hash map
  n > 10⁸:     O(log n) or O(1) — math, binary search
```

---
