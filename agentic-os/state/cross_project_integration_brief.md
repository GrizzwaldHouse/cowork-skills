# AgenticOS Cross-Project Integration Brief

Captured: 2026-05-02

## Shared Objective

Combine active CLAW, Claude, Codex, and Ollama work into one AgenticOS Universal Hub. AgenticOS remains the coordinator and canonical state bus; project-specific work stays in its own repository or project folder.

## Projects

- `C:/ClaudeSkills/AgenticOS`: Hub, dashboard, task runtime, terminal control, watcher policy, MCP, relay, and project registry.
- `C:/Users/daley/UnrealProjects/BaseGame/UnrealEditorGuideBookClaudeDesign`: Unreal guidebook and game-development knowledge source.
- `D:/portfolio-website`: Portfolio surface and public-facing project integration target.

## Agent Instructions

- Claim work through `C:/ClaudeSkills/agentic-os/tasks` before editing shared AgenticOS files.
- Respect task locks in `C:/ClaudeSkills/agentic-os/locks`; fail fast instead of duplicating another terminal's work.
- Keep project-specific code in its owning project folder, then publish status or integration metadata back to AgenticOS.
- Use AgenticOS as the bridge between projects: task state, project registry records, handoff manifests, MCP responses, and dashboard cards.
- Do not delete files outside the claimed task scope. For Ollama work, obey `C:/ClaudeSkills/agentic-os/state/ollama_scope.json`.
- If a terminal is off-scope, blocked, or working the wrong files, stop and write a checkpoint instead of continuing.

## Next Coordination Target

The next available worker should claim `task-integrate-agentic-os-projects`, inspect the three project roots, and produce a concrete integration map that names:

- Shared AgenticOS APIs each project will call.
- Files each agent owns during the merge.
- What knowledge moves into AgenticOS versus what remains project-local.
- Validation steps for Unreal, portfolio web, and AgenticOS dashboard flows.
