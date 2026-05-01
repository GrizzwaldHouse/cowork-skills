# mcp_server.py
# Developer: Marcus Daley
# Date: 2026-04-30
# Purpose: MCP (Model Context Protocol) server that exposes AgenticOS
#          project status and approval controls as Claude Desktop tools.
#          This is the fastest path to iPhone access: Claude Desktop on
#          phone/desktop connects here via MCP and gets live project state
#          and one-tap approval buttons — no browser or separate app needed.
#
#          Transport: stdio (Claude Desktop spawns this as a subprocess).
#          Setup: copy mcp_config.json to ~/.claude/claude_desktop_config.json
#                 or merge the "mcpServers" block into an existing config.

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# MCP SDK import guard
# ---------------------------------------------------------------------------
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        ListToolsResult,
        TextContent,
        Tool,
    )
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False

import httpx

from AgenticOS.config import (
    ALEXANDER_BRIDGE_URL,
    LOGGER_NAME,
    REST_PORT,
    SERVER_HOST,
)

_logger = logging.getLogger(f"{LOGGER_NAME}.mcp_server")

# Base URL for the AgenticOS REST API (same process, loopback).
_API_BASE = f"http://{SERVER_HOST}:{REST_PORT}"


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

async def _api_get(path: str) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{_API_BASE}{path}")
        resp.raise_for_status()
        return resp.json()


async def _api_post(path: str, body: dict) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{_API_BASE}{path}", json=body)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

_TOOLS: list[dict] = [
    {
        "name": "list_projects",
        "description": (
            "List all Claude Code projects registered with AgenticOS. "
            "Returns project name, path, active status, and current phase hint."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "active_only": {
                    "type": "boolean",
                    "description": "When true, return only projects seen recently.",
                    "default": True,
                }
            },
        },
    },
    {
        "name": "get_phase",
        "description": (
            "Get the current action Marcus needs to take for a specific project. "
            "Returns a plain-English 'what to do now' answer."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID from list_projects.",
                }
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "list_agents",
        "description": "Return all currently running agents and their status.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "approve_agent",
        "description": (
            "Approve, request more research, or trigger a review for an agent "
            "that is waiting at a gate."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "The agent_id from list_agents.",
                },
                "decision": {
                    "type": "string",
                    "enum": ["proceed", "research", "review"],
                    "description": "The approval decision to record.",
                },
            },
            "required": ["agent_id", "decision"],
        },
    },
    {
        "name": "get_skills",
        "description": "List which skill packages are active for a given project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID from list_projects.",
                }
            },
            "required": ["project_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

async def _handle_list_projects(args: dict) -> str:
    active_only = args.get("active_only", True)
    endpoint = "/projects/active" if active_only else "/projects"
    try:
        projects = await _api_get(endpoint)
    except httpx.HTTPError as exc:
        return f"Error fetching projects: {exc}"
    if not projects:
        return "No projects registered. Create a CLAUDE.md in any project directory."
    lines = []
    for p in projects:
        status = "ACTIVE" if p.get("is_active") else "inactive"
        lines.append(
            f"• [{p['name']}] id={p['id']} | {status} | {p['path']}"
        )
        if p.get("phase_hint"):
            lines.append(f"  → {p['phase_hint']}")
    return "\n".join(lines)


async def _handle_get_phase(args: dict) -> str:
    project_id = args["project_id"]
    try:
        data = await _api_get(f"/projects/{project_id}/phase")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Project {project_id} not found. Run list_projects to see valid IDs."
        return f"Error: {exc}"
    except httpx.HTTPError as exc:
        return f"Error fetching phase: {exc}"

    # Also try to enrich with Alexander context if available.
    context_lines = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                ALEXANDER_BRIDGE_URL,
                params={"project": data.get("name", project_id)},
            )
            if resp.status_code == 200:
                ctx = resp.json()
                for doc in ctx.get("docs", [])[:2]:
                    context_lines.append(f"  Knowledge: {doc.get('summary', '')}")
    except Exception:  # noqa: BLE001
        pass  # Alexander not running; degrade gracefully.

    out = [
        f"PROJECT: {data.get('name', project_id)}",
        f"WHAT TO DO NOW: {data.get('phase_hint') or 'No specific task recorded — check recent agent output.'}",
        f"Active agents: {data.get('agent_count', 0)}",
    ]
    if data.get("skills"):
        out.append(f"Active skills: {', '.join(data['skills'])}")
    out.extend(context_lines)
    return "\n".join(out)


async def _handle_list_agents(args: dict) -> str:
    try:
        agents = await _api_get("/agents")
    except httpx.HTTPError as exc:
        return f"Error fetching agents: {exc}"
    if not agents:
        return "No agents currently running."
    lines = []
    for a in agents:
        stuck = " ⚠STUCK" if a.get("is_stuck") else ""
        loop = " 🔁LOOP" if a.get("is_looping") else ""
        lines.append(
            f"• {a['agent_id']} | {a['status']}{stuck}{loop} | "
            f"stage {a['stage']}/{a['total_stages']} | {a['task'][:60]}"
        )
    return "\n".join(lines)


async def _handle_approve_agent(args: dict) -> str:
    agent_id = args["agent_id"]
    decision = args["decision"]
    endpoint_map = {
        "proceed": f"/approve/{agent_id}",
        "research": f"/research/{agent_id}",
        "review": f"/review/{agent_id}",
    }
    endpoint = endpoint_map.get(decision)
    if endpoint is None:
        return f"Unknown decision '{decision}'. Use: proceed, research, review."
    try:
        result = await _api_post(endpoint, {"decision": decision})
        return (
            f"Decision '{decision}' recorded for agent {agent_id} "
            f"at {result.get('decided_at', 'unknown time')}."
        )
    except httpx.HTTPError as exc:
        return f"Error recording decision: {exc}"


async def _handle_get_skills(args: dict) -> str:
    project_id = args["project_id"]
    try:
        data = await _api_get(f"/projects/{project_id}")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Project {project_id} not found."
        return f"Error: {exc}"
    except httpx.HTTPError as exc:
        return f"Error: {exc}"
    skills = data.get("skills", [])
    if not skills:
        return f"No skills registered for project {data.get('name', project_id)}."
    return f"Skills for {data.get('name', project_id)}:\n" + "\n".join(f"• {s}" for s in skills)


_HANDLER_MAP = {
    "list_projects": _handle_list_projects,
    "get_phase": _handle_get_phase,
    "list_agents": _handle_list_agents,
    "approve_agent": _handle_approve_agent,
    "get_skills": _handle_get_skills,
}


# ---------------------------------------------------------------------------
# MCP server entry point
# ---------------------------------------------------------------------------

async def _run_mcp_server() -> None:
    """Run the MCP stdio server. Called by main()."""
    server = Server("agentic-os")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in _TOOLS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = _HANDLER_MAP.get(name)
        if handler is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        try:
            result = await handler(arguments)
        except Exception as exc:  # noqa: BLE001
            result = f"Tool error: {exc!r}"
        return [TextContent(type="text", text=result)]

    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1],
            server.create_initialization_options(),
        )


def main() -> None:
    """Entry point: ``python -m AgenticOS.mcp_server``."""
    if not _MCP_AVAILABLE:
        print(
            "ERROR: 'mcp' package not installed. Run: pip install mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    logging.basicConfig(
        level=logging.WARNING,  # Keep stdio clean for MCP protocol frames.
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        stream=sys.stderr,
    )
    import asyncio
    asyncio.run(_run_mcp_server())


if __name__ == "__main__":
    main()
