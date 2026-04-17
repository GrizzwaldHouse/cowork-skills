---
name: mcp-integration-guide
description: "Reference guide for MCP (Model Context Protocol) server integrations. Use when the user asks about setting up MCP servers, configuring Context7, Tavily, Playwright MCP, Firecrawl, Task Master AI, Codebase Memory, or any MCP server integration. Also trigger for 'how to add an MCP server', 'MCP configuration', or troubleshooting MCP connections."
---

# MCP Integration Guide

MCP servers extend Claude Code with specialized capabilities -- real-time docs, web search, browser automation, and persistent memory. Each server runs as a separate process communicating via JSON-RPC over stdio or SSE.

## Configuration

MCP servers are configured in `.claude/settings.json` (project-level) or `~/.claude/settings.json` (global):

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "API_KEY": "your-key-here"
      }
    }
  }
}
```

**Security**: Store API keys in `.env` and reference via environment variables. Never commit keys to source control.

## Context7 - Real-Time Library Documentation

Fetches up-to-date documentation for any library on demand, eliminating hallucinated API calls.

```json
{
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp"]
  }
}
```

**Key Tools:**
- `resolve-library-id` - Find the Context7-compatible ID for a library
- `get-library-docs` - Fetch current documentation for a specific library

**Why it matters:** LLM training data goes stale. Context7 pulls live docs so Claude uses current APIs, not deprecated patterns. Essential for fast-moving libraries (React, Next.js, Tailwind).

**Usage:** Ask Claude to "use Context7 to check the latest Next.js App Router API" before implementing.

## Task Master AI - Project Planning & Dependencies

Structured task management with dependency tracking, priority scoring, and AI-powered task breakdown.

```json
{
  "taskmaster": {
    "command": "npx",
    "args": ["-y", "task-master-ai"],
    "env": {
      "ANTHROPIC_API_KEY": "your-key"
    }
  }
}
```

**Key Tools:**
- `create_task` - Create tasks with descriptions, priorities, dependencies
- `get_tasks` - List all tasks with status and blockers
- `update_task` - Modify task details, mark complete
- `analyze_complexity` - AI-powered complexity scoring
- `expand_task` - Break complex tasks into subtasks

**Why it matters:** Maintains project state across sessions. Dependencies prevent working on blocked tasks. Complexity analysis helps estimate effort accurately.

## Playwright MCP - Browser Automation & Testing

Browser automation for testing web apps, taking screenshots, filling forms, and scraping content.

```json
{
  "playwright": {
    "command": "npx",
    "args": ["-y", "@anthropic/playwright-mcp"]
  }
}
```

**Key Tools:**
- `browser_navigate` - Go to a URL
- `browser_screenshot` - Capture page screenshot
- `browser_click` - Click elements by selector or text
- `browser_fill` - Fill form inputs
- `browser_evaluate` - Run JavaScript in the page context
- `browser_wait` - Wait for elements or conditions

**Why it matters:** Enables visual QA of web applications, form testing, and screenshot-based debugging without leaving Claude Code. Essential for verifying frontend changes actually render correctly.

## Tavily - AI-Optimized Web Search

Search engine designed for AI agents -- returns clean, structured content instead of raw HTML.

```json
{
  "tavily": {
    "command": "npx",
    "args": ["-y", "tavily-mcp"],
    "env": {
      "TAVILY_API_KEY": "your-key"
    }
  }
}
```

**Key Tools:**
- `tavily_search` - Search the web with AI-optimized results
- `tavily_extract` - Extract clean content from specific URLs

**Why it matters:** Standard web search returns noisy HTML. Tavily returns structured, relevant content that fits efficiently in context windows. Better signal-to-noise ratio for research tasks.

## Codebase Memory - Persistent Knowledge Graph

Maintains a knowledge graph of your codebase that persists across sessions -- architecture decisions, patterns, relationships.

```json
{
  "codebase-memory": {
    "command": "npx",
    "args": ["-y", "codebase-memory-mcp"],
    "env": {
      "MEMORY_DIR": "./.codebase-memory"
    }
  }
}
```

**Key Tools:**
- `remember` - Store a fact about the codebase
- `recall` - Retrieve relevant facts for a query
- `forget` - Remove outdated information
- `list_memories` - Browse all stored knowledge

**Why it matters:** Claude starts each session fresh. Codebase Memory provides persistent context about WHY code is structured a certain way, not just WHAT it does. Reduces repeated explanations.

## Firecrawl - Web Scraping & Content Extraction

Crawl websites, extract structured content, and convert pages to clean markdown.

```json
{
  "firecrawl": {
    "command": "npx",
    "args": ["-y", "firecrawl-mcp"],
    "env": {
      "FIRECRAWL_API_KEY": "your-key"
    }
  }
}
```

**Key Tools:**
- `firecrawl_scrape` - Scrape a single page to clean markdown
- `firecrawl_crawl` - Crawl an entire site following links
- `firecrawl_search` - Search and scrape in one step
- `firecrawl_extract` - Extract structured data with a schema

**Why it matters:** JavaScript-rendered pages, SPAs, and dynamic content that standard fetch can't handle. Firecrawl renders pages fully before extraction, handles anti-bot measures, and returns clean markdown ready for context.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Server not found | Package not installed | Run the npx command manually first |
| Connection timeout | Server crashed on startup | Check API keys are set correctly |
| Tools not appearing | Server registered but not connected | Restart Claude Code |
| Permission denied | API key invalid or expired | Verify key in `.env` |
| Slow responses | Server under load | Check rate limits on the service |

## Best Practices

- **Project-level config**: Use `.claude/settings.json` for project-specific servers
- **Global config**: Use `~/.claude/settings.json` for universally useful servers (Context7, Tavily)
- **Minimal servers**: Only enable what you need -- each server consumes resources
- **Key rotation**: Rotate API keys periodically, never commit to git
- **Version pinning**: Use specific versions in args for reproducibility
