# EV-CyberRange Stop Script
# Para todos los servicios

$ErrorActionPreference = "SilentlyContinue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   EV-CyberRange - Parando Stack       " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Parar Frontend (proceso npm/node en puerto 5173)
Write-Host "`n[1/3] Parando Frontend..." -ForegroundColor Yellow
$frontendPid = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | 
               Select-Object -ExpandProperty OwningProcess -First 1
if ($frontendPid) {
    Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
    Write-Host "  Frontend parado (PID: $frontendPid)" -ForegroundColor Green
} else {
    Write-Host "  Frontend no estaba corriendo" -ForegroundColor Gray
}

# 2. Parar Backend (uvicorn en puerto 8000)
Write-Host "`n[2/3] Parando Backend..." -ForegroundColor Yellow
$backendPid = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
              Select-Object -ExpandProperty OwningProcess -First 1
if ($backendPid) {
    Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
    Write-Host "  Backend parado (PID: $backendPid)" -ForegroundColor Green
} else {
    Write-Host "  Backend no estaba corriendo" -ForegroundColor Gray
}

# 3. Parar EVerest (Docker)
Write-Host "`n[3/3] Parando EVerest..." -ForegroundColor Yellow
Push-Location "$ProjectRoot\everest"
if (Test-Path "docker-compose.yml") {
    docker compose -p everest down 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  EVerest containers parados" -ForegroundColor Green
    } else {
        Write-Host "  EVerest no estaba corriendo o Docker no disponible" -ForegroundColor Gray
    }
} else {
    Write-Host "  No hay docker-compose.yml en everest/" -ForegroundColor Gray
}
Pop-Location

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Stack Parado                        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
