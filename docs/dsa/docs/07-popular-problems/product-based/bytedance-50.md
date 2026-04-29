# ByteDance — 50 most-asked questions

> The 50 problems ByteDance (TikTok, Douyin, CapCut, Lark) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">ByteDance</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at ByteDance is like

| Round | Length | Focus |
|---|---|---|
| **OA / OnlineCoding** | 90 min | 2-3 medium / hard problems on a custom platform. |
| **Phone screen ×2** | 60 min each | Hard algorithms, often LeetCode-Hard verbatim. |
| **Onsite — coding ×2** | 60 min each | More algorithms; speed expected. |
| **Onsite — system design** | 60 min | Recommendation / video / messaging flavored. |
| **HR / culture** | 30-45 min | "ByteStyle" values. |

**ByteDance style**: heaviest LeetCode load on the planet. Volume + speed > elegance. Hard problems are normal; expect 2 hards in a 60-min round. Pace is China-tech intense. ML engineering questions appear if you're targeting recommendation roles.

---

## 🎯 What ByteDance tests

| Signal | Where | How to show |
|---|---|---|
| LC fluency | Every coding round | Pattern recognition in <2 min. |
| Speed | All | Code, not whiteboard slow-walk. |
| ML systems thinking | Some senior roles | Embedding stores, online learning. |
| Scale | Design | TikTok = 1.5B DAU, recommend at that scale. |

---

## 🧩 Patterns ByteDance loves

| Pattern | Frequency | Why |
|---|---|---|
| **Hash + sliding window** | ⭐⭐⭐⭐⭐ | Volume of medium / hard string problems. |
| **DP** | ⭐⭐⭐⭐⭐ | Their bias is much heavier than US-FAANG. |
| **Heap top-K** | ⭐⭐⭐⭐⭐ | Trending feeds. |
| **Trie + DFS** | ⭐⭐⭐⭐ | Auto-complete, hashtag search. |
| **Segment tree / BIT** | ⭐⭐⭐⭐ | Range stats over user activity — appears in onsite. |
| **Graph BFS / DFS** | ⭐⭐⭐⭐ | Social graph. |

---

## 📋 The 50 questions

### Arrays & strings (12)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 4 | Longest Repeating Character Replacement | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 5 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 6 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 🚧 |
| 7 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 8 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix + hash | 🚧 |
| 9 | Longest Palindromic Substring | <span class="diff-medium">Medium</span> | Expand center | 🚧 |
| 10 | Regex Match | <span class="diff-hard">Hard</span> | DP | 🚧 |
| 11 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 12 | First Missing Positive | <span class="diff-hard">Hard</span> | Cyclic sort | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 13 | Reverse Nodes in k-Group | <span class="diff-hard">Hard</span> | Iterative reverse | 🚧 |
| 14 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 15 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 16 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | Post-order | 🚧 |
| 17 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 18 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 19 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 20 | Recover BST | <span class="diff-medium">Medium</span> | Inorder + swap | 🚧 |
| 21 | Binary Tree Cameras | <span class="diff-hard">Hard</span> | Greedy DFS | 🚧 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 22 | Number of Islands | <span class="diff-medium">Medium</span> | DFS / BFS | 🚧 |
| 23 | Course Schedule II | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 24 | Word Ladder | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 25 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |
| 26 | Critical Connections (Tarjan) | <span class="diff-hard">Hard</span> | Bridge finding | 📝 |

### Heap / Top-K (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket | [✅](../../04-patterns/12-top-k-elements.md) |
| 28 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 29 | Kth Largest in Stream | <span class="diff-easy">Easy</span> | Min-heap K | 🚧 |
| 30 | Top K Trending Videos | <span class="diff-hard">Hard</span> | Heap + decay | 📝 |
| 31 | Schedule Tasks (Cooldown) | <span class="diff-medium">Medium</span> | Heap + queue | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 32 | Word Search II | <span class="diff-hard">Hard</span> | Trie + DFS | 🚧 |
| 33 | Permutations II | <span class="diff-medium">Medium</span> | Backtrack + dedup | 🚧 |
| 34 | N-Queens | <span class="diff-hard">Hard</span> | Backtrack + bitmask | 🚧 |

### DP (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 35 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 36 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 37 | Word Break II | <span class="diff-hard">Hard</span> | DP + trie | 🚧 |
| 38 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |
| 39 | Decode Ways | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 40 | Burst Balloons | <span class="diff-hard">Hard</span> | Interval DP | 🚧 |
| 41 | Maximum Product Subarray | <span class="diff-medium">Medium</span> | DP | 🚧 |
| 42 | Best Time to Buy / Sell Stock IV | <span class="diff-hard">Hard</span> | DP | 🚧 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 43 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 44 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | BS partition | 🚧 |
| 45 | Sort List | <span class="diff-medium">Medium</span> | Merge sort | 🚧 |

### Design (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 46 | Design TikTok Feed | <span class="diff-hard">Hard</span> | Recommend + cache | 📝 |
| 47 | Design Live Stream | <span class="diff-hard">Hard</span> | HLS + CDN | 🚧 |
| 48 | Design Comment System | <span class="diff-hard">Hard</span> | Hierarchical store | 🚧 |
| 49 | Design Hot Hashtag Detection | <span class="diff-hard">Hard</span> | Sketch + heap | 🚧 |
| 50 | Design Video Dedup | <span class="diff-hard">Hard</span> | Perceptual hash | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Top K Trending Videos (sliding window with decay)

??? question "Story: rank videos by score. Score decays with age — a video that got 1M views 24h ago should fall behind a fresh one with 100k views."

    Score = sum of `view × exp(-λ · age)`. Maintain bucket counters per minute and a heap over current scores.

```python
import heapq
import math
from collections import defaultdict

class TrendingVideos:
    def __init__(self, decay_per_hour: float = 1.0):
        self.lam = decay_per_hour / 3600.0
        self.last_view: dict[int, float] = {}
        self.score: dict[int, float] = defaultdict(float)

    def view(self, video_id: int, now: float) -> None:
        # decay existing score forward to `now`
        if video_id in self.last_view:
            dt = now - self.last_view[video_id]
            self.score[video_id] *= math.exp(-self.lam * dt)
        self.score[video_id] += 1.0
        self.last_view[video_id] = now

    def top_k(self, k: int, now: float) -> list[tuple[int, float]]:
        decayed = []
        for vid, s in self.score.items():
            dt = now - self.last_view[vid]
            decayed.append((vid, s * math.exp(-self.lam * dt)))
        return heapq.nlargest(k, decayed, key=lambda x: x[1])
```

??? abstract "Complexity"

    `view` O(1). `top_k` O(N log K) for N distinct videos.

??? tip "ByteDance follow-up: 'N is 1B. Your `top_k` is too slow.'"

    Shard by `video_id`, compute per-shard top-K decayed in parallel, then merge. Use a stale top-K cache (refreshed every minute) for the hot path.

---

### Deep-dive 2 — Critical Connections (LC 1192)

??? question "Story: in a service mesh, find edges whose removal would partition the graph (single points of failure)."

    Tarjan's bridge-finding algorithm. DFS with `disc[v]` (discovery time) and `low[v]` (lowest reachable). Edge `(u, v)` is a bridge iff `low[v] > disc[u]`.

```python
def critical_connections(n: int, connections: list[list[int]]) -> list[list[int]]:
    graph: dict[int, list[int]] = {i: [] for i in range(n)}
    for u, v in connections:
        graph[u].append(v)
        graph[v].append(u)

    disc = [-1] * n
    low = [0] * n
    bridges: list[list[int]] = []
    timer = [0]

    def dfs(u: int, parent: int) -> None:
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        for v in graph[u]:
            if v == parent:
                continue
            if disc[v] == -1:
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:
                    bridges.append([u, v])
            else:
                low[u] = min(low[u], disc[v])

    for i in range(n):
        if disc[i] == -1:
            dfs(i, -1)
    return bridges
```

??? abstract "Complexity"

    O(V + E) time and space.

??? tip "ByteDance follow-up: 'now do articulation points'"

    A vertex `u` is an articulation point if (a) it's the root of DFS with ≥2 children, or (b) it has a child `v` with `low[v] >= disc[u]`. Same DFS, slightly different test.

---

### Deep-dive 3 — TikTok Feed Recommendation

??? question "Story: every refresh, return 10 videos for the user. Mix recall (candidate pool) + ranking + diversity."

    Three-stage pipeline: **recall** (collaborative filtering, content tags, follow graph) → **rank** (model score) → **rerank for diversity** (penalise repeat-creator).

```python
from dataclasses import dataclass
from collections import defaultdict
import heapq

@dataclass
class Candidate:
    video_id: int
    creator_id: int
    score: float

def recommend(user_id: int, recall_pool: list[Candidate], k: int = 10) -> list[Candidate]:
    # Stage 1: recall_pool already gathered (size ~1000)
    # Stage 2: rank by score (already computed by upstream model)
    ranked = sorted(recall_pool, key=lambda c: -c.score)

    # Stage 3: diversity rerank — at most 2 from same creator in top-k
    out: list[Candidate] = []
    creator_count: dict[int, int] = defaultdict(int)
    for cand in ranked:
        if creator_count[cand.creator_id] >= 2:
            continue
        out.append(cand)
        creator_count[cand.creator_id] += 1
        if len(out) == k:
            break
    return out
```

??? abstract "Complexity"

    O(N log N) sort dominates. In production, recall is the bottleneck (~ms across multiple stores).

??? tip "ByteDance follow-up: 'how do you avoid the same video appearing twice in 5 minutes?'"

    Per-user "seen" Bloom filter with TTL of 5 min. Filter recall candidates against it. Bloom keeps memory bounded across 1.5B users.

---

## 🛡️ Day-of tips

- **Practice hards**: ByteDance is the only company where you should drill LC Hards 1:1 with mediums.
- **Speed kills**: 60 min often means TWO hards. If you spend 40 on the first, you've failed.
- **State patterns out loud**: "I see this is a sliding-window minimum window problem" earns points fast.
- **For TikTok roles**: read about embeddings + ANN (HNSW, FAISS) at least at a vocabulary level.
