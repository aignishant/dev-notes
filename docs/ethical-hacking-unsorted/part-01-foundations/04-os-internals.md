# 04 · OS Internals for Hackers

!!! abstract "Goal of this module"
    Reach the minimum bar of Linux and Windows internals knowledge required to **attack and defend** them effectively. You will leave this module able to read `/proc`, `procfs`, the Windows registry, and ACLs as fluently as you read Python dicts.

This module is **dual-column** — every concept is covered on both Linux and Windows so you see the parallels and differences.

---

## 4.1 Why OS internals matter to offense

Every attack, reduced far enough, is a question of what the operating system will let the current user do. Privilege escalation is misconfigured ACLs. Persistence is a scheduled task. Lateral movement is credential material reused across hosts. Evasion is understanding what the kernel logs vs what it doesn't.

If you only know "I run this tool and it gives me output," you're a script-runner. If you know **why** the tool works — what call it makes, what the OS permits, why the defender sees (or doesn't see) it — you're an operator.

---

## 4.2 Linux fundamentals

### 4.2.1 The `/proc` filesystem — where the kernel lives

`/proc` is a virtual filesystem that exposes kernel data structures as files. Every attacker-useful piece of live system state is here.

Key paths:

| Path | What it tells you |
|------|------------------|
| `/proc/cpuinfo` | CPU architecture, flags (AES-NI, VT-x, etc.) |
| `/proc/version` | Kernel version string — feed into `searchsploit` for known exploits |
| `/proc/cmdline` | Kernel boot cmdline (sometimes leaks secrets) |
| `/proc/meminfo` | Memory layout and sizes |
| `/proc/net/tcp` | Active TCP sockets (listeners, established) — often reveals internal services |
| `/proc/net/route` | Routing table |
| `/proc/mounts` | All mounts — look for NFS/CIFS shares, encrypted containers |
| `/proc/self` | Symlink to current process's dir |
| `/proc/<pid>/cmdline` | Command-line of each process — **frequently leaks passwords** |
| `/proc/<pid>/environ` | Environment variables — DB passwords, API keys |
| `/proc/<pid>/maps` | Memory map of a process (useful for RE / injection) |
| `/proc/<pid>/fd/` | Open file descriptors of each process |
| `/proc/<pid>/status` | UID, GID, capabilities |

**Offensive one-liner:** `cat /proc/*/cmdline 2>/dev/null | tr '\0' ' ' | grep -Ei 'pass|token|key|secret'` — often finds creds on the command line in sloppy deployments.

### 4.2.2 Permissions — the triad, plus the sticky bits that matter

Traditional Unix permissions are the `rwx` triad for user/group/others. But these are attacker goldmines:

- **SUID (`s` on user exec bit)** — binary runs as its owner, not the caller. If the owner is root and the binary does anything exploitable, it's privesc. Classic: `find / -perm -4000 2>/dev/null`.
- **SGID (`s` on group exec bit)** — similar, group-level.
- **Sticky bit on directories (`t` on others)** — only the owner can delete files (used on `/tmp`).
- **Linux capabilities** — fine-grained privileges on binaries: `getcap -r / 2>/dev/null`. Look for `cap_setuid`, `cap_dac_read_search`, `cap_sys_admin` on unusual binaries.
- **Extended ACLs** (`getfacl`) — add user/group-specific permissions on top of the triad. Frequently overlooked in audits.

### 4.2.3 Users, groups, and sudo

- `/etc/passwd` — users (readable by all).
- `/etc/shadow` — password hashes (root only; readable = privesc).
- `/etc/group` — group memberships.
- `/etc/sudoers` + `/etc/sudoers.d/*` — sudo rules. `sudo -l` as the current user is always step 1 post-exploit. Look for `NOPASSWD`, wildcards, env-variable preservation.
- `~/.ssh/authorized_keys` — SSH public keys authorized to log in as that user.

### 4.2.4 Services and scheduling

- **`systemd`** — the dominant init system. Service units live in `/etc/systemd/system/`, `/lib/systemd/system/`. User units in `~/.config/systemd/user/`.
- **Cron** — `/etc/crontab`, `/etc/cron.d/`, `/etc/cron.{hourly,daily,weekly}`, `/var/spool/cron/` (per-user). Classic privesc vector: a root-owned cron job running a world-writable script.
- **`at`, `anacron`** — occasional scheduling.

### 4.2.5 Networking state

- `ss -tlnp` — listening TCP sockets + process.
- `ip a`, `ip r` — interfaces and routes.
- `iptables -L -n -v`, `nft list ruleset` — firewall rules.
- `/etc/resolv.conf` — DNS.
- `/etc/hosts` — sometimes overrides DNS in interesting ways.

### 4.2.6 Logs

- `/var/log/auth.log`, `/var/log/secure` — authentication.
- `/var/log/syslog`, `/var/log/messages` — general.
- `journalctl` — systemd unified.
- `last`, `lastb`, `w` — login history.

Attacker angle: what the defender's SIEM is ingesting. Defender angle: what logs to forward to Wazuh/Elastic.

---

## 4.3 Windows fundamentals

### 4.3.1 The registry — Windows' configuration brain

The Windows Registry is a hierarchical key-value database. Attackers and defenders both live in it.

Root hives:

| Hive | Purpose |
|------|---------|
| `HKEY_LOCAL_MACHINE` (HKLM) | System-wide settings |
| `HKEY_CURRENT_USER` (HKCU) | Current user settings |
| `HKEY_USERS` (HKU) | All users' profiles |
| `HKEY_CLASSES_ROOT` (HKCR) | File associations (derived) |
| `HKEY_CURRENT_CONFIG` (HKCC) | Current hardware profile (small, rarely useful) |

Attacker-famous keys:

| Key | Why attackers love it |
|-----|----------------------|
| `HKLM\SYSTEM\CurrentControlSet\Services` | Every service; persistence & privesc |
| `HKLM\Software\Microsoft\Windows\CurrentVersion\Run` | Autostart (persistence) |
| `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | Per-user autostart |
| `HKLM\SYSTEM\CurrentControlSet\Control\Lsa` | LSA config; Kerberos/cached-creds tweaks |
| `HKLM\SAM` | Account DB (hash storage) — protected but dumpable with SYSTEM access |
| `HKLM\SECURITY` | Security policies, LSA secrets |
| `HKLM\Software\Policies` | Group Policy-applied settings |
| `HKCU\Software\Microsoft\Terminal Server Client\Servers` | Saved RDP creds |

Tools: `reg.exe`, `regedit.exe`, PowerShell `Get-ItemProperty`. From Linux, use `impacket-reg` or `secretsdump.py`.

### 4.3.2 Services

Windows services are long-running processes managed by Service Control Manager.

- Enumerate: `sc query`, `Get-Service`, `wmic service list brief`.
- Service binary path → if the path is unquoted and contains spaces, **unquoted service path vulnerability** (local privesc).
- Service permissions → `icacls` the binary; if a low-priv user can write the binary, replace and restart for privesc.
- Tool: **`PowerUp`** (PowerShell) automates finding these.

### 4.3.3 Scheduled Tasks

- `schtasks /query /fo LIST /v` (verbose).
- `Get-ScheduledTask` (PowerShell).
- Located in `\Windows\System32\Tasks\` as XML.
- Running as `SYSTEM` is the common privesc flavor.

### 4.3.4 WMI (Windows Management Instrumentation)

WMI is the richest enumeration and lateral-movement surface on Windows. Every ATT&CK adversary uses it.

Examples:
```powershell
# Processes
Get-WmiObject Win32_Process

# Services
Get-WmiObject Win32_Service

# Logical disks
Get-WmiObject Win32_LogicalDisk

# Remote: execute a command on another machine
Invoke-WmiMethod -Class Win32_Process -ComputerName TARGET -Name Create -ArgumentList "cmd /c whoami > C:\out.txt"
```

From Linux, use `impacket-wmiexec` or `impacket-wmiquery`.

### 4.3.5 Tokens and privileges

Windows authentication is token-based. When you log in, LSA hands you a token containing your SID, group SIDs, and privileges.

Privileges to scan for on compromised Windows hosts (`whoami /priv`):

| Privilege | Impact |
|-----------|--------|
| `SeImpersonatePrivilege` | Impersonate clients → **Potato family** privesc to SYSTEM |
| `SeAssignPrimaryTokenPrivilege` | Similar |
| `SeBackupPrivilege` | Read any file (hash dumping via VSS) |
| `SeRestorePrivilege` | Write any file (persistence / privesc) |
| `SeDebugPrivilege` | Attach to any process → LSASS dump → mimikatz |
| `SeTakeOwnershipPrivilege` | Claim objects → privesc |
| `SeLoadDriverPrivilege` | Load kernel driver → kernel exec (BYOVD) |
| `SeTcbPrivilege` | "Act as part of the OS" — effectively SYSTEM |

Seeing `SeImpersonatePrivilege` enabled is like finding a front door with no lock. Learn the Potato family (RottenPotato, JuicyPotato, PrintSpoofer, GodPotato) for Part 6.

### 4.3.6 ACLs on Windows

Windows uses **Discretionary Access Control Lists (DACLs)** composed of **Access Control Entries (ACEs)**.

- `icacls <path>` — file/dir ACLs.
- `Get-Acl` (PowerShell).
- Registry ACLs exist too: `Get-Acl "HKLM:\SYSTEM\..."`.

Each ACE grants or denies a specific right (ReadData, WriteData, ChangePermissions, TakeOwnership, etc.) to a specific trustee.

**Misconfigured ACLs are the #1 source of Windows privilege escalation.** Look for: `BUILTIN\Users: (W)`, `Authenticated Users: (M)`, `Everyone: (F)` on service binaries, service registry keys, scheduled-task XML files.

### 4.3.7 Active Directory essentials

(Full AD coverage is Part 7 Module 29; these are the basics for Module 04.)

- Forest → tree → domain.
- Users, groups, computers, OUs live in AD.
- Kerberos handles authentication via tickets (TGT → TGS).
- LDAP handles directory queries.
- `nltest /dsgetdc:redshift.local` — find DC.
- `net user /domain`, `net group "Domain Admins" /domain` — enumerate users/groups.
- From Linux: `ldapsearch`, `bloodhound.py`, `impacket-GetADUsers`.

### 4.3.8 Logs and ETW

- **Event Log** — `Get-WinEvent` / `wevtutil`. Key logs: Security, System, Application, Microsoft-Windows-PowerShell/Operational, Sysmon/Operational.
- **ETW (Event Tracing for Windows)** — high-volume telemetry, the substrate EDRs tap.
- **AMSI (Anti-Malware Scan Interface)** — hooks scripts and macros before execution for AV scanning.

As an attacker, you need to know what's logged and what isn't. As a SOAR engineer, this is your happy place.

---

## 4.4 Parallels at a glance

| Concept | Linux | Windows |
|---------|-------|---------|
| Privileged user | root (uid 0) | SYSTEM / Administrator |
| Persistence — user autostart | `~/.bashrc`, systemd user units | `HKCU\...\Run`, Startup folder |
| Persistence — system-wide | cron, `/etc/systemd/system/` | Services, scheduled tasks, `HKLM\...\Run` |
| Credentials at rest | `/etc/shadow` | SAM, NTDS.dit, LSA secrets |
| Credentials in memory | SSH agent, keyring | LSASS process |
| Remote exec | SSH, `ssh-agent`, `screen` | RDP, WinRM, SMB/PsExec, WMI |
| Permissions | rwx + ACLs + capabilities | DACLs (ACEs) + privileges |
| Package mgmt | apt, dnf, pacman | winget, Chocolatey, MSI |
| Logs | `/var/log/`, journalctl | Event Log, ETW |

---

## 4.5 Script · `linux_enum.py`

Local enumeration script for a Linux target (you've landed a shell — now what?). Produces a structured JSON + text report covering: kernel, distro, users, sudo, SUID, capabilities, world-writable files, cron jobs, interesting env vars, listening sockets.

**Location:** `scripts/part-01/04-os-internals/linux_enum.py`

## 4.6 Script · `windows_enum_wmi.py`

Runs WMI queries against a remote Windows target using `impacket-wmiquery`-style calls. From a Linux attacker, enumerate services, processes, logical disks, scheduled tasks.

**Location:** `scripts/part-01/04-os-internals/windows_enum_wmi.py`

!!! note
    This script requires `impacket` and valid domain or local credentials. Run only against hosts in your lab.

## 4.7 Real-world scenario — reading a target

You land on a Linux web server as `www-data` via an RCE. Your first 60 seconds:

```bash
# 1. Who am I? What can I do?
id; sudo -l 2>/dev/null

# 2. What OS / kernel?
uname -a; cat /etc/os-release

# 3. Anything juicy in the environment?
env | grep -iE 'pass|token|key'

# 4. Who else is on the box?
who; w; last | head -5

# 5. What's exposed?
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null

# 6. Any sudo without password? Sudoers entries for me?
sudo -l 2>/dev/null

# 7. Any SUID I can leverage? (always check GTFOBins for results)
find / -perm -4000 -type f 2>/dev/null

# 8. Any scheduled tasks I can hijack?
cat /etc/crontab; ls -la /etc/cron.*
```

Each of those commands is mechanized in `linux_enum.py`. Run it. Read the output. Train your eye to spot the anomaly.

Industry variants:

- **Financial services Linux host:** look for `/opt/trading/`, environment variables for market-data feeds (they sometimes contain credentials for order APIs).
- **Healthcare Linux host:** look for NFS mounts of EHR data, `hl7-listener` daemons, DICOM directories.
- **Cloud-hosted Linux:** check IMDS (instance metadata service) for IAM credentials before anything else: `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/`.

## 4.8 Exercises

1. **Run `linux_enum.py`** on `web01` from your lab. Review every section of the output — explain (out loud or in writing) what each finding means.
2. **Run `windows_enum_wmi.py`** against WS01 using a low-privilege domain account.
3. **On DC01, audit** all Domain Admins, all members of "Backup Operators," all accounts with `PasswordNeverExpires`. Produce a CSV.
4. **Write a short blog post** (even private) titled "How to read a freshly popped Linux box in 90 seconds." Ties enumeration into your learning loop.
5. **Find one misconfiguration on each OS:** plant a SUID binary on your Linux target and an unquoted service path on your Windows target. Have your enumeration scripts find them.

## 4.9 Further reading

- **GTFOBins** — <https://gtfobins.github.io/> (SUID / sudo escape book)
- **LOLBAS Project** — <https://lolbas-project.github.io/> (living-off-the-land Windows binaries)
- **HackTricks** — <https://book.hacktricks.xyz/> (bible for both platforms)
- **PayloadsAllTheThings** — <https://github.com/swisskyrepo/PayloadsAllTheThings>
- **Windows Internals** — Russinovich, Solomon, Ionescu (Books 1 & 2; sit on your desk forever)
- **The Linux Programming Interface** — Michael Kerrisk (for deeper Linux internals)
- **Microsoft Sysinternals suite** — process explorer, procmon, autoruns, sigcheck
- **PEASS-ng (linpeas/winpeas)** — the enumeration scripts the whole community leans on

!!! success "Exit criteria for Module 04"
    - You can narrate the difference between an ACL and a DACL.
    - You can read a Windows `whoami /priv` output and immediately flag dangerous privileges.
    - You can explain what `/proc/<pid>/environ` leaks and why it matters.
    - You know at least three places Linux and Windows keep credentials that defenders miss.
