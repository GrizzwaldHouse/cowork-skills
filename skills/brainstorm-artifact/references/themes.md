# Themes Reference

Themes live in a `THEMES` constant in the artifact. Each theme is a complete token package. Themes never cross-pollinate, adding a new theme is a pure addition.

## Theme token list

Every theme defines these tokens:

```js
{
  // palette
  bgBase: "#0a0e0a",          // outermost background
  bgSurface: "#141a14",       // cards, panels
  bgRaised: "#1f2820",        // raised elements (selected pills, modals)
  accent: "#8a6d3b",          // primary brand accent
  accentBright: "#c9a96e",    // hover and active states
  textPrimary: "#e8e0c8",     // body text
  textMuted: "#9aa093",       // secondary text, rationale
  border: "#2a3528",          // dividers, pill borders
  success: "#5a8a5a",         // achievement unlocks, completed sections
  warning: "#c9a96e",         // feedback flag button
  danger: "#a85a4a",          // destructive actions, errors
  sectionColors: ["#5a8a5a", "#8a6d3b", "#6d8a8a", "#a85a4a"], // used to differentiate sections in the wizard

  // typography
  fontDisplay: "'Playfair Display', serif",  // headers, section titles
  fontBody: "'Playfair Display', serif",     // body text
  fontMono: "'JetBrains Mono', monospace",   // code, IDs, timestamps

  // identity
  iconChar: "◆",              // shown in title bar
  rankNames: [                 // 7 rank tiers, used in gamification
    "Recruit",
    "Petty Officer 3rd Class",
    "Petty Officer 2nd Class",
    "Petty Officer 1st Class",
    "Chief Petty Officer",
    "Senior Chief Petty Officer",
    "Master Chief"
  ]
}
```

## Three shipping themes

### vetassist_tactical

Dark military palette. Deep forest greens, weathered bronze, parchment text on dark backgrounds. Playfair Display + JetBrains Mono. Navy enlisted ranks. Diamond icon.

Use for: VetAssist work, government/compliance projects, military or veteran-services projects, anything where a serious tone matters.

### game_dev_arcade

Neon retro palette. Deep purple background, hot pink accent, electric mint and yellow highlights. Press Start 2P + JetBrains Mono. Game development ranks (Pixel through Game Director). Triangle icon.

Use for: Agent Forge work, gameplay loop scoping, engine work, pixel art related artifacts. Loudest of the three themes, use only when project domain genuinely matches.

### research_editorial

Parchment academic palette. Cream background, deep brown accent, forest green and ochre highlights. Playfair Display + Georgia + JetBrains Mono. Academic ranks (Reader through Laureate). Bookmark icon.

Use for: research projects, writing work, regulatory analysis, anything text-heavy that reads well in a parchment aesthetic. Most subdued theme.

## Adding a project-specific theme

Pattern:

1. Pick a project name as the theme key. Use snake_case. Example: `agent_forge_neon`.
2. Define palette by picking three to five anchor colors that fit the project's domain. Restrained intensity is preferred (Marcus's stated UI preference).
3. Pick fonts. One display font for headers, one body font, one mono font. The Press Start 2P + JetBrains Mono pairing is the loudest option, the Playfair + Georgia pairing is the most subdued.
4. Define seven rank names that fit the project's metaphor system. Examples: military ranks, game dev ranks, academic ranks, sports ranks, climbing grades.
5. Pick an icon character that visually represents the project.
6. Add the theme as a new entry in the THEMES constant. Do not modify existing themes.
7. Set `metadata.themeKey` to the new theme's key when generating artifacts for that project.

## Calibration: what restrained looks like

Marcus prefers themes that feel native to the project but do not overpower the content. Indicators of an overpowering theme:

- More than three colors competing for attention in any single view
- Pure saturated colors (#FF0000 red, #00FF00 green) without earthy or muted undertones
- Display fonts used for body text (Press Start 2P body text is unreadable for long questions)
- Animated or gradient backgrounds during answer entry

Indicators of a well-calibrated theme:

- Two anchor colors plus accents
- Earthy, weathered, or muted intensity even on bright themes
- Display font reserved for headers, body uses a readable serif or sans-serif
- Static backgrounds, animation reserved for state changes (selection lock, achievement unlock)
