# PowerPoint Reference — Slide Design for create_powerpoint

## Core Rules

- **6x6 Rule**: Maximum 6 bullet points per slide. Maximum 6 words per bullet.
- **One idea per slide**: If you need a second idea, make a second slide.
- **10-15 slides** for a 20-minute presentation. 5-7 for an executive briefing.
- **Slide titles must be active**: "Revenue Grew 15%" not "Revenue Data". "Customers Prefer Mobile" not "Customer Survey Results".
- **No sentences in bullets**: Use fragments. Start with action verbs. Maintain parallel structure.
- **Data with insight**: Include comparison — "$2.1M, up 15% YoY" not just "$2.1M".

## Layout Selection Guide

The `create_powerpoint` tool supports these layouts:

| Layout | Index | Use For |
|--------|-------|---------|
| `title` | 0 | First slide only — presentation title + subtitle |
| `title_and_content` | 1 | Standard body slides — headline + bullets/text |
| `blank` | 5 | Image-only slides, custom layouts |
| `title_only` | 6 | Section dividers, slides where content is described in text |

### Slide Type Recommendations
- **Slide 1**: Always `"title"` — presentation title, presenter, date
- **Body slides**: `"title_and_content"` — descriptive title + concise content
- **Section dividers**: `"title_only"` — just the section name, clean break
- **Final slide**: `"title_and_content"` — summary/CTA or `"title"` — "Thank You" + contact

## Presentation Templates

### Executive Briefing (5-7 slides)

```json
[
  {"title": "Q4 2025 Business Review", "content": "Presented by [Name]\n[Company] | [Date]", "layout": "title"},
  {"title": "Key Highlights", "content": "Revenue up 15% to $3.1M\nCustomer base grew 22%\nChurn reduced to 2.1%\nNew product launched on schedule", "layout": "title_and_content"},
  {"title": "Revenue Grew 15% Year-over-Year", "content": "Q4 revenue reached $3.1M\nGrowth driven by enterprise segment\nARPU increased 8% through upsells\nPipeline strong entering Q1", "layout": "title_and_content"},
  {"title": "Customer Acquisition Accelerated", "content": "Added 1,200 new customers in Q4\nEnterprise deals up 35%\nSMB self-serve conversion improved 20%\nCAC decreased 12% through organic", "layout": "title_and_content"},
  {"title": "Strategic Priorities for Q1 2026", "content": "Launch v2.0 platform upgrade\nExpand into European market\nHire 15 additional engineers\nAchieve SOC 2 Type II certification", "layout": "title_and_content"},
  {"title": "Decisions Needed", "content": "Approve $500K budget for EU expansion\nSign off on v2.0 launch date: March 15\nApprove hiring plan for engineering", "layout": "title_and_content"}
]
```

### Project Status Update (8-10 slides)

```json
[
  {"title": "[Project Name] Status Update", "content": "Status: On Track\n[Date] | [Project Manager]", "layout": "title"},
  {"title": "Executive Summary", "content": "3 of 5 milestones completed\nOn budget at 62% spend\nTimeline on track for Q1 delivery\nOne risk flagged: API vendor delay", "layout": "title_and_content"},
  {"title": "Milestone Progress", "content": "Discovery: Complete\nDesign: Complete\nDevelopment: Complete\nTesting: In Progress (65%)\nLaunch: Planned March 15", "layout": "title_and_content"},
  {"title": "Key Metrics", "content": "Sprint velocity: 42 points (target 40)\nBug count: 12 open (3 critical)\nTest coverage: 87% (target 90%)\nTeam utilization: 92%", "layout": "title_and_content"},
  {"title": "Development Workstream", "content": "Core API: 100% complete\nFrontend: 90% complete\nIntegrations: 75% complete\nRemaining: payment flow, notifications", "layout": "title_and_content"},
  {"title": "Testing Workstream", "content": "Unit tests: 95% coverage\nIntegration tests: 80% coverage\nUAT: Begins February 15\nPerformance testing: Scheduled Feb 20", "layout": "title_and_content"},
  {"title": "Risks and Mitigations", "content": "API vendor 2-week delay: Using mock service\nKey developer PTO Feb 10-14: Tasks reassigned\nScope creep on notifications: Deferred to v1.1", "layout": "title_and_content"},
  {"title": "Next Two Weeks", "content": "Complete frontend development\nBegin UAT with stakeholders\nFinalize API vendor integration\nPrepare launch readiness review", "layout": "title_and_content"},
  {"title": "Decisions and Support Needed", "content": "Approve deferred scope for v1.1\nConfirm UAT participant list\nSchedule launch go/no-go for March 10", "layout": "title_and_content"}
]
```

### Product/Feature Overview (8-12 slides)

```json
[
  {"title": "[Product Name]", "content": "[Tagline or one-sentence description]\n[Company] | [Date]", "layout": "title"},
  {"title": "The Problem", "content": "[2-3 bullets describing the pain point]", "layout": "title_and_content"},
  {"title": "Our Solution", "content": "[2-3 bullets describing the approach]", "layout": "title_and_content"},
  {"title": "How It Works", "content": "Step 1: [Action]\nStep 2: [Action]\nStep 3: [Action]", "layout": "title_and_content"},
  {"title": "[Feature 1 Name]", "content": "[Description and benefit]", "layout": "title_and_content"},
  {"title": "[Feature 2 Name]", "content": "[Description and benefit]", "layout": "title_and_content"},
  {"title": "[Feature 3 Name]", "content": "[Description and benefit]", "layout": "title_and_content"},
  {"title": "Results and Impact", "content": "[Key metrics and outcomes]", "layout": "title_and_content"},
  {"title": "Get Started", "content": "[CTA, pricing, next steps, contact]", "layout": "title_and_content"}
]
```

## Content Writing Rules for Slides

- **Titles**: 3-6 words. Use active verbs. State the insight, not the topic.
  - Good: "Mobile Usage Surpassed Desktop"
  - Bad: "Mobile vs Desktop Usage Data"
- **Bullets**: Start with action verb. Parallel structure. No periods at end.
  - Good: "Launched 3 new features\nReduced churn by 15%\nExpanded to 5 markets"
  - Bad: "We launched some new features. The churn rate was reduced. We expanded."
- **Numbers**: Always include context — "45,000 users (up 22%)" not just "45,000 users"
- **Every slide answers "So what?"**: State the insight, not just the data
