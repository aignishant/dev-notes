# 05 · Python for Offensive Security

!!! abstract "Goal of this module"
    Build fluency in the Python patterns that matter for offense — not general Python, not "web-app Python," but the **subset every pentester, red teamer, and exploit dev uses daily**. Start the `redshift-toolkit` package that will grow for the rest of the curriculum.

## 5.1 Why Python, and why a personal toolkit

Most offensive tooling ships in Python: impacket, pwntools, bloodhound.py, Responder, large chunks of the Metasploit ecosystem, most nuclei replacements, most parsers and glue code. It's also what most security teams hire you to write.

The defender's Python is batch ETL and API glue. The offensive Python is:

- **Fast one-off scripts** you can type in a minute and throw away.
- **Concurrent / async** network work — you scan a /24 or crawl a site in seconds, not minutes.
- **Binary & protocol manipulation** — `struct`, `ctypes`, `socket`, `ssl`.
- **Cryptography and encoding** — `hashlib`, `base64`, `pycryptodome`, JWT tooling.
- **Impacket-family** SMB/LDAP/DCOM clients that don't depend on the Microsoft client stack.
- **Readable CLIs** with `argparse` / `rich` / `typer`, because tools without help output are tools you don't use.

By Module 66 you will own a ~300-script package. The discipline starts now.

## 5.2 The stdlib modules you will use forever

### 5.2.1 `socket` — raw network

The absolute bedrock. Every custom scanner, reverse shell, protocol client, or passive sniffer uses it.

```python
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(2.0)
    s.connect(("10.40.0.10", 22))
    banner = s.recv(256)
    print(banner.decode(errors="replace"))
```

Key call outs:

- `socket.setdefaulttimeout()` — save yourself from hanging forever.
- `SOCK_STREAM` (TCP) vs `SOCK_DGRAM` (UDP) vs `SOCK_RAW` (packet crafting; needs root).
- `AF_INET` (IPv4) vs `AF_INET6` vs `AF_UNIX`.

### 5.2.2 `struct` — pack and unpack binary data

Essential when you're talking to protocols or parsing binary files.

```python
import struct
# Pack a little-endian 32-bit int and a 4-byte bytes payload
packet = struct.pack("<I4s", 0xdeadbeef, b"ABCD")
print(packet.hex())     # efbeadde41424344
print(struct.unpack("<I4s", packet))
```

Cheat sheet:

| Format | Meaning |
|--------|---------|
| `<` / `>` / `=` / `!` | little / big / native / network (big-endian) |
| `b` / `B` | signed / unsigned char (1 byte) |
| `h` / `H` | signed / unsigned short (2) |
| `i` / `I` | signed / unsigned int (4) |
| `q` / `Q` | signed / unsigned long long (8) |
| `s` | bytes of length N |

You'll see struct in exploit-dev when crafting return addresses, in protocol parsers, in shellcode stubs, in custom C2 encoders.

### 5.2.3 `subprocess` — run external tools safely

```python
import subprocess
result = subprocess.run(
    ["nmap", "-sV", "-p22,80,443", target],
    capture_output=True, text=True, timeout=120, check=False,
)
print(result.stdout)
```

Rules:

- **Avoid `shell=True`** — command injection in your own tool is embarrassing.
- Always pass a **list of args**.
- Always set `timeout=` — external processes can hang.
- `check=False` + inspect `returncode` yourself.

### 5.2.4 `asyncio` — concurrency without thread pain

```python
import asyncio

async def check(ip: str, port: int) -> bool:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=2.0
        )
        writer.close()
        return True
    except (asyncio.TimeoutError, OSError):
        return False

async def sweep(ip: str, ports: list[int]) -> dict[int, bool]:
    results = await asyncio.gather(*(check(ip, p) for p in ports))
    return dict(zip(ports, results))

print(asyncio.run(sweep("10.40.0.10", [22, 80, 443, 445, 3389])))
```

A full /24 port sweep that would take 5 minutes in synchronous code takes seconds in asyncio. Async is the default pattern for network tooling from here on.

### 5.2.5 `argparse`, `logging`, `pathlib`, `dataclasses`

These four give you 90% of CLI scaffolding.

- **`argparse`** — CLI flags with help and validation.
- **`logging`** — structured logs you can grep, level-filter, and redirect.
- **`pathlib.Path`** — never concatenate paths with strings again.
- **`dataclasses.dataclass`** — type-hinted record types without boilerplate.

### 5.2.6 `hashlib`, `hmac`, `secrets`, `base64`, `ssl`

Cryptography stdlib. MD5, SHA-family, HMAC, constant-time compare, b64/b32/b16 codecs, TLS sockets. For heavy crypto, reach for `pycryptodome` or `cryptography`.

### 5.2.7 `ctypes` — calling native libraries

Entry point to interacting with system APIs (kernel32.dll, libc) from Python. Heavily used in evasion research and in-memory execution demos (Part 11–12).

```python
import ctypes
libc = ctypes.CDLL("libc.so.6")
print(libc.getuid())           # same as os.getuid() but via direct syscall
```

### 5.2.8 `os`, `sys`, `signal`, `platform`

Fundamentals. Learn `os.walk`, `sys.argv`, `signal.signal(SIGINT, handler)`, `platform.system()`.

## 5.3 The third-party libraries you'll live in

| Library | What for | Used in |
|---------|---------|---------|
| `requests` | Simple synchronous HTTP | Basic web probes, older scripts |
| `httpx` | Modern sync + async HTTP w/ HTTP/2 | Modern web / API scanners |
| `beautifulsoup4` + `lxml` | HTML/XML parsing | Scraping, recon |
| `scapy` | Packet crafting and sniffing | ARP spoofing, MITM, network fingerprinting |
| `impacket` | Windows protocols (SMB/LDAP/DCOM/Kerberos) | 90% of Windows attacks from Linux |
| `paramiko` | SSH client | Automated SSH pivoting |
| `pycryptodome` | AES/RSA/ECC/etc. | Crypto attacks, payload encoders |
| `cryptography` | Modern crypto (preferred over pycryptodome for new code) | Same |
| `dnspython` | DNS queries | DNS recon, zone transfer |
| `python-nmap` | Wrap nmap | Programmatic scanning |
| `pwntools` | Exploit-dev helpers | Part 12 |
| `rich` / `typer` | Pretty CLI output and typed CLIs | Your own tooling |
| `pyyaml` | YAML parse/emit | Configs |

## 5.4 Patterns every script should follow

### 5.4.1 The argparse skeleton

```python
#!/usr/bin/env python3
"""One-line summary. Longer explanation. Example usage."""
from __future__ import annotations
import argparse, sys

def main() -> int:
    p = argparse.ArgumentParser(description="What this does")
    p.add_argument("--target", "-t", required=True)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--verbose", "-v", action="count", default=0)
    args = p.parse_args()
    # ... work ...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Principles:

- Script has a docstring at the top — your future self thanks you.
- `-h` prints useful help with an example.
- Meaningful exit codes (`0` success, `1` logical failure, `2` usage/config error).
- `--format json` on every tool so it composes with others.
- `-v` / `-vv` for verbosity levels.

### 5.4.2 The logging skeleton

```python
import logging

def setup_logging(verbosity: int = 0) -> None:
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbosity, logging.DEBUG)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

log = logging.getLogger("redshift")
log.info("connecting to %s", target)
```

Log to stderr (default), keep stdout for tool-consumable output.

### 5.4.3 The async-scanner template

Pattern you'll reuse for port scans, web spidering, subdomain checking, login sprays, anything where you send many independent requests.

```python
import asyncio

async def work(item):
    ...  # one unit of work

async def run_many(items, concurrency=50):
    sem = asyncio.Semaphore(concurrency)
    async def bounded(i):
        async with sem:
            return await work(i)
    return await asyncio.gather(*(bounded(i) for i in items))

results = asyncio.run(run_many(my_items, concurrency=100))
```

Key discipline:

- **Bound concurrency** with a Semaphore — a SYN-flooding your own scanner is bad manners.
- **Handle exceptions per-task** — one bad item should not take down the batch.
- **Rate-limit** where needed — respect target capacity (and rate-limit-detect alarms).

### 5.4.4 Error handling — "fail soft, log loud"

Offensive tooling runs against hostile / broken targets. Don't write `try: ... except: pass`. Log the exception with context, move on to the next item.

```python
try:
    result = await probe(target)
except (asyncio.TimeoutError, ConnectionError) as exc:
    log.warning("probe failed for %s: %s", target, exc)
    result = None
```

### 5.4.5 Type hints — not optional

```python
def crack(hashes: list[str], wordlist: Path, *, mode: int) -> dict[str, str]:
    ...
```

Type hints let your IDE, your future self, and any contributor read the function without running it. They are non-negotiable in `redshift-toolkit`.

## 5.5 Starting the toolkit — `redshift-toolkit`

Your first commits:

```
redshift-toolkit/
├── pyproject.toml           # PEP 621 metadata
├── README.md
└── redshift_toolkit/
    ├── __init__.py
    ├── utils/
    │   ├── __init__.py
    │   ├── encoder_decoder.py   ← first real module (this lesson)
    │   ├── cheatsheet_cli.py    ← second (this lesson)
    │   └── notes_cli.py         ← third (this lesson)
    ├── recon/        (empty, filled in Part 3)
    ├── scan/         (empty, filled in Part 3)
    ├── web/          (empty, filled in Part 4)
    └── ... (rest of package tree)
```

Install it in editable mode once, then every script you write can `from redshift_toolkit.utils.encoder_decoder import b64`.

```bash
cd redshift-toolkit
pip install -e .
```

### 5.5.1 The `encoder_decoder.py` module

A Swiss-army-knife for every encoding you deal with on an engagement: base64/32/16, URL, hex, ROT-N, gzip, simple XOR. Usable as a library AND a CLI:

```bash
python -m redshift_toolkit.utils.encoder_decoder b64 encode "admin:admin"
python -m redshift_toolkit.utils.encoder_decoder b64 decode "YWRtaW46YWRtaW4="
echo -n "DEADBEEF" | python -m redshift_toolkit.utils.encoder_decoder hex decode
```

### 5.5.2 The `cheatsheet_cli.py` module

A terminal cheat sheet that lives next to your shell. Add commands you keep re-Googling (the `impacket-secretsdump` syntax, the `msfvenom` one-liner for a Windows reverse shell, etc.). Fuzzy-search from the command line.

```bash
python -m redshift_toolkit.utils.cheatsheet_cli search "secretsdump"
python -m redshift_toolkit.utils.cheatsheet_cli add --tags "impacket,creds" --body "impacket-secretsdump -just-dc-ntlm ..."
```

### 5.5.3 The `notes_cli.py` module

Per-engagement markdown notebook. Auto-timestamps every entry. Writes to a folder that becomes your evidence pile at the end of the engagement.

```bash
python -m redshift_toolkit.utils.notes_cli new "Acme-Q2-2026"
python -m redshift_toolkit.utils.notes_cli add "Acme-Q2-2026" --tag recon "found 12 subdomains via ..."
python -m redshift_toolkit.utils.notes_cli export "Acme-Q2-2026" --format markdown
```

These three plus the Module 01–04 scripts are your starter kit. Every subsequent Part adds substantial modules under the same `redshift_toolkit` namespace.

## 5.6 Real-world scenario — the 60-second recon script

You're on a bug bounty. You've picked a scope: `*.example.com`. Before you launch subfinder / amass / nuclei, you write a 40-line Python script that:

1. Pulls subdomains from `crt.sh` (certificate transparency logs) via its JSON endpoint.
2. Dedupes and probes each with an async HTTP GET.
3. Prints a CSV of `subdomain, status_code, title, server_header`.

That 40-line script is the **industry reality** of what "recon" actually looks like — the big tools are great for deep passes, but an operator who can whip up a 40-line custom script **against the specific program's quirks** will always find what the big tools miss. You'll write this script in Module 10 (Part 3 — Recon). Start warming up.

## 5.7 Exercises

1. **Install `redshift-toolkit` in editable mode** and confirm you can import it from any directory.
2. **Run the three utils modules** against their CLIs. Add five entries to your cheatsheet. Start an "onboarding" engagement note.
3. **Write an async port scanner** using the pattern in §5.4.3 — sweep 1–1024 on all hosts in your `lab.yaml`. Compare runtime to a synchronous version.
4. **Add a fourth util:** `http_replayer.py` that takes a saved request from Burp (or an `.http` file) and replays it with customizable params. (Answer will slot into the `utils/` directory later.)
5. **Read the source** of `impacket.smbconnection.SMBConnection` — just the class, not the whole library. 20 minutes. This builds the habit of reading offensive tools rather than just using them.

## 5.8 Further reading

- **Black Hat Python** — Justin Seitz & Tim Arnold (2nd ed.). The canonical book for this chapter.
- **Violent Python** — TJ O'Connor. Older but still taught.
- **Fluent Python** — Luciano Ramalho. Go from "I write Python" to "I understand Python" — pays back ten-fold in offensive work.
- **The Impacket examples** — <https://github.com/fortra/impacket/tree/master/examples>. Read 5 of these. Model your own scripts after them.
- **Real Python** — <https://realpython.com> — asyncio tutorials are excellent.
- **PEP 20** (Zen of Python) — keep on desk.

!!! success "Exit criteria for Module 05 and Part 1"
    - `pip install -e redshift-toolkit` works from a clean venv.
    - You've run all three utils CLIs and added your own content to them.
    - You can open any blank file and type the argparse + logging + async-scanner skeleton from memory.
    - You can explain (without notes) what `asyncio.Semaphore` does and why you bound concurrency.
    - **You can run `lab_health_check.py` against your lab and it returns all green.**
    
    All five boxes ticked → you are ready for Part 2 (Networking & Cryptography).
