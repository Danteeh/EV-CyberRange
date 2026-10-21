<#
.SYNOPSIS
    Start the EV-CyberRange Laboratory

.DESCRIPTION
    Starts all lab components: CSMS, Charge Points, Backend API, EVerest, MQTT, Node-RED, Kali Linux, and Frontend.

.PARAMETER Full
    Include additional Charge Points (3-6) with multiple connectors and DC fast chargers

.PARAMETER NoKali
    Skip Kali Linux (faster startup)

.PARAMETER Build
    Force rebuild of containers (usually not needed)

.EXAMPLE
    .\start.ps1           # Standard lab (2 CPs)
    .\start.ps1 -Full     # Full lab (6 CPs including DC fast chargers)
    .\start.ps1 -NoKali   # Without Kali attack host
#>

param(
    [switch]$Full,
    [switch]$NoKali,
    [switch]$Build
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "  ______     __     ______     __  __     ______     ______     ______     __   __     ______     ______    " -ForegroundColor Cyan
Write-Host " /\  ___\   /\ \   /\  ___\   /\ \_\ \   /\  == \   /\  __ \   /\  ___\   /\ '-.\ \   /\  ___\   /\  ___\   " -ForegroundColor Cyan
Write-Host " \ \  __\   \ \ \  \ \ \____  \ \____ \  \ \  __<   \ \  __ \  \ \ \__ \  \ \ \-.  \  \ \  __\   \ \___  \  " -ForegroundColor Cyan
Write-Host "  \ \_____\  \ \_\  \ \_____\  \/\_____\  \ \_\ \_\  \ \_\ \_\  \ \_____\  \ \_\\'\_\  \ \_____\  \/\_____\ " -ForegroundColor Cyan
Write-Host "   \/_____/   \/_/   \/_____/   \/_____/   \/_/ /_/   \/_/\/_/   \/_____/   \/_/ \/_/   \/_____/   \/_____/ " -ForegroundColor Cyan
Write-Host ""
Write-Host "  EV Charging Infrastructure Security Lab" -ForegroundColor Yellow
Write-Host "  OCPP 1.6 | EVerest | Cybersecurity Training" -ForegroundColor DarkGray
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

# Create shared-logs directory if not exists
if (-not (Test-Path "shared-logs")) {
    New-Item -ItemType Directory -Path "shared-logs" | Out-Null
}

# Build containers only if explicitly requested
if ($Build) {
    Write-Host "[*] Building containers (this may take a while)..." -ForegroundColor Yellow
    docker compose build 2>&1 | Out-Null
}

# Start core services first
Write-Host "[*] Starting core services (MQTT, CSMS, Backend)..." -ForegroundColor Gray
$null = docker compose up -d mqtt csms backend 2>&1

# Wait for CSMS to be healthy
Write-Host "[*] Waiting for CSMS to be healthy..." -ForegroundColor Gray
$timeout = 30
$start = Get-Date
while (((Get-Date) - $start).TotalSeconds -lt $timeout) {
    $csmsHealth = docker inspect --format='{{.State.Health.Status}}' evcr-csms 2>$null
    if ($csmsHealth -eq "healthy") { break }
    Start-Sleep -Seconds 2
}

# Start Charge Points
Write-Host "[*] Starting Charge Points..." -ForegroundColor Gray
$null = docker compose up -d chargepoint-1 chargepoint-2 2>&1

if ($Full) {
    Write-Host "[*] Starting additional Charge Points (3-6)..." -ForegroundColor Gray
    $null = docker compose --profile full up -d chargepoint-3 chargepoint-4 chargepoint-5 chargepoint-6 2>&1
}

# Start EVerest stack
Write-Host "[*] Starting EVerest stack..." -ForegroundColor Gray
$null = docker compose up -d everest-manager nodered 2>&1

# Start Kali if not skipped
if (-not $NoKali) {
    Write-Host "[*] Starting Kali attack host..." -ForegroundColor Yellow
    $null = docker compose up -d kali 2>&1
}

# Wait for all services
Write-Host "[*] Waiting for services to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Check for frontend dev server or start it
$frontendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) { $frontendRunning = $true }
} catch {}

if (-not $frontendRunning) {
    Write-Host "[*] Starting Frontend dev server..." -ForegroundColor Gray
    Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d $ProjectRoot\frontend && npm run dev" -WindowStyle Minimized
    Start-Sleep -Seconds 5
}

# Status check
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  LAB STATUS" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Check all services
$services = @{
    "MQTT Broker" = @{Port=1883; Color="Green"}
    "CSMS WebSocket" = @{Port=9000; Color="Green"}
    "CSMS REST API" = @{Port=9001; Color="Green"}
    "Backend API" = @{Port=8000; Color="Green"}
    "Node-RED (EVerest UI)" = @{Port=1880; Color="Green"}
    "Frontend" = @{Port=5173; Color="Cyan"}
}

if (-not $NoKali) {
    $services["Kali noVNC"] = @{Port=6080; Color="Red"}
}

foreach ($svc in $services.GetEnumerator()) {
    $ok = (Test-NetConnection -ComputerName localhost -Port $svc.Value.Port -WarningAction SilentlyContinue).TcpTestSucceeded
    $status = if ($ok) { "OK" } else { "STARTING..." }
    $color = if ($ok) { $svc.Value.Color } else { "Yellow" }
    $portStr = "($($svc.Value.Port))".PadRight(7)
    Write-Host "  $($svc.Key.PadRight(22)) $portStr $status" -ForegroundColor $color
}

# Count connected charge points
try {
    $cpData = Invoke-RestMethod -Uri "http://localhost:8000/api/ocpp/charge-points" -TimeoutSec 3 -ErrorAction SilentlyContinue
    $cpCount = $cpData.total
    Write-Host ""
    Write-Host "  Charge Points Connected: $cpCount" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "  Charge Points: Connecting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  ACCESS URLS" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Main Dashboard:      " -NoNewline; Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend API:         " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  CSMS API:            " -NoNewline; Write-Host "http://localhost:9001" -ForegroundColor Green
Write-Host "  Node-RED (EVerest):  " -NoNewline; Write-Host "http://localhost:1880" -ForegroundColor Green
if (-not $NoKali) {
    Write-Host "  Kali Linux (noVNC):  " -NoNewline; Write-Host "http://localhost:6080/vnc.html" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  QUICK COMMANDS" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Start charging:  " -NoNewline
Write-Host 'curl -X POST http://localhost:8000/api/ocpp/remote-start -H "Content-Type: application/json" -d "{\"charge_point_id\":\"EVCR-001\"}"' -ForegroundColor Yellow
Write-Host ""
Write-Host "  View OCPP logs:  " -NoNewline
Write-Host "Get-Content .\shared-logs\ocpp_traffic.log -Tail 20" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Stop lab:        " -NoNewline
Write-Host "docker compose down" -ForegroundColor DarkGray
Write-Host ""
