// WorkflowStatusPanel.tsx
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: Read-only HUD panel showing live status for autonomous-workflow
//          skill runs. Self-hides when no events exist. One section per
//          workflow_id with phase segment bar and vote badges.

import type { FC } from 'react';
import { useWorkflowEvents } from '@/hooks/useWorkflowEvents';
import type { PhaseRecord, WorkflowGroup, WorkflowTerminalStatus } from '@/types/workflow';
import './WorkflowStatusPanel.css';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function phaseState(phase: PhaseRecord): string {
  if (phase.voteResult === 'PASS') return 'voted-pass';
  if (phase.voteResult === 'FAIL' || phase.voteResult === 'BLOCKED') return 'voted-fail';
  if (phase.complete) return 'complete';
  if (phase.started) return 'active';
  return 'pending';
}

function formatTimestamp(iso: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return iso;
  }
}

function pillLabel(status: WorkflowTerminalStatus): string {
  if (status === 'complete') return 'COMPLETE';
  if (status === 'failed') return 'FAILED';
  return 'RUNNING';
}

// ---------------------------------------------------------------------------
// WorkflowSection — one workflow run
// ---------------------------------------------------------------------------

const WorkflowSection: FC<{ group: WorkflowGroup }> = ({ group }) => (
  <section
    className="workflow-section"
    aria-label={`Workflow ${group.workflowId}`}
  >
    <header className="workflow-section__header">
      <span className="workflow-section__id mono">
        {group.workflowId.slice(0, 8)}
      </span>
      {group.task !== null && (
        <span className="workflow-section__task" title={group.task}>
          {group.task}
        </span>
      )}
      <span
        className="workflow-pill tactical-label"
        data-status={group.terminalStatus}
        aria-label={`Status: ${pillLabel(group.terminalStatus)}`}
      >
        {pillLabel(group.terminalStatus)}
      </span>
    </header>

    <div className="workflow-phases" role="list" aria-label="Phase progress">
      {group.phases.map((phase) => {
        const state = phaseState(phase);
        return (
          <div
            key={phase.name}
            className="workflow-phase"
            data-state={state}
            role="listitem"
            aria-label={`${phase.name}: ${state}`}
          >
            <span>{phase.name.slice(0, 4).toUpperCase()}</span>
            {phase.voteResult !== null && (
              <span
                className="vote-badge"
                data-result={phase.voteResult}
                aria-label={`Vote: ${phase.voteResult}`}
              >
                {phase.voteResult}
              </span>
            )}
          </div>
        );
      })}
    </div>

    {group.failureReason !== null && (
      <p className="workflow-panel__error" role="alert">
        {group.failureReason}
      </p>
    )}

    <div className="workflow-section__meta">
      <span>Started {formatTimestamp(group.startedAt)}</span>
      <span>Updated {formatTimestamp(group.updatedAt)}</span>
    </div>
  </section>
);

// ---------------------------------------------------------------------------
// WorkflowStatusPanel
// ---------------------------------------------------------------------------

export const WorkflowStatusPanel: FC = () => {
  const { workflowGroups, error } = useWorkflowEvents();

  if (workflowGroups.size === 0 && error === null) {
    return (
      <aside className="workflow-panel workflow-panel--empty" aria-label="Workflow status">
        <h2 className="workflow-panel__title">WORKFLOW STATUS</h2>
        <p className="workflow-panel__empty-msg tactical-label">NO WORKFLOWS ACTIVE</p>
      </aside>
    );
  }

  return (
    <aside className="workflow-panel" aria-label="Workflow status">
      <h2 className="workflow-panel__title">WORKFLOW STATUS</h2>

      {error !== null && (
        <p className="workflow-panel__error" role="alert">{error}</p>
      )}

      {[...workflowGroups.values()].map((group) => (
        <WorkflowSection key={group.workflowId} group={group} />
      ))}
    </aside>
  );
};
