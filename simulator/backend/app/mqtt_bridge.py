"""
MQTT Bridge: conecta EVerest (Mosquitto) con el estado interno.
Maneja reconexión automática y enruta cada topic al handler correcto.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from threading import Thread
from typing import Any

import paho.mqtt.client as mqtt

from .config import (
    MQTT_CLIENT_ID,
    MQTT_HOST,
    MQTT_KEEPALIVE,
    MQTT_PORT,
    MQTT_RECONNECT_DELAY,
    MQTT_TOPICS_SUBSCRIBE,
    MQTT_CMD_PREFIX,
)
from .models import EventSeverity, EventType, SystemEvent
from .state_store import station

log = logging.getLogger(__name__)

# Regex para extraer connector_id del topic
# everest_api/evse_manager_1/var/session_info  → 1
# everest_api/evse_manager_2/var/powermeter    → 2
_EVSE_TOPIC_RE = re.compile(
    r"everest_api/evse_manager_(\d+)/var/(session_info|powermeter)"
)
_EXTERNAL_CMD_RE = re.compile(
    r"everest_external/nodered/(\d+)/(carsim|cmd)/(.*)"
)


def _decode(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MqttBridge:
    def __init__(self) -> None:
        self._client: mqtt.Client | None = None
        self._running = False

    # ──────────────────────────────────────────────────────────
    # Callbacks Paho
    # ──────────────────────────────────────────────────────────

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        connected = (reason_code == 0)
        station.on_mqtt_connect(connected)

        if connected:
            log.info("MQTT connected to %s:%d", MQTT_HOST, MQTT_PORT)
            for topic in MQTT_TOPICS_SUBSCRIBE:
                client.subscribe(topic, qos=0)
                log.debug("Subscribed: %s", topic)

            station.add_event(SystemEvent(
                event_type=EventType.SYSTEM,
                severity=EventSeverity.INFO,
                source="mqtt_bridge",
                message=f"MQTT connected to {MQTT_HOST}:{MQTT_PORT}",
            ))
        else:
            log.warning("MQTT connection failed: rc=%s", reason_code)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        station.on_mqtt_connect(False)
        log.warning("MQTT disconnected (rc=%s) — will reconnect", reason_code)
        station.add_event(SystemEvent(
            event_type=EventType.SYSTEM,
            severity=EventSeverity.WARNING,
            source="mqtt_bridge",
            message="MQTT disconnected — reconnecting...",
        ))

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        topic = msg.topic
        payload = _decode(msg.payload)
        self._route(topic, payload)

    # ──────────────────────────────────────────────────────────
    # Router
    # ──────────────────────────────────────────────────────────

    def _route(self, topic: str, payload: Any) -> None:
        # ── EVSE session_info / powermeter ───────────────────
        m = _EVSE_TOPIC_RE.match(topic)
        if m:
            connector_id = int(m.group(1))
            var = m.group(2)
            if isinstance(payload, dict):
                if var == "session_info":
                    station.on_session_info(connector_id, payload)
                elif var == "powermeter":
                    station.on_powermeter(connector_id, payload)
            station.add_event(SystemEvent(
                event_type=EventType.MQTT_EVENT,
                severity=EventSeverity.INFO,
                source="everest",
                message=f"evse_manager_{connector_id} → {var}",
                connector_id=connector_id,
                topic=topic,
                payload=payload if not isinstance(payload, dict) else None,
            ))
            return

        # ── OCPP connection_status ───────────────────────────
        if topic == "everest_api/ocpp/var/connection_status":
            station.on_ocpp_status(payload)
            station.add_event(SystemEvent(
                event_type=EventType.SYSTEM,
                severity=EventSeverity.INFO,
                source="ocpp",
                message=f"OCPP status → {payload}",
                topic=topic,
            ))
            return

        # ── Comandos externos (auditoría de seguridad) ───────
        m2 = _EXTERNAL_CMD_RE.match(topic)
        if m2:
            connector_id = int(m2.group(1))
            channel = m2.group(2)
            action = m2.group(3)
            station.add_event(SystemEvent(
                event_type=EventType.SECURITY_EVENT,
                severity=EventSeverity.HIGH,
                source="external_control",
                message=f"External cmd on connector {connector_id}: {channel}/{action}",
                connector_id=connector_id,
                topic=topic,
                payload=payload,
            ))
            return

        # ── Otros topics: loguear genérico ───────────────────
        station.add_event(SystemEvent(
            event_type=EventType.MQTT_EVENT,
            severity=EventSeverity.INFO,
            source="everest",
            message=f"topic: {topic}",
            topic=topic,
        ))

    # ──────────────────────────────────────────────────────────
    # Publicar comandos hacia EVerest
    # ──────────────────────────────────────────────────────────

    def publish(self, connector_id: int, channel: str, action: str, payload: Any) -> bool:
        """
        Publica un comando hacia EVerest vía MQTT.
        topic: everest_external/nodered/{connector_id}/{channel}/{action}

        Encoding:
          - bool  → "true" / "false"  (sin comillas JSON, EVerest espera raw)
          - dict/list → JSON serializado
          - str   → raw (sin comillas extras)
          - otros → str()
        """
        if self._client is None:
            log.error("Cannot publish: MQTT client not initialized")
            return False

        topic = f"{MQTT_CMD_PREFIX}/{connector_id}/{channel}/{action}"
        if isinstance(payload, bool):
            raw = "true" if payload else "false"
        elif isinstance(payload, (dict, list)):
            raw = json.dumps(payload)
        elif isinstance(payload, str):
            raw = payload          # ya es texto, no re-encodear con json.dumps
        else:
            raw = str(payload)

        result = self._client.publish(topic, raw, qos=0)
        ok = result.rc == mqtt.MQTT_ERR_SUCCESS
        log.info("PUBLISH %s → %s (rc=%d)", topic, raw[:80], result.rc)

        station.add_event(SystemEvent(
            event_type=EventType.CONTROL_CMD,
            severity=EventSeverity.INFO,
            source="backend",
            message=f"CMD connector {connector_id}: {channel}/{action} = {raw[:60]}",
            connector_id=connector_id,
            topic=topic,
            payload=payload,
        ))
        return ok

    def publish_to_topic(self, topic: str, payload: Any) -> bool:
        """
        Publica un mensaje a un topic MQTT arbitrario (no prefijado).
        Usado para topics como 'everest_api/dummy_token_provider/cmd/provide'.
        """
        if self._client is None:
            log.error("Cannot publish: MQTT client not initialized")
            return False

        if isinstance(payload, (dict, list)):
            raw = json.dumps(payload)
        elif isinstance(payload, bool):
            raw = "true" if payload else "false"
        elif isinstance(payload, str):
            raw = payload
        else:
            raw = str(payload)

        result = self._client.publish(topic, raw, qos=0)
        ok = result.rc == mqtt.MQTT_ERR_SUCCESS
        log.info("PUBLISH %s → %s (rc=%d)", topic, raw[:80], result.rc)
        return ok

    # ──────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────

    def start(self) -> None:
        self._running = True
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID,
        )
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message

        self._client = client

        def _connect_loop() -> None:
            while self._running:
                try:
                    client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
                    client.loop_forever(retry_first_connection=True)
                except Exception as exc:
                    log.error("MQTT connect error: %s — retry in %ds", exc, MQTT_RECONNECT_DELAY)
                    time.sleep(MQTT_RECONNECT_DELAY)

        t = Thread(target=_connect_loop, daemon=True, name="mqtt-bridge")
        t.start()
        log.info("MqttBridge started")

    def stop(self) -> None:
        self._running = False
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
        log.info("MqttBridge stopped")


# Instancia global
bridge = MqttBridge()
