---
name: automation-orchestration
description: "Workflow automation and multi-agent orchestration tools. Use when the user mentions n8n, Langflow, claude-squad, container-use, Dagger, workflow automation, pipeline orchestration, multi-agent coordination, or wants to set up automated workflows. Also trigger for 'automate this process', 'create a workflow', 'run agents in parallel', or integration of multiple tools into a pipeline."
---

# Automation & Orchestration

Tools and patterns for workflow automation, LLM pipelines, and multi-agent coordination.

## n8n - Visual Workflow Automation

Self-hosted workflow automation with 400+ integrations. Connects APIs, databases, and services with a visual editor.

### Setup
```bash
npx n8n                              # Quick start
# Or with Docker (production)
docker run -it --rm -p 5678:5678 n8nio/n8n
```

### Core Concepts
- **Nodes**: Individual operations (HTTP request, transform, filter)
- **Triggers**: Start workflows (webhook, cron, file change, email)
- **Connections**: Data flow between nodes
- **Credentials**: Stored authentication for services
- **Code Nodes**: Custom JavaScript or Python for complex logic

### Common Patterns
```
Webhook Trigger → Validate Input → Process Data → Send Result
Cron Schedule → Fetch Data → Transform → Store in DB → Notify
File Upload → Extract Text → AI Analysis → Email Report
GitHub PR → Run Tests → Post Results → Update Status
```

### When to Use
- Connecting multiple SaaS services (Slack, GitHub, Gmail, Notion)
- Scheduled data processing and reporting
- Event-driven automation (webhook triggers)
- Non-developer-friendly workflow creation

## Langflow - Visual LLM Pipeline Builder

Drag-and-drop builder for RAG pipelines, agent chains, and LLM applications.

### Setup
```bash
pip install langflow
langflow run                          # Opens at localhost:7860
```

### Core Concepts
- **Components**: Modular building blocks (LLMs, embeddings, vector stores, tools)
- **Flows**: Connected component graphs forming a pipeline
- **Custom Components**: Python classes extending base components
- **API Export**: Deploy flows as REST APIs

### Common Patterns
```
Document Loader → Text Splitter → Embeddings → Vector Store → RAG Chain
User Input → Prompt Template → LLM → Output Parser → Structured Response
Agent → Tool Selection → Execution → Memory → Response
```

### When to Use
- Building RAG applications visually
- Prototyping LLM chains before coding them
- Non-code-first LLM pipeline development
- Quick comparison of different LLM configurations

## claude-squad - Multi-Agent Terminal Orchestration

Run multiple Claude Code instances in parallel, each with its own git worktree.

### Setup
```bash
# Install (requires Go)
go install github.com/smtg-ai/claude-squad@latest

# Or download binary from GitHub releases
```

### Core Concepts
- **Sessions**: Independent Claude Code instances
- **Worktrees**: Each agent gets its own git worktree (isolated branches)
- **TUI Dashboard**: Monitor all agents from a single terminal
- **Auto-merge**: Combine agent outputs back to main branch

### Usage
```bash
claude-squad                          # Launch TUI dashboard
# Create new session: press 'n'
# View session: press 'Enter'
# Toggle diff: press 'd'
```

### When to Use
- Large refactoring tasks that touch many independent files
- Parallel feature development across modules
- Research tasks where multiple agents investigate different angles
- Any task that decomposes into independent, parallelizable subtasks

## container-use - Containerized Agent Execution (Dagger)

Run AI agents in isolated Docker containers for safe code execution.

### Setup
```json
// MCP configuration
{
  "container-use": {
    "command": "npx",
    "args": ["-y", "@anthropic/container-use-mcp"],
    "env": {
      "DOCKER_HOST": "unix:///var/run/docker.sock"
    }
  }
}
```

### Core Concepts
- **Sandboxed execution**: Agent code runs in containers, not on host
- **Reproducible environments**: Dockerfile defines exact dependencies
- **MCP integration**: Available as MCP server for Claude Code
- **Resource limits**: CPU, memory, network constraints per container

### When to Use
- Running untrusted or experimental code safely
- Reproducible build and test environments
- Isolating agent actions from the host system
- CI/CD-like workflows triggered by AI agents

## Orchestration Patterns

### Fan-Out / Fan-In
Distribute work to multiple agents, aggregate results:
```
Coordinator
├── Agent A → Result A ─┐
├── Agent B → Result B ──┼→ Aggregate → Final Output
└── Agent C → Result C ─┘
```
Use when: Tasks are independent and can run in parallel.

### Pipeline (Sequential Stages)
Each stage processes and passes to the next:
```
Research → Plan → Implement → Test → Review → Deploy
```
Use when: Each stage depends on the previous stage's output.

### Event-Driven
Agents react to events rather than being explicitly scheduled:
```
File Change → Lint Agent
PR Created → Review Agent
Test Failure → Debug Agent
Deploy Success → Monitor Agent
```
Use when: Responses should be triggered by external events.

### Supervisor / Worker
One coordinator manages many workers:
```
Supervisor (assigns tasks, monitors progress)
├── Worker 1 (executes assigned task)
├── Worker 2 (executes assigned task)
└── Worker 3 (executes assigned task)
```
Use when: Tasks need dynamic assignment and coordination.

### Map-Reduce
Split input, process in parallel, combine results:
```
Input Data → Split into chunks
├── Process chunk 1 → Partial result
├── Process chunk 2 → Partial result
└── Process chunk 3 → Partial result
Combine partial results → Final output
```
Use when: Processing large datasets or documents.

## Tool Comparison

| Tool | Best For | Setup | Code Required |
|------|----------|-------|---------------|
| n8n | SaaS integrations | Docker/npx | Low (visual) |
| Langflow | LLM pipelines | pip install | Low (visual) |
| claude-squad | Parallel Claude agents | Go binary | None |
| container-use | Safe code execution | Docker + MCP | Low |

## Choosing the Right Tool

- **"Connect Slack to GitHub to Notion"** → n8n
- **"Build a RAG pipeline with embeddings"** → Langflow
- **"Refactor 10 files in parallel"** → claude-squad
- **"Run untrusted code safely"** → container-use
- **"Complex multi-step agent workflow"** → Combine tools as needed
