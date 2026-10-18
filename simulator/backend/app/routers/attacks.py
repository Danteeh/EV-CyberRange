"""Router: escenarios de ciberataque."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..attack_engine import attack_engine
from ..state_store import station

router = APIRouter(prefix="/api/attacks", tags=["attacks"])


@router.get("/scenarios")
def list_scenarios() -> dict[str, Any]:
    return {"scenarios": attack_engine.get_scenarios()}


@router.get("")
def list_active() -> dict[str, Any]:
    return {"attacks": station.get_attacks()}


@router.post("/{scenario_id}/start")
async def start_attack(scenario_id: str) -> dict[str, Any]:
    sc = await attack_engine.start(scenario_id)
    if sc is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return {"status": "started", "attack": sc.to_dict()}


@router.post("/{scenario_id}/stop")
async def stop_attack(scenario_id: str) -> dict[str, Any]:
    ok = await attack_engine.stop(scenario_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No active attack '{scenario_id}'")
    return {"status": "stopped", "scenario_id": scenario_id}
