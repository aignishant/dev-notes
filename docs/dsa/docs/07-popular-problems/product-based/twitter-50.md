# Twitter / X — 50 most-asked questions

> The 50 problems Twitter / X (timeline, search, ads) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Twitter / X</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Twitter / X is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + culture. |
| **Tech phone screen** | 60 min | Coding (medium). |
| **Onsite — coding ×2** | 60 min each | Algorithms, often timeline / feed flavored. |
| **Onsite — system design** | 60 min | "Design Twitter" is the canonical question — they'll riff on it. |
| **Onsite — bar raiser** | 45 min | Cross-team senior IC. |
| **Onsite — manager** | 45 min | Behavioral. |

**Twitter style**: heavy timeline / fanout / feed-ranking flavor. Distributed systems thinking required even in coding rounds. Faster pace post-acquisition; cuts in late-2022 changed bar but interview shape persists.

---

## 🎯 What Twitter / X tests

| Signal | Where | How to show |
|---|---|---|
| Distributed systems instinct | Coding + design | Mention sharding, replication, eventual consistency. |
| Hot-key handling | Design | Celebrity follower fanout. |
| Heap / top-K fluency | Coding | Trending, top tweets per hour. |
| Tradeoff articulation | Every round | Don't just answer — name what you'd give up. |

---

## 🧩 Patterns Twitter / X loves

| Pattern | Frequency | Why |
|---|---|---|
| **Heap top-K** | ⭐⭐⭐⭐⭐ | Trending, top retweets. |
| **Hash + sliding window** | ⭐⭐⭐⭐ | Rate limit, dedup. |
| **K-way merge** | ⭐⭐⭐⭐ | Merge timelines from N follows. |
| **Graph BFS** | ⭐⭐⭐⭐ | Follower graph traversal. |
| **Design** | ⭐⭐⭐⭐⭐ | Design Twitter is ~50% of design rounds. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash | 🚧 |
| 4 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 5 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 6 | Container With Most Water | <span class="diff-medium">Medium</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Valid Anagram | <span class="diff-easy">Easy</span> | Hash count | 🚧 |
| 8 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand center | 🚧 |
| 9 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 10 | Encode and Decode Strings | <span class="diff-medium">Medium</span> | Length-prefix | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 15 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 16 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | Pre-order | 🚧 |
| 17 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 18 | Binary Tree Right Side View | <span class="diff-medium">Medium</span> | BFS last | 🚧 |
| 19 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | Post-order | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 20 | Number of Islands | <span class="diff-medium">Medium</span> | DFS | 🚧 |
| 21 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 22 | Word Ladder | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 23 | Friends of Friends | <span class="diff-medium">Medium</span> | BFS depth-2 | 📝 |
| 24 | Trending Hashtags | <span class="diff-medium">Medium</span> | Heap on stream | 📝 |

### Heap / Top-K (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 25 | Top K Frequent Words | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 26 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 27 | Kth Largest in Stream | <span class="diff-easy">Easy</span> | Min-heap K | 🚧 |
| 28 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 29 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 🚧 |
| 30 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 31 | K Closest Points to Origin | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 32 | Top K Hashtags Last Hour | <span class="diff-hard">Hard</span> | Heap + sliding window | 📝 |

### Backtracking (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Permutations | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 34 | Word Search | <span class="diff-medium">Medium</span> | DFS + visited | 🚧 |

### DP (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 35 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 36 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 37 | Word Break | <span class="diff-medium">Medium</span> | DP + dict | 🚧 |
| 38 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP | 🚧 |

### Search & sort (2)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 39 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 40 | Sort Tweets by Time + ID | <span class="diff-easy">Easy</span> | Compound key sort | 🚧 |

### Design (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Design Twitter | <span class="diff-medium">Medium</span> | Heap + fanout | 📝 |
| 42 | Design Trending Hashtags | <span class="diff-hard">Hard</span> | Heap + decay | 🚧 |
| 43 | Design Rate Limiter | <span class="diff-medium">Medium</span> | Token bucket | 🚧 |
| 44 | Design Tweet Storage | <span class="diff-hard">Hard</span> | Snowflake ID + shard | 🚧 |
| 45 | Design Live Search Suggestions | <span class="diff-hard">Hard</span> | Trie + popularity | 🚧 |
| 46 | Design Direct Message | <span class="diff-medium">Medium</span> | Pub/sub | 🚧 |
| 47 | Design Notification Service | <span class="diff-hard">Hard</span> | Fanout queue | 🚧 |
| 48 | Design Hot Key Detection | <span class="diff-hard">Hard</span> | Count-Min Sketch | 🚧 |
| 49 | Design Tweet Dedup | <span class="diff-medium">Medium</span> | Bloom filter | 🚧 |
| 50 | Design Spam Filter | <span class="diff-medium">Medium</span> | Hash + ML signals | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Design Twitter (LC 355)

??? question "Story: implement `postTweet`, `getNewsFeed` (10 most recent from self+follows), `follow`, `unfollow`."

    Two strategies: **fanout-on-write** (when you tweet, push to all followers' inboxes) vs **fanout-on-read** (build the feed on demand by merging follows). Real Twitter uses hybrid; the LC version uses fanout-on-read with a heap K-way merge.

```python
import heapq
from collections import defaultdict

class Twitter:
    def __init__(self):
        self.time = 0
        self.tweets: dict[int, list[tuple[int, int]]] = defaultdict(list)  # user → [(time, tweet_id)]
        self.follows: dict[int, set[int]] = defaultdict(set)

    def postTweet(self, user_id: int, tweet_id: int) -> None:
        self.time += 1
        self.tweets[user_id].append((self.time, tweet_id))

    def getNewsFeed(self, user_id: int) -> list[int]:
        users = self.follows[user_id] | {user_id}
        # max-heap on time across each user's tweets
        heap: list[tuple[int, int, int, int]] = []  # (-time, tweet_id, user, idx)
        for u in users:
            if self.tweets[u]:
                idx = len(self.tweets[u]) - 1
                t, tid = self.tweets[u][idx]
                heapq.heappush(heap, (-t, tid, u, idx))
        out: list[int] = []
        while heap and len(out) < 10:
            _, tid, u, idx = heapq.heappop(heap)
            out.append(tid)
            if idx > 0:
                t2, tid2 = self.tweets[u][idx - 1]
                heapq.heappush(heap, (-t2, tid2, u, idx - 1))
        return out

    def follow(self, follower: int, followee: int) -> None:
        if follower != followee:
            self.follows[follower].add(followee)

    def unfollow(self, follower: int, followee: int) -> None:
        self.follows[follower].discard(followee)
```

??? abstract "Complexity"

    `postTweet` O(1). `getNewsFeed` O(F + 10·log F) where F is number of follows.

??? tip "Twitter follow-up: 'what about a celebrity with 100M followers?'"

    Pure fanout-on-write would cost 100M writes per tweet — kills disk IO. Hybrid: regular users get fanout-on-write to followers' inboxes; celebrities skip the fanout, and at read time, your timeline merges *your inbox* with *fresh tweets from celebrities you follow*.

---

### Deep-dive 2 — Trending Hashtags (sliding hour)

??? question "Story: stream of hashtag events. Return top-10 hashtags from the last hour, updated continuously."

    Combine sliding window (drop events older than 1 hr) with a count-frequency map and a heap.

```python
from collections import deque, defaultdict
import heapq
import time

class Trending:
    def __init__(self, window_sec: int = 3600):
        self.window = window_sec
        self.events: deque[tuple[float, str]] = deque()
        self.count: dict[str, int] = defaultdict(int)

    def add(self, hashtag: str, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        self.events.append((now, hashtag))
        self.count[hashtag] += 1
        self._evict(now)

    def _evict(self, now: float) -> None:
        while self.events and now - self.events[0][0] > self.window:
            _, tag = self.events.popleft()
            self.count[tag] -= 1
            if self.count[tag] == 0:
                del self.count[tag]

    def top(self, k: int = 10) -> list[tuple[str, int]]:
        return heapq.nlargest(k, self.count.items(), key=lambda kv: kv[1])
```

??? abstract "Complexity"

    `add` amortised O(1). `top` O(N) for N distinct tags, fine for the typical N.

??? tip "Twitter follow-up: 'we ingest 500k events/sec — your map is too big'"

    Approximate top-K with a Count-Min Sketch + min-heap of K candidates. Trade exact counts for O(width × depth) memory regardless of stream size.

---

### Deep-dive 3 — Hot Key Detection (Count-Min Sketch)

??? question "Story: detect tweets going viral in real time. Stream is too big to count exactly."

    Count-Min Sketch: D hash functions × W counter columns. To increment a key, increment `cm[i][h_i(key) % W]` for each i. To estimate, take the min across rows. Overestimates but never under.

```python
import hashlib

class CountMinSketch:
    def __init__(self, depth: int = 5, width: int = 1 << 16):
        self.depth = depth
        self.width = width
        self.table = [[0] * width for _ in range(depth)]

    def _h(self, i: int, key: str) -> int:
        # cheap independent hashes via a salt
        h = hashlib.md5(f"{i}:{key}".encode()).digest()
        return int.from_bytes(h[:4], "big") % self.width

    def add(self, key: str, count: int = 1) -> None:
        for i in range(self.depth):
            self.table[i][self._h(i, key)] += count

    def estimate(self, key: str) -> int:
        return min(self.table[i][self._h(i, key)] for i in range(self.depth))
```

??? abstract "Complexity"

    O(D) per `add` / `estimate`. Memory O(D · W).

??? tip "Twitter follow-up: 'how do you know which keys are hot if you only have estimates?'"

    Pair the sketch with a top-K min-heap. On every increment, query the estimate; if it beats the heap's current min, push it (use the key as an existence guard to avoid duplicates).

---

## 🛡️ Day-of tips

- **"Design Twitter" is almost guaranteed**. Have one fanout-on-read story, one fanout-on-write story, and the hybrid for celebrities.
- **Think in distributed terms**: every coding answer should at least mention "this would shard by user_id".
- **Numbers matter**: know order-of-magnitude — 500M tweets/day, ~5800/sec average, 10× spike during events.
- **Post-acquisition reality**: cycle is faster, fewer rounds, fewer interviewers. Be sharper, not slower.
