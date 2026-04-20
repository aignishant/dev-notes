# Parsers — Interview Q&A

---

## Q1. What's CBN and what's UDM?

CBN (Configuration-Based Normalization) is the parser DSL used in `parser.conf` — filters + mutations that transform raw logs. UDM (Unified Data Model) is Google SecOps' canonical event schema — the normalized shape every parser produces.

---

## Q2. Where do parsers live?

`content/parsers/third_party/<community|partnerX>/<VENDOR_PRODUCT>/cbn/` — the `cbn/` subfolder contains `parser.conf`, `metadata.json`, `testdata/`, and an optional `README.md`.

---

## Q3. What's in `metadata.json`?

`log_type` (SecOps-known ID like `AZURE_AD`), `product`, `vendor`, `supported_format`, `category`, `description`, `references`. Log type must be recognized or pre-approved — you can't invent new ones.

---

## Q4. How does parser test data work?

Paired files in `testdata/`: `testcase1_logs.json` (raw input) + `testcase1_events.json` (expected UDM output). The validator runs the parser against the raw logs and diffs against expected. Multiple test cases supported via `testcaseN_` prefix.

---

## Q5. What are the two validation stages and what do they test?

**Validate Parsers** — automatic, tests structure + unit test correctness + log_type validity. **Validate Google & Parsers** — manually triggered via `secops` CLI against real customer logs in a live SecOps instance; tests parse efficiency and UDM field coverage regression.

---

## Q6. What are the prerequisites for contributing a parser?

CLA signed; `chronicle.admin` role in the tenant with the target log-type data; ≥1,000 log entries ingested for that log type; `chronicle.parsers.run` permission for local testing; PII scrubbed from testdata.

---

## Q7. Can you invent a new LogType?

No. Validation explicitly checks no new log type is added without support from the internal team. You coordinate through them first, then submit the parser.

---

## Q8. When would you build a parser vs. a connector for ingestion?

**Parser (Feed path) is preferred** — scales, normalizes to UDM, decoupled. **Connector** when: (a) the third-party doesn't expose a feed-friendly format, (b) per-alert processing must happen at ingest, (c) auth/pagination demands a stateful client.

---

## Q9. Why is timestamp normalization a common parser bug?

Vendors ship timestamps in wildly different formats — Unix seconds, Unix ms, ISO-8601, RFC-3339, "Oct 15 10:30:00" syslog style, vendor-specific epochs. UDM requires ISO-8601. Any format bug silently shifts events in time, breaking correlation and detection rules.

---

## Q10. How do parsers handle missing/optional fields?

Parsers must be defensive — optional fields may be absent. CBN allows conditional mutations (`if [field]`). Gracefully skipping missing fields rather than throwing is the standard pattern.

---

## Q11. Why is PII scrubbing important for testdata, and how strict is review?

Testdata becomes public Git history. Real emails, IPs, usernames, hostnames — any identifying data — leaks in perpetuity. Review is strict: any unscrubbed PII blocks merge. Contributors use TEST-NET-3 (`203.0.113.*`), TEST-NET-2 (`198.51.100.*`), and `example.com` domain for realistic but non-identifying replacements.

---

## Q12. Walk me through debugging a parser that the validator says produces output differing from expected.

1. Read the validator's diff output — it shows exactly which fields mismatched.
2. Run parser locally against the single problematic test case.
3. Log intermediate fields in CBN (temporary debug mutations).
4. Compare the produced UDM field vs the expected — is it a typo in field name? Missing array wrap? Wrong enum value?
5. Fix CBN rule, re-run, verify.
6. Sanity-check other test cases didn't regress.
7. Remove debug mutations.

---

## Q13. A parser was passing all tests but field coverage dropped in production after a vendor update. How do you handle?

1. **Pull recent production samples** from the affected customer tenant (with their approval).
2. **Diff** against the testdata — identify new fields/formats the vendor introduced.
3. **Add a new `testcaseN_*` pair** capturing the new format (PII-scrubbed).
4. **Update CBN rules** to handle both old and new (branching or wider grok patterns).
5. **Validate locally**, push fix PR with flag `regressive: false, new: false` in release notes (because it's a bug fix).
6. **Trigger Stage 2 validation** to confirm field coverage restored.
7. **Customer comms** — notify affected customers that the fix is landing.

---

## Q14. How do parsers relate to SOAR integrations?

Parsers feed the SIEM side — raw logs → UDM events → detection rules → alerts. Integrations handle the SOAR side — alerts → cases → playbooks → actions → remediation. A parser may feed alerts that an integration's actions later enrich. They're complementary, not competing.

---

## Q15. Why is the Validate Google & Parsers step manual instead of fully automated in CI?

Access restrictions. The live SecOps instance has real customer data and strict access controls. Making it fully automatic would require CI to have platform credentials with customer-data access — untenable. Contributors authenticate with their own `chronicle.admin` role and run the step themselves; the result is reported back to the PR.

---

## Next

→ **[Section 6: TIPCommon & SOAR SDK](../06-tipcommon-sdk/index.md)**
