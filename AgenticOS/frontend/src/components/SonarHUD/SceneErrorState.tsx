// SceneErrorState.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Friendly error card rendered when the Spline scene file fails
//          to load (missing .splinecode, network error, malformed scene).
//          Keeps the rest of the HUD operational and gives the designer a
//          breadcrumb to the expected scene file location.

import type { FC } from 'react';

// Hint path to surface to the designer in the error UI. Centralized so it
// stays in lockstep with SPLINE_SCENE_PATH in SonarHUD.tsx.
const EXPECTED_SCENE_PATH = '/spline/sonar-hud.splinecode' as const;

// Headline shown in the error card. Constant rather than inline literal so
// any localization layer can hook into it later without touching markup.
const ERROR_HEADLINE = 'Scene Load Error' as const;

// Body copy explaining the degraded state. Phrased to reassure the operator
// that approvals and agent tracking still work; only the 3D HUD is affected.
const ERROR_BODY =
  'The 3D sonar display is unavailable. Agent tracking and approval gates remain fully functional.';

// Designer-facing hint, rendered smaller. Tells whoever is configuring the
// scene where to drop the .splinecode file produced in the Spline editor.
const DESIGNER_HINT_PREFIX = 'Designers: drop sonar-hud.splinecode at';

interface SceneErrorStateProps {
  // Optional underlying error message for diagnostic visibility. Kept on
  // the surface (not just in the console) because this app runs as a
  // single-user tray app and there is no telemetry pipeline to inspect.
  readonly message?: string;
}

// SceneErrorState — pure presentational component. role="alert" so screen
// readers announce the degraded state when the scene first fails.
export const SceneErrorState: FC<SceneErrorStateProps> = ({ message }) => {
  return (
    <div className="sonar-hud__error" role="alert">
      <span className="sonar-hud__error-code">{ERROR_HEADLINE}</span>
      <span className="sonar-hud__error-message">{ERROR_BODY}</span>
      <span className="sonar-hud__error-hint">
        {DESIGNER_HINT_PREFIX} <code>{EXPECTED_SCENE_PATH}</code>
      </span>
      {message !== undefined && message.length > 0 && (
        <span className="sonar-hud__error-detail" aria-label="Error detail">
          {message}
        </span>
      )}
    </div>
  );
};
