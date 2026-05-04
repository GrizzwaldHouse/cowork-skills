<#
.SYNOPSIS
    Publish-guard for the C:\ClaudeSkills private repository.

.DESCRIPTION
    Scans the repository for personal markers and project codenames before any
    push, archive, or marketplace operation. Reads its rules from the JSON
    config so that adding a new codename never requires editing this script.

.PARAMETER Mode
    install : soft check, runs from setup.ps1 before files are copied locally.
    publish : hard check, runs before git push / git archive / marketplace upload.
    audit   : informational scan, prints findings grouped by severity.

.PARAMETER ConfigPath
    Override path to publish_guard.json. Defaults to the standard location so
    the script remains portable when the repo is cloned to another drive.

.PARAMETER RepoRoot
    Override path to the repository root. Defaults to two levels up from the
    script. Allows running the guard from CI where the working directory may
    not be C:\ClaudeSkills.

.EXAMPLE
    pwsh ./scripts/publish_guard.ps1 -Mode publish
    Runs a hard scan before pushing. Exits 1 if any redline trips.

.NOTES
    File    : publish_guard.ps1
    Author  : Marcus Daley
    Date    : 2026-04-29
    Purpose : Prevent leaks of personal info, codenames, or proprietary code
              when publishing to non-approved destinations.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("install", "publish", "audit")]
    [string]$Mode = "audit",

    [Parameter(Mandatory = $false)]
    [string]$ConfigPath,

    [Parameter(Mandatory = $false)]
    [string]$RepoRoot
)

# Stop on the first uncaught error so we never silently approve a push.
$ErrorActionPreference = "Stop"

# Resolve repo root and config path from script location so the guard works
# regardless of where the user invokes it from. Hardcoding C:\ClaudeSkills
# would violate the "no hardcoded values" rule from CLAUDE.md.
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot)   { $RepoRoot   = Resolve-Path (Join-Path $ScriptDir "..") | Select-Object -ExpandProperty Path }
if (-not $ConfigPath) { $ConfigPath = Join-Path $RepoRoot "config\publish_guard.json" }

function Read-GuardConfig {
    # WHY: a single load keeps all downstream functions consistent. If the
    # config is malformed we want to fail loud rather than silently fall back
    # to defaults that could let a leak through.
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "publish_guard.json not found at: $Path"
    }

    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        throw "Failed to parse publish_guard.json: $($_.Exception.Message)"
    }
}

function Write-GuardLog {
    # WHY: every guard run must leave an audit trail. A silent guard is a
    # broken guard. The log path comes from the config so it can be redirected
    # to a SIEM or central log share without code changes.
    param(
        [string]$RepoRoot,
        [string]$RelativeLogPath,
        [string]$Mode,
        [string]$Verdict,
        [int]   $MatchCount,
        [string[]]$Notes
    )

    $logDir  = Join-Path $RepoRoot (Split-Path $RelativeLogPath -Parent)
    $logFile = Join-Path $RepoRoot $RelativeLogPath

    if (-not (Test-Path -LiteralPath $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $stamp   = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    $noteStr = if ($Notes) { ($Notes -join " | ") } else { "" }
    $line    = "[$stamp] mode=$Mode verdict=$Verdict matches=$MatchCount notes=$noteStr"

    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
}

function Test-PathExcluded {
    # WHY: CLAUDE.md, COPYRIGHT.md, security/, etc. legitimately contain
    # personal markers because they ARE the legal/identity surface of the
    # project. Flagging them on every run would train Marcus to ignore the
    # guard, which is the exact failure mode we are trying to prevent.
    param(
        [string]$RelativePath,
        [string[]]$ExcludedPaths
    )

    $normalized = ($RelativePath -replace '\\', '/').TrimStart('/')

    foreach ($excluded in $ExcludedPaths) {
        $needle = ($excluded -replace '\\', '/').TrimStart('/')
        if ($needle.EndsWith('/')) {
            if ($normalized -like ($needle + '*')) { return $true }
        } else {
            if ($normalized -ieq $needle)          { return $true }
            if ($normalized -like ('*/' + $needle)) { return $true }
        }
    }

    return $false
}

function Test-IsBinaryFile {
    # WHY: regex scanning a 50MB PNG burns CPU and produces gibberish matches.
    # Skipping by extension is heuristic but fast and correct for this repo.
    param(
        [string]$Path,
        [string[]]$BinaryExtensions
    )

    $ext = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    return $BinaryExtensions -contains $ext
}

function Get-CandidateFiles {
    # WHY: enumerate once, filter once. Using -File with -Recurse is faster
    # than recursive Get-ChildItem in PowerShell 5.1.
    param(
        [string]$Root,
        [string[]]$ExcludedPaths,
        [string[]]$BinaryExtensions,
        [long]   $MaxBytes
    )

    $results = [System.Collections.Generic.List[string]]::new()

    Get-ChildItem -LiteralPath $Root -Recurse -File -Force -ErrorAction SilentlyContinue |
        ForEach-Object {
            $rel = $_.FullName.Substring($Root.Length).TrimStart('\','/')

            if (Test-PathExcluded -RelativePath $rel -ExcludedPaths $ExcludedPaths) { return }
            if (Test-IsBinaryFile -Path $_.FullName -BinaryExtensions $BinaryExtensions) { return }
            if ($_.Length -gt $MaxBytes) { return }

            [void]$results.Add($_.FullName)
        }

    return ,$results
}

function Find-Matches {
    # WHY: returns one record per (file, pattern, line) so the report can
    # group by severity and the log can record an exact count.
    param(
        [string]$Root,
        [string[]]$Files,
        [string[]]$Patterns,
        [string]  $Category
    )

    $hits = [System.Collections.Generic.List[psobject]]::new()

    foreach ($file in $Files) {
        try {
            $content = Get-Content -LiteralPath $file -Raw -ErrorAction Stop
        }
        catch {
            # WHY: a locked or unreadable file should not crash the whole
            # scan. Skip and move on; the audit log records the count of
            # successful scans, not file-level errors.
            continue
        }

        if (-not $content) { continue }

        foreach ($pattern in $Patterns) {
            if ([string]::IsNullOrWhiteSpace($pattern)) { continue }

            $regexMatches = [regex]::Matches($content, $pattern)
            if ($regexMatches.Count -eq 0) { continue }

            $rel = $file.Substring($Root.Length).TrimStart('\','/')

            foreach ($m in $regexMatches) {
                # Compute 1-based line number for the match offset so the
                # operator can jump straight to the offending line.
                $upToMatch = $content.Substring(0, $m.Index)
                $lineNum   = ($upToMatch -split "`n").Count

                [void]$hits.Add([pscustomobject]@{
                    Category = $Category
                    File     = $rel
                    Line     = $lineNum
                    Pattern  = $pattern
                    Match    = $m.Value
                })
            }
        }
    }

    return ,$hits
}

function Get-CurrentRemote {
    # WHY: the publish mode must verify the active remote against the
    # allowed_destinations list. If git is unavailable we treat the remote
    # as unknown and let the regex check decide.
    param([string]$RepoRoot)

    Push-Location $RepoRoot
    try {
        $remote = & git remote get-url origin 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        return $remote.Trim()
    }
    catch {
        return $null
    }
    finally {
        Pop-Location
    }
}

function Test-RemoteAllowed {
    param(
        [string]  $Remote,
        [string[]]$Allowed,
        [string[]]$Blocked
    )

    if (-not $Remote) {
        return [pscustomobject]@{ Decision = "unknown"; Reason = "No git remote detected." }
    }

    foreach ($pattern in $Blocked) {
        if ($Remote -match $pattern) {
            return [pscustomobject]@{ Decision = "blocked"; Reason = "Remote matches blocked pattern: $pattern" }
        }
    }

    foreach ($pattern in $Allowed) {
        if ($Remote -match $pattern) {
            return [pscustomobject]@{ Decision = "allowed"; Reason = "Remote matches allowed pattern: $pattern" }
        }
    }

    return [pscustomobject]@{ Decision = "unknown"; Reason = "Remote $Remote did not match allow or block list." }
}

function Write-Report {
    param(
        [string]$Mode,
        [psobject[]]$PersonalHits,
        [psobject[]]$CodenameHits,
        [psobject]  $RemoteCheck
    )

    Write-Host ""
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "  PUBLISH GUARD - mode: $Mode" -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan

    if ($RemoteCheck) {
        $color = switch ($RemoteCheck.Decision) {
            "allowed" { "Green" }
            "blocked" { "Red" }
            default   { "Yellow" }
        }
        Write-Host ("Remote check : {0} - {1}" -f $RemoteCheck.Decision.ToUpper(), $RemoteCheck.Reason) -ForegroundColor $color
    }

    Write-Host ""
    Write-Host ("Personal marker hits : {0}" -f $PersonalHits.Count) -ForegroundColor Yellow
    Write-Host ("Project codename hits: {0}" -f $CodenameHits.Count) -ForegroundColor Yellow
    Write-Host ""

    $all = @()
    if ($PersonalHits) { $all += $PersonalHits }
    if ($CodenameHits) { $all += $CodenameHits }

    if ($all.Count -gt 0) {
        $all |
            Sort-Object Category, File, Line |
            Format-Table -AutoSize Category, File, Line, Match, Pattern |
            Out-String |
            Write-Host
    } else {
        Write-Host "No redline matches found outside excluded paths." -ForegroundColor Green
    }
}

# -----------------------------------------------------------------------------
# Main flow
# -----------------------------------------------------------------------------

try {
    $cfg = Read-GuardConfig -Path $ConfigPath

    $repoFull = (Resolve-Path -LiteralPath $RepoRoot).Path

    Write-Host "publish_guard: scanning $repoFull" -ForegroundColor DarkCyan

    $files = Get-CandidateFiles `
        -Root $repoFull `
        -ExcludedPaths $cfg.excluded_paths `
        -BinaryExtensions $cfg.binary_extensions `
        -MaxBytes $cfg.max_file_size_bytes

    $personalHits = Find-Matches -Root $repoFull -Files $files -Patterns $cfg.personal_markers  -Category "PERSONAL"

    # Project codenames are literal strings, but we escape and apply word
    # boundaries so "Bob" does not match "Bobcat" inside an unrelated doc.
    $codenamePatterns = $cfg.project_codenames | ForEach-Object { '(?i)\b' + [regex]::Escape($_) + '\b' }
    $codenameHits = Find-Matches -Root $repoFull -Files $files -Patterns $codenamePatterns -Category "CODENAME"

    $remoteCheck = $null
    if ($Mode -eq "publish") {
        $remoteUrl   = Get-CurrentRemote -RepoRoot $repoFull
        $remoteCheck = Test-RemoteAllowed -Remote $remoteUrl `
                                          -Allowed $cfg.allowed_destinations `
                                          -Blocked $cfg.blocked_destinations
    }

    Write-Report -Mode $Mode -PersonalHits $personalHits -CodenameHits $codenameHits -RemoteCheck $remoteCheck

    $totalHits = $personalHits.Count + $codenameHits.Count
    $verdict   = "PASS"
    $exitCode  = 0
    $notes     = @()

    switch ($Mode) {
        "install" {
            # WHY soft: installing locally to ~/.claude/skills/ is fine; the
            # files never leave the user's machine. Warn so the operator
            # knows what is being copied but do not block.
            if ($totalHits -gt 0) {
                $verdict = "WARN"
                $notes  += "install-mode soft warn"
                Write-Host "Install-mode soft check: continuing despite $totalHits findings." -ForegroundColor Yellow
            }
            $exitCode = 0
        }

        "audit" {
            $verdict  = if ($totalHits -gt 0) { "WARN" } else { "PASS" }
            $exitCode = 0
        }

        "publish" {
            # WHY hard: this is the last gate before the repo leaves the box.
            # Any finding outside excluded_paths is treated as a redline.
            if ($remoteCheck.Decision -eq "blocked") {
                $verdict = "BLOCK"
                $notes  += "remote=blocked"
                $exitCode = $cfg.severity_levels.block.exit_code
            }
            elseif ($remoteCheck.Decision -eq "unknown") {
                $verdict = "BLOCK"
                $notes  += "remote=unknown"
                $exitCode = $cfg.severity_levels.block.exit_code
            }

            if ($totalHits -gt 0) {
                $verdict = "BLOCK"
                $notes  += "redlines=$totalHits"
                $exitCode = $cfg.severity_levels.block.exit_code
            }

            if ($exitCode -ne 0) {
                Write-Host ""
                Write-Host "PUBLISH BLOCKED. Resolve findings or move them under excluded_paths." -ForegroundColor Red
            } else {
                Write-Host ""
                Write-Host "PUBLISH OK. No redlines, remote is on the allow list." -ForegroundColor Green
            }
        }
    }

    Write-GuardLog -RepoRoot $repoFull `
                   -RelativeLogPath $cfg.log_path `
                   -Mode $Mode `
                   -Verdict $verdict `
                   -MatchCount $totalHits `
                   -Notes $notes

    exit $exitCode
}
catch {
    Write-Host "publish_guard FAILED: $($_.Exception.Message)" -ForegroundColor Red
    # WHY: a crashed guard must never look like a pass. Exit non-zero so any
    # caller (setup.ps1, pre-push hook, CI) treats it as a halt.
    exit 2
}
