# launch_cowork_setup.ps1
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: One-shot launcher that opens the OwlWatcher GUI in setup mode and
#          runs the Cowork install pipeline. Falls back to a headless console
#          run if PyQt6 is not available on this machine.

[CmdletBinding()]
param(
    [switch]$Headless,
    [switch]$DryRun,
    [switch]$SkipGuard
)

$ErrorActionPreference = "Stop"

# Configurable variables (no hardcoded values inline elsewhere)
$RepoRoot       = Split-Path -Parent $MyInvocation.MyCommand.Path
$Orchestrator   = Join-Path $RepoRoot "scripts\cowork_setup_orchestrator.py"
$GuardScript    = Join-Path $RepoRoot "scripts\publish_guard.ps1"
$VenvPython     = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$LogDir         = Join-Path $RepoRoot "logs"
$LaunchLog      = Join-Path $LogDir "launch_cowork_setup.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-LaunchLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File -FilePath $LaunchLog -Append -Encoding utf8
    Write-Host $Message
}

Write-LaunchLog "===== Cowork setup launch ====="
Write-LaunchLog "Repo:         $RepoRoot"
Write-LaunchLog "Orchestrator: $Orchestrator"
Write-LaunchLog "Headless:     $Headless"
Write-LaunchLog "DryRun:       $DryRun"

# Pre-flight: run the publish guard in install mode unless explicitly skipped.
# Soft mode (warnings allowed); hard mode is reserved for git-push.
if (-not $SkipGuard) {
    if (Test-Path $GuardScript) {
        Write-LaunchLog "Running publish guard in install mode..."
        & $GuardScript -Mode "install"
        if ($LASTEXITCODE -ne 0) {
            Write-LaunchLog "Publish guard returned non-zero. Aborting."
            exit $LASTEXITCODE
        }
    } else {
        Write-LaunchLog "Publish guard script not found, skipping."
    }
}

# Pick a Python interpreter: prefer the repo venv, then 'py' launcher, then 'python'.
$PythonExe = $null
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = (Get-Command py).Source
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = (Get-Command python).Source
} else {
    Write-LaunchLog "No Python interpreter found. Install Python 3.10+ and retry."
    exit 1
}
Write-LaunchLog "Python: $PythonExe"

# Build orchestrator argument list (variables, not positional magic strings)
$OrchestratorArgs = @($Orchestrator)
if ($Headless) { $OrchestratorArgs += "--headless" }
if ($DryRun)   { $OrchestratorArgs += "--dry-run" }

# Run the orchestrator. PyQt6 missing => fall back to headless mode automatically.
try {
    & $PythonExe @OrchestratorArgs
    $exitCode = $LASTEXITCODE
} catch {
    Write-LaunchLog "Orchestrator launch failed: $($_.Exception.Message)"
    exit 1
}

if ($exitCode -ne 0 -and -not $Headless) {
    Write-LaunchLog "GUI orchestrator failed. Retrying headless..."
    & $PythonExe $Orchestrator "--headless"
    $exitCode = $LASTEXITCODE
}

Write-LaunchLog "Setup orchestrator exited with code $exitCode."
exit $exitCode
