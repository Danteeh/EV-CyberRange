"""
Vulnerable Charge Points Launcher
Starts multiple vulnerable charge points for the EV-CyberRange lab.

Each CP simulates a different vendor with specific CVE vulnerabilities.
"""
import asyncio
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vulnerable_charge_points import run_vulnerable_cp, VULNERABLE_CP_TYPES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger('VulnCPLauncher')


# Configuration for vulnerable charge points
# Each entry: (cp_type, cp_id, http_port)
VULNERABLE_CPS = [
    # Hardy Barth - CVE-2024-11665, CVE-2024-11666 (RCE + MQTT)
    ("hardy_barth", "CP-HARDY-001", 8081),
    
    # Schneider EVlink - CVE-2018-7800, CVE-2018-7801 (Code injection)
    ("schneider", "CP-SCHNEIDER-001", 8082),
    
    # Wallbox Pulsar - CVE-2023-32249 (Unauth API)
    ("wallbox", "CP-WALLBOX-001", 8083),
    
    # ChargePoint Home Flex - CVE-2022-26132 (Buffer overflow DoS)
    ("chargepoint", "CP-CHARGEPOINT-001", 8084),
    
    # Generic Web Interface - CVE-2024-43659 (Exposed credentials)
    ("generic_web", "CP-GENERIC-001", 8085),
    
    # ISO 15118 Gateway - CVE-2025-12357 (MitM)
    ("iso15118", "CP-ISO15118-001", 8086),
]


async def main():
    csms_url = os.getenv('CSMS_URL', 'ws://csms:9000')
    
    log.info("=" * 60)
    log.info("EV-CyberRange Vulnerable Charge Points Launcher")
    log.info("=" * 60)
    log.info(f"CSMS URL: {csms_url}")
    log.info("")
    log.info("Starting the following vulnerable charge points:")
    log.info("-" * 60)
    
    for cp_type, cp_id, http_port in VULNERABLE_CPS:
        cp_class = VULNERABLE_CP_TYPES[cp_type]
        log.info(f"  {cp_id}:")
        log.info(f"    Type: {cp_class.VENDOR_NAME} {cp_class.MODEL_NAME}")
        log.info(f"    CVEs: {', '.join(cp_class.CVE_LIST)}")
        log.info(f"    HTTP: http://localhost:{http_port}")
    
    log.info("-" * 60)
    log.info("")
    
    # Wait for CSMS to be ready
    log.info("Waiting for CSMS to be ready...")
    await asyncio.sleep(5)
    
    # Start all charge points concurrently
    tasks = []
    for cp_type, cp_id, http_port in VULNERABLE_CPS:
        task = asyncio.create_task(
            run_vulnerable_cp(csms_url, cp_type, cp_id, http_port)
        )
        tasks.append(task)
        # Stagger startup to avoid overwhelming the CSMS
        await asyncio.sleep(1)
    
    log.info(f"All {len(tasks)} vulnerable charge points started!")
    log.info("")
    log.info("Attack targets available at:")
    for cp_type, cp_id, http_port in VULNERABLE_CPS:
        log.info(f"  http://localhost:{http_port} - {cp_id}")
    
    # Wait for all tasks (they run forever)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down...")
