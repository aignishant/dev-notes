# Part 2 · Networking & Cryptography for Hackers

> *"Every offensive technique you will ever learn is, underneath, packets crossing a wire and bytes being transformed. If you do not understand both, you are running other people's tools and praying."*

Part 1 made you legally and operationally safe to learn. **Part 2 makes you dangerous on the wire.**

This part is the most foundational technical block in the curriculum. Web hacking, AD attacks, C2, evasion — every later technique reduces to either *packets crossing the network* or *cryptographic primitives being misused*. If you can read a packet capture and reason about a TLS handshake, you have a permanent edge over operators who memorize tools.

## Why these three modules together

| Module | What it teaches | What you can do after |
|--------|-----------------|------------------------|
| **06 · Networking deep dive** | OSI vs TCP/IP, switching, routing, VLANs, sockets, raw frames, TCP state, NAT, IPv6 | Read any pcap, craft any packet, explain every netstat line, reason about why a payload reached the box. |
| **07 · Cryptography for offensive ops** | Symmetric/asymmetric, hashing, HMAC, PKI, TLS, common failure modes, padding oracles, nonce reuse, downgrade | Spot crypto failures in code review and on the wire, attack tokens, attack TLS, attack hashed creds. |
| **08 · Protocols you will attack** | HTTP(S), DNS, SMB/CIFS, LDAP/Kerberos, RDP, SSH, SMTP, SNMP — wire format and abuse surface | Recognize a Kerberos ticket, fingerprint SMB dialects, talk SMTP by hand, abuse SNMP for intel. |

## Learning outcomes

By the end of Part 2 you will be able to:

- Trace a packet from your laptop's NIC to a remote server's process and back, naming every layer it traverses.
- Write a raw TCP scanner from `socket()` upward without a library.
- Sniff your own LAN with Scapy, filter with BPF, and explain every byte of an Ethernet frame.
- Implement AES-CBC encryption *and* break it via padding oracle.
- Forge and crack JWTs (alg confusion, weak HMAC keys).
- Decode a Kerberos AS-REQ/AS-REP exchange field by field.
- Talk SMTP, SMB, LDAP, and SNMP by hand with `nc`, `ldapsearch`, `snmpwalk`, and your own Python clients.
- Recognize and exploit at least 6 classic crypto-misuse patterns in the wild.

## Toolkit additions in Part 2

By the end of this part your `redshift-toolkit` package will gain:

- `net/packet_sniffer.py` — async Scapy sniffer with BPF filters and live decode.
- `net/network_mapper.py` — passive host discovery from packet capture or live interface.
- `net/tcp_state_visualizer.py` — narrate TCP handshakes and teardowns from pcap.
- `net/raw_socket_scanner.py` — pure-stdlib raw TCP-connect scanner.
- `utils/crypto_helpers.py` — symmetric/asymmetric primitives, HMAC, KDFs.
- `utils/padding_oracle.py` — generic CBC padding oracle attacker.
- `utils/jwt_tool.py` — decode, forge, crack, alg-confusion JWTs.
- `utils/hash_identifier.py` — auto-ID hash type + Hashcat mode mapping.
- `protocols/dns_client.py` — raw DNS query/response builder.
- `protocols/smb_recon.py` — SMB version + share + signing enumeration.
- `protocols/ldap_recon.py` — anonymous + authenticated LDAP enum.
- `protocols/smtp_recon.py` — VRFY/EXPN/RCPT user enumeration.
- `protocols/snmp_walker.py` — community-string brute + walk.

## Prerequisites checklist

Before starting Part 2, confirm:

- [ ] Part 1 lab is up. Kali + at least DC01 + WS01 reachable from your VM host.
- [ ] You can run `tcpdump -i any` and see traffic on Kali.
- [ ] You ran the full `linux_enum.py` and `windows_enum_wmi.py` from Part 1 against your lab.
- [ ] Wireshark installed on Kali (`apt install wireshark`).
- [ ] Python 3.11+ and `pip install -r requirements.txt` from the project root.

## How to use Part 2

Networking is the one part of this curriculum where **you must read pcaps**, not just text. Every module has a "capture this, then read it in Wireshark" exercise. Don't skip them. The reps build pattern recognition that no amount of reading replaces.

The crypto module has a similar discipline: **type the math**. Don't just read about CBC padding — implement encrypt and decrypt yourself before attacking. Cryptography that you can't implement, you can't attack.

---

→ Start with [Module 06 · Networking deep dive](06-networking.md).
