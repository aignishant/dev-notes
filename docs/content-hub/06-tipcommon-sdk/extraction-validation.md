# Extraction & Validation

## `extraction.py` — The Extract Helpers

TIPCommon exposes three parallel helpers:

| Helper | For | From |
|---|---|---|
| `extract_action_param` | Action parameters | `SiemplifyAction` |
| `extract_connector_param` | Connector parameters | `SiemplifyConnectorExecution` |
| `extract_job_param` | Job parameters | `SiemplifyJob` |
| `extract_configuration_param` | Integration-level config | All three |

### Full Signature

```python
def extract_action_param(
    siemplify: SiemplifyAction,
    param_name: str,
    default_value: Any = None,
    input_type: type = str,
    is_mandatory: bool = False,
    print_value: bool = False,
    remove_whitespaces: bool = True,
) -> Any:
    """Pull a named parameter from the action's configuration."""
```

Parameter-by-parameter:

| Arg | Purpose |
|---|---|
| `siemplify` | SDK object |
| `param_name` | Must match exactly the `name:` in the YAML (case + spaces matter) |
| `default_value` | Fallback if not set (honored only if `is_mandatory=False`) |
| `input_type` | Python type to coerce to (`str`, `int`, `bool`, `float`) |
| `is_mandatory` | If True, raises `ParameterExtractionError` when missing |
| `print_value` | Logs the extracted value (omit for passwords!) |
| `remove_whitespaces` | Strips leading/trailing whitespace |

### Boolean Coercion Quirk

The SDK stores booleans as strings (`"true"` / `"false"`). `input_type=bool` handles the conversion:

```python
verify_ssl = extract_action_param(
    siemplify=self.soar_action,
    param_name="Verify SSL",
    default_value=False,
    input_type=bool,       # converts "true"/"false" → True/False
)
```

Without `input_type=bool`, you'd get the literal string `"false"` — which is truthy. Classic bug.

### Integer Coercion

```python
timeout = extract_action_param(
    siemplify=self.soar_action,
    param_name="Timeout (sec)",
    default_value=30,
    input_type=int,
    is_mandatory=False,
)
```

Non-numeric strings cause `ParameterExtractionError` — caught by the base class's `run()`.

### Never Log Passwords

For password parameters:

```python
api_key = extract_action_param(
    siemplify=self.soar_action,
    param_name="Api Key",
    is_mandatory=True,
    print_value=False,       # ← CRITICAL for secrets
)
```

`print_value=True` on a password is a **CVSS-worthy bug**. PR reviewers check this.

### `remove_whitespaces=False` — When You'd Want It

Default strips whitespace. Set to False when the parameter is legitimately whitespace-sensitive (e.g., a multi-line template, a format string with trailing space). Rare.

## `ParameterValidator`

Validation is a separate step (`_validate_params`) called after extraction. `ParameterValidator` provides typed validation methods.

### Construction

```python
from TIPCommon.validation import ParameterValidator

validator = ParameterValidator(self.soar_action)  # or siemplify / soar_job
```

### Common Validation Methods

| Method | Validates |
|---|---|
| `validate_json(param_name, json_string)` | Valid JSON string → returns parsed dict |
| `validate_csv(param_name, csv_string)` | Comma-separated list → returns `list[str]` |
| `validate_positive(param_name, value)` | Integer > 0 |
| `validate_range(param_name, value, min, max)` | Integer in [min, max] |
| `validate_email(param_name, email)` | Valid email format |
| `validate_url(param_name, url)` | Well-formed URL |
| `validate_regex(param_name, regex_string)` | Valid regex pattern |
| `validate_enum(param_name, value, allowed)` | Value is in allowed set |
| `validate_ip(param_name, ip_string)` | Valid IPv4/IPv6 |
| `validate_not_empty(param_name, value)` | Non-empty string |
| `validate_boolean(param_name, value)` | Valid boolean |
| `validate_datetime(param_name, dt_string, format)` | Parseable datetime |

### Raising vs Returning

These methods follow a dual pattern:

- **If the value is already extracted as string**: `validator.validate_json(param_name="X", json_string=raw)` returns the parsed dict OR raises `ParameterExtractionError`
- **If invalid**: raises → caught by base class → clear error in output_message

### Example — Full Extract + Validate Flow

```python
from TIPCommon.base.action import Action
from TIPCommon.extraction import extract_action_param
from TIPCommon.validation import ParameterValidator


class CheckIpReputation(Action):
    def _extract_action_parameters(self) -> None:
        self.params.api_key = extract_action_param(
            siemplify=self.soar_action,
            param_name="Api Key",
            is_mandatory=True,
            print_value=False,
        )
        self.params.max_days_str = extract_action_param(
            siemplify=self.soar_action,
            param_name="Max Age in Days",
            is_mandatory=True,
            print_value=True,
        )
        self.params.threshold_str = extract_action_param(
            siemplify=self.soar_action,
            param_name="Suspicious Threshold",
            default_value="50",
            is_mandatory=True,
            print_value=True,
        )
        self.params.create_insight = extract_action_param(
            siemplify=self.soar_action,
            param_name="Create Insight",
            input_type=bool,
            default_value=True,
            print_value=True,
        )

    def _validate_params(self) -> None:
        validator = ParameterValidator(self.soar_action)

        self.params.max_days = validator.validate_range(
            param_name="Max Age in Days",
            value=self.params.max_days_str,
            min_value=1,
            max_value=365,
        )
        self.params.threshold = validator.validate_range(
            param_name="Suspicious Threshold",
            value=self.params.threshold_str,
            min_value=0,
            max_value=100,
        )
```

Extract raw, validate/coerce into the final typed value. The split is deliberate: extraction failure (missing param) and validation failure (malformed value) produce different error messages to the user.

## `Container` — The Params Bag

`self.params` is a `Container` (from `TIPCommon.data_models`). It's a dict-like object you can also access via attribute dot notation:

```python
self.params.foo = "bar"     # sets
x = self.params.foo         # gets
if "foo" in self.params:    # membership
```

Safer than `self.params["foo"]` string indexing — typos fail loud.

## `is_first_run` Helper

```python
from TIPCommon.utils import is_first_run

if is_first_run(self.soar_action):
    # First time this action has ever been run in this tenant
    # — maybe set up required state, create a SOAR custom list, etc.
```

Helpful for actions that require one-time tenant-side initialization.

## `get_entity_original_identifier`

```python
from TIPCommon.utils import get_entity_original_identifier

identifier = get_entity_original_identifier(entity)
```

Entity identifiers are sometimes prefixed/suffixed by the platform (for deduplication). This helper returns the pristine original value — use it when passing the identifier to third-party APIs.

## Common Validation Pitfalls

| Pitfall | Prevention |
|---|---|
| Forgetting `input_type=bool` on boolean params | Strings always truthy — always specify `input_type` |
| `print_value=True` on password | Logs the secret. CRITICAL bug. |
| Extracting but not validating | Malformed values crash deep in business logic with unhelpful traces. Always validate. |
| Hand-parsing JSON instead of `validate_json` | Loses the consistent error message format |
| `is_mandatory=False` but no `default_value` | `None` propagates everywhere, NPE later |
| String-indexing `self.params["foo"]` | Typos fail silently. Use attribute access. |

## Next

→ **[EnvironmentCommon](envcommon.md)**
