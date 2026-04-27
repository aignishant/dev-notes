#!/usr/bin/env python3
"""
Linux Kernel Vulnerability Checker

Checks running kernel against database of known privilege escalation CVEs.
Includes embedded CVE database with version ranges and PoC information.

Usage:
    python3 -m redshift_toolkit.postex.linux_kernel_check
    python3 -m redshift_toolkit.postex.linux_kernel_check --format json

Author: Redshift Project — Module 20
License: MIT
"""

from __future__ import annotations

import re
import subprocess
import json
import argparse
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import platform


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
class CVEInfo:
    """CVE vulnerability information."""
    cve_id: str
    description: str
    severity: str
    affected_versions: List[str]
    poc_urls: List[str]
    references: List[str]
    exploitation_difficulty: str  # LOW, MEDIUM, HIGH


@dataclass
class KernelInfo:
    """Kernel information."""
    version: str
    release: str
    architecture: str
    distribution: str
    compiler_version: str


@dataclass
class VulnerabilityMatch:
    """Matched vulnerability."""
    cve: CVEInfo
    confidence: str  # HIGH, MEDIUM, LOW
    reason: str


@dataclass
class KernelAuditResult:
    """Complete kernel audit results."""
    kernel_info: KernelInfo
    vulnerable_cves: List[VulnerabilityMatch]
    recommendations: List[str]


# Embedded CVE database for Linux kernel privilege escalation vulnerabilities
KERNEL_CVES = {
    'CVE-2022-0847': CVEInfo(
        cve_id='CVE-2022-0847',
        description='Dirty Pipe - Overwriting data in arbitrary read-only files',
        severity='HIGH',
        affected_versions=['5.8.x', '5.9.x', '5.10.x', '5.11.x', '5.12.x', '5.13.x', '5.14.x', '5.15.x', '5.16.x'],
        poc_urls=[
            'https://github.com/AlexisAhmed/CVE-2022-0847-DirtyPipe-Exploits',
            'https://github.com/r1is/CVE-2022-0847',
            'https://github.com/Arinerron/CVE-2022-0847-DirtyPipe-Exploit'
        ],
        references=[
            'https://dirtypipe.cm4all.com/',
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2022-0847'
        ],
        exploitation_difficulty='MEDIUM'
    ),
    
    'CVE-2021-4034': CVEInfo(
        cve_id='CVE-2021-4034',
        description='PwnKit - Local privilege escalation in polkits pkexec',
        severity='HIGH',
        affected_versions=['All versions with polkit'],
        poc_urls=[
            'https://github.com/berdav/CVE-2021-4034',
            'https://github.com/arthepsy/CVE-2021-4034',
            'https://github.com/dzonerzy/CVE-2021-4034'
        ],
        references=[
            'https://blog.qualys.com/vulnerabilities-threat-research/2022/01/25/pwnkit-local-privilege-escalation-vulnerability-discovered-in-polkits-pkexec-cve-2021-4034'
        ],
        exploitation_difficulty='LOW'
    ),
    
    'CVE-2021-3156': CVEInfo(
        cve_id='CVE-2021-3156',
        description='Baron Samedit - Sudo heap-based buffer overflow',
        severity='HIGH',
        affected_versions=['Sudo 1.8.2 - 1.8.31p2', 'Sudo 1.9.0 - 1.9.5p1'],
        poc_urls=[
            'https://github.com/blasty/CVE-2021-3156',
            'https://github.com/worawit/CVE-2021-3156',
            'https://github.com/stong/CVE-2021-3156'
        ],
        references=[
            'https://blog.qualys.com/vulnerabilities-research/2021/01/26/cve-2021-3156-heap-based-buffer-overflow-in-sudo-baron-samedit'
        ],
        exploitation_difficulty='MEDIUM'
    ),
    
    'CVE-2017-16995': CVEInfo(
        cve_id='CVE-2017-16995',
        description='eBPF verifier - Race condition leads to privilege escalation',
        severity='HIGH',
        affected_versions=['4.4.x', '4.5.x', '4.6.x', '4.7.x', '4.8.x', '4.9.x', '4.10.x', '4.11.x', '4.12.x', '4.13.x', '4.14.x'],
        poc_urls=[
            'https://github.com/bcoles/kernel-exploits/tree/master/CVE-2017-16995',
            'https://www.exploit-db.com/exploits/45010'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2017-16995'
        ],
        exploitation_difficulty='HIGH'
    ),
    
    'CVE-2016-5195': CVEInfo(
        cve_id='CVE-2016-5195',
        description='Dirty COW - Race condition in get_user_pages()',
        severity='HIGH',
        affected_versions=['2.6.22', '3.x.x', '4.0.x', '4.1.x', '4.2.x', '4.3.x', '4.4.x', '4.5.x', '4.6.x', '4.7.x', '4.8.x'],
        poc_urls=[
            'https://github.com/dirtycow/dirtycow.github.io/wiki/PoCs',
            'https://github.com/gbonacini/CVE-2016-5195',
            'https://www.exploit-db.com/exploits/40839'
        ],
        references=[
            'https://dirtycow.ninja/',
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2016-5195'
        ],
        exploitation_difficulty='LOW'
    ),
    
    'CVE-2016-0728': CVEInfo(
        cve_id='CVE-2016-0728',
        description='Keyring - Use-after-free in keyring facility',
        severity='HIGH',
        affected_versions=['3.8.x', '3.9.x', '3.10.x', '3.11.x', '3.12.x', '3.13.x', '3.14.x', '3.15.x', '3.16.x', '3.17.x', '3.18.x', '3.19.x', '4.0.x', '4.1.x', '4.2.x', '4.3.x', '4.4.x'],
        poc_urls=[
            'https://github.com/jiayy/android_vuln_poc-exp/tree/master/EXP-CVE-2016-0728',
            'https://www.exploit-db.com/exploits/39277'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2016-0728'
        ],
        exploitation_difficulty='HIGH'
    ),
    
    'CVE-2015-1328': CVEInfo(
        cve_id='CVE-1328',
        description='overlayfs - Local privilege escalation',
        severity='HIGH',
        affected_versions=['3.13.x', '3.14.x', '3.15.x', '3.16.x', '3.17.x', '3.18.x', '3.19.x', '4.0.x', '4.1.x', '4.2.x'],
        poc_urls=[
            'https://www.exploit-db.com/exploits/37292',
            'https://github.com/offensive-security/exploitdb-bin-sploits/raw/master/bin-sploits/37292.c'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2015-1328'
        ],
        exploitation_difficulty='LOW'
    ),
    
    'CVE-2014-3153': CVEInfo(
        cve_id='CVE-2014-3153',
        description='Futex - Race condition in futex_requeue()',
        severity='HIGH',
        affected_versions=['3.3.x', '3.4.x', '3.5.x', '3.6.x', '3.7.x', '3.8.x', '3.9.x', '3.10.x', '3.11.x', '3.12.x', '3.13.x', '3.14.x'],
        poc_urls=[
            'https://www.exploit-db.com/exploits/35370',
            'https://github.com/geekben/towelroot'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-3153'
        ],
        exploitation_difficulty='MEDIUM'
    ),
    
    'CVE-2014-0196': CVEInfo(
        cve_id='CVE-2014-0196',
        description='rawmode PTY - Race condition in n_tty_write()',
        severity='HIGH',
        affected_versions=['2.6.31', '2.6.32', '2.6.33', '2.6.34', '2.6.35', '2.6.36', '2.6.37', '2.6.38', '2.6.39', '3.0.x', '3.1.x', '3.2.x', '3.3.x', '3.4.x', '3.5.x', '3.6.x', '3.7.x', '3.8.x', '3.9.x', '3.10.x', '3.11.x', '3.12.x', '3.13.x', '3.14.x'],
        poc_urls=[
            'https://www.exploit-db.com/exploits/33516',
            'https://github.com/offensive-security/exploitdb-bin-sploits/raw/master/bin-sploits/33516.c'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-0196'
        ],
        exploitation_difficulty='MEDIUM'
    ),
    
    'CVE-2024-1086': CVEInfo(
        cve_id='CVE-2024-1086',
        description='netfilter nf_tables - Use-after-free vulnerability',
        severity='HIGH',
        affected_versions=['5.15.x', '6.1.x', '6.2.x', '6.3.x', '6.4.x', '6.5.x', '6.6.x', '6.7.x'],
        poc_urls=[
            'https://github.com/Notselwyn/CVE-2024-1086',
            'https://github.com/kevcooper/CVE-2024-1086-checker'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1086',
            'https://nvd.nist.gov/vuln/detail/CVE-2024-1086'
        ],
        exploitation_difficulty='HIGH'
    ),
    
    'CVE-2023-32233': CVEInfo(
        cve_id='CVE-2023-32233',
        description='netfilter nf_tables - Use-after-free in nft_set_lookup_global',
        severity='HIGH',
        affected_versions=['6.0.x', '6.1.x', '6.2.x', '6.3.x'],
        poc_urls=[
            'https://github.com/Liuk3r/CVE-2023-32233',
            'https://github.com/g1vi/CVE-2023-32233'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-32233'
        ],
        exploitation_difficulty='HIGH'
    ),
    
    'CVE-2023-0386': CVEInfo(
        cve_id='CVE-2023-0386',
        description='OverlayFS - FUSE filesystem privilege escalation',
        severity='HIGH',
        affected_versions=['5.11.x', '5.12.x', '5.13.x', '5.14.x', '5.15.x', '5.16.x', '5.17.x', '5.18.x', '5.19.x', '6.0.x', '6.1.x', '6.2.x'],
        poc_urls=[
            'https://github.com/xkaneiki/CVE-2023-0386',
            'https://github.com/sxlmnwb/CVE-2023-0386'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-0386'
        ],
        exploitation_difficulty='MEDIUM'
    ),
    
    'CVE-2022-32250': CVEInfo(
        cve_id='CVE-2022-32250',
        description='netfilter - Use-after-free in nft_set_elem_init',
        severity='HIGH',
        affected_versions=['5.12.x', '5.13.x', '5.14.x', '5.15.x', '5.16.x', '5.17.x', '5.18.x'],
        poc_urls=[
            'https://github.com/theori-io/CVE-2022-32250-exploit'
        ],
        references=[
            'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2022-32250'
        ],
        exploitation_difficulty='HIGH'
    )
}


def run_command(cmd: List[str]) -> str:
    """Execute command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_kernel_info() -> KernelInfo:
    """Gather kernel and system information."""
    # Get kernel version
    uname_output = run_command(["uname", "-r"])
    kernel_version = uname_output if uname_output else "Unknown"
    
    # Get kernel release
    release_output = run_command(["uname", "-a"])
    
    # Get architecture
    arch = platform.machine()
    
    # Get distribution info
    distribution = "Unknown"
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    distribution = line.split("=", 1)[1].strip().strip('"')
                    break
    except FileNotFoundError:
        pass
    
    # Get compiler version (from /proc/version)
    compiler_version = "Unknown"
    try:
        with open("/proc/version", "r") as f:
            version_line = f.read()
            gcc_match = re.search(r'gcc version ([^\s]+)', version_line)
            if gcc_match:
                compiler_version = f"GCC {gcc_match.group(1)}"
    except FileNotFoundError:
        pass
    
    return KernelInfo(
        version=kernel_version,
        release=release_output,
        architecture=arch,
        distribution=distribution,
        compiler_version=compiler_version
    )


def parse_kernel_version(version_str: str) -> Tuple[int, int, int]:
    """Parse kernel version string into major, minor, patch."""
    # Extract version numbers from strings like "5.15.0-91-generic"
    version_match = re.match(r'(\d+)\.(\d+)\.?(\d+)?', version_str)
    if version_match:
        major = int(version_match.group(1))
        minor = int(version_match.group(2))
        patch = int(version_match.group(3)) if version_match.group(3) else 0
        return major, minor, patch
    return 0, 0, 0


def check_version_match(kernel_version: str, affected_versions: List[str]) -> Tuple[bool, str, str]:
    """Check if kernel version matches any affected versions."""
    kernel_major, kernel_minor, kernel_patch = parse_kernel_version(kernel_version)
    
    if kernel_major == 0:
        return False, "LOW", "Could not parse kernel version"
    
    for affected_version in affected_versions:
        # Handle special cases
        if "All versions" in affected_version:
            return True, "HIGH", f"All versions affected"
        
        if "Sudo" in affected_version:
            # This is a sudo vulnerability, check if sudo is installed
            sudo_check = run_command(["which", "sudo"])
            if sudo_check:
                return True, "HIGH", f"Sudo installed: {affected_version}"
            continue
        
        # Handle version ranges like "5.8.x"
        if "x" in affected_version:
            version_match = re.match(r'(\d+)\.(\d+)\.?x?', affected_version)
            if version_match:
                affected_major = int(version_match.group(1))
                affected_minor = int(version_match.group(2))
                
                if kernel_major == affected_major and kernel_minor == affected_minor:
                    return True, "HIGH", f"Exact version match: {affected_version}"
        
        # Handle specific version ranges like "5.8.0 - 5.15.74"
        if " - " in affected_version:
            parts = affected_version.split(" - ")
            if len(parts) == 2:
                start_version = parts[0].strip()
                end_version = parts[1].strip()
                
                start_major, start_minor, start_patch = parse_kernel_version(start_version)
                end_major, end_minor, end_patch = parse_kernel_version(end_version)
                
                # Simple range check
                kernel_tuple = (kernel_major, kernel_minor, kernel_patch)
                start_tuple = (start_major, start_minor, start_patch)
                end_tuple = (end_major, end_minor, end_patch)
                
                if start_tuple <= kernel_tuple <= end_tuple:
                    return True, "HIGH", f"Version in range: {affected_version}"
        
        # Handle single version matches
        else:
            affected_major, affected_minor, affected_patch = parse_kernel_version(affected_version)
            if (kernel_major == affected_major and 
                kernel_minor == affected_minor and 
                (affected_patch == 0 or kernel_patch == affected_patch)):
                return True, "HIGH", f"Exact version match: {affected_version}"
    
    # Check for close versions that might still be vulnerable
    for affected_version in affected_versions:
        if "x" in affected_version:
            version_match = re.match(r'(\d+)\.(\d+)', affected_version)
            if version_match:
                affected_major = int(version_match.group(1))
                affected_minor = int(version_match.group(2))
                
                # Check if we're close to an affected version
                if (kernel_major == affected_major and 
                    abs(kernel_minor - affected_minor) <= 2):
                    return True, "MEDIUM", f"Close to affected version: {affected_version}"
    
    return False, "LOW", "Version does not match known affected versions"


def check_vulnerabilities(kernel_info: KernelInfo) -> List[VulnerabilityMatch]:
    """Check kernel against CVE database."""
    matches = []
    
    print(paint(f"🔍 Checking {len(KERNEL_CVES)} CVEs against kernel {kernel_info.version}...", Colors.CYAN, True))
    
    for cve_id, cve_info in KERNEL_CVES.items():
        is_vulnerable, confidence, reason = check_version_match(
            kernel_info.version, 
            cve_info.affected_versions
        )
        
        if is_vulnerable:
            match = VulnerabilityMatch(
                cve=cve_info,
                confidence=confidence,
                reason=reason
            )
            matches.append(match)
    
    return matches


def generate_recommendations(matches: List[VulnerabilityMatch], kernel_info: KernelInfo) -> List[str]:
    """Generate recommendations based on findings."""
    recommendations = []
    
    if matches:
        high_conf_vulns = [m for m in matches if m.confidence == "HIGH"]
        
        if high_conf_vulns:
            recommendations.append("URGENT: Update kernel immediately - high confidence vulnerabilities found")
            recommendations.append(f"Current kernel: {kernel_info.version}")
            
            # Get latest stable kernel version (this would ideally be fetched from kernel.org)
            recommendations.append("Check https://kernel.org for latest stable release")
        
        # Specific recommendations based on CVEs found
        cve_ids = {m.cve.cve_id for m in matches}
        
        if any("CVE-2022-0847" in cve_id for cve_id in cve_ids):
            recommendations.append("Dirty Pipe vulnerability - upgrade to kernel 5.16.11+ or 5.15.25+")
        
        if any("CVE-2021-4034" in cve_id for cve_id in cve_ids):
            recommendations.append("PwnKit vulnerability - update polkit package")
        
        if any("CVE-2016-5195" in cve_id for cve_id in cve_ids):
            recommendations.append("Dirty COW vulnerability - critical, update immediately")
        
        recommendations.extend([
            "Apply all available security updates",
            "Consider upgrading to a Long Term Support (LTS) kernel version",
            "Monitor security advisories for your distribution",
            "Test kernel updates in development environment first"
        ])
    else:
        recommendations.extend([
            "No known high-risk vulnerabilities found for this kernel version",
            "Continue regular security update schedule",
            "Monitor security advisories for new vulnerabilities"
        ])
    
    return recommendations


def audit_kernel() -> KernelAuditResult:
    """Perform kernel vulnerability audit."""
    print(paint("🔍 Gathering kernel information...", Colors.CYAN, True))
    
    kernel_info = get_kernel_info()
    vulnerable_cves = check_vulnerabilities(kernel_info)
    recommendations = generate_recommendations(vulnerable_cves, kernel_info)
    
    return KernelAuditResult(
        kernel_info=kernel_info,
        vulnerable_cves=vulnerable_cves,
        recommendations=recommendations
    )


def print_results(result: KernelAuditResult, use_color: bool = True) -> None:
    """Print audit results."""
    print(paint(f"\n🎯 Linux Kernel Vulnerability Check Complete", Colors.GREEN, use_color))
    print(paint(f"🖥️  System: {result.kernel_info.distribution}", Colors.YELLOW, use_color))
    print(paint(f"🔧 Kernel: {result.kernel_info.version}", Colors.YELLOW, use_color))
    print(paint(f"🏗️  Architecture: {result.kernel_info.architecture}", Colors.YELLOW, use_color))
    print(paint(f"⚙️  Compiler: {result.kernel_info.compiler_version}", Colors.YELLOW, use_color))
    print(paint(f"🚨 Potential vulnerabilities: {len(result.vulnerable_cves)}", Colors.RED, use_color))
    
    if result.vulnerable_cves:
        # Group by confidence
        high_conf = [v for v in result.vulnerable_cves if v.confidence == "HIGH"]
        medium_conf = [v for v in result.vulnerable_cves if v.confidence == "MEDIUM"]
        
        if high_conf:
            print(paint(f"\n🔥 HIGH CONFIDENCE VULNERABILITIES ({len(high_conf)}):", Colors.RED, use_color))
            print(paint("="*70, Colors.RED, use_color))
            
            for vuln in high_conf:
                print(paint(f"\n📍 {vuln.cve.cve_id}: {vuln.cve.description}", Colors.BOLD, use_color))
                print(paint(f"   Severity: {vuln.cve.severity} | Difficulty: {vuln.cve.exploitation_difficulty}", Colors.CYAN, use_color))
                print(paint(f"   Reason: {vuln.reason}", Colors.GREY, use_color))
                
                if vuln.cve.poc_urls:
                    print(paint(f"   💥 PoC URLs:", Colors.YELLOW, use_color))
                    for poc_url in vuln.cve.poc_urls[:3]:  # Limit to first 3
                        print(paint(f"      • {poc_url}", Colors.WHITE, use_color))
        
        if medium_conf:
            print(paint(f"\n⚠️  MEDIUM CONFIDENCE VULNERABILITIES ({len(medium_conf)}):", Colors.YELLOW, use_color))
            for vuln in medium_conf:
                print(paint(f"   • {vuln.cve.cve_id}: {vuln.cve.description}", Colors.YELLOW, use_color))
                print(paint(f"     Reason: {vuln.reason}", Colors.GREY, use_color))
    
    else:
        print(paint(f"\n✅ No known vulnerabilities found for this kernel version", Colors.GREEN, use_color))
    
    if result.recommendations:
        print(paint(f"\n💡 RECOMMENDATIONS:", Colors.CYAN, use_color))
        for i, rec in enumerate(result.recommendations[:8], 1):  # Limit to top 8
            print(paint(f"   {i}. {rec}", Colors.CYAN, use_color))


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Linux Kernel Vulnerability Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check current kernel for vulnerabilities
    python3 -m redshift_toolkit.postex.linux_kernel_check
    
    # JSON output
    python3 -m redshift_toolkit.postex.linux_kernel_check --format json
    
    # No color output
    python3 -m redshift_toolkit.postex.linux_kernel_check --no-color

Note:
    - Checks against embedded CVE database
    - Version matching may have false positives/negatives
    - Always verify exploitability in target environment
    - Keep CVE database updated with latest vulnerabilities
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
        result = audit_kernel()
        
        if args.format == "json":
            print(json.dumps(asdict(result), indent=2, default=str))
        else:
            print_results(result, use_color)
        
        # Exit with appropriate code
        high_vulns = [v for v in result.vulnerable_cves if v.confidence == "HIGH"]
        if high_vulns:
            sys.exit(2)  # High confidence vulnerabilities found
        elif result.vulnerable_cves:
            sys.exit(1)  # Medium/low confidence vulnerabilities found
        else:
            sys.exit(0)  # No vulnerabilities found
        
    except KeyboardInterrupt:
        print(paint("\n❌ Check interrupted", Colors.RED, use_color))
        sys.exit(1)
    except Exception as e:
        print(paint(f"❌ Error during check: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
