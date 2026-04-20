# Base Classes — Action, Connector, Job

## The Design Pattern: Template Method

> *"All three base classes use the **Template Method** pattern. The base class's `run()` (or `start()`) defines the execution skeleton as a sequence of phase calls — `_extract_params` → `_validate_params` → `_init_api_clients` → `_perform_action` — and the subclass fills in only the abstract phase methods. The base handles logging, timing, error wrapping, timeout checks, SDK finalization, and output formatting — uniformly across every integration."*

That's the elevator pitch. Memorize it.

## `Action` Base Class

### Source Location

`packages/tipcommon/TIPCommon/src/TIPCommon/base/action/base_action.py`

### Class Declaration

```python
from abc import ABC, abstractmethod
from typing import Generic

from ..interfaces import ApiClient, ScriptLogger

class Action(ABC, Generic[ApiClient]):
    """A Unified Generic infrastructure implementation for Chronicle SOAR
    (Formerly known as 'Siemplify') Action development."""
```

**Two key things:**

- It's `ABC` — forces subclasses to implement abstract methods.
- It's `Generic[ApiClient]` — typed parameter lets subclasses declare the specific API client type.

### Constructor Signature

```python
def __init__(self, name: str):
    self._name = name
    self._soar_action = SiemplifyAction()   # SDK object
    self._api_client: ApiClient | None = None
    self._action_start_time = unix_now()
    self._logger = create_logger(...)
    self._params = create_params_container()

    self._entities_to_update = []
    self.json_results: JSON = {}

    # Case result collectors
    self._attachments = []
    self._contents = []
    self._data_tables = []
    self._html_reports = []
    self._links = []
    self._markdowns = []

    # Insights
    self._entity_insights = []
    self._case_insights = []

    # Final state
    self._execution_state = ExecutionState.IN_PROGRESS
    self._result_value = False
    self._output_message = ""
    self._error_output_message = ""
```

### Abstract Methods (Subclass MUST Implement)

```python
@abstractmethod
def _extract_action_parameters(self) -> None: ...

@abstractmethod
def _validate_params(self) -> None: ...

@abstractmethod
def _init_api_clients(self) -> Contains[ApiClient]: ...

@abstractmethod
def _perform_action(self, entity: Entity | None = None) -> None: ...
```

### The `run()` Method — What the Base Does for You

```python
def run(self) -> None:
    try:
        self._extract_action_parameters()
        self._validate_params()
        self._api_client = self._init_api_clients()
        self._perform_action()
        self._finalize_success()
    except ParameterExtractionError as e:
        self._finalize_parameter_failure(e)
    except CaseResultError as e:
        self._finalize_case_result_failure(e)
    except SDKWrapperError as e:
        self._finalize_sdk_failure(e)
    except GeneralActionException as e:
        self._finalize_general_failure(e)
    except Exception as e:
        self._finalize_unknown_failure(e)
    finally:
        self._commit_entity_updates()
        self._commit_case_results()
        self._soar_action.end(
            output_message=self._output_message or self._error_output_message,
            result_value=str(self._result_value).lower(),
            execution_state=self._execution_state,
        )
```

Every failure mode — parameter extraction, validation, SDK, or totally unknown — produces a **user-friendly output message and the correct execution state**. Your subclass literally cannot forget error handling.

### Subclass Example (Minimum Viable)

```python
from TIPCommon.base.action import Action
from TIPCommon.extraction import extract_action_param
from TIPCommon.validation import ParameterValidator

SCRIPT_NAME = "My Action"

def main() -> None:
    MyAction(name=SCRIPT_NAME).run()

class MyAction(Action):
    def _extract_action_parameters(self) -> None:
        self.params.foo = extract_action_param(
            siemplify=self.soar_action,
            param_name="Foo",
            is_mandatory=True,
            print_value=True,
        )

    def _validate_params(self) -> None:
        validator = ParameterValidator(self.soar_action)
        # chain calls as needed

    def _init_api_clients(self) -> Contains[ApiClient]:
        return MyClient(api_key=self.params.api_key)   # or None if no client needed

    def _perform_action(self, _: None = None) -> None:
        result = self._api_client.do_thing(self.params.foo)
        self.json_results = result.to_dict()
        self._output_message = f"Did the thing with {self.params.foo}"
        self._result_value = True

if __name__ == "__main__":
    main()
```

That's **all you write**. The base class handles the rest.

### Per-Entity Variant

`_perform_action` accepts an optional `entity: Entity | None` argument. For entity-iterating actions, override the iteration helper:

```python
def _perform_action_on_entity(self, entity: Entity) -> None:
    """Called per entity; base orchestrates iteration."""
    ...
```

The base's `run()` detects this and calls `_perform_action_on_entity` once per target entity, handling the four-bucket categorization (enriched/limit/failed/missing) for you.

## `BaseConnector` / `Connector`

### Source Location

`packages/tipcommon/TIPCommon/src/TIPCommon/base/connector/base_connector.py` (base) and `.../connector.py` (concrete sync variant).

### Class Shape

```python
class BaseConnector(ABC):
    def __init__(self, script_name: str, is_test_run: bool = False):
        self._siemplify = SiemplifyConnectorExecution()
        self._script_name = script_name
        self._connector_start_time = unix_now()
        self._logger = ...
        self._is_test_run = is_test_run
        self._params = create_params_container()
        self._context = create_params_container()
        self._vars = create_params_container()
        self._env_common = GetEnvironmentCommonFactory.create_environment_common(...)
        self._error_msg = "Connector generic error"
```

### Abstract Methods

```python
@abstractmethod
def validate_params(self) -> None: ...

@abstractmethod
def read_context_data(self) -> None: ...

@abstractmethod
def init_managers(self) -> None: ...

@abstractmethod
def get_alerts(self) -> list[BaseAlert]: ...

@abstractmethod
def create_alert_info(self, alert: BaseAlert) -> AlertInfo: ...

@abstractmethod
def store_alert_in_cache(self, alert: BaseAlert) -> None: ...
```

### `start()` Lifecycle

```python
def start(self) -> None:
    try:
        self.extract_params()
        self.validate_params()
        self.read_context_data()
        self.init_managers()
        alerts = self.get_alerts()
        processed = []
        for alert in alerts:
            if self._deadline_reached():
                break
            if is_overflowed(alert_info := self.create_alert_info(alert)):
                self.logger.warning(f"Alert {alert.alert_id} overflowed")
                continue
            processed.append(alert_info)
            self.store_alert_in_cache(alert)
        if not self.is_test_run:
            self._save_context_data()
            self._siemplify.return_package(processed)
    except Exception as e:
        # Similar centralized error handling as Action
        self._finalize_failure(e)
```

### Sync vs Async

Two concrete subclasses:

- `TIPCommon.base.connector.connector.Connector` — **sync**, default choice
- `TIPCommon.base.connector.async_connector.AsyncConnector` — **async**, for high-throughput fan-out

Async variant overrides `get_alerts` to return a coroutine; base `start()` is async as well.

## `Job` / `BaseJob`

### Source Location

`packages/tipcommon/TIPCommon/src/TIPCommon/base/job/base_job.py` and specialized variants: `base_sync_job.py`, `base_job_refresh_token.py`, `job_case.py`.

### Class Shape

```python
class Job(ABC):
    def __init__(self, name: str):
        self._soar_job = SiemplifyJob()
        self._name = name
        self._logger = ...
        self._params = create_params_container()
        self._job_start_time = unix_now()

    @abstractmethod
    def _extract_job_params(self) -> None: ...

    @abstractmethod
    def _validate_params(self) -> None: ...

    @abstractmethod
    def _init_api_clients(self) -> Contains[ApiClient]: ...

    @abstractmethod
    def _perform_job(self) -> None: ...

    def start(self) -> None:
        try:
            self._extract_job_params()
            self._validate_params()
            self._api_client = self._init_api_clients()
            self._perform_job()
        except Exception as e:
            self._finalize_failure(e)
```

### Specialized Subclasses

- `BaseSyncJob` — scaffolding for bi-directional sync (outbound + inbound phases)
- `BaseJobRefreshToken` — periodically refreshes OAuth tokens persisted to context
- `JobCase` — helpers for iterating cases with paging

Prefer these over rewriting the wheel.

## Generic Type Parameter `ApiClient`

All three base classes have `Generic[ApiClient]`:

```python
class MyAction(Action[MyProductClient]):
    def _init_api_clients(self) -> MyProductClient:
        return MyProductClient(api_key=self.params.api_key)

    def _perform_action(self, _) -> None:
        # self._api_client is typed as MyProductClient — IDE autocompletes
        result = self._api_client.do_thing(...)
```

This gives **full IDE autocompletion** inside `_perform_action`, caught by `ty` static type checking before runtime.

## Interface Protocols — `ApiClient`, `Session`, `Authable`, `Apiable`, `Logger`

Under `TIPCommon/base/interfaces/`:

- `ApiClient` — protocol any API client should conform to (has `session`, `base_url`, `headers`)
- `Session` — HTTP session protocol
- `Authable` — something that can authenticate (has `login`, `refresh_token`, `logout`)
- `Apiable` — combines ApiClient + Authable
- `ScriptLogger` — the logger protocol

Use these as type hints instead of concrete SDK classes — keeps your code swappable and testable.

## Why Class-Based > Function-Based (The Lead Answer)

1. **Template Method** — consistent skeleton enforces identical lifecycle across every integration
2. **Centralized error handling** — every failure mode produces consistent output
3. **Consistent logging** — timing + phase markers for free
4. **Testability** — each phase method is independently unit-testable
5. **Type safety** — Generic ApiClient gives IDE + `ty` full inference
6. **Forced separation of concerns** — extraction/validation/init/perform can't be tangled together
7. **Reduced review surface** — reviewers scan 4 known methods, not arbitrary procedural code
8. **SDK abstraction** — if the SDK changes, the base class absorbs it; subclasses unchanged

That list is the full answer to "why class-based?" Use any three in an interview.

## Next

→ **[Extraction & Validation](extraction-validation.md)**
