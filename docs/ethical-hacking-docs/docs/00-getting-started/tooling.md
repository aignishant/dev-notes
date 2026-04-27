# 🧰 Tooling

A complete catalog of the tools you will see throughout this curriculum, organized by what they do. **You don't need to install all of them today** — most ship with Kali. Skim once for vocabulary, return to it as a reference.

## How to think about tools

A tool is just a knife. Three traps to avoid:

1. **Tool worship** — knowing only Burp doesn't make you a web security expert.
2. **Tool monoculture** — relying on one tool means you miss what it doesn't see.
3. **Tool skipping** — refusing to learn the standard tools means you will not communicate well with teammates.

Learn each tool **deeply enough** to know when it lies, when it's slow, and when a different tool is better.

## Recon & OSINT

| Tool | Use |
|------|-----|
| `theHarvester` | Email/host harvesting from public sources |
| `recon-ng` | Modular OSINT framework |
| `Maltego` | Graph-based OSINT (community edition free) |
| `SpiderFoot` | Automated OSINT |
| `subfinder`, `assetfinder`, `amass` | Subdomain enumeration |
| `crt.sh` (web) | Certificate transparency search |
| `Shodan` (web/CLI) | Internet device search |
| `Censys` (web) | Like Shodan, alternative dataset |
| `Google dorks` | Advanced search operators |
| `holehe` | Email-to-account enumeration |
| `sherlock` | Username search across sites |
| `OSINT Framework` (web) | Curated OSINT directory |

## Network Discovery & Scanning

| Tool | Use |
|------|-----|
| `nmap` | Port/service/script scanning. The Swiss army knife. |
| `masscan` | Internet-scale port scanner |
| `rustscan` | Fast wrapper that hands off to nmap |
| `naabu` | Fast SYN scanner (ProjectDiscovery) |
| `unicornscan` | High-speed asynchronous scanner |
| `arp-scan`, `netdiscover` | LAN discovery |
| `fping` | Ping sweep |
| `hping3` | Packet crafting & probes |

## Vulnerability Scanners

| Tool | Use |
|------|-----|
| `Nessus` (Essentials free) | Authenticated/unauth vuln scanning |
| `OpenVAS / GVM` | Open-source vuln scanner |
| `Nuclei` | Templated CVE/misconfig scanner |
| `nikto` | Old-school web vuln scanner |
| `wpscan` | WordPress-specific |
| `searchsploit` | Local Exploit-DB search |

## Web Application Testing

| Tool | Use |
|------|-----|
| `Burp Suite` (Community / Pro) | Intercepting proxy, the standard |
| `OWASP ZAP` | Free alternative to Burp |
| `mitmproxy` | Scriptable Python proxy |
| `Caido` | Modern Burp alternative |
| `ffuf` | Fast HTTP fuzzer |
| `feroxbuster`, `gobuster`, `dirsearch` | Directory/file brute force |
| `wfuzz` | Multi-purpose fuzzer |
| `sqlmap` | Automated SQL injection |
| `xsstrike` | XSS detection/exploitation |
| `commix` | Command injection |
| `tplmap` | Template injection |
| `dalfox` | XSS scanner |
| `nuclei` | Templated vuln checks |
| `arjun` | HTTP parameter discovery |
| `paramspider` | Parameter discovery from web archives |
| `httpx` | Fast HTTP probing |
| `katana` | Modern crawler |
| `Postman / Insomnia / Bruno` | API testing GUIs |
| `mitmweb`, `Caido` proxies | Headless intercepting |

## System / Active Directory

| Tool | Use |
|------|-----|
| `Impacket` (Python) | SMB, Kerberos, MSRPC primitives |
| `NetExec` (formerly CrackMapExec) | Lateral-movement & enumeration swiss army |
| `BloodHound` + `SharpHound` / `bloodhound.py` | AD attack-path graph |
| `Rubeus` | Kerberos abuse on Windows |
| `mimikatz` | Credential extraction |
| `LaZagne` | Recover stored creds |
| `evil-winrm` | WinRM shell |
| `kerbrute` | User enumeration / pre-auth attacks |
| `enum4linux-ng` | SMB / RPC enumeration |
| `responder` | LLMNR/NBT-NS poisoning |
| `mitm6` | IPv6 / WPAD MITM for AD |
| `ntlmrelayx` (Impacket) | NTLM relay |
| `PowerView`, `PowerSploit`, `Nishang` | PowerShell offensive scripts |
| `WinPEAS`, `LinPEAS` | Privilege-escalation enumeration |
| `pspy` | Linux process monitoring without root |

## Wireless

| Tool | Use |
|------|-----|
| `aircrack-ng` suite | 802.11 capture, deauth, cracking |
| `wifite2` | Automated wireless attacks |
| `bettercap` | MITM, network attacks |
| `kismet` | Wireless detection / IDS |
| `hcxdumptool` + `hcxtools` | PMKID capture |
| `Reaver`, `Bully` | WPS attacks |
| `Wifiphisher` | Captive-portal phishing |

## Password Cracking

| Tool | Use |
|------|-----|
| `hashcat` | GPU-accelerated cracking, the standard |
| `John the Ripper` | CPU-based, format-rich |
| `hydra` | Online network login brute force |
| `medusa`, `ncrack` | Alt online brute force |
| `crunch`, `cewl`, `cupp` | Wordlist generation |
| `SecLists` | The wordlist collection |
| `RockYou.txt` | Classic password list |

## Reverse Engineering & Malware Analysis

| Tool | Use |
|------|-----|
| `Ghidra` | Free SRE platform from NSA |
| `IDA Free` | Industry standard disassembler |
| `Binary Ninja` | Modern alternative (paid) |
| `radare2 / rizin / cutter` | Open-source RE |
| `x64dbg` | Windows debugger |
| `gdb` + `pwndbg` / `gef` | Linux debugger w/ exploit aids |
| `WinDbg` | Microsoft kernel/user debugger |
| `Frida` | Dynamic instrumentation |
| `objection` | Frida helper for mobile |
| `dnSpy` | .NET debugging/decompiling |
| `JD-GUI`, `procyon` | Java decompilers |
| `apktool`, `jadx` | Android RE |
| `volatility3` | Memory forensics |
| `FLOSS` | Static string deobfuscation |
| `pestudio`, `pefile` | PE file inspection |
| `YARA` | Pattern matching for malware |
| `Cuckoo`, `ANY.RUN`, `Hybrid Analysis` | Sandbox |
| `CAPA` | Capability detection (Mandiant) |

## Exploit Development

| Tool | Use |
|------|-----|
| `pwntools` (Python) | Exploit-dev framework |
| `peda`, `pwndbg`, `gef` | gdb plugins |
| `ROPgadget`, `ropper` | Find ROP gadgets |
| `Immunity Debugger` + `mona.py` | Windows exploit dev |
| `AFL++`, `libFuzzer`, `honggfuzz` | Fuzzers |
| `Z3` | SMT solver for symbolic execution |

## Forensics & DFIR

| Tool | Use |
|------|-----|
| `Autopsy / Sleuth Kit` | Disk forensics |
| `FTK Imager`, `dd`, `dc3dd` | Disk imaging |
| `KAPE` | Triage collection |
| `Velociraptor`, `GRR` | Endpoint investigation at scale |
| `Volatility` | Memory analysis |
| `plaso / log2timeline` | Super-timeline |
| `Wireshark`, `tshark`, `NetworkMiner` | PCAP analysis |
| `Zeek` | Network metadata logging |
| `Suricata`, `Snort` | IDS/IPS |
| `EZ Tools` (Eric Zimmerman) | Win artifact parsing |
| `Sysinternals Suite` | Live Windows triage |
| `Splunk`, `ELK`, `OpenSearch`, `Wazuh` | SIEM |
| `Sigma` | Generic detection rules |

## Cloud Security

| Tool | Use |
|------|-----|
| `Pacu` | AWS exploitation framework |
| `ScoutSuite` | Multi-cloud security audit |
| `Prowler`, `cloudsploit`, `CloudSploit` | AWS/GCP/Azure auditors |
| `AzureHound` | Graph Azure AD |
| `ROADtools` | Azure AD exploitation |
| `kubectl`, `kubescape`, `kube-hunter`, `kube-bench` | Kubernetes |
| `trivy`, `grype` | Container/SBOM scanning |
| `gitleaks`, `trufflehog` | Secret detection |
| `terragoat`, `cdkgoat` | IaC vuln labs |

## Mobile

| Tool | Use |
|------|-----|
| `MobSF` | Mobile static + dynamic analysis |
| `Frida`, `objection` | Runtime hooking |
| `apktool`, `jadx`, `apkleaks` | Android |
| `Drozer` | Android attack surface |
| `Burp / mitmproxy + Frida cert-pinning bypass` | Mobile traffic |
| `class-dump`, `Hopper` (paid) | iOS |

## Privacy / OPSEC

| Tool | Use |
|------|-----|
| `Tor Browser` | Anonymous browsing |
| `Tails` OS | Forensics-resistant boot OS |
| `Whonix` | Tor gateway VMs |
| `Mullvad / ProtonVPN / IVPN` | Reputable VPNs |
| `KeePassXC`, `Bitwarden` (self-host: Vaultwarden) | Password managers |
| `YubiKey` / FIDO2 | Hardware auth keys |
| `signal-cli`, `Signal` | E2EE messaging |

## Reporting & Tracking

| Tool | Use |
|------|-----|
| `Obsidian`, `Notion`, `Joplin` | Note-taking |
| `CherryTree`, `KeepNote` | Pentest engagement notes |
| `Faraday`, `Dradis`, `PwnDoc`, `SysReptor` | Pentest reporting |
| `Markdown + pandoc` | DIY reports |
| `MITRE ATT&CK Navigator` | TTP coverage |
| `DefectDojo` | Vuln management |

## Daily-Driver Suggestions

If you can only learn five tools deeply this month, learn these:

1. **`nmap`** — port/service/script scanning
2. **`Burp Suite`** — web testing
3. **`Wireshark`** — packet analysis
4. **`Impacket` + `NetExec`** — Windows / AD interaction
5. **`Python`** — glue, custom tools, exploitation

Everything else is faster to learn once you know these well.

→ Next: [Legal & Ethics](legal-ethics.md)
