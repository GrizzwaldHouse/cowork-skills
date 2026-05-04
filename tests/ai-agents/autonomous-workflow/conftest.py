# tests/ai-agents/autonomous-workflow/conftest.py
# Marcus Daley — 2026-05-01 — Shared test configuration for autonomous-workflow

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "skills" / "ai-agents" / "autonomous-workflow" / "scripts"))
