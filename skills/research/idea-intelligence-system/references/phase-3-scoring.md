# Phase 3: Scoring Algorithm Reference

// Pattern: LLM-driven dimension estimation + weighted sum + priority labels

## Default Weights (Configurable)

```javascript
const DEFAULT_WEIGHTS = {
  profitability: 0.30,
  portfolio_value: 0.25,
  execution_speed: 0.15,
  complexity_inverse: 0.15,  // Note: inverted from raw complexity
  novelty: 0.15
};
// Sum: 1.00
```

## Priority Thresholds

```javascript
const THRESHOLDS = {
  HIGH: 0.75,
  MID: 0.50,
  LOW: 0.25,
  // SHINY_OBJECT < 0.25
};
```

## LLM Prompt Template

```
Score this idea on 5 dimensions (0.0 to 1.0 each).
Consider the user's context: {user_context}

Idea: {title}
Summary: {summary}
Category: {category}

Dimensions:
1. profitability — Revenue potential for the user
2. portfolio_value — How impressive this looks in their portfolio
3. execution_speed — How quickly one person can build an MVP
4. complexity — Technical difficulty (1.0 = extremely complex)
5. novelty — How unique vs existing solutions

Respond with JSON only:
{
  "profitability": 0.0,
  "portfolio_value": 0.0,
  "execution_speed": 0.0,
  "complexity": 0.0,
  "novelty": 0.0,
  "reasoning": "..."
}
```

## Module Structure

```javascript
// idea-scoring.js

class IdeaScoring {
  constructor(storage, eventBus, llmClient, config = {}) {
    this.storage = storage;
    this.eventBus = eventBus;
    this.llmClient = llmClient;
    this.weights = config.weights || DEFAULT_WEIGHTS;
    this.thresholds = config.thresholds || THRESHOLDS;
  }

  // Score a single idea via LLM
  async score(ideaRecord) {
    const prompt = this.buildPrompt(ideaRecord);
    const response = await this.llmClient.chat({
      task: 'idea_scoring',
      messages: [{ role: 'user', content: prompt }],
      response_format: 'json'
    });

    const parsed = JSON.parse(response.content);
    const dimensions = this.validateDimensions(parsed);
    const scoreTotal = this.computeScore(dimensions);
    const priorityLabel = this.assignPriority(scoreTotal);

    this.storage.updateIdea(ideaRecord.id, {
      profitability_score: dimensions.profitability,
      portfolio_score: dimensions.portfolio_value,
      execution_speed_score: dimensions.execution_speed,
      complexity_score: dimensions.complexity,
      novelty_score: dimensions.novelty,
      score_total: scoreTotal,
      priority_label: priorityLabel,
      status: 'scored'
    });

    this.eventBus.emit('idea_scored', {
      ideaId: ideaRecord.id,
      score: scoreTotal,
      dimensions
    });
    this.eventBus.emit('idea_ranked', {
      ideaId: ideaRecord.id,
      priorityLabel
    });

    return {
      ...ideaRecord,
      ...dimensions,
      score_total: scoreTotal,
      priority_label: priorityLabel
    };
  }

  // Clamp all dimension scores to 0.0-1.0 range
  validateDimensions(parsed) {
    const required = ['profitability', 'portfolio_value', 'execution_speed', 'complexity', 'novelty'];
    const result = {};
    for (const key of required) {
      const val = parsed[key];
      if (typeof val !== 'number') {
        throw new Error(`Missing or invalid dimension: ${key}`);
      }
      result[key] = Math.max(0.0, Math.min(1.0, val));
    }
    return result;
  }

  // Weighted sum with complexity inversion
  computeScore(d) {
    return (
      d.profitability * this.weights.profitability +
      d.portfolio_value * this.weights.portfolio_value +
      d.execution_speed * this.weights.execution_speed +
      (1.0 - d.complexity) * this.weights.complexity_inverse +
      d.novelty * this.weights.novelty
    );
  }

  // Assign priority label from total score
  assignPriority(score) {
    if (score >= this.thresholds.HIGH) return 'HIGH';
    if (score >= this.thresholds.MID) return 'MID';
    if (score >= this.thresholds.LOW) return 'LOW';
    return 'SHINY_OBJECT';
  }

  buildPrompt(ideaRecord) {
    // Pull user_context from config or use generic placeholder
    return `Score this idea on 5 dimensions (0.0 to 1.0 each).

Idea: ${ideaRecord.title}
Summary: ${ideaRecord.summary}
Category: ${ideaRecord.category}

Dimensions:
1. profitability — Revenue potential
2. portfolio_value — How impressive in a portfolio
3. execution_speed — How quickly one person can build an MVP
4. complexity — Technical difficulty (1.0 = extremely complex)
5. novelty — How unique vs existing solutions

Respond with JSON only:
{
  "profitability": 0.0,
  "portfolio_value": 0.0,
  "execution_speed": 0.0,
  "complexity": 0.0,
  "novelty": 0.0,
  "reasoning": "..."
}`;
  }
}

// Self-test (no LLM required)
if (process.argv.includes('--test')) {
  const scorer = new IdeaScoring(null, null, null);

  // Test 1: Perfect score should hit HIGH
  const perfect = { profitability: 1.0, portfolio_value: 1.0, execution_speed: 1.0, complexity: 0.0, novelty: 1.0 };
  const score1 = scorer.computeScore(perfect);
  console.assert(score1 === 1.0, `Expected 1.0, got ${score1}`);
  console.assert(scorer.assignPriority(score1) === 'HIGH');

  // Test 2: Zero score should hit SHINY_OBJECT
  const zero = { profitability: 0, portfolio_value: 0, execution_speed: 0, complexity: 1.0, novelty: 0 };
  const score2 = scorer.computeScore(zero);
  console.assert(score2 === 0.0, `Expected 0.0, got ${score2}`);
  console.assert(scorer.assignPriority(score2) === 'SHINY_OBJECT');

  // Test 3: Mid-range
  const mid = { profitability: 0.6, portfolio_value: 0.6, execution_speed: 0.6, complexity: 0.4, novelty: 0.6 };
  const score3 = scorer.computeScore(mid);
  console.assert(score3 >= 0.50 && score3 < 0.75, `Expected MID range, got ${score3}`);

  console.log('[TEST] PASS — scoring formula correct');
}
```

## Common Pitfalls

- **Don't forget to invert complexity** — high complexity should LOWER the score
- **Don't store complexity_inverse_score** — store raw complexity, invert at compute time
- **Don't hardcode weights** — accept via constructor config
- **Don't let weights exceed 1.0 sum** — validate at startup
- **Don't trust LLM scores blindly** — clamp to 0.0-1.0
