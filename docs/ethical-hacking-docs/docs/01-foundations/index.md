# 🧱 Phase 1 — Foundations

> The chapters most students skip and most professionals say "I wish I'd nailed earlier."

Six chapters. **Resist the urge to skim.** Every advanced technique later in this site assumes you understand what's here.

| # | Chapter | Why |
|---|---------|-----|
| 1 | [Cybersecurity Fundamentals](cybersecurity-fundamentals.md) | CIA triad, frameworks, ATT&CK, kill chains, vocabulary |
| 2 | [Networking](networking.md) | OSI, TCP/IP, protocols, subnetting, the math of every scan |
| 3 | [Linux](linux.md) | Filesystem, permissions, services, log files, the attacker's #1 OS |
| 4 | [Windows](windows.md) | NT internals, registry, PowerShell, Active Directory primer |
| 5 | [Cryptography](cryptography.md) | Symmetric, asymmetric, hashing, PKI, common misuse patterns |
| 6 | [Python for Security](python-for-security.md) | Sockets, requests, scapy, asyncio, the toolkit you'll build all of Phase 2/3 with |

## How to study this phase

This phase rewards **breadth + repetition** over depth. Don't try to memorize everything in one pass. Aim for:

1. **First pass (1 week):** read all six chapters, take light notes
2. **Second pass (2 weeks):** lab every command and run every Python snippet
3. **Third pass (ongoing):** spaced-repetition (Anki), come back when next phases reference these

You're done with Phase 1 when you can:

- Walk through a TCP three-way handshake with packet captures
- Subnet a `/16` into 16 equal subnets in your head
- Find SUID binaries and identify privesc-relevant ones on Linux
- List the top 5 Windows Event IDs you'd hunt on as a defender
- Explain why ECB mode is broken (with a picture)
- Write a Python async port scanner from scratch in 50 lines

→ Start: [Cybersecurity Fundamentals](cybersecurity-fundamentals.md)
