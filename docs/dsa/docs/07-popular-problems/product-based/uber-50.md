# Uber — 50 most-asked questions

> The 50 problems Uber (Rides, Eats, Freight) has asked most often, with the patterns behind them and what the interviewer is grading. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Uber</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 📖 How this page is organized

1. **What interviewing here is like**.
2. **What this company tests**.
3. **Common patterns**.
4. **The 50 questions**.
5. **Deep-dives** — 3 representative problems.
6. **Day-of tips**.

---

## 🏢 What interviewing at Uber is like

### Rounds (typical SWE II/III onsite — 2026)

| Round | Length | Focus |
|---|---|---|
| **Online assessment** | 90 min | 2 medium coding problems. CodeSignal. |
| **Phone screen** | 60 min | One coding problem. |
| **Onsite — coding ×2** | 60 min each | Algorithms + data structures. |
| **Onsite — system design** | 60 min | Often "design Uber" or a sub-system (matching, ETAs, surge pricing). |
| **Onsite — domain / depth** | 60 min | Distributed systems, geospatial, or backend deep-dive. |
| **Onsite — bar raiser / culture** | 60 min | Behavioral + Uber values ("Build with heart, do the right thing"). |

### What "the Uber style" actually means

- **Geospatial flavor everywhere.** Even abstract problems get re-skinned: "find the K closest *drivers*", "match riders to drivers in a grid", "ETA prediction".
- **Distributed-systems thinking matters.** Uber problems often have an implicit "now make this work across data centers" follow-up.
- **They love graph problems.** The road network is a graph; the rider-driver bipartite matching is a graph; surge zones are a graph.
- **OOP design is fair game.** "Design Uber's matching service" — class hierarchy, interfaces, pub-sub.
- **Surge of LeetCode mediums.** Less hard-grinding than Google; expect 2-3 mediums in 60 min in some rounds.

!!! tip "The Uber interviewer mindset"
    Uber interviewers ask: *"Could this person own a P0 in production?"* — they have lots of P0s. Expect questions about how you'd debug, alert, and rollback.

---

## 🎯 What Uber tests

| Signal | Where they grade it | How to show it |
|---|---|---|
| **Coding fluency** | Coding rounds | Speed + correctness. Mediums in 25 min. |
| **Distributed thinking** | Design rounds | Sharding, replication, consistency, geo-sharding. |
| **Geospatial intuition** | Some coding + design | Quadtrees, geohashes, R-trees, haversine distance. |
| **Production seniority** | Domain round | Real on-call stories, debugging at scale. |
| **Cross-functional** | Bar raiser | Working with PMs, ops teams, data scientists. |

---

## 🧩 Patterns that show up most often

| Pattern | Frequency | Why Uber likes it |
|---|---|---|
| **Graph BFS / DFS / Dijkstra** | ⭐⭐⭐⭐⭐ | Roads, ETAs, shortest paths. |
| **Heap / Top-K** | ⭐⭐⭐⭐⭐ | K-closest drivers, ride-matching. |
| **Hash map composition** | ⭐⭐⭐⭐ | Standard medium filter. |
| **Sliding window** | ⭐⭐⭐⭐ | Time-series, fare calculation windows. |
| **Trees** | ⭐⭐⭐ | Quadtrees for geospatial; binary trees as warm-ups. |
| **DP** | ⭐⭐⭐ | Less than Google. Surge-pricing optimization sometimes. |
| **Backtracking** | ⭐⭐⭐ | Combinations, route enumeration. |
| **OOP design** | ⭐⭐⭐ | "Design X" rounds. |
| **Concurrency** | ⭐⭐⭐ | Locks, atomic counters in surge / pricing rounds. |

---

## 📋 The 50 questions

Status: ✅ = full v3 in this bible &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash map | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 3 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 4 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 5 | Meeting Rooms II | <span class="diff-medium">Medium</span> | Min-heap | 🚧 |
| 6 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 8 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 9 | Best Time to Buy and Sell Stock | <span class="diff-easy">Easy</span> | Running min | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 10 | Insert Delete GetRandom O(1) | <span class="diff-medium">Medium</span> | Hash + array swap | 🚧 |

### Trees (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 12 | Binary Tree Maximum Path Sum | <span class="diff-hard">Hard</span> | DFS post-order | 🚧 |
| 13 | Lowest Common Ancestor (Binary Tree) | <span class="diff-medium">Medium</span> | DFS post-order | 🚧 |
| 14 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 15 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | DFS + queue | 🚧 |

### Graphs & shortest path (8) — **Uber specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 16 | Number of Islands | <span class="diff-medium">Medium</span> | Grid BFS/DFS | 🚧 |
| 17 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 18 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | [📝](#deep-dive-1-network-delay-time-dijkstra) |
| 19 | Cheapest Flights Within K Stops | <span class="diff-medium">Medium</span> | Bellman-Ford | 🚧 |
| 20 | Path with Maximum Probability | <span class="diff-medium">Medium</span> | Dijkstra (max) | 🚧 |
| 21 | Reconstruct Itinerary | <span class="diff-hard">Hard</span> | Eulerian path | 🚧 |
| 22 | Word Ladder | <span class="diff-hard">Hard</span> | BFS on word graph | 🚧 |
| 23 | Critical Connections in a Network | <span class="diff-hard">Hard</span> | Tarjan bridges | 🚧 |

### Heap & Top-K (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 24 | K Closest Points to Origin | <span class="diff-medium">Medium</span> | Heap / quickselect | 🚧 |
| 25 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket | 🚧 |
| 26 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Min-heap | 🚧 |
| 27 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | 🚧 |
| 28 | Sliding Window Median | <span class="diff-hard">Hard</span> | Two heaps + lazy | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | Climbing Stairs | <span class="diff-easy">Easy</span> | 1D DP | 🚧 |
| 30 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 31 | Word Break | <span class="diff-medium">Medium</span> | DP + dictionary | 🚧 |
| 32 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | Patience / DP | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 33 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 34 | Permutations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 35 | Combinations | <span class="diff-medium">Medium</span> | Backtracking | 🚧 |
| 36 | Word Search | <span class="diff-medium">Medium</span> | Grid DFS + backtrack | 🚧 |

### Stacks / queues (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 38 | Min Stack | <span class="diff-medium">Medium</span> | Two stacks | 🚧 |
| 39 | Daily Temperatures | <span class="diff-medium">Medium</span> | Monotonic stack | 🚧 |

### Geospatial / system-design coding (5) — **Uber specialty**

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Implement a Quadtree | <span class="diff-medium">Medium</span> | Tree of 4 children | [📝](#deep-dive-3-quadtree-for-geospatial-search) |
| 41 | Encode/Decode Geohash | <span class="diff-medium">Medium</span> | Binary interleave | 🚧 |
| 42 | Design Hit Counter | <span class="diff-medium">Medium</span> | Circular buffer | 🚧 |
| 43 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 44 | Design Rate Limiter | <span class="diff-medium">Medium</span> | Token bucket / sliding window | [📝](#deep-dive-2-token-bucket-rate-limiter) |

### Concurrency (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 45 | Print in Order | <span class="diff-easy">Easy</span> | Semaphores | 🚧 |
| 46 | Building H2O | <span class="diff-medium">Medium</span> | Barriers + semaphores | 🚧 |
| 47 | Web Crawler Multithreaded | <span class="diff-medium">Medium</span> | Producer/consumer + visited set | 🚧 |

### Misc (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 48 | Single Number | <span class="diff-easy">Easy</span> | XOR | [✅](../../04-patterns/20-bitwise-xor.md) |
| 49 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 50 | Pow(x, n) | <span class="diff-medium">Medium</span> | Fast exponentiation | 🚧 |

---

## 🔬 Deep-dives — 3 Uber-style walkthroughs

These three are picked because:

- **Network Delay Time** is the canonical Dijkstra problem — and a *direct* analog of "ETA from a single source on Uber's road graph."
- **Token Bucket Rate Limiter** is the classic Uber design micro-problem.
- **Quadtree** is *the* Uber geospatial structure — used for "find drivers in this radius."

---

### Deep-dive 1: Network Delay Time (Dijkstra)

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Uber</span>

> Given `times[i] = (u, v, w)` (directed edges with weights ≥ 0) and a starting node `k`, return the time it takes for a signal from `k` to reach all `n` nodes (or -1 if unreachable).

#### 📖 Story mode

A driver at intersection `k` needs to deliver to every intersection. What's the *latest* arrival time? That's `max(distance from k to every node)` — exactly Dijkstra.

#### 🧠 Thinking process

- **Why Dijkstra and not BFS?** Edge weights ≥ 0 but unequal. BFS gives hop count, not weighted distance.
- **Why not Bellman-Ford?** All weights ≥ 0, so Dijkstra's `O((V+E) log V)` beats Bellman-Ford's `O(V·E)`.
- **Implementation**: min-heap keyed on `(dist_so_far, node)`. Lazy deletion via `if dist > visited[node]: skip`.

#### 🐍 Optimal solution

```python
import heapq
from collections import defaultdict

def network_delay_time(times: list[list[int]], n: int, k: int) -> int:
    """Min time for a signal from k to reach every node, or -1."""
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))

    dist: dict[int, int] = {}
    heap: list[tuple[int, int]] = [(0, k)]

    while heap:
        d, u = heapq.heappop(heap)
        if u in dist:                       # already finalized
            continue
        dist[u] = d
        for v, w in graph[u]:
            if v not in dist:
                heapq.heappush(heap, (d + w, v))

    if len(dist) < n:
        return -1
    return max(dist.values())
```

**Why "if u in dist: continue"?** Dijkstra with a heap can push the same node multiple times via different paths. The first pop is the shortest.

#### 🔍 Dry run

`times = [[2,1,1],[2,3,1],[3,4,1]]`, `n=4`, `k=2`.

| pop | dist | heap |
|---|---|---|
| (0,2) | {2:0} | [(1,1),(1,3)] |
| (1,1) | {2:0, 1:1} | [(1,3)] |
| (1,3) | {2:0, 1:1, 3:1} | [(2,4)] |
| (2,4) | {2:0, 1:1, 3:1, 4:2} | [] |

`max = 2`. ✅

#### ⏱️ Complexity

| | Time | Space |
|---|---|---|
| **Dijkstra (heap)** | O((V+E) log V) | O(V+E) |

#### 🔄 Uber's classic follow-up

??? question "What if we allow up to K stops?"
    Switch to **Bellman-Ford** with K iterations. (LC 787 — Cheapest Flights Within K Stops.)

??? question "What if some edges have *negative* weights?"
    Dijkstra fails. Use Bellman-Ford `O(V·E)` or, if no negative cycles and DAG, topological sort + relax.

??? question "Now scale this to a road network with 100M nodes."
    **A\*** with a haversine heuristic. Or **Contraction Hierarchies** for offline preprocessing — used in production routing engines.

#### 🐛 Common bugs

- Forgetting "if u in dist: continue" — re-processes nodes wastefully but doesn't break correctness as long as you take the first one.
- Returning `min(dist.values())` instead of `max` — the answer is "when the *last* node receives the signal."

---

### Deep-dive 2: Token Bucket Rate Limiter

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Uber</span>

> Implement a rate limiter that allows up to `R` requests per second, with a burst capacity of `B` tokens. `allow(timestamp_ms) -> bool`.

#### 📖 Story mode

Uber's API gateway rate-limits every client. The token-bucket model: tokens drip in at rate `R`, you can burst up to `B`. Each request consumes 1 token. No tokens? Reject.

#### 🧠 Thinking process

- **Naive**: count requests in a 1-second sliding window. Doesn't model bursts well.
- **Insight**: think of it as a bucket that refills at `R/1000` tokens per ms, capped at `B`. On each request, refill based on elapsed time, then deduct.
- **Why this is elegant**: bursts are first-class — short idle periods *earn* you the right to a burst.

#### 🐍 Optimal solution

```python
class TokenBucket:
    def __init__(self, rate_per_sec: float, burst: int) -> None:
        self.rate = rate_per_sec / 1000.0      # tokens per ms
        self.burst = burst
        self.tokens = float(burst)             # start full
        self.last_ms = 0

    def allow(self, ts_ms: int) -> bool:
        # Refill: add (ts_ms - last_ms) * rate, cap at burst.
        if self.last_ms:
            self.tokens = min(self.burst, self.tokens + (ts_ms - self.last_ms) * self.rate)
        self.last_ms = ts_ms
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
```

**Why store as float?** Fractional tokens are fine — you can't *spend* a fractional token (the `>= 1` guard handles it), but they accumulate cleanly.

#### 🔍 Dry run on `rate=10/s, burst=5`

`allow(0) ×6 in a row` then `allow(1000)` then `allow(1100)`.

| op | tokens before | refill | tokens after | result |
|---|---|---|---|---|
| allow(0) #1 | 5 | 0 | 4 | True |
| allow(0) #2-5 | 4..1 | 0 | 0 | True four times |
| allow(0) #6 | 0 | 0 | 0 | False |
| allow(1000) | 0 | 1000·0.01 = 10, cap 5 | 4 | True |
| allow(1100) | 4 | 100·0.01 = 1 | 4 | True |

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| `allow` | O(1) | O(1) |

#### 🔄 Uber's classic follow-up

??? question "How would you scale this to 1B requests/sec across a fleet?"
    Token bucket is per-client; shard by client_id. State lives in Redis with `EVAL` or `INCR + EXPIRE` Lua scripts. Or **leaky bucket** at the load balancer.

??? question "How do you handle clock drift between the client and the server?"
    Use server time. Discard client timestamps. If client time is needed for ordering (idempotency keys), bound the skew window and reject if exceeded.

??? question "How do you choose between token bucket and sliding window log?"
    Token bucket: O(1) memory, allows bursts, less accurate. Sliding window log: O(R) memory, exact, no burst boost. Uber prefers the bucket for cost; the log for billing-grade accuracy.

#### 🐛 Common bugs

- Updating `last_ms` even when `allow` returns False — fine for this design; some variants only update on accept.
- Storing tokens as `int` and losing fractional accumulation — at low rates this *severely* under-counts.

---

### Deep-dive 3: Quadtree for Geospatial Search

<span class="diff-medium">Medium</span> &nbsp; <span class="company-tag">Uber</span>

> Design a quadtree that supports `insert(x, y)` and `query(x, y, r)` — return all points within radius `r` of `(x, y)`.

#### 📖 Story mode

Uber's matching service: "find all drivers within 2 km of the rider." Brute-force scan of all drivers is `O(n)` per request. A quadtree gives expected `O(log n + k)` where `k` is the result count.

#### 🧠 Thinking process

- **Idea**: recursively subdivide a 2D bounding box into 4 quadrants when its point count exceeds a capacity `C`. Each leaf holds ≤ C points.
- **Insert**: walk down by quadrant; subdivide if at capacity; rebalance.
- **Query**: at each node, prune subtrees whose bounding box doesn't intersect the query circle. Recurse only into intersecting children.

#### 🐍 Optimal solution (sketch — full impl is ~80 lines)

```python
class _Quad:
    def __init__(self, x0, y0, x1, y1, cap=4):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.cap = cap
        self.points: list[tuple[float, float]] = []
        self.children: list["_Quad"] | None = None

    def _intersects_circle(self, cx: float, cy: float, r: float) -> bool:
        # Closest point of the rectangle to (cx, cy)
        nx = max(self.x0, min(cx, self.x1))
        ny = max(self.y0, min(cy, self.y1))
        return (nx - cx) ** 2 + (ny - cy) ** 2 <= r * r

    def _subdivide(self) -> None:
        mx, my = (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2
        self.children = [
            _Quad(self.x0, self.y0, mx, my, self.cap),
            _Quad(mx, self.y0, self.x1, my, self.cap),
            _Quad(self.x0, my, mx, self.y1, self.cap),
            _Quad(mx, my, self.x1, self.y1, self.cap),
        ]
        for p in self.points:
            for c in self.children:
                if c.x0 <= p[0] <= c.x1 and c.y0 <= p[1] <= c.y1:
                    c.points.append(p)
                    break
        self.points = []

    def insert(self, x: float, y: float) -> None:
        if self.children is None:
            self.points.append((x, y))
            if len(self.points) > self.cap:
                self._subdivide()
            return
        for c in self.children:
            if c.x0 <= x <= c.x1 and c.y0 <= y <= c.y1:
                c.insert(x, y)
                return

    def query(self, cx: float, cy: float, r: float, out: list) -> None:
        if not self._intersects_circle(cx, cy, r):
            return
        if self.children is None:
            for px, py in self.points:
                if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                    out.append((px, py))
            return
        for c in self.children:
            c.query(cx, cy, r, out)
```

**Why circle-intersect-rect, not the other way?** Pruning subtrees by their *bounding box vs the query circle* is what gives the expected log-factor speedup.

#### ⏱️ Complexity

| Op | Time | Space |
|---|---|---|
| `insert` | O(log n) expected | O(1) per node |
| `query` | O(log n + k) expected | O(1) per node |
| Total | — | O(n) |

#### 🔄 Uber's classic follow-up

??? question "Now make `insert` and `delete` work concurrently."
    Per-node read-write locks; or copy-on-write paths from root. Or use **R-tree** with bulk-loading offline + read-only queries online (Uber's actual approach for production).

??? question "What if drivers move every 5 seconds — re-inserting all of them?"
    Maintain `driver_id -> current_quadtree_leaf` mapping. On move, *remove from old leaf, insert into new leaf*. Avoids full rebuild.

??? question "How does this compare to geohashes?"
    Geohash: encode `(lat, lng)` as a base-32 string. Closer points share longer prefixes — a *string* index. Cheaper sharding, but worse for radial queries (doesn't naturally express "within r km").

#### 🐛 Common bugs

- Re-inserting a point at the wrong child after subdivide — borders matter; pick a tie-break convention.
- Not using `cap` to control depth — pathological inputs blow up tree height.

---

## 🗓️ Day-of tips for an Uber interview

!!! tip "The morning checklist"
    1. **Sleep 8 hours**.
    2. **Re-read** [Dijkstra's algorithm](../../03-algorithms/index.md) — Uber's #1 graph problem.
    3. **One easy + one medium** warm-up. Pick a graph problem.
    4. **Re-read your own production stories** — Uber loves on-call narratives.

### During the interview

| Stage | What to say / do |
|---|---|
| **First 60s** | Restate. **Ask about scale.** "How many drivers? How many cities?" |
| **Pre-coding (~5 min)** | State approach + complexity. *Mention sharding.* |
| **Coding (~25 min)** | Narrate. Type clean. |
| **System design** | Capacity → APIs → data model → **geo-sharding** → caching → failure modes. Geo-sharding is the Uber-specific signal. |
| **Behavioral** | "Build with heart" stories — show you cared about a user / driver / partner outcome. |

### Red & green flags

- 🚩 Skipping clarifying questions about scale.
- 🚩 Suggesting a non-sharded design at Uber-scale.
- 🟢 Naming a concrete sharding key ("by city_id, with hot-spot rebalancing").
- 🟢 Mentioning a real production tradeoff ("we chose eventual consistency because the rider only needs the *latest* ETA, not all of them").

---

## 🔁 Where to go from here

- **Solve the 50** in roughly the order above.
- **System design** — start with [URL Shortener](../../08-system-design/index.md), then "Design Uber" subsystems (lands in Phase 9).
- **Geospatial** — read about geohashes, quadtrees, R-trees, S2 cells.
- **Cross-check** with the [Top 100 by Pattern](../top-100-by-pattern.md).

> Same six-part shape as [Google 50](google-50.md) and [Meta 50](meta-50.md).
