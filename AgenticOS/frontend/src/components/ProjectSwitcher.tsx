// ProjectSwitcher.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Left sidebar component that lists all registered AgenticOS projects
//          and lets Marcus switch focus between them. Filters the AgentCard
//          list to show only agents belonging to the selected project.
//          Fetches from GET /projects/active and refreshes every 15s.

import { useCallback, useEffect, useRef, useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Project {
  readonly id: string;
  readonly name: string;
  readonly path: string;
  readonly tech_stack: readonly string[];
  readonly skills: readonly string[];
  readonly last_seen: string;
  readonly is_active: boolean;
  readonly phase_hint: string | null;
  readonly active_session: string | null;
}

interface ProjectSwitcherProps {
  readonly selectedId: string | null;
  readonly onSelect: (id: string | null) => void;
  readonly apiBase?: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REFRESH_INTERVAL_MS = 15_000;
const DEFAULT_API_BASE = `http://${window.location.hostname}:7842`;

// ---------------------------------------------------------------------------
// Hook: useProjects
// ---------------------------------------------------------------------------

function useProjects(apiBase: string): {
  projects: Project[];
  loading: boolean;
  error: string | null;
} {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch = useCallback(async () => {
    try {
      const resp = await window.fetch(`${apiBase}/projects/active`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data: Project[] = await resp.json();
      setProjects(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    fetch();
    timerRef.current = setInterval(fetch, REFRESH_INTERVAL_MS);
    return () => {
      if (timerRef.current !== null) clearInterval(timerRef.current);
    };
  }, [fetch]);

  return { projects, loading, error };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ProjectSwitcher({
  selectedId,
  onSelect,
  apiBase = DEFAULT_API_BASE,
}: ProjectSwitcherProps) {
  const { projects, loading, error } = useProjects(apiBase);

  return (
    <aside
      style={{
        width: 220,
        minHeight: '100vh',
        background: 'rgba(10,10,20,0.92)',
        borderRight: '1px solid rgba(100,120,200,0.18)',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px 0',
        gap: 4,
      }}
    >
      <div
        style={{
          padding: '0 16px 12px',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.12em',
          color: 'rgba(160,180,255,0.6)',
          textTransform: 'uppercase',
          borderBottom: '1px solid rgba(100,120,200,0.12)',
          marginBottom: 8,
        }}
      >
        Projects
      </div>

      {/* All-projects option */}
      <ProjectRow
        id={null}
        name="All Projects"
        isActive={false}
        isSelected={selectedId === null}
        phaseHint={null}
        onSelect={onSelect}
      />

      {loading && (
        <div style={{ padding: '8px 16px', color: 'rgba(160,180,255,0.4)', fontSize: 12 }}>
          Loading…
        </div>
      )}

      {error && (
        <div style={{ padding: '8px 16px', color: '#ff6b6b', fontSize: 11 }}>
          {error}
        </div>
      )}

      {projects.map((p) => (
        <ProjectRow
          key={p.id}
          id={p.id}
          name={p.name}
          isActive={p.is_active}
          isSelected={selectedId === p.id}
          phaseHint={p.phase_hint}
          onSelect={onSelect}
        />
      ))}
    </aside>
  );
}

// ---------------------------------------------------------------------------
// ProjectRow
// ---------------------------------------------------------------------------

interface ProjectRowProps {
  readonly id: string | null;
  readonly name: string;
  readonly isActive: boolean;
  readonly isSelected: boolean;
  readonly phaseHint: string | null;
  readonly onSelect: (id: string | null) => void;
}

function ProjectRow({ id, name, isActive, isSelected, phaseHint, onSelect }: ProjectRowProps) {
  return (
    <button
      onClick={() => onSelect(id)}
      style={{
        background: isSelected ? 'rgba(100,120,255,0.18)' : 'transparent',
        border: 'none',
        borderLeft: isSelected ? '3px solid rgba(120,140,255,0.9)' : '3px solid transparent',
        borderRadius: 0,
        cursor: 'pointer',
        padding: '8px 16px',
        textAlign: 'left',
        width: '100%',
        transition: 'background 0.15s',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: isActive ? '#4ade80' : 'rgba(160,180,255,0.3)',
            flexShrink: 0,
          }}
        />
        <span
          style={{
            color: isSelected ? 'rgba(200,215,255,0.95)' : 'rgba(160,180,255,0.7)',
            fontSize: 13,
            fontWeight: isSelected ? 600 : 400,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {name}
        </span>
      </div>
      {phaseHint && isSelected && (
        <div
          style={{
            marginTop: 4,
            fontSize: 10,
            color: 'rgba(250,200,80,0.8)',
            lineHeight: 1.4,
            paddingLeft: 15,
          }}
        >
          {phaseHint.length > 60 ? phaseHint.slice(0, 57) + '…' : phaseHint}
        </div>
      )}
    </button>
  );
}

// Re-export Project type for consumers.
export type { Project as ProjectRecord };
