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

## 🗂️ Stage 3 Scripts

### `web/jwt_attack.py`
JWT vulnerability checker and exploit helper. Detects `alg:none`, weak HMAC (with built-in bruter), `kid` injection, key confusion (RS256→HS256), and crafts forgeries given the public key.
```bash
python web/jwt_attack.py "$TOKEN"
python web/jwt_attack.py "$TOKEN" --brute --wordlist rockyou.txt
python web/jwt_attack.py "$TOKEN" --rsa-pubkey pub.pem --forge '{"role":"admin"}'
python web/jwt_attack.py "$TOKEN" --json
```

### `system/linux_enum.py`
Pure-Python Linux privesc enumerator. Walks 12 categories: SUID/SGID, sudo, capabilities, cron, PATH, world-writable files, kernel/distro, credentials in files, container indicators, NFS, services, and PATH hijack candidates.
```bash
python system/linux_enum.py --summary
python system/linux_enum.py --json /tmp/enum.json
python system/linux_enum.py --skip-files       # quick run
```

### `system/windows_enum.py`
Windows enumeration over WinRM (uses `pywinrm`). Looks for AlwaysInstallElevated, unquoted service paths, weak service ACLs, `cmdkey` saved creds, scheduled task ACLs, and AutoLogon registry creds.
```bash
python system/windows_enum.py -t 10.0.0.5 -u alice -p 'Summer2026'
python system/windows_enum.py -t dc.corp.local -u alice -p 'Summer2026' --ssl --json out.json
```

### `ad/kerberoast_helper.py`
Wrapper around Impacket's `GetUserSPNs.py` that produces clean JSON, scores each ticket by triage priority (account name patterns, group memberships, encryption type), and writes hashcat-ready files.
```bash
python ad/kerberoast_helper.py -d corp.local -u alice -p 'Summer2026' --dc 10.0.0.5
python ad/kerberoast_helper.py -d corp.local -u alice -p 'Summer2026' --dc dc.corp.local --hashcat tickets.hash --json roast.json
```

### `ad/bloodhound_analyzer.py`
Parses BloodHound JSON exports (zip, directory, or single file) and finds the shortest privesc paths via BFS — no Neo4j or GUI needed. Reports paths to Domain Admins, Tier-0, and arbitrary targets.
```bash
python ad/bloodhound_analyzer.py 20260427_bloodhound.zip
python ad/bloodhound_analyzer.py ./bh-output/ --start 'ALICE@CORP.LOCAL' --target 'DOMAIN ADMINS@CORP.LOCAL'
python ad/bloodhound_analyzer.py ./bh-output/ --top-paths 10 --json paths.json
```

### `wireless/handshake_analyzer.py`
Analyzes WPA handshake captures (pcap/pcapng). Parses EAPOL frames, validates 4-way handshakes, extracts PMKID from association frames, and emits hashcat-22000 mode lines (modern replacement for `cap2hccapx`).
```bash
python wireless/handshake_analyzer.py capture.pcap
python wireless/handshake_analyzer.py capture.pcap --hashcat 22000.txt
python wireless/handshake_analyzer.py capture.pcap --bssid AA:BB:CC:DD:EE:FF --json
```

### `mobile/apk_static_analyzer.py`
Single-file APK static analyzer. Pure-Python AXML parser (no Android SDK), extracts manifest, permissions, exported components, signing certificates, and scans for hardcoded secrets and risky configurations.
```bash
python mobile/apk_static_analyzer.py target.apk
python mobile/apk_static_analyzer.py target.apk --json out.json
python mobile/apk_static_analyzer.py target.apk --secrets-only
```

### `cloud/aws_iam_analyzer.py`
AWS IAM privilege-escalation analyzer using the Rhino Security catalog (~22 known privesc paths: `iam:CreateAccessKey`, `iam:PassRole + lambda:CreateFunction`, `sts:AssumeRole` chains, etc.). Works live (boto3) or offline against a directory of policy JSON.
```bash
python cloud/aws_iam_analyzer.py --live --profile audit
python cloud/aws_iam_analyzer.py --policy-dir ./aws_policies/ --json findings.json
cat policy.json | python cloud/aws_iam_analyzer.py --stdin
```

### `cloud/s3_bucket_audit.py`
S3 bucket public-exposure auditor. Checks Public Access Block, bucket policy, ACLs, default encryption, versioning, server-access logging, and bucket ownership controls. Flags buckets that are publicly listable, writable, or unencrypted.
```bash
python cloud/s3_bucket_audit.py --all
python cloud/s3_bucket_audit.py --bucket my-bucket --bucket other-bucket --json audit.json
python cloud/s3_bucket_audit.py --all --profile audit --severity-min HIGH
```

### `malware/pe_analyzer.py`
PE (Windows executable) static analyzer using `pefile`. Reports sections with entropy (packer signal), imports categorized by suspicion (anti-debug, injection, network, crypto, registry), exports, resources, TLS callbacks, and runs a packer-detection heuristic.
```bash
python malware/pe_analyzer.py sample.exe
python malware/pe_analyzer.py sample.exe --json sample.json
python malware/pe_analyzer.py sample.exe --strings --min-string-len 8
```

---

## 🗂️ Stage 4 Scripts

### `exploit-dev/rop_gadget_finder.py`
Lightweight Capstone-based ROP gadget finder for x86_64 ELF binaries. Scans every executable segment, walks back from each `ret` (and `syscall` / `int 0x80`), validates instruction chains, deduplicates, and prints (or JSON-emits) gadgets sorted by length. Useful for chaining BOF exploits when full pwntools is not available.
```bash
python exploit-dev/rop_gadget_finder.py /bin/ls --max-len 5
python exploit-dev/rop_gadget_finder.py ./vuln --filter "pop r[a-z0-9]+; ret" --json gadgets.json
```

### `exploit-dev/pattern_create.py`
De Bruijn cyclic pattern generator and offset finder — a pure-Python equivalent of Metasploit's `pattern_create.rb` / `pattern_offset.rb`. Use it to generate a unique pattern, crash the target, then feed the EIP/RIP value back to find the exact buffer offset.
```bash
python exploit-dev/pattern_create.py --create 200
python exploit-dev/pattern_create.py --offset 0x6361616a
python exploit-dev/pattern_create.py --offset Aa9A   # accepts ASCII or hex
```

### `iot/firmware_extractor.py`
`binwalk` wrapper that runs signature-based extraction on a firmware blob, then computes Shannon entropy in sliding windows to locate compressed/encrypted regions and classifies extracted contents (squashfs, ext, jffs2, U-Boot images, etc.). Saves an entropy histogram alongside the extracted root.
```bash
python iot/firmware_extractor.py router.bin --out ./extracted
python iot/firmware_extractor.py firmware.img --window 4096 --json report.json
```

### `ai-sec/prompt_injection_fuzzer.py`
Async LLM red-team fuzzer compatible with any OpenAI-style `/v1/chat/completions` endpoint (OpenAI, Azure OpenAI, vLLM, llama.cpp server, Ollama, etc.). Ships a built-in 10-probe corpus across categories — instruction override, system-prompt leak, jailbreak, indirect injection, encoding smuggling, canary leak, excessive agency — and scores responses with simple heuristics.
```bash
python ai-sec/prompt_injection_fuzzer.py --base-url http://localhost:11434/v1 --model llama3
python ai-sec/prompt_injection_fuzzer.py --base-url https://api.openai.com/v1 --model gpt-4o --probes-file custom.json --json results.json
```

### `appsec/sast_secrets_scan.py`
Regex + Shannon-entropy hybrid secret scanner for source trees. Detects AWS access keys, GitHub PATs (classic + fine-grained), Slack/Stripe/Twilio tokens, JWTs, Postgres/Mongo connection strings, private keys, and high-entropy strings adjacent to assignment-like syntax. Honors `.gitignore`-style excludes.
```bash
python appsec/sast_secrets_scan.py ./repo
python appsec/sast_secrets_scan.py ./repo --json findings.json --exclude tests/ --min-entropy 4.0
```

### `malware/yara_scanner.py`
Recursive YARA scanner with a `ThreadPoolExecutor` worker pool, JSON output, and per-file metadata (size, sha256, mtime). Compiles a directory of `.yar` rules once and reuses; tolerates both new (`StringMatch`) and legacy tuple match shapes; handles binary blobs gracefully.
```bash
python malware/yara_scanner.py --rules ./rules /malware/samples
python malware/yara_scanner.py --rules ./rules ./quarantine --workers 8 --json hits.json
```

---

## 🗂️ Stage 5 Scripts

### `defense/dns_exfil_detector.py`
DNS exfiltration / DGA detector. Reads Zeek `dns.log` (TSV or JSON), live PCAPs (via Scapy), or stdin queries; flags subdomains by max-label length, Shannon entropy, and per-source-IP query rate (queries/min). Built for SOC pipelines — emits one JSON object per alert for SIEM ingest.
```bash
python defense/dns_exfil_detector.py --zeek dns.log --json alerts.jsonl
sudo python defense/dns_exfil_detector.py --pcap /var/log/capture.pcap
tshark -r capture.pcap -T fields -e dns.qry.name | python defense/dns_exfil_detector.py --stdin
```

### `defense/sigma_to_splunk.py`
Bulk-converts Sigma rule directories to Splunk SPL. Prefers the official `sigma-cli` if installed; falls back to a pure-Python translator that handles the most common Sigma constructs (`logsource`, `selection`, `condition`, `1 of`, `all of`, modifiers like `contains`, `startswith`, `endswith`, `re`).
```bash
python defense/sigma_to_splunk.py ./sigma/rules/windows --out ./spl/
python defense/sigma_to_splunk.py rule.yml --pure-python --print
```

### `forensics/evtx_triager.py`
Triages Windows EVTX directories using `python-evtx`. Extracts and highlights notable Event IDs across Security (4624/4625/4672/4688/4720/4732/4768/4769), Sysmon (1/3/7/11/13), PowerShell (4103/4104), Task Scheduler (106/200), and WinRM channels. Produces a tabular triage view plus a SOC-style timeline.
```bash
python forensics/evtx_triager.py /mnt/evidence/Windows/System32/winevt/Logs --since 2026-04-01 --json triage.json
python forensics/evtx_triager.py Security.evtx --top-eids
```

### `threat-intel/stix_query.py`
Pure-stdlib STIX 2.1 bundle parser. Extracts indicators (md5/sha1/sha256, ipv4/ipv6, domains, URLs, emails, filenames, registry keys, mutexes), threat actors, and ATT&CK technique references — no external library required. Useful when piping bundles from MISP, OpenCTI, or vendor feeds into downstream pipelines.
```bash
python threat-intel/stix_query.py bundle.json --type indicator --pattern-types ipv4-addr,domain-name
python threat-intel/stix_query.py bundle.json --techniques --json
cat bundle.json | python threat-intel/stix_query.py - --actors
```

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
