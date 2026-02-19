# Notion & Figma Integration

## Name

Notion & Figma Integration

## Description

A skill for bridging design and project management workflows between Notion and Figma. It helps generate Notion database entries from Figma designs, sync design tokens, and create structured project pages from design files.

## Prerequisites

- A Notion workspace with API access (Notion Integration token)
- A Figma account with API access (Figma Personal Access Token)
- Node.js or Python for running integration scripts
- Familiarity with Notion databases and Figma components

## Usage

1. Describe the integration you need between Notion and Figma.
2. Provide API tokens or specify which workspace/project to target.
3. Define the data flow direction (Figma to Notion, Notion to Figma, or bidirectional).
4. Review the generated integration script or workflow.

### Prompt Pattern

```
I want to [sync/export/import] [data type] between Notion and Figma.
Direction: [Figma -> Notion / Notion -> Figma / bidirectional]
Notion database: [name or ID]
Figma file: [name or URL]
Data to transfer: [design tokens, component list, page structure, etc.]
```

## Examples

### Example 1: Export Figma Components to Notion Database

**Input:**
```
I want to export all Figma components from my design system file to a Notion database.
Direction: Figma -> Notion
Figma file: Design System v2
Data to transfer: Component name, description, variant count, last modified date.
```

**Output:**
```javascript
const figmaComponents = await figma.getFileComponents(FILE_KEY);

for (const component of figmaComponents) {
  await notion.pages.create({
    parent: { database_id: NOTION_DB_ID },
    properties: {
      'Name': { title: [{ text: { content: component.name } }] },
      'Description': { rich_text: [{ text: { content: component.description } }] },
      'Variants': { number: component.variants?.length ?? 0 },
      'Last Modified': { date: { start: component.updated_at } },
    },
  });
}
```

## Configuration

| Parameter           | Default | Description                                        |
|---------------------|---------|----------------------------------------------------|
| direction           | figma_to_notion | Data flow direction                       |
| sync_interval       | manual  | How often to sync (manual, hourly, daily)          |
| include_thumbnails  | false   | Download and attach Figma thumbnails to Notion     |
| notion_db_id        | null    | Target Notion database ID                          |
| figma_file_key      | null    | Source Figma file key                              |

## Notes

- Store API tokens in environment variables, never in code or documentation.
- The Figma API has rate limits; batch requests when syncing large files.
- See `resources/` for example integration scripts and token configuration templates.
