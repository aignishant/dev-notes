# 📡 Network Scanning & Enumeration

> nmap is to security what `grep` is to Unix — you'll use it every day for the rest of your career. This chapter is the level of nmap fluency expected at OSCP and beyond, plus the modern fast scanners that complement it.

---

## 1. The Scanner Ecosystem

| Tool | Strength | Weakness |
|---|---|---|
| **nmap** | Most accurate, NSE scripts, service version DB | Slower at scale |
| **masscan** | Scans the entire IPv4 internet in minutes | No service detection |
| **rustscan** | Fast frontend → pipes to nmap | Just a wrapper |
| **naabu** (ProjectDiscovery) | Modern, async, clean output | Less precise than nmap |
| **zmap** | Research-grade IPv4 sweeps | Single-port, raw |
| **unicornscan** | Stateless | Largely abandoned |

Real-world workflow: **fast tool to find open ports, nmap to identify services.**

```bash
# Step 1: masscan finds open ports across many hosts
sudo masscan -p1-65535 10.0.0.0/24 --rate 10000 -oG masscan.gnmap

# Step 2: feed those ports into nmap for deep service detection
awk '/Host:/{ip=$2}/Ports:/{ports=$0; gsub(/.*Ports: /,"",ports); print ip" "ports}' masscan.gnmap \
  | while read host ports; do
      ports=$(echo $ports | tr ',' '\n' | awk -F'/' '{print $1}' | paste -sd,)
      nmap -sV -sC -Pn -p $ports $host -oN nmap_$host.txt
    done
```

We ship `scripts/scanning/masscan_to_nmap.py` that automates this pipeline.

---

## 2. nmap Deep Dive

### 2.1 Scan types

| Flag | Name | Notes |
|---|---|---|
| `-sS` | TCP SYN scan | Default for root; "half-open"; fast and stealthy-ish |
| `-sT` | TCP connect scan | Full handshake; needed when not root |
| `-sU` | UDP scan | Slow (need root); essential for SNMP/DNS/SIP |
| `-sA` | ACK scan | Maps firewall rules — open vs filtered |
| `-sN`, `-sF`, `-sX` | NULL/FIN/Xmas | Quirky flag combos to fingerprint stacks |
| `-sI` | Idle/zombie scan | Use a third host's IP-ID counter; legendary stealth |
| `-sY` | SCTP INIT | For telecom networks (SS7, Diameter) |

```bash
sudo nmap -sS -p- 10.0.0.5                 # all 65535 TCP ports, SYN scan
sudo nmap -sU --top-ports 100 10.0.0.5     # 100 most common UDP
sudo nmap -sS -sU -p T:1-1024,U:53,123,161 10.0.0.5  # mix
```

### 2.2 Host discovery

```bash
nmap -sn -PE 10.0.0.0/24            # ICMP echo
nmap -sn -PS22,80,443 10.0.0.0/24   # TCP SYN ping
nmap -sn -PA22,80,443 10.0.0.0/24   # TCP ACK ping (gets through stateless filters)
nmap -sn -PU53,161 10.0.0.0/24      # UDP ping
nmap -Pn 10.0.0.5                   # SKIP discovery — assume host is up
```

`-Pn` is your friend when targets drop ICMP. Without it, nmap refuses to scan a host that "looks down".

### 2.3 Timing and rate

```bash
-T0  paranoid    # 5 minutes between probes — for evasion
-T1  sneaky      # 15s
-T2  polite      # 0.4s; avoid breaking fragile networks
-T3  normal      # default
-T4  aggressive  # what you'll use 95% of the time
-T5  insane      # only on a LAN; you'll lose accuracy
```

For better control:

```bash
--min-rate 1000 --max-rate 5000     # packets per second
--max-retries 2
--host-timeout 60s
```

### 2.4 Service & version detection

```bash
nmap -sV -p 22,80,443 10.0.0.5                # versions
nmap -sV --version-intensity 9 10.0.0.5       # send ALL probes
nmap -A 10.0.0.5                              # -sV -sC -O --traceroute
nmap -O 10.0.0.5                              # OS fingerprint (needs open + closed port)
```

`-A` is the kitchen sink — fine for labs, **noisy** in real engagements.

### 2.5 NSE — the Nmap Scripting Engine

NSE turns nmap into a vulnerability scanner. Categories:

| Category | Use |
|---|---|
| `safe` | Won't crash services; default with `-sC` |
| `default` | Run with `-sC` |
| `discovery` | Active info gathering |
| `version` | Helps `-sV` |
| `auth` | Bypass / brute-force authentication |
| `brute` | Aggressive credential brute-force |
| `vuln` | CVE checks |
| `exploit` | Active exploitation |
| `intrusive` | May crash, alert, or violate ROE |
| `dos` | Denial of service |
| `malware` | Detect backdoors/rootkits |

```bash
nmap -sC 10.0.0.5                      # default + safe scripts
nmap --script vuln 10.0.0.5            # all vuln scripts
nmap --script "smb-vuln-*" 10.0.0.5    # all SMB vulns
nmap --script http-enum --script-args http-enum.basepath='/' -p 80 10.0.0.5
nmap --script-help "smb-vuln-*"        # docs for each
```

Custom NSE scripts live in `/usr/share/nmap/scripts/`. Reading a few teaches you the engine.

!!! danger "intrusive / exploit / dos"
    **Never** run these without explicit ROE permission. `smb-vuln-ms17-010` has been documented to crash unpatched targets.

### 2.6 Output formats

```bash
nmap -sV 10.0.0.5 \
  -oN normal.txt \    # human-readable
  -oX results.xml \   # XML — parse with Python
  -oG grep.gnmap \    # greppable (legacy, but pipe-friendly)
  -oA all             # all three at once with prefix `all`
```

We ship `scripts/scanning/nmap_xml_parser.py` to turn nmap XML into structured JSON for SIEM ingest.

### 2.7 Real-world scan recipes

```bash
# Fast top-1000 + version
sudo nmap -sS -sV --top-ports 1000 -T4 -oA quick 10.0.0.5

# All TCP ports, with banner grab and default scripts
sudo nmap -sS -sV -sC -p- --min-rate 2000 -oA full 10.0.0.5

# UDP top-100 (UDP is slow; never -p-)
sudo nmap -sU --top-ports 100 -T4 -oA udp 10.0.0.5

# Vuln scan
sudo nmap -sV --script vuln -p 22,80,443,445,3389 10.0.0.5 -oA vuln

# Subnet sweep + service detection in two steps (much faster than -A across /24)
sudo nmap -sn -PE -PS22,80,443 10.0.0.0/24 -oG live.gnmap
awk '/Up$/{print $2}' live.gnmap > alive.txt
sudo nmap -sS -sV -iL alive.txt --top-ports 1000 -oA svc
```

---

## 3. masscan — Internet-Scale Speed

Stateless, single-threaded, custom TCP/IP stack. Can saturate a 10 Gbps link.

```bash
sudo masscan 10.0.0.0/16 -p1-65535 --rate 100000 -oG out.gnmap
sudo masscan 0.0.0.0/0 -p443 --rate 1000000 --excludefile no-scan.txt
```

**Always use `--excludefile`** with at least RFC 1918, link-local, multicast, US Department of Defense ranges, and any provider's published "do-not-scan" list.

masscan finds open ports; **you still need nmap or curl/openssl to know what's running**.

---

## 4. naabu and rustscan — modern frontends

```bash
# naabu — async, clean, integrates with httpx/nuclei
naabu -host target.com -p - -rate 5000 -nmap-cli 'nmap -sV -sC'

# rustscan — fastest port discovery, pipes to nmap
rustscan -a 10.0.0.5 --ulimit 5000 -- -A
```

Both are convenience layers on top of "find ports fast → hand to nmap".

---

## 5. Banner Grabbing & Service Identification

Sometimes the version string is the entire vulnerability:

```bash
# Manual banner grabs
nc -nv 10.0.0.5 22                 # SSH banner
echo "" | openssl s_client -connect 10.0.0.5:443 -servername target.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
curl -I https://10.0.0.5            # HTTP server header

# Telnet to anything
telnet 10.0.0.5 25                 # SMTP banner

# Whatweb / wappalyzer for HTTP stack
whatweb https://target.com
```

Common banner-version → vuln pivots:

| Banner | Pivot |
|---|---|
| `OpenSSH 7.2p2` | CVE-2016-0777 (roaming), 2018 user-enum |
| `vsftpd 2.3.4` | Backdoor (notorious) |
| `Apache 2.4.49` | CVE-2021-41773 (path traversal) |
| `Tomcat 9.0.0.M1-9.0.0.30` | Ghostcat (CVE-2020-1938) |
| `Microsoft-IIS/7.5` + WebDAV | Multiple privesc |
| `Microsoft-HTTPAPI/2.0` on 5985 | WinRM exposed |

Banner-version is the cheapest way to find low-hanging vulnerabilities.

---

## 6. Pivot from Ports → Service Enumeration

Each open port is a chapter of its own. The next chapter, **Service Enumeration**, covers SMB, LDAP, SNMP, NFS, SMTP, FTP, RDP, MSSQL, Redis, and more in depth. For now, the rule of thumb:

1. nmap finds the port + service + version.
2. Look up CVEs for that exact version.
3. Run protocol-specific enumeration (`enum4linux-ng`, `smbclient`, `ldapsearch`, `snmpwalk`, etc.).
4. Document credentials, share names, user lists, share contents — all of it.

Recon never really *ends*; it deepens until you have your foothold.

---

## 7. Defensive View — Spotting a Scan in Logs

| Signal | Where to look | Detection logic |
|---|---|---|
| TCP SYN flood from one src | Firewall logs / Suricata | High `SYN` rate, low `SYN-ACK` |
| nmap `-sV` probes | Web access logs | Many odd User-Agents, crafted payloads to weird paths |
| OS fingerprint | Honeypot | Mix of TCP flag combinations a normal client would never send |
| UDP scan | Auth-DNS / NTP servers | Spike in malformed UDP requests |
| NSE `vuln` scripts | App logs | Specific exploit signatures (e.g., `' OR 1=1--`) |

Sample Suricata rule snippet:

```text
alert tcp any any -> $HOME_NET any (msg:"Possible nmap SYN scan"; \
    flags:S; threshold:type both, track by_src, count 20, seconds 60; \
    sid:1000001;)
```

In practice, modern detection uses NetFlow / Zeek + behavioral baselines, not just signatures.

---

## 8. Hands-On Lab

In your isolated lab (Phase 1 setup), against your **Metasploitable3** or **HackTheBox starting-point** machine:

1. `sudo nmap -sn 192.168.56.0/24` — find live hosts.
2. `sudo nmap -sS -p- --min-rate 2000 <victim>` — all TCP ports.
3. `sudo nmap -sV -sC -p<comma-list> <victim>` — version + default scripts.
4. `sudo nmap -sU --top-ports 50 <victim>` — UDP top 50.
5. `sudo nmap --script vuln -p<comma-list> <victim>` — vuln scripts.
6. `sudo masscan -p1-65535 <victim> --rate 5000` — compare speed and accuracy.
7. Parse the XML output with `nmap_xml_parser.py` → JSON.
8. Pick one open port; do manual banner-grabbing with `nc` / `openssl s_client`.
9. Look up the version on [exploit-db.com](https://www.exploit-db.com/).
10. Write a one-page recon report.

Time: 2–3 hours. Repeat weekly with different targets.

---

## 9. Interview Questions

- Difference between `-sS` and `-sT`? When does each apply?
- What does `-Pn` do and when do you need it?
- How does an `-sA` ACK scan distinguish stateful vs stateless firewalls?
- Why is UDP scanning slow, and how does nmap mitigate it?
- What does `--max-rate 1000` achieve? Why might you use it on a production target?
- Walk through a masscan → nmap pipeline.
- How would you detect an nmap scan from a defender's perspective?

---

## 10. Tools Quick Reference

| Job | Tool |
|---|---|
| Single host | `nmap` |
| Many hosts, fast | `masscan`, `naabu`, `rustscan`, `zmap` |
| Service detection | `nmap -sV`, `whatweb`, `wappalyzer` |
| OS fingerprint | `nmap -O`, `p0f` |
| NSE scripts | `nmap --script` |
| Output parsing | XML → custom; `nmap-parse-output`; our `nmap_xml_parser.py` |
| Continuous monitoring | `Censys Search`, `Shodan Monitor`, `RunZero` |

---

## 11. Further Reading

- *Nmap Network Scanning*, Gordon "Fyodor" Lyon — the official book; free online.
- nmap's `man` page; read it twice.
- `man masscan` — also surprisingly good.
- ProjectDiscovery's docs on naabu / nuclei.
- Robert Graham's masscan blog posts on internet-wide research.

---

[← Passive & Active Recon](passive-active-recon.md) · [Service Enumeration →](enumeration.md)
