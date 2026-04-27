# 🎓 Certifications Roadmap

> Certifications are the cybersecurity industry's tax: necessary in some places, useless in others, expensive everywhere. This chapter is the honest map: what's worth getting, in what order, for what role, and at what cost.

## The brutal truth about certifications

Three audiences read your cert list:

1. **HR ATS (Applicant Tracking System)** — keyword filter. "OSCP" or "CISSP" listed in the JD will gate you out without it.
2. **Hiring manager** — uses certs as a signal of seriousness, not skill. Some respect them; some don't.
3. **Government / regulated industries** — *requires* specific certs for specific roles (DoD 8140, FedRAMP, PCI QSA).

If you're aiming at a startup, the right portfolio + GitHub + CTF profile beats a wall of certs. If you're aiming at a federal cyber role, the right cert is required. Read the room.

## The realistic cost of cybersecurity certifications

| Tier | Cert example | Total cost (training + exam) | Time to prep |
|---|---|---|---|
| Foundational | Security+ | $400–$800 | 4–8 weeks |
| Practical (entry) | eJPT, PNPT | $250–$400 | 4–8 weeks |
| Practical (mid) | OSCP, CRTO | $1,500–$2,500 | 3–6 months |
| Practical (advanced) | OSEP, OSED, OSWE | $1,800 each | 4–6 months each |
| GIAC SANS | GCIH, GCFA, etc. | $7,000–$10,000+ | 2 months focused |
| Senior management | CISSP | $700–$1,500 | 3–6 months (5y exp prereq) |

A common surprise: SANS courses dominate the price chart. Employers often pay for SANS — individuals rarely should.

## The path: how I'd plan it (no employer sponsorship)

If you're paying out of pocket and aiming for a hands-on cyber career, here's an opinionated 18-month track:

```
Month 1–2:    Security+ (foundational, $400)              → Resume keyword + DoD 8140 IAT II baseline
Month 3–6:    PNPT or eJPT (practical entry, $400)        → First practical cert, AD focus
Month 7–12:   OSCP (industry standard, $1,650)            → THE pentest cert
Month 13–15:  CRTO or OSEP (advanced, $400 / $1,800)      → Red team / evasion focus
Month 16–18:  Specialty (Cloud, AppSec, ICS, AI)          → Match to your target role
```

Total cash outlay: ~$3,000–$5,000 over 18 months. That's the realistic budget.

If your employer sponsors training, swap in SANS courses (GPEN, GCIH, GCFA) at the right tier — they're excellent if someone else is paying.

## Foundational

### CompTIA Security+ (SY0-701 as of 2024)

- **Cost**: ~$400 voucher; ~$200 with student/military/CompTIA membership discount
- **Format**: 90 min, multiple choice + performance-based
- **Why it matters**: HR ATS filter; **DoD 8570 IAT II baseline** — required for many federal roles even at junior level
- **Honest assessment**: knowledge cert; the material is broad and shallow. Useful if you're new; signaling-only if you've already done practical training.
- **Substitute**: ISC2 SSCP, GIAC GSEC, or just skip if you have a stronger cert

### CompTIA Network+ / A+

Useful only if you're entering from non-IT background. Otherwise skip. Network+ is comparable to a single chapter of a CCNA prep book.

### CompTIA CySA+

- **Cost**: ~$400
- **Why**: SOC L1 / Tier-1 analyst-level cert. **DoD 8570 CSSP**.
- **Honest assessment**: weak technical depth. Worth it for federal SOC roles, otherwise prefer BTL1.

## Practical (entry)

### eJPT (eLearnSecurity / INE)

- **Cost**: ~$250 (with INE Premium subscription) or just the exam ~$200
- **Format**: 48-hour practical with a network of machines. Open-book.
- **Why**: First practical cert for many; gentle, modern.
- **Honest assessment**: Easier than OSCP, well-paced. Good first practical if you're new to pentesting.

### PNPT (TCM Security)

- **Cost**: ~$400 (course + 2 exam attempts)
- **Format**: 5-day practical with full report deliverable
- **Why**: AD-heavy, modern, includes report-writing
- **Honest assessment**: Excellent value. Heath Adams' content is among the best in the industry. Some employers don't recognize it yet, but it's growing fast.
- **My take**: Better preparation for OSCP than OSCP's own labs.

### CPTS (HackTheBox Certified Pentesting Specialist)

- **Cost**: ~$590 with HTB Academy subscription
- **Format**: Hands-on 10-day practical exam + report
- **Why**: Modern, comprehensive, more rigorous than eJPT
- **Honest assessment**: Hot trajectory, increasingly recognized. HTB-style content. Great alternative if you find OSCP too OffSec-flavored.

### Burp Suite Certified Practitioner

- **Cost**: ~$99
- **Why**: Excellent web cert tied to PortSwigger's free Web Security Academy
- **Honest assessment**: Cheap, focused, solid. Skip if you're already deep in web; required reading otherwise.

## The OffSec ecosystem (industry standard for pentest roles)

OffSec (formerly Offensive Security) certs share a brutal reputation. They're hands-on practical exams that are actually hard, which is why they're valued.

### OSCP — PEN-200

- **Cost**: ~$1,650 (90-day lab access)
- **Format**: 24-hour exam + 24-hour report. Compromise 5 boxes (now includes AD set).
- **Why**: **The** practical pentest cert in industry. Almost universally recognized.
- **Honest assessment**: Modernized in 2023 (added AD set). Still hard. Lab is good but limited; supplement with HTB / TJNull's OSCP-like list / Proving Grounds.
- **DoD 8140**: counts toward CSSP-Infrastructure.
- **Pass rate**: ~30% first attempt (OffSec doesn't publish; estimates).

### OSWE — PEN-300 series, web focus

- **Cost**: ~$1,800
- **Format**: 48-hour practical, source code review → exploit chain
- **Why**: Hardest hands-on web cert. Whitebox auth-bypass-to-RCE thinking.
- **Honest assessment**: Challenging, well-respected. Doesn't broaden you much beyond web.

### OSEP — Evasion / AD / red team

- **Cost**: ~$1,800
- **Format**: 48-hour practical, evade AV/EDR while compromising AD
- **Why**: Modern red-team focus. Deep AV bypass + AD attack.
- **Honest assessment**: Excellent material, OPSEC-aware. Best OffSec cert for red team aspirants.

### OSED — Exploit dev (Windows)

- **Cost**: ~$1,800
- **Format**: 48-hour practical, write a Windows exploit (BOF + ROP)
- **Why**: Genuine binary exploitation cert.
- **Honest assessment**: Specialized; useful for VR roles. Less broadly recognized than OSCP.

### OSCE³ (the trinity)

Earned automatically by holding **OSWE + OSEP + OSED** simultaneously. Recognized as expert-level. Few people hold all three; it's a flex. ~$5,400+ in cert costs alone.

### OSEE — Advanced Windows Exploitation

- **Cost**: ~$5,000+ (instructor-led course in person/virtual)
- **Format**: 72-hour kernel + browser exploitation exam
- **Why**: Hardest cert in the industry, period.
- **Honest assessment**: For VR researchers and tier-1 offensive teams. Niche.

## Red team specialist track

### CRTO / CRTL (Zero-Point Security, "RastaMouse")

- **CRTO**: ~$400 lab + exam. Cobalt Strike + EDR evasion + AD red team.
- **CRTL**: ~$400. More advanced (LDAP attacks, SQL relay, ADCS, SCCM).
- **Why**: Exceptional value, modern content, well-respected
- **Honest assessment**: Best red-team-focused cert outside OffSec OSEP. RastaMouse's content is gold.

### CRTP / CRTE (Altered Security, Nikhil Mittal)

- **CRTP**: ~$249. Practical AD attacker.
- **CRTE**: ~$399. Enterprise AD escalation.
- **Why**: AD-focused practicals; strong in this niche
- **Honest assessment**: Cheap, hands-on, AD-deep. Good for AD-heavy environments.

## Defensive track

### BTL1 / BTL2 (Security Blue Team)

- **BTL1**: ~$500. SOC analyst hands-on cert. **The** entry-level blue team practical.
- **BTL2**: ~$1,000. Advanced (DFIR, threat hunting, malware).
- **Why**: Modern, hands-on, increasingly recognized
- **Honest assessment**: Hot trajectory. Replacing CySA+ in many resumes.

### CDSA / CCD (HackTheBox)

- **Cost**: HTB Academy subscription + cert; ~$590 each
- **Why**: HTB's defender-side practicals; rich Sherlocks-flavored exam content
- **Honest assessment**: Newer; growing recognition.

### GIAC SANS certs

The "premium" defensive certs. Each requires (or strongly suggests) a SANS course at $8,000–$10,000.

| Cert | Focus |
|---|---|
| **GCIH** | Incident handling — most common GIAC cert |
| **GCFA** | Forensic analyst — top of forensics field |
| **GCFR** | Cloud forensic responder |
| **GREM** | Reverse-engineering malware |
| **GCIA** | Intrusion analyst — packet/network deep dive |
| **GNFA** | Network forensic analyst |
| **GCTI** | Cyber threat intelligence |
| **GPEN** | Pen testing (knowledge-based) |
| **GXPN** | Exploit dev / advanced pentest |
| **GCDA** | Continuous monitoring / SIEM engineer |
| **GMON** | Continuous monitoring (intermediate) |
| **GCED** | Enterprise defender |
| **GMOB** | Mobile security |
| **GWAPT / GWEB** | Web app pentest |
| **GSEC** | Security essentials (broad) |
| **GISF / GISP** | Information security fundamentals / professional |
| **GSE** | The pinnacle — multi-discipline practical, very few hold it |

If your employer pays: GCIH and GCFA are widely respected and worth taking. Otherwise, the ROI is poor for self-pay.

## Cloud certs

Vendor certs are the fastest-growing area.

### AWS

- **AWS Certified Security – Specialty (SCS-C02)** — the cloud-AppSec/cloud-defender cert
- **Solutions Architect – Associate** as a prereq for context if not already cloud-fluent
- Cost: ~$300 each

### Azure / Microsoft

- **AZ-500 (Microsoft Security Engineer Associate)** — for Azure-focused roles
- **SC-200 (Microsoft Security Operations Analyst)** — Defender / Sentinel SOC focus
- **SC-100 (Microsoft Cybersecurity Architect)** — senior/strategy level
- **SC-300 (Identity & Access Admin)** — Entra ID focus
- **SC-400 (Information Protection Admin)** — Purview / DLP
- Cost: ~$165 each (free vouchers via Microsoft Learn often)

### GCP

- **Professional Cloud Security Engineer**
- Cost: ~$200

### Kubernetes

- **CKS (Certified Kubernetes Security Specialist)** — hands-on, 2 hours, very respected
- Cost: ~$395; requires CKA prereq

### Cloud-neutral

- **CCSK (Cloud Security Alliance)** — knowledge cert
- **CCSP (ISC²)** — management/architectural cloud security cert; requires 5y exp

## AppSec track

### CSSLP (ISC²)

- **Cost**: ~$700; requires 4y exp (waiver options)
- **Why**: Secure SDLC management focus
- **Honest assessment**: Knowledge cert. Useful for management-track or compliance-heavy AppSec roles.

### Burp Suite Certified Practitioner / Pro

Mentioned above. Excellent value for web-focused roles.

### eWPTX (eLearnSecurity Web Pentester eXtreme)

- **Cost**: ~$400
- **Why**: Modern web pentest practical
- **Honest assessment**: Cheaper than OSWE; less rigorous but still respected.

## Senior / management

### CISSP (ISC²)

- **Cost**: ~$750 exam + endorsement process
- **Format**: 100–150 question CAT, 4 hours
- **Prereq**: 5 years cumulative cyber experience (1 year waivable with degree)
- **Why**: HR/management filter for senior roles. Very common requirement.
- **Honest assessment**: Knowledge cert. Broad and shallow. The board-level cert. **DoD 8570 IAT III baseline.**

### CCSP (ISC²)

- Cloud-flavored CISSP. Same audience.

### CISM (ISACA)

- Management-focused. Common for CISO-track resumes.

### CRISC (ISACA)

- Risk and control. Useful for GRC roles.

### CISA (ISACA)

- Audit-focused. Common for IT auditor / compliance roles.

## Country-specific notes

### India

- **CEH** (EC-Council) — overrated globally but **widely recognized in India** by HR
- **CHFI** (EC-Council) — forensic equivalent; same caveat
- **CCISO** (EC-Council) — appears in some senior Indian gov roles
- **DSCI certifications** — DSCI Certified Privacy Lead Assessor, etc., recognized by Indian industry
- **GATE** — not a cert, but a national engineering test that gates entry into IIT M.Tech and DRDO/CDAC research roles
- **CSA / NSCS / CERT-In affiliated training** — when offered, take it

### United States

- **DoD 8140 (replaces 8570)** — work-role-specific cert requirements for DoD positions; some roles require multiple
- **NICE Framework** mapping — every federal cyber job mapped to a "work role" with KSA + cert recommendations
- **Q-clearance certifications** — some DOE positions list specific cert requirements

### EU / UK

- **CREST** certifications (CRT, CCT-INF, CCT-APP, etc.) — required for UK CHECK pentests, common in EU
- **Cyber Essentials Plus assessor** — UK-specific
- **TIBER-EU lead/red team certifications** — required for regulated red-team engagements at EU financial institutions

## What I'd skip

Honest opinions, certain to make some readers angry:

- **CEH** — outside India/MENA, low respect-to-cost ratio. Skip unless your specific employer requires it.
- **CompTIA PenTest+** — overlaps Security+ + OSCP; not respected at either level.
- **Most EC-Council certs** beyond CEH/CHFI — inconsistent quality.
- **"Master CISO" / "Cyber Leadership"** programs from random universities — bootcamp pricing, debatable value.

## What I'd add to a degree

If you're a CS / IT student now, prioritize in this order:

1. CTF practice + portfolio (GitHub) — free, highest signal
2. Security+ (you'll need it for most internships)
3. PNPT or eJPT (your first practical)
4. OSCP if your career path is offensive
5. Internship — vastly more valuable than any cert

Government scholarships:

- **US**: [CyberCorps Scholarship for Service](https://sfs.opm.gov/) — full ride + 3-year federal service commitment
- **US**: [DoD Cyber Scholarship Program (DoD CySP)](https://public.cyber.mil/cspg/dod-cyber-scholarship-program/)
- **India**: [Cyber Surakshit Bharat](https://www.csb.gov.in/) — ISEA-affiliated training; **C-DAC scholarships**; **AICTE / DRDO PhD support**

## Renewing certs — the part nobody mentions

Most certs require renewal:

- **CompTIA**: 50 CEUs every 3 years + ~$50/yr maintenance
- **ISC²**: 120 CPEs over 3 years + ~$135/yr AMF
- **GIAC**: 36 CPEs every 4 years + ~$499/4yr renewal fee
- **OffSec**: One-time, no renewal (great policy)
- **EC-Council**: 120 ECEs over 3 years + ~$80/yr
- **ISACA**: 120 CPEs over 3 years + dues

Budget time + cash for renewals. CISSP + CISM + CCSP held simultaneously can cost $400+/yr in maintenance fees alone.

## Mapping certs to roles

| Target role | Recommended certs |
|---|---|
| **SOC L1** | Security+, BTL1, SC-200 |
| **SOC L2 / Threat hunter** | BTL2, GCIH, GCFA, eCTHPv2 |
| **DFIR** | GCFA, GCFR, GREM, EnCE |
| **Pentester (consulting)** | OSCP, CRTO, then OSEP/OSWE/OSED |
| **Red team** | OSCP, CRTO, CRTL, OSEP |
| **AppSec engineer** | OSWE, CSSLP, Burp Cert Pro, language-specific tools |
| **Cloud security** | AWS Security Specialty, Azure SC-200/SC-100, CKS, CCSK |
| **GRC / risk** | CISSP, CISM, CRISC, CCSP |
| **Threat intel** | GCTI, CRTIA |
| **CISO track** | CISSP, CISM, CISA, CCISO |
| **NSA / IC roles** | TS/SCI eligibility, OSCP/CISSP, OSEE for elite |
| **CISA / federal civilian** | Security+, CISSP, OSCP, CySA+ |
| **CERT-In / Indian gov** | CEH, OSCP, CISSP, GATE-eligible academic |
| **DRDO / CDAC** | M.Tech with cyber specialty, GATE, OSCP |

## Realistic timelines

People often overestimate how fast they'll burn through certs. Honest averages:

- Security+: 6 weeks part-time
- eJPT: 2 months part-time
- PNPT: 3 months part-time
- OSCP: 6 months focused (12 months realistic for first-attempt pass)
- OSEP / OSWE / OSED: 4–6 months each, post-OSCP
- CISSP: 3 months focused, after meeting experience requirement

If someone tells you they did OSCP in a month with no prior experience, they either lied or bought a cheat dump. Both are red flags; ignore them.

## Hands-on lab platforms (cheap practice)

Pair every cert with parallel lab time. Top platforms:

- **HackTheBox / HTB Academy** — paid; the de facto practice ground
- **TryHackMe** — paid; gentler than HTB, more guided
- **OffSec Proving Grounds Practice** — paid; OSCP-aligned
- **PortSwigger Web Security Academy** — free; required for any web cert
- **Hack The Box CDSA/CCD modules** — defender-side, modern
- **Pwn College** (ASU) — free; deep binary exploitation course
- **Vulnlab** — modern multi-machine red team labs
- **Letsdefend** — SOC simulation; for blue path
- **CyberDefenders** — DFIR / blue challenges

## Recommended reading

- *The Cybersecurity Career Guide* — Alyssa Miller
- *Cybersecurity Career Master Plan* — Helvik et al.
- *How to Hack Like a GHOST / GOD* — Sparc Flow (offensive trade)
- The actual CompTIA / OffSec / ISC² syllabi — read them before you commit dollars

## Interview questions

1. *"Walk me through your cert plan and why you chose it."*
2. *"How do you prepare for a cert that's pure knowledge vs one that's hands-on?"*
3. *"Why OSCP and not CEH?"* (or vice versa, depending on the employer)
4. *"What did you learn from your hardest cert?"*
5. *"Show me a project / writeup that demonstrates the cert wasn't just a check-box."*

---

[← Reporting](reporting.md)  ·  [Building a Security Portfolio →](portfolio.md)
