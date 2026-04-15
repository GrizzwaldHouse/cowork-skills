# pruner_agent.py
# Developer: Marcus Daley
# Date: 2026-04-06
# Purpose: Pruner agent — manages skill lifecycle, loads/unloads skills based on task needs

from __future__ import annotations

import json
import logging
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.agent_base import BaseAgent
from scripts.agent_event_bus import EventBus
from scripts.agent_events import (
    TaskStartEvent,
    TaskCompleteEvent,
    SkillLoadRequestEvent,
    SkillUnloadRequestEvent,
    SkillRegistryUpdatedEvent,
)

logger = logging.getLogger("agent.pruner")

_DEFAULT_PRUNER_CONFIG_PATH: Path = Path("C:/ClaudeSkills/config/pruner_config.json")


class PrunerAgent(BaseAgent):
    """Self-pruning skill orchestrator.

    Subscribes to task lifecycle events and dynamically loads/unloads skills
    to keep the active skill set under max_active_skills (default 15).

    Skill resolution priority for loading:
        temp_cache_dir -> source_skills_dir -> active_skills_dir -> GitHub fallback

    Unloading moves skills to temp_cache_dir (not deletion) so they can be
    quickly restored on the next task that needs them.
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(name="pruner-agent", agent_type="pruner")
        self._event_bus: EventBus = event_bus

        # State lock — separate from BaseAgent's _lock (which is non-reentrant
        # and used by _record_processed/_record_emitted). Keeping the locks
        # separate avoids deadlock when handlers call those metric helpers.
        self._state_lock: threading.Lock = threading.Lock()
        self._pruner_config: dict[str, Any] = {}
        self._bundles: dict[str, Any] = {}
        self._registry: dict[str, Any] = {}
        self._predictive: Any = None  # PredictiveLoader instance

        # Resolved paths (set in on_configure)
        self._active_dir: Path = Path()
        self._source_dir: Path = Path()
        self._temp_dir: Path = Path()
        self._registry_path: Path = Path()
        self._usage_log_path: Path = Path()
        self._handoff_path: Path = Path()
        self._max_active: int = 15
        self._core_bundle: str = "core"

    # -- Lifecycle hooks ----------------------------------------------------

    def on_configure(self, config: dict[str, Any]) -> None:
        """Load pruner config, registry, bundles, and subscribe to events."""
        self._pruner_config = self._load_pruner_config()
        self._bundles = self._load_bundles()
        self._registry = self._load_registry()

        # Resolve all paths from config
        self._active_dir = Path(self._pruner_config["active_skills_dir"])
        self._source_dir = Path(self._pruner_config["source_skills_dir"])
        self._temp_dir = Path(self._pruner_config["temp_cache_dir"])
        self._registry_path = Path(self._pruner_config["registry_path"])
        self._usage_log_path = Path(self._pruner_config["usage_log_path"])
        self._handoff_path = Path(self._pruner_config["handoff_path"])
        self._max_active = int(self._pruner_config.get("max_active_skills", 15))
        self._core_bundle = self._pruner_config.get("core_bundle", "core")

        # Ensure temp cache directory exists
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        # Lazy import — avoid circular dependency
        from scripts.predictive_loader import PredictiveLoader
        self._predictive = PredictiveLoader(self._registry, self._pruner_config)

        # Subscribe to lifecycle events
        self._event_bus.subscribe(TaskStartEvent, self._handle_task_start)
        self._event_bus.subscribe(TaskCompleteEvent, self._handle_task_complete)
        self._event_bus.subscribe(SkillLoadRequestEvent, self._handle_load_request)
        self._event_bus.subscribe(SkillUnloadRequestEvent, self._handle_unload_request)

        logger.info(
            "PrunerAgent configured: max_active=%d, bundles=%d, registry_skills=%d",
            self._max_active,
            len(self._bundles.get("bundles", {})),
            len(self._registry.get("skills", {})),
        )

    def on_stop(self) -> None:
        """Unsubscribe and persist registry on shutdown."""
        self._event_bus.unsubscribe(TaskStartEvent, self._handle_task_start)
        self._event_bus.unsubscribe(TaskCompleteEvent, self._handle_task_complete)
        self._event_bus.unsubscribe(SkillLoadRequestEvent, self._handle_load_request)
        self._event_bus.unsubscribe(SkillUnloadRequestEvent, self._handle_unload_request)
        self._save_registry()

    # -- Event handlers -----------------------------------------------------

    def _handle_task_start(self, event: TaskStartEvent) -> None:
        """Resolve required skills, load missing ones, enforce max_active limit."""
        if self.status.value != "running":
            return

        try:
            self._record_processed()
            with self._state_lock:
                # Resolve required skills (expand bundle names if any)
                required: set[str] = set()
                for item in event.required_skills:
                    if item in self._bundles.get("bundles", {}):
                        required.update(self._resolve_bundle(item))
                    else:
                        required.add(item)

                # Always include core bundle
                required.update(self._resolve_bundle(self._core_bundle))

                # Find which are missing from active dir
                active_now = self._scan_active_skills()
                missing = required - active_now

                loaded: list[str] = []
                for skill in missing:
                    if self._load_skill(skill):
                        loaded.append(skill)

                # Enforce max_active_skills (evict LRU non-core if over limit)
                active_after = self._scan_active_skills()
                overflow = len(active_after) - self._max_active
                evicted: list[str] = []
                if overflow > 0:
                    evicted = self._evict_lru(overflow, protected=required)

                # Predictive preloading — fill remaining slots with co-occurrence picks
                final_active = self._scan_active_skills()
                free_slots = self._max_active - len(final_active)
                preloaded: list[str] = []
                if free_slots > 0 and self._predictive:
                    candidates = self._predictive.get_preload_candidates(
                        list(final_active), free_slots
                    )
                    for skill in candidates:
                        if self._load_skill(skill):
                            preloaded.append(skill)

                self._update_usage_log([
                    f"## {datetime.now(timezone.utc).isoformat()} - Task: {event.task_name}",
                    f"- LOADED: {', '.join(loaded) if loaded else '(none)'}",
                    f"- PRELOADED: {', '.join(preloaded) if preloaded else '(none)'}",
                    f"- EVICTED: {', '.join(evicted) if evicted else '(none)'}",
                    f"- Active: {len(self._scan_active_skills())}/{self._max_active}",
                    "",
                ])
                self._save_registry()
                self._update_handoff()

            self._event_bus.publish(SkillRegistryUpdatedEvent(
                action="load",
                skills=tuple(loaded + preloaded),
                active_count=len(self._scan_active_skills()),
            ))
            self._record_emitted()

            logger.info(
                "Task '%s': loaded=%d preloaded=%d evicted=%d active=%d",
                event.task_name, len(loaded), len(preloaded),
                len(evicted), len(self._scan_active_skills()),
            )

        except Exception as exc:
            self._set_error(f"task_start handler failed: {exc}")
            logger.exception("PrunerAgent error on TaskStartEvent")

    def _handle_task_complete(self, event: TaskCompleteEvent) -> None:
        """Mark unused skills for pruning, update usage stats, run preloading."""
        if self.status.value != "running":
            return

        try:
            self._record_processed()
            with self._state_lock:
                used = set(event.skills_used)
                active = self._scan_active_skills()
                core_skills = set(self._resolve_bundle(self._core_bundle))

                # Update usage_count and last_used for skills that were used
                now_iso = datetime.now(timezone.utc).isoformat()
                skills_data = self._registry.setdefault("skills", {})
                for skill in used:
                    entry = skills_data.setdefault(skill, {})
                    entry["usage_count"] = int(entry.get("usage_count", 0)) + 1
                    entry["last_used"] = now_iso
                    skills_data[skill] = entry

                # Update co-occurrence matrix via PredictiveLoader
                if self._predictive and len(used) >= 2:
                    self._registry = self._predictive.update_co_occurrence(
                        self._registry, list(used)
                    )

                # Identify unused (active but not used and not core)
                unused = active - used - core_skills
                unloaded: list[str] = []
                for skill in unused:
                    if self._unload_skill(skill):
                        unloaded.append(skill)

                self._update_usage_log([
                    f"## {datetime.now(timezone.utc).isoformat()} - Task Complete: {event.task_name}",
                    f"- USED: {', '.join(sorted(used)) if used else '(none)'}",
                    f"- UNLOADED: {', '.join(unloaded) if unloaded else '(none)'}",
                    f"- Active: {len(self._scan_active_skills())}/{self._max_active}",
                    f"- Duration: {event.duration_seconds:.1f}s",
                    "",
                ])
                self._save_registry()
                self._update_handoff()

            self._event_bus.publish(SkillRegistryUpdatedEvent(
                action="unload",
                skills=tuple(unloaded),
                active_count=len(self._scan_active_skills()),
            ))
            self._record_emitted()

            logger.info(
                "Task complete '%s': unloaded=%d active=%d",
                event.task_name, len(unloaded), len(self._scan_active_skills()),
            )

        except Exception as exc:
            self._set_error(f"task_complete handler failed: {exc}")
            logger.exception("PrunerAgent error on TaskCompleteEvent")

    def _handle_load_request(self, event: SkillLoadRequestEvent) -> None:
        """Manually load skills or a bundle into the active set."""
        if self.status.value != "running":
            return

        try:
            self._record_processed()
            with self._state_lock:
                targets: set[str] = set(event.skill_names)
                if event.bundle_name:
                    targets.update(self._resolve_bundle(event.bundle_name))

                loaded: list[str] = []
                for skill in targets:
                    if self._load_skill(skill):
                        loaded.append(skill)

                self._save_registry()
                self._update_handoff()

            self._event_bus.publish(SkillRegistryUpdatedEvent(
                action="load",
                skills=tuple(loaded),
                active_count=len(self._scan_active_skills()),
            ))
            self._record_emitted()

            logger.info(
                "Load request: bundle=%s reason=%s loaded=%d",
                event.bundle_name, event.reason, len(loaded),
            )

        except Exception as exc:
            self._set_error(f"load_request handler failed: {exc}")
            logger.exception("PrunerAgent error on SkillLoadRequestEvent")

    def _handle_unload_request(self, event: SkillUnloadRequestEvent) -> None:
        """Manually unload skills (move them to temp cache)."""
        if self.status.value != "running":
            return

        try:
            self._record_processed()
            with self._state_lock:
                core_skills = set(self._resolve_bundle(self._core_bundle))
                unloaded: list[str] = []
                for skill in event.skill_names:
                    if skill in core_skills:
                        logger.debug("Skipping core skill: %s", skill)
                        continue
                    if self._unload_skill(skill):
                        unloaded.append(skill)

                self._save_registry()
                self._update_handoff()

            self._event_bus.publish(SkillRegistryUpdatedEvent(
                action="unload",
                skills=tuple(unloaded),
                active_count=len(self._scan_active_skills()),
            ))
            self._record_emitted()

            logger.info(
                "Unload request: reason=%s unloaded=%d",
                event.reason, len(unloaded),
            )

        except Exception as exc:
            self._set_error(f"unload_request handler failed: {exc}")
            logger.exception("PrunerAgent error on SkillUnloadRequestEvent")

    # -- Skill resolution helpers -------------------------------------------

    def _resolve_bundle(self, bundle_name: str) -> list[str]:
        """Expand a bundle name to its list of skill names."""
        bundle = self._bundles.get("bundles", {}).get(bundle_name, {})
        return list(bundle.get("skills", []))

    def _scan_active_skills(self) -> set[str]:
        """Return the set of skill names currently in the active directory."""
        if not self._active_dir.exists():
            return set()
        return {p.name for p in self._active_dir.iterdir()}

    def _load_skill(self, skill_name: str) -> bool:
        """Copy a skill from temp_cache or source dir into the active dir.

        Resolution order: temp_cache_dir -> source_skills_dir.
        Returns True if the skill is now active.
        """
        target = self._active_dir / skill_name
        if target.exists():
            return True  # Already active

        # Try temp cache first (move back, faster)
        cached = self._temp_dir / skill_name
        if cached.exists():
            try:
                shutil.move(str(cached), str(target))
                self._update_registry_status(skill_name, "active")
                logger.debug("Restored '%s' from temp cache", skill_name)
                return True
            except OSError as exc:
                logger.warning("Failed to restore '%s': %s", skill_name, exc)

        # Try source dir (copy)
        source = self._source_dir / skill_name
        if source.exists():
            try:
                if source.is_dir():
                    shutil.copytree(str(source), str(target))
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(source), str(target))
                self._update_registry_status(skill_name, "active")
                logger.debug("Copied '%s' from source dir", skill_name)
                return True
            except OSError as exc:
                logger.warning("Failed to copy '%s': %s", skill_name, exc)

        # GitHub fallback would go here (out of scope for initial implementation)
        if self._pruner_config.get("fail_fast_on_missing", True):
            logger.warning("Skill not found in any source: '%s'", skill_name)
        return False

    def _unload_skill(self, skill_name: str) -> bool:
        """Move a skill from active dir to temp cache."""
        source = self._active_dir / skill_name
        if not source.exists():
            return False

        target = self._temp_dir / skill_name
        # If something already exists in cache, remove it first
        if target.exists():
            try:
                if target.is_dir():
                    shutil.rmtree(str(target))
                else:
                    target.unlink()
            except OSError as exc:
                logger.warning("Failed to clear cache slot for '%s': %s", skill_name, exc)
                return False

        try:
            shutil.move(str(source), str(target))
            self._update_registry_status(skill_name, "cached")
            logger.debug("Cached '%s'", skill_name)
            return True
        except OSError as exc:
            logger.warning("Failed to cache '%s': %s", skill_name, exc)
            return False

    def _evict_lru(self, count: int, protected: set[str]) -> list[str]:
        """Evict the N least-recently-used non-protected skills."""
        if count <= 0:
            return []

        active = self._scan_active_skills()
        core_skills = set(self._resolve_bundle(self._core_bundle))
        skills_data = self._registry.get("skills", {})

        # Build (last_used, skill_name) pairs for eviction candidates
        candidates: list[tuple[str, str]] = []
        for skill in active:
            if skill in protected or skill in core_skills:
                continue
            last_used = skills_data.get(skill, {}).get("last_used", "")
            candidates.append((last_used, skill))

        # Sort: empty last_used (never used) comes first, then oldest
        candidates.sort(key=lambda pair: (pair[0] or "", pair[1]))

        evicted: list[str] = []
        for _, skill in candidates[:count]:
            if self._unload_skill(skill):
                evicted.append(skill)
        return evicted

    def _update_registry_status(self, skill_name: str, status: str) -> None:
        """Set the status field on a registry entry, creating it if needed."""
        skills_data = self._registry.setdefault("skills", {})
        entry = skills_data.setdefault(skill_name, {})
        entry["status"] = status
        if status == "active":
            entry.setdefault("path", str(self._active_dir / skill_name))
        skills_data[skill_name] = entry

    # -- Persistence helpers ------------------------------------------------

    def _load_pruner_config(self) -> dict[str, Any]:
        """Load pruner_config.json. Raises if missing — pruner can't run without it."""
        if not _DEFAULT_PRUNER_CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Pruner config not found: {_DEFAULT_PRUNER_CONFIG_PATH}"
            )
        return json.loads(_DEFAULT_PRUNER_CONFIG_PATH.read_text(encoding="utf-8"))

    def _load_bundles(self) -> dict[str, Any]:
        """Load skill_bundles.json. Returns empty if missing."""
        path = Path(self._pruner_config.get("bundles_path", ""))
        if not path.exists():
            logger.warning("Bundles file not found: %s", path)
            return {"bundles": {}}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load bundles: %s", exc)
            return {"bundles": {}}

    def _load_registry(self) -> dict[str, Any]:
        """Load skill_registry.json. Returns empty registry if missing."""
        path = Path(self._pruner_config.get("registry_path", ""))
        if not path.exists():
            return {
                "schema_version": "1.0",
                "max_active_skills": self._pruner_config.get("max_active_skills", 15),
                "last_updated": "",
                "skills": {},
            }
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load registry: %s", exc)
            return {"schema_version": "1.0", "skills": {}}

    def _save_registry(self) -> None:
        """Persist the registry to disk."""
        try:
            self._registry["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._registry_path.parent.mkdir(parents=True, exist_ok=True)
            self._registry_path.write_text(
                json.dumps(self._registry, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to save registry: %s", exc)

    def _update_usage_log(self, lines: list[str]) -> None:
        """Append entries to the usage log markdown file."""
        try:
            self._usage_log_path.parent.mkdir(parents=True, exist_ok=True)
            existing = ""
            if self._usage_log_path.exists():
                existing = self._usage_log_path.read_text(encoding="utf-8")
            else:
                existing = "# Skill Usage Log\n\n"
            with self._usage_log_path.open("a", encoding="utf-8") as fh:
                if not existing.endswith("\n"):
                    fh.write("\n")
                fh.write("\n".join(lines))
                fh.write("\n")
        except OSError as exc:
            logger.warning("Failed to update usage log: %s", exc)

    def _update_handoff(self) -> None:
        """Rewrite the HANDOFF.md file with current state."""
        try:
            active = sorted(self._scan_active_skills())
            cached: list[str] = []
            if self._temp_dir.exists():
                cached = sorted(p.name for p in self._temp_dir.iterdir())

            core_skills = set(self._resolve_bundle(self._core_bundle))
            core_active = sorted(s for s in active if s in core_skills)
            other_active = sorted(s for s in active if s not in core_skills)

            lines = [
                "# Session Handoff",
                "",
                f"## Active Skills ({len(active)}/{self._max_active})",
                f"- core: {', '.join(core_active) if core_active else '(none)'}",
                f"- task: {', '.join(other_active) if other_active else '(none)'}",
                "",
                f"## Cached Skills ({len(cached)})",
                f"- {', '.join(cached) if cached else '(none)'}",
                "",
                f"_Last updated: {datetime.now(timezone.utc).isoformat()}_",
                "",
            ]
            self._handoff_path.parent.mkdir(parents=True, exist_ok=True)
            self._handoff_path.write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to update handoff: %s", exc)
