# Cowork Skills

Claude Code skills and task templates for professional design, document generation, AI workflows, and game development.

## Quick Setup

Clone this repo on any machine, then run the setup script to install skills globally:

```bash
# Clone
git clone https://github.com/daley/cowork-skills.git
cd cowork-skills

# Install (Linux/macOS/Git Bash)
./setup.sh

# Install (Windows PowerShell)
.\setup.ps1
```

Skills install to `~/.claude/skills/` and are available in **all** Claude Code sessions on that machine.

To update: `git pull && ./setup.sh`

## Skills

### design-system (auto-loaded)
Foundational design principles applied automatically to all visual and document tasks.
- Color theory (WCAG contrast, 60-30-10 rule, 6 ready-to-use palettes)
- Typography (font pairings, type scale, readability rules)
- Layout (8px grid, 12-column system, composition patterns)
- Accessibility standards

### canva-designer (invoke with `/canva-designer`)
Canva-specific prompt engineering for higher quality design generation.
- Query templates for every design type (logo, presentation, poster, social media)
- Platform dimensions reference (Instagram, LinkedIn, YouTube, print, etc.)
- Quality checklist for pre-commit review

### document-designer (auto-loaded)
Professional formatting for Excel, Word, PowerPoint, and PDF generation.
- Excel: sheet organization, data formatting, dashboard patterns
- Word: memo, report, proposal, meeting minutes templates
- PowerPoint: 6x6 rule, slide templates, content writing rules
- PDF: layout standards, document type templates

## Task Templates

Pre-built task checklists for common workflows:

| Category | File | What's Included |
|----------|------|-----------------|
| App Development | `tasks/app-development/tasks.md` | Feature implementation, bug fixes, UI upgrades, API endpoints, deployment |
| AI Workflows | `tasks/ai-workflows/tasks.md` | Canva generation, document creation, prompt engineering, agent safety review |
| Game Development | `tasks/game-development/tasks.md` | Level design, Unreal Blueprints, AI agents, HUD/UI, multiplayer, optimization |

## How It Works

**Background skills** (`design-system`, `document-designer`) load automatically whenever Claude detects a relevant task. You don't need to do anything.

**User-invocable skills** (`canva-designer`) are triggered by typing the slash command in Claude Code:
```
/canva-designer
```

**Task templates** are reference checklists. Copy the relevant section into your project or reference them when planning work.

## Structure

```
cowork-skills/
  skills/
    design-system/        # Color, typography, layout, accessibility
    canva-designer/       # Canva prompt engineering & quality review
    document-designer/    # Excel, Word, PPT, PDF best practices
  tasks/
    app-development/      # Feature dev, bug fix, UI upgrade, API, deploy
    ai-workflows/         # Design gen, doc creation, prompt eng, safety
    game-development/     # Level design, Unreal, AI, HUD, multiplayer
  setup.sh                # Linux/macOS/Git Bash installer
  setup.ps1               # Windows PowerShell installer
```

## Multi-Machine Sync

1. Push changes from any machine: `git add -A && git commit -m "update skills" && git push`
2. Pull on other machine: `git pull && ./setup.sh`

That's it. Both machines stay in sync.

## License

MIT
