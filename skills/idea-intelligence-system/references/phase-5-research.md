# Phase 5: Research Intelligence Reference

// Pattern: LLM-driven competitive analysis (HIGH/MID priority only)

## LLM Prompt Template

```
Analyze this idea for competitive positioning.

Idea: {title}
Summary: {summary}
Category: {category}
Score: {score_total} ({priority_label})

Provide a competitive analysis:
1. Similar existing projects/tools (name, URL if known, key features)
2. Top 5 features competitors have
3. Features competitors are MISSING that this idea could provide
4. Key differentiator / competitive advantage

Respond with JSON only:
{
  "similar_projects": [
    {"name": "...", "description": "...", "url": "...", "features": ["..."]}
  ],
  "top_features": ["..."],
  "missing_features": ["..."],
  "gap_analysis": "...",
  "competitive_advantage": "..."
}
```

## Module Structure

```javascript
// research-agent.js

class ResearchAgent {
  constructor(storage, eventBus, llmClient, config = {}) {
    this.storage = storage;
    this.eventBus = eventBus;
    this.llmClient = llmClient;
    this.minPriority = config.min_priority || 'MID';
    this.allowedPriorities = this.getAllowedPriorities();
  }

  // Determine which priority labels qualify for research
  getAllowedPriorities() {
    const order = ['SHINY_OBJECT', 'LOW', 'MID', 'HIGH'];
    const minIdx = order.indexOf(this.minPriority);
    return order.slice(minIdx);
  }

  // Analyze a single scored idea
  async analyze(scoredIdea) {
    if (!this.allowedPriorities.includes(scoredIdea.priority_label)) {
      console.log(`[RESEARCH] Skip ${scoredIdea.id} — priority ${scoredIdea.priority_label} below ${this.minPriority}`);
      return null;
    }

    this.eventBus.emit('research_started', { ideaId: scoredIdea.id });

    const prompt = this.buildPrompt(scoredIdea);
    const response = await this.llmClient.chat({
      task: 'idea_research',
      messages: [{ role: 'user', content: prompt }],
      response_format: 'json'
    });

    const report = JSON.parse(response.content);
    this.validateReport(report);

    this.storage.updateIdea(scoredIdea.id, {
      related_projects: JSON.stringify(report.similar_projects),
      missing_features: JSON.stringify(report.missing_features),
      status: 'researched'
    });

    this.eventBus.emit('research_completed', {
      ideaId: scoredIdea.id,
      similarCount: report.similar_projects.length,
      gapsFound: report.missing_features.length
    });

    return report;
  }

  // Validate report structure has required fields
  validateReport(report) {
    const required = ['similar_projects', 'top_features', 'missing_features', 'gap_analysis'];
    for (const field of required) {
      if (!(field in report)) {
        throw new Error(`Research report missing field: ${field}`);
      }
    }
    if (!Array.isArray(report.similar_projects)) {
      throw new Error('similar_projects must be an array');
    }
  }

  // Process a batch — filters by priority automatically
  async analyzeBatch(scoredIdeas) {
    const results = [];
    for (const idea of scoredIdeas) {
      const report = await this.analyze(idea);
      if (report) results.push({ idea, report });
    }
    return results;
  }

  buildPrompt(idea) {
    return `Analyze this idea for competitive positioning.

Idea: ${idea.title}
Summary: ${idea.summary}
Category: ${idea.category}
Score: ${idea.score_total.toFixed(2)} (${idea.priority_label})

Provide a competitive analysis:
1. Similar existing projects/tools (name, URL if known, key features)
2. Top 5 features competitors have
3. Features competitors are MISSING that this idea could provide
4. Key differentiator / competitive advantage

Respond with JSON only:
{
  "similar_projects": [
    {"name": "...", "description": "...", "url": "...", "features": ["..."]}
  ],
  "top_features": ["..."],
  "missing_features": ["..."],
  "gap_analysis": "...",
  "competitive_advantage": "..."
}`;
  }
}

// Self-test (no LLM required)
if (process.argv.includes('--test')) {
  const research = new ResearchAgent(null, null, null);

  // Test priority filtering
  console.assert(research.allowedPriorities.includes('HIGH'));
  console.assert(research.allowedPriorities.includes('MID'));
  console.assert(!research.allowedPriorities.includes('LOW'));
  console.assert(!research.allowedPriorities.includes('SHINY_OBJECT'));

  // Test report validation
  try {
    research.validateReport({ similar_projects: [], top_features: [] });
    console.error('[TEST] FAIL — should have thrown for missing fields');
    process.exit(1);
  } catch (err) {
    console.log('[TEST] Validation correctly rejected incomplete report');
  }

  console.log('[TEST] PASS — research agent structural');
}
```

## Common Pitfalls

- **Don't analyze every idea** — research is expensive, skip LOW/SHINY_OBJECT
- **Don't store unparsed JSON in columns** — JSON.stringify before storage
- **Don't forget URL safety** — competitor URLs from LLM may be hallucinated, treat as suggestions
- **Don't run research synchronously** — it's slow, use a queue if processing many ideas
- **Don't omit the priority check** — wastes tokens on ideas that don't matter
