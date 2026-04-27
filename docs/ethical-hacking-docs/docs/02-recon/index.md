# 🔍 Phase 2 — Reconnaissance & Assessment

> Before you exploit anything, you map it. Recon is 60% of every real engagement.

This phase teaches you to gather information about a target — passively (no packets sent to them) and actively (scanning, probing) — and then assess the attack surface for vulnerabilities. You'll come out of this phase able to walk into any engagement and produce a recon report worthy of a senior pen-tester or threat-intel analyst.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 2.1 | [OSINT — Open Source Intelligence](osint.md) | Recon without touching the target |
| 2.2 | [Passive & Active Reconnaissance](passive-active-recon.md) | Whois, DNS, subdomain enum, certificate transparency |
| 2.3 | [Network Scanning & Enumeration](scanning.md) | nmap mastery, masscan, banner grabbing |
| 2.4 | [Service Enumeration](enumeration.md) | SMB, LDAP, SNMP, NFS, SMTP, FTP, RDP, MSSQL, Redis |
| 2.5 | [Vulnerability Assessment](vulnerability-assessment.md) | Nessus, OpenVAS, Nuclei, manual analysis |
| 2.6 | [Web Application Recon](web-recon.md) | Subdomains, virtual hosts, content discovery, JS analysis |

## What you'll be able to do at the end

- Map a target's external attack surface from a domain name alone
- Identify subdomains, IPs, technologies, employees, exposed buckets, leaked credentials
- Run a full nmap scan and interpret every flag
- Discover hidden web content (directories, parameters, subdomains, API endpoints)
- Triage thousands of hosts with Nuclei + custom templates
- Produce a recon report worthy of a real client

## Tools you'll learn

`amass`, `subfinder`, `assetfinder`, `httpx`, `nuclei`, `nmap`, `masscan`, `rustscan`, `naabu`, `theHarvester`, `recon-ng`, `Maltego`, `shodan`, `censys`, `gitleaks`, `trufflehog`, `gobuster`, `ffuf`, `feroxbuster`, `arjun`, `kiterunner`, `gau`, `waybackurls`, `katana`, `nxc` (NetExec), `enum4linux-ng`, `bloodhound.py`, `windapsearch`, `Nessus`, `OpenVAS`.

## Python scripts shipped with this phase

1. **`recon/subdomain_enum.py`** — multi-source passive subdomain orchestrator.
2. **`recon/vhost_finder.py`** — virtual-host discovery with response-diffing.
3. **`recon/tech_fingerprint.py`** — header + favicon + body stack detection.
4. **`recon/google_dorker.py`** — generates targeted Google dork queries.
5. **`recon/wayback_url_extractor.py`** — pull historic URLs from web.archive.org.
6. **`recon/ad_ldap_recon.py`** — read-only AD enumeration via LDAP.
7. **`scanning/nmap_xml_parser.py`** — turn nmap XML into structured JSON.
8. **`scanning/cve_correlator.py`** — banner → CVE intel via NVD.

## Estimated time

- Full-time: 2–3 weeks
- Part-time: 4–6 weeks

## Prerequisites

✅ Phase 1 complete. You should be comfortable with networking, Linux, Python.

---

[← Back to Phase 1](../01-foundations/index.md)  ·  [Phase 3 →](../03-offensive/index.md)
