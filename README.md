# EV-CyberRange

Laboratorio de ciberseguridad para infraestructura de carga de vehiculos electricos (EV). Simula una estacion de carga real usando EVerest y proporciona herramientas de ataque desde Kali Linux, todo accesible desde el navegador.

## Requisitos

- **Docker Desktop** (Windows/Mac) o Docker Engine (Linux)
- ~4GB RAM disponible
- ~3GB espacio en disco (imagenes Docker)

## Inicio Rapido

```powershell
# Clonar el repositorio
git clone https://github.com/tu-usuario/EV-CyberRange.git
cd EV-CyberRange

# Iniciar el laboratorio (primera vez toma ~5 min para construir Kali)
.\start.ps1

# O sin Kali (mas rapido, ~1 min)
.\start.ps1 -NoKali
```

## URLs de Acceso

| Servicio | URL | Descripcion |
|----------|-----|-------------|
| EVSE Control Panel | http://localhost:1880/ui | Simular conexion/carga de vehiculo |
| Node-RED Editor | http://localhost:1880 | Editar flujos del simulador |
| Kali Linux | http://localhost:6080/vnc.html | Entorno de ataque (noVNC) |
| MQTT Broker | tcp://localhost:1883 | Comunicacion EVerest |

## Arquitectura

```
+-------------------+     +-------------------+     +-------------------+
|   Kali Linux      |     |    EVerest        |     |   Node-RED UI     |
|   (Atacante)      |---->|    Manager        |<----|   (Control EVSE)  |
|   :6080           |     |   (Simulador)     |     |   :1880           |
+-------------------+     +-------------------+     +-------------------+
         |                        |                        |
         |                        v                        |
         |               +-------------------+             |
         +-------------->|   MQTT Broker     |<------------+
                         |   :1883           |
                         +-------------------+
```

## Herramientas de Ataque (en Kali)

Abre http://localhost:6080/vnc.html y ejecuta en la terminal:

```bash
# Escanear infraestructura EVSE
/opt/attack-tools/bin/python3 /root/tools/evse_scanner.py --mqtt-host everest-mqtt --deep

# Monitorear sesiones de carga en tiempo real
/opt/attack-tools/bin/python3 /root/tools/session_hijacker.py --target everest-mqtt --mode monitor

# Enumerar todos los topics MQTT
/opt/attack-tools/bin/python3 /root/tools/mqtt_fuzzer.py --target everest-mqtt --mode enumerate

# Intentar inyeccion de comandos
/opt/attack-tools/bin/python3 /root/tools/session_hijacker.py --target everest-mqtt --mode inject --action pause
```

## Escenarios de Practica

### 1. Reconocimiento
- Enumerar topics MQTT expuestos
- Identificar estructura de comandos de EVerest
- Mapear arquitectura del sistema

### 2. Intercepcion
- Capturar telemetria de sesiones de carga
- Observar datos sensibles (energia, corriente, estado)

### 3. Manipulacion
- Intentar inyectar comandos de control
- Probar modificacion de parametros de carga
- Evaluar resistencia del sistema a ataques

## Detener el Laboratorio

```powershell
docker compose down
```

## Estructura del Proyecto

```
EV-CyberRange/
├── docker-compose.yml    # Stack completo del lab
├── start.ps1             # Script de inicio (Windows)
├── kali/
│   ├── Dockerfile        # Imagen Kali con herramientas
│   └── tools/            # Scripts de ataque Python
├── everest/              # Config EVerest (referencia)
├── simulator/
│   └── backend/          # API FastAPI (opcional)
└── frontend/             # Dashboard React (opcional)
```

## Notas de Seguridad

Este laboratorio es **solo para fines educativos** en entornos controlados. Las herramientas incluidas pueden detectar y explotar vulnerabilidades reales. Usalo responsablemente.

## Solucion de Problemas

**Docker no inicia:**
- Verificar que Docker Desktop este corriendo
- En Windows: asegurar que WSL2 este habilitado

**Kali no conecta a MQTT:**
- Verificar que todos los contenedores esten en la misma red: `docker network inspect ev-cyberrange`

**Node-RED no carga:**
- Esperar 30 segundos adicionales, EVerest toma tiempo en inicializar
- Ver logs: `docker compose logs nodered`

## Licencia

MIT
