#!/usr/bin/env python3
"""
Linux Post-Exploitation Enumeration Script

Comprehensive system enumeration for privilege escalation research.
Outputs structured JSON with 80+ fields covering system information,
security configurations, and potential attack vectors.

Usage:
    python3 -m redshift_toolkit.postex.linux_enum
    python3 -m redshift_toolkit.postex.linux_enum --format json
    python3 -m redshift_toolkit.postex.linux_enum --no-color

Author: Redshift Project — Module 20
License: MIT
"""

from __future__ import annotations

import json
import os
import pwd
import grp
import stat
import subprocess
import socket
import glob
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
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
class LinuxSystemInfo:
    """Complete Linux system enumeration results."""
    
    # Basic System Information
    hostname: str = ""
    os_release: Dict[str, str] = None
    kernel_version: str = ""
    architecture: str = ""
    uptime: str = ""
    timezone: str = ""
    
    # Current User Context
    current_user: str = ""
    current_uid: int = 0
    current_gid: int = 0
    current_groups: List[str] = None
    home_directory: str = ""
    shell: str = ""
    
    # Users and Groups
    users: List[Dict[str, Any]] = None
    groups: List[Dict[str, Any]] = None
    recent_logins: List[str] = None
    
    # File System
    world_writable_files: List[str] = None
    world_writable_dirs: List[str] = None
    suid_binaries: List[str] = None
    sgid_binaries: List[str] = None
    capabilities: List[Dict[str, str]] = None
    sticky_bit_dirs: List[str] = None
    
    # SSH Configuration
    ssh_keys: List[Dict[str, str]] = None
    ssh_config: Dict[str, Any] = None
    authorized_keys: List[str] = None
    
    # Processes and Services
    running_processes: List[Dict[str, Any]] = None
    listening_ports: List[Dict[str, Any]] = None
    active_connections: List[Dict[str, str]] = None
    
    # Scheduled Tasks
    cron_jobs: List[Dict[str, str]] = None
    systemd_timers: List[str] = None
    at_jobs: List[str] = None
    
    # Sudo and Privileges
    sudo_version: str = ""
    sudoers_readable: bool = False
    sudo_rules: List[str] = None
    
    # Environment and Configuration
    environment_vars: Dict[str, str] = None
    path_dirs: List[str] = None
    ld_preload: str = ""
    ld_library_path: str = ""
    
    # Mounted File Systems
    mounts: List[Dict[str, str]] = None
    nfs_mounts: List[str] = None
    
    # Container and Virtualization
    docker_socket: bool = False
    docker_group: bool = False
    lxc_containers: List[str] = None
    kubernetes_token: bool = False
    vm_type: str = ""
    
    # Development and Compilers
    compilers: List[str] = None
    interpreters: List[str] = None
    development_tools: List[str] = None
    
    # Security Tools and Configs
    apparmor_status: str = ""
    selinux_status: str = ""
    iptables_rules: List[str] = None
    
    # Log Files
    readable_logs: List[str] = None
    
    # Interesting Files
    config_files: List[str] = None
    backup_files: List[str] = None
    database_files: List[str] = None
    
    # Network Configuration
    network_interfaces: List[Dict[str, str]] = None
    dns_servers: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists and dicts."""
        if self.os_release is None:
            self.os_release = {}
        if self.current_groups is None:
            self.current_groups = []
        if self.users is None:
            self.users = []
        if self.groups is None:
            self.groups = []
        if self.recent_logins is None:
            self.recent_logins = []
        if self.world_writable_files is None:
            self.world_writable_files = []
        if self.world_writable_dirs is None:
            self.world_writable_dirs = []
        if self.suid_binaries is None:
            self.suid_binaries = []
        if self.sgid_binaries is None:
            self.sgid_binaries = []
        if self.capabilities is None:
            self.capabilities = []
        if self.sticky_bit_dirs is None:
            self.sticky_bit_dirs = []
        if self.ssh_keys is None:
            self.ssh_keys = []
        if self.ssh_config is None:
            self.ssh_config = {}
        if self.authorized_keys is None:
            self.authorized_keys = []
        if self.running_processes is None:
            self.running_processes = []
        if self.listening_ports is None:
            self.listening_ports = []
        if self.active_connections is None:
            self.active_connections = []
        if self.cron_jobs is None:
            self.cron_jobs = []
        if self.systemd_timers is None:
            self.systemd_timers = []
        if self.at_jobs is None:
            self.at_jobs = []
        if self.sudo_rules is None:
            self.sudo_rules = []
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.path_dirs is None:
            self.path_dirs = []
        if self.mounts is None:
            self.mounts = []
        if self.nfs_mounts is None:
            self.nfs_mounts = []
        if self.lxc_containers is None:
            self.lxc_containers = []
        if self.compilers is None:
            self.compilers = []
        if self.interpreters is None:
            self.interpreters = []
        if self.development_tools is None:
            self.development_tools = []
        if self.iptables_rules is None:
            self.iptables_rules = []
        if self.readable_logs is None:
            self.readable_logs = []
        if self.config_files is None:
            self.config_files = []
        if self.backup_files is None:
            self.backup_files = []
        if self.database_files is None:
            self.database_files = []
        if self.network_interfaces is None:
            self.network_interfaces = []
        if self.dns_servers is None:
            self.dns_servers = []


def run_command(cmd: List[str], capture_stderr: bool = True) -> str:
    """Execute command and return stdout, suppress errors."""
    try:
        if capture_stderr:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return ""


def enumerate_system_info() -> Dict[str, Any]:
    """Gather basic system information."""
    info = {}
    
    # Hostname
    info["hostname"] = socket.gethostname()
    
    # OS Release
    os_release = {}
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os_release[key] = value.strip('"')
    except FileNotFoundError:
        pass
    info["os_release"] = os_release
    
    # Kernel version
    info["kernel_version"] = run_command(["uname", "-r"])
    
    # Architecture
    info["architecture"] = run_command(["uname", "-m"])
    
    # Uptime
    info["uptime"] = run_command(["uptime"])
    
    # Timezone
    info["timezone"] = run_command(["timedatectl", "show", "--value", "-p", "Timezone"])
    
    return info


def enumerate_user_context() -> Dict[str, Any]:
    """Gather current user and group information."""
    info = {}
    
    # Current user context
    info["current_user"] = os.getenv("USER", "")
    info["current_uid"] = os.getuid()
    info["current_gid"] = os.getgid()
    
    # Current groups
    try:
        groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
        info["current_groups"] = groups
    except KeyError:
        info["current_groups"] = []
    
    # Home directory
    info["home_directory"] = os.path.expanduser("~")
    
    # Shell
    info["shell"] = os.getenv("SHELL", "")
    
    return info


def enumerate_users_groups() -> Dict[str, Any]:
    """Enumerate all system users and groups."""
    info = {"users": [], "groups": []}
    
    # Users from /etc/passwd
    try:
        with open("/etc/passwd", "r") as f:
            for line in f:
                fields = line.strip().split(":")
                if len(fields) >= 7:
                    user = {
                        "username": fields[0],
                        "uid": fields[2],
                        "gid": fields[3],
                        "home": fields[5],
                        "shell": fields[6]
                    }
                    info["users"].append(user)
    except FileNotFoundError:
        pass
    
    # Groups from /etc/group
    try:
        with open("/etc/group", "r") as f:
            for line in f:
                fields = line.strip().split(":")
                if len(fields) >= 4:
                    group = {
                        "groupname": fields[0],
                        "gid": fields[2],
                        "members": fields[3].split(",") if fields[3] else []
                    }
                    info["groups"].append(group)
    except FileNotFoundError:
        pass
    
    # Recent logins
    last_output = run_command(["last", "-n", "20"])
    info["recent_logins"] = last_output.split("\n")[:20] if last_output else []
    
    return info


def enumerate_file_permissions() -> Dict[str, Any]:
    """Find interesting file permissions."""
    info = {
        "world_writable_files": [],
        "world_writable_dirs": [],
        "suid_binaries": [],
        "sgid_binaries": [],
        "capabilities": [],
        "sticky_bit_dirs": []
    }
    
    # World writable files (limit search to common directories)
    search_paths = ["/tmp", "/var/tmp", "/dev/shm", "/etc", "/var", "/opt", "/usr/local"]
    for search_path in search_paths:
        if os.path.exists(search_path):
            try:
                # Find world-writable files
                cmd = f"find {search_path} -type f -perm -002 2>/dev/null | head -50"
                result = run_command(["bash", "-c", cmd])
                if result:
                    info["world_writable_files"].extend(result.split("\n"))
                
                # Find world-writable directories
                cmd = f"find {search_path} -type d -perm -002 2>/dev/null | head -50"
                result = run_command(["bash", "-c", cmd])
                if result:
                    info["world_writable_dirs"].extend(result.split("\n"))
            except Exception:
                pass
    
    # SUID binaries
    suid_output = run_command(["bash", "-c", "find /usr /bin /sbin -type f -perm -4000 2>/dev/null"])
    if suid_output:
        info["suid_binaries"] = suid_output.split("\n")
    
    # SGID binaries
    sgid_output = run_command(["bash", "-c", "find /usr /bin /sbin -type f -perm -2000 2>/dev/null"])
    if sgid_output:
        info["sgid_binaries"] = sgid_output.split("\n")
    
    # File capabilities
    getcap_output = run_command(["bash", "-c", "getcap -r /usr /bin /sbin 2>/dev/null"])
    if getcap_output:
        for line in getcap_output.split("\n"):
            if "=" in line:
                path, caps = line.split("=", 1)
                info["capabilities"].append({"path": path.strip(), "capabilities": caps.strip()})
    
    return info


def enumerate_ssh_info() -> Dict[str, Any]:
    """Gather SSH-related information."""
    info = {"ssh_keys": [], "ssh_config": {}, "authorized_keys": []}
    
    # SSH keys in common locations
    ssh_key_paths = [
        "~/.ssh/id_rsa", "~/.ssh/id_ecdsa", "~/.ssh/id_ed25519",
        "/root/.ssh/id_rsa", "/root/.ssh/id_ecdsa", "/root/.ssh/id_ed25519"
    ]
    
    for key_path in ssh_key_paths:
        expanded_path = os.path.expanduser(key_path)
        if os.path.exists(expanded_path) and os.access(expanded_path, os.R_OK):
            try:
                with open(expanded_path, "r") as f:
                    first_line = f.readline().strip()
                info["ssh_keys"].append({
                    "path": expanded_path,
                    "type": first_line.split()[0] if first_line else "unknown"
                })
            except Exception:
                pass
    
    # SSH configuration
    ssh_config_path = "/etc/ssh/sshd_config"
    if os.path.exists(ssh_config_path) and os.access(ssh_config_path, os.R_OK):
        try:
            with open(ssh_config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and " " in line:
                        key, value = line.split(None, 1)
                        info["ssh_config"][key.lower()] = value
        except Exception:
            pass
    
    # Authorized keys
    auth_keys_paths = ["~/.ssh/authorized_keys", "/root/.ssh/authorized_keys"]
    for auth_path in auth_keys_paths:
        expanded_path = os.path.expanduser(auth_path)
        if os.path.exists(expanded_path) and os.access(expanded_path, os.R_OK):
            try:
                with open(expanded_path, "r") as f:
                    info["authorized_keys"].extend([line.strip() for line in f if line.strip()])
            except Exception:
                pass
    
    return info


def enumerate_processes_network() -> Dict[str, Any]:
    """Enumerate running processes and network connections."""
    info = {
        "running_processes": [],
        "listening_ports": [],
        "active_connections": []
    }
    
    # Running processes
    ps_output = run_command(["ps", "aux"])
    if ps_output:
        lines = ps_output.split("\n")[1:]  # Skip header
        for line in lines[:50]:  # Limit to first 50 processes
            fields = line.split(None, 10)
            if len(fields) >= 11:
                process = {
                    "user": fields[0],
                    "pid": fields[1],
                    "command": fields[10]
                }
                info["running_processes"].append(process)
    
    # Listening ports
    netstat_output = run_command(["netstat", "-tuln"])
    if netstat_output:
        for line in netstat_output.split("\n"):
            if "LISTEN" in line or "udp" in line:
                fields = line.split()
                if len(fields) >= 4:
                    port_info = {
                        "protocol": fields[0],
                        "address": fields[3]
                    }
                    info["listening_ports"].append(port_info)
    
    # Active connections
    active_output = run_command(["netstat", "-tun"])
    if active_output:
        for line in active_output.split("\n")[2:22]:  # Skip headers, limit to 20
            if "ESTABLISHED" in line:
                fields = line.split()
                if len(fields) >= 5:
                    conn_info = {
                        "local": fields[3],
                        "remote": fields[4],
                        "state": fields[5]
                    }
                    info["active_connections"].append(conn_info)
    
    return info


def enumerate_scheduled_tasks() -> Dict[str, Any]:
    """Enumerate cron jobs and scheduled tasks."""
    info = {
        "cron_jobs": [],
        "systemd_timers": [],
        "at_jobs": []
    }
    
    # System crontab
    cron_files = ["/etc/crontab", "/etc/cron.d/*", "/etc/cron.daily", "/etc/cron.hourly"]
    for pattern in cron_files:
        for filepath in glob.glob(pattern):
            if os.path.isfile(filepath) and os.access(filepath, os.R_OK):
                try:
                    with open(filepath, "r") as f:
                        content = f.read().strip()
                        if content:
                            info["cron_jobs"].append({"file": filepath, "content": content[:500]})
                except Exception:
                    pass
    
    # User crontab
    crontab_output = run_command(["crontab", "-l"])
    if crontab_output:
        info["cron_jobs"].append({"file": "user_crontab", "content": crontab_output[:500]})
    
    # Systemd timers
    timers_output = run_command(["systemctl", "list-timers", "--no-pager"])
    if timers_output:
        info["systemd_timers"] = timers_output.split("\n")[:20]
    
    # At jobs
    at_output = run_command(["atq"])
    if at_output:
        info["at_jobs"] = at_output.split("\n")
    
    return info


def enumerate_sudo() -> Dict[str, Any]:
    """Check sudo configuration and permissions."""
    info = {
        "sudo_version": "",
        "sudoers_readable": False,
        "sudo_rules": []
    }
    
    # Sudo version
    info["sudo_version"] = run_command(["sudo", "--version"])
    
    # Check if sudoers is readable
    sudoers_path = "/etc/sudoers"
    info["sudoers_readable"] = os.access(sudoers_path, os.R_OK)
    
    # Try to get sudo rules
    sudo_l_output = run_command(["sudo", "-l"], capture_stderr=False)
    if sudo_l_output:
        info["sudo_rules"] = sudo_l_output.split("\n")
    
    return info


def enumerate_environment() -> Dict[str, Any]:
    """Enumerate environment variables and library paths."""
    info = {
        "environment_vars": dict(os.environ),
        "path_dirs": os.environ.get("PATH", "").split(":"),
        "ld_preload": os.environ.get("LD_PRELOAD", ""),
        "ld_library_path": os.environ.get("LD_LIBRARY_PATH", "")
    }
    return info


def enumerate_mounts() -> Dict[str, Any]:
    """Enumerate mounted filesystems."""
    info = {"mounts": [], "nfs_mounts": []}
    
    # Parse /proc/mounts
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                fields = line.strip().split()
                if len(fields) >= 3:
                    mount = {
                        "device": fields[0],
                        "mountpoint": fields[1],
                        "filesystem": fields[2],
                        "options": fields[3] if len(fields) > 3 else ""
                    }
                    info["mounts"].append(mount)
                    
                    # Check for NFS mounts
                    if fields[2].startswith("nfs"):
                        info["nfs_mounts"].append(line.strip())
    except FileNotFoundError:
        pass
    
    return info


def enumerate_containers() -> Dict[str, Any]:
    """Check for container and virtualization indicators."""
    info = {
        "docker_socket": False,
        "docker_group": False,
        "lxc_containers": [],
        "kubernetes_token": False,
        "vm_type": ""
    }
    
    # Docker socket
    info["docker_socket"] = os.path.exists("/var/run/docker.sock")
    
    # Docker group membership
    try:
        docker_group = grp.getgrnam("docker")
        current_groups = os.getgroups()
        info["docker_group"] = docker_group.gr_gid in current_groups
    except KeyError:
        pass
    
    # LXC containers
    lxc_path = "/var/lib/lxc"
    if os.path.exists(lxc_path):
        try:
            info["lxc_containers"] = os.listdir(lxc_path)
        except PermissionError:
            pass
    
    # Kubernetes service account token
    k8s_token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    info["kubernetes_token"] = os.path.exists(k8s_token_path)
    
    # VM type detection
    vm_indicators = [
        ("/sys/class/dmi/id/product_name", ["VMware", "VirtualBox", "KVM"]),
        ("/proc/cpuinfo", ["vmware", "qemu"]),
        ("/sys/devices/virtual/dmi/id/bios_vendor", ["VMware"])
    ]
    
    for filepath, indicators in vm_indicators:
        try:
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read().lower()
                    for indicator in indicators:
                        if indicator.lower() in content:
                            info["vm_type"] = indicator
                            break
        except Exception:
            continue
    
    return info


def enumerate_development_tools() -> Dict[str, Any]:
    """Check for development tools and compilers."""
    info = {
        "compilers": [],
        "interpreters": [],
        "development_tools": []
    }
    
    # Common compilers
    compilers = ["gcc", "g++", "clang", "rustc", "go", "javac"]
    for compiler in compilers:
        if run_command(["which", compiler]):
            info["compilers"].append(compiler)
    
    # Common interpreters
    interpreters = ["python", "python3", "perl", "ruby", "node", "php"]
    for interpreter in interpreters:
        if run_command(["which", interpreter]):
            info["interpreters"].append(interpreter)
    
    # Development tools
    dev_tools = ["make", "cmake", "git", "vim", "nano", "wget", "curl", "nc", "netcat"]
    for tool in dev_tools:
        if run_command(["which", tool]):
            info["development_tools"].append(tool)
    
    return info


def enumerate_security_configs() -> Dict[str, Any]:
    """Check security configurations."""
    info = {
        "apparmor_status": "",
        "selinux_status": "",
        "iptables_rules": []
    }
    
    # AppArmor
    info["apparmor_status"] = run_command(["aa-status"])
    
    # SELinux
    info["selinux_status"] = run_command(["sestatus"])
    
    # Iptables rules
    iptables_output = run_command(["iptables", "-L"])
    if iptables_output:
        info["iptables_rules"] = iptables_output.split("\n")
    
    return info


def run_enumeration() -> LinuxSystemInfo:
    """Run complete Linux enumeration."""
    system_info = LinuxSystemInfo()
    
    # Gather all information
    print(paint("🔍 Enumerating system information...", Colors.CYAN, True))
    basic_info = enumerate_system_info()
    for key, value in basic_info.items():
        setattr(system_info, key, value)
    
    print(paint("👤 Enumerating user context...", Colors.CYAN, True))
    user_info = enumerate_user_context()
    for key, value in user_info.items():
        setattr(system_info, key, value)
    
    print(paint("👥 Enumerating users and groups...", Colors.CYAN, True))
    users_info = enumerate_users_groups()
    for key, value in users_info.items():
        setattr(system_info, key, value)
    
    print(paint("📁 Enumerating file permissions...", Colors.CYAN, True))
    file_info = enumerate_file_permissions()
    for key, value in file_info.items():
        setattr(system_info, key, value)
    
    print(paint("🔑 Enumerating SSH configuration...", Colors.CYAN, True))
    ssh_info = enumerate_ssh_info()
    for key, value in ssh_info.items():
        setattr(system_info, key, value)
    
    print(paint("🔄 Enumerating processes and network...", Colors.CYAN, True))
    proc_info = enumerate_processes_network()
    for key, value in proc_info.items():
        setattr(system_info, key, value)
    
    print(paint("⏰ Enumerating scheduled tasks...", Colors.CYAN, True))
    sched_info = enumerate_scheduled_tasks()
    for key, value in sched_info.items():
        setattr(system_info, key, value)
    
    print(paint("🛡️ Enumerating sudo configuration...", Colors.CYAN, True))
    sudo_info = enumerate_sudo()
    for key, value in sudo_info.items():
        setattr(system_info, key, value)
    
    print(paint("🌍 Enumerating environment...", Colors.CYAN, True))
    env_info = enumerate_environment()
    for key, value in env_info.items():
        setattr(system_info, key, value)
    
    print(paint("💾 Enumerating mounts...", Colors.CYAN, True))
    mount_info = enumerate_mounts()
    for key, value in mount_info.items():
        setattr(system_info, key, value)
    
    print(paint("📦 Enumerating containers...", Colors.CYAN, True))
    container_info = enumerate_containers()
    for key, value in container_info.items():
        setattr(system_info, key, value)
    
    print(paint("⚒️ Enumerating development tools...", Colors.CYAN, True))
    dev_info = enumerate_development_tools()
    for key, value in dev_info.items():
        setattr(system_info, key, value)
    
    print(paint("🔒 Enumerating security configurations...", Colors.CYAN, True))
    sec_info = enumerate_security_configs()
    for key, value in sec_info.items():
        setattr(system_info, key, value)
    
    return system_info


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Linux Post-Exploitation Enumeration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic enumeration
    python3 -m redshift_toolkit.postex.linux_enum
    
    # JSON output
    python3 -m redshift_toolkit.postex.linux_enum --format json
    
    # No color output
    python3 -m redshift_toolkit.postex.linux_enum --no-color
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
        # Run enumeration
        results = run_enumeration()
        
        if args.format == "json":
            print(json.dumps(asdict(results), indent=2, default=str))
        else:
            print(paint(f"\n🎯 Linux Enumeration Complete for: {results.hostname}", Colors.GREEN, use_color))
            print(paint(f"📊 Current User: {results.current_user} (UID: {results.current_uid})", Colors.YELLOW, use_color))
            print(paint(f"🖥️  OS: {results.os_release.get('PRETTY_NAME', 'Unknown')}", Colors.YELLOW, use_color))
            print(paint(f"🔧 Kernel: {results.kernel_version}", Colors.YELLOW, use_color))
            print(paint(f"⚡ SUID Binaries Found: {len(results.suid_binaries)}", Colors.YELLOW, use_color))
            print(paint(f"🔑 SSH Keys Found: {len(results.ssh_keys)}", Colors.YELLOW, use_color))
            print(paint(f"🐳 Docker Access: {'Yes' if results.docker_socket or results.docker_group else 'No'}", Colors.YELLOW, use_color))
            print(paint(f"☸️  Kubernetes Token: {'Yes' if results.kubernetes_token else 'No'}", Colors.YELLOW, use_color))
            
            if results.capabilities:
                print(paint(f"🎯 File Capabilities: {len(results.capabilities)} found", Colors.RED, use_color))
            
            if results.world_writable_files:
                print(paint(f"⚠️  World-Writable Files: {len(results.world_writable_files)} found", Colors.RED, use_color))
        
    except KeyboardInterrupt:
        print(paint("\n❌ Enumeration interrupted", Colors.RED, use_color))
        sys.exit(1)
    except Exception as e:
        print(paint(f"❌ Error during enumeration: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
