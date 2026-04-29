# Design a Parking Lot

> The "hello world" of LLD interviews. Asked at Amazon, Microsoft, Atlassian, Uber, almost everywhere.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design a parking-lot system. Cars and bikes (and trucks) come in. They get assigned spots. When they leave, they pay. Multi-floor. Different vehicle types use different-sized spots. Pricing depends on duration and vehicle type."*

A 30-45 minute LLD round. The interviewer expects:

1. **Clarifying questions** (don't dive into code).
2. **Class diagram sketch** (could be a list of classes + relationships).
3. **Code for 2-3 key methods** (`park`, `unpark`, `find_spot`).
4. **Consideration of growth** (concurrency, multiple lots, online booking).

---

## ❓ Clarifying questions

1. **Vehicle types?** Bike, Car, Truck — each fitting different spot sizes?
2. **Spot types?** Compact / Large / Bike-only / EV (with charger)?
3. **Multi-floor?** Single lot or building?
4. **Entry / exit gates?** One or many? Reservations?
5. **Pricing model?** Hourly? Tiered? Day-pass?
6. **Payment methods?** Cash / card / app?
7. **Concurrency?** Multiple cars arriving simultaneously?
8. **Display board?** Show free spots per floor?

**Default assumptions** (state out loud):

- 3 vehicle types: Bike, Car, Truck.
- 3 spot types: Bike, Compact, Large.
- Multi-floor.
- Hourly pricing, vehicle-type-specific.
- Single entry, single exit; concurrent-safe.
- Display board per floor.

---

## 🏛️ Class design

### Core entities

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import uuid

class VehicleType(Enum):
    BIKE = "BIKE"
    CAR = "CAR"
    TRUCK = "TRUCK"

class SpotType(Enum):
    BIKE = "BIKE"
    COMPACT = "COMPACT"
    LARGE = "LARGE"

# Which spot can fit which vehicle
FITS: dict[VehicleType, list[SpotType]] = {
    VehicleType.BIKE: [SpotType.BIKE, SpotType.COMPACT, SpotType.LARGE],
    VehicleType.CAR: [SpotType.COMPACT, SpotType.LARGE],
    VehicleType.TRUCK: [SpotType.LARGE],
}


@dataclass
class Vehicle:
    plate: str
    type: VehicleType
```

### Spot, Floor, Lot

```python
@dataclass
class Spot:
    id: str
    floor: int
    type: SpotType
    occupied_by: Vehicle | None = None

    def is_free(self) -> bool:
        return self.occupied_by is None

    def park(self, v: Vehicle):
        self.occupied_by = v

    def vacate(self):
        self.occupied_by = None


class Floor:
    def __init__(self, number: int, spots: list[Spot]):
        self.number = number
        self.spots = spots
        # Bucket by type for O(1) free-spot pick
        self._free: dict[SpotType, list[Spot]] = {
            t: [s for s in spots if s.type == t] for t in SpotType
        }
        self._lock = threading.Lock()

    def find_spot(self, vt: VehicleType) -> Spot | None:
        with self._lock:
            for st in FITS[vt]:                # smallest fitting first
                for s in self._free[st]:
                    if s.is_free():
                        return s
            return None
```

### Ticket + Pricing (Strategy pattern)

```python
@dataclass
class Ticket:
    id: str
    vehicle: Vehicle
    spot: Spot
    entry_time: datetime
    exit_time: datetime | None = None
    fee: float | None = None


class PricingStrategy(ABC):
    @abstractmethod
    def fee(self, t: Ticket) -> float: ...


class HourlyPricing(PricingStrategy):
    RATES = {
        VehicleType.BIKE:  10.0,
        VehicleType.CAR:   20.0,
        VehicleType.TRUCK: 50.0,
    }

    def fee(self, t: Ticket) -> float:
        assert t.exit_time is not None
        hours = max(1, int((t.exit_time - t.entry_time).total_seconds() // 3600) + 1)
        return hours * self.RATES[t.vehicle.type]
```

### The Lot (Facade)

```python
class ParkingLot:
    def __init__(self, floors: list[Floor], pricing: PricingStrategy):
        self.floors = floors
        self.pricing = pricing
        self.tickets: dict[str, Ticket] = {}
        self._lock = threading.Lock()

    def park(self, v: Vehicle) -> Ticket | None:
        for f in self.floors:
            spot = f.find_spot(v.type)
            if spot is not None:
                with self._lock:
                    if not spot.is_free():     # double-check after coarse lock
                        continue
                    spot.park(v)
                    t = Ticket(
                        id=str(uuid.uuid4()),
                        vehicle=v, spot=spot,
                        entry_time=datetime.utcnow(),
                    )
                    self.tickets[t.id] = t
                    return t
        return None                             # lot full

    def unpark(self, ticket_id: str) -> float:
        with self._lock:
            t = self.tickets.get(ticket_id)
            if t is None or t.exit_time is not None:
                raise ValueError("invalid ticket")
            t.exit_time = datetime.utcnow()
            t.fee = self.pricing.fee(t)
            t.spot.vacate()
            return t.fee
```

---

## 🧪 Walkthrough

```python
# Build a tiny lot
floor = Floor(0, [
    Spot("A1", 0, SpotType.BIKE),
    Spot("A2", 0, SpotType.COMPACT),
    Spot("A3", 0, SpotType.LARGE),
])
lot = ParkingLot([floor], HourlyPricing())

car = Vehicle("MH04AB1234", VehicleType.CAR)
ticket = lot.park(car)              # → assigned A2 (compact, smallest fit)
# ... time passes ...
fee = lot.unpark(ticket.id)         # → 20.0 for 1 hour
```

The car got the **smallest fitting spot** (Compact, not Large) — that's the `FITS` ordering.

---

## 🎯 Patterns + SOLID applied

| Decision | Pattern / principle |
|---|---|
| `PricingStrategy` ABC + `HourlyPricing` impl | **Strategy** + **Open/Closed** |
| `Spot` doesn't know about vehicles' fee logic | **Single Responsibility** |
| `ParkingLot` exposes `park` / `unpark` over many internals | **Facade** |
| `Floor` finds smallest-fitting spot via per-type buckets | **Composite** (Lot → Floor → Spot) |
| Could add `EVSpot extends Spot with charger` later | **Liskov** (must respect Spot contract) |

---

## 🚀 Extensions interviewers like to probe

??? question "Multiple lots / city-wide booking?"

    Add a `LotRegistry` keyed by location. Add `find_lot(coords)` that picks the nearest lot with a free fitting spot. Uses the same H3-style geo indexing as ride-sharing.

??? question "Reservations?"

    Add a `Reservation` entity with a hold time. `find_spot` skips spots reserved within the next N minutes. On entry, validate reservation; on no-show, release.

??? question "Concurrency at scale?"

    Replace the coarse `_lock` with per-spot atomic CAS (e.g. Redis `SET NX EX`). Each spot is a key; first writer wins. Failed claim → try next candidate.

??? question "EV charging?"

    `EVSpot(Spot)` with a charger reference. Pricing strategy adds an energy component. `FITS` for EVs: `[EV_SPOT, COMPACT, LARGE]` (EV-priority).

??? question "Display board / live counts?"

    Per-floor `free_count` updated on `park` / `vacate`. Push to display via Observer (subject = Floor, observers = displays + APIs).

??? question "What if the lot is huge — say 10K spots?"

    Per-type indexing already gives O(1) free-spot pick. But if `find_spot` scans 10K-element lists, replace with a **deque** of free spots — pop on park, push on vacate.

??? question "What about valet / multi-step parking?"

    Adds an `Attendant` role and a queue. Uses Command pattern: each `(park, vehicle, slot)` is a command, executed by an attendant.

??? question "Audit log?"

    Every state change emits an event (Observer). Persist to append-only log for billing reconciliation and disputes.

---

## ⏱️ Pacing

| Minute | What you should be doing |
|---|---|
| 0–3 | Clarifying questions; default assumptions stated. |
| 3–8 | Class list on whiteboard: `Vehicle`, `Spot`, `Floor`, `Lot`, `Ticket`, `Pricing`. Relationships drawn. |
| 8–25 | Code core: enums, `find_spot`, `park`, `unpark`. |
| 25–35 | Extensions: pricing strategies, concurrency, multi-lot. |
| 35–45 | Q&A; dive into one extension deeply. |

---

## 🪤 Common mistakes

??? warning "One God class for the lot"

    Don't put pricing, parking, ticketing, persistence in `ParkingLot`. Decompose.

??? warning "Strings for vehicle types"

    Use `Enum`. Strings are typo-magnets and not exhaustively checkable.

??? warning "Forgetting concurrency"

    Two cars arriving at once can both think a spot is free. Mention locking even if you don't fully implement it.

??? warning "Hard-coding pricing logic"

    Use Strategy from the start. Even one pricing model — the abstraction signals OOP maturity.

??? warning "Vehicle-spot fit logic in 6 places"

    Centralise in the `FITS` dict (or `vehicle.fits(spot)` method). Don't duplicate.

---

## ➡️ Where this connects

- [OOP fundamentals](../01-oop-fundamentals.md) — encapsulation, enums, dataclass.
- [SOLID](../02-solid-principles.md) — Strategy = OCP, Lot = Facade.
- [Design patterns](../03-design-patterns.md) — Strategy, Observer (extensions), Composite.
- Next LLD: [Elevator](02-elevator-system.md), [LRU Cache](03-lru-cache.md), [Vending Machine](04-vending-machine.md).
