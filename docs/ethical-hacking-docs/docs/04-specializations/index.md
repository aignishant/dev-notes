# ☁️ Phase 4 — Specializations

> The fork in the road. Senior security careers come from depth in one or two of these areas, on top of the foundations from Phases 1–3. Pick what you love.

Each specialization is its own deep, multi-chapter unit. Don't try to do all six at once. Pick **one primary** and **one secondary**.

## Tracks

### ☁️ Cloud Security (AWS, Azure, GCP, Kubernetes)
The hottest track. Every modern enterprise runs on cloud.

- AWS IAM, S3, EC2, IMDSv2 abuse, AssumeRole chains
- Azure AD / Entra ID, Conditional Access bypasses, Graph API attacks
- GCP IAM, service accounts, metadata server
- Kubernetes — RBAC, service accounts, pod security, sidecar injection
- CSPM tools — Prowler, ScoutSuite, CloudFox, Stratus Red Team
- Certs: AWS Security Specialty, AZ-500, GCP Pro Cloud Security, CCSP

### 🦠 Malware Analysis & Reverse Engineering
For roles in DFIR, CTI, and security research.

- Static analysis — strings, PE/ELF parsing, YARA, capa
- Dynamic analysis — sandboxes, debuggers, API monitors
- Unpacking, anti-debug evasion, anti-VM
- Ghidra and IDA workflows
- Real-world malware families: Emotet, Cobalt Strike, ICEDID, BumbleBee, ransomware
- Certs: GREM, Practical Malware Analysis & Triage (TCM)

### ⚙️ Exploit Development & Binary Exploitation
The most technical track. For research and red teams.

- x86/x64 assembly, calling conventions
- Stack-based BOFs, ROP, ret2libc
- Format strings, heap exploitation
- ASLR, DEP/NX, SafeSEH, CFG, CET shadow stack bypasses
- Windows kernel exploitation primer
- Browser exploitation primer (V8/JIT)
- Certs: OSED, OSEE

### 🌐 IoT / ICS / OT Security
For critical infrastructure roles (NCIIPC, CISA, DOE, utilities).

- Embedded firmware analysis (binwalk, firmwalker, firmadyne)
- UART/JTAG hardware reverse engineering
- BLE, Zigbee, Z-Wave, LoRa, RF basics with HackRF/RTL-SDR
- ICS protocols — Modbus, DNP3, IEC-104, Profinet, OPC-UA
- Purdue model, ISA/IEC 62443
- Certs: GICSP, GRID

### 🤖 AI/ML Security
The newest track. Massive demand.

- Adversarial ML — evasion, poisoning, model extraction
- Prompt injection, jailbreaks, indirect prompt injection
- RAG security, agent abuse, tool-use attacks
- Model supply-chain (HuggingFace, pickle deserialization)
- OWASP LLM Top 10, MITRE ATLAS framework
- Defensive: NeMo Guardrails, Microsoft PyRIT, Garak red-teaming

### 🛡️ Application Security & Secure SDLC
For AppSec engineer roles, often the highest-paid track at tech companies.

- Threat modeling (STRIDE, LINDDUN, PASTA)
- Secure code review (SAST, DAST, SCA, IAST)
- Supply chain security (SLSA, Sigstore, SBOM, dependency hijacking)
- Cryptography review
- Containers, IaC (Terraform/Helm) security
- Bug bounty program management
- Certs: CSSLP, OSWE

## What you'll be able to do at the end

- Hold senior-level technical interviews in your chosen specialization
- Identify a 2-year specialization roadmap with concrete milestones
- Know which industry contacts, conferences, and reading lists matter

---

!!! tip "Stage 3/4 of this curriculum"
    Cloud + Malware ship in Stage 3. RE/Exploit Dev + IoT + AI in Stage 4.

[← Phase 3](../03-offensive/index.md)  ·  [Phase 5 →](../05-defense/index.md)
