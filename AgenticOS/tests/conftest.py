# conftest.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Pytest fixtures and import-path setup shared by every test
#          module in this folder. Ensures C:\ClaudeSkills is on
#          sys.path so ``from AgenticOS....`` imports resolve when
#          pytest is invoked from inside AgenticOS or from anywhere
#          else on the workstation.

from __future__ import annotations

import sys
from pathlib import Path

# The AgenticOS package lives one directory up from this tests folder.
# Its parent (C:\ClaudeSkills) must be importable, so we prepend it.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
