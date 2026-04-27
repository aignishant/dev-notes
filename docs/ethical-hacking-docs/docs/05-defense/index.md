# 🛡️ Phase 5 — Defense & Operations

> Most cybersecurity jobs are blue team. SOC analyst, incident responder, threat hunter, detection engineer, threat intel analyst. This is where the volume of hiring is — and where the entry-level bar is most reachable.

If you want a government cybersecurity job, this phase matters more than offensive. NSA, CISA, FBI Cyber, USCYBERCOM, CERT-In, NCIIPC all run massive defensive operations.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 5.1 | Red Team Operations | Adversary emulation, OPSEC, C2 frameworks, evasion |
| 5.2 | Blue Team / SOC Operations | Tier 1/2/3 workflow, alert triage, escalation |
| 5.3 | SIEM Engineering | Splunk, Elastic, Sentinel, log sources, SPL/KQL |
| 5.4 | Detection Engineering | Sigma rules, ATT&CK coverage, threat-informed defense |
| 5.5 | Digital Forensics & Incident Response | DFIR methodology, Volatility, KAPE, timelines |
| 5.6 | Threat Hunting | Hypothesis-driven, anomaly-based, IOC sweeps |
| 5.7 | Cyber Threat Intelligence | Strategic, operational, tactical; TLP, STIX/TAXII, MISP |
| 5.8 | Purple Teaming | Atomic Red Team, CALDERA, detection validation |
| 5.9 | Crisis Management & Tabletop Exercises | Communications, executive reporting, IR runbooks |

## What you'll be able to do at the end

- Walk into a SOC L1/L2 role on day one and run the alert queue
- Author Sigma rules that map cleanly to ATT&CK
- Triage a malware incident from telemetry to scoping to remediation
- Produce a CTI report for an executive and a technical audience
- Run a purple-team exercise that validates 50+ detections
- Run a tabletop exercise for a ransomware scenario

## Tools you'll learn

Splunk Free, Elastic Stack, Microsoft Sentinel, Wazuh, Sigma, Sysmon, Velociraptor, KAPE, Eric Zimmerman's tools, Volatility 3, plaso/log2timeline, TheHive + Cortex, MISP, Atomic Red Team, CALDERA, Mythic, Sliver, Havoc, Cobalt Strike (commercial), ProcMon, ProcExplorer, RegRipper, Eric Zimmerman parsers (MFTECmd, AmcacheParser, RECmd), KAPE.

## Python scripts you'll build

1. **`failed_ssh_analyzer.py`** — parse `/var/log/auth.log` and produce attacker IP heatmap.
2. **`dns_exfil_detector.py`** — flag long, high-entropy subdomains in DNS logs.
3. **`sigma_to_splunk.py`** — convert a Sigma rule directory to Splunk SPL.
4. **`ioc_extractor.py`** — extract IOCs (IP, domain, hash, URL) from any text.
5. **`misp_pull.py`** — pull recent IOCs from MISP via API and produce a threat feed.
6. **`evtx_triager.py`** — fast triage of `.evtx` files for IOCs (logon, 4624/4625/4688/4697/4698).
7. **`vt_lookup.py`** — bulk VirusTotal hash lookup with caching and rate limiting.
8. **`yara_scanner.py`** — recursive YARA scanner with rich output and JSON results.

## Reference frameworks

- **MITRE ATT&CK** + **D3FEND**
- **NIST SP 800-61 r2** — Computer Security Incident Handling Guide
- **SANS PICERL** — Preparation, Identification, Containment, Eradication, Recovery, Lessons learned
- **ISO/IEC 27035** — Incident management
- **VERIS / Verizon DBIR** — Vocabulary for breach reporting
- **Pyramid of Pain** — Bianco
- **Diamond Model** — Sergio Caltagirone et al.
- **Detection Maturity Level (DML)** — Ryan Stillions

## Estimated time

- Full-time: 6–8 weeks
- Part-time: 12–16 weeks

## Prerequisites

✅ Phases 1, 2, 3. (Specializations from Phase 4 are optional — the more offense you understand, the better defender you become.)

---

!!! tip "Stage 4 of this curriculum"
    All chapters and the 8 scripts ship in Stage 4.

[← Phase 4](../04-specializations/index.md)  ·  [Phase 6 →](../06-career/index.md)
