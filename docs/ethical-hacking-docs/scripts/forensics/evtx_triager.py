#!/usr/bin/env python3
"""Fast EVTX triage: per-channel summary + notable-event highlighting.

Walks Windows Event Log (.evtx) files and produces a quick triage report
showing:

  - Per-source / per-EventID counts
  - Time range per file
  - Highlighted notable events (logon, process creation, service install,
    PowerShell, scheduled task creation, lateral-movement candidates)

Defensive DFIR / SOC use only.

Dependencies
------------
    pip install python-evtx

Usage
-----
    python3 evtx_triager.py /path/to/Security.evtx
    python3 evtx_triager.py C:/Windows/System32/winevt/Logs/ --json triage.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from Evtx.Evtx import Evtx  # type: ignore
except ImportError:  # pragma: no cover
    print("[-] python-evtx required: pip install python-evtx", file=sys.stderr)
    sys.exit(2)


# Notable IDs by channel — non-exhaustive but high-signal
NOTABLE: dict[str, dict[int, str]] = {
    "Security": {
        4624: "Account Logon",
        4625: "Failed Logon",
        4634: "Logoff",
        4648: "Explicit Logon",
        4672: "Special Privileges Assigned",
        4688: "Process Creation",
        4697: "Service Installed",
        4698: "Scheduled Task Created",
        4699: "Scheduled Task Deleted",
        4720: "User Account Created",
        4722: "User Account Enabled",
        4724: "Password Reset",
        4728: "User Added to Sec-Enabled Global Group",
        4732: "User Added to Sec-Enabled Local Group",
        4768: "TGT Requested (Kerberos)",
        4769: "Service Ticket Requested (Kerberos)",
        4771: "Kerberos Pre-Auth Failed",
        4776: "NTLM Authentication",
        5140: "Network Share Object Accessed",
        5145: "Detailed Share Access",
        1102: "Audit Log Cleared",
    },
    "System": {
        7045: "Service Installed",
        7036: "Service State Change",
        104: "Event Log Cleared",
        6005: "Event Log Service Started",
        6006: "Event Log Service Stopped",
    },
    "Microsoft-Windows-Sysmon/Operational": {
        1: "Process Create",
        3: "Network Connection",
        7: "Image Loaded",
        8: "CreateRemoteThread",
        10: "Process Access",
        11: "File Created",
        12: "Registry Object Add/Delete",
        13: "Registry Value Set",
        15: "FileCreateStreamHash",
        17: "Pipe Created",
        18: "Pipe Connected",
        22: "DNS Query",
        23: "File Delete",
        25: "Process Tampering",
    },
    "Microsoft-Windows-PowerShell/Operational": {
        4103: "Module Logging",
        4104: "Script Block Logging",
        4105: "Script Execution Started",
        4106: "Script Execution Stopped",
    },
    "Windows PowerShell": {
        400: "Engine Started",
        403: "Engine Stopped",
        600: "Provider Lifecycle",
    },
    "Microsoft-Windows-TaskScheduler/Operational": {
        106: "Task Registered",
        140: "Task Updated",
        141: "Task Deleted",
        200: "Action Started",
        201: "Action Completed",
    },
    "Microsoft-Windows-WinRM/Operational": {
        91: "Session Created",
        168: "WSMan Authenticate",
    },
    "Microsoft-Windows-Bits-Client/Operational": {
        59: "Job Started",
        61: "Transfer Error",
    },
}


# Generic fallback channel name guesses
def detect_channel(filename: str) -> str:
    name = filename.lower()
    if "security" in name:
        return "Security"
    if "sysmon" in name:
        return "Microsoft-Windows-Sysmon/Operational"
    if "powershell" in name and "operational" in name:
        return "Microsoft-Windows-PowerShell/Operational"
    if "powershell" in name:
        return "Windows PowerShell"
    if "taskscheduler" in name:
        return "Microsoft-Windows-TaskScheduler/Operational"
    if "system" in name:
        return "System"
    if "winrm" in name:
        return "Microsoft-Windows-WinRM/Operational"
    if "application" in name:
        return "Application"
    return "Unknown"


NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}


def parse_record(xml_str: str) -> dict | None:
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return None
    sys_el = root.find("e:System", NS)
    if sys_el is None:
        return None

    eid_el = sys_el.find("e:EventID", NS)
    eid = int(eid_el.text) if eid_el is not None and eid_el.text else 0
    prov_el = sys_el.find("e:Provider", NS)
    provider = prov_el.attrib.get("Name", "") if prov_el is not None else ""
    chan_el = sys_el.find("e:Channel", NS)
    channel = chan_el.text if chan_el is not None else ""
    time_el = sys_el.find("e:TimeCreated", NS)
    ts = time_el.attrib.get("SystemTime", "") if time_el is not None else ""
    comp_el = sys_el.find("e:Computer", NS)
    computer = comp_el.text if comp_el is not None else ""

    # Pull out a few common EventData fields
    data = {}
    for d in root.findall("e:EventData/e:Data", NS):
        n = d.attrib.get("Name", "")
        if n:
            data[n] = d.text

    return {
        "EventID": eid,
        "Provider": provider,
        "Channel": channel,
        "Time": ts,
        "Computer": computer,
        "Data": data,
    }


def triage_file(path: Path, max_notable: int = 50) -> dict:
    channel_guess = detect_channel(path.name)
    counts: Counter = Counter()
    by_eid_provider: dict[tuple[int, str], int] = defaultdict(int)
    times: list[str] = []
    notable_events: list[dict] = []
    total = 0
    parse_errors = 0

    with Evtx(str(path)) as log:
        for rec in log.records():
            total += 1
            try:
                xml = rec.xml()
            except Exception:
                parse_errors += 1
                continue
            ev = parse_record(xml)
            if not ev:
                parse_errors += 1
                continue
            counts[ev["EventID"]] += 1
            by_eid_provider[(ev["EventID"], ev["Provider"])] += 1
            if ev["Time"]:
                times.append(ev["Time"])
            channel = ev["Channel"] or channel_guess
            ids = NOTABLE.get(channel, {})
            if ev["EventID"] in ids and len(notable_events) < max_notable:
                notable_events.append({
                    "label": ids[ev["EventID"]],
                    "EventID": ev["EventID"],
                    "Channel": channel,
                    "Time": ev["Time"],
                    "Computer": ev["Computer"],
                    "Provider": ev["Provider"],
                    "Data": ev["Data"],
                })

    times.sort()
    return {
        "file": str(path),
        "channel_guess": channel_guess,
        "total_records": total,
        "parse_errors": parse_errors,
        "first_event_time": times[0] if times else None,
        "last_event_time": times[-1] if times else None,
        "top_event_ids": counts.most_common(20),
        "notable_events": notable_events,
    }


def collect_files(path: Path) -> list[Path]:
    if path.is_file() and path.suffix.lower() == ".evtx":
        return [path]
    files = []
    for root, _, fns in os.walk(path):
        for fn in fns:
            if fn.lower().endswith(".evtx"):
                files.append(Path(root) / fn)
    return files


def print_summary(report: dict) -> None:
    print(f"\n=== {report['file']} ===")
    print(f"  channel guess  : {report['channel_guess']}")
    print(f"  total records  : {report['total_records']}")
    print(f"  parse errors   : {report['parse_errors']}")
    print(f"  time range     : {report['first_event_time']}  ->  {report['last_event_time']}")
    print(f"  top EventIDs (id : count):")
    for eid, cnt in report["top_event_ids"]:
        print(f"      {eid:<6} : {cnt}")
    if report["notable_events"]:
        print(f"  notable events (showing {len(report['notable_events'])}):")
        for n in report["notable_events"][:25]:
            print(f"      [{n['Time']}] {n['EventID']:<6} {n['label']:<32}  on {n['Computer']}")
        if len(report["notable_events"]) > 25:
            print(f"      ... ({len(report['notable_events']) - 25} more — use --json)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", type=Path, help=".evtx file or directory of files")
    ap.add_argument("--max-notable", type=int, default=200, help="cap notable events stored per file")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    if not args.path.exists():
        print(f"[-] path not found: {args.path}", file=sys.stderr)
        return 2

    files = collect_files(args.path)
    if not files:
        print(f"[-] no .evtx files found in {args.path}", file=sys.stderr)
        return 1

    print(f"[+] triaging {len(files)} EVTX file(s)")
    reports = []
    for f in files:
        try:
            r = triage_file(f, args.max_notable)
            reports.append(r)
            print_summary(r)
        except Exception as e:
            print(f"[-] error on {f}: {e}")

    if args.json:
        args.json.write_text(json.dumps({"reports": reports}, indent=2, default=str))
        print(f"\n[+] full triage -> {args.json}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(130)
