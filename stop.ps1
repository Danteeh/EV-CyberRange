<#
.SYNOPSIS
    Stop the EV-CyberRange Laboratory

.PARAMETER KeepVolumes
    Keep Docker volumes (preserves logs and data)

.EXAMPLE
    .\stop.ps1
    .\stop.ps1 -KeepVolumes
#>

param(
    [switch]$KeepVolumes
)

Write-Host ""
Write-Host "  Stopping EV-CyberRange Lab..." -ForegroundColor Yellow
Write-Host ""

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }
Set-Location $ProjectRoot

# Stop frontend dev server if running (kill by port)
$frontendConn = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($frontendConn) {
    Write-Host "[*] Stopping Frontend dev server (port 5173)..." -ForegroundColor Gray
    $frontendConn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

# Stop all containers
Write-Host "[*] Stopping Docker containers..." -ForegroundColor Gray
if ($KeepVolumes) {
    docker compose --profile full down 2>$null
} else {
    docker compose --profile full down -v 2>$null
}

Write-Host ""
Write-Host "  Lab stopped." -ForegroundColor Green
Write-Host "  Restart with: .\start.ps1" -ForegroundColor DarkGray
Write-Host ""
