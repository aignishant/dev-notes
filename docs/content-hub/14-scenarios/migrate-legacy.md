# Migrate Legacy Integration

## The Prompt

> *"Here's a legacy procedural action using `@output_handler`. Refactor it into the TIPCommon 2.x base class pattern. [Interviewer shares a 100-line legacy Python file.]"*

Compressed version of the AbuseIPDB legacy Ping:

```python
from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED
from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import output_handler

from ..core.AbuseIPDB import AbuseIPDBInvalidAPIKeyManagerError, AbuseIPDBManager

SCRIPT_NAME = "AbuseIPDB - Ping"


@output_handler
def main():
    siemplify = SiemplifyAction()
    siemplify.script_name = SCRIPT_NAME
    api_key = siemplify.extract_configuration_param(siemplify, param_name="Api Key")
    verify_ssl = siemplify.extract_configuration_param(
        siemplify, param_name="Verify SSL",
        default_value=False, input_type=bool,
    )

    try:
        ipdb = AbuseIPDBManager(api_key, verify_ssl)
        ipdb.test_connectivity()
        status = EXECUTION_STATE_COMPLETED
        output_message = "Connection Established"
        result_value = "true"
    except AbuseIPDBInvalidAPIKeyManagerError:
        status = EXECUTION_STATE_FAILED
        result_value = "false"
        output_message = "Invalid API key was provided. Access is forbidden."
    except Exception as e:
        status = EXECUTION_STATE_FAILED
        result_value = "false"
        output_message = f"General error: {e}"

    siemplify.end(output_message, result_value, status)


if __name__ == "__main__":
    main()
```

## Step 1 — Explain What You're Changing (1 min)

Before touching code, say:

> *"I'm going to refactor this into the TIPCommon 2.x `Action` base class. The key transformations: (1) the procedural `main()` becomes a class subclassing `Action`, (2) parameter extraction moves into `_extract_action_parameters`, (3) API client instantiation into `_init_api_clients`, (4) business logic into `_perform_action`, (5) error handling is largely delegated to the base class, so the try/except gets simpler. The base's `run()` method orchestrates everything."*

Narrating the transformation shows you understand the pattern, not just the mechanics.

## Step 2 — Transformation

```python
from __future__ import annotations
from typing import TYPE_CHECKING

from TIPCommon.base.action import Action
from TIPCommon.extraction import extract_configuration_param

from ..core.AbuseIPDB import AbuseIPDBInvalidAPIKeyManagerError, AbuseIPDBManager

if TYPE_CHECKING:
    from TIPCommon.types import Contains

SCRIPT_NAME: str = "AbuseIPDB - Ping"


def main() -> None:
    Ping(name=SCRIPT_NAME).run()


class Ping(Action[AbuseIPDBManager]):
    def _extract_action_parameters(self) -> None:
        self.params.api_key = extract_configuration_param(
            siemplify=self.soar_action,
            provider_name="AbuseIPDB",
            param_name="Api Key",
            is_mandatory=True,
            print_value=False,
        )
        self.params.verify_ssl = extract_configuration_param(
            siemplify=self.soar_action,
            provider_name="AbuseIPDB",
            param_name="Verify SSL",
            input_type=bool,
            default_value=True,
            print_value=True,
        )

    def _validate_params(self) -> None:
        """No additional validation needed — extraction handles required/boolean."""

    def _init_api_clients(self) -> Contains[AbuseIPDBManager]:
        return AbuseIPDBManager(self.params.api_key, self.params.verify_ssl)

    def _perform_action(self, _: None = None) -> None:
        try:
            self._api_client.test_connectivity()
        except AbuseIPDBInvalidAPIKeyManagerError:
            self._result_value = False
            self._error_output_message = "Invalid API key was provided. Access is forbidden."
            raise  # Re-raise so base class sets EXECUTION_STATE_FAILED
        self._result_value = True
        self._output_message = "Connection Established"


if __name__ == "__main__":
    main()
```

## Step 3 — Point Out What You Improved

- **`print_value=False` on Api Key** — legacy didn't specify; likely logged secret
- **`verify_ssl` default changed** — legacy had `False` (insecure default); updated to `True` (secure default)
- **Error handling simplified** — base class catches everything and sets state; subclass just sets specific message for specific error
- **Type hints** — every parameter and return typed
- **Generic type `Action[AbuseIPDBManager]`** — IDE autocomplete on `self._api_client`
- **`from __future__ import annotations`** — modern syntax
- **No more procedural `status` / `output_message` / `result_value` variables** — fields on the instance

## Step 4 — Tests to Add

```python
class TestPing:
    def test_ping_success(self, mock_siemplify):
        with patch("..actions.ping.AbuseIPDBManager") as MockClient:
            MockClient.return_value.test_connectivity.return_value = True
            Ping(name="Ping").run()

        mock_siemplify.end.assert_called_once()
        args = mock_siemplify.end.call_args.args
        assert args[1] == "true"
        assert "Connection Established" in args[0]

    def test_ping_invalid_key(self, mock_siemplify):
        with patch("..actions.ping.AbuseIPDBManager") as MockClient:
            MockClient.return_value.test_connectivity.side_effect = \
                AbuseIPDBInvalidAPIKeyManagerError()
            Ping(name="Ping").run()

        args = mock_siemplify.end.call_args.args
        assert args[1] == "false"
        assert "Invalid API key" in args[0]

    def test_ping_generic_error(self, mock_siemplify):
        with patch("..actions.ping.AbuseIPDBManager") as MockClient:
            MockClient.return_value.test_connectivity.side_effect = \
                RuntimeError("boom")
            Ping(name="Ping").run()

        args = mock_siemplify.end.call_args.args
        assert args[1] == "false"
        # base class produces "general" error message
```

Three tests minimum: happy path, specific error, generic error.

## Step 5 — What You Intentionally Did NOT Do

Narrate your restraint:

- *"I didn't modify the core `AbuseIPDBManager` class — that's a separate refactor; scoped this PR to the action only."*
- *"I didn't add retry logic — Ping shouldn't retry. Feature creep."*
- *"I didn't change the action's external contract — same parameter names, same outputs. Customers shouldn't have to change anything."*

A lead knows what *not* to do.

## Step 6 — Release Notes Entry

```yaml
- description: Migrated Ping action to TIPCommon 2.x base class pattern. No behavior change.
  integration_version: 3.0.0
  item_name: Ping
  item_type: Action
  regressive: false
  new: false
  publish_time: '2026-04-15'
```

`regressive: false` because behavior is preserved; major version bump signals "internals changed materially" per semver conventions.

## Common Mistakes in This Exercise

| Mistake | What to say instead |
|---|---|
| Rewriting the core client too | "I scoped to the action layer; core client stays" |
| Changing parameter names | "External contract preserved; only internals moved" |
| Adding untested new features | "Migration PRs are behavior-preserving; features go in separate PRs" |
| Ignoring the `Generic[ApiClient]` typing opportunity | "Typed the Action as `Action[AbuseIPDBManager]` for IDE autocomplete" |
| Missing the base class's error handling | "I kept only the specific-exception branch; base handles the generic path" |

## Next

→ **[Whiteboard Problems](whiteboard.md)**
