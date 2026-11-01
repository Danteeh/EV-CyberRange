"""
Vulnerable Charge Point Simulators for EV-CyberRange
Each class simulates a specific vendor's vulnerabilities based on real CVEs.

WARNING: These are INTENTIONALLY VULNERABLE for educational/lab purposes only.
DO NOT use in production environments.
"""
import asyncio
import logging
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from aiohttp import web

from ocpp.v16 import ChargePoint as CP
from ocpp.v16 import call, call_result
from ocpp.v16.enums import (
    RegistrationStatus, AuthorizationStatus, ChargePointStatus,
    ChargePointErrorCode, Action
)
from ocpp.routing import on

import websockets

log = logging.getLogger('VulnerableCP')


# ═══════════════════════════════════════════════════════════════════════════════
# BASE CLASS FOR VULNERABLE CHARGE POINTS
# ═══════════════════════════════════════════════════════════════════════════════

class VulnerableChargePoint(CP):
    """
    Base class for vulnerable charge point simulators.
    Extends OCPP functionality with intentional security flaws.
    """
    
    # Vulnerability flags - override in subclasses
    VENDOR_NAME = "Generic"
    MODEL_NAME = "Vulnerable-CP"
    FIRMWARE_VERSION = "1.0.0"
    CVE_LIST = []
    
    # Vulnerability toggles
    SKIP_AUTHORIZATION = False
    ALLOW_COMMAND_INJECTION = False
    EXPOSE_CREDENTIALS = False
    WEAK_AUTHENTICATION = False
    NO_INPUT_VALIDATION = False
    BUFFER_OVERFLOW_VULNERABLE = False
    
    def __init__(self, charge_point_id: str, websocket, http_port: int = None):
        super().__init__(charge_point_id, websocket)
        self.registered = False
        self.http_port = http_port
        self.http_app = None
        self.http_runner = None
        
        # State
        self.status = ChargePointStatus.available
        self.transaction_id = None
        self.meter_value = 0
        self.charging = False
        self.power_w = 0
        
        # Credentials (intentionally weak/exposed)
        self.admin_username = "admin"
        self.admin_password = "admin123"
        self.api_key = "EVSE-API-KEY-12345"
        
        log.info(f"[{self.id}] {self.VENDOR_NAME} {self.MODEL_NAME} initialized")
        log.info(f"[{self.id}] Vulnerabilities: {', '.join(self.CVE_LIST)}")
    
    async def start(self):
        """Start the charge point with HTTP server if configured"""
        # Start HTTP server for web vulnerabilities
        if self.http_port:
            asyncio.create_task(self._start_http_server())
        
        # Start OCPP message handler
        handler_task = asyncio.create_task(super().start())
        
        try:
            response = await self.call(call.BootNotification(
                charge_point_vendor=self.VENDOR_NAME,
                charge_point_model=self.MODEL_NAME,
                charge_point_serial_number=self.id,
                firmware_version=self.FIRMWARE_VERSION
            ))
            
            if response.status == RegistrationStatus.accepted:
                log.info(f"[{self.id}] Registered with CSMS")
                self.registered = True
                asyncio.create_task(self._heartbeat_loop(response.interval))
                await self.send_status(ChargePointStatus.available)
                await handler_task
            else:
                log.error(f"[{self.id}] Registration rejected")
                handler_task.cancel()
        except Exception as e:
            log.error(f"[{self.id}] Error: {e}")
            handler_task.cancel()
            raise
    
    async def _start_http_server(self):
        """Start vulnerable HTTP server"""
        self.http_app = web.Application()
        self._setup_http_routes()
        
        self.http_runner = web.AppRunner(self.http_app)
        await self.http_runner.setup()
        site = web.TCPSite(self.http_runner, '0.0.0.0', self.http_port)
        await site.start()
        log.info(f"[{self.id}] HTTP server on port {self.http_port}")
    
    def _setup_http_routes(self):
        """Override in subclasses to add vulnerable endpoints"""
        pass
    
    async def _heartbeat_loop(self, interval: int):
        while self.registered:
            await asyncio.sleep(interval)
            try:
                await self.call(call.Heartbeat())
            except:
                break
    
    async def send_status(self, status: ChargePointStatus):
        self.status = status
        await self.call(call.StatusNotification(
            connector_id=1,
            error_code=ChargePointErrorCode.no_error.value,
            status=status.value
        ))


# ═══════════════════════════════════════════════════════════════════════════════
# CVE-2024-11665 & CVE-2024-11666: Hardy Barth eCharge Salia
# RCE via PHP + MQTT without SSL verification
# ═══════════════════════════════════════════════════════════════════════════════

class HardyBarthChargePoint(VulnerableChargePoint):
    """
    Simulates Hardy Barth eCharge Salia vulnerabilities:
    - CVE-2024-11665: RCE via insecure PHP scripts (no auth)
    - CVE-2024-11666: MQTT command injection via disabled SSL
    """
    
    VENDOR_NAME = "Hardy Barth"
    MODEL_NAME = "eCharge Salia"
    FIRMWARE_VERSION = "1.51.4"  # Vulnerable version
    CVE_LIST = ["CVE-2024-11665", "CVE-2024-11666"]
    
    ALLOW_COMMAND_INJECTION = True
    SKIP_AUTHORIZATION = True
    
    def _setup_http_routes(self):
        """Setup vulnerable PHP-like endpoints"""
        self.http_app.router.add_get('/cgi-bin/status.php', self._handle_status)
        self.http_app.router.add_get('/cgi-bin/diag.php', self._handle_diag_rce)
        self.http_app.router.add_get('/api/config', self._handle_config)
        self.http_app.router.add_post('/api/mqtt/publish', self._handle_mqtt_inject)
        self.http_app.router.add_get('/', self._handle_index)
    
    async def _handle_index(self, request):
        """Landing page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>{self.VENDOR_NAME} {self.MODEL_NAME}</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>{self.VENDOR_NAME} {self.MODEL_NAME}</h1>
            <p>Charge Point ID: {self.id}</p>
            <p>Firmware: {self.FIRMWARE_VERSION}</p>
            <hr>
            <h3>Endpoints:</h3>
            <ul>
                <li><a href="/cgi-bin/status.php">/cgi-bin/status.php</a> - Status</li>
                <li><a href="/cgi-bin/diag.php?cmd=whoami">/cgi-bin/diag.php?cmd=...</a> - Diagnostics</li>
                <li><a href="/api/config">/api/config</a> - Configuration</li>
            </ul>
            <p style="color: red;"><b>WARNING: This device has known vulnerabilities (CVE-2024-11665, CVE-2024-11666)</b></p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_status(self, request):
        """Status endpoint - no auth required"""
        return web.json_response({
            "chargepoint_id": self.id,
            "vendor": self.VENDOR_NAME,
            "model": self.MODEL_NAME,
            "firmware": self.FIRMWARE_VERSION,
            "status": self.status.value,
            "charging": self.charging,
            "meter_wh": self.meter_value
        })
    
    async def _handle_diag_rce(self, request):
        """
        CVE-2024-11665: Remote Code Execution
        The cmd parameter is passed directly to shell without sanitization.
        Example: /cgi-bin/diag.php?cmd=id
        """
        cmd = request.query.get('cmd', 'echo "No command specified"')
        
        log.warning(f"[{self.id}] CVE-2024-11665 EXPLOIT: Command injection attempt: {cmd}")
        
        try:
            # VULNERABLE: Direct command execution without sanitization
            result = subprocess.run(
                cmd,
                shell=True,  # VULNERABLE: shell=True allows injection
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = "Command timed out"
        except Exception as e:
            output = f"Error: {str(e)}"
        
        return web.Response(text=f"""
<html>
<head><title>Diagnostics - {self.VENDOR_NAME}</title></head>
<body>
<h2>Diagnostic Output</h2>
<pre>{output}</pre>
<hr>
<form method="GET">
    <input type="text" name="cmd" placeholder="Enter command..." size="50">
    <button type="submit">Execute</button>
</form>
</body>
</html>
""", content_type='text/html')
    
    async def _handle_config(self, request):
        """Returns configuration including credentials - CVE-2024-11665"""
        return web.json_response({
            "network": {
                "ip": "192.168.1.100",
                "gateway": "192.168.1.1",
                "dns": "8.8.8.8"
            },
            "mqtt": {
                "broker": "mqtt://mqtt:1883",
                "ssl_verify": False,  # CVE-2024-11666: SSL verification disabled
                "username": "evse_mqtt",
                "password": "mqtt_pass_123"  # VULNERABLE: Credentials exposed
            },
            "admin": {
                "username": self.admin_username,
                "password": self.admin_password  # VULNERABLE: Credentials exposed
            },
            "api_key": self.api_key
        })
    
    async def _handle_mqtt_inject(self, request):
        """
        CVE-2024-11666: MQTT command injection via disabled SSL
        Accepts arbitrary MQTT publish commands without verification
        """
        try:
            data = await request.json()
            topic = data.get('topic', '')
            payload = data.get('payload', '')
            
            log.warning(f"[{self.id}] CVE-2024-11666 EXPLOIT: MQTT injection - topic: {topic}")
            
            # In a real attack, this would publish to the MQTT broker
            # without SSL verification, allowing MITM attacks
            return web.json_response({
                "status": "published",
                "topic": topic,
                "payload": payload,
                "ssl_verified": False,
                "warning": "SSL verification is DISABLED"
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    @on(Action.remote_start_transaction)
    async def on_remote_start(self, id_tag: str, **kwargs):
        """VULNERABLE: Accepts any id_tag without proper authorization"""
        log.warning(f"[{self.id}] CVE-2024-11665: Accepting remote start without auth validation")
        
        # VULNERABLE: No authorization check
        self.charging = True
        self.transaction_id = 1000 + hash(id_tag) % 9000
        self.status = ChargePointStatus.charging
        
        asyncio.create_task(self._fake_charging_session())
        return call_result.RemoteStartTransaction(status='Accepted')
    
    async def _fake_charging_session(self):
        """Simulate charging"""
        await self.send_status(ChargePointStatus.charging)
        while self.charging:
            await asyncio.sleep(5)
            self.meter_value += 500  # Add 500Wh every 5 seconds


# ═══════════════════════════════════════════════════════════════════════════════
# CVE-2018-7800 & CVE-2018-7801: Schneider Electric EVlink
# Code injection + Arbitrary command execution
# ═══════════════════════════════════════════════════════════════════════════════

class SchneiderEVlinkChargePoint(VulnerableChargePoint):
    """
    Simulates Schneider Electric EVlink vulnerabilities:
    - CVE-2018-7800: Code injection via vendor parameters
    - CVE-2018-7801: Arbitrary command execution with max privileges
    """
    
    VENDOR_NAME = "Schneider Electric"
    MODEL_NAME = "EVlink"
    FIRMWARE_VERSION = "3.2.0-12_v1"  # Vulnerable version
    CVE_LIST = ["CVE-2018-7800", "CVE-2018-7801"]
    
    ALLOW_COMMAND_INJECTION = True
    NO_INPUT_VALIDATION = True
    
    def _setup_http_routes(self):
        self.http_app.router.add_get('/', self._handle_index)
        self.http_app.router.add_get('/status', self._handle_status)
        self.http_app.router.add_post('/api/firmware/update', self._handle_firmware_inject)
        self.http_app.router.add_post('/api/execute', self._handle_execute)
    
    async def _handle_index(self, request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>{self.VENDOR_NAME} {self.MODEL_NAME}</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>{self.VENDOR_NAME} {self.MODEL_NAME}</h1>
            <p>Station ID: {self.id}</p>
            <p>Firmware: {self.FIRMWARE_VERSION}</p>
            <p style="color: red;"><b>Vulnerabilities: CVE-2018-7800, CVE-2018-7801</b></p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_status(self, request):
        return web.json_response({
            "station_id": self.id,
            "vendor": self.VENDOR_NAME,
            "model": self.MODEL_NAME,
            "status": self.status.value
        })
    
    async def _handle_firmware_inject(self, request):
        """
        CVE-2018-7800: Code injection in firmware update
        The firmware URL is not validated, allowing injection
        """
        try:
            data = await request.json()
            firmware_url = data.get('url', '')
            
            log.warning(f"[{self.id}] CVE-2018-7800 EXPLOIT: Code injection via firmware URL: {firmware_url}")
            
            # VULNERABLE: URL passed to shell without sanitization
            # In real exploit: curl "$(malicious_url); malicious_command"
            if ';' in firmware_url or '|' in firmware_url or '`' in firmware_url:
                # Simulate successful injection
                return web.json_response({
                    "status": "firmware_update_started",
                    "url": firmware_url,
                    "warning": "INJECTION DETECTED - Command would execute with root privileges"
                })
            
            return web.json_response({"status": "downloading", "url": firmware_url})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    async def _handle_execute(self, request):
        """
        CVE-2018-7801: Arbitrary command execution
        Executes commands with maximum privileges
        """
        try:
            data = await request.json()
            command = data.get('command', '')
            
            log.warning(f"[{self.id}] CVE-2018-7801 EXPLOIT: Command execution: {command}")
            
            # VULNERABLE: Direct execution
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return web.json_response({
                    "status": "executed",
                    "command": command,
                    "output": result.stdout,
                    "error": result.stderr,
                    "return_code": result.returncode
                })
            except subprocess.TimeoutExpired:
                return web.json_response({"error": "timeout"}, status=408)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    @on(Action.data_transfer)
    async def on_data_transfer(self, vendor_id: str, **kwargs):
        """
        CVE-2018-7800: Vendor ID used in eval() without sanitization
        """
        message_id = kwargs.get('message_id', '')
        data = kwargs.get('data', '')
        
        log.warning(f"[{self.id}] CVE-2018-7800 EXPLOIT: DataTransfer with vendor_id: {vendor_id}")
        
        # VULNERABLE: vendor_id passed to eval-like function
        # Simulating the injection by checking for code patterns
        if any(x in vendor_id for x in ['__', 'import', 'exec', 'eval', 'system']):
            log.critical(f"[{self.id}] CODE INJECTION ATTEMPT DETECTED in vendor_id!")
            return call_result.DataTransfer(
                status='Accepted',
                data=json.dumps({
                    "warning": "INJECTION_EXECUTED",
                    "vendor_id": vendor_id
                })
            )
        
        return call_result.DataTransfer(status='Accepted')


# ═══════════════════════════════════════════════════════════════════════════════
# CVE-2023-32249: Wallbox Pulsar Plus
# Unauthenticated API + No encryption
# ═══════════════════════════════════════════════════════════════════════════════

class WallboxPulsarChargePoint(VulnerableChargePoint):
    """
    Simulates Wallbox Pulsar Plus vulnerabilities:
    - CVE-2023-32249: Unencrypted API, weak authentication
    - Local API allows unauthorized control of charging
    """
    
    VENDOR_NAME = "Wallbox"
    MODEL_NAME = "Pulsar Plus"
    FIRMWARE_VERSION = "5.5.10"  # Vulnerable version
    CVE_LIST = ["CVE-2023-32249"]
    
    WEAK_AUTHENTICATION = True
    SKIP_AUTHORIZATION = True
    
    def _setup_http_routes(self):
        # All endpoints are unauthenticated - CVE-2023-32249
        self.http_app.router.add_get('/', self._handle_index)
        self.http_app.router.add_get('/api/status', self._handle_status)
        self.http_app.router.add_post('/api/charge/start', self._handle_start_charge)
        self.http_app.router.add_post('/api/charge/stop', self._handle_stop_charge)
        self.http_app.router.add_post('/api/current/set', self._handle_set_current)
        self.http_app.router.add_get('/api/config', self._handle_get_config)
        self.http_app.router.add_post('/api/config', self._handle_set_config)
    
    async def _handle_index(self, request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>{self.VENDOR_NAME} {self.MODEL_NAME}</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>{self.VENDOR_NAME} {self.MODEL_NAME}</h1>
            <p>Serial: {self.id}</p>
            <p>Firmware: {self.FIRMWARE_VERSION}</p>
            <h3>API Endpoints (NO AUTHENTICATION REQUIRED):</h3>
            <ul>
                <li>GET /api/status - Get charger status</li>
                <li>POST /api/charge/start - Start charging</li>
                <li>POST /api/charge/stop - Stop charging</li>
                <li>POST /api/current/set - Set charging current</li>
                <li>GET /api/config - Get configuration</li>
                <li>POST /api/config - Set configuration</li>
            </ul>
            <p style="color: red;"><b>CVE-2023-32249: No encryption, weak authentication</b></p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_status(self, request):
        """Unauthenticated status endpoint"""
        return web.json_response({
            "serial": self.id,
            "vendor": self.VENDOR_NAME,
            "model": self.MODEL_NAME,
            "firmware": self.FIRMWARE_VERSION,
            "status": self.status.value,
            "charging": self.charging,
            "current_amps": 32 if self.charging else 0,
            "power_kw": self.power_w / 1000,
            "energy_kwh": self.meter_value / 1000,
            "locked": False,
            "max_current": 32,
            "authentication_required": False  # CVE-2023-32249
        })
    
    async def _handle_start_charge(self, request):
        """CVE-2023-32249: Start charging without authentication"""
        log.warning(f"[{self.id}] CVE-2023-32249 EXPLOIT: Unauthenticated charge start")
        
        self.charging = True
        self.power_w = 7400  # 32A @ 230V
        self.status = ChargePointStatus.charging
        
        asyncio.create_task(self._charging_loop())
        
        return web.json_response({
            "status": "charging_started",
            "warning": "No authentication was required"
        })
    
    async def _handle_stop_charge(self, request):
        """CVE-2023-32249: Stop charging without authentication"""
        log.warning(f"[{self.id}] CVE-2023-32249 EXPLOIT: Unauthenticated charge stop")
        
        self.charging = False
        self.power_w = 0
        self.status = ChargePointStatus.available
        
        return web.json_response({
            "status": "charging_stopped",
            "energy_delivered_kwh": self.meter_value / 1000
        })
    
    async def _handle_set_current(self, request):
        """CVE-2023-32249: Set charging current without auth - potential safety issue"""
        try:
            data = await request.json()
            current = data.get('current', 32)
            
            log.warning(f"[{self.id}] CVE-2023-32249 EXPLOIT: Setting current to {current}A without auth")
            
            # VULNERABLE: No validation of current limits
            self.power_w = current * 230  # P = I * V
            
            return web.json_response({
                "status": "current_set",
                "current_amps": current,
                "power_w": self.power_w,
                "warning": "No authentication or safety validation performed"
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    async def _handle_get_config(self, request):
        """Expose all configuration including sensitive data"""
        return web.json_response({
            "serial": self.id,
            "wifi_ssid": "HomeNetwork",
            "wifi_password": "wifi_pass_123",  # VULNERABLE: Password exposed
            "api_key": self.api_key,
            "admin_password": self.admin_password,  # VULNERABLE
            "ocpp_url": "ws://csms:9000",
            "max_current": 32,
            "encryption_enabled": False  # CVE-2023-32249
        })
    
    async def _handle_set_config(self, request):
        """Allow changing configuration without auth"""
        try:
            data = await request.json()
            log.warning(f"[{self.id}] CVE-2023-32249 EXPLOIT: Config change without auth: {data}")
            return web.json_response({"status": "config_updated", "data": data})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    async def _charging_loop(self):
        """Simulate charging"""
        while self.charging:
            await asyncio.sleep(5)
            self.meter_value += int(self.power_w * 5 / 3600)


# ═══════════════════════════════════════════════════════════════════════════════
# CVE-2022-26132: ChargePoint Home Flex
# Stack overflow / DoS vulnerability
# ═══════════════════════════════════════════════════════════════════════════════

class ChargePointHomeFlexCP(VulnerableChargePoint):
    """
    Simulates ChargePoint Home Flex vulnerabilities:
    - CVE-2022-26132: Stack buffer overflow causing DoS
    """
    
    VENDOR_NAME = "ChargePoint"
    MODEL_NAME = "Home Flex"
    FIRMWARE_VERSION = "1.0.0.31"  # Vulnerable version
    CVE_LIST = ["CVE-2022-26132"]
    
    BUFFER_OVERFLOW_VULNERABLE = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crash_count = 0
        self.max_message_size = 1024  # Vulnerable buffer size
    
    def _setup_http_routes(self):
        self.http_app.router.add_get('/', self._handle_index)
        self.http_app.router.add_get('/status', self._handle_status)
        self.http_app.router.add_post('/api/message', self._handle_message)
        self.http_app.router.add_post('/api/firmware', self._handle_firmware)
    
    async def _handle_index(self, request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>{self.VENDOR_NAME} {self.MODEL_NAME}</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>{self.VENDOR_NAME} {self.MODEL_NAME}</h1>
            <p>Unit ID: {self.id}</p>
            <p>Firmware: {self.FIRMWARE_VERSION}</p>
            <p>Crash count: {self.crash_count}</p>
            <p style="color: red;"><b>CVE-2022-26132: Stack buffer overflow (DoS)</b></p>
            <p>Buffer size: {self.max_message_size} bytes</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_status(self, request):
        return web.json_response({
            "unit_id": self.id,
            "vendor": self.VENDOR_NAME,
            "model": self.MODEL_NAME,
            "firmware": self.FIRMWARE_VERSION,
            "status": self.status.value,
            "crash_count": self.crash_count,
            "vulnerable_buffer_size": self.max_message_size
        })
    
    async def _handle_message(self, request):
        """
        CVE-2022-26132: Stack buffer overflow
        Messages larger than buffer size cause crash
        """
        try:
            data = await request.read()
            message_size = len(data)
            
            if message_size > self.max_message_size:
                self.crash_count += 1
                log.critical(f"[{self.id}] CVE-2022-26132 EXPLOIT: Buffer overflow! Size: {message_size} > {self.max_message_size}")
                log.critical(f"[{self.id}] SIMULATED CRASH #{self.crash_count}")
                
                return web.json_response({
                    "error": "STACK_BUFFER_OVERFLOW",
                    "message_size": message_size,
                    "buffer_size": self.max_message_size,
                    "crash_count": self.crash_count,
                    "status": "DEVICE_CRASHED_SIMULATED"
                }, status=500)
            
            return web.json_response({
                "status": "message_processed",
                "size": message_size
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    async def _handle_firmware(self, request):
        """Firmware update also vulnerable to overflow"""
        data = await request.read()
        if len(data) > self.max_message_size * 10:
            self.crash_count += 1
            log.critical(f"[{self.id}] CVE-2022-26132: Firmware buffer overflow!")
            return web.Response(status=500, text="CRASH: Buffer overflow in firmware handler")
        return web.json_response({"status": "firmware_received"})
    
    @on(Action.data_transfer)
    async def on_data_transfer(self, vendor_id: str, **kwargs):
        """OCPP DataTransfer also vulnerable to overflow"""
        data = kwargs.get('data', '')
        
        if len(data) > self.max_message_size:
            self.crash_count += 1
            log.critical(f"[{self.id}] CVE-2022-26132: OCPP DataTransfer overflow! Size: {len(data)}")
            # Simulate crash by returning error
            return call_result.DataTransfer(
                status='Rejected',
                data=json.dumps({"error": "BUFFER_OVERFLOW", "crash_count": self.crash_count})
            )
        
        return call_result.DataTransfer(status='Accepted')


# ═══════════════════════════════════════════════════════════════════════════════
# CVE-2024-43659: Generic EV Charger Web Interface
# Exposed superuser credentials
# ═══════════════════════════════════════════════════════════════════════════════

class GenericWebVulnerableCP(VulnerableChargePoint):
    """
    Simulates generic EV charger web interface vulnerabilities:
    - CVE-2024-43659: Exposed superuser credentials
    - Full device compromise via credential exposure
    """
    
    VENDOR_NAME = "Generic EV"
    MODEL_NAME = "WebConnect Pro"
    FIRMWARE_VERSION = "2.1.0"
    CVE_LIST = ["CVE-2024-43659"]
    
    EXPOSE_CREDENTIALS = True
    WEAK_AUTHENTICATION = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Intentionally weak/default credentials
        self.root_password = "root123"
        self.debug_enabled = True
    
    def _setup_http_routes(self):
        self.http_app.router.add_get('/', self._handle_index)
        self.http_app.router.add_get('/status', self._handle_status)
        self.http_app.router.add_get('/api/debug', self._handle_debug)
        self.http_app.router.add_get('/api/system/info', self._handle_system_info)
        self.http_app.router.add_get('/backup/config.tar.gz', self._handle_backup)
        self.http_app.router.add_post('/api/login', self._handle_login)
    
    async def _handle_index(self, request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>{self.VENDOR_NAME} {self.MODEL_NAME}</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>{self.VENDOR_NAME} {self.MODEL_NAME}</h1>
            <p>Device ID: {self.id}</p>
            <p>Firmware: {self.FIRMWARE_VERSION}</p>
            <h3>Login</h3>
            <form action="/api/login" method="POST">
                <input type="text" name="username" placeholder="Username"><br><br>
                <input type="password" name="password" placeholder="Password"><br><br>
                <button type="submit">Login</button>
            </form>
            <p style="color: red;"><b>CVE-2024-43659: Superuser credentials exposed</b></p>
            <p>Hint: Check /api/debug or /backup/config.tar.gz</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_status(self, request):
        return web.json_response({
            "device_id": self.id,
            "vendor": self.VENDOR_NAME,
            "model": self.MODEL_NAME,
            "status": self.status.value,
            "debug_mode": self.debug_enabled
        })
    
    async def _handle_debug(self, request):
        """
        CVE-2024-43659: Debug endpoint exposes credentials
        """
        log.warning(f"[{self.id}] CVE-2024-43659 EXPLOIT: Debug endpoint accessed - credentials exposed!")
        
        return web.json_response({
            "debug_info": {
                "device_id": self.id,
                "uptime": 123456,
                "memory_free": 45678,
                "cpu_usage": 23
            },
            "credentials": {  # VULNERABLE: Credentials in debug output
                "admin_user": self.admin_username,
                "admin_pass": self.admin_password,
                "root_user": "root",
                "root_pass": self.root_password,
                "api_key": self.api_key
            },
            "network": {
                "ip": "192.168.1.150",
                "mac": "AA:BB:CC:DD:EE:FF",
                "ssid": "EVCharger_Network",
                "wifi_password": "ev_wifi_123"
            },
            "warning": "DEBUG MODE ENABLED - CREDENTIALS VISIBLE"
        })
    
    async def _handle_system_info(self, request):
        """System info with sensitive data"""
        return web.json_response({
            "hostname": f"evcharger-{self.id}",
            "kernel": "Linux 4.9.0",
            "users": [
                {"name": "root", "uid": 0, "shell": "/bin/bash"},
                {"name": "admin", "uid": 1000, "shell": "/bin/bash"}
            ],
            "services": ["sshd", "httpd", "ocpp-client", "mqtt-agent"],
            "ssh_enabled": True,
            "ssh_port": 22,
            "ssh_root_login": True  # VULNERABLE: Root SSH enabled
        })
    
    async def _handle_backup(self, request):
        """
        CVE-2024-43659: Backup file contains cleartext credentials
        """
        log.warning(f"[{self.id}] CVE-2024-43659 EXPLOIT: Backup downloaded with cleartext credentials!")
        
        # Simulate a config backup file content
        backup_content = f"""
# EV Charger Configuration Backup
# Device: {self.id}
# WARNING: This file contains sensitive credentials!

[admin]
username = {self.admin_username}
password = {self.admin_password}

[root]
username = root
password = {self.root_password}

[api]
key = {self.api_key}

[wifi]
ssid = EVCharger_Network
password = ev_wifi_123

[ocpp]
url = ws://csms:9000/{self.id}
auth_key = ocpp_auth_12345
"""
        return web.Response(
            text=backup_content,
            content_type='application/octet-stream',
            headers={'Content-Disposition': 'attachment; filename="config.tar.gz"'}
        )
    
    async def _handle_login(self, request):
        """Login with weak credential checking"""
        try:
            data = await request.post()
            username = data.get('username', '')
            password = data.get('password', '')
            
            # VULNERABLE: Weak authentication
            if (username == self.admin_username and password == self.admin_password) or \
               (username == 'root' and password == self.root_password):
                return web.json_response({
                    "status": "authenticated",
                    "token": "ADMIN_TOKEN_12345",  # VULNERABLE: Static token
                    "role": "admin" if username == 'admin' else "root"
                })
            
            return web.json_response({"status": "failed", "error": "Invalid credentials"}, status=401)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════════════════
# CVE-2025-12357: ISO 15118-2 MitM
# Man-in-the-Middle attack on charging communication
# ═══════════════════════════════════════════════════════════════════════════════

class ISO15118VulnerableCP(VulnerableChargePoint):
    """
    Simulates ISO 15118-2 MitM vulnerabilities:
    - CVE-2025-12357: Signal attenuation manipulation for traffic interception
    - No certificate verification in TLS
    """
    
    VENDOR_NAME = "ISO15118"
    MODEL_NAME = "PnC Gateway"
    FIRMWARE_VERSION = "1.0.0"
    CVE_LIST = ["CVE-2025-12357"]
    
    NO_INPUT_VALIDATION = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tls_verify = False  # VULNERABLE
        self.certificates = {
            "root_ca": "FAKE_ROOT_CA_CERT",
            "device_cert": "FAKE_DEVICE_CERT",
            "private_key": "FAKE_PRIVATE_KEY_EXPOSED"  # VULNERABLE
        }
    
    def _setup_http_routes(self):
        self.http_app.router.add_get('/', self._handle_index)
        self.http_app.router.add_get('/api/v2g/status', self._handle_v2g_status)
        self.http_app.router.add_get('/api/certificates', self._handle_certs)
        self.http_app.router.add_post('/api/v2g/session', self._handle_v2g_session)
    
    async def _handle_index(self, request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>{self.VENDOR_NAME} {self.MODEL_NAME}</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>{self.VENDOR_NAME} {self.MODEL_NAME}</h1>
            <p>Device: {self.id}</p>
            <p>TLS Certificate Verification: <b style="color:red">DISABLED</b></p>
            <p style="color: red;"><b>CVE-2025-12357: MitM vulnerability in ISO 15118-2</b></p>
            <h3>Attack Vector:</h3>
            <ol>
                <li>Signal attenuation manipulation during SLAC</li>
                <li>TLS connection without certificate verification</li>
                <li>Intercept V2G communication messages</li>
            </ol>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_v2g_status(self, request):
        return web.json_response({
            "device_id": self.id,
            "iso15118_version": "15118-2:2014",
            "tls_enabled": True,
            "tls_verify": self.tls_verify,  # VULNERABLE: False
            "pnc_enabled": True,
            "slac_status": "ready",
            "warning": "TLS certificate verification is DISABLED"
        })
    
    async def _handle_certs(self, request):
        """
        CVE-2025-12357: Certificates exposed including private key
        """
        log.warning(f"[{self.id}] CVE-2025-12357 EXPLOIT: Certificates/private key exposed!")
        
        return web.json_response({
            "certificates": self.certificates,
            "warning": "PRIVATE KEY EXPOSED - MitM POSSIBLE"
        })
    
    async def _handle_v2g_session(self, request):
        """
        Simulates V2G session establishment - vulnerable to MitM
        """
        try:
            data = await request.json()
            
            log.warning(f"[{self.id}] CVE-2025-12357: V2G session without proper TLS verification")
            
            return web.json_response({
                "session_id": "V2G-" + self.id + "-12345",
                "status": "established",
                "tls_verified": False,
                "mitm_possible": True,
                "contract_id": data.get('contract_id', 'UNKNOWN'),
                "warning": "Session established WITHOUT certificate verification"
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION - Create charge points by type
# ═══════════════════════════════════════════════════════════════════════════════

VULNERABLE_CP_TYPES = {
    "hardy_barth": HardyBarthChargePoint,
    "schneider": SchneiderEVlinkChargePoint,
    "wallbox": WallboxPulsarChargePoint,
    "chargepoint": ChargePointHomeFlexCP,
    "generic_web": GenericWebVulnerableCP,
    "iso15118": ISO15118VulnerableCP,
}

def create_vulnerable_cp(cp_type: str, charge_point_id: str, websocket, http_port: int = None):
    """Factory function to create vulnerable charge points"""
    if cp_type not in VULNERABLE_CP_TYPES:
        raise ValueError(f"Unknown CP type: {cp_type}. Available: {list(VULNERABLE_CP_TYPES.keys())}")
    
    return VULNERABLE_CP_TYPES[cp_type](charge_point_id, websocket, http_port)


async def run_vulnerable_cp(csms_url: str, cp_type: str, charge_point_id: str, http_port: int = None):
    """Connect a vulnerable charge point to the CSMS"""
    log.info(f"Starting {cp_type} charge point: {charge_point_id}")
    
    while True:
        try:
            async with websockets.connect(
                f"{csms_url}/{charge_point_id}",
                subprotocols=['ocpp1.6']
            ) as ws:
                cp = create_vulnerable_cp(cp_type, charge_point_id, ws, http_port)
                await cp.start()
        except Exception as e:
            log.error(f"[{charge_point_id}] Connection error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python vulnerable_charge_points.py <csms_url> <cp_type> <cp_id> [http_port]")
        print(f"Available types: {list(VULNERABLE_CP_TYPES.keys())}")
        sys.exit(1)
    
    csms_url = sys.argv[1]
    cp_type = sys.argv[2]
    cp_id = sys.argv[3]
    http_port = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    asyncio.run(run_vulnerable_cp(csms_url, cp_type, cp_id, http_port))
