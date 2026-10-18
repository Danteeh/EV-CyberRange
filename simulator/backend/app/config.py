"""
Configuración centralizada de EV-CyberRange Backend.
Todos los parámetros de conexión y constantes en un solo lugar.
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────
# Identidad de la estación
# ──────────────────────────────────────────────────────────────
STATION_ID = "EVCR-001"
STATION_NAME = "EV-CyberRange Station 01"
PROTOCOL = "OCPP 1.6J"
NUM_CONNECTORS = 2

# ──────────────────────────────────────────────────────────────
# MQTT (Mosquitto dentro de WSL/Docker)
# ──────────────────────────────────────────────────────────────
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ev-cyberrange-backend"
MQTT_KEEPALIVE = 30
MQTT_RECONNECT_DELAY = 5          # segundos entre reintentos

# Topics EVerest que el backend escucha
MQTT_TOPICS_SUBSCRIBE = [
    # EVSE managers — session y powermeter
    "everest_api/evse_manager_1/var/session_info",
    "everest_api/evse_manager_1/var/powermeter",
    "everest_api/evse_manager_2/var/session_info",
    "everest_api/evse_manager_2/var/powermeter",
    # Estado OCPP (topic exacto)
    "everest_api/ocpp/var/connection_status",
    # Toda la API de EVerest (módulo API y EvAPI)
    "everest_api/#",
    # Comandos externos entrantes (auditoría)
    "everest_external/#",
]

# Prefix para publicar comandos desde el backend
MQTT_CMD_PREFIX = "everest_external/nodered"

# ──────────────────────────────────────────────────────────────
# SteVe (OCPP Central System)
# ──────────────────────────────────────────────────────────────
STEVE_BASE_URL = "http://127.0.0.1:8180/steve"
STEVE_API_URL = f"{STEVE_BASE_URL}/api/v1"
STEVE_WEB_URL = f"{STEVE_BASE_URL}/"
STEVE_HTTP_TIMEOUT = 10.0

# ──────────────────────────────────────────────────────────────
# Base de datos local (eventos / auditoría)
# ──────────────────────────────────────────────────────────────
DB_PATH = "ev_cyberrange.db"
EVENTS_MAX_MEMORY = 500           # máx eventos en memoria (deque)

# ──────────────────────────────────────────────────────────────
# WebSocket push (frontend)
# ──────────────────────────────────────────────────────────────
WS_PUSH_INTERVAL = 0.5           # segundos entre broadcasts de estado
WS_PING_INTERVAL = 20

# ──────────────────────────────────────────────────────────────
# CORS (desarrollo: permite cualquier origen)
# ──────────────────────────────────────────────────────────────
CORS_ORIGINS = ["*"]
