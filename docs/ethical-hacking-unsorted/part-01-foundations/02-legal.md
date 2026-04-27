# 02 · Legal & Ethical Framework

!!! danger "This module is non-negotiable"
    Every year, technically talented people end their security careers — or go to federal prison — because they skipped this material. Read it. Re-read it. Internalize the instincts. Nothing you learn in Modules 03–66 is useful if you lose your freedom, your clearance, or your ability to be bonded.

## 2.1 The primary US statute: the Computer Fraud and Abuse Act

**18 U.S.C. § 1030 — the Computer Fraud and Abuse Act (CFAA)** — is the federal statute that criminalizes unauthorized access to a "protected computer." For practical purposes, every internet-connected computer in the US qualifies as protected.

The CFAA creates criminal and civil liability for, among other things:

| Subsection | Prohibited conduct |
|------------|-------------------|
| § 1030(a)(1) | Accessing a computer without authorization and obtaining classified information |
| § 1030(a)(2) | Accessing a computer without authorization and obtaining any information |
| § 1030(a)(3) | Accessing a nonpublic US government computer without authorization |
| § 1030(a)(4) | Accessing a computer to defraud and obtain value |
| § 1030(a)(5) | Transmitting code/commands that intentionally cause damage |
| § 1030(a)(6) | Trafficking in passwords |
| § 1030(a)(7) | Extortion involving computers (ransomware territory) |

Penalties scale from misdemeanor (first offense, no damage) to **10–20 years** per count depending on circumstances. The statute has been amended multiple times (USA PATRIOT Act, Identity Theft Enforcement and Restitution Act). Always read the current text, not the one you learned in school.

### 2.1.1 The two phrases that define your boundary

Every question about whether your actions are legal under the CFAA collapses to two phrases:

- **"without authorization"** — you had no permission at all.
- **"exceeds authorized access"** — you had *some* permission and went past it.

The 2021 Supreme Court decision in **Van Buren v. United States** narrowed "exceeds authorized access" to mean accessing **files, folders, or databases** you weren't allowed into — *not* using access you did have for an improper purpose. This was a relief for researchers, but it does NOT make it legal to poke at systems you were never authorized to access in the first place.

### 2.1.2 What "authorization" looks like in practice

Authorization is a spectrum:

1. **Your own lab, your own hardware, your own network** → always fine.
2. **A platform-provided lab** (HackTheBox, TryHackMe, OffSec PG, PortSwigger Academy) → authorization comes from the platform's terms; stay within them.
3. **Bug bounty program in scope** → authorization comes from the program's published policy. Out-of-scope = no authorization.
4. **Penetration test with signed SOW + ROE** → authorization is the SOW + ROE + written kick-off email.
5. **Employer engagement** → authorization is your written job description plus an engagement-specific authorization memo.
6. **Classified / government mission** → authorization is the mission order; you will not lack for documentation.

Absence of any of these for a target = no authorization. There is no middle ground.

## 2.2 Other US federal statutes you must know

### 2.2.1 Electronic Communications Privacy Act (ECPA) / Wiretap Act

**18 U.S.C. §§ 2510–2523.** Makes it a crime to intercept, disclose, or use the contents of wire, oral, or electronic communications. Relevant when you:

- Run packet sniffers on networks you don't own.
- Use MITM techniques against real traffic.
- Access stored communications without authorization (Stored Communications Act, § 2701).

For pentesters: if your ROE does not explicitly authorize packet capture, don't capture packets.

### 2.2.2 Digital Millennium Copyright Act (DMCA)

**17 U.S.C. § 1201** prohibits circumventing technological protection measures (TPMs) on copyrighted works. Historically this criminalized even benign security research on DRM'd firmware. The **DMCA Security Research Exemption** (now permanent, renewed every three years by the Library of Congress) creates a safe harbor for "good faith security research" on certain consumer devices. But:

- The exemption is narrow — read the current Federal Register text.
- It does not cover distribution of circumvention tools.
- It does not preempt CFAA.

### 2.2.3 Economic Espionage Act (EEA)

**18 U.S.C. §§ 1831–1839.** Criminalizes theft of trade secrets. Important for insider-threat scenarios and when handling client data.

### 2.2.4 Export controls (EAR / ITAR)

Offensive security tools can fall under the **Export Administration Regulations** (15 CFR 730–774) and occasionally **ITAR** (22 CFR 120–130). The **Wassenaar Arrangement** covers "intrusion software" exports. Implications:

- Publishing exploit code on GitHub may have export-control implications if it's unlicensed cryptographic or "cyber" content.
- Selling offensive tooling across borders can require a license.
- For federal work, this becomes a significant compliance burden.

Most researchers are fine publishing academic PoC code, but when you start working for defense contractors, export controls become a daily concern.

### 2.2.5 Sarbanes-Oxley (SOX), HIPAA, GLBA, PCI-DSS

These aren't hacking statutes per se, but they govern what happens to the data you touch during engagements:

- **HIPAA** (health) — if your engagement scope contains PHI, your firm must be a Business Associate with a BAA.
- **PCI-DSS** (payment cards) — if you're testing a CDE, special methodology applies (PCI ASV, qualified pentester requirements).
- **GLBA** (financial) — imposes confidentiality obligations on customer data.
- **SOX** — impacts how findings are documented and disclosed for publicly traded companies.

## 2.3 State-level computer crime laws

Every US state has its own computer crime statute, and they are frequently *broader* than the CFAA. Examples:

- **California Penal Code § 502** — very broad; criminalizes "without permission" access.
- **New York Penal Law § 156** — computer trespass, criminal tampering.
- **Texas Penal Code § 33.02** — breach of computer security.

A single action can generate both federal (CFAA) and state charges. Prosecutors often charge both to maximize leverage.

## 2.4 International considerations

Short version: it gets complicated fast.

- **UK:** Computer Misuse Act 1990 (as amended). Broadly analogous to CFAA.
- **EU:** NIS2 Directive, GDPR (for personal-data handling).
- **Canada:** Criminal Code §§ 342.1, 430(1.1).
- **Australia:** Criminal Code Act 1995 Part 10.7.
- **Germany:** StGB § 202a-d (the "hacker paragraphs" — so strict that possessing certain tools has been prosecuted).

If your engagement touches any non-US infrastructure, get local counsel. If you're a US citizen working overseas, US law often still follows you.

## 2.5 Authorization artifacts you'll work with

Anatomy of a properly authorized engagement:

### 2.5.1 Statement of Work (SOW)

Contract between your firm and the client. Defines:

- Work to be performed.
- Deliverables.
- Timeline.
- Price.
- Assumptions and dependencies.
- Limitations of liability.

### 2.5.2 Rules of Engagement (ROE)

The operational bible. Defines:

- **In-scope targets** — IP ranges, domains, apps, accounts.
- **Out-of-scope targets** — what you cannot touch even if reachable.
- **Authorized techniques** — social engineering? DoS testing? Malware drops?
- **Testing windows** — calendar dates, clock hours, blackout periods.
- **Data handling** — where findings live, how evidence is stored, retention.
- **Emergency contact** — who to call if something breaks production.
- **Stop conditions** — triggers that halt testing (production incident, credential exposure, law enforcement call).
- **Reporting requirements** — artifact formats, timelines, who receives what.

### 2.5.3 Authorization Letter / "Get Out of Jail Free" card

A signed, printed letter from the client's authorizing officer (usually CISO or legal) stating:

- Who you are.
- What you are authorized to do.
- The date range of authorization.
- A phone number to verify.

Keep this on your person during on-site engagements. If a building guard catches you tailgating, this is what de-escalates the conversation.

### 2.5.4 Business Associate Agreement / NDA

For regulated data (HIPAA BAA) or confidentiality generally (NDA).

### 2.5.5 Change control approval

For anything that modifies state (exploit execution against production) — many mature clients require a change ticket.

## 2.6 Rules-of-Engagement checklist (use before every engagement)

- [ ] IP ranges and domains clearly enumerated with CIDR notation
- [ ] Out-of-scope list explicit (especially shared infrastructure, third-party SaaS)
- [ ] Social engineering permissions (phishing, pretexting, phone, physical) each called out
- [ ] Credential handling policy (found creds: report only? use to pivot? to what depth?)
- [ ] Data exfiltration boundary (prove-it with one row, not the full dump)
- [ ] Testing window (timezone-aware; business hours vs off-hours)
- [ ] Emergency contacts with 24/7 phone numbers
- [ ] Communication channel (encrypted — Signal, Wire, or enterprise secure messaging)
- [ ] Stop-work conditions defined
- [ ] Evidence retention policy (who keeps what, for how long, encrypted at rest)
- [ ] Report format and distribution list
- [ ] Retest timeline
- [ ] All signatures captured (yours, theirs, date-stamped)

## 2.7 Bug bounty legal framework

Bug bounties ≠ universal permission. Each program has:

- A **scope** (in/out domains, apps, APIs).
- **Testing restrictions** (rate limits, specific techniques prohibited).
- **Safe harbor language** (some programs; not all).
- **A disclosure policy** (when you can talk publicly).

Read the program's policy **before** starting. If the company has no stated safe harbor, you are still at CFAA risk even for good-faith testing. Look for programs that reference the **[disclose.io](https://disclose.io/)** core terms or a similar standardized safe harbor.

Notorious failure mode: researcher finds an issue on `company.com`, reports to security team, gets thanked, then finds another issue on `partner.company.com`. Partner is out of scope. Partner sues. Researcher's lawyer bills run past their bounty earnings.

## 2.8 Responsible disclosure vs full disclosure vs 0-day markets

Three disclosure philosophies:

1. **Coordinated (responsible) disclosure** — report privately to vendor, give them reasonable time (90 days is standard via Project Zero), publish after patch.
2. **Full disclosure** — publish everything immediately. Historically used to force lazy vendors.
3. **Selling** — private sale to a broker (Zerodium, Crowdfense) or directly to a government buyer. Legal but ethically and politically fraught; changes your career trajectory permanently.

For your career path (ethical hacking → gov), **always coordinated disclosure**. Respectable agencies will not hire someone who sold 0-days to non-government brokers.

Tools for coordinated disclosure:

- **CVE assignment** — via MITRE (cveform.mitre.org), a CNA (CVE Numbering Authority), or automatically via some vendors.
- **CISA's Vulnerability Disclosure Program** — `cyber.dhs.gov/vdp/` for US federal agencies.
- **Vendor-specific PSIRTs** — most major software vendors have security@ addresses and PGP keys.

## 2.9 Real cases that should shape your instincts

### 2.9.1 United States v. Auernheimer (2012) — "weev"

Facts: Andrew Auernheimer and a collaborator iterated ICC-ID numbers on an AT&T public URL to retrieve email addresses of iPad owners. No password bypass; just HTTP GET requests to a publicly reachable endpoint.

Outcome: convicted of CFAA violation and identity theft. Sentence vacated on appeal (2014) on venue grounds, not merits.

Lesson: even "public-facing URL iteration" can be charged under the CFAA if the feeling of the action is "unauthorized." The law is as much about perception as technicality.

### 2.9.2 United States v. Swartz (2011–2013) — Aaron Swartz

Facts: Aaron Swartz downloaded academic papers en masse from JSTOR via an MIT network closet. JSTOR declined to press charges. Federal prosecutors pursued 13 felony counts totaling potentially 35 years.

Outcome: Swartz took his own life before trial.

Lesson: prosecutorial discretion under the CFAA is unreviewable and can be devastating. Technical legality is not legal safety.

### 2.9.3 Van Buren v. United States (2021)

Facts: a police officer used his legitimate access to a law enforcement database to look up a license plate for a bribe.

Outcome: Supreme Court narrowed "exceeds authorized access" to mean breaching technical barriers (files/databases you can't reach), not "using allowed access improperly."

Lesson: a welcome narrowing for researchers, but it does NOT expand what you can do without authorization.

### 2.9.4 The Coalfire / Iowa courthouse incident (2019)

Facts: Coalfire pentesters, hired by the State Court Administration of Iowa, performed authorized physical pentesting of a county courthouse. Local sheriff — who hadn't been looped in — arrested them. They spent a night in jail.

Outcome: charges eventually dropped, but the contract dispute between Iowa and Coalfire dragged on.

Lesson: even with authorization, physical testing must include notification to local law enforcement. A "get out of jail free" letter + a phone call to verify is not optional.

### 2.9.5 Marcus Hutchins / MalwareTech (2017–2019)

Facts: Researcher famous for sinkholing WannaCry was arrested in the US on old charges related to Kronos banking malware he allegedly co-authored years earlier as a teenager.

Outcome: pled guilty to reduced charges; sentenced to time served.

Lesson: your teenage GitHub and IRC history matters. Don't write malware for sale. Don't keep incriminating repos. Clean your history. The clearance process will find everything.

## 2.10 Ethics beyond the law

Legal and ethical are not the same. Things that are technically legal but you won't do if you want to work at the agency level:

- Selling exploits to private brokers.
- Doxing security researchers you disagree with.
- "Helping" people without their informed consent.
- Using your offensive skills in personal disputes (exes, landlords, online rivals).
- Consulting for clients whose mission conflicts with your ethics (some dictators hire cleared US firms via intermediaries; know who is paying).

A good gut-check: **if this ended up on the front page of the Washington Post, would I be comfortable?**

## 2.11 Script · `scope_validator.py`

Pre-flight check. Given an engagement config and a target (IP, hostname, or URL), tells you whether the target is in scope before you run anything.

**Location:** `scripts/part-01/02-legal/scope_validator.py`

```bash
# Is this target in scope?
python scope_validator.py --config engagement.yaml --target 192.168.50.12

# Validate a list
python scope_validator.py --config engagement.yaml --targets-file targets.txt

# Use as exit-code gate in a pipeline
python scope_validator.py --config engagement.yaml --target $T && nmap -sC -sV $T
```

## 2.12 Script · `roe_checker.py`

Parses an ROE YAML and checks whether a planned action (technique, target, time) is allowed. Sits between your head and any tool you're about to run.

**Location:** `scripts/part-01/02-legal/roe_checker.py`

```bash
python roe_checker.py --roe engagement.yaml \
    --action "T1190-exploit-public-facing-app" \
    --target "api.client.example" \
    --when "2026-05-12T14:30-04:00"
```

## 2.13 Exercises

1. **Write your own ROE template.** Take the checklist in §2.6 and build a reusable YAML template. Save it to your `redshift-toolkit/utils/templates/` directory.
2. **Read the full CFAA.** Not the summary. The statute. 18 U.S.C. § 1030. Takes 20 minutes. Do it.
3. **Read three CFAA case summaries** beyond the ones here. Suggested: *United States v. Nosal* (9th Cir.), *hiQ Labs v. LinkedIn*, *United States v. Valle*.
4. **Find a bug bounty program and read its policy in full** — pick Tesla, Microsoft, or Apple. Note: scope, safe harbor, exclusions, disclosure timeline. Compare two programs' safe-harbor language.
5. **Write a scope-violation tabletop.** Describe, in writing, three scenarios where you'd be tempted to step outside scope during an engagement, and how you'd handle each.

## 2.14 Further reading

- **18 U.S.C. § 1030** — [full text on house.gov](https://www.govinfo.gov/content/pkg/USCODE-2023-title18/pdf/USCODE-2023-title18-partI-chap47-sec1030.pdf)
- **disclose.io** — standardized safe harbor language
- **A Framework for Programs of Vulnerability Disclosure and Handling** — ISO/IEC 29147 and 30111
- **CISA Binding Operational Directive 20-01** — VDP for federal civilian agencies
- **"A Legal Guide to Bug Bounty Programs"** — Lee Matheson, HackerOne archived whitepaper
- **"Tallinn Manual 2.0"** — international law applied to cyber operations (heavy reading; relevant for gov career)
- **EFF Coders' Rights Project** — <https://www.eff.org/issues/coders>

!!! warning "Before moving on"
    Confirm you can answer these out loud without notes:
    
    1. What are the two CFAA phrases that define your boundary?
    2. What artifacts must you have in hand before running a scan against a client's IP?
    3. What do you do when you find data exfil-worthy PII during a bounded pentest?
    4. What happens if your ROE doesn't cover something and you find an interesting vector?
    
    If any of those four are fuzzy, re-read the relevant section above before starting Module 03.
