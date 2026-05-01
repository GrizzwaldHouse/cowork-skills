# config.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Central constants for the AgenticOS Command Center state bus.
#          Every port, path, timeout, and template lives here and only here.
#          No other module in AgenticOS may hardcode a value that could
#          conceivably change between environments or releases.

from __future__ import annotations

from pathlib import Path
from typing import Final


# ---------------------------------------------------------------------------
# Base directories
# ---------------------------------------------------------------------------

# Root of the ClaudeSkills installation on Marcus's workstation. Hardcoded
# here intentionally: it is the single anchor point the entire project
# pivots around, and it is documented in the project CLAUDE.md as such.
BASE_DIR: Final[Path] = Path("C:/ClaudeSkills")

# Root of the AgenticOS subsystem inside ClaudeSkills.
AGENTIC_DIR: Final[Path] = BASE_DIR / "AgenticOS"


# ---------------------------------------------------------------------------
# Network endpoints
# ---------------------------------------------------------------------------

# Single port the FastAPI app binds to. The React client builds its
# WebSocket URL (ws://host:WEBSOCKET_PORT/ws) from this value, so changing
# the port here is sufficient: never duplicate it elsewhere.
WEBSOCKET_PORT: Final[int] = 7842

# REST endpoints share the same FastAPI process and therefore the same
# port. Kept as a separate constant so the two concerns can diverge later
# (for example: a reverse proxy that fronts WebSocket on one port and
# REST on another) without touching call sites.
REST_PORT: Final[int] = 7842

# Bind address. 0.0.0.0 exposes the service on all interfaces, which is
# required for Tailscale reachability from iPhone / Claude Desktop MCP.
# Never expose port 8765 to the public internet; restrict via Tailscale ACLs.
SERVER_HOST: Final[str] = "0.0.0.0"

# Tailscale shared-secret used by ws_relay.py to authenticate remote clients.
# Set TAILSCALE_AUTH_TOKEN in .env; never hardcode here.
import os as _os
TAILSCALE_AUTH_TOKEN: Final[str] = _os.environ.get("TAILSCALE_AUTH_TOKEN", "")

# CORS origins permitted by the FastAPI middleware. Includes the Vite dev
# server defaults and the same-host production build so a developer can
# work in either mode without editing this file.
CORS_ORIGINS: Final[list[str]] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    f"http://localhost:{REST_PORT}",
    f"http://127.0.0.1:{REST_PORT}",
]


# ---------------------------------------------------------------------------
# WebSocket tuning
# ---------------------------------------------------------------------------

# Seconds between keep-alive pings to connected WebSocket clients.
WS_PING_INTERVAL_SECONDS: Final[int] = 20

# Seconds a client has to respond to a ping before being considered dead.
WS_PING_TIMEOUT_SECONDS: Final[int] = 10


# ---------------------------------------------------------------------------
# State file paths
# ---------------------------------------------------------------------------

# Directory holding all runtime state JSON files. Created on first run.
STATE_DIR: Final[Path] = AGENTIC_DIR / "state"

# Live agent state. Sub-agents write here at every stage transition; the
# watchdog observer reacts to modifications and triggers a broadcast.
AGENTS_JSON: Final[Path] = STATE_DIR / "agents.json"

# Pending human approval decisions. The FastAPI REST endpoints append
# entries here; waiting agents read and clear their own entries.
APPROVAL_QUEUE_JSON: Final[Path] = STATE_DIR / "approval_queue.json"

# Directory where agent output files and reviewer verdicts are written.
OUTPUTS_DIR: Final[Path] = STATE_DIR / "outputs"


# ---------------------------------------------------------------------------
# Atomic write tuning
# ---------------------------------------------------------------------------

# Suffix used when staging a temp file before rename. Including the PID
# in the suffix at call time prevents collisions when multiple processes
# touch the same target concurrently; this constant is just the prefix.
ATOMIC_WRITE_TEMP_SUFFIX: Final[str] = ".tmp"

# Seconds a writer waits while attempting to acquire the advisory lock
# before giving up. Exists so a stuck writer cannot deadlock callers.
LOCK_ACQUIRE_TIMEOUT_SECONDS: Final[float] = 5.0

# Seconds to sleep between lock acquisition attempts. Kept small so the
# system feels responsive but large enough to avoid spinning the CPU.
LOCK_RETRY_INTERVAL_SECONDS: Final[float] = 0.05


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

# Path to the built React frontend. Served as static files by FastAPI
# only when the directory exists (so server can start before frontend
# is built during early development).
FRONTEND_DIST_DIR: Final[Path] = AGENTIC_DIR / "frontend" / "dist"

# URL prefix under which the built frontend is mounted.
FRONTEND_MOUNT_PATH: Final[str] = "/app"


# ---------------------------------------------------------------------------
# Reviewer subprocess
# ---------------------------------------------------------------------------

# Claude model used for reviewer agents. Haiku is fast, cheap, and a
# different model instance from the orchestrator so review bias is low.
REVIEWER_MODEL: Final[str] = "claude-haiku-4-5-20251001"

# Seconds the reviewer subprocess is given before it is forcibly killed.
REVIEWER_TIMEOUT_SECONDS: Final[int] = 120

# Filename template for reviewer verdict files inside OUTPUTS_DIR.
# Usage: REVIEWER_OUTPUT_TEMPLATE.format(agent_id="AGENT-01")
REVIEWER_OUTPUT_TEMPLATE: Final[str] = "agent-{agent_id}-review.md"

# Reviewer system prompt template. The {content} placeholder is filled
# with the contents of the agent output file at spawn time.
REVIEWER_PROMPT_TEMPLATE: Final[str] = (
    "You are an independent reviewer agent. Review the following work output "
    "for correctness, completeness, and bias. Output a structured verdict: "
    "PASS, REVISE, or REJECT, followed by specific actionable notes.\n\n"
    "Work output:\n{content}"
)

# Executable name used when spawning the reviewer. Kept here so a custom
# wrapper or absolute path can be substituted via configuration.
CLAUDE_CLI_EXECUTABLE: Final[str] = "claude"


# ---------------------------------------------------------------------------
# File watcher
# ---------------------------------------------------------------------------

# Whether the watchdog observer descends into subdirectories. False
# because every file we watch lives directly in STATE_DIR.
WATCHER_RECURSIVE: Final[bool] = False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

# Logger name used by every AgenticOS module. Keeps log filtering simple.
LOGGER_NAME: Final[str] = "agentic_os"


# ---------------------------------------------------------------------------
# Session discovery (Phase 2 expansion -- 2026-04-29)
# ---------------------------------------------------------------------------

# Cowork sessions root on Marcus's machine. Each plugin has its own subdir
# containing per-session state directories with mission-state.json files.
COWORK_SESSIONS_ROOT: Final[Path] = (
    Path.home() / "AppData" / "Roaming" / "Claude" / "local-agent-mode-sessions"
)

# A session counts as "active" when its mission-state.json mtime is within
# this many seconds. Tuned wide enough to cover slow LLM round trips.
SESSION_ACTIVE_THRESHOLD_S: Final[int] = 60

# How often the discovery loop re-scans the sessions root.
SESSION_SCAN_INTERVAL_S: Final[float] = 5.0

# Stuck detection -- no progress for this many seconds flags the agent.
STUCK_IDLE_THRESHOLD_S: Final[int] = 90

# Loop detection -- last N timeline entries identical means the agent is
# stuck in a tight loop.
LOOP_WINDOW_SIZE: Final[int] = 5
LOOP_IDENTICAL_THRESHOLD: Final[int] = 5

# Bound the rendered agent count so the UI cannot DoS itself.
MAX_DISCOVERED_SESSIONS: Final[int] = 32

# Progress log path. Append-only NDJSON; one record per state transition.
PROGRESS_LOG_PATH: Final[Path] = AGENTIC_DIR / "state" / "progress.log"


# ---------------------------------------------------------------------------
# Session discovery (Phase 2 expansion -- 2026-04-29)
# ---------------------------------------------------------------------------

# Cowork sessions root on Marcus's machine. Each plugin has its own subdir
# containing per-session state directories with mission-state.json files.
COWORK_SESSIONS_ROOT: Final[Path] = (
    Path.home() / "AppData" / "Roaming" / "Claude" / "local-agent-mode-sessions"
)

# A session counts as "active" when its mission-state.json mtime is within
# this many seconds. Tuned wide enough to cover slow LLM round trips.
SESSION_ACTIVE_THRESHOLD_S: Final[int] = 60

# How often the discovery loop re-scans the sessions root.
SESSION_SCAN_INTERVAL_S: Final[float] = 5.0

# Stuck detection -- no progress for this many seconds flags the agent.
STUCK_IDLE_THRESHOLD_S: Final[int] = 90

# Loop detection -- last N timeline entries identical means the agent is
# stuck in a tight loop.
LOOP_WINDOW_SIZE: Final[int] = 5
LOOP_IDENTICAL_THRESHOLD: Final[int] = 5

# Bound the rendered agent count so the UI cannot DoS itself.
MAX_DISCOVERED_SESSIONS: Final[int] = 32


# ---------------------------------------------------------------------------
# Project registry (Phase 1 -- Universal Hub)
# ---------------------------------------------------------------------------

# SQLite database file that persists registered projects across restarts.
REGISTRY_DB_PATH: Final[Path] = AGENTIC_DIR / "state" / "projects.db"

# Root paths the project_watcher daemon monitors for new CLAUDE.md files.
# These directories are watched recursively; any new CLAUDE.md triggers
# a project registration event.  Kept here so a single edit covers all
# call sites rather than hunting through watcher code.
PROJECT_WATCH_ROOTS: Final[list[str]] = [
    str(Path.home() / "Projects"),
    str(Path.home() / "UnrealProjects"),
    "C:/ClaudeSkills",
    "D:/",
]

# How often (seconds) the process scanner polls for new claude.exe PIDs
# whose cwd is not yet registered as a project.
PROCESS_SCAN_INTERVAL_S: Final[float] = 10.0

# How long (seconds) a project must be unseen before it is marked inactive.
PROJECT_STALE_THRESHOLD_S: Final[int] = 300


# ---------------------------------------------------------------------------
# MCP server (Phase 3 -- Claude Desktop / iPhone path)
# ---------------------------------------------------------------------------

# Port the MCP SSE server listens on. Keep separate from REST_PORT so both
# can run simultaneously without a proxy.
MCP_PORT: Final[int] = 8766

# Agent-Alexander bridge URL. If Alexander is not running, MCP context
# enrichment is skipped rather than failing the whole tool call.
ALEXANDER_BRIDGE_URL: Final[str] = _os.environ.get(
    "ALEXANDER_BRIDGE_URL", "http://localhost:3001/api/bridge"
)


# ---------------------------------------------------------------------------
# Ollama handoff (Continuous-work feature -- built into AgenticOS)
# ---------------------------------------------------------------------------

# URL of the local Ollama instance used for autonomous handoff work.
OLLAMA_BASE_URL: Final[str] = _os.environ.get(
    "OLLAMA_BASE_URL", "http://localhost:11434"
)

# Model name Ollama uses for handoff continuation tasks. Prefer a capable
# coding model; codellama:13b is a reasonable default.
OLLAMA_HANDOFF_MODEL: Final[str] = _os.environ.get(
    "OLLAMA_HANDOFF_MODEL", "codellama:13b"
)

# Path where the handoff manifest is written when Claude Code nears its
# context limit. Ollama reads this on startup and resumes from it.
HANDOFF_MANIFEST_PATH: Final[Path] = AGENTIC_DIR / "state" / "handoff_manifest.json"
