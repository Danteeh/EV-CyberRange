#!/usr/bin/env python3
"""
Attack Reporter - Sends attack events to the EV-CyberRange frontend
for real-time visualization of exploit activity.

Usage:
    from attack_reporter import report_attack, report_step

    report_attack("CVE-2024-11665", "Hardy Barth RCE", "critical", "192.168.1.100:8081")
    report_step("Sending malicious payload...", details={"payload": "..."})
    report_success("Got shell access")
    report_failure("Target not vulnerable")
"""
import json
import os
import sys
import socket
from datetime import datetime, timezone
from typing import Optional

# Backend API endpoint (inside Docker network)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://evcr-backend:8000")
# Shared log file (mounted volume)
ATTACK_LOG_PATH = os.environ.get("ATTACK_LOG_PATH", "/shared-logs/attack_events.jsonl")

# Current attack context
_current_attack = {
    "cve": None,
    "name": None,
    "target": None,
    "severity": "info"
}


def _get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_event(event: dict) -> None:
    """Write event to shared log file and optionally POST to backend"""
    event["timestamp"] = _get_timestamp()
    event["hostname"] = socket.gethostname()
    
    # Write to shared log file (primary method - works without network)
    try:
        os.makedirs(os.path.dirname(ATTACK_LOG_PATH), exist_ok=True)
        with open(ATTACK_LOG_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"[!] Failed to write to log file: {e}", file=sys.stderr)
    
    # Also try HTTP POST (backup method)
    try:
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(
            f"{BACKEND_URL}/api/attack-feed/log",
            data=json.dumps(event).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        # Silently fail - file logging is the primary method
        pass


def report_attack(
    cve: str,
    name: str,
    severity: str = "high",
    target: str = "",
    attack_type: str = "exploit"
) -> None:
    """
    Report the start of a new attack.
    
    Args:
        cve: CVE identifier (e.g., "CVE-2024-11665")
        name: Human-readable name (e.g., "Hardy Barth RCE")
        severity: One of "critical", "high", "medium", "low", "info"
        target: Target host:port
        attack_type: Type of attack (rce, dos, auth_bypass, credential_exposure, mitm)
    """
    global _current_attack
    _current_attack = {
        "cve": cve,
        "name": name,
        "target": target,
        "severity": severity
    }
    
    _write_event({
        "type": "attack_start",
        "cve": cve,
        "name": name,
        "severity": severity,
        "target": target,
        "attack_type": attack_type,
        "message": f"Starting {name} ({cve}) against {target}",
        "source": "kali"
    })


def report_step(
    message: str,
    severity: Optional[str] = None,
    details: Optional[dict] = None
) -> None:
    """
    Report a step in the attack process.
    
    Args:
        message: Description of what's happening
        severity: Override current severity
        details: Additional details (shown when expanded)
    """
    event = {
        "type": "attack_step",
        "cve": _current_attack.get("cve"),
        "target": _current_attack.get("target"),
        "severity": severity or _current_attack.get("severity", "info"),
        "message": message,
        "source": "kali"
    }
    if details:
        event["details"] = details
    
    _write_event(event)


def report_success(
    message: str,
    details: Optional[dict] = None
) -> None:
    """Report successful exploitation"""
    event = {
        "type": "attack_success",
        "cve": _current_attack.get("cve"),
        "target": _current_attack.get("target"),
        "severity": "critical",
        "attack_type": "success",
        "message": f"[SUCCESS] {message}",
        "source": "kali"
    }
    if details:
        event["details"] = details
    
    _write_event(event)


def report_failure(
    message: str,
    details: Optional[dict] = None
) -> None:
    """Report failed exploitation attempt"""
    event = {
        "type": "attack_failure",
        "cve": _current_attack.get("cve"),
        "target": _current_attack.get("target"),
        "severity": "info",
        "attack_type": "failure",
        "message": f"[FAILED] {message}",
        "source": "kali"
    }
    if details:
        event["details"] = details
    
    _write_event(event)


def report_data(
    data_type: str,
    data: dict,
    message: Optional[str] = None
) -> None:
    """
    Report extracted/captured data.
    
    Args:
        data_type: Type of data (credentials, config, system_info, etc.)
        data: The extracted data
        message: Optional description
    """
    _write_event({
        "type": "data_extracted",
        "cve": _current_attack.get("cve"),
        "target": _current_attack.get("target"),
        "severity": "critical",
        "data_type": data_type,
        "message": message or f"Extracted {data_type}",
        "details": data,
        "source": "kali"
    })


def report_command(
    command: str,
    output: Optional[str] = None,
    success: bool = True
) -> None:
    """
    Report a command execution (for RCE exploits).
    
    Args:
        command: The command that was executed
        output: Command output (truncated for display)
        success: Whether the command succeeded
    """
    event = {
        "type": "command_exec",
        "cve": _current_attack.get("cve"),
        "target": _current_attack.get("target"),
        "severity": "critical" if success else "high",
        "attack_type": "rce",
        "message": f"$ {command}",
        "source": "kali"
    }
    
    if output:
        # Truncate long output
        if len(output) > 500:
            output = output[:500] + "\n... (truncated)"
        event["details"] = {"command": command, "output": output}
    
    _write_event(event)


# Convenience aliases
start = report_attack
step = report_step
success = report_success
fail = report_failure
cmd = report_command
data = report_data


if __name__ == "__main__":
    # Test the reporter
    print("Testing attack reporter...")
    
    report_attack(
        cve="CVE-TEST-001",
        name="Test Exploit",
        severity="high",
        target="localhost:8080",
        attack_type="rce"
    )
    
    report_step("Scanning target for vulnerabilities...")
    report_step("Found vulnerable endpoint at /api/admin")
    report_command("id", output="uid=0(root) gid=0(root)")
    report_data("credentials", {"username": "admin", "password": "admin123"})
    report_success("Got root shell!")
    
    print(f"Events written to {ATTACK_LOG_PATH}")
