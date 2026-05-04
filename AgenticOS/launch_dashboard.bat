@echo off
REM AgenticOS Command Center Launcher
REM Developer: Marcus Daley
REM Date: 2026-05-02
REM Purpose: One-click launcher for the AgenticOS dashboard window.
REM          Delegates to the repo-root PowerShell launcher so desktop
REM          shortcuts, autostart, and manual launches use the same
REM          uv-managed PyQt runtime path.

cd /d "C:\ClaudeSkills"
start "AgenticOS Command Center" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\ClaudeSkills\launch_agentic_os.ps1"
