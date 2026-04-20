# 05 — Data Structures & Algorithms (DSA)
## Complete Interview Questions with Python Examples

---

## 5.1 Complexity Analysis

### Q1: Explain Big O notation with Python examples.

**Answer:**

```python
# Time Complexity — how runtime grows with input size

# O(1) — Constant: dict lookup, array index
def get_first(lst):
    return lst[0]          # Always one operation

d = {"key": "value"}
d["key"]                    # Hash table lookup = O(1) average

# O(log n) — Logarithmic: binary search, balanced BST
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
# Halves search space each step: log₂(1,000,000) ≈ 20 steps

# O(n) — Linear: single loop, linear search
def find_max(arr):
    max_val = arr[0]
    for x in arr:           # Visit each element once
        if x > max_val:
            max_val = x
    return max_val

# O(n log n) — Linearithmic: efficient sorting
sorted([3, 1, 4, 1, 5])   # Timsort = O(n log n)

# O(n²) — Quadratic: nested loops
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - 1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]

# O(2ⁿ) — Exponential: naive recursive fibonacci
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)   # Each call branches into 2

# Space Complexity
# O(1): in-place operations, fixed variables
# O(n): creating a copy, hash set, recursion stack of depth n
# O(n²): 2D matrix

# Python built-in complexities:
"""
list:
  - Access by index:  O(1)
  - Append:           O(1) amortized
  - Insert at start:  O(n)
  - Search (in):      O(n)
  - Sort:             O(n log n)

dict:
  - Get/Set/Delete:   O(1) average, O(n) worst
  - Search (in):      O(1) average

set:
  - Add/Remove/Check: O(1) average

collections.deque:
  - Append/Pop both ends: O(1)
  - Access by index:      O(n)

heapq:
  - Push/Pop:         O(log n)
  - Heapify:          O(n)
"""
```

---

## 5.2 Arrays & Strings

### Q2: Two Sum — the classic.

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Find two indices whose values sum to target.
    Time: O(n), Space: O(n)
    """
    seen = {}   # value → index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Example
print(two_sum([2, 7, 11, 15], 9))  # [0, 1] — nums[0]+nums[1] = 2+7 = 9

# Usage: Hash map pattern — trade space for time
# Instead of O(n²) brute force with two loops, use O(n) with hash map
```

### Q3: Sliding Window — Maximum sum subarray of size k.

```python
def max_subarray_sum(arr: list[int], k: int) -> int:
    """
    Find max sum of any contiguous subarray of size k.
    Time: O(n), Space: O(1)
    """
    if len(arr) < k:
        return -1

    # Calculate first window
    window_sum = sum(arr[:k])
    max_sum = window_sum

    # Slide the window: add right, remove left
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)

    return max_sum

print(max_subarray_sum([1, 4, 2, 10, 2, 3, 1, 0, 20], 4))  # 24 (10+2+3+1... wait)
# Actually: subarray [2, 10, 2, 3] = 17 or [3, 1, 0, 20] = 24

# Usage: Sliding window avoids recomputing from scratch each time
# Pattern: Fixed-size window → add right element, remove left element
```

### Q4: Two Pointer — Container with most water.

```python
def max_area(height: list[int]) -> int:
    """
    Find two lines that together with x-axis forms the container with most water.
    Time: O(n), Space: O(1)
    """
    left, right = 0, len(height) - 1
    max_water = 0

    while left < right:
        width = right - left
        h = min(height[left], height[right])
        max_water = max(max_water, width * h)

        # Move the shorter line inward (it limits the area)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1

    return max_water

print(max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]))  # 49

# Usage: Two-pointer pattern works when:
# - Array is sorted (or has a monotonic property)
# - You need to find a pair satisfying a condition
# - Moving one pointer can eliminate candidates
```

### Q5: Valid Anagram.

```python
from collections import Counter

def is_anagram(s: str, t: str) -> bool:
    """
    Check if t is an anagram of s.
    Time: O(n), Space: O(n)
    """
    return Counter(s) == Counter(t)

# Alternative without Counter
def is_anagram_v2(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    for c in t:
        freq[c] = freq.get(c, 0) - 1
        if freq[c] < 0:
            return False
    return True

print(is_anagram("anagram", "nagaram"))  # True
print(is_anagram("rat", "car"))          # False
```

### Q6: Longest Substring Without Repeating Characters.

```python
def length_of_longest_substring(s: str) -> int:
    """
    Sliding window with set.
    Time: O(n), Space: O(min(n, alphabet_size))
    """
    char_index = {}
    max_len = 0
    left = 0

    for right, char in enumerate(s):
        if char in char_index and char_index[char] >= left:
            left = char_index[char] + 1   # Shrink window
        char_index[char] = right
        max_len = max(max_len, right - left + 1)

    return max_len

print(length_of_longest_substring("abcabcbb"))  # 3 ("abc")
print(length_of_longest_substring("pwwkew"))     # 3 ("wke")
```

---

## 5.3 Linked Lists

### Q7: Implement and manipulate linked lists.

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        vals = []
        node = self
        while node:
            vals.append(str(node.val))
            node = node.next
        return " → ".join(vals)

def build_list(values):
    dummy = ListNode(0)
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next

# Reverse a linked list — O(n) time, O(1) space
def reverse_list(head):
    prev = None
    curr = head
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    return prev

lst = build_list([1, 2, 3, 4, 5])
print(lst)                    # 1 → 2 → 3 → 4 → 5
print(reverse_list(lst))     # 5 → 4 → 3 → 2 → 1

# Detect cycle — Floyd's Tortoise and Hare
def has_cycle(head):
    """Time: O(n), Space: O(1)"""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False

# Merge two sorted lists
def merge_sorted(l1, l2):
    """Time: O(n+m), Space: O(1)"""
    dummy = ListNode(0)
    curr = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    curr.next = l1 or l2
    return dummy.next

# Find middle of linked list
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

---

## 5.4 Stacks & Queues

### Q8: Stack and queue problems.

```python
from collections import deque

# ═══════════════════════════════════════
# Valid Parentheses
# ═══════════════════════════════════════
def is_valid_parens(s: str) -> bool:
    """Time: O(n), Space: O(n)"""
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}

    for char in s:
        if char in pairs.values():     # Opening bracket
            stack.append(char)
        elif char in pairs:            # Closing bracket
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()

    return len(stack) == 0

print(is_valid_parens("({[]})"))    # True
print(is_valid_parens("([)]"))      # False

# ═══════════════════════════════════════
# Min Stack — O(1) get minimum
# ═══════════════════════════════════════
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, val):
        self.stack.append(val)
        if not self.min_stack or val <= self.min_stack[-1]:
            self.min_stack.append(val)

    def pop(self):
        val = self.stack.pop()
        if val == self.min_stack[-1]:
            self.min_stack.pop()
        return val

    def get_min(self):
        return self.min_stack[-1]

ms = MinStack()
ms.push(5); ms.push(2); ms.push(7); ms.push(1)
print(ms.get_min())  # 1
ms.pop()
print(ms.get_min())  # 2

# ═══════════════════════════════════════
# BFS with Queue — Level order traversal
# ═══════════════════════════════════════
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def level_order(root):
    """BFS — Time: O(n), Space: O(n)"""
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left: queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level)
    return result
```

---

## 5.5 Trees

### Q9: Binary tree problems.

```python
# Maximum depth of binary tree
def max_depth(root):
    """DFS — Time: O(n), Space: O(h) where h is height"""
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))

# Validate BST
def is_valid_bst(root, lo=float('-inf'), hi=float('inf')):
    if not root:
        return True
    if not (lo < root.val < hi):
        return False
    return (is_valid_bst(root.left, lo, root.val) and
            is_valid_bst(root.right, root.val, hi))

# Lowest Common Ancestor
def lca(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left and right:
        return root
    return left or right

# Inorder traversal (iterative) — gives sorted order for BST
def inorder_iterative(root):
    result = []
    stack = []
    current = root
    while current or stack:
        while current:
            stack.append(current)
            current = current.left
        current = stack.pop()
        result.append(current.val)
        current = current.right
    return result

# Serialize / Deserialize binary tree
def serialize(root):
    if not root:
        return "null"
    return f"{root.val},{serialize(root.left)},{serialize(root.right)}"

def deserialize(data):
    def helper(nodes):
        val = next(nodes)
        if val == "null":
            return None
        node = TreeNode(int(val))
        node.left = helper(nodes)
        node.right = helper(nodes)
        return node
    return helper(iter(data.split(",")))
```

---

## 5.6 Hash Maps & Sets

### Q10: Common hash map patterns.

```python
from collections import Counter, defaultdict

# ═══════════════════════════════════════
# Group Anagrams
# ═══════════════════════════════════════
def group_anagrams(strs: list[str]) -> list[list[str]]:
    """Time: O(n * k log k), Space: O(n*k) where k = max string length"""
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))     # Anagrams have same sorted form
        groups[key].append(s)
    return list(groups.values())

print(group_anagrams(["eat","tea","tan","ate","nat","bat"]))
# [['eat','tea','ate'], ['tan','nat'], ['bat']]

# ═══════════════════════════════════════
# Top K Frequent Elements
# ═══════════════════════════════════════
import heapq

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Time: O(n log k), Space: O(n)"""
    count = Counter(nums)
    return heapq.nlargest(k, count.keys(), key=count.get)

print(top_k_frequent([1,1,1,2,2,3], 2))  # [1, 2]

# ═══════════════════════════════════════
# Subarray Sum Equals K (prefix sum + hash map)
# ═══════════════════════════════════════
def subarray_sum(nums: list[int], k: int) -> int:
    """Count subarrays summing to k. Time: O(n), Space: O(n)"""
    count = 0
    prefix_sum = 0
    prefix_counts = {0: 1}     # base case: empty prefix

    for num in nums:
        prefix_sum += num
        # If (prefix_sum - k) was seen before, those subarrays sum to k
        count += prefix_counts.get(prefix_sum - k, 0)
        prefix_counts[prefix_sum] = prefix_counts.get(prefix_sum, 0) + 1

    return count

print(subarray_sum([1, 1, 1], 2))  # 2 — subarrays [1,1] at indices 0-1 and 1-2
```

---

## 5.7 Dynamic Programming

### Q11: Essential DP problems.

```python
# ═══════════════════════════════════════
# Climbing Stairs — bottom-up DP
# ═══════════════════════════════════════
def climb_stairs(n: int) -> int:
    """
    How many distinct ways to climb n stairs (1 or 2 steps)?
    Time: O(n), Space: O(1)
    """
    if n <= 2:
        return n
    prev2, prev1 = 1, 2
    for _ in range(3, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    return prev1

print(climb_stairs(5))  # 8

# ═══════════════════════════════════════
# Longest Common Subsequence
# ═══════════════════════════════════════
def lcs(text1: str, text2: str) -> int:
    """Time: O(m*n), Space: O(m*n)"""
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    return dp[m][n]

print(lcs("abcde", "ace"))  # 3 ("ace")

# ═══════════════════════════════════════
# 0/1 Knapsack
# ═══════════════════════════════════════
def knapsack(weights, values, capacity):
    """Time: O(n * capacity), Space: O(capacity)"""
    n = len(weights)
    dp = [0] * (capacity + 1)

    for i in range(n):
        # Traverse backwards to avoid using same item twice
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])

    return dp[capacity]

print(knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7))  # 9

# ═══════════════════════════════════════
# Coin Change — minimum coins
# ═══════════════════════════════════════
def coin_change(coins: list[int], amount: int) -> int:
    """Time: O(amount * len(coins)), Space: O(amount)"""
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0

    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1

print(coin_change([1, 5, 10, 25], 30))  # 2 (25 + 5)

# ═══════════════════════════════════════
# Maximum Subarray (Kadane's Algorithm)
# ═══════════════════════════════════════
def max_subarray(nums: list[int]) -> int:
    """Time: O(n), Space: O(1)"""
    max_sum = curr_sum = nums[0]
    for num in nums[1:]:
        curr_sum = max(num, curr_sum + num)
        max_sum = max(max_sum, curr_sum)
    return max_sum

print(max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))  # 6 ([4,-1,2,1])
```

---

## 5.8 Graphs

### Q12: Graph traversals and common problems.

```python
from collections import defaultdict, deque

# ═══════════════════════════════════════
# Graph representation
# ═══════════════════════════════════════
# Adjacency list (most common in Python)
graph = defaultdict(list)
edges = [(0,1), (0,2), (1,3), (2,3), (3,4)]
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)    # For undirected graph

# ═══════════════════════════════════════
# BFS — Breadth-First Search
# ═══════════════════════════════════════
def bfs(graph, start):
    """Time: O(V+E), Space: O(V)"""
    visited = {start}
    queue = deque([start])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order

# ═══════════════════════════════════════
# DFS — Depth-First Search
# ═══════════════════════════════════════
def dfs(graph, start, visited=None):
    """Time: O(V+E), Space: O(V)"""
    if visited is None:
        visited = set()
    visited.add(start)
    print(start, end=" ")
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)

# Iterative DFS
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    order = []
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            order.append(node)
            for neighbor in reversed(graph[node]):
                stack.append(neighbor)
    return order

# ═══════════════════════════════════════
# Number of Islands (grid DFS)
# ═══════════════════════════════════════
def num_islands(grid: list[list[str]]) -> int:
    """Time: O(m*n), Space: O(m*n)"""
    if not grid:
        return 0

    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == '0':
            return
        grid[r][c] = '0'  # Mark visited
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)

    return count

# ═══════════════════════════════════════
# Topological Sort (for DAGs — task scheduling)
# ═══════════════════════════════════════
def topological_sort(num_nodes, edges):
    """Kahn's algorithm (BFS). Time: O(V+E)"""
    graph = defaultdict(list)
    in_degree = [0] * num_nodes

    for u, v in edges:
        graph[u].append(v)
        in_degree[v] += 1

    queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order if len(order) == num_nodes else []  # Empty = cycle exists

# ═══════════════════════════════════════
# Dijkstra's Algorithm — shortest path
# ═══════════════════════════════════════
import heapq

def dijkstra(graph, start):
    """Time: O((V+E) log V) with min-heap"""
    distances = {start: 0}
    heap = [(0, start)]
    visited = set()

    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph[node]:
            new_dist = dist + weight
            if new_dist < distances.get(neighbor, float('inf')):
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return distances

# Usage
weighted_graph = {
    'A': [('B', 1), ('C', 4)],
    'B': [('C', 2), ('D', 5)],
    'C': [('D', 1)],
    'D': []
}
print(dijkstra(weighted_graph, 'A'))  # {'A': 0, 'B': 1, 'C': 3, 'D': 4}
```

---

## 5.9 Sorting Algorithms

### Q13: Implement key sorting algorithms.

```python
# ═══════════════════════════════════════
# Merge Sort — O(n log n), stable
# ═══════════════════════════════════════
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# ═══════════════════════════════════════
# Quick Sort — O(n log n) average, O(n²) worst
# ═══════════════════════════════════════
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# Python's built-in: Timsort — hybrid merge+insertion sort
# O(n log n) worst case, O(n) best case (already sorted)
# STABLE sort — preserves order of equal elements
sorted([3, 1, 4, 1, 5])       # Returns new list
[3, 1, 4, 1, 5].sort()        # Sorts in place

# Custom sorting
students = [("Alice", 3.9), ("Bob", 3.7), ("Charlie", 3.9)]
sorted(students, key=lambda s: (-s[1], s[0]))
# Sort by GPA descending, then name ascending
# [('Alice', 3.9), ('Charlie', 3.9), ('Bob', 3.7)]
```

---

## 5.10 Heap / Priority Queue

### Q14: Heap operations in Python.

```python
import heapq

# Python's heapq is a MIN-HEAP
nums = [3, 1, 4, 1, 5, 9, 2, 6]
heapq.heapify(nums)            # O(n) — transform list into heap
print(nums)                     # [1, 1, 2, 3, 5, 9, 4, 6]

heapq.heappush(nums, 0)        # O(log n)
print(heapq.heappop(nums))     # 0 — smallest element

# For MAX-HEAP: negate values
max_heap = []
for n in [3, 1, 4, 1, 5]:
    heapq.heappush(max_heap, -n)
print(-heapq.heappop(max_heap))  # 5 (largest)

# K largest/smallest
heapq.nlargest(3, [3, 1, 4, 1, 5])    # [5, 4, 3]
heapq.nsmallest(3, [3, 1, 4, 1, 5])   # [1, 1, 3]

# Merge sorted streams — O(n log k) where k = number of streams
merged = list(heapq.merge([1, 3, 5], [2, 4, 6], [0, 7]))
print(merged)  # [0, 1, 2, 3, 4, 5, 6, 7]

# Kth Largest Element — O(n log k)
def find_kth_largest(nums, k):
    heap = nums[:k]
    heapq.heapify(heap)
    for num in nums[k:]:
        if num > heap[0]:
            heapq.heapreplace(heap, num)  # Pop and push in one operation
    return heap[0]

print(find_kth_largest([3, 2, 1, 5, 6, 4], 2))  # 5
```

---

## 5.11 Binary Search Patterns

### Q15: Binary search variations.

```python
import bisect

# Standard binary search
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2      # Avoid overflow (matters in other languages)
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# Find first occurrence (leftmost)
def bisect_left_custom(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo

# Python's bisect module
arr = [1, 2, 2, 2, 3, 4, 5]
bisect.bisect_left(arr, 2)      # 1 — first position to insert 2
bisect.bisect_right(arr, 2)     # 4 — position after last 2
bisect.insort(arr, 2.5)         # Insert maintaining sorted order

# Binary search on answer — "Can we achieve X?"
def min_days_to_make_bouquets(bloomDay, m, k):
    """Binary search on the answer (day)."""
    def can_make(day):
        bouquets = flowers = 0
        for bloom in bloomDay:
            if bloom <= day:
                flowers += 1
                if flowers == k:
                    bouquets += 1
                    flowers = 0
            else:
                flowers = 0
        return bouquets >= m

    if m * k > len(bloomDay):
        return -1
    lo, hi = min(bloomDay), max(bloomDay)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_make(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

---
