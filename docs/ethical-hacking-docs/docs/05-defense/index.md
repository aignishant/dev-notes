# 🛡️ Phase 5 — Defense & Operations

> Most cybersecurity jobs are blue team. SOC analyst, incident responder, threat hunter, detection engineer, threat intel analyst. This is where the volume of hiring is — and where the entry-level bar is most reachable.

If you want a government cybersecurity job, this phase matters more than offensive. NSA, CISA, FBI Cyber, USCYBERCOM, CERT-In, NCIIPC all run massive defensive operations.

## Chapters in this phase

| # | Chapter | Focus | Status |
|---|---|---|---|
| 5.1 | [Red Team Operations](red-team.md) | Adversary emulation, kill chain, C2 frameworks, EDR evasion, OPSEC | ✅ |
| 5.2 | [Blue Team / SOC Operations](blue-team.md) | SIEM, EDR, Sigma, detection engineering, threat hunting, SOAR | ✅ |
| 5.3 | [Digital Forensics & Incident Response](dfir.md) | PICERL lifecycle, memory + disk + network forensics, EVTX, cloud IR | ✅ |
| 5.4 | [Cyber Threat Intelligence](threat-intel.md) | CTI lifecycle, IoCs vs TTPs, ATT&CK, STIX/TAXII, MISP, OpenCTI, ISACs | ✅ |
| 5.5 | [Purple Team & Detection Validation](purple-team.md) | Atomic Red Team, Caldera, Stratus Red Team, VECTR, DETT&CT | ✅ |

## What you'll be able to do at the end

- Walk into a SOC L1/L2 role on day one and run the alert queue
- Author Sigma rules that map cleanly to ATT&CK
- Triage a malware incident from telemetry through scoping to remediation
- Run memory forensics with Volatility 3 and disk forensics with Eric Zimmerman tools
- Produce a CTI report for both an executive and a technical audience
- Run a purple-team exercise that validates detections against MITRE ATT&CK techniques
- Lead an IR engagement — including the difficult conversations with leadership

## Tools you'll learn

**SIEM**: Splunk, Microsoft Sentinel, Elastic Security, Chronicle, Wazuh
**EDR**: CrowdStrike Falcon, Microsoft Defender for Endpoint, SentinelOne, Carbon Black
**Detection**: Sigma + sigma-cli, SigmaHQ rules, chainsaw, Hayabusa
**Endpoint telemetry**: Sysmon, Sysmon for Linux, auditd, osquery, Falco, Velociraptor
**Memory forensics**: Volatility 3, WinPMEM, LiME, AVML, pypykatz
**Disk forensics**: Autopsy, The Sleuth Kit, KAPE, Eric Zimmerman tools (MFTECmd, RECmd, EvtxECmd, AmcacheParser)
**Network forensics**: Wireshark, tshark, Suricata, Zeek, Arkime
**Red team C2**: Cobalt Strike, Sliver, Mythic, Havoc, Brute Ratel
**Adversary emulation**: Atomic Red Team, MITRE Caldera, Stratus Red Team, PurpleSharp, APTSimulator
**TIPs**: MISP, OpenCTI, Yeti, TheHive + Cortex
**Coverage tracking**: VECTR, DETT&CT, ATT&CK Navigator

## Python scripts in this phase

| Script | Purpose |
|---|---|
| [`defense/failed_ssh_analyzer.py`](../../scripts/defense/failed_ssh_analyzer.py) | Parse `/var/log/auth.log` for failed SSH attempts (Stage 1) |
| [`defense/ioc_extractor.py`](../../scripts/defense/ioc_extractor.py) | Extract IOCs from any text (Stage 1) |
| [`defense/mini_honeypot.py`](../../scripts/defense/mini_honeypot.py) | Tiny multi-port honeypot (Stage 1) |
| [`defense/dns_exfil_detector.py`](../../scripts/defense/dns_exfil_detector.py) | Flag high-entropy DNS subdomain queries (Stage 4) |
| [`defense/sigma_to_splunk.py`](../../scripts/defense/sigma_to_splunk.py) | Bulk-convert Sigma → Splunk SPL (Stage 4) |
| [`forensics/evtx_triager.py`](../../scripts/forensics/evtx_triager.py) | Triage Windows EVTX directories (Stage 4) |
| [`threat-intel/stix_query.py`](../../scripts/threat-intel/stix_query.py) | Query STIX 2.1 bundles for IoCs/TTPs (Stage 4) |

## Reference frameworks

- **MITRE ATT&CK** + **D3FEND** — TTPs and countermeasures
- **NIST SP 800-61 r2** — Computer Security Incident Handling Guide
- **SANS PICERL** — Preparation, Identification, Containment, Eradication, Recovery, Lessons learned
- **ISO/IEC 27035** — Incident management
- **VERIS / Verizon DBIR** — Vocabulary for breach reporting
- **Pyramid of Pain** (David Bianco)
- **Diamond Model of Intrusion Analysis** (Caltagirone et al.)
- **Detection Maturity Level (DML)** (Ryan Stillions)
- **Cyber Kill Chain** (Lockheed Martin)
- **F3EAD** (Find, Fix, Finish, Exploit, Analyze, Disseminate)
- **TLP v2.0** (FIRST)
- **EPSS + CISA KEV** for vuln prioritization

## Estimated time

- Full-time: 6–8 weeks
- Part-time: 12–16 weeks

## Prerequisites

✅ Phases 1, 2, 3. (Specializations from Phase 4 are optional — the more offense you understand, the better defender you become.)

---

[← Phase 4](../04-specializations/index.md)  ·  [Phase 6 →](../06-career/index.md)
