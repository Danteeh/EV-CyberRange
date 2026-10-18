# EV-CyberRange Laboratory Architecture

## Overview

EV-CyberRange is a **cybersecurity research laboratory** for Electric Vehicle charging infrastructure. It provides a realistic environment to study, demonstrate, and defend against attacks on EV charging stations.

## Design Principles

1. **Realism** — Use production-grade EVerest software, real protocols (MQTT, OCPP), actual attack tools
2. **Isolation** — Segmented networks prevent lab attacks from escaping
3. **Observability** — Full packet capture, event logging, forensic trail
4. **Reproducibility** — Containerized, version-controlled, documented scenarios

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EV-CyberRange Laboratory                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Frontend (React Dashboard)                        │   │
│  │                    http://localhost:3000                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ REST API + WebSocket                   │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Backend (FastAPI)                                 │   │
│  │                    http://localhost:8000                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ MQTT Bridge │  │ State Store │  │Attack Engine│  │ Event Log  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ══════════════════════════════════╪════════════════════════════════════   │
│                           MQTT Bus │ (Mosquitto :1883)                      │
│  ══════════════════════════════════╪════════════════════════════════════   │
│                                    │                                        │
│      ┌─────────────────────────────┼─────────────────────────────┐         │
│      │                             │                             │         │
│      ▼                             ▼                             ▼         │
│  ┌────────────┐            ┌────────────┐              ┌────────────────┐  │
│  │  EVerest   │            │  Node-RED  │              │  Kali Linux    │  │
│  │  Manager   │            │    UI      │              │  Attack Host   │  │
│  │            │            │   :1880    │              │   :6080 (VNC)  │  │
│  │ - EVSE Sim │            │ - Control  │              │ - nmap         │  │
│  │ - EV Sim   │            │ - Simulate │              │ - wireshark    │  │
│  │ - ISO15118 │            │ - Monitor  │              │ - mosquitto    │  │
│  └────────────┘            └────────────┘              │ - mitmproxy    │  │
│                                                        │ - custom tools │  │
│                                                        └────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Network: ev-cyberrange                │
│                    Subnet: 172.28.0.0/16                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   172.28.1.0/24 - Management Network                           │
│   ├── 172.28.1.10  backend (FastAPI)                           │
│   ├── 172.28.1.11  frontend (React)                            │
│   └── 172.28.1.12  mqtt-broker (Mosquitto)                     │
│                                                                 │
│   172.28.2.0/24 - Charging Infrastructure                      │
│   ├── 172.28.2.10  everest-manager (EVSE)                      │
│   ├── 172.28.2.11  nodered-ui (HMI)                            │
│   └── 172.28.2.12  ev-simulator (Vehicle)                      │
│                                                                 │
│   172.28.3.0/24 - Attack Network                               │
│   └── 172.28.3.10  kali-attack (Attacker)                      │
│                                                                 │
│   All networks interconnected via mqtt-broker                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. EVerest Stack (Charging Infrastructure)

| Component | Image | Purpose |
|-----------|-------|---------|
| everest-manager | ghcr.io/everest/everest-demo/manager | EVSE + EV simulation, ISO 15118 |
| everest-mqtt | eclipse-mosquitto | Message broker for all EVerest comms |
| everest-ui | ghcr.io/everest/everest-demo/nodered | Web UI for simulation control |

### 2. Backend (Monitoring & Control)

| Component | Technology | Purpose |
|-----------|------------|---------|
| FastAPI | Python 3.12 | REST API, WebSocket push |
| MQTT Bridge | paho-mqtt | Subscribe to EVerest topics |
| State Store | In-memory + SQLite | Real-time state, event persistence |
| Attack Engine | Python | Execute and coordinate attacks |

### 3. Frontend (Dashboard)

| Component | Technology | Purpose |
|-----------|------------|---------|
| React | Vite + TypeScript | Real-time monitoring dashboard |
| WebSocket | Native | Live state updates |
| Attack Console | React | Launch and monitor attacks |

### 4. Attack Host (Kali Linux)

| Tool | Purpose |
|------|---------|
| nmap | Network reconnaissance |
| wireshark/tshark | Packet capture and analysis |
| mosquitto-clients | MQTT injection and fuzzing |
| mitmproxy | Man-in-the-middle attacks |
| ettercap | ARP spoofing |
| scapy | Custom packet crafting |
| Custom scripts | Specific EV charging attacks |

## Attack Scenarios

### Category 1: MQTT Protocol Attacks

| ID | Name | Technique | Impact |
|----|------|-----------|--------|
| MQTT-01 | Topic Enumeration | Wildcard subscription | Information disclosure |
| MQTT-02 | Message Injection | Publish malicious payloads | Unauthorized control |
| MQTT-03 | DoS via Flood | High-rate publishing | Service disruption |
| MQTT-04 | Session Hijack | ClientID collision | Impersonation |

### Category 2: Charging Session Attacks

| ID | Name | Technique | Impact |
|----|------|-----------|--------|
| CHRG-01 | Unauthorized Start | Forge authorization | Free charging |
| CHRG-02 | Session Termination | Inject stop command | Denial of service |
| CHRG-03 | Power Manipulation | Modify limit commands | Equipment damage |
| CHRG-04 | Billing Fraud | Tamper energy readings | Financial loss |

### Category 3: Network Attacks

| ID | Name | Technique | Impact |
|----|------|-----------|--------|
| NET-01 | ARP Spoofing | Redirect traffic | MITM position |
| NET-02 | DNS Poisoning | Redirect backend calls | Credential theft |
| NET-03 | Service Discovery | Port scanning | Attack surface mapping |

## Data Flow

### Normal Charging Session

```
1. User → Node-RED UI → "Plug In" button
2. Node-RED → MQTT → everest_external/nodered/1/cmd/plug_in
3. EVerest Manager processes → State change
4. EVerest → MQTT → everest_api/connector_1/var/session_info
5. Backend MQTT Bridge receives → Updates State Store
6. Backend → WebSocket → Frontend Dashboard (real-time)
```

### Attack Execution

```
1. User → Frontend Dashboard → Start Attack "MQTT-02"
2. Frontend → REST API → POST /api/attacks/mqtt-02/start
3. Backend Attack Engine → Spawns attack subprocess
4. Attack runs on Kali container (or locally)
5. Attack publishes to MQTT (or performs network attack)
6. Backend monitors → Logs events
7. Results → WebSocket → Frontend (real-time feedback)
```

## Ports

| Port | Service | Access |
|------|---------|--------|
| 3000 | React Frontend | http://localhost:3000 |
| 8000 | FastAPI Backend | http://localhost:8000 |
| 1883 | MQTT Broker | tcp://localhost:1883 |
| 1880 | Node-RED UI | http://localhost:1880 |
| 6080 | Kali noVNC | http://localhost:6080 |

## File Structure

```
EV-CyberRange/
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   ├── EVEREST-SETUP.md         # EVerest specific docs
│   ├── ATTACK-PLAYBOOK.md       # Attack procedures
│   └── LAB-GUIDES/              # Step-by-step lab exercises
│       ├── 01-reconnaissance.md
│       ├── 02-mqtt-attacks.md
│       └── 03-session-hijacking.md
├── simulator/
│   ├── backend/                 # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── mqtt_bridge.py
│   │   │   ├── state_store.py
│   │   │   ├── attack_engine.py
│   │   │   └── routers/
│   │   └── requirements.txt
│   └── frontend/                # React dashboard
│       ├── src/
│       └── package.json
├── everest/
│   └── docker-compose.yml       # EVerest stack
├── kali/
│   ├── Dockerfile               # Custom Kali image
│   ├── docker-compose.yml       # Kali stack
│   └── tools/                   # Custom attack scripts
│       ├── mqtt_fuzzer.py
│       ├── session_hijacker.py
│       └── evse_scanner.py
├── infrastructure/
│   └── docker-compose.full.yml  # Complete lab stack
├── scripts/
│   ├── start-lab.ps1            # Start entire lab
│   ├── stop-lab.ps1             # Stop entire lab
│   └── reset-lab.ps1            # Reset to clean state
└── data/
    ├── captures/                # Packet captures
    ├── logs/                    # Attack logs
    └── evidence/                # Forensic artifacts
```

## Security Considerations

⚠️ **This laboratory is designed for educational and research purposes only.**

- Run only in isolated environments
- Never expose to public networks
- All attack tools are for authorized testing only
- Follow responsible disclosure for any vulnerabilities found

## Getting Started

See individual setup guides:
1. [EVerest Setup](./EVEREST-SETUP.md)
2. [Kali Attack Host Setup](./KALI-SETUP.md)
3. [Lab Exercises](./LAB-GUIDES/)
