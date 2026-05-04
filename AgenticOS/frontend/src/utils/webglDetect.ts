// webglDetect.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Synchronous WebGL2 capability probe used by the SonarHUD before it
//          attempts to instantiate the Spline scene. A pure helper with no
//          side effects beyond ephemeral canvas creation; the canvas is
//          eligible for GC the moment this function returns.

// Context identifier requested from the canvas. WebGL2 is required by the
// Spline runtime for the lighting model used in the submarine HUD; falling
// back to webgl1 would render the scene incorrectly, so we treat its absence
// as "WebGL unavailable" and route to the CSS fallback.
const REQUIRED_CONTEXT_TYPE = 'webgl2' as const;

// hasWebGL2 — returns true when the host environment can produce a WebGL2
// rendering context. Wrapped in try/catch because some sandboxed iframes,
// remote-desktop sessions, and headless test runners throw rather than
// returning null from getContext.
export function hasWebGL2(): boolean {
  // Guard: this module is imported by SSR-style tooling occasionally; if
  // document is missing there is no DOM to test against, and the caller
  // must use the fallback path.
  if (typeof document === 'undefined') {
    return false;
  }

  try {
    // Build an off-DOM canvas. It is never appended, so it does not affect
    // layout and is collected as soon as the local reference falls away.
    const probe = document.createElement('canvas');
    const context = probe.getContext(REQUIRED_CONTEXT_TYPE);
    // Some drivers return a context object that is immediately lost; we
    // treat any non-null context as success because Spline performs its
    // own deeper validation when the scene is instantiated.
    return context !== null;
  } catch {
    // getContext can throw SecurityError in restricted iframes; swallow it
    // here because the caller only needs a boolean signal.
    return false;
  }
}
