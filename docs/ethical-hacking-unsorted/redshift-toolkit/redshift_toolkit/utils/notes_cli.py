"""
redshift_toolkit.utils.notes_cli
================================

Per-engagement markdown notebook. Every entry is auto-timestamped and tagged.
Folder structure on disk:

    ~/.redshift/engagements/
    └── <engagement-slug>/
        ├── engagement.yaml      # metadata (client, start date, scope refs)
        ├── notes.md             # running notes, chronological
        └── evidence/            # for screenshots, CLI transcripts, dumps

CLI
---
    rs-notes new  "Acme-Q2-2026" --client "Acme Corp"
    rs-notes add  "Acme-Q2-2026" --tag recon "found 12 subdomains via crt.sh"
    rs-notes add  "Acme-Q2-2026" --tag web --from-file output.txt
    rs-notes list
    rs-notes show "Acme-Q2-2026" --grep kerberos
    rs-notes export "Acme-Q2-2026" --format markdown > report-raw.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(os.environ.get("REDSHIFT_HOME",
                           Path.home() / ".redshift")) / "engagements"

G = "\033[92m"; C = "\033[96m"; Y = "\033[93m"; D = "\033[2m"; B = "\033[1m"; X = "\033[0m"

SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def slugify(text: str) -> str:
    return SLUG_RE.sub("-", text.strip()).strip("-").lower() or "engagement"


# --- Data ---------------------------------------------------------------------

@dataclass
class Engagement:
    slug: str
    client: str = ""
    start: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scope_ref: str = ""
    path: Path = field(default=Path(), repr=False)

    def save_meta(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "engagement.yaml").write_text(
            yaml.safe_dump(
                {k: v for k, v in asdict(self).items() if k != "path"},
                sort_keys=False,
            )
        )
        (self.path / "evidence").mkdir(exist_ok=True)
        notes = self.path / "notes.md"
        if not notes.exists():
            notes.write_text(f"# Engagement: {self.client or self.slug}\n\n"
                             f"_Started {self.start}_\n\n")

    @classmethod
    def load(cls, slug: str) -> "Engagement":
        slug = slugify(slug)
        path = ROOT / slug
        meta_path = path / "engagement.yaml"
        if not meta_path.exists():
            raise FileNotFoundError(f"no engagement {slug} (use `new` first)")
        meta = yaml.safe_load(meta_path.read_text()) or {}
        return cls(slug=slug, path=path, **{k: v for k, v in meta.items() if k != "slug"})


# --- Operations ---------------------------------------------------------------

def new_engagement(slug: str, client: str = "", scope_ref: str = "") -> Engagement:
    eng = Engagement(slug=slugify(slug), client=client, scope_ref=scope_ref,
                     path=ROOT / slugify(slug))
    eng.save_meta()
    return eng


def add_note(slug: str, body: str, tags: list[str]) -> Path:
    eng = Engagement.load(slug)
    notes = eng.path / "notes.md"
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tag_str = " ".join(f"`#{t}`" for t in tags)
    entry = f"\n---\n\n### {ts} {tag_str}\n\n{body}\n"
    with notes.open("a") as f:
        f.write(entry)
    return notes


def list_engagements() -> list[Engagement]:
    if not ROOT.exists():
        return []
    out = []
    for d in sorted(ROOT.iterdir()):
        if (d / "engagement.yaml").exists():
            try:
                out.append(Engagement.load(d.name))
            except Exception:
                continue
    return out


def show(slug: str, grep: str | None = None) -> str:
    eng = Engagement.load(slug)
    content = (eng.path / "notes.md").read_text()
    if grep:
        content = "\n".join(
            line for line in content.splitlines() if grep.lower() in line.lower()
        )
    return content


def export(slug: str, fmt: str) -> str:
    eng = Engagement.load(slug)
    if fmt == "markdown":
        return (eng.path / "notes.md").read_text()
    if fmt == "json":
        entries = _parse_markdown(eng.path / "notes.md")
        return json.dumps({"engagement": asdict(eng), "entries": entries},
                          default=str, indent=2)
    raise ValueError(f"unknown format {fmt}")


def _parse_markdown(md: Path) -> list[dict]:
    """Naive parser: split on ### timestamp headers."""
    entries = []
    current: dict | None = None
    ts_re = re.compile(r"^### (\S+)\s*(.*)$")
    for line in md.read_text().splitlines():
        m = ts_re.match(line)
        if m:
            if current:
                entries.append(current)
            tags = re.findall(r"`#([\w-]+)`", m.group(2))
            current = {"timestamp": m.group(1), "tags": tags, "body": ""}
        elif current is not None:
            current["body"] += line + "\n"
    if current:
        entries.append(current)
    return entries


# --- CLI ----------------------------------------------------------------------

def _render_list(engs: list[Engagement], *, color: bool) -> str:
    def c(code: str) -> str: return code if color else ""
    if not engs:
        return f"{c(D)}(no engagements yet){c(X)}"
    rows = []
    for e in engs:
        rows.append(f"{c(B)}{e.slug:<30}{c(X)} "
                    f"{c(C)}{e.client:<30}{c(X)} "
                    f"{c(D)}started {e.start}{c(X)}")
    return "\n".join(rows)


def main() -> int:
    p = argparse.ArgumentParser(description="Per-engagement markdown notebook.")
    p.add_argument("--no-color", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="start a new engagement notebook")
    p_new.add_argument("slug")
    p_new.add_argument("--client", default="")
    p_new.add_argument("--scope-ref", default="", help="path to scope/ROE file")

    p_add = sub.add_parser("add", help="append a timestamped entry")
    p_add.add_argument("slug")
    p_add.add_argument("body", nargs="?", help="body (or use --from-file / stdin)")
    p_add.add_argument("--tag", action="append", default=[],
                       help="repeatable tag flag: --tag recon --tag web")
    p_add.add_argument("--from-file", type=Path,
                       help="read body from a file (e.g. tool output)")

    sub.add_parser("list", help="list all engagements")

    p_show = sub.add_parser("show", help="print notebook markdown")
    p_show.add_argument("slug")
    p_show.add_argument("--grep", help="filter lines containing substring")

    p_exp = sub.add_parser("export", help="export notebook")
    p_exp.add_argument("slug")
    p_exp.add_argument("--format", choices=["markdown", "json"], default="markdown")

    args = p.parse_args()
    color = not args.no_color

    try:
        if args.cmd == "new":
            eng = new_engagement(args.slug, args.client, args.scope_ref)
            print(f"created {eng.path}")
            return 0

        if args.cmd == "add":
            if args.from_file:
                body = args.from_file.read_text()
            elif args.body:
                body = args.body
            else:
                body = sys.stdin.read()
            if not body.strip():
                print("ERROR: empty body", file=sys.stderr); return 2
            path = add_note(args.slug, body.rstrip(), args.tag)
            print(f"appended to {path}")
            return 0

        if args.cmd == "list":
            print(_render_list(list_engagements(), color=color))
            return 0

        if args.cmd == "show":
            print(show(args.slug, args.grep))
            return 0

        if args.cmd == "export":
            print(export(args.slug, args.format))
            return 0

    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
