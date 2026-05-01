# project_registry.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: SQLite-backed registry that tracks every Claude Code project
#          discovered on Marcus's machine. Provides async CRUD for the
#          project_watcher daemon and the /projects REST endpoints.
#          Uses aiosqlite with WAL mode so concurrent reads never block writes.

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from AgenticOS.config import LOGGER_NAME, REGISTRY_DB_PATH

_logger = logging.getLogger(f"{LOGGER_NAME}.project_registry")

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    path            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    tech_stack      TEXT NOT NULL DEFAULT '[]',
    skills          TEXT NOT NULL DEFAULT '[]',
    last_seen       TEXT NOT NULL,
    active_session  TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    phase_hint      TEXT
);
"""


# ---------------------------------------------------------------------------
# Public data class (no Pydantic dependency so project_watcher stays lean)
# ---------------------------------------------------------------------------

class ProjectRecord:
    """One row in the projects table. Constructed from a sqlite3 Row."""

    __slots__ = (
        "id", "path", "name", "tech_stack", "skills",
        "last_seen", "active_session", "is_active", "phase_hint",
    )

    def __init__(
        self,
        id: str,
        path: str,
        name: str,
        tech_stack: list[str],
        skills: list[str],
        last_seen: str,
        active_session: Optional[str],
        is_active: bool,
        phase_hint: Optional[str],
    ) -> None:
        self.id = id
        self.path = path
        self.name = name
        self.tech_stack = tech_stack
        self.skills = skills
        self.last_seen = last_seen
        self.active_session = active_session
        self.is_active = is_active
        self.phase_hint = phase_hint

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "tech_stack": self.tech_stack,
            "skills": self.skills,
            "last_seen": self.last_seen,
            "active_session": self.active_session,
            "is_active": self.is_active,
            "phase_hint": self.phase_hint,
        }

    @staticmethod
    def from_row(row: aiosqlite.Row) -> "ProjectRecord":
        return ProjectRecord(
            id=row["id"],
            path=row["path"],
            name=row["name"],
            tech_stack=json.loads(row["tech_stack"]),
            skills=json.loads(row["skills"]),
            last_seen=row["last_seen"],
            active_session=row["active_session"],
            is_active=bool(row["is_active"]),
            phase_hint=row["phase_hint"],
        )


# ---------------------------------------------------------------------------
# Registry class
# ---------------------------------------------------------------------------

class ProjectRegistry:
    """Async interface to the projects SQLite database.

    Callers must call ``await registry.open()`` before use and
    ``await registry.close()`` on shutdown. The FastAPI lifespan handler
    owns this lifecycle.
    """

    def __init__(self, db_path: Path = REGISTRY_DB_PATH) -> None:
        self._db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def open(self) -> None:
        """Open the database, apply WAL mode, and create tables."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self._db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.executescript(_DDL)
        await self._conn.commit()
        _logger.info("Project registry open at %s", self._db_path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    def _require_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("ProjectRegistry.open() must be called first")
        return self._conn

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------

    async def upsert(
        self,
        *,
        project_id: str,
        path: str,
        name: str,
        tech_stack: list[str],
        skills: list[str],
        phase_hint: Optional[str] = None,
        active_session: Optional[str] = None,
    ) -> ProjectRecord:
        """Insert or update a project row. Returns the saved record."""
        conn = self._require_conn()
        now = datetime.now(timezone.utc).isoformat()
        await conn.execute(
            """
            INSERT INTO projects (id, path, name, tech_stack, skills, last_seen,
                                  active_session, is_active, phase_hint)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(id) DO UPDATE SET
                path           = excluded.path,
                name           = excluded.name,
                tech_stack     = excluded.tech_stack,
                skills         = excluded.skills,
                last_seen      = excluded.last_seen,
                active_session = COALESCE(excluded.active_session, active_session),
                is_active      = 1,
                phase_hint     = COALESCE(excluded.phase_hint, phase_hint)
            """,
            (
                project_id,
                path,
                name,
                json.dumps(tech_stack),
                json.dumps(skills),
                now,
                active_session,
                phase_hint,
            ),
        )
        await conn.commit()
        _logger.info("Upserted project %s at %s", name, path)
        return await self.get(project_id)  # type: ignore[return-value]

    async def get(self, project_id: str) -> Optional[ProjectRecord]:
        conn = self._require_conn()
        async with conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ) as cur:
            row = await cur.fetchone()
        return ProjectRecord.from_row(row) if row else None

    async def get_by_path(self, path: str) -> Optional[ProjectRecord]:
        conn = self._require_conn()
        async with conn.execute(
            "SELECT * FROM projects WHERE path = ?", (path,)
        ) as cur:
            row = await cur.fetchone()
        return ProjectRecord.from_row(row) if row else None

    async def list_all(self) -> list[ProjectRecord]:
        conn = self._require_conn()
        async with conn.execute(
            "SELECT * FROM projects ORDER BY last_seen DESC"
        ) as cur:
            rows = await cur.fetchall()
        return [ProjectRecord.from_row(r) for r in rows]

    async def list_active(self) -> list[ProjectRecord]:
        conn = self._require_conn()
        async with conn.execute(
            "SELECT * FROM projects WHERE is_active = 1 ORDER BY last_seen DESC"
        ) as cur:
            rows = await cur.fetchall()
        return [ProjectRecord.from_row(r) for r in rows]

    async def set_inactive(self, project_id: str) -> None:
        conn = self._require_conn()
        await conn.execute(
            "UPDATE projects SET is_active = 0 WHERE id = ?", (project_id,)
        )
        await conn.commit()

    async def update_phase_hint(self, project_id: str, hint: str) -> None:
        conn = self._require_conn()
        await conn.execute(
            "UPDATE projects SET phase_hint = ? WHERE id = ?", (hint, project_id)
        )
        await conn.commit()

    async def update_session(self, project_id: str, session_id: Optional[str]) -> None:
        conn = self._require_conn()
        await conn.execute(
            "UPDATE projects SET active_session = ? WHERE id = ?",
            (session_id, project_id),
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# CLAUDE.md parser helpers
# ---------------------------------------------------------------------------

def extract_project_metadata(claude_md_path: Path) -> dict[str, Any]:
    """Parse a CLAUDE.md file and extract name, tech_stack, and skill refs.

    Returns a dict with keys: name (str), tech_stack (list[str]),
    skills (list[str]).  Never raises; unknown fields default to empty lists.
    """
    try:
        text = claude_md_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _logger.warning("Could not read %s: %s", claude_md_path, exc)
        return {"name": claude_md_path.parent.name, "tech_stack": [], "skills": []}

    # Project name: first H1 or H2 heading, or fall back to directory name.
    name_match = re.search(r"^#{1,2}\s+(.+)$", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else claude_md_path.parent.name

    # Tech stack: lines mentioning Python, TypeScript, Unreal, React, etc.
    tech_keywords = [
        "Python", "TypeScript", "JavaScript", "Rust", "Go", "C++", "C#",
        "React", "Next.js", "FastAPI", "Unreal", "Unity", "Node",
    ]
    found_tech: list[str] = []
    for kw in tech_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
            found_tech.append(kw)

    # Skill refs: lines like `skills/foo-bar/` or `- foo-bar` inside a
    # Skills section.
    skill_refs: list[str] = []
    skill_pattern = re.compile(r"skills?[/\\]([\w-]+)", re.IGNORECASE)
    for m in skill_pattern.finditer(text):
        slug = m.group(1)
        if slug not in skill_refs:
            skill_refs.append(slug)

    return {"name": name, "tech_stack": found_tech, "skills": skill_refs}


# ---------------------------------------------------------------------------
# Module-level singleton (populated by the FastAPI lifespan handler)
# ---------------------------------------------------------------------------

registry: ProjectRegistry = ProjectRegistry()
