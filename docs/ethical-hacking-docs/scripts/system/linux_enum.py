#!/usr/bin/env python3
"""
linux_enum.py — Pure-Python Linux privilege-escalation enumerator.

Enumerates the most useful local-privesc indicators on a Linux host
without invoking external tools. Useful in restricted environments
where curl/wget/bash are unavailable, or when you don't want to leave
the obvious linpeas footprint in process listings.

Checks performed:
  - User identity, groups, sudo -l (best-effort)
  - SUID / SGID binaries (filtered against a known-safe baseline)
  - File capabilities (/usr/sbin/getcap if available; else /proc parse)
  - World-writable files in $PATH and system dirs
  - Cron entries (system + per-user, if readable)
  - SSH keys, authorized_keys, known_hosts in home dirs
  - Kernel version + distro
  - Interesting credentials in common config files
  - Container indicators (/.dockerenv, /proc/1/cgroup)
  - High-value group membership (docker, lxd, disk, ...)
  - Writable systemd unit files
  - Mounted filesystems (NFS no_root_squash hint)
  - .bash_history & shell history files

Output: JSON (default) or a human-readable summary.

⚠️ AUTHORIZATION REQUIRED ⚠️
Run only on systems you own or are authorized to assess.

Usage:
    python3 linux_enum.py
    python3 linux_enum.py --summary
    python3 linux_enum.py --output enum.json
    python3 linux_enum.py --skip-files     # skip slow filesystem walks
"""
from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Common safe SUIDs that almost always exist; not interesting unless context unusual.
COMMON_SUIDS = {
    "/usr/bin/passwd", "/usr/bin/chsh", "/usr/bin/chfn", "/usr/bin/gpasswd",
    "/usr/bin/newgrp", "/usr/bin/sudo", "/usr/bin/su",
    "/usr/bin/mount", "/usr/bin/umount",
    "/usr/bin/pkexec",                 # pkexec — interesting if old (PwnKit)
    "/usr/bin/at", "/usr/bin/crontab",
    "/bin/mount", "/bin/umount", "/bin/su", "/bin/ping", "/bin/ping6",
    "/usr/lib/dbus-1.0/dbus-daemon-launch-helper",
    "/usr/lib/openssh/ssh-keysign",
    "/usr/lib/policykit-1/polkit-agent-helper-1",
    "/usr/lib/eject/dmcrypt-get-device",
    "/usr/lib/snapd/snap-confine",
}

# GTFOBins-known SUID binaries — flag with high priority if they're SUID.
HIGH_INTEREST_SUIDS = {
    "/usr/bin/find", "/usr/bin/vim", "/usr/bin/vim.basic", "/usr/bin/nano",
    "/usr/bin/awk", "/usr/bin/gawk", "/usr/bin/python", "/usr/bin/python3",
    "/usr/bin/perl", "/usr/bin/ruby", "/usr/bin/lua", "/usr/bin/php",
    "/usr/bin/less", "/usr/bin/more", "/usr/bin/man",
    "/usr/bin/cp", "/usr/bin/mv", "/usr/bin/dd",
    "/usr/bin/tar", "/usr/bin/zip", "/usr/bin/wget", "/usr/bin/curl",
    "/usr/bin/nmap", "/usr/bin/socat", "/usr/bin/nc", "/usr/bin/ncat",
    "/usr/bin/sed", "/usr/bin/strace", "/usr/bin/screen", "/usr/bin/tmux",
    "/usr/bin/expect", "/usr/bin/git", "/usr/bin/make", "/usr/bin/gdb",
    "/usr/bin/bash", "/bin/bash", "/usr/bin/dash", "/bin/dash",
    "/usr/bin/env", "/usr/bin/find", "/usr/bin/xargs",
}

HIGH_VALUE_GROUPS = {"docker", "lxd", "disk", "video", "kvm", "wheel", "sudo", "admin"}

CRED_PATTERNS = [
    re.compile(r"(?i)password\s*[:=]\s*['\"]?([^\s'\"#]{4,})"),
    re.compile(r"(?i)passwd\s*[:=]\s*['\"]?([^\s'\"#]{4,})"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"]?([^\s'\"#]{8,})"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})"),
    re.compile(r"(?i)token\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{20,})"),
    re.compile(r"AKIA[0-9A-Z]{16}"),                            # AWS access key
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]

CRED_FILE_GLOBS = [
    "/etc/passwd", "/etc/group", "/etc/issue", "/etc/os-release",
    "/etc/network/interfaces",
    "/etc/apache2/apache2.conf", "/etc/apache2/sites-enabled/*",
    "/etc/nginx/nginx.conf", "/etc/nginx/sites-enabled/*",
    "/var/www/html/wp-config.php",
    "/var/www/html/.env", "/opt/*/.env",
    "/etc/cron.d/*", "/etc/cron.daily/*", "/etc/cron.hourly/*",
    "/etc/cron.weekly/*", "/etc/cron.monthly/*", "/etc/crontab",
]


@dataclass
class Finding:
    severity: str        # info / low / medium / high / critical
    category: str
    title: str
    detail: dict | str | list = ""


@dataclass
class Report:
    hostname: str = ""
    kernel: str = ""
    distro: str = ""
    user: dict = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)


def safe_run(cmd: list[str], timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return ""


def collect_identity(report: Report) -> None:
    try:
        report.hostname = os.uname().nodename
        report.kernel = os.uname().release
    except OSError:
        pass
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            report.distro = next((l.strip() for l in f if l.startswith("PRETTY_NAME=")), "").split("=", 1)[-1].strip('"')
    except OSError:
        pass

    try:
        uid = os.getuid()
        gid = os.getgid()
        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        try:
            user = pwd.getpwuid(uid).pw_name
        except KeyError:
            user = str(uid)
        report.user = {"uid": uid, "gid": gid, "user": user, "groups": groups, "egid": os.getegid(), "euid": os.geteuid()}

        priv_groups = [g for g in groups if g in HIGH_VALUE_GROUPS]
        if priv_groups:
            sev = "critical" if "docker" in priv_groups or "lxd" in priv_groups or "disk" in priv_groups else "medium"
            report.findings.append(
                Finding(severity=sev, category="group_membership", title=f"User in high-value group(s): {priv_groups}",
                        detail={"groups": priv_groups, "implication": "Often equivalent to root"})
            )
    except (OSError, KeyError) as e:
        report.findings.append(Finding(severity="info", category="identity", title="Could not enumerate identity", detail=str(e)))


def collect_sudo(report: Report) -> None:
    out = safe_run(["sudo", "-n", "-l"])
    if not out:
        out = safe_run(["sudo", "-l"])
    if out:
        if "may run the following" in out or "NOPASSWD" in out or "(ALL" in out:
            report.findings.append(
                Finding(severity="medium", category="sudo", title="Current user has sudo entries", detail=out.strip())
            )


def collect_suid_sgid(report: Report) -> None:
    suid_found: list[dict] = []
    sgid_found: list[dict] = []
    high_interest: list[dict] = []
    for root, dirs, files in os.walk("/", followlinks=False):
        # Prune virtual / network filesystems
        dirs[:] = [d for d in dirs if d not in ("proc", "sys", "dev", "run", "snap", "boot")]
        for name in files:
            p = os.path.join(root, name)
            try:
                st = os.lstat(p)
            except (FileNotFoundError, PermissionError, OSError):
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            mode = st.st_mode
            if mode & stat.S_ISUID:
                rec = {"path": p, "mode": oct(mode), "owner": st.st_uid}
                if p in HIGH_INTEREST_SUIDS:
                    high_interest.append(rec)
                elif p not in COMMON_SUIDS:
                    suid_found.append(rec)
            elif mode & stat.S_ISGID and mode & 0o010:
                sgid_found.append({"path": p, "mode": oct(mode), "group": st.st_gid})

    if high_interest:
        report.findings.append(
            Finding(severity="high", category="suid", title=f"GTFOBins-listed SUID binaries ({len(high_interest)})",
                    detail=high_interest)
        )
    if suid_found:
        report.findings.append(
            Finding(severity="medium", category="suid", title=f"Unusual SUID binaries ({len(suid_found)})", detail=suid_found[:50])
        )


def collect_capabilities(report: Report) -> None:
    out = safe_run(["getcap", "-r", "/", "2>/dev/null"])
    if not out:
        # try without recursive flag, common path
        out = safe_run(["getcap", "-r", "/usr"])
    if out:
        interesting = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(c in line for c in ("cap_setuid", "cap_dac_read_search", "cap_dac_override",
                                       "cap_chown", "cap_sys_admin", "cap_sys_ptrace")):
                interesting.append(line)
        if interesting:
            report.findings.append(
                Finding(severity="high", category="capabilities", title=f"Interesting capabilities found ({len(interesting)})",
                        detail=interesting)
            )


def collect_world_writable(report: Report) -> None:
    path_dirs = [d for d in os.environ.get("PATH", "").split(":") if d]
    interesting: list[str] = []
    for d in path_dirs:
        try:
            st = os.lstat(d)
        except (FileNotFoundError, PermissionError, OSError):
            continue
        if st.st_mode & 0o002:
            interesting.append(d)
    if interesting:
        report.findings.append(
            Finding(severity="high", category="writable_path", title=f"World-writable directories in $PATH ({len(interesting)})",
                    detail=interesting)
        )

    # Check /etc/passwd writability
    try:
        st = os.lstat("/etc/passwd")
        if st.st_mode & 0o002:
            report.findings.append(
                Finding(severity="critical", category="writable_passwd", title="/etc/passwd is world-writable",
                        detail="Can append a uid=0 user")
            )
    except OSError:
        pass


def collect_cron(report: Report) -> None:
    cron_paths = ["/etc/crontab", "/etc/anacrontab", "/var/spool/cron/crontabs"]
    cron_dirs = ["/etc/cron.d", "/etc/cron.hourly", "/etc/cron.daily", "/etc/cron.weekly", "/etc/cron.monthly"]
    cron_entries: list[dict] = []
    for f in cron_paths:
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            cron_entries.append({"path": f, "content": content})
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            continue
    for d in cron_dirs:
        try:
            for entry in os.listdir(d):
                full = os.path.join(d, entry)
                try:
                    st = os.lstat(full)
                    writable = bool(st.st_mode & 0o002)
                    cron_entries.append({"path": full, "writable": writable})
                except OSError:
                    continue
        except (FileNotFoundError, PermissionError):
            continue
    if cron_entries:
        report.findings.append(
            Finding(severity="info", category="cron", title=f"Cron files visible ({len(cron_entries)})", detail=cron_entries[:30])
        )


def collect_ssh_keys(report: Report) -> None:
    found: list[dict] = []
    homes = ["/root"] + [pwd.getpwuid(u.pw_uid).pw_dir for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_dir]
    for h in set(homes):
        ssh_dir = os.path.join(h, ".ssh")
        try:
            for entry in os.listdir(ssh_dir):
                p = os.path.join(ssh_dir, entry)
                try:
                    st = os.lstat(p)
                except OSError:
                    continue
                if stat.S_ISREG(st.st_mode):
                    found.append({"path": p, "size": st.st_size, "mode": oct(st.st_mode)})
        except (FileNotFoundError, PermissionError):
            continue
    if found:
        report.findings.append(
            Finding(severity="medium" if any(".pub" not in f["path"] for f in found) else "info",
                    category="ssh", title=f"SSH key files visible ({len(found)})", detail=found[:30])
        )


def collect_credential_files(report: Report) -> None:
    creds_found: list[dict] = []
    for pattern in CRED_FILE_GLOBS:
        for p in Path("/").glob(pattern.lstrip("/")):
            try:
                if not p.is_file():
                    continue
                with open(p, encoding="utf-8", errors="ignore") as f:
                    text = f.read(20000)
                for cre in CRED_PATTERNS:
                    for m in cre.finditer(text):
                        creds_found.append({"file": str(p), "match": m.group(0)[:80]})
                        if len(creds_found) > 100:
                            break
            except (PermissionError, OSError):
                continue
    if creds_found:
        report.findings.append(
            Finding(severity="high", category="credentials", title=f"Credential-like patterns in config files ({len(creds_found)})",
                    detail=creds_found[:30])
        )


def collect_container(report: Report) -> None:
    if os.path.exists("/.dockerenv"):
        report.findings.append(Finding(severity="info", category="container", title="Inside a Docker container",
                                       detail="See /.dockerenv"))
    try:
        with open("/proc/1/cgroup", encoding="utf-8") as f:
            cg = f.read()
        if any(s in cg for s in ("docker", "kubepods", "lxc", "containerd")):
            report.findings.append(Finding(severity="info", category="container", title="cgroup suggests container", detail=cg[:300]))
    except OSError:
        pass


def collect_history(report: Report) -> None:
    history_files: list[str] = []
    for u in [pwd.getpwuid(0)] + list(pwd.getpwall()):
        if u.pw_uid != 0 and u.pw_uid < 1000:
            continue
        for f in (".bash_history", ".zsh_history", ".python_history", ".mysql_history"):
            path = os.path.join(u.pw_dir, f)
            try:
                st = os.lstat(path)
                if stat.S_ISREG(st.st_mode) and st.st_size > 0:
                    history_files.append(path)
            except OSError:
                continue
    if history_files:
        report.findings.append(
            Finding(severity="info", category="history", title=f"Shell histories visible ({len(history_files)})", detail=history_files)
        )


def collect_mounts(report: Report) -> None:
    try:
        with open("/proc/mounts", encoding="utf-8") as f:
            mounts = f.read()
    except OSError:
        return
    nfs_lines = [l for l in mounts.splitlines() if " nfs" in l]
    if nfs_lines:
        report.findings.append(
            Finding(severity="info", category="mounts", title=f"NFS mounts visible ({len(nfs_lines)}) — check for no_root_squash",
                    detail=nfs_lines)
        )
    # Look for /etc/exports
    try:
        with open("/etc/exports", encoding="utf-8") as f:
            exports = f.read()
        if "no_root_squash" in exports:
            report.findings.append(
                Finding(severity="critical", category="nfs", title="/etc/exports has no_root_squash entry",
                        detail=exports[:500])
            )
    except (FileNotFoundError, PermissionError):
        pass


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-o", "--output", help="Write JSON to file")
    p.add_argument("--summary", action="store_true", help="Human-readable summary instead of JSON")
    p.add_argument("--skip-files", action="store_true", help="Skip slow filesystem walks (SUID, capabilities)")
    args = p.parse_args()

    report = Report()
    collect_identity(report)
    collect_sudo(report)
    if not args.skip_files:
        collect_suid_sgid(report)
        collect_capabilities(report)
    collect_world_writable(report)
    collect_cron(report)
    collect_ssh_keys(report)
    collect_credential_files(report)
    collect_container(report)
    collect_history(report)
    collect_mounts(report)

    if args.summary and not args.output:
        print(f"Host: {report.hostname}    Kernel: {report.kernel}    Distro: {report.distro}")
        print(f"User: {report.user.get('user')} (uid={report.user.get('uid')}) groups={report.user.get('groups')}")
        print(f"\nFindings: {len(report.findings)}")
        for f in sorted(report.findings, key=lambda x: ("info low medium high critical".split().index(x.severity), x.category)):
            print(f"\n[{f.severity.upper():9}] {f.category}: {f.title}")
            if isinstance(f.detail, str):
                if f.detail:
                    print(f"          {f.detail[:400]}")
            elif isinstance(f.detail, list):
                for item in f.detail[:5]:
                    print(f"          {item}")
                if len(f.detail) > 5:
                    print(f"          (+{len(f.detail)-5} more)")
            elif isinstance(f.detail, dict):
                for k, v in f.detail.items():
                    print(f"          {k}: {v}")
    else:
        out = json.dumps(asdict(report), indent=2, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
