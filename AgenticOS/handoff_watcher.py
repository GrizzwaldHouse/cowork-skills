# handoff_watcher.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: Background thread that detects a pending handoff manifest and
#          automatically submits work to Ollama, then updates manifest status.

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from AgenticOS.config import HANDOFF_MANIFEST_PATH, LOGGER_NAME
from AgenticOS.handoff_writer import read_handoff_manifest, update_handoff_status
from AgenticOS.ollama_runner import OllamaError, submit_to_ollama

_logger = logging.getLogger(f"{LOGGER_NAME}.handoff_watcher")

# Seconds between polls of the handoff manifest path.
_POLL_INTERVAL_S: float = 10.0


class HandoffWatcher(threading.Thread):
    """Daemon thread that polls HANDOFF_MANIFEST_PATH every 10 seconds.

    When a manifest with status 'pending_ollama' is detected, it calls
    submit_to_ollama().  On success the manifest transitions to
    'ollama_complete'; on OllamaError it transitions to 'ollama_error'.

    Call stop() to signal the thread to exit gracefully.  The thread is
    a daemon so it will not prevent process exit even if stop() is not called.
    """

    def __init__(self) -> None:
        super().__init__(name="HandoffWatcher", daemon=True)
        # Event set by stop() to break the poll loop.
        self._stop_event: threading.Event = threading.Event()

    def stop(self) -> None:
        """Signal the watcher to exit after the current poll completes."""
        self._stop_event.set()

    def run(self) -> None:
        """Poll loop: check the manifest file every _POLL_INTERVAL_S seconds."""
        _logger.info(
            "HandoffWatcher started; polling %s every %.0fs",
            HANDOFF_MANIFEST_PATH,
            _POLL_INTERVAL_S,
        )
        while not self._stop_event.is_set():
            self._check_and_submit()
            # Wait for the poll interval or until stop() fires.
            self._stop_event.wait(timeout=_POLL_INTERVAL_S)

        _logger.info("HandoffWatcher stopped.")

    def _check_and_submit(self) -> None:
        """Read the manifest; if pending_ollama, submit and update status."""
        manifest: Optional[dict] = read_handoff_manifest()
        if manifest is None:
            return

        if manifest.get("status") != "pending_ollama":
            # Not our turn — manifest may already be in progress or done.
            return

        agent_id: str = manifest.get("agent_id", "unknown")
        _logger.info(
            "Detected pending handoff for agent '%s'; submitting to Ollama.", agent_id
        )

        try:
            submit_to_ollama(manifest)
            # update_handoff_status is called inside submit_to_ollama on success.
            _logger.info("Ollama submission succeeded for agent '%s'.", agent_id)
        except OllamaError as exc:
            _logger.error(
                "Ollama submission failed for agent '%s': %s", agent_id, exc
            )
            try:
                update_handoff_status("ollama_error")
            except Exception as update_exc:  # noqa: BLE001
                _logger.warning(
                    "Could not update manifest to ollama_error: %s", update_exc
                )
