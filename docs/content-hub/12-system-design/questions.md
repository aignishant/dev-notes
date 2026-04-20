# System Design — Interview Q&A

---

## Q1. Our CrowdStrike connector is falling behind — ingesting 500 alerts/cycle but volume is now 5000/cycle. How do you scale?

**Structure:**

1. **Measure first** — instrument per-phase time. Identify bottleneck (usually N+1 detail fetches).
2. **Batch endpoints** — CrowdStrike has `/detections/entities/summaries/GET/v1` which takes many IDs at once. 10-100× win over per-ID.
3. **Pre-filter** — apply severity filter on the list query before spending requests on detail fetches.
4. **Concurrency** — threads (`ThreadPoolExecutor`) for simplicity, or async with `AsyncConnector` + semaphore for peak throughput.
5. **Cursor-based pagination with context checkpointing** — if a cycle can't finish, save cursor, resume next cycle.
6. **Connector splitting** — High-severity connector at higher cadence, low-severity at lower cadence.
7. **Schedule tuning** — more frequent cycles with smaller batches often beats fewer-larger.
8. **Consider Feed + Parser** — if volume is truly high, SIEM path scales better than connectors.
9. **Observability** — instrument alert count, duration, queue depth. Catch next scale issue earlier.

---

## Q2. Design an integration for a new EDR vendor from scratch.

10-step framework (compressed):

1. **Discovery** — auth model, rate limits, volume, webhooks?
2. **Folder structure** — actions/, core/, connectors/, jobs/, tests/, widgets/, resources/
3. **definition.yaml** — API Root, Client ID, Client Secret (`type: password`), Verify SSL
4. **Core API client** — typed, retry-capable, with custom exception hierarchy
5. **Ping action** — always first
6. **Actions by analyst journey** — enrichment (entity-based), remediation (entity-based), triage (parameter-based)
7. **Connector** — cursor pagination, processed-IDs cache, environment extraction
8. **ontology_mapping.yaml** — Product-level with start_time, end_time, entity mappings
9. **Jobs** — bidirectional sync if needed, with loop prevention
10. **Tests** — mock product, mock session, per-action tests, connector idempotency test, 80%+ coverage

---

## Q3. We have 40+ community integrations on TIPCommon 1.x. Migrate them.

Phased plan:

- **Phase 0:** `mp validate` rejects new 1.x integrations — stop bleeding
- **Phase 1:** Inventory + prioritization matrix (usage × change frequency)
- **Phase 2:** Compatibility shim — ensure 2.x base classes preserve all 1.x behaviors
- **Phase 3:** Migration kit (auto-generates 2.x skeleton; leaves business logic as TODO)
- **Phase 4:** Pilot 3 integrations end-to-end myself, build runbook
- **Phase 5:** Team waves of 5/week
- **Phase 6:** Regression harness — replay fixtures against old+new, diff outputs
- **Phase 7:** Parallel-deploy old+new; customers opt in; telemetry-driven cutover
- **Phase 8:** Deprecate 1.x after usage drops to zero

Realistic timeline: **3-4 months** with 2-3 engineers.

---

## Q4. MSSP customer serves 50 end-customers from one SOAR tenant. How do you design integration multi-tenancy?

- **One environment per customer** — `customer-acme`, `customer-globex`, ...
- **Environment extraction in connectors** — `Environment Field Name` parameter + `Environment Regex Pattern`, resolved via `EnvironmentCommon.get_environment()`
- **Every `AlertInfo` tagged** with `info.environment = extracted`
- **Jobs scoped** — always filter `get_cases_ids_by_filter(environments=[env])`; one job instance per environment
- **Per-environment connector instances** if configs differ (separate API keys, schedules)
- **Stagger schedules** to avoid competing for shared third-party rate limits
- **Testing** — explicit multi-tenant isolation tests that fail loudly if an alert leaks across envs

---

## Q5. How do you decide between a connector and a SIEM parser for ingestion?

**Parser (Feed) preferred** because:
- Scales to high volume (millions of events/day)
- Decoupled from per-alert processing
- Normalizes to UDM for universal search

**Connector when:**
- Third party doesn't expose feed-friendly format (API-only, paginated)
- Alert-specific processing must happen at ingestion
- Auth/rate limits demand stateful client
- The product's alert is more than just a log line — has structured metadata that doesn't fit UDM cleanly

For a new integration, always ask the vendor first — do you ship logs via syslog or HTTPS feed? If yes, parser first.

---

## Q6. A customer reports that SOAR is creating one case per alert instead of grouping. Your connector is the suspect. Debug.

1. **Check ontology mapping** — most common cause is missing `start_time`/`end_time`
2. **Inspect live alerts in SOAR** — do the mapped fields exist in the raw `events`?
3. **Check ontology status** in the platform UI — is the mapping applied to the Product?
4. **Verify entity mappings** — no mapped entities means no overlap to group on
5. **Check case grouping rules** in tenant config — time window might be too tight
6. **Deploy a fix via hot update** if mapping was wrong; customer redeploys integration
7. **Postmortem** — add a `mp validate` check to enforce `start_time`/`end_time` for any integration with a connector

---

## Q7. Ten connectors all hit the same third-party API; rate limit is shared. Design.

- **Short term:** stagger schedules to minimize collision (connector A at :00, B at :02, ...)
- **Medium term:** central rate-limit coordinator — write remaining-quota to shared context; each connector checks before calling
- **Long term:** if vendor supports, per-customer API keys so each has own quota
- **Per-connector:** add max_requests_per_minute param, respect `Retry-After`, exponential backoff with jitter
- **Observability:** log rate-limit events across all connectors; alert when frequency exceeds threshold

---

## Q8. We want to add a webhook receiver alternative to polling. How do you design it?

Webhook pattern in SOAR is typically done via a **webhook power-up integration**:

- Power-up `webhook` provides a Connector that listens on a public URL for incoming HTTP POSTs
- Third party configured to POST alerts to the public URL
- Connector validates, builds `AlertInfo`, emits immediately — no polling latency

Integration components:

- **Definition** — params: API token, allowed source IPs, signature verification secret
- **Webhook endpoint** — `/webhook/<tenant-id>/<integration-id>` (platform-managed)
- **Signature verification** — HMAC-SHA256 using shared secret, per third-party standard
- **Idempotency** — third party may retry; dedupe by webhook delivery ID
- **Per-tenant rate limit** — reject noisy senders; don't overload pipeline

Downsides: public URL + secret exchange; harder in air-gapped environments. Not a universal replacement — complement to polling, not replacement.

---

## Q9. Customer wants to mirror SOAR case comments to ServiceNow and vice versa. Design.

- **Job 1:** `ServiceNowSyncJob` using `BaseSyncJob`
- **Outbound phase** — fetch SOAR cases updated since last_run, for each case mirror new (non-already-mirrored) comments to the SNow ticket
- **Inbound phase** — fetch SNow tickets updated since last_inbound, for each ticket mirror new (non-mirrored) comments to SOAR case
- **Loop prevention** — author tag `[SOAR-Mirror]` + idempotency key in SNow custom field
- **Ordering** — strict serial: outbound → inbound
- **External ID reference** — every SOAR case has `external_ticket_id` property; every SNow ticket has `soar_case_id` custom field
- **Status mapping** — explicit dict in both directions; unknown status → log warning, no mutation
- **Schedule** — every 5 minutes
- **Error handling** — per-case try/except; one bad case doesn't block others
- **Tests** — mock ServiceNow, exercise outbound, inbound, round-trip, loop-break

---

## Q10. Customer's tenant has 100 integrations installed; many share network calls to common TI APIs. How do you prevent quota exhaustion?

Several levers:

1. **Power-up enrichment integration** — one consolidated TI enricher that proxies all TI lookups; individual integrations call it instead of calling VT/AbuseIPDB/etc. directly
2. **Shared cache at the proxy level** — same IP lookup within N minutes returns cached result
3. **Per-tenant rate limit pools** — admin-configurable, enforced at the proxy
4. **Integration-level caching** — `TIPCommon.cache` with TTL for repeated lookups within a run
5. **Deduplication at playbook level** — a playbook step "enrich IOCs" that dedupes before calling downstream
6. **Observability** — dashboard showing quota usage per TI provider; alert when approaching limit

The org-level fix is the **shared proxy/enricher power-up** — it's the architectural answer most of the others depend on.

---

## Next

→ **[Section 13: Leadership & Behavioral](../13-leadership/index.md)**
