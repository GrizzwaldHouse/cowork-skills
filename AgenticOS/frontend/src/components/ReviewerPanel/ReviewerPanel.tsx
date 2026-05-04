// ReviewerPanel.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Expandable panel that reveals the reviewer agent verdict once
//          the reviewer subprocess writes one. Hidden entirely when the
//          parent agent has no reviewer_verdict; auto-expands the first
//          time a verdict appears so the user notices the new content.

import { useEffect, useState, type FC } from 'react';
import './ReviewerPanel.css';

interface ReviewerPanelProps {
  // Verdict text written by the reviewer agent. Null until a reviewer
  // has produced a verdict; when null the panel is invisible.
  readonly verdict: string | null;
}

// The verdict body uses <pre> with white-space: pre-wrap so the
// reviewer's structured PASS / REVISE / REJECT formatting survives.
export const ReviewerPanel: FC<ReviewerPanelProps> = ({ verdict }) => {
  // Track open/closed state. The initial value is false; the effect
  // below opens the panel exactly once when a verdict arrives.
  const [isOpen, setIsOpen] = useState<boolean>(false);

  // Auto-open on the first non-null verdict. We do not collapse on a
  // verdict change; the user can manually toggle if they want.
  useEffect(() => {
    if (verdict !== null) {
      setIsOpen(true);
    }
  }, [verdict]);

  // No verdict yet means nothing to show. Returning null keeps the
  // card layout flush with no extra spacing.
  if (verdict === null) {
    return null;
  }

  return (
    <section className="reviewer-panel">
      <button
        type="button"
        className="reviewer-panel__toggle tactical-label"
        aria-expanded={isOpen}
        aria-controls="reviewer-panel__body"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span>REVIEWER VERDICT</span>
        <span
          className="reviewer-panel__chevron"
          aria-hidden="true"
          data-open={isOpen}
        >
          {/* Down chevron rotates 180 degrees via CSS when open. */}
          v
        </span>
      </button>

      {isOpen && (
        <div
          id="reviewer-panel__body"
          className="reviewer-panel__body"
          role="region"
          aria-label="Reviewer verdict content"
        >
          <pre className="reviewer-panel__text">{verdict}</pre>
        </div>
      )}
    </section>
  );
};
