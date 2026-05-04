# Cowork Skills

Claude Code skills and task templates for professional design, document generation, coding standards, security engineering, desktop UI development, game development, research, marketing, SEO, and workflow automation.

## Quick Setup

Clone this repo on any machine, then run the setup script to install skills globally:

```bash
# Clone
git clone https://github.com/GrizzwaldHouse/cowork-skills.git
cd cowork-skills

# Install (Linux/macOS/Git Bash)
./setup.sh

# Install (Windows PowerShell)
.\setup.ps1
```

Skills install to `~/.claude/skills/` and are available in **all** Claude Code sessions on that machine.

To update: `git pull && ./setup.sh`

Single reference for repos, Clauditor, Hugging Face, and sync cadence: [`docs/CANONICAL_SOURCES.md`](docs/CANONICAL_SOURCES.md).

## Skills

### Background Skills (auto-loaded)

These skills load automatically when Claude detects a relevant task. No invocation needed.

#### Core Standards
| Skill | Purpose |
|-------|---------|
| `universal-coding-standards` | Non-negotiable coding rules across all languages (access control, initialization, Observer pattern, no polling) |
| `architecture-patterns` | Observer, composition, interface-driven, data-driven, repository, separation of concerns |
| `dev-workflow` | Brainstorm-first methodology, session management, build/tooling, version control, debugging |
| `enterprise-secure-ai-engineering` | OWASP, NIST SSDF, SLSA, SOC2 guardrails for runtime safety and AI code governance |
| `brainstorm-artifact` | Pre-work scope-locking artifact: grouped checklist sections, trade-off options, decision pre-checking, blocks code generation until Marcus confirms |

#### Design & Documents
| Skill | Purpose |
|-------|---------|
| `design-system` | Color theory, typography, layout, accessibility (auto-loaded for visual tasks) |
| `document-designer` | Professional Excel, Word, PowerPoint, PDF formatting |
| `frontend-design` | Distinctive, non-generic frontend UI/component design |
| `canvas-design` | Visual art creation for posters, designs, static pieces |
| `pdf` | Read, merge, split, OCR, create, fill forms on PDF files |
| `xlsx` | Spreadsheet creation, formulas, formatting, data analysis |
| `pptx` | Presentation creation, editing, design-forward slide decks |
| `doc-coauthoring` | 3-stage collaborative workflow for specs, proposals, RFCs, PRDs |

#### Research & Strategy
| Skill | Purpose |
|-------|---------|
| `deep-research` | Multi-source research with planner-executor-publisher pipeline and cited reports |
| `autoresearch` | Autonomous experiment loops (Karpathy pattern) with git-tracked results |
| `claude-seo` | Technical SEO audits, schema markup, content optimization, site architecture |
| `marketing-toolkit` | CRO, copywriting, email sequences, launch strategy, customer research |

#### Development Workflow
| Skill | Purpose |
|-------|---------|
| `superpowers-workflow` | TDD (red-green-refactor), systematic debugging, structured code review, SDD |
| `context-optimization` | Context window management, compression strategies, memory systems, multi-agent coordination |
| `prompt-engineering` | Prompt design patterns, testing with promptfoo, evaluation strategies |
| `skill-creator` | Meta-skill for creating, evaluating, and optimizing new skills |

#### Tools & Infrastructure
| Skill | Purpose |
|-------|---------|
| `mcp-integration-guide` | Setup guide for Context7, Tavily, Playwright MCP, Firecrawl, Codebase Memory, Task Master |
| `automation-orchestration` | n8n, Langflow, claude-squad, container-use orchestration patterns |
| `video-generation` | Programmatic video creation with Remotion (React + TypeScript) |
| `obsidian-knowledge` | Obsidian vault management, OFM syntax, Zettelkasten/PARA, Dataview queries |
| `verified-build-gate` | 6-step build verification pipeline (build, launch, stability, tests, review, verdict) |

### User-Invocable Skills

These skills are triggered by typing the slash command in Claude Code.

| Skill | Command | Purpose |
|-------|---------|---------|
| `canva-designer` | `/canva-designer` | Canva prompt engineering for design generation |
| `desktop-ui-designer` | `/desktop-ui-designer` | PyQt6/PySide6 desktop app design and implementation |
| `pyqt6-ui-debugger` | `/pyqt6-ui-debugger` | Systematic PyQt6 layout/widget debugging |
| `python-code-reviewer` | `/python-code-reviewer` | Python code review against universal standards |
| `ue5-blueprint-organization` | `/ue5-blueprint-organization` | UE5 Blueprint graph best practices |
| `ue5-plugin-scaffold` | `/ue5-plugin-scaffold` | Scaffold production-ready UE5 plugins |
| `ue5-plugin-review` | `/ue5-plugin-review` | Audit UE5 plugins for quality and portability |

## Task Templates

Pre-built task checklists for common workflows:

| Category | File | What's Included |
|----------|------|-----------------|
| App Development | `tasks/app-development/tasks.md` | Feature implementation, bug fixes, UI upgrades, API endpoints, deployment |
| AI Workflows | `tasks/ai-workflows/tasks.md` | Canva generation, document creation, prompt engineering, agent safety review |
| Game Development | `tasks/game-development/tasks.md` | Level design, Unreal Blueprints, AI agents, HUD/UI, multiplayer, optimization |

## How It Works

**Background skills** load automatically whenever Claude detects a relevant task. You don't need to do anything.

**User-invocable skills** are triggered by typing the slash command (e.g., `/canva-designer`).

**Task templates** are reference checklists. Copy the relevant section into your project or reference them when planning work.

## Multi-Agent System

The `scripts/` directory contains a Python-based multi-agent runtime that coordinates specialized agents (extractor, validator, refactor, sync, pruner) over a shared typed event bus. Agents communicate via `EventBus.publish` with handler-level exception isolation so one bad handler can't stall the pipeline.

Security-sensitive components are covered by unit tests in `tests/`:

| Component | File | Tests | Purpose |
|---|---|---|---|
| EventBus | `scripts/agent_event_bus.py` | `tests/test_agent_event_bus.py` | Typed pub/sub with RLock + snapshot dispatch |
| SkillIsolator | `scripts/skill_isolator.py` | `tests/test_skill_isolator.py` (93 tests) | Per-agent skill manifest writer with strict path-traversal validation (CWE-22/41/66) |
| Extractor agent | `scripts/agents/extractor_agent.py` | `tests/test_extractor_agent.py` | Skill extraction pipeline |
| Validator agent | `scripts/agents/validator_agent.py` | `tests/test_validator_agent.py` | Skill validation against security rules |
| Sandbox manager | `scripts/testing/sandbox_manager.py` | `tests/test_sandbox_manager.py` | Process isolation for untrusted code |

Run tests:
```bash
py -3 tests/test_skill_isolator.py                                           # 93 assertions
py -3 -m pytest tests/test_agent_event_bus.py tests/test_sandbox_manager.py  # pytest suite
```

## Structure

```
cowork-skills/
  skills/
    # Core Standards
    universal-coding-standards/         # Access control, init, events, anti-patterns
    architecture-patterns/              # Observer, composition, data-driven, repo pattern
    dev-workflow/                       # Brainstorm-first, debugging, version control
    enterprise-secure-ai-engineering/   # OWASP, NIST, SLSA, SOC2 guardrails
    # Design & Documents
    design-system/                      # Color, typography, layout, accessibility
    document-designer/                  # Excel, Word, PPT, PDF best practices
    frontend-design/                    # Distinctive frontend UI design
    canvas-design/                      # Visual art and poster creation
    canva-designer/                     # Canva prompt engineering
    pdf/                                # PDF processing and creation
    xlsx/                               # Spreadsheet operations
    pptx/                               # Presentation creation
    doc-coauthoring/                    # Collaborative document writing
    # Research & Strategy
    deep-research/                      # Multi-source research reports
    autoresearch/                       # Autonomous experiment loops
    claude-seo/                         # SEO audits and optimization
    marketing-toolkit/                  # CRO, copy, growth, launch
    # Development Workflow
    superpowers-workflow/               # TDD, debugging, code review
    context-optimization/               # Context window management
    prompt-engineering/                 # Prompt testing and evaluation
    skill-creator/                      # Meta-skill for creating skills
    # Tools & Infrastructure
    mcp-integration-guide/              # MCP server setup guide
    automation-orchestration/           # n8n, Langflow, claude-squad
    video-generation/                   # Remotion video creation
    obsidian-knowledge/                 # Obsidian vault management
    verified-build-gate/                # Build verification pipeline
    # Desktop & Game Dev
    desktop-ui-designer/                # PyQt6/PySide6 desktop apps
    pyqt6-ui-debugger/                  # PyQt6 layout debugging
    python-code-reviewer/               # Python standards review
    ue5-blueprint-organization/         # UE5 Blueprint best practices
    vault-analysis/                     # Vault/security analysis
  scripts/
    agent_event_bus.py                  # Typed pub/sub for inter-agent communication
    agent_events.py                     # Event dataclasses
    agent_runtime.py                    # Agent orchestration
    skill_isolator.py                   # Per-agent skill manifests (path-traversal hardened)
    agents/                             # Extractor, validator, refactor, sync, pruner agents
  tests/                                # Unit and security tests
  tasks/                                # Task template checklists
  setup.sh                              # Linux/macOS/Git Bash installer
  setup.ps1                             # Windows PowerShell installer
```

## Multi-Machine Sync

1. Push changes from any machine: `git add -A && git commit -m "update skills" && git push`
2. Pull on other machine: `git pull && ./setup.sh`

That's it. Both machines stay in sync.

## Sources & Attribution

Skills in this repository draw from patterns and techniques in these community projects:

- [Anthropic Skills](https://github.com/anthropics/skills) - Official skill specifications (pdf, xlsx, pptx, doc-coauthoring, frontend-design, skill-creator)
- [Superpowers](https://github.com/obra/superpowers) - TDD, systematic debugging, subagent-driven development
- [Marketing Skills](https://github.com/coreyhaines31/marketingskills) - Foundation-first marketing patterns
- [Context Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) - Context optimization and memory systems
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher) - Deep research pipeline architecture
- [Karpathy autoresearch](https://github.com/karpathy/autoresearch) - Autonomous experiment loop pattern
- [Obsidian Skills](https://github.com/kepano/obsidian-skills) - Vault management patterns
- [promptfoo](https://github.com/promptfoo/promptfoo) - Prompt testing and evaluation
- [Remotion](https://github.com/remotion-dev/remotion) - Programmatic video creation

## License

MIT
