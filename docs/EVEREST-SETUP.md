# EVerest Setup - Opcion A (Sin Central System OCPP)

## Arquitectura Target

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EV-CyberRange                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     HTTP/WS      ┌─────────────────┐              │
│  │   Frontend  │ ◄──────────────► │  Backend        │              │
│  │   React     │                  │  FastAPI        │              │
│  │   :5173     │                  │  :8000          │              │
│  └─────────────┘                  └────────┬────────┘              │
│                                            │                        │
│                                            │ MQTT                   │
│                                            │ :1883                  │
│                                            ▼                        │
│                                   ┌─────────────────┐              │
│                                   │   Mosquitto     │              │
│                                   │   MQTT Broker   │              │
│                                   └────────┬────────┘              │
│                                            │                        │
│                                            │ MQTT                   │
│                                            ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     EVerest (Docker)                         │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐               │   │
│  │  │EvseManager│  │  Auth     │  │ EnergyMgr │               │   │
│  │  └───────────┘  └───────────┘  └───────────┘               │   │
│  │  ┌───────────┐  ┌───────────┐                              │   │
│  │  │ Car Sim   │  │ API Module│◄─── UI :1880                 │   │
│  │  └───────────┘  └───────────┘                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Flujo de Comunicacion

1. **Frontend** envia comandos al **Backend** (start charge, stop, inject fault)
2. **Backend** publica comandos via **MQTT** a topics de EVerest
3. **EVerest** ejecuta la simulacion y publica estado a **MQTT**
4. **Backend** recibe eventos y actualiza el **Frontend** via WebSocket

## Topics MQTT de EVerest (AC Simulation) - MAPEADOS

### Topics de Estado Principal (lectura)

| Topic | Descripcion | Ejemplo |
|-------|-------------|---------|
| `everest_api/connector_1/var/session_info` | Estado de sesion | `{"state":"Unplugged","charged_energy_wh":0}` |
| `everest_api/connector_1/var/powermeter` | Mediciones energia | `{"power_W":{"total":0},"voltage_V":{"L1":230.67}}` |
| `everest_api/connector_1/var/limits` | Limites corriente | `{"max_current":32,"nr_of_phases_available":3}` |
| `everest_api/connector_1/var/telemetry` | Telemetria EVSE | `{"temperature":25,"fan_rpm":1500}` |
| `everest_api/connector_1/var/hardware_capabilities` | Capacidades HW | `{"max_current_A_import":32}` |
| `everest_api/connectors` | Lista conectores | `["connector_1"]` |
| `everest_api/errors/var/active_errors` | Errores activos | `[]` |

### Topics Node-RED UI (lectura)

| Topic | Descripcion |
|-------|-------------|
| `everest_external/nodered/1/state/max_current` | Corriente maxima |
| `everest_external/nodered/1/state/temperature` | Temperatura EVSE |
| `everest_external/nodered/1/powermeter_json` | Mediciones JSON |

### Topics Telemetria Avanzada (lectura)

| Topic | Descripcion |
|-------|-------------|
| `everest-telemetry/livedata/1/power_path_controller` | Estado controlador |
| `everest-telemetry/livedata/1/power_switch` | Estado interruptor |
| `/external/powermeter/*` | Mediciones externas |

### Estados de Sesion (`session_info.state`)

- `Unplugged` - Cable desconectado
- `Preparing` - Preparando carga
- `Charging` - Cargando
- `ChargingPausedEV` - Pausado por EV
- `ChargingPausedEVSE` - Pausado por EVSE
- `Finished` - Completado

### Topics de Comando (escritura)

```
everest/modules/connector_1/impl/evse/cmd      # Comandos al EVSE
everest/modules/connector_1/impl/energy_grid/cmd  # Control energia
```

## Prerrequisitos

- Docker Desktop instalado y corriendo
- WSL2 configurado (Windows)
- Puerto 1883 disponible (MQTT)
- Puerto 1880 disponible (EVerest UI)

## Instalacion

### Paso 1: Verificar Docker

```powershell
docker --version
docker compose version
```

### Paso 2: Levantar EVerest AC Simulation

Desde WSL o PowerShell:

```bash
# Opcion A: Script oficial (descarga y ejecuta)
curl https://raw.githubusercontent.com/everest/everest-demo/main/demo-ac.sh | bash

# Opcion B: Docker compose directo (mas control)
curl -o docker-compose.yml https://raw.githubusercontent.com/EVerest/everest-demo/main/docker-compose.everest-sil.yml
docker compose -p everest up -d
```

### Paso 3: Verificar que funciona

1. Abrir UI de EVerest: http://localhost:1880
2. Ver logs: `docker logs -f everest-manager-1`
3. Probar MQTT: 
   ```bash
   # Suscribirse a todos los topics
   mosquitto_sub -h localhost -t 'everest_api/#' -v
   ```

### Paso 4: Configurar Backend para conectar

El backend debe:
1. Conectarse a MQTT en `localhost:1883`
2. Suscribirse a `everest_api/+/var/#` para recibir estado
3. Publicar a `everest_api/+/cmd/#` para enviar comandos

## Estructura de Carpetas Final

```
EV-CyberRange/
├── frontend/           # React app (ya existe)
├── simulator/
│   └── backend/        # FastAPI (ya existe)
├── everest/            # Configuracion EVerest
│   ├── docker-compose.yml
│   └── config/         # Configs custom si necesario
├── docs/
│   └── EVEREST-SETUP.md
└── scripts/
    ├── start-all.ps1   # Levanta todo el stack
    └── stop-all.ps1    # Para todo
```

## Diferencias con MVP Anterior

| Aspecto | MVP Anterior | MVP 2 (Ahora) |
|---------|--------------|---------------|
| Central System | SteVe (Java) | Ninguno |
| Protocolo OCPP | OCPP 1.6 via SteVe | No se usa |
| Autorizacion | RFID en SteVe DB | EVerest interno |
| Complejidad | Alta (4 servicios) | Media (2 servicios) |
| Topics MQTT | Confusos, mal documentados | Bien definidos |

## Proximos Pasos

1. [x] Documentar arquitectura
2. [x] Descargar EVerest demo AC
3. [x] Mapear topics MQTT reales (verificado con mosquitto_sub)
4. [ ] Actualizar mqtt_bridge.py para topics correctos
5. [ ] Probar flujo end-to-end
6. [ ] Documentar vectores de ataque sin OCPP
