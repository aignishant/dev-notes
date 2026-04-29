# Tesla — 50 most-asked questions

> The 50 problems Tesla (Autopilot, Full Self-Driving, Megapack, Optimus) has asked most often. Same six-part shape as the [Google 50](google-50.md) page.

<span class="company-tag">Tesla</span> &nbsp; <span class="phase-status phase-inprogress">Phase 8 — company page</span>

---

## 🏢 What interviewing at Tesla is like

| Round | Length | Focus |
|---|---|---|
| **Recruiter screen** | 30 min | Background. |
| **Tech phone screen** | 60 min | Coding (C++ for kernel/embedded; Python for autonomy ML). |
| **Onsite — coding ×2** | 60 min each | Algorithms + low-level / real-time thinking. |
| **Onsite — domain** | 60 min | Embedded / signal-processing / ML / robotics depending on team. |
| **Onsite — system design** | 60 min | Vehicle telemetry, OTA updates, sensor fusion. |
| **Onsite — manager / Elon-style** | 30-45 min | Project deep-dive; expect to defend every claim. |

**Tesla style**: hardware-software-deeply-coupled. Real-time + safety-critical + scrappy. Fast pace, ruthless deadlines, Friday-night culture. Bias toward **first principles** thinking — they grade you on whether you'd reduce a complex problem to its physics.

---

## 🎯 What Tesla tests

| Signal | Where | How to show |
|---|---|---|
| First-principles reasoning | All | Reduce problems to their essence; avoid received wisdom. |
| Real-time / safety mindset | Domain | Bounded latency, watchdog timers, fault recovery. |
| Embedded sensibility | Domain | Memory budgets, no dynamic allocation in hot paths. |
| Pragmatism | All | Simplest thing that works > elegant thing that doesn't. |

---

## 🧩 Patterns Tesla loves

| Pattern | Frequency | Why |
|---|---|---|
| **Bit / SIMD thinking** | ⭐⭐⭐⭐ | Embedded / signal processing. |
| **Hash + sliding window** | ⭐⭐⭐⭐ | Standard. |
| **Heap / partial sort** | ⭐⭐⭐⭐ | Top-K detections. |
| **Graph BFS / DFS** | ⭐⭐⭐⭐ | Path planning, occupancy grids. |
| **DP** | ⭐⭐⭐⭐ | Trajectory optimisation. |
| **State machine design** | ⭐⭐⭐⭐⭐ | Autopilot lane-change, charging session FSM. |

---

## 📋 The 50 questions

### Arrays & strings (10)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 1 | Two Sum | <span class="diff-easy">Easy</span> | Hash | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 2 | Maximum Subarray | <span class="diff-medium">Medium</span> | Kadane | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 3 | Trapping Rain Water | <span class="diff-hard">Hard</span> | Two pointers | [✅](../../02-data-structures/arrays/01-array-basics.md) |
| 4 | Sliding Window Maximum | <span class="diff-hard">Hard</span> | Monotonic deque | 🚧 |
| 5 | Median of Two Sorted Arrays | <span class="diff-hard">Hard</span> | BS partition | 🚧 |
| 6 | Subarray Sum Equals K | <span class="diff-medium">Medium</span> | Prefix + hash | 🚧 |
| 7 | Set Matrix Zeroes | <span class="diff-medium">Medium</span> | In-place markers | 🚧 |
| 8 | Spiral Matrix | <span class="diff-medium">Medium</span> | Layer | 🚧 |
| 9 | Find Duplicate | <span class="diff-medium">Medium</span> | Floyd's | 🚧 |
| 10 | First Missing Positive | <span class="diff-hard">Hard</span> | Cyclic sort | 🚧 |

### Linked lists (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 11 | Reverse Linked List | <span class="diff-easy">Easy</span> | 3-pointer | 🚧 |
| 12 | LRU Cache | <span class="diff-medium">Medium</span> | Hash + DLL | 🚧 |
| 13 | Detect Cycle | <span class="diff-easy">Easy</span> | Floyd's | 🚧 |

### Trees (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 14 | Validate BST | <span class="diff-medium">Medium</span> | DFS bounds | 🚧 |
| 15 | LCA of Binary Tree | <span class="diff-medium">Medium</span> | Post-order | 🚧 |
| 16 | Serialize / Deserialize | <span class="diff-hard">Hard</span> | BFS | 🚧 |
| 17 | Tree of Calls (call graph) | <span class="diff-medium">Medium</span> | DFS | 🚧 |

### Graphs (6)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 18 | Number of Islands | <span class="diff-medium">Medium</span> | DFS | 🚧 |
| 19 | Course Schedule | <span class="diff-medium">Medium</span> | Topo sort | 🚧 |
| 20 | Network Delay Time | <span class="diff-medium">Medium</span> | Dijkstra | 📝 (see [Uber 50](uber-50.md)) |
| 21 | A* Path Planning | <span class="diff-hard">Hard</span> | Heap + heuristic | 📝 |
| 22 | Shortest Path in Grid (occupancy) | <span class="diff-medium">Medium</span> | BFS | 🚧 |
| 23 | Minimum Spanning Tree | <span class="diff-medium">Medium</span> | Kruskal | 🚧 |

### Heap / Top-K (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 24 | Top K Frequent Elements | <span class="diff-medium">Medium</span> | Heap | [✅](../../04-patterns/12-top-k-elements.md) |
| 25 | Find Median from Data Stream | <span class="diff-hard">Hard</span> | Two heaps | [✅](../../04-patterns/09-two-heaps.md) |
| 26 | Top K Detections per Frame | <span class="diff-medium">Medium</span> | Heap | 🚧 |
| 27 | Merge K Sensor Streams | <span class="diff-hard">Hard</span> | Heap | 🚧 |

### DP (5)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 28 | Climbing Stairs | <span class="diff-easy">Easy</span> | Fib DP | 🚧 |
| 29 | Coin Change | <span class="diff-medium">Medium</span> | Unbounded knapsack | 🚧 |
| 30 | Longest Increasing Subsequence | <span class="diff-medium">Medium</span> | DP + BS | 🚧 |
| 31 | Edit Distance | <span class="diff-hard">Hard</span> | 2D DP | 🚧 |
| 32 | Minimum Path Sum | <span class="diff-medium">Medium</span> | Grid DP | 🚧 |

### Bit / numerics (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 33 | Single Number | <span class="diff-easy">Easy</span> | XOR | 🚧 |
| 34 | Number of 1 Bits | <span class="diff-easy">Easy</span> | Brian Kernighan | 🚧 |
| 35 | Pow(x, n) | <span class="diff-medium">Medium</span> | Binary exp | 📝 (see [Microsoft 50](microsoft-50.md)) |
| 36 | CRC32 | <span class="diff-medium">Medium</span> | Bit shift + table | 📝 |

### Search & sort (3)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 37 | Search in Rotated Sorted Array | <span class="diff-medium">Medium</span> | Modified BS | 🚧 |
| 38 | Sort Colors | <span class="diff-medium">Medium</span> | Dutch flag | 🚧 |
| 39 | Find Peak Element | <span class="diff-medium">Medium</span> | BS variant | 🚧 |

### State machines / concurrency (4)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 40 | Charging Session FSM | <span class="diff-medium">Medium</span> | FSM table | 📝 |
| 41 | Lane Change Controller | <span class="diff-hard">Hard</span> | FSM + safety guards | 🚧 |
| 42 | Bounded Blocking Queue | <span class="diff-medium">Medium</span> | Lock + cond var | 🚧 |
| 43 | Watchdog Timer | <span class="diff-medium">Medium</span> | Timer + reset | 🚧 |

### Design (7)

| # | Problem | Difficulty | Pattern | Status |
|---|---|---|---|---|
| 44 | Design Vehicle Telemetry | <span class="diff-hard">Hard</span> | Edge buffer + cellular | 📝 |
| 45 | Design OTA Update | <span class="diff-hard">Hard</span> | A/B partition + verify | 🚧 |
| 46 | Design Sensor Fusion Pipeline | <span class="diff-hard">Hard</span> | Time-aligned merge | 🚧 |
| 47 | Design Charging Network Router | <span class="diff-hard">Hard</span> | Capacity + ETA | 🚧 |
| 48 | Design Megapack Energy Scheduler | <span class="diff-hard">Hard</span> | Optimisation + grid prices | 🚧 |
| 49 | Design Replay Tool for Driving Logs | <span class="diff-hard">Hard</span> | Time-indexed events | 🚧 |
| 50 | Design Fleet Health Dashboard | <span class="diff-medium">Medium</span> | Aggregation + alerts | 🚧 |

---

## 🔬 Three deep-dives

### Deep-dive 1 — A* Path Planning

??? question "Story: plan a path on an occupancy grid from start to goal. Avoid obstacles."

    A* combines BFS-style exploration with a heuristic estimate of remaining cost. With an admissible heuristic (e.g., Manhattan distance), A* is optimal AND faster than plain Dijkstra.

```python
import heapq

def astar(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
    """grid[r][c] = 0 free, 1 blocked. Returns path or [] if none."""
    R, C = len(grid), len(grid[0])

    def h(p: tuple[int, int]) -> int:
        return abs(p[0] - goal[0]) + abs(p[1] - goal[1])

    open_set: list[tuple[int, tuple[int, int]]] = []
    heapq.heappush(open_set, (h(start), start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], int] = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))
        r, c = current
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < R and 0 <= nc < C) or grid[nr][nc] == 1:
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get((nr, nc), float("inf")):
                came_from[(nr, nc)] = current
                g_score[(nr, nc)] = tentative_g
                heapq.heappush(open_set, (tentative_g + h((nr, nc)), (nr, nc)))
    return []
```

??? abstract "Complexity"

    O(E log V) worst case. With a tight heuristic, exploration shrinks dramatically.

??? tip "Tesla follow-up: 'now make it run at 100 Hz on a 500x500 grid'"

    Two tricks: (1) replace dict with flat arrays sized R·C — O(1) access without hashing; (2) use **bucket queue** instead of heap when costs are integer (D'Esopo-Pape). Pre-compute neighbors for the active region.

---

### Deep-dive 2 — Charging Session FSM

??? question "Story: a Supercharging session has phases — IDLE → PLUG_INSERTED → AUTH → NEGOTIATING → CHARGING → STOPPING → IDLE. Faults can hit anywhere."

    State table with explicit transitions. Each transition is a `(state, event) → (next_state, action)` cell. Faults always route to a SAFE state.

```python
from enum import Enum
from typing import Callable

class State(Enum):
    IDLE = "IDLE"
    PLUG_IN = "PLUG_IN"
    AUTH = "AUTH"
    NEGOTIATE = "NEGOTIATE"
    CHARGING = "CHARGING"
    STOPPING = "STOPPING"
    FAULT = "FAULT"

class Event(Enum):
    PLUG = "PLUG"
    AUTH_OK = "AUTH_OK"
    NEGOTIATE_OK = "NEGOTIATE_OK"
    UNPLUG = "UNPLUG"
    FAULT_RAISED = "FAULT_RAISED"
    RESET = "RESET"

Action = Callable[[], None]

def noop() -> None:
    pass

class ChargingFSM:
    def __init__(self):
        self.state = State.IDLE
        self.table: dict[tuple[State, Event], tuple[State, Action]] = {
            (State.IDLE, Event.PLUG): (State.PLUG_IN, noop),
            (State.PLUG_IN, Event.AUTH_OK): (State.AUTH, noop),
            (State.AUTH, Event.NEGOTIATE_OK): (State.NEGOTIATE, noop),
            (State.NEGOTIATE, Event.NEGOTIATE_OK): (State.CHARGING, noop),
            (State.CHARGING, Event.UNPLUG): (State.STOPPING, noop),
            (State.STOPPING, Event.UNPLUG): (State.IDLE, noop),
            (State.FAULT, Event.RESET): (State.IDLE, noop),
        }

    def step(self, event: Event) -> None:
        # any state + FAULT_RAISED → FAULT
        if event == Event.FAULT_RAISED:
            self.state = State.FAULT
            return
        key = (self.state, event)
        if key in self.table:
            self.state, action = self.table[key]
            action()
        # else: ignore unsolicited events (or log)
```

??? abstract "Complexity"

    O(1) per event. Memory O(S · E) for the table.

??? tip "Tesla follow-up: 'how do you test this?'"

    Generate every (state, event) pair; assert the transition is **defined or explicitly rejected**. Combined with a fuzzer over event sequences, you find unreachable states fast. CI gate this.

---

### Deep-dive 3 — Vehicle Telemetry Pipeline

??? question "Story: 5M cars stream sensor data. Cellular is intermittent. Don't lose data; don't bankrupt the bandwidth budget."

    On-vehicle: buffer + prioritise + compress + batch. Upload over LTE in opportunistic windows. Backend: ingest → time-partition → cold-store.

```python
from dataclasses import dataclass
from collections import deque
import time

@dataclass
class TelemetryEvent:
    ts: float
    priority: int  # 0 = critical, 9 = nice-to-have
    payload: bytes

class EdgeBuffer:
    def __init__(self, max_bytes: int = 64 * 1024 * 1024):
        self.q: deque[TelemetryEvent] = deque()
        self.size = 0
        self.cap = max_bytes

    def push(self, ev: TelemetryEvent) -> None:
        # if full, drop lowest-priority oldest event
        while self.size + len(ev.payload) > self.cap and self.q:
            victim = max(range(len(self.q)), key=lambda i: (self.q[i].priority, self.q[i].ts))
            removed = self.q[victim]
            del self.q[victim]
            self.size -= len(removed.payload)
        self.q.append(ev)
        self.size += len(ev.payload)

    def drain_for_upload(self, max_bytes: int) -> list[TelemetryEvent]:
        # send oldest critical first
        sorted_events = sorted(self.q, key=lambda e: (e.priority, e.ts))
        out: list[TelemetryEvent] = []
        used = 0
        for e in sorted_events:
            if used + len(e.payload) > max_bytes:
                break
            out.append(e)
            used += len(e.payload)
        for e in out:
            self.q.remove(e)
            self.size -= len(e.payload)
        return out
```

??? abstract "Complexity"

    `push` O(N) worst case (priority eviction); amortised much less. `drain` O(N log N).

??? tip "Tesla follow-up: 'what about a crash? You can't trust on-vehicle storage.'"

    Mirror the buffer to flash with `fsync` on critical events only. After reboot, replay-on-connect. Critical data (collision frame) goes through a redundant path — small in size, blast it out 3x with dedup ID.

---

## 🛡️ Day-of tips

- **First principles**: when stuck, restate the problem as physics or constraint inequalities. They notice when you do.
- **Defend everything**: any claim — performance number, complexity, design choice — be ready to back up. Vague answers get pressed.
- **Real-time vocabulary**: deterministic, jitter, watchdog, hard real-time vs soft real-time.
- **No fluff**: no "design patterns" name-dropping for its own sake. Name them only when they earn their keep.
