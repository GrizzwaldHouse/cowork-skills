// ViewModeToggle.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Top-right toggle between 'grid' and 'brain' view modes.
//          Persists the user's choice to localStorage so a refresh
//          restores the same view. Keeps the option list driven by
//          VIEW_MODES from config.ts so a future third mode does
//          not require touching this file's logic, only its labels.

import { useCallback, type FC } from 'react';
import {
  VIEW_MODE_STORAGE_KEY,
  VIEW_MODES,
  type ViewMode,
} from '@/config';
import './ViewModeToggle.css';

// Human-readable labels for each mode. Kept here rather than in config
// because the labels are UI-only and may localize differently than the
// internal mode literals.
const MODE_LABELS: Record<ViewMode, string> = {
  grid: 'GRID',
  brain: 'BRAIN',
};

interface ViewModeToggleProps {
  // The currently active mode. Owned by the parent so this component
  // is purely presentational; we never own the source of truth.
  readonly mode: ViewMode;

  // Callback fired when the user picks a new mode. The parent is
  // responsible for re-rendering with the new mode value.
  readonly onChange: (next: ViewMode) => void;
}

// Persist a mode choice. Wrapped in a try/catch because localStorage
// can throw in private browsing modes; we never want a write failure
// to break the toggle itself.
function persistMode(mode: ViewMode): void {
  try {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, mode);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('ViewModeToggle: localStorage write failed', err);
  }
}

export const ViewModeToggle: FC<ViewModeToggleProps> = ({
  mode,
  onChange,
}) => {
  // handleClick centralizes the persistence + parent notification so
  // each button's onClick is a one-liner.
  const handleClick = useCallback(
    (next: ViewMode) => () => {
      if (next === mode) {
        // Clicking the active mode is a no-op; saves a re-render and
        // a wasted localStorage write.
        return;
      }
      persistMode(next);
      onChange(next);
    },
    [mode, onChange],
  );

  return (
    <div
      className="view-mode-toggle"
      role="radiogroup"
      aria-label="View mode"
    >
      {VIEW_MODES.map((option) => {
        const isActive = option === mode;
        return (
          <button
            key={option}
            type="button"
            className="view-mode-toggle__option"
            data-active={String(isActive)}
            role="radio"
            aria-checked={isActive}
            onClick={handleClick(option)}
          >
            {MODE_LABELS[option]}
          </button>
        );
      })}
    </div>
  );
};

// Helper exported for the parent so it can compute the initial mode
// from localStorage at mount time. Returns the default when no
// previously-persisted value is present or the value is invalid.
export function readPersistedMode(defaultMode: ViewMode): ViewMode {
  try {
    const raw = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    if (raw !== null && (VIEW_MODES as readonly string[]).includes(raw)) {
      return raw as ViewMode;
    }
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('ViewModeToggle: localStorage read failed', err);
  }
  return defaultMode;
}
