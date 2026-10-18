"""
Modelos de dominio de EV-CyberRange.
Dataclasses puras — sin dependencias externas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Enumeraciones
# ──────────────────────────────────────────────────────────────

class ConnectorState(str, Enum):
    UNKNOWN = "UNKNOWN"
    AVAILABLE = "Available"
    PREPARING = "Preparing"
    CHARGING = "Charging"
    SUSPENDED_EV = "SuspendedEV"
    SUSPENDED_EVSE = "SuspendedEVSE"
    FINISHING = "Finishing"
    RESERVED = "Reserved"
    UNAVAILABLE = "Unavailable"
    FAULTED = "Faulted"
    # Estados internos de EVerest (no OCPP, pero que EVerest publica en session_info)
    UNPLUGGED = "Unplugged"
    WAITING_FOR_AUTHENTICATION = "WaitingForAuthentication"
    TRANSACTION_STARTED = "TransactionStarted"
    TRANSACTION_FINISHED = "TransactionFinished"


class OcppStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    UNKNOWN = "UNKNOWN"


class EventSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventType(str, Enum):
    MQTT_EVENT = "MQTT_EVENT"
    EVSE_SESSION = "EVSE_SESSION"
    OCPP_TRANSACTION = "OCPP_TRANSACTION"
    OCPP_MESSAGE = "OCPP_MESSAGE"
    SECURITY_EVENT = "SECURITY_EVENT"
    CONTROL_CMD = "CONTROL_CMD"
    ATTACK_EVENT = "ATTACK_EVENT"
    SYSTEM = "SYSTEM"


class AttackType(str, Enum):
    OCPP_REPLAY = "OCPP_REPLAY"
    MQTT_FUZZING = "MQTT_FUZZING"
    UNAUTHORIZED_REMOTE_START = "UNAUTHORIZED_REMOTE_START"
    FIRMWARE_MANIPULATION = "FIRMWARE_MANIPULATION"
    DOS_OCPP = "DOS_OCPP"


class AttackStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


# ──────────────────────────────────────────────────────────────
# Estado eléctrico de un conector
# ──────────────────────────────────────────────────────────────

@dataclass
class PowerMetrics:
    power_w: float = 0.0
    energy_wh: float = 0.0
    voltage_l1_v: float = 0.0
    voltage_l2_v: float = 0.0
    voltage_l3_v: float = 0.0
    current_l1_a: float = 0.0
    current_l2_a: float = 0.0
    current_l3_a: float = 0.0
    frequency_hz: float = 50.0
    temperature_c: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "power_w": self.power_w,
            "energy_wh": self.energy_wh,
            "voltage_l1_v": self.voltage_l1_v,
            "voltage_l2_v": self.voltage_l2_v,
            "voltage_l3_v": self.voltage_l3_v,
            "current_l1_a": self.current_l1_a,
            "current_l2_a": self.current_l2_a,
            "current_l3_a": self.current_l3_a,
            "frequency_hz": self.frequency_hz,
            "temperature_c": self.temperature_c,
        }


@dataclass
class ConnectorStatus:
    connector_id: int
    state: ConnectorState = ConnectorState.UNKNOWN
    session_id: str | None = None
    id_tag: str | None = None
    charging_duration_s: int = 0
    metrics: PowerMetrics = field(default_factory=PowerMetrics)
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "state": self.state.value,
            "session_id": self.session_id,
            "id_tag": self.id_tag,
            "charging_duration_s": self.charging_duration_s,
            "metrics": self.metrics.to_dict(),
            "updated_at": self.updated_at,
        }


# ──────────────────────────────────────────────────────────────
# Evento del sistema
# ──────────────────────────────────────────────────────────────

@dataclass
class SystemEvent:
    event_type: EventType
    severity: EventSeverity
    source: str
    message: str
    connector_id: int | None = None
    topic: str | None = None
    payload: Any = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "source": self.source,
            "message": self.message,
            "connector_id": self.connector_id,
            "topic": self.topic,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


# ──────────────────────────────────────────────────────────────
# Escenario de ataque
# ──────────────────────────────────────────────────────────────

@dataclass
class AttackScenario:
    id: str
    name: str
    attack_type: AttackType
    description: str
    severity: EventSeverity
    target: str
    status: AttackStatus = AttackStatus.IDLE
    started_at: str | None = None
    completed_at: str | None = None
    events_generated: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "attack_type": self.attack_type.value,
            "description": self.description,
            "severity": self.severity.value,
            "target": self.target,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "events_generated": self.events_generated,
        }
