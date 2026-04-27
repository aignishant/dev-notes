# 🐍 Security Scripts

A growing collection of production-quality Python tools that accompany this curriculum. Every script is **defensive / authorized-use only** and is referenced from the relevant chapter.

## 📦 Install

```bash
pip install -r ../requirements-tools.txt
```

Or just the libs each script needs (each script lists its imports at the top).

## 🔐 Authorization First

These tools are intended for use against:

- Systems you own
- Lab VMs (TryHackMe, HackTheBox, your own Kali + targets)
- Targets you have **written permission** to assess
- Public test targets that explicitly invite testing (e.g., `scanme.nmap.org`)

Running scanners or sniffers against systems you don't own can violate the **CFAA (US)**, the **IT Act 2000 (India)**, and equivalent laws worldwide. **Read [`docs/00-getting-started/legal-ethics.md`](../docs/00-getting-started/legal-ethics.md) before using any of these.**

---

## 🗂️ Stage 1 Scripts

### `scanning/async_port_scanner.py`
Async TCP port scanner with banner grabbing, top-N support, and rich output.
```bash
python scanning/async_port_scanner.py 127.0.0.1 --top 100
python scanning/async_port_scanner.py 192.168.1.10 --ports 1-1024 --concurrency 1000
```

### `recon/arp_spoof_detector.py`
**Defensive.** Sniffs ARP traffic on your LAN and alerts on poisoning attempts (MAC flap, one-MAC-many-IPs, gateway MAC change). Run as root.
```bash
sudo python recon/arp_spoof_detector.py --iface eth0 --json-log /var/log/arp.log
```

### `recon/ct_subdomain_enum.py`
Passive subdomain enumerator using public Certificate Transparency logs (crt.sh). 100% non-intrusive — no traffic to the target.
```bash
python recon/ct_subdomain_enum.py example.com --resolve --json subs.json
```

### `crypto/hash_identifier.py`
Identify the algorithm that produced a hash (MD5, SHA-1/256/512, NTLM, bcrypt, Argon2, JWT, MySQL, Cisco, etc.). Includes hashcat & john format hints.
```bash
python crypto/hash_identifier.py 5f4dcc3b5aa765d61d8327deb882cf99
echo '$2b$12$abcdefghij...'  | python crypto/hash_identifier.py -
```

### `crypto/jwt_analyzer.py`
Decode + audit a JWT. Flags `alg:none`, weak HMAC use, missing `exp`, sensitive claims, algorithm-confusion vectors, and more. Optional signature verification.
```bash
python crypto/jwt_analyzer.py "eyJhbGciOi..."
python crypto/jwt_analyzer.py "$TOKEN" --secret 'your-shared-secret'
python crypto/jwt_analyzer.py "$TOKEN" --jwks https://example.com/.well-known/jwks.json
```

### `defense/failed_ssh_analyzer.py`
Parse `/var/log/auth.log` (or `journalctl`) and produce a SOC-style report on SSH brute-force attempts. Calls out source IPs that had failures **followed by a success** — the highest-priority case for incident response.
```bash
sudo python defense/failed_ssh_analyzer.py
journalctl -u ssh -o short | python defense/failed_ssh_analyzer.py -
```

### `defense/ioc_extractor.py`
Extract IOCs (IPs, domains, URLs, emails, hashes, CVEs, ATT&CK techniques, file paths, BTC/XMR addresses) from any text source. Auto-refangs common defangs (`hxxp`, `[.]`, `[at]`, etc.).
```bash
python defense/ioc_extractor.py threat-report.txt --json iocs.json
cat email.eml | python defense/ioc_extractor.py - --no-private
```

### `web/http_header_auditor.py`
Grade a target on its HTTP security headers, cookie hygiene, and TLS version. Produces a letter grade (A–F) plus per-check findings; emits JSON for SIEM/dashboarding.
```bash
python web/http_header_auditor.py https://example.com
python web/http_header_auditor.py https://example.com --json
```

### `defense/mini_honeypot.py`
Passive multi-port asyncio honeypot. Listens on configurable TCP ports, records the first bytes attackers send, and never replies — useful for catching opportunistic scans and lateral movement on internal networks.
```bash
sudo python defense/mini_honeypot.py --ports 21,22,23,80,443,3389 --log honeypot.jsonl
python defense/mini_honeypot.py --ports 2222,8080  # high ports, no root
```

---

## 🗂️ Stage 2 Scripts

### `recon/subdomain_enum.py`
Multi-source passive subdomain enumerator. Aggregates from crt.sh (CT logs), HackerTarget, AlienVault OTX, URLScan.io, and ProjectDiscovery's chaos (with API key). Optionally resolves and emits JSON.
```bash
python recon/subdomain_enum.py example.com
python recon/subdomain_enum.py example.com --resolve --output subs.json
python recon/subdomain_enum.py example.com --sources crt,otx --quiet
```

### `recon/vhost_finder.py`
Virtual-host discovery via Host-header brute-force, with response-size + content-hash diffing against a baseline so soft-404s are filtered out.
```bash
python recon/vhost_finder.py http://10.0.0.5 -d target.com -w subs.txt
python recon/vhost_finder.py https://target.com -d target.com -w subs.txt --json
```

### `recon/tech_fingerprint.py`
Web technology fingerprinter combining headers, cookies, body markers, and Shodan-compatible favicon hashing.
```bash
python recon/tech_fingerprint.py https://example.com
python recon/tech_fingerprint.py -l urls.txt --json -o results.json
```

### `recon/google_dorker.py`
Generates categorized Google dork queries (and equivalent search-engine URLs) for a target domain. Does **not** auto-search — output is meant for manual review.
```bash
python recon/google_dorker.py example.com
python recon/google_dorker.py example.com --categories secrets,exposed_files
python recon/google_dorker.py example.com --engine bing --json
```

### `recon/wayback_url_extractor.py`
Harvests historic URLs for a domain from the Wayback Machine's CDX API. Optionally filters by extension or "interesting" heuristics (paths containing `admin`, `api`, `.git`, etc.).
```bash
python recon/wayback_url_extractor.py example.com --subs --from 2020 -o urls.txt
python recon/wayback_url_extractor.py example.com --interesting-only
```

### `recon/ad_ldap_recon.py`
**Read-only** Active Directory enumeration via LDAP. Pulls users, groups, computers, GPOs, trusts, password policy, Kerberoastable accounts, ASREPRoastable accounts, and high-priv group memberships into a single JSON report.
```bash
python recon/ad_ldap_recon.py -d corp.local -u alice -p 'Summer2026' -s 10.0.0.5
python recon/ad_ldap_recon.py -d corp.local -u alice -p 'Summer2026' -s dc.corp.local --ldaps -o report.json
```

### `scanning/nmap_xml_parser.py`
Parses nmap XML (`-oX`) output into structured JSON for SIEM ingest. Includes a human-readable summary mode and a `--diff` mode that compares two scans (newly-open ports, version changes, lost hosts).
```bash
python scanning/nmap_xml_parser.py scan.xml --summary
python scanning/nmap_xml_parser.py scan.xml --pretty -o scan.json
python scanning/nmap_xml_parser.py today.xml --diff yesterday.xml
```

### `scanning/cve_correlator.py`
Cross-references service banners (from nmap XML, the `nmap_xml_parser.py` JSON output, or manual `product:version` strings) against the NVD CVE database, enriching results with CISA KEV ("known exploited") status and EPSS exploit-prediction scores.
```bash
python scanning/cve_correlator.py --nmap-xml scan.xml --kev-only
python scanning/cve_correlator.py --banner "Apache httpd:2.4.49" --banner "OpenSSH:8.2p1"
python scanning/cve_correlator.py --nmap-json parsed.json -o cves.json
```

### `web/dir_bruter.py`
Polite, rate-limited directory & file bruteforcer with auto-calibrated baseline 404 detection. Designed for engagements where ROE forbids hammering targets.
```bash
python web/dir_bruter.py https://target.com -w wordlists/dirs.txt
python web/dir_bruter.py https://target.com -w big.txt -e .php,.bak,.zip --rate 10
```

### `web/sqli_detector.py`
Careful, probe-only SQL Injection detector. Sends a small fixed set of detection probes per parameter and reports candidates for manual analysis (with sqlmap or hand). Detects error-based, boolean-blind, and time-blind signals.
```bash
python web/sqli_detector.py "https://target.com/page?id=1&q=test"
python web/sqli_detector.py "https://target.com/page" --post "id=1&q=test"
python web/sqli_detector.py "https://target.com/page?id=1" -H "Cookie: session=abc"
```

### `web/xss_payload_generator.py`
Context-aware XSS payload generator. Given the *context* in which user input is reflected (HTML body, attribute, JS string, URL, …) and an optional set of filtered characters, generates candidate payloads. Educational — does not make HTTP requests.
```bash
python web/xss_payload_generator.py --context html_body
python web/xss_payload_generator.py --context html_attr_double --filter "<,script"
python web/xss_payload_generator.py --context js_string --variants
python web/xss_payload_generator.py --list-contexts
```

---

## 🛣️ Coming in Later Stages

| Script | Stage | Purpose |
|---|---|---|
| `automation/recon_orchestrator.py` | 3 | Chain recon tools into a single pipeline |
| `web/param_miner.py` | 3 | Hidden parameter discovery |
| `crypto/wordlist_mutator.py` | 3 | Rule-based wordlist mutation for password audits |
| `system/linux_enum.py` | 3 | Linux privesc enumeration in pure Python |
| `system/windows_enum.py` | 3 | Windows enumeration via WinRM/WMI |
| `ad/kerberoast_helper.py` | 3 | Convenience wrapper around Impacket's GetUserSPNs |
| `defense/dns_exfil_detector.py` | 4 | Flag long, high-entropy DNS subdomains |
| `defense/sigma_to_splunk.py` | 4 | Convert Sigma rule directories to SPL |
| `forensics/evtx_triager.py` | 4 | Fast EVTX triage for logon/process/service events |
| `malware-analysis/yara_scanner.py` | 4 | Recursive YARA scanner with rich JSON output |
| `automation/report_generator.py` | 5 | Markdown → PDF pentest report generator |

---

## 🧰 Code Quality Standards (apply to every script)

- Python 3.11+
- Type hints throughout
- `argparse` (or Typer) for CLI
- `rich` for terminal output where it adds value
- Dataclasses for structured results
- Async (`asyncio`) for IO-bound work
- Always include a clear authorization warning in the docstring
- Emit JSON output option for SIEM/SOAR integration
- Graceful Ctrl-C handling
- No silent `except` blocks — log/handle each case
