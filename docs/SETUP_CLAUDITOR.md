# Clauditor install (Windows / Claude Code)

[Clauditor](https://github.com/IyadhKhalfallah/clauditor) reduces wasted quota by rotating oversized Claude Code sessions. It hooks the Claude Code CLI and supported IDE extensions (not Claude Code web).

## Prerequisites

- Node.js **20+**
- Claude Code CLI or supported IDE integration

## Commands

Global install:

```powershell
npm install -g @iyadhk/clauditor
clauditor install
```

No global install (uses npx):

```powershell
npx @iyadhk/clauditor install
```

Hooks stay registered across Clauditor upgrades per upstream README.

## Verify

Open Claude Code and run a normal session; when session waste factor exceeds Clauditor thresholds, prompts should block and reference saved session handoffs under `~/.clauditor/` (see upstream docs).
