// TerminalStreamPanel.tsx
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Modal panel that opens when an agent is clicked. Connects
//          to GET /agents/{agentId}/stream via EventSource and renders
//          incoming lines into a virtualized scrollback buffer. Caps
//          the buffer at TERMINAL_STREAM_MAX_LINES so a runaway agent
//          cannot exhaust browser memory. Closes on the close button,
//          on Escape, or when the parent unmounts.

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FC,
} from 'react';
import { SSE_ENDPOINTS, TERMINAL_STREAM_MAX_LINES } from '@/config';
import './TerminalStreamPanel.css';

interface TerminalStreamPanelProps {
  // The agent whose stream to tail. Null hides the panel entirely.
  // Using null rather than a separate `open` boolean keeps the panel's
  // open/closed state inseparable from the target -- it can never be
  // open without an agent or open with a stale agent.
  readonly agentId: string | null;

  // Fired when the user closes the panel. Parent should null its
  // tracked agent so this component unmounts.
  readonly onClose: () => void;
}

// Per-line entry. We keep a sequence number so React keys stay stable
// even when the same text repeats (which is common for tool-call loops).
interface StreamLine {
  readonly seq: number;
  readonly text: string;
  readonly isError: boolean;
}

export const TerminalStreamPanel: FC<TerminalStreamPanelProps> = ({
  agentId,
  onClose,
}) => {
  // The scrollback buffer. Capped at TERMINAL_STREAM_MAX_LINES; we
  // shift from the head when overflowing so memory stays bounded
  // regardless of how chatty the agent gets.
  const [lines, setLines] = useState<StreamLine[]>([]);

  // Connection status drives the header label. 'connecting' is the
  // initial state; 'connected' on first message; 'closed' on error or
  // intentional close.
  const [status, setStatus] = useState<'connecting' | 'connected' | 'closed'>('connecting');

  // Monotonic sequence counter for React keys. Stored in a ref so
  // bumping it does not trigger an unrelated re-render.
  const seqRef = useRef<number>(0);

  // The scrollback container; used to auto-scroll to the bottom when
  // new lines arrive. We only auto-scroll when the user is already at
  // the bottom so manual scrollback is not yanked away.
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const stickToBottomRef = useRef<boolean>(true);

  // appendLine bumps the seq, builds an entry, and applies the cap.
  const appendLine = useCallback((text: string, isError = false): void => {
    setLines((prev) => {
      const seq = seqRef.current++;
      const next = prev.concat({ seq, text, isError });
      if (next.length > TERMINAL_STREAM_MAX_LINES) {
        // Drop oldest lines so we are exactly at the cap.
        return next.slice(next.length - TERMINAL_STREAM_MAX_LINES);
      }
      return next;
    });
  }, []);

  // EventSource lifecycle. Re-runs whenever agentId changes (including
  // null -> agent on open). The cleanup closes the connection so we
  // never leak sockets on rapid agent switches.
  useEffect(() => {
    if (agentId === null) {
      // Panel hidden; nothing to do.
      return;
    }

    setLines([]);
    setStatus('connecting');
    seqRef.current = 0;

    const url = SSE_ENDPOINTS.agentStream(agentId);
    const source = new EventSource(url);

    source.onopen = (): void => {
      setStatus('connected');
    };

    source.onmessage = (event: MessageEvent): void => {
      // The server emits one SSE 'data:' frame per file line. EventSource
      // strips the 'data: ' prefix for us; event.data is the raw line.
      if (typeof event.data === 'string') {
        appendLine(event.data, false);
      }
    };

    source.addEventListener('error', (event: Event) => {
      // Could be a transient network blip or a fatal close. The browser's
      // EventSource auto-reconnects on transient errors, so we just
      // surface the state and let it recover.
      const target = event.target as EventSource | null;
      if (target !== null && target.readyState === EventSource.CLOSED) {
        setStatus('closed');
      }
    });

    return () => {
      source.close();
    };
  }, [agentId, appendLine]);

  // Escape-to-close. Bound only while the panel is open to avoid
  // capturing keys when the panel is hidden.
  useEffect(() => {
    if (agentId === null) {
      return;
    }
    const handleKey = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [agentId, onClose]);

  // Auto-scroll to bottom on new lines, but only when the user has not
  // manually scrolled up. We detect that by snapshotting whether the
  // container is at the bottom right before each append.
  useEffect(() => {
    const el = scrollRef.current;
    if (el === null) {
      return;
    }
    if (stickToBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [lines]);

  // Track whether the user is at the bottom. Reading scrollTop here
  // is cheap; we are not running it inside an animation frame so it
  // does not feel like polling.
  const handleScroll = useCallback((): void => {
    const el = scrollRef.current;
    if (el === null) {
      return;
    }
    const distanceFromBottom = el.scrollHeight - el.clientHeight - el.scrollTop;
    stickToBottomRef.current = distanceFromBottom < 24;
  }, []);

  if (agentId === null) {
    return null;
  }

  return (
    <div
      className="terminal-stream-panel"
      role="dialog"
      aria-modal="true"
      aria-label={`Terminal stream for ${agentId}`}
    >
      <div className="terminal-stream-panel__backdrop" onClick={onClose} />
      <div className="terminal-stream-panel__window">
        <header className="terminal-stream-panel__header">
          <span className="terminal-stream-panel__id">{agentId}</span>
          <span
            className="terminal-stream-panel__status"
            data-status={status}
          >
            {status.toUpperCase()}
          </span>
          <button
            type="button"
            className="terminal-stream-panel__close"
            onClick={onClose}
            aria-label="Close terminal stream"
          >
            CLOSE
          </button>
        </header>
        <div
          ref={scrollRef}
          className="terminal-stream-panel__scrollback"
          onScroll={handleScroll}
        >
          {lines.length === 0 ? (
            <p className="terminal-stream-panel__empty">
              Waiting for output...
            </p>
          ) : (
            lines.map((line) => (
              <pre
                key={line.seq}
                className="terminal-stream-panel__line"
                data-error={String(line.isError)}
              >
                {line.text}
              </pre>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
