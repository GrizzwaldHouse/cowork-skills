---
name: vault-analysis
description: Continuous AI engineering analysis system for Alexander Vault — architecture, security, dependency, and concurrency scanners with visualization dashboard.
user-invocable: false
---

# Vault Analysis System

> Automated static analysis pipeline for Alexander Vault. Runs architecture, security, dependency, and concurrency scans with live event-driven results.

## Description

The analysis system provides a continuous quality engineering loop that can be triggered manually, from git hooks, or via CLI. It scans the codebase for architectural violations, security vulnerabilities, dependency issues, and concurrency bugs.

## Architecture

### Analyzers (server/analysis/)

| Analyzer | File | Detects |
|----------|------|---------|
| Architecture | architecture-analyzer.ts | Circular deps, tight coupling, module boundary violations, event flow |
| Security | security-scanner.ts | Hardcoded keys, auth gaps, path traversal, stack trace leaks |
| Dependency | dependency-auditor.ts | npm vulns, unused deps, outdated packages |
| Concurrency | concurrency-analyzer.ts | Missing await, race conditions, EventBus error handling |
| Orchestrator | analysis-orchestrator.ts | Coordinates all 4 analyzers, caches results, persists to knowledge/ |

### API Endpoints (server/routes/analysis.ts)

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/analysis/run | Run full analysis (all 4 analyzers) |
| POST | /api/analysis/run/:type | Run single analyzer |
| GET | /api/analysis/results | Get latest run results |
| GET | /api/analysis/results/:runId | Get specific run by ID |
| GET | /api/analysis/architecture-map | Module dependency graph |
| GET | /api/analysis/event-bus-map | EventBus emitter/subscriber map |
| GET | /api/analysis/history | List of past analysis runs |

### Types (server/analysis/analysis-types.ts)

// Finding — single issue found by an analyzer
// Fields: id, type, severity (critical|high|medium|low|info), title, description, file?, line?, suggestion?

// AnalysisResult — from a single analyzer run
// Fields: analyzerId, timestamp, duration, findings[], summary, severityCounts

// AnalysisRunResult — from running all analyzers
// Fields: id, timestamp, analyzers (Record<string, AnalysisResult>), overallStatus (pass|warn|fail)

### EventBus Integration

// Analysis events flow through the same SSE stream as extraction events
// Event types: analysis:start, analysis:progress, analysis:complete, analysis:error
// Server: extractionEventBus.emitAnalysis(event)
// Client: SSE stream at /api/extraction/events includes analysis events

### Frontend

// Architecture.tsx — visualization page with:
// - Force-directed module dependency graph (canvas-based)
// - Run buttons for full and individual analyzers
// - Findings panel with severity tabs and grouping
// - History timeline
// - Selected module detail (imports from/imported by)
// Hook: client/src/hooks/use-analysis.ts (React Query)

## CLI Commands

```bash
npm run analysis:run        # Full analysis (all 4 analyzers)
npm run analysis:security   # Security scan only
npm run docs:generate       # Generate architecture-map.md, event-bus-map.md, security-architecture.md
npm run hooks:install       # Install git pre-commit + post-commit hooks
```

## Git Hooks

// pre-commit: Runs security scan. Blocks commit if critical findings detected.
// post-commit: Runs full analysis (non-blocking, informational only).
// Install: npm run hooks:install
// Bypass: git commit --no-verify

## Extending

To add a new analyzer:
1. Create server/analysis/your-analyzer.ts implementing run(): AnalysisResult
2. Import and wire it in analysis-orchestrator.ts (runFullAnalysis + runSingleAnalysis)
3. Add the type to the Zod enum in server/routes/analysis.ts
4. Frontend will automatically pick it up via the existing tab system

## Related Skills

- architecture-patterns — Module boundaries and Observer pattern rules
- enterprise-secure-ai-engineering — Security guardrails
- dev-workflow — Build/test workflow standards
