<#
.SYNOPSIS
    Start the EV-CyberRange Laboratory

.DESCRIPTION
    Starts all lab components: EVerest (EVSE simulator), MQTT, Node-RED UI, and Kali Linux attack host.

.PARAMETER NoKali
    Skip Kali Linux (faster startup, ~2 min vs ~5 min first time)

.EXAMPLE
    .\start.ps1
    .\start.ps1 -NoKali
#>

param(
    [switch]$NoKali
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ______     __     ______     __  __     ______     ______     ______     __   __     ______     ______    " -ForegroundColor Cyan
Write-Host " /\  ___\   /\ \   /\  ___\   /\ \_\ \   /\  == \   /\  __ \   /\  ___\   /\ '-.\ \   /\  ___\   /\  ___\   " -ForegroundColor Cyan
Write-Host " \ \  __\   \ \ \  \ \ \____  \ \____ \  \ \  __<   \ \  __ \  \ \ \__ \  \ \ \-.  \  \ \  __\   \ \___  \  " -ForegroundColor Cyan
Write-Host "  \ \_____\  \ \_\  \ \_____\  \/\_____\  \ \_\ \_\  \ \_\ \_\  \ \_____\  \ \_\\'\_\  \ \_____\  \/\_____\ " -ForegroundColor Cyan
Write-Host "   \/_____/   \/_/   \/_____/   \/_____/   \/_/ /_/   \/_/\/_/   \/_____/   \/_/ \/_/   \/_____/   \/_____/ " -ForegroundColor Cyan
Write-Host ""
Write-Host "  EV Charging Infrastructure Security Lab" -ForegroundColor Yellow
Write-Host ""

# Check Docker
Write-Host "[*] Checking Docker..." -ForegroundColor Gray
try {
    $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
    if (-not $dockerVersion) { throw "Docker not running" }
    Write-Host "    Docker Engine $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "    ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "    Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Set working directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }
Set-Location $ProjectRoot

# Determine services
if ($NoKali) {
    Write-Host "[*] Starting lab WITHOUT Kali (use -NoKali:$false for full lab)" -ForegroundColor Yellow
    $services = "mqtt", "everest-manager", "nodered"
} else {
    Write-Host "[*] Starting full lab (first run builds Kali ~5 min)" -ForegroundColor Yellow
    $services = $null  # All services
}

# Pull/build and start
Write-Host "[*] Starting containers..." -ForegroundColor Gray
if ($services) {
    docker compose up -d $services
} else {
    docker compose up -d
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "    ERROR: Failed to start containers" -ForegroundColor Red
    Write-Host "    Check: docker compose logs" -ForegroundColor Yellow
    exit 1
}

# Wait for services
Write-Host "[*] Waiting for services to initialize..." -ForegroundColor Gray
$timeout = 60
$start = Get-Date

while (((Get-Date) - $start).TotalSeconds -lt $timeout) {
    Start-Sleep -Seconds 3
    
    $mqttOk = (Test-NetConnection -ComputerName localhost -Port 1883 -WarningAction SilentlyContinue).TcpTestSucceeded
    $noderedOk = (Test-NetConnection -ComputerName localhost -Port 1880 -WarningAction SilentlyContinue).TcpTestSucceeded
    
    if ($mqttOk -and $noderedOk) { break }
    Write-Host "    Waiting... (MQTT: $mqttOk, Node-RED: $noderedOk)" -ForegroundColor Gray
}

# Status
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  LAB STATUS" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

$mqttOk = (Test-NetConnection -ComputerName localhost -Port 1883 -WarningAction SilentlyContinue).TcpTestSucceeded
$noderedOk = (Test-NetConnection -ComputerName localhost -Port 1880 -WarningAction SilentlyContinue).TcpTestSucceeded
$kaliOk = (Test-NetConnection -ComputerName localhost -Port 6080 -WarningAction SilentlyContinue).TcpTestSucceeded

Write-Host ""
$mqttStatus = if ($mqttOk) { "OK" } else { "FAILED" }
$mqttColor = if ($mqttOk) { "Green" } else { "Red" }
Write-Host "  MQTT Broker (1883):      $mqttStatus" -ForegroundColor $mqttColor

$noderedStatus = if ($noderedOk) { "OK" } else { "FAILED" }
$noderedColor = if ($noderedOk) { "Green" } else { "Red" }
Write-Host "  Node-RED UI (1880):      $noderedStatus" -ForegroundColor $noderedColor

if (-not $NoKali) {
    $kaliStatus = if ($kaliOk) { "OK" } else { "STARTING..." }
    $kaliColor = if ($kaliOk) { "Green" } else { "Yellow" }
    Write-Host "  Kali Attack Host (6080): $kaliStatus" -ForegroundColor $kaliColor
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  ACCESS URLS" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  EVSE Control Panel:  " -NoNewline; Write-Host "http://localhost:1880/ui" -ForegroundColor Cyan
Write-Host "  Node-RED Editor:     " -NoNewline; Write-Host "http://localhost:1880" -ForegroundColor Cyan
if (-not $NoKali) {
    Write-Host "  Kali Linux (noVNC):  " -NoNewline; Write-Host "http://localhost:6080/vnc.html" -ForegroundColor Red
}
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  QUICK START" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Open EVSE Control Panel and click 'Plug In'" -ForegroundColor White
Write-Host "  2. Open Kali Linux and run attack tools:" -ForegroundColor White
Write-Host ""
Write-Host "     # Scan for EVSE vulnerabilities" -ForegroundColor Gray
Write-Host "     /opt/attack-tools/bin/python3 /root/tools/evse_scanner.py --mqtt-host everest-mqtt --deep" -ForegroundColor Yellow
Write-Host ""
Write-Host "     # Monitor charging sessions" -ForegroundColor Gray
Write-Host "     /opt/attack-tools/bin/python3 /root/tools/session_hijacker.py --target everest-mqtt --mode monitor" -ForegroundColor Yellow
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Stop lab:  docker compose down" -ForegroundColor DarkGray
Write-Host "  View logs: docker compose logs -f" -ForegroundColor DarkGray
Write-Host ""
