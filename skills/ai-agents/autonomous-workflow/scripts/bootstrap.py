# bootstrap.py
# Marcus Daley — 2026-05-01 — Runtime scaffold generator for autonomous-workflow

import shutil
from pathlib import Path

SCAFFOLD_DIRS = ["workflows", "tasks", "skills", "orchestrator", "state"]

TEMPLATE_MAP = {
    "workflow.md": "workflows",
    "task.md": "tasks",
    "skill-template.md": "skills",
}


class ScaffoldError(ValueError):
    pass


def validate_target_path(base: Path, relative: str) -> Path:
    """Resolve relative path under base and reject any path traversal."""
    resolved = (base / relative).resolve()
    base_resolved = base.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise ScaffoldError(f"Path traversal detected in: {relative!r}")
    return resolved


def scaffold_project(target_dir: Path, templates_dir: Path) -> None:
    """Create the runtime scaffold directory structure under target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)

    for subdir in SCAFFOLD_DIRS:
        (target_dir / subdir).mkdir(exist_ok=True)

    for template_file, dest_subdir in TEMPLATE_MAP.items():
        src = templates_dir / template_file
        dst = target_dir / dest_subdir / template_file
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
