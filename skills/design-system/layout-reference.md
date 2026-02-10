# Layout Reference — Grids, Spacing & Composition

## 8px Base Spacing Scale
| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Tight inline spacing, icon gaps |
| sm | 8px | Compact element spacing |
| md | 16px | Default element spacing |
| lg | 24px | Section inner padding |
| xl | 32px | Card padding, form groups |
| 2xl | 48px | Section separation |
| 3xl | 64px | Major section breaks |
| 4xl | 96px | Page section dividers |

**Rule**: All spacing values should be multiples of 8px. The only exception is 4px for tight micro-spacing.

## 12-Column Grid Specifications

### Breakpoints
| Name | Width | Columns | Gutter | Margin |
|------|-------|---------|--------|--------|
| Mobile | <640px | 4 | 16px | 16px |
| Tablet | 640-1024px | 8 | 24px | 40px |
| Desktop | 1024-1440px | 12 | 24px | 80px |
| Wide | >1440px | 12 | 32px | auto (max 1280px content) |

### Column Spans
| Columns | Width | Common Use |
|---------|-------|-----------|
| 2 of 12 | 16.67% | Sidebar icon rail |
| 3 of 12 | 25% | Sidebar, card in 4-col grid |
| 4 of 12 | 33.33% | Card in 3-col grid, sidebar |
| 6 of 12 | 50% | Half-width content, two-column |
| 8 of 12 | 66.67% | Main content area (with sidebar) |
| 9 of 12 | 75% | Main content (narrow sidebar) |
| 12 of 12 | 100% | Full-width hero, single column |

## Common Layout Patterns

### Hero Section
- Full-width background (color or image)
- Centered text block: H1 + subtitle + CTA button
- Height: 60-80vh on desktop, 50-60vh on mobile
- Text over image: add dark overlay (rgba(0,0,0,0.4-0.6)) for readability

### Card Grid
- 3 or 4 columns on desktop, 2 on tablet, 1 on mobile
- Gap: 16-24px between cards
- Equal height cards (use flexbox/grid alignment)
- Card padding: 24-32px internal
- Card corner radius: match brand system (4-16px)

### Two-Column Content
- Ratio: 60/40 or 2:1 (content/sidebar)
- Image + text pattern: image on one side, text on the other
- Alternate sides every section for visual rhythm
- Gap between columns: 32-48px

### Sidebar Layout
- Sidebar: 240-300px fixed width (or 25% of container)
- Main content: remaining width
- Sidebar items: 8-12px vertical spacing
- Active item: background color change, left border accent

### Dashboard Layout
- Top bar: 56-64px height, full width
- Left sidebar: 240-280px, collapsible to 64px (icon-only)
- Main area: fluid, with 24-32px padding
- Cards/widgets: 16-24px gap grid

## Composition Rules

### Rule of Thirds
Divide canvas into 3x3 grid. Place key elements at intersection points.
- Logo/brand mark: top-left intersection
- Primary CTA: bottom-right intersection
- Hero image focal point: along a vertical third line

### F-Pattern (Text-Heavy Pages)
1. Eyes scan horizontally across the top (headline)
2. Drop down, scan shorter horizontal line (subheading)
3. Vertical scan down the left side (bullet starts, bold text)
- Place most important content top-left
- Use bold/color to create "scan points" along the left edge

### Z-Pattern (Landing Pages / Posters)
1. Top-left: Logo/brand
2. Top-right: Navigation/CTA
3. Center: Hero content (diagonal scan)
4. Bottom-left: Supporting info
5. Bottom-right: Primary CTA
- Works best with minimal text, strong visual elements

### Golden Ratio Proportions
- Content width to sidebar: 1.618:1 (e.g., 800px content, 494px sidebar)
- Image aspect ratios: 1:1.618, 1.618:1
- Section height proportions: larger section is 1.618x the smaller
- When choosing between two sizes, multiply or divide by 1.618

## Print-Specific Layout
- **Bleed**: 3mm (0.125in) on all sides beyond trim line
- **Safe zone**: Keep important content 6mm (0.25in) inside trim line
- **Resolution**: 300 DPI minimum for all print output
- **Color mode**: CMYK for professional print (note: Canva handles conversion)
- **Margins**: Minimum 12.7mm (0.5in) for bound documents, 19mm (0.75in) for presentation handouts
