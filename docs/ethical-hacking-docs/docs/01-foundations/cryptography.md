# 🔐 Cryptography

> Crypto is the math under every authentication, every TLS handshake, every signed binary, every blockchain. You don't need a PhD — but you need enough to read protocol specs, spot misuse, and answer interview questions confidently.

---

## 1. Goals & Vocabulary

Cryptography provides:

| Goal | Mechanism |
|---|---|
| **Confidentiality** | Encryption (symmetric + asymmetric) |
| **Integrity** | Hashes, MACs, signatures |
| **Authenticity** | MACs, signatures, certificates |
| **Non-repudiation** | Digital signatures |
| **Forward secrecy** | Ephemeral key exchange (DHE/ECDHE) |

Vocabulary:

- **Plaintext** — what you start with.
- **Ciphertext** — encrypted output.
- **Key** — the secret. Algorithm is public; key is what protects you.
- **IV / nonce** — fresh value per message; prevents identical plaintexts producing identical ciphertexts.
- **MAC** — Message Authentication Code; integrity + authenticity (with a shared key).
- **Signature** — like a MAC but with asymmetric keys (anyone can verify, only the signer can produce).
- **KDF** — Key Derivation Function (turns a password into a key).

> **Kerckhoffs's principle:** "A cryptosystem should be secure even if everything about the system, except the key, is public knowledge." Never trust crypto that depends on its algorithm being secret.

---

## 2. Symmetric Encryption

Same key encrypts and decrypts. Fast (GBs/sec on modern CPUs).

### Stream vs Block

- **Stream ciphers** — XOR plaintext with a keystream (RC4 ☠️, ChaCha20 ✅).
- **Block ciphers** — operate on fixed-size blocks (AES = 128-bit blocks).

### AES (Advanced Encryption Standard)

The standard. 128 / 192 / 256-bit keys. Block size 128 bits. Approved by NIST FIPS 197.

### Block cipher modes (this is where most mistakes happen)

| Mode | Properties | Use? |
|---|---|---|
| **ECB** (Electronic Codebook) | Same block → same ciphertext (insecure) | ❌ never |
| **CBC** (Cipher Block Chaining) | XOR with previous ct; needs IV | Legacy only |
| **CTR** (Counter) | Stream-like; needs nonce | OK with separate MAC |
| **GCM** (Galois/Counter Mode) | CTR + auth tag = AEAD | ✅ default for new |
| **CCM** | AEAD, used in IoT/Bluetooth | ✅ |
| **ChaCha20-Poly1305** | AEAD, software-friendly | ✅ |

### Why ECB is famous

ECB encrypts identical blocks identically. Encrypt a bitmap → patterns leak.

```
Plaintext bitmap (Tux penguin)        ECB ciphertext
█████░░░░░█████                       ▓▓▓▓▓░░░░░▓▓▓▓▓
██░██░░░██░██                         ▓▓░▓▓░░░▓▓░▓▓
░░███████░░                           ░░▓▓▓▓▓▓▓░░
```

You can still see Tux. **Never use ECB for real data.**

### AEAD (Authenticated Encryption with Associated Data)

Modern symmetric crypto = AEAD = encryption + authentication in one primitive.
Always pick **AES-256-GCM** or **ChaCha20-Poly1305** unless you have a very specific reason not to.

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)         # 96 bits, MUST be unique per (key, message)
ct = AESGCM(key).encrypt(nonce, b"my secret data", b"context-info")
pt = AESGCM(key).decrypt(nonce, ct, b"context-info")
```

!!! danger "Nonce reuse with GCM is catastrophic"
    Reusing a nonce with the same key in GCM leaks the authentication key. Always use random 96-bit nonces, or a strict counter.

---

## 3. Asymmetric (Public-Key) Cryptography

Two keys: a public key and a private key. Slow compared to symmetric (so we use it to negotiate symmetric keys).

### RSA

Based on the difficulty of factoring large integers.

- Key sizes: 2048 minimum, 3072+ recommended, 4096 common.
- Used for encryption (RSA-OAEP) or signing (RSA-PSS).
- **Don't use raw RSA / PKCS#1 v1.5 padding** in new code — padding oracle attacks (Bleichenbacher).

### Elliptic Curve Cryptography (ECC)

Same security with much smaller keys.

| Symmetric | RSA | ECC |
|---|---|---|
| 128 bits | 3072 bits | 256 bits |
| 256 bits | 15360 bits | 512 bits |

Modern curves: **Curve25519** (key exchange), **Ed25519** (signatures), **secp256r1 / P-256** (NIST).

### Diffie-Hellman & ECDH

A way for two parties to derive a shared secret over a public channel.

```
Alice picks a, sends g^a mod p
Bob picks b, sends g^b mod p
Both compute (g^a)^b = (g^b)^a = shared secret
```

ECDH is the same idea on elliptic curves. Used in TLS to negotiate the session key.

**Ephemeral DH (DHE / ECDHE)** = a fresh key exchange per session = **forward secrecy** (capturing today's traffic + tomorrow's server key still doesn't decrypt the past).

### Digital signatures

| Algorithm | Use |
|---|---|
| **RSA-PSS** | Modern RSA signatures |
| **ECDSA** | Elliptic-curve signatures (TLS, code signing) |
| **Ed25519** | Modern, fast, deterministic |

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

key = Ed25519PrivateKey.generate()
pub = key.public_key()

sig = key.sign(b"hello")
pub.verify(sig, b"hello")        # raises if invalid
```

---

## 4. Hash Functions

Take arbitrary input → fixed-size output. Properties:

- **Pre-image resistance** — given hash, can't find input.
- **Second pre-image resistance** — given input, can't find another with same hash.
- **Collision resistance** — can't find any two inputs with same hash.

| Hash | Output | Status |
|---|---|---|
| **MD5** | 128 | ☠️ broken (collisions) |
| **SHA-1** | 160 | ☠️ broken (SHAttered 2017) |
| **SHA-256 / 512** | 256 / 512 | ✅ |
| **SHA-3** | 224–512 | ✅ |
| **BLAKE2 / BLAKE3** | configurable | ✅ fast |

```python
import hashlib
print(hashlib.sha256(b"hello").hexdigest())
```

### Length-extension attack

SHA-1, SHA-256, SHA-512 are vulnerable to length-extension if used as `hash(secret + msg)` for MAC purposes. **Use HMAC instead.**

### MAC vs Hash

A hash alone doesn't authenticate (anyone can compute it). HMAC adds a key.

```python
import hmac, hashlib
mac = hmac.new(b"secret-key", b"message", hashlib.sha256).hexdigest()
```

---

## 5. Password Hashing (very different from regular hashing)

For passwords, you want **slow** hashes — to make brute force expensive.

| Algorithm | Notes |
|---|---|
| **bcrypt** | 1999. Still solid. Cost factor (work). 72-byte input limit. |
| **scrypt** | Memory-hard. |
| **Argon2id** | **Winner of PHC 2015. Use this for new systems.** |
| **PBKDF2** | OK if Argon2/bcrypt unavailable. NIST-approved. |

```python
import argon2
ph = argon2.PasswordHasher()
hash_ = ph.hash("CorrectHorseBatteryStaple")
ph.verify(hash_, "CorrectHorseBatteryStaple")    # True
```

!!! danger "Never store plain SHA-256 of a password"
    GPUs do >50 billion SHA-256 / sec. Use bcrypt / scrypt / Argon2id with a **per-user salt**.

### Salt vs Pepper

- **Salt** — per-user random value, stored with the hash. Prevents rainbow tables.
- **Pepper** — global secret, stored separately (HSM, env var). Adds defense if DB leaks but app secret doesn't.

---

## 6. Key Derivation Functions (KDF)

Turn a password / shared secret into a cryptographic key.

| KDF | Use |
|---|---|
| **PBKDF2** | Password → key, slow |
| **scrypt / Argon2** | Password, memory-hard |
| **HKDF** | High-entropy input (e.g., DH output) → multiple keys |

```python
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"v1 enc"
          ).derive(shared_dh_secret)
```

---

## 7. PKI — Public Key Infrastructure

The trust system around public keys. CA signs your cert; clients trust the CA's root.

### X.509 certificate structure

```
Subject:        CN=example.com, O=Acme, C=US
Subject Alt:    DNS:example.com, DNS:www.example.com
Issuer:         CN=Let's Encrypt R3
Validity:       Not Before / Not After
Public Key:     ECDSA P-256
Extensions:     Key Usage, EKU, SAN, CRL DP, AIA, SCT (CT logs)
Signature:      sha256WithRSAEncryption (CA's signature over the rest)
```

Read certs with `openssl`:

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null \
  | openssl x509 -text -noout
```

### Trust stores

- Browsers ship a CA bundle.
- OS bundles (Windows, macOS, Linux distros).
- Java has its own (`cacerts`).
- Go uses the OS by default.
- Python uses `certifi` by default.

### Certificate Transparency (CT)

All publicly-issued certs are logged in CT logs. Useful for OSINT — `crt.sh` lets you find every cert ever issued for a domain → subdomain enumeration goldmine.

### Revocation

- **CRL** (Certificate Revocation List) — signed list, downloaded periodically.
- **OCSP** — query the CA per cert.
- **OCSP stapling** — server fetches OCSP, attaches to handshake.

In practice, browsers rely heavily on **short-lived certs** (Let's Encrypt 90-day) and **CRLite/CRLSets** rather than per-cert OCSP.

### ACME / Let's Encrypt

ACME (RFC 8555) automates cert issuance. `certbot`, `acme.sh`, and `traefik`/`caddy` use it.

---

## 8. TLS in 60 Seconds (More in the Networking Chapter)

TLS 1.3 = faster + simpler + safer than 1.2. Always prefer 1.3.

Cipher in TLS 1.3 looks like `TLS_AES_256_GCM_SHA384`:

- AES-256-GCM (AEAD)
- SHA-384 (transcript hash + HKDF)
- Key exchange/auth are negotiated separately and are always (EC)DHE-based.

Test your server with:

```bash
testssl.sh https://example.com
sslyze --regular example.com
nmap --script ssl-enum-ciphers -p 443 example.com
```

---

## 9. Common Crypto Attacks (You Should Know These)

| Attack | What it does |
|---|---|
| **Padding oracle** (CBC) | Decrypt without the key by submitting ciphertexts and observing errors |
| **Bleichenbacher (PKCS#1 v1.5)** | RSA padding oracle |
| **BEAST / POODLE / CRIME / BREACH** | TLS-era attacks (mostly fixed) |
| **Length-extension** | Misuse of SHA-256 as MAC |
| **Hash collisions** | MD5/SHA-1 can be forced to collide |
| **Replay attacks** | Capture & resend valid messages (defeated by nonces, timestamps) |
| **Side-channel** | Timing, power, EM, cache (Spectre/Meltdown family) |
| **Downgrade** | Force a peer to use a weaker version (TLS_FALLBACK_SCSV mitigates) |
| **Nonce reuse** | Catastrophic in GCM, ChaCha20-Poly1305 |
| **Weak RNG** | Predictable keys → e.g., Debian OpenSSL 2008 |
| **Key reuse across protocols** | Same key for sign + encrypt → cross-protocol attacks |

---

## 10. JWT — JSON Web Tokens (commonly broken)

JWT is the most-attacked crypto format on the web. Anatomy:

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NSIsImV4cCI6MTcwMDAwMDAwMH0.signature
└── header (b64url) ──┘└──── payload (b64url) ────┘└─── signature ───┘
```

### Common JWT bugs

1. **`alg: none`** — server accepts unsigned tokens.
2. **`alg` confusion** — server expects RS256, attacker submits HS256 with the public key as the HMAC secret.
3. **Weak HMAC secret** — crackable with `hashcat -m 16500`.
4. **Missing `exp` validation**.
5. **`kid`/`jku`/`x5u` injection** — pointed at attacker server.
6. **Mutable claims** — server trusts `role: admin` from the client.

Use the `scripts/crypto/jwt_analyzer.py` tool we ship in this curriculum to triage JWTs you find.

```bash
python scripts/crypto/jwt_analyzer.py "eyJhbGciOi..."
```

Defense: pin the algorithm server-side, enforce `exp`/`nbf`/`iss`/`aud`, rotate keys, never accept `none`.

---

## 11. Quantum & Post-Quantum (where this is going)

Shor's algorithm (on a sufficiently large quantum computer) breaks RSA, DH, and ECC. Symmetric crypto is mostly fine (double the key size).

NIST has standardized post-quantum algorithms:

- **ML-KEM** (Kyber) — key encapsulation (FIPS 203)
- **ML-DSA** (Dilithium) — signatures (FIPS 204)
- **SLH-DSA** (SPHINCS+) — stateless hash-based signatures (FIPS 205)
- **HQC**, **Falcon** — alternates

Hybrid TLS (X25519 + ML-KEM) is being deployed by Cloudflare, Google, Apple. Watch this space.

**Today** what you should do: prepare for crypto agility. Keep crypto out of business logic; behind interfaces.

---

## 12. Hands-On

### Use real primitives

```python
# Encrypt a file with AES-256-GCM
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, sys, pathlib

path = pathlib.Path(sys.argv[1])
key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
ct = AESGCM(key).encrypt(nonce, path.read_bytes(), None)
path.with_suffix(path.suffix + ".enc").write_bytes(nonce + ct)
print("key:", key.hex())
```

### Identify a hash

Run our `scripts/crypto/hash_identifier.py`:

```bash
python scripts/crypto/hash_identifier.py 5f4dcc3b5aa765d61d8327deb882cf99
# → MD5 (5f4dcc3b... = "password")
```

### Inspect a TLS cert

```bash
echo | openssl s_client -connect github.com:443 -servername github.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

### Crack a weak JWT (lab)

Run on a JWT you minted yourself:

```bash
hashcat -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
```

---

## 13. Interview Questions

1. Difference between encryption, hashing, and encoding.
2. Why is ECB mode broken? Show how with a picture.
3. Walk through a TLS 1.3 handshake. Why is it faster than 1.2?
4. What's the difference between bcrypt and SHA-256 for passwords?
5. Explain the difference between a digital signature and a MAC.
6. What is forward secrecy? Why does it matter?
7. Why is Argon2id preferred over bcrypt today?
8. What is `alg: none` JWT and how do you defend?
9. Why is nonce reuse a catastrophic problem in AES-GCM?
10. What does HKDF do that simple SHA-256 doesn't?

---

## 📚 Further Reading

- **Cryptography Engineering** — Ferguson, Schneier, Kohno. The textbook.
- **Serious Cryptography (2nd ed.)** — JP Aumasson. Modern.
- **Real-World Cryptography** — David Wong.
- **Cryptopals challenges** — <https://cryptopals.com> — implement attacks. Best learning tool out there.
- **NIST SP 800-57** — key management recommendations.
- **OWASP Cheat Sheets** — Cryptographic Storage, Password Storage, JWT, Transport Layer Protection.
- **`cryptography` docs** — <https://cryptography.io>

---

## ✅ Phase 1 — Complete!

You now have the fundamentals. You can:

- ✅ Reason about CIA, AAA, kill chain, ATT&CK
- ✅ Read a Wireshark capture and explain it
- ✅ Operate Linux at the level expected of a junior pentester
- ✅ Operate Windows at the level expected of a SOC analyst
- ✅ Build security tooling in Python
- ✅ Pick the right crypto for the job and spot common misuse

Time to apply it. Continue to [Phase 2 — Recon & Assessment →](../02-recon/index.md).
