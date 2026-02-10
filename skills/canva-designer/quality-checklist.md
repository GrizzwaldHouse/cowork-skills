# Quality Checklist — Pre-Commit Design Review

Run through this checklist before calling `commit-editing-transaction` on any Canva design.

## Text Quality
- [ ] All text is readable — not overlapping images, backgrounds, or other elements
- [ ] No placeholder text remains ("Lorem ipsum", "Your text here", "Title", "Subtitle")
- [ ] Spelling and grammar are correct in all visible text
- [ ] Text contrast meets WCAG AA: 4.5:1 for body text, 3:1 for large text (18px+)
- [ ] Maximum 3 font families used in the entire design
- [ ] Text hierarchy is clear — viewer instantly knows what to read first
- [ ] No text is cut off at edges or hidden behind elements
- [ ] All-caps text has increased letter spacing (if applicable)

## Visual Balance
- [ ] Layout feels balanced — no side is visually "heavier" than the other
- [ ] Consistent spacing between similar elements (margins, padding, gaps)
- [ ] Images are high quality — not pixelated, stretched, or distorted
- [ ] Color palette is cohesive — maximum 3 primary colors plus neutrals
- [ ] Adequate whitespace — at least 20% of canvas is breathing room
- [ ] Visual hierarchy guides the eye: most important element is dominant
- [ ] Alignment is consistent — elements on a clear grid, not randomly placed
- [ ] No orphaned elements floating with unclear relationship to other content

## Technical Specs
- [ ] Design dimensions match intended platform/use (check dimensions-reference.md)
- [ ] Important content is within safe zones (not in platform overlay areas)
- [ ] Logo/brand elements are correctly positioned with adequate clear space
- [ ] All required information is present (dates, URLs, CTAs, credits as needed)
- [ ] No critical content within 3mm of edges (for print designs with bleed)

## Presentation-Specific
- [ ] Slide count matches the approved outline
- [ ] One main idea per slide — no information overload
- [ ] Consistent visual style across ALL slides (colors, fonts, spacing)
- [ ] Title slide includes: presentation title, presenter/company, date
- [ ] Final slide has clear CTA, summary, or "Thank You" with contact info
- [ ] 6x6 rule followed: max 6 bullets per slide, max 6 words per bullet
- [ ] Slide titles are active and descriptive ("Revenue Grew 15%" not "Revenue Data")

## Logo-Specific
- [ ] Logo works at small size (32px) — still recognizable
- [ ] Logo works on both light and dark backgrounds
- [ ] Logo has adequate clear space around it
- [ ] If combination mark: icon and text are balanced
- [ ] Color version AND monochrome version both work

## Before Export
- [ ] Export format matches intended use:
  - PNG: web, social media, digital display
  - JPG: photos, large images (with acceptable quality loss)
  - PDF: print, professional documents
  - PPTX: editable presentations
  - SVG: logos, icons (if available)
- [ ] Resolution is appropriate: 72 DPI for screen, 300 DPI for print
- [ ] File size is reasonable for intended distribution method

## Final Approval
- [ ] Show the user a thumbnail of every modified page
- [ ] Explicitly ask "Would you like me to save these changes to your design?"
- [ ] Wait for clear user approval before committing
