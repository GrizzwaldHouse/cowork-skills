---
name: document-designer
description: Professional document formatting for Excel, Word, PowerPoint, and PDF generation via cowork-win tools. Auto-loaded for document creation tasks.
user-invocable: false
---

# Document Designer — Professional Formatting Standards

Apply these standards whenever generating documents through cowork-win tools (`create_excel`, `create_word`, `create_powerpoint`, `create_pdf`) or advising on document structure.

## General Document Principles

- **Purpose first**: Before creating any document, define its purpose and audience. A board report looks different from a team memo.
- **Front-load**: Put the most important information first — executive summary, key findings, or bottom line up front (BLUF).
- **Heading hierarchy**: H1 for document title (once), H2 for major sections, H3 for subsections. Never skip levels (H1 to H3).
- **Paragraph length**: 3-5 sentences each, never more than 7. Break long paragraphs into two.
- **Sentence length**: 15-25 words average. Vary for rhythm, but avoid 40+ word sentences.
- **Active voice**: "The team completed the project" not "The project was completed by the team."
- **Lists**: Use for 3-7 items. Parallel grammatical structure. Fewer than 3? Use prose. More than 7? Group into subcategories.
- **Numbers**: Comma-separated thousands (1,000). Two decimal places for currency ($1,234.56). One decimal for percentages (15.3%).
- **Dates**: ISO 8601 in data (2026-02-10). Localized in prose (February 10, 2026).

## Tool-Specific Guidance

### create_excel — See `excel-reference.md`
- Always include a "Summary" or "Dashboard" sheet as Sheet 1
- Bold headers are applied automatically — make them short and descriptive
- Include units in headers ("Revenue ($M)") not in data cells
- Sort data meaningfully — by date, by value, or by category
- Add a totals row at the bottom of numerical data

### create_word — See `word-reference.md`
- Always start with a heading level 1 (document title)
- Use the structured block format: heading, paragraph, table in logical order
- Never put two headings back-to-back — always have content between headings
- Tables need descriptive headers, not "Column A, Column B"
- Business documents should follow standard templates (memo, report, proposal)

### create_powerpoint — See `powerpoint-reference.md`
- First slide: always "title" layout with presentation title + context
- Body slides: "title_and_content" layout for text-based slides
- 6x6 Rule: max 6 bullets per slide, max 6 words per bullet
- One idea per slide — if you need two ideas, make two slides
- End with a clear CTA, summary, or next steps slide

### create_pdf — See `pdf-reference.md`
- Structure as heading/paragraph pairs — the tool only supports these two types
- Never create back-to-back headings without a paragraph between them
- Keep paragraphs under 100 words for PDF readability
- First page: title heading + introductory paragraph explaining the document

## Accessibility Standards

- All tables must have header rows with descriptive column names
- All documents must have logical reading order (heading hierarchy intact)
- Use descriptive titles — "Q4 Revenue by Region" not "Table 1"
- Avoid conveying meaning through color alone (use labels, icons, bold text)
- Minimum body text: 10pt for print, 12pt for screen-viewed PDFs
- Language should be plain and clear — avoid jargon unless audience is specialized
