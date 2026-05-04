# skill_actions.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Project-skill dispatch helpers for the AgenticOS command panel.
#          A button click becomes a canonical AgenticOS task, so existing
#          watchers, task cards, and agent-state streams can observe the work.

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from AgenticOS.models import AgenticTask, TaskStatus
from AgenticOS.task_store import log_event, write_snapshot, write_task


@dataclass(frozen=True)
class SkillAction:
    """One command-panel skill action exposed to the frontend."""

    slug: str
    label: str
    description: str
    default_objective: str
    agent_id: str


_DEFAULT_PROJECT_ROOT = Path("C:/Users/daley/Projects/SeniorDevBuddy")
_GLOBAL_SKILL_ROOT = Path("C:/ClaudeSkills/skills")

_ACTIONS: dict[str, SkillAction] = {
    "agentforge-agent-contracts": SkillAction(
        slug="agentforge-agent-contracts",
        label="Agent Contracts",
        description="Agent interfaces, outputs, registry wiring, and tests.",
        default_objective="Inspect the AgentForge agent contract surface and make the requested agent change safely.",
        agent_id="skill-agent-contracts",
    ),
    "agentforge-model-routing": SkillAction(
        slug="agentforge-model-routing",
        label="Model Routing",
        description="Provider ranking, fallback, health, budget, and task classification.",
        default_objective="Inspect the AgentForge model-routing surface and make the requested routing change safely.",
        agent_id="skill-agent-routing",
    ),
    "agentforge-safety-policy": SkillAction(
        slug="agentforge-safety-policy",
        label="Safety Policy",
        description="Safety gates, approvals, kill switch, audit logs, and guarded automation.",
        default_objective="Inspect the AgentForge safety-policy surface and make the requested safety change conservatively.",
        agent_id="skill-agent-safety",
    ),
}


def list_skill_actions(project_path: str | None = None) -> list[dict[str, Any]]:
    """Return command-panel actions with resolved skill paths.

    Parameters:
        project_path: Optional project root selected in the AgenticOS UI.
            When provided, project-local skills are preferred.

    Returns:
        list[dict[str, Any]]: UI-ready action records containing labels,
        agent ids, resolved skill paths, and availability flags.

    Notes:
        This is read-only. It never creates tasks or modifies project files,
        so the frontend can poll or refresh it freely.
    """
    return [
        {
            "slug": action.slug,
            "label": action.label,
            "description": action.description,
            "default_objective": action.default_objective,
            "agent_id": action.agent_id,
            "skill_path": str(resolve_skill_path(action.slug, project_path)),
            "available": resolve_skill_path(action.slug, project_path).exists(),
        }
        for action in _ACTIONS.values()
    ]


def dispatch_skill_action(
    slug: str,
    *,
    objective: str | None,
    project_path: str | None,
    project_name: str | None,
) -> dict[str, Any]:
    """Create one canonical task for a skill-backed agent workflow.

    Parameters:
        slug: Skill action slug, such as ``agentforge-safety-policy``.
        objective: Operator-written goal from the command panel. Empty
            values fall back to the action's default objective.
        project_path: Optional selected project root. Defaults to the
            SeniorDevBuddy workspace when omitted.
        project_name: Optional display name for the selected project.

    Returns:
        dict[str, Any]: Dispatch payload containing the selected action,
        the serialized AgenticOS task, and the generated prompt checkpoint.

    Raises:
        KeyError: If ``slug`` is not one of the registered skill actions.
        TaskRuntimeError: Propagated from the task store if the canonical
            task runtime cannot persist the new task.

    Notes:
        The function does not run the agent itself. It creates a watched
        task so AgenticOS' existing filesystem watcher and dashboard bridge
        can display progress as workers claim/checkpoint/complete it.
    """
    action = _ACTIONS.get(slug)
    if action is None:
        raise KeyError(f"Unknown skill action: {slug}")

    clean_objective = (objective or "").strip() or action.default_objective
    resolved_project_path = str(Path(project_path).resolve()) if project_path else str(_DEFAULT_PROJECT_ROOT)
    resolved_project_name = project_name or Path(resolved_project_path).name
    skill_path = resolve_skill_path(slug, resolved_project_path)
    now = datetime.now(timezone.utc)
    task_id = _build_task_id(slug, now)
    prompt = build_skill_prompt(
        action=action,
        objective=clean_objective,
        project_path=resolved_project_path,
        project_name=resolved_project_name,
        skill_path=skill_path,
        task_id=task_id,
    )

    task = AgenticTask(
        id=task_id,
        title=f"{action.label}: {_shorten(clean_objective, 96)}",
        status=TaskStatus.PENDING,
        assigned_to=action.agent_id,
        dependencies=[],
        priority=1,
        locked_by=None,
        created_at=now,
        updated_at=now,
        checkpoints=[
            {
                "agent_id": "agentic-os-command-panel",
                "created_at": now.isoformat(),
                "kind": "skill-dispatch",
                "skill": slug,
                "skill_path": str(skill_path),
                "project_path": resolved_project_path,
                "prompt": prompt,
            }
        ],
        output=None,
    )

    write_task(task)
    log_event(f"DISPATCHED {task_id} to {action.agent_id} via {slug}")
    write_snapshot()

    return {
        "action": list_skill_actions(resolved_project_path)[
            list(_ACTIONS).index(slug)
        ],
        "task": task.model_dump(mode="json"),
        "prompt": prompt,
    }


def resolve_skill_path(slug: str, project_path: str | None = None) -> Path:
    """Resolve the best available SKILL.md path for a slug.

    Parameters:
        slug: Skill folder name to resolve.
        project_path: Optional selected project root whose ``skills`` folder
            should be searched first.

    Returns:
        Path: Existing SKILL.md path when found, otherwise the first
        project-local candidate where the skill would be expected.

    Notes:
        Search order intentionally favors project-local skills so a repo can
        override or pin behavior without changing the global skill library.
    """
    candidates: list[Path] = []
    if project_path:
        candidates.append(Path(project_path) / "skills" / slug / "SKILL.md")
    candidates.extend(
        [
            _DEFAULT_PROJECT_ROOT / "skills" / slug / "SKILL.md",
            _GLOBAL_SKILL_ROOT / slug / "SKILL.md",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_skill_prompt(
    *,
    action: SkillAction,
    objective: str,
    project_path: str,
    project_name: str,
    skill_path: Path,
    task_id: str,
) -> str:
    """Build the task prompt stored in the task checkpoint.

    Parameters:
        action: Registered skill action metadata.
        objective: Operator-written work objective.
        project_path: Absolute path to the target project.
        project_name: Human-readable project name.
        skill_path: Resolved path to the skill's SKILL.md file.
        task_id: Canonical AgenticOS task id created for this dispatch.

    Returns:
        str: Prompt text suitable for a worker agent to execute.

    Notes:
        The prompt is designed for token discipline: load the named skill,
        inspect only task-relevant files, checkpoint progress, and report a
        concise result.
    """
    return "\n".join(
        [
            f"Use ${action.slug} at {skill_path} to work on {project_name}.",
            "",
            f"Project path: {project_path}",
            f"AgenticOS task id: {task_id}",
            "",
            "Objective:",
            objective,
            "",
            "Execution contract:",
            "1. Load the skill body first, then only the referenced files needed for this task.",
            "2. Work inside the selected project unless the user explicitly asks otherwise.",
            "3. Update the AgenticOS task with checkpoints as meaningful progress is made.",
            "4. Run focused verification and report skipped checks with the reason.",
            "5. Keep the final output concise: files changed, tests run, result, and next action.",
        ]
    )


def _build_task_id(slug: str, now: datetime) -> str:
    """Create a stable, filesystem-safe task id for one dispatch.

    Parameters:
        slug: Skill slug being dispatched.
        now: UTC timestamp used to make the id unique.

    Returns:
        str: Task id in the form ``skill-{slug}-{yyyymmddHHMMSS}``.

    Notes:
        The timestamp is second-level precision because UI button clicks are
        human paced; if later automation dispatches multiple tasks per second,
        append a short random suffix here.
    """
    safe_slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    timestamp = now.strftime("%Y%m%d%H%M%S")
    return f"skill-{safe_slug}-{timestamp}"


def _shorten(value: str, limit: int) -> str:
    """Trim text for compact task titles.

    Parameters:
        value: Original text.
        limit: Maximum returned character count.

    Returns:
        str: ``value`` unchanged when it fits, otherwise a shortened string
        ending in ``...``.

    Notes:
        This affects only the dashboard title. The full objective remains in
        the generated prompt checkpoint.
    """
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."
