# 06 · Networking Deep Dive for Hackers

> *Networks are not magic. Every byte you ever exfiltrate is a TCP segment, in an IP packet, in an Ethernet frame, on a wire or radio, going through routers that you can predict and switches that you can fool.*

This is the single highest-leverage module in the entire curriculum. Master networking and you understand *why* every later technique works. Skim it and every subsequent module will feel like memorization.

We are going to walk top-down through the stack you will actually use, then bottom-up through the attacks each layer enables. Along the way you will write a TCP scanner from raw sockets, sniff your own LAN, decode TCP handshakes, and craft packets with Scapy.

---

## 6.1 The Two Models: OSI vs TCP/IP

Vendors and academics teach **OSI**. The internet runs on **TCP/IP**. You need both because exam questions, vendor docs, and tcpdump output all mix them.

### Layer-by-layer comparison

| OSI # | OSI name | TCP/IP name | What lives here | What you'll see in tcpdump |
|-------|----------|-------------|-----------------|----------------------------|
| 7 | Application | Application | HTTP, DNS, SMB, SSH, SMTP, LDAP | URLs, queries, payloads |
| 6 | Presentation | Application | TLS, ASN.1 encoding, MIME | Cert chains, content-type |
| 5 | Session | Application | RPC, NetBIOS, sockets | Session IDs, RPC calls |
| 4 | Transport | Transport | TCP, UDP, QUIC, SCTP | Ports, flags (`S`, `S.`, `F.`, `R`) |
| 3 | Network | Internet | IPv4, IPv6, ICMP, IPsec | IP addresses, TTL, fragmentation |
| 2 | Data Link | Link | Ethernet, ARP, Wi-Fi (802.11), VLAN tags | MAC addresses, frame types |
| 1 | Physical | Link | Copper, fiber, radio, modulation | Not visible in tcpdump |

### Mental model

Think of the stack as **nesting envelopes**. Your HTTP request is a letter. TLS wraps it in a sealed envelope. TCP puts that envelope into a labeled package with a sequence number. IP labels the package with source and destination addresses. Ethernet drops it onto a truck heading to the next intersection. The truck (frame) only goes one hop; at every router the frame is unwrapped and rewrapped.

This nesting is why a packet capture looks layered: scrolling top-down through Wireshark fields *is* peeling the envelopes.

!!! tip "SOAR-engineer translation"
    You already think in playbooks: trigger → enrich → action → ticket. Networking is the same — *every* upper-layer action is the result of a lower-layer event. When a malicious payload reaches an EDR, you can trace it backward: app → TLS → TCP segment → IP packet → MAC frame → physical port. Forensics and packet analysis are the same skill.

---

## 6.2 Layer 2 — Ethernet, ARP, and Switches

### Ethernet frame anatomy

```
+-----------+--------------+-----------+----------+----------+--------+
| Preamble  | Dest MAC (6) | Src MAC (6)| EtherType| Payload  |  CRC   |
| 8 bytes   |              |           | (2)      | 46-1500  |  (4)   |
+-----------+--------------+-----------+----------+----------+--------+
```

`EtherType` tells the receiver what's inside: `0x0800` = IPv4, `0x0806` = ARP, `0x86DD` = IPv6, `0x8100` = VLAN-tagged.

### MAC addresses

48 bits, usually written `aa:bb:cc:dd:ee:ff`. First 24 bits = OUI (vendor). You can look up `00:50:56` and instantly know it's VMware. `52:54:00` = QEMU. This is **passive fingerprinting** — useful during recon and incident response.

### ARP — the trust nobody questions

ARP resolves IP → MAC inside a broadcast domain. There is **no authentication**. Anyone on the LAN can answer "I am that IP" and the asker will believe them. This is why ARP spoofing remains the entry point for half of LAN MITM attacks 30+ years after Ethernet shipped.

```
Host A: "Who has 10.0.0.1? Tell 10.0.0.5"          (ARP request, broadcast)
Host B: "10.0.0.1 is at 00:1c:42:11:22:33"          (ARP reply, unicast)
Attacker: "10.0.0.1 is at 00:de:ad:be:ef:00"        (ARP reply, unsolicited!)
```

The attacker's reply is **unsolicited and unauthenticated**, but everyone updates their ARP table. Now traffic to the gateway flows through the attacker.

### Switch behavior and CAM tables

Switches learn MAC → port mappings into a **CAM table**. They forward frames only to the port owning the destination MAC. **CAM overflow** — flooding a switch with thousands of bogus source MACs — fills the table; switches then fall back to broadcasting every frame to every port (turning the switch into a hub). This is `macof` from `dsniff`.

### VLANs and tagging

VLANs tag frames with a 12-bit VLAN ID (4094 usable). A switch port is either:
- **Access port** — untagged, in one VLAN.
- **Trunk port** — accepts tagged frames from multiple VLANs.

**VLAN hopping** — `switch spoofing` (DTP abuse) and `double tagging` — abuses misconfigured trunks. Modern enterprises mostly disable DTP, but you'll still find VLAN-hopping opportunities in aging environments and ICS networks.

!!! warning "ICS/SCADA reality"
    Industrial networks are notorious for flat L2 domains, default trunk configs, and unsegmented engineering workstations. Volt Typhoon-style intrusions repeatedly exploit this — once you're on any port in the OT VLAN, you can typically see the entire process network.

---

## 6.3 Layer 3 — IP, ICMP, Routing

### IPv4 header (the parts you'll touch)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Fields you'll lean on as an attacker:

- **TTL** — decremented by every router. Default 64 (Linux), 128 (Windows), 255 (network gear). Use this for **passive OS fingerprinting** — if a packet arrives with TTL=63 or 62, the source set TTL=64 originally, so it's likely Linux.
- **Identification + Flags + Fragment Offset** — used for **IP fragmentation**. Some IDS/firewalls handle reassembly badly, enabling evasion.
- **Protocol** — `1`=ICMP, `6`=TCP, `17`=UDP, `47`=GRE, `50`=ESP (IPsec), `132`=SCTP.

### ICMP — the protocol that knows everything

ICMP isn't just `ping`. It's how networks tell each other things are broken:

| Type | Name | What it means |
|------|------|---------------|
| 0/8 | Echo Reply / Echo Request | Ping |
| 3 | Destination Unreachable | "Can't get there" — has subcodes for *port unreachable*, *host unreachable*, *fragmentation needed* |
| 5 | Redirect | "Use this gateway instead" — historic MITM vector |
| 11 | Time Exceeded | TTL hit zero — **this is how traceroute works** |
| 13/14 | Timestamp Request/Reply | Disclosure vector, sometimes used in covert channels |

**ICMP exfiltration** — embed data in `ICMP echo` payloads. Many networks allow ICMP outbound without inspection. Tools: `iodine`-style implementations, your own Scapy script.

### Routing in 60 seconds

Every host has a routing table. `ip route` (Linux) or `route print` (Windows) shows it. The host picks the **most-specific** matching prefix:

```
$ ip route
default via 10.0.0.1 dev eth0
10.0.0.0/24 dev eth0 proto kernel scope link
192.168.50.0/24 via 10.0.0.7 dev eth0
```

That host: traffic to `192.168.50.0/24` goes through `10.0.0.7`. Traffic to anything else goes through `10.0.0.1`. **`10.0.0.7`** is interesting — it's a static route to another network, suggesting a multi-homed host. *On a real engagement, this is your pivot point.*

### NAT and what it hides

Most internal networks live behind NAT. Source NAT rewrites your private source IP into a public one when leaving. The NAT device tracks state (5-tuple): `(src IP, src port, dst IP, dst port, proto)`. Inbound packets matching active state get rewritten and forwarded.

**For attackers**: outbound connections from inside a NATed network typically work; inbound connections to specific high ports do not, unless port-forwarding is configured. This is why C2 frameworks always favor *outbound* beaconing.

---

## 6.4 Layer 4 — TCP and UDP

### TCP — the state machine you must internalize

```
                 +---------+         +---------+
                 |  CLOSED |<--------|  LISTEN | ←  server starts
                 +---------+         +---------+
                      |                   |
            (active)  | SYN              | SYN
                      v                   v
                 +---------+         +---------+
                 |   SYN   |         |   SYN   |
                 |   SENT  |         |   RCVD  |
                 +---------+         +---------+
                      |                   |
            SYN+ACK   |                   | ACK
                      v                   v
                 +---------+   ACK   +---------+
                 |  ESTAB  |<------->|  ESTAB  |  ←  data flows
                 +---------+         +---------+
                      |                   |
                 (FIN/RST teardown)
```

### The flags every hacker memorizes

```
SYN — start a connection
ACK — acknowledging received data
FIN — graceful close
RST — abrupt close ("go away")
PSH — push data to application immediately
URG — urgent data (rarely used)
```

### Scan types you must know

| Scan | Sends | Open response | Closed response | Why use it |
|------|-------|---------------|-----------------|------------|
| **Connect (`-sT`)** | full 3-way handshake | handshake completes | RST | Always works, no privileges, *very loud* |
| **SYN / half-open (`-sS`)** | SYN | SYN+ACK (then we send RST) | RST | Default, fast, requires raw sockets/root |
| **FIN / NULL / Xmas (`-sF/-sN/-sX`)** | FIN / nothing / FIN+PSH+URG | (nothing) | RST | RFC says closed = RST, open = nothing. Bypasses some old stateless filters. Doesn't work on Windows. |
| **ACK (`-sA`)** | ACK | RST (if reachable) | — | Maps firewall rules — does NOT determine open/closed, but tells you whether traffic is filtered. |
| **UDP (`-sU`)** | UDP packet | (often nothing — assumed open) | ICMP port unreachable | Slow, unreliable, but UDP services exist (DNS, SNMP, NetBIOS, NFS). |

### TCP sequence numbers and why they matter

Every TCP byte has a sequence number. The sender picks an **ISN (Initial Sequence Number)** for the SYN. Modern stacks randomize ISNs; older ones (and many embedded/IoT devices) generate predictable ISNs, enabling **TCP injection** attacks.

For testing: `nmap --osscan-limit -O target` reports ISN predictability. If you see `Difficulty=0 (Trivial joke)`, you've found a device vulnerable to RFC-793-era attacks.

---

## 6.5 Sockets — How Programs Touch the Network

A **socket** is an OS abstraction over a network endpoint. Every TCP connection is a 5-tuple bound to two sockets (one each side):

```
(protocol, local IP, local port, remote IP, remote port)
```

### Socket lifecycle (server)

```python
sock = socket.socket(AF_INET, SOCK_STREAM)   # create
sock.bind(('0.0.0.0', 4444))                 # claim address+port
sock.listen(5)                               # mark as listener (backlog=5)
client, addr = sock.accept()                 # block until incoming SYN+handshake
data = client.recv(4096)                     # read
client.send(b'pong\n')                       # write
client.close()                               # FIN
```

### Socket lifecycle (client)

```python
sock = socket.socket(AF_INET, SOCK_STREAM)
sock.connect(('10.0.0.1', 22))               # full 3-way handshake
banner = sock.recv(1024)                     # read SSH banner
sock.close()
```

### Socket types

| AF | Description | Used for |
|----|-------------|----------|
| `AF_INET` | IPv4 | Most code |
| `AF_INET6` | IPv6 | Modern dual-stack |
| `AF_UNIX` | Unix domain | Local IPC, Docker socket abuse |
| `AF_PACKET` | Raw L2 (Linux) | Sniffing, packet crafting |

| Type | Description |
|------|-------------|
| `SOCK_STREAM` | TCP |
| `SOCK_DGRAM` | UDP |
| `SOCK_RAW` | Raw IP — needs CAP_NET_RAW or root |

You will write code in all of these by Part 5.

---

## 6.6 IPv6 — Already Here

Most enterprises have IPv6 enabled by default on Windows and Linux but never configured monitoring for it. This makes IPv6 a stealth channel.

Key facts:

- **128-bit addresses**, written `2001:db8::1`. The `::` collapses one run of zero groups.
- **Link-local addresses** (`fe80::/10`) auto-configured on every interface, no DHCP needed.
- **Neighbor Discovery (ND)** replaces ARP — also unauthenticated, also spoofable.
- **SLAAC** (Stateless Address Autoconfiguration) lets hosts pick their own addresses.
- **Router Advertisements (RAs)** — anyone can send one. **mitm6** abuses this to become the IPv6 default gateway for Windows hosts on a network where IPv6 is "off but actually on."

If your lab DC and workstation are stock, mitm6 + ntlmrelayx will own them. We'll do this exercise in Module 21.

---

## 6.7 Real-World Recon: Reading a tcpdump

Here is a real `tcpdump -nn -i any` line. Decode every field:

```
14:32:05.123456 IP 10.0.0.5.51234 > 10.0.0.10.443: Flags [S], seq 3829405, win 65535, options [mss 1460,sackOK,TS val 1234567 ecr 0,nop,wscale 7], length 0
```

Reading it:

- `14:32:05.123456` — timestamp.
- `IP` — Layer 3 protocol.
- `10.0.0.5.51234 > 10.0.0.10.443` — source `:port` to dest `:port`. Port 443 = HTTPS.
- `Flags [S]` — TCP flags. `[S]`=SYN, `[S.]`=SYN+ACK, `[.]`=ACK, `[F.]`=FIN+ACK, `[R.]`=RST+ACK, `[P.]`=PSH+ACK.
- `seq 3829405` — initial sequence number (ISN).
- `win 65535` — window size.
- `options [mss 1460,sackOK,TS val 1234567 ecr 0,nop,wscale 7]` — TCP options. *MSS=1460* is classic Ethernet (1500 - 20 IP - 20 TCP). *wscale=7* means window scaling factor of 128.
- `length 0` — no payload (this is just a SYN).

**Use this as fingerprinting**: TCP options ordering and values (`MSS`, `WindowScale`, `SACK`, `Timestamps`, `NOP`) form a **p0f signature**. Linux/Windows/macOS have different default option sets, so you can identify a host's OS just from its SYN packet. This is `p0f`'s entire premise.

---

## 6.8 Lab Exercise — Capture, Decode, Reproduce

Run all three of these on your Kali VM with traffic flowing to your DC01.

### Exercise 1: Capture a TCP handshake

```bash
# Terminal 1
sudo tcpdump -i eth0 -nn -w handshake.pcap host 10.0.0.10 and port 445

# Terminal 2
nc -zv 10.0.0.10 445

# Terminal 1: stop with Ctrl-C, then
wireshark handshake.pcap
```

Open in Wireshark. Right-click the SYN → **Follow → TCP Stream**. You should see exactly 3 packets if the port was open, or SYN + RST if closed.

### Exercise 2: Sniff your own DNS query

```bash
sudo tcpdump -i any -nn -X port 53 &
nslookup example.com
```

Read the hex dump. Identify the query ID, the QNAME (length-prefixed labels), the QTYPE (1=A, 28=AAAA), and the response RDATA. We rebuild this byte for byte in Module 08.

### Exercise 3: Detect ARP spoofing on your own LAN

Run the included `arp_watcher.py` (provided as the script for this module — see below). On a separate VM, run `arpspoof` against your gateway. Watch the watcher detect the duplicate MAC binding.

---

## 6.9 Industry Scenarios

### Financial — internal MITM during a black-box engagement

You're internal at a regional bank. The terminal-services subnet uses static ARP **but** the management subnet does not. ARP spoof a sysadmin's workstation, capture their RDP credentials (NTLMv2 hash), relay to ESXi management, get hypervisor admin. *Real engagement pattern, common in retail and regional banks.*

### Healthcare — pivoting through unsegmented L2

Hospital networks routinely have HL7 / DICOM endpoints in the same broadcast domain as guest Wi-Fi. After landing on a guest Wi-Fi laptop, ARP scan reveals medical-device IPs. Many use cleartext FTP for image transfer. *Patient PHI exfiltrated without ever touching a "real" server.*

### ICS — engineering workstation as kingdom keys

Modbus, DNP3, and S7 protocols don't authenticate. If you can sniff and inject on the OT segment, you can read process state and forge commands. We'll attack these in Part 10. The networking job here is identifying *which port on the engineering workstation peers with the PLC* — invariably a flat L2 segment makes this trivial.

### Cloud — VPC peering as an exfil path

In AWS/Azure/GCP, VPC peering (or VNet peering) creates direct L3 connectivity between accounts/subscriptions. Compromise one workload in a "lower-trust" environment, the peering relationship lets you scan into "higher-trust" environments. Cloud security review checklists routinely miss east-west peering.

---

## 6.10 Detection / Blue-Team Angle

Networking attacks are *visible* if anyone is looking. The blue team should:

- **Static ARP** on critical subnets (servers, ICS).
- **DHCP snooping + Dynamic ARP Inspection** on switches — drops gratuitous ARPs from untrusted ports.
- **802.1X port authentication** so unauthorized devices can't even get an IP.
- **NetFlow / IPFIX** export from routers — every connection logged at flow level.
- **Zeek (formerly Bro)** for protocol parsing on a SPAN port.
- **mitm6 detection** — alert on unexpected DHCPv6 servers and rogue RAs.

Sigma rule sketch (network logs):

```yaml
title: Suspicious ARP gratuitous reply
detection:
  selection:
    event_type: arp
    operation: reply
    target_ip: <gateway_ip>
  condition: selection and not src_mac in known_gateway_macs
level: high
```

---

## 6.11 Toolbelt

| Tool | Purpose | One-liner |
|------|---------|-----------|
| `tcpdump` | CLI packet capture | `tcpdump -nn -i any -w cap.pcap host X and port Y` |
| `Wireshark` / `tshark` | GUI / scriptable analysis | `tshark -r cap.pcap -Y 'tcp.flags.syn==1 && tcp.flags.ack==0'` |
| `nmap` | Port scanning, OS detect | `nmap -sS -sV -O -T4 10.0.0.0/24` |
| `Scapy` (Python) | Craft any packet | See `arp_watcher.py` and `tcp_state_visualizer.py` |
| `netcat` (`nc` / `ncat`) | Banner grab, listener, port test | `nc -zv host port` |
| `hping3` | Custom-flag TCP/UDP/ICMP | `hping3 -S -p 443 host` |
| `arp-scan` | LAN discovery | `arp-scan -l` |
| `responder` | LLMNR/NBT-NS/mDNS poisoning | `responder -I eth0` |
| `mitm6` | IPv6 SLAAC abuse | `mitm6 -i eth0 -d corp.local` |
| `bettercap` | All-in-one MITM toolkit | `bettercap -iface eth0` |

---

## 6.12 Scripts for This Module

Five scripts, each a different facet of network mastery. All in `scripts/part-02/06-networking/`.

### 1. `raw_socket_scanner.py` — TCP scanner from scratch

Pure stdlib. No `nmap`, no `scapy`. Just `socket`, `select`, `asyncio`. Proves you understand sockets at the OS level.

### 2. `arp_watcher.py` — detect ARP spoofing live

Scapy sniffer that watches every ARP reply on the wire. Maintains a `(IP, MAC)` mapping. Alerts when a new MAC claims an IP that already had a different MAC. Defensive utility, also useful offensively to detect *other* attackers on the same network during red-team ops.

### 3. `tcp_state_visualizer.py` — narrate TCP handshakes from pcap

Reads a pcap, follows every TCP stream, prints a colored timeline showing SYN, SYN+ACK, ACK, data, FIN, RST. Useful for both learning and incident analysis.

### 4. `packet_crafter.py` — Scapy-driven packet builder

Crafts arbitrary IP/TCP/UDP/ICMP packets from a YAML spec. Used for testing IDS rules, reproducing CVEs, demonstrating layer-3/4 manipulations. Lab-only.

### 5. `network_mapper.py` *(toolkit module)* — passive host discovery

Lands in `redshift_toolkit/net/network_mapper.py`. Sniffs traffic on an interface (or reads pcap), discovers hosts from observed src/dst IPs, fingerprints OS from TTL and TCP options. No active probes — perfectly silent recon.

---

## 6.13 Further Reading

- **Stevens, *TCP/IP Illustrated, Vol. 1*** — still the best networking book ever written.
- **Beej's Guide to Network Programming** — free, covers every socket API call you'll need.
- **Chris Sanders, *Practical Packet Analysis*** — pcap reading skills.
- **The Wireshark Wiki — SampleCaptures** — hundreds of real protocols to dissect.
- **RFC 793 (TCP)**, **RFC 791 (IPv4)**, **RFC 826 (ARP)** — surprisingly readable.
- **DEF CON 28: *Tales from the Trenches: Network Reconnaissance and Visualization at Scale*** — operational pcap workflows.
- **MITRE ATT&CK Network Sniffing — T1040** and **ARP Cache Poisoning — T1557.002**.

---

> **Do the captures.** Reading about networking is unbelievably less effective than typing `tcpdump`, watching three packets fly past, and tracing them in Wireshark. Five hours of pcaps will teach you more than this entire chapter.

→ Next: [Module 07 · Cryptography for Offensive Ops](07-crypto.md).
