# Phase 1: Ingestion Engine Reference

// Pattern: Recursive directory scan with content hashing and metadata extraction

## Module Structure

```javascript
// idea-ingestion.js / Developer: Marcus Daley / Date / Idea file scanner

import { readdir, readFile, stat } from 'fs/promises';
import { join, extname, basename } from 'path';
import { createHash, randomUUID } from 'crypto';
import errorHandler from '../core/error-handler.js';

class IdeaIngestion {
  constructor(storage, eventBus) {
    this.storage = storage;
    this.eventBus = eventBus;
    this.supportedExtensions = ['.md', '.txt', '.json'];
  }

  // Recursively scan directory for idea files
  // Returns array of new IdeaRecord objects (deduped against storage)
  async scan(directory) {
    const files = await this.walkDirectory(directory);
    const newIdeas = [];

    for (const filePath of files) {
      try {
        const idea = await this.processFile(filePath);
        if (idea) {
          newIdeas.push(idea);
          this.eventBus.emit('idea_detected', { ideaId: idea.id, path: filePath });
        }
      } catch (err) {
        console.warn(`[IDEA-INGEST] Skip ${filePath}:`, err.message);
      }
    }

    return newIdeas;
  }

  // Recursive directory walker filtered by extension
  async walkDirectory(dir) {
    const entries = await readdir(dir, { withFileTypes: true });
    const files = [];

    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      if (entry.isDirectory()) {
        files.push(...await this.walkDirectory(fullPath));
      } else if (this.supportedExtensions.includes(extname(entry.name))) {
        files.push(fullPath);
      }
    }

    return files;
  }

  // Read file, hash, dedup check, extract metadata
  async processFile(filePath) {
    const content = await readFile(filePath, 'utf8');
    const contentHash = createHash('sha256').update(content).digest('hex');

    // Dedup check — skip if already in storage
    const existing = this.storage.findByHash(contentHash);
    if (existing) return null;

    const ext = extname(filePath);
    let metadata;

    if (ext === '.md') {
      metadata = this.extractMarkdownMeta(content, filePath);
    } else if (ext === '.txt') {
      metadata = this.extractTextMeta(content, filePath);
    } else if (ext === '.json') {
      metadata = this.extractJsonMeta(content, filePath);
    }

    return {
      id: randomUUID().slice(0, 12),
      title: metadata.title,
      summary: metadata.summary,
      tags: metadata.tags,
      source_path: filePath,
      content_hash: contentHash,
      raw_content: content,
      file_type: ext.slice(1),
      created_at: new Date().toISOString()
    };
  }

  // Parse markdown: frontmatter for tags, first # heading for title
  extractMarkdownMeta(content, filePath) {
    let title = basename(filePath, '.md');
    let tags = [];
    let summary = '';

    // Frontmatter parser (simple YAML extraction)
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (frontmatterMatch) {
      const fm = frontmatterMatch[1];
      const tagsMatch = fm.match(/tags:\s*\[(.*?)\]/);
      if (tagsMatch) {
        tags = tagsMatch[1].split(',').map(t => t.trim().replace(/['"]/g, ''));
      }
      content = content.slice(frontmatterMatch[0].length);
    }

    // First # heading
    const headingMatch = content.match(/^#\s+(.+)$/m);
    if (headingMatch) title = headingMatch[1].trim();

    // First non-empty paragraph after headings
    const paragraphs = content.split('\n\n').filter(p =>
      p.trim() && !p.trim().startsWith('#') && !p.trim().startsWith('---')
    );
    if (paragraphs.length > 0) {
      summary = paragraphs[0].trim().slice(0, 500);
    }

    // Inline #tags (if no frontmatter tags)
    if (tags.length === 0) {
      const inlineTags = content.match(/#(\w[\w-]*)/g);
      if (inlineTags) {
        tags = [...new Set(inlineTags.map(t => t.slice(1)))];
      }
    }

    return { title, summary, tags };
  }

  // Parse plain text: first line as title, find #tags
  extractTextMeta(content, filePath) {
    const lines = content.split('\n').filter(l => l.trim());
    const title = lines[0]?.trim() || basename(filePath, '.txt');
    const summary = lines.slice(1).join(' ').trim().slice(0, 500);

    const inlineTags = content.match(/#(\w[\w-]*)/g);
    const tags = inlineTags ? [...new Set(inlineTags.map(t => t.slice(1)))] : [];

    return { title, summary, tags };
  }

  // Parse JSON: read structured fields directly
  extractJsonMeta(content, filePath) {
    const data = JSON.parse(content);
    return {
      title: data.title || basename(filePath, '.json'),
      summary: (data.summary || data.description || '').slice(0, 500),
      tags: Array.isArray(data.tags) ? data.tags : []
    };
  }
}

export { IdeaIngestion };

// Self-test block
if (process.argv.includes('--test')) {
  // Mock storage with findByHash
  const mockStorage = {
    seen: new Set(),
    findByHash(hash) { return this.seen.has(hash) ? { hash } : null; },
  };
  const mockEventBus = { emit: (type, payload) => console.log(`[EVENT] ${type}`, payload) };

  const ingestion = new IdeaIngestion(mockStorage, mockEventBus);
  console.log('[TEST] Scanning fixtures...');
  const results = await ingestion.scan('./src/idea/fixtures');
  console.log(`[TEST] Found ${results.length} ideas`);

  if (results.length > 0) {
    console.log('[TEST] PASS — ingestion working');
  } else {
    console.log('[TEST] FAIL — no ideas detected');
    process.exit(1);
  }
}
```

## Test Cases

1. Scan a directory with 3 fixture files → returns 3 IdeaRecord objects
2. Scan again → returns 0 (dedup via content hash)
3. Modify a fixture → returns 1 (hash changed)
4. Unreadable file → logged warning, skipped, scan continues
5. Each record has: id, title, summary, tags, source_path, content_hash

## Common Pitfalls

- **Don't use sync fs operations** — use fs/promises throughout
- **Don't hash the path** — hash the content to detect changes
- **Don't trust the filename for title** — prefer first heading or structured field
- **Don't load huge files into memory** — add a max file size check (e.g., 10MB)
- **Don't emit events before storing** — emit after successful processing
