# 12 · OSINT Automation & Asset Graphing

> *Tools you can run by hand teach you the technique. Pipelines you can
> rerun nightly catch the change. Real engagements need both.*

The previous three modules each produced JSON output. This module ties
them together: **asset graphing**, **pipeline orchestration**, **report
generation**, and **diff-over-time monitoring**.

After Module 12 you will have:

- A single CLI command that runs passive recon, active scan, and
  vulnerability correlation against any target.
- A unified asset graph schema that survives across runs.
- A Markdown report ready to hand to a customer or paste into a Notion
  page.
- A diff tool that compares two snapshots to flag what changed.

---

## 12.1 The asset graph schema

Every recon source emits records at different granularities. We
normalize them all into a graph with three node types:

```
Domain ──── has_subdomain ───► Subdomain
Subdomain ── resolves_to ────► IP
IP ──────── has_service ─────► Service
Service ─── runs_version ────► VersionInfo
VersionInfo ── has_cve ──────► CVE
```

JSON representation (one canonical record per node, edges implicit by
ID references):

```json
{
  "domains":    { "example.com": { "registrar": "...", "asn": 15169 } },
  "subdomains": { "api.example.com": { "parent": "example.com",
                                        "sources": ["ct", "brute"] } },
  "ips":        { "93.184.216.34": { "subdomains": ["api.example.com"],
                                     "asn": "AS15133" } },
  "services":   { "93.184.216.34:443": { "ip": "93.184.216.34",
                                          "port": 443, "proto": "https",
                                          "banner": "...",
                                          "version": "nginx 1.18.0" } },
  "findings":   [ { "service": "93.184.216.34:443",
                    "cve": "CVE-2021-23017",
                    "severity": "high",
                    "summary": "..." } ],
  "metadata":   { "generated_at": "2026-04-25T...", "tool_versions": {...} }
}
```

This schema is what `asset_graph.py` produces and every other Part-3
toolkit module reads.

---

## 12.2 The pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                       osint_pipeline.py                      │
│                                                              │
│  ┌───────────┐   ┌─────────────┐   ┌─────────────────────┐  │
│  │ passive   │   │  active     │   │  correlation +       │  │
│  │ recon     ├──►│  scan       ├──►│  reporting           │  │
│  │           │   │             │   │                      │  │
│  │ whois_asn │   │ masscan     │   │ vuln_correlator      │  │
│  │ cert      │   │ svc_enum    │   │ asset_graph (merge)  │  │
│  │ passive   │   │ os_finger   │   │ report_generator     │  │
│  │   subs    │   │ tls_inspect │   │                      │  │
│  └───────────┘   └─────────────┘   └─────────────────────┘  │
│                                                              │
│  Outputs: assets.json, findings.json, report.md             │
└──────────────────────────────────────────────────────────────┘
```

A single CLI invocation:

```bash
python3 -m redshift_toolkit.automation.osint_pipeline \
    --target example.com \
    --outdir engagements/example/2026-04-25/ \
    --passive --active --report
```

You get back a folder of JSON artifacts plus `report.md`.

---

## 12.3 Reporting that gets read

A 200-page nmap dump goes unread. A 4-page report with these sections
gets read every time:

1. **Executive summary** — 3-5 sentences. *What did we find that matters?*
2. **Scope** — what was tested, when, how.
3. **Top 10 findings** — sorted by severity × exploitability, each with
   a one-paragraph remediation.
4. **Asset summary** — counts of domains, subdomains, IPs, services.
5. **Notable services** — old versions, exposed admin interfaces,
   default credentials likely.
6. **Appendices** — full asset graph as JSON, every CVE with detail.

`report_generator.py` produces exactly this layout.

---

## 12.4 Diff over time

Recon-as-a-product means running the same pipeline weekly and comparing.
Useful diff signals:

- **New subdomain appearing** — possibly a new staging environment.
- **Subdomain disappearing** — service decommissioned (good!) or DNS
  pruned (track separately).
- **New service on existing IP** — new feature, or unauthorized service.
- **Service version regression** — rare but signals rollback.
- **New CVE on existing service** — same software, new disclosure.

`recon_diff.py` consumes two snapshot JSON files and emits a third JSON
plus a Markdown changelog.

---

## 12.5 Operationalizing

Common patterns once your pipeline works:

- **Run nightly via cron** against your own perimeter (defensive).
- **Run weekly against scoped engagement targets** — early-warning of
  scope changes mid-engagement.
- **Webhook on diff** — Slack message when a new subdomain or service
  appears.
- **Threshold gates** — fail a CI build if the production attack
  surface gains a new exposed port.

This is where your SOAR background pays off literally — recon is a
playbook problem, not a manual one.

---

## 12.6 Industry scenarios

### Continuous attack-surface management for a Fortune 500

The pipeline runs hourly against the org's known domain. CT alerts plus
diff-over-time catch a marketing team standing up a campaign subdomain
without involving security. Auto-ticket → review → quick remediation
before adversaries notice.

### Bug bounty reconnaissance

Runs nightly against in-scope domains. New subdomain = first one to
test gets the bug bounty. Recon automation is what separates top bug
hunters from average ones.

### Engagement preparation for a bank

Two weeks before the engagement window, the pipeline runs daily.
Engagement team starts with a complete asset map before they ever touch
the target — entire engagement becomes "exploit known issues" rather
than "find something."

### Threat-intel analyst tracking adversary infrastructure

Same pipeline points at adversary-affiliated domains. Catches new C2
subdomains, new TLS certs, new email infrastructure as adversaries
build it.

---

## 12.7 Detection / blue-team angle

The blue-team mirror image of this module is **External Attack Surface
Management (EASM)** — running this same pipeline against your own
infrastructure to find what you forgot you exposed. Every Fortune 500
security team should be running an EASM tool. The toolkit you've built
is exactly that, minus the SaaS price tag.

Defender priorities:

- **CT monitoring** with auto-ticket on new cert.
- **DNS inventory reconciliation** against CMDB.
- **Service inventory** against asset DB.
- **Continuous external scan** with diff-over-time.

---

## 12.8 Toolbelt

| Tool | Purpose |
|------|---------|
| `SpiderFoot` | Big-bag-of-modules OSINT framework |
| `recon-ng` | Modular framework |
| `Maltego` | Graph visualization |
| `OWASP Amass` | Subdomain + asset graphing |
| `Detectify`, `Intrigue.io`, `Censys ASM`, `Randori`, `Project Discovery cloud` | Commercial EASM platforms |

Open source pipelines you'll see in the wild:

- `reconftw` — bash-driven, comprehensive, opinionated
- `axiom` — distributed scanning across cloud spot instances
- `nuclei` + custom workflows — the modern way

Our toolkit gives you the building blocks; the patterns above are how
you'd assemble them at scale.

---

## 12.9 Scripts for this module

In `scripts/part-03/12-osint-automation/` and `redshift-toolkit/redshift_toolkit/automation/`:

1. **`asset_graph.py`** *(toolkit)* — merges all recon JSON outputs into
   the canonical schema; deduplicates; serializes/deserializes.
2. **`osint_pipeline.py`** *(toolkit)* — passive → active → correlate
   driver that calls the other toolkit modules in sequence.
3. **`report_generator.py`** *(toolkit)* — Markdown report from asset
   graph + findings.
4. **`recon_diff.py`** *(toolkit)* — diffs two asset graphs and emits
   a changelog.
5. **`recon_orchestrator.py`** — module-level demo script that
   exercises the full pipeline against a small sample target.

---

## 12.10 Lab exercises

1. Run `osint_pipeline.py` (passive only) against your own domain.
   Inspect the resulting `assets.json`. Verify the schema matches what
   you read above.
2. Run it again 24 hours later. Run `recon_diff.py` against the two
   outputs. Anything change?
3. Run the full pipeline (passive + active) against your home lab. Use
   `report_generator.py` to produce a report. Read it as if you were a
   non-technical stakeholder. What's missing?
4. Deliberately misconfigure something in your lab between snapshots
   (open a port, deploy an old version of nginx). Run the diff. Verify
   it's caught.
5. Build a `cron` entry that runs the pipeline weekly, posts the diff
   to a Slack channel via webhook. *(Project; uses Part 14 material.)*

---

## 12.11 Further reading

- **`reconftw` repository** — community-driven all-in-one recon pipeline.
- **`ProjectDiscovery` blog** — pipeline patterns, nuclei templates.
- **`Bug Bounty Reconnaissance Framework`** — `0xpatrik.com`, Patrik Hudak.
- **Daniel Miessler's `mechanizing-security` essays** — the philosophy.
- **`ATT&CK Recon TA0043` and `Discovery TA0007`** combined view.

---

> You now have *the recon stack*. Every later module in this curriculum
> assumes you have a populated asset graph for the target. Run your
> pipeline, then go exploit.

→ Next: **Part 4 · Web Application Security** *(coming in the next ship — Modules 13-17: Web fundamentals, OWASP Top 10 deep dives, modern API attacks, GraphQL, web cache poisoning, request smuggling)*.
