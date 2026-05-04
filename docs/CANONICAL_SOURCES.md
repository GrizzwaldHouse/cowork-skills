# Canonical agent sources (Marcus Daley)

Single reference for repos, tooling, and sync cadence. Agents should consult these **before improvising** workflows or duplicate standards.

## Git remotes

| Purpose | URL | Notes |
|--------|-----|--------|
| Skills canon (local clone) | `https://github.com/GrizzwaldHouse/cowork-skills.git` | Primary remote for `C:\ClaudeSkills`. Default branch: **`master`** (verify with `git branch -vv`). |
| Workflow / process patterns | `https://github.com/obra/superpowers.git` | **Intent reference**: pin decisions to GitHub releases/tags when documenting behavior. Copies delivered via Claude Code / Cursor plugin cache are **convenience only** — if plugin copy disagrees with GitHub, prefer GitHub then re-sync skills from cowork-skills. |
| Claude Code session hygiene | `https://github.com/IyadhKhalfallah/clauditor.git` | Quota/session rotation hooks for **Claude Code CLI / IDE extensions** — not Cursor MCP. Install: `npm install -g @iyadhk/clauditor` then `clauditor install` (Node 20+). |
| ML Hub | `https://huggingface.co/` | Models, datasets, Spaces, docs. Prefer **`plugin-huggingface-skills-huggingface-skills`** MCP tools in Cursor when work touches Hub APIs, datasets, or cited model cards — avoid guessing APIs. |

## Local path

- **`C:\ClaudeSkills`**: Working tree for **cowork-skills**. Edit skills here; push to `origin`.

## Update cadence

1. `git pull origin master`
2. Resync Claude Code skills: **`.\setup.ps1`** (Windows) or **`./setup.sh`** (Git/Git Bash/macOS/Linux)
3. Optional: reinstall Clauditor hooks after major Claude Code upgrades (`clauditor install` again per upstream README).

## Brainstorm scope lock

- Skill directory: `skills/brainstorm-artifact/` (`SKILL.md`, `templates/`, `examples/`).
- Locked artifacts: project `docs/BRAINSTORM_YYYY-MM-DD.md`.
- Global fallback text is mirrored in repo **`CLAUDE.md`** / **`AGENTS.md`** under **Brainstorming Artifact Standard**; **`CLAUDE_MD_ADDITION.md`** at repo root is the same package snippet for merges into **`~/.claude/CLAUDE.md`** on new machines.

## Precedence

1. Marcus **AGENT_CONTEXT** / Universal Coding Standards (Top 5 rules) — wins on conflicts.
2. **`brainstorm-artifact`** skill when loaded — checklist structure and confirmation gate.
3. **obra/superpowers** — adopt TDD / verification patterns where they do not conflict with (1)–(2).
