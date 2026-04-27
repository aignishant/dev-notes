# 10 · Active Recon & Network Mapping

> *Active recon means traffic to the target. Once you start, the clock
> is ticking — the target's logs are recording you. Make every packet count.*

After Module 9 you have an asset inventory built without sending a packet.
Now we turn that inventory into a **service map**: which IPs respond on
which ports, what versions are running, what known vulnerabilities exist.

Active recon is a balance: **breadth then depth**. First a fast wide scan
to understand the surface area, then targeted version detection on
interesting hits, then vuln correlation on identified versions. Skipping
straight to deep nmap on every IP wastes hours.

---

## 10.1 Scanning at scale: nmap vs masscan vs zmap

| Tool | Speed | Accuracy | Use when |
|------|-------|----------|----------|
| **nmap** | ~1k ports/sec safely | High; great service detection | Up to /24 in reasonable time; service+OS detection |
| **masscan** | 10M+ pkts/sec | Fast SYN, no version detect | /16, /8, internet-wide first pass |
| **zmap** | Similar to masscan | Single-port at a time | Internet-wide research scans |
| **rustscan** | Wraps nmap | Fast port discovery → nmap detail | "Modern nmap" feel |
| **naabu** (ProjectDiscovery) | Fast SYN | Easy to chain | Pipelines |

**Pattern that works on real engagements:**

```
masscan → ports.json
   ↓
svc_enum.py → versions.json   (concurrent banner-grab + nmap -sV per host)
   ↓
vuln_correlator.py → findings.json   (CPE → CVE)
   ↓
report_generator.py → report.md
```

This is exactly what `recon_pipeline.py` does for you in Module 12.

---

## 10.2 Port-scan techniques (review from Part 2)

| Scan | nmap flag | Sends | Identifies |
|------|-----------|-------|------------|
| TCP connect | `-sT` | full handshake | open/closed (always works, loud) |
| TCP SYN ("half-open") | `-sS` | SYN | open/closed/filtered (fast, default) |
| UDP | `-sU` | UDP probe | open|filtered/closed (slow) |
| ACK | `-sA` | ACK | filtered vs unfiltered (firewall mapping) |
| FIN/NULL/Xmas | `-sF/-sN/-sX` | RFC-violating | closed (some legacy filters bypass) |
| Idle/Zombie | `-sI` | uses third-party host | source-anonymous scan |

For internal pentests, default to `-sS -sV -O --top-ports 1000 -T4`. For
internet-facing surface, do `masscan -p1-65535 --rate 50000` for breadth,
then `nmap -sVC -p<discovered>` for depth.

---

## 10.3 Service version detection

**Banner grab** is the cheapest method but covers only services that
greet on connection (SSH, FTP, SMTP). For everything else, you need
**probe-based** version detection:

- nmap's `nmap-service-probes` file has thousands of probe→regex pairs.
- `nmap -sV` sends probes in order of likelihood until a match.
- `--version-intensity 9` is exhaustive (slow but thorough).

Our `svc_enum.py` does a focused alternative: per port, send the
canonical probe (HTTP `GET / HTTP/1.0`, MSSQL pre-login, MySQL handshake,
Redis `INFO`), parse the response, extract version. Faster than full
`-sV` because we skip probes that obviously don't apply to a port.

### TLS service detection

For TLS-wrapped services, the cert itself is high-value:

- **CN / SAN** entries reveal hostnames the server expects to serve.
- **Issuer** reveals the organization's PKI vendor.
- **Validity dates** reveal patch / rotation cadence.
- **Public key parameters** reveal weak keys (small RSA, shared primes).

`openssl s_client -connect host:443 -showcerts` is the manual one-liner;
we automate this in the toolkit.

---

## 10.4 OS fingerprinting

Two flavors:

- **Active fingerprinting** (`nmap -O`): sends crafted packets, observes
  response idiosyncrasies (TCP options ordering, ICMP behavior, ISN
  generation). High accuracy, easily detected.
- **Passive fingerprinting** (`p0f`-style): observes existing traffic,
  identifies OS from initial TTL, TCP window size, options ordering.
  Silent.

Defaults for initial TTL:

| OS | Initial TTL |
|----|-------------|
| Linux / macOS / BSD | 64 |
| Windows | 128 |
| Cisco / network gear | 255 |

A packet arriving with TTL=62 traveled 2 hops from an OS that set 64 —
i.e. Linux. Our `os_fingerprint.py` toolkit module uses TTL + TCP options
to score candidates.

---

## 10.5 Vulnerability correlation

You've identified `nginx 1.18.0`. Is it vulnerable? You need the
**CPE** (Common Platform Enumeration), then look it up against the
**NVD** (National Vulnerability Database) JSON feed.

CPE format: `cpe:2.3:a:nginx:nginx:1.18.0:*:*:*:*:*:*:*`

Workflow:

1. Banner / version → CPE string (regex + lookup table).
2. CPE → list of CVEs from NVD JSON.
3. CVE → CVSS score, exploit availability, public PoC links.
4. Filter to CVSS ≥ 7 with public PoC and rank.

Our `vuln_correlator.py` ships with a small embedded CPE→CVE map for
common services so the toolkit works offline. For real engagements, point
it at a downloaded NVD JSON feed (`nvd.nist.gov/feeds/json/cve/1.1/`).

!!! note "ExploitDB and CISA KEV"
    Two extra signal sources: **ExploitDB** for public PoCs (often
    pre-CVE), and **CISA's Known Exploited Vulnerabilities** catalog for
    "what attackers are actively using right now." Cross-reference both
    against your version inventory.

---

## 10.6 Stealth, evasion, rate-limiting

Active recon is detectable. To minimize signal:

- **`-T2` or `-T1`** in nmap (slows scan, fewer simultaneous probes).
- **Source IP rotation** — if you have multiple cloud egress IPs.
- **Decoys** — `nmap -D RND:10` mixes your scan with 10 fake sources.
- **Fragmentation** — `-f` or `-ff` (defeats some old IDSes).
- **Custom timing options** — `--max-rate`, `--scan-delay`.
- **DNS resolution off** — `-n` skips reverse-DNS, saves time and noise.
- **No ICMP** — `-Pn` skips host-discovery ping (some networks block ICMP).

Modern IDS/EDR will still catch you. The goal is making detection
**after the fact**, when you have your inventory and are ready for
exploitation.

---

## 10.7 Industry scenarios

### Cloud — finding the misconfigured S3/Azure blob

Subdomain enumeration (Module 11) yields `data-uat.example.com`. Active
scan reveals it's a CNAME to `data-uat.s3.amazonaws.com`. `curl https://data-uat.s3.amazonaws.com/?list-type=2` returns a public bucket listing.

### Financial — finding the legacy admin port

`masscan -p0-65535 --rate 10000` against the bank's egress range
discovers an exposed admin interface on TCP/9090 — a Jenkins instance
behind no auth. Routine for unmaintained DR/BCP infrastructure.

### Government — old Citrix front-end

`svc_enum.py` identifies Citrix Netscaler. Version regex matches
`NS12.1`. `vuln_correlator` flags CVE-2019-19781 (path traversal RCE).
Single CVE-aware version finding → one of the most-exploited CVEs of the
last 5 years.

### Healthcare — DICOM port discovery

DICOM servers listen on TCP/104 by default. `masscan -p104,11112,2762,2761`
against the hospital's allocated range finds 6 DICOM endpoints. Half are
behind segmentation; half are not. The unsegmented ones become Module 8
deep-protocol attacks.

---

## 10.8 Detection / blue-team angle

Active scans show up in:

- **Firewall logs** as bursts of denied SYNs.
- **EDR network telemetry** as unusual outbound connections.
- **NetFlow** as low-volume connections to many destinations.
- **IDS signatures** for nmap defaults (e.g. specific TCP options ordering).

Defender priorities:

- **Egress filtering** — most internal hosts shouldn't be initiating arbitrary outbound TCP.
- **Honeyports** — listening services on improbable ports that immediately alert on connection.
- **Suricata/Zeek `notice.log`** for scan-detection scripts.
- **Anomaly baselines** — connection counts per source per minute.

Sigma rule sketch:

```yaml
title: Mass port scan from internal host
detection:
  selection:
    src_ip|in: $internal_subnets
    distinct_count_dst_port: '> 100 in 60s'
  condition: selection
level: high
```

---

## 10.9 Toolbelt

| Tool | Use |
|------|-----|
| `nmap` | Service + OS detection; standard reference |
| `masscan` | Wide-net port scanning |
| `zmap` | Single-port internet-wide |
| `rustscan` | Modern fast wrapper |
| `naabu` | Fast TCP connect scan, good for chains |
| `nuclei` | Template-driven vuln scanning (we cover this in Part 4) |
| `httpx` | Mass HTTP probing |
| `tlsx` | Mass TLS probing |
| `Shodan / Censys` | Pre-indexed (passive but covers active surface) |

---

## 10.10 Scripts for this module

In `scripts/part-03/10-active-recon/` and `redshift-toolkit/redshift_toolkit/scan/`:

1. **`masscan_wrapper.py`** *(toolkit)* — drives `masscan` with sane
   defaults, parses `-oJ` output into toolkit JSON schema.
2. **`svc_enum.py`** *(toolkit)* — concurrent service version probe
   (HTTP, SSH, FTP, SMTP, MSSQL, MySQL, Redis, MongoDB).
3. **`os_fingerprint.py`** *(toolkit)* — OS guess from observed TTL +
   TCP options + banner heuristics.
4. **`vuln_correlator.py`** *(toolkit)* — service version → CPE → CVE
   match with severity filtering. Ships with embedded data for offline
   use; can read NVD JSON feed.
5. **`tls_inspector.py`** *(toolkit)* — TLS cert extraction and
   issuer/CN/SAN/expiry/key-strength reporting.

---

## 10.11 Lab exercises

1. `masscan_wrapper.py` against your home lab `/24`, then feed the
   results to `svc_enum.py`. Compare timing to `nmap -sV` against the
   same range.
2. Set up a deliberately old nginx (`nginx:1.14.0-alpine` Docker image)
   in your lab. Run `svc_enum.py` followed by `vuln_correlator.py`.
   Expected: at least one critical CVE flagged.
3. Boot a Linux VM and a Windows VM. Run `os_fingerprint.py` against
   both based on a single SYN handshake. Verify TTL inference.
4. Run `tls_inspector.py` against `https://example.com`. Save the JSON
   output, then run again a week later — diff the issuer and validity
   to see what you can detect about CA/cert lifecycle.

---

## 10.12 Further reading

- **Fyodor, *Nmap Network Scanning*** — written by the author, free
  online, encyclopedic.
- **`masscan` README and the original whitepaper** by Robert Graham.
- **NIST SP 800-115** — *Technical Guide to Information Security Testing*.
- **MITRE ATT&CK Discovery TA0007** — active discovery techniques.
- **NVD JSON Feed format docs** — `nvd.nist.gov/developers`.

---

→ Next: [Module 11 · DNS & Subdomain Enumeration](11-dns-subdomains.md).
