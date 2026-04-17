---
name: context-optimization
description: "Optimize context window usage, prevent context degradation, and implement memory systems for AI agents. Use when the user asks about context window management, token optimization, agent memory, context compression, multi-agent context coordination, or when working with long conversations that approach context limits. Also trigger when the user mentions 'context degradation', 'lost in the middle', 'context poisoning', attention mechanics, or needs to design memory/caching systems for AI applications."
---

# Context Optimization Skill

Patterns and strategies for managing AI context windows effectively, based on research into LLM attention mechanics and multi-agent coordination.

## Context Fundamentals

### Token Budget Awareness
- **Know your limits**: Track approximate token usage across the conversation
- **Front-load critical info**: Place the most important context early in the prompt
- **Prune aggressively**: Remove information that's no longer relevant
- **Use progressive disclosure**: Load detailed information only when needed

### Attention Mechanics
LLMs attend unevenly across the context window:
- **Primacy effect**: Strong attention to content at the beginning
- **Recency effect**: Strong attention to content at the end
- **Lost-in-the-middle**: Weakened attention for content in the middle of long contexts
- **Implication**: Place critical instructions at the start AND end, not buried in the middle

## Context Degradation Patterns

### Types of Degradation

1. **Lost-in-the-Middle**: Important information in the middle of the context gets overlooked
   - **Fix**: Move critical info to beginning or end; use explicit references

2. **Context Poisoning**: Incorrect or outdated information earlier in the conversation overrides correct information later
   - **Fix**: Explicitly invalidate old info ("Ignore previous instruction about X, the correct approach is Y")

3. **Distraction**: Irrelevant context dilutes attention from important information
   - **Fix**: Remove irrelevant context; keep conversations focused

4. **Context Clash**: Contradictory instructions cause unpredictable behavior
   - **Fix**: Audit for contradictions; establish clear priority rules

5. **Saturation**: Too much information causes shallow processing across all content
   - **Fix**: Summarize and compress; use hierarchical context loading

## Compression Strategies

### Summarization
Replace verbose context with concise summaries when full detail isn't needed:
```
BEFORE (500 tokens): [Full discussion of architecture decisions A, B, C, D]
AFTER (100 tokens): "Architecture: Chose microservices (A) over monolith for scalability.
Key tradeoff: Higher operational complexity accepted for independent deployability."
```

### Hierarchical Context
Structure information in layers of detail:
1. **Layer 1** (always loaded): Project overview, current objective, key constraints
2. **Layer 2** (loaded on demand): Module-specific details, API specs
3. **Layer 3** (loaded when needed): Implementation details, code examples, edge cases

### Context Offloading
Move information out of the context window to external storage:
- **Filesystem**: Write detailed plans, specs, and intermediate results to files
- **Structured logs**: Append decisions and findings to JSONL files
- **Summary files**: Maintain a running summary that gets updated, not appended

### KV-Cache Optimization
For multi-turn conversations:
- Keep system prompt stable (shared KV-cache prefix across turns)
- Batch related queries to reuse cached context
- Structure messages so common prefix is maximized

## Memory Systems for Agents

### Short-Term Memory (Within Session)
- **Working memory**: Current task context, recent findings, active decisions
- **Conversation buffer**: Last N exchanges (sliding window)
- **Implementation**: Keep in-context, prune as conversation grows

### Long-Term Memory (Across Sessions)
- **Persistent files**: MEMORY.md, project notes, decision logs
- **Structured storage**: JSON/JSONL files for searchable records
- **Pattern**: Write key learnings to memory files at end of significant tasks

### Memory Architecture Pattern
```
memory/
├── MEMORY.md           # Always loaded (keep concise, <200 lines)
├── decisions.md        # Architectural decisions and rationale
├── patterns.md         # Discovered patterns and conventions
├── debugging.md        # Solutions to recurring problems
└── project-context.md  # Project-specific knowledge
```

### Memory Write Rules
- **Save**: Stable patterns confirmed across multiple interactions
- **Save**: User preferences explicitly stated
- **Save**: Solutions to recurring problems
- **Skip**: Session-specific context (current task details)
- **Skip**: Speculative conclusions from a single observation
- **Update**: Correct outdated information immediately

## Multi-Agent Context Coordination

### Context Partitioning
When multiple agents work in parallel:
- **Shared context**: Project-level goals, constraints, conventions
- **Agent-specific context**: Task details, relevant code sections
- **Handoff context**: Summary of findings for the next agent

### Handoff Protocol
When passing work between agents:
```markdown
## Handoff Summary
**Completed**: [What was done]
**Key Findings**: [Important discoveries]
**Current State**: [Where things stand]
**Next Steps**: [What the receiving agent should do]
**Files Modified**: [List of changed files]
**Open Questions**: [Unresolved issues]
```

### Context Isolation
- Each agent should have only the context it needs
- Avoid loading full conversation history into subagents
- Pass specific, relevant information in the task prompt
- Use files for sharing large data between agents

## Practical Patterns

### For Long Coding Sessions
1. Periodically summarize progress to a scratchpad file
2. Before starting a new subtask, re-read the current objective
3. When context gets long, create a "current state" summary
4. Use structured TODO lists to track remaining work

### For Research Tasks
1. Write findings to files as you go (don't keep everything in context)
2. Create an outline file early, update it as research progresses
3. Final synthesis reads from files, not from conversation history

### For Multi-File Edits
1. Read all files first, create a plan
2. Execute edits in order, tracking what's been done
3. Use a checklist file to track progress
4. Final verification reads modified files to confirm correctness
