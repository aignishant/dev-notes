# 💥 Phase 3 — Offensive Security

> The OSCP track. This is what most people picture when they hear "ethical hacking" — gaining initial access, escalating privileges, pivoting through networks, owning Active Directory, and writing it all up.

Every technique here is taught in PEN-200 (OSCP), PEN-300 (OSEP), HTB CPTS, and EC-Council CEH. Every technique pairs with detection and defense, because you can't be a good red teamer without thinking like a blue teamer.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 3.1 | [Web Methodology & OWASP Top 10](web-methodology.md) | Burp setup, WSTG methodology, A01–A10 tour |
| 3.2 | [Injection Attacks](web-injection.md) | SQLi, NoSQLi, command injection, LDAP, SSTI, prototype pollution |
| 3.3 | [XSS, CSRF & SSRF](web-xss-csrf-ssrf.md) | Three highest-impact web bug classes |
| 3.4 | Authentication & Session Attacks *(Stage 3)* | Brute, credential stuffing, session fixation, JWT, OAuth, SAML |
| 3.5 | Linux System Hacking *(Stage 3)* | All major privesc paths |
| 3.6 | Windows System Hacking *(Stage 3)* | All major privesc paths |
| 3.7 | Active Directory Attack Path *(Stage 3)* | Kerberoasting, AS-REP, ACL abuse, ADCS, BloodHound |
| 3.8 | Wireless Attacks *(Stage 3)* | WPA2/WPA3, evil twin, PMKID, enterprise auth |
| 3.9 | Mobile Application Security *(Stage 3)* | Android & iOS app pentesting basics |
| 3.10 | Network Pivoting *(Stage 3)* | Proxychains, sshuttle, chisel, ligolo-ng, port forwarding |

## What you'll be able to do at the end

- Test any web application against OWASP Top 10 systematically
- Escalate privileges on Linux and Windows reliably
- Compromise an Active Directory forest from a low-priv user via 5+ different techniques
- Pivot through multi-tier networks
- Write professional pentest reports with reproducible findings
- Pass eJPT comfortably and approach OSCP / CPTS

## Tools you'll learn

Burp Suite Pro, OWASP ZAP, sqlmap, nuclei, ffuf, dalfox, Arjun, Metasploit, msfvenom, hydra, hashcat, john, BloodHound + SharpHound, Kerbrute, CrackMapExec/NetExec, Impacket, Mimikatz, Rubeus, Certipy, Responder, ntlmrelayx, aircrack-ng, hcxdumptool, MobSF, Frida, objection, chisel, ligolo-ng, sshuttle, proxychains.

## Python scripts shipped with this phase (Stage 2)

1. **`web/dir_bruter.py`** — production-quality directory bruteforce with rate limiting + smart 404 detection.
2. **`web/sqli_detector.py`** — careful SQLi probe-only detector for in-scope engagements.
3. **`web/xss_payload_generator.py`** — context-aware XSS payload mutator (educational).

## Estimated time

- Full-time: 8–10 weeks
- Part-time: 16–20 weeks

## Prerequisites

✅ Phases 1 & 2.

---

[← Phase 2](../02-recon/index.md)  ·  [Phase 4 →](../04-specializations/index.md)
