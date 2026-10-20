"""
EV-CyberRange CSMS (Central System Management System)
OCPP 1.6J WebSocket Server

Based on mobilityhouse/ocpp library
Designed to be hackable for security research
"""
import asyncio
import logging
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

import websockets
from websockets.asyncio.server import serve, ServerConnection

from ocpp.v16 import ChargePoint as CP
from ocpp.v16 import call_result, call
from ocpp.v16.enums import (
    Action, RegistrationStatus, AuthorizationStatus,
    RemoteStartStopStatus, ConfigurationStatus, TriggerMessageStatus,
    AvailabilityStatus, AvailabilityType, ResetStatus, ResetType,
    UnlockStatus, ClearCacheStatus
)
from ocpp.routing import on

# Action enum uses snake_case in ocpp 2.x
# Map for clarity
BOOT_NOTIFICATION = Action.boot_notification
HEARTBEAT = Action.heartbeat
STATUS_NOTIFICATION = Action.status_notification
AUTHORIZE = Action.authorize
START_TRANSACTION = Action.start_transaction
STOP_TRANSACTION = Action.stop_transaction
METER_VALUES = Action.meter_values
DATA_TRANSFER = Action.data_transfer
GET_CONFIGURATION = Action.get_configuration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger('CSMS')

# ============================================================
# Data Models
# ============================================================

@dataclass
class ChargingSession:
    transaction_id: int
    connector_id: int
    id_tag: str
    start_time: datetime
    meter_start: int
    meter_values: list = field(default_factory=list)
    
@dataclass  
class ChargePointInfo:
    id: str
    vendor: str = "Unknown"
    model: str = "Unknown"
    serial_number: str = ""
    firmware_version: str = ""
    status: str = "Available"
    last_heartbeat: Optional[datetime] = None
    sessions: Dict[int, ChargingSession] = field(default_factory=dict)

# ============================================================
# Charge Point Handler (OCPP 1.6)
# ============================================================

class ChargePointHandler(CP):
    """
    Handles OCPP messages from a single Charge Point.
    All @on decorated methods respond to CP-initiated messages.
    """
    
    def __init__(self, charge_point_id: str, websocket: ServerConnection, csms: 'CSMS'):
        super().__init__(charge_point_id, websocket)
        self.csms = csms
        self.info = ChargePointInfo(id=charge_point_id)
        self._transaction_id_counter = 1000
        
    def _next_transaction_id(self) -> int:
        self._transaction_id_counter += 1
        return self._transaction_id_counter

    # ─────────────────────────────────────────────────────────
    # Boot & Status Messages
    # ─────────────────────────────────────────────────────────
    
    @on(BOOT_NOTIFICATION)
    async def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        """CP just booted - register it"""
        self.info.vendor = charge_point_vendor
        self.info.model = charge_point_model
        self.info.serial_number = kwargs.get('charge_point_serial_number', '')
        self.info.firmware_version = kwargs.get('firmware_version', '')
        
        log.info(f"[{self.id}] Boot: {charge_point_vendor} {charge_point_model}")
        
        # SECURITY NOTE: In production, validate the CP identity here
        # For the lab, we accept all connections (vulnerable by design)
        
        return call_result.BootNotification(
            current_time=datetime.now(timezone.utc).isoformat(),
            interval=300,  # Heartbeat interval in seconds
            status=RegistrationStatus.accepted
        )
    
    @on(HEARTBEAT)
    async def on_heartbeat(self):
        """CP heartbeat - proves it's alive"""
        self.info.last_heartbeat = datetime.now(timezone.utc)
        log.debug(f"[{self.id}] Heartbeat")
        return call_result.Heartbeat(
            current_time=datetime.now(timezone.utc).isoformat()
        )
    
    @on(STATUS_NOTIFICATION)
    async def on_status_notification(self, connector_id: int, error_code: str, status: str, **kwargs):
        """CP reporting connector status change"""
        self.info.status = status
        log.info(f"[{self.id}] Connector {connector_id}: {status} (error: {error_code})")
        
        # Broadcast to CSMS event listeners
        await self.csms.broadcast_event({
            'type': 'status_change',
            'charge_point_id': self.id,
            'connector_id': connector_id,
            'status': status,
            'error_code': error_code,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return call_result.StatusNotification()

    # ─────────────────────────────────────────────────────────
    # Authorization
    # ─────────────────────────────────────────────────────────
    
    @on(AUTHORIZE)
    async def on_authorize(self, id_tag: str):
        """
        CP asking if an ID tag (RFID) is authorized.
        
        SECURITY NOTE: This is a key attack surface.
        - Weak auth: accept all tags
        - No rate limiting
        - No tag validation
        """
        log.info(f"[{self.id}] Authorize request for tag: {id_tag}")
        
        # VULNERABLE: Accept any tag (for lab purposes)
        # In production, validate against database
        authorized = self.csms.authorize_tag(id_tag)
        
        return call_result.Authorize(
            id_tag_info={
                'status': AuthorizationStatus.accepted if authorized else AuthorizationStatus.invalid
            }
        )

    # ─────────────────────────────────────────────────────────
    # Transactions
    # ─────────────────────────────────────────────────────────
    
    @on(START_TRANSACTION)
    async def on_start_transaction(self, connector_id: int, id_tag: str, meter_start: int, timestamp: str, **kwargs):
        """
        CP reporting a charging session has started.
        
        SECURITY NOTE: 
        - Transaction ID can be predicted
        - No validation of meter_start
        - Timestamp from CP is trusted
        """
        transaction_id = self._next_transaction_id()
        
        session = ChargingSession(
            transaction_id=transaction_id,
            connector_id=connector_id,
            id_tag=id_tag,
            start_time=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
            meter_start=meter_start
        )
        self.info.sessions[transaction_id] = session
        
        log.info(f"[{self.id}] Transaction {transaction_id} started on connector {connector_id}")
        
        await self.csms.broadcast_event({
            'type': 'transaction_start',
            'charge_point_id': self.id,
            'transaction_id': transaction_id,
            'connector_id': connector_id,
            'id_tag': id_tag,
            'meter_start': meter_start,
            'timestamp': timestamp
        })
        
        return call_result.StartTransaction(
            transaction_id=transaction_id,
            id_tag_info={'status': AuthorizationStatus.accepted}
        )
    
    @on(STOP_TRANSACTION)
    async def on_stop_transaction(self, meter_stop: int, timestamp: str, transaction_id: int, **kwargs):
        """
        CP reporting a charging session has ended.
        
        SECURITY NOTE:
        - meter_stop value is trusted (billing fraud risk)
        - No validation against meter_start
        """
        session = self.info.sessions.get(transaction_id)
        energy_delivered = 0
        
        if session:
            energy_delivered = meter_stop - session.meter_start
            del self.info.sessions[transaction_id]
        
        log.info(f"[{self.id}] Transaction {transaction_id} stopped. Energy: {energy_delivered} Wh")
        
        await self.csms.broadcast_event({
            'type': 'transaction_stop',
            'charge_point_id': self.id,
            'transaction_id': transaction_id,
            'meter_stop': meter_stop,
            'energy_wh': energy_delivered,
            'timestamp': timestamp
        })
        
        return call_result.StopTransaction(
            id_tag_info={'status': AuthorizationStatus.accepted}
        )
    
    @on(METER_VALUES)
    async def on_meter_values(self, connector_id: int, meter_value: list, **kwargs):
        """
        CP sending periodic meter readings.
        
        SECURITY NOTE:
        - Values are trusted without verification
        - Can be spoofed for billing manipulation
        """
        transaction_id = kwargs.get('transaction_id')
        
        # Extract power/energy from meter values
        for mv in meter_value:
            sampled_values = mv.get('sampled_value', [])
            for sv in sampled_values:
                measurand = sv.get('measurand', 'Energy.Active.Import.Register')
                value = sv.get('value', '0')
                log.debug(f"[{self.id}] Meter: {measurand} = {value}")
        
        return call_result.MeterValues()

    # ─────────────────────────────────────────────────────────
    # Data Transfer (Custom Messages)
    # ─────────────────────────────────────────────────────────
    
    @on(DATA_TRANSFER)
    async def on_data_transfer(self, vendor_id: str, **kwargs):
        """
        Custom vendor-specific messages.
        
        SECURITY NOTE:
        - Arbitrary data can be injected
        - No validation of vendor_id
        """
        message_id = kwargs.get('message_id', '')
        data = kwargs.get('data', '')
        
        log.info(f"[{self.id}] DataTransfer from {vendor_id}: {message_id}")
        
        return call_result.DataTransfer(status='Accepted')

    # ─────────────────────────────────────────────────────────
    # CSMS-Initiated Commands (called by our API)
    # ─────────────────────────────────────────────────────────
    
    async def remote_start_transaction(self, id_tag: str, connector_id: int = 1) -> bool:
        """Tell CP to start charging"""
        try:
            request = call.RemoteStartTransaction(id_tag=id_tag, connector_id=connector_id)
            response = await self.call(request)
            return response.status == RemoteStartStopStatus.accepted
        except Exception as e:
            log.error(f"RemoteStartTransaction failed: {e}")
            return False
    
    async def remote_stop_transaction(self, transaction_id: int) -> bool:
        """Tell CP to stop charging"""
        try:
            request = call.RemoteStopTransaction(transaction_id=transaction_id)
            response = await self.call(request)
            return response.status == RemoteStartStopStatus.accepted
        except Exception as e:
            log.error(f"RemoteStopTransaction failed: {e}")
            return False
    
    async def reset(self, reset_type: str = "Soft") -> bool:
        """Reset the charge point"""
        try:
            request = call.Reset(type=ResetType(reset_type.lower()))
            response = await self.call(request)
            return response.status == ResetStatus.accepted
        except Exception as e:
            log.error(f"Reset failed: {e}")
            return False
    
    async def unlock_connector(self, connector_id: int = 1) -> bool:
        """Unlock a connector"""
        try:
            request = call.UnlockConnector(connector_id=connector_id)
            response = await self.call(request)
            return response.status == UnlockStatus.unlocked
        except Exception as e:
            log.error(f"UnlockConnector failed: {e}")
            return False
    
    async def change_availability(self, connector_id: int, availability_type: str) -> bool:
        """Change connector availability"""
        try:
            request = call.ChangeAvailability(
                connector_id=connector_id,
                type=AvailabilityType(availability_type.lower())
            )
            response = await self.call(request)
            return response.status == AvailabilityStatus.accepted
        except Exception as e:
            log.error(f"ChangeAvailability failed: {e}")
            return False


# ============================================================
# CSMS Server
# ============================================================

class CSMS:
    """
    Central System Management System
    Manages multiple Charge Points via OCPP WebSocket
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9000):
        self.host = host
        self.port = port
        self.charge_points: Dict[str, ChargePointHandler] = {}
        self.event_listeners: list = []
        
        # Simple auth database (VULNERABLE: hardcoded)
        self.authorized_tags = {
            "TAG001", "TAG002", "ADMIN", "TEST", 
            "EVCR001", "EVCR002", "RFID1234"
        }
    
    def authorize_tag(self, id_tag: str) -> bool:
        """
        Check if a tag is authorized.
        
        SECURITY FLAW: 
        - Hardcoded tags
        - No logging of failed attempts
        - Case sensitive comparison only
        """
        # VULNERABLE: Accept any tag containing "TEST" or "ADMIN"
        if "TEST" in id_tag.upper() or "ADMIN" in id_tag.upper():
            return True
        return id_tag in self.authorized_tags
    
    async def broadcast_event(self, event: dict):
        """Send event to all listeners (for integration with our backend)"""
        for listener in self.event_listeners:
            try:
                await listener(event)
            except Exception as e:
                log.error(f"Event listener error: {e}")
    
    async def handle_connection(self, websocket: ServerConnection):
        """
        Handle new WebSocket connection from a Charge Point.
        
        OCPP path format: /ocpp/<charge_point_id>
        or: /<charge_point_id>
        """
        # Extract charge point ID from path
        path = websocket.request.path if hasattr(websocket, 'request') else '/'
        charge_point_id = path.strip('/').split('/')[-1]
        
        if not charge_point_id:
            charge_point_id = f"CP-{id(websocket)}"
            log.warning(f"Connection without charge point ID, assigned: {charge_point_id}")
        
        remote_addr = websocket.remote_address if hasattr(websocket, 'remote_address') else 'unknown'
        log.info(f"New connection: {charge_point_id} from {remote_addr}")
        
        # Create handler for this charge point
        handler = ChargePointHandler(charge_point_id, websocket, self)
        self.charge_points[charge_point_id] = handler
        
        try:
            await handler.start()
        except websockets.exceptions.ConnectionClosed:
            log.info(f"Connection closed: {charge_point_id}")
        except Exception as e:
            log.error(f"Error handling {charge_point_id}: {e}")
        finally:
            if charge_point_id in self.charge_points:
                del self.charge_points[charge_point_id]
                log.info(f"Removed: {charge_point_id}")
    
    async def start(self):
        """Start the CSMS WebSocket server"""
        log.info(f"Starting CSMS on ws://{self.host}:{self.port}")
        log.info("OCPP endpoint: ws://<host>:<port>/<charge_point_id>")
        
        async with serve(
            self.handle_connection,
            self.host,
            self.port,
            subprotocols=['ocpp1.6']
        ):
            log.info("CSMS ready. Waiting for Charge Points...")
            await asyncio.Future()  # Run forever
    
    # ─────────────────────────────────────────────────────────
    # API Methods (for external control)
    # ─────────────────────────────────────────────────────────
    
    def get_charge_points(self) -> list:
        """List all connected charge points"""
        return [
            {
                'id': cp_id,
                'vendor': handler.info.vendor,
                'model': handler.info.model,
                'status': handler.info.status,
                'last_heartbeat': handler.info.last_heartbeat.isoformat() if handler.info.last_heartbeat else None,
                'active_sessions': len(handler.info.sessions)
            }
            for cp_id, handler in self.charge_points.items()
        ]
    
    def get_charge_point(self, charge_point_id: str) -> Optional[ChargePointHandler]:
        """Get a specific charge point handler"""
        return self.charge_points.get(charge_point_id)


# ============================================================
# Main
# ============================================================

# Global CSMS instance for HTTP API access
_csms_instance: CSMS | None = None

async def run_http_api(csms: CSMS, port: int = 9001):
    """
    Simple HTTP API for the CSMS.
    Runs alongside the WebSocket server.
    """
    global _csms_instance
    _csms_instance = csms
    
    from aiohttp import web
    
    async def get_status(request):
        return web.json_response({
            "status": "running",
            "connected_charge_points": len(csms.charge_points),
            "charge_points": list(csms.charge_points.keys())
        })
    
    async def list_charge_points(request):
        return web.json_response(csms.get_charge_points())
    
    async def get_charge_point(request):
        cp_id = request.match_info['cp_id']
        handler = csms.get_charge_point(cp_id)
        if not handler:
            return web.json_response({"error": "Not found"}, status=404)
        return web.json_response({
            "id": cp_id,
            "vendor": handler.info.vendor,
            "model": handler.info.model,
            "status": handler.info.status,
            "last_heartbeat": handler.info.last_heartbeat.isoformat() if handler.info.last_heartbeat else None,
            "sessions": [
                {
                    "transaction_id": s.transaction_id,
                    "connector_id": s.connector_id,
                    "id_tag": s.id_tag,
                    "start_time": s.start_time.isoformat(),
                    "meter_start": s.meter_start
                }
                for s in handler.info.sessions.values()
            ]
        })
    
    async def remote_start(request):
        try:
            data = await request.json()
            cp_id = data.get("charge_point_id")
            id_tag = data.get("id_tag", "RFID-001")
            connector_id = data.get("connector_id", 1)
            
            handler = csms.get_charge_point(cp_id)
            if not handler:
                return web.json_response({
                    "status": "Rejected", 
                    "error": f"Charge point {cp_id} not connected",
                    "connected": list(csms.charge_points.keys())
                }, status=404)
            
            success = await handler.remote_start_transaction(id_tag, connector_id)
            return web.json_response({
                "status": "Accepted" if success else "Rejected",
                "charge_point_id": cp_id,
                "id_tag": id_tag,
                "connector_id": connector_id
            })
        except Exception as e:
            log.error(f"remote_start error: {e}")
            return web.json_response({"status": "Error", "error": str(e)}, status=500)
    
    async def remote_stop(request):
        try:
            data = await request.json()
            cp_id = data.get("charge_point_id")
            transaction_id = data.get("transaction_id")
            
            handler = csms.get_charge_point(cp_id)
            if not handler:
                return web.json_response({"status": "Rejected", "error": "Charge point not connected"}, status=404)
            
            success = await handler.remote_stop_transaction(transaction_id)
            return web.json_response({
                "status": "Accepted" if success else "Rejected",
                "charge_point_id": cp_id,
                "transaction_id": transaction_id
            })
        except Exception as e:
            log.error(f"remote_stop error: {e}")
            return web.json_response({"status": "Error", "error": str(e)}, status=500)
    
    async def reset_cp(request):
        try:
            data = await request.json()
            cp_id = data.get("charge_point_id")
            reset_type = data.get("reset_type", "Soft")
            
            handler = csms.get_charge_point(cp_id)
            if not handler:
                return web.json_response({"status": "Rejected", "error": "Charge point not connected"}, status=404)
            
            success = await handler.reset(reset_type)
            return web.json_response({
                "status": "Accepted" if success else "Rejected",
                "charge_point_id": cp_id,
                "reset_type": reset_type
            })
        except Exception as e:
            log.error(f"reset error: {e}")
            return web.json_response({"status": "Error", "error": str(e)}, status=500)
    
    app = web.Application()
    app.router.add_get('/api/status', get_status)
    app.router.add_get('/api/charge-points', list_charge_points)
    app.router.add_get('/api/charge-points/{cp_id}', get_charge_point)
    app.router.add_post('/api/remote-start', remote_start)
    app.router.add_post('/api/remote-stop', remote_stop)
    app.router.add_post('/api/reset', reset_cp)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    log.info(f"HTTP API running on http://0.0.0.0:{port}")


async def main():
    csms = CSMS(host="0.0.0.0", port=9000)
    
    # Example event listener (logs all events)
    async def log_events(event):
        log.info(f"EVENT: {json.dumps(event)}")
    
    csms.event_listeners.append(log_events)
    
    # Start HTTP API in parallel
    await asyncio.gather(
        run_http_api(csms, port=9001),
        csms.start()
    )

if __name__ == "__main__":
    asyncio.run(main())
