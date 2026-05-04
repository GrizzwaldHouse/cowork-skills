# Phase 4: Database Schema Reference

// Pattern: Migration added to existing orchestration storage — never a separate DB

## Migration v2 SQL

```sql
-- Migration v2: Idea Intelligence tables
-- Adds 2 tables to existing orchestration database

CREATE TABLE IF NOT EXISTS ideas (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  summary TEXT,
  category TEXT CHECK (category IN (
    'AI', 'Tooling', 'Product', 'Experimental', 'Game Dev', 'Infrastructure'
  )),
  score_total REAL DEFAULT 0.0,
  priority_label TEXT CHECK (priority_label IN ('HIGH', 'MID', 'LOW', 'SHINY_OBJECT')),
  profitability_score REAL DEFAULT 0.0,
  portfolio_score REAL DEFAULT 0.0,
  complexity_score REAL DEFAULT 0.0,
  novelty_score REAL DEFAULT 0.0,
  execution_speed_score REAL DEFAULT 0.0,
  related_projects TEXT DEFAULT '[]',
  missing_features TEXT DEFAULT '[]',
  source_path TEXT,
  content_hash TEXT NOT NULL,
  embedding TEXT,
  vault_path TEXT,
  status TEXT DEFAULT 'raw' CHECK (status IN (
    'raw', 'classified', 'scored', 'researched', 'indexed', 'executing', 'completed'
  )),
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS idea_relationships (
  id TEXT PRIMARY KEY,
  idea_id TEXT NOT NULL,
  related_idea_id TEXT NOT NULL,
  similarity_score REAL DEFAULT 0.0,
  relationship_type TEXT CHECK (relationship_type IN (
    'duplicate', 'related', 'extends', 'conflicts', 'supersedes'
  )),
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE,
  FOREIGN KEY (related_idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ideas_priority ON ideas(priority_label);
CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
CREATE INDEX IF NOT EXISTS idx_ideas_score ON ideas(score_total DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_hash ON ideas(content_hash);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_idea_rels_idea ON idea_relationships(idea_id);
CREATE INDEX IF NOT EXISTS idx_idea_rels_related ON idea_relationships(related_idea_id);
```

## CRUD Methods to Add

```javascript
// Add to OrchestrationStorage class

// Insert new idea, returns id
insertIdea(idea) {
  const stmt = this.db.prepare(`
    INSERT INTO ideas (id, title, summary, category, content_hash, source_path, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);
  stmt.run(idea.id, idea.title, idea.summary, idea.category || null,
           idea.content_hash, idea.source_path, idea.status || 'raw');
  return idea.id;
}

// Get single idea
getIdea(id) {
  return this.db.prepare('SELECT * FROM ideas WHERE id = ?').get(id);
}

// Partial update with auto updated_at
updateIdea(id, fields) {
  const allowed = [
    'title', 'summary', 'category', 'score_total', 'priority_label',
    'profitability_score', 'portfolio_score', 'complexity_score',
    'novelty_score', 'execution_speed_score', 'related_projects',
    'missing_features', 'embedding', 'vault_path', 'status'
  ];
  const updates = Object.keys(fields).filter(k => allowed.includes(k));
  if (updates.length === 0) return;

  const setClause = updates.map(k => `${k} = ?`).join(', ');
  const values = updates.map(k => fields[k]);
  const sql = `UPDATE ideas SET ${setClause}, updated_at = datetime('now') WHERE id = ?`;
  this.db.prepare(sql).run(...values, id);
}

// Delete idea (hard delete)
deleteIdea(id) {
  this.db.prepare('DELETE FROM ideas WHERE id = ?').run(id);
}

// Filter by priority
getIdeasByPriority(label) {
  return this.db.prepare('SELECT * FROM ideas WHERE priority_label = ? ORDER BY score_total DESC').all(label);
}

// Filter by category
getIdeasByCategory(category) {
  return this.db.prepare('SELECT * FROM ideas WHERE category = ? ORDER BY score_total DESC').all(category);
}

// Filter by processing status
getIdeasByStatus(status) {
  return this.db.prepare('SELECT * FROM ideas WHERE status = ?').all(status);
}

// Dedup check via content hash
findByHash(hash) {
  return this.db.prepare('SELECT * FROM ideas WHERE content_hash = ?').get(hash);
}

// Text search on title + summary
searchIdeas(query) {
  const pattern = `%${query}%`;
  return this.db.prepare(`
    SELECT * FROM ideas
    WHERE title LIKE ? OR summary LIKE ?
    ORDER BY score_total DESC
  `).all(pattern, pattern);
}

// Top N by score
getTopIdeas(limit = 10) {
  return this.db.prepare('SELECT * FROM ideas ORDER BY score_total DESC LIMIT ?').all(limit);
}

// Full list
getAllIdeas() {
  return this.db.prepare('SELECT * FROM ideas ORDER BY created_at DESC').all();
}

// Add relationship
insertRelationship(rel) {
  const id = randomUUID().slice(0, 12);
  this.db.prepare(`
    INSERT INTO idea_relationships (id, idea_id, related_idea_id, similarity_score, relationship_type)
    VALUES (?, ?, ?, ?, ?)
  `).run(id, rel.idea_id, rel.related_idea_id, rel.similarity_score, rel.relationship_type);
  return id;
}

// Get all relationships for an idea
getRelationships(ideaId) {
  return this.db.prepare(`
    SELECT * FROM idea_relationships
    WHERE idea_id = ? OR related_idea_id = ?
  `).all(ideaId, ideaId);
}

// Find duplicate relationships
findDuplicates(ideaId) {
  return this.db.prepare(`
    SELECT * FROM idea_relationships
    WHERE (idea_id = ? OR related_idea_id = ?) AND relationship_type = 'duplicate'
  `).all(ideaId, ideaId);
}
```

## Common Pitfalls

- **Don't create a separate database** — add migration to existing orchestration.db
- **Don't forget the migration version table** — increment to v2
- **Don't skip the CHECK constraints** — they prevent bad enum values
- **Don't store JSON columns as parsed objects** — keep as TEXT, parse on read
- **Don't omit the indexes** — query performance degrades fast at 1000+ ideas
- **Don't use AUTOINCREMENT** — use TEXT primary keys with randomUUID().slice(0, 12)
