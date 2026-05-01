# test_bootstrap.py
# Marcus Daley — 2026-05-01 — Unit tests for bootstrap scaffold generator

import pytest
from pathlib import Path

from bootstrap import scaffold_project, validate_target_path, ScaffoldError

TEMPLATES_DIR = Path(__file__).parents[3] / "skills" / "ai-agents" / "autonomous-workflow" / "templates"


def test_validate_target_path_rejects_traversal(tmp_path):
    with pytest.raises(ScaffoldError, match="traversal"):
        validate_target_path(tmp_path, "../../../etc/passwd")


def test_validate_target_path_accepts_relative(tmp_path):
    result = validate_target_path(tmp_path, "my-project/workflow")
    assert result == tmp_path / "my-project" / "workflow"


def test_scaffold_creates_expected_structure(tmp_path):
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    for subdir in ["workflows", "tasks", "skills", "orchestrator", "state"]:
        assert (tmp_path / "my-project" / subdir).is_dir(), f"Missing: {subdir}/"


def test_scaffold_copies_templates(tmp_path):
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    assert (tmp_path / "my-project" / "workflows" / "workflow.md").exists()
    assert (tmp_path / "my-project" / "tasks" / "task.md").exists()
    assert (tmp_path / "my-project" / "skills" / "skill-template.md").exists()


def test_scaffold_state_dir_is_empty(tmp_path):
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    state_dir = tmp_path / "my-project" / "state"
    assert state_dir.is_dir()
    assert not (state_dir / "workflow_state.json").exists()


def test_scaffold_is_idempotent(tmp_path):
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    scaffold_project(target_dir=tmp_path / "my-project", templates_dir=TEMPLATES_DIR)
    assert (tmp_path / "my-project" / "workflows" / "workflow.md").exists()


def test_validate_target_path_rejects_prefix_sibling(tmp_path):
    """Sibling directory whose name is a string prefix of base must be rejected."""
    sibling = "../" + tmp_path.name + "-evil"
    with pytest.raises(ScaffoldError, match="traversal"):
        validate_target_path(tmp_path, sibling)
