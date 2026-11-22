"""
Live Attack Feed - SSE endpoint for real-time attack visibility
Streams attack events from Kali tools to the frontend
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/attack-feed", tags=["Attack Feed"])

# Shared log path where Kali exploits write their output
ATTACK_LOG_PATH = os.environ.get(
    "ATTACK_LOG_PATH", 
    "/shared-logs/attack_events.jsonl"
)

# In-memory buffer for recent attacks (for initial load)
_recent_attacks: list[dict] = []
MAX_BUFFER_SIZE = 100


def add_attack_event(event: dict) -> None:
    """Add event to in-memory buffer"""
    global _recent_attacks
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    _recent_attacks.append(event)
    if len(_recent_attacks) > MAX_BUFFER_SIZE:
        _recent_attacks = _recent_attacks[-MAX_BUFFER_SIZE:]


async def tail_attack_log() -> AsyncGenerator[str, None]:
    """
    Tail the attack log file and yield new lines as SSE events.
    Similar to `tail -f` but async.
    """
    log_path = Path(ATTACK_LOG_PATH)
    
    # Create file if it doesn't exist
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.touch()
    
    # Start from end of file
    with open(log_path, "r") as f:
        f.seek(0, 2)  # Seek to end
        
        while True:
            line = f.readline()
            if line:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        add_attack_event(event)
                        yield f"data: {json.dumps(event)}\n\n"
                    except json.JSONDecodeError:
                        # Plain text line, wrap it
                        event = {
                            "type": "log",
                            "message": line,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        add_attack_event(event)
                        yield f"data: {json.dumps(event)}\n\n"
            else:
                await asyncio.sleep(0.2)


@router.get("/stream")
async def stream_attacks(request: Request):
    """
    SSE endpoint for live attack feed.
    Connect to this endpoint to receive real-time attack events.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        # Send initial buffer
        for event in _recent_attacks[-20:]:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Then stream new events
        async for event in tail_attack_log():
            # Check if client disconnected
            if await request.is_disconnected():
                break
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/recent")
async def get_recent_attacks():
    """Get the most recent attack events from buffer"""
    return {"events": _recent_attacks[-50:]}


@router.post("/log")
async def log_attack_event(event: dict):
    """
    Endpoint for Kali tools to POST attack events.
    Alternative to file-based logging.
    """
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    event["source"] = event.get("source", "kali")
    
    add_attack_event(event)
    
    # Also write to file for persistence
    log_path = Path(ATTACK_LOG_PATH)
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "a") as f:
        f.write(json.dumps(event) + "\n")
    
    return {"status": "logged", "event": event}
