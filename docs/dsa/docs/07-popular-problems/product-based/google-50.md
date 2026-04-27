# Google — 50 most-asked questions

> The 50 problems Google has asked most often over the last 5 years, with the patterns behind them and what the interviewer is actually grading. This page is the **template** for every other company page in this bible.

<span class="company-tag">Google</span> &nbsp; <span class="phase-status phase-inprogress">Phase 1 — sample company page</span>

---

## 📖 How this page is organized

Every company page in this bible follows the **same six-part shape**. Once you've read one, you've read them all.

1. **What interviewing here is like** — rounds, format, signal, vibe.
2. **What this company tests** — the specific skills they grade for.
3. **Common patterns** — which of the 20 patterns show up most often, with frequency hints.
4. **The 50 questions** — grouped by topic, with difficulty + pattern + a one-liner.
5. **Deep-dives** — 3 representative problems in mini-v3 format with Google-specific framing.
6. **Day-of tips** — last-minute reminders.

---

## 🏢 What interviewing at Google is like

### Rounds (typical SWE L3/L4 onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Phone screen** | 45 min | One coding problem. Usually medium. Shared doc, no IDE. |
| **Onsite — coding ×2** | 45 min each | Two coding rounds, one medium + one hard, on the whiteboard or shared doc. |
| **Onsite — coding ×1** | 45 min | "Big" problem — open-ended, often graph/DP/design-y. |
| **Onsite — system design** | 45 min | L4+ only. Whiteboard or Miro. |
| **Googleyness & leadership** | 45 min | Behavioral. STAR stories. |

L3 = new grad. L4 = ~2-5 yr exp. L5+ adds extra design + leadership rounds.

### What "the Google style" actually means

- **Talk through your approach before writing**. Silent coding loses points fast.
- **You will be interrupted with edge-case questions** while you're mid-code. This is intentional. They want to see you absorb feedback gracefully.
- **They love follow-ups.** Solve the problem in 20 min, expect a hard variant in the last 25 min.
- **Code quality is a signal**. Variable names, edge cases, function decomposition — they all get notes.
- **Time/space complexity is mandatory**. State it out loud, before you finish coding.

!!! tip "The Google interviewer mindset"
    Google interviewers are looking for **future colleagues**, not just problem solvers. They mentally ask: *"Could I work with this person on a hard, ambiguous problem for six months?"* That's the bar.

---

## 🎯 What Google tests

Mapping rounds → signals:

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Algorithmic depth** | Coding rounds | Solve hard medium / easy hard cleanly. Discuss tradeoffs between O(n log n) and O(n). |
| **Code quality** | All coding rounds | Readable names, edge cases at top, decomposed helpers, type hints. |
| **Communication** | Every round | Narrate your thought process. Acknowledge when you're stuck. Ask before assuming. |
| **Generalization** | The "big" coding round | Solve a smaller version, then scale your idea. Don't restart from scratch. |
| **Scale thinking** | System design (L4+) | Estimate QPS, storage, latency. Pick consistency vs availability deliberately. |
| **Googleyness** | Behavioral | Curiosity, low ego, bias to ship, comfort with ambiguity. |

---

## 🧩 Patterns that show up most often

Based on 5 years of public reports (Glassdoor, LeetCode discuss, Blind, ex-Googler blogs):

| Pattern | Frequency | Why Google likes it |
|---|---|---|
| **BFS / DFS on grid or graph** | ⭐⭐⭐⭐⭐ | Search, ranking, maps, knowledge-graph problems are core to Google products. |
| **DP (1D + 2D)** | ⭐⭐⭐⭐⭐ | Tests whether you can derive recurrence from first principles. |
| **Sliding window** | ⭐⭐⭐⭐ | Strings, logs, time-series — Google has all three. |
| **Heap / priority queue** | ⭐⭐⭐⭐ | Top-K, ranking, streaming — Search/Ads at heart. |
| **Two pointers** | ⭐⭐⭐⭐ | Their go-to "is the candidate beyond brute-force?" filter. |
| **Trie** | ⭐⭐⭐ | Autocomplete is literally a Google product. |
| **Binary search on answer** | ⭐⭐⭐ | The "monotonic-property" question type they love. |
| **Backtracking** | ⭐⭐⭐ | N-Queens, word search, combinations. |
| **Topological sort** | ⭐⭐⭐ | Build systems, dependency resolution. |
| **Union-find** | ⭐⭐ | Connected components in social/knowledge graphs. |
| **Segment tree / BIT** | ⭐⭐ | Rare, but appears in "big problem" round at L5+. |

---

## 📋 The 50 questions

Difficulty pill conventions:

- <span class="diff-easy">Easy</span> &nbsp; <span class="diff-medium">Medium</span> &nbsp; <span class="diff-hard">Hard</span>

Status:

- ✅ = full v3 solution exists in this bible (link given)
- 📝 = covered in mini-v3 below
- 🚧 = lands in Phase 8 (full v3 solutions for every Google problem)

### Arrays & strings (15)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Maximum Subarray (Kadane's) | <span class="diff-medium">Medium</span> | DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Product of Array Except Self | <span class="diff-medium">Medium</span> | Prefix/suffix | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 4 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 5 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 6 | 3Sum | <span class="diff-medium">Medium</span> | Sort + two ptrs | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | [📝](#deep-dive-1-longest-substring-without-repeating-characters) |
| 8 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash map + key | 🚧 |
| 9 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand-around-center | 🚧 |
| 10 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 11 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 12 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 13 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | Binary search on partition | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 14 | First Missing Positive | <span class="diff-hard">Hard</span> | Cyclic sort | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 15 | Longest Consecutive Sequence | <span class="diff-medium">Medium</span> | Hash set + start detect | [✅](../../02-data-structures/arrays/01-array-basics.md) |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 16 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer iteration | 🚧 |
| 17 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 18 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + doubly-linked list | [📝](#deep-dive-3-lru-cache) |

### Trees (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 19 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 20 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 21 | Lowest Common Ancestor (BST) | <span class="diff-medium">Medium</span> | DFS recursion | 🚧 |
| 22 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |
| 23 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | DFS post-order | 🚧 |
| 24 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | DFS post-order | 🚧 |
| 25 | Construct Tree from Preorder + Inorder | <span class="diff-medium">Medium</span> | Recursive partition | 🚧 |
| 26 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |

### Graphs (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Number of Islands | <span class="diff-medium">Medium</span> | Grid DFS/BFS | 🚧 |
| 28 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 29 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on graph of words | 🚧 |
| 30 | Clone Graph | <span class="diff-medium">Medium</span> | DFS + hash | 🚧 |
| 31 | Pacific Atlantic Water Flow | <span class="diff-medium">Medium</span> | Multi-source BFS | 🚧 |
| 32 | Alien Dictionary | <span class="diff-hard">Hard</span> | Topo sort | 🚧 |

### Dynamic programming (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 34 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | Patience sort / DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 35 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | [📝](#deep-dive-2-word-break) |
| 36 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 37 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 38 | Regular Expression Matching | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 39 | Decode Ways | <span class="diff-medium">Medium</span> | 1D DP | 🚧 |
| 40 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |

### Heap & priority queue (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket sort | 🚧 |
| 42 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |
| 43 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 44 | N-Queens | <span class="diff-hard">Hard</span> | Backtracking + diag sets | 🚧 |
| 45 | Word Search | <span class="diff-medium">Medium</span> | Grid DFS + backtrack | 🚧 |
| 46 | Combination Sum | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |

### Design (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 47 | Insert Delete GetRandom O(1) | <span class="diff-medium">Medium</span> | Hash + array swap | 🚧 |
| 48 | Design Twitter | <span class="diff-medium">Medium</span> | Heap + hash + linked list | 🚧 |

### Math & misc (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 49 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |
| 50 | Reverse Integer | <span class="diff-medium">Medium</span> | Math + overflow | 🚧 |

---

## 🔬 Deep-dives — 3 Google-style walkthroughs

These three are picked because:

- They're each asked at Google **at least once a quarter** (per public reports).
- They each demonstrate a **different signal** Google grades on (sliding window mastery, DP intuition, design + data-structure composition).
- They each have a **classic Google follow-up** that turns the problem into a fresh challenge.

Format: shorter than the full chapter v3 — just thinking process, optimal solution, dry run, complexity, and a Google-specific follow-up.

---

### Deep-dive 1: Longest substring without repeating characters

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Meta</span>

> Given a string `s`, find the length of the longest substring without repeating characters.

#### 📖 Story mode

Imagine reading a book where every word can only appear once in your "current sentence." If you hit a repeat, you have to start a new sentence from just *after* the previous occurrence of that word. What's the longest sentence you can make?

Example: `"abcabcbb"` → longest is `"abc"` (length 3). After the 4th char (`a`), we'd repeat, so we restart.

#### 🧠 Thinking process

- **Brute force**: For every pair `(i, j)`, check if `s[i:j+1]` has all unique chars. O(n³).
- **Better brute**: For each `i`, walk `j` forward until duplicate. Reset on duplicate. Still O(n²) worst case.
- **Insight**: When we hit a duplicate at `s[j]`, we don't have to restart from `i+1`. We can jump `i` directly past the *previous* occurrence of `s[j]`. That's a sliding window with a hash map.

#### 🐍 Optimal solution

```python
def length_of_longest_substring(s: str) -> int:
    """Length of the longest substring with all unique characters."""
    last_seen: dict[str, int] = {}   # char -> most recent index
    left = 0
    best = 0

    for right, ch in enumerate(s):
        # If we've seen ch inside the current window, jump left past it.
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1

        last_seen[ch] = right
        best = max(best, right - left + 1)

    return best
```

**Why this is O(n)**: each char is read once (`right` advances), and `left` only ever moves forward. The hash map gives O(1) lookup.

#### 🔍 Dry run on `"abcabcbb"`

| right | ch | last_seen[ch] ≥ left? | left | last_seen | window | best |
|---|---|---|---|---|---|---|
| 0 | a | no | 0 | {a:0} | "a" | 1 |
| 1 | b | no | 0 | {a:0,b:1} | "ab" | 2 |
| 2 | c | no | 0 | {a:0,b:1,c:2} | "abc" | 3 |
| 3 | a | yes (0≥0) | 1 | {a:3,b:1,c:2} | "bca" | 3 |
| 4 | b | yes (1≥1) | 2 | {a:3,b:4,c:2} | "cab" | 3 |
| 5 | c | yes (2≥2) | 3 | {a:3,b:4,c:5} | "abc" | 3 |
| 6 | b | yes (4≥3) | 5 | {a:3,b:6,c:5} | "cb" | 3 |
| 7 | b | yes (6≥5) | 7 | {a:3,b:7,c:5} | "b" | 3 |

Answer: 3.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Optimal** | O(n) | O(min(n, alphabet)) |

#### 🔄 Google's classic follow-up

??? question "What if the string is a stream — chars arrive one at a time, can't be re-read?"
    The same algorithm works *as-is*. The window only ever moves forward, so we never need to look back. Just process each char on arrival.

??? question "What if we allow up to K repeating characters?"
    Generalize to "longest substring with at most K duplicates of any char." Maintain a count map; expand right; while any count > K, shrink left. This is the **template for all 'longest substring with property X'** problems.

??? question "What if the alphabet is huge (e.g. unicode)?"
    Hash map still works (O(min(n, alphabet)) space). If memory is a concern, use a fixed-size array indexed by codepoint and check bounds.

#### 🐛 Common bugs in this exact problem

- Forgetting the `last_seen[ch] >= left` check — without it, an old (out-of-window) duplicate moves `left` *backward*, breaking the invariant.
- Using `set` instead of `dict` and removing chars one by one — works, but turns O(n) into amortized O(n) with worse constants and harder reasoning.

---

### Deep-dive 2: Word break

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Apple</span>

> Given a string `s` and a dictionary `word_dict`, return `True` if `s` can be segmented into a space-separated sequence of dictionary words.

#### 📖 Story mode

You have a long string with no spaces (`"applepenapple"`) and a dictionary (`["apple", "pen"]`). Can you cut the string into pieces so every piece is in the dictionary? Yes — `apple | pen | apple`.

#### 🧠 Thinking process

- **Brute force**: try every split. For each prefix that's a valid word, recurse on the rest. O(2ⁿ) without memoization.
- **Insight**: many sub-strings are checked repeatedly. Memoize: "can `s[i:]` be segmented?" — a function of `i` only.
- **Bottom-up DP**: `dp[i]` = "can `s[:i]` be segmented?" `dp[0] = True`. For each `i`, check every `j < i` where `dp[j]` is true *and* `s[j:i]` is in the dictionary.

#### 🐍 Optimal solution

```python
def word_break(s: str, word_dict: list[str]) -> bool:
    """Can s be split into a sequence of words from word_dict?"""
    words = set(word_dict)                       # O(1) lookup
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True                                 # empty prefix is always segmentable

    max_word_len = max((len(w) for w in words), default=0)

    for i in range(1, n + 1):
        # Only look back as far as the longest word in the dict
        for j in range(max(0, i - max_word_len), i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break

    return dp[n]
```

**Two ideas working together**: hash set for O(1) lookups, plus the `max_word_len` clamp so the inner loop is bounded by the longest word, not by `i`.

#### 🔍 Dry run on `s = "applepen"`, `dict = ["apple", "pen"]`

`max_word_len = 5`. dp = [T, F, F, F, F, F, F, F, F]

| i | range j | check | dp[i] |
|---|---|---|---|
| 1 | 0 | dp[0]&"a"∈dict → no | F |
| 2 | 0..1 | "ap"∉, ... | F |
| 3 | 0..2 | "app"∉, ... | F |
| 4 | 0..3 | "appl"∉, ... | F |
| 5 | 0..4 | dp[0]&"apple"∈dict → **yes** | **T** |
| 6 | 1..5 | dp[5]&"p"∉, ... | F |
| 7 | 2..6 | dp[5]&"pe"∉, ... | F |
| 8 | 3..7 | dp[5]&"pen"∈dict → **yes** | **T** |

Answer: True.

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **DP** | O(n · L) where L = max word length | O(n + sum of word lengths) |

#### 🔄 Google's classic follow-up

??? question "Return the actual segmentation, not just True/False."
    Track `parent[i] = j` that made `dp[i]` true. Walk parents back to reconstruct. (Or DFS+memo from the start, returning the path.)

??? question "Return ALL possible segmentations."
    Word Break II. Now you need DFS + memo where memo maps index → list of suffix-segmentations. O(2ⁿ) worst case but with heavy pruning.

??? question "What if the dictionary is huge (10M words) and the string is short?"
    Hash set still O(1) per lookup. The bottleneck shifts to memory — consider a Trie if many words share prefixes.

??? question "What if the dictionary is small (~50 words) but `s` is huge (10MB)?"
    Aho-Corasick automaton: build it from the dict in O(sum of word lens), then sweep `s` once in O(n).

#### 🐛 Common bugs

- Forgetting `dp[0] = True` — every other entry will be False.
- Using `s[j:i]` correctness: it's the slice from index j (inclusive) to i (exclusive), matching the prefix `dp[i]` represents.
- Not capping inner loop by `max_word_len` — passes for small inputs, TLEs on Google's harder test cases.

---

### Deep-dive 3: LRU Cache

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">Microsoft</span>

> Design a data structure for a Least-Recently-Used cache supporting `get(key)` and `put(key, value)` in O(1).

#### 📖 Story mode

Your phone shows the 6 most recent apps. Open one — it jumps to the front. Open a new one when 6 are already shown — the oldest gets pushed off. That's LRU.

#### 🧠 Thinking process

- **Naive**: list + linear search. `get` is O(n).
- **Hash map alone**: O(1) get/put but no notion of "least recent" — no order.
- **Insight**: combine two structures. Hash map for O(1) lookup → node. Doubly-linked list for O(1) move-to-front and O(1) drop-from-tail.

The hash map's *value* is a **pointer into the linked list**. That's the trick.

#### 🐍 Optimal solution

```python
class _Node:
    __slots__ = ("key", "val", "prev", "next")
    def __init__(self, key: int, val: int) -> None:
        self.key, self.val = key, val
        self.prev: _Node | None = None
        self.next: _Node | None = None


class LRUCache:
    """Hash map + doubly-linked list. All ops O(1)."""

    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.map: dict[int, _Node] = {}
        # Sentinel head/tail simplify edge cases (no None checks).
        self.head = _Node(0, 0)
        self.tail = _Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: _Node) -> None:
        node.prev.next, node.next.prev = node.next, node.prev

    def _add_to_front(self, node: _Node) -> None:
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.map:
            return -1
        node = self.map[key]
        self._remove(node)
        self._add_to_front(node)         # most recently used
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.map:
            self._remove(self.map[key])
        node = _Node(key, value)
        self._add_to_front(node)
        self.map[key] = node
        if len(self.map) > self.cap:
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]
```

**Why sentinels?** They mean every real node has both a `prev` and a `next`. No `if node.prev is None` checks.

#### 🔍 Dry run

`cap=2`, ops: `put(1,1) put(2,2) get(1) put(3,3) get(2)`

| op | map | list (head → tail) | result |
|---|---|---|---|
| put(1,1) | {1} | 1 | — |
| put(2,2) | {1,2} | 2,1 | — |
| get(1) | {1,2} | 1,2 | 1 |
| put(3,3) | {1,3} | 3,1 (evicted 2) | — |
| get(2) | {1,3} | 3,1 | -1 |

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| `get`, `put` | O(1) | — |
| Total | — | O(capacity) |

#### 🔄 Google's classic follow-up

??? question "Make it thread-safe."
    Wrap every public op in a mutex. For a fully concurrent LRU you need finer-grained locking (segmenting by hash bucket) or lock-free designs — explain the tradeoffs.

??? question "Add TTL (time-to-live) per key."
    On every op, lazily evict expired entries from the tail side. Or use a second priority structure (heap) keyed by expiry.

??? question "Replace LRU with LFU (least frequently used)."
    Now you need to track frequency per key and break ties by recency. Standard answer: hash map of key → node, plus hash map of freq → DLL of nodes-with-that-freq, plus a `min_freq` integer. Tougher; this is its own LeetCode hard.

??? question "Why not Python's `collections.OrderedDict`?"
    Totally valid in interviews — say "in production I'd use `OrderedDict`'s `move_to_end` for one-line LRU. But Google probably wants me to show I know what's happening underneath, so I'll implement the DLL." Best of both worlds.

#### 🐛 Common bugs

- Forgetting to update the hash map on eviction — the next `get` returns a stale node.
- Not handling the "key already exists" case in `put` — leads to two list nodes for one key.
- Off-by-one on capacity check (`>=` vs `>`) — drops the just-inserted entry.

---

## 🗓️ Day-of tips for a Google interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours** the night before. No coding past 8 PM.
    2. **Re-read** *only* the [pattern cheat-sheet](../../04-patterns/index.md), not new problems. Your brain consolidates patterns, not last-minute facts.
    3. **One easy warm-up** the morning of — Two Sum, Reverse Linked List. Get into the rhythm.
    4. **Test your video / mic / IDE** 30 min before. Murphy's law applies.
    5. **Have water + a notepad**. Whiteboard problems benefit from sketching arrays/trees on paper.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60 seconds** | Restate the problem in your own words. Ask 2 clarifying questions ("what's the input range?", "can the input be empty?"). |
| **Pre-coding (3-5 min)** | State your approach. State its complexity. **Then** ask "shall I code it?" |
| **Coding (15-20 min)** | Narrate. Type clean variable names. Handle edge cases at the top of the function. |
| **Testing (5 min)** | Walk through one example by hand. Then walk through one edge case. Don't ask the interviewer to test for you. |
| **Follow-up question** | If they ask "how would you handle X?", *think for 5 seconds before answering*. Silence is fine here. |

### Red flags they'll note

- Coding silently for 10+ minutes without narration.
- Producing buggy code and not catching it before saying "done."
- Defending a wrong answer when the interviewer hints at a bug.
- Skipping edge-case handling and saying "I'd add that in real code."
- Not knowing your own time/space complexity.

### Green flags they'll note

- Asking smart clarifying questions before coding.
- Saying "I don't know" once and pivoting to "but here's what I'd try…"
- Spotting your own bug while testing and fixing it cleanly.
- Refactoring mid-interview when a function gets long.
- Mentioning a real-world variant: "in production, I'd add a cache here because…"

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above (arrays → strings → trees → graphs → DP → other). Each topic compounds.
- **For each problem** you don't recognize, hit the [pattern that drives it](../../04-patterns/index.md) before grinding more instances.
- **Cross-check** with [Common across all companies — Arrays](../../12-common-across-all-companies/02-arrays-common.md). The overlap is real — anything on both lists is **must-do**.
- **System design** at L4+ has its own page. Start with [URL Shortener](../../08-system-design/index.md).

> When this page is filled out for every other company, the structure stays exactly the same — the table contents, deep-dive picks, and "interview style" section change, but the six-part shape doesn't.
