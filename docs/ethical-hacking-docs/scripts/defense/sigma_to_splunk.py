#!/usr/bin/env python3
"""Bulk Sigma rule -> Splunk SPL converter.

Two paths:
1. If `sigma` CLI (pySigma + sigma-cli) is installed, shell out for proper
   conversions (`sigma convert -t splunk ...`).
2. Otherwise, fall back to a pure-Python YAML pattern translator that handles
   the common subset of Sigma logsources/detections used in blue-team rules.

Defensive blue-team / detection engineering only.

Dependencies
------------
- `pyyaml` (required for fallback parsing)
- `sigma-cli` recommended: `pip install sigma-cli pysigma-backend-splunk`

Usage
-----
    # Convert single file (best-effort)
    python3 sigma_to_splunk.py rule.yml

    # Convert directory (recursive)
    python3 sigma_to_splunk.py /path/to/sigma/rules --out converted.spl

    # Force fallback even if sigma-cli installed
    python3 sigma_to_splunk.py rules/ --no-sigma-cli
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    print("[-] PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


def have_sigma_cli() -> bool:
    return shutil.which("sigma") is not None


def convert_via_cli(rule_path: Path, target: str = "splunk") -> tuple[str, str]:
    """Use sigma-cli to convert. Returns (spl, stderr). Raises on failure."""
    cmd = ["sigma", "convert", "-t", target, str(rule_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.stdout.strip(), r.stderr.strip()


# ---- Fallback pure-Python translator (handles a useful subset) -----------------------------
def _quote(value) -> str:
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if not s:
        return '""'
    # Splunk-style: wrap if any whitespace/wildcard/operator
    if any(ch in s for ch in ' \t"()='):
        return '"' + s.replace('"', r'\"') + '"'
    return s


def _modifier_to_spl(field: str, modifier: str, value) -> str:
    """Translate a single field-modifier-value Sigma fragment into SPL."""
    if not isinstance(value, list):
        value = [value]

    if modifier == "contains":
        clauses = [f'{field}=*{_quote(v).strip("\"")}*' for v in value]
    elif modifier == "startswith":
        clauses = [f'{field}={_quote(v).strip("\"")}*' for v in value]
    elif modifier == "endswith":
        clauses = [f'{field}=*{_quote(v).strip("\"")}' for v in value]
    elif modifier == "re":
        clauses = [f'| regex {field}="{v}"' for v in value]
        return " ".join(clauses)
    elif modifier in {"gt", "gte", "lt", "lte"}:
        op_map = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
        clauses = [f"{field}{op_map[modifier]}{_quote(v)}" for v in value]
    else:  # equals (default)
        clauses = [f"{field}={_quote(v)}" for v in value]
    if len(clauses) == 1:
        return clauses[0]
    return "(" + " OR ".join(clauses) + ")"


def _selection_to_spl(selection: dict) -> str:
    parts: list[str] = []
    for key, value in selection.items():
        if "|" in key:
            field, modifier = key.split("|", 1)
            modifier = modifier.split("|")[0]  # drop chained modifiers (best-effort)
        else:
            field, modifier = key, "equals"
        parts.append(_modifier_to_spl(field, modifier, value))
    return " ".join(parts)


def _condition_to_spl(condition: str, selections: dict) -> str:
    """Resolve the Sigma `condition` string by substituting selection blocks."""
    # Limited support: handle "selection" / "all of selection*" / "1 of selection*" /
    # logical operators 'and', 'or', 'not'
    cond = condition.strip()
    # Replace 'all of <prefix>*' and '1 of <prefix>*'
    import re

    def all_of(m):
        prefix = m.group(1)
        names = [n for n in selections if n.startswith(prefix)]
        if not names:
            return "()"
        return "(" + " AND ".join(f"({_selection_to_spl(selections[n])})" for n in names) + ")"

    def one_of(m):
        prefix = m.group(1)
        names = [n for n in selections if n.startswith(prefix)]
        if not names:
            return "()"
        return "(" + " OR ".join(f"({_selection_to_spl(selections[n])})" for n in names) + ")"

    cond = re.sub(r"all of (\w+)\*", all_of, cond)
    cond = re.sub(r"1 of (\w+)\*", one_of, cond)

    # Plain selection name -> inline SPL
    def sel_repl(m):
        name = m.group(0)
        if name in selections:
            return "(" + _selection_to_spl(selections[name]) + ")"
        return name

    cond = re.sub(r"\b\w+\b", sel_repl, cond)
    # Logical operators
    cond = cond.replace(" and ", " AND ").replace(" or ", " OR ").replace(" not ", " NOT ")
    return cond


def fallback_convert(rule_path: Path) -> str:
    raw = yaml.safe_load(rule_path.read_text())
    if raw is None:
        return ""
    detection = raw.get("detection", {})
    condition = detection.get("condition", "selection")
    selections = {k: v for k, v in detection.items() if k != "condition" and k != "timeframe" and isinstance(v, dict)}
    if not selections:
        return f"# [WARN] {rule_path.name}: no selection blocks parseable"
    spl_body = _condition_to_spl(condition, selections)
    title = raw.get("title", rule_path.stem)
    level = raw.get("level", "")
    desc = (raw.get("description") or "").replace("\n", " ").strip()
    return f"# [{level.upper() if level else 'rule'}] {title}\n# {desc}\n# Source: {rule_path.name}\n{spl_body}"


def gather_rules(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    rules: list[Path] = []
    for root, _, files in os.walk(target):
        for fn in files:
            if fn.endswith((".yml", ".yaml")):
                rules.append(Path(root) / fn)
    return rules


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", type=Path, help="Sigma rule file or directory")
    ap.add_argument("--out", type=Path, default=None, help="write converted SPL to file (default: stdout)")
    ap.add_argument("--no-sigma-cli", action="store_true", help="force pure-Python fallback")
    ap.add_argument("--target", default="splunk", help="sigma-cli backend target (default: splunk)")
    ap.add_argument("--json", type=Path, default=None, help="also emit JSON manifest of conversions")
    args = ap.parse_args()

    if not args.path.exists():
        print(f"[-] path not found: {args.path}", file=sys.stderr)
        return 2

    rules = gather_rules(args.path)
    if not rules:
        print(f"[-] no .yml/.yaml rules found in {args.path}", file=sys.stderr)
        return 1

    use_cli = (not args.no_sigma_cli) and have_sigma_cli()
    print(f"[+] {len(rules)} rule(s); converter = {'sigma-cli' if use_cli else 'fallback (best-effort)'}")

    converted: list[dict] = []
    blocks: list[str] = []
    for r in rules:
        try:
            if use_cli:
                spl, err = convert_via_cli(r, args.target)
                if err and not spl:
                    raise RuntimeError(err)
            else:
                spl = fallback_convert(r)
        except Exception as e:
            spl = f"# [ERROR] {r.name}: {e}"

        block = f"# === {r.name} ===\n{spl}\n"
        blocks.append(block)
        converted.append({"file": str(r), "spl": spl})

    output = "\n".join(blocks)

    if args.out:
        args.out.write_text(output)
        print(f"[+] wrote {len(blocks)} blocks -> {args.out}")
    else:
        print(output)

    if args.json:
        args.json.write_text(json.dumps({"converter": "sigma-cli" if use_cli else "fallback", "rules": converted}, indent=2))
        print(f"[+] manifest -> {args.json}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        sys.exit(130)
