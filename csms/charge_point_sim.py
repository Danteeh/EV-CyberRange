"""
EV-CyberRange Charge Point Simulator
OCPP 1.6J Client that connects to our CSMS

Simulates a charging station with realistic behavior.
Can be controlled via MQTT to sync with EVerest simulation.
"""
import asyncio
import logging
import json
import random
from datetime import datetime, timezone
from typing import Optional

import paho.mqtt.client as mqtt
from ocpp.v16 import ChargePoint as CP
from ocpp.v16 import call, call_result
from ocpp.v16.enums import (
    RegistrationStatus, AuthorizationStatus, ChargePointStatus,
    ChargePointErrorCode, Action
)
from ocpp.routing import on, after

import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger('ChargePoint')


class ChargePointSimulator(CP):
    """
    Simulates an EVSE (Electric Vehicle Supply Equipment)
    Connects to CSMS via OCPP 1.6J WebSocket
    Supports multiple connectors per charge point
    """
    
    def __init__(self, charge_point_id: str, websocket, num_connectors: int = 1, max_power_kw: float = 11.0, mqtt_client: Optional[mqtt.Client] = None):
        super().__init__(charge_point_id, websocket)
        self.mqtt = mqtt_client
        self.registered = False
        self.num_connectors = num_connectors
        self.max_power_w = max_power_kw * 1000
        self.voltage = 230  # V
        
        # Per-connector state
        self.connectors = {}
        for i in range(1, num_connectors + 1):
            self.connectors[i] = {
                'status': ChargePointStatus.available,
                'transaction_id': None,
                'meter_value': 0,  # Wh
                'charging': False,
                'power_w': 0,
                'id_tag': None,
            }
        
        log.info(f"[{self.id}] Initialized with {num_connectors} connector(s), max {max_power_kw} kW")
        
    async def start(self):
        """Start the charge point - process messages and send BootNotification"""
        # Start the message handler in background first
        # This allows us to receive responses to our calls
        handler_task = asyncio.create_task(super().start())
        
        try:
            # Send boot notification
            response = await self.call(call.BootNotification(
                charge_point_vendor="EV-CyberRange",
                charge_point_model=f"EVCR-SIM-{self.num_connectors}C",
                charge_point_serial_number=self.id,
                firmware_version="2.0.0"
            ))
            
            if response.status == RegistrationStatus.accepted:
                log.info(f"[{self.id}] Registered with CSMS. Heartbeat interval: {response.interval}s")
                self.registered = True
                
                # Start heartbeat task
                asyncio.create_task(self._heartbeat_loop(response.interval))
                
                # Send initial status for ALL connectors
                for connector_id in self.connectors:
                    await self.send_status(ChargePointStatus.available, connector_id)
                
                # Wait for the handler to complete (runs forever until disconnected)
                await handler_task
            else:
                log.error(f"[{self.id}] Registration rejected: {response.status}")
                handler_task.cancel()
        except Exception as e:
            log.error(f"[{self.id}] Error during start: {e}")
            handler_task.cancel()
            raise
    
    async def _heartbeat_loop(self, interval: int):
        """Send periodic heartbeats"""
        while self.registered:
            await asyncio.sleep(interval)
            try:
                await self.call(call.Heartbeat())
                log.debug(f"[{self.id}] Heartbeat sent")
            except Exception as e:
                log.error(f"[{self.id}] Heartbeat failed: {e}")
                break
    
    async def send_status(self, status: ChargePointStatus, connector_id: int = 1, error_code: ChargePointErrorCode = ChargePointErrorCode.no_error):
        """Send status notification to CSMS"""
        if connector_id in self.connectors:
            self.connectors[connector_id]['status'] = status
        await self.call(call.StatusNotification(
            connector_id=connector_id,
            error_code=error_code.value,
            status=status.value
        ))
        log.info(f"[{self.id}] Connector {connector_id} Status: {status.value}")
    
    async def authorize(self, id_tag: str) -> bool:
        """Check if an ID tag is authorized"""
        response = await self.call(call.Authorize(id_tag=id_tag))
        return response.id_tag_info['status'] == AuthorizationStatus.accepted.value
    
    async def start_charging(self, id_tag: str, connector_id: int = 1) -> bool:
        """
        Start a charging session on a specific connector.
        
        1. Send Authorize
        2. Send StatusNotification (Preparing)
        3. Send StartTransaction
        4. Start sending MeterValues
        """
        if connector_id not in self.connectors:
            log.warning(f"[{self.id}] Invalid connector {connector_id}")
            return False
            
        conn = self.connectors[connector_id]
        
        if conn['charging']:
            log.warning(f"[{self.id}] Connector {connector_id} already charging")
            return False
        
        log.info(f"[{self.id}] Starting charge on connector {connector_id} for tag: {id_tag}")
        
        # Authorize first
        if not await self.authorize(id_tag):
            log.warning(f"[{self.id}] Authorization failed for {id_tag}")
            return False
        
        # Update status to Preparing
        await self.send_status(ChargePointStatus.preparing, connector_id)
        
        # Start transaction
        response = await self.call(call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=conn['meter_value'],
            timestamp=datetime.now(timezone.utc).isoformat()
        ))
        
        if response.id_tag_info['status'] == AuthorizationStatus.accepted.value:
            conn['transaction_id'] = response.transaction_id
            conn['charging'] = True
            conn['power_w'] = self.max_power_w
            conn['id_tag'] = id_tag
            
            # Update status to Charging
            await self.send_status(ChargePointStatus.charging, connector_id)
            
            # Start meter values loop for this connector
            asyncio.create_task(self._meter_values_loop(connector_id))
            
            log.info(f"[{self.id}] Transaction {conn['transaction_id']} started on connector {connector_id}")
            return True
        else:
            log.warning(f"[{self.id}] Transaction start rejected on connector {connector_id}")
            await self.send_status(ChargePointStatus.available, connector_id)
            return False
    
    async def stop_charging(self, connector_id: int = 1) -> bool:
        """Stop the charging session on a specific connector"""
        if connector_id not in self.connectors:
            log.warning(f"[{self.id}] Invalid connector {connector_id}")
            return False
            
        conn = self.connectors[connector_id]
        
        if not conn['transaction_id']:
            log.warning(f"[{self.id}] No active transaction on connector {connector_id}")
            return False
        
        log.info(f"[{self.id}] Stopping transaction {conn['transaction_id']} on connector {connector_id}")
        
        conn['charging'] = False
        conn['power_w'] = 0
        
        # Send StopTransaction
        await self.call(call.StopTransaction(
            meter_stop=conn['meter_value'],
            timestamp=datetime.now(timezone.utc).isoformat(),
            transaction_id=conn['transaction_id']
        ))
        
        # Update status
        await self.send_status(ChargePointStatus.finishing, connector_id)
        await asyncio.sleep(2)
        await self.send_status(ChargePointStatus.available, connector_id)
        
        log.info(f"[{self.id}] Transaction {conn['transaction_id']} stopped on connector {connector_id}. Total energy: {conn['meter_value']} Wh")
        conn['transaction_id'] = None
        conn['id_tag'] = None
        return True
    
    async def _meter_values_loop(self, connector_id: int = 1):
        """Send periodic meter values while charging"""
        conn = self.connectors.get(connector_id)
        if not conn:
            return
            
        while conn['charging']:
            await asyncio.sleep(10)  # Send every 10 seconds
            
            if not conn['charging']:
                break
            
            # Simulate energy consumption (power * time)
            # Add some noise for realism
            power_variation = random.uniform(0.95, 1.05)
            actual_power = conn['power_w'] * power_variation
            energy_increment = int(actual_power * (10 / 3600))  # Wh in 10 seconds
            conn['meter_value'] += energy_increment
            
            # Calculate current (P = V * I * sqrt(3) for 3-phase)
            current_a = actual_power / (self.voltage * 1.732)  # 3-phase
            
            # Send meter values
            await self.call(call.MeterValues(
                connector_id=connector_id,
                transaction_id=conn['transaction_id'],
                meter_value=[{
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'sampled_value': [
                        {
                            'value': str(conn['meter_value']),
                            'measurand': 'Energy.Active.Import.Register',
                            'unit': 'Wh'
                        },
                        {
                            'value': f"{actual_power:.0f}",
                            'measurand': 'Power.Active.Import',
                            'unit': 'W'
                        },
                        {
                            'value': f"{current_a:.1f}",
                            'measurand': 'Current.Import',
                            'unit': 'A'
                        },
                        {
                            'value': str(self.voltage),
                            'measurand': 'Voltage',
                            'unit': 'V'
                        }
                    ]
                }]
            ))
            
            log.debug(f"[{self.id}] Connector {connector_id} MeterValue: {conn['meter_value']} Wh, {actual_power:.0f} W")
    
    # ─────────────────────────────────────────────────────────
    # Handle CSMS-initiated messages
    # ─────────────────────────────────────────────────────────
    
    @on(Action.remote_start_transaction)
    async def on_remote_start(self, id_tag: str, **kwargs):
        """CSMS requests to start charging"""
        connector_id = kwargs.get('connector_id', 1)
        log.info(f"[{self.id}] Remote start requested for tag: {id_tag}")
        
        # Start charging in background
        asyncio.create_task(self.start_charging(id_tag, connector_id))
        
        return call_result.RemoteStartTransaction(status='Accepted')
    
    @on(Action.remote_stop_transaction)
    async def on_remote_stop(self, transaction_id: int):
        """CSMS requests to stop charging"""
        log.info(f"[{self.id}] Remote stop requested for transaction: {transaction_id}")
        
        # Find the connector with this transaction
        for conn_id, conn in self.connectors.items():
            if conn['transaction_id'] == transaction_id:
                asyncio.create_task(self.stop_charging(conn_id))
                return call_result.RemoteStopTransaction(status='Accepted')
        
        return call_result.RemoteStopTransaction(status='Rejected')
    
    @on(Action.reset)
    async def on_reset(self, type: str):
        """CSMS requests reset"""
        log.info(f"[{self.id}] Reset requested: {type}")
        # In a real implementation, this would restart the charge point
        return call_result.Reset(status='Accepted')
    
    @on(Action.unlock_connector)
    async def on_unlock(self, connector_id: int):
        """CSMS requests to unlock connector"""
        log.info(f"[{self.id}] Unlock requested for connector {connector_id}")
        return call_result.UnlockConnector(status='Unlocked')
    
    @on(Action.change_availability)
    async def on_change_availability(self, connector_id: int, type: str):
        """CSMS requests availability change"""
        log.info(f"[{self.id}] Availability change: connector {connector_id} -> {type}")
        return call_result.ChangeAvailability(status='Accepted')
    
    @on(Action.get_configuration)
    async def on_get_configuration(self, **kwargs):
        """CSMS requests configuration"""
        keys = kwargs.get('key', [])
        return call_result.GetConfiguration(
            configuration_key=[
                {"key": "HeartbeatInterval", "readonly": False, "value": "300"},
                {"key": "MeterValueSampleInterval", "readonly": False, "value": "10"},
                {"key": "NumberOfConnectors", "readonly": True, "value": str(self.num_connectors)},
                {"key": "ChargePointMaxPower", "readonly": True, "value": str(int(self.max_power_w))},
            ]
        )


async def connect_to_csms(csms_url: str, charge_point_id: str, num_connectors: int = 1, max_power_kw: float = 11.0):
    """Connect to CSMS and run the charge point"""
    log.info(f"Connecting to CSMS: {csms_url}/{charge_point_id}")
    log.info(f"Configuration: {num_connectors} connector(s), {max_power_kw} kW max power")
    import sys
    sys.stdout.flush()
    
    while True:
        try:
            log.info("Attempting WebSocket connection...")
            sys.stdout.flush()
            async with websockets.connect(
                f"{csms_url}/{charge_point_id}",
                subprotocols=['ocpp1.6']
            ) as ws:
                log.info(f"WebSocket connected! Creating ChargePointSimulator...")
                sys.stdout.flush()
                cp = ChargePointSimulator(charge_point_id, ws, num_connectors=num_connectors, max_power_kw=max_power_kw)
                log.info("Starting ChargePoint...")
                sys.stdout.flush()
                await cp.start()
        except Exception as e:
            import traceback
            log.error(f"Connection failed: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            log.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


async def main():
    import os
    
    csms_url = os.environ.get('CSMS_URL', 'ws://localhost:9000')
    charge_point_id = os.environ.get('CHARGE_POINT_ID', 'EVCR-001')
    num_connectors = int(os.environ.get('NUM_CONNECTORS', '1'))
    max_power_kw = float(os.environ.get('MAX_POWER_KW', '11'))
    
    await connect_to_csms(csms_url, charge_point_id, num_connectors, max_power_kw)


if __name__ == "__main__":
    asyncio.run(main())
