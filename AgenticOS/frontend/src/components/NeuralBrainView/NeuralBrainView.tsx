// NeuralBrainView.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Spline-backed 3D neural-brain visualization. The Spline scene
//          renders behind a d3-force-positioned SVG overlay; each agent
//          becomes a node and parent/child task lineage produces edges.
//          Click on a node fires the parent's onNodeClick callback so
//          TerminalStreamPanel can open with the correct agent. Falls
//          back to a 2D SVG-only graph if Spline fails to load.
//
// Why d3-force: a static layout collapses to overlapping nodes the
// moment you have more than three agents in the same status. The
// force simulation gives every node a comfortable orbit around the
// center, with related nodes pulled together by their edge force.

import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FC,
} from 'react';
import {
  forceCenter,
  forceLink,
  forceManyBody,
  forceSimulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force';
import type { AgentState } from '@/types/agent';
import {
  BRAIN_CANVAS_HEIGHT_PX,
  BRAIN_CANVAS_WIDTH_PX,
  BRAIN_NODE_COLORS,
  BRAIN_SPLINE_SCENE_PATH,
  FORCE_CENTER_X_RATIO,
  FORCE_CENTER_Y_RATIO,
  FORCE_CHARGE_STRENGTH,
  FORCE_LINK_DISTANCE_PX,
  FORCE_RADIUS_PX,
} from '@/config';
import './NeuralBrainView.css';

// Lazy-load the Spline runtime so the bundle size cost is paid only
// when the user toggles into brain mode. Mirrors the SonarHUD pattern
// so the two scenes share the same loading characteristics.
const SplineLazy = lazy(async () => {
  const moduleImport = await import('@splinetool/react-spline');
  return { default: moduleImport.default };
});

// Visual styling constants. Kept here rather than in config.ts because
// they are layout-internal: the d3 simulation reads them, the SVG
// renderer reads them, nothing else does.
const NODE_STROKE_WIDTH_PX = 2 as const;
const EDGE_STROKE_WIDTH_PX = 1.25 as const;
const NODE_LABEL_OFFSET_PX = 4 as const;

// Force simulation alpha decay. Lower = the simulation runs longer
// before settling. 0.05 is the d3 default and produces a satisfying
// "drift then stop" feel without spinning forever.
const SIMULATION_ALPHA_DECAY = 0.05 as const;

// d3-force expects nodes that allow mutable x/y. We extend our read-only
// AgentState with the simulation-managed positions in a private type so
// the upstream AgentState shape stays untouched.
interface BrainNode extends SimulationNodeDatum {
  // Original agent reference; never mutated by the simulation. The
  // simulation only writes x, y, vx, vy onto this object.
  readonly agent: AgentState;

  // Stable id used as the d3 link source/target.
  readonly id: string;
}

// Edge type. Source and target are agent_ids; d3 will resolve them
// against the node id field for us.
interface BrainLink extends SimulationLinkDatum<BrainNode> {
  readonly source: string;
  readonly target: string;
}

interface NeuralBrainViewProps {
  // The complete list of currently tracked agents. Drives node count
  // and edge derivation.
  readonly agents: ReadonlyArray<AgentState>;

  // Callback invoked when a node is clicked. The parent uses this to
  // open the TerminalStreamPanel for the selected agent.
  readonly onNodeClick: (agentId: string) => void;
}

export const NeuralBrainView: FC<NeuralBrainViewProps> = ({
  agents,
  onNodeClick,
}) => {
  // Track Spline load failure so we can render the 2D-only fallback.
  // Initialized to false; flipped true on the lazy module's onError.
  const [splineFailed, setSplineFailed] = useState<boolean>(false);

  // Node and link arrays maintained by the d3 simulation. We keep them
  // in state so React re-renders the SVG on every tick. The simulation
  // mutates the node objects in place, so we deliberately store the
  // same array reference and trigger a render via a tick counter.
  const [tick, setTick] = useState<number>(0);

  // The simulation instance. Created on mount, restarted whenever the
  // agents list changes shape. Stored in a ref because it is mutable
  // and never triggers a render directly.
  const simRef = useRef<ReturnType<typeof forceSimulation<BrainNode, BrainLink>> | null>(null);

  // Build the node + edge graph once per agents update. Memoized so
  // unrelated re-renders do not throw away simulation state.
  const { nodes, links } = useMemo(() => {
    const buildNodes: BrainNode[] = agents.map((agent) => ({
      agent,
      id: agent.agent_id,
      // Seed positions roughly at center so the first frame is not
      // a chaotic explosion. d3 will spread them out within a few ticks.
      x: BRAIN_CANVAS_WIDTH_PX * FORCE_CENTER_X_RATIO,
      y: BRAIN_CANVAS_HEIGHT_PX * FORCE_CENTER_Y_RATIO,
    }));

    // Edges come from spawned_by: a child references its parent by id.
    // Only emit an edge when the parent is also in the active set; a
    // dangling reference would crash d3-force's link resolver.
    const ids = new Set(buildNodes.map((n) => n.id));
    const buildLinks: BrainLink[] = [];
    for (const agent of agents) {
      if (agent.spawned_by !== null && ids.has(agent.spawned_by)) {
        buildLinks.push({
          source: agent.spawned_by,
          target: agent.agent_id,
        });
      }
    }
    return { nodes: buildNodes, links: buildLinks };
  }, [agents]);

  // (Re)build the simulation whenever the graph shape changes. We do
  // not run it on a setInterval; d3-force's internal tick loop is the
  // event source, and we hook into its 'tick' event to re-render.
  useEffect(() => {
    // Stop any previous simulation before swapping it out so two
    // simulations never animate the same nodes.
    if (simRef.current !== null) {
      simRef.current.stop();
    }

    if (nodes.length === 0) {
      // Nothing to simulate. Bump tick once so the SVG renders empty.
      setTick((t) => t + 1);
      return;
    }

    const simulation = forceSimulation<BrainNode>(nodes)
      .force(
        'link',
        forceLink<BrainNode, BrainLink>(links)
          .id((d) => d.id)
          .distance(FORCE_LINK_DISTANCE_PX),
      )
      .force('charge', forceManyBody().strength(FORCE_CHARGE_STRENGTH))
      .force(
        'center',
        forceCenter(
          BRAIN_CANVAS_WIDTH_PX * FORCE_CENTER_X_RATIO,
          BRAIN_CANVAS_HEIGHT_PX * FORCE_CENTER_Y_RATIO,
        ),
      )
      .alphaDecay(SIMULATION_ALPHA_DECAY)
      .on('tick', () => {
        // Force a render. The nodes array is mutated by d3 in place,
        // so React will not see a new reference -- using the tick
        // counter as a render trigger is the simplest reliable path.
        setTick((t) => t + 1);
      });

    simRef.current = simulation;

    return () => {
      simulation.stop();
    };
  }, [nodes, links]);

  // Compute the color for a node from its status flags. Stuck and
  // looping take priority over the base status: those are the cases
  // Marcus needs to spot first.
  const colorForAgent = useCallback((agent: AgentState): string => {
    if (agent.is_stuck) {
      return BRAIN_NODE_COLORS.stuck;
    }
    if (agent.is_looping) {
      return BRAIN_NODE_COLORS.looping;
    }
    return BRAIN_NODE_COLORS[agent.status] ?? BRAIN_NODE_COLORS.active;
  }, []);

  // Click handler -- invoked on both circle and label so the entire
  // node is a hit target. Stops propagation so the underlying Spline
  // canvas does not also receive the click event.
  const handleNodeClick = useCallback(
    (agentId: string) => (event: React.MouseEvent): void => {
      event.stopPropagation();
      onNodeClick(agentId);
    },
    [onNodeClick],
  );

  // Spline error handler -- flip splineFailed so the next render
  // path falls through to the SVG-only mode. Logged so a debugger
  // session has a breadcrumb.
  const handleSplineError = useCallback((err: unknown): void => {
    // eslint-disable-next-line no-console
    console.warn('NeuralBrainView: Spline scene failed; falling back to 2D', err);
    setSplineFailed(true);
  }, []);

  // The SVG overlay. Identical between the Spline-backed and
  // fallback paths so styling is consistent.
  const overlay = (
    <svg
      className="neural-brain__svg"
      viewBox={`0 0 ${BRAIN_CANVAS_WIDTH_PX} ${BRAIN_CANVAS_HEIGHT_PX}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Neural brain agent graph"
      data-tick={tick}
    >
      {/* Edges first so circles render on top. */}
      <g className="neural-brain__edges">
        {links.map((link, idx) => {
          // d3 mutates source/target into BrainNode references after
          // the first tick; before that they are still strings. We
          // accept either by reading x/y defensively.
          const src = typeof link.source === 'object' ? link.source : null;
          const tgt = typeof link.target === 'object' ? link.target : null;
          if (src === null || tgt === null) {
            return null;
          }
          return (
            <line
              key={`edge-${idx}-${(src as BrainNode).id}-${(tgt as BrainNode).id}`}
              x1={(src as BrainNode).x ?? 0}
              y1={(src as BrainNode).y ?? 0}
              x2={(tgt as BrainNode).x ?? 0}
              y2={(tgt as BrainNode).y ?? 0}
              stroke="rgba(201, 169, 78, 0.45)"
              strokeWidth={EDGE_STROKE_WIDTH_PX}
            />
          );
        })}
      </g>

      <g className="neural-brain__nodes">
        {nodes.map((node) => {
          const color = colorForAgent(node.agent);
          const isPulsing = node.agent.is_stuck === true;
          return (
            <g
              key={node.id}
              className="neural-brain__node"
              data-pulsing={String(isPulsing)}
              transform={`translate(${node.x ?? 0}, ${node.y ?? 0})`}
              onClick={handleNodeClick(node.agent.agent_id)}
              role="button"
              tabIndex={0}
              aria-label={`Agent ${node.agent.agent_id}`}
            >
              <circle
                r={FORCE_RADIUS_PX}
                fill={color}
                stroke="rgba(0, 0, 0, 0.6)"
                strokeWidth={NODE_STROKE_WIDTH_PX}
              />
              <text
                className="neural-brain__node-label"
                y={FORCE_RADIUS_PX + NODE_LABEL_OFFSET_PX + 12}
                textAnchor="middle"
                fill="#e8e6e1"
                fontSize="11"
              >
                {node.agent.agent_id}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );

  // Render path 1: Spline failed -> 2D-only fallback. The overlay is
  // rendered above a static gradient backdrop instead of the 3D scene.
  if (splineFailed) {
    return (
      <div className="neural-brain neural-brain--fallback" aria-busy="false">
        <div className="neural-brain__fallback-bg" aria-hidden="true" />
        {overlay}
      </div>
    );
  }

  // Render path 2: Spline scene + overlay.
  return (
    <div className="neural-brain" aria-busy="false">
      <Suspense
        fallback={
          <div className="neural-brain__loading" aria-hidden="true">
            Initializing neural brain...
          </div>
        }
      >
        <SplineLazy
          className="neural-brain__scene"
          scene={BRAIN_SPLINE_SCENE_PATH}
          onError={handleSplineError}
          renderOnDemand
        />
      </Suspense>
      {overlay}
    </div>
  );
};
