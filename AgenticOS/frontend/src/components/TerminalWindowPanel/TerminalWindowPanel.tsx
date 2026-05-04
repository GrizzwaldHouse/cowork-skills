// TerminalWindowPanel.tsx
// Developer: Marcus Daley
// Date: 2026-05-01
// Purpose: Operator panel for visible Windows terminal sessions. Lets
//          Marcus focus, gracefully close, or explicitly terminate CLAW,
//          Claude, Codex, and Ollama command windows from AgenticOS.

import { useCallback, useEffect, useMemo, useState, type FC } from 'react';
import {
  ENDPOINTS,
  TERMINAL_PANEL_REFRESH_MS,
  TERMINAL_TERMINATE_CONFIRMATION,
} from '@/config';
import type { TerminalActionResult, TerminalWindow } from '@/types/terminal';
import './TerminalWindowPanel.css';

type TerminalAction = 'focus' | 'close' | 'terminate';

function terminalKey(windowInfo: TerminalWindow): string {
  return `${windowInfo.hwnd}:${windowInfo.pid}`;
}

async function postTerminalAction(
  action: TerminalAction,
  windowInfo: TerminalWindow
): Promise<TerminalActionResult> {
  const url =
    action === 'focus'
      ? ENDPOINTS.terminalFocus(windowInfo.hwnd)
      : action === 'close'
        ? ENDPOINTS.terminalClose(windowInfo.hwnd)
        : ENDPOINTS.terminalTerminate(windowInfo.pid);

  const init: RequestInit = { method: 'POST' };
  if (action === 'terminate') {
    init.headers = { 'Content-Type': 'application/json' };
    init.body = JSON.stringify({ confirm: TERMINAL_TERMINATE_CONFIRMATION });
  }

  const response = await fetch(url, init);

  const payload = (await response.json()) as TerminalActionResult | { detail?: string };
  if (!response.ok) {
    throw new Error('detail' in payload && payload.detail ? payload.detail : response.statusText);
  }
  return payload as TerminalActionResult;
}

export const TerminalWindowPanel: FC = () => {
  const [windows, setWindows] = useState<TerminalWindow[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [agentOnly, setAgentOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const agentWindowCount = useMemo(
    () => windows.filter((windowInfo) => windowInfo.is_agent_like).length,
    [windows]
  );

  const refresh = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const url = `${ENDPOINTS.terminals()}?agent_only=${agentOnly ? 'true' : 'false'}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      const payload = (await response.json()) as TerminalWindow[];
      setWindows(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load terminals');
    } finally {
      setLoading(false);
    }
  }, [agentOnly]);

  useEffect(() => {
    void refresh();
    const intervalId = window.setInterval(() => {
      void refresh();
    }, TERMINAL_PANEL_REFRESH_MS);
    return () => window.clearInterval(intervalId);
  }, [refresh]);

  const runAction = useCallback(
    async (action: TerminalAction, windowInfo: TerminalWindow): Promise<void> => {
      if (
        action === 'terminate' &&
        !window.confirm(`Terminate process ${windowInfo.pid}? This does not save shell state.`)
      ) {
        return;
      }

      const key = terminalKey(windowInfo);
      setBusyKey(key);
      setError(null);
      setMessage(null);
      try {
        const result = await postTerminalAction(action, windowInfo);
        setMessage(result.message);
        await refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : `Unable to ${action} terminal`);
      } finally {
        setBusyKey(null);
      }
    },
    [refresh]
  );

  return (
    <section className="terminal-panel" aria-label="Terminal control">
      <div className="terminal-panel__header">
        <div>
          <h2 className="terminal-panel__title">TERMINAL CONTROL</h2>
          <p className="terminal-panel__meta mono">
            {windows.length} visible / {agentWindowCount} agent-marked
          </p>
        </div>

        <div className="terminal-panel__tools">
          <label className="terminal-panel__toggle tactical-label">
            <input
              type="checkbox"
              checked={agentOnly}
              onChange={(event) => setAgentOnly(event.currentTarget.checked)}
            />
            AGENTS
          </label>
          <button
            type="button"
            className="terminal-panel__button"
            onClick={() => void refresh()}
            disabled={loading}
            title="Refresh terminal list"
          >
            REFRESH
          </button>
        </div>
      </div>

      {error !== null && (
        <p className="terminal-panel__notice terminal-panel__notice--error" role="alert">
          {error}
        </p>
      )}
      {message !== null && (
        <p className="terminal-panel__notice terminal-panel__notice--ok">{message}</p>
      )}

      <div className="terminal-panel__list">
        {windows.length === 0 ? (
          <p className="terminal-panel__empty">
            {loading ? 'Scanning terminal windows...' : 'No visible terminal windows found.'}
          </p>
        ) : (
          windows.map((windowInfo) => {
            const key = terminalKey(windowInfo);
            const isBusy = busyKey === key;
            return (
              <article
                key={key}
                className="terminal-panel__row"
                data-agent-like={String(windowInfo.is_agent_like)}
              >
                <div className="terminal-panel__main">
                  <div className="terminal-panel__row-title" title={windowInfo.title}>
                    {windowInfo.title}
                  </div>
                  <div className="terminal-panel__row-meta mono">
                    PID {windowInfo.pid} / HWND {windowInfo.hwnd} / {windowInfo.process_name}
                  </div>
                  {windowInfo.cwd !== null && (
                    <div className="terminal-panel__cwd mono" title={windowInfo.cwd}>
                      {windowInfo.cwd}
                    </div>
                  )}
                </div>

                <div className="terminal-panel__actions">
                  <button
                    type="button"
                    className="terminal-panel__button"
                    onClick={() => void runAction('focus', windowInfo)}
                    disabled={isBusy}
                    title="Bring this terminal to the foreground"
                  >
                    FOCUS
                  </button>
                  <button
                    type="button"
                    className="terminal-panel__button"
                    onClick={() => void runAction('close', windowInfo)}
                    disabled={isBusy}
                    title="Ask this terminal window to close"
                  >
                    CLOSE
                  </button>
                  <button
                    type="button"
                    className="terminal-panel__button terminal-panel__button--danger"
                    onClick={() => void runAction('terminate', windowInfo)}
                    disabled={isBusy}
                    title="Terminate the owning terminal process"
                  >
                    END
                  </button>
                </div>
              </article>
            );
          })
        )}
      </div>
    </section>
  );
};
