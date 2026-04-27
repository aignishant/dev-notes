# 07 · Cryptography for Offensive Operations

> *"Don't roll your own crypto" is advice for defenders. Attackers learn it inside out — because every meaningful breach in the last decade involved either a stolen credential, a forged token, a downgraded TLS connection, or a misused primitive.*

You are not learning cryptography to *build* it. You are learning it to **recognize when it is broken**, **understand what attacks each primitive enables**, and **read code well enough to tell a competent implementation from a vulnerable one**.

This module is dense. Read it once, then implement every example yourself before moving on. Crypto you can't implement is crypto you can't attack.

---

## 7.1 The Three Goals — Confidentiality, Integrity, Authenticity

| Goal | What it guarantees | Primitives that provide it |
|------|--------------------|----------------------------|
| **Confidentiality** | Adversary cannot read the plaintext | Symmetric ciphers (AES), asymmetric (RSA-OAEP, ECIES) |
| **Integrity** | Tampering is detected | Hashes (SHA-256), MACs (HMAC, AES-GMAC) |
| **Authenticity** | The message came from who you think | Signatures (RSA-PSS, ECDSA, Ed25519), MACs (with shared key) |

A common attacker insight: **systems that provide confidentiality without integrity are usually exploitable**. Padding oracles, bit-flipping, and CBC malleability all exist because someone encrypted without authenticating.

> Modern guidance: always use **authenticated encryption** (AES-GCM, ChaCha20-Poly1305). When you see plain CBC, CTR, or ECB in code, it's a *finding*.

---

## 7.2 Symmetric Cryptography

### Block ciphers and modes

A **block cipher** (AES) encrypts fixed-size blocks (128 bits). To encrypt larger messages, you use a **mode**:

| Mode | Properties | Use it? | Why it's broken |
|------|------------|---------|-----------------|
| **ECB** | Same plaintext block → same ciphertext block | **Never** | Patterns visible (the "ECB penguin"), trivial to detect |
| **CBC** | XOR with previous ciphertext | Only with HMAC | **Padding oracle**, bit-flipping, IV reuse leaks |
| **CTR** | Turns block cipher into stream cipher | Only with HMAC | Nonce reuse → catastrophic XOR-of-plaintexts |
| **GCM** | CTR + authentication (Galois MAC) | **Yes** | Nonce reuse still catastrophic, but otherwise safe |
| **ChaCha20-Poly1305** | Stream + Poly1305 MAC | **Yes** | Modern, fast on CPUs without AES-NI |

### The ECB penguin (visualizing the problem)

```
Plaintext:    [block A][block A][block A][block B]
                ECB:    ↓        ↓        ↓        ↓
Ciphertext:  [enc A] [enc A] [enc A] [enc B]
```

Same input block → same output block. Any structural repetition in plaintext — fixed headers, alignment padding, repeated user IDs — is visible in ciphertext. **ECB encrypts but does not hide.**

### CBC and the padding oracle

CBC encrypts each block as `C[i] = E(P[i] XOR C[i-1])`. The IV serves as `C[-1]`.

PKCS#7 padding: pad to block boundary with bytes equal to the pad length. A 5-byte short message gets `\x05\x05\x05\x05\x05` appended. Block-aligned messages get a full block of `\x10\x10...`.

**The vulnerability**: when an application decrypts a CBC ciphertext and *behaves differently* depending on whether the padding is valid (different error message, different timing, different HTTP code), an attacker can flip ciphertext bytes and observe whether the decrypted padding remained valid. By iterating, one byte of plaintext per ~256 queries falls. The entire ciphertext can be decrypted *without the key*.

This is the **padding oracle**. CVE-2002-0656 (OpenSSL), CVE-2010-3332 (ASP.NET — the famous one), POODLE (CVE-2014-3566 against SSL 3.0). We implement the attack in `padding_oracle.py` (toolkit module shipped with this part).

!!! danger "If you ever see plain CBC in production code"
    *Without HMAC-then-encrypt or encrypt-then-HMAC* — flag it as critical. It is decryptable end-to-end if any oracle exists, including timing differences in error returns.

### CTR mode and nonce reuse

CTR turns AES into a keystream generator: `keystream = E(K, nonce || counter)`, then `ciphertext = plaintext XOR keystream`.

If you ever encrypt two messages `P1` and `P2` with the same `(K, nonce)`:

```
C1 = P1 XOR keystream
C2 = P2 XOR keystream
C1 XOR C2 = P1 XOR P2     ← keystream cancels!
```

You now have the XOR of two plaintexts. Standard cribbing techniques (English-language frequency, known headers) recover both.

**This is how WEP fell.** It's how many embedded devices still fall. We attack it in the lab exercise.

### Stream ciphers in general

Stream ciphers (RC4, ChaCha20, the CTR mode of any block cipher) generate a keystream and XOR. **Nonce reuse always breaks them.** RC4 also has weak-key issues (plaintext recovery in TLS via `BEAST`/`Lucky 13` derivatives until RC4 was finally retired).

---

## 7.3 Hashing

### Properties of a cryptographic hash

| Property | What it means | When it matters |
|----------|---------------|-----------------|
| **Preimage resistance** | Given `h`, can't find `m` such that `H(m)=h` | Password storage |
| **Second-preimage resistance** | Given `m1`, can't find `m2 != m1` with same hash | Document signing |
| **Collision resistance** | Can't find any `m1 != m2` with same hash | Certificates, deduplication |

| Hash | Output | Status | Notes |
|------|--------|--------|-------|
| **MD5** | 128 | **Broken** | Collisions in seconds, still found in legacy systems and CTFs |
| **SHA-1** | 160 | **Broken** | SHAttered (2017) demonstrated practical collision |
| **SHA-256** | 256 | **OK** | Most widely used. SHA-2 family |
| **SHA-3** | variable | OK | Different construction (Keccak), not a SHA-2 replacement, just a backup |
| **BLAKE3** | variable | OK | Modern, very fast |

### Password hashing — different problem entirely

Passwords are *low-entropy* (humans), so a fast hash is a *vulnerability*. Use **slow, memory-hard** functions:

| Function | Year | Notes |
|----------|------|-------|
| **bcrypt** | 1999 | Still acceptable, but no GPU resistance |
| **scrypt** | 2009 | Memory-hard, GPU resistant |
| **Argon2id** | 2015 | OWASP recommended, modern |
| **PBKDF2** | 2000 | Acceptable with high iterations (≥600k SHA-256) — used in 1Password, KeePass, etc. |

**Things that aren't password hashes** but are commonly mistaken for them:
- `md5`, `sha1`, `sha256`, `sha512` (raw) — too fast, no salt, **always crackable**.
- `md5(salt + password)` — still too fast, salt only prevents rainbow tables.

### Length-extension attacks

`SHA-256(secret || message)` looks like a MAC. **It is not.** Anyone with `H(secret || message)` can compute `H(secret || message || padding || extension)` for arbitrary `extension`. This is **Merkle-Damgård length extension**, and it's why HMAC exists.

Use HMAC. Don't roll your own. We demonstrate the attack in `length_extension_demo.py`.

---

## 7.4 MACs and HMAC

A **MAC** (Message Authentication Code) gives integrity and authenticity with a *shared symmetric key*. HMAC is the standard construction:

```
HMAC(K, m) = H( (K ⊕ opad) || H( (K ⊕ ipad) || m ) )
```

Two nested hashes with two derived keys, immune to length extension.

**Common HMAC mistakes**:
- **Timing-unsafe comparison** — comparing HMACs with `==` leaks the position of the first differing byte. Use `hmac.compare_digest()` in Python, `crypto/subtle.ConstantTimeCompare` in Go, etc.
- **Key as plain string in code** — searchable with `git log -p`, `grep -r`, or `truffleHog`.
- **Same key for HMAC and encryption** — separate keys, period.

---

## 7.5 Asymmetric Cryptography

### RSA — the workhorse

Public key `(e, n)`. Private key `(d, n)`. Encryption: `c = m^e mod n`. Decryption: `m = c^d mod n`.

Common attacks worth memorizing:

- **Small `e` + no padding** — if `e=3` and `m^3 < n`, you can take cube root and recover `m`. *Implement once to internalize.*
- **PKCS#1 v1.5 padding oracle (Bleichenbacher 1998)** — TLS pre-master secret recovery. Variants resurface yearly (ROBOT 2017, hundreds of products).
- **Common modulus attack** — if two parties share `n` but use different `e`, anyone with both ciphertexts can recover plaintext (extended Euclidean algorithm).
- **Wiener's attack** — if private exponent `d` is small relative to `n`, continued fractions recover `d`.
- **Shared prime** — two RSA moduli that share a prime factor are both factorable via GCD. **Mass scanning of TLS keys finds this in the wild** (Heninger et al., 2012).

Modern RSA: **at least 2048 bits**, **always with OAEP padding** for encryption and **PSS** for signatures.

### Elliptic Curves (ECC)

Same operations (encryption, signature, key exchange) but on elliptic curves over finite fields. Smaller keys for equivalent security: 256-bit ECC ≈ 3072-bit RSA.

You will see:

- **secp256r1 / P-256** — NIST curve, ubiquitous in TLS.
- **secp256k1** — Bitcoin/Ethereum.
- **Curve25519** — Bernstein curve, in WireGuard, modern SSH.
- **Ed25519** — signatures on Curve25519. Default for new SSH keys.

Common ECC attack: **invalid curve attacks** (sending points not on the curve), **nonce reuse in ECDSA** (recovers private key — Sony PS3 fell to this).

### Diffie-Hellman key exchange

Both sides agree on a shared secret over an insecure channel. **Not authenticated by itself** — needs a signature on top, or pinned identities, or it's MITM-able.

Vulnerabilities:
- **Logjam** (CVE-2015-4000) — small/common DH parameters, broken offline.
- **Static DH parameters in firmware** — embedded vendors reuse the same `(p, g)` across millions of devices.

---

## 7.6 PKI and TLS

### Certificate chain in 10 seconds

```
Root CA (self-signed, in your trust store)
  └── Intermediate CA (signed by root)
       └── End-entity cert (signed by intermediate, contains the website's public key)
```

When you visit `https://example.com`:
1. Server sends its cert + intermediate.
2. Browser verifies intermediate is signed by a trusted root.
3. Browser verifies end-entity is signed by intermediate.
4. Browser verifies hostname in cert matches URL.
5. Browser verifies cert is not expired and not revoked (CRL/OCSP/CT).

Every step is a place attackers and defenders fight.

### TLS handshake (1.3, simplified)

```
Client                                                 Server
  | --- ClientHello (supported ciphers, key share) --> |
  |                                                    |
  | <-- ServerHello (chosen cipher, key share)         |
  | <-- Certificate                                    |
  | <-- CertificateVerify (signature)                  |
  | <-- Finished                                       |
  |                                                    |
  | --- Finished -------------------------------------> |
  |                                                    |
  | <======= encrypted application data =====>         |
```

TLS 1.3 dropped: RSA key exchange (forward-secrecy required), CBC modes, SHA-1, compression (CRIME), renegotiation (logjam variants), static DH.

### Common TLS attacks

| Attack | Year | What it does |
|--------|------|--------------|
| **BEAST** | 2011 | CBC IV predictability in TLS 1.0 |
| **CRIME** | 2012 | Compression-based cookie recovery |
| **Lucky 13** | 2013 | Timing on CBC MAC |
| **Heartbleed** | 2014 | OpenSSL out-of-bounds read leaking memory (CVE-2014-0160) |
| **POODLE** | 2014 | SSL 3.0 padding oracle |
| **FREAK** | 2015 | Forced RSA export-grade keys |
| **Logjam** | 2015 | DH parameter downgrade |
| **DROWN** | 2016 | SSLv2 cross-protocol attack |
| **ROBOT** | 2017 | Bleichenbacher resurfacing |
| **Raccoon** | 2020 | DH timing |

A configured TLS server today should support **only TLS 1.2+ and only AEAD ciphers**. Tools: `testssl.sh`, `nmap --script ssl-enum-ciphers`, `sslyze`.

---

## 7.7 JWT — Where Crypto Meets Web

JSON Web Tokens are signed (and sometimes encrypted) tokens used everywhere in modern auth. Format:

```
base64url(header) . base64url(payload) . base64url(signature)
```

Common attacks:

- **`alg: none`** — older libraries accepted unsigned tokens. Set the alg field, drop the signature, profit.
- **Algorithm confusion** — server expects RS256 (asymmetric), you submit HS256 (symmetric) using the public key as the HMAC secret. Many libraries verify with the wrong key type.
- **Weak HMAC secret** — `secret`, `changeme`, `<vendor>` — crackable in seconds with `jwt_tool.py`.
- **`kid` injection** — `kid` (key ID) parameter passed unsanitized to a database or filesystem; SQLi or path traversal yields a key the attacker controls.
- **JWKS spoofing** — `jku` or `x5u` header pointing at attacker-controlled URL.

We exploit all of these in `jwt_tool.py` (toolkit) with examples against a deliberately vulnerable lab server.

---

## 7.8 Random Number Generation

| Source | Quality | Use it for |
|--------|---------|------------|
| `random.random()` (Python) | **Predictable** — Mersenne Twister, recoverable from output | Games, simulations, *never crypto* |
| `numpy.random.*` | Same | Same |
| `os.urandom()` | Cryptographic (kernel CSPRNG) | Tokens, keys, salts |
| `secrets.token_bytes()` | Same as `os.urandom`, with nicer API | Same |
| `/dev/urandom` (Linux) | Cryptographic | Anything |
| `/dev/random` (Linux, old) | Cryptographic, blocking — **use `urandom`** | Don't use |

**Predictable RNG = catastrophic bugs**. Notable cases: Debian OpenSSL 2008 (only 32k possible keys generated for years), Cloudflare 2014 (predictable Apache cookies), countless CTF challenges.

If you see `Math.random()` generating session tokens in code review — that's a finding.

---

## 7.9 Detection / Blue-Team Angle

Crypto failures rarely show up as "alerts" — they show up as audit findings and code-review items. But several things are detectable:

- **Cleartext credentials in non-TLS traffic** — Zeek picks up plain HTTP basic auth, FTP USER/PASS, SMTP AUTH PLAIN.
- **TLS downgrade attempts** — Suricata signatures for SSL 3.0 / TLS 1.0 ClientHellos.
- **Certificate transparency monitoring** — alerts when *new* certs are issued for your domains (catches misissuance and phishing prep).
- **JWT brute-force** — repeated requests with similar tokens to login endpoints.
- **JA3 / JA4 fingerprinting** — TLS clients have characteristic ClientHello fingerprints. Cobalt Strike, Sliver, and stock `curl` are all distinguishable.

Sigma rule sketch:

```yaml
title: JWT alg=none token submitted
detection:
  selection:
    http.request.headers.authorization|contains: 'eyJhbGciOiJub25lIg'  # b64 of {"alg":"none"
  condition: selection
level: high
```

---

## 7.10 Industry Scenarios

### Healthcare — DICOM with no transport encryption

DICOM (medical imaging protocol) historically ships cleartext. Many hospital networks still run DICOM in cleartext on the LAN. Sniffing yields PHI: patient names, IDs, full-resolution medical images. *No crypto attack required — the crypto was simply absent.*

### Financial — JWT alg confusion against an internal API

Bank's internal microservice mesh uses RS256-signed JWTs from an identity provider. Test the API gateway: change `alg` to `HS256`, sign with the IdP's *public* key (extracted from JWKS endpoint). Many gateways accept both algs and verify HS256 using whatever key bytes are configured for RS256. Token forgery → arbitrary user impersonation → access to other accounts.

### Cloud / SaaS — predictable session tokens

A SaaS app's session tokens are 16 bytes of `Math.random()` output. Capture 100 valid tokens, recover the Mersenne Twister state, predict the next session token issued. Hijack arbitrary users.

### Government — legacy VPN with weak DH parameters

VPN concentrator running pre-2015 firmware. IKE SA negotiation accepts 768-bit DH (Group 1). Logjam-style offline computation breaks the key exchange. Real engagements still find this in air-gapped lab networks and old appliances.

---

## 7.11 Toolbelt

| Tool | Purpose |
|------|---------|
| **`hashcat`** | GPU password cracking. Master `--show`, `--rules`, `--increment`, `--attack-mode 6 (hybrid)` |
| **`john`** (John the Ripper) | CPU cracking, especially good for weird hash formats |
| **`openssl`** CLI | Inspect certs, generate keys, encrypt/decrypt, debug TLS |
| **`testssl.sh`** | TLS configuration audit (single script, comprehensive) |
| **`sslyze`** | Programmatic TLS scanner |
| **`jwt_tool`** | JWT manipulation — included in our toolkit |
| **`Cyberchef`** | "Cyber Swiss Army knife" for encoding/encryption transforms |
| **`hashid`** / **`hash-identifier`** | Identify hash type from format |
| **PyCryptodome** | Python crypto library for offensive scripts |
| **`cryptography`** (Python) | Higher-level Python crypto |
| **`pwntools`** | CTF crypto challenges, padding oracle helpers |

---

## 7.12 Scripts for This Module

Five scripts in `scripts/part-02/07-crypto/` and toolkit:

### 1. `aes_modes_demo.py` — see ECB break visually

Encrypts a tile-based bitmap with ECB and CBC, saves both as PNGs. The ECB output preserves visible patterns. **The famous "ECB penguin" demonstration.** Reproducible on any image.

### 2. `padding_oracle.py` *(toolkit)* — automated CBC oracle attack

Generic padding-oracle attacker. Plug in a target URL and a function describing what counts as "padding-valid response," and it decrypts arbitrary CBC ciphertext one byte at a time. Lands in `redshift_toolkit/utils/padding_oracle.py`.

### 3. `jwt_tool.py` *(toolkit)* — JWT swiss-army knife

Decode, modify, sign, verify, alg-confusion, brute-force HMAC secret, kid injection. Lands in `redshift_toolkit/utils/jwt_tool.py`. Replaces `pyjwt` for offensive work because we *want* to send invalid tokens.

### 4. `hash_identifier.py` *(toolkit)* — hash type detection + Hashcat mapping

Given a hash, identifies likely algorithm based on length, charset, and prefix; outputs Hashcat mode number for cracking. Lands in `redshift_toolkit/utils/hash_identifier.py`.

### 5. `length_extension_demo.py` — break naive `H(secret||msg)` MAC

Implements the SHA-256 length-extension attack from scratch. Demonstrates *why* HMAC exists. Educational, no real-world hash construction is built this way today, but you'll see it in CTFs and ancient code.

---

## 7.13 Lab Exercises

1. Run `aes_modes_demo.py` against a logo image. Compare the ECB and CBC outputs. **Look at them visually.** This is the kind of explanation you can give to a non-technical audit committee.
2. Stand up a deliberately vulnerable JWT lab service (script provided in repo). Use `jwt_tool.py` to:
   - Forge an admin token via `alg: none`.
   - Forge an admin token via algorithm confusion.
   - Brute-force a weak HMAC secret.
3. Implement `padding_oracle.py` against a local Flask app that decrypts a session cookie and returns 200 on valid padding, 500 on invalid. Decrypt the cookie. Time how long it takes.
4. Generate two RSA-2048 keypairs that share a prime factor (intentionally for the lab). Recover both private keys by computing GCD of the moduli.

---

## 7.14 Further Reading

- **Boneh & Shoup, *A Graduate Course in Applied Cryptography*** — free PDF, the gold standard.
- **Aumasson, *Serious Cryptography*** — readable, modern, attacker-aware.
- **The Cryptopals Challenges** (`https://cryptopals.com`) — 8 sets, 64 challenges. **If you finish set 4, you understand more crypto than 95% of practitioners.**
- **NIST SP 800-57** — key management guidance.
- **OWASP Cryptographic Storage Cheat Sheet** — what to recommend after you find issues.
- **Filippo Valsorda's blog** (`words.filippo.io`) — modern crypto commentary.
- **MITRE ATT&CK — T1552.004 Unsecured Credentials: Private Keys**, **T1606 Forge Web Credentials**, **T1557 Adversary-in-the-Middle**.

---

> Crypto is the layer where the difference between *senior* and *junior* practitioners is widest. Every hour you put in here pays dividends for the rest of your career. **Do Cryptopals set 1 this weekend.**

→ Next: [Module 08 · Protocols You Will Attack](08-protocols.md).
