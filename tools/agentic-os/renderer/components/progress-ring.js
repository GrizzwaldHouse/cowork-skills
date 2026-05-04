// progress-ring.js / Developer: Marcus Daley / Date: 2026-04-30
// Description: Factory function for an SVG ring progress indicator.
//   Used by render.js renderOverall() to show overall pipeline completion
//   as a circular arc with a gradient stroke and centred percentage label.
//   All geometry is self-contained — no external CSS class dependencies
//   beyond the .progress-ring-wrap container defined in panels.css.

'use strict';

// SVG geometry constants for the progress ring.
// Centralised here so changing the ring size only requires updating these values.

// RING_SIZE — width and height of the SVG viewport in pixels.
// Purpose: Square viewport keeps the centre calculation simple (size/2, size/2).
const RING_SIZE = 80;

// RING_RADIUS — radius of the progress arc circle in SVG user units.
// Purpose: Chosen so the stroke (width 6) fits within the viewport with ~4px margin
//   on each side: (80/2) - 6 = 34. This prevents the arc from being clipped.
const RING_RADIUS = 34;

// RING_CX / RING_CY — centre coordinates of the ring circle.
// Purpose: Always half of RING_SIZE for a centred circle in the square viewport.
const RING_CX = RING_SIZE / 2;
const RING_CY = RING_SIZE / 2;

// RING_STROKE_WIDTH — thickness of both the background track and the progress arc.
const RING_STROKE_WIDTH = 6;

// CIRCUMFERENCE — full perimeter of the progress arc circle.
// Purpose: Used to compute stroke-dasharray and stroke-dashoffset.
//   circumference = 2 * π * radius ≈ 213.628
// Notes: Rounded to 3 decimal places to keep the SVG markup readable.
const CIRCUMFERENCE = parseFloat((2 * Math.PI * RING_RADIUS).toFixed(3));

// progressRing — builds the HTML string for an SVG circular progress indicator.
// Purpose: Produces a self-contained SVG ring that communicates overall pipeline
//   progress at a glance. The arc uses a linear gradient fill (accent → accent2)
//   and rotates -90° so the arc starts at the 12 o'clock position rather than 3
//   o'clock (SVG default). The centre text displays the rounded percentage.
// Params:
//   pct (number) — progress percentage, 0-100.
//     Values outside this range are clamped to [0, 100].
// Returns: string — HTML markup containing a .progress-ring-wrap div wrapping
//   an 80×80 SVG with background circle, progress arc, and centred text.
// Notes:
//   - stroke-dasharray is set to the full circumference so the entire circle
//     is a potential draw area.
//   - stroke-dashoffset = circumference * (1 - pct/100) controls how much
//     of the arc is visible: 0 = full circle, circumference = empty.
//   - The SVG transform="rotate(-90, cx, cy)" on the arc group rotates the
//     start point to 12 o'clock without CSS transform (avoids transform-origin
//     cross-browser inconsistencies in SVG context).
//   - The linearGradient is defined in <defs> with a unique id "ring-gradient".
//     If multiple rings are rendered simultaneously this id would collide —
//     but the dashboard renders exactly one ring, so a static id is safe.
function progressRing(pct) {
  // Clamp input to valid range.
  const safePct = Math.min(100, Math.max(0, Number(pct) || 0));

  // Compute stroke-dashoffset: full offset = empty arc, zero offset = full arc.
  const offset = parseFloat((CIRCUMFERENCE * (1 - safePct / 100)).toFixed(3));

  // Round percentage for the label display.
  const label = Math.round(safePct);

  return `<div class="progress-ring-wrap">
  <svg
    width="${RING_SIZE}"
    height="${RING_SIZE}"
    viewBox="0 0 ${RING_SIZE} ${RING_SIZE}"
    xmlns="http://www.w3.org/2000/svg"
    aria-label="Overall progress: ${label}%"
    role="img"
  >
    <defs>
      <!-- ring-gradient — horizontal linear gradient from accent to accent2.
           Applied to the progress arc stroke to match the dashboard colour palette. -->
      <linearGradient id="ring-gradient" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%"   stop-color="var(--accent)" />
        <stop offset="100%" stop-color="var(--accent2)" />
      </linearGradient>
    </defs>

    <!-- Background track circle — full ring drawn in border colour.
         Provides the grey ring visible behind the progress arc. -->
    <circle
      cx="${RING_CX}"
      cy="${RING_CY}"
      r="${RING_RADIUS}"
      fill="none"
      stroke="var(--border)"
      stroke-width="${RING_STROKE_WIDTH}"
    />

    <!-- Progress arc group — rotated -90° so the arc starts at 12 o'clock.
         SVG transform attribute used (not CSS) for consistent cross-browser behaviour
         in the SVG rendering context. -->
    <g transform="rotate(-90, ${RING_CX}, ${RING_CY})">
      <circle
        cx="${RING_CX}"
        cy="${RING_CY}"
        r="${RING_RADIUS}"
        fill="none"
        stroke="url(#ring-gradient)"
        stroke-width="${RING_STROKE_WIDTH}"
        stroke-dasharray="${CIRCUMFERENCE}"
        stroke-dashoffset="${offset}"
        stroke-linecap="round"
        style="transition: stroke-dashoffset 0.6s ease;"
      />
    </g>

    <!-- Centre percentage label — positioned at the geometric centre of the SVG.
         dominant-baseline and text-anchor centre the text both vertically and
         horizontally without requiring manual offset calculations. -->
    <text
      x="${RING_CX}"
      y="${RING_CY}"
      text-anchor="middle"
      dominant-baseline="central"
      fill="var(--text)"
      font-size="14"
      font-weight="600"
      font-family="var(--font)"
    >${label}%</text>

  </svg>
</div>`;
}

// Export on window so render.js can call window.progressRing() after this script loads.
window.progressRing = progressRing;
