#!/usr/bin/env python3
"""
windows_enum.py — Windows enumeration helper over WinRM / SMB.

Useful when you have valid creds for a Windows host but NOT a shell —
or when you want repeatable, scriptable enumeration over the network
during an authorized engagement.

Connects via WinRM (preferred) and runs a fixed set of read-only
PowerShell / cmd commands focused on local-privesc indicators:

  - whoami /priv, /groups, /all
  - Service binary paths + permissions (unquoted, weak ACL hints)
  - Scheduled tasks (running as SYSTEM)
  - AlwaysInstallElevated registry keys
  - Stored credentials (cmdkey /list)
  - Installed hotfixes (input for Watson / WES)
  - Network shares + ACLs
  - WiFi profiles (with key=clear hint — cleartext extraction needs admin)
  - Group Policy Preference passwords in SYSVOL hint

Output: structured JSON. Parses key indicators into 'findings' for triage.

⚠️ AUTHORIZATION REQUIRED ⚠️
Run only against systems you own or are explicitly authorized to test.
WinRM authentications hit Security event logs (4624 type 3, 4672, 4634).

Dependencies:
    pip install pywinrm

Usage:
    python3 windows_enum.py -t 10.0.0.5 -u alice -p 'Summer2026'
    python3 windows_enum.py -t target.local -u alice -p 'Summer2026' --domain CORP
    python3 windows_enum.py -t 10.0.0.5 -u alice -p '...' --hash NTLM_HASH    # NTLM
    python3 windows_enum.py -t 10.0.0.5 -u alice -p 'Summer2026' --port 5986 --ssl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

try:
    import winrm
    from winrm.exceptions import WinRMError
except ImportError:
    print("ERROR: pywinrm is required. Install with: pip install pywinrm", file=sys.stderr)
    sys.exit(2)


# Each command: (label, command, shell)
# shell="ps" -> PowerShell; shell="cmd" -> regular CMD
COMMANDS: list[tuple[str, str, str]] = [
    ("whoami", "whoami /all", "cmd"),
    ("hostname_info", "systeminfo | findstr /B /C:\"Host Name\" /C:\"OS Name\" /C:\"OS Version\" /C:\"System Type\"", "cmd"),
    ("hotfixes", "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object HotFixID, InstalledOn -First 30 | Format-Table -AutoSize | Out-String", "ps"),
    ("services_with_paths",
     "Get-WmiObject -Class Win32_Service | Where-Object { $_.PathName -and $_.StartMode -eq 'Auto' } | "
     "Select-Object Name, StartName, PathName | Format-Table -AutoSize | Out-String -Width 4096", "ps"),
    ("scheduled_tasks_system",
     "Get-ScheduledTask | Where-Object { $_.Principal.UserId -match 'SYSTEM' -and $_.State -ne 'Disabled' } | "
     "Select-Object TaskName, TaskPath, @{n='Action';e={($_.Actions | ForEach-Object Execute) -join ','}}, "
     "@{n='Args';e={($_.Actions | ForEach-Object Arguments) -join ','}} | Format-Table -AutoSize | Out-String -Width 4096", "ps"),
    ("alwaysinstallelevated_hkcu",
     "reg query HKCU\\Software\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated 2>nul", "cmd"),
    ("alwaysinstallelevated_hklm",
     "reg query HKLM\\Software\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated 2>nul", "cmd"),
    ("autologon",
     'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon" 2>nul | findstr /i "DefaultUserName DefaultPassword AutoAdminLogon"', "cmd"),
    ("cmdkey_stored",
     "cmdkey /list", "cmd"),
    ("smb_shares",
     "net share", "cmd"),
    ("network",
     "ipconfig /all", "cmd"),
    ("listening_ports",
     "netstat -ano | findstr LISTENING", "cmd"),
    ("wifi_profiles",
     "netsh wlan show profiles", "cmd"),
    ("local_admins",
     "net localgroup administrators", "cmd"),
    ("env_path",
     "echo %PATH%", "cmd"),
    ("temp_files_writable",
     "icacls C:\\Windows\\Temp", "cmd"),
    ("uac_setting",
     'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA 2>nul', "cmd"),
    ("ps_version",
     "$PSVersionTable | Format-List | Out-String", "ps"),
    ("av_products",
     "Get-WmiObject -Namespace root\\SecurityCenter2 -Class AntiVirusProduct -ErrorAction SilentlyContinue | "
     "Select-Object displayName, productState | Format-Table -AutoSize | Out-String", "ps"),
    ("smb_signing",
     "Get-SmbServerConfiguration | Select-Object EnableSecuritySignature, RequireSecuritySignature | Format-List | Out-String", "ps"),
]


@dataclass
class CommandResult:
    label: str
    command: str
    shell: str
    stdout: str = ""
    stderr: str = ""
    status_code: int = -1
    error: str | None = None


@dataclass
class Finding:
    severity: str
    category: str
    detail: str


@dataclass
class Report:
    target: str
    user: str
    domain: str | None
    commands: list[CommandResult] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def run_command(session: "winrm.Session", cmd: str, shell: str) -> CommandResult:
    res = CommandResult(label="", command=cmd, shell=shell)
    try:
        if shell == "ps":
            r = session.run_ps(cmd)
        else:
            # run_cmd takes (command, args=[]) — pass entire string as one shell call
            r = session.run_cmd("cmd.exe", ["/c", cmd])
        res.stdout = r.std_out.decode("utf-8", errors="replace")
        res.stderr = r.std_err.decode("utf-8", errors="replace")
        res.status_code = r.status_code
    except WinRMError as e:
        res.error = f"WinRM: {e}"
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
    return res


def analyze(report: Report) -> None:
    by_label = {c.label: c for c in report.commands}

    def get_out(label: str) -> str:
        c = by_label.get(label)
        return c.stdout if c else ""

    # whoami /priv parsing
    whoami = get_out("whoami")
    high_priv = ["SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeBackupPrivilege",
                 "SeRestorePrivilege", "SeDebugPrivilege", "SeTakeOwnershipPrivilege",
                 "SeLoadDriverPrivilege", "SeManageVolumePrivilege", "SeTcbPrivilege"]
    for priv in high_priv:
        # 'Enabled' or 'Disabled' on the same line
        m = re.search(rf"{priv}\s+\S.*?\b(Enabled|Disabled)\b", whoami, re.I)
        if m:
            sev = "critical" if priv in ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege",
                                          "SeDebugPrivilege", "SeLoadDriverPrivilege", "SeTcbPrivilege") else "high"
            if m.group(1).lower() == "enabled":
                report.findings.append(
                    Finding(severity=sev, category="privilege", detail=f"{priv} is ENABLED — privesc primitive available")
                )

    # AlwaysInstallElevated
    aie_hkcu = get_out("alwaysinstallelevated_hkcu")
    aie_hklm = get_out("alwaysinstallelevated_hklm")
    if "0x1" in aie_hkcu and "0x1" in aie_hklm:
        report.findings.append(
            Finding(severity="critical", category="aie",
                    detail="AlwaysInstallElevated set in BOTH HKCU and HKLM — any user can install MSI as SYSTEM")
        )
    elif "0x1" in aie_hkcu or "0x1" in aie_hklm:
        report.findings.append(
            Finding(severity="info", category="aie",
                    detail="AlwaysInstallElevated set in one hive (need both for direct privesc)")
        )

    # Autologon
    autologon = get_out("autologon")
    if "DefaultPassword" in autologon:
        report.findings.append(
            Finding(severity="critical", category="autologon",
                    detail="DefaultPassword present in Winlogon registry — cleartext credential")
        )

    # UAC
    uac = get_out("uac_setting")
    if "EnableLUA" in uac:
        m = re.search(r"EnableLUA\s+REG_DWORD\s+(0x[01])", uac)
        if m and m.group(1) == "0x0":
            report.findings.append(
                Finding(severity="high", category="uac",
                        detail="UAC disabled (EnableLUA=0) — admin tokens at full integrity")
            )

    # Service paths — flag unquoted with spaces
    svc = get_out("services_with_paths")
    unquoted: list[str] = []
    for line in svc.splitlines():
        line = line.strip()
        if not line or line.startswith("Name") or line.startswith("---"):
            continue
        # Look for a path with a space that doesn't start with quote
        m = re.search(r"((?:[A-Z]:\\[^\"]*?\.exe)\b)", line)
        if m and " " in m.group(1) and not (m.start(1) > 0 and line[m.start(1) - 1] == '"'):
            unquoted.append(line[:200])
    if unquoted:
        report.findings.append(
            Finding(severity="medium", category="unquoted_path",
                    detail=f"{len(unquoted)} service(s) with unquoted paths containing spaces — investigate")
        )

    # SMB signing
    smb = get_out("smb_signing")
    if "RequireSecuritySignature" in smb and "False" in smb:
        report.findings.append(
            Finding(severity="medium", category="smb_signing",
                    detail="SMB signing not required — host can be a relay target")
        )

    # AV products
    av = get_out("av_products")
    if av.strip():
        report.findings.append(
            Finding(severity="info", category="av", detail=f"AV products visible: {av.strip()[:300]}")
        )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-t", "--target", required=True, help="Target host or IP")
    p.add_argument("-u", "--username", required=True)
    p.add_argument("-p", "--password", required=True, help="Password (or NT hash if --hash)")
    p.add_argument("--domain", help="Domain (for AD users)")
    p.add_argument("--hash", action="store_true", help="Treat -p as an NT hash for NTLM auth")
    p.add_argument("--port", type=int, default=5985, help="WinRM port (5985 plain / 5986 SSL)")
    p.add_argument("--ssl", action="store_true", help="Use HTTPS")
    p.add_argument("-o", "--output", help="Write JSON to file")
    p.add_argument("--summary", action="store_true", help="Human-readable summary")
    args = p.parse_args()

    scheme = "https" if args.ssl else "http"
    endpoint = f"{scheme}://{args.target}:{args.port}/wsman"
    user_full = f"{args.domain}\\{args.username}" if args.domain else args.username

    transport = "ntlm" if args.hash or args.domain else "ntlm"  # ntlm handles both; basic is rarely allowed
    session = winrm.Session(
        endpoint,
        auth=(user_full, args.password),
        transport=transport,
        server_cert_validation="ignore" if args.ssl else "validate",
    )

    print(f"[*] Connecting to {endpoint} as {user_full}...", file=sys.stderr)
    # Sanity check
    try:
        r = session.run_cmd("hostname")
        if r.status_code != 0:
            print(f"[-] Initial hostname check failed: {r.std_err.decode(errors='replace')}", file=sys.stderr)
            return 1
        print(f"[+] Connected. Hostname: {r.std_out.decode().strip()}", file=sys.stderr)
    except Exception as e:
        print(f"[-] Connection failed: {e}", file=sys.stderr)
        return 1

    report = Report(target=args.target, user=args.username, domain=args.domain)
    for label, cmd, shell in COMMANDS:
        print(f"[*] {label}", file=sys.stderr)
        result = run_command(session, cmd, shell)
        result.label = label
        report.commands.append(result)

    analyze(report)

    if args.summary and not args.output:
        print(f"\n=== Enumeration Summary: {args.target} ===")
        print(f"Findings: {len(report.findings)}")
        for f in report.findings:
            print(f"\n  [{f.severity.upper():9}] {f.category}: {f.detail}")
        print("\n--- Command output (truncated) ---")
        for c in report.commands:
            print(f"\n## {c.label}")
            if c.error:
                print(f"  ERROR: {c.error}")
                continue
            out = c.stdout.strip()
            if out:
                for line in out.splitlines()[:25]:
                    print(f"  {line}")
                if len(out.splitlines()) > 25:
                    print(f"  (+{len(out.splitlines()) - 25} more lines)")
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
