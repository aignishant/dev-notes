# 08 · Protocols You Will Attack

> *Tools come and go. The protocols last 30 years. Learn the wire format once and you'll understand every CVE for the next decade.*

This module is a tour of the application-layer protocols that comprise 90% of real-world engagement traffic. We focus on **wire format**, **authentication mechanisms**, and **abuse surface** — not exhaustive RFC reading.

For each protocol we answer four questions:

1. **What does the wire actually look like?**
2. **How does authentication work, and what are its weak points?**
3. **What does enumeration look like (banner / version / share / user discovery)?**
4. **What are the canonical attacks?**

---

## 8.1 HTTP and HTTPS

You'll spend more time here than anywhere else. Web hacking gets its own multi-module Part 4; this section establishes the protocol foundation.

### Wire format

```
GET /admin/users?id=42 HTTP/1.1
Host: app.example.com
User-Agent: curl/8.4.0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Cookie: session=abc123; tracking=xyz
Accept: application/json
\r\n
```

Status line, headers (case-insensitive name : value), blank line, optional body. Every byte is text in HTTP/1.1. **HTTP/2 is binary** with the same semantic structure plus multiplexing. **HTTP/3** runs over QUIC over UDP.

### Methods worth knowing

| Method | Idempotent | Has body | Notes |
|--------|------------|----------|-------|
| GET | yes | no | Cacheable. Don't put state-change actions here. |
| POST | no | yes | State change, form submission, RPC |
| PUT | yes | yes | Replace resource |
| PATCH | no | yes | Partial update |
| DELETE | yes | no/yes | Remove resource |
| HEAD | yes | no | Like GET, response has no body |
| OPTIONS | yes | no | CORS preflight, also allowed-methods discovery |
| TRACE / TRACK | yes | no | **Should be disabled** — XST attack |
| CONNECT | no | no | Used by proxies and `HTTP/2` upgrade |

### Authentication mechanisms

| Mechanism | How it works | Common weakness |
|-----------|--------------|-----------------|
| **Basic** | `Authorization: Basic base64(user:pass)` | Trivially decoded, must be over TLS |
| **Bearer / JWT** | `Authorization: Bearer <token>` | Module 07 attacks |
| **Cookie session** | Server-side state, `Cookie: session=...` | Session fixation, IDOR on session ID |
| **NTLM / Negotiate** | Windows challenge-response | Relay attacks (Module 21) |
| **Mutual TLS** | Client cert | Cert provisioning failures, weak enforcement |
| **OAuth 2.0 / OIDC** | Token issuance + validation | Redirect URI confusion, scope abuse |

### Common attacks (Part 4 will go deep)

- **SSRF** via fetch endpoints, image proxies, webhooks.
- **Open redirect** chained with phishing or OAuth.
- **Header injection** (CR/LF in user-controlled headers).
- **HTTP request smuggling** — desync between front-end and back-end Content-Length / Transfer-Encoding parsing.
- **HTTP/2 specific** — pseudo-header injection, RST flood (CVE-2023-44487).

### Useful tooling

- **`curl`** — every flag you'll ever need; learn `-v`, `-d`, `-H`, `-b/-c` cookies, `--resolve` for vhosts.
- **`httpie`** — friendlier CLI.
- **Burp Suite / Caido** — intercept proxy, the workbench for HTTP work.
- **`ffuf`** / **`feroxbuster`** — directory and parameter fuzzing.

---

## 8.2 DNS

DNS underlies everything. A DNS-aware attacker has reconnaissance, exfiltration, and C2 channels in one protocol.

### Wire format

DNS runs over UDP/53 (typical) or TCP/53 (large responses, AXFR). All-binary header followed by length-prefixed labels:

```
Header (12 bytes)
  ID (2)         — transaction ID
  Flags (2)      — QR, OPCODE, AA, TC, RD, RA, Z, RCODE
  QDCOUNT (2)    — questions
  ANCOUNT (2)    — answer records
  NSCOUNT (2)    — authority records
  ARCOUNT (2)    — additional records

Question section (each question)
  QNAME    — sequence of length-prefixed labels, ending in 0x00
             "example.com" → "\x07example\x03com\x00"
  QTYPE  (2) — 1=A, 2=NS, 5=CNAME, 6=SOA, 12=PTR, 15=MX, 16=TXT, 28=AAAA, 33=SRV, 257=CAA
  QCLASS (2) — almost always 1 (IN)

Answer / Authority / Additional sections
  Same name format + TTL + RDLENGTH + RDATA
```

You can read a DNS packet in a hex dump if you know this. We do exactly this in `dns_client.py`.

### Record types worth recognizing

| Type | Purpose | Recon value |
|------|---------|-------------|
| **A / AAAA** | Hostname → IPv4 / IPv6 | Asset enum |
| **NS** | Authoritative nameservers | Find the org's DNS provider |
| **MX** | Mail exchanger | Often reveals mail provider (O365, Google) |
| **TXT** | Free-form text | SPF, DKIM, domain ownership proofs, **leaked IPs and tooling info** |
| **CNAME** | Alias | Trace cloud services, find takeover candidates |
| **SOA** | Zone metadata | Get the email of the DNS admin, refresh intervals |
| **SRV** | Service discovery | `_kerberos._tcp`, `_ldap._tcp`, `_sip._tcp` reveal AD and VoIP infrastructure |
| **PTR** | Reverse: IP → hostname | Ranges of corporate IPs |
| **CAA** | Cert issuance authorization | What CAs are allowed to sign for this domain |

### Reconnaissance techniques

- **Zone transfer (AXFR)** — ask the authoritative server for the entire zone. Almost always disabled now, but try every NS. *Still works in 2026 against neglected internal domains.*
- **NSEC / NSEC3 walking** — DNSSEC reveals the next domain name in the zone. With NSEC, you can walk the entire zone. NSEC3 is hashed but still vulnerable to offline cracking.
- **Subdomain brute-force** — top-N wordlists against `_target.tld`.
- **Certificate transparency** — `crt.sh`, search every cert ever issued for `*.target.tld`.
- **Passive DNS** — `SecurityTrails`, `RiskIQ`, `VirusTotal` databases of historical DNS observations.
- **Reverse DNS sweep** — `nmap -sL <CIDR>` or just iterating PTR queries.

### DNS as exfil/C2

Encode data into subdomain labels: `<base32-encoded-secret>.exfil.attacker.tld`. Attacker's authoritative server logs the queries. Detection-evasive because most networks let DNS leave unrestricted.

Tools: `iodine`, `dnscat2`, custom Python (`dns_c2.py` in Part 11).

### Detection

- Look for **abnormal DNS volume** per host.
- **Rare TLDs** in queries.
- **Long subdomain labels** — entropy and length both useful.
- **Unique queries per minute** above a baseline.
- **Non-resolving queries** for nonexistent names spiking.

---

## 8.3 SMB / CIFS

The Windows file-sharing protocol. Three dialect generations matter:

| Version | Year | Notes |
|---------|------|-------|
| **SMB1** | 1990s | **Disable everywhere.** EternalBlue, WannaCry, NotPetya all rode SMB1. |
| **SMB2** | 2006 | Vista+, modernized |
| **SMB3** | 2012 | Encryption, signing improvements |

### Authentication

SMB authenticates via NTLM, Kerberos (in domains), or anonymously (rare today, but `IPC$` historically).

NTLM auth flow:

```
Client                                                 Server
  | --- Negotiate (capabilities)                  ---> |
  | <-- Challenge (8-byte server challenge)            |
  | --- Authenticate (NTLM response, username, host) -> |
  | <-- Success or failure                              |
```

The NTLM response is `HMAC-MD5(NTLM-hash, server_challenge || client_challenge || timestamp || domain)`. Capturing this on the wire gives you a hash you can crack offline (`hashcat -m 5600`) or **relay** to another service (Module 21).

### Enumeration

```bash
# Version + dialects
nmap --script smb-protocols -p 445 10.0.0.10

# Anonymous share listing (rarely allowed today)
smbclient -L //10.0.0.10 -N
enum4linux -a 10.0.0.10
crackmapexec smb 10.0.0.0/24

# With creds
crackmapexec smb 10.0.0.0/24 -u alice -p Password1
crackmapexec smb 10.0.0.0/24 -u alice -H <ntlm_hash>   # pass-the-hash
```

### Signing — the relay enabler

If a server **doesn't require SMB signing**, you can capture an NTLM auth attempt (e.g. via Responder poisoning LLMNR/NBT-NS) and replay it to that server. Coverage:

```bash
nmap --script smb2-security-mode -p 445 10.0.0.0/24
# Look for "message_signing: disabled (dangerous, but default)"
```

Domain controllers require signing by default. Member servers and workstations frequently don't.

### Canonical attacks

- **EternalBlue** (CVE-2017-0144, MS17-010) — SMB1 buffer overflow → kernel RCE. Still finds unpatched targets in 2026.
- **PrintNightmare**-related and **PetitPotam** — coercing a target to authenticate to an attacker.
- **NTLM relay** to LDAP, SMB, AD CS, MSSQL.
- **Forced authentication via UNC paths** — `\\attacker\share\foo` in office docs, browsers, MS apps triggers NTLM.

---

## 8.4 LDAP and Active Directory

LDAP is *the* directory protocol for enterprises. In a domain environment it's how you query everything: users, groups, computers, GPOs, sites, services.

### Wire basics

- TCP/389 plaintext, TCP/636 LDAPS (TLS), TCP/3268 Global Catalog.
- ASN.1 / BER encoded.
- Bind operation = authentication. Anonymous, simple (DN + password), or SASL (Kerberos/GSSAPI).

### What's queryable

Every domain user can read **most of AD by default**:

- All user accounts (`(objectClass=user)`)
- All groups
- All computers
- All GPOs
- Most attributes including `description` (notorious for storing passwords)
- `servicePrincipalName` attributes (Kerberoastable accounts!)
- `userAccountControl` flags (account disabled, no preauth required, etc.)

```bash
# Quick anonymous probe
ldapsearch -x -H ldap://10.0.0.10 -s base -b "" "(objectClass=*)"

# Authenticated dump (every user, password info, last logon)
ldapsearch -x -H ldap://10.0.0.10 -D "alice@corp.local" -W \
    -b "DC=corp,DC=local" "(objectClass=user)" \
    samaccountname userprincipalname pwdlastset lastlogon useraccountcontrol description
```

### Useful filters

```
(&(objectCategory=person)(objectClass=user))                        all users
(&(objectClass=user)(servicePrincipalName=*))                       Kerberoastable
(userAccountControl:1.2.840.113556.1.4.803:=4194304)                no preauth → AS-REP roastable
(&(objectClass=user)(adminCount=1))                                 protected (was admin)
(memberOf=CN=Domain Admins,CN=Users,DC=corp,DC=local)               DA members
(&(objectClass=group)(member=CN=alice,...))                         what groups is alice in?
```

### LDAP injection

`username = (& (uid=alice) (password=*))` — if user input lands unescaped in an LDAP filter, attacker can bypass auth or enumerate. Same instinct as SQL injection. **OWASP top-10 weakness in LDAP-heavy apps.**

### BloodHound + SharpHound

The standard AD attack-graph tool. SharpHound collects (user, group, computer, session, ACL, GPO) data via LDAP and SMB. BloodHound visualizes attack paths to Domain Admin. We use BloodHound heavily in Part 7.

---

## 8.5 Kerberos

The MIT-designed, ticket-based authentication protocol that AD uses. Hard at first, mechanical once you draw it three times.

### The 3-leg dance

```
                       AS-REQ (1)
            ────────────────────────────────►
Client                                          KDC (DC)
            ◄────────────────────────────────
                       AS-REP (2)
        Contains: TGT (encrypted with KRBTGT)
                  + session key (encrypted with user's hash)

                       TGS-REQ (3) (presents TGT, asks for ticket to service X)
            ────────────────────────────────►
Client                                          KDC (DC)
            ◄────────────────────────────────
                       TGS-REP (4)
        Contains: Service ticket (encrypted with service's hash)

                       AP-REQ (5) (presents service ticket)
            ────────────────────────────────►
Client                                          Service
            ◄────────────────────────────────
                       AP-REP (6)
```

### Attacks (we'll execute these in Part 7)

| Attack | Targets | What you need | What you get |
|--------|---------|---------------|---------------|
| **AS-REP roasting** | User accounts with `DONT_REQ_PREAUTH` | Username, network access | Crackable hash |
| **Kerberoasting** | Any account with an SPN | Domain user creds | Crackable service ticket |
| **Pass-the-Ticket** | An exported TGT or service ticket | The `.kirbi`/`.ccache` file | Authenticated as the user |
| **Golden Ticket** | KRBTGT hash | DC compromise (one-time) | TGT for any user, valid until KRBTGT rotation |
| **Silver Ticket** | Service account hash | Service hash | Service-ticket for that service |
| **Diamond / Sapphire Ticket** | Newer variants | Various | Bypass detection of golden-ticket abuse |

### Common parser confusion

You'll see hash format strings like:

```
$krb5asrep$23$alice@CORP.LOCAL:....
$krb5tgs$23$*svc_sql$CORP.LOCAL$MSSQLSvc/sql.corp.local~1433*$....
```

Hashcat modes: `18200` (AS-REP RC4), `13100` (Kerberoast RC4), `19600` (AS-REP AES), `19700` (Kerberoast AES). **AES-encrypted tickets are slower to crack but still crackable** — the password's entropy is the real bottleneck.

---

## 8.6 SSH

OpenSSH is the most-deployed remote-administration protocol. Modern OpenSSH is hard to attack directly; the wins come from key management, configuration, and abuse of features.

### Wire / version banner

```
$ nc -nv 10.0.0.10 22
SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.5
```

The banner reveals version. Match against vulnerability databases. **OpenSSH 9.0 - 9.7 → CVE-2024-6387 ("regreSSHion")** is a recent example.

### Key types

| Type | Notes |
|------|-------|
| **RSA** | Still common, generate at 4096+ |
| **DSA** | **Deprecated.** Don't use, don't accept. |
| **ECDSA** | OK but Curve25519 preferred |
| **Ed25519** | Modern default. Short, fast, secure. |

### Configuration findings worth flagging

- `PermitRootLogin yes`
- `PasswordAuthentication yes` on internet-facing host without rate limiting
- `PermitEmptyPasswords yes`
- Old algorithms enabled (`ssh-rsa` host keys, `diffie-hellman-group1-sha1`)
- `AuthorizedKeysCommand` running as root with insufficient validation

### Abuse vectors

- **Authorized_keys backdoors** — adding your key to a compromised user's `~/.ssh/authorized_keys`. Persistence pattern.
- **SSH agent hijacking** — if `SSH_AUTH_SOCK` is exposed (especially via socket forwarding from a jump host), you can use the user's keys without ever having them.
- **`ProxyCommand` and `ProxyJump`** — tunnel through bastion hosts. Equally useful offensively (pivoting via SOCKS).
- **Port forwarding (`-L`, `-R`, `-D`)** — local, remote, dynamic SOCKS. Master these.

```bash
# Local forward — make remote server's MySQL look local
ssh -L 3306:localhost:3306 user@bastion

# Remote forward — make your laptop's listener available on the remote box
ssh -R 4444:localhost:4444 user@target

# Dynamic SOCKS proxy — pivot all traffic through SSH
ssh -D 9050 user@target
# Then proxychains nmap -sT -Pn target_internal
```

### Auditing

```bash
ssh-audit target.tld                   # comprehensive config audit (open source tool)
nmap --script ssh2-enum-algos -p 22 target.tld
```

---

## 8.7 SMTP

Plain-text protocol with verbs. Easy to talk by hand, useful for user enumeration and (legacy) open relay testing.

```
$ nc mail.example.com 25
220 mail.example.com ESMTP Postfix
HELO test
250 mail.example.com
VRFY alice
252 2.0.0 alice
VRFY nobody
550 5.1.1 <nobody>: Recipient address rejected: User unknown
EXPN sales
550 5.0.0 EXPN command is disabled
MAIL FROM: <attacker@attacker.tld>
250 2.1.0 Ok
RCPT TO: <alice@example.com>
250 2.1.5 Ok
RCPT TO: <nobody@example.com>
550 5.1.1 <nobody@example.com>: Recipient address rejected: User unknown
```

### Enumeration techniques

| Verb | What it does | Default state today |
|------|--------------|---------------------|
| **VRFY** | Verify a user exists | Usually disabled |
| **EXPN** | Expand a mailing list | Usually disabled |
| **RCPT TO** | Recipient — succeeds vs fails reveals existence | Often still leaks |

### Open relay testing

Try to send `MAIL FROM: external@external.tld` to `RCPT TO: another@external.tld`. If accepted, the server is an open relay — instantly used by spammers, instant finding.

### Modern attacks

- **SMTP smuggling** (CVE-2023-51764 et al.) — exploiting end-of-data sequence parsing differences between sending and receiving MTAs to inject additional emails.
- **SPF/DKIM/DMARC bypass** — find subdomains without DMARC, send spoofed emails for phishing pretexts.
- **Header injection** in apps that use SMTP backends.

---

## 8.8 SNMP

The "Simple Network Management Protocol" is the most misunderstood enumeration goldmine in enterprise networks.

### Versions

| Version | Auth | Encryption |
|---------|------|------------|
| **v1** | Community string in plaintext | None |
| **v2c** | Same | None |
| **v3** | User+password (HMAC) | Optional (DES/AES) |

Most network gear and printers ship with v1/v2c and a default community string of `public`.

### Goldmine MIBs to walk

| OID prefix | What it gives you |
|------------|---------------------|
| `1.3.6.1.2.1.1` | sysDescr, sysName, sysContact, sysLocation |
| `1.3.6.1.2.1.25.1.6` | Process count |
| `1.3.6.1.2.1.25.4.2.1.2` | **Running process names** |
| `1.3.6.1.2.1.25.6.3.1.2` | **Installed software list** |
| `1.3.6.1.4.1.77.1.2.25` | **Windows users** (legacy) |
| `1.3.6.1.4.1.77.1.4` | Windows shares |
| `1.3.6.1.2.1.4.20` | IP addresses on interfaces |

```bash
# Walk everything (v2c)
snmpwalk -v 2c -c public 10.0.0.10

# Specific tree
snmpwalk -v 2c -c public 10.0.0.10 1.3.6.1.2.1.25.4.2.1.2

# Brute force community strings
onesixtyone -c communities.txt -i targets.txt
```

Common findings: **routers and switches with SNMP RW community `private`** — set rwcommunity allows you to alter their config remotely, exfiltrate the config, change routing.

---

## 8.9 RDP, VNC, Telnet, FTP — quick hits

| Protocol | Port | Notes |
|----------|------|-------|
| **RDP** | 3389 | NLA enabled = challenge-response auth pre-session. Disabled = capture creds via MITM. CredSSP downgrades historically possible. **BlueKeep** (CVE-2019-0708) and `RDPDoor` for old versions. Hashcat mode 26200 for newer NLA captures. |
| **VNC** | 5900-590x | Often passwordless or weak DES-based auth. Many CCTV / IoT devices ship with VNC + default password. |
| **Telnet** | 23 | Cleartext. Banner-grab and credential capture. Common on old network gear and IoT. |
| **FTP** | 21 (control) + dynamic data port | Often allows anonymous reads. Cleartext credentials. FTPS=22? No, FTPS uses 21 with TLS, **SFTP is SSH on 22**. |

```bash
# Telnet/FTP banner
nc -nv 10.0.0.10 23

# RDP enumeration
nmap --script rdp-enum-encryption,rdp-ntlm-info -p 3389 10.0.0.10

# VNC unauth check
nmap --script vnc-info,vnc-brute -p 5900 10.0.0.10
```

---

## 8.10 Industry Scenarios

### Healthcare — DICOM and HL7 unauthenticated on internal networks

DICOM (port 104) and HL7 (port 2575) often run inside hospitals without auth, encryption, or network segmentation. Sniffing yields PHI; injection yields false records or commands. Both protocols still have active CVEs.

### Financial — FIX protocol enumeration

FIX (Financial Information eXchange) is the trading protocol. Engagements at brokerages and exchanges include FIX testing — version, auth, message tampering. Very protocol-specific and lucrative niche.

### Government — Kerberos misconfigurations on .gov tenants

Federal AD environments still routinely have AS-REP roastable accounts (legacy service users), Kerberoastable SPNs on neglected service accounts, and unconstrained delegation on file servers. **All routinely chained to Domain Admin.**

### Cloud — IMDS abuse via SSRF

The classic cloud protocol attack: SSRF in a web app reaches the cloud metadata service. AWS `169.254.169.254/latest/meta-data/iam/security-credentials/<role>` returns IAM credentials. Azure and GCP have analogous endpoints. **Capital One 2019 was this.**

### ICS — Modbus/TCP queries against PLCs

Modbus has no authentication. `read_coils`, `read_holding_registers`, `write_single_coil` all work over TCP/502 to anyone on the network. We attack this in Part 10.

---

## 8.11 Detection / Blue-Team Angle

Protocols are noisy when abused if you log the right thing:

- **DNS** — Sysmon Event ID 22, Zeek `dns.log`. Look for high-entropy subdomains, TXT lookups from servers, NXDOMAIN spikes.
- **SMB** — Windows Event 5145 (detailed file share), 4624 with logon type 3 (network), 4625 (failures). Sigma rules for null sessions, anonymous IPC.
- **LDAP** — Event 1644 logs LDAP queries; massive query volume from a workstation = SharpHound/BloodHound.
- **Kerberos** — Event 4769 (service ticket) with RC4 = candidate for Kerberoasting; 4768 with `Account: ANONYMOUS LOGON` = AS-REP probe.
- **SNMP** — UDP/161 traffic from non-management hosts.
- **SSH** — `/var/log/auth.log` failed/successful, audit `~/.ssh/authorized_keys` writes via auditd.

---

## 8.12 Toolbelt

| Tool | Protocol | Use |
|------|----------|-----|
| `dnsrecon`, `dnsenum`, `dnsx` | DNS | Recon, brute, AXFR |
| `enum4linux-ng` | SMB/RPC | Comprehensive Windows enum |
| `crackmapexec` / `nxc` | SMB/WMI/WinRM/SSH/MSSQL | Multi-protocol auth + enum |
| `impacket` (full suite) | SMB/Kerberos/MSRPC | scripts: `secretsdump`, `GetUserSPNs`, `GetNPUsers`, `psexec`, `wmiexec`, `smbexec` |
| `ldapsearch` / `ldapdomaindump` | LDAP | AD enum |
| `BloodHound` + `SharpHound`/`bloodhound.py` | LDAP/SMB | Attack path analysis |
| `Rubeus` (Windows-side) | Kerberos | Ticket manipulation |
| `kerbrute` | Kerberos | User enum, password spray pre-auth |
| `responder` | LLMNR/NBT-NS/mDNS | Hash capture |
| `ntlmrelayx` | NTLM | Relay to SMB/LDAP/HTTP/MSSQL |
| `ssh-audit` | SSH | Config audit |
| `swaks` | SMTP | Test/abuse SMTP servers |
| `snmpwalk` / `onesixtyone` | SNMP | Walking + brute |
| `tshark` | Any | Read pcap programmatically |

---

## 8.13 Scripts for This Module

Six scripts in `scripts/part-02/08-protocols/` and toolkit:

### 1. `dns_client.py` — DNS query builder from scratch

Builds and parses DNS packets byte-by-byte. No `dnspython`. Sends over UDP, parses response, prints decoded structure. **Read this script and you understand DNS.**

### 2. `smb_recon.py` *(toolkit)* — SMB enumeration

Lands in `redshift_toolkit/protocols/smb_recon.py`. Identifies SMB version, signing requirements, dialects, public shares, share-level access (anonymous and authenticated). Wraps `impacket`'s `SMBConnection`.

### 3. `ldap_recon.py` *(toolkit)* — LDAP enumeration

Lands in `redshift_toolkit/protocols/ldap_recon.py`. Anonymous probe → identify naming context → authenticated dump of users/groups/SPNs/preauth-disabled accounts.

### 4. `smtp_recon.py` *(toolkit)* — SMTP user enum

Tries VRFY, EXPN, RCPT TO. Detects open relay. Honors rate limiting. Lands in `redshift_toolkit/protocols/smtp_recon.py`.

### 5. `snmp_walker.py` *(toolkit)* — SNMP walk + community brute

Brute-forces community strings, walks high-value MIBs. Lands in `redshift_toolkit/protocols/snmp_walker.py`.

### 6. `protocol_fingerprinter.py` — multi-protocol banner grabber

Concurrent banner grabbing across HTTP/SSH/FTP/SMTP/SMB/Telnet/VNC/RDP/SNMP. Identifies versions and flags known-vulnerable banners. Useful for the first 10 minutes of an internal pentest.

---

## 8.14 Lab Exercises

1. Run `dns_client.py` against `8.8.8.8` for `example.com A`, then for the same name on `MX`, `TXT`, `NS`. Read the responses byte by byte — verify your understanding of the wire format.
2. From Kali, run `smb_recon.py 10.0.0.10` against your DC01. Compare output against `enum4linux-ng -A 10.0.0.10`.
3. Set `responder -I eth0` running on Kali. From your WS01, browse to `\\nonexistent.corp.local\share` (Windows file explorer). Watch Responder capture an NTLMv2 hash. Crack it with `hashcat -m 5600` and a small wordlist.
4. Run `protocol_fingerprinter.py` against your entire lab subnet. You should get banners from every running service. Save the output as a JSON asset list.

---

## 8.15 Further Reading

- **Beale et al., *Network Security Assessment* (3rd ed.)** — protocol-by-protocol, very practical.
- **Microsoft *MS-* protocol specs** — `MS-SMB2`, `MS-NLMP`, `MS-KILE` (Kerberos), `MS-ADTS` (LDAP/AD). Free, definitive, surprisingly readable.
- **HackTricks** — `book.hacktricks.xyz` — community wiki, every port has an entry.
- **PayloadsAllTheThings** — payload patterns for each protocol.
- **Specter Ops blog** — AD, ADCS, Kerberos depth.
- **DEF CON 27: *AD attacks: from zero to hero*** by Sean Metcalf.
- **MITRE ATT&CK Initial Access TA0001** — every protocol abuse pattern catalogued.

---

> The protocols in this chapter run trillions of times a day across every network on Earth. Learn them once. The CVEs are just commentary — the wire format is forever.

→ Next: **Part 3 · Reconnaissance** *(coming in the next ship — Modules 09-12: passive recon, active recon, OSINT, DNS/subdomain enumeration)*.
