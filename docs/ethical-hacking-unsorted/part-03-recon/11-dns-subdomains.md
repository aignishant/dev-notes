# 11 · DNS & Subdomain Enumeration

> *Subdomains are the seams of an organization's perimeter. The main
> domain has corporate budget behind it; the subdomain six SREs forgot
> about does not.*

DNS enumeration is the highest-ROI recon activity per minute spent.
Every additional subdomain you discover is a potential foothold,
information leak, or pivot point. The orgs who win the most pentests
are the ones who enumerate subdomains the *most thoroughly*.

This module covers six independent discovery techniques. Use them all
and **merge** the outputs — different sources find different names.

---

## 11.1 The six techniques

| # | Technique | What it finds | Best for |
|---|-----------|---------------|----------|
| 1 | **DNS brute-force** | Names matching common patterns | Generic prefixes (`mail`, `vpn`, `ftp`, `dev`) |
| 2 | **Permutation engine** | Names derived from existing ones | Once you have seeds (e.g. `app1`, `app2`, `app-uat`) |
| 3 | **Certificate Transparency** | Every cert ever issued | Public-facing services with TLS |
| 4 | **Passive DNS aggregators** | Historical resolutions | Services moved or decommissioned |
| 5 | **NSEC / NSEC3 walking** | Full zone enumeration | DNSSEC-signed zones with NSEC |
| 6 | **Virtual-host fuzzing** | Hosts that share an IP but aren't in DNS | Behind shared hosting / CDNs |

Combine #1+#3+#4 for breadth, #2 for depth, #5 when DNSSEC enables it,
#6 for the long tail.

---

## 11.2 DNS brute-force

You query `<word>.target.com` for each `<word>` in a wordlist. Names
that resolve are real. Issues:

- **Wildcard records** — `*.target.com → 1.2.3.4` makes everything
  resolve. You must detect and filter.
- **CDN / load balancers** — many subdomains return the same IP; that's
  not a wildcard but it does need investigation.
- **Rate limiting** — large recursive resolvers throttle you. Run
  against multiple resolvers in parallel.
- **Wordlist quality** — `subdomains-top1million.txt` (SecLists) is the
  standard. `assetnote/wordlists` has curated lists.

Our `subdomain_enum.py` does async DNS with wildcard detection, multiple
resolvers, retries, and CIDR / record-type aware output.

---

## 11.3 Permutation engines

Once you have seed subdomains (`api.target.com`, `dev.target.com`),
generate variations:

- Number suffixes: `api1`, `api2`, …, `api10`
- Environment prefixes: `dev-api`, `uat-api`, `staging-api`, `prod-api`
- Region/zone: `us-east-api`, `eu-api`, `ap-api`
- Acquisition / brand mix: `targetcorp-api`, `formerco-api`
- Common appendages: `api-internal`, `api-old`, `api-test`, `api-bk`

The reference tool is `altdns` / `dnsgen`. Our `subdomain_permuter.py`
emits patterns from a small DSL and pipes into our DNS resolver.

---

## 11.4 NSEC / NSEC3 walking

DNSSEC-signed zones publish authenticated denial-of-existence records:

- **NSEC** record at name `A` says "the next existing name is `B`."
  Walking these from `A → B → C → …` enumerates the entire zone.
- **NSEC3** hashes names before chaining. Hashes can still be cracked
  offline (small alphabet, common patterns).

Tools: `nsec3walker`, `dnswalk`. Our `dns_zone_walker.py` does both
NSEC walking and NSEC3 hash collection (cracking is left to `hashcat`
mode 8300 / equivalent).

This technique is dropping in usefulness as zones move to NSEC3 with
high iterations or to "white-lie" NSEC, but is still found on slow-moving
infrastructure.

---

## 11.5 Virtual-host fuzzing

When you find an IP serving HTTP, the response depends on the `Host:`
header. Hidden hosts may share the same IP without DNS records pointing
to them. Process:

1. Confirm the IP serves a default page on `Host: <ip>`.
2. Fuzz `Host: <wordlist>.target.com` and any internal-naming patterns
   you've seen.
3. Compare responses (status, length, content hash) against the default.
4. Anything different is a candidate.

Our `vhost_fuzzer.py` uses a hash-based response classifier and ranks
candidates by deviation from the default.

---

## 11.6 Subdomain takeover

A **subdomain takeover** happens when DNS still points at a third-party
service that you can re-register:

```
old-marketing.target.com.    CNAME    target-cdn.s3.amazonaws.com.
```

If `target-cdn` is no longer registered as an S3 bucket, anyone (you)
can claim it and serve content from `old-marketing.target.com`.

Vulnerable services include S3, Azure Blob, GitHub Pages, Heroku,
Fastly, Shopify, Tumblr, Bitbucket, Cargo, ZenDesk, FreshDesk, Surge.sh,
Tilda, Wix, Webflow, …

Pattern in DNS:

- CNAME points at a fingerprinted service domain.
- Service returns a known "no such resource" message.
- Service allows public registration of the missing resource.

Our `subdomain_takeover_check.py` runs the standard fingerprint database
against any list of subdomains.

---

## 11.7 Putting it together — the merge

After running all six techniques, you have N output files of subdomains.
The merge step:

1. **Normalize** — lowercase, strip trailing dots, remove duplicates.
2. **Resolve** — every candidate gets re-resolved (records may have
   changed since the last source's data).
3. **Deduplicate by IP set** — many "different" subdomains resolve to
   the same load-balancer IP; group them.
4. **Score** — interesting names (prefixes like `dev-`, `staging-`,
   `internal-`, `vpn-`, `admin-`) rank higher.

This is exactly what `passive_subdomains.py` and the Module 12
orchestrator do.

---

## 11.8 Industry scenarios

### Financial — uncovering the staging banking app

Bank's main domain is hardened. CT logs reveal `mob-stg.bank.example`.
DNS resolves; HTTPS serves the staging mobile-app API with relaxed
auth controls. Real engagement pattern; closes 70% of pre-prod testing
gaps for the bank.

### Government — orphan .gov subdomain takeover

Old marketing campaign subdomain still points at a deprovisioned cloud
service. Re-register it. Now `[old-campaign].agency.gov` is yours,
serving phishing pages with a perfectly legitimate domain.

### Healthcare — telemedicine surge artifacts

COVID-era surge spun up `telemed-uat.hospital.org`. Lockdown ended;
service was decommissioned but DNS not. Subdomain takeover via
abandoned cloud bucket → phishing pretexts targeting clinicians.

### Tech — internal hostname leak via CT

A company's internal CA (typo'd in monitoring config) issued certs that
made it into a public CT log: `vault.dc1.corp-internal`. Now the
attacker knows the internal naming scheme: `<service>.<dc>.corp-internal`.
That's enough to begin password-spray pretexting.

---

## 11.9 Detection / blue-team angle

Subdomain enumeration is hard to detect when done right because:

- DNS brute uses *recursive* resolvers (your traffic doesn't hit the
  authoritative directly).
- CT log queries hit `crt.sh`, not the target.
- Passive DNS hits a third-party aggregator.

Detection moves to the *target's authoritative DNS* logs, where high
NXDOMAIN volume from a single source still indicates active enumeration.

Defender priorities:

- **CT monitoring** for own domains (catch new subdomains as soon as
  cert is issued).
- **DNS analytics** at the authoritative server — NXDOMAIN ratios,
  query-source distributions.
- **Subdomain inventory** as a continuous control — ServiceNow CMDB plus
  DNS reconciliation.
- **DMARC + CAA** to limit which CAs can issue and where mail can go.
- **Decommissioning runbooks** — DNS records always die *before* cloud
  resources, never after.

Sigma rule sketch:

```yaml
title: High NXDOMAIN rate against authoritative DNS
detection:
  selection:
    server_role: authoritative
    rcode: NXDOMAIN
    count: '>1000 in 60s from same src'
  condition: selection
level: medium
```

---

## 11.10 Toolbelt

| Tool | Purpose |
|------|---------|
| `dnsx` (ProjectDiscovery) | Fast DNS resolver / brute |
| `subfinder` | Aggregator across passive sources |
| `amass` | Multi-source enumeration with graphing |
| `assetfinder` | Lightweight passive collector |
| `chaos` (ProjectDiscovery) | API for known subdomain corpora |
| `puredns` | DNS brute with wildcard handling |
| `massdns` | Stub resolver, fast |
| `altdns`, `dnsgen` | Permutation generators |
| `subjack`, `subzy`, `nuclei takeover templates` | Takeover detection |
| `crt.sh` (manual) | CT log query |

---

## 11.11 Scripts for this module

In `scripts/part-03/11-dns-subdomains/` and `redshift-toolkit/redshift_toolkit/recon/`:

1. **`subdomain_enum.py`** *(toolkit)* — async DNS brute with wildcard
   detection, multi-resolver, retries.
2. **`subdomain_permuter.py`** *(toolkit)* — pattern-based mutation engine.
3. **`passive_subdomains.py`** *(toolkit)* — multi-source aggregator
   (crt.sh + hackertarget + alienvault OTX).
4. **`dns_zone_walker.py`** *(toolkit)* — NSEC walking + AXFR attempt.
5. **`vhost_fuzzer.py`** *(toolkit)* — virtual-host fuzzing on a target IP.
6. **`subdomain_takeover_check.py`** *(toolkit)* — orphaned-CNAME
   takeover candidate detector.
7. **`subdomain_pipeline.py`** — module-level orchestrator that runs
   1, 3, 5, 6 against a single target and produces a merged JSON.

---

## 11.12 Lab exercises

1. Pick a domain you own. Run `subdomain_enum.py` with the included tiny
   wordlist. Verify wildcard detection by adding `*.yourdomain.com` to
   the zone temporarily.
2. Run `passive_subdomains.py` against `nasa.gov` (a permissive,
   public-friendly target). Compare CT-only vs aggregated results.
3. Use `subdomain_permuter.py` with seeds `api`, `app`, `web` and
   prefixes `dev`, `uat`, `prod`, suffixes `1`, `2`, `3`. Pipe into
   `subdomain_enum.py`. Note how many of the permutations exist.
4. Run `subdomain_takeover_check.py` against a list of known stale
   subdomains (your old projects). Practice the fingerprint workflow.
5. Stand up two Apache vhosts in the lab on the same IP. Run
   `vhost_fuzzer.py` against the IP with a wordlist that includes both
   names. Verify both are detected.

---

## 11.13 Further reading

- **`HackerOne` / `Bugcrowd` reports tagged `subdomain-takeover`** —
  hundreds of real takeover writeups.
- **Patrik Hudak's blog `0xpatrik.com`** — definitive subdomain-takeover
  reference.
- **`Project Sonar`** — Rapid7's internet-wide scan datasets.
- **DNS-OARC research papers** — DNS abuse measurement at scale.
- **MITRE ATT&CK Sub-technique T1590.001 — Domain Properties.**

---

→ Next: [Module 12 · OSINT Automation & Asset Graphing](12-osint-automation.md).
