# 🔴 Red Team Operations

> Pentesting is finding bugs. Red teaming is **emulating an adversary**. The objective isn't a list of vulnerabilities — it's stealing the crown jewels without getting caught, and then teaching the blue team how to catch you next time.

For roles in: **internal red teams (Microsoft, Google, Amazon, banks, defense contractors)**, **TIBER-EU / iCAST / CBEST regulated red teams (EU/HK/UK)**, **NSA Tailored Access Operations (TAO)**, **DRDO/NTRO offensive units (India)**, and high-end consultancies (Mandiant, NCC Group, IOActive, SpecterOps).

## Pentest vs Red Team — the real difference

| | Pentest | Red Team |
|---|---|---|
| Goal | Find as many bugs as possible | Achieve a specific objective (steal X, persist for Y days) |
| Scope | Defined assets / IPs | Often "the whole company" |
| Time | Days to weeks | Weeks to months |
| Stealth | Not required | Critical |
| Notification | Blue team knows | Blue team does *not* know (most cases) |
| Output | List of findings + CVSS | Story of how the objective fell + detection gaps |
| Adversary emulation | No | Yes — emulate FIN7, APT29, Volt Typhoon, etc. |

A pentest finds vulnerabilities. A red team finds **systemic weaknesses** — the misconfigured GPO that lets every helpdesk AD attack work, the SOC that can't correlate cross-system alerts, the assumption that "we have EDR" means "we'll see it."

## The kill chain you'll actually follow

```
Recon → Initial Access → Execution → Persistence → Defense Evasion →
Credential Access → Discovery → Lateral Movement → Collection →
Command & Control → Exfiltration → Impact
```

This is **MITRE ATT&CK**. Memorize the column headers, learn 3–5 representative techniques per column, and you have the working vocabulary of every red team report.

## Adversary emulation — the modern standard

Don't "be a generic attacker." Pick a real threat group your client cares about and emulate them:

| Group | Hallmarks |
|---|---|
| **APT29 (Cozy Bear / SVR)** | Stealthy, patient, custom malware (Beacon, GoldFinder, Sibot), abuses Azure / O365 |
| **APT28 (Fancy Bear / GRU)** | Spearphish, X-Agent, X-Tunnel, election-meddling, military targeting |
| **Lazarus (DPRK)** | Financial (banks, crypto), supply chain (3CX, JumpCloud), wiper deployment |
| **Volt Typhoon (PRC)** | Living-off-the-land in critical infrastructure, ProxyShell-era exploits, dormant footholds |
| **FIN7** | E-crime, sophisticated social engineering, custom Carbanak/Tirion |
| **APT41 (PRC)** | Dual-mission espionage + financial, vast initial access toolkit |
| **Conti / LockBit / ALPHV** | Big Game ransomware: Cobalt Strike, Mimikatz, RClone, fast TTPs |
| **Scattered Spider / UNC3944** | Helpdesk social engineering, MFA fatigue, Okta/Azure abuse — the model 2024 e-crime threat |

**[MITRE Adversary Emulation Library](https://github.com/center-for-threat-informed-defense/adversary_emulation_library)** has scenario plans for many of these. **[CALDERA](https://caldera.mitre.org/)** automates execution. **[Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)** has individual technique tests.

## The red team operation lifecycle

### 1. Pre-engagement & ROE

You can't skip this. Get in writing:
- **Objectives** — exactly what counts as success
- **Scope** — which IPs, domains, subsidiaries, cloud tenants
- **Out of scope** — DR systems, life-safety systems, third parties
- **Crown jewels** — what you're trying to reach
- **Deconfliction contacts** — who at the client knows about you (usually 2-3 people: CISO, GC, head of detection — the "trusted agents")
- **Get-out-of-jail-free letter** — signed authorization you carry on physical engagements
- **Stop conditions** — when do you halt and call?
- **Communication channel** — encrypted, frequency
- **Reporting deliverables and timeline**

For TIBER-EU/CBEST/iCAST regulated tests, the structure is more formal — threat intel report comes first (a separate consultancy), then the red team works from that profile.

### 2. Threat intel & target profile

Before you touch anything:
- OSINT on the target (LinkedIn, GitHub, certs, DNS, reused infrastructure)
- Tech stack inference (job postings, conference talks)
- Cultural intel (org structure, executive names, internal lingo)
- Known suppliers and managed service providers
- Public breach data — credential reuse is gold

### 3. Initial access

Most realistic vectors in 2026:
- **Phishing** — still works, especially Microsoft 365 OAuth consent grants and device code phishing
- **Supply chain / third-party** — your target's MSP may be softer
- **Public-facing exploit** — old VPN appliances, Exchange, Citrix, MOVEit, Confluence
- **Valid credentials** — purchased or leaked on TG/Russian Market/breach dumps
- **Social engineering helpdesk → MFA reset** (Scattered Spider playbook)
- **Physical** (if scoped): tailgate, badge clone, drop USB
- **Wireless** (if scoped): rogue AP, captive portal cred-cap
- **Implant / dropbox** (if physical scoped): Raspberry Pi or LAN Turtle in a conference room

### 4. C2 — Command & Control

Your beacon's lifeline. Modern frameworks:

| Framework | License | Notes |
|---|---|---|
| **[Cobalt Strike](https://www.cobaltstrike.com/)** | Commercial | Industry standard. Beacon is excellent. Detected by every EDR. |
| **[Sliver](https://github.com/BishopFox/sliver)** | OSS (BSD) | Bishop Fox's. Mature, multi-platform, growing. |
| **[Mythic](https://github.com/its-a-feature/Mythic)** | OSS | Modular — many "agents" (Apollo, Athena, Poseidon, etc.) |
| **[Havoc](https://github.com/HavocFramework/Havoc)** | OSS | Clean modern UI, capable beacon (Demon) |
| **[Brute Ratel C4](https://bruteratel.com/)** | Commercial | Pricier than CS, very strong evasion |
| **[Empire (revival)](https://github.com/BC-SECURITY/Empire)** | OSS | Powershell-heavy, mostly mature |
| **[Nighthawk](https://www.mdsec.co.uk/nighthawk/)** | Commercial (vetted clients only) | Top-tier, hard to acquire |

C2 traffic patterns to design for:
- **HTTPS over CDN domain fronting** — until cloud providers banned it. Now: legitimate domains you control, with category-aged certs.
- **Mailslot / SMB beacon** — for C2 over an internal network when your initial host has egress but lateral hosts don't
- **DNS C2** — slow but bypasses many filters
- **Cloud apps as C2** (Slack, Discord, Telegram, GitHub) — blends with normal traffic
- **Long sleep + jitter** — beacons callback every 30–60 minutes, not every 5 seconds

### 5. EDR evasion — the actual battle

Modern EDR (CrowdStrike Falcon, Microsoft Defender for Endpoint, SentinelOne, Carbon Black) does:

- **Userland API hooking** — they monitor `kernel32!CreateRemoteThread`, `ntdll!NtAllocateVirtualMemory`, etc.
- **Kernel callbacks** — `PsSetCreateProcessNotifyRoutine`, `PsSetLoadImageNotifyRoutine`
- **ETW (Event Tracing for Windows)** — telemetry firehose; many EDRs read from `Microsoft-Windows-Threat-Intelligence`
- **AMSI** — anti-malware scan interface, every PowerShell command runs through it
- **Behavioral detection** — sequences of actions, not just one
- **Memory scanning** — periodic scan for unbacked executable pages, beacon signatures

Common evasion (defensive technique knowledge — for red teams operating *with permission*):

| Technique | Description |
|---|---|
| Direct/indirect syscalls (HellsGate, HalosGate, RecycledGate, Tartarus) | Bypass userland hooks by calling syscalls directly |
| API unhooking | Restore original ntdll bytes from disk before suspicious calls |
| AMSI bypass | Patch `AmsiScanBuffer` in memory to return clean (signature changes monthly) |
| ETW bypass | Patch `EtwEventWrite` to NOP; or unhook ntdll's ETW providers |
| Module stomping / module overloading | Load benign DLL, overwrite its .text with shellcode, original module name remains |
| Process injection alternatives — APC, early bird, thread hijacking, Atom Bombing | Avoid CreateRemoteThread |
| In-memory encryption (sleeptask) | Encrypt beacon between callbacks, decrypt to execute |
| Beacon Object Files (BOFs) | Run small C-compiled tools in beacon's process — no new process tree |
| Userland reflective loading via fork-and-run alternatives | Avoid suspicious child processes |
| Living off the land (LOL bins) | rundll32, regsvr32, mshta, msbuild, installutil, csc.exe, wmic, certutil |
| Kerberos abuse instead of password attacks | Doesn't trigger NTLM-based detection |

**Important**: this is rapidly-changing cat-and-mouse. Anything written today may be detected tomorrow. Red teamers maintain private toolkits, rotate them, and accept burns.

### 6. Internal recon

Once you've got a foothold — keep your noise low.

```powershell
# from a beacon, NOT in a SOC-noisy way
whoami /priv /groups
hostname
ipconfig /all
net config workstation
nltest /domain_trusts
nltest /dclist:corp.local

# AD enumeration via LDAP (no SharpHound noise)
$searcher = [adsisearcher]"(objectClass=user)"
$searcher.FindAll() | Select -ExpandProperty Properties

# softer than SharpHound:
SharpHound.exe -c DCOnly --Stealth
# or — better — collect via custom script using ADWS
```

For Active Directory specifically, see [Phase 3 / Active Directory chapter](../03-offensive/active-directory.md). For pivoting see [Phase 3 / Pivoting](../03-offensive/pivoting.md).

### 7. Persistence

Plant something durable. Categories:

- **Scheduled tasks / cron** — basic but works
- **Service installation** — needs SYSTEM
- **Registry Run keys / startup folder** — user-context persistence
- **WMI event subscription** — fileless, classic
- **Skeleton key, DCShadow, AdminSDHolder ACL** — AD persistence (post-DA)
- **Golden ticket** (offline forging) — tier-0 persistence
- **Hidden services** — abuse Windows services with debug paths
- **Browser extension implants** — recently popular for cred theft
- **Cloud persistence** — service principal with secret you control, password reset for an admin account, federated trust to attacker IdP

Choose the persistence method that **doesn't blink in the EDR's behavior model**. WMI subscriptions and registry tweaks pre-2018 were silent — many are now alerted on. Test in a lab matching the client's stack.

### 8. Lateral movement

See [Phase 3 / Pivoting](../03-offensive/pivoting.md). Add to the list:
- **WMI exec** (`wmic /node:host process call create`)
- **DCOM** (MMC20.Application, ShellWindows, ShellBrowserWindow)
- **PSExec / WinRM** — loud unless customized
- **Pass-the-hash, pass-the-ticket** — quiet if you control the auth flow
- **RDP with stolen creds** — interactive evidence on target
- **ADCS abuse** — if the target has misconfigured cert templates, Tier-0 in one step

### 9. Action on objectives

What you came to do. Most common objectives:
- **Domain admin / global admin / cloud root** — proves Tier-0 reach
- **Specific dataset** — credit card warehouse, customer DB, source code repo
- **Industrial control** — touch-but-don't-disrupt a PLC (with careful ROE)
- **Wire transfer** — table-top demonstration only, never actually move money
- **C-suite mailbox** — proves influence-operation potential

Document the path; don't disrupt. Take screenshots, gather evidence, leave artifacts that the blue team can reasonably find later.

### 10. Reporting and debrief

The most underrated phase. A red team report has:

- **Executive summary** — narrative of how the objective fell, in board-readable language
- **Attack path diagram** — every host, every credential, every pivot
- **Detection gap analysis** — for each TTP used, did the SOC see it? Which control should have caught it?
- **Recommendations** — prioritized, concrete, and tied to specific gaps
- **Appendices** — IOCs, command logs, MITRE ATT&CK mapping

Then a **purple team debrief** — replay the engagement with the blue team, walking through their telemetry to find what they missed. This is the actual value delivered.

## OPSEC — operational security

Your tradecraft is your reputation. A few rules:

- **Compartmentalize infrastructure.** One client per VPS, fresh redirector domains, no overlap
- **Pre-stage and age domains.** New domains are flagged. Buy aged domains, build category reputation
- **Validate every C2 callback.** Reverse-DNS your own redirectors, check certificate revocation. Sandbox callers (CrowdStrike, etc.) probe your infrastructure
- **Wait for activity hours.** Don't do recon at 3 a.m. local time
- **Watch for honeypots.** Workstations named `HOUNDS01`, file shares named `Confidential_Salaries.xlsx` left in obvious places, AD users named `svc_admin_legacy`
- **Don't reuse infrastructure across clients.** Defenders share IOCs. One client burns your domain, all of them do.

## C2 infrastructure design

The classic redirector architecture:

```
Client target   ──HTTPS──▶  Cloudfront/CDN   ──▶  Apache/Nginx redirector  ──▶  Team server (CS)
                                ↑                       (HTTP profiles)
                                Legitimate-looking domain, aged, categorized as "business" or "tech news"
```

Or DNS-only:

```
Beacon ─DNS queries to attacker.example.org─▶ NS server (TS or routed)
```

Modern variants use cloud serverless (CloudFront/Azure Front Door for redirector-as-a-service) and SaaS apps (Slack/Discord webhooks) to blend in.

## Tools red teamers actually use day-to-day

| Category | Tool |
|---|---|
| C2 | Cobalt Strike, Sliver, Mythic, Havoc, Nighthawk |
| AD enumeration | SharpHound, BloodHound CE, ADExplorer, AD-Recon |
| AD attacks | Rubeus, Mimikatz, Certipy, Coercer, ADCSPwn, krbrelayx |
| Exec | PSExec (Impacket), WMIExec, DCOMExec, WinRM, SMBexec, AtExec |
| Cred dumping | Mimikatz, lsassy, secretsdump.py, NanoDump, dontstealmycheese (DSC) |
| Phishing | EvilGinx2 / EvilGinx3 (AiTM), GoPhish, Modlishka, Muraena, MailSniper (M365 recon) |
| Payload generation | msfvenom, Donut, ScareCrow, Inceptor, Veil, ConfuserEx (.NET) |
| LOL execution | rundll32, regsvr32, mshta, certutil, csc, msbuild — all valid Windows binaries |
| Misc | RClone (exfil), 7z (compression), Cobalt Strike's BOFs (sysinfo, whoami, etc.), GhostPack tools |

## Frameworks and methodologies

- **MITRE ATT&CK** — TTPs (https://attack.mitre.org)
- **MITRE Engage** — adversary engagement (deception)
- **MITRE D3FEND** — defense techniques mapped to ATT&CK
- **Cyber Kill Chain (Lockheed Martin)** — older but still used
- **Diamond Model of Intrusion Analysis** — for analysis/attribution
- **TIBER-EU, CBEST (UK), iCAST (HK), AASE (Singapore)** — regulated red team frameworks for financial sector

## Hands-on labs

- **[GOAD (Game of Active Directory)](https://github.com/Orange-Cyberdefense/GOAD)** — a fully vulnerable multi-domain AD lab, free to deploy
- **[Vulnlab](https://www.vulnlab.com/)** / **[Hack The Box Pro Labs](https://app.hackthebox.com/prolabs)** — multi-machine red team labs (Offshore, RastaLabs, Cybernetics)
- **[OSEP](https://www.offsec.com/courses/pen-300/)** course + exam — OffSec's red team / evasion cert
- **[CRTO / CRTL](https://training.zeropointsecurity.co.uk/)** (Zero-Point Security) — Rastamouse's Cobalt Strike-focused red team certs, very respected
- **[Maldev Academy](https://maldevacademy.com/)** — malware development, evasion-focused
- **[Black Hat Python](https://nostarch.com/blackhatpython2E)** + **[The Hacker Playbook](https://thehackerplaybook.com/)** — book series

## Certifications

| Cert | Provider | Hands-on | Notes |
|---|---|---|---|
| **CRTO / CRTO-II** | Zero-Point Security | ✅ | Cobalt Strike + EDR evasion focused, excellent value |
| **CRTL** | Zero-Point Security | ✅ | Advanced (LDAP+ADCS+SQL relays etc.) |
| **OSEP** | OffSec | ✅ | Evasion-heavy, AV bypasses |
| **CRTP** | Altered Security | ✅ | AD-focused practical |
| **CRTE** | Altered Security | ✅ | Enterprise-AD red team practical |
| **GPEN / GXPN** | SANS | ⚠️ | Knowledge-based, expensive |
| **CCRTM** | CREST | ✅ | UK CREST equivalent |
| **CRT-RT** | CREST | ✅ | TIBER-aligned UK regulated framework |

## Real campaigns to study

- **APT29's SolarWinds intrusion (Sunburst, 2020)** — supply chain, golden SAML, mailbox access
- **Lapsus$ (2022)** — social engineering helpdesks, Okta MFA bypass, source code theft from Nvidia/Microsoft/Samsung
- **3CX double supply chain (2023)** — DPRK Lazarus
- **MOVEit campaign (Cl0p, 2023)** — mass exploitation, e-crime
- **Volt Typhoon (PRC, 2023–24)** — living-off-the-land in US critical infrastructure
- **Scattered Spider (UNC3944) MGM/Caesars (2023)** — helpdesk SE, ESXi ransomware deploy

[The DFIR Report](https://thedfirreport.com/) publishes detailed real-incident writeups quarterly. Read every one — these are your model for what good (and bad) operators look like in detection logs.

## Interview questions

1. *"Difference between a pentest and a red team engagement?"*
2. *"How do you choose a C2 framework for a 6-month engagement?"*
3. *"Describe AMSI bypass at the high level."*
4. *"You've got a low-priv user on a domain workstation. Walk me through to DA, prioritizing OPSEC."*
5. *"What's a BOF and why does it matter?"*
6. *"How does ADCS ESC1 work?"*
7. *"What's the diamond model? When do you use it?"*

## Recommended reading

- *Operator Handbook: Red Team + OSINT + Blue Team* (Whitehouse) — desk reference
- *Red Team Field Manual (RTFM)* (Clark) — pocket reference, Windows command cheat sheet
- *The Hacker Playbook 3* (Kim)
- *Operating with EmpireC2 / EvasionLabs* — modern blogs trump old books here
- [SpecterOps blog](https://posts.specterops.io/) — IppSec-tier writeups on AD and red team tradecraft
- [MDSec blog](https://www.mdsec.co.uk/insights/research-blog/)
- [Outflank blog](https://www.outflank.nl/blog/)
- [Sektor7 institute](https://institute.sektor7.net/) — paid courses, malware dev focused

---

[← Phase 4](../04-specializations/index.md)  ·  [Blue Team →](blue-team.md)
