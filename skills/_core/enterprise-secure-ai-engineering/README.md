# Enterprise Secure AI Engineering

Enterprise-grade runtime, security, dependency, and AI-assisted coding guardrails for all Claude Code sessions.

## Quick Start

These guardrails are auto-applied. Every code change must pass:

1. **Runtime** -- Supported, non-EOL versions only
2. **Dependencies** -- Version-locked, no critical CVEs, no abandoned packages
3. **Secure Coding** -- Parameterized queries, Zod validation, no custom crypto/auth
4. **Secrets** -- No hardcoded credentials, no secrets in repo
5. **Deployment** -- No direct prod edits, reproducible builds, environment separation
6. **Vulnerability Mgmt** -- Track, severity-rate, block release on critical
7. **Security Testing** -- Static analysis required, findings resolved before merge
8. **Secure Design** -- Least privilege, no unnecessary endpoints, server-side validation
9. **AI Code Governance** -- Manual review, 350-line threshold, placeholder/hallucination detection
10. **Web Protections** -- Rate limiting, Arcjet, server action hardening, Zod input validation
11. **State Management** -- Zustand (client), TanStack Query (server/async)
12. **Architecture** -- Atomic design, route group separation, Drizzle ORM

## Compliance

Aligned with OWASP Top 10, NIST SSDF, SLSA Supply Chain Levels, and SOC2 Change Management Controls.

## Recommended Tools

CodeRabbit, Dependabot, Arcjet, Zod, Drizzle ORM, Zustand, TanStack Query
