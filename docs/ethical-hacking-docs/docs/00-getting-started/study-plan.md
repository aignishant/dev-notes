# 📅 Study Plan

Pick the plan that matches your hours-per-week budget. Stick to a plan even imperfectly; the people who finish are not the geniuses, they're the ones who came back tomorrow.

## Plan A — Sprint (3 months, ~25 hr/week)

You have a runway and want to be hireable as a junior pentester or SOC analyst as quickly as possible.

| Week | Goal | Output |
|------|------|--------|
| 1 | Phase 1: Foundations — networking, Linux | Lab built, OSI fluency |
| 2 | Phase 1: Windows, crypto, Python recap | Subnet drills, hashing tools |
| 3 | Phase 2: Recon — OSINT, scanning | Recon report on a CTF box |
| 4 | Phase 2: Vuln assessment | Nessus + Nuclei walkthrough |
| 5 | Phase 3: Web — OWASP Top 10 | DVWA + Juice Shop fully owned |
| 6 | Phase 3: Web — advanced (XXE, SSRF, deser, IDOR) | PortSwigger Academy 70 % |
| 7 | Phase 3: System pentesting (Linux & Windows privesc) | 5 HTB easy boxes |
| 8 | Phase 3: Active Directory | Full GOAD walkthrough |
| 9 | Phase 4: Cloud — AWS basics | ScoutSuite + Pacu run |
| 10 | Phase 4: Malware analysis intro + RE basics | Static + dynamic analysis of a sample |
| 11 | Phase 5: Defense — DFIR + SIEM (Splunk/ELK) | Build detection lab |
| 12 | Phase 6: CTFs + reporting + interview prep | Full pentest report draft |

**Realistic expectation at end:** Sec+ ready, eJPT achievable, applying for Tier-1 SOC and junior pentest roles.

## Plan B — Steady (6 months, ~12 hr/week)

The most realistic plan if you have a job. Most readers should pick this.

| Month | Phase | Focus |
|-------|-------|-------|
| 1 | Phase 1 | Networking, Linux, Windows fluency |
| 2 | Phase 1 + 2 | Crypto, Python, recon basics |
| 3 | Phase 2 + 3 | Vuln assessment, web pentest core |
| 4 | Phase 3 | Web advanced + system privesc |
| 5 | Phase 3 | Active Directory deep dive |
| 6 | Phase 4 + 6 | Pick one specialization + start cert prep |

**Realistic at end:** Sec+ done, eJPT done, OSCP-ready by month 8 if you keep going.

## Plan C — Marathon (12 months, ~6 hr/week)

For students or full-time professionals who can't break daily routines.

| Quarter | Theme |
|---------|-------|
| Q1 | Foundations + cert (Network+ or Sec+) |
| Q2 | Recon, Vulnerability Assessment, intro web (eJPT) |
| Q3 | Offensive deep — Web + System + AD (CRTP / OSCP prep) |
| Q4 | Specialization of choice + DFIR / threat intel + portfolio |

**Realistic at end:** Sec+ done, CySA+ or eJPT done, OSCP attempt scheduled, GitHub portfolio of 5–10 well-documented projects, applying widely.

## Daily / Weekly Rhythm

A repeatable rhythm beats heroic weekends:

| Day | What |
|-----|------|
| Mon | 1 hr theory (chapter from this site) |
| Tue | 1 hr lab (run the chapter's commands) |
| Wed | 1 hr CTF (TryHackMe / HTB) |
| Thu | 1 hr writing (notes, blog post, report) |
| Fri | 1 hr reading (advisories, conference talks) |
| Sat | 3 hr deep work (a hard box, a long lab) |
| Sun | rest, review, plan |

Adjust to your life — but **block calendar time**, don't trust mood.

## Spaced Repetition (Anki)

Cards I recommend creating from day one:

- Top 50 ports → service
- Common nmap flags
- TCP flag combinations and what each scan looks like
- Top 25 OWASP attacks → root cause → mitigation
- MITRE ATT&CK tactics in order
- Common Linux privesc paths
- Common Windows privesc paths
- AD attack technique → preconditions → detection
- Common shellcode primitives
- Common Wireshark filters
- Top 30 PowerShell cmdlets

10 minutes/day, every day. After three months, recall is automatic.

## CTF Cadence

Goal: at least **one box / one room per week**.

| Source | Sweet spot for |
|--------|----------------|
| TryHackMe | Beginners, structured paths |
| HackTheBox | Intermediate, retired boxes have writeups |
| picoCTF | Foundations, fun |
| OverTheWire | Linux fluency |
| RootMe | Bite-size challenges |
| PortSwigger Web Academy | Web specifically |
| PentesterLab | Curated paid track |
| LetsDefend | Blue-team scenarios |
| Blue Team Labs Online | DFIR + SOC |

For **government careers**, prioritize:

- Hands-on tools (BloodHound, Splunk, Velociraptor, Volatility)
- Detection writing (Sigma, YARA, Snort)
- Incident-response simulations

## Portfolio While You Learn

By end of Phase 3, you should have:

1. A **GitHub** with the Python tools you wrote (cleaned up, README'd)
2. A **blog** with 6–10 posts: walkthroughs, deep dives on a CVE, an article on a tool you wrote
3. A **resume** that lists the labs you've completed (not just certs)
4. A **LinkedIn** with cybersecurity content reshared with your perspective
5. An **HTB / THM profile** with steady activity

Show your work. Hiring managers want evidence of self-direction.

## Red Flags to Avoid

- **Course collector** — you watch but never lab
- **Skill-list resume** — "I know nmap" is not a skill, completing 30 boxes is
- **Reckless practice** — testing on someone's website without permission
- **Tooling without theory** — running `sqlmap` without understanding SQLi
- **Theory without tooling** — reading 5 books, never building a lab
- **Specialization too early** — pick one at end of Phase 4, not before
- **Too many certs, too little practice** — certs without lab time fool no one in interviews

## Self-Test (before moving on)

- [ ] You've picked Plan A, B, or C and committed it to your calendar
- [ ] Your VM lab is built (per [Lab Setup](lab-setup.md))
- [ ] You've created a GitHub repo for your scripts
- [ ] You've created an Obsidian / Notion vault for notes
- [ ] You've signed up for one CTF platform
- [ ] You've started your first Anki deck

When all six are checked, → **[Phase 1 — Foundations](../01-foundations/index.md)**.
