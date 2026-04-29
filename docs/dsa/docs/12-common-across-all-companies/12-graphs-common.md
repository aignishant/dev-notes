# Graphs — common across all companies

> Grids are graphs, courses are graphs, friendships are graphs. Pick BFS, DFS, or Union-Find — pick well.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Graph problems feel scary because there are many algorithms — but in interviews ~95% reduce to one of: BFS for unweighted shortest path, DFS for connectivity / topological order, Dijkstra for weighted shortest path, Union-Find for "are these merged?" questions, or BFS/DFS on a grid. Recognise the shape and pick the tool — the rest is plumbing.

## Pattern frequency

| Pattern | Frequency | Typical signal |
|---|---|---|
| Grid BFS / DFS | ⭐⭐⭐⭐⭐ | "islands", "rotting", "regions", "shortest path in matrix" |
| Topological sort (Kahn / DFS) | ⭐⭐⭐⭐ | "courses", "ordering", "build order" |
| Multi-source BFS | ⭐⭐⭐⭐ | "rotting oranges", "walls and gates", "0/1 matrix" |
| Union-Find (DSU) | ⭐⭐⭐ | "redundant edge", "accounts merge", "MST" |
| Dijkstra | ⭐⭐⭐ | weighted shortest path, "k stops" |
| BFS word ladder / state space | ⭐⭐ | implicit graph over strings |

## Problem set

| # | Problem | Difficulty | Pattern | LeetCode |
|---|---|---|---|---|
| 1 | Number of Islands | Medium | Grid DFS / BFS / DSU | 200 |
| 2 | Clone Graph | Medium | DFS / BFS + map | 133 |
| 3 | Course Schedule | Medium | Topo sort / cycle | 207 |
| 4 | Course Schedule II | Medium | Kahn's BFS | 210 |
| 5 | Pacific Atlantic Water Flow | Medium | Reverse BFS from edges | 417 |
| 6 | Word Ladder | Hard | BFS over strings | 127 |
| 7 | Network Delay Time | Medium | Dijkstra | 743 |
| 8 | Cheapest Flights Within K Stops | Medium | Bellman-Ford / Dijkstra+stops | 787 |
| 9 | Reconstruct Itinerary | Hard | Hierholzer's Eulerian | 332 |
| 10 | Surrounded Regions | Medium | Reverse DFS from edges | 130 |
| 11 | Walls and Gates | Medium | Multi-source BFS | 286 |
| 12 | Rotting Oranges | Medium | Multi-source BFS | 994 |
| 13 | Shortest Path in Binary Matrix | Medium | BFS (8-dir) | 1091 |
| 14 | Min Cost to Connect All Points | Medium | MST (Prim / Kruskal) | 1584 |
| 15 | Redundant Connection | Medium | Union-Find | 684 |
| 16 | Accounts Merge | Medium | Union-Find / DFS | 721 |

---

## Deep-dive 1 — Course Schedule II (LC 210, Kahn's algorithm)

??? question "Why Kahn over DFS?"
    Both work. **Kahn's BFS topological sort** is more interview-friendly because it doubles as cycle detection: if you can't process all `n` nodes, there's a cycle. Easier to explain on a whiteboard than DFS-with-three-colors.

The setup:

- Build a directed graph `prereq → course`.
- Compute in-degree (number of prereqs left) for each course.
- Start a queue with everyone whose in-degree is 0 (no prereqs).
- Pop, append to order, decrement in-degree of neighbors, enqueue any that hit 0.
- If `len(order) == n`, return it. Otherwise, return `[]` — there's a cycle.

```python linenums="1"
from __future__ import annotations
from collections import defaultdict, deque


class Solution:
    def findOrder(self, numCourses: int, prerequisites: list[list[int]]) -> list[int]:
        graph: dict[int, list[int]] = defaultdict(list)
        in_degree = [0] * numCourses

        for course, prereq in prerequisites:        # edge: prereq → course
            graph[prereq].append(course)
            in_degree[course] += 1

        # Seed queue with all zero-in-degree courses.
        queue: deque[int] = deque(i for i in range(numCourses) if in_degree[i] == 0)
        order: list[int] = []

        while queue:
            node = queue.popleft()
            order.append(node)                      # (1)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1            # (2)
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Cycle ⇒ we couldn't process every node.
        return order if len(order) == numCourses else []  # (3)
```

1. We commit to processing this course — its prereqs are all done.
2. We "remove" the edge `node → neighbor` by decrementing.
3. The processed-count trick: if any course still has in-degree > 0, it's stuck in a cycle.

??? note "Complexity"
    - Time **O(V + E)** — each node and edge processed once.
    - Space **O(V + E)** for graph + queue + in-degree array.

??? tip "Course Schedule I (LC 207)"
    Same code; just return `len(order) == numCourses` instead of the order itself.

---

## Deep-dive 2 — Number of Islands (LC 200) — three flavors

??? question "Why three approaches?"
    Interviewers love asking "now do it differently." DFS is shortest to write. BFS avoids stack overflow on huge grids. Union-Find is the right answer if islands can grow dynamically (LC 305 follow-up).

### Approach A — DFS (primary)

```python linenums="1"
from __future__ import annotations


class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        if not grid or not grid[0]:
            return 0
        rows, cols = len(grid), len(grid[0])
        count = 0

        def dfs(r: int, c: int) -> None:
            # Out of bounds or water/visited ⇒ stop.
            if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
                return
            grid[r][c] = "0"                        # (1) sink it — acts as visited mark
            dfs(r + 1, c); dfs(r - 1, c)
            dfs(r, c + 1); dfs(r, c - 1)

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "1":
                    count += 1                      # (2) found a new island
                    dfs(r, c)                       # sink the whole landmass

        return count
```

1. Mutating the grid avoids a separate `visited` set — saves memory. Mention this in the interview.
2. Each unvisited `'1'` is a fresh island; DFS swallows everything connected.

??? note "Complexity"
    - Time **O(R · C)** — each cell visited once.
    - Space **O(R · C)** worst case for recursion (one giant island).

### Approach B — BFS (iterative, safer for huge grids)

```python linenums="1"
from collections import deque


def numIslandsBFS(grid: list[list[str]]) -> int:
    rows, cols = len(grid), len(grid[0])
    count = 0

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != "1":
                continue
            count += 1
            q = deque([(r, c)])
            grid[r][c] = "0"
            while q:
                x, y = q.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == "1":
                        grid[nx][ny] = "0"          # mark on enqueue, not dequeue
                        q.append((nx, ny))
    return count
```

### Approach C — Union-Find

```python linenums="1"
class DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.count = 0  # number of components

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path compression
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb
            self.count -= 1


def numIslandsDSU(grid: list[list[str]]) -> int:
    rows, cols = len(grid), len(grid[0])
    dsu = DSU(rows * cols)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                dsu.count += 1
                for dr, dc in ((1, 0), (0, 1)):     # only down/right — avoid double work
                    nr, nc = r + dr, c + dc
                    if nr < rows and nc < cols and grid[nr][nc] == "1":
                        dsu.union(r * cols + c, nr * cols + nc)
    return dsu.count
```

??? tip "Which to pick in the interview"
    Default to **DFS** — fewest lines, easiest to explain. Switch to **BFS** if they say "what if the grid is 10⁶ × 10⁶" (recursion limit). Switch to **DSU** if they ask "what if cells become land *after* we start?" (dynamic connectivity, LC 305).

---

## Common gotchas

!!! warning "Things that bite people"
    - **Word Ladder** — build the bucket map (`h*t` → `[hat, hot, hit]`) once; don't compare every pair.
    - **Pacific Atlantic** — don't search *to* the oceans for every cell. BFS *from* each ocean's edge cells (reverse direction).
    - **Cheapest Flights K Stops** — plain Dijkstra fails. Track `(cost, node, stops)` and allow re-visits with fewer stops.
    - **Reconstruct Itinerary** — Hierholzer's: DFS lexically smallest; append to result on the way *up*; reverse at the end.
    - **Multi-source BFS** — enqueue *all* sources before starting; don't loop sequentially.

## 🃏 Cheatsheet

| Move | When | Skeleton |
|---|---|---|
| Grid DFS | islands, regions | `dfs(r,c)` 4-dirs, mutate grid as visited |
| Multi-source BFS | rotting, walls, 0/1 matrix | enqueue *all* sources first, then BFS |
| Kahn topo | courses, build order | in-degree array + queue of zeros |
| Dijkstra | weighted shortest path | min-heap of `(dist, node)` |
| Union-Find | "are these connected?" | path-compress + union-by-size |
| BFS word ladder | string transforms | bucket map (`h*t`) for O(1) neighbors |

??? tip "Quick algorithm chooser"
    1. Unweighted shortest path? **BFS**.
    2. Weighted, non-negative? **Dijkstra**.
    3. Weighted with negatives or "k edges"? **Bellman-Ford**.
    4. "Is it a DAG / give an order"? **Topological sort**.
    5. "Are nodes in the same group?" **Union-Find**.
    6. "All-pairs shortest path on small graph"? **Floyd-Warshall**.
