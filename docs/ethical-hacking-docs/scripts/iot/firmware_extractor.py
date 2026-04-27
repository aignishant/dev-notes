#!/usr/bin/env python3
"""Firmware extractor and entropy analyser.

Wraps `binwalk` for signature scanning + extraction, then performs an
in-process entropy analysis (Shannon entropy in fixed-size windows) to
help identify packed/encrypted regions and embedded filesystems.

Authorized firmware analysis only. Designed for IoT/embedded reverse
engineering where you have rights to the firmware image.

Dependencies
------------
- binwalk (system binary; `apt install binwalk` or `pip install binwalk`)
- No required Python deps beyond stdlib

Usage
-----
    python3 firmware_extractor.py firmware.bin
    python3 firmware_extractor.py firmware.bin --extract --outdir extracted/
    python3 firmware_extractor.py firmware.bin --window 4096 --json report.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_WINDOW = 1024


def shannon_entropy(buf: bytes) -> float:
    if not buf:
        return 0.0
    counts = [0] * 256
    for b in buf:
        counts[b] += 1
    n = len(buf)
    h = 0.0
    for c in counts:
        if c:
            p = c / n
            h -= p * math.log2(p)
    return h


def windowed_entropy(path: Path, window: int) -> list[dict]:
    out = []
    offset = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(window)
            if not chunk:
                break
            h = shannon_entropy(chunk)
            out.append({"offset": offset, "size": len(chunk), "entropy": round(h, 4)})
            offset += len(chunk)
    return out


def classify_entropy(h: float) -> str:
    if h < 1.0:
        return "null/zero (padding or sparse)"
    if h < 4.5:
        return "low (text or simple structure)"
    if h < 6.5:
        return "medium (mixed, code or partly compressed)"
    if h < 7.5:
        return "high (compressed)"
    return "very high (likely encrypted or fully compressed)"


def run_binwalk_signatures(path: Path) -> str:
    if shutil.which("binwalk") is None:
        return ""
    try:
        r = subprocess.run(["binwalk", str(path)], capture_output=True, text=True, timeout=180)
        return r.stdout
    except Exception as e:
        return f"[binwalk error: {e}]"


def run_binwalk_extract(path: Path, outdir: Path) -> str:
    if shutil.which("binwalk") is None:
        return "[binwalk not installed]"
    outdir.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(
            ["binwalk", "-e", "--directory", str(outdir), str(path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        return r.stdout + r.stderr
    except Exception as e:
        return f"[extract error: {e}]"


def parse_binwalk_lines(output: str) -> list[dict]:
    """Parse binwalk's text table into structured signatures."""
    sigs = []
    started = False
    for line in output.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("DECIMAL"):
            started = True
            continue
        if not started:
            continue
        if line.startswith("---"):
            continue
        # binwalk output: <decimal> <hex> <description>
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            dec = int(parts[0])
            hexv = parts[1]
        except ValueError:
            continue
        sigs.append({"decimal_offset": dec, "hex_offset": hexv, "description": parts[2]})
    return sigs


def histogram_text(windows: list[dict], width: int = 60) -> str:
    """ASCII bar-chart of entropy windows: 0 -> ' ', 8 -> '#'."""
    rows = []
    for w in windows[:200]:  # cap output rows
        h = w["entropy"]
        bar_len = int((h / 8.0) * width)
        bar = "#" * bar_len + " " * (width - bar_len)
        rows.append(f"{w['offset']:>10} | {bar} | {h:.2f}")
    if len(windows) > 200:
        rows.append(f"... ({len(windows) - 200} more windows; use --json for full data)")
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("firmware", type=Path, help="firmware binary to analyse")
    ap.add_argument("--window", type=int, default=DEFAULT_WINDOW, help="entropy window size in bytes")
    ap.add_argument("--extract", action="store_true", help="run binwalk extraction")
    ap.add_argument("--outdir", type=Path, default=Path("./_firmware_extracted"), help="extraction directory")
    ap.add_argument("--json", type=Path, default=None, help="write structured report to JSON")
    ap.add_argument("--no-binwalk", action="store_true", help="skip binwalk signature scan")
    args = ap.parse_args()

    if not args.firmware.is_file():
        print(f"[-] not a file: {args.firmware}", file=sys.stderr)
        return 2

    size = args.firmware.stat().st_size
    print(f"[+] analysing {args.firmware} ({size} bytes)")

    sigs: list[dict] = []
    if not args.no_binwalk:
        out = run_binwalk_signatures(args.firmware)
        if out:
            sigs = parse_binwalk_lines(out)
            print(f"[+] binwalk found {len(sigs)} signature hits")
            for s in sigs[:25]:
                print(f"    {s['hex_offset']:>10}  {s['description'][:120]}")
            if len(sigs) > 25:
                print(f"    ... ({len(sigs) - 25} more)")
        else:
            print("[-] binwalk not available or no output")

    print(f"\n[+] computing windowed Shannon entropy (window={args.window})")
    windows = windowed_entropy(args.firmware, args.window)
    overall = shannon_entropy(args.firmware.read_bytes())
    print(f"[+] overall entropy: {overall:.4f} -- {classify_entropy(overall)}")
    print(f"[+] {len(windows)} windows analysed\n")
    print(histogram_text(windows))

    extract_log = ""
    if args.extract:
        print(f"\n[+] extracting via binwalk -> {args.outdir}")
        extract_log = run_binwalk_extract(args.firmware, args.outdir)
        print(extract_log[-2000:])

    if args.json:
        report = {
            "file": str(args.firmware),
            "size": size,
            "overall_entropy": overall,
            "overall_classification": classify_entropy(overall),
            "binwalk_signatures": sigs,
            "entropy_windows": windows,
            "window_size": args.window,
            "extracted": args.extract,
            "extract_log": extract_log if args.extract else None,
        }
        args.json.write_text(json.dumps(report, indent=2))
        print(f"\n[+] full report -> {args.json}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(130)
