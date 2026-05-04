// SkillCommandPanel.tsx
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: Command-panel controls for dispatching project-local skills into
//          AgenticOS' watched task runtime.

import { useCallback, useEffect, useMemo, useRef, useState, type FC } from 'react';
import { ENDPOINTS } from '@/config';
import type { Project } from '@/components/ProjectSwitcher';
import './SkillCommandPanel.css';

type TaskStatus = 'pending' | 'blocked' | 'in_progress' | 'complete' | 'failed';

interface SkillAction {
  readonly slug: string;
  readonly label: string;
  readonly description: string;
  readonly default_objective: string;
  readonly agent_id: string;
  readonly skill_path: string;
  readonly available: boolean;
}

interface AgenticTask {
  readonly id: string;
  readonly title: string;
  readonly status: TaskStatus;
  readonly assigned_to: string | null;
  readonly priority: number;
  readonly updated_at: string;
  readonly checkpoints: readonly Record<string, unknown>[];
  readonly output: unknown;
}

interface TaskSnapshot {
  readonly timestamp: string;
  readonly tasks: readonly AgenticTask[];
}

interface SkillCommandPanelProps {
  readonly selectedProject: Project | null;
}

const REFRESH_MS = 4_000;
const DEFAULT_OBJECTIVE = 'Use the selected skill to move the AgentForge project forward.';

function statusLabel(status: TaskStatus): string {
  return status.replace('_', ' ').toUpperCase();
}

function checkpointMessage(task: AgenticTask): string {
  const latest = task.checkpoints.at(-1);
  if (!latest) return 'Awaiting first checkpoint';
  const message = latest.message;
  if (typeof message === 'string') return message;
  const kind = latest.kind;
  if (typeof kind === 'string') return kind;
  return 'Checkpoint recorded';
}

function useSkillActions(projectPath: string | null) {
  const [actions, setActions] = useState<readonly SkillAction[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await window.fetch(ENDPOINTS.skillActions(projectPath ?? undefined));
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as SkillAction[];
      setActions(payload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [projectPath]);

  useEffect(() => {
    void load();
  }, [load]);

  return { actions, error, reload: load };
}

function useSkillTasks() {
  const [tasks, setTasks] = useState<readonly AgenticTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await window.fetch(ENDPOINTS.taskSnapshot());
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as TaskSnapshot;
      setTasks(payload.tasks.filter((task) => task.id.startsWith('skill-')));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void load();
    timer.current = setInterval(() => void load(), REFRESH_MS);
    return () => {
      if (timer.current !== null) clearInterval(timer.current);
    };
  }, [load]);

  return { tasks, error, reload: load };
}

export const SkillCommandPanel: FC<SkillCommandPanelProps> = ({ selectedProject }) => {
  const projectPath = selectedProject?.path ?? null;
  const { actions, error: actionsError, reload: reloadActions } = useSkillActions(projectPath);
  const { tasks, error: tasksError, reload: reloadTasks } = useSkillTasks();
  const [objective, setObjective] = useState(DEFAULT_OBJECTIVE);
  const [runningSlug, setRunningSlug] = useState<string | null>(null);
  const [dispatchError, setDispatchError] = useState<string | null>(null);

  const visibleTasks = useMemo(() => tasks.slice(0, 5), [tasks]);

  const runAction = useCallback(
    async (action: SkillAction) => {
      setRunningSlug(action.slug);
      setDispatchError(null);
      try {
        const response = await window.fetch(ENDPOINTS.runSkillAction(action.slug), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            objective,
            project_path: selectedProject?.path,
            project_name: selectedProject?.name,
          }),
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        await reloadTasks();
        await reloadActions();
      } catch (err) {
        setDispatchError(err instanceof Error ? err.message : String(err));
      } finally {
        setRunningSlug(null);
      }
    },
    [objective, reloadActions, reloadTasks, selectedProject?.name, selectedProject?.path]
  );

  return (
    <section className="skill-command-panel" aria-label="Skill command panel">
      <header className="skill-command-panel__header">
        <div>
          <h2 className="skill-command-panel__title tactical-label">SKILL COMMANDS</h2>
          <p className="skill-command-panel__project mono">
            {selectedProject?.name ?? 'ALL PROJECTS'}
          </p>
        </div>
        <span className="skill-command-panel__count mono">{tasks.length} WATCHED</span>
      </header>

      <textarea
        className="skill-command-panel__objective"
        value={objective}
        onChange={(event) => setObjective(event.target.value)}
        rows={2}
        aria-label="Skill task objective"
      />

      <div className="skill-command-panel__actions">
        {actions.map((action) => (
          <button
            key={action.slug}
            className="skill-command-panel__button"
            type="button"
            disabled={runningSlug !== null || !action.available}
            onClick={() => void runAction(action)}
            title={action.skill_path}
          >
            <span className="skill-command-panel__button-label">{action.label}</span>
            <span className="skill-command-panel__button-meta">{action.agent_id}</span>
          </button>
        ))}
      </div>

      {(actionsError || tasksError || dispatchError) && (
        <p className="skill-command-panel__error" role="alert">
          {dispatchError ?? actionsError ?? tasksError}
        </p>
      )}

      <div className="skill-command-panel__watch">
        <div className="skill-command-panel__watch-header">
          <span className="tactical-label">WATCHED SKILL WORK</span>
          <button
            className="skill-command-panel__refresh tactical-label"
            type="button"
            onClick={() => void reloadTasks()}
          >
            REFRESH
          </button>
        </div>

        {visibleTasks.length === 0 ? (
          <p className="skill-command-panel__empty tactical-label">NO SKILL TASKS</p>
        ) : (
          <ul className="skill-command-panel__task-list">
            {visibleTasks.map((task) => (
              <li
                key={task.id}
                className="skill-command-panel__task"
                data-status={task.status}
              >
                <div className="skill-command-panel__task-main">
                  <span className="skill-command-panel__task-title">{task.title}</span>
                  <span className="skill-command-panel__task-note">{checkpointMessage(task)}</span>
                </div>
                <div className="skill-command-panel__task-meta">
                  <span className="mono">{statusLabel(task.status)}</span>
                  <span className="mono">{task.assigned_to ?? 'unassigned'}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
};
