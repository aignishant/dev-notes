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

## 🗂️ Stage 1 Scripts (shipped now)

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

## 🛣️ Coming in Later Stages

| Script | Stage | Purpose |
|---|---|---|
| `recon/subdomain_enum.py` | 2 | Multi-source passive subdomain enum (CT + DNS + APIs) |
| `recon/tech_fingerprint.py` | 2 | Web stack fingerprinting from headers + body |
| `web/web_directory_bruter.py` | 2 | Polite directory bruteforce with rate limiting |
| `web/param_miner.py` | 2 | Hidden parameter discovery |
| `automation/recon_orchestrator.py` | 2 | Chain recon tools into a single pipeline |
| `crypto/wordlist_mutator.py` | 2 | Rule-based wordlist mutation for password audits |
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
