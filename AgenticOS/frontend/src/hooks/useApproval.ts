// useApproval.ts
// Developer: Marcus Daley
// Date: 2026-04-29
// Purpose: POSTs ApprovalPayload bodies to the FastAPI REST endpoints,
//          tracks per-agent loading and error state, and emits an
//          idempotency key so the server can dedupe accidental retries.
//          Each agent gets independent loading and error state so a
//          slow gate on AGENT-01 does not freeze the UI for AGENT-02.

import { useCallback, useState } from 'react';
import type { ApprovalKind, ApprovalPayload } from '@/types/agent';
import { ENDPOINTS, IDEMPOTENCY_HEADER } from '@/config';

// ---------------------------------------------------------------------------
// UseApprovalReturn
// ---------------------------------------------------------------------------

export interface UseApprovalReturn {
  // True while a POST is in-flight for the given agent_id.
  readonly loading: Readonly<Record<string, boolean>>;

  // Last error message for the given agent_id; null if last call was OK.
  readonly error: Readonly<Record<string, string | null>>;

  // Posts the decision and resolves when the server responds. Optional
  // reviewerContext is forwarded only when decision === 'review'.
  readonly approve: (
    agentId: string,
    decision: ApprovalKind,
    reviewerContext?: string
  ) => Promise<void>;
}

// ---------------------------------------------------------------------------
// resolveEndpoint
//
// Selects the URL for the given decision. Exhaustive switch so adding a
// new ApprovalKind is a TypeScript compile error until handled here.
// ---------------------------------------------------------------------------

function resolveEndpoint(agentId: string, decision: ApprovalKind): string {
  switch (decision) {
    case 'proceed':
      return ENDPOINTS.approve(agentId);
    case 'research':
      return ENDPOINTS.research(agentId);
    case 'review':
      return ENDPOINTS.review(agentId);
  }
}

// ---------------------------------------------------------------------------
// generateIdempotencyKey
//
// crypto.randomUUID is available in modern browsers and the WebView2
// host. We fall back to a timestamp+random key only if the API is
// unavailable; either way the value is opaque to the server.
// ---------------------------------------------------------------------------

function generateIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback path. Not cryptographically strong; only needs to be
  // unique within a session of the dashboard.
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

// ---------------------------------------------------------------------------
// useApproval
// ---------------------------------------------------------------------------

export function useApproval(): UseApprovalReturn {
  // Per-agent loading flags. Keyed by agent_id so independent posts do
  // not block each other.
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  // Per-agent error strings. Cleared on a successful follow-up post.
  const [error, setError] = useState<Record<string, string | null>>({});

  // Stable across renders so child components can pass it to React.memo
  // boundaries without busting referential equality every render.
  const approve = useCallback(
    async (
      agentId: string,
      decision: ApprovalKind,
      reviewerContext?: string
    ): Promise<void> => {
      // Mark loading and clear stale error for this agent only.
      setLoading((prev) => ({ ...prev, [agentId]: true }));
      setError((prev) => ({ ...prev, [agentId]: null }));

      const url = resolveEndpoint(agentId, decision);

      // Build the payload. reviewer_context only included when present
      // because exactOptionalPropertyTypes treats explicit undefined
      // differently from the key being absent.
      const payload: ApprovalPayload =
        reviewerContext !== undefined
          ? { decision, reviewer_context: reviewerContext }
          : { decision };

      const idempotencyKey = generateIdempotencyKey();

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            [IDEMPOTENCY_HEADER]: idempotencyKey,
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          // Surface HTTP errors with their status; FastAPI uses these.
          throw new Error(
            `Server responded with ${response.status}: ${response.statusText}`
          );
        }
      } catch (caught) {
        // Distinguish Error instances (typical) from arbitrary throws.
        const message =
          caught instanceof Error
            ? caught.message
            : 'Unknown error posting approval decision';
        setError((prev) => ({ ...prev, [agentId]: message }));
      } finally {
        // Always release the loading flag, success or failure.
        setLoading((prev) => ({ ...prev, [agentId]: false }));
      }
    },
    []
  );

  return { loading, error, approve };
}
