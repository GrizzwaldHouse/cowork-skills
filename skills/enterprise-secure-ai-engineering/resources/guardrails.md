# Enterprise AI Engineering Guardrails

This repository enforces enterprise-grade AI-assisted development standards.

## 1. Runtime
- Supported runtime only
- No EOL versions
- No deprecated frameworks

## 2. Dependencies
- Version locked (no latest)
- Dependabot enabled
- No abandoned packages
- No critical CVEs allowed

## 3. Secure Coding
- Parameterized queries only
- No dynamic SQL
- Zod validation required (client + server)
- No custom crypto
- No custom auth
- No sensitive logs
- Debug disabled in production

## 4. Web Protection
- All Next.js server actions treated as public endpoints
- Protected via Arcjet or equivalent
- Rate limiting mandatory
- Middleware (proxy.ts) required

## 5. AI Code Governance
- AI code > 350 lines requires manual review
- Scan for hallucinated functions
- No placeholder comments like "TODO: implement later"
- Review for race conditions and edge cases
- Use CodeRabbit for PR audits

## 6. Architecture
- Atomic design
- Clear folder segregation:
  - /auth
  - /marketing
  - /resources
- Drizzle ORM preferred
- Zustand for state
- TanStack Query for async caching

## 7. Configuration & Secrets
- No hardcoded credentials
- Separate config from logic
- No env-specific paths
- No secrets in repo

## 8. Version Control & Deployment
- Approved git repo only
- No direct production edits
- Environment separation required
- Reproducible builds required

## 9. Vulnerability Management
- Track in issue system
- Assign severity
- Block release if critical
- Root cause analysis required

## 10. Security Testing
- Static analysis required
- Significant findings must be resolved
- Security review for critical apps
- Non-production testing required

## 11. Secure Design
- Disable unused services
- Least privilege required
- No unnecessary exposed endpoints
- No client-side validation only
