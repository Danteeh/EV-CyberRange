"""Router: OCPP/CSMS integration - Charge Points status and commands."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocpp", tags=["ocpp"])

# CSMS HTTP API endpoint (internal Docker network)
CSMS_API_URL = "http://evcr-csms:9001/api"


class RemoteStartRequest(BaseModel):
    charge_point_id: str
    id_tag: str = "RFID-001"
    connector_id: int = 1


class RemoteStopRequest(BaseModel):
    charge_point_id: str
    transaction_id: int


class ResetRequest(BaseModel):
    charge_point_id: str
    reset_type: str = "Soft"  # Soft or Hard


# ──────────────────────────────────────────────────────────────
# CSMS HTTP API Client
# ──────────────────────────────────────────────────────────────

async def csms_get(endpoint: str) -> dict[str, Any]:
    """GET request to CSMS API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{CSMS_API_URL}{endpoint}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            log.error(f"CSMS API error: {e}")
            raise HTTPException(status_code=502, detail=f"CSMS unavailable: {e}")


async def csms_post(endpoint: str, data: dict) -> dict[str, Any]:
    """POST request to CSMS API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{CSMS_API_URL}{endpoint}", json=data)
            return response.json()
        except httpx.HTTPError as e:
            log.error(f"CSMS API error: {e}")
            raise HTTPException(status_code=502, detail=f"CSMS unavailable: {e}")


# ──────────────────────────────────────────────────────────────
# REST Endpoints
# ──────────────────────────────────────────────────────────────

@router.get("/status")
async def csms_status() -> dict[str, Any]:
    """Check CSMS connectivity and status."""
    try:
        status = await csms_get("/status")
        return {
            "csms_url": CSMS_API_URL,
            "connected": True,
            "protocol": "OCPP 1.6J",
            **status
        }
    except HTTPException:
        return {
            "csms_url": CSMS_API_URL,
            "connected": False,
            "protocol": "OCPP 1.6J",
            "error": "CSMS not reachable"
        }


@router.get("/charge-points")
async def list_charge_points() -> dict[str, Any]:
    """List all connected Charge Points from CSMS."""
    try:
        charge_points = await csms_get("/charge-points")
        return {
            "charge_points": charge_points,
            "total": len(charge_points),
            "updated_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        # Fallback to placeholder if CSMS unavailable
        return {
            "charge_points": [],
            "total": 0,
            "error": "CSMS not reachable",
            "updated_at": datetime.utcnow().isoformat(),
        }


@router.get("/charge-points/{cp_id}")
async def get_charge_point(cp_id: str) -> dict[str, Any]:
    """Get details of a specific Charge Point."""
    return await csms_get(f"/charge-points/{cp_id}")


@router.post("/remote-start")
async def remote_start(req: RemoteStartRequest) -> dict[str, Any]:
    """Send RemoteStartTransaction to a Charge Point."""
    log.info(f"RemoteStart: CP={req.charge_point_id}, Tag={req.id_tag}, Connector={req.connector_id}")
    
    result = await csms_post("/remote-start", {
        "charge_point_id": req.charge_point_id,
        "id_tag": req.id_tag,
        "connector_id": req.connector_id
    })
    
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/remote-stop")
async def remote_stop(req: RemoteStopRequest) -> dict[str, Any]:
    """Send RemoteStopTransaction to a Charge Point."""
    log.info(f"RemoteStop: CP={req.charge_point_id}, TxId={req.transaction_id}")
    
    result = await csms_post("/remote-stop", {
        "charge_point_id": req.charge_point_id,
        "transaction_id": req.transaction_id
    })
    
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/reset")
async def reset_charge_point(req: ResetRequest) -> dict[str, Any]:
    """Send Reset command to a Charge Point."""
    log.info(f"Reset: CP={req.charge_point_id}, Type={req.reset_type}")
    
    result = await csms_post("/reset", {
        "charge_point_id": req.charge_point_id,
        "reset_type": req.reset_type
    })
    
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/authorizations")
def list_authorizations() -> dict[str, Any]:
    """List authorized RFID tags (hardcoded - VULNERABLE)."""
    return {
        "tags": [
            {"id_tag": "TAG001", "status": "Accepted", "expiry": None},
            {"id_tag": "TAG002", "status": "Accepted", "expiry": None},
            {"id_tag": "ADMIN", "status": "Accepted", "expiry": None},
            {"id_tag": "TEST", "status": "Accepted", "expiry": None},
            {"id_tag": "EVCR001", "status": "Accepted", "expiry": None},
            {"id_tag": "RFID1234", "status": "Accepted", "expiry": None},
        ],
        "note": "VULNERABLE: Any tag containing 'TEST' or 'ADMIN' is auto-accepted",
        "total": 6,
    }
