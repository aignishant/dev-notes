# Salesforce — 50 most-asked questions

> The 50 problems Salesforce (Sales Cloud, Service Cloud, Slack, MuleSoft, Tableau) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Salesforce</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Salesforce is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background + values fit. |
| **OA (HackerRank)** | 90 min | 2 medium coding + a few MCQs on Apex / SQL. |
| **Tech screen** | 45 min | DS + algorithms (Java or Python). |
| **Onsite — coding ×2** | 45 min each | Standard + a domain-flavored problem. |
| **Onsite — system / OOP design** | 60 min | "Design a multi-tenant CRM event log." |
| **Hiring manager + Trust round** | 45 min each | Behavioral, "Trust is our #1 value." |

**Salesforce style**: SaaS-veteran, multi-tenancy obsession, friendlier than FAANG. Java + Apex world. Behavioral round explicitly called the **Trust round** — they grade you on whether you'd surface a customer-impacting issue even when inconvenient.

---

## 🎯 What Salesforce tests

| Signal | Where | How to show |
|---|---|---|
| OOP fluency | Phone + onsite | Clean class boundaries; sane inheritance. |
| Multi-tenancy thinking | System design | Tenant isolation, noisy-neighbor mitigation. |
| SQL / data model | OA + onsite | Joins, indexes, query plans. |
| Trust + customer obsession | Behavioral | Concrete examples of doing the right thing. |

---

## 🧩 Patterns Salesforce loves

| Pattern | Frequency | Why |
|---|---|---|
| **OOP class design** | ⭐⭐⭐⭐⭐ | Their bread-and-butter. |
| **Hash + LRU** | ⭐⭐⭐⭐ | Caching layer questions. |
| **BFS / DFS on trees** | ⭐⭐⭐⭐ | Org hierarchies, account trees. |
| **SQL / query optimisation** | ⭐⭐⭐⭐ | SOQL cousins. |
| **Backtracking** | ⭐⭐⭐ | Permission-set assignment puzzles. |

---

## 📋 The 50 questions

Status: ✅ = full v3 &nbsp; 📝 = mini-v3 below &nbsp; 🚧 = lands later in Phase 8.

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Valid Parentheses | <span class="diff-easy">Easy</span> | Stack | 🚧 |
| 3 | Longest Substring Without Repeating Characters | <span class="diff-medium">Medium</span> | Sliding window | 🚧 |
| 4 | Group Anagrams | <span class="diff-medium">Medium</span> | Hash + sorted-key | 🚧 |
| 5 | String to Integer (atoi) | <span class="diff-medium">Medium</span> | State machine | 🚧 |
| 6 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane's | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 7 | Merge Intervals | <span class="diff-medium">Medium</span> | Sort + sweep | [✅](../../04-patterns/04-merge-intervals.md) |
| 8 | Insert Interval | <span class="diff-medium">Medium</span> | Sweep | 🚧 |
| 9 | Spiral Matrix | <span class="diff-medium">Medium</span> | Layer-by-layer | 🚧 |
| 10 | Sparse Search | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |

### Linked lists (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | Merge Two Sorted Lists | <span class="diff-easy">Easy</span> | Two pointers | 🚧 |
| 13 | Linked List Cycle II | <span class="diff-medium">Medium</span> | Floyd's | 🚧 |
| 14 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |

### Trees (8)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 15 | Binary Tree Level Order Traversal | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 16 | Validate BST | <span class="diff-medium">Medium</span> | DFS + bounds | 🚧 |
| 17 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order DFS | 🚧 |
| 18 | Serialize / Deserialize Binary Tree | <span class="diff-hard">Hard</span> | BFS / pre-order | 🚧 |
| 19 | Path Sum II | <span class="diff-medium">Medium</span> | DFS + backtrack | 🚧 |
| 20 | Right Side View | <span class="diff-medium">Medium</span> | BFS last-of-level | 🚧 |
| 21 | Symmetric Tree | <span class="diff-easy">Easy</span> | Mirror DFS | 🚧 |
| 22 | Diameter of Binary Tree | <span class="diff-easy">Easy</span> | Post-order | 🚧 |

### Graphs (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 23 | Number of Islands | <span class="diff-medium">Medium</span> | DFS / BFS | 🚧 |
| 24 | Clone Graph | <span class="diff-medium">Medium</span> | DFS + hash | 🚧 |
| 25 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 26 | Word Ladder | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 27 | Reconstruct Itinerary | <span class="diff-hard">Hard</span> | Hierholzer DFS | 🚧 |
| 28 | Account Merge | <span class="diff-medium">Medium</span> | Union-Find | 📝 |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 29 | Kth Largest in Stream | <span class="diff-easy">Easy</span> | Min-heap K | 🚧 |
| 30 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap / bucket | [✅](../../04-patterns/12-top-k-elements.md) |
| 31 | Merge K Sorted Lists | <span class="diff-hard">Hard</span> | Heap | 🚧 |
| 32 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |

### Backtracking (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Subsets | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 34 | Permutations | <span class="diff-medium">Medium</span> | Backtrack | 🚧 |
| 35 | Word Search | <span class="diff-medium">Medium</span> | DFS + visited | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 36 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 37 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 38 | Word Break | <span class="diff-medium">Medium</span> | DP + dict | 🚧 |
| 39 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP / patience | 🚧 |
| 40 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 41 | Binary Search | <span class="diff-easy">Easy</span> | BS | 🚧 |
| 42 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 43 | Sort Colors | <span class="diff-medium">Medium</span> | Dutch national flag | 🚧 |

### Design (7)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 44 | Design HashMap | <span class="diff-easy">Easy</span> | Chaining | 🚧 |
| 45 | Design Tic-Tac-Toe | <span class="diff-medium">Medium</span> | Counters | 📝 (see [Microsoft 50](microsoft-50.md)) |
| 46 | Design Multi-tenant Rate Limiter | <span class="diff-hard">Hard</span> | Token bucket per tenant | 📝 |
| 47 | Design Trigger Engine | <span class="diff-hard">Hard</span> | Event queue + topo sort | 🚧 |
| 48 | Design Audit Log | <span class="diff-medium">Medium</span> | Append-only log | 🚧 |
| 49 | Design Permission System | <span class="diff-hard">Hard</span> | RBAC + hierarchical roles | 🚧 |
| 50 | Design Object Manager | <span class="diff-hard">Hard</span> | Schema registry | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — Account Merge (LC 721)

??? question "Story: customer service is showing one person as 5 separate accounts because they signed up with 5 emails. Merge them."

    Each row is `[name, email1, email2, ...]`. Two rows belong to the same person iff they share at least one email. Merge into one canonical account per person.

??? note "Thinking"

    Classic Union-Find problem. Union all emails inside the same row, then group emails by root. Names are just labels — store one name per root.

```python
class DSU:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def accounts_merge(accounts: list[list[str]]) -> list[list[str]]:
    dsu = DSU()
    email_to_name: dict[str, str] = {}

    for acc in accounts:
        name, emails = acc[0], acc[1:]
        for e in emails:
            dsu.parent.setdefault(e, e)
            email_to_name[e] = name
            dsu.union(emails[0], e)

    groups: dict[str, list[str]] = {}
    for email in dsu.parent:
        root = dsu.find(email)
        groups.setdefault(root, []).append(email)

    return [[email_to_name[root]] + sorted(emails) for root, emails in groups.items()]
```

??? example "Dry run"

    `[["John","a@","b@"], ["John","b@","c@"], ["Mary","d@"]]` → after unions, `a@/b@/c@` share a root → output `[["John","a@","b@","c@"], ["Mary","d@"]]`.

??? abstract "Complexity"

    Time: O(N · α(N)) where N is total emails. Space: O(N).

??? tip "Salesforce follow-up: 'what if a row has 10k emails — does this still work?'"

    Yes — path compression keeps amortised time near-linear. The bottleneck becomes the final sort per group.

---

### Deep-dive 2 — Multi-tenant Rate Limiter

??? question "Story: enforce per-org API quotas. Org A pays for 1k req/sec, Org B for 100. Don't let A starve B."

    Two tiers: per-tenant token bucket + a global ceiling. Each tenant fills tokens at its own rate; the global cap protects shared infra.

```python
import time
import threading
from dataclasses import dataclass

@dataclass
class Bucket:
    capacity: float
    refill_per_sec: float
    tokens: float
    last: float

class MultiTenantRateLimiter:
    def __init__(self, global_capacity: float, global_refill: float):
        self.tenants: dict[str, Bucket] = {}
        self.lock = threading.Lock()
        self.global_bucket = Bucket(global_capacity, global_refill, global_capacity, time.monotonic())

    def configure(self, tenant_id: str, capacity: float, refill_per_sec: float) -> None:
        with self.lock:
            self.tenants[tenant_id] = Bucket(capacity, refill_per_sec, capacity, time.monotonic())

    def _refill(self, b: Bucket, now: float) -> None:
        b.tokens = min(b.capacity, b.tokens + (now - b.last) * b.refill_per_sec)
        b.last = now

    def allow(self, tenant_id: str, cost: float = 1.0) -> bool:
        with self.lock:
            now = time.monotonic()
            tenant = self.tenants.get(tenant_id)
            if tenant is None:
                return False
            self._refill(tenant, now)
            self._refill(self.global_bucket, now)
            if tenant.tokens >= cost and self.global_bucket.tokens >= cost:
                tenant.tokens -= cost
                self.global_bucket.tokens -= cost
                return True
            return False
```

??? abstract "Complexity"

    O(1) per `allow` call. Memory O(T) for T tenants.

??? tip "Salesforce follow-up: 'how do you keep this consistent across 30 API servers?'"

    Push the bucket state to Redis with `INCR / EXPIRE` (or `CL.THROTTLE`). Lua script makes the refill+consume atomic.

---

### Deep-dive 3 — Org Hierarchy LCA

??? question "Story: given a Salesforce org tree, find the lowest common manager between two reps."

    Standard LCA on an n-ary tree. Recursive: if either child returns the answer, propagate. Else if both descendants found, current node IS the LCA.

```python
class OrgNode:
    def __init__(self, name: str):
        self.name = name
        self.reports: list[OrgNode] = []

def lca(root: OrgNode | None, a: OrgNode, b: OrgNode) -> OrgNode | None:
    if root is None or root is a or root is b:
        return root
    found: list[OrgNode] = []
    for child in root.reports:
        result = lca(child, a, b)
        if result is not None:
            found.append(result)
        if len(found) == 2:
            return root
    return found[0] if found else None
```

??? abstract "Complexity"

    O(N) time, O(H) space where H is tree height.

??? tip "Salesforce follow-up: 'what if the tree changes a lot — daily reorgs?'"

    Cache parent pointers and recompute only the affected subtree on each reorg event. For deep trees, switch to Euler tour + RMQ for O(1) LCA at the cost of O(N log N) preprocessing.

---

## 🛡️ Day-of tips

- **Trust round**: have one story where you flagged a customer-impact issue your manager didn't want to hear. They specifically grade for this.
- **Apex / SOQL**: even Python-track candidates get asked basic SOQL — know `WHERE`, `GROUP BY`, governor limits.
- **Multi-tenancy**: every system-design answer should mention tenant isolation explicitly.
- **Ohana culture**: name-drop "Ohana" once, naturally — they really do live it. Never twice.
