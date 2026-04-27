# 🔍 Phase 2 — Reconnaissance & Assessment

> Before you exploit anything, you map it. Recon is 60% of every real engagement.

This phase teaches you to gather information about a target — passively (no packets sent to them) and actively (scanning, probing) — and then assess the attack surface for vulnerabilities.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 2.1 | OSINT — Open Source Intelligence | Recon without touching the target |
| 2.2 | Passive & Active Reconnaissance | Whois, DNS, subdomain enum, certificate transparency |
| 2.3 | Network Scanning & Enumeration | nmap mastery, masscan, banner grabbing |
| 2.4 | Service Enumeration | SMB, LDAP, SNMP, NFS, SMTP, FTP, RDP |
| 2.5 | Vulnerability Assessment | Nessus, OpenVAS, Nuclei, manual analysis |
| 2.6 | Web Application Recon | Subdomains, virtual hosts, content discovery, JS analysis |

## What you'll be able to do at the end

- Map a target's external attack surface from a domain name alone
- Identify subdomains, IPs, technologies, employees, exposed buckets, leaked credentials
- Run a full nmap scan and interpret every flag
- Discover hidden web content (directories, parameters, subdomains, API endpoints)
- Triage thousands of hosts with Nuclei + custom templates
- Produce a recon report worthy of a real client

## Tools you'll learn

`amass`, `subfinder`, `assetfinder`, `httpx`, `nuclei`, `nmap`, `masscan`, `rustscan`, `naabu`, `theHarvester`, `recon-ng`, `Maltego`, `shodan`, `censys`, `gitleaks`, `trufflehog`, `gobuster`, `ffuf`, `feroxbuster`, `arjun`, `kiterunner`, `gau`, `waybackurls`, `katana`.

## Python scripts you'll build in this phase

1. **`subdomain_enum.py`** — multi-source passive subdomain enumerator (CT logs + DNS + passive APIs).
2. **`virtual_host_finder.py`** — find vhosts on a single IP.
3. **`tech_fingerprint.py`** — fingerprint web stack from headers + body.
4. **`shodan_recon.py`** — automate Shodan queries with caching.
5. **`recon_orchestrator.py`** — chain the above into a single pipeline.

## Estimated time

- Full-time: 2–3 weeks
- Part-time: 4–6 weeks

## Prerequisites

✅ Phase 1 complete. You should be comfortable with networking, Linux, Python.

---

!!! tip "Stage 2 of this curriculum"
    This phase is in the **Stage 2** delivery of the curriculum (full chapters, scripts, and labs). What you have now is the structure and roadmap.

[← Back to Phase 1](../01-foundations/index.md)  ·  [Phase 3 →](../03-offensive/index.md)
