# 🕵️ Digital Forensics & Incident Response (DFIR)

> When the alert is real, this is the team that runs in. DFIR is where security meets physical evidence — disk images, RAM captures, packet logs, and the meticulous reconstruction of "what did the attacker do, when did they do it, and what data is gone?"

For roles in: **CSIRT teams (US-CERT, CERT-In, JPCERT, AusCERT)**, **IR consultancy (Mandiant, CrowdStrike Services, Volexity, Stroz Friedberg, KPMG / EY / PwC IR teams)**, **government forensic labs (FBI Cyber Division, India CFSL, defense forensics)**, **internal IR at any large enterprise**, **e-discovery / litigation support**.

## DFIR fundamentals

DFIR has two intertwined disciplines:

- **Digital Forensics (DF)** — evidence-grade investigation. Chain of custody, hashes, write-blockers. May end up in court.
- **Incident Response (IR)** — operational. Speed matters. Less concerned with court admissibility, more with stopping the bleeding.

Most modern incidents need both. You triage first (IR), preserve evidence at the right moments (DF), and produce both a technical report and (often) materials suitable for legal proceedings.

## The PICERL lifecycle (in detail)

```
Preparation → Identification → Containment → Eradication → Recovery → Lessons Learned
```

### Preparation

The phase that decides whether you'll succeed.

- **IR plan written, tested, signed off** by legal and execs. Includes external counsel and PR contacts.
- **Runbooks** for common incident types (BEC, ransomware, web compromise, insider data theft).
- **Tooling** licensed and ready: forensic image acquisition, EDR with deploy-everywhere capability, isolated forensic VMs.
- **Logging baseline** — you have what you'll need. (Yes, this is also blue team's job. They overlap.)
- **Tabletop exercises** quarterly minimum. The first time you run the playbook should never be in a real incident.
- **Retainer** with an external IR firm for surge capacity — or established relationships with multiple if you're large.
- **Cyber insurance** policies — know what they cover and what they require (some require pre-approval to engage IR firms).

### Identification

How does the incident come to you?
- SOC alert (most common)
- Threat intel notification ("we saw your domain in attacker infrastructure")
- Third party (FBI, CISA, ISP, peer org)
- User report ("I got this weird email" / "my files have weird extensions")
- External (ransom note, dark web post, journalist)

Your first job: confirm it's real, not noise. Second: quickly assess scope.

### Containment

Two flavors:

| Flavor | When | How |
|---|---|---|
| **Short-term** | Right now, stop the bleeding | Network isolation, account disable, token revoke, kill malicious process |
| **Long-term** | Days to weeks | Patch the vuln, segment the network, roll all credentials |

**Order of operations matters.** Disable accounts before you alert the attacker by isolating hosts. Revoke OAuth tokens before disabling accounts (a disabled-but-still-tokened account can keep working in M365 for hours).

For ransomware specifically:
1. **Don't power off** infected hosts — you lose memory artifacts. Disconnect network instead.
2. Identify patient zero and the spread method (SMB, RDP, AD).
3. Block lateral movement immediately (firewall rules between subnets, disable SMB if feasible).
4. Preserve evidence per ROE before re-imaging anything.

### Eradication

Remove the attacker's persistence mechanisms:
- Reset all credentials with confirmed exposure (and probably more — Mandiant's rule of thumb: assume all)
- Reset the **krbtgt account password twice** (with proper waiting period) if AD was compromised — this invalidates Golden Tickets
- Remove malicious AD objects, scheduled tasks, services, registry keys, scripts in startup folders
- Remove malicious cloud identities, OAuth grants, app registrations, federated trusts
- Patch the entry vulnerability

If you missed any persistence, the attacker comes back. Be thorough. Better orgs run a hunt sweep across all hosts/identities looking for any indicators of the attacker's known TTPs.

### Recovery

Bring services back. Validate they're clean. Monitor closely for re-emergence (the attacker is watching you bring things back; common pattern: lay low for 30 days, return).

### Lessons learned

Write the post-incident report. Include:
- Timeline (UTC times)
- Root cause and contributing factors
- Detection gaps — what *should* have caught this earlier
- Response gaps — where the runbook failed or didn't exist
- Action items with owners and dates
- Costs (incident hours, downtime, IR firm bill, insurance, legal, regulatory fines)

Hold a blameless post-mortem. Punishing analysts who reported "weird logs that turned out to matter" is how organizations die.

## Order of volatility

When acquiring evidence, capture from most volatile to least:

1. **CPU registers, cache** — gone in nanoseconds, rarely captured
2. **RAM (memory)** — gone on power-off
3. **Network state** (connections, ARP cache, routing) — minutes
4. **Running processes** — seconds to minutes
5. **Disk** — survives shutdown, but be careful — encryption, secure delete, anti-forensics
6. **Remote logs / archives** — backed up, durable
7. **Physical configuration / topology** — durable

If you only have time for one: **memory**. RAM holds passwords, encryption keys, in-memory beacons, network connections, processes that didn't write to disk, and PowerShell command history.

## Memory forensics

The single highest-yield artifact in modern IR.

### Acquisition

**Windows:**
- [WinPMEM](https://github.com/Velocidex/WinPmem) — open source, FOSS
- [DumpIt](https://www.comae.com/) — Comae's, free
- [Magnet RAM Capture](https://www.magnetforensics.com/resources/magnet-ram-capture/) — free, GUI
- [FTK Imager](https://www.exterro.com/digital-forensics-software/ftk-imager) — free, ubiquitous
- For VMs: snapshot the VM with memory included — your hypervisor already did the work

**Linux:**
- [LiME](https://github.com/504ensicsLabs/LiME) — Linux Memory Extractor
- [AVML](https://github.com/microsoft/avml) — Microsoft's, single static binary

**macOS:**
- [OSXPmem](https://github.com/google/rekall/tree/master/tools/osx/MacPmem) — old but works for some versions
- [macOSPmem](https://github.com/Velocidex/c-aff4/tree/master/tools/pmem) — newer, builds the AFF4 file format

### Analysis — Volatility 3

The de-facto memory forensics framework.

```bash
# Identify the OS / profile
vol -f memory.raw banners

# Process listing
vol -f memory.raw windows.pslist
vol -f memory.raw windows.pstree                # parent-child tree
vol -f memory.raw windows.psscan                # scan for hidden / terminated

# Network connections
vol -f memory.raw windows.netscan

# Loaded DLLs (for a specific PID)
vol -f memory.raw windows.dlllist --pid 1234

# Code injection signals
vol -f memory.raw windows.malfind                # finds RWX private memory regions
vol -f memory.raw windows.hollowfind             # process hollowing detection
vol -f memory.raw windows.svcscan                # services
vol -f memory.raw windows.cmdline                # command-line arguments

# Dump executable memory regions
vol -f memory.raw windows.malfind --dump --dump-dir ./dumps/

# Registry hives in memory
vol -f memory.raw windows.registry.hivelist
vol -f memory.raw windows.registry.printkey --key 'Software\Microsoft\Windows\CurrentVersion\Run'

# LSASS — credential dump
vol -f memory.raw windows.dumpfiles --pid <lsass_pid>
# then: pypykatz lsa minidump <dumpfile>     to extract creds, like Mimikatz
```

For Linux memory:
```bash
vol -f memory.raw linux.banner
vol -f memory.raw linux.pslist
vol -f memory.raw linux.bash         # bash history from memory!
vol -f memory.raw linux.malfind
vol -f memory.raw linux.tty_check    # check tty struct integrity
```

## Disk forensics

### Imaging

Always use a **write-blocker** (hardware preferred: Tableau / WiebeTech) when imaging from physical disks. The image is your evidence; the original disk is preserved untouched.

Tools:
- **dd / dcfldd** — bit-for-bit Linux imaging
- **FTK Imager** — Windows, free, friendly
- **Guymager** — Linux, fast, used by SANS DFIR distros
- **EnCase Forensic Imager** — commercial, court-standard
- For modern macOS / Windows BitLocker / FileVault: image while running, get the encryption key from RAM, or compel/recover the password

Image formats:
- **E01 (EnCase)** — chunked, compressed, with built-in hashing. Industry standard.
- **AFF4** — modern open format
- **Raw / dd** — simplest, no metadata

### Analysis — Autopsy / The Sleuth Kit

[Autopsy](https://www.autopsy.com/) is the open-source GUI; under the hood it uses [The Sleuth Kit (TSK)](https://www.sleuthkit.org/sleuthkit/). Free.

Commercial: **EnCase**, **FTK**, **X-Ways Forensics** (the connoisseur's choice), **Magnet AXIOM**.

What you'll do:
- File system timeline (NTFS $MFT, EXT inode timestamps)
- Recover deleted files
- Carve unallocated space (PhotoRec, Foremost, Bulk Extractor)
- Analyze browser history / cache / cookies
- Parse registry hives (RegRipper, Eric Zimmerman tools)
- Extract Windows artifacts (Prefetch, Amcache, ShimCache, UsrClass.dat, ShellBags, USN Journal, $LogFile)
- Mount the image read-only with `mmls` + `mount -o ro,loop,offset=...` for live triage

### Eric Zimmerman's tools (the standard Windows artifact toolkit)

Free, fast, exhaustive. [https://ericzimmerman.github.io/](https://ericzimmerman.github.io/)

| Tool | Artifact |
|---|---|
| `MFTECmd` | NTFS $MFT — file metadata + deleted file recovery |
| `RegistryExplorer` / `RECmd` | Registry hives |
| `PECmd` | Prefetch (.pf) — what ran |
| `SBECmd` | ShellBags (User folder access) |
| `LECmd` | Lnk files (.lnk) |
| `JLECmd` | Jump Lists |
| `AmcacheParser` | Amcache.hve — executed binaries |
| `EvtxECmd` | EVTX parsing |
| `WxTCmd` | ActivitiesCache.db — Windows timeline |

Combine with [KAPE (Kroll Artifact Parser and Extractor)](https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape) — KAPE collects "all the artifacts" off a live or imaged Windows system, then runs the parsers automatically.

## Windows event log forensics — EVTX

The single richest artifact set on Windows. Live: `C:\Windows\System32\winevt\Logs\*.evtx`. From an image: same path.

Key channels:

| Log | Critical events |
|---|---|
| `Security.evtx` | 4624 (logon), 4625 (failed logon), 4634/4647 (logoff), 4672 (privileged logon), 4688 (process create), 4720/4726 (account create/delete), 4732/4733 (group changes), 4768/4769 (Kerberos), 7045 (service install) |
| `System.evtx` | 7045 (service install), 6005 (boot), 1074 (shutdown / reason) |
| `Microsoft-Windows-Sysmon/Operational.evtx` | 1 (process), 3 (network), 7 (image load), 8 (CreateRemoteThread), 10 (process access), 11 (file create), 13 (registry), 22 (DNS) |
| `Microsoft-Windows-PowerShell/Operational.evtx` | 4103 (pipeline), 4104 (script block — the gold mine), 4105/4106 (start/stop) |
| `Microsoft-Windows-WinRM/Operational.evtx` | WinRM use — common lateral movement evidence |
| `Microsoft-Windows-TerminalServices-LocalSessionManager/Operational.evtx` | RDP session start/stop |
| `Microsoft-Windows-TaskScheduler/Operational.evtx` | Scheduled task creation/run |

Parse with: `EvtxECmd`, **chainsaw** ([https://github.com/WithSecureLabs/chainsaw](https://github.com/WithSecureLabs/chainsaw)), **DeepBlueCLI** ([https://github.com/sans-blue-team/DeepBlueCLI](https://github.com/sans-blue-team/DeepBlueCLI)), or our [`forensics/evtx_triager.py`](../../scripts/forensics/evtx_triager.py).

`chainsaw` is the go-to: applies Sigma rules across EVTX directories, very fast.

## Network forensics

### Full PCAP

If you have it, it's the ground truth. Tools:

- **Wireshark** — universal
- **tshark** — Wireshark CLI for big files
- **Arkime** (formerly Moloch) — index full pcap at scale, Elasticsearch-backed
- **Suricata + EVE JSON** — IDS that produces structured logs alongside alerts
- **Zeek (Bro)** — protocol logs (conn.log, http.log, ssl.log, dns.log) — the most useful network artifact ever invented

### Flow data

When pcap is too much:
- NetFlow / sFlow / IPFIX — connection metadata
- Zeek conn.log — better; includes service inferred, bytes per direction, durations
- Cloud equivalents: VPC Flow Logs (AWS), NSG flow logs (Azure), VPC Flow Logs (GCP)

### What to look for

- **C2 beaconing**: regular intervals (with jitter), small request/response sizes, long durations
- **Data exfiltration**: large outbound from an unusual host to an unusual destination, especially over DNS or HTTPS to non-business domains
- **Lateral movement**: SMB / WinRM / RDP traffic between hosts that don't usually talk
- **Anomalous JA3/JA4**: TLS fingerprint of clients — Cobalt Strike beacon's JA3 has been catalogued; many implants have stable, identifiable JA3 hashes
- **DNS tunneling**: unusually long subdomain labels, high subdomain entropy, lots of TXT/NULL queries, sub-domain volumes inconsistent with browsing patterns

Our [`defense/dns_exfil_detector.py`](../../scripts/defense/dns_exfil_detector.py) script catches the simple DNS exfil patterns.

## Cloud forensics

The hot growth area. The big three:

### AWS

- **CloudTrail** — every API call. Configure organization trail to all-regions, immutable, multi-account.
- **VPC Flow Logs** — connection metadata
- **GuardDuty** — managed threat detection
- **Athena over CloudTrail S3 logs** — fastest way to query at scale
- **AWS Detective** — graph-based investigation
- **CloudWatch Logs** — application logs
- For compromise: snapshot the EBS volume, dump instance memory if possible, capture metadata for the IAM role/credentials in use

### Azure / Entra ID

- **Microsoft Sentinel** — SIEM with native Entra/Defender integration
- **Microsoft Defender for Cloud (MDC)** — formerly Azure Security Center
- **Audit logs** + **Sign-in logs** in Entra ID
- **Unified Audit Log** in M365 — every user action across SharePoint/Exchange/Teams (90-day default retention; extend!)
- **Get-AzureADAuditSignInLogs / MS Graph** — programmatic access
- For compromise: `Get-MailboxAuditConfig`, `Search-MailboxAuditLog` for mailbox-level evidence; check mailbox forwarding rules, OAuth grants, app registrations, conditional access bypasses

### GCP

- **Cloud Audit Logs** — Admin Activity, Data Access, System Event, Policy Denied
- **Security Command Center** — managed detection
- **VPC Flow Logs**

Tools that span clouds:
- **[Cado Response](https://www.cadosecurity.com/)** — commercial, IR-focused cloud forensics
- **[Cloud-Forensic-Utils (CFU)](https://github.com/google/cloud-forensics-utils)** — Google open source
- **[AWS_IR](https://github.com/ThreatResponse/aws_ir)** / **[Margaritashotgun](https://github.com/ThreatResponse/margaritashotgun)** — cloud memory acquisition
- **[Hayabusa](https://github.com/Yamato-Security/hayabusa)** for Windows event analysis

## Container and Kubernetes forensics

Increasingly common. Containers are ephemeral — once they're killed, evidence is gone.

- **Falco runtime alerts** — capture behavioral evidence as it happens
- **Container image hash and registry source** — track provenance
- **Kubernetes audit log** — every API call
- **etcd state snapshot** — at minimum, before recovery
- **eBPF-based EDRs (Tetragon, Tracee)** — preserve syscall-level events
- **Process namespace dump** — `nsenter` into the container, run forensic tools

## Indicators of Compromise (IOCs)

You'll extract these as you investigate, share them with peers/threat intel, hunt for them across your environment.

Categories: IPs, domains, URLs, file hashes (MD5/SHA1/SHA256), JA3/JA4, mutex names, registry keys, persistence mechanism details, SSH keys, TLS cert thumbprints, named pipes, scheduled task names, service names.

Our [`defense/ioc_extractor.py`](../../scripts/defense/ioc_extractor.py) extracts IOCs from any text source. Output → MISP / OpenCTI for sharing (see [Threat Intel](threat-intel.md)).

## Anti-forensics — what attackers do

You'll fight this. Common techniques:

- **Log clearing** (`wevtutil clear-log`, `Clear-EventLog`) — but the action of clearing leaves an event (1102 in Security)
- **Timestomp** — modify file MAC times. Detectable: $MFT $STANDARD_INFORMATION vs $FILE_NAME divergence
- **Slack space hiding** — small files in unallocated NTFS slack
- **Encryption** — VeraCrypt containers, hidden volumes
- **Self-deleting droppers** — common in ransomware
- **Fileless** — PowerShell-only, registry-stored payloads
- **Living off the land** — no malware on disk to find
- **Anti-VM / anti-sandbox checks** — sample doesn't detonate in your sandbox

The defender's edge: most attackers don't fully clean up. Forensics is finding the things they missed.

## Reporting

A DFIR report has:
- **Executive summary** (1 page) — what happened, business impact, status, key recommendations
- **Incident overview** — scope, timeline, attribution (with confidence)
- **Technical narrative** — chronological, hyperlinked to evidence
- **Indicators of Compromise** — for blocking/sharing
- **MITRE ATT&CK mapping** — every observed TTP
- **Lessons learned and recommendations** — concrete, prioritized
- **Appendices** — detailed artifacts, tool output, screenshots

For court-relevant cases, every claim must be backed by evidence with documented chain of custody. The technical narrative is essentially the prosecution's story, and it has to hold up under cross-examination.

## Hands-on labs

- **[BlueTeamLabs Online — DFIR challenges](https://blueteamlabs.online/)** — many free
- **[CyberDefenders.org](https://cyberdefenders.org/)** — phenomenal real-world challenges
- **[Magnet Weekly CTF](https://www.magnetforensics.com/blog/category/magnet-weekly-ctf-challenge/)** — vendor's free monthly challenge
- **[SANS DFIR Challenges (DFIR.training)](https://www.dfir.training/challenges)**
- **[Sherlocks (HackTheBox)](https://app.hackthebox.com/sherlocks)**
- **[Splunk BOTS v1/v2/v3](https://github.com/splunk/botsv3)** — datasets + questions, bring your own Splunk
- **[Volatility memory samples](https://github.com/volatilityfoundation/volatility/wiki/Memory-Samples)** — practice on canonical CTF memory dumps

## Certifications

| Cert | Provider | Notes |
|---|---|---|
| **GCFA** | SANS | Forensic Analyst — top of the field, very expensive |
| **GCFR** | SANS | Cloud Forensic Responder |
| **GCIH** | SANS | Incident Handler |
| **GNFA** | SANS | Network Forensic Analyst |
| **GREM** | SANS | Reverse-Engineering Malware (overlaps with [Malware Analysis](../04-specializations/malware-analysis.md)) |
| **GIAC GCDA / GCED** | SANS | Defensive certs at different levels |
| **CHFI** | EC-Council | Forensic, broad |
| **EnCE** | Guidance Software | EnCase Certified Examiner — court-credibility cert |
| **AccessData ACE** | AccessData | FTK Certified Examiner |
| **Magnet AX200/AX250** | Magnet Forensics | AXIOM-focused |
| **PNPT (TCM)** | TCM Security | Includes IR/forensics |
| **CDSA / CCD** | HackTheBox | Modern, hands-on |

## Real incidents to study

- **Colonial Pipeline (2021, DarkSide ransomware)** — root cause: dormant VPN account, no MFA. Read the [SANS analysis](https://www.sans.org/blog/colonial-pipeline-attack-overview/).
- **MOVEit (2023, Cl0p)** — mass exploitation; thousands of victims. Read the CISA advisory and [Mandiant's report](https://cloud.google.com/blog/topics/threat-intelligence/zero-day-moveit-data-theft).
- **MGM/Caesars (2023, Scattered Spider)** — helpdesk social engineering, ESXi ransomware. Read [TrustedSec writeup](https://www.trustedsec.com/blog/scattered-spider-cease-and-desist).
- **Microsoft Storm-0558 (2023)** — token forgery from stolen MSA key. CISA's [Cyber Safety Review Board report](https://www.cisa.gov/sites/default/files/2024-04/CSRB_Review_of_the_Summer_2023_MEO_Intrusion_Final_508c.pdf) is required reading.
- **xz/liblzma (2024)** — supply chain near-miss. The original [openwall mailing list post by Andres Freund](https://www.openwall.com/lists/oss-security/2024/03/29/4).
- **Snowflake customer breaches (2024)** — credential reuse + no MFA — affected Ticketmaster, AT&T, Santander.

## Interview questions

1. *"Walk me through the order of volatility."*
2. *"You're called to a host suspected of compromise. What do you do first? What do you avoid?"*
3. *"What does Volatility's `malfind` plugin look for?"*
4. *"Difference between $STANDARD_INFORMATION and $FILE_NAME timestamps in NTFS — and why a forensic examiner cares."*
5. *"How do you investigate a Business Email Compromise in M365?"*
6. *"What's krbtgt and why do you reset it twice?"*
7. *"Walk me through your DFIR approach to a confirmed ransomware incident."*

## Recommended reading

- *Practical Forensic Imaging* (Bruce Nikkel) — mostly about imaging done right
- *The Art of Memory Forensics* (Ligh / Case / Levy / Walters) — the volatility canon
- *Incident Response & Computer Forensics, 3rd ed.* (Luttgens / Pepe / Mandia) — Mandiant's playbook
- *File System Forensic Analysis* (Brian Carrier) — the bible. Yes, all 600+ pages.
- *Practical Malware Analysis* (Sikorski / Honig) — companion for IR
- *Investigating Windows Systems* (Carvey)
- [SANS DFIR posters](https://www.sans.org/posters/?focus-area=digital-forensics) — free, frequently updated, print and pin to your wall
- [Eric Zimmerman's blog](https://binaryforay.blogspot.com/) — author of half the tools you'll use
- [DFIR.training](https://www.dfir.training/) — community-curated resources

## Python script reference

This phase ships:
- [`forensics/evtx_triager.py`](../../scripts/forensics/evtx_triager.py) — fast triage of Windows EVTX directories with per-channel summaries and notable-event highlighting

---

[← Blue Team](blue-team.md)  ·  [Threat Intel →](threat-intel.md)
