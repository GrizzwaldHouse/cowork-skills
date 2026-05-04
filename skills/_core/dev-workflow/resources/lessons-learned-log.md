# Lessons Learned Log

Running log of significant discoveries. See `problem-tracker-template.md` for the full template.

## LS-001 Security Engine Feedback Loop

**Date:** 2026-02-20
**Category:** Security | File Watcher
**Severity:** High
**Reusable:** Yes

**Symptom:** audit_log.json growing uncontrollably with repeated entries.

**Root Cause:** SecurityEngine.scan_event() wrote to audit_log.json before checking whether the triggering file was transient or internal. The file watcher lacked exclusions for the security/ directory and transient file patterns (.tmp_*, .lock).

**Solution:** Moved transient file and security directory checks before the audit log write. Added matching filters to both watcher modules and the watch config.

**Prevention:** Always place filter/skip checks before any side effects. Test self-referential systems (watchers that write to watched directories) with rapid event simulation.

## LS-002 Subprocess Port Conflict Crash Loop

**Date:** 2026-03-04
**Category:** Infrastructure | Subprocess Management
**Severity:** Critical
**Reusable:** Yes

**Symptom:** Python FastAPI subprocess (model-bridge) crash-looping with 30+ restarts. Port 8001 repeatedly showing `[Errno 10048]` (address already in use). Generation requests returning "Python server is not running (state: starting)".

**Root Cause:** Two interacting bugs:
1. The bridge manager's `_waitForStartup()` polled the health endpoint on a port without verifying the *spawned* process was the one responding. A zombie Python process from a previous run held the port, so health checks passed against the wrong process. The newly spawned process crashed immediately on port bind, but the state machine thought startup succeeded.
2. The `start()` method didn't check if a port was already occupied before spawning a new process on it. Each spawn attempt was doomed to fail.

**Solution:**
- Added `_isPortOccupied(port)` pre-check in `start()` — skips ports with existing healthy servers
- Added process liveness verification in `_waitForStartup()` — aborts immediately if `this.pythonProcess` is null (meaning the spawned process died)
- Added `_initErrorLog()` for stderr file logging to capture Python crash details

**Prevention:**
- Always verify the process you spawned is alive during startup, not just that the port responds
- Check port availability before spawning subprocesses
- Log subprocess stderr to a persistent file for post-mortem debugging
- On Windows, killed processes may hold ports briefly (`TIME_WAIT` state) — allow port scanning fallback

## LS-003 Frontend Script Scope Exposure

**Date:** 2026-03-04
**Category:** Frontend | JavaScript
**Severity:** Medium
**Reusable:** Yes

**Symptom:** ESLint `no-undef` errors for classes loaded via separate `<script>` tags. Classes defined in one script file not visible in another.

**Root Cause:** BrightForge frontend uses plain `<script>` tags (not ES modules). Classes defined in separate files are local to their script scope. ESLint doesn't know about globals defined in other files.

**Solution:**
- Expose classes to `window` scope: `window.SSEClient = SSEClient;`
- Declare globals in consuming files: `/* global SSEClient */`
- Ensure script load order in `index.html`: dependencies before consumers

**Prevention:** For any new frontend class loaded via `<script>` tag (not ES module), always add `window.ClassName = ClassName;` at the end of the file and `/* global ClassName */` in files that use it.

## LS-004 SQL LIMIT Template Literal Injection

**Date:** 2026-03-06
**Category:** Security | Database
**Severity:** Medium
**Reusable:** Yes

**Symptom:** Security review flagged `LIMIT ${options.limit || 50}` as injectable — user-supplied value interpolated directly into SQL.

**Root Cause:** Even though `parseInt()` was applied at the API layer (route handler), the database method itself had no defense-in-depth. If any internal caller passed a raw string or skipped validation, the LIMIT clause could be manipulated.

**Solution:** Sanitize LIMIT inside the database method: `Math.min(Math.max(parseInt(limit, 10) || 50, 1), 500)` and use parameterized `LIMIT ?` instead of template literal interpolation.

**Prevention:** Never interpolate user-facing values into SQL, even for LIMIT/OFFSET. Always use parameterized queries (`?` placeholders) for ALL dynamic values, including pagination parameters. Validate at both API boundary AND data access layer.

## LS-005 HTTP Response Path Leakage

**Date:** 2026-03-06
**Category:** Security | API
**Severity:** Medium
**Reusable:** Yes

**Symptom:** Descriptor endpoint returned raw `file_path` and `assembled_path` fields from database, exposing internal filesystem structure (e.g., `C:\Users\daley\Projects\...`) to HTTP clients.

**Root Cause:** Fallback descriptor builder mapped DB fields directly to response JSON without filtering sensitive fields. The happy path (reading from file) was fine, but the fallback path leaked paths.

**Solution:** Omit `filePath` and `assembledPath` from response. Replace with relative `downloadUrl` pointing to the download endpoint.

**Prevention:** When building HTTP responses from database records, explicitly whitelist fields rather than passing raw DB rows. Any field containing filesystem paths should be transformed to relative URLs or omitted entirely.
