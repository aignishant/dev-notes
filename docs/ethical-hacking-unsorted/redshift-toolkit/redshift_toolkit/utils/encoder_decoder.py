"""
redshift_toolkit.utils.encoder_decoder
======================================

A Swiss-army-knife for every encoding you deal with on an engagement.

Supports
--------
    base64, base32, base16 (hex)     — standard RFC-4648 codecs
    url / url_all                    — percent-encoding
    hex                              — raw hex dump / undump
    rot / rotN                       — any Caesar shift (default 13)
    gzip                             — gzip + base64 in one step (common PS payload prep)
    xor                              — repeating-key XOR, hex or base64 output
    null / stripnull                 — handle wide-char / null-padded strings

Use as a library
----------------
    from redshift_toolkit.utils.encoder_decoder import b64, b64_decode
    b64("admin:admin")      # 'YWRtaW46YWRtaW4='
    b64_decode(b'YWRtaW46YWRtaW4=')  # b'admin:admin'

Use as a CLI
------------
    python -m redshift_toolkit.utils.encoder_decoder b64 encode "admin:admin"
    echo -n "YWRtaW46YWRtaW4=" | python -m redshift_toolkit.utils.encoder_decoder b64 decode
    rs-encode xor encode --key "S3cr3t" "payload data"
    rs-encode rot encode --n 13 "HELLO"
"""
from __future__ import annotations

import argparse
import base64
import codecs
import gzip
import sys
from typing import Callable
from urllib.parse import quote, quote_plus, unquote

__all__ = [
    "b64", "b64_decode", "b32", "b32_decode", "b16", "b16_decode",
    "urlenc", "urldec", "hex_encode", "hex_decode",
    "rot", "gzip_b64", "gzip_b64_decode", "xor_bytes",
]


# --- Primitive helpers --------------------------------------------------------

def _as_bytes(data: str | bytes) -> bytes:
    return data.encode() if isinstance(data, str) else data


def _as_str(data: bytes) -> str:
    return data.decode(errors="replace")


# --- Base-N --------------------------------------------------------------------

def b64(data: str | bytes) -> str:
    return base64.b64encode(_as_bytes(data)).decode()


def b64_decode(data: str | bytes) -> bytes:
    return base64.b64decode(_as_bytes(data))


def b32(data: str | bytes) -> str:
    return base64.b32encode(_as_bytes(data)).decode()


def b32_decode(data: str | bytes) -> bytes:
    return base64.b32decode(_as_bytes(data))


def b16(data: str | bytes) -> str:
    return base64.b16encode(_as_bytes(data)).decode()


def b16_decode(data: str | bytes) -> bytes:
    return base64.b16decode(_as_bytes(data), casefold=True)


# --- URL -----------------------------------------------------------------------

def urlenc(data: str, *, plus: bool = False, all_chars: bool = False) -> str:
    """URL-encode a string. `all_chars=True` encodes every byte (useful for WAF bypass)."""
    if all_chars:
        return "".join(f"%{b:02x}" for b in _as_bytes(data))
    return (quote_plus if plus else quote)(data, safe="")


def urldec(data: str) -> str:
    return unquote(data)


# --- Hex -----------------------------------------------------------------------

def hex_encode(data: str | bytes) -> str:
    return _as_bytes(data).hex()


def hex_decode(data: str | bytes) -> bytes:
    clean = _as_str(data) if isinstance(data, (bytes, bytearray)) else data
    clean = clean.replace(" ", "").replace("\n", "").replace(":", "")
    if clean.startswith(("0x", "0X")):
        clean = clean[2:]
    return bytes.fromhex(clean)


# --- Caesar / ROT ---------------------------------------------------------------

def rot(data: str, n: int = 13) -> str:
    """Caesar-shift alphabetic chars by N. Non-alpha pass through."""
    out = []
    for ch in data:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - ord("a") + n) % 26 + ord("a")))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - ord("A") + n) % 26 + ord("A")))
        else:
            out.append(ch)
    return "".join(out)


# --- Gzip + base64 (PS payload prep) -------------------------------------------

def gzip_b64(data: str | bytes) -> str:
    """Gzip-compress then base64. Common pattern for PowerShell payload delivery."""
    return base64.b64encode(gzip.compress(_as_bytes(data))).decode()


def gzip_b64_decode(data: str | bytes) -> bytes:
    return gzip.decompress(base64.b64decode(_as_bytes(data)))


# --- XOR -----------------------------------------------------------------------

def xor_bytes(data: str | bytes, key: str | bytes) -> bytes:
    """Repeating-key XOR. Returns raw bytes."""
    d = _as_bytes(data); k = _as_bytes(key)
    if not k:
        raise ValueError("XOR key cannot be empty")
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(d))


# --- CLI dispatch --------------------------------------------------------------

ENCODERS: dict[tuple[str, str], Callable[..., str | bytes]] = {
    ("b64", "encode"): lambda x, **_: b64(x),
    ("b64", "decode"): lambda x, **_: b64_decode(x),
    ("b32", "encode"): lambda x, **_: b32(x),
    ("b32", "decode"): lambda x, **_: b32_decode(x),
    ("b16", "encode"): lambda x, **_: b16(x),
    ("b16", "decode"): lambda x, **_: b16_decode(x),
    ("hex", "encode"): lambda x, **_: hex_encode(x),
    ("hex", "decode"): lambda x, **_: hex_decode(x),
    ("url", "encode"): lambda x, plus=False, all_chars=False, **_: urlenc(
        x if isinstance(x, str) else x.decode(), plus=plus, all_chars=all_chars),
    ("url", "decode"): lambda x, **_: urldec(
        x if isinstance(x, str) else x.decode()),
    ("rot", "encode"): lambda x, n=13, **_: rot(
        x if isinstance(x, str) else x.decode(), n),
    ("rot", "decode"): lambda x, n=13, **_: rot(
        x if isinstance(x, str) else x.decode(), -n),
    ("gzip", "encode"): lambda x, **_: gzip_b64(x),
    ("gzip", "decode"): lambda x, **_: gzip_b64_decode(x),
    ("xor", "encode"): lambda x, key, out="hex", **_: (
        hex_encode(xor_bytes(x, key)) if out == "hex" else b64(xor_bytes(x, key))),
    ("xor", "decode"): lambda x, key, _input="hex", **_: xor_bytes(
        hex_decode(x) if _input == "hex" else b64_decode(x), key),
}


def _read_input(data_arg: str | None) -> bytes:
    """Read from argv data, or stdin if data is None or '-'."""
    if data_arg is None or data_arg == "-":
        return sys.stdin.buffer.read().rstrip(b"\n")
    return data_arg.encode()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Encode / decode data in common offensive formats.",
        epilog="Data can be passed as argv or piped on stdin.",
    )
    p.add_argument("codec", choices=sorted({c for c, _ in ENCODERS}))
    p.add_argument("direction", choices=["encode", "decode"])
    p.add_argument("data", nargs="?", help="data (omit or '-' to read stdin)")
    p.add_argument("--key", help="XOR key (required for xor)")
    p.add_argument("--n", type=int, default=13, help="ROT shift amount")
    p.add_argument("--plus", action="store_true",
                   help="url: use '+' for spaces")
    p.add_argument("--all-chars", action="store_true",
                   help="url: encode every byte")
    p.add_argument("--out", choices=["hex", "b64"], default="hex",
                   help="xor encode output format")
    p.add_argument("--input", choices=["hex", "b64"], default="hex",
                   dest="input_format", help="xor decode input format")
    p.add_argument("--raw", action="store_true",
                   help="print decoded bytes as raw (no trailing newline)")
    args = p.parse_args()

    fn = ENCODERS.get((args.codec, args.direction))
    if fn is None:
        print(f"ERROR: unsupported: {args.codec} {args.direction}", file=sys.stderr)
        return 2

    data = _read_input(args.data)
    kwargs: dict = {}
    if args.codec == "xor":
        if not args.key:
            print("ERROR: --key required for xor", file=sys.stderr); return 2
        kwargs["key"] = args.key
        kwargs["out"] = args.out
        kwargs["_input"] = args.input_format
    if args.codec == "url":
        kwargs["plus"] = args.plus
        kwargs["all_chars"] = args.all_chars
    if args.codec == "rot":
        kwargs["n"] = args.n

    try:
        result = fn(data, **kwargs)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if isinstance(result, bytes):
        if args.raw:
            sys.stdout.buffer.write(result)
        else:
            sys.stdout.buffer.write(result + b"\n")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
