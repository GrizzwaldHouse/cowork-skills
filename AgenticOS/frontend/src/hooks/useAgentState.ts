// useAgentState.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Owns the WebSocket connection to the FastAPI state bus, parses
//          SnapshotMessage and DiffMessage frames, folds them into an
//          immutable agent map, and reconnects with exponential backoff.
//          Returns the current map plus connection metadata so the UI
//          can show a live connection indicator without polling.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { AgentState } from '@/types/agent';
import {
  WS_RECONNECT_BASE_MS,
  WS_RECONNECT_MAX_MS,
  WS_URL,
} from '@/config';
import {
  isDiffMessage,
  isSnapshotMessage,
} from '@/types/messages';
import {
  agentMapToArray,
  applyDiff,
  applySnapshot,
  type AgentMap,
} from '@/utils/diffMerge';

// ---------------------------------------------------------------------------
// UseAgentStateReturn
//
// We surface both a Map (for O(1) by-id lookup) and a sorted array (for
// .map rendering). Components prefer the array; tests prefer the Map.
// ---------------------------------------------------------------------------

export interface UseAgentStateReturn {
  // Sorted list of all known agents, stable by agent_id.
  readonly agents: ReadonlyArray<AgentState>;

  // Same data keyed by agent_id for fast lookup by Card components.
  readonly agentMap: AgentMap;

  // True when the WebSocket is open and the connection is healthy.
  readonly connected: boolean;

  // Last connection or parse error string; null when healthy.
  readonly error: string | null;

  // Last server-assigned sequence number we accepted. Useful for tests
  // and for a future "request snapshot" recovery path.
  readonly lastSeq: number | null;
}

// ---------------------------------------------------------------------------
// useAgentState
//
// Single-flight WebSocket lifecycle. The hook owns one connection at a
// time and reconnects with backoff on any unexpected close. Cleanup on
// unmount removes the onclose handler before close() so the cleanup
// path does not race the reconnect timer.
// ---------------------------------------------------------------------------

export function useAgentState(): UseAgentStateReturn {
  // Immutable Map of current agents. Each new frame produces a new Map
  // so React's reference-equality check sees the change.
  const [agentMap, setAgentMap] = useState<AgentMap>(
    () => new Map<string, AgentState>()
  );

  // Connection health flags. We keep them as separate state so a parse
  // error does not disconnect the socket but still surfaces in the UI.
  const [connected, setConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSeq, setLastSeq] = useState<number | null>(null);

  // Refs hold values that should not trigger re-renders. The active
  // socket, the current backoff delay, and the pending reconnect timer.
  const socketRef = useRef<WebSocket | null>(null);
  const backoffRef = useRef<number>(WS_RECONNECT_BASE_MS);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // unmountedRef prevents a late-arriving reconnect from creating a new
  // socket after the consumer has unmounted. Without this guard a fast
  // reconnect could leak a connection.
  const unmountedRef = useRef<boolean>(false);

  // ingestFrame parses a raw WebSocket payload and updates state. We
  // accept malformed messages without disconnecting so a single bad
  // frame cannot kill the live view.
  const ingestFrame = useCallback((rawData: string): void => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(rawData);
    } catch {
      setError('Received malformed WebSocket frame (not valid JSON)');
      return;
    }

    if (isSnapshotMessage(parsed)) {
      // Snapshot replaces the entire map; sequence resets to its value.
      setAgentMap(applySnapshot(parsed));
      setLastSeq(parsed.seq);
      setError(null);
      return;
    }

    if (isDiffMessage(parsed)) {
      // Capture the narrowed message into a local so the closure passed
      // to setAgentMap closes over a properly typed value rather than
      // the unknown that lives in the parent scope.
      const diff = parsed;
      setAgentMap((previous) => applyDiff(previous, diff));
      setLastSeq(diff.seq);
      setError(null);
      return;
    }

    // Unknown discriminator. Surface as an error but keep the socket
    // open; the next frame may be valid.
    setError('Received WebSocket frame with unknown type discriminator');
  }, []);

  // connect opens a new WebSocket. Ref-stable across renders so the
  // useEffect dependency does not re-trigger on every state change.
  const connect = useCallback((): void => {
    // Defensive close on any existing socket. Guards against duplicate
    // connect() calls that could otherwise leak sockets.
    if (socketRef.current !== null) {
      socketRef.current.onclose = null;
      socketRef.current.close();
    }

    const socket = new WebSocket(WS_URL);
    socketRef.current = socket;

    socket.onopen = (): void => {
      // Successful open. Reset backoff so a future drop starts at base.
      setConnected(true);
      setError(null);
      backoffRef.current = WS_RECONNECT_BASE_MS;
    };

    socket.onmessage = (event: MessageEvent): void => {
      // The server only sends string payloads; binary frames would be
      // unexpected and indicate a protocol mismatch we should log.
      if (typeof event.data === 'string') {
        ingestFrame(event.data);
        return;
      }
      setError('Received WebSocket frame with non-string payload');
    };

    socket.onerror = (): void => {
      // onerror always precedes onclose. Mark unhealthy here so the UI
      // updates immediately rather than after the close handler runs.
      setConnected(false);
      setError(`WebSocket error connecting to ${WS_URL}`);
    };

    socket.onclose = (): void => {
      setConnected(false);

      // Skip rescheduling if the consumer already unmounted.
      if (unmountedRef.current) {
        return;
      }

      // Capture current delay, then double for next time, capped.
      const delay = Math.min(backoffRef.current, WS_RECONNECT_MAX_MS);
      backoffRef.current = Math.min(delay * 2, WS_RECONNECT_MAX_MS);

      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, [ingestFrame]);

  useEffect(() => {
    // Reset the unmount flag in case React calls the effect twice in
    // dev StrictMode. We only set it true in cleanup.
    unmountedRef.current = false;
    connect();

    return () => {
      // Mark unmounted first so any scheduled reconnect aborts.
      unmountedRef.current = true;

      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      const socket = socketRef.current;
      if (socket !== null) {
        // Detach onclose first so close() does not schedule a reconnect.
        socket.onclose = null;
        socket.close();
        socketRef.current = null;
      }
    };
  }, [connect]);

  // Memoize the array projection so consumers can pass it to
  // React.memo'd children without busting their referential equality
  // every render. The Map identity changes only on a real update.
  const agents = agentMapToArray(agentMap);

  return { agents, agentMap, connected, error, lastSeq };
}

// ---------------------------------------------------------------------------
// useFilteredAgents
//
// Wraps useAgentState and narrows the agent list to those whose task or
// output_ref contains the selectedProjectPath. Pass null to see all agents.
// Keeps the filter logic out of every consumer component.
// ---------------------------------------------------------------------------

export function useFilteredAgents(
  selectedProjectPath: string | null
): UseAgentStateReturn {
  const state = useAgentState();

  const filtered = useMemo(() => {
    if (selectedProjectPath === null) return state.agents;
    const pathFragment = selectedProjectPath.split('/').pop()?.toLowerCase() ?? '';
    return state.agents.filter(
      (a) =>
        (a.output_ref?.includes(selectedProjectPath) ?? false) ||
        a.task.toLowerCase().includes(pathFragment)
    );
  }, [state.agents, selectedProjectPath]);

  const filteredMap = useMemo(
    () => new Map(filtered.map((a) => [a.agent_id, a])),
    [filtered]
  );

  return {
    ...state,
    agents: filtered,
    agentMap: filteredMap,
  };
}
