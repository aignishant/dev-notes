# 🐧 Linux

The attacker's primary OS, the defender's primary server, the hobbyist's daily driver. If you can't operate Linux at the command line, you cannot do this job.

## 1. The Filesystem Hierarchy

The **FHS** (Filesystem Hierarchy Standard) layout you'll see on every distro:

| Path | Purpose | Why it matters |
|------|---------|----------------|
| `/` | Root | Top of everything |
| `/bin` `/sbin` `/usr/bin` `/usr/sbin` | Binaries | Where commands live |
| `/lib` `/lib64` `/usr/lib` | Shared libs | Hijack target |
| `/etc` | System config | `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/cron*`, `/etc/ssh/` |
| `/home/<user>` | User homes | SSH keys, dotfiles, history |
| `/root` | Root's home | Always check first if you have access |
| `/var` | Variable data | `/var/log/`, `/var/spool/`, `/var/www/` |
| `/var/log` | Logs | Auth events, syslog, web access |
| `/tmp` `/var/tmp` `/dev/shm` | Temporary | Often world-writable; payload staging |
| `/opt` | 3rd-party | App-specific installs |
| `/proc` `/sys` | Kernel pseudo-FS | `/proc/<pid>/`, `/proc/net/tcp`, `/proc/version` |
| `/dev` | Devices | `/dev/null`, `/dev/random`, `/dev/sda` |
| `/run` | Runtime state | Sockets, PIDs, cred caches |
| `/boot` | Kernel + bootloader | GRUB lives here |
| `/mnt` `/media` | Mount points | External drives |

Knowing where things live makes you fast. Drill it.

## 2. Permissions

The Unix permission model — **read / write / execute** for **owner / group / other**:

```bash
$ ls -l /etc/passwd /etc/shadow
-rw-r--r-- 1 root root  3128 Apr 22 10:00 /etc/passwd
-rw-r----- 1 root shadow 1893 Apr 22 10:00 /etc/shadow
```

Numeric (octal) form:

| Number | Permissions |
|--------|-------------|
| 7 | rwx |
| 6 | rw- |
| 5 | r-x |
| 4 | r-- |
| 3 | -wx |
| 2 | -w- |
| 1 | --x |
| 0 | --- |

`chmod 750` = `rwxr-x---` (owner full, group read/exec, other none).

### Special bits — SUID, SGID, sticky

| Symbol | What |
|--------|------|
| **SUID** (`u+s`, e.g. `4755`) | Run as **file owner** (often root). Massive privesc target. |
| **SGID** (`g+s`, e.g. `2755`) | Run as file group. On a directory, new files inherit the group. |
| **Sticky** (`+t`, e.g. `1777`) | Only owner can delete. `/tmp` has this. |

Find SUID binaries:

```bash
find / -perm -4000 -type f 2>/dev/null
```

Cross-reference with **GTFOBins** (<https://gtfobins.github.io>) for known SUID-abuse paths. This is one of the **single most common privilege escalation vectors**.

### Linux capabilities

Modern alternative to SUID — fine-grained super-powers a binary can hold:

```bash
getcap -r / 2>/dev/null
# /usr/bin/ping = cap_net_raw+ep
```

Dangerous capabilities to look for: `cap_setuid`, `cap_dac_read_search`, `cap_sys_ptrace`, `cap_sys_admin`. GTFOBins covers each.

### ACLs

Posix ACLs add per-user / per-group entries on top of the classic mode:

```bash
getfacl /path/to/file
setfacl -m u:alice:rwx /path/to/file
```

You'll see ACLs on hardened filesystems. They can grant access that `ls -l` won't show.

## 3. Users, Groups, PAM, sudo

User database files:

| File | Contents |
|------|----------|
| `/etc/passwd` | Username, UID, GID, home, shell — world-readable |
| `/etc/shadow` | Username, password hash, age policy — root-only |
| `/etc/group` | Group names + members |
| `/etc/gshadow` | Group password hashes |
| `/etc/sudoers` (+ `/etc/sudoers.d/`) | Who can sudo what |

**Password hash format** in `/etc/shadow`:

```
alice:$6$saltsalt$hashhashhash...:19000:0:99999:7:::
        ^id   ^salt    ^hash
```

| ID | Algorithm |
|-----|-----------|
| `$1$` | MD5 (broken) |
| `$5$` | SHA-256 |
| `$6$` | SHA-512 |
| `$y$` | yescrypt (modern) |
| `$argon2id$` | Argon2id (best) |

Crack with:

```bash
john --format=sha512crypt /tmp/shadow_to_crack
hashcat -m 1800 hash.txt rockyou.txt    # SHA-512 crypt
hashcat -m 16500 jwt.txt rockyou.txt     # JWT HS256
```

### sudo abuse

Look for sudo rights that allow command execution:

```bash
sudo -l           # what can I run?
# (root) NOPASSWD: /usr/bin/find          ← cookbook GTFObin
# (root) NOPASSWD: /usr/bin/python3       ← obvious
# (root) ALL: ALL                         ← jackpot
```

GTFOBins again is your reference. Common: `find`, `vim`, `less`, `man`, `awk`, `nmap`, `python`, `tar`, `zip`, `tee`.

### PAM

Pluggable Authentication Modules — pipeline of modules that run on login. Files in `/etc/pam.d/` (sshd, sudo, login). Misconfigured PAM has produced famous CVEs. As an attacker, look for `nullok` and unusual modules. As a defender, harden it (set strong `pam_faillock`, `pam_unix sha512 rounds=`, etc.).

## 4. Process Management

```bash
ps aux                # all processes
ps -ef                # alt format
ps auxf               # tree
top / htop            # interactive
pstree -p             # tree with PIDs
pgrep nginx           # find by name
pkill -HUP nginx      # signal by name
kill -9 1234          # force kill PID
nice / renice         # priority
```

### systemd

Modern init / service manager on most distros:

```bash
systemctl status sshd
systemctl start nginx
systemctl enable nginx        # start at boot
systemctl list-units --type=service
systemctl list-timers
journalctl -u sshd -f          # follow service logs
journalctl --since "1 hour ago"
journalctl _UID=1000           # everything by UID 1000
```

A **service unit** is a text file in `/etc/systemd/system/` or `/lib/systemd/system/`. As an attacker, look for unit files writable by your user (privesc); as a defender, write hardened units (`NoNewPrivileges=true`, `ProtectSystem=strict`).

### cron / timers

Both are scheduled-task systems.

```bash
crontab -l            # current user
crontab -e
ls -la /etc/cron.*    # system-wide
cat /etc/crontab
systemctl list-timers # systemd alternative
```

Writable cron jobs run as the listed user → privesc. **Always** check `/etc/cron*` and per-user crontabs.

## 5. Networking on Linux

```bash
ip a                       # addresses
ip r                       # routes
ip n                       # neighbors (ARP/NDP)
ip link set eth0 up
ip addr add 10.0.0.5/24 dev eth0
ss -tulnp                  # listening sockets, with PIDs

# Old equivalents (deprecated but everywhere)
ifconfig
route -n
netstat -tulnp

# Firewalls
iptables -L -n -v          # legacy
nft list ruleset           # nftables
ufw status                 # Ubuntu's frontend
firewall-cmd --list-all    # RHEL/Fedora's frontend
```

Routing decisions, sniffing, and packet crafting are the same as covered in [Networking](networking.md).

## 6. Logs — Where Evidence Lives

### Common locations

| File / Dir | Contents |
|------------|----------|
| `/var/log/auth.log` (Debian) / `/var/log/secure` (RHEL) | sshd, sudo, su, PAM events |
| `/var/log/syslog` / `/var/log/messages` | Generic syslog |
| `/var/log/kern.log` | Kernel messages |
| `/var/log/dmesg` | Boot/kernel buffer |
| `/var/log/wtmp` | Past logins (`last`) |
| `/var/log/btmp` | Failed logins (`lastb`) |
| `/var/run/utmp` | Currently logged-in users (`who`) |
| `/var/log/audit/audit.log` | auditd records |
| `/var/log/nginx/`, `/var/log/apache2/` | Web logs |
| `/var/log/journal/` | systemd-journald binary logs |
| `~/.bash_history` `~/.zsh_history` | Command history |
| `~/.viminfo` `~/.lesshst` | Editor history |
| `/var/log/lastlog` | Last login per user |

### Useful one-liners

```bash
last -a                           # past sessions
lastb -a                          # failed logins
who                               # who is logged in now
journalctl -u sshd --since today
grep "Failed password" /var/log/auth.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### auditd — Linux's audit subsystem

Configurable, kernel-level. Often deployed in compliance environments (PCI, FedRAMP).

```bash
# Watch /etc/passwd for any change
auditctl -w /etc/passwd -p wa -k passwd_change

# Search
ausearch -k passwd_change
aureport -au                  # auth report
```

For defense, auditd + Sigma rules + a SIEM is a strong combination. Phase 5 covers this.

## 7. Linux Internals (the parts that matter for security)

| Concept | Why it matters |
|---------|----------------|
| **Namespaces** (`pid`, `mnt`, `net`, `user`, `uts`, `ipc`, `cgroup`, `time`) | Container isolation |
| **cgroups** | Resource limits; container escapes care about this |
| **seccomp** | Syscall filter, sandboxing |
| **AppArmor / SELinux** | MAC frameworks |
| **eBPF** | In-kernel programs — observability + security tools (Falco, Tracee) |
| **/proc** | Kernel info: `/proc/self/maps` (memory), `/proc/<pid>/environ` (env vars), `/proc/version` (kernel) |
| **systemd-resolved / nscd** | Caching layers — affect DNS recon |
| **shared libraries / LD_PRELOAD** | Hijack execution, used by both attackers and rootkits |
| **kernel modules** | rootkit territory; `lsmod` to enumerate |
| **bind mounts / chroots** | Filesystem tricks; not real isolation |

## 8. Common Privilege Escalation Vectors (Linux)

A short tour. Phase 3 has the full chapter.

| Vector | Quick check |
|--------|-------------|
| **Kernel exploits** | `uname -a`; check unpatched CVEs (Dirty Pipe CVE-2022-0847, OverlayFS CVE-2023-0386, GameOver(lay) CVE-2023-2640/32629, etc.) |
| **SUID misuse** | `find / -perm -4000 -type f 2>/dev/null` + GTFOBins |
| **sudo misuse** | `sudo -l` |
| **Capabilities** | `getcap -r / 2>/dev/null` |
| **Writable cron** | `ls -la /etc/cron* /var/spool/cron/` |
| **Writable PATH dirs** | `echo $PATH`; if `.` first, or `/tmp` early — danger |
| **Writable systemd unit / service path** | `find / -writable -name '*.service' 2>/dev/null` |
| **Hijackable shared libraries** | `ldd /usr/local/bin/foo`; check writable paths |
| **NFS no_root_squash** | mount, write SUID file, run on victim |
| **Docker group membership** | `id`; member of `docker` ≈ root |
| **Kubernetes default service tokens** | inside pods: `/var/run/secrets/kubernetes.io/serviceaccount/token` |
| **CVE-2021-4034 (PwnKit)** | Polkit's pkexec — patched everywhere now, but legacy systems |
| **DirtyPipe (CVE-2022-0847)** | Kernel < 5.16.11 |

Run **`linpeas.sh`** during real engagements; **read the output** rather than blindly copying. Understanding *why* something is flagged is what makes you good.

## 9. Hardening Linux (high level)

For when you're the defender:

- **Patch promptly** (`unattended-upgrades`, `dnf-automatic`, configuration mgmt)
- **Minimize installed packages** — fewer attack surfaces
- **Strong SSH config** (covered in [Networking](networking.md))
- **Disable root login** (`PermitRootLogin no`)
- **fail2ban** for brute-force throttling
- **Firewalld / nftables** with default-deny
- **Enable auditd** with sane rules (`audit-userspace` rules collection)
- **AppArmor or SELinux** in enforcing mode
- **Mount options:** `nodev`, `nosuid`, `noexec` on `/tmp`, `/var`, `/home` where possible
- **Kernel hardening:** sysctls (`kernel.kptr_restrict=2`, `kernel.dmesg_restrict=1`, `net.ipv4.tcp_syncookies=1`)
- **Centralize logs** (rsyslog → SIEM)
- **Disable IPv6** if you're not using it (or properly secure it)
- **CIS Benchmark** for your distro is the canonical hardening checklist

## 10. Kali Linux — Quick Map

Kali is "Debian + 600 security tools." Where they live:

```
/usr/share/wordlists/             # SecLists, rockyou.txt.gz
/usr/share/metasploit-framework/  # MSF
/usr/share/seclists/              # if installed separately
/opt/                             # often used for big tools (Burp, etc.)
~/.local/share/                   # user-installed (pipx, etc.)
```

Common operational habits:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install kali-linux-large
sudo apt install pipx && pipx ensurepath

# Per-engagement workspace
mkdir -p ~/engagements/$(date +%Y-%m)/$CLIENT/{recon,scans,creds,loot,reports}
```

## 11. Bash — The Shell You Live In

Quick essentials:

```bash
# Pipes & redirects
cmd1 | cmd2          # stdout → cmd2
cmd > file           # overwrite stdout
cmd >> file          # append
cmd 2> err           # stderr
cmd &> all           # both
cmd < input.txt      # stdin
cmd1 && cmd2         # run cmd2 if cmd1 succeeds
cmd1 || cmd2         # run cmd2 if cmd1 fails
cmd1 ; cmd2          # run both regardless

# Subshells & command substitution
$(cmd)               # output of cmd
`cmd`                # legacy backticks
(cd /tmp && ls)      # subshell
{ cmd1; cmd2; }      # group in current shell

# Loops
for x in a b c; do echo $x; done
while read line; do echo $line; done < file
seq 1 5 | xargs -I{} echo "iter {}"

# Find with action
find /var -mtime -1 -type f -exec ls -l {} \;
find . -name "*.log" -size +10M -print

# Process substitution
diff <(cmd1) <(cmd2)
```

**Bash is also a programming language.** Useful, but for anything beyond ~30 lines, switch to Python.

### Useful one-liners

```bash
# Pull all unique IPs from a log
grep -oE '[0-9]{1,3}(\.[0-9]{1,3}){3}' /var/log/auth.log | sort -u

# Count Apache 5xx by URL
awk '$9 ~ /^5/ {print $7}' /var/log/apache2/access.log | sort | uniq -c | sort -rn

# Watch a file grow live
tail -f /var/log/syslog | grep --color=auto -i fail

# All listening services with the binary
ss -tulnp | sort -u
```

## Self-Test

1. Show me the find one-liner for SUID binaries world-wide.
2. Where do failed SSH logins go on Debian? On RHEL?
3. What does `chmod 4755` do?
4. `getcap -r / 2>/dev/null` — what is it for and why use it?
5. List three privesc vectors you'd check on a fresh Linux shell.
6. Write a one-liner: top 10 IPs by failed login count from `/var/log/auth.log`.
7. Difference between `/var/log/wtmp` and `/var/log/btmp`?
8. What does `NoNewPrivileges=true` in a systemd unit prevent?

→ Next: [Windows](windows.md)
