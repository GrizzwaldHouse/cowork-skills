# Color Reference — Ready-to-Use Palettes

## Professional / Corporate
- Primary: `#2563EB` (blue-600)
- Secondary: `#1E40AF` (blue-800)
- Accent: `#F59E0B` (amber-500)
- Neutrals: `#F8FAFC` (slate-50), `#64748B` (slate-500), `#1E293B` (slate-800)
- Success: `#16A34A`, Warning: `#D97706`, Error: `#DC2626`, Info: `#2563EB`
- Best for: Finance, legal, enterprise SaaS, consulting

## Startup / Modern Tech
- Primary: `#8B5CF6` (violet-500)
- Secondary: `#06B6D4` (cyan-500)
- Accent: `#F43F5E` (rose-500)
- Neutrals: `#FAFAFA` (neutral-50), `#737373` (neutral-500), `#171717` (neutral-900)
- Success: `#22C55E`, Warning: `#F59E0B`, Error: `#EF4444`, Info: `#3B82F6`
- Best for: SaaS, developer tools, AI products, social platforms

## Warm / Creative
- Primary: `#EA580C` (orange-600)
- Secondary: `#CA8A04` (yellow-600)
- Accent: `#DC2626` (red-600)
- Neutrals: `#FFFBEB` (amber-50), `#78716C` (stone-500), `#292524` (stone-800)
- Best for: Food, hospitality, entertainment, creative agencies

## Nature / Wellness
- Primary: `#059669` (emerald-600)
- Secondary: `#0D9488` (teal-600)
- Accent: `#D97706` (amber-600)
- Neutrals: `#F0FDF4` (green-50), `#6B7280` (gray-500), `#1F2937` (gray-800)
- Best for: Health, sustainability, outdoor, organic products

## Luxury / Premium
- Primary: `#1E293B` (slate-800)
- Secondary: `#B45309` (amber-700)
- Accent: `#A16207` (yellow-700)
- Neutrals: `#FAFAF9` (stone-50), `#A8A29E` (stone-400), `#0C0A09` (stone-950)
- Best for: Fashion, jewelry, high-end services, premium brands

## Dark Mode Palette
- Surface level 0: `#121212`
- Surface level 1 (cards): `#1E1E1E`
- Surface level 2 (elevated): `#2D2D2D`
- Surface level 3 (popover): `#383838`
- Text primary: `#E0E0E0`, Text secondary: `#A0A0A0`, Text disabled: `#666666`
- Accent: use light-mode accent desaturated 10-15%, increased brightness 10%
- Borders: `#333333` (subtle), `#555555` (prominent)

## Gradient Construction Rules
- **Direction**: 135deg (top-left to bottom-right) is the most natural and modern.
- **Stops**: 2 stops for subtle, 3 stops max for rich gradients. Never more than 3.
- **Hue shift**: Keep stops within 60 degrees on the color wheel for harmonious gradients.
- **Examples**:
  - Ocean: `#2563EB` to `#06B6D4` (blue to cyan, 135deg)
  - Sunset: `#F43F5E` to `#F59E0B` (rose to amber, 135deg)
  - Purple haze: `#8B5CF6` to `#EC4899` (violet to pink, 135deg)
  - Dark premium: `#1E293B` to `#334155` (slate-800 to slate-700, 180deg)

## Data Visualization Colors
- **Categorical** (max 8 distinct hues, ordered by distinguishability):
  `#2563EB`, `#DC2626`, `#16A34A`, `#F59E0B`, `#8B5CF6`, `#06B6D4`, `#EC4899`, `#78716C`
- **Sequential** (single hue, light to dark):
  Blue: `#DBEAFE`, `#93C5FD`, `#3B82F6`, `#1D4ED8`, `#1E3A8A`
  Green: `#DCFCE7`, `#86EFAC`, `#22C55E`, `#15803D`, `#14532D`
- **Diverging** (two hues meeting at neutral):
  Red-Blue: `#DC2626` > `#FCA5A5` > `#F5F5F5` > `#93C5FD` > `#2563EB`
- **Rules**: Avoid red-green pairs (colorblind unfriendly). Always include a legend. Use opacity (0.7-0.8) for overlapping elements.

## Background + Text Pairing Quick Reference
| Background | Text | Contrast | Use |
|------------|------|----------|-----|
| `#FFFFFF` | `#1E293B` | 14.5:1 | Standard light |
| `#F8FAFC` | `#334155` | 9.7:1 | Soft light |
| `#1E293B` | `#F8FAFC` | 14.5:1 | Standard dark |
| `#121212` | `#E0E0E0` | 13.3:1 | True dark mode |
| `#2563EB` | `#FFFFFF` | 4.6:1 | Blue button (AA pass) |
| `#16A34A` | `#FFFFFF` | 3.5:1 | Green button (large text only) |
| `#DC2626` | `#FFFFFF` | 4.6:1 | Red alert (AA pass) |
