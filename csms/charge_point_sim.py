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
from ocpp.v16 import call
from ocpp.v16.enums import (
    RegistrationStatus, AuthorizationStatus, ChargePointStatus,
    ChargePointErrorCode
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
    Syncs state with EVerest via MQTT
    """
    
    def __init__(self, charge_point_id: str, websocket, mqtt_client: Optional[mqtt.Client] = None):
        super().__init__(charge_point_id, websocket)
        self.mqtt = mqtt_client
        self.registered = False
        self.current_transaction_id: Optional[int] = None
        self.meter_value = 0  # Wh
        self.charging = False
        self.connector_status = ChargePointStatus.available
        
        # Simulation parameters
        self.power_w = 0  # Current charging power
        self.max_power_w = 11000  # 11 kW
        self.voltage = 230  # V
        
    async def start(self):
        """Start the charge point - send BootNotification first"""
        # Send boot notification
        response = await self.call(call.BootNotification(
            charge_point_vendor="EV-CyberRange",
            charge_point_model="EVCR-SIM-001",
            charge_point_serial_number=self.id,
            firmware_version="1.0.0"
        ))
        
        if response.status == RegistrationStatus.accepted:
            log.info(f"[{self.id}] Registered with CSMS. Heartbeat interval: {response.interval}s")
            self.registered = True
            
            # Start heartbeat task
            asyncio.create_task(self._heartbeat_loop(response.interval))
            
            # Send initial status
            await self.send_status(ChargePointStatus.available)
            
            # Start the message handler
            await super().start()
        else:
            log.error(f"[{self.id}] Registration rejected: {response.status}")
    
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
        self.connector_status = status
        await self.call(call.StatusNotification(
            connector_id=connector_id,
            error_code=error_code.value,
            status=status.value
        ))
        log.info(f"[{self.id}] Status: {status.value}")
    
    async def authorize(self, id_tag: str) -> bool:
        """Check if an ID tag is authorized"""
        response = await self.call(call.Authorize(id_tag=id_tag))
        return response.id_tag_info['status'] == AuthorizationStatus.accepted.value
    
    async def start_charging(self, id_tag: str, connector_id: int = 1) -> bool:
        """
        Start a charging session.
        
        1. Send Authorize
        2. Send StatusNotification (Preparing)
        3. Send StartTransaction
        4. Start sending MeterValues
        """
        log.info(f"[{self.id}] Starting charge for tag: {id_tag}")
        
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
            meter_start=self.meter_value,
            timestamp=datetime.now(timezone.utc).isoformat()
        ))
        
        if response.id_tag_info['status'] == AuthorizationStatus.accepted.value:
            self.current_transaction_id = response.transaction_id
            self.charging = True
            self.power_w = self.max_power_w
            
            # Update status to Charging
            await self.send_status(ChargePointStatus.charging, connector_id)
            
            # Start meter values loop
            asyncio.create_task(self._meter_values_loop(connector_id))
            
            log.info(f"[{self.id}] Transaction {self.current_transaction_id} started")
            return True
        else:
            log.warning(f"[{self.id}] Transaction start rejected")
            await self.send_status(ChargePointStatus.available, connector_id)
            return False
    
    async def stop_charging(self, connector_id: int = 1) -> bool:
        """Stop the current charging session"""
        if not self.current_transaction_id:
            log.warning(f"[{self.id}] No active transaction to stop")
            return False
        
        log.info(f"[{self.id}] Stopping transaction {self.current_transaction_id}")
        
        self.charging = False
        self.power_w = 0
        
        # Send StopTransaction
        await self.call(call.StopTransaction(
            meter_stop=self.meter_value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transaction_id=self.current_transaction_id
        ))
        
        # Update status
        await self.send_status(ChargePointStatus.finishing, connector_id)
        await asyncio.sleep(2)
        await self.send_status(ChargePointStatus.available, connector_id)
        
        log.info(f"[{self.id}] Transaction {self.current_transaction_id} stopped. Total energy: {self.meter_value} Wh")
        self.current_transaction_id = None
        return True
    
    async def _meter_values_loop(self, connector_id: int = 1):
        """Send periodic meter values while charging"""
        while self.charging:
            await asyncio.sleep(10)  # Send every 10 seconds
            
            if not self.charging:
                break
            
            # Simulate energy consumption (power * time)
            # Add some noise for realism
            power_variation = random.uniform(0.95, 1.05)
            actual_power = self.power_w * power_variation
            energy_increment = int(actual_power * (10 / 3600))  # Wh in 10 seconds
            self.meter_value += energy_increment
            
            # Calculate current (P = V * I * sqrt(3) for 3-phase)
            current_a = actual_power / (self.voltage * 1.732)  # 3-phase
            
            # Send meter values
            await self.call(call.MeterValues(
                connector_id=connector_id,
                transaction_id=self.current_transaction_id,
                meter_value=[{
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'sampled_value': [
                        {
                            'value': str(self.meter_value),
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
            
            log.debug(f"[{self.id}] MeterValue: {self.meter_value} Wh, {actual_power:.0f} W")
    
    # ─────────────────────────────────────────────────────────
    # Handle CSMS-initiated messages
    # ─────────────────────────────────────────────────────────
    
    @on('RemoteStartTransaction')
    async def on_remote_start(self, id_tag: str, **kwargs):
        """CSMS requests to start charging"""
        connector_id = kwargs.get('connector_id', 1)
        log.info(f"[{self.id}] Remote start requested for tag: {id_tag}")
        
        # Start charging in background
        asyncio.create_task(self.start_charging(id_tag, connector_id))
        
        return call.RemoteStartTransactionPayload(status='Accepted')
    
    @on('RemoteStopTransaction')
    async def on_remote_stop(self, transaction_id: int):
        """CSMS requests to stop charging"""
        log.info(f"[{self.id}] Remote stop requested for transaction: {transaction_id}")
        
        if transaction_id == self.current_transaction_id:
            asyncio.create_task(self.stop_charging())
            return call.RemoteStopTransactionPayload(status='Accepted')
        else:
            return call.RemoteStopTransactionPayload(status='Rejected')
    
    @on('Reset')
    async def on_reset(self, type: str):
        """CSMS requests reset"""
        log.info(f"[{self.id}] Reset requested: {type}")
        # In a real implementation, this would restart the charge point
        return call.ResetPayload(status='Accepted')
    
    @on('UnlockConnector')
    async def on_unlock(self, connector_id: int):
        """CSMS requests to unlock connector"""
        log.info(f"[{self.id}] Unlock requested for connector {connector_id}")
        return call.UnlockConnectorPayload(status='Unlocked')
    
    @on('ChangeAvailability')
    async def on_change_availability(self, connector_id: int, type: str):
        """CSMS requests availability change"""
        log.info(f"[{self.id}] Availability change: connector {connector_id} -> {type}")
        return call.ChangeAvailabilityPayload(status='Accepted')
    
    @on('GetConfiguration')
    async def on_get_configuration(self, **kwargs):
        """CSMS requests configuration"""
        return call.GetConfigurationPayload(
            configuration_key=[
                {'key': 'HeartbeatInterval', 'readonly': False, 'value': '300'},
                {'key': 'MeterValueSampleInterval', 'readonly': False, 'value': '10'},
                {'key': 'NumberOfConnectors', 'readonly': True, 'value': '1'},
            ]
        )


async def connect_to_csms(csms_url: str, charge_point_id: str):
    """Connect to CSMS and run the charge point"""
    log.info(f"Connecting to CSMS: {csms_url}/{charge_point_id}")
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
                cp = ChargePointSimulator(charge_point_id, ws)
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
    
    await connect_to_csms(csms_url, charge_point_id)


if __name__ == "__main__":
    asyncio.run(main())
