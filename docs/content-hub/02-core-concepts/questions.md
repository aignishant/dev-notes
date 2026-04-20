# Core Concepts — Interview Q&A

---

## Q1. Explain the data flow from raw log to playbook execution.

**Model answer:**
> *"Raw logs are ingested two ways. On the SIEM side, they go through a parser written in CBN that normalizes them into UDM events, then detection rules run against UDM and emit alerts. On the SOAR side, connectors in response integrations poll third-party APIs and post alerts directly with their events. Either way we land at an Alert. The ontology mapping is then applied to each event in the alert to extract entities — IPs, users, hashes. The platform groups alerts into cases based on time proximity and shared entities. Playbooks are triggered when a case or alert matches the trigger conditions, and they execute steps — most of which are integration actions that enrich entities or drive remediation through third-party APIs."*

---

## Q2. What's the difference between an Action, Connector, and Job?

Action = on-demand task from playbook. Connector = continuous alert ingestion (cron-like). Job = continuous state sync between SOAR and third party (also cron-like, but no new alerts).

**Depth cue:** *"Jobs differ from connectors in that they don't create new alerts — they update existing SOAR state from third-party state or vice versa. Example: a job that mirrors analyst comments from SOAR cases to the corresponding ServiceNow ticket. Connectors would add noise; jobs keep existing state synchronized."*

---

## Q3. When would you choose a Connector over SIEM Feed + Parser for ingestion?

**Model answer:**
> *"Feed + Parser is the preferred path because it scales better, normalizes into UDM for search, and decouples ingestion from response. I'd choose a Connector when: (1) the third-party product doesn't expose a feed-friendly format — it's a REST API with paginated polling; (2) alert-specific enrichment must happen at ingestion (e.g., the vendor's alert object carries structured incident metadata that doesn't fit UDM cleanly); (3) the third party's rate limits and auth model require stateful client logic that feed ingestion can't do. The tradeoff is that connectors don't scale linearly — a single connector on a large tenant can fall behind."*

---

## Q4. Why does `ontology_mapping.yaml` matter?

> *"It's how events become entities. Without ontology, IPs/users/hashes embedded in event fields never surface as SOAR entities, which means: case grouping by entity overlap breaks, playbook entity triggers don't fire, enrichment actions receive empty `target_entities`, and the whole SOAR promise of 'follow an IP across alerts' collapses. The two fields that absolutely must be mapped are `start_time` and `end_time` — without them, the alert-to-case grouping breaks silently."*

---

## Q5. Walk me through how a connector's alert becomes a case with enrichment.

1. Connector polls third-party API on its configured interval.
2. For each new third-party alert, connector builds an `AlertInfo` with `alert_id`, `display_id`, and a list of event dicts.
3. Platform ingests the `AlertInfo`.
4. Ontology mapping rules in `ontology_mapping.yaml` (Product-level, typically) process each event dict and extract Entity objects (IPs, users, etc.).
5. Platform evaluates alert grouping rules (time window + entity overlap) and either creates a new Case or attaches the alert to an existing one.
6. Any Playbook whose `trigger.yaml` matches the alert fires. If the trigger type is Alert, the playbook receives the alert as context.
7. Playbook steps execute in order; Integration Actions receive entities via `siemplify.target_entities`.
8. Actions enrich each entity's `additional_properties` and may set `is_suspicious=True`.
9. Jobs run on their own schedule to sync back any state changes (comments, status) to the third-party product.

---

## Q6. Why can't you just put business logic in `ontology_mapping.yaml`?

> *"Ontology is intentionally declarative — field-to-entity rules. Putting conditional enrichment logic there would (a) make it non-reviewable (the file would grow unbounded), (b) break the separation between ingestion and response, (c) prevent customers from customizing ontology in the UI without redeploying code. Business logic belongs in actions, which are versioned, tested, and replaceable without changing ingestion."*

---

## Q7. What are power-up integrations and when do you use them?

> *"Power-ups are Google-maintained utility integration packs — `email_utilities`, `template_engine`, `git_sync`, `file_utilities`, `enrichment`, `insights`. They're not vertical product integrations; they're reusable building blocks. A playbook would call a power-up action like 'Render Template' or 'Send Email via SMTP' as part of its flow. They live in `content/response_integrations/power_ups/` and are maintained by Google with the highest rigor because many playbooks depend on them."*

---

## Q8. What's the difference between community and partner integrations, and why does the distinction exist?

> *"Both live under `third_party/` and follow identical structure. The difference is who maintains it: community is individual contributors — best-effort support; partner is the official vendor coordinating releases with us. Customers see the label in the catalog and choose accordingly. The distinction exists because enterprise customers often require vendor-backed support for critical integrations (their Infoblox or CrowdStrike integration), whereas experimental or long-tail integrations fit the community lane fine."*

---

## Q9. Can a playbook call another playbook?

Yes — via **Blocks**. A Block is effectively a sub-playbook reused across parent playbooks. In a step, you set `NestedWorkflowIdentifier` to the block's identifier (from its `definition.yaml`). The official guidance is: *"if your playbook uses blocks that already exist in the repo, don't duplicate them — reference by identifier."*

---

## Q10. What's the minimum a valid integration must contain?

- `definition.yaml` (identity + config)
- `pyproject.toml` + `uv.lock` (dependencies)
- `.python-version` (= 3.11)
- `release_notes.yaml` (changelog)
- `actions/Ping.py` + `actions/Ping.yaml` (connectivity test — mandatory)
- One service-specific action (otherwise the integration adds zero value)
- `core/` API client class
- `tests/` with basic test coverage
- `resources/logo.svg` and `resources/image.png`

And if it has a connector: `ontology_mapping.yaml` becomes mandatory.

---

## Q11. What entity types will you most commonly work with and what do they represent?

`ADDRESS` (IP), `USER`, `FILEHASH`, `URL`, `HOSTNAME`, `PROCESS`, `EMAIL_ADDRESS`, `MACADDRESS`, `CVE`, `THREATCAMPAIGN`. Found in `soar_sdk.SiemplifyDataModel.EntityTypes`.

---

## Q12. How should an action handle partial failure when iterating entities?

**Model answer:**
> *"Use the four-bucket pattern: `enriched_entities`, `limit_entities`, `failed_entities`, `missing_entities`. For each entity, try the enrichment in a try/except — on exception, classify into failed or limit (for rate-limit-specific errors). On a 'not found' response from the third party, push to missing, not failed. Always continue to the next entity. Aggregate the counts in the final output message. A single bad entity should never fail the entire action — playbooks chain dozens of actions and one failure shouldn't break the pipeline."*

---

## Q13. What does `entity.is_internal` mean and when do you respect it?

`is_internal` is True when the entity matches the customer's configured internal network ranges. Respect it in **TI enrichment actions** — looking up internal IPs in VirusTotal / AbuseIPDB is wasted quota and returns nothing useful. Some integrations expose an explicit "Exclude Internal Addresses" action parameter (AbuseIPDB does this) to let playbook authors opt in.

---

## Q14. What are the three trigger types for playbooks and when do you use each?

| Trigger | When |
|---|---|
| **Alert** | Most common — fires on alert create/update that matches conditions. Good for rule-driven automation. |
| **Entity** | Fires on entity create/update. Good for entity-focused flows like "whenever a new user appears, check for compromise." |
| **Manual** | Analyst-initiated from the UI. Good for containment actions you don't want to auto-run. |

---

## Q15. What's a predefined widget and how is it different from a playbook widget?

- **Predefined widget** — HTML widget bound to an **Action's JSON Result**, defined inside an integration's `widgets/` dir. Rendered in the alert view when a playbook step referenced in the widget's condition has run.
- **Playbook widget** — defined inside the playbook's `widgets/` dir, rendered in the case overview, fed from step data.

They're rendered in different parts of the UI, configured in different files, and serve different purposes (action-level visualization vs. case-overview dashboard).

---

## Q16. How does case grouping work?

The platform groups alerts into the same case when they share: (1) a similar time window (configurable proximity), (2) overlapping entities. Admin-configurable rules tune the grouping. Without mapped `start_time`/`end_time` in ontology and without entity extraction, grouping **silently breaks** — every alert becomes its own case.

---

## Q17. Can a connector update an existing alert?

Yes. Connectors can post updates to previously-ingested alerts by matching on external alert ID. Alert Triggers in playbooks can be configured to fire on "create or update", which is how you implement flows like "re-enrich when a new event arrives on the existing incident."

---

## Q18. What's the recommended way to define ontology — at Source, Product, or Event level — and why?

**Product level**, because the Product corresponds to the connector and applies consistently to every alert that connector ingests. Source is too broad (multiple connectors may share a source), Event is too granular and creates duplication. Use Event-level only for truly event-specific overrides.

---

## Q19. You ship a connector to production and SOAR starts creating one case per alert instead of grouping them. What's your diagnosis?

First suspect: **missing `start_time` / `end_time` mapping in `ontology_mapping.yaml`**. Without those, the grouping engine has no time signal and treats every alert as isolated. Second suspect: **no entity mappings at all**, so no entity overlap between alerts. Check the connector's output event dicts contain the fields you mapped, and that Ontology Status in the platform UI shows the mapping is applied. If the mapping is correct in the repo but missing in the platform, the integration may not have been redeployed with the updated ontology.

---

## Q20. Why is Content Hub split into content/packages/tools instead of flat?

> *"Content is the deliverable, packages are the shared libraries and tooling that content depends on, tools are one-off developer-side utilities. Mixing them would mean customers pulling content would inadvertently consume developer-only code. The split also clarifies review scope: a PR to `content/` is reviewed by content maintainers, a PR to `packages/tipcommon/` changes behavior for every integration and gets a much higher bar."*

---

## Next

→ **[Section 3: Response Integrations Deep Dive](../03-response-integrations/index.md)**
