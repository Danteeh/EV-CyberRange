"""
Estado global de EV-CyberRange.
Thread-safe. Único punto de verdad para backend + WebSocket push.
"""
from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from .config import EVENTS_MAX_MEMORY, NUM_CONNECTORS, STATION_ID, STATION_NAME, PROTOCOL
from .models import (
    AttackScenario,
    AttackStatus,
    ConnectorStatus,
    EventSeverity,
    EventType,
    OcppStatus,
    PowerMetrics,
    SystemEvent,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


class StationState:
    """
    Estado completo de la estación EV-CyberRange.
    Acceso thread-safe mediante un único RLock.
    """

    def __init__(self) -> None:
        self._lock = Lock()

        # ── Conectividad ──────────────────────────────────────
        self.mqtt_connected: bool = False
        self.ocpp_status: OcppStatus = OcppStatus.UNKNOWN

        # ── Conectores (1..NUM_CONNECTORS) ───────────────────
        self.connectors: dict[int, ConnectorStatus] = {
            i: ConnectorStatus(connector_id=i)
            for i in range(1, NUM_CONNECTORS + 1)
        }

        # ── Historial de eventos (en memoria) ─────────────────
        self.events: deque[SystemEvent] = deque(maxlen=EVENTS_MAX_MEMORY)

        # ── Escenarios de ataque activos ──────────────────────
        self.active_attacks: dict[str, AttackScenario] = {}

        # ── Metadatos del backend ─────────────────────────────
        self.started_at: str = _utc_now()
        self.updated_at: str = _utc_now()

    # ──────────────────────────────────────────────────────────
    # MQTT ingestion helpers
    # ──────────────────────────────────────────────────────────

    def on_mqtt_connect(self, connected: bool) -> None:
        with self._lock:
            self.mqtt_connected = connected
            self.updated_at = _utc_now()

    def on_session_info(self, connector_id: int, payload: dict[str, Any]) -> None:
        """Procesa everest_api/evse_manager_N/var/session_info"""
        with self._lock:
            c = self.connectors.get(connector_id)
            if c is None:
                return

            raw_state = payload.get("state", c.state.value)
            # EVerest usa strings como "Charging", "Available"...
            from .models import ConnectorState
            try:
                c.state = ConnectorState(raw_state)
            except ValueError:
                c.state = ConnectorState.UNKNOWN

            c.session_id = payload.get("session_id") or payload.get("transaction_id")
            c.id_tag = payload.get("id_tag") or payload.get("id_token")
            c.charging_duration_s = _safe_int(
                payload.get("charging_duration_s"), c.charging_duration_s
            )
            c.metrics.energy_wh = _safe_float(
                payload.get("charged_energy_wh"), c.metrics.energy_wh
            )
            c.updated_at = _utc_now()
            self.updated_at = c.updated_at

    def on_powermeter(self, connector_id: int, payload: dict[str, Any]) -> None:
        """Procesa everest_api/evse_manager_N/var/powermeter"""
        with self._lock:
            c = self.connectors.get(connector_id)
            if c is None:
                return
            m = c.metrics

            power = payload.get("power_W", {})
            voltage = payload.get("voltage_V", {})
            current = payload.get("current_A", {})
            energy = payload.get("energy_Wh_import", {})
            temp = payload.get("temperature_C", {})

            if isinstance(power, dict):
                m.power_w = _safe_float(power.get("total"), m.power_w)
            elif isinstance(power, (int, float)):
                m.power_w = _safe_float(power, m.power_w)

            if isinstance(energy, dict):
                m.energy_wh = _safe_float(energy.get("total"), m.energy_wh)

            if isinstance(voltage, dict):
                m.voltage_l1_v = _safe_float(voltage.get("L1"), m.voltage_l1_v)
                m.voltage_l2_v = _safe_float(voltage.get("L2"), m.voltage_l2_v)
                m.voltage_l3_v = _safe_float(voltage.get("L3"), m.voltage_l3_v)

            if isinstance(current, dict):
                m.current_l1_a = _safe_float(current.get("L1"), m.current_l1_a)
                m.current_l2_a = _safe_float(current.get("L2"), m.current_l2_a)
                m.current_l3_a = _safe_float(current.get("L3"), m.current_l3_a)

            if isinstance(temp, dict):
                m.temperature_c = _safe_float(temp.get("value"), m.temperature_c)
            elif isinstance(temp, (int, float)):
                m.temperature_c = _safe_float(temp, m.temperature_c)

            c.updated_at = _utc_now()
            self.updated_at = c.updated_at

    def on_ocpp_status(self, raw: Any) -> None:
        """Procesa everest_api/ocpp/var/connection_status"""
        with self._lock:
            if isinstance(raw, str):
                v = raw.strip().lower()
                if v == "connected":
                    self.ocpp_status = OcppStatus.CONNECTED
                elif v in {"disconnected", "connection_failed", "failed"}:
                    self.ocpp_status = OcppStatus.DISCONNECTED
            elif isinstance(raw, dict):
                val = raw.get("connected") or raw.get("is_connected")
                if val is True:
                    self.ocpp_status = OcppStatus.CONNECTED
                elif val is False:
                    self.ocpp_status = OcppStatus.DISCONNECTED
            elif isinstance(raw, bool):
                self.ocpp_status = OcppStatus.CONNECTED if raw else OcppStatus.DISCONNECTED
            self.updated_at = _utc_now()

    # ──────────────────────────────────────────────────────────
    # Eventos
    # ──────────────────────────────────────────────────────────

    def add_event(self, event: SystemEvent) -> None:
        with self._lock:
            self.events.appendleft(event)
            self.updated_at = _utc_now()

    def get_events(self, limit: int = 100, event_type: str | None = None) -> list[dict]:
        with self._lock:
            evs = list(self.events)
        if event_type:
            evs = [e for e in evs if e.event_type.value == event_type]
        return [e.to_dict() for e in evs[:limit]]

    # ──────────────────────────────────────────────────────────
    # Ataques
    # ──────────────────────────────────────────────────────────

    def register_attack(self, scenario: AttackScenario) -> None:
        with self._lock:
            self.active_attacks[scenario.id] = scenario

    def update_attack(self, attack_id: str, **kwargs: Any) -> None:
        with self._lock:
            sc = self.active_attacks.get(attack_id)
            if sc is None:
                return
            for k, v in kwargs.items():
                if hasattr(sc, k):
                    setattr(sc, k, v)

    def get_attacks(self) -> list[dict]:
        with self._lock:
            return [a.to_dict() for a in self.active_attacks.values()]

    # ──────────────────────────────────────────────────────────
    # Snapshot completo para WebSocket push
    # ──────────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            connectors = {
                str(cid): c.to_dict()
                for cid, c in self.connectors.items()
            }
            attacks = [a.to_dict() for a in self.active_attacks.values()]
            recent_events = [e.to_dict() for e in list(self.events)[:20]]

        return {
            "type": "state",
            "station": {
                "id": STATION_ID,
                "name": STATION_NAME,
                "protocol": PROTOCOL,
            },
            "connectivity": {
                "mqtt": self.mqtt_connected,
                "ocpp": self.ocpp_status.value,
            },
            "connectors": connectors,
            "attacks": attacks,
            "recent_events": recent_events,
            "updated_at": self.updated_at,
        }


# Instancia global — importada por todos los módulos
station = StationState()
