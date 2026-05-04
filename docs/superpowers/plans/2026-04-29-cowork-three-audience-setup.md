# Cowork Three Audience Setup Plan

**Date:** 2026-04-29 (rewritten 2026-04-30)
**Developer:** Marcus Daley
**Project:** C:\ClaudeSkills (Cowork host)
**Source research:** Conversation summary of Anthropic guidance for Cowork (game development, personal use, professional use)
**Goal:** Translate Anthropic's recommended Cowork setup path into an ordered, executable plan that respects the existing private skills repository, the publish guard (planned), OWL Watcher (planned), and AgenticOS Command Center (mostly built), and ends with three role-based plugins.

## How to read this plan

Every phase has a Status block. Items are tagged one of three ways.

`STATUS: VERIFY` means the item is already loaded in the current Cowork session or already on disk. Confirm and move on.

`STATUS: INSTALL` means the item is a real plugin or connector that the Cowork library exposes but is not yet active for this user. Run the install action.

`STATUS: TO BUILD` means the item was previously asserted to exist but the disk check showed it absent or partial. The item is part of the work, not a precondition.

## Phase 0. Baseline (one time, applies to all three audiences)

Status check items first. Verify each before installing anything.

| Item | Verification command or action | Expected state |
|---|---|---|
| Paid Claude plan | claude.ai account page | Pro, Max, Team, or Enterprise active |
| Claude Desktop installed and current | Help menu, About, version compare with claude.com/download | Latest stable |
| Mobile app paired | Mobile app, settings, paired devices list | Desktop is listed |
| Cowork mode visible | Desktop app, mode switcher | Chat, Code, and Cowork all show |
| Folder permissions | Cowork home, Folders pane | C:\ClaudeSkills is mounted, Documents and Downloads optional |

Action checklist.

1. Confirm plan tier on claude.ai. If on Free, upgrade to Pro to unlock Cowork.
2. Update Claude Desktop from claude.com/download. Restart the app.
3. Open the mobile app, pair to desktop if not already paired.
4. Open Cowork from the desktop mode switcher.
5. Mount C:\ClaudeSkills as the primary working folder (already done in this session).

The original plan included a Windows Virtual Machine Platform enable step. That step is removed because Cowork mode already runs in this session without it. Add it back only if a future Cowork build requires it.

The original plan included a publish guard audit step. That step is moved to Phase 4 because the script does not yet exist on disk.

Estimated time: 15 minutes.

Exit criteria for Phase 0. The Cowork home loads, C:\ClaudeSkills is mounted, and the brainstorm-artifact behavior described in CLAUDE.md fires when "brainstorm" is typed.

## Phase 0.5. Inventory diff (one time, before any other phase)

Reality check before action. The original plan asserted several files and folders were already in place. The disk check on 2026-04-30 returned the following.

| Item asserted | On disk | Status |
|---|---|---|
| `C:\ClaudeSkills\scripts\publish_guard.ps1` | No | TO BUILD in Phase 4.2 |
| `C:\ClaudeSkills\config\publish_guard.json` | No | TO BUILD in Phase 4.2 |
| `C:\ClaudeSkills\skills\_taxonomy.yaml` | No | TO BUILD in Phase 4.1 |
| 11 skill categories under `skills\` | Partial. Two categories present (design, documents) | Expand in Phase 4.1 |
| `skills\agentic-parallel\SKILL.md` | No | TO BUILD via Plan 5 |
| `skills\agentic-parallel\README.md` | No | TO BUILD via Plan 5 |
| `tasks\agentic-parallel\tasks.md` | No | TO BUILD via Plan 5 |
| `skills\game-dev\ue5\ue5-blueprint-organization\` | No | TO BUILD in Phase 1.3 |
| `skills\game-dev\ue5\ue5-build-verify\` | No | TO BUILD in Phase 1.3 |
| `C:\ClaudeSkills\AgenticOS\` package | Yes, with backend, dashboard, frontend, tests | VERIFY in Phase 4.4 |
| `C:\ClaudeSkills\AgenticOS\frontend\dist\` | Yes (build output present) | VERIFY |
| `C:\ClaudeSkills\AgenticOS\frontend\public\spline\sonar-hud.splinecode` | Yes | VERIFY |
| `C:\ClaudeSkills\launch_agentic_os.ps1` | Yes | VERIFY |
| `C:\ClaudeSkills\AgenticOS\dashboard\requirements.txt` | Yes | VERIFY |
| OWL Watcher tray app with Open AgenticOS entry | No | TO BUILD or scope down |

Take action on the diff before any phase that depends on a TO BUILD item runs.

Reconciliation note. The CLAUDE.md project file describes a sync engine with `scripts/main.py`, `observer.py`, `broadcaster.py`, `sync_utils.py` and a `cloud/main_cloud.json`. The disk check on 2026-04-30 found `cloud/`, `scripts/`, `config/`, `data/`, `logs/`, `security/`, plus a top-level `orchestrator.py`, `detect_interruption.py`, and `pipeline_config.json`. CLAUDE.md and the disk are not in lockstep. Reconcile in Phase 4.

Estimated time: 20 minutes.

Exit criteria for Phase 0.5. Every TO BUILD item has an owner phase. CLAUDE.md either matches the disk state or has explicit "to be built" markers.

## Phase 1. Game Development track

Audience profile. Portfolio focused C++ and game development work, AAA studio practices, UE5 primary, secondary tools include Blender for asset analysis and design system tools for UI mockups.

### Phase 1.1 Plugins

Install in this order so dependencies resolve cleanly.

1. `anthropic-skills:skill-creator`. STATUS: VERIFY. Already loaded.
2. `cowork-plugin-management:create-cowork-plugin`. STATUS: VERIFY. Already loaded.
3. Engineering function plugin set (`engineering:*`). STATUS: VERIFY. Already loaded with 10 commands.
4. Design function plugin set (`design:*`). STATUS: VERIFY. Already loaded with 7 commands.
5. Superpowers (optional). STATUS: INSTALL only if you want the upstream community version alongside the local skills.

### Phase 1.2 Connectors

1. Blender MCP connector. STATUS: INSTALL.
2. GitHub connector. STATUS: VERIFY or INSTALL depending on current state.
3. Unreal Engine. STATUS: NO ACTION. There is no official UE5 connector. Use shell access plus the UE5 skills planned in Phase 1.3 plus any custom MCPs.

### Phase 1.3 Custom skills

STATUS: TO BUILD. Author `skills\game-dev\ue5\ue5-blueprint-organization\` and `skills\game-dev\ue5\ue5-build-verify\` using `anthropic-skills:skill-creator`. Optional third skill `ue5-asset-naming-conventions` or `ue5-build-pipeline` may follow.

### Phase 1.4 First concrete action

1. Open a Cowork session with C:\ClaudeSkills mounted.
2. Type "brainstorm a UE5 build verification skill update".
3. Mark choices, lock the artifact, run `anthropic-skills:skill-creator` on the result.
4. Save the new skill to `C:\ClaudeSkills\skills\game-dev\ue5\<skill-name>\SKILL.md`.

Estimated time. 30 minutes for verify pass plus 60 minutes for first skill authoring.

Exit criteria for Phase 1. Plugins verified, Blender MCP connected, one new game dev skill authored end to end.

## Phase 2. Personal Use track

Audience profile. Documents, household logistics, hobby projects, recurring reports, low autonomy at first.

### Phase 2.1 Plugins

1. Productivity function plugin set (`productivity:*`). STATUS: VERIFY. Already loaded.
2. Finance function plugin (optional). STATUS: INSTALL only if you want Cowork touching financial data.

### Phase 2.2 Connectors

1. Gmail (already authenticated in this session) or Microsoft 365 mail. STATUS: VERIFY for Gmail.
2. Google Drive or OneDrive. STATUS: INSTALL if needed.
3. Hold off on calendar, task tracker, and notes connectors for the first one or two weeks.

### Phase 2.3 Custom skills

STATUS: VERIFY for the document-designer skill, present at `skills\documents\document-designer\SKILL.md`. STATUS: USE PLUGIN NAMESPACE for `pdf`, `xlsx`, `pptx`. The Anthropic-installed plugin namespaces (`anthropic-skills:pdf`, `anthropic-skills:xlsx`, `anthropic-skills:pptx`) cover the functionality. Build local copies under `skills\documents\` only if the plugin namespace is unavailable in a downstream context.

### Phase 2.4 First concrete action

1. Open a Cowork session, mount Documents and Downloads.
2. Authenticate the mail connector if not authenticated.
3. Run "summarize my inbox from the past 24 hours and propose three replies".
4. Watch the approval flow. Approve or reject each step.
5. Once comfortable, graduate to "draft a one page summary of last month's expenses".

Estimated time. 15 minutes plus one to two weeks of casual use.

Exit criteria for Phase 2. Mail connector authenticated, productivity plugin verified, two completed personal tasks executed.

## Phase 3. Professional Use track

Audience profile. Team or contract work where consistency matters, intellectual property posture is enforced, and admin policy may apply.

### Phase 3.1 Plugins

1. Role-specific function plugin (sales, finance, legal, marketing, HR, engineering, design, operations, or data analysis). STATUS: VERIFY for engineering and design (loaded). STATUS: INSTALL for any of the others.
2. `cowork-plugin-management:*`. STATUS: VERIFY. Already loaded.
3. `product-management:*`. STATUS: VERIFY. Already loaded.

### Phase 3.2 Connectors

1. Slack. STATUS: INSTALL if not authenticated.
2. GitHub. STATUS: VERIFY.
3. One project tracker. STATUS: INSTALL on the engagement that uses it.
4. One document or storage connector. STATUS: INSTALL if your team standardizes on it.

### Phase 3.3 Admin policy actions (Team and Enterprise only)

Skip if you are on Pro or Max.

1. Set network access policy to match the engagement's data classification.
2. Restrict the connector list to the approved set above.
3. Audit installed plugins against the approved list.
4. Configure SSO and enforce MFA.

### Phase 3.4 Author a team wide plugin

STATUS: TO BUILD blocker. The plan says to run the publish guard before publishing. The publish guard does not yet exist on disk. Phase 4.2 must complete before this step can run.

1. Invoke `cowork-plugin-management:create-cowork-plugin`.
2. Bundle the team's standard slash commands, role-specific skills, sub-agent set, and internal MCPs.
3. Run `publish_guard -Mode publish` on the new plugin folder. Hard-block on personal markers and proprietary codenames.
4. Publish to the team's approved internal distribution channel only.

### Phase 3.5 First concrete action

1. Verify role-specific function plugin is loaded.
2. Authenticate two or three core connectors.
3. Run a low-risk task end to end.
4. Schedule the team wide plugin authoring session for after Phase 4.2 completes.

Estimated time. 60 minutes plus 2 to 4 hours for the plugin authoring session.

Exit criteria for Phase 3. Role plugin verified or installed, two to three connectors authenticated, team wide plugin authoring blocked behind Phase 4.2 completion.

## Phase 4. Cross audience integration (custom layer)

Phase 4 is a build phase, not a verification phase. The original plan presented these items as already shipped. The disk check disagrees on three of four.

### Phase 4.1 Categorized skills repository

STATUS: TO BUILD (partial). Two categories on disk (design, documents). Build the rest.

1. Author `C:\ClaudeSkills\skills\_taxonomy.yaml`.
2. Author missing category folders. Possible additions: `universal-coding-standards`, `architecture-patterns`, `dev-workflow`, `enterprise-secure-ai-engineering`, `desktop-ui-designer`, `pyqt6-ui-debugger`, `python-code-reviewer`, `vault-analysis`, `verified-build-gate`, `game-dev`, `documents`, `design`, `agentic-parallel`.
3. Migrate or author at least one SKILL.md per new category.
4. Decide whether `Example_Skills\` merges into the new taxonomy or stays as a reference set. Record the decision in CLAUDE.md.

### Phase 4.2 Publish guard

STATUS: TO BUILD.

1. Author `C:\ClaudeSkills\scripts\publish_guard.ps1` with `audit` and `publish` modes.
2. Author `C:\ClaudeSkills\config\publish_guard.json` with the codename deny-list. Seed with: Marcus, Daley, daleym12, Navy veteran, Full Sail, Nick Penney, stay at home dad, GrizzwaldHouse, Bob, SentinelMail, AgentForge, MCP Command Panel, Quidditch AI, IslandEscape, VetAssist, OWL Watcher, OwlWatcher, DeepCommand, AgenticOS, Agentic OS, agentic-parallel, Cowork Setup Orchestrator.
3. Add a smoke test that runs `publish_guard -Mode audit` on the repo head and exits 0 on a clean tree.
4. Document at `C:\ClaudeSkills\scripts\publish_guard_README.md`.

### Phase 4.3 OWL Watcher file security monitor

STATUS: TO BUILD or scope down.

1. Decide scope. Tray app, console daemon, or scheduled task.
2. Author the watcher under a path you pick (suggest `C:\ClaudeSkills\OWL_Watcher\`).
3. Wire the "Open AgenticOS" tray entry only after Phase 4.4 produces a runnable AgenticOS.

### Phase 4.4 AgenticOS Command Center

STATUS: VERIFY (mostly built). The disk check on 2026-04-30 found:
- `AgenticOS/agentic_server.py`, `models.py`, `state_store.py`, `config.py`, `file_watcher.py`, `websocket_broadcaster.py`, `reviewer_spawner.py`, `session_discovery.py`, `session_bridge.py`, `stuck_detector.py`, `progress_log.py`
- `AgenticOS/dashboard/agentic_dashboard.py`, `agentic_dashboard.xaml`, `webview_host.py`, `tray_icon.py`, `process_supervisor.py`, `registry_helper.py`, `config.py`, `assets/tray-icon.ico`, `requirements.txt`
- `AgenticOS/frontend/` with full src tree, components, hooks, utils, tests, node_modules installed, public/spline/sonar-hud.splinecode present, dist/ present
- `AgenticOS/tests/` with state, server, broadcaster tests
- `launch_agentic_os.ps1` at the repo root

Outstanding install steps:

1. `pip install -r AgenticOS\dashboard\requirements.txt` against the venv that runs the dashboard.
2. Inside `AgenticOS\frontend\` confirm `node_modules\` is present (already true). Run `npm run build` if `dist\` needs refreshing.
3. Confirm `pwsh C:\ClaudeSkills\launch_agentic_os.ps1` opens the dashboard.
4. Verify Plan 5 deliverables exist before agents try to participate. See Phase 5 backlog.

## Phase 5. Three role based plugins

These plugin manifests stay aspirational. Each manifest lists the target skills. Below each is a Skills backlog section listing exactly which skills must be authored before the plugin can ship.

### Phase 5.1 Game Development plugin

| Field | Value |
|---|---|
| Name | `marcus-game-dev` |
| Skills (target) | universal-coding-standards, architecture-patterns, dev-workflow, brainstorm-artifact, ue5-blueprint-organization, ue5-build-verify, python-code-reviewer, frontend-design |
| Connectors | Blender MCP, GitHub |
| Sub-agents | engineering:code-review, engineering:debug, engineering:system-design |
| Slash commands | /brainstorm, /ue5-review, /verified-build, /security-review |
| Privacy posture | Private. Excluded from any public marketplace by publish guard. |

Skills backlog for `marcus-game-dev`. All TO BUILD unless noted.
- universal-coding-standards (TO BUILD)
- architecture-patterns (TO BUILD)
- dev-workflow (TO BUILD)
- brainstorm-artifact (TO BUILD or extract from CLAUDE.md prose)
- ue5-blueprint-organization (TO BUILD)
- ue5-build-verify (TO BUILD)
- python-code-reviewer (TO BUILD)
- frontend-design (TO BUILD or rename to design-system)

### Phase 5.2 Personal Use plugin

| Field | Value |
|---|---|
| Name | `marcus-personal` |
| Skills (target) | document-designer, pdf, xlsx, pptx, doc-coauthoring, productivity:task-management, productivity:memory-management |
| Connectors | One mail connector, one drive or storage connector |
| Sub-agents | None (low autonomy on purpose) |
| Slash commands | /summary, /tasks, /draft |
| Privacy posture | Private. Personal data flows stay on the local device when possible. |

Skills backlog for `marcus-personal`.
- document-designer (VERIFY, on disk)
- pdf (VERIFY via plugin namespace)
- xlsx (VERIFY via plugin namespace)
- pptx (VERIFY via plugin namespace)
- doc-coauthoring (TO BUILD)
- productivity:task-management (VERIFY)
- productivity:memory-management (VERIFY)

### Phase 5.3 Professional Use plugin

| Field | Value |
|---|---|
| Name | `marcus-professional` |
| Skills (target) | universal-coding-standards, dev-workflow, enterprise-secure-ai-engineering, agentic-parallel, doc-coauthoring, design:design-handoff, design:accessibility-review, product-management:write-spec, product-management:stakeholder-update |
| Connectors | Slack, GitHub, one project tracker, one document store |
| Sub-agents | engineering:code-review, product-management:competitive-brief, design:design-critique |
| Slash commands | /brainstorm, /spec, /standup, /security-review, /publish-guard |
| Privacy posture | Private. Subject to the publish guard before any internal publication. |

Skills backlog for `marcus-professional`.
- universal-coding-standards (TO BUILD, shared with marcus-game-dev)
- dev-workflow (TO BUILD, shared)
- enterprise-secure-ai-engineering (TO BUILD)
- agentic-parallel (TO BUILD via Plan 5; this is the dependency the AgenticOS pipeline needs)
- doc-coauthoring (TO BUILD, shared with marcus-personal)
- design:design-handoff (VERIFY)
- design:accessibility-review (VERIFY)
- product-management:write-spec (VERIFY)
- product-management:stakeholder-update (VERIFY)

### Phase 5.4 Authoring order

Game Development first. Smallest scope, fastest validation cycle. Personal Use second. Lowest risk surface and lets you exercise the approval flow with non sensitive tasks. Professional Use third. Largest scope and benefits from the lessons of the first two.

Each plugin authoring session uses `cowork-plugin-management:create-cowork-plugin`, runs `publish_guard -Mode publish` before any internal publication once Phase 4.2 is done, and produces a plugin folder under `C:\ClaudeSkills\plugins\<name>`, a SKILL.md or plugin.yaml manifest at the root, and smoke test artifacts proving every bundled skill loads.

Authoring is gated on Phase 4 completion. If Phase 4.1 (taxonomy plus skill folders) and Phase 4.2 (publish guard) are not done, Phase 5 cannot ship. Phase 5 manifests can still be drafted and reviewed in parallel with Phase 4 work.

## Self review checklist

- [ ] Phase 0 covers the same baseline items Anthropic lists in the Get started article, with the unnecessary Virtual Machine Platform step removed
- [ ] Phase 0.5 inventory diff is present and references actual disk state
- [ ] Each track has plugin list, connector list, custom skill notes, and a first concrete action
- [ ] Phase 1.1, 2.1, and 3.1 use VERIFY language for plugins already loaded in the session
- [ ] Phase 4 is reframed as build, not verify, except 4.4 which is mostly built
- [ ] Phase 5 plugin manifests are kept as targets with explicit Skills backlog sections
- [ ] Phase 5 authoring is gated on Phase 4 completion
- [ ] Time estimates are present for every phase
- [ ] Exit criteria are present for every phase
- [ ] No dash-as-pause punctuation. Use commas, periods, parens, or "and" instead

## Locked references

Reference this plan from CLAUDE.md as a pinned setup roadmap.

```
- Cowork three audience setup plan: docs/superpowers/plans/2026-04-29-cowork-three-audience-setup.md (locked 2026-04-29, rewritten 2026-04-30)
```

Source of truth note. Where this plan and CLAUDE.md disagree on what is built, the disk is the source of truth. Reconcile CLAUDE.md against this plan in Phase 4.1.
