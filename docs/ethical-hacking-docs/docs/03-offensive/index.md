# 💥 Phase 3 — Offensive Security

> The OSCP track. This is what most people picture when they hear "ethical hacking" — gaining initial access, escalating privileges, pivoting through networks, owning Active Directory, and writing it all up.

Every technique here is taught in PEN-200 (OSCP), PEN-300 (OSEP), HTB CPTS, and EC-Council CEH. Every technique pairs with detection and defense, because you can't be a good red teamer without thinking like a blue teamer.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 3.1 | [Web Methodology & OWASP Top 10](web-methodology.md) | Burp setup, WSTG methodology, A01–A10 tour |
| 3.2 | [Injection Attacks](web-injection.md) | SQLi, NoSQLi, command injection, LDAP, SSTI, prototype pollution |
| 3.3 | [XSS, CSRF & SSRF](web-xss-csrf-ssrf.md) | Three highest-impact web bug classes |
| 3.4 | [Authentication & Session Attacks](web-auth-session.md) | Brute force, credential stuffing, session fixation, JWT, OAuth, SAML |
| 3.5 | [Linux Privilege Escalation](linux-privesc.md) | SUID, sudo, capabilities, cron, kernel exploits, container escapes |
| 3.6 | [Windows Privilege Escalation](windows-privesc.md) | Services, AlwaysInstallElevated, unquoted paths, Potatoes, UAC bypass |
| 3.7 | [Active Directory Attacks](active-directory.md) | Kerberoasting, AS-REP, ACL abuse, ADCS, BloodHound, DCSync, Golden Ticket |
| 3.8 | [Wireless Attacks](wireless.md) | WPA2/WPA3, PMKID, evil twin, enterprise (eaphammer), KRACK |
| 3.9 | [Mobile Application Security](mobile.md) | Android (jadx, Frida, objection), iOS, OWASP Mobile Top 10 |
| 3.10 | [Pivoting & Lateral Movement](pivoting.md) | SSH tunnels, sshuttle, chisel, ligolo-ng, Meterpreter routes |

## What you'll be able to do at the end

- Test any web application against OWASP Top 10 systematically
- Escalate privileges on Linux and Windows reliably
- Compromise an Active Directory forest from a low-priv user via 5+ different techniques
- Pivot through multi-tier networks
- Write professional pentest reports with reproducible findings
- Pass eJPT comfortably and approach OSCP / CPTS

## Tools you'll learn

Burp Suite Pro, OWASP ZAP, sqlmap, nuclei, ffuf, dalfox, Arjun, Metasploit, msfvenom, hydra, hashcat, john, BloodHound + SharpHound, Kerbrute, CrackMapExec/NetExec, Impacket, Mimikatz, Rubeus, Certipy, Responder, ntlmrelayx, aircrack-ng, hcxdumptool, MobSF, Frida, objection, chisel, ligolo-ng, sshuttle, proxychains.

## Python scripts shipped with this phase

**Stage 2:**

1. **`web/dir_bruter.py`** — production-quality directory bruteforce with rate limiting + smart 404 detection.
2. **`web/sqli_detector.py`** — careful SQLi probe-only detector for in-scope engagements.
3. **`web/xss_payload_generator.py`** — context-aware XSS payload mutator (educational).

**Stage 3:**

4. **`web/jwt_attack.py`** — JWT vulnerability checker (alg:none, weak HMAC bruter, kid injection, key confusion, RS256→HS256 forgery).
5. **`system/linux_enum.py`** — pure-Python Linux privesc enumerator (SUID/sudo/caps/cron/PATH/creds/container detection).
6. **`system/windows_enum.py`** — Windows enumeration via WinRM (services, AlwaysInstallElevated, unquoted paths, cmdkey).
7. **`ad/kerberoast_helper.py`** — wrapper around impacket-GetUserSPNs with cleaner JSON output and triage scoring.
8. **`ad/bloodhound_analyzer.py`** — parses BloodHound JSON exports and finds shortest privesc paths via BFS (no GUI needed).
9. **`wireless/handshake_analyzer.py`** — analyzes WPA handshake captures, extracts PMKID, emits hashcat-22000 lines.
10. **`mobile/apk_static_analyzer.py`** — APK static analysis with pure-Python AXML parser (manifest, permissions, exported components, secrets).
11. **`cloud/aws_iam_analyzer.py`** — AWS IAM privesc path analyzer (Rhino Security catalog, ~22 paths, live or offline).
12. **`cloud/s3_bucket_audit.py`** — S3 bucket public-exposure auditor (PAB, policy parser, ACLs, encryption, versioning, logging).

## Estimated time

- Full-time: 8–10 weeks
- Part-time: 16–20 weeks

## Prerequisites

✅ Phases 1 & 2.

---

[← Phase 2](../02-recon/index.md)  ·  [Phase 4 →](../04-specializations/index.md)
