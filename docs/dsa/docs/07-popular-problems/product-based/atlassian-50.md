# Atlassian — 50 most-asked questions

> The 50 problems Atlassian (Jira, Confluence, Bitbucket, Trello, Loom) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Atlassian</span> &nbsp; <span class="phase-status phase-done">Phase 8 — Company list</span>

---

## 🏢 What interviewing at Atlassian is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + values fit. |
| **OA / take-home** | ~2 hr | One open-ended coding problem with tests. |
| **Tech screen** | 60 min | DS + algorithms, pair-programming style. |
| **Onsite — coding** | 60 min | Medium / hard with collaborative discussion. |
| **Onsite — system design** | 60 min | "Design Jira's notification system." |
| **Onsite — values interview** | 45 min | Atlassian's 5 values, **strong filter**. |
| **Onsite — manager** | 45 min | Project deep-dive. |

**Atlassian style**: Australian work-life-balance ethos, 5 values run deep ("Open company, no bullshit", "Build with heart and balance", etc.). Pair programming over speed solo. Take-home is graded for testability + readability, not cleverness.

---

## 🎯 What Atlassian tests

| Signal | Where | How to show |
|---|---|---|
| Collaboration | Tech screen | Talk through your reasoning; ask for input. |
| Code quality | Take-home | Tests + clean structure beat shorter clever code. |
| Values fit | Values round | Concrete stories per value, not slogans. |
| System design pragmatism | Onsite | Boring, scalable, observable beats novel. |

---

## 🧩 Patterns Atlassian loves

| Pattern | Frequency | Why |
|---|---|---|
| **Hash + sliding window** | ⭐⭐⭐⭐⭐ | String / log fluency. |
| **Tree DFS** | ⭐⭐⭐⭐ | Wiki / page hierarchies. |
| **Graph BFS** | ⭐⭐⭐⭐ | Issue dependency graphs. |
| **Heap top-K** | ⭐⭐⭐⭐ | Activity feeds, leaderboards. |
| **Design** | ⭐⭐⭐⭐⭐ | Always one design round. |

---

## 📋 The 50 questions

Status: ✅ = full v3 &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 3 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 4 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash | 🚧 |
| 5 | Minimum Window Substring | <span class="diff-hard">Hard</span> | Sliding window | 🚧 |
| 6 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 7 | Insert Interval | <span class="diff-medium">Medium</span> | Sweep | 🚧 |
| 8 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 9 | Product of Array Except Self | <span class="diff-medium">Medium</span> | Prefix / suffix | 🚧 |
| 10 | Longest Consecutive Sequence | <span class="diff-medium">Medium</span> | Hash set | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 13 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 15 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 16 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order DFS | 🚧 |
| 17 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | BFS / pre-order | 🚧 |
| 18 | Path Sum II | <span class="diff-medium">Medium</span> | DFS + backtrack | 🚧 |
| 19 | Subtree of Another Tree | <span class="diff-easy">Easy</span> | DFS | 🚧 |
| 20 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | Post-order | 🚧 |
| 21 | Confluence Page Tree Search | <span class="diff-medium">Medium</span> | DFS + breadcrumb | 📝 |

### Graphs (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 22 | Number of Islands | <span class="diff-medium">Medium</span> | DFS / BFS | 🚧 |
| 23 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 24 | Clone Graph | <span class="diff-medium">Medium</span> | DFS + hash | 🚧 |
| 25 | Word Ladder | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 26 | Jira Issue Cycle Detection | <span class="diff-medium">Medium</span> | DFS coloring | 📝 |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 27 | Kth Largest in Stream | <span class="diff-easy">Easy</span> | Min-heap K | 🚧 |
| 28 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 29 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 30 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 31 | Subsets | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 32 | Permutations | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 33 | Word Break II | <span class="diff-hard">Hard</span> | Backtrack + memo | 🚧 |

### DP (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 34 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 35 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 36 | Word Break | <span class="diff-medium">Medium</span> | DP + dict | 🚧 |
| 37 | Longest Common Subsequence | <span class="diff-medium">Medium</span> | 2D DP | 🚧 |

### Search (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 38 | Binary Search | <span class="diff-easy">Easy</span> | BS | 🚧 |
| 39 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 40 | Find Peak Element | <span class="diff-medium">Medium</span> | BS variant | 🚧 |

### Design (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Design HashMap | <span class="diff-easy">Easy</span> | Chaining | 🚧 |
| 42 | Design Notification System | <span class="diff-hard">Hard</span> | Pub/sub + delivery | 📝 |
| 43 | Design Activity Feed | <span class="diff-hard">Hard</span> | Heap + fanout | 🚧 |
| 44 | Design Issue Tracker | <span class="diff-hard">Hard</span> | OOP + state machine | 🚧 |
| 45 | Design Wiki Search | <span class="diff-hard">Hard</span> | Inverted index | 🚧 |
| 46 | Design Rate Limiter | <span class="diff-medium">Medium</span> | Token bucket | 🚧 |
| 47 | Design Mention Service | <span class="diff-medium">Medium</span> | Trie + ranking | 🚧 |
| 48 | Design Permission Check | <span class="diff-medium">Medium</span> | RBAC + caching | 🚧 |
| 49 | Design Deploy Pipeline | <span class="diff-hard">Hard</span> | DAG + topo sort | 🚧 |
| 50 | Design Live Document Sync | <span class="diff-hard">Hard</span> | OT / CRDT | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Notification System

??? question "Story: a Jira ticket is updated. Send email to assignee, Slack to watchers, in-app to mentioned users — fan-out to 50 channels."

    A pub/sub queue with per-channel workers. Producer enqueues a `NotificationEvent`. Each channel subscribes and dispatches independently — one slow channel can't block others.

```python
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    payload: dict

class Bus:
    def __init__(self):
        self.subs: dict[str, list[deque]] = defaultdict(list)

    def subscribe(self, event_type: str) -> deque:
        q: deque = deque()
        self.subs[event_type].append(q)
        return q

    def publish(self, event: Event) -> None:
        for q in self.subs[event.type]:
            q.append(event)

def email_worker(q: deque) -> None:
    while q:
        ev = q.popleft()
        # send_email(ev.payload)

def slack_worker(q: deque) -> None:
    while q:
        ev = q.popleft()
        # post_slack(ev.payload)
```

??? abstract "Complexity"

    Publish O(C) where C is channels. Each worker is independent: backpressure stays local.

??? tip "Atlassian follow-up: 'what if Slack is down for 30 min?'"

    Per-channel dead letter queue + exponential backoff retry. Persist `Event` so you can replay after recovery.

---

### Deep-dive 2 — Issue Cycle Detection

??? question "Story: Jira lets epics block each other. Detect cycles before saving."

    Directed graph cycle detection via DFS coloring: WHITE (unvisited) / GRAY (on stack) / BLACK (done). A back edge to GRAY = cycle.

```python
def has_cycle(graph: dict[str, list[str]]) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for nxt in graph[node]:
            if color[nxt] == GRAY:
                return True  # back edge
            if color[nxt] == WHITE and dfs(nxt):
                return True
        color[node] = BLACK
        return False

    return any(color[n] == WHITE and dfs(n) for n in graph)
```

??? abstract "Complexity"

    O(V + E). Same as topological sort.

??? tip "Atlassian follow-up: 'show me the cycle, not just yes/no'"

    Track parent pointers along the GRAY path. When you hit a back edge, walk parents back to the target to reconstruct the cycle.

---

### Deep-dive 3 — Confluence Page Tree Search

??? question "Story: Confluence pages form a tree. Build search that returns the page + breadcrumb path."

    DFS with a path stack. When the search predicate matches, snapshot the path.

```python
class Page:
    def __init__(self, title: str, body: str):
        self.title = title
        self.body = body
        self.children: list[Page] = []

def search(root: Page, query: str) -> list[list[str]]:
    results: list[list[str]] = []
    path: list[str] = []

    def dfs(node: Page) -> None:
        path.append(node.title)
        if query.lower() in node.body.lower() or query.lower() in node.title.lower():
            results.append(path.copy())
        for child in node.children:
            dfs(child)
        path.pop()

    dfs(root)
    return results
```

??? abstract "Complexity"

    O(N · L) where N is pages, L is body length. Real impl uses an inverted index.

??? tip "Atlassian follow-up: 'this is too slow at 1M pages — what now?'"

    Build an inverted index: word → set of page IDs. Query = intersect posting lists. Add ranking (BM25) on top.

---

## 🛡️ Day-of tips

- **Values round is real**: have one story per value. "Open, no bullshit" wants a moment you flagged something uncomfortable. "Don't #@!% the customer" wants a customer-first call.
- **Take-home grading**: tests + README + trade-off notes matter as much as the algorithm. Don't skip them.
- **Pair programming**: think aloud constantly. Silence is your enemy.
- **Boring is good**: in design rounds, propose Postgres + Redis + a queue before anything fancy.
