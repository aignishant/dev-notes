# 📝 Phase 6 — Career & Certifications

> The make-or-break phase. Knowing the technical material is necessary but not sufficient. To **get hired** — especially into government agencies — you need certs, a portfolio, interview skill, and an understanding of how recruiting actually works.

This phase is the most concrete one. Tick the boxes here and you will get interviews.

## Chapters in this phase

| # | Chapter | Focus |
|---|---|---|
| 6.1 | Pentest Reporting | Executive summary, technical findings, evidence, risk rating, remediation |
| 6.2 | Certifications Roadmap | Sec+ → eJPT → CPTS / OSCP → OSEP/OSWE/OSED → CISSP/OSCE3 |
| 6.3 | Building a Portfolio | GitHub, blog, CTF profile, writeups, public talks |
| 6.4 | LinkedIn, Resume & Interviewing | Industry-specific resume tips, common interview formats |
| 6.5 | 🇺🇸 US Government Cyber Careers | NSA, CISA, FBI, USCYBERCOM, DoD civilian, clearances |
| 6.6 | 🇮🇳 India Government Cyber Careers | CERT-In, NCIIPC, NTRO, DRDO, I4C, DCyA |
| 6.7 | CTFs & Bug Bounty | Picking platforms, scoring, monetization |
| 6.8 | Continuous Learning | Conferences, podcasts, RSS, mentors |

---

## 🎓 Certifications Roadmap (Detailed)

### Foundational (start here regardless of track)

- **CompTIA Security+** — vendor-neutral, widely recognized, DoD 8570/8140 baseline.
  - Cost: ~$400; voucher discounts available.
  - Time: 4–8 weeks of focused study.
  - Why: HR filters often require it. Solid fundamentals.

### Practical pentest entry

- **eJPT (INE)** — entry-level practical. ~$249. Excellent first practical cert.
- **PNPT (TCM Security)** — modern, AD-focused, includes report. ~$399. Highly respected.
- **CPTS (HTB Academy)** — robust, modern alternative to OSCP. ~$590 (with Academy sub).

### Industry-standard practical

- **OSCP (PEN-200)** — the canonical practical pentest cert. ~$1,649 (90 days lab).
  - 24-hour exam → 5 machines + AD set.
  - Required by many DoD contractors.

### Senior / specialized

- **OSWE** (PEN-300 series) — advanced web exploitation, source code review.
- **OSEP** — advanced evasion, AD, anti-AV.
- **OSED** — Windows exploit development.
- **OSCE³** — earned by holding all three above.
- **CRTP / CRTE / CRTM** (Altered Security) — Active Directory specialist track.

### Defense / SOC / DFIR

- **CySA+** (CompTIA) — SOC analyst.
- **GCIH, GCFE, GCFA, GREM, GCIA, GNFA, GCTI** (SANS GIAC) — gold standard for blue team.
- **GSE** — SANS's most prestigious.
- **Microsoft SC-200** — Sentinel/Defender focused, free voucher options.

### Leadership / management

- **CISSP** (ISC²) — required for many senior / management roles. 5+ years experience needed.
- **CISM, CRISC** (ISACA) — risk and management.
- **CCSP** (ISC²) — cloud-focused.

### Cloud

- **AWS Security Specialty**
- **Azure AZ-500** + **SC-100**
- **GCP Professional Cloud Security Engineer**
- **CKS** — Kubernetes Security

---

## 💼 Resume That Lands Interviews

A few rules that work:

1. **Tailor to the role.** SOC L1 ≠ pentester ≠ AppSec engineer. One resume per role-type.
2. **Lead with results.** "Reduced false positives by 35% by writing 12 Sigma rules" beats "wrote Sigma rules".
3. **Show artifacts.** Link to GitHub, writeups, talks, CVEs you've reported, bug bounty profile.
4. **Quantify everything.** "Reviewed 8 microservices, found 14 vulnerabilities, 3 critical."
5. **Keywords for ATS.** Mirror the JD: "OSCP, Burp Suite, CrowdStrike, Splunk, ATT&CK, Sigma."
6. **One page** until you have ~10 years of relevant experience.

### Sample bullet patterns

- "Built a Python tool (`tool-name`, ★ N stars) that automated X, saving Y hours/week."
- "Identified [vuln type] in [system], leading to [impact]; reported via [channel]; CVE-XXXX-XXXX."
- "Tuned N detections in [SIEM], reducing alert fatigue by Z% over Q quarters."
- "Solved N HackTheBox / TryHackMe boxes with public writeups; ranked top X% globally."

---

## 🇺🇸 US Government Cybersecurity Careers

### Major employers

| Agency | Mission | Typical roles |
|---|---|---|
| **NSA** | Signals intelligence, cyber defense | CNE/CNA operators, cryptanalysts, RE engineers |
| **CISA** | Critical infrastructure defense | Threat hunters, IR, vuln management, red team (CSD) |
| **FBI Cyber Division** | Cyber crime investigation | Special Agents, computer scientists, intel analysts |
| **USCYBERCOM** | Military cyber | Military and civilian operators |
| **DoD components** | Defensive + offensive | RMF assessors, AppSec, pentesters |
| **DOE National Labs** (LLNL, LANL, ORNL, PNNL, INL, Sandia) | Research, ICS/OT | Researchers, RE, ICS specialists |
| **DHS / TSA / Coast Guard** | Mission-specific | SOC, IR, AppSec |
| **Secret Service** | Financial crime, network intrusion | Investigators, forensics |
| **NIST** | Standards | Researchers, framework authors |
| **Federal Reserve / Treasury** | Financial sector | SOC, IR, AppSec |

### How federal hiring works

- Almost all roles posted on **USAJOBS** (`usajobs.gov`).
- Roles are at **GS-7 through GS-15** (general schedule); **SES** for executive.
- Cybersecurity uses **GS-2210** (info tech specialist), **GS-1550** (computer scientist), **GS-1801** (general inspection/investigation), **GS-1811** (criminal investigator) for FBI agents.
- **DCWF / NICE Framework** — every cyber role mapped to a "work role" code (e.g., **PR-VAM-001** = Vulnerability Assessment Analyst).
- Apply early; closing dates can be sudden.

### Special hiring authorities

- **Cybersecurity Talent Management System (CTMS)** at CISA — bypasses standard GS pay scales.
- **Cyber Excepted Service (CES)** at DoD — flexible pay/grades.
- **Pathways Program** — internships and recent-grad track.
- **Direct Hire Authority** for cyber.
- **Scholarship for Service (SFS)** — full ride + 3-year service commitment.
- **DoD Cyber Scholarship Program**.

### Security clearances

- **Public Trust** — basic vetting.
- **Secret** — most common for cyber civilians; ~3–6 months.
- **Top Secret (TS)** — adds in-depth investigation.
- **TS/SCI** — Sensitive Compartmented Information; required at NSA / IC.
- **TS/SCI w/ poly** — full-scope or counterintelligence polygraph.

The clearance is **sponsored by the employer**. You can't get one on your own. Don't lie on the **SF-86**. Drug history, foreign contacts, financial issues are the most common disqualifiers — but most are mitigable.

### Citizenship
- US citizenship required for cleared roles.
- Some cleared roles also require birth in the US (very rare; mostly IC).

### Pay

- **GS pay tables** are public.
- Base + locality (DC, SF, NYC have higher locality).
- DoD/IC can pay more via CES/CTMS.

### Tips for federal cyber jobs

1. Read the **vacancy announcement carefully**. Self-rate honestly on the questionnaire.
2. Tailor your resume to the **specific KSAs** listed.
3. Federal resumes can be 4–6 pages — the opposite of industry.
4. Apply to multiple announcements of the same role.
5. Network at **AFCEA**, **ISC²**, **(ISC)² Capital Region**, **DEF CON**, **BSides DC**.
6. Consider **contracting first** (Booz Allen, Leidos, Raytheon, MITRE, Mandiant, GDIT) — easier entry, equivalent work, can transition later.

---

## 🇮🇳 India Government Cybersecurity Careers

### Major employers

| Agency | Mission | Reports to |
|---|---|---|
| **CERT-In** | National Computer Emergency Response Team | MeitY |
| **NCIIPC** | Critical Information Infrastructure Protection | NTRO / NSCS |
| **NTRO** | National Technical Research Organisation (technical intel) | NSCS / PMO |
| **DRDO** (incl. **CAIR, DESC**) | Defence R&D, including cyber | MoD |
| **I4C** | Indian Cyber Crime Coordination Centre | MHA |
| **Defence Cyber Agency (DCyA)** | Tri-services cyber | MoD |
| **MeitY / National Cyber Security Coordinator** | Policy, coordination | PMO |
| **NCSCS / NSCS Cyber Security Division** | National strategy | PMO |
| **Intelligence Bureau (IB), R&AW** | Intel agencies | MHA / Cabinet Sec |
| **State LEAs / Cyber Cells** | State cyber crime | State Govts |
| **CDAC** | Govt R&D, training | MeitY |
| **IIT Cyber Centres** (e.g., IIT-K C3iHub, IIT-B Trust Lab) | Research, hiring pipeline | Academic |
| **Public Sector** — RBI, SEBI, NPCI, ISRO, BEL, BSNL | Sector cyber | Various |

### How recruitment works in India

Multiple channels. There is **no single USAJOBS equivalent**.

1. **UPSC / SSC exams** — civil services route (general; can be assigned to MeitY, MHA, DoT cyber roles).
2. **Direct recruitment** at MeitY, CERT-In, NCIIPC — periodic notifications, project-mode + permanent.
3. **DRDO RAC** — DRDO Recruitment & Assessment Centre; technical/engineering roles.
4. **I4C** notifications — periodic, often via NIC.
5. **Defence Cyber Agency** — primarily through tri-services + civilian project contracts.
6. **Public Sector Banks / RBI / NPCI** — separate exams (IBPS, RBI Grade B).
7. **C-DAC** — recruits via online tests, walk-ins.
8. **Indian Armed Forces Cyber Roles** — through NDA, CDS, AFCAT, TES, Tech Entry Schemes; ITS / SSC commissions; lateral entry for officers.
9. **State police cyber cells** — via state PSCs.
10. **GATE → IITs → Govt labs** — research roles via M.Tech / PhD programs.

### Helpful resources to monitor

- **CERT-In notifications**: `https://www.cert-in.org.in/`
- **MeitY careers**: `https://www.meity.gov.in/`
- **NCIIPC**: `https://nciipc.gov.in/`
- **DRDO**: `https://drdo.gov.in/careers`
- **C-DAC**: `https://cdac.in/`
- **I4C**: `https://i4c.mha.gov.in/`
- **National Career Service**: `https://www.ncs.gov.in/`

### What helps in India

1. **Strong technical foundation** + **portfolio** are weighted heavily.
2. **OSCP / CEH / CHFI / CCNA Security** are widely recognized.
3. **B.Tech (IT/CS) / M.Tech in Cyber Security / MCA** are typical academic backgrounds.
4. **GATE score** — useful for govt research labs.
5. **Hackathons / CTFs** — Smart India Hackathon, c0c0n CTF, NullCon CTF, CTFTime presence is a real signal.
6. **Speaking at NullCon, c0c0n, BSides Delhi/Bangalore** — visibility.
7. **Contract / project mode** roles at CERT-In and NCIIPC are common entry points.
8. **Public sector banks / NPCI / SEBI** are excellent stepping stones.

### Salary expectations (rough, India)

- Govt direct recruitment: ₹6–18 LPA depending on grade and project mode.
- Public sector banks / RBI cyber: ₹12–25 LPA.
- DRDO Scientist B: ~₹12–14 LPA initial CTC.
- Top private (Mandiant India, FireEye, Palo Alto, EY, Big4): ₹15–60+ LPA depending on level.

---

## 🏆 CTFs & Bug Bounty

### Top CTF platforms

- **HackTheBox** — pro-style boxes, AD, web, RE, pwn, crypto.
- **TryHackMe** — guided rooms; great for beginners.
- **PortSwigger Web Security Academy** — free, the gold standard for web.
- **OverTheWire / PicoCTF / Pwn College** — fundamentals.
- **CTFtime** — calendar of all major time-bound CTFs.
- **NullCon HackIM, c0c0n CTF, Smart India Hackathon (Cyber), Indian CTF League** — India-specific.

### Bug bounty platforms

- **HackerOne**, **Bugcrowd**, **Intigriti**, **YesWeHack**, **Synack** (invite-only).
- **Indian Bug Bounty programs**: Paytm, MakeMyTrip, Flipkart (various, sometimes private).
- **ZeroDay Initiative** for serious researchers.

### Pacing

A realistic CTF/BB target:
- **First 6 months** — 25 boxes solved, 3 public writeups, 1 valid bug bounty submission (any severity).
- **Year 1** — 50+ boxes, OSCP-level, 5–10 valid BB submissions.

---

## 🧭 Continuous Learning

| Type | Recommendations |
|---|---|
| **Podcasts** | Risky Business, Darknet Diaries, Hacking Humans, Hackable?, SANS Internet StormCast |
| **YouTube** | IppSec, John Hammond, LiveOverflow, 0xdf, Conda, S1REN, Kitboga |
| **Blogs** | Krebs on Security, The Hacker News, Bleeping Computer, Mandiant blog, MS Threat Intel, Project Zero |
| **Newsletters** | tl;dr sec, return-on-security, Risky.biz, CISA Cybersecurity Advisories |
| **Conferences** | DEF CON, Black Hat, RSA, BSides (everywhere), NullCon, c0c0n, BSides Delhi/Bangalore, InfoSec Girls events |
| **Forums** | r/netsec, r/AskNetsec, HN, x/twitter infosec community |
| **Mentorship** | Cyber Mentor (Heath Adams), Mentor Cruise, ISC² mentorship, NICE Framework mentor links |

---

## ✅ Final Career Checklist

By the time you finish this curriculum:

- [ ] Sec+ certified (or skip if you have a stronger cert)
- [ ] eJPT or PNPT or CPTS achieved
- [ ] OSCP — in progress or scheduled
- [ ] GitHub portfolio with 10+ tools, 1k+ stars across (target)
- [ ] 3+ public CTF / HTB writeups
- [ ] LinkedIn polished, with 500+ connections in cyber
- [ ] Resume tailored for 3 different role types (offensive, defensive, AppSec)
- [ ] Bug bounty profile with at least 3 valid submissions
- [ ] Spoken at one local meetup or BSides
- [ ] Identified your target agencies (US or India) and tracked their job boards for 6 months
- [ ] Applied to 30+ roles
- [ ] Mock interview practice with at least 3 different formats

You will have the skills. The job is then a matter of **persistence**. Keep applying.

---

[Appendix →](../99-appendix/index.md)
