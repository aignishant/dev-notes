# 🌐 IoT, ICS & OT Security

> Critical infrastructure security — power grids, water treatment, manufacturing plants, hospitals, ports. The systems where a buffer overflow doesn't crash a website, it spills sewage into a river or stops a centrifuge.

For roles in: **CISA (US)**, **NCIIPC (India)**, **DOE national labs**, **ICS-CERT**, **Idaho National Laboratory**, **Dragos**, **Claroty**, **Nozomi**, **utility companies**, **defense contractors**.

## Why this track matters

Every other Phase 4 specialization assumes the target is software. ICS/OT assumes the target is a **physical process** — a chemical reaction, a turbine, a substation. Compromising the wrong PLC doesn't leak data; it can kill people. The Stuxnet worm (2010, Natanz nuclear facility) proved this is no longer theoretical.

Three things make this track different from regular IT security:

1. **Reliability and safety beat confidentiality.** A power grid that's confidential but down is worse than one that's compromised but running.
2. **The systems are old.** Twenty-year-old PLCs running 1990s-era protocols are the norm, not the exception. You can't just "apply the patch."
3. **The blast radius is physical.** Compromise → process disruption → real-world consequence (blackout, water contamination, derailment).

## The Purdue Model — the architecture you'll see everywhere

```
┌────────────────────────────────────────────────────────────────┐
│  Level 5: Enterprise (Internet, business email, SaaS)          │
├────────────────────────────────────────────────────────────────┤
│  Level 4: Business / IT (ERP, file servers, AD)                │
├────────────────────────────────────────────────────────────────┤
│  IT/OT DMZ — historian, jump hosts, patch repos                │
├────────────────────────────────────────────────────────────────┤
│  Level 3: Operations (SCADA servers, engineering workstations) │
├────────────────────────────────────────────────────────────────┤
│  Level 2: Supervisory (HMIs, local SCADA, alarm servers)       │
├────────────────────────────────────────────────────────────────┤
│  Level 1: Control (PLCs, RTUs, IEDs, safety controllers)       │
├────────────────────────────────────────────────────────────────┤
│  Level 0: Process (sensors, actuators, motors, valves)         │
└────────────────────────────────────────────────────────────────┘
```

Attacks typically traverse **L4 → DMZ → L3 → L2 → L1** by abusing weak segmentation, dual-homed engineering laptops, or remote-access tools (RDP, TeamViewer, ICS vendor remote support tunnels).

The 2021 Oldsmar water treatment attack (Florida) used TeamViewer left enabled on an HMI workstation. The 2015 Ukraine power grid attack used spear-phishing → BlackEnergy → KillDisk → harvested VPN creds → SCADA HMI manipulation.

## ICS protocols you must recognize

| Protocol | Layer | Default port | Usage |
|---|---|---|---|
| Modbus TCP | TCP | 502 | Most common — read/write registers on PLCs. **No auth, no encryption.** |
| DNP3 | TCP/UDP | 20000 | Power utilities. SAv5 adds auth (rare in deployment). |
| IEC 60870-5-104 | TCP | 2404 | European power utilities. Cleartext. |
| IEC 61850 (MMS, GOOSE, SV) | OSI/Ethernet | 102 (MMS) | Substations. GOOSE is multicast Ethernet — sub-millisecond latency. |
| EtherNet/IP (CIP) | TCP/UDP | 44818, 2222 | Allen-Bradley / Rockwell. PLC programming. |
| S7comm / S7CommPlus | TCP | 102 | Siemens S7 PLCs. S7CommPlus encrypts but well-studied. |
| OPC UA | TCP | 4840 | Modern, can use TLS + auth. Replacement for OPC Classic. |
| BACnet | UDP | 47808 | Building automation (HVAC, fire, access). |
| Profinet RT/IRT | Ethernet | — | Real-time variant of Profinet. Industrial Ethernet. |
| Modbus RTU / Modbus ASCII | Serial (RS-485) | — | Legacy serial. Common via gateway. |

**Read-only recon is usually safe; writes are dangerous.** A `Modbus Write Single Coil` to the wrong holding register can stop a pump.

## Reconnaissance (defensive, with permission)

### Network scanning — be careful

Default `nmap -A` against an ICS device can crash it. Old PLCs respond to malformed TCP packets by hanging or factory-resetting.

Use ICS-aware scanners:
- **[nmap NSE scripts](https://nmap.org/nsedoc/categories/safe.html)** with `--script=safe` filter — `modbus-discover`, `s7-info`, `bacnet-info`, `enip-info`. Run with `-T2` or `-T1` (paranoid timing).
- **[Shodan](https://www.shodan.io/)** — passive: `port:502`, `port:44818`, `product:"Schneider Electric"`. Internet-exposed PLCs are appallingly common.
- **[GRASSMARLIN](https://github.com/nsacyber/GRASSMARLIN)** — NSA-released passive ICS network mapper.
- **[Industroyer2 detection rules](https://github.com/SigmaHQ/sigma)** — published Sigma rules for known ICS malware.

### Asset inventory queries (Modbus example)

Modbus function codes 0x2B / 0x0E (Read Device Identification) return vendor / product / version strings:

```python
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient("10.10.10.5", port=502)
c.connect()
res = c.execute(ReadDeviceInformationRequest(slave=1))
print(res.information)   # {0: b'Schneider', 1: b'Modicon M340', 2: b'2.70'}
```

This is read-only and safe. Map every asset before doing anything else.

## ICS-specific attack patterns

| Pattern | Explanation | Real example |
|---|---|---|
| Replay | Capture legitimate process commands, replay later | Triton, BlackEnergy |
| Stale data injection | Spoof historian/HMI data so operators see "all green" while plant melts down | Stuxnet (rotor speeds shown normal while spinning at destructive rates) |
| Logic-bomb PLC firmware | Replace a PLC ladder logic program with malicious one | Stuxnet S7 attack code |
| Safety system bypass | Compromise the *safety* PLC (SIS) — process can run past safe limits | Triton/Trisis on Schneider Triconex |
| Wireless hijack | RF capture → replay control commands (cranes, pump controllers) | Trend Micro RF research, multiple vendors 2018 |

## Embedded firmware analysis

Most IoT exploits start with extracting and analyzing firmware.

### 1. Extraction

```bash
# Most common: analyze a firmware blob from vendor's site
binwalk -e firmware.bin

# Modern variant
unblob firmware.bin -o extracted/

# Hardware: dump from chip
flashrom -p ch341a_spi -r flash.bin              # SPI flash via CH341A
# JTAG (board with header):
openocd -f interface/jlink.cfg -f target/stm32f4x.cfg
# UART: cat /dev/ttyUSB0 → bootloader prompt → dump RAM
```

Our [`iot/firmware_extractor.py`](../../scripts/iot/firmware_extractor.py) wraps `binwalk` + entropy + filesystem detection in one CLI.

### 2. Static analysis on the extracted root filesystem

```bash
firmwalker extracted/squashfs-root/         # finds passwords, certificates, /etc/shadow, web roots
grep -r "password\|admin\|telnet" extracted/etc/
file extracted/usr/bin/httpd                 # vendor's tiny web server
```

The [`appsec/sast_secrets_scan.py`](../../scripts/appsec/sast_secrets_scan.py) script (next chapter) also works great here.

### 3. Emulation

You usually can't run an ARM/MIPS firmware on your x86 laptop directly. Use:

- **[FAT (firmware analysis toolkit)](https://github.com/attify/firmware-analysis-toolkit)** — uses firmadyne to spin up emulated firmware
- **[QEMU user-mode](https://www.qemu.org/)** for individual ARM/MIPS binaries: `qemu-arm -L /usr/arm-linux-gnueabi httpd`
- **[Renode](https://renode.io/)** for full-system embedded emulation (great for STM32, RISC-V, etc.)

### 4. Vulnerability hunting

| Category | What to look for |
|---|---|
| Auth bypass | `if (strcmp(password, "") == 0)` jokes that aren't jokes — vendors leave these in |
| Hardcoded creds | `admin:admin`, vendor-specific backdoor accounts (2024 Contec CMS8000 patient monitor) |
| Command injection | `system("ping " + user_input)` in CGI scripts |
| Buffer overflow | `strcpy`, `sprintf`, `scanf` in any C binary on the device |
| Insecure update | Unsigned firmware images, downloads over HTTP |
| Telnet/SSH defaults | Devices ship with `root:vizxv`, `root:xc3511`, etc. — Mirai botnet's wordlist |

## Hardware reverse engineering

The fun, low-level part. Most IoT devices have:

- **UART** — usually 4 pins (VCC, GND, TX, RX), often labeled, often outputs a debug shell at 115200 baud. Tools: USB-TTL adapter, screen, `picocom`.
- **JTAG** — debug interface for direct CPU control. Pinout often unlabeled — find with [JTAGulator](http://www.grandideastudio.com/jtagulator/) or guess with Bus Pirate.
- **SWD** — ARM's 2-wire JTAG variant (SWDIO + SWCLK). Very common on STM32, nRF52, etc.
- **SPI flash** — usually a SOIC-8 chip on the board. Read in-circuit with CH341A + SOIC-8 clip. Often contains the entire firmware including bootloader.
- **I²C** — sensor/peripheral bus. Sometimes config EEPROM.
- **eMMC / NAND** — larger storage, requires more careful work (BGA reballing for eMMC).

Tools to own:
- **Bus Pirate** ($30) — universal protocol explorer, OK at most things, master of none
- **Saleae Logic Pro 8 / 16** ($400+) — serious logic analyzer
- **HydraBus / HydraNFC** ($60) — open hardware, scriptable, very capable
- **CH341A** ($5) — cheap SPI flash reader/writer
- **HackRF One** ($300) or **bladeRF** ($400) — software-defined radio
- **Ubertooth One** ($120) — Bluetooth Classic + LE sniffing
- **Flipper Zero** ($170) — sub-GHz RF + NFC + iButton + GPIO swiss army knife
- **Proxmark3 RDV4** ($300) — RFID/NFC professional tool
- **JLink EDU Mini** ($60) — JTAG/SWD debug probe (ARM)

## RF and wireless

Once you go beyond Wi-Fi (Phase 3), there's a whole world:

| Technology | Frequency | Tools |
|---|---|---|
| Bluetooth Classic | 2.4 GHz | Ubertooth, btmon, Wireshark + sniffer dongle |
| Bluetooth Low Energy (BLE) | 2.4 GHz | nRF Connect, Frida + iOS, btlejack, sniffle (TI CC1352) |
| Zigbee | 2.4 GHz | KillerBee, ZBOSS, Z3sec |
| Z-Wave | 868/908 MHz | Z-Wave PC Controller, EzZWave |
| LoRaWAN | 868/915 MHz | Chirpstack, LoRaShark |
| ISM bands (315/433/868/915 MHz) — garage doors, alarms | Sub-GHz | RTL-SDR + URH (Universal Radio Hacker), HackRF, Flipper Zero |
| GSM | 900/1800 MHz | OpenBTS, YateBTS, gr-gsm (research only — using a real BTS without license is illegal in most countries) |
| LTE | various | srsLTE, OpenAirInterface |
| GPS | L1 1575 MHz | gps-sdr-sim (spoofing — also illegal without permission) |
| RFID 125 kHz / 13.56 MHz | LF / HF | Proxmark3, ChameleonMini, Flipper |

[Universal Radio Hacker (URH)](https://github.com/jopohl/urh) is the must-know tool — capture, demodulate, analyze, replay any sub-GHz protocol with a GUI.

## ICS-specific frameworks & resources

- **MITRE ATT&CK for ICS** — [https://attack.mitre.org/matrices/ics/](https://attack.mitre.org/matrices/ics/) — TTPs specific to ICS environments
- **MITRE D3FEND for ICS** — defensive countermeasures
- **NIST SP 800-82r3** — Guide to Operational Technology (OT) Security
- **ISA/IEC 62443** — the standards body for industrial automation security
- **ICS-CERT advisories** — [https://www.cisa.gov/news-events/cybersecurity-advisories?f%5B0%5D=advisory_type%3A95](https://www.cisa.gov/news-events/cybersecurity-advisories) — monthly bulletins
- **Dragos WorldView intel reports** — paid, but free public ones cover known threat groups (XENOTIME, ELECTRUM, CHERNOVITE, VOLTZITE)
- **CISA Known Exploited Vulnerabilities (KEV)** — search for ICS vendors

## Defensive priorities for OT environments

When you're hired to defend, the playbook is different from corporate IT:

1. **Asset inventory.** You can't protect what you don't know about. Passive tools (Dragos, Claroty, Nozomi, GRASSMARLIN) only — don't actively scan.
2. **Network segmentation.** Strict L4/DMZ/L3 boundaries, data diodes from L3→L4 where possible, no flat networks.
3. **Remote access hygiene.** No vendor permanent VPN tunnels. Use jump hosts with MFA, session recording, time-limited grants.
4. **Logging without disrupting.** Tap network traffic via SPAN ports / network taps, parse offline. Don't install agents on PLCs.
5. **Patching schedules tied to maintenance windows.** Annually or quarterly is realistic, not weekly. Compensate with detection + segmentation.
6. **Backup & restore-tested PLC programs** — if a PLC's logic is overwritten, you need to know exactly what was there.
7. **Tabletop exercises** — practice "PLC X stops responding, what do we do?" with the engineering and ops teams, not just IT.

## CTFs and labs

- **[ICS-CTF (S4 conference)](https://s4xevents.com/)** — yearly, world-class
- **[CISA's ICS-300 / ICS-400 training](https://www.cisa.gov/topics/industrial-control-systems)** — free, in-person at INL
- **[Pwn2Own ICS edition](https://www.zerodayinitiative.com/Pwn2OwnMiamiSouthBeach2025)** — Pwn2Own Miami / Toronto IoT
- **[Damn Vulnerable Industrial Controller (DVIC)](https://github.com/cmu-sei/DVIC)** — CMU SEI's training environment
- **[Conpot](https://github.com/mushorg/conpot)** — ICS honeypot, learn what attacks look like in your logs

## Hands-on home lab

Affordable starter kit (~$200–300):
- One Modbus PLC: a [Click PLC](https://www.automationdirect.com/adc/shopping/catalog/programmable_controllers/click_series_plcs_(stackable_micro_brick)) (~$70) or even an ESP32 running [esp-modbus](https://github.com/espressif/esp-modbus)
- [OpenPLC Runtime](https://www.openplcproject.com/) on a Raspberry Pi (free) — software PLC speaking Modbus/DNP3
- [Rapid SCADA](https://rapidscada.org/) or [ScadaBR](https://www.scadabr.com.br/) — free SCADA HMI software
- Old laptop running [Conpot](https://github.com/mushorg/conpot) as a honeypot
- Wireshark + dedicated managed switch with port mirroring

You'll have a 3-tier ICS environment for under $300 to attack and defend in your home network.

## Interview questions

1. *"Walk through the Stuxnet attack chain at a high level."*
2. *"What's the difference between Modbus and DNP3? Which would you find at a power utility?"*
3. *"Why is a vendor remote-support tunnel a bigger risk than a single misconfigured firewall rule?"*
4. *"You've found an internet-exposed Modbus PLC during a recon scan. What do you do? What don't you do?"*
5. *"Explain the Purdue Model. What's at L0 and what's at L3?"*
6. *"What's a safety instrumented system (SIS) and why is Triton significant?"*
7. *"You're handed a router firmware blob. Walk through your analysis steps."*

## Recommended reading

- *Hacking Exposed: Industrial Control Systems* (Bodungen, Singer, et al.)
- *Practical Industrial Cybersecurity* (Bartman & Greer)
- *Industrial Network Security* (Knapp & Langill)
- Robert M. Lee's blogs and talks (Dragos CEO, INL alum) — best big-picture analysis on ICS adversaries
- *Countdown to Zero Day* (Kim Zetter) — narrative history of Stuxnet, the book that defined this field

## Python script reference

This phase ships:
- [`iot/firmware_extractor.py`](../../scripts/iot/firmware_extractor.py) — wrapper around binwalk + entropy + filesystem detection

---

[← Exploit Dev](exploit-dev.md)  ·  [AI/ML Security →](ai-security.md)
