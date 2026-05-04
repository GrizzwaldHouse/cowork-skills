// SubagentActivityPanel.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Live read-only view of every spawned sub-agent's current activity,
//          grouped under their parent mission. Shows stage label, progress,
//          status pill, and context usage at a glance. Renders nothing when
//          no sub-agents are present.

import type { FC } from 'react';
import type { AgentState } from '@/types/agent';
import { StatusPill } from '@/components/StatusPill/StatusPill';
import { ProgressBar } from '@/components/ProgressBar/ProgressBar';
import { formatDomainLabel, formatTimestamp } from '@/utils/formatters';
import { CONTEXT_WARN_PCT, CONTEXT_CRIT_PCT } from '@/config';
import './SubagentActivityPanel.css';

interface SubagentActivityPanelProps {
  // Full flat list of all agents currently known to the state bus.
  // The panel derives the parent/child tree from spawned_by links.
  readonly agents: readonly AgentState[];
}

// resolveContextLevel maps a context percentage to a severity token
// used as a data attribute so CSS can drive the color without JS hex.
function resolveContextLevel(pct: number): 'ok' | 'warn' | 'crit' {
  if (pct >= CONTEXT_CRIT_PCT) return 'crit';
  if (pct >= CONTEXT_WARN_PCT) return 'warn';
  return 'ok';
}

// buildActivityTree groups all sub-agents (spawned_by !== null) under their
// parent agent_id. Top-level agents (spawned_by === null/undefined) that have
// at least one child are included as section headers.
function buildActivityTree(
  agents: readonly AgentState[]
): Map<string, AgentState[]> {
  const tree = new Map<string, AgentState[]>();

  for (const agent of agents) {
    const parentId = agent.spawned_by;
    if (parentId === null || parentId === undefined) continue;

    if (!tree.has(parentId)) tree.set(parentId, []);
    // Non-null assertion safe: we just set it if absent.
    tree.get(parentId)!.push(agent);
  }

  return tree;
}

// SubagentRow renders one spawned sub-agent as a compact activity row.
const SubagentRow: FC<{ agent: AgentState }> = ({ agent }) => {
  const contextLevel = resolveContextLevel(agent.context_pct_used);
  const updatedAt = formatTimestamp(agent.updated_at);
  const domain = formatDomainLabel(agent.domain);

  return (
    <li
      className="subagent-row"
      data-status={agent.status}
      aria-label={`Sub-agent ${agent.agent_id}`}
    >
      {/* Left column: identity + stage label */}
      <div className="subagent-row__identity">
        <span className="subagent-row__id mono">{agent.agent_id}</span>
        <span className="subagent-row__domain tactical-label">[{domain}]</span>
        <span className="subagent-row__stage-label">{agent.stage_label}</span>
      </div>

      {/* Center column: progress bar + stage fraction */}
      <div className="subagent-row__progress">
        <ProgressBar
          value={agent.progress_pct}
          label={`Stage ${agent.stage}/${agent.total_stages}`}
          ariaLabel={`Progress for sub-agent ${agent.agent_id}`}
        />
      </div>

      {/* Right column: status pill + context meter + timestamp */}
      <div className="subagent-row__meta">
        <StatusPill status={agent.status} />
        <span
          className="subagent-row__context mono"
          data-level={contextLevel}
          aria-label={`Context used: ${agent.context_pct_used}%`}
        >
          CTX {agent.context_pct_used}%
        </span>
        <span className="subagent-row__updated mono">{updatedAt}</span>
      </div>

      {/* Error message inline — only when status is error */}
      {agent.status === 'error' && agent.error_msg !== null && (
        <p className="subagent-row__error" role="alert">
          {agent.error_msg}
        </p>
      )}
    </li>
  );
};

// MissionSection renders one parent agent's header and all its sub-agents.
const MissionSection: FC<{
  parentId: string;
  parentAgent: AgentState | undefined;
  children: readonly AgentState[];
}> = ({ parentId, parentAgent, children }) => (
  <section
    className="subagent-section"
    aria-labelledby={`mission-header-${parentId}`}
  >
    <header className="subagent-section__header">
      <span
        className="subagent-section__parent-id mono"
        id={`mission-header-${parentId}`}
      >
        {parentId}
      </span>
      {/* Show the parent's current task as a subtitle if we have it */}
      {parentAgent !== undefined && (
        <span className="subagent-section__parent-task">
          {parentAgent.task}
        </span>
      )}
      <span className="subagent-section__count tactical-label">
        {children.length} SUB-AGENT{children.length !== 1 ? 'S' : ''}
      </span>
    </header>

    <ul className="subagent-section__list" role="list">
      {children.map((agent) => (
        <SubagentRow key={agent.agent_id} agent={agent} />
      ))}
    </ul>
  </section>
);

// SubagentActivityPanel is the exported panel. Renders an empty state when
// no sub-agents exist; otherwise renders one MissionSection per parent.
export const SubagentActivityPanel: FC<SubagentActivityPanelProps> = ({
  agents,
}) => {
  const tree = buildActivityTree(agents);

  // Nothing spawned yet — render a quiet empty state, not an error.
  if (tree.size === 0) {
    return (
      <aside className="subagent-panel subagent-panel--empty" aria-label="Sub-agent activity">
        <p className="subagent-panel__empty-msg tactical-label">
          NO SUB-AGENTS ACTIVE
        </p>
      </aside>
    );
  }

  // Build an index of all agents by id for parent lookups.
  const agentIndex = new Map<string, AgentState>(
    agents.map((a) => [a.agent_id, a])
  );

  return (
    <aside className="subagent-panel" aria-label="Sub-agent activity">
      <h2 className="subagent-panel__title tactical-label">
        SUB-AGENT ACTIVITY
      </h2>

      {/* Render one section per unique parent, sorted by parent id */}
      {[...tree.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([parentId, children]) => (
          <MissionSection
            key={parentId}
            parentId={parentId}
            parentAgent={agentIndex.get(parentId)}
            children={children}
          />
        ))}
    </aside>
  );
};
