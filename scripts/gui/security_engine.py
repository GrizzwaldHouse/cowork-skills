# security_engine.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Detect suspicious file activity and maintain integrity baselines to protect monitored directories

"""
Security audit engine for the Claude Skills system.

Monitors file changes for suspicious activity, maintains SHA-256 integrity
baselines, logs all file events to an audit trail, and detects permission
or attribute changes on Windows. Generates Markdown audit reports on demand.
"""

from __future__ import annotations

import hashlib
import json
import logging
import stat
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from gui.constants import (
    BURST_THRESHOLD,
    BURST_WINDOW_SECONDS,
    DEFAULT_LARGE_FILE_BYTES,
    MAX_AUDIT_ENTRIES,
    SUSPICIOUS_EXTENSIONS,
)
from watcher_core import SECURITY_DIR, is_security_dir, is_transient

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path("C:/ClaudeSkills")
INTEGRITY_DB_PATH = SECURITY_DIR / "integrity_db.json"
AUDIT_LOG_PATH = SECURITY_DIR / "audit_log.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("security_engine")


# ---------------------------------------------------------------------------
# Alert levels and data
# ---------------------------------------------------------------------------

class AlertLevel(str, Enum):
    """Severity levels for security alerts."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class SecurityAlert:
    """A single security alert produced by the audit engine."""

    level: AlertLevel
    message: str
    file_path: str
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the alert to a JSON-safe dictionary."""
        data = asdict(self)
        data["level"] = self.level.value
        return data


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    """Read and parse a JSON file.  Returns None on any error."""
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return None


def _write_json(path: Path, data: Any) -> None:
    """Write JSON data to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _file_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# File attribute snapshot (Windows-aware)
# ---------------------------------------------------------------------------

def _stat_snapshot(path: Path) -> dict[str, Any]:
    """Capture file stat information relevant to security auditing."""
    try:
        st = path.stat()
    except OSError:
        return {}
    return {
        "size": st.st_size,
        "mode": st.st_mode,
        "readonly": not (st.st_mode & stat.S_IWRITE),
        "hidden": path.name.startswith("."),
        "mtime": st.st_mtime,
    }


def _detect_attribute_changes(
    old_attrs: dict[str, Any],
    new_attrs: dict[str, Any],
) -> list[str]:
    """Compare two stat snapshots and return a list of change descriptions."""
    changes: list[str] = []
    if not old_attrs or not new_attrs:
        return changes

    if old_attrs.get("readonly") != new_attrs.get("readonly"):
        old_val = old_attrs.get("readonly")
        new_val = new_attrs.get("readonly")
        changes.append(f"read-only changed from {old_val} to {new_val}")

    if old_attrs.get("mode") != new_attrs.get("mode"):
        old_mode = oct(old_attrs.get("mode", 0))
        new_mode = oct(new_attrs.get("mode", 0))
        changes.append(f"mode changed from {old_mode} to {new_mode}")

    if old_attrs.get("hidden") != new_attrs.get("hidden"):
        old_val = old_attrs.get("hidden")
        new_val = new_attrs.get("hidden")
        changes.append(f"hidden changed from {old_val} to {new_val}")

    return changes


# ---------------------------------------------------------------------------
# Security engine
# ---------------------------------------------------------------------------

class SecurityEngine:
    """Central security audit engine.

    Tracks file integrity via SHA-256 baselines, detects suspicious
    activity patterns, logs all events to an audit trail, and exports
    Markdown audit reports.

    Parameters
    ----------
    large_file_threshold:
        File size in bytes above which a WARNING alert is raised.
    """

    def __init__(
        self,
        large_file_threshold: int = DEFAULT_LARGE_FILE_BYTES,
    ) -> None:
        self.large_file_threshold = large_file_threshold

        # Burst detection state: directory -> list of monotonic timestamps
        self._burst_tracker: dict[str, list[float]] = defaultdict(list)

        # In-memory caches (loaded lazily from disk)
        self._integrity_db: dict[str, Any] | None = None
        self._audit_log: list[dict[str, Any]] | None = None

    # -- integrity database -------------------------------------------------

    def _load_integrity_db(self) -> dict[str, Any]:
        """Load the integrity database from disk, or create an empty one."""
        if self._integrity_db is None:
            data = _read_json(INTEGRITY_DB_PATH)
            if isinstance(data, dict):
                self._integrity_db = data
            else:
                self._integrity_db = {"files": {}, "created": _now_iso()}
        return self._integrity_db

    def _save_integrity_db(self) -> None:
        """Persist the in-memory integrity database to disk."""
        db = self._load_integrity_db()
        db["last_updated"] = _now_iso()
        _write_json(INTEGRITY_DB_PATH, db)

    # -- audit log ----------------------------------------------------------

    def _load_audit_log(self) -> list[dict[str, Any]]:
        """Load the audit log from disk, or create an empty list."""
        if self._audit_log is None:
            data = _read_json(AUDIT_LOG_PATH)
            if isinstance(data, list):
                self._audit_log = data
            else:
                self._audit_log = []
        return self._audit_log

    def _append_audit_entry(self, entry: dict[str, Any]) -> None:
        """Append an entry to the audit log, rotating if needed."""
        log = self._load_audit_log()
        log.append(entry)

        if len(log) > MAX_AUDIT_ENTRIES:
            self._rotate_audit_log(log)

        _write_json(AUDIT_LOG_PATH, self._audit_log)

    def _rotate_audit_log(self, log: list[dict[str, Any]]) -> None:
        """Rotate the oldest half of entries to a timestamped archive file."""
        split_point = len(log) // 2
        archived = log[:split_point]
        remaining = log[split_point:]

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive_path = SECURITY_DIR / f"audit_log.{ts}.json"
        _write_json(archive_path, archived)
        logger.info(
            "Rotated %d audit entries to %s", len(archived), archive_path,
        )

        self._audit_log = remaining

    # -- burst detection ----------------------------------------------------

    def _check_burst(self, directory: str) -> bool:
        """Return True if there is a burst of events in *directory*."""
        now = time.monotonic()
        timestamps = self._burst_tracker[directory]
        # Prune events outside the window.
        cutoff = now - BURST_WINDOW_SECONDS
        timestamps[:] = [t for t in timestamps if t >= cutoff]
        timestamps.append(now)
        return len(timestamps) > BURST_THRESHOLD

    # -- public API ---------------------------------------------------------

    def scan_event(
        self,
        event_type: str,
        file_path: str | Path,
    ) -> SecurityAlert | None:
        """Analyse a single file-system event and return an alert if warranted.

        Parameters
        ----------
        event_type:
            One of ``"created"``, ``"modified"``, ``"deleted"``, ``"moved"``.
        file_path:
            Absolute path to the affected file.

        Returns
        -------
        A :class:`SecurityAlert` if the event is suspicious, otherwise *None*.
        """
        path = Path(file_path)
        now_iso = _now_iso()
        alert: SecurityAlert | None = None

        # 0. Skip transient files (atomic writes, locks, tooling artifacts).
        if is_transient(path):
            return None

        # 0b. Skip files inside the security directory (our own audit logs)
        # to prevent a write->detect->write feedback loop.
        if is_security_dir(path):
            return None

        # Always log the event to the audit trail.
        size: int | None = None
        file_hash: str | None = None
        if path.exists() and path.is_file():
            try:
                size = path.stat().st_size
            except OSError:
                pass
            try:
                file_hash = _file_sha256(path)
            except OSError:
                pass

        audit_entry: dict[str, Any] = {
            "timestamp": now_iso,
            "event_type": event_type,
            "path": str(path),
            "file_size": size,
            "file_hash": file_hash,
        }
        self._append_audit_entry(audit_entry)

        # 1. Suspicious extension check
        suffix = path.suffix.lower()
        if suffix in SUSPICIOUS_EXTENSIONS:
            level = AlertLevel.CRITICAL if event_type == "created" else AlertLevel.WARNING
            alert = SecurityAlert(
                level=level,
                message=f"Suspicious file type detected: {suffix}",
                file_path=str(path),
                timestamp=now_iso,
                details={
                    "extension": suffix,
                    "event_type": event_type,
                    "file_size": size,
                },
            )
            logger.warning("Suspicious file: %s (%s)", path, suffix)
            return alert

        # 2. Hidden file check
        if path.name.startswith(".") and event_type == "created":
            alert = SecurityAlert(
                level=AlertLevel.WARNING,
                message=f"Hidden file created: {path.name}",
                file_path=str(path),
                timestamp=now_iso,
                details={"event_type": event_type},
            )
            logger.warning("Hidden file created: %s", path)
            return alert

        # 3. Burst detection
        parent_dir = str(path.parent)
        if self._check_burst(parent_dir):
            alert = SecurityAlert(
                level=AlertLevel.WARNING,
                message=f"Rapid burst of changes in {parent_dir}",
                file_path=str(path),
                timestamp=now_iso,
                details={
                    "directory": parent_dir,
                    "event_type": event_type,
                    "burst_threshold": BURST_THRESHOLD,
                    "burst_window_seconds": BURST_WINDOW_SECONDS,
                },
            )
            logger.warning("Burst detected in %s", parent_dir)
            return alert

        # 4. Large file check
        if size is not None and size > self.large_file_threshold:
            alert = SecurityAlert(
                level=AlertLevel.WARNING,
                message=f"Large file detected ({size / (1024 * 1024):.1f} MB)",
                file_path=str(path),
                timestamp=now_iso,
                details={
                    "file_size": size,
                    "threshold": self.large_file_threshold,
                    "event_type": event_type,
                },
            )
            logger.warning("Large file: %s (%d bytes)", path, size)
            return alert

        # 5. Integrity check on modification
        if event_type == "modified" and file_hash is not None:
            db = self._load_integrity_db()
            key = str(path)
            baseline = db.get("files", {}).get(key)
            if baseline is not None:
                old_hash = baseline.get("sha256")
                if old_hash and old_hash != file_hash:
                    # Check attribute changes too
                    new_attrs = _stat_snapshot(path)
                    old_attrs = baseline.get("attributes", {})
                    attr_changes = _detect_attribute_changes(old_attrs, new_attrs)

                    if attr_changes:
                        alert = SecurityAlert(
                            level=AlertLevel.CRITICAL,
                            message="File modified with attribute changes",
                            file_path=str(path),
                            timestamp=now_iso,
                            details={
                                "old_hash": old_hash,
                                "new_hash": file_hash,
                                "attribute_changes": attr_changes,
                                "event_type": event_type,
                            },
                        )
                        logger.critical(
                            "Integrity + attribute change: %s", path,
                        )
                        return alert

                    alert = SecurityAlert(
                        level=AlertLevel.CRITICAL,
                        message="File integrity violation (hash mismatch)",
                        file_path=str(path),
                        timestamp=now_iso,
                        details={
                            "old_hash": old_hash,
                            "new_hash": file_hash,
                            "event_type": event_type,
                        },
                    )
                    logger.critical("Integrity violation: %s", path)
                    return alert

        # No alert needed.
        return None

    def verify_integrity(self) -> list[SecurityAlert]:
        """Verify all baselined files against their stored SHA-256 hashes.

        Returns a list of :class:`SecurityAlert` instances for every file
        whose current hash does not match the baseline, or that is missing.
        """
        db = self._load_integrity_db()
        files: dict[str, Any] = db.get("files", {})
        alerts: list[SecurityAlert] = []
        now_iso = _now_iso()

        for file_key, baseline in files.items():
            path = Path(file_key)

            if not path.exists():
                alerts.append(SecurityAlert(
                    level=AlertLevel.CRITICAL,
                    message="Baselined file is missing",
                    file_path=file_key,
                    timestamp=now_iso,
                    details={
                        "expected_hash": baseline.get("sha256", ""),
                        "baseline_date": baseline.get("baselined_at", ""),
                    },
                ))
                continue

            if not path.is_file():
                continue

            try:
                current_hash = _file_sha256(path)
            except OSError as exc:
                alerts.append(SecurityAlert(
                    level=AlertLevel.WARNING,
                    message=f"Cannot read file for integrity check: {exc}",
                    file_path=file_key,
                    timestamp=now_iso,
                    details={"error": str(exc)},
                ))
                continue

            expected_hash = baseline.get("sha256", "")
            if current_hash != expected_hash:
                alerts.append(SecurityAlert(
                    level=AlertLevel.CRITICAL,
                    message="File integrity violation (hash mismatch)",
                    file_path=file_key,
                    timestamp=now_iso,
                    details={
                        "expected_hash": expected_hash,
                        "current_hash": current_hash,
                    },
                ))

            # Check attribute drift
            old_attrs = baseline.get("attributes", {})
            new_attrs = _stat_snapshot(path)
            attr_changes = _detect_attribute_changes(old_attrs, new_attrs)
            if attr_changes:
                alerts.append(SecurityAlert(
                    level=AlertLevel.CRITICAL,
                    message="File attribute change detected",
                    file_path=file_key,
                    timestamp=now_iso,
                    details={"attribute_changes": attr_changes},
                ))

        logger.info(
            "Integrity verification complete: %d file(s) checked, %d alert(s)",
            len(files), len(alerts),
        )
        return alerts

    def baseline_directory(self, directory: str | Path) -> int:
        """Baseline all files under *directory* with SHA-256 hashes.

        Recursively walks *directory*, computes a SHA-256 hash and captures
        stat attributes for every file, then stores them in the integrity
        database.

        Parameters
        ----------
        directory:
            Path to the directory to baseline.

        Returns
        -------
        The number of files baselined.
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            logger.error("Cannot baseline: %s is not a directory", dir_path)
            return 0

        db = self._load_integrity_db()
        files_db: dict[str, Any] = db.setdefault("files", {})
        count = 0
        now_iso = _now_iso()

        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            # Skip the security directory itself to avoid circular tracking.
            if is_security_dir(file_path):
                continue

            try:
                file_hash = _file_sha256(file_path)
                attrs = _stat_snapshot(file_path)
            except OSError as exc:
                logger.warning("Skipping %s: %s", file_path, exc)
                continue

            key = str(file_path)
            files_db[key] = {
                "sha256": file_hash,
                "attributes": attrs,
                "baselined_at": now_iso,
            }
            count += 1

        self._save_integrity_db()
        logger.info("Baselined %d file(s) under %s", count, dir_path)
        return count

    def export_report(
        self,
        output_path: str | Path,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Path:
        """Export a Markdown audit report for the given date range.

        Parameters
        ----------
        output_path:
            Where to write the ``.md`` file.
        start_date:
            Include events on or after this datetime (UTC).  Defaults to
            the beginning of the audit log.
        end_date:
            Include events on or before this datetime (UTC).  Defaults to
            now.

        Returns
        -------
        The resolved :class:`~pathlib.Path` to the written report.
        """
        out = Path(output_path)
        log = self._load_audit_log()

        if end_date is None:
            end_date = datetime.now(timezone.utc)

        # Filter entries by date range.
        filtered: list[dict[str, Any]] = []
        for entry in log:
            ts_str = entry.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                continue
            if start_date is not None and ts < start_date:
                continue
            if ts > end_date:
                continue
            filtered.append(entry)

        # Run integrity verification for the report.
        integrity_alerts = self.verify_integrity()

        # Build report.
        lines: list[str] = []
        lines.append("# Security Audit Report")
        lines.append("")
        range_start = start_date.isoformat() if start_date else "(all time)"
        range_end = end_date.isoformat()
        lines.append(f"**Period:** {range_start} to {range_end}")
        lines.append(f"**Generated:** {_now_iso()}")
        lines.append("")

        # Summary statistics
        lines.append("## Summary")
        lines.append("")
        event_counts: dict[str, int] = defaultdict(int)
        for entry in filtered:
            event_counts[entry.get("event_type", "unknown")] += 1
        lines.append(f"- **Total events:** {len(filtered)}")
        for evt_type, count in sorted(event_counts.items()):
            lines.append(f"  - {evt_type}: {count}")
        lines.append(f"- **Integrity alerts:** {len(integrity_alerts)}")
        lines.append("")

        # Suspicious events
        suspicious = [
            e for e in filtered
            if _is_suspicious_path(e.get("path", ""))
        ]
        lines.append("## Suspicious Events")
        lines.append("")
        if suspicious:
            lines.append("| Timestamp | Event | Path | Size |")
            lines.append("|-----------|-------|------|------|")
            for entry in suspicious:
                ts = entry.get("timestamp", "")
                evt = entry.get("event_type", "")
                p = entry.get("path", "")
                sz = entry.get("file_size")
                sz_str = _format_size(sz) if sz is not None else "N/A"
                lines.append(f"| {ts} | {evt} | `{p}` | {sz_str} |")
        else:
            lines.append("No suspicious events detected.")
        lines.append("")

        # Integrity violations
        lines.append("## Integrity Violations")
        lines.append("")
        if integrity_alerts:
            lines.append("| Level | File | Message | Details |")
            lines.append("|-------|------|---------|---------|")
            for alert in integrity_alerts:
                details_str = "; ".join(
                    f"{k}={v}" for k, v in alert.details.items()
                )
                lines.append(
                    f"| {alert.level.value} | `{alert.file_path}` "
                    f"| {alert.message} | {details_str} |"
                )
        else:
            lines.append("No integrity violations detected.")
        lines.append("")

        # Event timeline
        lines.append("## Event Timeline (last 100)")
        lines.append("")
        recent = filtered[-100:]
        if recent:
            lines.append("| Timestamp | Event | Path | Hash |")
            lines.append("|-----------|-------|------|------|")
            for entry in recent:
                ts = entry.get("timestamp", "")
                evt = entry.get("event_type", "")
                p = entry.get("path", "")
                h = entry.get("file_hash", "")
                h_short = h[:12] + "..." if h else "N/A"
                lines.append(f"| {ts} | {evt} | `{p}` | {h_short} |")
        else:
            lines.append("No events in the selected period.")
        lines.append("")

        report_text = "\n".join(lines)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report_text, encoding="utf-8")
        logger.info("Audit report exported to %s", out)
        return out


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _is_suspicious_path(path_str: str) -> bool:
    """Return True if the file path has a suspicious extension or is hidden.

    Transient files from atomic writes, locks, and tooling are excluded.
    """
    path = Path(path_str)
    if is_transient(path):
        return False
    if path.suffix.lower() in SUSPICIOUS_EXTENSIONS:
        return True
    if path.name.startswith("."):
        return True
    return False


def _format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
