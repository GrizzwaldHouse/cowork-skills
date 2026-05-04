// SonarHUD.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Spline 3D scene wrapper that drives sonar ring and depth gauge
//          animations from live AgentState[] props. Three render paths:
//          (1) WebGL absent           -> SonarFallback (CSS rings)
//          (2) Scene file load error  -> SceneErrorState (friendly card)
//          (3) Normal                 -> Lazy-loaded Spline scene
//          The component is purely event-driven via React's render cycle:
//          a useEffect on the agents prop dispatches syncSplineState; no
//          polling loop, no setInterval anywhere in the chain.

import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useRef,
  useState,
  type FC,
} from 'react';
import type { Application } from '@splinetool/runtime';
import type { AgentState } from '@/types/agent';
import { syncSplineState } from '@/utils/splineSync';
import { hasWebGL2 } from '@/utils/webglDetect';
import { SonarFallback } from './SonarFallback';
import { SceneErrorState } from './SceneErrorState';
import './SonarHUD.css';

// Path to the self-hosted .splinecode file. Public/spline/ is served by
// Vite in dev and by FastAPI's static mount in production; using a root
// path keeps the URL identical in both environments and avoids CORS.
const SPLINE_SCENE_PATH = '/spline/sonar-hud.splinecode' as const;

// Suspense fallback copy. The placeholder renders briefly while the
// @splinetool/runtime chunk downloads; copy is a constant so a future
// localization layer can pick it up without touching the JSX.
const LOADING_LABEL = 'Initializing Sonar' as const;

// Spline scene render mode: renderOnDemand=true tells the runtime to skip
// the per-frame draw loop and only redraw when a variable changes. This is
// critical for a tray-resident app that may run for hours; it drops idle
// CPU and GPU usage to near zero.
const RENDER_ON_DEMAND = true as const;

// Lazy import of the Spline component. The runtime is roughly 1MB; lazy
// loading keeps the initial bundle small and lets the agent grid paint
// before the 3D scene is ready. The dynamic import resolves at build time
// against the package listed in dependencies.
const SplineLazy = lazy(async () => {
  const module = await import('@splinetool/react-spline');
  return { default: module.default };
});

interface SonarHUDProps {
  // The complete list of currently tracked agents. The component renders
  // up to MAX_AGENT_SLOTS of them; the array is treated as readonly to
  // prevent accidental mutation by downstream effect hooks.
  readonly agents: readonly AgentState[];
}

// SonarHUD — top-level wrapper. Owns three pieces of state:
//   webGLAvailable: boolean   computed once at mount, never re-checked
//   sceneError:     string    null until Spline emits onError
//   splineRef:      Application stored on onLoad, read by every sync
export const SonarHUD: FC<SonarHUDProps> = ({ agents }) => {
  // Synchronous WebGL2 capability check. Run via lazy initializer so the
  // canvas probe happens exactly once per component instance, not on every
  // render. The result drives the very first render path decision.
  const [webGLAvailable] = useState<boolean>(() => hasWebGL2());

  // Scene load error state. Populated by handleError; resets on remount.
  // Null means "no error so far"; a string means "error already happened".
  const [sceneError, setSceneError] = useState<string | null>(null);

  // The Spline Application reference, captured by handleLoad. Stored in a
  // ref because it is mutable and never participates in a render decision
  // directly; React state would force unnecessary re-renders.
  const splineRef = useRef<Application | null>(null);

  // Re-sync Spline variables on every agents change. This is the entire
  // event-driven update loop: when WebSocket diffs land, the parent
  // re-renders with new agents, this effect fires, and Spline updates.
  // The guard skips runs before the scene has loaded.
  useEffect(() => {
    if (splineRef.current !== null) {
      syncSplineState(splineRef.current, agents);
    }
  }, [agents]);

  // handleLoad — onLoad callback. Captures the Application ref and
  // immediately writes the current agent state so the scene is correct
  // on its first paint, not one render-cycle behind. agents is intentionally
  // a dependency: if the prop changes between mount and load, we want the
  // initialization sync to use the freshest data, not stale closure data.
  const handleLoad = useCallback(
    (spline: Application): void => {
      splineRef.current = spline;
      syncSplineState(spline, agents);
    },
    [agents]
  );

  // handleError — onError callback. Spline emits this for missing scene
  // files, malformed .splinecode, and runtime instantiation failures.
  // We strip the message string so SceneErrorState can show diagnostic
  // detail without leaking the full Error object into JSX.
  const handleError = useCallback((error: unknown): void => {
    const message =
      error instanceof Error ? error.message : 'Unknown scene load error';
    setSceneError(message);
  }, []);

  // Path 1: WebGL2 unavailable. Render the CSS fallback and never even
  // attempt to load the Spline runtime; this saves a megabyte of bundle
  // download for users on headless or sandboxed environments.
  // suppressSlotIds=true because SonarHUD is embedded inside AgentCard
  // which already renders the agent_id in its header; showing it again
  // inside the fallback slots would create duplicate text nodes.
  if (!webGLAvailable) {
    return <SonarFallback agents={agents} suppressSlotIds={true} />;
  }

  // Path 2: Scene file failed to load. The rest of the app is unaffected
  // because this component is the only Spline consumer.
  if (sceneError !== null) {
    return <SceneErrorState message={sceneError} />;
  }

  // Path 3: Normal. Lazy-loaded Spline component inside Suspense; the
  // Suspense fallback uses the same palette so the transition fades
  // rather than flashes.
  return (
    <div className="sonar-hud">
      <Suspense fallback={<SceneLoadingPlaceholder />}>
        <SplineLazy
          className="sonar-hud__canvas"
          scene={SPLINE_SCENE_PATH}
          onLoad={handleLoad}
          onError={handleError}
          renderOnDemand={RENDER_ON_DEMAND}
        />
      </Suspense>
    </div>
  );
};

// SceneLoadingPlaceholder — animated ring shown while the Spline runtime
// chunk is downloading. Lives inside this file because it is purely a UX
// detail of the SonarHUD load sequence; no other component renders it.
const SceneLoadingPlaceholder: FC = () => {
  return (
    <div className="sonar-hud__loading" aria-label="Loading sonar display">
      <div className="sonar-hud__loading-ring" />
      <span className="sonar-hud__loading-text">{LOADING_LABEL}</span>
    </div>
  );
};
