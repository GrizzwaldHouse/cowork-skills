// MobileApproval.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Large-button approval UI optimised for iPhone screen dimensions.
//          Shows the waiting agent, its task, and three full-width decision
//          buttons (Approve / Research / Review). Designed so Marcus can
//          approve agents in two taps with no scrolling required on a 6"
//          phone screen. Calls the existing POST /approve|research|review
//          endpoints on the AgenticOS state bus.

import { useState } from 'react';
import type { AgentState } from '@/types/agent';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MobileApprovalProps {
  readonly agent: AgentState;
  readonly apiBase?: string;
  readonly onDecision?: (agentId: string, decision: string) => void;
}

type Decision = 'proceed' | 'research' | 'review';
type ActionState = 'idle' | 'loading' | 'done' | 'error';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_API = `http://${window.location.hostname}:7842`;

const ENDPOINT_MAP: Record<Decision, string> = {
  proceed: 'approve',
  research: 'research',
  review: 'review',
};

const BUTTON_CONFIG: Array<{
  decision: Decision;
  label: string;
  description: string;
  color: string;
  activeColor: string;
}> = [
  {
    decision: 'proceed',
    label: '✓ Approve',
    description: 'Resume normal execution',
    color: 'rgba(74,222,128,0.15)',
    activeColor: 'rgba(74,222,128,0.35)',
  },
  {
    decision: 'research',
    label: '🔍 Research More',
    description: 'Spawn a research sub-agent first',
    color: 'rgba(251,191,36,0.12)',
    activeColor: 'rgba(251,191,36,0.30)',
  },
  {
    decision: 'review',
    label: '📋 Review',
    description: 'Spawn an independent reviewer',
    color: 'rgba(99,102,241,0.15)',
    activeColor: 'rgba(99,102,241,0.35)',
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function MobileApproval({ agent, apiBase = DEFAULT_API, onDecision }: MobileApprovalProps) {
  const [actionState, setActionState] = useState<ActionState>('idle');
  const [activeDecision, setActiveDecision] = useState<Decision | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleDecision(decision: Decision) {
    setActionState('loading');
    setActiveDecision(decision);
    setErrorMsg(null);

    const endpoint = ENDPOINT_MAP[decision];
    try {
      const resp = await window.fetch(`${apiBase}/${endpoint}/${agent.agent_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
      });
      if (!resp.ok) {
        const detail = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${detail}`);
      }
      setActionState('done');
      onDecision?.(agent.agent_id, decision);
    } catch (err) {
      setActionState('error');
      setErrorMsg(err instanceof Error ? err.message : String(err));
      setActiveDecision(null);
    }
  }

  if (actionState === 'done') {
    return (
      <div style={containerStyle}>
        <div
          style={{
            textAlign: 'center',
            padding: '24px 16px',
            color: '#4ade80',
            fontSize: 16,
            fontWeight: 600,
          }}
        >
          ✓ Decision recorded for {agent.agent_id}
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      {/* Agent summary */}
      <div style={summaryStyle}>
        <div style={{ fontSize: 11, color: 'rgba(160,180,255,0.55)', marginBottom: 4, fontWeight: 700, letterSpacing: '0.1em' }}>
          WAITING FOR APPROVAL
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'rgba(220,230,255,0.92)', lineHeight: 1.4 }}>
          {agent.agent_id}
        </div>
        <div style={{ fontSize: 12, color: 'rgba(160,180,255,0.7)', marginTop: 4, lineHeight: 1.4 }}>
          {agent.task.length > 100 ? agent.task.slice(0, 97) + '…' : agent.task}
        </div>
        {agent.stage_label && (
          <div style={{ fontSize: 11, color: 'rgba(160,180,255,0.45)', marginTop: 6 }}>
            Stage {agent.stage}/{agent.total_stages}: {agent.stage_label}
          </div>
        )}
      </div>

      {/* Error message */}
      {actionState === 'error' && errorMsg && (
        <div style={{ background: 'rgba(255,80,80,0.12)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 12, fontSize: 12, color: '#ff6b6b' }}>
          {errorMsg}
        </div>
      )}

      {/* Decision buttons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {BUTTON_CONFIG.map(({ decision, label, description, color, activeColor }) => {
          const isActive = activeDecision === decision && actionState === 'loading';
          return (
            <button
              key={decision}
              onClick={() => handleDecision(decision)}
              disabled={actionState === 'loading'}
              style={{
                background: isActive ? activeColor : color,
                border: `1px solid ${isActive ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)'}`,
                borderRadius: 12,
                padding: '16px 20px',
                cursor: actionState === 'loading' ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                width: '100%',
                opacity: actionState === 'loading' && !isActive ? 0.5 : 1,
                transition: 'all 0.15s',
                fontFamily: 'inherit',
              }}
            >
              <div style={{ fontSize: 16, fontWeight: 700, color: 'rgba(220,230,255,0.95)', marginBottom: 3 }}>
                {isActive ? '…' : label}
              </div>
              <div style={{ fontSize: 12, color: 'rgba(160,180,255,0.65)' }}>
                {description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const containerStyle: React.CSSProperties = {
  background: 'rgba(10,12,28,0.95)',
  border: '1px solid rgba(100,120,200,0.2)',
  borderRadius: 16,
  padding: '16px',
  maxWidth: 420,
  width: '100%',
  margin: '0 auto',
};

const summaryStyle: React.CSSProperties = {
  background: 'rgba(30,35,70,0.6)',
  border: '1px solid rgba(100,120,200,0.15)',
  borderRadius: 10,
  padding: '12px 14px',
  marginBottom: 16,
};
