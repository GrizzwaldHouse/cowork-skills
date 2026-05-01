# AIArchGuide — Plan & UI Influence Notes
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Plan file for the AI Architecture Field Guide component.
#          Captures design decisions and UI influence for the AgenticOS HUD.

## Source Component
The AIArchGuide.jsx component (provided by Marcus) is a standalone React
interactive guide covering 8 AI architectures with a Grizzwald Workshop theme.

## Integration Plan

### Phase A — Standalone (done)
The component is complete as-is. Save as:
`C:\ClaudeSkills\AgenticOS\frontend\src\components\AIArchGuide.tsx`

Convert from .jsx to .tsx with proper TypeScript types.

### Phase B — AgenticOS HUD Influence
The AIArchGuide informs the AgenticOS UI in these ways:

1. **Agent domain colors** — each AgentDomain maps to an arch color:
   - `game-dev` → #10b981 (Mamba green — real-time, fast)
   - `software-eng` → #f59e0b (Transformer amber — reasoning)
   - `va-advisory` → #06b6d4 (GNN cyan — relationship graphs)
   - `3d-content` → #ec4899 (Diffusion pink — generative art)
   - `general` → #8b5cf6 (RWKV purple — hybrid)

2. **PhaseCard styling** — the "Submarine Analogy" card style from AIArchGuide
   (dark bg, colored left border, italic quote text) influences the PhaseCard
   layout directly.

3. **SkillBadge** — styled like the AIArchGuide's `.chip` component but smaller
   and interactive.

4. **MobileApproval buttons** — large, full-width, inspired by the roadmap
   phase cards in AIArchGuide's "Your AI Roadmap" tab.

## Models Referenced (from AIArchGuide)

| Architecture | Use in AgenticOS |
|---|---|
| Transformer (Ollama) | Default Ollama handoff model |
| Mamba/SSM | Future: real-time session stream analysis |
| RWKV | Future: streaming agent commentary |
| Diffusion | Future: auto-generate AgentCard thumbnails |
| GNN | Future: project dependency graph visualization |
| RL | Future: auto-tune stuck detection thresholds |
| MoE Hybrid | Future: route handoff tasks to best local model |

## Skill Package Reference
The `agentic-hub` skill package references this plan.
Models to use for Ollama handoff (configurable via OLLAMA_HANDOFF_MODEL env var):

- **Default**: `codellama:13b` — strong at code continuation
- **Fast/cheap**: `qwen2.5-coder:7b` — good enough for simple tasks
- **High quality**: `deepseek-r1:14b` — best reasoning for complex tasks
- **Specialist**: `qwen2.5-coder:32b` — for large refactoring tasks

## Next Steps
1. Convert AIArchGuide.jsx → AIArchGuide.tsx (add TypeScript types)
2. Add a `/guide` route to the React frontend
3. Wire domain color constants from AIArchGuide into AgentCard.tsx
4. Add model selector to handoff_runner.py UI
