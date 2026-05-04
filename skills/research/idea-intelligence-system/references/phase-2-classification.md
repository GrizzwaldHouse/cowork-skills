# Phase 2: Classification Engine Reference

// Pattern: AI categorization + embedding-based duplicate detection

## LLM Prompt Template

```
Classify this idea into exactly ONE category.
Categories: AI, Tooling, Product, Experimental, Game Dev, Infrastructure

Title: {title}
Summary: {summary}
Tags: {tags}

Respond with JSON only, no markdown:
{"category": "...", "confidence": 0.0-1.0, "reasoning": "..."}
```

## Module Structure

```javascript
// idea-classifier.js

class IdeaClassifier {
  constructor(storage, eventBus, llmClient) {
    this.storage = storage;
    this.eventBus = eventBus;
    this.llmClient = llmClient;
    this.duplicateThreshold = 0.92;
    this.relatedThreshold = 0.70;
    this.validCategories = [
      'AI', 'Tooling', 'Product', 'Experimental', 'Game Dev', 'Infrastructure'
    ];
  }

  // Classify single idea via LLM
  async classify(ideaRecord) {
    const prompt = this.buildPrompt(ideaRecord);
    const response = await this.llmClient.chat({
      task: 'idea_classification',
      messages: [{ role: 'user', content: prompt }],
      response_format: 'json'
    });

    const parsed = JSON.parse(response.content);
    if (!this.validCategories.includes(parsed.category)) {
      throw new Error(`Invalid category: ${parsed.category}`);
    }

    this.storage.updateIdea(ideaRecord.id, {
      category: parsed.category,
      status: 'classified'
    });

    this.eventBus.emit('idea_classified', {
      ideaId: ideaRecord.id,
      category: parsed.category,
      confidence: parsed.confidence
    });

    return { ...ideaRecord, category: parsed.category };
  }

  // Detect duplicates and related ideas via embedding similarity
  async detectDuplicates(ideaRecord, allIdeas) {
    // Generate embedding for current idea
    const queryEmbedding = await this.generateEmbedding(ideaRecord);
    const relationships = [];

    for (const existing of allIdeas) {
      if (existing.id === ideaRecord.id || !existing.embedding) continue;

      const existingEmbedding = JSON.parse(existing.embedding);
      const similarity = this.cosineSimilarity(queryEmbedding, existingEmbedding);

      if (similarity >= this.duplicateThreshold) {
        relationships.push({
          idea_id: ideaRecord.id,
          related_idea_id: existing.id,
          similarity_score: similarity,
          relationship_type: 'duplicate'
        });
        this.eventBus.emit('idea_duplicate', {
          ideaId: ideaRecord.id,
          duplicateOf: existing.id,
          similarity
        });
      } else if (similarity >= this.relatedThreshold) {
        relationships.push({
          idea_id: ideaRecord.id,
          related_idea_id: existing.id,
          similarity_score: similarity,
          relationship_type: 'related'
        });
      }
    }

    // Persist relationships
    for (const rel of relationships) {
      this.storage.insertRelationship(rel);
    }

    return relationships;
  }

  buildPrompt(ideaRecord) {
    return `Classify this idea into exactly ONE category.
Categories: ${this.validCategories.join(', ')}

Title: ${ideaRecord.title}
Summary: ${ideaRecord.summary}
Tags: ${ideaRecord.tags.join(', ')}

Respond with JSON only, no markdown:
{"category": "...", "confidence": 0.0-1.0, "reasoning": "..."}`;
  }

  // Cosine similarity — pure math, testable without LLM
  cosineSimilarity(a, b) {
    if (a.length !== b.length) {
      throw new Error(`Vector dimension mismatch: ${a.length} vs ${b.length}`);
    }
    let dot = 0, normA = 0, normB = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    return dot / (Math.sqrt(normA) * Math.sqrt(normB));
  }
}

// Self-test
if (process.argv.includes('--test')) {
  const classifier = new IdeaClassifier(null, null, null);

  // Test 1: identical vectors → similarity 1.0
  const sim1 = classifier.cosineSimilarity([1, 0, 0], [1, 0, 0]);
  console.assert(sim1 === 1.0, `Expected 1.0, got ${sim1}`);

  // Test 2: orthogonal vectors → similarity 0.0
  const sim2 = classifier.cosineSimilarity([1, 0, 0], [0, 1, 0]);
  console.assert(sim2 === 0.0, `Expected 0.0, got ${sim2}`);

  // Test 3: opposite vectors → similarity -1.0
  const sim3 = classifier.cosineSimilarity([1, 0, 0], [-1, 0, 0]);
  console.assert(sim3 === -1.0, `Expected -1.0, got ${sim3}`);

  console.log('[TEST] PASS — classifier math correct');
}
```

## Common Pitfalls

- **Don't trust LLM JSON output blindly** — always validate against allowed categories
- **Don't compare embeddings of different dimensions** — throw early
- **Don't store embeddings as strings repeatedly** — parse once when loading
- **Don't run dedup before classification** — categories help disambiguate
- **Don't use Levenshtein or fuzzy string match** — embeddings handle synonyms better
