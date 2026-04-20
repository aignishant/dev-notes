# 19 — DSA Patterns Bible: Product-Based Company Preparation
## Google, Amazon, Meta, Microsoft Level — Pattern Recognition Guide

---

## 🎯 THE GOLDEN RULE: Learn PATTERNS, Not Problems

```
Don't memorize 500 problems. Learn 15 patterns that solve 500 problems.
When you see a new problem → identify the pattern → apply the template.
```

---

## PATTERN 1: Sliding Window
**When to use:** Subarray/substring problems with contiguous elements
**Signal words:** "subarray", "substring", "window", "contiguous", "consecutive"

### Template:
```python
def sliding_window_fixed(arr, k):
    """Fixed-size window of size k."""
    window_sum = sum(arr[:k])
    best = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]    # Slide: add right, remove left
        best = max(best, window_sum)
    return best

def sliding_window_variable(s, condition):
    """Variable-size window — expand right, shrink left."""
    left = 0
    best = 0
    state = {}   # Track window state (freq map, count, etc.)
    
    for right in range(len(s)):
        # EXPAND: add s[right] to window state
        state[s[right]] = state.get(s[right], 0) + 1
        
        # SHRINK: while window is invalid
        while not condition(state):
            state[s[left]] -= 1
            if state[s[left]] == 0:
                del state[s[left]]
            left += 1
        
        # UPDATE answer
        best = max(best, right - left + 1)
    
    return best
```

### Must-Solve Problems:
```python
# 1. Maximum Sum Subarray of Size K — O(n)
def max_sum_subarray(arr, k):
    window = sum(arr[:k])
    best = window
    for i in range(k, len(arr)):
        window += arr[i] - arr[i-k]
        best = max(best, window)
    return best

# 2. Longest Substring Without Repeating Characters — O(n)
def longest_unique_substring(s):
    seen = {}
    left = 0
    best = 0
    for right, char in enumerate(s):
        if char in seen and seen[char] >= left:
            left = seen[char] + 1
        seen[char] = right
        best = max(best, right - left + 1)
    return best

# Example: "abcabcbb" → 3 ("abc")

# 3. Minimum Window Substring — O(n) [HARD — Google favorite]
from collections import Counter

def min_window(s, t):
    """Find smallest substring of s containing all chars of t."""
    need = Counter(t)
    missing = len(t)
    left = 0
    best = (0, float('inf'))  # (start, end)
    
    for right, char in enumerate(s):
        if need[char] > 0:
            missing -= 1
        need[char] -= 1
        
        while missing == 0:    # Valid window — try to shrink
            if right - left < best[1] - best[0]:
                best = (left, right)
            need[s[left]] += 1
            if need[s[left]] > 0:
                missing += 1
            left += 1
    
    return s[best[0]:best[1]+1] if best[1] != float('inf') else ""

# Example: s="ADOBECODEBANC", t="ABC" → "BANC"

# 4. Maximum of All Subarrays of Size K (Deque approach) — O(n)
from collections import deque

def max_sliding_window(nums, k):
    dq = deque()   # Stores indices — monotonic decreasing
    result = []
    for i, num in enumerate(nums):
        while dq and dq[0] < i - k + 1:
            dq.popleft()        # Remove out-of-window
        while dq and nums[dq[-1]] < num:
            dq.pop()            # Maintain decreasing order
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result

# 5. Longest Substring with At Most K Distinct Characters — O(n)
def longest_k_distinct(s, k):
    freq = {}
    left = 0
    best = 0
    for right, char in enumerate(s):
        freq[char] = freq.get(char, 0) + 1
        while len(freq) > k:
            freq[s[left]] -= 1
            if freq[s[left]] == 0:
                del freq[s[left]]
            left += 1
        best = max(best, right - left + 1)
    return best
```

---

## PATTERN 2: Two Pointers
**When to use:** Sorted arrays, pair finding, partitioning
**Signal words:** "pair", "triplet", "sorted array", "two sum", "palindrome"

### Must-Solve Problems:
```python
# 1. Two Sum II (Sorted Array) — O(n)
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return [left, right]
        elif total < target:
            left += 1
        else:
            right -= 1
    return []

# 2. Three Sum — O(n²) [Very frequently asked]
def three_sum(nums):
    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i-1]:
            continue                        # Skip duplicates
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left+1]:
                    left += 1               # Skip duplicates
                while left < right and nums[right] == nums[right-1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return result

# 3. Container With Most Water — O(n)
def max_area(height):
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        area = min(height[left], height[right]) * (right - left)
        best = max(best, area)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best

# 4. Trapping Rain Water — O(n) [HARD — Google classic]
def trap(height):
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    while left < right:
        if height[left] < height[right]:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water

# 5. Valid Palindrome II — Can you make palindrome by removing at most 1 char?
def valid_palindrome_ii(s):
    def is_pali(lo, hi):
        while lo < hi:
            if s[lo] != s[hi]:
                return False
            lo += 1
            hi -= 1
        return True
    
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return is_pali(left+1, right) or is_pali(left, right-1)
        left += 1
        right -= 1
    return True

# 6. Remove Duplicates from Sorted Array (In-place) — O(n)
def remove_duplicates(nums):
    if not nums:
        return 0
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[read - 1]:
            nums[write] = nums[read]
            write += 1
    return write
```

---

## PATTERN 3: Fast & Slow Pointers (Floyd's)
**When to use:** Cycle detection, finding middle, linked list problems
**Signal words:** "cycle", "circular", "middle of linked list", "happy number"

```python
# 1. Detect Cycle in Linked List — O(n)
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False

# 2. Find Cycle Start — O(n)
def detect_cycle_start(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            # Reset one pointer to head
            slow = head
            while slow is not fast:
                slow = slow.next
                fast = fast.next
            return slow    # Cycle start!
    return None

# 3. Find Middle of Linked List — O(n)
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow

# 4. Happy Number — O(log n)
def is_happy(n):
    def get_next(num):
        return sum(int(d) ** 2 for d in str(num))
    slow = n
    fast = get_next(n)
    while fast != 1 and slow != fast:
        slow = get_next(slow)
        fast = get_next(get_next(fast))
    return fast == 1

# Example: 19 → 82 → 68 → 100 → 1 ✓ Happy!

# 5. Palindrome Linked List — O(n) time, O(1) space
def is_palindrome_list(head):
    # Find middle
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    
    # Reverse second half
    prev = None
    while slow:
        slow.next, prev, slow = prev, slow, slow.next
    
    # Compare halves
    left, right = head, prev
    while right:
        if left.val != right.val:
            return False
        left = left.next
        right = right.next
    return True
```

---

## PATTERN 4: Merge Intervals
**When to use:** Overlapping intervals, scheduling, time ranges
**Signal words:** "intervals", "overlapping", "merge", "schedule", "meeting rooms"

```python
# 1. Merge Overlapping Intervals — O(n log n)
def merge_intervals(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:    # Overlapping
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

# Example: [[1,3],[2,6],[8,10],[15,18]] → [[1,6],[8,10],[15,18]]

# 2. Insert Interval — O(n)
def insert_interval(intervals, new):
    result = []
    i = 0
    # Add all intervals that come before new
    while i < len(intervals) and intervals[i][1] < new[0]:
        result.append(intervals[i])
        i += 1
    # Merge overlapping intervals with new
    while i < len(intervals) and intervals[i][0] <= new[1]:
        new = [min(new[0], intervals[i][0]), max(new[1], intervals[i][1])]
        i += 1
    result.append(new)
    # Add remaining
    result.extend(intervals[i:])
    return result

# 3. Meeting Rooms II — Minimum rooms needed — O(n log n) [Amazon favorite]
import heapq

def min_meeting_rooms(intervals):
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    heap = [intervals[0][1]]   # End times
    for start, end in intervals[1:]:
        if start >= heap[0]:   # Room freed up
            heapq.heapreplace(heap, end)
        else:
            heapq.heappush(heap, end)
    return len(heap)

# 4. Non-overlapping Intervals — Minimum removals — O(n log n)
def erase_overlap_intervals(intervals):
    intervals.sort(key=lambda x: x[1])   # Sort by END time (greedy)
    count = 0
    prev_end = float('-inf')
    for start, end in intervals:
        if start >= prev_end:
            prev_end = end
        else:
            count += 1
    return count
```

---

## PATTERN 5: Binary Search Variations
**When to use:** Sorted data, search space reduction, "minimum maximum" problems
**Signal words:** "sorted", "find minimum/maximum that satisfies", "search", "rotated"

```python
# 1. Search in Rotated Sorted Array — O(log n) [Google classic]
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        
        # Left half is sorted
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        # Right half is sorted
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1

# 2. Find Minimum in Rotated Sorted Array — O(log n)
def find_min_rotated(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]

# 3. Binary Search on Answer — "Minimum capacity to ship packages in D days"
def ship_within_days(weights, days):
    def can_ship(capacity):
        current = 0
        d = 1
        for w in weights:
            if current + w > capacity:
                d += 1
                current = 0
            current += w
        return d <= days
    
    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_ship(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo

# 4. Koko Eating Bananas — O(n log m)
def min_eating_speed(piles, h):
    import math
    def can_eat(speed):
        return sum(math.ceil(p / speed) for p in piles) <= h
    
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if can_eat(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo

# 5. Find Peak Element — O(log n)
def find_peak(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo

# 6. Median of Two Sorted Arrays — O(log(min(m,n))) [HARD — Google]
def find_median_sorted_arrays(nums1, nums2):
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    lo, hi = 0, m
    
    while lo <= hi:
        i = (lo + hi) // 2
        j = (m + n + 1) // 2 - i
        
        left1 = nums1[i-1] if i > 0 else float('-inf')
        right1 = nums1[i] if i < m else float('inf')
        left2 = nums2[j-1] if j > 0 else float('-inf')
        right2 = nums2[j] if j < n else float('inf')
        
        if left1 <= right2 and left2 <= right1:
            if (m + n) % 2 == 0:
                return (max(left1, left2) + min(right1, right2)) / 2
            return max(left1, left2)
        elif left1 > right2:
            hi = i - 1
        else:
            lo = i + 1
```

---

## PATTERN 6: BFS / DFS on Graphs & Trees
**When to use:** Traversal, shortest path, connected components, tree problems

```python
from collections import deque

# 1. Number of Islands — O(m*n)
def num_islands(grid):
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0
    
    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == '0':
            return
        grid[r][c] = '0'
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)
    return count

# 2. Shortest Path in Binary Matrix (BFS) — O(n²)
def shortest_path(grid):
    n = len(grid)
    if grid[0][0] or grid[n-1][n-1]:
        return -1
    queue = deque([(0, 0, 1)])
    visited = {(0, 0)}
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    while queue:
        r, c, dist = queue.popleft()
        if r == n-1 and c == n-1:
            return dist
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0 and (nr,nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc, dist + 1))
    return -1

# 3. Clone Graph — O(V + E)
def clone_graph(node):
    if not node:
        return None
    clones = {}
    
    def dfs(n):
        if n in clones:
            return clones[n]
        copy = Node(n.val)
        clones[n] = copy
        for neighbor in n.neighbors:
            copy.neighbors.append(dfs(neighbor))
        return copy
    
    return dfs(node)

# 4. Course Schedule (Cycle Detection in Directed Graph) — O(V + E)
def can_finish(num_courses, prerequisites):
    graph = [[] for _ in range(num_courses)]
    in_degree = [0] * num_courses
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    
    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    completed = 0
    while queue:
        course = queue.popleft()
        completed += 1
        for next_course in graph[course]:
            in_degree[next_course] -= 1
            if in_degree[next_course] == 0:
                queue.append(next_course)
    return completed == num_courses

# 5. Word Ladder — BFS — O(n * m²) [HARD]
def ladder_length(begin_word, end_word, word_list):
    word_set = set(word_list)
    if end_word not in word_set:
        return 0
    queue = deque([(begin_word, 1)])
    visited = {begin_word}
    
    while queue:
        word, length = queue.popleft()
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                next_word = word[:i] + c + word[i+1:]
                if next_word == end_word:
                    return length + 1
                if next_word in word_set and next_word not in visited:
                    visited.add(next_word)
                    queue.append((next_word, length + 1))
    return 0

# 6. Binary Tree Maximum Path Sum — O(n) [HARD — frequently asked]
def max_path_sum(root):
    best = [float('-inf')]
    
    def dfs(node):
        if not node:
            return 0
        left = max(dfs(node.left), 0)    # Ignore negative paths
        right = max(dfs(node.right), 0)
        
        # Path through this node (potentially the answer)
        best[0] = max(best[0], left + node.val + right)
        
        # Return max single-branch path for parent
        return node.val + max(left, right)
    
    dfs(root)
    return best[0]
```

---

## PATTERN 7: Dynamic Programming
**When to use:** Optimal substructure + overlapping subproblems
**Signal words:** "minimum/maximum", "count ways", "is it possible", "longest/shortest"

### DP Framework:
```
1. Define state: What info do I need? → dp[i] means...
2. Base case: What's the trivially known answer?
3. Transition: How do I build from smaller to larger?
4. Answer: Where is the final answer?
```

```python
# 1. Longest Increasing Subsequence — O(n log n)
import bisect

def length_of_lis(nums):
    tails = []     # tails[i] = smallest tail of increasing subsequence of length i+1
    for num in nums:
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    return len(tails)

# Example: [10,9,2,5,3,7,101,18] → 4 (subsequence: [2,3,7,101])

# 2. Edit Distance — O(m*n) [Google classic]
def min_distance(word1, word2):
    m, n = len(word1), len(word2)
    dp = [[0] * (n+1) for _ in range(m+1)]
    
    for i in range(m+1):
        dp[i][0] = i
    for j in range(n+1):
        dp[0][j] = j
    
    for i in range(1, m+1):
        for j in range(1, n+1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]

# 3. Longest Palindromic Substring — O(n²)
def longest_palindrome(s):
    n = len(s)
    if n < 2:
        return s
    
    start, max_len = 0, 1
    
    def expand(left, right):
        nonlocal start, max_len
        while left >= 0 and right < n and s[left] == s[right]:
            if right - left + 1 > max_len:
                start = left
                max_len = right - left + 1
            left -= 1
            right += 1
    
    for i in range(n):
        expand(i, i)       # Odd length
        expand(i, i + 1)   # Even length
    
    return s[start:start + max_len]

# 4. House Robber — O(n)
def rob(nums):
    if not nums:
        return 0
    if len(nums) <= 2:
        return max(nums)
    prev2, prev1 = nums[0], max(nums[0], nums[1])
    for i in range(2, len(nums)):
        curr = max(prev1, prev2 + nums[i])
        prev2, prev1 = prev1, curr
    return prev1

# 5. Word Break — O(n²)
def word_break(s, word_dict):
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    words = set(word_dict)
    
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break
    return dp[n]

# 6. Unique Paths — O(m*n)
def unique_paths(m, n):
    dp = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j-1]
    return dp[-1]

# 7. Decode Ways — O(n) [Amazon favorite]
def num_decodings(s):
    if not s or s[0] == '0':
        return 0
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = dp[1] = 1
    for i in range(2, n + 1):
        if s[i-1] != '0':
            dp[i] += dp[i-1]
        two_digit = int(s[i-2:i])
        if 10 <= two_digit <= 26:
            dp[i] += dp[i-2]
    return dp[n]
```

---

## PATTERN 8: Backtracking
**When to use:** Generate all combinations/permutations, constraint satisfaction
**Signal words:** "generate all", "all possible", "combinations", "permutations", "subsets"

```python
# 1. Subsets — O(2^n)
def subsets(nums):
    result = []
    def backtrack(start, current):
        result.append(current[:])
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    backtrack(0, [])
    return result

# 2. Permutations — O(n!)
def permutations(nums):
    result = []
    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])
            return
        for i in range(len(remaining)):
            current.append(remaining[i])
            backtrack(current, remaining[:i] + remaining[i+1:])
            current.pop()
    backtrack([], nums)
    return result

# 3. Combination Sum — O(2^target)
def combination_sum(candidates, target):
    result = []
    def backtrack(start, current, remaining):
        if remaining == 0:
            result.append(current[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break
            current.append(candidates[i])
            backtrack(i, current, remaining - candidates[i])
            current.pop()
    candidates.sort()
    backtrack(0, [], target)
    return result

# 4. N-Queens — O(n!) [Google classic]
def solve_n_queens(n):
    result = []
    board = ['.' * n for _ in range(n)]
    cols = set()
    diag1 = set()   # row - col
    diag2 = set()   # row + col
    
    def backtrack(row):
        if row == n:
            result.append(board[:])
            return
        for col in range(n):
            if col in cols or (row-col) in diag1 or (row+col) in diag2:
                continue
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            board[row] = board[row][:col] + 'Q' + board[row][col+1:]
            backtrack(row + 1)
            board[row] = board[row][:col] + '.' + board[row][col+1:]
            cols.discard(col)
            diag1.discard(row - col)
            diag2.discard(row + col)
    
    backtrack(0)
    return result

# 5. Word Search in Grid — O(m*n*4^L)
def exist(board, word):
    rows, cols = len(board), len(board[0])
    
    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[idx]:
            return False
        temp = board[r][c]
        board[r][c] = '#'    # Mark visited
        found = (dfs(r+1,c,idx+1) or dfs(r-1,c,idx+1) or
                 dfs(r,c+1,idx+1) or dfs(r,c-1,idx+1))
        board[r][c] = temp   # Unmark
        return found
    
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False
```

---

## PATTERN 9: Heap / Priority Queue (Top K)
**When to use:** Kth largest/smallest, merge sorted lists, frequency problems

```python
import heapq

# 1. Kth Largest Element — O(n log k)
def find_kth_largest(nums, k):
    heap = nums[:k]
    heapq.heapify(heap)
    for num in nums[k:]:
        if num > heap[0]:
            heapq.heapreplace(heap, num)
    return heap[0]

# 2. Merge K Sorted Lists — O(n log k)
def merge_k_lists(lists):
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst.val, i, lst))
    
    dummy = ListNode(0)
    curr = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        curr.next = node
        curr = curr.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next

# 3. Find Median from Data Stream — O(log n) per add [HARD]
class MedianFinder:
    def __init__(self):
        self.small = []    # Max heap (negate values)
        self.large = []    # Min heap
    
    def addNum(self, num):
        heapq.heappush(self.small, -num)
        heapq.heappush(self.large, -heapq.heappop(self.small))
        if len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))
    
    def findMedian(self):
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2

# 4. Task Scheduler — O(n)
from collections import Counter

def least_interval(tasks, n):
    freq = Counter(tasks)
    max_freq = max(freq.values())
    max_count = sum(1 for v in freq.values() if v == max_freq)
    return max(len(tasks), (max_freq - 1) * (n + 1) + max_count)
```

---

## PATTERN 10: Trie (Prefix Tree)
**When to use:** Prefix search, autocomplete, word dictionary

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word):
        node = self._find(word)
        return node is not None and node.is_end
    
    def starts_with(self, prefix):
        return self._find(prefix) is not None
    
    def _find(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

# Usage: Autocomplete, spell checking, IP routing, word games
```

---

## PATTERN 11: Monotonic Stack
**When to use:** "Next greater/smaller element", temperature problems, histogram

```python
# 1. Next Greater Element — O(n)
def next_greater(nums):
    result = [-1] * len(nums)
    stack = []    # Indices with no answer yet
    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] < num:
            result[stack.pop()] = num
        stack.append(i)
    return result

# 2. Daily Temperatures — O(n)
def daily_temperatures(temps):
    result = [0] * len(temps)
    stack = []
    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            prev = stack.pop()
            result[prev] = i - prev
        stack.append(i)
    return result

# 3. Largest Rectangle in Histogram — O(n) [HARD — Google]
def largest_rectangle(heights):
    stack = []
    max_area = 0
    heights.append(0)   # Sentinel
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)
    return max_area
```

---

## PATTERN 12: Union-Find (Disjoint Set)
**When to use:** Connected components, cycle detection in undirected graph

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])   # Path compression
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        self.components -= 1
        return True

# Number of Connected Components
def count_components(n, edges):
    uf = UnionFind(n)
    for u, v in edges:
        uf.union(u, v)
    return uf.components
```

---

## 🗺️ Pattern → Problem Mapping Quick Reference

```
Contiguous subarray/substring → Sliding Window
Pair/triplet in sorted array → Two Pointers
Cycle detection, linked list middle → Fast & Slow Pointers
Overlapping intervals → Merge Intervals
Sorted/rotated array search → Binary Search
Shortest path, level-order → BFS
Connected components, paths → DFS
Optimal value, counting ways → Dynamic Programming
All combinations/permutations → Backtracking
Kth element, merge streams → Heap
Prefix matching, dictionary → Trie
Next greater/smaller → Monotonic Stack
Connected components → Union-Find
Topological ordering → Kahn's BFS / DFS
```

---
