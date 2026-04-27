#!/usr/bin/env python3
"""
nmap_xml_parser.py — Parse nmap XML output into structured JSON.

Turns nmap's `-oX` XML output into a clean, structured JSON document suitable
for:
  - SIEM ingestion (Splunk, Elastic, Sumo)
  - Diff-ing across scans (compare yesterday's XML vs today's)
  - Pipeline input to other tools (CVE correlator, vuln tracker, ticketing)
  - Human-readable summary

Pure stdlib — no external dependencies.

Usage:
    nmap -sV -sC -oX scan.xml 10.0.0.5
    python3 nmap_xml_parser.py scan.xml
    python3 nmap_xml_parser.py scan.xml --pretty
    python3 nmap_xml_parser.py scan.xml --summary
    python3 nmap_xml_parser.py scan.xml --diff yesterday.xml
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict


@dataclass
class Service:
    name: str = ""
    product: str = ""
    version: str = ""
    extrainfo: str = ""
    cpe: list[str] = field(default_factory=list)
    confidence: int = 0

    def display(self) -> str:
        bits = [self.product, self.version, self.extrainfo]
        return " ".join(b for b in bits if b)


@dataclass
class Port:
    port: int
    protocol: str
    state: str
    reason: str = ""
    service: Service = field(default_factory=Service)
    scripts: dict[str, str] = field(default_factory=dict)


@dataclass
class HostResult:
    address: str
    address_type: str = "ipv4"
    hostnames: list[str] = field(default_factory=list)
    state: str = ""
    os_matches: list[dict] = field(default_factory=list)
    ports: list[Port] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)


@dataclass
class ScanReport:
    args: str
    start: str
    elapsed: str
    version: str
    hosts: list[HostResult] = field(default_factory=list)


def parse_service(svc_elem: ET.Element | None) -> Service:
    if svc_elem is None:
        return Service()
    cpes = [c.text for c in svc_elem.findall("cpe") if c.text]
    return Service(
        name=svc_elem.get("name", ""),
        product=svc_elem.get("product", ""),
        version=svc_elem.get("version", ""),
        extrainfo=svc_elem.get("extrainfo", ""),
        cpe=cpes,
        confidence=int(svc_elem.get("conf") or 0),
    )


def parse_port(port_elem: ET.Element) -> Port:
    state_elem = port_elem.find("state")
    p = Port(
        port=int(port_elem.get("portid") or 0),
        protocol=port_elem.get("protocol", ""),
        state=state_elem.get("state", "") if state_elem is not None else "",
        reason=state_elem.get("reason", "") if state_elem is not None else "",
        service=parse_service(port_elem.find("service")),
    )
    for script_elem in port_elem.findall("script"):
        sid = script_elem.get("id", "")
        out = script_elem.get("output", "").strip()
        if sid:
            p.scripts[sid] = out
    return p


def parse_host(host_elem: ET.Element) -> HostResult:
    state_elem = host_elem.find("status")
    state = state_elem.get("state", "") if state_elem is not None else ""

    addr = "0.0.0.0"
    addr_type = "ipv4"
    for a in host_elem.findall("address"):
        if a.get("addrtype") in ("ipv4", "ipv6"):
            addr = a.get("addr", addr)
            addr_type = a.get("addrtype", addr_type)
            break

    hostnames = [h.get("name", "") for h in host_elem.findall("./hostnames/hostname") if h.get("name")]

    host = HostResult(address=addr, address_type=addr_type, hostnames=hostnames, state=state)

    for port_elem in host_elem.findall("./ports/port"):
        host.ports.append(parse_port(port_elem))

    for os_match in host_elem.findall("./os/osmatch"):
        host.os_matches.append(
            {"name": os_match.get("name", ""), "accuracy": int(os_match.get("accuracy") or 0)}
        )

    for hostscript in host_elem.findall("./hostscript/script"):
        sid = hostscript.get("id", "")
        if sid:
            host.scripts[sid] = hostscript.get("output", "").strip()

    return host


def parse_xml(path: str) -> ScanReport:
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "nmaprun":
        raise ValueError(f"{path} doesn't look like nmap XML (root={root.tag!r})")

    runstats = root.find("runstats/finished")
    elapsed = runstats.get("elapsed", "") if runstats is not None else ""
    report = ScanReport(
        args=root.get("args", ""),
        start=root.get("startstr", ""),
        elapsed=elapsed,
        version=root.get("version", ""),
    )
    for host_elem in root.findall("host"):
        report.hosts.append(parse_host(host_elem))
    return report


def report_to_dict(report: ScanReport) -> dict:
    """Convert dataclass tree into a JSON-friendly dict."""
    return asdict(report)


def summarize(report: ScanReport) -> str:
    lines = [
        f"# nmap scan summary",
        f"  args:    {report.args}",
        f"  started: {report.start}",
        f"  elapsed: {report.elapsed}s",
        f"  hosts:   {len(report.hosts)}",
        "",
    ]
    for h in report.hosts:
        if h.state != "up":
            continue
        title = h.address
        if h.hostnames:
            title += f" ({', '.join(h.hostnames)})"
        lines.append(f"## {title}")
        if h.os_matches:
            lines.append(f"  OS guess: {h.os_matches[0]['name']} ({h.os_matches[0]['accuracy']}%)")
        open_ports = [p for p in h.ports if p.state == "open"]
        lines.append(f"  Open ports: {len(open_ports)}")
        for p in sorted(open_ports, key=lambda x: x.port):
            svc = p.service.display() or p.service.name or "?"
            lines.append(f"    {p.port}/{p.protocol:<3} {p.service.name:<15} {svc}")
            for sid, output in p.scripts.items():
                first_line = output.splitlines()[0] if output else ""
                lines.append(f"      └─ [{sid}] {first_line}")
        lines.append("")
    return "\n".join(lines)


def diff_reports(old: ScanReport, new: ScanReport) -> dict:
    """Diff two scan reports — what hosts/ports are new, gone, or changed."""

    def host_index(r: ScanReport) -> dict[str, HostResult]:
        return {h.address: h for h in r.hosts}

    def port_key(p: Port) -> tuple:
        return (p.port, p.protocol)

    old_idx = host_index(old)
    new_idx = host_index(new)

    new_hosts = sorted(set(new_idx) - set(old_idx))
    gone_hosts = sorted(set(old_idx) - set(new_idx))

    changed: list[dict] = []
    for addr in sorted(set(old_idx) & set(new_idx)):
        oh, nh = old_idx[addr], new_idx[addr]
        old_ports = {port_key(p): p for p in oh.ports if p.state == "open"}
        new_ports = {port_key(p): p for p in nh.ports if p.state == "open"}
        opened = [k for k in new_ports if k not in old_ports]
        closed = [k for k in old_ports if k not in new_ports]
        version_changed = []
        for k in old_ports.keys() & new_ports.keys():
            if old_ports[k].service.display() != new_ports[k].service.display():
                version_changed.append(
                    {
                        "port": k[0],
                        "protocol": k[1],
                        "old": old_ports[k].service.display(),
                        "new": new_ports[k].service.display(),
                    }
                )
        if opened or closed or version_changed:
            changed.append(
                {
                    "host": addr,
                    "newly_open": [{"port": p[0], "protocol": p[1]} for p in opened],
                    "newly_closed": [{"port": p[0], "protocol": p[1]} for p in closed],
                    "version_changed": version_changed,
                }
            )

    return {"new_hosts": new_hosts, "gone_hosts": gone_hosts, "changed_hosts": changed}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("xml", help="nmap XML file to parse")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    p.add_argument("--summary", action="store_true", help="Print human-readable summary instead of JSON")
    p.add_argument("--diff", metavar="OLD_XML", help="Compare against a previous nmap XML")
    p.add_argument("-o", "--output", help="Write to file")
    args = p.parse_args()

    try:
        new_report = parse_xml(args.xml)
    except (ET.ParseError, ValueError, FileNotFoundError) as e:
        print(f"[-] Could not parse {args.xml}: {e}", file=sys.stderr)
        return 1

    if args.diff:
        try:
            old_report = parse_xml(args.diff)
        except (ET.ParseError, ValueError, FileNotFoundError) as e:
            print(f"[-] Could not parse {args.diff}: {e}", file=sys.stderr)
            return 1
        diff = diff_reports(old_report, new_report)
        out = json.dumps(diff, indent=2 if args.pretty else None)
    elif args.summary:
        out = summarize(new_report)
    else:
        out = json.dumps(report_to_dict(new_report), indent=2 if args.pretty else None, default=str)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[+] Wrote {args.output}", file=sys.stderr)
    else:
        print(out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
