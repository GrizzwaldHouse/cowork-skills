# Word Reference — Document Templates for create_word

## Business Memo Structure

```json
[
  {"type": "heading", "level": 1, "text": "MEMORANDUM"},
  {"type": "paragraph", "text": "TO: [Recipients]\nFROM: [Sender]\nDATE: [Date]\nRE: [Subject]"},
  {"type": "heading", "level": 2, "text": "Summary"},
  {"type": "paragraph", "text": "[1-2 sentence executive summary of the memo's purpose and key message]"},
  {"type": "heading", "level": 2, "text": "Background"},
  {"type": "paragraph", "text": "[Context and relevant history]"},
  {"type": "heading", "level": 2, "text": "Discussion"},
  {"type": "paragraph", "text": "[Main analysis, findings, or argument]"},
  {"type": "heading", "level": 2, "text": "Recommendation"},
  {"type": "paragraph", "text": "[Clear recommended action with rationale]"},
  {"type": "heading", "level": 2, "text": "Next Steps"},
  {"type": "paragraph", "text": "[Specific actions, owners, and deadlines]"}
]
```

## Business Report Structure

```json
[
  {"type": "heading", "level": 1, "text": "[Report Title]"},
  {"type": "paragraph", "text": "Prepared by [Author] | [Date] | [Organization]"},
  {"type": "heading", "level": 2, "text": "Executive Summary"},
  {"type": "paragraph", "text": "[2-3 sentences: purpose, key finding, recommendation]"},
  {"type": "heading", "level": 2, "text": "Introduction"},
  {"type": "paragraph", "text": "[Background, scope, methodology overview]"},
  {"type": "heading", "level": 2, "text": "Findings"},
  {"type": "heading", "level": 3, "text": "[Finding Area 1]"},
  {"type": "paragraph", "text": "[Analysis and evidence]"},
  {"type": "table", "headers": ["Metric", "Value", "Benchmark", "Status"], "rows": [["...","...","...","..."]]},
  {"type": "heading", "level": 3, "text": "[Finding Area 2]"},
  {"type": "paragraph", "text": "[Analysis and evidence]"},
  {"type": "heading", "level": 2, "text": "Recommendations"},
  {"type": "paragraph", "text": "[Prioritized recommendations with expected impact]"},
  {"type": "heading", "level": 2, "text": "Conclusion"},
  {"type": "paragraph", "text": "[Summary of key points and call to action]"}
]
```

## Proposal Structure

```json
[
  {"type": "heading", "level": 1, "text": "[Proposal Title]"},
  {"type": "paragraph", "text": "Submitted to [Client] by [Company] | [Date]"},
  {"type": "heading", "level": 2, "text": "Executive Summary"},
  {"type": "paragraph", "text": "[Problem + proposed solution + expected outcome in 3-4 sentences]"},
  {"type": "heading", "level": 2, "text": "Problem Statement"},
  {"type": "paragraph", "text": "[Clear description of the challenge and its business impact]"},
  {"type": "heading", "level": 2, "text": "Proposed Solution"},
  {"type": "paragraph", "text": "[How you will solve the problem, key approach, differentiators]"},
  {"type": "heading", "level": 2, "text": "Scope of Work"},
  {"type": "table", "headers": ["Deliverable", "Description", "Timeline"], "rows": [["...","...","..."]]},
  {"type": "heading", "level": 2, "text": "Timeline"},
  {"type": "table", "headers": ["Phase", "Activities", "Start", "End"], "rows": [["...","...","...","..."]]},
  {"type": "heading", "level": 2, "text": "Investment"},
  {"type": "table", "headers": ["Item", "Description", "Cost"], "rows": [["...","...","..."]]},
  {"type": "paragraph", "text": "Total investment: $[amount]"},
  {"type": "heading", "level": 2, "text": "About Us"},
  {"type": "paragraph", "text": "[Company qualifications, relevant experience, team]"},
  {"type": "heading", "level": 2, "text": "Terms & Conditions"},
  {"type": "paragraph", "text": "[Payment terms, validity period, acceptance process]"}
]
```

## Meeting Minutes Structure

```json
[
  {"type": "heading", "level": 1, "text": "Meeting Minutes: [Meeting Name]"},
  {"type": "paragraph", "text": "Date: [Date] | Time: [Time] | Location: [Location]"},
  {"type": "paragraph", "text": "Attendees: [Names]\nAbsent: [Names]"},
  {"type": "heading", "level": 2, "text": "Agenda"},
  {"type": "paragraph", "text": "1. [Item 1]\n2. [Item 2]\n3. [Item 3]"},
  {"type": "heading", "level": 2, "text": "Discussion"},
  {"type": "heading", "level": 3, "text": "[Agenda Item 1]"},
  {"type": "paragraph", "text": "[Key points discussed, decisions made]"},
  {"type": "heading", "level": 2, "text": "Action Items"},
  {"type": "table", "headers": ["Action", "Owner", "Due Date", "Status"], "rows": [["...","...","...","..."]]},
  {"type": "heading", "level": 2, "text": "Next Meeting"},
  {"type": "paragraph", "text": "[Date, time, location, preliminary agenda]"}
]
```

## Text Quality Rules

- **Paragraphs**: 3-5 sentences each. If longer, split into two paragraphs.
- **Sentences**: Vary length (10-30 words). Average 15-25. Never exceed 40 words.
- **Active voice**: Preferred. "We recommend..." not "It is recommended that..."
- **Bullet lists in paragraphs**: Use numbered items: "Key priorities: 1) Revenue growth. 2) Cost reduction. 3) Market expansion."
- **Tables**: Use for comparisons, timelines, and structured data. Always include meaningful headers.
- **Headings**: Active and descriptive. "Revenue Increased 15% in Q4" not "Financial Results"
- **Jargon**: Avoid unless the audience is specialized. Define acronyms on first use.
