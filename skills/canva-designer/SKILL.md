---
name: canva-designer
description: Canva design generation skill with prompt engineering, format specs, and quality review for logos, presentations, posters, and social media.
user-invocable: true
---

# Canva Designer — Professional Design Generation

Use this skill when generating Canva designs via MCP tools. Apply these principles to every `generate-design`, `request-outline-review`, `generate-design-structured`, and `perform-editing-operations` call.

## Query Engineering for generate-design

The `query` parameter is the most important factor in output quality. Always include:

1. **Style direction**: "minimalist", "bold and modern", "elegant and premium", "playful and colorful"
2. **Color direction**: Specify exact colors or palette mood — "using navy blue (#1E3A5F) with electric blue (#00B4D8) accents"
3. **Layout intent**: "with large hero image top, headline centered below" not just "a poster"
4. **Target audience**: "for C-suite executives" or "for university students" — this changes everything
5. **Text hierarchy**: "large prominent headline, medium subtitle, small supporting details"
6. **Whitespace**: Always include "with generous whitespace and clean layout" — Canva defaults tend to be too busy

**Anti-patterns to avoid**:
- Vague queries: "make a nice poster" — always be specific
- No color guidance: leads to random, incoherent palettes
- Ignoring the audience: a startup pitch deck should feel different from a government report
- See `prompt-patterns.md` for complete query templates by design type.

## Design Type Decision Matrix

| User Need | Canva Tool | design_type | Key Consideration |
|-----------|-----------|-------------|-------------------|
| Logo | `generate-design` | `logo` | Request 4 candidates, evaluate scalability |
| Presentation | `request-outline-review` first | `presentation` | ALWAYS outline review before generation |
| Social media | `generate-design` | platform-specific | Match exact platform dimensions |
| Poster / flyer | `generate-design` | `poster` or `flyer` | Specify physical size and bleed |
| Infographic | `generate-design` | `infographic` | Clear hierarchy, data emphasis |
| Business doc | Prefer cowork-win tools | N/A | Use create_word/create_pdf for structured docs |

## Quality Gates — Before Committing Any Design

Run this mental checklist before calling `commit-editing-transaction`:

1. **Text readable?** — Not overlapping images, sufficient contrast, no cut-off text
2. **No placeholders?** — Zero "Lorem ipsum", "Your text here", or default Canva text
3. **Spelling correct?** — All visible text proofread
4. **Color cohesive?** — Max 3 primary colors + neutrals, consistent throughout
5. **Balance?** — No lopsided visual weight, adequate whitespace (20%+)
6. **Correct dimensions?** — Matches intended platform/use (see `dimensions-reference.md`)
7. **Brand match?** — Consistent with any established brand elements
8. See `quality-checklist.md` for the full detailed checklist.

## Editing Best Practices

When using `perform-editing-operations`:
- **Batch operations** per page to minimize API calls
- **Always use `get-assets`** to inspect existing images before replacing — verify which image is which
- **Preserve existing styles** — when replacing text, maintain the original font/size unless intentionally changing
- **Get thumbnails** of every modified page after operations and show them to the user
- **Never commit** without explicit user approval — always ask first

## Presentation-Specific Rules

When using `request-outline-review` + `generate-design-structured`:
- **topic**: Be specific — "Q4 2025 Revenue Analysis for Board Meeting" not "quarterly update"
- **audience**: Specify role + knowledge — "C-suite executives familiar with SaaS metrics"
- **style**: Match brand — "minimalist" for tech, "elegant" for luxury, "digital" for modern
- **Slide descriptions**: Max 90 characters each, focus on the KEY message
- **length**: "short" (1-5) for executive summaries, "balanced" (5-15) for standard
- One idea per slide. If you need a second idea, add a second slide.
