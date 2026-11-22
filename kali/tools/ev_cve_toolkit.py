#!/usr/bin/env python3
"""
EV-CyberRange CVE Attack Toolkit
Master script for all EV charging infrastructure exploits

Usage:
    python3 ev_cve_toolkit.py --scan              # Scan all targets
    python3 ev_cve_toolkit.py --list              # List available exploits
    python3 ev_cve_toolkit.py --attack <cve_id>   # Run specific exploit

DISCLAIMER: For authorized security testing and education only.
"""

import argparse
import subprocess
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


# Target definitions - Use container name for Docker network connectivity
VULNERABLE_CPS_HOST = "evcr-vulnerable-cps"

TARGETS = {
    "hardy_barth": {
        "name": "Hardy Barth eCharge Salia",
        "host": VULNERABLE_CPS_HOST,
        "port": 8081,
        "cves": ["CVE-2024-11665", "CVE-2024-11666"],
        "script": "cve_2024_11665_hardy_barth_rce.py",
        "description": "RCE via PHP + MQTT without SSL verification"
    },
    "schneider": {
        "name": "Schneider Electric EVlink",
        "host": VULNERABLE_CPS_HOST,
        "port": 8082,
        "cves": ["CVE-2018-7800", "CVE-2018-7801"],
        "script": "cve_2018_7800_schneider_evlink.py",
        "description": "Code injection + Arbitrary command execution"
    },
    "wallbox": {
        "name": "Wallbox Pulsar Plus",
        "host": VULNERABLE_CPS_HOST,
        "port": 8083,
        "cves": ["CVE-2023-32249"],
        "script": "cve_2023_32249_wallbox_unauth.py",
        "description": "Unauthenticated API, no encryption"
    },
    "chargepoint": {
        "name": "ChargePoint Home Flex",
        "host": VULNERABLE_CPS_HOST,
        "port": 8084,
        "cves": ["CVE-2022-26132"],
        "script": "cve_2022_26132_chargepoint_dos.py",
        "description": "Stack buffer overflow (DoS)"
    },
    "generic_web": {
        "name": "Generic WebConnect Pro",
        "host": VULNERABLE_CPS_HOST,
        "port": 8085,
        "cves": ["CVE-2024-43659"],
        "script": "cve_2024_43659_credential_exposure.py",
        "description": "Exposed superuser credentials"
    },
    "iso15118": {
        "name": "ISO 15118 PnC Gateway",
        "host": VULNERABLE_CPS_HOST,
        "port": 8086,
        "cves": ["CVE-2025-12357"],
        "script": "cve_2025_12357_iso15118_mitm.py",
        "description": "MitM attack on charging communication"
    }
}


def print_banner():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║           EV-CyberRange CVE Attack Toolkit                    ║
    ║                                                               ║
    ║   Practice exploiting real-world EV charging vulnerabilities  ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)


def list_exploits():
    """List all available exploits"""
    print("\n" + "="*70)
    print("AVAILABLE EXPLOITS")
    print("="*70)
    
    for target_id, target in TARGETS.items():
        print(f"\n{target['name']} (Port {target['port']})")
        print("-" * 50)
        print(f"  CVEs: {', '.join(target['cves'])}")
        print(f"  Impact: {target['description']}")
        print(f"  Script: {target['script'] or 'Not implemented'}")
        print(f"  URL: http://localhost:{target['port']}")


def scan_target(target_id: str, target: dict) -> dict:
    """Scan a single target"""
    result = {
        "id": target_id,
        "name": target["name"],
        "port": target["port"],
        "cves": target["cves"],
        "online": False,
        "vulnerable": False
    }
    
    try:
        url = f"http://{target['host']}:{target['port']}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            result["online"] = True
            result["vulnerable"] = True  # If accessible, assume vulnerable
    except:
        pass
    
    return result


def scan_all_targets():
    """Scan all targets for availability"""
    print("\n" + "="*70)
    print("SCANNING TARGETS")
    print("="*70)
    
    results = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(scan_target, tid, t): tid 
            for tid, t in TARGETS.items()
        }
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    # Print results
    print(f"\n{'Target':<30} {'Port':<8} {'Status':<12} {'CVEs'}")
    print("-" * 70)
    
    online_count = 0
    for r in sorted(results, key=lambda x: x['port']):
        status = "ONLINE" if r["online"] else "OFFLINE"
        status_color = "\033[92m" if r["online"] else "\033[91m"
        print(f"{r['name']:<30} {r['port']:<8} {status_color}{status:<12}\033[0m {', '.join(r['cves'])}")
        if r["online"]:
            online_count += 1
    
    print("-" * 70)
    print(f"Total: {online_count}/{len(results)} targets online")
    
    return results


def run_exploit(cve_id: str):
    """Run exploit for a specific CVE"""
    # Find target by CVE
    target = None
    for tid, t in TARGETS.items():
        if cve_id.upper() in [c.upper() for c in t["cves"]]:
            target = t
            target["id"] = tid
            break
    
    if not target:
        print(f"[-] No exploit found for {cve_id}")
        print(f"    Available CVEs: {', '.join(sum([t['cves'] for t in TARGETS.values()], []))}")
        return
    
    print(f"\n[*] Exploit for {cve_id}")
    print(f"    Target: {target['name']}")
    print(f"    Port: {target['port']}")
    
    if not target["script"]:
        print(f"[-] Exploit script not implemented yet")
        return
    
    script_path = f"/root/tools/{target['script']}"
    
    print(f"\n[*] Running: python3 {script_path} {target['host']} {target['port']}")
    print("="*70)
    
    try:
        subprocess.run([
            "python3", script_path, 
            target["host"], str(target["port"])
        ])
    except FileNotFoundError:
        # Try current directory
        print(f"[*] Trying local path...")
        subprocess.run([
            "python3", target["script"],
            target["host"], str(target["port"])
        ])


def interactive_menu():
    """Interactive attack menu"""
    while True:
        print("\n" + "="*50)
        print("EV-CyberRange Attack Menu")
        print("="*50)
        print("1. Scan all targets")
        print("2. List available exploits")
        print("3. Attack by CVE")
        print("4. Attack by target")
        print("5. Run all exploits (automated)")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            scan_all_targets()
        elif choice == "2":
            list_exploits()
        elif choice == "3":
            cve = input("Enter CVE ID (e.g., CVE-2024-11665): ").strip()
            run_exploit(cve)
        elif choice == "4":
            print("\nTargets:")
            for i, (tid, t) in enumerate(TARGETS.items(), 1):
                print(f"  {i}. {t['name']} (:{t['port']})")
            idx = int(input("Select target: ")) - 1
            target_list = list(TARGETS.items())
            if 0 <= idx < len(target_list):
                tid, t = target_list[idx]
                run_exploit(t["cves"][0])
        elif choice == "5":
            print("\n[!] Running all available exploits...")
            for tid, t in TARGETS.items():
                if t["script"]:
                    print(f"\n{'='*50}")
                    print(f"Attacking {t['name']}...")
                    run_exploit(t["cves"][0])
        elif choice == "0":
            break


def main():
    parser = argparse.ArgumentParser(
        description="EV-CyberRange CVE Attack Toolkit"
    )
    parser.add_argument("--scan", action="store_true", help="Scan all targets")
    parser.add_argument("--list", action="store_true", help="List available exploits")
    parser.add_argument("--attack", metavar="CVE", help="Run exploit for specific CVE")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.scan:
        scan_all_targets()
    elif args.list:
        list_exploits()
    elif args.attack:
        run_exploit(args.attack)
    elif args.interactive:
        interactive_menu()
    else:
        # Default: scan and show menu
        scan_all_targets()
        interactive_menu()


if __name__ == "__main__":
    main()
