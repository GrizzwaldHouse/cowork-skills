# AgenticOS Dashboard Assets

Developer: Marcus Daley
Date: 2026-04-29
Purpose: Designer-facing reference for every binary asset the WPF
launcher loads at runtime. Each entry below lists the expected file
name, format, dimensions, palette references, and the conversion path
from the source artwork to the runtime asset.

The dashboard tolerates every asset being absent: missing files
fall back to plain text or to a transparent placeholder so the
application still boots while the asset pipeline is in progress.

## Tray Icon

- File on disk: `tray-icon.ico`
- Format: Windows multi-resolution ICO containing 16x16, 32x32, and
  48x48 frames. Windows 11 picks 32x32 by default but the smaller
  frames keep the icon legible on classic small taskbars.
- Palette references (`AgenticOS/dashboard/agentic_dashboard.xaml`):
  - GoldAccentBrush #C9A94E (submarine silhouette fill)
  - BorderGoldBrush  #8B7435 (hull outline, periscope strut)
  - DeepNavyBrush    #1B2838 (transparent background; do not bake the
    navy into the ICO -- the tray host already supplies the back colour)
- Style: flat silhouette of a Hogwarts-meets-Ohio-class submarine,
  no gradients, no soft shadows. The 16x16 frame must remain readable
  at the standard tray density on a high-DPI display.
- Conversion pipeline:
  1. Author the source as `tray-icon.svg` next to this README.
  2. Export 16, 32, and 48 px PNG frames using Inkscape or Figma.
  3. Combine with `magick` (ImageMagick) into a multi-frame ICO:
     `magick convert tray-icon-16.png tray-icon-32.png tray-icon-48.png tray-icon.ico`
  4. Drop the resulting `tray-icon.ico` in this folder, replacing the
     placeholder text file shipped in source control.

## Window Icon (future)

- File on disk: `window-icon.ico`
- Same palette and conversion path as the tray icon.
- Unused today; reserved so we can promote the WPF window from a
  plain DragMove chrome to a fully decorated taskbar entry without a
  schema change to `agentic_dashboard.xaml`.

## Sound Cues (future)

- Folder: `sounds/`
- Format: 16-bit PCM WAV at 44.1 kHz, mono.
- Files:
  - `sonar-ping.wav` (server transitions to running)
  - `klaxon.wav` (supervisor crashed state)
- Reserved for the SonarHUD integration in Plan 3. Not yet wired.

## Why a placeholder file?

Source control is clearer when every referenced runtime asset has a
deterministic path even before the binary is produced. The tray-icon
placeholder is a plain text file so a `git diff` immediately shows
when the designer drops in the real binary. The launcher tolerates a
non-image file and falls back to no glyph gracefully.
