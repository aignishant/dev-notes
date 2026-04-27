# 09 · Passive Recon & OSINT

> *Every byte of intelligence you can gather without sending a packet to
> the target is intelligence the defender cannot see you collecting. The
> best recon engineers spend two days here before they touch nmap.*

Passive recon means **no traffic to the target**. You query third-party
sources, public databases, and historical records. The target has no logs
of you ever existing. This is the right opening move on any engagement
because:

1. It builds an asset inventory before you draw attention.
2. It surfaces leaked credentials, exposed configs, forgotten subdomains.
3. It is how nation-state actors typically begin (and what blue teams
   often miss).

---

## 9.1 The OSINT source taxonomy

| Source category | What it gives you | Examples |
|-----------------|-------------------|----------|
| **Domain & IP records** | ownership, contacts, ASN, BGP origin | WHOIS, RDAP, BGPView, RIPE/ARIN |
| **Certificate Transparency** | every cert ever issued for a name | `crt.sh`, Censys CT, Google CT |
| **Search engines** | indexed content, cached pages, leaked docs | Google, Bing, Yandex, DuckDuckGo |
| **Code search** | hardcoded creds, internal hostnames, configs | GitHub, GitLab, BitBucket, Sourcegraph |
| **Archives** | historical pages, old endpoints, deleted content | Wayback Machine, archive.today, Common Crawl |
| **Passive DNS** | historical resolutions | SecurityTrails, RiskIQ, VirusTotal, DNSDB |
| **Breach corpora** | leaked credentials, password reuse | HIBP, DeHashed, internal aggregations |
| **Social** | employee names, tech stack, projects | LinkedIn, GitHub orgs, conference talks |
| **Document metadata** | author names, software versions, internal paths | EXIF, `metagoofil`, FOCA-style extraction |

---

## 9.2 WHOIS, RDAP, and BGP/ASN

WHOIS is the legacy protocol; **RDAP** (Registration Data Access Protocol,
RFC 7480-7484) is its modern HTTP/JSON replacement. Both reveal:

- Domain registrar, creation/expiration dates
- Registrant contact (often privacy-protected today)
- Nameservers
- For IP blocks: organization name, ASN, BGP origin, allocation history

**ASN/BGP** is the highest-leverage piece. If you discover the target's
ASN (e.g. `AS15169` for Google), you can enumerate every IP prefix they
announce, then reverse-DNS each block, then port-scan only theirs. This
prevents wasting time on cloud-provider IPs that aren't actually theirs.

```bash
# Manual one-liners
whois example.com
whois 8.8.8.8
curl -s 'https://rdap.org/domain/example.com' | jq
curl -s 'https://api.bgpview.io/asn/15169/prefixes' | jq '.data.ipv4_prefixes[].prefix'
```

Our toolkit wraps these into `whois_asn.py`.

---

## 9.3 Certificate Transparency — the goldmine

Every TLS cert issued by a CA must be logged in public, append-only
**CT logs**. Aggregators (notably **crt.sh**) make these searchable.

A single query for `%example.com` returns:

- Every subdomain that ever had a cert (most are real — TLS provisioning
  needs a real DNS record).
- Internal hostnames that leaked (`internal.example.com`, `dev-jenkins.example.com`).
- Wildcard cert reveals the parent domain's full coverage policy.
- Issuance frequency reveals automation (Let's Encrypt → 90-day cycles).

```bash
# Quick CT enum
curl -s 'https://crt.sh/?q=%25.example.com&output=json' | jq -r '.[].name_value' | sort -u
```

Our `cert_harvester.py` does this with deduplication, retries, and JSON output.

---

## 9.4 GitHub dorking — leaked secrets at scale

Developers leak secrets by accident — AWS keys in commit histories,
internal Jenkins URLs in docker-compose files, database connection
strings in `.env` examples. GitHub code search finds them.

**Effective dorks** (search them in GitHub's code search):

- `"corp.example.com" password`
- `org:targetorg AKIA`     ← AWS access keys
- `org:targetorg jenkins.example.com`
- `org:targetorg "BEGIN RSA PRIVATE KEY"`
- `"corp-internal" extension:env`
- `"Authorization: Bearer" extension:json target.com`
- `extension:pcap target.com`

The volume is unmanageable manually. Our `github_dorks.py` runs a curated
list, dedupes by repo + filepath, and flags high-signal hits.

!!! warning "Always use a token"
    Unauthenticated GitHub search is heavily rate-limited and only
    indexes a fraction of public code. Authenticated tokens get full
    coverage and ~30 req/min.

---

## 9.5 The Wayback Machine

`web.archive.org` keeps snapshots of millions of sites going back ~25
years. Useful for:

- **Old endpoints** still on the live server but no longer linked.
- **Old JavaScript bundles** revealing API routes since hidden.
- **Old robots.txt / sitemap.xml** revealing internal paths.
- **Pre-rebrand content** that retains old hostnames and tech stack.
- **Deleted blog posts** mentioning internal tools.

```bash
# Pull every URL ever archived for a host
curl -s 'https://web.archive.org/cdx/search/cdx?url=*.example.com/*&output=json&fl=original&collapse=urlkey'
```

Our `wayback_paths.py` does this and additionally extracts unique URL
parameters across all archived pages — these often reveal hidden API
arguments worth fuzzing.

---

## 9.6 Breach corpora and credential intel

Public credential dumps (Collection #1, RockYou2024, ZenZenshield, etc.)
contain billions of email/password pairs. Ethical use:

1. **HaveIBeenPwned API** — yes/no per email, no plaintext exposed.
2. **Local corpus on a research machine** — for engagements with
   explicit authorization to perform credential-spray on stale leaks.
3. **DeHashed / IntelX** — paid commercial services with structured search.

For the toolkit, `breach_lookup.py` operates against an offline corpus
(SHA-1 prefix index, HIBP-style) so you never expose query strings to a
third party.

!!! danger "Legal note"
    Possession of breach corpora is *legally distinct* from using them.
    Use only on engagements with written authorization, and never store
    plaintext credentials longer than the engagement requires.

---

## 9.7 Document metadata and tech-stack fingerprinting

When a target publishes PDFs, Office documents, or images, their
metadata often leaks:

- **Author names** (great for phishing pretexts and password sprays).
- **Software versions** (MS Office 2013 = old patch baseline).
- **Internal file paths** (`\\fileserver\dept-finance\` in PDF metadata).
- **Camera serial numbers** in images (linking documents to specific people).

`exiftool` is the standard. `metagoofil` automates "google for site:target.com filetype:pdf, download, exiftool, aggregate."

For tech-stack fingerprinting **without touching the target**:

- **BuiltWith / Wappalyzer** databases catalog observed tech per domain.
- **Shodan / Censys / FOFA** index banner data globally.
- **HTTP Archive** stores response headers from millions of crawled sites.

---

## 9.8 Passive DNS

When DNS records change, passive DNS aggregators retain history:

- `IP X used to resolve Y between dates A and B`
- `Hostname H used to point at IP I before moving to J`

Why useful:

- **CDN bypass** — the *origin* IP often pre-dates Cloudflare adoption
  and is still in passive DNS, still serving the same content.
- **Subdomain discovery** — historical lookups reveal names not in
  current DNS.
- **Infrastructure pivots** — find other domains that resolved to the
  same internal IP space.

Sources: VirusTotal passive DNS, SecurityTrails, RiskIQ, DNSDB (Farsight).
Most require API keys; SecurityTrails and VirusTotal offer free tiers.

---

## 9.9 Industry scenarios

### Financial — pre-engagement intel for a regional bank

WHOIS the bank's domain → privacy-protected. ASN lookup → AS reveals 4
prefixes. CT logs → 80+ subdomains, including `dev-internetbanking`,
`uat-mobileapp`, `vpn-staff`. GitHub dorks → a public repo from a former
contractor includes the test environment's reverse-proxy config with
internal hostnames. **All of this happens without touching the bank.**

### Healthcare — finding the unmonitored DICOM endpoint

Hospital's main domain has good DNS hygiene. CT logs reveal
`pacs-staging.hospital.org`. Wayback Machine has a 2019 snapshot
showing the staging PACS exposed an unauthenticated DICOM web viewer.
Live check: still up. *Patient images accessible without authentication.*
Real pattern, found multiple times in 2023-2024 health-org reports.

### Cloud / SaaS — the abandoned subdomain

Company A acquires Company B. Company B's old marketing domains have
DNS records still pointing at S3 buckets/Heroku apps that were
decommissioned. CT logs surface them. Subdomain takeover via re-registering
the orphaned cloud resource. Phishing pretexts on credible domains.

### Government — vendor names from procurement records

Federal agency publishes contract awards. Vendor names are public. Each
vendor's GitHub org reveals the technology stack supplied to the agency.
Internal hostnames in vendor repos. **Supply-chain recon entirely from
public records.**

---

## 9.10 Detection / blue-team angle

Passive recon is, definitionally, undetectable from the target's perspective.
Defenders must therefore:

- **Monitor CT logs for their own domains.** Tools: `cert-spotter`,
  Cloudflare's CT alerting, `crt.sh` RSS feeds, your own
  `cert_harvester.py` running daily.
- **Audit GitHub orgs and ex-employee accounts** for leaked configs.
  Tools: `truffleHog`, `gitleaks`, `noseyparker`.
- **Monitor breach corpora for company emails** — HIBP enterprise, DeHashed.
- **Audit DNS hygiene** — kill orphan CNAMEs, expire stale subdomains,
  set strict CAA records.
- **Watermark internal docs** so leaks are traceable when they appear in
  search engine indexes.

---

## 9.11 Toolbelt

| Tool | Purpose |
|------|---------|
| `whois`, `whoisit` | Domain/IP WHOIS |
| `rdap-cli` | Modern RDAP queries |
| `mtr`, `traceroute` | Hop-by-hop path (passive on remote target's perspective) |
| `crt.sh` (via curl/jq) | CT log search |
| `theHarvester` | Email/subdomain harvester |
| `metagoofil` | Document metadata harvest |
| `gitleaks`, `truffleHog`, `noseyparker` | Repo secret scanners |
| `Wayback Machine CDX API` | Archived URL extraction |
| `BuiltWith`, `Wappalyzer` | Tech-stack fingerprint |
| `Shodan`, `Censys`, `FOFA` | Pre-indexed banner search |
| `SpiderFoot` | All-source OSINT pipeline (heavy) |
| `recon-ng` | Modular OSINT framework |
| `Maltego` | Graph-based OSINT |

---

## 9.12 Scripts for this module

In `scripts/part-03/09-passive-osint/` and `redshift-toolkit/redshift_toolkit/recon/`:

1. **`whois_asn.py`** *(toolkit)* — given a domain or IP, returns registrar,
   nameservers, ASN, BGP-announced prefixes (via `bgpview.io` public API).
2. **`cert_harvester.py`** *(toolkit)* — pulls every certificate ever
   issued for a domain pattern from `crt.sh`, dedupes, returns
   subdomains and issuance metadata.
3. **`github_dorks.py`** *(toolkit)* — GitHub code search runner with a
   curated dork list (AWS keys, RSA keys, internal hostnames, env files).
4. **`wayback_paths.py`** *(toolkit)* — Wayback CDX API runner,
   extracts URLs, query parameters, and per-extension counts.
5. **`breach_lookup.py`** *(toolkit)* — local breach corpus query using
   SHA-1 prefix indexing (HIBP-style); ships with a tiny demo corpus.
6. **`osint_runner.py`** — module-level orchestrator that runs items
   1-4 sequentially against a single target and produces a unified JSON.

---

## 9.13 Lab exercises

1. Pick a domain you own. Run `whois_asn.py` against it, then `cert_harvester.py`.
   Compare CT subdomains to your live DNS — anything obsolete?
2. Run `github_dorks.py` against your own GitHub username. Anything you'd
   rather not see indexed?
3. Run `wayback_paths.py` against your own blog or company domain. How
   many endpoints does archive.org know about that you forgot existed?
4. Build a local mini breach corpus from the included sample, run
   `breach_lookup.py` against your own emails. Expected: zero hits in
   the demo corpus, but you've validated the workflow.

---

## 9.14 Further reading

- **Justin Seitz, *Open Source Intelligence Techniques*** — encyclopedic.
- **Michael Bazzell, *Open Source Intelligence*** — investigator-oriented.
- **`OSINT Framework`** — `osintframework.com` — visual source map.
- **`The OSINT Curious Project`** — community blog and podcast.
- **DEF CON 26: *OSINT Tools and Techniques for Red Teams*** — Yael Basurto.
- **MITRE ATT&CK Recon TA0043** — every passive technique catalogued.

---

→ Next: [Module 10 · Active Recon & Network Mapping](10-active-recon.md).
