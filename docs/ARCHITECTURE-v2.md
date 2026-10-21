# EV-CyberRange Architecture v2

> Updated: 2026-10-21 - Multi-connector support, new React frontend, OCPP logging

## Overview

EV-CyberRange is a cybersecurity training laboratory for EV charging infrastructure. It provides a complete OCPP 1.6 environment with simulated charge points, a central management system, and attack tools for security research and training.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React + Vite)                           │
│                              localhost:5173                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Topology Canvas │  │ Embedded Panels │  │   Control Panel │             │
│  │  (React Flow)   │  │ Kali│NodeRED│Log│  │  Attacks│Status │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Backend API (FastAPI)                               │
│                            localhost:8000                                   │
│  Endpoints: /api/ocpp/charge-points, /api/ocpp/remote-start,               │
│             /api/ocpp/remote-stop, /api/ocpp/logs                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────────────┐
│     CSMS (WebSocket:9000)     │   │          EVerest Stack                │
│        REST API:9001          │   │  ┌─────────────────────────────────┐  │
│  ┌─────────────────────────┐  │   │  │    MQTT Broker (1883)           │  │
│  │  OCPP 1.6 Server        │  │   │  └─────────────────────────────────┘  │
│  │  - BootNotification     │  │   │  ┌─────────────────────────────────┐  │
│  │  - Authorize            │  │   │  │    EVerest Manager              │  │
│  │  - StartTransaction     │  │   │  │    (ISO 15118 Simulation)       │  │
│  │  - StopTransaction      │  │   │  └─────────────────────────────────┘  │
│  │  - StatusNotification   │  │   │  ┌─────────────────────────────────┐  │
│  │  - MeterValues          │  │   │  │    Node-RED UI (1880)           │  │
│  │  - RemoteStart/Stop     │  │   │  │    (EVerest Dashboard)          │  │
│  └─────────────────────────┘  │   │  └─────────────────────────────────┘  │
│  ┌─────────────────────────┐  │   └───────────────────────────────────────┘
│  │  OCPP Traffic Logger    │  │
│  │  → /shared-logs/        │  │
│  └─────────────────────────┘  │
└───────────────────────────────┘
                │
    ┌───────────┼───────────┬───────────┬───────────┬───────────┐
    ▼           ▼           ▼           ▼           ▼           ▼
┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐
│ CP-1  │   │ CP-2  │   │ CP-3  │   │ CP-4  │   │ CP-5  │   │ CP-6  │
│ 1x11kW│   │ 1x11kW│   │ 2x11kW│   │ 2x11kW│   │ 1x50kW│   │1x150kW│
│  AC   │   │  AC   │   │  AC   │   │  AC   │   │DC Fast│   │DC Ultra│
└───────┘   └───────┘   └───────┘   └───────┘   └───────┘   └───────┘
                                                    │
                                    ┌───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │   Kali Linux Attack Host      │
                    │        noVNC:6080             │
                    │  ┌─────────────────────────┐  │
                    │  │ Tools:                  │  │
                    │  │ - evse_scanner.py       │  │
                    │  │ - session_hijacker.py   │  │
                    │  │ - ocpp_mitm.sh          │  │
                    │  │ - Wireshark, tcpdump    │  │
                    │  │ - arpspoof (dsniff)     │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │ /shared-logs/ (mounted) │  │
                    │  │ - ocpp_traffic.log      │  │
                    │  └─────────────────────────┘  │
                    └───────────────────────────────┘
```

## Components

### Frontend (React + Vite)
- **Technology**: React 18, Vite, React Flow, Zustand
- **Port**: 5173 (dev server)
- **Features**:
  - Drag-and-drop topology editor with 2.5D isometric nodes
  - Embedded Kali Linux terminal (noVNC iframe)
  - Embedded Node-RED dashboard (iframe)
  - Real-time OCPP traffic logs viewer
  - Charge point control panel
  - Attack simulation controls

### Backend API (FastAPI)
- **Port**: 8000
- **Endpoints**:
  - `GET /api/ocpp/charge-points` - List connected charge points
  - `POST /api/ocpp/remote-start` - Start charging session
  - `POST /api/ocpp/remote-stop` - Stop charging session
  - `GET /api/ocpp/logs?lines=N` - Get OCPP traffic logs

### CSMS (Central System Management System)
- **Ports**: 9000 (WebSocket), 9001 (REST API)
- **Protocol**: OCPP 1.6-J (JSON over WebSocket)
- **Features**:
  - Full OCPP 1.6 message handling
  - Transaction management
  - Authorization (accepts all tags for training)
  - Raw message logging to shared volume

### Charge Point Simulators
Configuration via environment variables:
- `CSMS_URL`: WebSocket URL of CSMS
- `CHARGE_POINT_ID`: Unique identifier
- `NUM_CONNECTORS`: Number of connectors (1-4)
- `MAX_POWER_KW`: Maximum power per connector

| ID | Connectors | Power | Type | Profile |
|----|------------|-------|------|---------|
| EVCR-001 | 1 | 11 kW | AC | default |
| EVCR-002 | 1 | 11 kW | AC | default |
| EVCR-003 | 2 | 11 kW | AC | full |
| EVCR-004 | 2 | 11 kW | AC | full |
| EVCR-005 | 1 | 50 kW | DC Fast | full |
| EVCR-006 | 1 | 150 kW | DC Ultra | full |

### EVerest Stack
- **MQTT Broker** (1883): Message bus for EVerest components
- **EVerest Manager**: ISO 15118 and charging simulation
- **Node-RED** (1880): Visual dashboard for EVerest control

### Kali Linux Attack Host
- **Access**: noVNC at port 6080
- **Network capabilities**: NET_ADMIN, NET_RAW for MitM attacks
- **Pre-installed tools**:
  - Custom: `evse_scanner.py`, `session_hijacker.py`, `ocpp_mitm.sh`
  - System: Wireshark, tcpdump, tshark, nmap, arpspoof (dsniff)
- **Shared volume**: `/shared-logs/` for OCPP traffic analysis

## Network Architecture

All containers run on a custom Docker network `ev-cyberrange` (172.20.0.0/16):
- Containers can communicate by service name
- Kali has elevated network privileges for packet capture and ARP spoofing
- Shared volume `/shared-logs/` accessible by CSMS, Backend, and Kali

## Quick Start

```powershell
# Standard lab (2 charge points)
.\start.ps1

# Full lab (6 charge points including DC fast chargers)
.\start.ps1 -Full

# Without Kali (faster startup)
.\start.ps1 -NoKali

# Stop everything
.\stop.ps1
```

## URLs

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:5173 |
| Backend API Docs | http://localhost:8000/docs |
| CSMS REST API | http://localhost:9001 |
| Node-RED (EVerest) | http://localhost:1880 |
| Kali Linux (noVNC) | http://localhost:6080/vnc.html |

## File Structure

```
EV-CyberRange/
├── csms/
│   ├── csms_server.py          # OCPP 1.6 Central System
│   ├── charge_point_sim.py     # Multi-connector CP simulator
│   └── Dockerfile.chargepoint
├── frontend/
│   └── src/
│       ├── App.jsx             # Main layout with embedded panels
│       ├── index.css           # Industrial color palette
│       └── components/
│           ├── TopologyCanvas.jsx   # React Flow canvas
│           ├── Sidebar.jsx          # Controls and drag components
│           ├── EmbeddedPanel.jsx    # Kali/NodeRED/Logs iframes
│           └── StatusBar.jsx        # Real-time events
├── kali/
│   ├── Dockerfile
│   └── tools/
│       ├── evse_scanner.py
│       ├── session_hijacker.py
│       └── ocpp_mitm.sh
├── simulator/backend/
│   └── app/routers/ocpp.py     # Backend OCPP endpoints
├── shared-logs/                # OCPP traffic logs (Docker volume)
├── docker-compose.yml
├── start.ps1
└── stop.ps1
```
