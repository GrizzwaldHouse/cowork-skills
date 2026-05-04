# Cross-System Bridge Specification

// Pattern: Decoupled HTTP POST event bridge between two independent systems

## When to Use This Pattern

When two systems need to exchange data but MUST remain independently deployable:
- BrightForge ↔ Honeybadger Vault
- Idea pipeline ↔ Document storage
- Orchestrator ↔ Execution agent on different host

## Architecture

```
┌─────────────────┐         HTTP POST          ┌─────────────────┐
│   System A      │ ─────────────────────────► │   System B      │
│   (Publisher)   │ ◄───────────────────────── │   (Subscriber)  │
│                 │      Async Acknowledgment   │                 │
│   Event Bus     │                              │   Event Bus     │
│   (internal)    │                              │   (internal)    │
└─────────────────┘                              └─────────────────┘
       ▲                                                  ▲
       │                                                  │
       └──────────────┬───────────────────────────────────┘
                      │
              Bridge Endpoints
              POST /bridge/event
              GET  /bridge/health
              GET  /bridge/events?since=...
```

## Event Schema

```typescript
interface BridgeEvent {
  event_id: string;        // UUID v4
  timestamp: string;       // ISO 8601
  source_system: string;   // 'BrightForge' | 'Honeybadger'
  target_system: string;   // 'BrightForge' | 'Honeybadger' | 'broadcast'
  event_type: string;      // From allowed event types
  payload: Record<string, any>;
  status: 'pending' | 'processed' | 'failed';
  retry_count?: number;
  error_message?: string;
}
```

## Allowed Event Types

```javascript
const BRIDGE_EVENTS = [
  // BrightForge → Honeybadger
  'idea_detected',
  'idea_scored',
  'idea_ranked',
  'index_request',
  'execution_started',

  // Honeybadger → BrightForge
  'index_completed',
  'document_linked',
  'execution_completed',
  'validation_passed',
  'validation_failed',

  // Bidirectional
  'agent_communication',
  'health_check'
];
```

## HTTP Endpoints

### POST /bridge/event

Receive an event from another system.

**Request**:
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-06T19:30:00Z",
  "source_system": "BrightForge",
  "target_system": "Honeybadger",
  "event_type": "idea_scored",
  "payload": {
    "idea_id": "abc123def456",
    "score": 0.82,
    "priority": "HIGH"
  },
  "status": "pending"
}
```

**Response 200**:
```json
{
  "received": true,
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "processed_at": "2026-04-06T19:30:01Z"
}
```

**Response 400**: Invalid event schema
**Response 503**: Subscriber unavailable, retry later

### GET /bridge/health

Health check for bridge availability.

**Response 200**:
```json
{
  "status": "healthy",
  "system": "Honeybadger",
  "uptime_seconds": 12345,
  "events_received": 487,
  "last_event_at": "2026-04-06T19:29:55Z"
}
```

### GET /bridge/events?since=ISO8601

Replay events since a timestamp (debugging/recovery).

## Integration Pattern (Publisher Side)

```javascript
// In System A's existing event bus
class BridgePublisher {
  constructor(targetUrl, sourceSystem) {
    this.targetUrl = targetUrl;  // 'http://localhost:3000'
    this.sourceSystem = sourceSystem;  // 'BrightForge'
    this.queue = [];
    this.maxRetries = 3;
  }

  // Publish event to remote system
  async publish(eventType, payload, targetSystem) {
    const event = {
      event_id: randomUUID(),
      timestamp: new Date().toISOString(),
      source_system: this.sourceSystem,
      target_system: targetSystem,
      event_type: eventType,
      payload,
      status: 'pending'
    };

    try {
      const response = await fetch(`${this.targetUrl}/bridge/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event)
      });

      if (!response.ok) {
        throw new Error(`Bridge POST failed: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      // Queue for retry
      this.queue.push({ event, retries: 0 });
      console.warn(`[BRIDGE] Queued event ${event.event_id}:`, err.message);
    }
  }

  // Subscribe to local event bus, forward to bridge
  attachToEventBus(eventBus) {
    const forwardEvents = ['idea_scored', 'idea_indexed', 'research_completed'];
    for (const eventType of forwardEvents) {
      eventBus.on(eventType, (payload) => {
        this.publish(eventType, payload, 'Honeybadger');
      });
    }
  }
}
```

## Integration Pattern (Subscriber Side)

```javascript
// In System B's existing API
import express from 'express';

const router = express.Router();

router.post('/bridge/event', (req, res) => {
  const event = req.body;

  // Validate schema
  if (!event.event_id || !event.event_type || !event.payload) {
    return res.status(400).json({ error: 'Invalid event schema' });
  }

  // Forward to local event bus for internal handling
  localEventBus.emit(`bridge:${event.event_type}`, event.payload);

  // Persist for audit/replay
  bridgeStorage.recordEvent(event);

  res.json({
    received: true,
    event_id: event.event_id,
    processed_at: new Date().toISOString()
  });
});

router.get('/bridge/health', (req, res) => {
  res.json({
    status: 'healthy',
    system: 'Honeybadger',
    uptime_seconds: process.uptime(),
    events_received: bridgeStorage.getCount(),
    last_event_at: bridgeStorage.getLastTimestamp()
  });
});

export { router as bridgeRouter };
```

## Testing Plan

```bash
# 1. Health check both systems
curl http://localhost:3847/bridge/health  # BrightForge
curl http://localhost:3000/bridge/health  # Honeybadger

# 2. Publish a test event from BrightForge to Honeybadger
curl -X POST http://localhost:3000/bridge/event \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-001",
    "timestamp": "2026-04-06T20:00:00Z",
    "source_system": "BrightForge",
    "target_system": "Honeybadger",
    "event_type": "idea_scored",
    "payload": {"idea_id": "test", "score": 0.85},
    "status": "pending"
  }'

# 3. Verify Honeybadger received it
curl http://localhost:3000/bridge/events?since=2026-04-06T19:00:00Z

# 4. Replay test (should be idempotent)
# Re-send the same event_id, expect 200 with no duplicate processing
```

## Constraints (Hard Rules)

- **No shared modules** between repos
- **No direct imports** between repos
- **No schema coupling** — each system owns its own DB
- **No file system dependencies** — communication via HTTP only
- **All async** — never block on bridge calls
- **Idempotent** — same event_id processed twice = no duplicate effect
- **Fail open** — bridge unavailability does NOT crash either system
- **Localhost only** — bind to 127.0.0.1, never 0.0.0.0
