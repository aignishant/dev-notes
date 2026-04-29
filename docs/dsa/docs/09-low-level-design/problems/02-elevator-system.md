# Design an Elevator System

> A multi-elevator, multi-floor system that schedules requests efficiently. Tests state machines + scheduling + concurrency.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design an elevator system for a building with N floors and M elevators. Users press a button on a floor to call an elevator. Elevators move up/down, open doors, accept passengers. Optimise so calls are answered quickly."*

A 30-45 minute LLD round. Interviewer expects:

1. **Clarifying questions**.
2. **State machine** for an elevator (Idle / Moving / Stopped / Doors-Open).
3. **Scheduling logic** for which elevator answers a call.
4. **Concurrency thinking**: many calls arriving simultaneously.

---

## ❓ Clarifying questions

1. **How many floors?** Up to 50 typical for an office tower.
2. **How many elevators?** 4-6 typical.
3. **Floor buttons or elevator buttons?** Both — a hall call (up/down at a floor) vs a cabin call (destination floor).
4. **Door behaviour?** Open on stop, close after timeout, can re-open if blocked.
5. **Express elevators / zoning?** Skip lower floors for a high-floor zone? Out-of-scope unless asked.
6. **Capacity?** Max persons / weight per cabin?
7. **Maintenance mode?** Out-of-rotation elevators?

**Default assumptions**:

- 20 floors, 4 elevators.
- Hall calls (up/down) + cabin calls (destination).
- Door auto-close after 5s.
- No zoning; basic SCAN/LOOK scheduling.
- Capacity 10 persons; pause new boarding at limit.

---

## 🏛️ Class design

### Enums

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import threading
import heapq

class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0

class DoorState(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class ElevatorState(Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    STOPPED = "STOPPED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
```

### Requests

```python
@dataclass(frozen=True)
class HallCall:
    """Pressed at a floor to summon an elevator."""
    floor: int
    direction: Direction         # UP or DOWN

@dataclass(frozen=True)
class CabinCall:
    """Pressed inside an elevator to go to a destination."""
    elevator_id: int
    floor: int
```

### Elevator (state machine)

```python
class Elevator:
    def __init__(self, id: int, capacity: int = 10):
        self.id = id
        self.capacity = capacity
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.state = ElevatorState.IDLE
        self.door = DoorState.CLOSED
        # Pending stops in current direction (sorted)
        self.up_stops: list[int] = []           # min-heap
        self.down_stops: list[int] = []         # max-heap (negate)
        self.passengers = 0
        self.lock = threading.Lock()

    # --- public API ---
    def add_stop(self, floor: int):
        with self.lock:
            if floor > self.current_floor:
                heapq.heappush(self.up_stops, floor)
            elif floor < self.current_floor:
                heapq.heappush(self.down_stops, -floor)
            # If floor == current_floor, just open doors

    def step(self):
        """Called every simulation tick."""
        with self.lock:
            if self.state == ElevatorState.STOPPED:
                self._handle_stop()
                return

            target = self._next_target()
            if target is None:
                self.state = ElevatorState.IDLE
                self.direction = Direction.IDLE
                return

            self.state = ElevatorState.MOVING
            if target > self.current_floor:
                self.direction = Direction.UP
                self.current_floor += 1
            elif target < self.current_floor:
                self.direction = Direction.DOWN
                self.current_floor -= 1

            if self.current_floor == target:
                self._arrive(target)

    # --- internals ---
    def _next_target(self) -> int | None:
        if self.direction == Direction.UP and self.up_stops:
            return self.up_stops[0]
        if self.direction == Direction.DOWN and self.down_stops:
            return -self.down_stops[0]
        # Idle or just finished a direction — flip
        if self.up_stops:
            self.direction = Direction.UP
            return self.up_stops[0]
        if self.down_stops:
            self.direction = Direction.DOWN
            return -self.down_stops[0]
        return None

    def _arrive(self, floor: int):
        # Pop the floor we just reached
        if self.up_stops and self.up_stops[0] == floor:
            heapq.heappop(self.up_stops)
        elif self.down_stops and -self.down_stops[0] == floor:
            heapq.heappop(self.down_stops)
        self.state = ElevatorState.STOPPED
        self.door = DoorState.OPEN

    def _handle_stop(self):
        # In real system, wait for passenger boarding signal / timeout
        self.door = DoorState.CLOSED
        self.state = ElevatorState.IDLE
```

### Scheduler (Strategy pattern)

```python
class Scheduler(ABC):
    @abstractmethod
    def pick(self, elevators: list[Elevator], call: HallCall) -> Elevator: ...


class NearestCarScheduler(Scheduler):
    """Pick the elevator that can serve the call fastest."""

    def pick(self, elevators, call):
        best, best_score = None, float("inf")
        for e in elevators:
            if e.state == ElevatorState.OUT_OF_SERVICE:
                continue
            score = self._score(e, call)
            if score < best_score:
                best_score, best = score, e
        if best is None:
            raise NoElevatorAvailable
        return best

    def _score(self, e: Elevator, call: HallCall) -> int:
        # Idle: just distance.
        if e.direction == Direction.IDLE:
            return abs(e.current_floor - call.floor)
        # Moving towards the call AND in the right direction → distance.
        if e.direction == call.direction:
            if (call.direction == Direction.UP and e.current_floor <= call.floor) or \
               (call.direction == Direction.DOWN and e.current_floor >= call.floor):
                return abs(e.current_floor - call.floor)
        # Wrong direction or past the floor → penalise (must finish current run first).
        return abs(e.current_floor - call.floor) + 100
```

### The Controller (Facade)

```python
class ElevatorController:
    def __init__(self, n_elevators: int, n_floors: int, scheduler: Scheduler):
        self.elevators = [Elevator(i) for i in range(n_elevators)]
        self.n_floors = n_floors
        self.scheduler = scheduler

    def hall_call(self, call: HallCall) -> int:
        e = self.scheduler.pick(self.elevators, call)
        e.add_stop(call.floor)
        return e.id

    def cabin_call(self, call: CabinCall):
        e = self.elevators[call.elevator_id]
        e.add_stop(call.floor)

    def tick(self):
        for e in self.elevators:
            e.step()
```

---

## 🧪 Walkthrough

```python
ctrl = ElevatorController(n_elevators=2, n_floors=10, scheduler=NearestCarScheduler())

# Person on floor 5 presses UP
ctrl.hall_call(HallCall(floor=5, direction=Direction.UP))
# → Elevator 0 (idle at floor 0) is chosen (closer? actually tied → first match)
# → It's added stop=5

# Tick the simulation
for _ in range(10):
    ctrl.tick()

# Once it stops at floor 5, person boards and presses 9
ctrl.cabin_call(CabinCall(elevator_id=0, floor=9))
```

---

## 🎯 Patterns + SOLID applied

| Decision | Pattern / principle |
|---|---|
| `Scheduler` ABC + `NearestCarScheduler` | **Strategy** + **Open/Closed** — swap to `LookScheduler` later. |
| `Direction`, `DoorState`, `ElevatorState` enums | Type-safe state. |
| Elevator owns its state machine; Controller orchestrates | **Single Responsibility**. |
| `tick()` is the only mutator path | Predictable, testable. |
| Per-elevator lock | Concurrency boundary. |

---

## 🚀 Extensions

??? question "Improve scheduling — what's better than nearest-car?"

    **LOOK / SCAN** algorithms: elevator only reverses direction when its current-direction queue is empty. Reduces wasted travel. Or **Up-peak / Down-peak / Sabbath** modes for office buildings.

??? question "Capacity?"

    Track `passengers`. On boarding, if at capacity, don't accept more for this stop. Cabin call may "skip" floors when full → drop to lobby express.

??? question "Multiple call buttons pressed simultaneously?"

    All hall calls flow through Controller. Scheduler picks one elevator per call. Calls remain pending until an elevator confirms a stop on that floor. If no elevator is available, queue.

??? question "Failure / out-of-service?"

    Elevator reports state `OUT_OF_SERVICE`. Scheduler skips it. Existing passengers in cabin still go to their destination (last action before disable).

??? question "Earthquake / fire mode?"

    Override behaviour: all elevators go to ground floor, doors open, ignore all calls. Implement as a Controller-wide directive.

??? question "Smart scheduling with destination dispatch?"

    Modern systems: passenger types destination *before* boarding (lobby panel). Controller groups passengers heading to same/nearby floors into the same cabin. Reduces stops. Used in skyscrapers.

??? question "How would you simulate this for testing?"

    Replace real-time `tick()` with a discrete event simulator: a min-heap of `(time, event)` events. Tests run in millisecond simulated time, not real time.

---

## ⏱️ Pacing

| Minute | What |
|---|---|
| 0–3 | Clarifying questions; defaults stated. |
| 3–10 | State machine drawn. Pseudocode for `Elevator.step`. |
| 10–25 | Code Scheduler + Controller. |
| 25–35 | Pick one extension (LOOK / capacity / failure) and code it. |
| 35–45 | Q&A. |

---

## 🪤 Common mistakes

??? warning "Single shared queue for all elevators"

    Each elevator has its own pending stops. A shared queue plus a "who picks up?" question is messier than per-elevator state.

??? warning "Boolean flags instead of state"

    `is_moving`, `is_idle`, `door_open` — combinatorial chaos. Use `Enum` + state machine.

??? warning "Direction as string"

    `"up"` / `"down"` / `"idle"` is typo-prone. Enum.

??? warning "Mixing UI events into core model"

    Floor button presses are events; elevator state is the model. Keep them separate.

??? warning "Forgetting reverse-direction logic"

    Elevator at floor 8 going DOWN, passenger at floor 5 presses UP — what happens? Service after the down-run, not now. Make the rule explicit.

---

## ➡️ Where this connects

- [SOLID](../02-solid-principles.md) — Strategy gives Open/Closed.
- [Design patterns](../03-design-patterns.md) — State, Strategy, Observer (call boards).
- Other LLD: [Parking Lot](01-parking-lot.md), [LRU Cache](03-lru-cache.md), [Vending Machine](04-vending-machine.md).
