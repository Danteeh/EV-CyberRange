# EV-CyberRange Start Script
# Levanta EVerest + Backend + Frontend

param(
    [switch]$SkipEverest,
    [switch]$SkipBackend,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   EV-CyberRange - Iniciando Stack     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Verificar Docker
Write-Host "`n[1/4] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
    if (-not $dockerVersion) {
        throw "Docker daemon no esta corriendo"
    }
    Write-Host "  Docker OK (v$dockerVersion)" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker Desktop no esta corriendo" -ForegroundColor Red
    Write-Host "  Por favor abre Docker Desktop e intenta de nuevo" -ForegroundColor Red
    exit 1
}

# 2. Levantar EVerest
if (-not $SkipEverest) {
    Write-Host "`n[2/4] Levantando EVerest (AC Simulation)..." -ForegroundColor Yellow
    Push-Location "$ProjectRoot\everest"
    
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Host "  Descargando docker-compose.yml..." -ForegroundColor Gray
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/EVerest/everest-demo/main/docker-compose.everest-sil.yml" -OutFile "docker-compose.yml"
    }
    
    docker compose -p everest up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Fallo al levantar EVerest" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Esperar a que EVerest este listo
    Write-Host "  Esperando a que EVerest este listo..." -ForegroundColor Gray
    $maxWait = 60
    $waited = 0
    while ($waited -lt $maxWait) {
        $health = docker inspect --format='{{.State.Health.Status}}' everest-manager-1 2>$null
        if ($health -eq "healthy" -or $health -eq $null) {
            # Si no tiene healthcheck, verificamos que este running
            $state = docker inspect --format='{{.State.Status}}' everest-manager-1 2>$null
            if ($state -eq "running") {
                break
            }
        }
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host "." -NoNewline
    }
    Write-Host ""
    Write-Host "  EVerest OK - UI disponible en http://localhost:1880" -ForegroundColor Green
    Pop-Location
} else {
    Write-Host "`n[2/4] Saltando EVerest (--SkipEverest)" -ForegroundColor Gray
}

# 3. Levantar Backend
if (-not $SkipBackend) {
    Write-Host "`n[3/4] Levantando Backend FastAPI..." -ForegroundColor Yellow
    $backendPath = "$ProjectRoot\simulator\backend"
    
    # Verificar/crear venv
    if (-not (Test-Path "$backendPath\.venv")) {
        Write-Host "  Creando entorno virtual..." -ForegroundColor Gray
        Push-Location $backendPath
        python -m venv .venv
        & ".venv\Scripts\pip.exe" install -r requirements.txt --quiet
        Pop-Location
    }
    
    # Iniciar backend en background
    $env:MQTT_BROKER = "localhost"
    $env:MQTT_PORT = "1883"
    Start-Process -FilePath "$backendPath\.venv\Scripts\python.exe" `
                  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
                  -WorkingDirectory $backendPath `
                  -WindowStyle Hidden
    
    Write-Host "  Backend OK - API disponible en http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "`n[3/4] Saltando Backend (--SkipBackend)" -ForegroundColor Gray
}

# 4. Levantar Frontend
if (-not $SkipFrontend) {
    Write-Host "`n[4/4] Levantando Frontend React..." -ForegroundColor Yellow
    $frontendPath = "$ProjectRoot\frontend"
    
    # Verificar node_modules
    if (-not (Test-Path "$frontendPath\node_modules")) {
        Write-Host "  Instalando dependencias npm..." -ForegroundColor Gray
        Push-Location $frontendPath
        npm install --silent
        Pop-Location
    }
    
    # Iniciar frontend en background
    Start-Process -FilePath "cmd.exe" `
                  -ArgumentList "/c", "cd /d `"$frontendPath`" && npm run dev" `
                  -WindowStyle Hidden
    
    Write-Host "  Frontend OK - UI disponible en http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "`n[4/4] Saltando Frontend (--SkipFrontend)" -ForegroundColor Gray
}

# Resumen
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Stack Iniciado Correctamente!       " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Servicios:" -ForegroundColor White
Write-Host "    - EVerest UI:     http://localhost:1880" -ForegroundColor Gray
Write-Host "    - Backend API:    http://localhost:8000" -ForegroundColor Gray
Write-Host "    - Frontend:       http://localhost:5173" -ForegroundColor Gray
Write-Host "    - MQTT Broker:    localhost:1883" -ForegroundColor Gray
Write-Host ""
Write-Host "  Para parar: .\scripts\stop-all.ps1" -ForegroundColor Yellow
