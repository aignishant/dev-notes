# Part 1 — Foundations

!!! abstract "What this part gives you"
    The five foundations every offensive security professional must stand on: a clear **mindset**, a clear **legal framework**, a real **lab**, working knowledge of **Linux & Windows internals**, and a **Python toolkit skeleton** you'll grow for the rest of the course.

## Why this part matters

Most people who fail at ethical hacking fail here. They skip the philosophy and pattern-match to "scan, exploit, loot." They skip the legal module and blow up their career. They skip the lab and try to learn on compromised CTF VPNs. They skip Linux internals because "I know `ls`." They skip Python fundamentals because "I already know Python."

Don't be that person. Part 1 is the rebar inside every later technique.

## Modules

| # | Title | What you'll walk away with |
|---|-------|---------------------------|
| [01](01-philosophy.md) | Philosophy of Ethical Hacking | Hacker archetypes, kill chains, ATT&CK fluency, the attacker mindset, how your SOAR brain is an asset |
| [02](02-legal.md) | Legal & Ethical Framework | CFAA/ECPA/DMCA literacy, ROE templates, authorization artifacts, bug-bounty legal, responsible disclosure, real cases that put hackers in prison |
| [03](03-lab-setup.md) | Lab Setup | A full isolated home lab — hypervisor, networks, Kali/Parrot, Windows 11 + Server 2022 AD, vulnerable apps, snapshot workflow |
| [04](04-os-internals.md) | OS Internals for Hackers | Linux (procfs, perms, SUID, systemd) and Windows (registry, services, WMI, ACLs, tokens, AD) at the level you need to attack them |
| [05](05-python-toolkit.md) | Python for Offensive Security | The stdlib and third-party patterns that actually matter for offense, and the first commits to your personal `redshift-toolkit` package |

## Time budget

Plan for **2–3 weeks** of focused evenings/weekends for Part 1. You can read everything in a weekend, but the lab build and toolkit skeleton take time to do right. Do them right.

## Scripts shipping with Part 1

Every module ships with runnable Python. These live in `scripts/part-01/<module>/` and their helper counterparts land in `redshift-toolkit/`. Highlights:

- `attack_path_visualizer.py` — renders a kill chain for a hypothetical engagement (Module 01)
- `scope_validator.py` — pre-flight check: "is this IP in my ROE?" (Module 02)
- `roe_checker.py` — parses a Rules-of-Engagement YAML and validates planned actions (Module 02)
- `lab_health_check.py` — pings every lab VM and reports readiness (Module 03)
- `linux_enum.py` — comprehensive local enumeration on a Linux target (Module 04)
- `windows_enum_wmi.py` — WMI-based Windows enumeration from a Linux attacker (Module 04)
- `async_scanner_template.py` — the async-scanner pattern you'll reuse forever (Module 05)
- `redshift_toolkit/utils/encoder_decoder.py` — first toolkit module (Module 05)
- `redshift_toolkit/utils/cheatsheet_cli.py` — searchable command cheatsheet (Module 05)

## Prerequisites check

Before you start, confirm:

- [ ] You have a machine with **32 GB RAM** minimum (64 GB strongly recommended) and **1 TB SSD**.
- [ ] You can install a hypervisor (VMware Workstation Pro / Fusion, Proxmox, or VirtualBox).
- [ ] You have **Python 3.12+** and can run `pip install` without admin issues.
- [ ] You have accounts on **HackTheBox**, **TryHackMe**, and **PortSwigger Web Security Academy** (all have free tiers).
- [ ] You have a **dedicated** GitHub account for this journey (don't mix with your employer work).

Once all five boxes are ticked, move on.

[Start with Module 01 →](01-philosophy.md){ .md-button .md-button--primary }
