"""
Router: control del simulador EV.
Todos los comandos se traducen a publicaciones MQTT hacia EVerest.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Path
from pydantic import BaseModel

from ..mqtt_bridge import bridge
from ..state_store import station

router = APIRouter(prefix="/api/control", tags=["control"])


def _publish_or_raise(connector_id: int, channel: str, action: str, payload: Any) -> None:
    ok = bridge.publish(connector_id, channel, action, payload)
    if not ok:
        raise HTTPException(status_code=503, detail="MQTT not connected")


class PluginRequest(BaseModel):
    simulation: str = "sleep 1;iec_wait_pwr_ready;sleep 1;draw_power_regulated 16,3;sleep 36000"
    id_tag: str = "CARD-001"


@router.post("/connector/{connector_id}/plugin")
def car_plugin(
    connector_id: int = Path(ge=1, le=2),
    req: PluginRequest = Body(default=None),
) -> dict[str, Any]:
    if req is None:
        req = PluginRequest()
    """
    Simula el enchufado del vehiculo.
    1. enable=true                 -- activa simulador EV
    2. execute_charging_session    -- EV se enchufa fisicamente
    3. present_authorization_token -- RFID autoriza la carga (EVerest: WaitingForAuth -> Charging)
    """
    # 1. Habilitar simulacion
    bridge.publish(connector_id, "carsim", "cmd/enable", True)

    # 2. Enchufar EV
    _publish_or_raise(connector_id, "carsim", "cmd/execute_charging_session", req.simulation)

    # 3. Presentar RFID con pequeño delay para que EVerest procese el enchufado
    time.sleep(0.5)
    token_payload = {
        "request_id": 1,
        "id_token": {
            "value": req.id_tag,
            "type": "ISO14443"
        },
        "connectors": [connector_id]
    }
    bridge.publish_to_topic("everest_api/dummy_token_provider/cmd/provide", token_payload)

    return {"status": "ok", "action": "plugin", "connector_id": connector_id, "id_tag": req.id_tag}


@router.post("/connector/{connector_id}/unplug")
def car_unplug(connector_id: int = Path(ge=1, le=2)) -> dict[str, Any]:
    """Simula el desenchufado del vehiculo."""
    _publish_or_raise(connector_id, "carsim", "cmd/modify_charging_session", "stop")
    return {"status": "ok", "action": "unplug", "connector_id": connector_id}


@router.post("/connector/{connector_id}/pause")
def pause_charging(connector_id: int = Path(ge=1, le=2)) -> dict[str, Any]:
    """Pausa la carga activa."""
    _publish_or_raise(connector_id, "cmd", "pause_charging", "")
    return {"status": "ok", "action": "pause", "connector_id": connector_id}


@router.post("/connector/{connector_id}/resume")
def resume_charging(connector_id: int = Path(ge=1, le=2)) -> dict[str, Any]:
    """Reanuda la carga pausada."""
    _publish_or_raise(connector_id, "cmd", "resume_charging", "")
    return {"status": "ok", "action": "resume", "connector_id": connector_id}


@router.post("/connector/{connector_id}/enable")
def enable_simulation(
    connector_id: int = Path(ge=1, le=2),
    enabled: bool = Body(default=True, embed=True),
) -> dict[str, Any]:
    """Habilita/deshabilita la simulacion del EV."""
    _publish_or_raise(connector_id, "carsim", "cmd/enable", enabled)
    return {"status": "ok", "action": "enable", "connector_id": connector_id, "enabled": enabled}


@router.post("/connector/{connector_id}/authorize")
def authorize(
    connector_id: int = Path(ge=1, le=2),
    id_tag: str = Body(default="CARD-001", embed=True),
) -> dict[str, Any]:
    """Presenta un idTag RFID al autorizador de EVerest usando DummyTokenProviderManual."""
    token_payload = {
        "request_id": 1,
        "id_token": {
            "value": id_tag,
            "type": "ISO14443"
        },
        "connectors": [connector_id]
    }
    # DummyTokenProviderManual escucha en everest_api/dummy_token_provider/cmd/provide
    ok = bridge.publish_to_topic("everest_api/dummy_token_provider/cmd/provide", token_payload)
    if not ok:
        raise HTTPException(status_code=503, detail="MQTT not connected")
    return {"status": "ok", "action": "authorize", "connector_id": connector_id, "id_tag": id_tag}


@router.post("/connector/{connector_id}/set_max_current")
def set_max_current(
    connector_id: int = Path(ge=1, le=2),
    amperes: float = Body(..., embed=True, ge=0, le=32),
) -> dict[str, Any]:
    """Establece la corriente maxima del conector."""
    _publish_or_raise(connector_id, "cmd", "set_max_current", amperes)
    return {"status": "ok", "action": "set_max_current", "connector_id": connector_id, "amperes": amperes}
