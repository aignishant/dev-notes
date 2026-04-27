#!/usr/bin/env python3
"""
Windows Post-Exploitation Enumeration Script

Comprehensive Windows system enumeration for privilege escalation research.
Uses subprocess calls to PowerShell and Windows commands for data gathering.
Outputs structured JSON with Windows-specific security configurations.

Usage:
    python3 -m redshift_toolkit.postex.windows_enum
    python3 -m redshift_toolkit.postex.windows_enum --format json

Author: Redshift Project — Module 21
License: MIT

Note: Designed to run on Windows systems or in Windows-compatible environments.
"""

from __future__ import annotations

import json
import subprocess
import re
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import argparse
import sys


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
class WindowsSystemInfo:
    """Complete Windows system enumeration results."""
    
    # Basic System Information
    hostname: str = ""
    os_version: str = ""
    os_build: str = ""
    architecture: str = ""
    domain: str = ""
    workgroup: str = ""
    install_date: str = ""
    boot_time: str = ""
    timezone: str = ""
    
    # Current User Context
    current_user: str = ""
    user_sid: str = ""
    user_groups: List[str] = None
    user_privileges: List[str] = None
    is_admin: bool = False
    uac_level: str = ""
    
    # Users and Groups
    local_users: List[Dict[str, str]] = None
    local_groups: List[Dict[str, str]] = None
    domain_users: List[str] = None
    recent_logons: List[str] = None
    
    # Services
    running_services: List[Dict[str, str]] = None
    stopped_services: List[Dict[str, str]] = None
    unquoted_service_paths: List[Dict[str, str]] = None
    weak_service_permissions: List[Dict[str, str]] = None
    modifiable_services: List[str] = None
    
    # File System and Permissions
    weak_file_permissions: List[Dict[str, str]] = None
    unattended_files: List[str] = None
    gpp_passwords: List[Dict[str, str]] = None
    credential_files: List[str] = None
    
    # Registry and Autostart
    autostart_programs: List[Dict[str, str]] = None
    registry_autologon: Dict[str, str] = None
    always_install_elevated: bool = False
    
    # Network Configuration
    network_interfaces: List[Dict[str, str]] = None
    listening_ports: List[Dict[str, str]] = None
    active_connections: List[Dict[str, str]] = None
    firewall_status: str = ""
    firewall_rules: List[str] = None
    
    # Installed Software
    installed_programs: List[Dict[str, str]] = None
    running_processes: List[Dict[str, str]] = None
    scheduled_tasks: List[Dict[str, str]] = None
    
    # Security Features
    av_products: List[str] = None
    applocker_policy: str = ""
    wsl_distributions: List[str] = None
    
    # Credentials and Secrets
    wifi_profiles: List[Dict[str, str]] = None
    saved_rdp_connections: List[str] = None
    credential_manager_entries: List[str] = None
    dpapi_masterkeys: List[str] = None
    
    # Drivers and Hardware
    installed_drivers: List[Dict[str, str]] = None
    pnp_devices: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists and dicts."""
        if self.user_groups is None:
            self.user_groups = []
        if self.user_privileges is None:
            self.user_privileges = []
        if self.local_users is None:
            self.local_users = []
        if self.local_groups is None:
            self.local_groups = []
        if self.domain_users is None:
            self.domain_users = []
        if self.recent_logons is None:
            self.recent_logons = []
        if self.running_services is None:
            self.running_services = []
        if self.stopped_services is None:
            self.stopped_services = []
        if self.unquoted_service_paths is None:
            self.unquoted_service_paths = []
        if self.weak_service_permissions is None:
            self.weak_service_permissions = []
        if self.modifiable_services is None:
            self.modifiable_services = []
        if self.weak_file_permissions is None:
            self.weak_file_permissions = []
        if self.unattended_files is None:
            self.unattended_files = []
        if self.gpp_passwords is None:
            self.gpp_passwords = []
        if self.credential_files is None:
            self.credential_files = []
        if self.autostart_programs is None:
            self.autostart_programs = []
        if self.registry_autologon is None:
            self.registry_autologon = {}
        if self.network_interfaces is None:
            self.network_interfaces = []
        if self.listening_ports is None:
            self.listening_ports = []
        if self.active_connections is None:
            self.active_connections = []
        if self.firewall_rules is None:
            self.firewall_rules = []
        if self.installed_programs is None:
            self.installed_programs = []
        if self.running_processes is None:
            self.running_processes = []
        if self.scheduled_tasks is None:
            self.scheduled_tasks = []
        if self.av_products is None:
            self.av_products = []
        if self.wsl_distributions is None:
            self.wsl_distributions = []
        if self.wifi_profiles is None:
            self.wifi_profiles = []
        if self.saved_rdp_connections is None:
            self.saved_rdp_connections = []
        if self.credential_manager_entries is None:
            self.credential_manager_entries = []
        if self.dpapi_masterkeys is None:
            self.dpapi_masterkeys = []
        if self.installed_drivers is None:
            self.installed_drivers = []
        if self.pnp_devices is None:
            self.pnp_devices = []


def run_powershell(command: str) -> str:
    """Execute PowerShell command and return output."""
    try:
        # Use PowerShell with execution policy bypass
        ps_cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", command]
        result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def run_cmd(command: str) -> str:
    """Execute cmd command and return output."""
    try:
        result = subprocess.run(["cmd", "/c", command], capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def enumerate_system_info() -> Dict[str, str]:
    """Gather basic Windows system information."""
    info = {}
    
    print(paint("🔍 Gathering system information...", Colors.CYAN, True))
    
    # Hostname
    hostname = run_cmd("hostname")
    info["hostname"] = hostname
    
    # OS Version
    os_info = run_powershell("Get-WmiObject -Class Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, InstallDate, LastBootUpTime")
    if os_info:
        lines = os_info.split('\n')
        for line in lines:
            if "Caption" in line and ":" in line:
                info["os_version"] = line.split(":", 1)[1].strip()
            elif "Version" in line and ":" in line:
                version = line.split(":", 1)[1].strip()
                if version != info.get("os_version", ""):
                    info["os_build"] = version
            elif "BuildNumber" in line and ":" in line:
                info["os_build"] = line.split(":", 1)[1].strip()
    
    # Architecture
    arch = run_cmd("echo %PROCESSOR_ARCHITECTURE%")
    info["architecture"] = arch
    
    # Domain/Workgroup
    domain_info = run_powershell("Get-WmiObject -Class Win32_ComputerSystem | Select-Object Domain, Workgroup")
    if domain_info:
        for line in domain_info.split('\n'):
            if "Domain" in line and ":" in line:
                info["domain"] = line.split(":", 1)[1].strip()
            elif "Workgroup" in line and ":" in line:
                info["workgroup"] = line.split(":", 1)[1].strip()
    
    # Timezone
    tz_info = run_powershell("Get-TimeZone | Select-Object Id")
    if tz_info and ":" in tz_info:
        info["timezone"] = tz_info.split(":", 1)[1].strip()
    
    return info


def enumerate_current_user() -> Dict[str, Any]:
    """Enumerate current user context and privileges."""
    info = {}
    
    print(paint("👤 Gathering user context...", Colors.CYAN, True))
    
    # Current user
    current_user = run_cmd("echo %USERNAME%")
    info["current_user"] = current_user
    
    # User SID
    sid_output = run_powershell("(Get-WmiObject -Class Win32_UserAccount -Filter \"Name='%USERNAME%'\").SID")
    info["user_sid"] = sid_output
    
    # User groups
    groups_output = run_cmd("whoami /groups")
    groups = []
    if groups_output:
        lines = groups_output.split('\n')[3:]  # Skip header lines
        for line in lines:
            if line.strip() and not line.startswith("="):
                parts = line.split()
                if parts:
                    groups.append(parts[0])
    info["user_groups"] = groups
    
    # User privileges
    privs_output = run_cmd("whoami /priv")
    privileges = []
    if privs_output:
        lines = privs_output.split('\n')
        for line in lines:
            if "Se" in line and ("Enabled" in line or "Disabled" in line):
                parts = line.split()
                if len(parts) >= 2:
                    priv_name = parts[0]
                    status = "Enabled" if "Enabled" in line else "Disabled"
                    privileges.append(f"{priv_name} ({status})")
    info["user_privileges"] = privileges
    
    # Check if admin
    admin_check = run_cmd("net user %USERNAME% | findstr /C:\"Local Group Memberships\"")
    info["is_admin"] = "Administrators" in admin_check
    
    # UAC Level
    uac_output = run_powershell("Get-ItemProperty HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System -Name ConsentPromptBehaviorAdmin")
    if uac_output and ":" in uac_output:
        uac_value = uac_output.split(":", 1)[1].strip()
        uac_levels = {
            "0": "Never notify",
            "1": "Prompt for credentials on the secure desktop",
            "2": "Prompt for consent on the secure desktop", 
            "5": "Prompt for consent for non-Windows binaries"
        }
        info["uac_level"] = uac_levels.get(uac_value, f"Unknown ({uac_value})")
    
    return info


def enumerate_users_groups() -> Dict[str, List]:
    """Enumerate local users and groups."""
    info = {"local_users": [], "local_groups": [], "recent_logons": []}
    
    print(paint("👥 Enumerating users and groups...", Colors.CYAN, True))
    
    # Local users
    users_output = run_cmd("net user")
    if users_output:
        # Extract usernames from net user output
        lines = users_output.split('\n')
        for line in lines:
            if line.strip() and not line.startswith("-") and "User accounts for" not in line:
                users_in_line = line.split()
                for user in users_in_line:
                    if user.strip():
                        info["local_users"].append({"username": user.strip()})
    
    # Local groups
    groups_output = run_cmd("net localgroup")
    if groups_output:
        lines = groups_output.split('\n')
        for line in lines:
            if line.strip() and line.startswith("*"):
                group_name = line.strip().lstrip("*").strip()
                if group_name:
                    info["local_groups"].append({"groupname": group_name})
    
    # Recent logons (from event log - simplified)
    logon_output = run_powershell("Get-EventLog -LogName Security -InstanceId 4624 -Newest 10 -ErrorAction SilentlyContinue | Select-Object TimeGenerated, Message")
    if logon_output:
        info["recent_logons"] = [line.strip() for line in logon_output.split('\n')[:10] if line.strip()]
    
    return info


def enumerate_services() -> Dict[str, List]:
    """Enumerate Windows services and their configurations."""
    info = {
        "running_services": [],
        "stopped_services": [],
        "unquoted_service_paths": [],
        "weak_service_permissions": []
    }
    
    print(paint("⚙️ Enumerating services...", Colors.CYAN, True))
    
    # Get all services
    services_output = run_powershell("Get-WmiObject -Class Win32_Service | Select-Object Name, State, PathName, StartMode, StartName")
    
    if services_output:
        lines = services_output.split('\n')
        current_service = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "Name" in line and ":" in line:
                if current_service:
                    # Process previous service
                    if current_service.get("State") == "Running":
                        info["running_services"].append(current_service.copy())
                    else:
                        info["stopped_services"].append(current_service.copy())
                    
                    # Check for unquoted paths
                    path = current_service.get("PathName", "")
                    if path and not path.startswith('"') and " " in path:
                        info["unquoted_service_paths"].append({
                            "service": current_service.get("Name", ""),
                            "path": path
                        })
                
                current_service = {"Name": line.split(":", 1)[1].strip()}
            
            elif "State" in line and ":" in line:
                current_service["State"] = line.split(":", 1)[1].strip()
            elif "PathName" in line and ":" in line:
                current_service["PathName"] = line.split(":", 1)[1].strip()
            elif "StartMode" in line and ":" in line:
                current_service["StartMode"] = line.split(":", 1)[1].strip()
            elif "StartName" in line and ":" in line:
                current_service["StartName"] = line.split(":", 1)[1].strip()
        
        # Process last service
        if current_service:
            if current_service.get("State") == "Running":
                info["running_services"].append(current_service.copy())
            else:
                info["stopped_services"].append(current_service.copy())
    
    return info


def enumerate_network() -> Dict[str, List]:
    """Enumerate network configuration and connections."""
    info = {
        "network_interfaces": [],
        "listening_ports": [],
        "active_connections": [],
        "firewall_rules": []
    }
    
    print(paint("🌐 Enumerating network configuration...", Colors.CYAN, True))
    
    # Network interfaces
    interfaces_output = run_powershell("Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object {$_.IPEnabled} | Select-Object Description, IPAddress, SubnetMask, DefaultIPGateway")
    if interfaces_output:
        info["network_interfaces"] = [{"description": "Network interfaces found"}]
    
    # Listening ports
    netstat_output = run_cmd("netstat -an")
    if netstat_output:
        lines = netstat_output.split('\n')
        for line in lines:
            if "LISTENING" in line or "ESTABLISHED" in line:
                parts = line.split()
                if len(parts) >= 4:
                    info["listening_ports"].append({
                        "protocol": parts[0],
                        "local_address": parts[1],
                        "state": parts[3] if len(parts) > 3 else ""
                    })
    
    # Firewall status
    fw_status = run_cmd("netsh advfirewall show allprofiles")
    info["firewall_status"] = "Enabled" if "ON" in fw_status else "Disabled"
    
    return info


def enumerate_installed_software() -> Dict[str, List]:
    """Enumerate installed software and running processes."""
    info = {"installed_programs": [], "running_processes": []}
    
    print(paint("💾 Enumerating installed software...", Colors.CYAN, True))
    
    # Installed programs from registry
    programs_output = run_powershell("Get-WmiObject -Class Win32_Product | Select-Object Name, Version, Vendor")
    if programs_output:
        lines = programs_output.split('\n')
        current_program = {}
        
        for line in lines:
            if "Name" in line and ":" in line:
                if current_program:
                    info["installed_programs"].append(current_program.copy())
                current_program = {"Name": line.split(":", 1)[1].strip()}
            elif "Version" in line and ":" in line:
                current_program["Version"] = line.split(":", 1)[1].strip()
            elif "Vendor" in line and ":" in line:
                current_program["Vendor"] = line.split(":", 1)[1].strip()
        
        if current_program:
            info["installed_programs"].append(current_program)
    
    # Running processes
    processes_output = run_cmd("tasklist /fo csv")
    if processes_output:
        lines = processes_output.split('\n')[1:]  # Skip header
        for line in lines[:20]:  # Limit to first 20 processes
            if line.strip():
                parts = line.split(',')
                if len(parts) >= 2:
                    process_name = parts[0].strip('"')
                    pid = parts[1].strip('"')
                    info["running_processes"].append({
                        "name": process_name,
                        "pid": pid
                    })
    
    return info


def enumerate_credentials() -> Dict[str, List]:
    """Look for credentials and sensitive files."""
    info = {
        "wifi_profiles": [],
        "credential_manager_entries": [],
        "unattended_files": [],
        "dpapi_masterkeys": []
    }
    
    print(paint("🔑 Searching for credentials...", Colors.CYAN, True))
    
    # WiFi profiles
    wifi_output = run_cmd("netsh wlan show profiles")
    if wifi_output:
        lines = wifi_output.split('\n')
        for line in lines:
            if "All User Profile" in line and ":" in line:
                profile_name = line.split(":", 1)[1].strip()
                info["wifi_profiles"].append({"profile": profile_name})
    
    # Credential Manager
    cmdkey_output = run_cmd("cmdkey /list")
    if cmdkey_output:
        info["credential_manager_entries"] = [line.strip() for line in cmdkey_output.split('\n')[:10] if line.strip()]
    
    # Common unattended files locations
    unattended_paths = [
        "C:\\Windows\\Panther\\unattend.xml",
        "C:\\Windows\\Panther\\Unattended.xml",
        "C:\\Windows\\System32\\sysprep\\Unattend.xml",
        "C:\\unattend.xml"
    ]
    
    for path in unattended_paths:
        if run_cmd(f"dir \"{path}\" 2>nul"):
            info["unattended_files"].append(path)
    
    return info


def enumerate_registry_settings() -> Dict[str, Any]:
    """Check important registry settings."""
    info = {"always_install_elevated": False, "registry_autologon": {}}
    
    print(paint("📝 Checking registry settings...", Colors.CYAN, True))
    
    # AlwaysInstallElevated
    aie_hklm = run_powershell("Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer' -Name AlwaysInstallElevated -ErrorAction SilentlyContinue")
    aie_hkcu = run_powershell("Get-ItemProperty -Path 'HKCU:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer' -Name AlwaysInstallElevated -ErrorAction SilentlyContinue")
    
    if "1" in aie_hklm and "1" in aie_hkcu:
        info["always_install_elevated"] = True
    
    # AutoLogon
    autologon = run_powershell("Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name AutoAdminLogon -ErrorAction SilentlyContinue")
    if "1" in autologon:
        username = run_powershell("Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name DefaultUserName -ErrorAction SilentlyContinue")
        password = run_powershell("Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name DefaultPassword -ErrorAction SilentlyContinue")
        info["registry_autologon"] = {
            "enabled": True,
            "username": username.split(":")[-1].strip() if ":" in username else "",
            "password_set": "DefaultPassword" in password
        }
    
    return info


def run_enumeration() -> WindowsSystemInfo:
    """Run complete Windows enumeration."""
    system_info = WindowsSystemInfo()
    
    # Basic system information
    basic_info = enumerate_system_info()
    for key, value in basic_info.items():
        setattr(system_info, key, value)
    
    # Current user context
    user_info = enumerate_current_user()
    for key, value in user_info.items():
        setattr(system_info, key, value)
    
    # Users and groups
    users_info = enumerate_users_groups()
    for key, value in users_info.items():
        setattr(system_info, key, value)
    
    # Services
    services_info = enumerate_services()
    for key, value in services_info.items():
        setattr(system_info, key, value)
    
    # Network
    network_info = enumerate_network()
    for key, value in network_info.items():
        setattr(system_info, key, value)
    
    # Installed software
    software_info = enumerate_installed_software()
    for key, value in software_info.items():
        setattr(system_info, key, value)
    
    # Credentials
    creds_info = enumerate_credentials()
    for key, value in creds_info.items():
        setattr(system_info, key, value)
    
    # Registry settings
    registry_info = enumerate_registry_settings()
    for key, value in registry_info.items():
        setattr(system_info, key, value)
    
    return system_info


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Windows Post-Exploitation Enumeration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic enumeration
    python3 -m redshift_toolkit.postex.windows_enum
    
    # JSON output
    python3 -m redshift_toolkit.postex.windows_enum --format json
    
    # No color output
    python3 -m redshift_toolkit.postex.windows_enum --no-color

Note:
    - Requires Windows system or Windows-compatible environment
    - Uses PowerShell and cmd commands for data gathering
    - Some functions may require administrative privileges
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
    
    # Check if we're on Windows
    if os.name != "nt":
        print(paint("⚠️  Warning: This script is designed for Windows systems", Colors.YELLOW, use_color))
        print(paint("📋 Results may be limited on non-Windows platforms", Colors.GREY, use_color))
    
    try:
        # Run enumeration
        results = run_enumeration()
        
        if args.format == "json":
            print(json.dumps(asdict(results), indent=2, default=str))
        else:
            print(paint(f"\n🎯 Windows Enumeration Complete", Colors.GREEN, use_color))
            print(paint(f"🖥️  Hostname: {results.hostname}", Colors.YELLOW, use_color))
            print(paint(f"👤 Current User: {results.current_user}", Colors.YELLOW, use_color))
            print(paint(f"🔑 Is Admin: {'Yes' if results.is_admin else 'No'}", Colors.YELLOW, use_color))
            print(paint(f"🛡️  UAC Level: {results.uac_level}", Colors.YELLOW, use_color))
            print(paint(f"⚙️  Running Services: {len(results.running_services)}", Colors.YELLOW, use_color))
            print(paint(f"📊 Unquoted Service Paths: {len(results.unquoted_service_paths)}", Colors.RED if results.unquoted_service_paths else Colors.GREEN, use_color))
            print(paint(f"🔧 AlwaysInstallElevated: {'Yes' if results.always_install_elevated else 'No'}", Colors.RED if results.always_install_elevated else Colors.GREEN, use_color))
            
            if results.user_privileges:
                dangerous_privs = [p for p in results.user_privileges if any(dangerous in p for dangerous in ['SeImpersonate', 'SeAssignPrimary', 'SeBackup', 'SeRestore', 'SeDebug', 'SeTakeOwnership'])]
                if dangerous_privs:
                    print(paint(f"🎯 Dangerous Privileges: {len(dangerous_privs)} found", Colors.RED, use_color))
        
    except KeyboardInterrupt:
        print(paint("\n❌ Enumeration interrupted", Colors.RED, use_color))
        sys.exit(1)
    except Exception as e:
        print(paint(f"❌ Error during enumeration: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
