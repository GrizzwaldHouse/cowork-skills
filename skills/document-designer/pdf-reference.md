# PDF Reference — Layout Standards for create_pdf

## Tool Constraints

The `create_pdf` tool uses FPDF with these fixed settings:
- Font: Helvetica (Regular 12pt body, Bold 16pt headings)
- Auto page break with 15mm bottom margin
- Default FPDF margins (10mm left/right)
- Only two block types supported: `"heading"` and `"paragraph"`
- No bullet lists, tables, images, or custom fonts

Work within these constraints by:
- Using numbered items within paragraphs for lists
- Using clear paragraph breaks for visual separation
- Structuring information through heading/paragraph pairs

## Content Organization Rules

1. **Always start with a title heading** followed by an introductory paragraph
2. **Never put two headings back-to-back** — always have at least one paragraph between headings
3. **Each heading should be followed by 1-3 paragraphs** before the next heading
4. **Keep paragraphs under 100 words** for PDF readability
5. **Front-load each paragraph** with its key message in the first sentence
6. **Use short sentences** (15-20 words average) since PDF is often read on screen

## Document Type Templates

### One-Pager / Executive Brief

```json
[
  {"type": "heading", "text": "[Title: Clear and Specific]"},
  {"type": "paragraph", "text": "[2-3 sentence overview: what this document covers and why it matters]"},
  {"type": "heading", "text": "Key Findings"},
  {"type": "paragraph", "text": "[Most important finding or insight, stated clearly with supporting data. Include 2-3 key data points.]"},
  {"type": "heading", "text": "Recommendation"},
  {"type": "paragraph", "text": "[Clear recommended action with rationale. State expected impact and timeline.]"},
  {"type": "heading", "text": "Next Steps"},
  {"type": "paragraph", "text": "The following actions are recommended: 1) [Action with owner and deadline]. 2) [Action with owner and deadline]. 3) [Action with owner and deadline]."}
]
```

### Standard Report

```json
[
  {"type": "heading", "text": "[Report Title]"},
  {"type": "paragraph", "text": "Prepared by [Author] on [Date] for [Audience]. This report covers [scope] for the period [timeframe]."},
  {"type": "heading", "text": "Executive Summary"},
  {"type": "paragraph", "text": "[3-4 sentences: purpose, key finding, main recommendation, expected impact]"},
  {"type": "heading", "text": "Background"},
  {"type": "paragraph", "text": "[Context, why this report exists, what prompted the analysis]"},
  {"type": "heading", "text": "Methodology"},
  {"type": "paragraph", "text": "[How the analysis was conducted, data sources, time period, limitations]"},
  {"type": "heading", "text": "Findings"},
  {"type": "paragraph", "text": "[Finding 1 with evidence and data. State the insight clearly.]"},
  {"type": "paragraph", "text": "[Finding 2 with evidence and data.]"},
  {"type": "paragraph", "text": "[Finding 3 with evidence and data.]"},
  {"type": "heading", "text": "Recommendations"},
  {"type": "paragraph", "text": "Based on the findings above, we recommend: 1) [Priority recommendation]. 2) [Secondary recommendation]. 3) [Supporting recommendation]."},
  {"type": "heading", "text": "Conclusion"},
  {"type": "paragraph", "text": "[Summary of key points, restate the most important recommendation, call to action]"}
]
```

### Letter / Formal Communication

```json
[
  {"type": "heading", "text": "[Organization Name]"},
  {"type": "paragraph", "text": "[Date]\n\n[Recipient Name]\n[Recipient Title]\n[Organization]\n[Address]"},
  {"type": "paragraph", "text": "Dear [Recipient],"},
  {"type": "paragraph", "text": "[Opening paragraph: state the purpose of the letter clearly]"},
  {"type": "paragraph", "text": "[Body paragraph 1: main content, details, or argument]"},
  {"type": "paragraph", "text": "[Body paragraph 2: additional details or supporting information]"},
  {"type": "paragraph", "text": "[Closing paragraph: summarize, state next steps, thank the reader]"},
  {"type": "paragraph", "text": "Sincerely,\n\n[Your Name]\n[Your Title]\n[Contact Information]"}
]
```

### Quick Reference / Cheat Sheet

```json
[
  {"type": "heading", "text": "[Topic] Quick Reference"},
  {"type": "paragraph", "text": "This reference covers [scope]. Last updated: [Date]."},
  {"type": "heading", "text": "[Category 1]"},
  {"type": "paragraph", "text": "[Item]: [Definition or instruction]. [Item]: [Definition or instruction]. [Item]: [Definition or instruction]."},
  {"type": "heading", "text": "[Category 2]"},
  {"type": "paragraph", "text": "[Item]: [Definition or instruction]. [Item]: [Definition or instruction]."},
  {"type": "heading", "text": "[Category 3]"},
  {"type": "paragraph", "text": "[Item]: [Definition or instruction]. [Item]: [Definition or instruction]."},
  {"type": "heading", "text": "Additional Resources"},
  {"type": "paragraph", "text": "For more information: [Resource 1]. [Resource 2]. [Resource 3]."}
]
```

## Text Quality for PDF

Since PDF content is static and cannot be edited after generation:
- **Proofread all content** before generating — no fix is possible after creation
- **Front-load key messages** — first sentence of each paragraph carries the weight
- **Use transitional phrases** between sections for reading flow
- **Numbered lists within paragraphs** replace bullet points: "Key points: 1) First. 2) Second. 3) Third."
- **Keep total document length reasonable** — a PDF should accomplish its purpose in the minimum pages necessary
- **Page breaks happen automatically** — structure content so headings don't appear at the very bottom of a page (add a short paragraph before a new section if needed)
