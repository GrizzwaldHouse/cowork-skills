---
name: design-system
description: Design principles for visual output — color theory, typography, layout, accessibility. Auto-loaded for any design, Canva, or document task.
user-invocable: false
---

# Design System — Foundational Principles

Apply these principles whenever creating visual designs (Canva), documents (Excel, Word, PowerPoint, PDF), or advising on design decisions.

## Color Theory

- **Contrast**: WCAG AA minimum 4.5:1 for body text, 3:1 for large text (18px+ or 14px bold). Target AAA (7:1) when possible.
- **60-30-10 Rule**: 60% dominant/neutral color, 30% secondary color, 10% accent. Never use more than 3 primary colors plus neutrals.
- **Avoid pure extremes**: Use off-black (#1E293B or #171717) instead of #000000. Use off-white (#F8FAFC or #FAFAFA) instead of #FFFFFF.
- **Semantic meaning**: Blue = trust/corporate, Green = growth/success, Red = urgency/error, Orange = energy/warning, Purple = premium/creative, Yellow = optimism/caution.
- **Colorblind safety**: Never rely on color alone to convey meaning. Pair color with icons, labels, or patterns.
- See `color-reference.md` for ready-to-use palettes.

## Typography

- **Maximum 2 typefaces** per design (heading + body). Only add a 3rd if it serves a distinct decorative purpose.
- **Type scale**: Use ratio 1.25 (major third) or 1.333 (perfect fourth). From 16px base: H1=32-43px, H2=25-34px, H3=20-26px, body=16px, caption=13px.
- **Minimum sizes**: 16px body on screen, 10pt body in print. Never go below 12px for any readable text.
- **Line height**: 1.4-1.6x for body text, 1.1-1.2x for headings.
- **Line length**: 45-75 characters per line for optimal readability.
- **Weight contrast**: Minimum 2 weight steps between heading and body (e.g., 700 heading, 400 body).
- **All-caps**: Increase letter-spacing by 2-5%. Use sparingly — only for short labels, never body text.
- See `typography-reference.md` for proven font pairings.

## Layout

- **Visual hierarchy**: Size > Color > Contrast > Position > Shape. Lead the eye to the most important element first.
- **Whitespace**: Minimum 20-30% of total canvas should be breathing room. When in doubt, add more space.
- **Alignment**: Use a consistent system. Left-align body text (most readable for LTR languages). Center-align only for short headings or hero text.
- **Proximity**: Related items 8-16px apart. Unrelated groups separated by 24-48px minimum. Sections by 48-96px.
- **Grid**: 8px base unit for all spacing. 12-column grid for complex layouts, 4-column for simple/mobile.
- **Composition**: Rule of thirds for image/focal point placement. F-pattern for text-heavy pages. Z-pattern for landing pages and posters.
- **Golden ratio** (1:1.618): Use for content area proportions, image cropping, and section sizing.
- See `layout-reference.md` for grid templates and spacing scale.

## Brand Consistency

- Consistent corner radius throughout (0px=corporate, 4-8px=modern, 12-16px=friendly).
- Icon style must be uniform: filled OR outlined OR duotone — never mix within one design.
- Logo clear space: minimum 1x the logo mark height on all sides.
- Maintain the same color palette, type pairing, and spacing system across all deliverables in a project.

## Accessibility Checklist

- All text meets WCAG AA contrast (4.5:1 body, 3:1 large).
- Color is not the sole indicator of meaning.
- Text is actual text (not baked into images) when possible.
- Tables have header rows. Documents have logical heading hierarchy (H1 > H2 > H3, no skipping).
- Font size is never below 12px/10pt for any readable content.
