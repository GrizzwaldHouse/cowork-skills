# session_bridge.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Async bridge that ties session_discovery and stuck_detector to
#          the existing state_store. On each scan tick it:
#            1. Calls scan_active_sessions() to enumerate live Cowork sessions.
#            2. Translates each DiscoveredSession into an AgentState.
#            3. Reads the current agents.json, merges discovered agents
#               (keyed by discovered_session_id), preserves manually-
#               registered agents (those without discovered_session_id).
#            4. Runs stuck_detector functions and updates is_stuck/is_looping.
#            5. Writes the merged list back via state_store.write_agents.
#            6. Appends a progress log entry on every transition.
#
# The loop runs as an asyncio task started by the FastAPI lifespan
# handler, mirroring the watchdog observer pattern. asyncio.Event is
# used as the stop signal so shutdown is deterministic.

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from AgenticOS.config import (
    AGENTS_JSON,
    LOGGER_NAME,
    LOOP_IDENTICAL_THRESHOLD,
    LOOP_WINDOW_SIZE,
    SESSION_SCAN_INTERVAL_S,
    STUCK_IDLE_THRESHOLD_S,
)
from AgenticOS.models import (
    AgentDomain,
    AgentState,
    AgentStatus,
    DiscoveredSession,
)
from AgenticOS.progress_log import progress_log
from AgenticOS.session_discovery import scan_active_sessions
from AgenticOS.state_store import (
    StateSchemaError,
    read_agents,
    write_agents,
)
from AgenticOS.stuck_detector import (
    detect_silent_failure,
    is_looping,
    is_stuck,
)


# Module logger; child of the project-wide AgenticOS logger so a single
# log filter sees every line we emit.
_logger = logging.getLogger(f"{LOGGER_NAME}.session_bridge")


# Mapping from Cowork-style mission status strings to our AgentStatus
# enum. Anything we do not recognise stays as ACTIVE; the bridge cannot
# guess what a brand-new Cowork status is supposed to mean, so we err
# toward "still doing work" and let the user investigate the card.
_STATUS_TRANSLATIONS: dict[str, AgentStatus] = {
    "in_progress": AgentStatus.ACTIVE,
    "running": AgentStatus.ACTIVE,
    "active": AgentStatus.ACTIVE,
    "working": AgentStatus.ACTIVE,
    "complete": AgentStatus.COMPLETE,
    "completed": AgentStatus.COMPLETE,
    "done": AgentStatus.COMPLETE,
    "error": AgentStatus.ERROR,
    "failed": AgentStatus.ERROR,
    "waiting_approval": AgentStatus.WAITING_APPROVAL,
    "waiting_review": AgentStatus.WAITING_REVIEW,
}


# Default placeholder values used when a discovered session has not
# given us a richer signal. Kept up here so changing the placeholder
# does not require hunting through code.
_DEFAULT_STAGE_LABEL: str = "Discovered Session"
_DEFAULT_TOTAL_STAGES: int = 1
_DEFAULT_DOMAIN: AgentDomain = AgentDomain.GENERAL


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_bridge_loop(
    stop_event: asyncio.Event,
    interval_s: float = SESSION_SCAN_INTERVAL_S,
) -> None:
    """Periodically scan for active Cowork sessions, merge them with the
    existing agents.json contents, and write the merged list back.

    The loop runs until ``stop_event`` is set. The asyncio.wait_for
    around stop_event.wait() is the timer; no busy polling. Every
    iteration is wrapped in a try/except so a transient failure on one
    cycle does not kill the bridge.
    """
    _logger.info(
        "Session bridge starting; scan interval %.1fs", interval_s
    )

    # Track the prior state so we can emit only real transitions to the
    # progress log. Indexed by discovered_session_id (None for legacy
    # manually-registered agents that we should never overwrite).
    last_known: dict[str, AgentState] = {}

    while not stop_event.is_set():
        try:
            await _run_one_cycle(last_known)
        except Exception as exc:  # noqa: BLE001 -- bridge must not die
            # We log the unexpected error and keep going. A single bad
            # scan cannot disable observability for the whole system.
            _logger.exception(
                "Session bridge cycle failed: %s", exc
            )
            try:
                progress_log.append(
                    {
                        "kind": "bridge_error",
                        "error": repr(exc),
                    }
                )
            except Exception:  # noqa: BLE001 -- log + swallow
                # Even the progress log can fail (disk full, locked).
                # Do not let that propagate either.
                _logger.exception("progress_log append also failed")

        # Sleep until either the interval elapses or stop_event is set.
        # asyncio.wait_for with stop_event.wait() lets shutdown
        # interrupt the sleep immediately rather than wait the full tick.
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
        except asyncio.TimeoutError:
            # Normal path: timer expired, run another cycle.
            continue

    _logger.info("Session bridge stopped")


# ---------------------------------------------------------------------------
# Per-cycle body
# ---------------------------------------------------------------------------

async def _run_one_cycle(last_known: dict[str, AgentState]) -> None:
    """One scan -> merge -> write cycle. Pulled out so the loop body is
    short and so tests can call this directly without owning a loop."""
    # Discovery itself is synchronous (psutil + filesystem). Run it on
    # the thread pool so the asyncio loop stays responsive even when
    # the process table scan takes a few hundred milliseconds.
    discovered: list[DiscoveredSession] = await asyncio.to_thread(
        scan_active_sessions
    )

    # Read current agents.json. A schema error means a writer wrote a
    # bad row recently; we log and skip this cycle rather than overwrite
    # otherwise-good rows with our partial view.
    try:
        existing: list[AgentState] = await asyncio.to_thread(
            read_agents, AGENTS_JSON
        )
    except StateSchemaError as exc:
        _logger.warning(
            "Skipping bridge cycle; agents.json invalid: %s", exc
        )
        return

    merged = _merge_agents(existing, discovered)

    # Stuck / loop / silent-failure flags are filled in here so the
    # bridge is the single place those decisions are made. Pure
    # functions => deterministic, testable, no side effects.
    now = datetime.now(timezone.utc)
    for agent in merged:
        _apply_classifications(agent, discovered, now)

    # Detect transitions BEFORE the write so a write failure does not
    # leave the progress log out of sync with itself.
    transitions = _detect_transitions(last_known, merged)

    # Persist. read_agents/write_agents are synchronous so they go on
    # the thread pool too.
    try:
        await asyncio.to_thread(write_agents, merged, AGENTS_JSON)
    except Exception as exc:  # noqa: BLE001 -- log and surface
        _logger.exception("Could not write merged agents.json: %s", exc)
        # Still record the failure so Marcus sees something in the log.
        progress_log.append(
            {"kind": "bridge_error", "error": f"write_failed: {exc!r}"}
        )
        return

    # Emit transitions to the progress log AFTER a successful write.
    for entry in transitions:
        try:
            progress_log.append(entry)
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "Could not append progress event %s: %s",
                entry.get("kind"), exc,
            )

    # Refresh the last-known cache for the next cycle. Replace, never
    # merge: an agent that disappeared from the merged list must also
    # disappear from last_known so a re-add later counts as a new event.
    last_known.clear()
    for agent in merged:
        if agent.discovered_session_id is not None:
            last_known[agent.discovered_session_id] = agent


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

def _session_to_agent_state(
    session: DiscoveredSession,
    previous: Optional[AgentState],
) -> AgentState:
    """Build an AgentState from a DiscoveredSession.

    ``previous`` is the prior state of the same agent (looked up by
    discovered_session_id) and is used to preserve fields that are not
    present in the Cowork mission file -- approval state, error_msg,
    reviewer verdict, last_progress_at -- so the bridge does not erase
    information when it refreshes the row.
    """
    status = _translate_status(session.status)

    # last_progress_at: if this is the first time we see the session,
    # use the discovery's last_active_at. On subsequent visits, only
    # bump it when the timeline actually changed -- otherwise leave
    # the prior timestamp so stuck detection works.
    if previous is None:
        last_progress_at = session.last_active_at
    elif _timeline_changed(previous, session):
        last_progress_at = session.last_active_at
    else:
        last_progress_at = previous.last_progress_at or session.last_active_at

    # Stage info: Cowork does not always expose stages, but we preserve
    # whatever the previous AgentState had so a manually-staged agent
    # is not regressed back to "stage 1 of 1" by every refresh.
    stage = previous.stage if previous else 1
    total_stages = (
        previous.total_stages if previous else _DEFAULT_TOTAL_STAGES
    )
    stage_label = (
        previous.stage_label if previous and previous.stage_label
        else _DEFAULT_STAGE_LABEL
    )
    progress_pct = previous.progress_pct if previous else 0
    context_pct_used = previous.context_pct_used if previous else 0

    return AgentState(
        agent_id=_session_agent_id(session),
        domain=previous.domain if previous else _DEFAULT_DOMAIN,
        task=session.objective,
        stage_label=stage_label,
        stage=stage,
        total_stages=total_stages,
        progress_pct=progress_pct,
        status=status,
        context_pct_used=context_pct_used,
        output_ref=str(session.output_dir) if session.output_dir else None,
        awaiting=previous.awaiting if previous else None,
        error_msg=previous.error_msg if previous else None,
        spawned_by=previous.spawned_by if previous else None,
        reviewer_verdict=previous.reviewer_verdict if previous else None,
        updated_at=session.last_active_at,
        # New phase-2 fields. Stuck/loop are computed later in
        # _apply_classifications; they default to False here.
        is_stuck=False,
        is_looping=False,
        last_progress_at=last_progress_at,
        sub_agent_count=session.sub_agent_count,
        discovered_session_id=session.session_id,
    )


def _session_agent_id(session: DiscoveredSession) -> str:
    """Produce a stable, human-readable agent_id for a discovered session.

    We prefix with the plugin id so two sessions from different plugins
    cannot collide on the session id alone. The agent_id is also used
    as the discovered_session_id link, so it must be deterministic
    across scans.
    """
    return f"{session.plugin_id}/{session.session_id}"


def _translate_status(raw: str) -> AgentStatus:
    """Map a Cowork mission status string to our AgentStatus enum.
    Falls back to ACTIVE for anything unrecognised so the card still
    shows up; the user can investigate from there."""
    return _STATUS_TRANSLATIONS.get(raw.lower(), AgentStatus.ACTIVE)


def _timeline_changed(
    previous: AgentState,
    current: DiscoveredSession,
) -> bool:
    """True iff the most recent timeline entry has changed since the
    previous observation. Compared on the small key (kind, agent) so
    a minor argument tweak still counts as forward progress -- but a
    completely identical entry does not."""
    if not current.timeline_tail:
        return False
    latest = current.timeline_tail[-1]
    last_key = (
        str(latest.get("kind", "")),
        str(latest.get("agent", "")),
    )
    # We do not store the previous tail on AgentState (would bloat the
    # wire shape), so we approximate by checking last_progress_at: if
    # the discovery's last_active_at is newer than the previous
    # last_progress_at, *something* changed on disk.
    if previous.last_progress_at is None:
        return True
    return current.last_active_at > previous.last_progress_at


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

def _merge_agents(
    existing: list[AgentState],
    discovered: list[DiscoveredSession],
) -> list[AgentState]:
    """Combine the existing agents list with the freshly discovered
    sessions. Manually-registered agents (no discovered_session_id) are
    preserved verbatim. Discovered agents are upserted by their
    discovered_session_id."""
    # Index existing by the discovered_session_id for O(1) lookup.
    existing_by_session: dict[str, AgentState] = {}
    manual_agents: list[AgentState] = []
    for agent in existing:
        if agent.discovered_session_id is not None:
            existing_by_session[agent.discovered_session_id] = agent
        else:
            manual_agents.append(agent)

    # Build new rows for every discovered session. We keep stable order
    # by sorting on the agent_id we synthesize so the UI does not
    # reshuffle cards on every scan.
    discovered_rows: list[AgentState] = []
    for session in discovered:
        previous = existing_by_session.get(session.session_id)
        discovered_rows.append(_session_to_agent_state(session, previous))

    discovered_rows.sort(key=lambda a: a.agent_id)
    # Manual agents come first so the user sees their hand-registered
    # rows above the noise of an active scan; sort within group too.
    manual_agents.sort(key=lambda a: a.agent_id)
    return manual_agents + discovered_rows


# ---------------------------------------------------------------------------
# Classification (stuck / loop / silent failure)
# ---------------------------------------------------------------------------

def _apply_classifications(
    agent: AgentState,
    discovered: list[DiscoveredSession],
    now: datetime,
) -> None:
    """Mutate the agent in place to set is_stuck / is_looping / error_msg
    based on the stuck_detector policy. Operates on AgentState directly
    rather than a dict so type errors are caught at edit time.

    Pydantic v2 models are immutable by default in our config (extra =
    'forbid' but no frozen=True), so attribute assignment works. If we
    ever add frozen=True we will need to switch to model_copy here.
    """
    # is_stuck depends only on last_progress_at and now.
    agent.is_stuck = is_stuck(
        agent.last_progress_at, now, threshold_s=STUCK_IDLE_THRESHOLD_S
    )

    # is_looping needs the timeline tail of the matching DiscoveredSession.
    matching_session: Optional[DiscoveredSession] = None
    for session in discovered:
        if session.session_id == agent.discovered_session_id:
            matching_session = session
            break

    if matching_session is not None:
        agent.is_looping = is_looping(
            matching_session.timeline_tail,
            window=LOOP_WINDOW_SIZE,
            threshold=LOOP_IDENTICAL_THRESHOLD,
        )
        # Silent failure: status says "in_progress" but no live process.
        has_process = matching_session.sub_agent_count > 0
        if detect_silent_failure(matching_session.status, has_process):
            # Surface as an error_msg so the existing AgentCard error
            # banner picks it up. We do NOT change status to ERROR
            # automatically -- that would mask the original status and
            # is a Marcus-decides moment per the brainstorm.
            agent.error_msg = (
                "Silent failure: mission status reports work but no "
                "matching claude process is running."
            )


# ---------------------------------------------------------------------------
# Transition detection
# ---------------------------------------------------------------------------

def _detect_transitions(
    last_known: dict[str, AgentState],
    merged: list[AgentState],
) -> list[dict[str, Any]]:
    """Return a list of progress-log records describing what changed
    between ``last_known`` and ``merged``. The events are emitted in a
    stable order so consumers can replay deterministically."""
    events: list[dict[str, Any]] = []
    current_ids: set[str] = set()

    for agent in merged:
        if agent.discovered_session_id is None:
            # Manual agent; bridge does not own its lifecycle and
            # should not emit transitions for it.
            continue
        current_ids.add(agent.discovered_session_id)
        previous = last_known.get(agent.discovered_session_id)

        if previous is None:
            events.append(
                {
                    "kind": "added",
                    "agent_id": agent.agent_id,
                    "session_id": agent.discovered_session_id,
                    "status": agent.status.value,
                }
            )
            continue

        # Status change?
        if previous.status != agent.status:
            events.append(
                {
                    "kind": "status_changed",
                    "agent_id": agent.agent_id,
                    "from": previous.status.value,
                    "to": agent.status.value,
                }
            )

        # is_stuck flipping is a significant transition; only log on
        # the rising edge to avoid log spam every scan.
        if agent.is_stuck and not previous.is_stuck:
            events.append(
                {
                    "kind": "stuck_flagged",
                    "agent_id": agent.agent_id,
                    "threshold_s": STUCK_IDLE_THRESHOLD_S,
                }
            )

        # Same for loop flagging.
        if agent.is_looping and not previous.is_looping:
            events.append(
                {
                    "kind": "loop_flagged",
                    "agent_id": agent.agent_id,
                    "window": LOOP_WINDOW_SIZE,
                    "threshold": LOOP_IDENTICAL_THRESHOLD,
                }
            )

        # Silent failure surfaces via error_msg: log when error_msg
        # transitions from None to set (rising edge only).
        if agent.error_msg and not previous.error_msg:
            events.append(
                {
                    "kind": "silent_failure_flagged",
                    "agent_id": agent.agent_id,
                    "error_msg": agent.error_msg,
                }
            )

    # Detect removals: anything in last_known but missing from current.
    for session_id, prior in last_known.items():
        if session_id not in current_ids:
            events.append(
                {
                    "kind": "removed",
                    "agent_id": prior.agent_id,
                    "session_id": session_id,
                }
            )

    return events
