// session-manager.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Manages subagent session records for the Agentic OS dashboard.
//   Persists sessions to data/sessions.json in the app directory.
//   Called by ipc-handlers.js on session:start and session:end events.
//   Provides an in-memory array backed by a JSON flat-file store so sessions
//   survive app restarts and are available for skill-artifact generation.

'use strict';

const fs   = require('node:fs');
const path = require('node:path');

// DATA_DIR — absolute path to the data directory relative to this module.
// Placed one level above src/ so it sits at the app root: <app>/data/
// Using __dirname keeps the path portable regardless of where Node is launched from.
const DATA_DIR = path.join(__dirname, '..', 'data');

// SESSIONS_FILE — absolute path to the sessions JSON flat-file.
// Each entry is a session record object. The file is pretty-printed (2-space
// indent) so it is human-readable during development and debugging.
const SESSIONS_FILE = path.join(DATA_DIR, 'sessions.json');

// _sessions — in-memory array of all session records loaded from or added since
//   the last init() call. Acts as the working cache; _persist() writes it to disk.
// Shape of each record:
//   id             (string)  — unique session identifier (Date.now().toString() at creation)
//   startTime      (string)  — ISO 8601 timestamp when the session started
//   endTime        (string|null) — ISO 8601 timestamp when the session ended, or null if active
//   agentName      (string)  — human-readable name of the agent that ran this session
//   tasksCompleted (number)  — count of tasks completed by the time the session ended
//   tasksPlanned   (number)  — count of tasks planned at session start
//   skillsUsed     (Array<string>) — list of skill identifiers used during the session
//   outcome        (string)  — one of 'in-progress' | 'success' | 'partial' | 'failed'
let _sessions = [];

// init — initialises the session manager at module load time.
// Purpose: Ensures the data directory exists and loads any previously persisted
//   sessions from SESSIONS_FILE into _sessions so the in-memory cache is warm
//   from the start. Safe to call multiple times (mkdirSync recursive is idempotent).
// Params: none
// Returns: void
// Notes: If SESSIONS_FILE does not exist, _sessions starts as an empty array and
//   the file is created lazily on the first _persist() call.
//   JSON parse errors are caught and logged — a corrupted sessions file results in
//   a clean slate rather than crashing the app on startup.
function init() {
  // Create the data directory if it does not already exist.
  // { recursive: true } makes this a no-op when the directory is already present.
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  } catch (mkErr) {
    console.error('[session-manager] Failed to create data directory:', mkErr);
  }

  // Load existing sessions from disk if the file is present.
  if (fs.existsSync(SESSIONS_FILE)) {
    try {
      const raw = fs.readFileSync(SESSIONS_FILE, 'utf8');
      const parsed = JSON.parse(raw);
      // Defensive check: parsed value must be an array; reset to [] if not.
      _sessions = Array.isArray(parsed) ? parsed : [];
      console.log(`[session-manager] Loaded ${_sessions.length} session(s) from ${SESSIONS_FILE}`);
    } catch (readErr) {
      // Corrupted or malformed JSON — start fresh and log the error.
      console.error('[session-manager] Failed to parse sessions file — starting with empty sessions:', readErr);
      _sessions = [];
    }
  } else {
    // File does not yet exist — first run, start with an empty array.
    _sessions = [];
    console.log('[session-manager] No sessions file found — starting with empty session store');
  }
}

// addSession — appends a new session record to the in-memory array and persists.
// Purpose: Called by ipc-handlers.js when a session:start event is received.
//   Keeps the in-memory cache and the on-disk file in sync after every addition.
// Params:
//   record (Object) — fully-formed session record to add. Expected shape:
//     { id, startTime, endTime, agentName, tasksCompleted, tasksPlanned, skillsUsed, outcome }
// Returns: void
// Notes: No duplicate-id check is performed — callers are responsible for unique ids.
//   Calls _persist() synchronously after push so the disk is updated before this
//   function returns (important if the process crashes shortly after).
function addSession(record) {
  _sessions.push(record);
  _persist();
}

// updateSession — finds a session by id and merges a partial update into it.
// Purpose: Called by ipc-handlers.js when a session:end event is received to
//   stamp the endTime, tasksCompleted, and outcome fields on an existing record.
//   Also used for any incremental update during a running session.
// Params:
//   id      (string) — unique session identifier to look up
//   partial (Object) — subset of session record fields to merge (shallow)
// Returns: Object|null — the updated session record, or null if no session with
//   the given id was found. Callers can use null to detect race conditions.
// Notes: Uses Object.assign for a shallow merge so nested arrays (e.g. skillsUsed)
//   are fully replaced rather than deep-merged. Callers must send the complete
//   array if they need to append to a nested collection.
//   Calls _persist() only when a matching session is found (avoids a redundant
//   disk write when the session id is stale or the record was never created).
function updateSession(id, partial) {
  const session = _sessions.find(s => s.id === id);
  if (!session) {
    // Session not found — return null so the caller can log or handle the miss.
    console.warn(`[session-manager] updateSession: no session found with id "${id}"`);
    return null;
  }
  Object.assign(session, partial);
  _persist();
  return session;
}

// getSession — retrieves a single session record by id.
// Purpose: Allows ipc-handlers.js and skill-artifact.js to look up a specific
//   session without iterating the full array.
// Params:
//   id (string) — unique session identifier
// Returns: Object|null — the session record if found, or null if no match exists.
// Notes: Returns the live object from _sessions (not a copy). Callers that need
//   an immutable snapshot should JSON.parse(JSON.stringify(getSession(id))).
function getSession(id) {
  return _sessions.find(s => s.id === id) || null;
}

// getAllSessions — returns a shallow copy of the complete sessions array.
// Purpose: Provides a safe read of all sessions without exposing the internal
//   _sessions reference. A shallow copy means callers cannot push/splice the
//   internal array, though they could mutate individual record objects.
// Params: none
// Returns: Array<Object> — shallow copy of _sessions (may be empty)
// Notes: If a deep copy is needed (e.g. for serialisation), callers should use
//   JSON.parse(JSON.stringify(getAllSessions())).
function getAllSessions() {
  return _sessions.slice();
}

// _persist — writes the current _sessions array to SESSIONS_FILE as pretty JSON.
// Purpose: Called after every mutation (addSession, updateSession) to keep the
//   on-disk file in sync with the in-memory state.
// Params: none
// Returns: void
// Notes: Errors are caught and logged but never thrown. A write failure is a
//   non-fatal degradation — sessions remain in memory for the current process
//   lifetime; the risk is data loss only if the process crashes before a
//   subsequent successful write.
//   writeFileSync is used (not async) because:
//     1. Sessions are written infrequently (once per start/end event).
//     2. Synchronous write ensures the file is flushed before the IPC handler
//        returns, giving the caller a consistent view of disk state.
function _persist() {
  try {
    const json = JSON.stringify(_sessions, null, 2);
    fs.writeFileSync(SESSIONS_FILE, json, 'utf8');
  } catch (writeErr) {
    console.error('[session-manager] Failed to persist sessions to disk:', writeErr);
  }
}

// Call init() at module load time so the session store is ready before any
// IPC handler tries to use it. This is synchronous and fast (~1ms on SSD).
init();

// Export the public API. _persist and _sessions are intentionally not exported —
// all mutations must go through addSession/updateSession to ensure disk sync.
module.exports = {
  addSession,
  updateSession,
  getSession,
  getAllSessions,
};
