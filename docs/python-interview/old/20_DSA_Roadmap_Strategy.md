# 20 — DSA Learning Roadmap & Strategy
## The Exact Plan to Crack Google/Amazon/Meta

---

## 🎯 The 6-Week DSA Preparation Plan

### How to Solve ANY Problem (5-Step Method):
```
Step 1: UNDERSTAND (3 min)
  → Read problem twice. Identify inputs, outputs, constraints.
  → Draw examples. Ask "What if input is empty? One element? All same?"

Step 2: PATTERN (2 min)
  → What pattern does this match? (See File 19)
  → Keywords: "subarray" → sliding window, "sorted" → binary search, etc.

Step 3: APPROACH (3 min)
  → Brute force first (always). State its complexity.
  → Then optimize: "Can I reduce with hash map? Binary search? DP?"

Step 4: CODE (15 min)
  → Write clean code. Use meaningful variable names.
  → Handle edge cases: empty input, single element, negatives, overflow.

Step 5: TEST (2 min)
  → Walk through with your example. Check edge cases.
  → State time/space complexity.
```

---

## Week 1: Arrays & Hashing (Foundation)

**Day 1-2: Arrays Basics**
```
Must-Solve:
  ✅ Two Sum (HashMap)
  ✅ Best Time to Buy and Sell Stock
  ✅ Contains Duplicate
  ✅ Product of Array Except Self
  ✅ Maximum Subarray (Kadane's)
```

```python
# Best Time to Buy and Sell Stock — O(n) [Most asked easy problem]
def max_profit(prices):
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    return max_profit

# Product of Array Except Self — O(n) without division
def product_except_self(nums):
    n = len(nums)
    result = [1] * n
    # Left pass: result[i] = product of all elements to the left
    prefix = 1
    for i in range(n):
        result[i] = prefix
        prefix *= nums[i]
    # Right pass: multiply by product of all elements to the right
    suffix = 1
    for i in range(n - 1, -1, -1):
        result[i] *= suffix
        suffix *= nums[i]
    return result

# Example: [1,2,3,4] → [24,12,8,6]
```

**Day 3-4: Hashing Patterns**
```
Must-Solve:
  ✅ Group Anagrams
  ✅ Valid Anagram
  ✅ Top K Frequent Elements
  ✅ Longest Consecutive Sequence
  ✅ Subarray Sum Equals K
```

```python
# Longest Consecutive Sequence — O(n) [Google/Amazon]
def longest_consecutive(nums):
    num_set = set(nums)
    best = 0
    for num in num_set:
        if num - 1 not in num_set:   # Only start from sequence beginning
            length = 1
            while num + length in num_set:
                length += 1
            best = max(best, length)
    return best

# Example: [100,4,200,1,3,2] → 4 (sequence: 1,2,3,4)
```

**Day 5-7: Strings**
```
Must-Solve:
  ✅ Valid Palindrome
  ✅ Longest Palindromic Substring
  ✅ Longest Substring Without Repeating Characters
  ✅ String to Integer (atoi)
  ✅ Longest Common Prefix
```

---

## Week 2: Two Pointers, Sliding Window & Binary Search

**Day 1-2: Two Pointers**
```
Must-Solve:
  ✅ Three Sum
  ✅ Container With Most Water
  ✅ Trapping Rain Water
  ✅ Valid Palindrome
  ✅ Move Zeroes
```

```python
# Move Zeroes — O(n), In-place
def move_zeroes(nums):
    write = 0
    for read in range(len(nums)):
        if nums[read] != 0:
            nums[write], nums[read] = nums[read], nums[write]
            write += 1
```

**Day 3-4: Sliding Window**
```
Must-Solve:
  ✅ Minimum Window Substring
  ✅ Longest Repeating Character Replacement
  ✅ Permutation in String
  ✅ Maximum Sum Subarray of Size K
  ✅ Fruit Into Baskets
```

```python
# Longest Repeating Character Replacement — O(n)
def character_replacement(s, k):
    freq = {}
    left = 0
    max_count = 0    # Most frequent char in current window
    best = 0
    for right in range(len(s)):
        freq[s[right]] = freq.get(s[right], 0) + 1
        max_count = max(max_count, freq[s[right]])
        # Window size - most frequent = chars to replace
        while (right - left + 1) - max_count > k:
            freq[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
```

**Day 5-7: Binary Search**
```
Must-Solve:
  ✅ Binary Search (basic)
  ✅ Search in Rotated Sorted Array
  ✅ Find Minimum in Rotated Sorted Array
  ✅ Koko Eating Bananas
  ✅ Median of Two Sorted Arrays
```

---

## Week 3: Linked Lists, Stacks & Queues

**Day 1-3: Linked Lists**
```
Must-Solve:
  ✅ Reverse Linked List
  ✅ Merge Two Sorted Lists
  ✅ Detect Cycle (Floyd's)
  ✅ Remove Nth Node From End
  ✅ Reorder List
  ✅ LRU Cache (HashMap + Doubly Linked List) [HARD — very frequently asked]
```

```python
# LRU Cache — O(1) get and put [Amazon/Google favorite]
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)    # Mark as recently used
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)   # Remove least recently used

# Remove Nth Node From End — O(n) one pass
def remove_nth_from_end(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n + 1):
        fast = fast.next
    while fast:
        slow = slow.next
        fast = fast.next
    slow.next = slow.next.next
    return dummy.next
```

**Day 4-5: Stacks**
```
Must-Solve:
  ✅ Valid Parentheses
  ✅ Min Stack
  ✅ Daily Temperatures
  ✅ Largest Rectangle in Histogram
  ✅ Evaluate Reverse Polish Notation
```

**Day 6-7: Queues & Deques**
```
Must-Solve:
  ✅ Sliding Window Maximum (Monotonic Deque)
  ✅ Implement Queue using Stacks
  ✅ Design Circular Queue
```

---

## Week 4: Trees & Graphs

**Day 1-3: Binary Trees**
```
Must-Solve:
  ✅ Maximum Depth of Binary Tree
  ✅ Invert Binary Tree
  ✅ Same Tree
  ✅ Subtree of Another Tree
  ✅ Lowest Common Ancestor
  ✅ Binary Tree Level Order Traversal
  ✅ Validate BST
  ✅ Serialize and Deserialize Binary Tree
  ✅ Binary Tree Maximum Path Sum
  ✅ Construct Binary Tree from Preorder and Inorder
```

```python
# Construct from Preorder + Inorder — O(n)
def build_tree(preorder, inorder):
    if not preorder:
        return None
    root = TreeNode(preorder[0])
    mid = inorder.index(preorder[0])
    root.left = build_tree(preorder[1:mid+1], inorder[:mid])
    root.right = build_tree(preorder[mid+1:], inorder[mid+1:])
    return root

# Diameter of Binary Tree — O(n) [Frequently asked]
def diameter_of_tree(root):
    diameter = [0]
    def depth(node):
        if not node:
            return 0
        left = depth(node.left)
        right = depth(node.right)
        diameter[0] = max(diameter[0], left + right)
        return 1 + max(left, right)
    depth(root)
    return diameter[0]
```

**Day 4-5: Graphs**
```
Must-Solve:
  ✅ Number of Islands
  ✅ Clone Graph
  ✅ Course Schedule (Topological Sort)
  ✅ Pacific Atlantic Water Flow
  ✅ Number of Connected Components
  ✅ Word Ladder
  ✅ Graph Valid Tree
```

**Day 6-7: Advanced Graph**
```
Must-Solve:
  ✅ Dijkstra's Shortest Path
  ✅ Network Delay Time
  ✅ Alien Dictionary (Topological Sort) [HARD]
```

```python
# Alien Dictionary — O(V + E) [Google classic]
def alien_order(words):
    # Build graph from adjacent word comparisons
    graph = {c: set() for word in words for c in word}
    in_degree = {c: 0 for c in graph}
    
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        min_len = min(len(w1), len(w2))
        if len(w1) > len(w2) and w1[:min_len] == w2[:min_len]:
            return ""    # Invalid: "abc" before "ab"
        for j in range(min_len):
            if w1[j] != w2[j]:
                if w2[j] not in graph[w1[j]]:
                    graph[w1[j]].add(w2[j])
                    in_degree[w2[j]] += 1
                break
    
    # Topological sort (BFS)
    queue = deque([c for c in in_degree if in_degree[c] == 0])
    result = []
    while queue:
        c = queue.popleft()
        result.append(c)
        for neighbor in graph[c]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return "".join(result) if len(result) == len(graph) else ""
```

---

## Week 5: Dynamic Programming & Backtracking

**Day 1-4: DP (Most Important Week)**
```
Must-Solve:
  ✅ Climbing Stairs
  ✅ House Robber / House Robber II
  ✅ Coin Change
  ✅ Longest Increasing Subsequence
  ✅ Longest Common Subsequence
  ✅ Word Break
  ✅ 0/1 Knapsack
  ✅ Edit Distance
  ✅ Unique Paths
  ✅ Decode Ways
  ✅ Maximum Product Subarray
  ✅ Partition Equal Subset Sum
  ✅ Target Sum
```

```python
# Maximum Product Subarray — O(n)
def max_product(nums):
    max_so_far = min_so_far = result = nums[0]
    for num in nums[1:]:
        candidates = (num, max_so_far * num, min_so_far * num)
        max_so_far = max(candidates)
        min_so_far = min(candidates)
        result = max(result, max_so_far)
    return result

# Partition Equal Subset Sum — O(n * sum) [Amazon favorite]
def can_partition(nums):
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    dp = {0}
    for num in nums:
        dp = dp | {s + num for s in dp if s + num <= target}
    return target in dp
```

**Day 5-7: Backtracking**
```
Must-Solve:
  ✅ Subsets / Subsets II
  ✅ Permutations
  ✅ Combination Sum / II
  ✅ N-Queens
  ✅ Word Search
  ✅ Palindrome Partitioning
  ✅ Letter Combinations of Phone Number
```

---

## Week 6: Heaps, Tries, Intervals & Review

**Day 1-2: Heaps / Priority Queues**
```
Must-Solve:
  ✅ Kth Largest Element
  ✅ Merge K Sorted Lists
  ✅ Find Median from Data Stream
  ✅ Top K Frequent Elements
  ✅ Task Scheduler
```

**Day 3: Tries**
```
  ✅ Implement Trie
  ✅ Design Add and Search Words Data Structure
  ✅ Word Search II
```

**Day 4: Intervals**
```
  ✅ Merge Intervals
  ✅ Insert Interval
  ✅ Non-overlapping Intervals
  ✅ Meeting Rooms / Meeting Rooms II
```

**Day 5-7: Revision & Mock Interviews**
```
  → Redo problems you got wrong
  → Time yourself: 20 min per medium, 35 min per hard
  → Practice explaining your thought process OUT LOUD
  → Do 2-3 mock interviews on Pramp / interviewing.io
```

---

## 📊 The 75 Must-Solve Problems (NeetCode 75)

```
Arrays & Hashing:     Two Sum, Group Anagrams, Top K Frequent, Product Except Self,
                      Longest Consecutive, Valid Anagram, Contains Duplicate, Encode/Decode Strings

Two Pointers:         Valid Palindrome, 3Sum, Container With Most Water, Trapping Rain Water

Sliding Window:       Longest Substring No Repeat, Longest Repeating Char Replace, Min Window Substring

Stack:                Valid Parentheses, Min Stack, Daily Temperatures, Largest Rectangle Histogram,
                      Evaluate Reverse Polish

Binary Search:        Search Rotated Array, Find Min Rotated, Koko Bananas, Median Two Sorted Arrays

Linked List:          Reverse LL, Merge Two Sorted, Detect Cycle, Remove Nth From End,
                      Reorder List, LRU Cache, Merge K Sorted

Trees:                Max Depth, Invert Tree, Same Tree, Subtree, LCA, Level Order,
                      Validate BST, Build from Pre+In, Max Path Sum, Serialize/Deserialize

Graphs:               Number of Islands, Clone Graph, Course Schedule, Pacific Atlantic,
                      Word Ladder, Graph Valid Tree

Heap:                 Kth Largest, Merge K Lists, Find Median Stream, Task Scheduler, Top K Frequent

DP:                   Climbing Stairs, House Robber, Coin Change, LIS, LCS, Word Break,
                      Edit Distance, Unique Paths, Decode Ways, Max Product Subarray

Backtracking:         Subsets, Permutations, Combination Sum, N-Queens, Word Search

Intervals:            Merge Intervals, Insert Interval, Non-overlapping, Meeting Rooms II

Greedy:               Jump Game, Jump Game II, Gas Station, Hand of Straights

Bit Manipulation:     Single Number, Number of 1 Bits, Counting Bits, Reverse Bits, Missing Number
```

---

## 🧠 Time Complexity Cheat Sheet

```
O(1):       Hash lookup, array access, push/pop
O(log n):   Binary search, balanced BST operations
O(n):       Linear scan, hash map build, single pass
O(n log n): Sorting (merge sort, timsort), heap operations on n items
O(n²):      Nested loops, brute force pairs, DP with 2 dimensions
O(2ⁿ):      Subsets, recursive backtracking without pruning
O(n!):      Permutations, TSP brute force

Space:
O(1):       In-place, constant extra space
O(n):       Hash map, stack, queue, recursion depth n
O(n²):      2D DP table, adjacency matrix
```

---
