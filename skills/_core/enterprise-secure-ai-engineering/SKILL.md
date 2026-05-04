---
name: enterprise-secure-ai-engineering
description: Enforces enterprise-grade runtime, security, dependency, and AI-assisted coding guardrails aligned with OWASP, NIST SSDF, SLSA, and SOC2-aligned SDLC practices.
user-invocable: false
---

# Enterprise Secure AI Engineering

> Enterprise-grade software engineering, AI-assisted development governance, and security guardrails for all Claude Code sessions.

## Description

Enforces runtime safety, dependency hygiene, secure coding practices, web application protections, AI-generated code governance, and architecture standards across all projects. Aligned with OWASP Top 10, NIST Secure Software Development Framework (SSDF), SLSA Supply Chain Levels, and SOC2 Change Management Controls.

## Prerequisites

- Node.js LTS (supported, non-EOL version)
- Package manager with lockfile support (npm, yarn, pnpm)
- Dependabot or equivalent dependency scanner enabled on repository
- CodeRabbit or equivalent for PR audit (recommended)

## Usage

These guardrails are auto-applied. Every code generation, review, and architecture decision must pass these checks before presenting to Marcus.

1. Verify runtime and framework versions are supported and non-EOL
2. Check all dependencies are version-locked with no critical CVEs
3. Apply secure coding rules (parameterized queries, Zod validation, no custom crypto/auth)
4. Enforce web protections (rate limiting, server action hardening, proxy middleware)
5. Govern AI-generated code (manual review thresholds, placeholder detection, edge case scanning)
6. Validate architecture follows atomic design with proper folder segregation

### Prompt Pattern

```
Review this [project/PR/feature] against enterprise secure AI engineering guardrails.
Check: runtime, dependencies, secure coding, web protections, AI code governance, architecture.
Flag violations by severity (CRITICAL, HIGH, MEDIUM, LOW).
```

## 1. Runtime & Framework

| Rule | Severity |
|------|----------|
| Supported runtime versions only (Node.js LTS, current React/Next.js) | CRITICAL |
| No end-of-life (EOL) versions in production | CRITICAL |
| No deprecated frameworks or libraries | HIGH |
| No obsolete language features (var in TS, class components without reason) | MEDIUM |

## 2. Dependencies

| Rule | Severity |
|------|----------|
| Document ALL dependencies with purpose justification | HIGH |
| Version-locked in lockfile (no `^`, no `latest` tags) | CRITICAL |
| Reject abandoned packages (no updates in 12+ months, no maintainer) | HIGH |
| Block known critical vulnerabilities (CVE with CVSS >= 9.0) | CRITICAL |
| Enable Dependabot or equivalent automated scanner | HIGH |
| Audit transitive dependencies for supply chain risk | MEDIUM |

## 3. Secure Coding

| Rule | Severity |
|------|----------|
| Parameterized queries only -- NEVER dynamic SQL/query construction | CRITICAL |
| Server-side validation required for ALL external input | CRITICAL |
| Validate with Zod on both client and server | HIGH |
| No custom cryptography implementations | CRITICAL |
| No custom authentication logic (use established libraries: NextAuth, Clerk, Auth0) | CRITICAL |
| No sensitive data in logs (passwords, tokens, PII, credit cards) | CRITICAL |
| Hide stack traces in production error responses | HIGH |
| Debug mode disabled in production builds | HIGH |

## 4. Configuration & Secrets

| Rule | Severity |
|------|----------|
| No hardcoded credentials, API keys, or tokens in source code | CRITICAL |
| Separate configuration from business logic | HIGH |
| No environment-specific paths hardcoded in source | HIGH |
| No secrets committed to repository (use .env + .gitignore, secret managers) | CRITICAL |

## 5. Version Control & Deployment

| Rule | Severity |
|------|----------|
| All code changes go through approved git repository | HIGH |
| No direct production edits -- all changes through CI/CD pipeline | CRITICAL |
| Environment separation required (dev, staging, production) | HIGH |
| Reproducible builds required (lockfiles, pinned versions, deterministic output) | HIGH |

## 6. Vulnerability Management

| Rule | Severity |
|------|----------|
| Track all vulnerabilities in issue tracking system | HIGH |
| Assign severity rating (CVSS or equivalent) to every finding | HIGH |
| Block release if unresolved critical vulnerabilities exist | CRITICAL |
| Root cause analysis required for every security incident | HIGH |

## 7. Security Testing

| Rule | Severity |
|------|----------|
| Static analysis required (ESLint security plugins, Semgrep, or equivalent) | HIGH |
| All significant static analysis findings must be resolved before merge | HIGH |
| Security review required for critical application changes | HIGH |
| All testing done in non-production environments | HIGH |

## 8. Secure Design

| Rule | Severity |
|------|----------|
| Disable unused services, ports, and endpoints | MEDIUM |
| Least privilege required for all service accounts and API keys | HIGH |
| No unnecessary exposed endpoints (audit route files regularly) | HIGH |
| Never rely on client-side validation alone | CRITICAL |

## 9. AI-Generated Code Governance

| Rule | Severity |
|------|----------|
| All AI-generated code must be reviewed manually before commit | HIGH |
| AI output exceeding 350 lines requires dedicated review pass | HIGH |
| Detect and reject pseudocode or placeholder comments ("TODO: implement later") | HIGH |
| Scan AI output for race conditions and concurrency issues | HIGH |
| Scan AI output for unhandled edge cases (null, empty, boundary values) | HIGH |
| Scan AI output for attack surface vectors (injection, XSS, SSRF) | CRITICAL |
| Detect hallucinated function calls (functions that don't exist in the codebase) | HIGH |
| Use CodeRabbit or equivalent for automated PR audit | MEDIUM |

## 10. Web Application Protections

| Rule | Severity |
|------|----------|
| Rate limiting required on all public endpoints | HIGH |
| Use Arcjet or equivalent runtime protection layer | HIGH |
| Treat ALL Next.js server actions as public endpoints (apply auth + validation) | CRITICAL |
| Proxy middleware (proxy.ts or equivalent) required for external API calls | HIGH |
| Validate all inputs with Zod schemas before processing | HIGH |

## 11. State Management

| Concern | Recommended | Notes |
|---------|-------------|-------|
| Client state | Zustand | Lightweight, no boilerplate, TS-first |
| Server/async data | TanStack Query | Caching, deduplication, background refresh |
| Suspense boundaries | Use with caution | Warn on latency risk; provide loading states |

## 12. Architecture Patterns

### Folder Structure

```
app/
  (main_app)/        # Core application routes
  (auth)/            # Authentication pages (login, register, reset)
  (marketing)/       # Landing pages, public-facing content
  (resources)/       # Legal docs, blog, changelog, backlog
```

### Design Rules

| Rule | Details |
|------|---------|
| Atomic design required | Atoms, molecules, organisms, templates, pages |
| Drizzle ORM preferred | Type-safe database access, schema-as-code |
| Clear route group separation | Auth, marketing, resources isolated from main app |
| Shared components in `/components` | Reusable across all route groups |

## Compliance Alignment

| Standard | Coverage |
|----------|----------|
| OWASP Top 10 | Sections 3, 4, 8, 10 (injection, auth, secrets, input validation) |
| NIST SSDF | Sections 1, 2, 5, 6, 7 (runtime, dependencies, VCS, vuln mgmt, testing) |
| SLSA Supply Chain Levels | Sections 2, 5 (dependency integrity, reproducible builds) |
| SOC2 Change Management | Sections 5, 6, 7 (version control, vuln tracking, security testing) |

## External Tools (Recommended)

| Tool | Purpose |
|------|---------|
| CodeRabbit | Automated PR security and quality audit |
| Dependabot | Dependency vulnerability scanning and auto-updates |
| Arcjet | Runtime protection (rate limiting, bot detection, data redaction) |
| Zod | Schema validation for TypeScript (client + server) |
| Drizzle ORM | Type-safe SQL with schema-as-code |
| Zustand | Lightweight client state management |
| TanStack Query | Server state, caching, and async data management |

## Examples

### Example 1: Server Action Security Review

**Input:**
```
Review this Next.js server action for enterprise guardrails.
```

**Output:**
Check: (1) Auth guard present -- server actions are public endpoints, (2) Zod schema validates all input, (3) Rate limiting via Arcjet applied, (4) No raw SQL -- using Drizzle parameterized queries, (5) No sensitive data in error responses, (6) Errors logged server-side only with contextual IDs.

### Example 2: Dependency Audit

**Input:**
```
Audit dependencies in package.json against enterprise guardrails.
```

**Output:**
Check: (1) All versions pinned (no ^/~), (2) No packages with critical CVEs, (3) No abandoned packages (last publish > 12 months), (4) All dependencies documented with purpose, (5) Lockfile committed and consistent, (6) Dependabot configured.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| auto_apply | true | Guardrails active on all sessions |
| ai_review_threshold | 350 | Lines of AI output requiring dedicated review |
| cvss_block_threshold | 9.0 | Block release at this CVSS severity or above |
| rate_limit_required | true | All public endpoints must have rate limiting |

## File Structure

```
enterprise-secure-ai-engineering/
  SKILL.md                          # This skill definition
  README.md                         # Quick-start guide
  resources/
    guardrails.md                   # Human-readable guardrails reference
    skill-definition.json           # Machine-readable JSON definition
```

## Notes

- These guardrails enforce a security-first development posture. They are not optional.
- AI-generated code governance is particularly critical -- AI can produce plausible but vulnerable code.
- Server actions in Next.js are the most common source of unprotected endpoints. Treat every server action as a public API.
- Drizzle ORM is preferred over raw SQL or Prisma for its type safety and schema-as-code approach.
- When a rule conflicts with Marcus's universal coding standards, the MORE restrictive rule wins.
