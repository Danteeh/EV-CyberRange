"""
EV-CyberRange Backend v2.0
FastAPI + MQTT bridge + WebSocket push + Attack Engine
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .mqtt_bridge import bridge
from .websocket_manager import ws_manager
from .routers import attacks, control, events, station as station_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("EV-CyberRange backend starting...")
    bridge.start()
    ws_manager.start_push_loop()
    yield
    log.info("EV-CyberRange backend shutting down...")
    ws_manager.stop_push_loop()
    bridge.stop()


# ──────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="EV-CyberRange Backend",
    version="2.0.0",
    description=(
        "Backend de integración, monitoreo y ciberseguridad "
        "para el simulador EV-CyberRange (EVerest + SteVe)."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Routers REST
# ──────────────────────────────────────────────────────────────

app.include_router(station_router.router)
app.include_router(control.router)
app.include_router(attacks.router)
app.include_router(events.router)


# ──────────────────────────────────────────────────────────────
# WebSocket endpoint
# ──────────────────────────────────────────────────────────────

@app.websocket("/ws/realtime")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws_manager.connect(ws)
    try:
        # Mantener la conexión viva esperando mensajes o desconexión.
        # receive_bytes() retorna en desconexión sin lanzar en keepalive pings.
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            # Mensajes de texto entrantes del frontend (ej. ping)
            # se ignoran — el push es unidireccional desde el servidor.
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.error("WS error: %s", exc)
    finally:
        ws_manager.disconnect(ws)


# ──────────────────────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "application": "EV-CyberRange",
        "version": "2.0.0",
        "docs": "/docs",
        "ws": "/ws/realtime",
    }
