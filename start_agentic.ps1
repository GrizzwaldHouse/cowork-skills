# start_agentic.ps1
# Developer: Marcus Daley
# Date: 2026-05-02
# Purpose: Single-click launcher for both AgenticOS services.
#          Starts the FastAPI state bus (port 7842) and the Tailscale
#          WebSocket relay (port 7843) in separate titled windows so
#          each can be monitored or restarted independently.

$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\ClaudeSkills"

Write-Host "AgenticOS Launcher" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

# Confirm no stale process already holds 7842
$stale = Get-NetTCPConnection -LocalPort 7842 -State Listen -ErrorAction SilentlyContinue
if ($stale) {
    Write-Host "Port 7842 already in use (PID $($stale.OwningProcess)). Kill it first or it is already running." -ForegroundColor Yellow
    $choice = Read-Host "Kill existing process and restart? [y/N]"
    if ($choice -eq 'y') {
        Stop-Process -Id $stale.OwningProcess -Force
        Start-Sleep 1
        Write-Host "Killed PID $($stale.OwningProcess)." -ForegroundColor Green
    } else {
        Write-Host "Leaving existing server running. Starting relay only." -ForegroundColor Yellow
    }
}

# Launch AgenticOS state bus
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ProjectRoot'; `$host.UI.RawUI.WindowTitle = 'AgenticOS Server :7842'; python -m AgenticOS.agentic_server"
) -WindowStyle Normal

Write-Host "Started AgenticOS server  ->  http://0.0.0.0:7842" -ForegroundColor Green

Start-Sleep 2  # Give the server time to bind before relay tries to connect upstream

# Launch Tailscale WebSocket relay
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$ProjectRoot'; `$host.UI.RawUI.WindowTitle = 'AgenticOS Relay  :7843'; python -m AgenticOS.ws_relay"
) -WindowStyle Normal

Write-Host "Started Tailscale relay   ->  ws://0.0.0.0:7843" -ForegroundColor Green
Write-Host ""
Write-Host "iPhone URL:  ws://100.97.206.37:7843/?token=<your-auth-token>" -ForegroundColor Cyan
Write-Host "REST API:    http://100.97.206.37:7842/projects" -ForegroundColor Cyan
Write-Host ""
Write-Host "Both services running. Close their windows to stop them." -ForegroundColor Gray
