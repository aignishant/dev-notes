# Part 3 · Reconnaissance

> *Reconnaissance is the most under-rated phase of every engagement. The
> operators who win the most ground in the least time are the ones who
> spent disproportionate effort here. **You cannot exploit what you have
> not enumerated.***

Part 1 made you safe. Part 2 made you dangerous on the wire. **Part 3 makes
you fast** — fast at finding targets, fast at mapping their attack surface,
fast at turning raw output into prioritized leads.

Every Part of this curriculum past this point assumes you can do recon at
scale. The scripts you write here will compound: every later module —
web, AD, cloud, ICS, red-team ops — starts with the asset graph that the
recon pipeline produces.

## Why split recon into four modules

| Module | What it teaches | What you'll build |
|--------|-----------------|-------------------|
| **09 · Passive recon & OSINT** | Search-engine intel, GitHub dorks, certificate transparency, archive.org, WHOIS/RDAP, BGP/ASN, breach corpora | 5 toolkit utilities that pull public sources without ever touching the target |
| **10 · Active recon & network mapping** | Port scanning at scale, version detection, OS fingerprinting, vuln correlation | Concurrent service-enumeration toolchain that scales to /16 networks |
| **11 · DNS & subdomain enumeration** | Wordlist + permutation + CT logs + DNSSEC walking + virtual-host fuzzing + subdomain takeovers | The complete subdomain discovery toolkit |
| **12 · OSINT automation & asset graphing** | Pipeline orchestration, dedup, scoring, reporting, recon-diff over time | The orchestrator that ties Modules 9-11 into a single command and produces a Markdown report |

## Learning outcomes

By the end of Part 3 you will be able to:

- Build a complete asset inventory of any organization from public sources alone, without ever sending a packet to their infrastructure.
- Discover subdomains using six independent techniques (DNS brute, CT logs, passive DNS aggregators, NSEC/NSEC3 walking, permutation, virtual-host fuzzing) and merge the results.
- Scan a /16 in under 5 minutes, then correlate every banner against known CVEs.
- Write reports that stakeholders actually read — prioritized leads, not raw nmap dumps.
- Detect organizational changes between recon runs (new subdomain, new exposed service, expired certificate).
- Automate the entire passive→active→correlate→report loop into a single CLI invocation.

## Toolkit additions in Part 3

By the end of this part your `redshift-toolkit` package will gain:

**`recon/`** (passive sources):

- `whois_asn.py` — WHOIS, RDAP, and BGP/ASN origin lookup
- `cert_harvester.py` — Certificate Transparency log harvester (crt.sh, Censys CT)
- `github_dorks.py` — GitHub code search for leaked secrets, internal hostnames, configs
- `wayback_paths.py` — archive.org URL extraction with parameter mining
- `breach_lookup.py` — local breach corpus check (HIBP-style, offline)
- `passive_subdomains.py` — multi-source subdomain aggregator
- `subdomain_enum.py` — async DNS brute-force with wildcard handling
- `dns_zone_walker.py` — NSEC / NSEC3 walking + AXFR attempt
- `vhost_fuzzer.py` — Host-header fuzzing for hidden virtual hosts
- `subdomain_permuter.py` — pattern-based subdomain mutation engine
- `subdomain_takeover_check.py` — orphaned-CNAME takeover candidate detector

**`scan/`** (active sources):

- `masscan_wrapper.py` — drives masscan, parses output into toolkit-format JSON
- `svc_enum.py` — concurrent service version detection
- `os_fingerprint.py` — TTL + TCP options + banner-based OS identification
- `vuln_correlator.py` — service version → CPE → CVE lookup against the NVD JSON feed

**`automation/`** (orchestration):

- `asset_graph.py` — merges every recon source into a normalized asset graph
- `osint_pipeline.py` — passive → active → correlate → report driver
- `report_generator.py` — turns asset graph + findings into a Markdown engagement report
- `recon_diff.py` — diffs two snapshots, highlights what changed (new hosts, new services, missing services)

## Prerequisites checklist

Before starting Part 3, confirm:

- [ ] Part 1 lab is up; Kali can reach the public internet.
- [ ] You have read Part 2 and run `dns_client.py` against `1.1.1.1`.
- [ ] You have `nmap`, `masscan`, `dig`, `curl`, and `jq` installed on Kali.
- [ ] `pip install -e redshift-toolkit/` ran cleanly after Part 2.

## How to use Part 3

Run **every** script in this part against your own assets first — a personal domain, a company you legitimately own, or a CTF target you have authorization for. Recon scripts are easy to weaponize accidentally; building muscle memory for which sources are passive vs. which sources hit the target is part of the curriculum.

Module 12 ties everything together. Read modules 9, 10, and 11 first, run their scripts standalone, then use Module 12's orchestrator to drive them all from a single command.

---

→ Start with [Module 09 · Passive Recon & OSINT](09-passive-osint.md).
