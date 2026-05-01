// PhaseCard.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Top-banner card showing "WHAT MARCUS NEEDS TO DO RIGHT NOW"
//          for the currently selected project. Fetches from
//          GET /projects/{id}/phase and refreshes every 10s.
//          Designed to be the first thing Marcus sees — ADHD-friendly,
//          single focused action, large text, high contrast.

import { useCallback, useEffect, useRef, useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PhaseData {
  readonly id: string;
  readonly name: string;
  readonly phase_hint: string | null;
  readonly agent_count: number;
  readonly waiting_count: number;
  readonly skills: readonly string[];
  readonly last_seen: string;
}

interface PhaseCardProps {
  readonly projectId: string | null;
  readonly apiBase?: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REFRESH_MS = 10_000;
const DEFAULT_API = `http://${window.location.hostname}:7842`;

// ---------------------------------------------------------------------------
// Hook: usePhaseData
// ---------------------------------------------------------------------------

function usePhaseData(projectId: string | null, apiBase: string) {
  const [data, setData] = useState<PhaseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    if (!projectId) { setData(null); return; }
    setLoading(true);
    try {
      const resp = await window.fetch(`${apiBase}/projects/${projectId}/phase`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      setData(await resp.json());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [projectId, apiBase]);

  useEffect(() => {
    load();
    timer.current = setInterval(load, REFRESH_MS);
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [load]);

  return { data, loading, error };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PhaseCard({ projectId, apiBase = DEFAULT_API }: PhaseCardProps) {
  const { data, loading, error } = usePhaseData(projectId, apiBase);

  // No project selected — show a neutral prompt.
  if (!projectId) {
    return (
      <div style={cardStyle('#1a1a2e')}>
        <span style={labelStyle}>SELECT A PROJECT</span>
        <div style={actionStyle}>Pick a project from the sidebar to see your next action.</div>
      </div>
    );
  }

  if (loading && !data) {
    return <div style={cardStyle('#1a1a2e')}><span style={labelStyle}>Loading…</span></div>;
  }

  if (error) {
    return (
      <div style={cardStyle('#2a1010')}>
        <span style={labelStyle}>ERROR</span>
        <div style={{ ...actionStyle, color: '#ff6b6b' }}>{error}</div>
      </div>
    );
  }

  const hasWaiting = (data?.waiting_count ?? 0) > 0;
  const bg = hasWaiting ? 'rgba(255,180,0,0.08)' : 'rgba(10,20,40,0.7)';
  const accent = hasWaiting ? '#fbbf24' : 'rgba(120,140,255,0.9)';

  return (
    <div
      style={{
        ...cardStyle(bg),
        borderLeft: `4px solid ${accent}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <span style={{ ...labelStyle, color: accent }}>
          {data?.name ?? '—'}
        </span>
        {hasWaiting && (
          <span
            style={{
              background: '#fbbf24',
              color: '#1a1000',
              fontSize: 10,
              fontWeight: 700,
              borderRadius: 4,
              padding: '2px 7px',
              letterSpacing: '0.08em',
            }}
          >
            ACTION NEEDED
          </span>
        )}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'rgba(160,180,255,0.45)' }}>
          {data?.agent_count ?? 0} agent{data?.agent_count !== 1 ? 's' : ''}
        </span>
      </div>

      <div style={actionStyle}>
        {data?.phase_hint ?? 'No current task. Add one via POST /projects/{id}/phase.'}
      </div>

      {data?.skills && data.skills.length > 0 && (
        <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {data.skills.slice(0, 6).map((s) => (
            <span key={s} style={skillChipStyle}>{s}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles (inline to avoid CSS module coupling in a shared component)
// ---------------------------------------------------------------------------

const cardStyle = (bg: string): React.CSSProperties => ({
  background: bg,
  border: '1px solid rgba(100,120,200,0.18)',
  borderRadius: 10,
  padding: '14px 18px',
  minHeight: 72,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
});

const labelStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: '0.14em',
  color: 'rgba(160,180,255,0.55)',
  textTransform: 'uppercase',
};

const actionStyle: React.CSSProperties = {
  fontSize: 15,
  fontWeight: 600,
  color: 'rgba(220,230,255,0.92)',
  lineHeight: 1.5,
  marginTop: 4,
};

const skillChipStyle: React.CSSProperties = {
  background: 'rgba(100,120,255,0.12)',
  border: '1px solid rgba(100,120,255,0.25)',
  borderRadius: 4,
  padding: '2px 8px',
  fontSize: 10,
  color: 'rgba(160,180,255,0.75)',
};
