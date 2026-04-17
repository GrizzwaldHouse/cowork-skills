---
name: obsidian-knowledge
description: "Work with Obsidian vaults, markdown-based knowledge management, and personal knowledge systems. Use when the user mentions Obsidian, vault, wikilinks, PKM, personal knowledge management, Zettelkasten, PARA method, Maps of Content, daily notes, Dataview queries, or wants to organize notes and knowledge. Also trigger for creating knowledge base structures, linking strategies, or managing markdown-based documentation systems."
---

# Obsidian Knowledge Management

Patterns for working with Obsidian vaults -- markdown-based personal knowledge management with bidirectional linking.

## Obsidian Flavored Markdown (OFM)

### Wikilinks & Embeds
```markdown
[[Page Name]]                    # Link to page
[[Page Name|Display Text]]      # Link with alias
[[Page Name#Heading]]            # Link to specific heading
![[Page Name]]                   # Embed entire page
![[image.png]]                   # Embed image
![[Page Name#Heading]]           # Embed specific section
![[audio.mp3]]                   # Embed audio
```

### Properties (YAML Frontmatter)
```yaml
---
title: Note Title
date: 2026-04-15
tags: [project, research]
status: draft
aliases: [alternate-name]
cssclasses: [wide-page]
---
```

### Callouts
```markdown
> [!note] Title
> Standard informational callout

> [!warning] Caution
> Warning content

> [!tip] Pro Tip
> Helpful suggestion

> [!example]- Collapsible Example
> Content hidden by default (note the `-`)

> [!bug] Known Issue
> Bug description

> [!quote] Attribution
> Quoted content
```

Available types: `note`, `abstract`, `info`, `tip`, `success`, `question`, `warning`, `failure`, `danger`, `bug`, `example`, `quote`, `todo`

### Tags
```markdown
#tag                  # Inline tag
#project/subproject   # Nested tag
```

## Vault Structure Strategies

### Flat + Links (Zettelkasten)
```
vault/
├── inbox/           # Unsorted new notes
├── notes/           # All permanent notes (flat)
├── daily/           # Daily notes
├── templates/       # Note templates
└── attachments/     # Images, files
```
Relies on links and tags for organization, not folders. Each note is atomic (one idea per note) with explicit links to related notes.

### PARA Method
```
vault/
├── 1-Projects/      # Active projects with deadlines
├── 2-Areas/         # Ongoing responsibilities
├── 3-Resources/     # Reference material by topic
├── 4-Archive/       # Completed/inactive items
├── daily/
└── templates/
```

### MOC-Based (Maps of Content)
```
vault/
├── MOCs/            # Index notes that link to related content
│   ├── Programming MOC.md
│   ├── Game Dev MOC.md
│   └── Research MOC.md
├── notes/
├── projects/
└── daily/
```

MOC example:
```markdown
# Programming MOC

## Languages
- [[C++ Modern Patterns]]
- [[Python Best Practices]]
- [[TypeScript Advanced Types]]

## Architecture
- [[Design Patterns Overview]]
- [[Clean Architecture Notes]]

## Tools
- [[Git Workflow]]
- [[Docker Patterns]]
```

## Linking Strategies

### Link Types by Purpose
| Pattern | Use Case | Example |
|---------|----------|---------|
| Direct `[[link]]` | Explicit relationship | `See [[Observer Pattern]]` |
| Backlinks | Discover implicit connections | Check backlinks panel |
| Tags `#tag` | Categorization | `#gamedev #cpp` |
| Embedded `![[link]]` | Include content inline | `![[API Reference#Auth]]` |

### Atomic Notes
- One idea per note (easier to link, reuse, and find)
- Title should be a clear, searchable statement
- Link to source material and related concepts
- Add context for WHY you saved this (your insight, not just the fact)

## Dataview Queries

Dataview turns your vault into a queryable database:

```markdown
<!-- List all notes tagged 'project' modified this week -->
```dataview
LIST
FROM #project
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
```

<!-- Table of tasks across vault -->
```dataview
TABLE status, due, priority
FROM #task
WHERE status != "done"
SORT priority ASC
```

<!-- Count notes by tag -->
```dataview
TABLE length(rows) AS Count
FROM ""
FLATTEN file.tags AS tag
GROUP BY tag
SORT length(rows) DESC
```
```

### Common Dataview Filters
- `FROM "folder"` or `FROM #tag` - Source
- `WHERE contains(file.name, "term")` - Filter
- `SORT file.mtime DESC` - Order
- `LIMIT 10` - Cap results
- `GROUP BY field` - Aggregate

## Templates

### Daily Note Template
```markdown
---
date: {{date}}
tags: [daily]
---

# {{date:YYYY-MM-DD}} {{date:dddd}}

## Tasks
- [ ]

## Notes


## Log

```

### Project Note Template
```markdown
---
title: {{title}}
date: {{date}}
status: active
tags: [project]
---

# {{title}}

## Goal


## Tasks
- [ ]

## Notes


## Resources
-

## Log
### {{date}}
-
```

## JSON Canvas (.canvas)

Obsidian's visual canvas format for spatial note arrangement:

```json
{
  "nodes": [
    {
      "id": "node1",
      "type": "text",
      "text": "# Idea\nSome content",
      "x": 0, "y": 0, "width": 400, "height": 200
    },
    {
      "id": "node2",
      "type": "file",
      "file": "notes/My Note.md",
      "x": 500, "y": 0, "width": 400, "height": 300
    },
    {
      "id": "node3",
      "type": "link",
      "url": "https://example.com",
      "x": 0, "y": 300, "width": 400, "height": 200
    }
  ],
  "edges": [
    {
      "id": "edge1",
      "fromNode": "node1",
      "toNode": "node2",
      "label": "relates to"
    }
  ]
}
```

Node types: `text`, `file`, `link`, `group`

## CLI Operations

### Bulk Operations with Python
```python
from pathlib import Path
import re

vault = Path("path/to/vault")

# Find all notes linking to a specific page
target = "Design Patterns"
for md_file in vault.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    if f"[[{target}]]" in content or f"[[{target}|" in content:
        print(f"  {md_file.relative_to(vault)}")

# Find orphan notes (no incoming links)
all_notes = {f.stem for f in vault.rglob("*.md")}
linked_notes = set()
for md_file in vault.rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    links = re.findall(r'\[\[([^|\]]+)', content)
    linked_notes.update(links)

orphans = all_notes - linked_notes
print(f"Orphan notes: {len(orphans)}")

# Add tag to all notes in a folder
for md_file in (vault / "projects").rglob("*.md"):
    content = md_file.read_text(encoding="utf-8")
    if "#project" not in content:
        content = content.rstrip() + "\n\n#project\n"
        md_file.write_text(content, encoding="utf-8")
```

## Best Practices

- **Link generously**: When in doubt, link. Backlinks surface unexpected connections
- **Use aliases**: Add `aliases` in frontmatter for notes you reference by different names
- **Daily notes as inbox**: Capture everything in daily notes, then refine into permanent notes
- **Progressive summarization**: Bold key passages, highlight the bold, summarize highlights
- **Review regularly**: Scheduled review of recent notes strengthens connections
- **Templates save time**: Create templates for recurring note types (meetings, projects, books)
