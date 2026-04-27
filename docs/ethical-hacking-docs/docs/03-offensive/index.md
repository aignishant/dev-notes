# 💥 Phase 3 — Offensive Security

> The OSCP track. This is what most people picture when they hear "ethical hacking" — gaining initial access, escalating privileges, pivoting through networks, owning Active Directory, and writing it all up.

Every technique here is taught in PEN-200 (OSCP), PEN-300 (OSEP), HTB CPTS, and EC-Council CEH. Every technique pairs with detection and defense, because you can't be a good red teamer without thinking like a blue teamer.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 3.1 | Web Application Security — OWASP Top 10 | A01–A10 with hands-on labs |
| 3.2 | SQL Injection, Command Injection, SSRF, XXE | Deep dives on the heavy hitters |
| 3.3 | Authentication & Session Attacks | Brute, credential stuffing, session fixation, JWT, OAuth |
| 3.4 | Linux System Hacking | All major privesc paths |
| 3.5 | Windows System Hacking | All major privesc paths |
| 3.6 | Active Directory Attack Path | Kerberoasting, AS-REP, ACL abuse, ADCS, BloodHound |
| 3.7 | Wireless Attacks | WPA2/WPA3, evil twin, PMKID, enterprise auth |
| 3.8 | Mobile Application Security | Android & iOS app pentesting basics |
| 3.9 | Network Pivoting | Proxychains, sshuttle, chisel, ligolo-ng, port forwarding |

## What you'll be able to do at the end

- Test any web application against OWASP Top 10 systematically
- Escalate privileges on Linux and Windows reliably
- Compromise an Active Directory forest from a low-priv user via 5+ different techniques
- Pivot through multi-tier networks
- Write professional pentest reports with reproducible findings
- Pass eJPT comfortably and approach OSCP / CPTS

## Tools you'll learn

Burp Suite Pro, OWASP ZAP, sqlmap, nuclei, ffuf, dalfox, Arjun, Metasploit, msfvenom, hydra, hashcat, john, BloodHound + SharpHound, Kerbrute, CrackMapExec/NetExec, Impacket, Mimikatz, Rubeus, Certipy, Responder, ntlmrelayx, aircrack-ng, hcxdumptool, MobSF, Frida, objection, chisel, ligolo-ng, sshuttle, proxychains.

## Python scripts you'll build

1. **`web_directory_bruter.py`** — production-quality directory bruteforce with rate limiting + respect for robots.
2. **`param_miner.py`** — parameter discovery with reflection / response-diff detection.
3. **`xss_finder.py`** — context-aware reflected XSS detector.
4. **`sql_blind_oracle.py`** — boolean / time-based blind SQLi extractor.
5. **`linux_enum.py`** — Linux privesc enumeration in pure Python.
6. **`windows_enum.py`** — Windows enumeration via WinRM/WMI.
7. **`kerberoast_helper.py`** — convenience wrapper around Impacket's GetUserSPNs.
8. **`ad_recon.py`** — read-only AD recon via LDAP3.

## Estimated time

- Full-time: 8–10 weeks
- Part-time: 16–20 weeks

## Prerequisites

✅ Phases 1 & 2.

---

!!! tip "Stage 2/3 of this curriculum"
    Web AppSec ships in Stage 2; system hacking, AD, wireless, and mobile in Stage 3.

[← Phase 2](../02-recon/index.md)  ·  [Phase 4 →](../04-specializations/index.md)
