"""Router: estado de la estación y conectores."""
from __future__ import annotations

import socket
from typing import Any

from fastapi import APIRouter

from ..config import STATION_ID, STATION_NAME, PROTOCOL, STEVE_WEB_URL
from ..state_store import station

router = APIRouter(prefix="/api", tags=["station"])


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "components": {
            "backend": True,
            "mqtt": station.mqtt_connected,
            "steve": _port_open("127.0.0.1", 8180),
            "nodered": _port_open("127.0.0.1", 1880),
            "ocpp": station.ocpp_status.value,
        },
        "station_id": STATION_ID,
        "uptime_started": station.started_at,
    }


@router.get("/station")
def get_station() -> dict[str, Any]:
    snap = station.snapshot()
    return {
        "station": snap["station"],
        "connectivity": snap["connectivity"],
        "connectors": snap["connectors"],
        "updated_at": snap["updated_at"],
    }


@router.get("/connectors")
def get_connectors() -> dict[str, Any]:
    with station._lock:
        return {
            str(cid): c.to_dict()
            for cid, c in station.connectors.items()
        }


@router.get("/connectors/{connector_id}")
def get_connector(connector_id: int) -> dict[str, Any]:
    with station._lock:
        c = station.connectors.get(connector_id)
    if c is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
    return c.to_dict()
