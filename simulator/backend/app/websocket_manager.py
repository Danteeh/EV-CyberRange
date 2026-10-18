"""
WebSocket Manager: push de estado en tiempo real al frontend.
Gestiona múltiples conexiones y un loop de broadcast periódico.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from .config import WS_PUSH_INTERVAL
from .state_store import station

log = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        # Conexiones que completaron el handshake y recibieron el snapshot inicial
        self._ready: set[WebSocket] = set()
        self._task: asyncio.Task | None = None

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        # Enviar snapshot inmediato antes de agregar al pool de broadcast
        try:
            await ws.send_text(json.dumps(station.snapshot()))
            self._ready.add(ws)
            log.info("WS client ready — total: %d", len(self._ready))
        except Exception as exc:
            log.warning("WS initial snapshot failed, dropping: %s", exc)

    def disconnect(self, ws: WebSocket) -> None:
        self._ready.discard(ws)
        log.info("WS client disconnected — total: %d", len(self._ready))

    async def broadcast(self, data: dict[str, Any]) -> None:
        if not self._ready:
            return
        message = json.dumps(data)
        dead: set[WebSocket] = set()
        for ws in list(self._ready):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._ready.discard(ws)

    async def broadcast_event(self, event_dict: dict[str, Any]) -> None:
        await self.broadcast({"type": "event", "event": event_dict})

    async def _push_loop(self) -> None:
        log.info("WS push loop started (interval=%.1fs)", WS_PUSH_INTERVAL)
        while True:
            await asyncio.sleep(WS_PUSH_INTERVAL)
            try:
                if self._ready:
                    await self.broadcast(station.snapshot())
            except Exception as exc:
                log.error("WS push loop error: %s", exc)

    def start_push_loop(self) -> None:
        self._task = asyncio.create_task(self._push_loop())

    def stop_push_loop(self) -> None:
        if self._task:
            self._task.cancel()


ws_manager = WebSocketManager()
