# Type Hints — Best Practices

## The Rule

> *"Use Python type hints throughout the codebase."* — from the deep-dive docs.

Type hints are **not optional** in the Content Hub. `mp validate` enforces their presence on public APIs; `ty` verifies correctness.

## The Core Idiom (Memorize This Header)

Every action/connector/job file starts with:

```python
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from TIPCommon.base.action import Action
from TIPCommon.extraction import extract_action_param
from TIPCommon.validation import ParameterValidator

if TYPE_CHECKING:
    from TIPCommon.base.interfaces import ApiClient
    from TIPCommon.types import JSON, Contains

SCRIPT_NAME: str = "My Action"
```

Five components:

1. `from __future__ import annotations` — enables modern hint syntax
2. Standard library imports
3. Third-party imports (TIPCommon is third-party from your integration's perspective)
4. `TYPE_CHECKING` block for hint-only imports
5. Module-level constants with type annotations

## Modern Syntax (3.10+)

```python
# Old                             # Modern (use these)
from typing import List           list[str]
from typing import Dict           dict[str, int]
from typing import Tuple          tuple[int, ...]
from typing import Optional[X]    X | None
from typing import Union[X, Y]    X | Y
from typing import Type[X]        type[X]
```

The repo uses modern syntax. Ruff's `UP` rules auto-upgrade legacy hints.

## Function Signatures

```python
def enrich_entities(
    entities: list[Entity],
    threshold: int = 50,
    include_internal: bool = False,
) -> dict[str, JSON]:
    ...
```

Rules:

- Every parameter typed
- Return type always present (use `-> None` for no return)
- Default values after type annotations

## Class Attributes

```python
class MyAction(Action):
    name: str = "My Action"
    timeout_seconds: int = 30
    json_results: JSON = {}

    def __init__(self, name: str) -> None:
        self._api_client: ApiClient | None = None
        super().__init__(name)
```

## Protocols (Instead of ABCs Where Possible)

For interfaces your code consumes (rather than inherits), use `Protocol` for structural subtyping:

```python
from typing import Protocol

class ApiClient(Protocol):
    base_url: str

    def get(self, path: str) -> dict: ...
    def post(self, path: str, body: dict) -> dict: ...
```

Any class with those methods satisfies the protocol — no inheritance required. TIPCommon uses this heavily under `base/interfaces/`.

## Generics

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value
```

TIPCommon's `Action(Generic[ApiClient])` is the pattern you'll see most often.

## Type Aliases

For complex types used repeatedly:

```python
from typing import TypeAlias

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

EntityId: TypeAlias = str
EnrichmentKey: TypeAlias = str
```

TIPCommon defines these in `TIPCommon.types` — import them.

## Narrowing with `isinstance` and Guards

```python
def process(entity: Entity) -> None:
    if entity.entity_type != EntityTypes.ADDRESS:
        return
    # After this guard, `ty` narrows knowledge
    process_ip_address(entity.identifier)
```

Type checkers understand early returns and narrow accordingly.

## `TypedDict` for Dict-Shaped Data

When a dict has known keys:

```python
from typing import TypedDict

class AlertPayload(TypedDict):
    display_name: str
    events: list[dict]
    severity: str
```

```python
alert: AlertPayload = {"display_name": "...", "events": [...], "severity": "High"}
alert["display_name"]  # autocomplete, type-checked
```

Useful for stateful third-party JSON payloads where Pydantic is overkill.

## `Literal` for String Enums

```python
from typing import Literal

def set_priority(priority: Literal["Low", "Medium", "High", "Critical"]) -> None: ...

set_priority("High")       # ok
set_priority("Urgent")     # type error
```

More lightweight than creating a `StrEnum` for one-off cases.

## `Never` / `NoReturn` for Terminal Functions

```python
from typing import NoReturn

def fail_fast(message: str) -> NoReturn:
    raise RuntimeError(message)
```

Signals to the type checker that control never returns. Eliminates "missing return" warnings on branches that call the function.

## The `Self` Type (3.11+)

```python
from typing import Self

class ChainableBuilder:
    def add_header(self, name: str, value: str) -> Self:
        self.headers[name] = value
        return self

    def add_query(self, key: str, value: str) -> Self:
        self.query[key] = value
        return self
```

Subclasses now return their own type, not the parent. Clean for fluent APIs.

## Pragma: `# type: ignore`

When the type checker genuinely can't reason:

```python
result = legacy_function()  # type: ignore[no-untyped-call]
```

**Always include the specific error code** — `# type: ignore` alone suppresses everything and is forbidden by config.

## What Gets Reviewed Hard

| Item | Expectation |
|---|---|
| Missing return type | Blocks PR |
| `Any` without justification | Comment needed |
| `# type: ignore` without code | Blocks PR |
| `# type: ignore` without comment explaining why | Comment needed |
| Mutable default (`foo: list = []`) | Use `field(default_factory=list)` or `None`+factory |
| String-literal type (`"ApiClient"`) outside TYPE_CHECKING | Usually unnecessary; remove |

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `def foo(items = None)` with no type | `def foo(items: list | None = None)` |
| Forgetting return type on `__init__` | Add `-> None` |
| `List` / `Dict` / `Optional` (old-style) | Modernize: `list`, `dict`, `X | None` |
| Circular imports in hints | Move the import under `TYPE_CHECKING` |
| Using `Any` by reflex | Prefer `object`, Protocol, or a Union |

## Next

→ **[IDE Setup](ide-setup.md)**
