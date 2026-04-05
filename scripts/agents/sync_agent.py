# sync_agent.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Sync agent — installs approved skills and triggers distribution

from __future__ import annotations

import logging
from typing import Any

from scripts.agent_base import BaseAgent
from scripts.agent_events import (
    SkillValidatedEvent,
    SkillSyncedEvent,
)
from scripts.agent_event_bus import EventBus

logger = logging.getLogger("agent.sync")


class SyncAgent(BaseAgent):
    """Installs approved skills and triggers sync distribution.

    Wraps AdminControlProtocol (governance gate), OpenModelManager
    (skill installation), and Broadcaster (distribution sync).
    Only processes skills with 'approved' disposition.
    """

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(name="sync-agent", agent_type="sync")
        self._event_bus: EventBus = event_bus
        self._admin: Any = None         # AdminControlProtocol instance
        self._model_manager: Any = None  # OpenModelManager instance

    # -- Lifecycle hooks ---------------------------------------------------

    def on_configure(self, config: dict[str, Any]) -> None:
        """Instantiate governance and installation modules."""
        from scripts.admin_protocol import AdminControlProtocol
        from scripts.open_model_manager import OpenModelManager

        self._admin = AdminControlProtocol(config)
        self._model_manager = OpenModelManager()

        self._event_bus.subscribe(SkillValidatedEvent, self._handle_validated)

    def on_stop(self) -> None:
        """Unsubscribe from events on shutdown."""
        self._event_bus.unsubscribe(SkillValidatedEvent, self._handle_validated)

    # -- Event handler -----------------------------------------------------

    def _handle_validated(self, event: SkillValidatedEvent) -> None:
        """Process approved skills through governance and installation.

        Steps:
        1. Submit through AdminControlProtocol for audit trail
        2. Install via OpenModelManager to all install targets
        3. Trigger Broadcaster.full_sync() for distribution
        4. Publish SkillSyncedEvent
        """
        if self.status.value != "running":
            return

        # Only process approved skills — all other dispositions are ignored
        if event.disposition != "approved":
            return

        try:
            self._record_processed()

            # Build validation dict for the admin/model-manager APIs
            validation_dict = {
                "skill_id": event.skill_id,
                "result": "APPROVED",
                "architecture_score": event.dimension_scores.get("architecture", 0.0),
                "security_score": event.dimension_scores.get("security", 0.0),
                "quality_score": event.dimension_scores.get("quality", 0.0),
                "composite_score": event.composite_score,
                "violations": list(event.violations),
            }

            # Extract skill_data from the quality_report payload if available
            skill_data = (
                event.quality_report.get("skill_data", {})
                if event.quality_report
                else {}
            )
            # Ensure skill_id is present in skill_data for downstream consumers
            if skill_data:
                skill_data.setdefault("skill_id", event.skill_id)

            # Step 1: Submit through governance protocol for audit trail
            if self._admin:
                self._admin.submit_for_review(skill_data, validation_dict)

            # Step 2: Install via model manager
            installed = False
            if self._model_manager and skill_data:
                installed = self._model_manager.install_skill(
                    skill_data, validation_dict
                )

            # Step 3: Trigger sync distribution
            if installed:
                self._trigger_sync()

            # Step 4: Publish sync event
            targets = ("skills", "cloud")
            self._event_bus.publish(SkillSyncedEvent(
                skill_id=event.skill_id,
                skill_name=event.skill_name,
                targets=targets,
                sync_type="install" if installed else "submitted",
            ))
            self._record_emitted()

            logger.info(
                "Skill '%s' %s (score: %.2f)",
                event.skill_name,
                "installed and synced" if installed else "submitted for review",
                event.composite_score,
            )

        except Exception as exc:
            self._set_error(f"Sync failed: {exc}")
            logger.exception("Sync error for '%s'", event.skill_name)

    # -- Internal helpers --------------------------------------------------

    @staticmethod
    def _trigger_sync() -> None:
        """Invoke Broadcaster.full_sync() for distribution to all targets."""
        try:
            from scripts.broadcaster import full_sync
            full_sync(preview=False)
        except ImportError:
            logger.debug("Broadcaster not available for sync")
        except Exception as sync_exc:
            logger.warning("Sync after install failed: %s", sync_exc)
