"""
redshift_toolkit.utils.cheatsheet_cli
=====================================

A personal command cheat-sheet that lives next to your shell.

Add the commands you keep re-Googling — one-liners, impacket syntax,
msfvenom incantations, Nmap NSE calls — and fuzzy-search them when you
need them. Stored locally as YAML so it's versionable and greppable.

Default store: ~/.redshift/cheats.yaml

Use as a CLI
------------
    rs-cheats add --tags "impacket,creds" --body \\
        "impacket-secretsdump -just-dc-ntlm redshift.local/admin@dc01"

    rs-cheats search "kerberoast"
    rs-cheats list --tag impacket
    rs-cheats delete <id>
    rs-cheats export --format json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)

DEFAULT_STORE = Path(os.environ.get("REDSHIFT_HOME",
                                    Path.home() / ".redshift")) / "cheats.yaml"

G = "\033[92m"; C = "\033[96m"; Y = "\033[93m"; D = "\033[2m"; B = "\033[1m"; X = "\033[0m"


@dataclass
class Cheat:
    id: str
    title: str
    body: str
    tags: list[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def new(cls, title: str, body: str, tags: list[str]) -> "Cheat":
        cid = hashlib.sha1(
            f"{title}|{body}|{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        return cls(id=cid, title=title, body=body, tags=tags)


# --- Store --------------------------------------------------------------------

def _load(path: Path) -> list[Cheat]:
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text()) or []
    except yaml.YAMLError as exc:
        print(f"ERROR: invalid store {path}: {exc}", file=sys.stderr)
        sys.exit(1)
    return [Cheat(**entry) for entry in raw]


def _save(path: Path, cheats: list[Cheat]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump([asdict(c) for c in cheats],
                                   sort_keys=False, allow_unicode=True))


# --- Operations ---------------------------------------------------------------

def add(store: Path, title: str, body: str, tags: list[str]) -> Cheat:
    cheats = _load(store)
    cheat = Cheat.new(title, body, tags)
    cheats.append(cheat)
    _save(store, cheats)
    return cheat


def search(store: Path, query: str, tag: str | None = None) -> list[Cheat]:
    q = query.lower()
    results = []
    for c in _load(store):
        if tag and tag not in c.tags:
            continue
        haystack = f"{c.title}\n{c.body}\n{' '.join(c.tags)}".lower()
        if q in haystack:
            results.append(c)
    return results


def list_all(store: Path, tag: str | None = None) -> list[Cheat]:
    return [c for c in _load(store) if not tag or tag in c.tags]


def delete(store: Path, cheat_id: str) -> bool:
    cheats = _load(store)
    kept = [c for c in cheats if c.id != cheat_id]
    if len(kept) == len(cheats):
        return False
    _save(store, kept)
    return True


# --- Rendering ----------------------------------------------------------------

def render(cheats: list[Cheat], *, color: bool = True) -> str:
    def c(code: str) -> str:
        return code if color else ""
    if not cheats:
        return f"{c(D)}(no matches){c(X)}"
    out = []
    for ch in cheats:
        tag_str = " ".join(f"#{t}" for t in ch.tags)
        out.append(f"{c(B)}[{ch.id}]{c(X)} {c(C)}{ch.title or '(untitled)'}{c(X)} "
                   f"{c(Y)}{tag_str}{c(X)}")
        for line in ch.body.splitlines():
            out.append(f"    {line}")
        out.append(f"    {c(D)}created {ch.created}{c(X)}")
        out.append("")
    return "\n".join(out)


# --- CLI ----------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Personal offensive command cheat-sheet.")
    p.add_argument("--store", "-S", type=Path, default=DEFAULT_STORE)
    p.add_argument("--no-color", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add a new cheat")
    p_add.add_argument("--title", "-T", default="")
    p_add.add_argument("--tags", default="", help="comma-separated")
    p_add.add_argument("--body", "-b", help="body (or omit to read stdin)")

    p_search = sub.add_parser("search", help="fuzzy-search title/body/tags")
    p_search.add_argument("query")
    p_search.add_argument("--tag", help="restrict to a tag")

    p_list = sub.add_parser("list", help="list all cheats")
    p_list.add_argument("--tag", help="restrict to a tag")

    p_del = sub.add_parser("delete", help="delete a cheat by id")
    p_del.add_argument("id")

    p_export = sub.add_parser("export", help="dump store as JSON or YAML")
    p_export.add_argument("--format", choices=["json", "yaml"], default="json")

    args = p.parse_args()
    color = not args.no_color

    if args.cmd == "add":
        body = args.body if args.body else sys.stdin.read().rstrip("\n")
        if not body:
            print("ERROR: empty body", file=sys.stderr); return 2
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        cheat = add(args.store, args.title, body, tags)
        print(f"added [{cheat.id}] {cheat.title}")
        return 0

    if args.cmd == "search":
        print(render(search(args.store, args.query, args.tag), color=color))
        return 0

    if args.cmd == "list":
        print(render(list_all(args.store, args.tag), color=color))
        return 0

    if args.cmd == "delete":
        ok = delete(args.store, args.id)
        print(f"{'deleted' if ok else 'not found'}: {args.id}")
        return 0 if ok else 1

    if args.cmd == "export":
        cheats = _load(args.store)
        if args.format == "json":
            print(json.dumps([asdict(c) for c in cheats], indent=2))
        else:
            print(yaml.safe_dump([asdict(c) for c in cheats], sort_keys=False))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
