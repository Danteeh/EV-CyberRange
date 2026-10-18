"""Router: historial de eventos y auditoría."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..state_store import station

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def get_events(
    limit: int = Query(default=100, ge=1, le=500),
    event_type: str | None = Query(default=None),
) -> dict[str, Any]:
    events = station.get_events(limit=limit, event_type=event_type)
    return {"count": len(events), "events": events}


@router.delete("")
def clear_events() -> dict[str, Any]:
    with station._lock:
        station.events.clear()
    return {"status": "cleared"}
