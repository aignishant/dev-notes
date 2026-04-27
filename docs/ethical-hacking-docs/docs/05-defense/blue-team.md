# 🔵 Blue Team & SOC Operations

> Defenders are the unsung 90% of security. Every red team writeup you've read existed because someone, eventually, caught it. Blue team work is detection engineering, alert triage, incident response, threat hunting, and the relentless tuning of telemetry.

For roles in: **SOC analyst (Tier 1–3) at any large organization**, **detection engineer at security vendors / cloud providers**, **CSIRT / CERT teams (US-CERT/CISA, CERT-In, JPCERT)**, **MSSP / MDR providers**, **threat hunter**, **SIEM/EDR engineer**.

## The defender mindset

Where red teamers ask "how can I get in?", blue teamers ask "what would I see if someone tried?" The shift takes practice. Some defining traits:

- **Visibility first.** You can't detect what you can't see. The first defender question is always: "Do we have the logs?"
- **Signal over noise.** A SOC drowning in alerts catches nothing. Tuning is half the job.
- **Adversary-informed.** Generic "log everything, alert on everything" doesn't scale. Map detection coverage to MITRE ATT&CK techniques you've decided matter.
- **Hypothesis-driven hunting.** Threats live longer in your environment than alerts admit. Hunt by hypothesis: "If APT29 were here, where would I see them?"

## SOC tiering

```
Tier 1 (analyst)        Initial triage, validate alerts, escalate the real ones
Tier 2 (analyst/IR)     Investigate confirmed incidents, scope, contain
Tier 3 (senior IR/hunt) Threat hunting, complex IR, malware analysis, detection engineering
SOC manager / lead      Process, metrics, runbooks, hiring, vendor mgmt
Detection engineer      Builds and tunes detections (Sigma, Snort, KQL, SPL, SQL)
Threat intel analyst    See [Threat Intel chapter](threat-intel.md)
```

The career ladder isn't strictly linear. Many move T1 → detection engineer, or T1 → DFIR, or join the threat intel team. The Tier-1-forever role is a red flag for that SOC, not the analyst.

## The telemetry pyramid

```
                    ┌─────────────────┐
                    │ Threat intel    │  ← who, why, IoCs, TTPs
                    ├─────────────────┤
                    │ User behavior   │  ← UEBA — anomaly, not signature
                    ├─────────────────┤
                    │ Application     │  ← app logs, audit trails, DB queries
                    ├─────────────────┤
                    │ Endpoint (EDR)  │  ← processes, file mods, registry, syscalls
                    ├─────────────────┤
                    │ Network         │  ← Zeek/Suricata/NetFlow, DNS, proxy
                    ├─────────────────┤
                    │ Identity        │  ← AD, Entra ID, IdP signins, MFA failures
                    ├─────────────────┤
                    │ Cloud           │  ← CloudTrail, GuardDuty, AzureActivity
                    ├─────────────────┤
                    │ Asset / Config  │  ← what exists, current state, drift
                    └─────────────────┘
```

Endpoint + identity is the modern detection nexus. If you can only have two data sources, take EDR and Entra ID / AD authentication logs.

## SIEM — the central nervous system

Every SOC has a SIEM. Currently dominant:

| SIEM | Notes |
|---|---|
| **Splunk Enterprise Security** | Industry standard; expensive but comprehensive. SPL is its query language. |
| **Microsoft Sentinel** | KQL-based; tightly integrated with Azure / Defender / Entra |
| **Elastic Security (ELK)** | Open source core; very flexible; KQL/Lucene/EQL |
| **Google Chronicle / SecOps** | YARA-L for detections, scales massively |
| **CrowdStrike Falcon LogScale (formerly Humio)** | Schema-less, fast |
| **Wazuh** (FOSS) | Free, capable for SMBs and home labs |
| **Sumo Logic, IBM QRadar, ArcSight, Exabeam** | Still in many enterprises |

You'll use one primarily. Learn its query language deeply, understand the others well enough to read examples.

### Splunk SPL (basic)
```spl
index=windows EventCode=4625 src_ip=*
| stats count by src_ip, dest_user
| where count > 5
| sort -count
```

### Microsoft Sentinel KQL
```kql
SecurityEvent
| where EventID == 4625
| summarize count() by IpAddress, Account
| where count_ > 5
| sort by count_ desc
```

### Elastic EQL (event correlation)
```eql
sequence by host.name with maxspan=5m
  [process where event.action == "creation" and process.name == "powershell.exe"]
  [network where event.action == "connection_accepted" and destination.port == 4444]
```

## EDR — endpoint detection & response

EDR replaced antivirus. Modern leaders: **CrowdStrike Falcon**, **Microsoft Defender for Endpoint (MDE)**, **SentinelOne**, **Carbon Black**, **Sophos Intercept X**, **Cortex XDR**.

What EDR collects per endpoint:
- Every process create + command line + parent
- File creates / writes / deletes (selective)
- Registry modifications (Windows)
- Network connections (5-tuple + process)
- DNS queries (process attribution)
- Module loads (DLL injection signal)
- AMSI script content (PowerShell, JScript, VBScript)
- Suspicious memory operations

Your job: write or tune the detections, triage the alerts, hunt across the data.

## Sigma — the universal detection language

Vendor-neutral YAML format that converts to SPL/KQL/EQL/etc. via [`sigma-cli`](https://github.com/SigmaHQ/sigma-cli).

```yaml
title: Suspicious PowerShell Encoded Command
id: 88819f8f-3af0-4bbf-8a07-f54bb8fa2519
description: Detects encoded PowerShell — common in malware
status: stable
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - '-enc'
      - '-encodedcommand'
      - '-e '
  filter:
    User|startswith: 'NT AUTHORITY\SYSTEM'
  condition: selection and not filter
falsepositives:
  - Scheduled tasks legitimately using encoded commands
level: medium
tags:
  - attack.t1059.001
  - attack.execution
```

The [SigmaHQ rule repository](https://github.com/SigmaHQ/sigma) has 3,000+ open-source rules. Treat it as a starter pack, not a production deployment — every rule needs tuning for *your* environment.

Our [`defense/sigma_to_splunk.py`](../../scripts/defense/sigma_to_splunk.py) script bulk-converts a Sigma directory to SPL.

## Detection engineering — the craft

Writing a good detection is harder than it looks. The ideal detection is:

- **Specific** — fires on attacker behavior, not benign behavior
- **Generalized** — covers a *class* of attacks, not just one tool's specific bytes
- **Resilient** — survives the next version of the attacker tool
- **Cheap** — runs at SIEM scale without crushing query volume
- **Correlated** — the highest-confidence alerts are usually multi-event

The classical engineering loop:

```
1. Pick a TTP (e.g., MITRE T1003.001 — LSASS Memory Dumping)
2. Reproduce in lab (Atomic Red Team test #1, procdump.exe lsass.exe)
3. Observe telemetry — what does EDR / Sysmon / Sentinel see?
4. Write the detection (Sigma)
5. Test for false positives in production volume
6. Tune. Test. Tune again.
7. Document: response runbook, expected FP rate, severity.
8. Ship to production with `disabled` for 1 week, watch volume.
9. Enable. Iterate.
```

Pyramid of Pain (David Bianco) — what costs the attacker most to change:

```
TTPs               ← hardest to change (re-tooling required)
Tools              ← rebuilds, weeks
Network/Host artifacts ← redeploy infrastructure
Domain names       ← register new
IP addresses       ← buy new VPS
Hash values        ← recompile (trivial)
```

Detect on TTPs and tools. Block on hashes/IPs as exposure mitigation, not as your detection strategy.

## Sysmon — the free Windows telemetry hero

Microsoft's [Sysinternals Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) provides forensic-grade telemetry as Windows event log entries. Configure with [SwiftOnSecurity's config](https://github.com/SwiftOnSecurity/sysmon-config) or [Olaf Hartong's Sysmon-Modular](https://github.com/olafhartong/sysmon-modular) — both excellent starting points.

Key event IDs:

| Event ID | Description |
|---|---|
| 1 | Process create |
| 3 | Network connection |
| 7 | Image (DLL) load |
| 8 | CreateRemoteThread |
| 10 | Process access (mimikatz signal) |
| 11 | File create |
| 13 | Registry value set |
| 22 | DNS query |

Sysmon + Windows Security log + PowerShell Operational log + RDP/Terminal Services logs covers most attacker behavior visible without a commercial EDR.

## Linux endpoint telemetry

Less mature than Windows but improving fast.

- **[auditd](https://linux.die.net/man/8/auditd)** — kernel-level, exhaustive, hard to query at scale
- **[auditbeat](https://www.elastic.co/beats/auditbeat)** — Elastic's friendly auditd wrapper
- **[osquery](https://osquery.io/)** — SQL queries against your endpoint state
- **[Falco](https://falco.org/)** — runtime detection rules for Linux + containers (CNCF graduated)
- **[Sysmon for Linux](https://github.com/Sysinternals/SysmonForLinux)** — yes, it exists, and works
- **eBPF-based EDRs** — Tracee, Tetragon (Cilium)

## Threat hunting

A hunt is a hypothesis-driven search. Templates:

- "If X attacker is here, I'd see Y." Then look for Y.
- "What's running on a domain controller that shouldn't be?"
- "Show me PowerShell processes whose parent is a browser, an Office app, or a shell."
- "Show me lsass.exe being read by a process that isn't taskmgr or wmiprvse."
- "Show me Kerberos TGS requests with unusual encryption types (RC4 in a modern environment)."

Frameworks:
- **TaHiTI** (Threat Hunting in TI), **PEAK** (Prepare-Execute-Act-Knowledge), **Mandiant TTP-based hunting** — all converge on the same hypothesis-driven loop.

[ThreatHuntingProject](https://github.com/threathuntingproject/ThreatHunting) and [HuntPedia](https://www.threathunting.net/library) are good starting libraries.

## Notable detection patterns

These show up in interviews and on the job constantly:

| Behavior | Detect by |
|---|---|
| Mimikatz / lsass dumping | EDR memory access alert; Sysmon EID 10 with target=lsass and unusual source |
| PowerShell empire / cobalt strike powershell stagers | AMSI events, encoded commands, unusual parent process |
| Kerberoasting | Many TGS-REQs from one principal in a short window for service tickets with RC4 |
| Pass-the-ticket | Logon Type 3 with unusual AuthenticationPackageName, ticket times near max lifetime |
| DCSync | Replication request from a non-DC account (4662 with replication GUID) |
| Golden ticket | Logons with Kerberos tickets whose lifetime exceeds domain policy, unusual encryption types |
| Web shell | New file write into web root by IIS/PHP process, then process spawns from web server |
| C2 beaconing | DNS / HTTPS callbacks at regular intervals (jitter analysis), low byte counts, unusual SNI |
| Lateral movement | Workstation→workstation SMB authentication that wasn't there yesterday; new admin shares |
| Living-off-the-land | rundll32/regsvr32/mshta running with internet egress; certutil downloading; bitsadmin uploads |

## Honeypots & deception

Cheap, disproportionately effective. Plant:
- A user account named `svc_backup_admin` in a privileged group, that nobody uses. Any auth attempt = alert.
- A file share named `Confidential_HR_2025` on a server that nobody should access. Any open = alert.
- Internal-network honeypots ([T-Pot](https://github.com/telekom-security/tpot), [Conpot](https://github.com/mushorg/conpot) for ICS).
- Canarytokens ([canarytokens.org](https://canarytokens.org/)) — embed in documents, AWS keys, DNS zones.
- Honey hashes — fake creds in LSASS memory of decoy hosts; Mimikatz extracts them; SOC alerts on those creds being used.

The signal-to-noise ratio is unbeatable. Real attackers trip honeypots; legitimate users don't.

## Incident response — the basics here, full chapter in [DFIR](dfir.md)

The PICERL lifecycle:

```
Preparation → Identification → Containment → Eradication → Recovery → Lessons
```

In practice:

1. **Detect** — alert fires
2. **Triage** — Tier 1 / Tier 2 confirms it's real
3. **Scope** — how many hosts? what data? when did it start?
4. **Contain** — isolate hosts, disable accounts, revoke tokens (read this list twice — order matters)
5. **Eradicate** — remove malware, close vuln, rotate creds
6. **Recover** — bring services back online with confidence
7. **Lessons** — write the post-incident report; update detections

For a major incident: declare, get leadership in the loop, retain external IR if needed (Mandiant, CrowdStrike Services, Volexity, etc.), notify legal/comms/regulators on appropriate timelines (72h for GDPR, varies in US).

## SOAR — automation that doesn't replace humans

SOAR (Security Orchestration, Automation, Response) ties SIEM alerts to runbooks. Common platforms: **Splunk SOAR (Phantom)**, **Tines**, **Microsoft Sentinel automation rules**, **Cortex XSOAR**, **Swimlane**, **Shuffle (OSS)**.

Good automation candidates:
- Enrich alert with threat intel lookups
- Reset stolen MFA enrollments
- Disable Entra ID account on confirmed compromise
- Pull EDR triage package from suspicious host
- File ServiceNow / Jira ticket with templated content
- Block IP at perimeter

Bad automation: anything irreversible without human approval. Auto-isolation of hosts during legitimate red team exercises has caused outages.

## Metrics that matter

The SOC's KPIs aren't "alerts closed":

- **Mean Time to Detect (MTTD)** — from initial compromise to first alert
- **Mean Time to Triage (MTTT)** — alert to analyst engagement
- **Mean Time to Contain (MTTC)** — alert to host isolated / account disabled
- **False Positive Rate** by detection
- **Coverage by ATT&CK technique** — how many of the techniques you care about have detections
- **Detection-as-code velocity** — PRs to detection repo, time to ship a new detection
- **Hunt yield** — hunts that found something / total hunts

## Tools to know

| Category | Tools |
|---|---|
| SIEM | Splunk, Sentinel, Elastic, Chronicle, Wazuh |
| EDR | CrowdStrike, MDE, SentinelOne, Cortex XDR, Carbon Black |
| Network IDS | Suricata, Snort, Zeek (Bro), Arkime (full pcap) |
| Endpoint forensics | KAPE (Eric Zimmerman), Velociraptor, GRR (Google) |
| Memory forensics | Volatility 3, Rekall (legacy) |
| Disk forensics | Autopsy, FTK, X-Ways |
| Log enrichment | MaxMind GeoIP, GreyNoise, AbuseIPDB, VirusTotal |
| YARA | yara-x, capa (capability scan) |
| Sandboxing | Cuckoo (legacy), Cape, ANY.RUN, Joe Sandbox, Hatching Triage |
| TIP | OpenCTI, MISP, Anomali |
| Atomic testing | Atomic Red Team, MITRE Caldera, Stratus Red Team (cloud) |
| Honeypots | T-Pot, Cowrie (SSH), Conpot (ICS), [`defense/mini_honeypot.py`](../../scripts/defense/mini_honeypot.py) |

## Hands-on lab path

1. **[Blue Team Labs Online](https://blueteamlabs.online/)** — investigations and challenges
2. **[CyberDefenders](https://cyberdefenders.org/)** — DFIR + blue team challenges
3. **[Letsdefend.io](https://letsdefend.io/)** — simulated SOC analyst environment
4. **[TryHackMe SOC Level 1 / 2 paths](https://tryhackme.com/path/outline/soclevel1)** — guided
5. **[HackTheBox Sherlocks](https://app.hackthebox.com/sherlocks)** — DFIR challenges
6. **[Splunk Boss of the SOC (BOTS)](https://github.com/splunk/botsv3)** — public datasets, fantastic for SPL practice
7. **[ELK + Sysmon home lab](https://detectionlab.network/)** — Chris Long's DetectionLab — pre-built attack/defense lab

## Certifications

| Cert | Level | Notes |
|---|---|---|
| **Security+ (CompTIA)** | Entry | Foundational, often a HR filter |
| **CySA+ (CompTIA)** | Junior SOC | Good for Tier 1 roles |
| **BTL1 / BTL2 (Security Blue Team)** | Junior–mid | Hands-on, well-regarded |
| **CDSA / CCD (HackTheBox)** | Mid | Modern blue team practical |
| **GCIH (SANS)** | Mid | Incident handling, expensive |
| **GCFA / GCFR / GCIA (SANS)** | Senior | Forensic, network, incident response — top of the field |
| **CISSP (ISC²)** | Manager | Knowledge cert, broad |
| **CySA+ → CCD → BTL2 → GCIH/GCFA** is a typical defender ladder |

## Real campaigns to study (for detection)

For each, ask: *what would I have seen?*

- **Sunburst (SolarWinds, 2020)** — backdoored DLL phoning home, careful sleeps. Detection only worked when FireEye realized their own red team tools were stolen.
- **HAFNIUM Exchange ProxyShell (2021)** — webshells dropped, EDR alerts on w3wp.exe spawning powershell, command-and-control beacons.
- **Conti leaks (2022)** — internal playbooks of a top-tier ransomware gang. Read them like exam answers.
- **Lapsus$ (2022)** — social engineering helpdesks. Detection: anomalous admin-tool logins after account-recovery flows.
- **MOVEit (Cl0p, 2023)** — mass exploitation, the day it broke. Detection: unusual file-write/web shell on MOVEit Transfer servers.
- **Volt Typhoon (PRC, 2023–24)** — living-off-the-land. Detection: anomalous PowerShell patterns from utilities, cmd.exe spawning from netsh, scheduled task creation by service accounts.

[The DFIR Report](https://thedfirreport.com/) again — read every quarterly writeup, it's the best free SOC training material on Earth.

## Interview questions

1. *"You see an alert: powershell.exe with `-enc`, parent process winword.exe. Walk me through your triage."*
2. *"What's the difference between EDR and antivirus?"*
3. *"Explain Kerberoasting from a defender's perspective. How would you detect it?"*
4. *"What does a beaconing C2 look like in network logs?"*
5. *"Walk me through PICERL with a ransomware example."*
6. *"How do you tune a noisy detection?"*
7. *"What's the Pyramid of Pain and why does it matter for detection strategy?"*

## Recommended reading

- *Blue Team Handbook: Incident Response Edition* (Murdoch)
- *The Practice of Network Security Monitoring* (Bejtlich) — older but the NSM mindset is timeless
- *Applied Network Security Monitoring* (Sanders & Smith)
- *Crafting the InfoSec Playbook* (Bollinger / Enright / Valites)
- [SANS Reading Room](https://www.sans.org/white-papers/) — free papers
- [Detection Engineering Weekly](https://www.detectionengineering.net/) — newsletter
- [Florian Roth's blog](https://cyb3rops.medium.com/) — Sigma originator, signature/detection legend

## Python script reference

This phase ships:
- [`defense/sigma_to_splunk.py`](../../scripts/defense/sigma_to_splunk.py) — bulk-convert Sigma rule directories to Splunk SPL
- [`defense/dns_exfil_detector.py`](../../scripts/defense/dns_exfil_detector.py) — flag long, high-entropy DNS subdomain queries (DNS exfiltration / iodine / dnscat2)

Plus carry-overs from earlier phases:
- [`defense/failed_ssh_analyzer.py`](../../scripts/defense/failed_ssh_analyzer.py)
- [`defense/ioc_extractor.py`](../../scripts/defense/ioc_extractor.py)
- [`defense/mini_honeypot.py`](../../scripts/defense/mini_honeypot.py)

---

[← Red Team](red-team.md)  ·  [DFIR →](dfir.md)
