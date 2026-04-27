# 🐍 Python for Security

> Python is the lingua franca of offensive *and* defensive security. Burp extensions, Volatility plugins, Metasploit modules, Ghidra scripts, half of CTF tooling, and most blue-team automation are written in Python. By the end of this chapter you should read security-tool source the way you read a newspaper.

---

## 1. Why Python (and when *not* to use it)

Python wins for security because:

- **Batteries included** — `socket`, `ssl`, `hashlib`, `hmac`, `secrets`, `struct`, `ctypes`, `subprocess` ship in stdlib.
- **Massive ecosystem** — `scapy`, `impacket`, `pwntools`, `requests`, `beautifulsoup4`, `paramiko`, `pycryptodome`, `volatility3`, `yara-python`, `angr`.
- **Glue language** — wraps C libs, drives binaries, parses everything.
- **Read-write parity** — quick to write, quick to read in someone else's PoC.

Where Python loses:

- **Speed** — fuzzing, password cracking, ML inference → C/C++/Rust/Go.
- **Stealth implants** — interpreters are noisy and easy to fingerprint; red teams reach for C, C#, Nim, Go, Rust.
- **Kernel work** — write a driver in C, not Python.

**Rule of thumb:** Python for orchestration, parsing, web work, automation, and PoCs. Drop down a language when a hot loop costs you minutes per run.

---

## 2. Environment You'll Actually Use

```bash
# Always work inside virtualenvs. Never `sudo pip install` on a Kali box.
python3 -m venv ~/venvs/sec
source ~/venvs/sec/bin/activate

# Modern installer/resolver
pip install --upgrade pip
pip install pipx                  # for CLI tools
pipx install ruff black mypy     # lint, format, types
```

For per-project tooling, use `pyproject.toml` with [`uv`](https://github.com/astral-sh/uv) or `poetry`. For ad-hoc scripts, single-file scripts with [PEP 723 inline metadata](https://peps.python.org/pep-0723/) are unbeatable:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "rich"]
# ///
import httpx
from rich import print
print(httpx.get("https://httpbin.org/ip").json())
```

Run with `uv run script.py` and it builds the env on the fly — perfect for CTF and engagement scripts.

!!! tip "Versions"
    Target **Python 3.11+**. You get exception groups, `tomllib`, much better tracebacks, and `asyncio.TaskGroup`.

---

## 3. Standard Library You Must Know Cold

| Module | Use |
|---|---|
| `socket` | Raw TCP/UDP, DNS lookups |
| `ssl` | TLS contexts, cert pinning, ALPN |
| `struct` | Pack/unpack binary data (PE, ELF, packets) |
| `hashlib`, `hmac` | Hashes, MACs |
| `secrets` | CSPRNG — use this, **never** `random` for crypto |
| `base64`, `binascii` | Encoding for everything |
| `urllib.parse` | URL encoding/decoding without dependencies |
| `subprocess` | Run binaries safely |
| `pathlib` | Modern file I/O |
| `argparse` | CLI flags |
| `logging` | Structured logs (not `print`!) |
| `json`, `tomllib` | Config & data |
| `re` | Regex (use `regex` lib for anything serious) |
| `ipaddress` | IPv4/IPv6 math without bugs |
| `asyncio` | Concurrency for I/O-bound work |

If you can't read code that uses these without looking up the docs, drill them.

---

## 4. Networking Toolkit

### 4.1 Raw sockets — the foundation

```python
import socket

def banner_grab(host: str, port: int, timeout: float = 2.0) -> bytes | None:
    """Connect, send a tiny probe, read whatever comes back."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            try:
                # Nudge chatty services that won't speak first
                s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
            except OSError:
                pass
            return s.recv(4096)
    except (OSError, socket.timeout):
        return None

if __name__ == "__main__":
    print(banner_grab("scanme.nmap.org", 80))
```

### 4.2 `requests` and `httpx` — HTTP that doesn't fight you

```python
import httpx

# httpx is async-capable, HTTP/2 ready, drop-in for requests
with httpx.Client(http2=True, verify=False, timeout=10) as c:
    r = c.get("https://example.com",
              headers={"User-Agent": "research-bot/1.0"})
    print(r.status_code, len(r.content))
```

When you need to **proxy through Burp** for testing:

```python
proxies = {"all://": "http://127.0.0.1:8080"}
with httpx.Client(proxies=proxies, verify=False) as c:
    c.get("https://target.example")
```

### 4.3 `scapy` — packet surgery

```python
from scapy.all import IP, TCP, sr1, conf
conf.verb = 0

# TCP SYN scan of one port (root required)
def syn_scan(host: str, port: int) -> str:
    pkt = IP(dst=host)/TCP(dport=port, flags="S")
    ans = sr1(pkt, timeout=1)
    if ans is None:
        return "filtered"
    if ans.haslayer(TCP):
        flags = ans[TCP].flags
        if flags == 0x12:        # SYN-ACK
            sr1(IP(dst=host)/TCP(dport=port, flags="R"), timeout=1)
            return "open"
        if flags == 0x14:        # RST-ACK
            return "closed"
    return "unknown"
```

Scapy is a **swiss-army knife**: ARP, DHCP, DNS, 802.11, custom layers — everything is a Python object you can mutate.

### 4.4 `paramiko` / `asyncssh` — SSH automation

```python
import asyncssh, asyncio

async def remote_cmd(host: str, user: str, key: str, cmd: str) -> str:
    async with asyncssh.connect(host, username=user, client_keys=[key],
                                 known_hosts=None) as conn:
        result = await conn.run(cmd, check=True)
        return result.stdout
```

Use this for managing your own lab VMs, not for breaking into things you don't own.

---

## 5. Web Toolkit

| Library | Use |
|---|---|
| `httpx` / `requests` | HTTP client |
| `beautifulsoup4` + `lxml` | HTML parsing |
| `playwright` | Headless browser (handles JS, CSP, modern SPAs) |
| `mitmproxy` | Intercepting proxy you can script |
| `urllib3` | Lower-level retry/connection control |
| `selectolax` | Insanely fast HTML parser |

**Playwright** matters more every year — most modern targets render with JavaScript, so `requests` alone misses half the attack surface:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(ignore_https_errors=True)
    page = ctx.new_page()
    page.goto("https://target.example/login")
    page.fill('input[name="user"]', "admin")
    page.fill('input[name="pass"]', "wrong")
    page.click('button[type="submit"]')
    print(page.content())
    browser.close()
```

---

## 6. Cryptography in Python

The standard library has primitives, but for anything beyond hashes use [`cryptography`](https://cryptography.io/) — it's audited, opinionated, and won't let you build a footgun by accident.

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
aes = AESGCM(key)
nonce = os.urandom(12)                # 96-bit nonce for GCM
ct = aes.encrypt(nonce, b"sensitive", associated_data=b"context")
pt = aes.decrypt(nonce, ct, associated_data=b"context")
assert pt == b"sensitive"
```

Avoid `pycrypto` (abandoned). [`pycryptodome`](https://pycryptodome.readthedocs.io/) is fine and often used in CTFs because it exposes every primitive, including the dangerous ones you sometimes need to attack.

For CTF-style crypto math, **`sympy`** and **`gmpy2`** are your friends (RSA private-key recovery, lattice attacks via [`sage`](https://www.sagemath.org/)).

---

## 7. Binary & File Parsing

```python
import struct

# Parse the first bytes of a PE file
def is_pe(path: str) -> bool:
    with open(path, "rb") as f:
        if f.read(2) != b"MZ":
            return False
        f.seek(0x3C)
        e_lfanew, = struct.unpack("<I", f.read(4))
        f.seek(e_lfanew)
        return f.read(4) == b"PE\x00\x00"
```

For more than a few bytes, reach for:

- **`pefile`** — PE/COFF parsing (Windows malware)
- **`pyelftools`** — ELF parsing (Linux)
- **`construct`** — declarative binary parsers
- **`kaitai-struct-runtime`** — generated parsers from `.ksy` specs

**`pwntools`** is a meta-library: ELF parsing, ROP chain building, gdb scripting, format-string exploitation helpers. If you do binary CTFs, you live here.

---

## 8. Concurrency: Async First

Most security tooling is **I/O bound** — port scanners, fuzzers, web crawlers, log shippers. That's exactly what `asyncio` was built for.

```python
import asyncio

async def is_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError):
        return False

async def scan(host: str, ports: list[int], concurrency: int = 500) -> list[int]:
    sem = asyncio.Semaphore(concurrency)
    async def worker(p: int) -> int | None:
        async with sem:
            return p if await is_open(host, p) else None
    results = await asyncio.gather(*(worker(p) for p in ports))
    return sorted(p for p in results if p is not None)

if __name__ == "__main__":
    print(asyncio.run(scan("scanme.nmap.org", list(range(1, 1025)))))
```

A semaphore caps concurrent sockets so you don't blow past your OS file-descriptor limit (`ulimit -n`). Threads would work too — but threads + 5,000 sockets means 5,000 stacks; async = one thread, one event loop, one stack.

For CPU-bound work (hashing, decompression, ML), reach for `concurrent.futures.ProcessPoolExecutor`.

---

## 9. Project Layout for Real Tools

When your "script" grows past 200 lines, give it a real shape:

```
mytool/
├── pyproject.toml
├── README.md
├── src/
│   └── mytool/
│       ├── __init__.py
│       ├── cli.py            # typer or argparse entrypoint
│       ├── core.py           # business logic
│       ├── net.py            # I/O
│       └── output.py         # rich tables, JSON, CSV
└── tests/
    └── test_core.py
```

A minimal `pyproject.toml`:

```toml
[project]
name = "mytool"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27", "typer>=0.12", "rich>=13"]

[project.scripts]
mytool = "mytool.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Now `pip install -e .` gives you a `mytool` command on PATH — same as nmap, just yours.

---

## 10. CLI Patterns That Don't Suck

[`typer`](https://typer.tiangolo.com/) + [`rich`](https://rich.readthedocs.io/) gives you a tool people actually want to run:

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Demonstration scanner")
console = Console()

@app.command()
def scan(target: str, ports: str = "1-1024", json_out: bool = False) -> None:
    """Scan TARGET for open ports."""
    open_ports = [22, 80, 443]   # placeholder
    if json_out:
        import json
        console.print_json(data={"target": target, "open": open_ports})
        return
    table = Table(title=f"Open ports on {target}")
    table.add_column("Port", justify="right")
    table.add_column("Service")
    for p in open_ports:
        table.add_row(str(p), {22: "ssh", 80: "http", 443: "https"}.get(p, "?"))
    console.print(table)

if __name__ == "__main__":
    app()
```

---

## 11. Logging, Not `print`

```python
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
log = logging.getLogger("scanner")

log.info("starting scan against %s", "10.0.0.1")
log.warning("port %d filtered", 445)
log.debug("raw packet: %r", b"\x00...")
```

Levels matter: `DEBUG` for packet dumps, `INFO` for milestones, `WARNING` for unexpected-but-recoverable, `ERROR` for failures, `CRITICAL` for "tool exits now". Pipe through `jq` if you log JSON.

---

## 12. Safety, Errors, and Reproducibility

A few non-negotiables for tools you'll actually deploy:

- **Pin dependencies** in production (`uv lock` / `poetry.lock` / `pip-tools`).
- **Type-check** with `mypy --strict` once your codebase passes a few hundred lines.
- **Validate inputs** — `pydantic` for config, `ipaddress` for IPs, never `eval()`.
- **Never `shell=True`** in `subprocess` with user input. Pass a list:
  ```python
  subprocess.run(["nmap", "-sV", target], check=True, capture_output=True)
  ```
- **Time out everything** — every socket, every HTTP call, every subprocess.
- **Handle Ctrl-C** gracefully so partial results aren't lost.
- **Don't log secrets.** Sanitize tokens in error messages.

---

## 13. Worked Example — Async Port Scanner

We'll build a real tool you can drop into your toolbox: a concurrent port scanner with banner grabbing, JSON output, and configurable rate limiting.

The full source lives in `scripts/scanning/async_port_scanner.py`. Here is the architecture:

```mermaid
flowchart LR
    A[CLI: typer] --> B[Resolve target]
    B --> C[Build port list]
    C --> D[asyncio.Semaphore<br/>concurrency cap]
    D --> E[probe(host, port)]
    E --> F{open?}
    F -- yes --> G[banner_grab]
    F -- no  --> H[discard]
    G --> I[Result: port, service, banner]
    H --> J[Aggregate]
    I --> J
    J --> K[rich Table or JSON]
```

Highlights of the implementation:

- **`asyncio.open_connection`** for the TCP handshake — non-blocking, fast.
- **Semaphore-bounded concurrency** so you don't melt the kernel.
- **Banner grab** with a service-aware probe (HTTP `HEAD`, otherwise just read).
- **`typer` CLI**, **`rich` output**, **`--json`** for piping into other tools.
- **Graceful Ctrl-C** by catching `KeyboardInterrupt` at the top.

Run it:

```bash
python scripts/scanning/async_port_scanner.py scanme.nmap.org --ports 1-1024
python scripts/scanning/async_port_scanner.py 10.0.0.5 --ports 22,80,443,8080-8090 --json
```

Read the source. Tweak the concurrency. Add UDP. Add IPv6. **That's how you learn this craft.**

---

## 14. Ten Mini-Projects to Build

To go from "I read Python" to "I write security tools," build these. Each one is small (an evening), useful, and forces a different skill.

1. **Async port scanner** *(done — `scripts/scanning/async_port_scanner.py`)*
2. **Subdomain enumerator** via Certificate Transparency logs *(`scripts/recon/ct_subdomain_enum.py`)*
3. **ARP spoof detector** that watches a network for ARP-cache poisoning *(`scripts/recon/arp_spoof_detector.py`)*
4. **Hash identifier** that fingerprints common hash formats *(`scripts/crypto/hash_identifier.py`)*
5. **JWT analyzer** that decodes tokens, flags `alg:none`, weak HS256 keys *(`scripts/crypto/jwt_analyzer.py`)*
6. **Failed-SSH log analyzer** — parse `auth.log`, summarize attacker IPs/usernames *(`scripts/defense/failed_ssh_analyzer.py`)*
7. **IOC extractor** — pull IPs, domains, hashes, URLs from any text/PDF *(`scripts/defense/ioc_extractor.py`)*
8. **HTTP header auditor** — score targets on HSTS, CSP, X-Frame-Options, cookies
9. **Password-policy generator + dictionary mutator** — produce realistic wordlists from rules
10. **Mini honeypot** — listen on common ports, log probes, never respond

Build all ten and you'll have written more security Python than most junior analysts ship in their first year.

---

## 15. Reading Other People's Security Code

Some of the best Python you'll ever read:

- **`impacket`** — Windows protocol implementations (SMB/Kerberos/MS-RPC). Read `examples/` first.
- **`scapy`** — packet object model.
- **`mitmproxy`** — addons system, async TCP proxy.
- **`volatility3`** — memory-forensics plugin architecture.
- **`pwntools`** — exploit dev DSL.
- **`yara-python`**, **`capa`** — malware analysis.

Clone them. `grep -R "def "` them. Steal their patterns.

---

## 16. Interview & Practical Checks

You should be able to:

- Explain the difference between threads, processes, and asyncio.
- Implement a connection pool with concurrency limits using `asyncio.Semaphore`.
- Write a TCP banner grabber in <20 lines.
- Decode a JWT without using a third-party library (just `base64` + `json`).
- Read a packet capture programmatically with `scapy.rdpcap`.
- Pin TLS certificates in `httpx`.
- Avoid every common `subprocess` injection bug.

If any of those make you sweat, that's tonight's practice.

---

## 17. Further Reading

- *Black Hat Python* (2nd ed.), Justin Seitz & Tim Arnold — the canonical book.
- *Violent Python*, TJ O'Connor — older but pedagogically clean.
- [Real Python](https://realpython.com/) — solid general-purpose tutorials.
- [PEP 8](https://peps.python.org/pep-0008/) and [PEP 20](https://peps.python.org/pep-0020/) — style and philosophy.
- The `cpython` source itself; `Lib/asyncio/` is a masterclass.

---

> Phase 1 ends here. You now have **the prerequisites that every serious offensive or defensive role assumes you already have.** Phase 2 puts them to work — recon, OSINT, scanning, vulnerability assessment.

[← Cryptography](cryptography.md) · [Phase 2: Recon →](../02-recon/index.md)
