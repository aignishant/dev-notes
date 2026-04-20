# TIPCommon & SOAR SDK — Interview Q&A

---

## Q1. What is TIPCommon and why does it exist?

TIPCommon is the shared runtime library that every integration depends on. It wraps the lower-level SOAR SDK with a consistent, typed, testable API — base classes for Actions/Connectors/Jobs, parameter extraction + validation helpers, time utilities, OAuth flows, encryption, caching, HTTP helpers. It exists to (a) DRY up boilerplate across 100+ integrations, (b) centralize error handling and logging, (c) shield integrations from SOAR SDK churn.

---

## Q2. What design pattern do the base classes use?

**Template Method.** The base class's `run()` (Action) / `start()` (Connector/Job) defines the execution skeleton as a sequence of phase method calls. Subclasses override only the abstract phase methods. The base handles logging, timing, error wrapping, timeout checks, SDK finalization, output formatting.

---

## Q3. What are the abstract methods I must implement in an Action subclass?

Four:

1. `_extract_action_parameters()` — pull params from SDK
2. `_validate_params()` — validate via `ParameterValidator`
3. `_init_api_clients()` — build + return the API client
4. `_perform_action(entity=None)` — business logic

---

## Q4. Why are extraction and validation split into two separate phases?

Different failure modes need different error messages. Extraction failure = "Param X is missing." Validation failure = "Param X must be a positive integer, got 'abc'." Telling an analyst "invalid param" in both cases is unhelpful. Separating the phases also lets you extract all params first (fast fail if any are missing) before doing expensive validation.

---

## Q5. What does `extract_action_param(input_type=bool)` actually do?

The SDK stores parameters as strings — booleans come through as `"true"` / `"false"` / `"True"` / `"False"`. `input_type=bool` coerces them to real Python booleans. Without it, `"false"` is a truthy string, which causes hilariously broken conditionals.

---

## Q6. Why would you set `print_value=False` on `extract_action_param`?

For passwords and secrets. `print_value=True` logs the value — logging a password is a CVSS-worthy security incident.

---

## Q7. Explain `Generic[ApiClient]` in the Action base class.

`class Action(ABC, Generic[ApiClient])` — the parametric type lets subclasses pin the specific API client type:

```python
class MyAction(Action[MyProductClient]):
    def _init_api_clients(self) -> MyProductClient:
        ...
```

Benefit: `self._api_client` is typed as `MyProductClient` inside `_perform_action`, so the IDE autocompletes methods and `ty` catches type errors before runtime. Standard generic type design.

---

## Q8. What's the difference between `TIPCommon.base.connector.Connector` and `AsyncConnector`?

Same Template Method pattern, different execution model. `Connector` (sync) is the default — serial alert processing, simpler to reason about. `AsyncConnector` uses `asyncio` — `get_alerts` is a coroutine, `start` is async. Use async when: (a) the third-party API tolerates concurrent requests, (b) alert volume per cycle is high, (c) per-alert detail fetches parallelize cleanly.

---

## Q9. What does `BaseSyncJob` add over `BaseJob`?

Scaffolding for bidirectional sync jobs. Exposes explicit outbound + inbound phase methods so you don't mix them. Handles the loop-prevention concerns (idempotency keys, author tags) that bidirectional sync needs.

---

## Q10. How does the Template Method base class handle timeouts?

It checks `is_approaching_action_timeout` (from `TIPCommon.smp_time`) before and during phase execution. On timeout, it sets `execution_state = EXECUTION_STATE_TIMEDOUT`, commits any partial results already staged (entity updates, case results), and calls `siemplify.end()` with a user-friendly timeout message. Subclass code doesn't need to remember to handle timeouts — but for long-running iterations (entity loops) you still check the deadline inside your own loop.

---

## Q11. Why does the repo keep old TIPCommon wheels under `whls/`?

Back-compat. Deployed integrations pin a specific version. Forcing them to 2.0.6 would require re-testing every one. Each integration's `pyproject.toml` points at the specific wheel via `[tool.uv.sources]`, so versions can coexist.

---

## Q12. If TIPCommon changes, do I need to update all my integrations?

Not immediately. Each integration pins its TIPCommon version via `pyproject.toml`. You can continue running 1.0.14 for years while writing new integrations on 2.0.6. That said, `mp validate` now **rejects new integrations pinning 1.x** — new work must use the latest 2.x. And legacy integrations are migrated opportunistically during feature work.

---

## Q13. Why is `soar-sdk` a dev-only dependency?

Because at runtime, the platform provides its own SDK build. If you ship your integration zip with a copy of the SDK in production dependencies, you get a **conflict** — the zipped SDK clashes with the platform's. Dev-only means you use it for IDE autocompletion + type checking locally, but it's not bundled into the deployable package.

---

## Q14. What does `Container` do in `TIPCommon.data_models`?

It's a dict-like bag with attribute access. Used for `self.params`:

```python
self.params.api_key = "..."      # set
x = self.params.api_key          # get
```

Safer than string indexing — typos fail loudly instead of silently returning None.

---

## Q15. What's `ParameterValidator.validate_json` and why not just use `json.loads`?

`validate_json` combines parsing + a user-facing error message in the base-class error flow. `json.loads` throws `JSONDecodeError` which propagates to a generic `GeneralActionException` with an ugly message. The validator produces something like "Parameter 'Alert JSON' is not a valid JSON string" — much better for analyst eyes.

---

## Q16. What problem does `EnvironmentCommon` solve?

Multi-tenant environment resolution for connectors. A single SOAR tenant can serve many BUs/regions; each alert must be tagged with the right environment. EnvironmentCommon takes three connector parameters — `Environment Field Name`, `Environment Regex Pattern`, `Default Environment` — and provides a single `get_environment(event)` call that resolves the env based on them. Keeps the regex logic out of connector code.

---

## Q17. Can you use EnvironmentCommon without TIPCommon?

Yes — it has no upward dependency. TIPCommon depends on EnvironmentCommon, but not vice versa. You can add just EnvironmentCommon for a script that only needs environment resolution.

---

## Q18. Walk me through what happens from `MyAction(...).run()` to `siemplify.end()`.

1. Constructor — builds `SiemplifyAction`, starts the clock, sets up `Container`, initializes collectors.
2. `run()` calls `_extract_action_parameters()` — subclass pulls params from SDK.
3. `_validate_params()` — subclass validates via `ParameterValidator`.
4. `_init_api_clients()` — subclass returns the API client.
5. `_perform_action()` — subclass does business logic, sets `self.json_results`, updates entities.
6. Base class checks for timeout, catches any exception, maps it to a specific `ExecutionState`.
7. Base class commits entity updates, case results, insights.
8. Base class calls `siemplify.end(output_message, result_value, execution_state)`.

Each phase has structured logging with start/end markers. Errors produce consistent user-facing messages.

---

## Q19. What happens if `_init_api_clients` returns `None`?

That's valid — some actions (like "Load JSON String to Object") don't need an API client. The base class handles `None` gracefully — `self._api_client` stays `None`, and `_perform_action` just doesn't access it. The return type is `Contains[ApiClient]` which includes `None`.

---

## Q20. How does TIPCommon shield integrations from SDK changes?

The SDK can change its method signatures, class names, or behavior between releases. TIPCommon's wrappers (`extract_action_param`, `ParameterValidator`, the base classes) present a stable contract to integration code. When the SDK changes, TIPCommon maintainers update the wrapper once; hundreds of integrations don't need to change. This is the primary reason integrations should **never** call SDK methods directly when a TIPCommon wrapper exists.

---

## Q21. Suppose I need to add a new validation method. Where does it go and what's the API contract?

New method in `TIPCommon/validation.py` as a `ParameterValidator` instance method. Convention: `validate_<thing>(param_name, value, ...extra_args)`. Must raise `ParameterExtractionError` on failure with a human-readable message. Return the parsed/coerced value on success. Write unit tests under the TIPCommon package's own tests. Open a PR to the `packages/tipcommon/` path — this goes through a stricter review than integration PRs because every integration consumes the change.

---

## Q22. What's your take on "should we just use the SDK directly and drop TIPCommon"?

Strong opinion: **no.** Reasons:

1. **SDK churn** — the SDK is explicitly documented as "work in progress, reference only." Integrations pinning the SDK directly would break on every SDK change.
2. **Duplication** — 100+ integrations would each reimplement extraction, validation, error handling, logging.
3. **Review burden** — every PR becomes a review of boilerplate as much as business logic.
4. **Testing** — centralized TIPCommon is testable in isolation; 100+ SDK direct usages are not.
5. **Centralized observability** — TIPCommon adds consistent logging structure that makes SOC analysts' lives better.

The indirection is the feature. Drop TIPCommon and you're rebuilding it a year later under a different name.

---

## Next

→ **[Section 7: `mp` CLI](../07-mp-cli/index.md)**
