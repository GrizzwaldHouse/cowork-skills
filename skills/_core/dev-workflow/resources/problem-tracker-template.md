# Problem Tracker

Use this template to document every significant bug, gotcha, or discovery.

## Template

```
## PT-### [Short Title]

**Date:** YYYY-MM-DD
**Category:** Build System | UI | Networking | Data | Performance | Security | etc.
**Severity:** Critical | High | Medium | Low

**Symptom:**
[What you observed -- error message, wrong behavior, unexpected output]

**Root Cause:**
[Why it happened -- the actual underlying issue]

**Solution:**
[How you fixed it -- specific changes made]

**Prevention:**
[How to avoid this in the future -- process change, automated check, etc.]
```

## Lessons Learned Template

```
## LS-### [Short Title]

**Date:** YYYY-MM-DD
**Category:** Build System | UI | Networking | Data | Performance | etc.
**Severity:** Critical | High | Medium | Low
**Reusable:** Yes | No (Does this apply across projects?)

**Symptom:**
[What you observed]

**Root Cause:**
[Why it happened]

**Solution:**
[How you fixed it]

**Prevention:**
[How to avoid this in the future]
```

## Example Entry

```
## PT-001 Security Engine Feedback Loop

**Date:** 2026-02-20
**Category:** Security | File Watcher
**Severity:** High

**Symptom:**
audit_log.json growing uncontrollably. File watcher detecting its own
security engine writes, creating an infinite loop of events.

**Root Cause:**
SecurityEngine.scan_event() wrote to audit_log.json BEFORE checking
whether the file was a transient/internal file. The watcher also lacked
exclusions for the security/ directory and transient file patterns.

**Solution:**
1. Moved transient file check before audit log write in scan_event()
2. Added security directory self-exclusion in scan_event()
3. Added transient file and security dir filters to both watchers
4. Added security, .tmp_*, *.lock to watch_config ignored_patterns

**Prevention:**
Always place filter/skip checks BEFORE any side effects (writes, logs).
Test with rapid event simulation to verify no feedback loops.
```
