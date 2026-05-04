# launch_agentic_os.ps1
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Top-level PowerShell entry point that launches the
#          AgenticOS Command Center dashboard. Resolves the Python
#          runtime, sets PYTHONPATH so the AgenticOS package is
#          importable, appends a timestamped launch record to a
#          long-running log file, and invokes the PyQt launcher via
#          "python -m AgenticOS.launch_dashboard". The older WPF
#          launcher remains in the repo for reference, but the desktop
#          shortcut uses PyQt because it has proven reliable on this
#          workstation without pythonnet/WPF assembly failures.

[CmdletBinding()]
param(
    # Allow callers (CI, the registry Run key, a desktop shortcut) to
    # override the interpreter without editing this file. When omitted,
    # the launcher prefers uv with Python 3.13 because pythonnet does
    # not currently support the Python 3.14 ABI.
    [string] $PythonExe = $null,

    # Pass-through to override the default repository root if the
    # script is ever executed from a clone in a non-standard location.
    [string] $RepoRoot = "C:\ClaudeSkills"
)

# Stop on the first error so a misconfigured environment surfaces
# loudly rather than silently launching nothing.
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Path constants
#
# Every path is named so the body of the script reads as a sequence
# of declarative steps rather than concatenating literal strings.
# ---------------------------------------------------------------------------

$AgenticDir       = Join-Path $RepoRoot "AgenticOS"
$DashboardDir     = Join-Path $AgenticDir "dashboard"
$LogsDir          = Join-Path $AgenticDir "logs"
$LauncherLogPath  = Join-Path $LogsDir "launcher.log"
$DashboardModule  = "AgenticOS.launch_dashboard"
$UvCacheDir       = Join-Path $RepoRoot ".uv-cache"
$UvPythonDir      = Join-Path $RepoRoot ".uv-python"
$ServerReqPath    = Join-Path $AgenticDir "requirements.txt"
$DashboardReqPath = Join-Path $DashboardDir "requirements.txt"
$PreferredPython  = "3.13"

# Ensure the log directory exists before the first write attempt.
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

# ---------------------------------------------------------------------------
# Interpreter resolution
#
# Order of preference:
#   1. Explicit -PythonExe argument (caller knows best)
#   2. The Windows "py" launcher with -3 (handles a multi-version system)
#   3. Bare "python" on PATH (fallback for venv-only setups)
# ---------------------------------------------------------------------------

function Resolve-PythonInterpreter {
    <#
    .SYNOPSIS
    Resolves the fallback Python interpreter for AgenticOS.

    .PARAMETER explicit
    Optional caller-provided interpreter path.

    .OUTPUTS
    System.String. Path or executable name to run when uv is unavailable.

    .NOTES
    This fallback is intentionally secondary. The primary launch path uses
    uv so AgenticOS gets the pinned FastAPI, pythonnet, and dashboard
    dependencies without requiring the user's global Python to be prepared.
    #>
    param([string] $explicit)

    if ($explicit) {
        return $explicit
    }
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        # The launcher resolves the right interpreter at runtime.
        return $pyLauncher.Source
    }
    $bare = Get-Command python -ErrorAction SilentlyContinue
    if ($bare) {
        return $bare.Source
    }
    throw "No Python interpreter found. Install Python 3.11+ or pass -PythonExe."
}

function Resolve-LaunchCommand {
    <#
    .SYNOPSIS
    Builds the executable and argument vector for the dashboard process.

    .PARAMETER explicitPython
    Optional caller-provided Python executable.

    .OUTPUTS
    PSCustomObject with FilePath, Arguments, and Mode fields.

    .NOTES
    uv mode pins Python 3.13 so the dashboard runtime is stable across
    Windows Store / Python.org installs. It installs both server and
    desktop launcher requirements in an isolated environment, removing
    the need to remember any setup command before launching AgenticOS.
    #>
    param([string] $explicitPython)

    if (-not $explicitPython) {
        $uv = Get-Command uv -ErrorAction SilentlyContinue
        if ($uv) {
            return [pscustomobject]@{
                FilePath = $uv.Source
                Arguments = @(
                    "run",
                    "--python", $PreferredPython,
                    "--with-requirements", $ServerReqPath,
                    "--with-requirements", $DashboardReqPath,
                    "python",
                    "-m", $DashboardModule
                )
                Mode = "uv-pythonnet"
            }
        }
    }

    $resolved = Resolve-PythonInterpreter -explicit $explicitPython
    if ($resolved -like "*\py.exe") {
        return [pscustomobject]@{
            FilePath = $resolved
            Arguments = @("-3.13", "-m", $DashboardModule)
            Mode = "py-fallback"
        }
    }

    return [pscustomobject]@{
        FilePath = $resolved
        Arguments = @("-m", $DashboardModule)
        Mode = "python-fallback"
    }
}

$LaunchCommand = Resolve-LaunchCommand -explicitPython $PythonExe

if ($LaunchCommand.Mode -eq "uv-pythonnet") {
    $ResolvedPython = $LaunchCommand.FilePath
} else {
    $ResolvedPython = Resolve-PythonInterpreter -explicit $PythonExe
}

# ---------------------------------------------------------------------------
# Environment
#
# PYTHONPATH points at the repo root so "import AgenticOS" works
# without requiring the package to be pip-installed.
# ---------------------------------------------------------------------------

$env:PYTHONPATH = "$RepoRoot;$env:PYTHONPATH"
$env:UV_CACHE_DIR = $UvCacheDir
$env:UV_PYTHON_INSTALL_DIR = $UvPythonDir
$env:PYTHONNET_RUNTIME = "netfx"

# ---------------------------------------------------------------------------
# Audit trail
#
# Every launch appends a single line containing UTC timestamp,
# resolved interpreter, and the argv. Useful when diagnosing why the
# dashboard refused to start at logon.
# ---------------------------------------------------------------------------

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$LaunchLine = "$Timestamp mode=$($LaunchCommand.Mode) executable=$($LaunchCommand.FilePath) args=$($LaunchCommand.Arguments -join ' ')"
Add-Content -Path $LauncherLogPath -Value $LaunchLine

# ---------------------------------------------------------------------------
# Launch
#
# Run the launcher in the current PowerShell process. This is deliberate:
# Start-Process can fail silently on machines whose environment contains
# duplicate PATH/Path keys, which looks exactly like "I clicked it and
# nothing happened." The desktop .bat starts this PowerShell window
# minimized, while this script keeps the child attached and logs any
# startup error instead of losing it.
# ---------------------------------------------------------------------------

Set-Location -Path $RepoRoot
& $LaunchCommand.FilePath @($LaunchCommand.Arguments) *>> $LauncherLogPath
$ExitCode = if ($LASTEXITCODE -ne $null) { $LASTEXITCODE } else { 0 }
$ExitTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$ExitLine = "$ExitTimestamp exit_code=$ExitCode"
Add-Content -Path $LauncherLogPath -Value $ExitLine
exit $ExitCode
