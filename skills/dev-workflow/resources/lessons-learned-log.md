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
