# Phase 6: Indexing Engine Reference

// Pattern: Vector embeddings + cosine similarity + cross-linking

## Module Structure

```javascript
// idea-indexer.js

class IdeaIndexer {
  constructor(storage, eventBus, llmClient, config = {}) {
    this.storage = storage;
    this.eventBus = eventBus;
    this.llmClient = llmClient;
    this.embeddingModel = config.embedding_model || 'nomic-embed-text';
    this.duplicateThreshold = config.duplicate_threshold || 0.92;
    this.relatedThreshold = config.related_threshold || 0.70;
  }

  // Generate vector embedding for arbitrary text
  async generateEmbedding(text) {
    const response = await this.llmClient.chat({
      task: 'idea_embedding',
      messages: [{ role: 'user', content: text }],
      embedding_mode: true,
      model_override: this.embeddingModel
    });

    if (!Array.isArray(response.embedding)) {
      throw new Error('Embedding response must be an array of numbers');
    }
    return response.embedding;
  }

  // Index a single idea: generate + store embedding
  async index(ideaRecord) {
    const text = `${ideaRecord.title}\n${ideaRecord.summary}\n${ideaRecord.category || ''}\nTags: ${(ideaRecord.tags || []).join(', ')}`;
    const embedding = await this.generateEmbedding(text);

    this.storage.updateIdea(ideaRecord.id, {
      embedding: JSON.stringify(embedding),
      status: 'indexed'
    });

    this.eventBus.emit('idea_indexed', {
      ideaId: ideaRecord.id,
      dimensions: embedding.length
    });

    return { ...ideaRecord, embedding };
  }

  // Cross-link a single idea against all other indexed ideas
  async crossLink(ideaId) {
    const target = this.storage.getIdea(ideaId);
    if (!target?.embedding) {
      throw new Error(`Idea ${ideaId} has no embedding — index first`);
    }

    const targetVec = JSON.parse(target.embedding);
    const allIdeas = this.storage.getAllIdeas().filter(i =>
      i.id !== ideaId && i.embedding
    );

    const newRelationships = [];

    for (const other of allIdeas) {
      const otherVec = JSON.parse(other.embedding);
      const similarity = IdeaIndexer.cosineSimilarity(targetVec, otherVec);

      let relationshipType = null;
      if (similarity >= this.duplicateThreshold) {
        relationshipType = 'duplicate';
      } else if (similarity >= this.relatedThreshold) {
        relationshipType = 'related';
      }

      if (relationshipType) {
        const relId = this.storage.insertRelationship({
          idea_id: ideaId,
          related_idea_id: other.id,
          similarity_score: similarity,
          relationship_type: relationshipType
        });
        newRelationships.push({ id: relId, similarity, type: relationshipType });
        this.eventBus.emit('idea_linked', {
          ideaId,
          relatedId: other.id,
          similarity,
          type: relationshipType
        });
      }
    }

    return newRelationships;
  }

  // Semantic search: query text → top K similar ideas
  async search(queryText, topK = 10) {
    const queryVec = await this.generateEmbedding(queryText);
    const allIdeas = this.storage.getAllIdeas().filter(i => i.embedding);

    const ranked = allIdeas
      .map(idea => ({
        ...idea,
        similarity: IdeaIndexer.cosineSimilarity(queryVec, JSON.parse(idea.embedding))
      }))
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, topK);

    return ranked;
  }

  // Index all unindexed ideas, then cross-link each
  async indexAll() {
    const unindexed = this.storage.getIdeasByStatus('scored');
    const results = [];

    for (const idea of unindexed) {
      const indexed = await this.index(idea);
      const links = await this.crossLink(idea.id);
      results.push({ idea: indexed, links });
    }

    return results;
  }

  // Cosine similarity — pure math, static for testability
  static cosineSimilarity(a, b) {
    if (a.length !== b.length) {
      throw new Error(`Vector dimension mismatch: ${a.length} vs ${b.length}`);
    }
    let dot = 0, normA = 0, normB = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    const denom = Math.sqrt(normA) * Math.sqrt(normB);
    return denom === 0 ? 0 : dot / denom;
  }
}

// Self-test (no LLM required)
if (process.argv.includes('--test')) {
  // Test 1: identical → 1.0
  const sim1 = IdeaIndexer.cosineSimilarity([1, 2, 3], [1, 2, 3]);
  console.assert(Math.abs(sim1 - 1.0) < 1e-10, `Expected ~1.0, got ${sim1}`);

  // Test 2: orthogonal → 0.0
  const sim2 = IdeaIndexer.cosineSimilarity([1, 0, 0], [0, 1, 0]);
  console.assert(sim2 === 0.0, `Expected 0.0, got ${sim2}`);

  // Test 3: zero vector handling
  const sim3 = IdeaIndexer.cosineSimilarity([0, 0, 0], [1, 2, 3]);
  console.assert(sim3 === 0, `Expected 0 for zero vector, got ${sim3}`);

  // Test 4: dimension mismatch throws
  try {
    IdeaIndexer.cosineSimilarity([1, 2], [1, 2, 3]);
    console.error('[TEST] FAIL — should throw for mismatch');
    process.exit(1);
  } catch (err) {
    console.log('[TEST] Dimension mismatch correctly rejected');
  }

  console.log('[TEST] PASS — indexer math correct');
}
```

## Common Pitfalls

- **Don't forget zero-vector edge case** — divide-by-zero produces NaN
- **Don't store embeddings as separate file** — keep in DB column for query simplicity
- **Don't skip dimension validation** — catch model mismatches early
- **Don't recompute embeddings every search** — they're stored, only embed the query
- **Don't cross-link without checking existing relationships** — duplicates accumulate
- **Don't use Euclidean distance** — cosine handles magnitude differences better for embeddings
- **Don't load all embeddings every search at scale** — for >10k ideas, switch to FAISS or sqlite-vss
