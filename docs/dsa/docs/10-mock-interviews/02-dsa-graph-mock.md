# Mock 2 — DSA Coding Round, Graph Variant (45 min)

> **Setup**: principal-level loop. Problem starts as "shortest path in a grid" but the interviewer keeps escalating. The point of this transcript is the **escalation game** — what to do when the problem keeps changing.

<span class="phase-status phase-done">Phase 14 — Mock Interview</span>

---

## 🎬 Transcript

### Round 0: the original problem

> **I**: Given an `m × n` grid of 0s and 1s where 1 = wall and 0 = open, return the shortest path length from `(0,0)` to `(m-1, n-1)`. 4-directional moves. -1 if unreachable.
>
> **C**: Plain BFS. Queue of `(r, c, dist)`; visited set. Return on first dequeue of target.

```python
from collections import deque

def shortest_path(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    if grid[0][0] or grid[m-1][n-1]:
        return -1
    q = deque([(0, 0, 1)])
    seen = {(0, 0)}
    while q:
        r, c, d = q.popleft()
        if (r, c) == (m-1, n-1):
            return d
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < m and 0 <= nc < n and not grid[nr][nc] and (nr,nc) not in seen:
                seen.add((nr,nc))
                q.append((nr,nc,d+1))
    return -1
```

> **I**: Good. Complexity?
>
> **C**: O(m·n) time, O(m·n) space.

??? tip "What just happened"

    No drama. BFS for unweighted shortest path is muscle memory. Got it out in 5 min.

### Escalation 1: "you can break at most K walls"

> **I**: Now you can knock down up to **K walls** along the path. Same start, same end, same goal — shortest path length, but you have a budget of K wall-breaks.

> **C**: The state needs to grow. Now a "node" in BFS is `(r, c, breaks_used)`. Visited becomes a set of those triples. From `(r, c, k)`, moving to a wall costs `+1` to k; moving to an open cell costs 0. Skip if k > K.
>
> **I**: How does that change complexity?
>
> **C**: O(m · n · K) time and space. Each cell has K+1 versions.

```python
def shortest_with_breaks(grid: list[list[int]], K: int) -> int:
    m, n = len(grid), len(grid[0])
    q = deque([(0, 0, 0, 1)])              # r, c, breaks_used, dist
    seen = {(0, 0, 0)}
    while q:
        r, c, k, d = q.popleft()
        if (r, c) == (m-1, n-1):
            return d
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if not (0 <= nr < m and 0 <= nc < n):
                continue
            nk = k + grid[nr][nc]
            if nk > K or (nr, nc, nk) in seen:
                continue
            seen.add((nr, nc, nk))
            q.append((nr, nc, nk, d+1))
    return -1
```

??? tip "What just happened"

    The candidate didn't panic-rewrite. They identified that *only the state changes* — the algorithm is still BFS. That insight is the lesson.

### Escalation 2: "moves have weights now"

> **I**: Cells have a positive integer cost; cost of a path is sum of cell costs you step on (excluding the start cell). What's the cheapest path?

> **C**: Now BFS doesn't work — edges aren't unit weight. Dijkstra. Min-heap of `(cost, r, c)`.
>
> **I**: Why not BFS with a queue per cost level?
>
> **C**: That works if costs are bounded small integers — it's the "0-1 BFS" generalisation. For unbounded positive weights, Dijkstra with a heap is cleaner and O((m·n) log(m·n)).

??? tip "What just happened"

    Two algorithms named (Dijkstra + 0-1 BFS), one chosen, one ruled out by reasoning about cost magnitude. Crisp.

### Escalation 3: "cells can have negative cost (refunds)"

> **C**: Negative weights kill Dijkstra — it relies on the fact that once a node is popped, its distance is final. That assumption requires non-negative edges. Options:
>
> 1. Bellman-Ford: O((m·n)²). Works with negatives, detects negative cycles.
> 2. SPFA: a queue-based BF with empirical speedup, same worst case.
> 3. If we can prove no negative *cycles*, Johnson's algorithm or just a topological sort if the grid is a DAG (it's not — it's an undirected grid).
>
> Most likely we have to drop to Bellman-Ford. Is the answer guaranteed to be finite — no negative cycles?
>
> **I**: Good question. Assume no negative cycles.

??? tip "What just happened"

    Asked the question that determines whether the problem is well-posed. Without that, the candidate would be coding an answer for "any input" that includes inputs with no answer.

### Escalation 4: "millions of cells"

> **I**: m, n ~ 5000. K up to 100. Costs are non-negative integers up to 10. Will your code finish?

> **C**: m·n = 25 M. With K = 100, the K-walls variant is 2.5 B states — too slow. Two angles:
>
> 1. **Bidirectional BFS** from start and end, meet in the middle. Roughly halves the search. Doesn't help with the K dimension though — we'd need bidirectional search over `(r, c, k)` triples. Still ~1.25 B.
> 2. **A\*** with a Manhattan-distance heuristic on `(r, c)`. Admissible because moving costs ≥ 0 and Manhattan ≤ true distance in 4-directional unweighted. With small heuristic gain, could prune heavily.
>
> Most pragmatic at this scale: A* with a tight heuristic. If still too slow, accept the problem doesn't fit in memory and discuss approximation: hierarchical pathfinding (cluster grid into super-cells, plan high-level, refine).

??? tip "What just happened"

    Once the inputs blow up, classical algorithms aren't enough. Naming **A***, **bidirectional**, and **hierarchical pathfinding** — and reasoning about which applies — is the senior signal.

### Last 5 min: candidate questions

> **C**: When you see a problem at this scale in production, do you reach for a custom algorithm or for a graph DB / library?

??? tip "What just happened"

    A real-world hook. Pulls the interviewer into talking about their actual work.

---

## 🟢 What was good

- Each escalation reframed as "what changes in the state / algorithm?" without rewriting from scratch.
- Named-and-rejected: 0-1 BFS for the second problem, Dijkstra for the third — explicit "this won't work because…" reasoning.
- Asked about negative cycles before charging into Bellman-Ford.
- At scale, knew the right tools (bidirectional, A*, hierarchical) and *why* each applied.

## 🟡 What was weak

- Forgot to check whether grid mutates between calls (would affect memoisation).
- Didn't propose a unit test framework for the K-walls variant.
- The Dijkstra complexity quoted as `O((m·n) log(m·n))` — should clarify it's `O(E log V)` and that grid edges = 4·m·n.

## 🔁 How to do it better

1. **For each escalation, name the invariant that broke.** "BFS doesn't work because edges aren't unit weight" is gold. Without that line, you sound like you're guessing.
2. **At scale, explicitly drop accuracy for tractability.** "If exact is infeasible, here's the approximation tier I'd reach for." Interviewers love seeing the engineer who knows when to stop optimising.
3. **Ask permission to abandon the perfect algorithm.** "If A\* is still too slow, do you want me to think about caching common substructures, or accept an approximate result?"

---

## 🃏 Cheatsheet for escalating problems

- BFS for unit weights; 0-1 BFS for {0,1} weights; Dijkstra for non-negative; Bellman-Ford / SPFA for negatives.
- Adding state to a node (`(r, c, k)`) is often cheaper than changing the algorithm.
- Bidirectional search for huge known-target searches.
- A* when a tight admissible heuristic exists.
- Hierarchical decomposition when the grid won't fit.
- *Always* check problem well-posedness (negative cycles, integer overflow, multiple valid paths).
