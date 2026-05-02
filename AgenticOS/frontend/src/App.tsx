// App.tsx
// Developer: Marcus Daley
// Date: 2026-04-30
// Purpose: Root component for the AgenticOS Command Center. Owns the
//          WebSocket connection (via useFilteredAgents), the approval
//          POST hook (via useApproval), project selection state that
//          feeds ProjectSwitcher, and hash-based routing so /guide
//          renders the AIArchGuide without a full router dependency.

import { useCallback, useEffect, useState, type FC } from 'react';
import { useFilteredAgents } from '@/hooks/useAgentState';
import { useApproval } from '@/hooks/useApproval';
import { AgentCard } from '@/components/AgentCard/AgentCard';
import { NeuralBrainView } from '@/components/NeuralBrainView/NeuralBrainView';
import { ViewModeToggle, readPersistedMode } from '@/components/ViewModeToggle/ViewModeToggle';
import { TerminalStreamPanel } from '@/components/TerminalStreamPanel/TerminalStreamPanel';
import { ProjectSwitcher, type Project } from '@/components/ProjectSwitcher';
import { PhaseCard } from '@/components/PhaseCard';
import AIArchGuide from '@/components/AIArchGuide';
import { TerminalWindowPanel } from '@/components/TerminalWindowPanel/TerminalWindowPanel';
import { SkillCommandPanel } from '@/components/SkillCommandPanel/SkillCommandPanel';
import { WorkflowStatusPanel } from '@/components/WorkflowStatusPanel/WorkflowStatusPanel';
import { DEFAULT_VIEW_MODE, MAX_AGENT_SLOTS, type ViewMode } from '@/config';
import type { ApprovalKind } from '@/types/agent';
import './App.css';

// ---------------------------------------------------------------------------
// Hash routing — avoids adding react-router for a single alternate view.
// The /guide hash toggles the AI Architecture Field Guide full-screen.
// ---------------------------------------------------------------------------

type AppRoute = 'hub' | 'guide';

function useHashRoute(): [AppRoute, (r: AppRoute) => void] {
  const [route, setRouteState] = useState<AppRoute>(() =>
    window.location.hash === '#guide' ? 'guide' : 'hub'
  );

  useEffect(() => {
    const handler = (): void => {
      setRouteState(window.location.hash === '#guide' ? 'guide' : 'hub');
    };
    window.addEventListener('hashchange', handler);
    return () => window.removeEventListener('hashchange', handler);
  }, []);

  const setRoute = useCallback((r: AppRoute): void => {
    window.location.hash = r === 'guide' ? 'guide' : '';
    setRouteState(r);
  }, []);

  return [route, setRoute];
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

const App: FC = () => {
  const [route, setRoute] = useHashRoute();

  // Project selection — null means "all projects".
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Filtered agent list: narrows to the selected project's path when set.
  const { agents, connected, error: wsError, lastSeq } = useFilteredAgents(
    selectedProject?.path ?? null
  );

  const { loading, error: postErrors, approve } = useApproval();

  const [viewMode, setViewMode] = useState<ViewMode>(
    () => readPersistedMode(DEFAULT_VIEW_MODE)
  );

  const [streamingAgentId, setStreamingAgentId] = useState<string | null>(null);

  const handleApprove = (agentId: string, decision: ApprovalKind): void => {
    void approve(agentId, decision);
  };

  const handleOpenStream = useCallback((agentId: string): void => {
    setStreamingAgentId(agentId);
  }, []);

  const handleCloseStream = useCallback((): void => {
    setStreamingAgentId(null);
  }, []);

  // ProjectSwitcher gives us the full Project object; we store it so
  // PhaseCard can receive the id and the filtered-agents hook gets the path.
  const handleProjectSelect = useCallback((id: string | null, projects: Project[]): void => {
    setSelectedProject(id === null ? null : (projects.find((p) => p.id === id) ?? null));
  }, []);

  // AIArchGuide renders full-screen; skip the rest of the shell.
  if (route === 'guide') {
    return (
      <>
        <button
          onClick={() => setRoute('hub')}
          style={{
            position: 'fixed',
            top: 12,
            right: 16,
            zIndex: 9999,
            background: 'rgba(10,8,5,0.85)',
            border: '1px solid rgba(200,121,65,0.5)',
            borderRadius: 6,
            color: '#c87941',
            fontFamily: 'inherit',
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '0.1em',
            padding: '5px 12px',
            cursor: 'pointer',
          }}
        >
          ← HUB
        </button>
        <AIArchGuide />
      </>
    );
  }

  const visibleAgents = agents.slice(0, MAX_AGENT_SLOTS);
  const truncated = agents.length > MAX_AGENT_SLOTS;

  return (
    <div className="app">
      {/* ---- Header bar ---- */}
      <header className="app__header">
        <h1 className="app__title">AGENTIC OS // COMMAND CENTER</h1>

        <div className="app__header-right" aria-live="polite">
          <button
            className="app__guide-link tactical-label"
            onClick={() => setRoute('guide')}
            aria-label="Open AI Architecture Field Guide"
          >
            AI GUIDE
          </button>
          <ViewModeToggle mode={viewMode} onChange={setViewMode} />
          <span
            className="app__connection-dot"
            aria-hidden="true"
            data-connected={String(connected)}
          />
          <span className="app__connection-label tactical-label">
            {connected ? 'CONNECTED' : 'CONNECTING'}
          </span>
          {lastSeq !== null && (
            <span className="app__sequence mono" aria-label="Last sequence">
              SEQ {lastSeq}
            </span>
          )}
        </div>
      </header>

      {wsError !== null && (
        <div className="app__ws-error" role="alert">
          {wsError}
        </div>
      )}

      {/* ---- Body: sidebar + main content ---- */}
      <div className="app__body">
        {/* Left sidebar: project list */}
        {/* onSelectWithProjects is the authoritative handler — it resolves
            the full Project object from the fetched list. onSelect is
            required by the prop interface but does nothing here because
            every click goes through onSelectWithProjects. */}
        <ProjectSwitcher
          selectedId={selectedProject?.id ?? null}
          onSelect={() => { /* handled by onSelectWithProjects */ }}
          onSelectWithProjects={handleProjectSelect}
        />

        {/* Right: phase banner + agent grid/brain */}
        <div className="app__content">
          <TerminalWindowPanel />

          {/* ADHD-friendly "what to do right now" banner */}
          <PhaseCard projectId={selectedProject?.id ?? null} />

          <SkillCommandPanel selectedProject={selectedProject} />

          <WorkflowStatusPanel />

          {viewMode === 'brain' ? (
            <main className="app__brain" aria-label="Neural brain view">
              <NeuralBrainView
                agents={visibleAgents}
                onNodeClick={handleOpenStream}
              />
            </main>
          ) : (
            <main className="app__grid" aria-label="Active agents">
              {visibleAgents.length === 0 ? (
                <p className="app__empty-state">
                  No agents active. Cards appear here as soon as a task runs.
                </p>
              ) : (
                visibleAgents.map((agent) => (
                  <AgentCard
                    key={agent.agent_id}
                    agent={agent}
                    isLoading={loading[agent.agent_id] ?? false}
                    postError={postErrors[agent.agent_id] ?? null}
                    onApprove={handleApprove}
                  />
                ))
              )}
              {truncated && (
                <p className="app__truncated-note">
                  Showing first {MAX_AGENT_SLOTS} of {agents.length} agents.
                </p>
              )}
            </main>
          )}
        </div>
      </div>

      {/* ---- Footer status bar ---- */}
      <footer className="app__status-bar">
        <span className="tactical-label">AGENTIC OS</span>
        <span className="mono">
          {visibleAgents.length} of {agents.length} tracked
          {selectedProject !== null && ` · ${selectedProject.name}`}
        </span>
      </footer>

      <TerminalStreamPanel
        agentId={streamingAgentId}
        onClose={handleCloseStream}
      />
    </div>
  );
};

export default App;
