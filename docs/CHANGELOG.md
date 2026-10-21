# Changelog

## [0.2.0] - 2026-10-21

### Added

#### Multi-Connector Support
- Charge Point simulator now supports multiple connectors per station
- New environment variables: `NUM_CONNECTORS`, `MAX_POWER_KW`
- Each connector has independent state (status, transaction_id, meter_value, charging, power_w, id_tag)
- BootNotification reports correct model based on connector count (e.g., `EVCR-SIM-2C`)
- GetConfiguration returns actual `NumberOfConnectors` value

#### Additional Charge Points (Profile: full)
- **EVCR-003**: 2 connectors, 11 kW (AC)
- **EVCR-004**: 2 connectors, 11 kW (AC)
- **EVCR-005**: 1 connector, 50 kW (DC Fast)
- **EVCR-006**: 1 connector, 150 kW (DC Ultra-Fast)
- Start with `.\start.ps1 -Full` or `docker compose --profile full up -d`

#### New React Frontend
- Professional industrial/SCADA color palette (warm grays, teal #4da6a8, muted greens/ambers)
- React Flow-based topology canvas with drag-and-drop support
- 2.5D isometric SVG nodes for EV, EVSE, and CSMS
- Embedded panels for:
  - Kali Linux (noVNC iframe)
  - Node-RED/EVerest UI (iframe)
  - OCPP traffic logs (real-time)
- Sidebar with draggable components, attack controls, and charge point controls
- Status bar showing real-time events

#### OCPP Traffic Logging
- CSMS now logs all raw OCPP messages to `/shared-logs/ocpp_traffic.log`
- New backend endpoint: `GET /api/ocpp/logs?lines=N`
- Shared Docker volume between CSMS, Backend, and Kali for log access
- Frontend displays logs with syntax highlighting by message type

#### Kali Attack Host Enhancements
- Added `dsniff` package for ARP spoofing attacks
- Network capabilities (NET_ADMIN, NET_RAW) for MitM attacks
- New tool: `/root/tools/ocpp_mitm.sh` for OCPP traffic interception
- Access to shared OCPP logs at `/shared-logs/`

#### Lab Scripts
- Updated `start.ps1` with all services (CSMS, CPs, Backend, EVerest, Kali, Frontend)
- New `stop.ps1` with proper frontend process cleanup
- Parameters: `-Full` (6 CPs), `-NoKali` (faster start), `-Build` (rebuild containers)

### Changed
- `charge_point_sim.py`: Refactored to support N connectors with per-connector state
- `csms_server.py`: Added OCPP message logging to shared file
- `docker-compose.yml`: Added CPs 3-6, shared volumes, Kali network capabilities
- Frontend completely redesigned from scratch with React Flow

### Technical Details

#### Charge Point Simulator State Structure
```python
self.connectors = {
    connector_id: {
        "status": "Available",
        "transaction_id": None,
        "meter_value": 0,
        "charging": False,
        "power_w": 0,
        "id_tag": None
    }
    for connector_id in range(1, num_connectors + 1)
}
```

#### Docker Compose Profiles
- Default: mqtt, csms, backend, chargepoint-1, chargepoint-2, everest-*, kali
- Full: Adds chargepoint-3, chargepoint-4, chargepoint-5, chargepoint-6

## [0.1.0] - 2026-10-18

### Initial Release
- Basic OCPP 1.6 CSMS server
- 2 Charge Point simulators (single connector each)
- EVerest integration (MQTT + Node-RED)
- Kali Linux attack host with custom tools
- FastAPI backend for control API
- Basic React frontend
