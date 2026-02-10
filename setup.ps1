# cowork-skills setup script for Windows PowerShell
# Syncs skills from this repo to your ~/.claude/skills/ directory
# Run this on any Windows machine after cloning the repo

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsSource = Join-Path $ScriptDir "skills"
$SkillsTarget = Join-Path $env:USERPROFILE ".claude\skills"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Cowork Skills - Setup & Sync" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Source: $SkillsSource"
Write-Host "Target: $SkillsTarget"
Write-Host ""

# Create target directory
if (-not (Test-Path $SkillsTarget)) {
    New-Item -ItemType Directory -Path $SkillsTarget -Force | Out-Null
}

# Sync each skill
$skills = Get-ChildItem -Path $SkillsSource -Directory
foreach ($skill in $skills) {
    $targetSkill = Join-Path $SkillsTarget $skill.Name
    Write-Host "  Installing skill: $($skill.Name)" -ForegroundColor Yellow

    if (-not (Test-Path $targetSkill)) {
        New-Item -ItemType Directory -Path $targetSkill -Force | Out-Null
    }

    Copy-Item -Path "$($skill.FullName)\*" -Destination $targetSkill -Recurse -Force
}

Write-Host ""
Write-Host "Skills installed to $SkillsTarget`:" -ForegroundColor Green
Get-ChildItem -Path $SkillsTarget -Directory | ForEach-Object { Write-Host "  $($_.Name)" }
Write-Host ""
Write-Host "Done! Skills are now available in all Claude Code sessions." -ForegroundColor Green
Write-Host "Background skills (design-system, document-designer) auto-load."
Write-Host "User skills: type /canva-designer to invoke."
Write-Host ""
Write-Host "To update: git pull; .\setup.ps1" -ForegroundColor Cyan
