# Multi-Tenant Considerations

## The Context

SOAR tenants often serve multiple **environments** — different BUs, subsidiaries, customers-of-an-MSSP. Your integration code must respect environment boundaries, not cross them.

## Three Axes of Multi-Tenancy

1. **Alert scope** — alert X belongs to environment A; analyst for B must not see it
2. **Job scope** — job mutating cases must filter to its environment
3. **Configuration scope** — different tenants may run the same integration with different API keys

## Environment Tagging in Alerts

From [EnvironmentCommon](../06-tipcommon-sdk/envcommon.md): connectors use `GetEnvironmentCommonFactory` to resolve per-alert environment.

```python
info = AlertInfo()
info.environment = self._env_common.get_environment(event_dict)
```

If omitted, alerts land in the "default" environment and potentially leak to the wrong tenant.

## Jobs: Always Scope Environment

```python
case_ids = soar_job.get_cases_ids_by_filter(
    status=CaseFilterStatusEnum.OPEN,
    environments=[self.params.environment_name],   # ← essential
)
```

Without this filter, a job configured for environment A mutates cases in B too. **Serious bug** — causes cross-tenant data contamination.

Make `environment_name` a mandatory job parameter:

```yaml
parameters:
  - name: Environment Name
    type: string
    is_mandatory: true
    description: Environment this job operates on
```

## Configuration Isolation

SOAR handles this — each tenant has its own integration configuration instance. The integration code doesn't need to multi-tenant-aware at the auth level; SOAR isolates configs.

What your code does need: don't cache cross-tenant data. Each action/connector/job run gets config for the specific tenant/instance that scheduled it. Don't mix instances in static class state.

## Per-Environment Connectors

For customer environments with very different volumes or configs, run separate connector instances:

- CrowdStrike connector, instance 1 → Environment A (polls every 5 min, max 1000 alerts)
- CrowdStrike connector, instance 2 → Environment B (polls every 15 min, max 100 alerts)

SOAR supports instances of the same connector with different configs — just configure them separately in the UI.

## MSSP Pattern

For Managed Security Service Providers serving dozens of customers:

- **Each customer = one environment**
- **Tight naming convention** — `customer-acme`, `customer-globex`
- **Environment field extraction** from alerts (`Environment Field Name` in connector config)
- **Playbooks scoped per-customer** — via trigger condition `alert.environment equals "customer-acme"`

## Multi-Region Considerations

For integrations with region-specific endpoints (AWS, Azure, some SaaS):

```yaml
parameters:
  - name: Region
    type: ddl
    optional_values:
      - us-east-1
      - us-west-2
      - eu-west-1
      - ap-southeast-1
    default_value: us-east-1
```

Region feeds into API Root:

```python
self.api_root = f"https://api.{self.params.region}.vendor.com"
```

## Dealing with Shared Rate Limits

Some vendor APIs rate-limit per account, not per connector instance. Three MSSP customers polling at the same time compete for the same quota.

Mitigations:

1. **Stagger schedules** — customer A connects at :00, B at :02, C at :04
2. **Central rate-limit coordinator** — write state to a shared store; connectors acquire tokens before calling
3. **Per-customer credentials** — if vendor supports, give each customer their own API key (larger total quota)
4. **Global backoff** — on 429, all connectors pause briefly

## Data Leak Prevention

The biggest multi-tenant risk is **data from environment A appearing in environment B's view**.

Prevention checklist:

- [ ] Connector sets `AlertInfo.environment` for every alert
- [ ] Jobs filter `get_cases_ids_by_filter(environments=[env])`
- [ ] Actions don't operate across environments — each invocation is scoped
- [ ] No static caches of cross-tenant data in connectors (use instance-level context)
- [ ] Logs don't include cross-tenant identifiers inadvertently

## Testing Multi-Tenant Isolation

```python
def test_connector_tags_alerts_with_correct_environment(self, mock_siemplify_connector):
    mock_siemplify_connector.context_property["environment_field_name"] = "customer"
    mock_siemplify_connector.context_property["environment_regex_pattern"] = "(.+)"

    # Alert from customer-acme
    mock_product.add_alert({"customer": "customer-acme", "id": 1})
    # Alert from customer-globex
    mock_product.add_alert({"customer": "customer-globex", "id": 2})

    connector = MyConnector(...)
    connector.start()

    returned = mock_siemplify_connector.return_package.call_args.args[0]
    environments = {a.environment for a in returned}
    assert environments == {"customer-acme", "customer-globex"}
```

## Common Multi-Tenant Mistakes

| Mistake | Impact |
|---|---|
| Forgetting `info.environment` in connector | All alerts land in default env → cross-tenant leak |
| Job without environment filter | Mutates cases across all envs |
| Caching per-tenant data in class attr | Cross-pollination between runs |
| Hardcoded env name | Breaks if tenant has different env name |
| Single job for all envs, iterating internally | Makes single-env troubleshooting impossible — better: one job instance per env |

## Next

→ **[Migration Strategy](migration.md)**
