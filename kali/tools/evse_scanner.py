#!/usr/bin/env python3
"""
EV-CyberRange EVSE Scanner
Reconnaissance tool for discovering and profiling EV charging infrastructure.

Usage:
    python3 evse_scanner.py --target 172.28.0.0/24
    python3 evse_scanner.py --mqtt-host everest-mqtt --deep
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt", "rich"])
    import paho.mqtt.client as mqtt
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress

console = Console()


@dataclass
class EVSEProfile:
    """Profile of a discovered EVSE/charging station."""
    ip: str
    hostname: Optional[str] = None
    mqtt_port: Optional[int] = None
    http_ports: list = field(default_factory=list)
    ocpp_ws_port: Optional[int] = None
    connectors: int = 0
    connector_states: dict = field(default_factory=dict)
    mqtt_topics: list = field(default_factory=list)
    capabilities: dict = field(default_factory=dict)
    firmware_version: Optional[str] = None
    vulnerabilities: list = field(default_factory=list)


class EVSEScanner:
    COMMON_PORTS = {
        1883: "MQTT",
        8883: "MQTT/TLS",
        1880: "Node-RED",
        8080: "HTTP/WebSocket",
        8180: "SteVe OCPP",
        443: "HTTPS",
        80: "HTTP",
        9000: "OCPP WebSocket",
        9001: "MQTT WebSocket",
    }
    
    def __init__(self):
        self.profiles: list[EVSEProfile] = []
        self.mqtt_client = None
        
    def scan_port(self, ip: str, port: int, timeout: float = 1.0) -> bool:
        """Check if a port is open."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex((ip, port)) == 0
        except:
            return False
    
    def scan_host(self, ip: str) -> Optional[EVSEProfile]:
        """Scan a single host for EVSE-related services."""
        profile = EVSEProfile(ip=ip)
        found_anything = False
        
        # Try to get hostname
        try:
            profile.hostname = socket.gethostbyaddr(ip)[0]
        except:
            pass
        
        # Scan common ports
        for port, service in self.COMMON_PORTS.items():
            if self.scan_port(ip, port):
                found_anything = True
                if port in (1883, 8883):
                    profile.mqtt_port = port
                elif port in (80, 443, 1880, 8080, 8180):
                    profile.http_ports.append((port, service))
                elif port in (9000,):
                    profile.ocpp_ws_port = port
        
        return profile if found_anything else None
    
    def scan_network(self, cidr: str) -> list[EVSEProfile]:
        """Scan a network range for EVSE hosts."""
        import ipaddress
        
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            console.print(f"[red]Invalid CIDR: {e}[/red]")
            return []
        
        hosts = list(network.hosts())
        console.print(f"[yellow]Scanning {len(hosts)} hosts in {cidr}...[/yellow]")
        
        profiles = []
        with Progress() as progress:
            task = progress.add_task("Scanning...", total=len(hosts))
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(self.scan_host, str(ip)): ip for ip in hosts}
                
                for future in as_completed(futures):
                    progress.advance(task)
                    result = future.result()
                    if result:
                        profiles.append(result)
        
        self.profiles = profiles
        return profiles
    
    def probe_mqtt(self, host: str, port: int = 1883, duration: int = 10) -> dict:
        """Deep probe MQTT broker for EVSE topics."""
        info = {
            "topics": set(),
            "connectors": {},
            "messages_seen": 0,
        }
        
        def on_message(client, userdata, msg):
            info["topics"].add(msg.topic)
            info["messages_seen"] += 1
            
            # Parse connector info
            if "connector_" in msg.topic and "/var/" in msg.topic:
                parts = msg.topic.split("/")
                for p in parts:
                    if p.startswith("connector_"):
                        conn_id = p.replace("connector_", "")
                        if conn_id not in info["connectors"]:
                            info["connectors"][conn_id] = {}
                        
                        try:
                            payload = json.loads(msg.payload.decode())
                            topic_type = parts[-1]  # session_info, powermeter, etc.
                            info["connectors"][conn_id][topic_type] = payload
                        except:
                            pass
        
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"scanner-{os.getpid()}")
            client.on_message = on_message
            client.connect(host, port, 60)
            client.subscribe("#")
            client.loop_start()
            
            console.print(f"[yellow]Probing MQTT {host}:{port} for {duration}s...[/yellow]")
            time.sleep(duration)
            
            client.loop_stop()
            client.disconnect()
            
            info["topics"] = list(info["topics"])
            return info
            
        except Exception as e:
            console.print(f"[red]MQTT probe failed: {e}[/red]")
            return info
    
    def analyze_vulnerabilities(self, profile: EVSEProfile) -> list[str]:
        """Analyze profile for potential vulnerabilities."""
        vulns = []
        
        # MQTT without TLS
        if profile.mqtt_port == 1883:
            vulns.append("MQTT-NOTLS: MQTT broker accepts unencrypted connections")
        
        # Anonymous MQTT
        if profile.mqtt_port:
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "anon-test")
                client.connect(profile.ip, profile.mqtt_port, 5)
                client.disconnect()
                vulns.append("MQTT-ANON: MQTT broker allows anonymous connections")
            except:
                pass
        
        # Exposed management interfaces
        for port, service in profile.http_ports:
            if service == "Node-RED":
                vulns.append(f"MGMT-EXPOSED: Node-RED UI exposed on port {port}")
            if service == "SteVe OCPP":
                vulns.append(f"MGMT-EXPOSED: SteVe management interface on port {port}")
        
        # Wildcard subscription allowed
        if profile.mqtt_topics:
            if any("#" in t or "+" in t for t in profile.mqtt_topics):
                vulns.append("MQTT-WILDCARD: Wildcard subscriptions allowed")
        
        profile.vulnerabilities = vulns
        return vulns
    
    def print_report(self, profiles: list[EVSEProfile], detailed: bool = False):
        """Print scan report."""
        if not profiles:
            console.print("[yellow]No EVSE hosts discovered[/yellow]")
            return
        
        # Summary table
        table = Table(title="EVSE Hosts Discovered")
        table.add_column("IP", style="cyan")
        table.add_column("Hostname", style="green")
        table.add_column("MQTT", style="yellow")
        table.add_column("HTTP Ports", style="blue")
        table.add_column("Connectors", style="magenta")
        table.add_column("Vulns", style="red")
        
        for p in profiles:
            mqtt_str = str(p.mqtt_port) if p.mqtt_port else "-"
            http_str = ", ".join([str(port) for port, _ in p.http_ports]) or "-"
            conn_str = str(p.connectors) if p.connectors else "-"
            vuln_str = str(len(p.vulnerabilities)) if p.vulnerabilities else "0"
            
            table.add_row(
                p.ip, 
                p.hostname or "-",
                mqtt_str,
                http_str,
                conn_str,
                vuln_str
            )
        
        console.print(table)
        
        if detailed:
            for p in profiles:
                if p.mqtt_topics or p.vulnerabilities or p.connector_states:
                    console.print(Panel(
                        f"[bold]IP:[/bold] {p.ip}\n"
                        f"[bold]MQTT Topics:[/bold] {len(p.mqtt_topics)}\n"
                        f"[bold]Connectors:[/bold] {json.dumps(p.connector_states, indent=2)[:500]}\n"
                        f"[bold]Vulnerabilities:[/bold]\n" + 
                        "\n".join(f"  • {v}" for v in p.vulnerabilities),
                        title=f"Detailed: {p.hostname or p.ip}"
                    ))
    
    def export_json(self, profiles: list[EVSEProfile], filename: str):
        """Export results to JSON."""
        data = []
        for p in profiles:
            data.append({
                "ip": p.ip,
                "hostname": p.hostname,
                "mqtt_port": p.mqtt_port,
                "http_ports": p.http_ports,
                "ocpp_ws_port": p.ocpp_ws_port,
                "connectors": p.connectors,
                "connector_states": p.connector_states,
                "mqtt_topics": p.mqtt_topics,
                "vulnerabilities": p.vulnerabilities,
            })
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]Results exported to {filename}[/green]")


def main():
    parser = argparse.ArgumentParser(description="EV-CyberRange EVSE Scanner")
    parser.add_argument("--target", "-t", help="Target IP, hostname, or CIDR range")
    parser.add_argument("--mqtt-host", help="MQTT broker to probe directly")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT port")
    parser.add_argument("--deep", action="store_true", help="Deep scan with MQTT probing")
    parser.add_argument("--duration", type=int, default=10, help="MQTT probe duration")
    parser.add_argument("--output", "-o", help="Export results to JSON file")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold blue]EV-CyberRange EVSE Scanner[/bold blue]\n"
        "Reconnaissance tool for EV charging infrastructure",
        border_style="blue"
    ))
    
    scanner = EVSEScanner()
    profiles = []
    
    if args.mqtt_host:
        # Direct MQTT probe
        console.print(f"[cyan]Direct MQTT probe: {args.mqtt_host}:{args.mqtt_port}[/cyan]")
        
        profile = EVSEProfile(ip=args.mqtt_host, mqtt_port=args.mqtt_port)
        mqtt_info = scanner.probe_mqtt(args.mqtt_host, args.mqtt_port, args.duration)
        
        profile.mqtt_topics = mqtt_info["topics"]
        profile.connector_states = mqtt_info["connectors"]
        profile.connectors = len(mqtt_info["connectors"])
        
        scanner.analyze_vulnerabilities(profile)
        profiles = [profile]
        
    elif args.target:
        # Network scan
        if "/" in args.target:
            profiles = scanner.scan_network(args.target)
        else:
            profile = scanner.scan_host(args.target)
            if profile:
                profiles = [profile]
        
        if args.deep:
            # Deep probe each discovered MQTT host
            for p in profiles:
                if p.mqtt_port:
                    mqtt_info = scanner.probe_mqtt(p.ip, p.mqtt_port, args.duration)
                    p.mqtt_topics = mqtt_info["topics"]
                    p.connector_states = mqtt_info["connectors"]
                    p.connectors = len(mqtt_info["connectors"])
                scanner.analyze_vulnerabilities(p)
    else:
        # Default: scan common lab networks
        console.print("[yellow]No target specified. Scanning common lab ranges...[/yellow]")
        for cidr in ["172.28.0.0/24", "192.168.1.0/24", "10.0.0.0/24"]:
            profiles.extend(scanner.scan_network(cidr))
    
    scanner.print_report(profiles, detailed=args.deep)
    
    if args.output:
        scanner.export_json(profiles, args.output)


if __name__ == "__main__":
    main()
