// useAgentState.test.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: Unit tests for useAgentState. Stubs the global WebSocket so
//          we can drive open/message/close/error events deterministically.
//          Uses fake timers to advance the reconnect backoff without
//          actually waiting in real time.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAgentState } from '@/hooks/useAgentState';
import {
  MESSAGE_TYPE_DIFF,
  MESSAGE_TYPE_SNAPSHOT,
} from '@/config';
import type { AgentState } from '@/types/agent';
import type { DiffMessage, SnapshotMessage } from '@/types/messages';

// ---------------------------------------------------------------------------
// MockWebSocket
//
// Minimal stand-in for the global WebSocket. Stores every instance so
// the test can drive its handlers; the hook only reads the standard
// callback properties so this is sufficient.
// ---------------------------------------------------------------------------

class MockWebSocket {
  public static instances: MockWebSocket[] = [];

  // Standard fields the hook may consult.
  public readonly url: string;
  public readyState: number = 0;

  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;

  public constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  // Test helpers; not part of the real WebSocket API.
  public triggerOpen(): void {
    this.readyState = 1;
    this.onopen?.(new Event('open'));
  }

  public triggerMessage(data: unknown): void {
    this.onmessage?.(
      new MessageEvent('message', { data: JSON.stringify(data) })
    );
  }

  public triggerRawMessage(raw: string): void {
    this.onmessage?.(new MessageEvent('message', { data: raw }));
  }

  public triggerClose(): void {
    this.readyState = 3;
    this.onclose?.(new CloseEvent('close'));
  }

  public close(): void {
    this.readyState = 3;
  }
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const AGENT_ONE: AgentState = {
  agent_id: 'AGENT-01',
  domain: 'general',
  task: 'Test task',
  stage_label: 'Running',
  stage: 1,
  total_stages: 3,
  progress_pct: 33,
  status: 'active',
  context_pct_used: 10,
  output_ref: null,
  awaiting: null,
  error_msg: null,
  spawned_by: null,
  reviewer_verdict: null,
  updated_at: '2026-04-29T10:00:00Z',
};

const AGENT_TWO: AgentState = {
  ...AGENT_ONE,
  agent_id: 'AGENT-02',
  progress_pct: 66,
};

function buildSnapshot(seq: number): SnapshotMessage {
  return {
    type: MESSAGE_TYPE_SNAPSHOT,
    seq,
    agents: { [AGENT_ONE.agent_id]: AGENT_ONE },
  };
}

function buildDiff(seq: number): DiffMessage {
  return {
    type: MESSAGE_TYPE_DIFF,
    seq,
    added: { [AGENT_TWO.agent_id]: AGENT_TWO },
    updated: {},
    removed: [],
  };
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket);
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('useAgentState', () => {
  it('ingests a snapshot frame and exposes its agents', () => {
    // Snapshot replaces the entire map. After ingest the map should
    // contain exactly the snapshot agents and nothing else.
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerMessage(buildSnapshot(1));
    });
    expect(result.current.connected).toBe(true);
    expect(result.current.agents).toHaveLength(1);
    expect(result.current.agents[0].agent_id).toBe('AGENT-01');
    expect(result.current.lastSeq).toBe(1);
  });

  it('applies a diff frame on top of the snapshot', () => {
    // The diff adds AGENT-02; AGENT-01 stays from the snapshot.
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerMessage(buildSnapshot(1));
      MockWebSocket.instances[0].triggerMessage(buildDiff(2));
    });
    expect(result.current.agents).toHaveLength(2);
    expect(result.current.agentMap.get('AGENT-02')?.progress_pct).toBe(66);
    expect(result.current.lastSeq).toBe(2);
  });

  it('schedules a reconnect after the socket closes unexpectedly', () => {
    // Open then close the first socket; advance fake timers past the
    // base backoff. A second socket instance should be created.
    renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerClose();
    });
    expect(MockWebSocket.instances).toHaveLength(1);

    // Advance past WS_RECONNECT_BASE_MS (1000ms) plus a small buffer.
    act(() => {
      vi.advanceTimersByTime(1500);
    });
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it('surfaces an error on malformed JSON without disconnecting', () => {
    // Bad frames must not close the socket; the next valid frame should
    // still be processed normally.
    const { result } = renderHook(() => useAgentState());
    act(() => {
      MockWebSocket.instances[0].triggerOpen();
      MockWebSocket.instances[0].triggerRawMessage('not-json{{{');
    });
    expect(result.current.error).toMatch(/malformed/iu);
    expect(result.current.connected).toBe(true);
  });
});
