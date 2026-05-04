# Publish Guard - Operator Guide

**File:** `security/PUBLISH_GUARD.md`
**Owner:** Marcus Daley
**Date:** 2026-04-29
**Related:** `COPYRIGHT.md`, `PRIVACY.md`, `config/publish_guard.json`

---

## What it does

The publish guard is a two-mode redline scanner that runs over the whole
`C:\ClaudeSkills` repository before any operation that could expose its
contents externally. It enforces three policies in one pass:

1. **No personal markers leak** - Marcus Daley, his email, military / academic
   biography, family references, and absolute Windows paths are all flagged.
2. **No project codenames leak** - Bob, SentinelMail, AgentForge, MCP Command
   Panel, Quidditch AI, IslandEscape, VetAssist, OWL Watcher, DeepCommand,
   GrizzwaldHouse, etc.
3. **No publishing to non-approved destinations** - the active git remote is
   compared against `allowed_destinations` and `blocked_destinations` regex
   lists.

Findings inside `excluded_paths` (CLAUDE.md, COPYRIGHT.md, PRIVACY.md, NOTICE,
LICENSE, .env, security/, logs/, backups/, the guard's own files) are
suppressed because those files are the **legitimate** identity surface of the
repo and would otherwise generate constant false positives.

## Files

| Path | Purpose |
|---|---|
| `config/publish_guard.json` | Single source of truth: regex lists, codenames, destinations, excluded paths, severity table. |
| `scripts/publish_guard.ps1` | PowerShell 5.1+ implementation. Used on Windows by `setup.ps1` and pre-push hooks. |
| `scripts/publish_guard.sh`  | Bash 4+ implementation. Used in CI and on Linux/macOS. |
| `logs/publish_guard.log`    | Append-only audit log: timestamp, mode, verdict, match count, notes. |
| `.gitattributes`            | Backstop: `export-ignore` keeps identity files out of `git archive`. |
| `.gitignore`                | Backstop: blocks committing `.env`, `logs/`, `backups/`, `.merge-tmp/`. |

## Modes

```text
install   Soft check.  Always exits 0.  Used by setup.ps1 / setup.sh
          before files are copied to ~/.claude/skills/.  Local install
          is fine; we only want a heads-up.

audit     Informational scan.  Always exits 0.  Use this to review what
          the guard sees without affecting any workflow.

publish   Hard check.  Exits 1 if any redline is hit OR the active git
          remote is not on the allow list.  Wire this into pre-push
          hooks, CI, and any script that calls `git archive` or pushes
          to a marketplace.
```

## How to run

### PowerShell (Windows)

```powershell
# Soft scan during local install
pwsh -File .\scripts\publish_guard.ps1 -Mode install

# Full audit report
pwsh -File .\scripts\publish_guard.ps1 -Mode audit

# Hard pre-push gate
pwsh -File .\scripts\publish_guard.ps1 -Mode publish
if ($LASTEXITCODE -ne 0) { throw "Publish blocked." }
```

### Bash (Linux / macOS / git-bash / CI)

```bash
./scripts/publish_guard.sh --mode install
./scripts/publish_guard.sh --mode audit
./scripts/publish_guard.sh --mode publish
```

### Wire it into git

Add to `.git/hooks/pre-push` (not committed; install via setup script):

```bash
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/scripts/publish_guard.sh" --mode publish
```

## Adding a new project codename

1. Open `config/publish_guard.json`.
2. Append the codename string to the `project_codenames` array. Use the
   exact spelling AND any common variants (with/without spaces, casing
   variants). The script already applies word-boundary matching, so
   short names like `Bob` will not catch `Bobcat`.
3. If the new project introduces new personal markers (a co-author's name,
   a shared email), add a regex to `personal_markers` instead - those use
   raw regex syntax with case-insensitive `(?i)` prefix.
4. Run `audit` mode and confirm the new pattern fires only where expected.
5. Commit `config/publish_guard.json`. **Never** edit the scripts themselves
   to add a value - that violates the project's no-hardcoded-values rule.

## Adding a new approved destination

If you stand up a second private mirror (e.g. a self-hosted Gitea), add a
regex to `allowed_destinations`. Keep them as restrictive as possible - the
default pattern only allows repos under `github.com/GrizzwaldHouse/`.

## Expected workflow

```text
local edit  ->  publish_guard --mode audit
                     |
                     v
 stage / commit  ->  pre-push hook runs --mode publish
                     |               |
                     | exit 0        | exit 1
                     v               v
              git push to       BLOCKED.  Fix or move
              GrizzwaldHouse    finding into excluded_paths.
                     |
                     v
              CI runs --mode publish on the remote
              as a defense-in-depth backstop.
```

## Updating the log retention

Logs go to `logs/publish_guard.log` (gitignored). Rotate or archive on the
schedule defined in your retention policy. The guard never deletes its own
log lines - that is intentional, so a tampering attempt is visible.

## Cross-reference

- `COPYRIGHT.md` - declares the repository's licensing posture and identity.
- `PRIVACY.md` - declares what personal data the repo intentionally contains
  and why it is not for public distribution.
- `skills/enterprise-secure-ai-engineering/` - the broader security guardrail
  framework (OWASP, NIST SSDF, SLSA, SOC2 alignment) that this guard
  operationalizes for the publish surface.
