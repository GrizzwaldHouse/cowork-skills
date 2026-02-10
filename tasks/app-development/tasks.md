# App Development Task Templates

Reusable task templates for building applications. Copy the relevant section into your project's tasks.md or use directly with Claude Code.

---

## New Feature Implementation

### Planning Phase
- [ ] Define user story: "As a [user], I want [feature] so that [benefit]"
- [ ] Identify acceptance criteria (minimum 3)
- [ ] Research existing patterns in codebase
- [ ] Design component architecture (which files, which functions)
- [ ] Identify dependencies and potential breaking changes

### Implementation Phase
- [ ] Create feature branch: `feature/[name]`
- [ ] Implement core logic
- [ ] Add input validation and error handling
- [ ] Write unit tests (aim for 80%+ coverage)
- [ ] Add integration tests for critical paths
- [ ] Update types/interfaces if TypeScript

### UI Implementation
- [ ] Build component structure (HTML/JSX)
- [ ] Apply styling following design system (8px grid, color palette, typography)
- [ ] Add responsive breakpoints (mobile: 640px, tablet: 1024px, desktop: 1440px)
- [ ] Implement loading states and error states
- [ ] Add keyboard navigation and focus management
- [ ] Test on mobile viewport

### Review Phase
- [ ] Self-review diff for code quality
- [ ] Run linter and fix warnings
- [ ] Run full test suite
- [ ] Test edge cases manually
- [ ] Create PR with description and screenshots

---

## Bug Fix Workflow

- [ ] Reproduce the bug consistently
- [ ] Identify root cause (add debug logging if needed)
- [ ] Write a failing test that captures the bug
- [ ] Implement the fix
- [ ] Verify the failing test now passes
- [ ] Check for similar bugs in related code
- [ ] Run regression tests
- [ ] Document what caused the bug and how it was fixed

---

## UI/UX Upgrade (Prototype to Production)

### Audit Current State
- [ ] Screenshot every screen/component at current state
- [ ] List all UI issues: spacing, alignment, colors, typography, responsiveness
- [ ] Check accessibility: contrast ratios, keyboard nav, screen reader labels
- [ ] Identify components that can be reused/standardized

### Design System Setup
- [ ] Define color palette (primary, secondary, accent, neutrals, semantic)
- [ ] Define typography scale (heading sizes, body, caption, using 1.25 or 1.333 ratio)
- [ ] Define spacing scale (4, 8, 16, 24, 32, 48, 64, 96px)
- [ ] Define border radius system (consistent across all components)
- [ ] Create CSS variables or theme tokens for all design values

### Component Upgrade (per component)
- [ ] Apply correct colors from palette
- [ ] Apply correct typography (font, size, weight, line-height)
- [ ] Apply correct spacing (margins, padding from spacing scale)
- [ ] Add hover/focus/active states
- [ ] Add transition animations (150-300ms ease)
- [ ] Test responsive behavior
- [ ] Test dark mode (if applicable)

### Final Polish
- [ ] Consistent border radius across all elements
- [ ] Consistent shadow system (sm, md, lg)
- [ ] Loading skeletons for async content
- [ ] Empty states for lists/tables
- [ ] Error states with recovery actions
- [ ] Smooth page transitions

---

## API Endpoint Implementation

- [ ] Define route, method, request/response schema
- [ ] Implement request validation (Pydantic, Zod, or equivalent)
- [ ] Implement business logic
- [ ] Add proper error handling with status codes
- [ ] Add authentication/authorization checks
- [ ] Write API tests (happy path + error cases)
- [ ] Document endpoint (OpenAPI/Swagger or README)
- [ ] Test with real client (frontend or Postman)

---

## Database Schema Change

- [ ] Design schema change (new table, column, index, relation)
- [ ] Write migration script (up and down)
- [ ] Test migration on local database
- [ ] Update ORM models/types
- [ ] Update affected queries
- [ ] Update affected API endpoints
- [ ] Run full test suite
- [ ] Plan production migration (downtime, rollback strategy)

---

## Performance Optimization

- [ ] Profile current performance (load time, render time, API response time)
- [ ] Identify top 3 bottlenecks
- [ ] For each bottleneck:
  - [ ] Measure baseline metric
  - [ ] Implement optimization
  - [ ] Measure improvement
  - [ ] Verify no regressions
- [ ] Common optimizations to check:
  - [ ] Unnecessary re-renders (React.memo, useMemo)
  - [ ] N+1 database queries
  - [ ] Missing indexes on frequently queried columns
  - [ ] Unoptimized images (compression, lazy loading, WebP)
  - [ ] Bundle size (tree shaking, code splitting, dynamic imports)
  - [ ] Caching (API responses, computed values, static assets)

---

## Deployment Checklist

- [ ] All tests passing
- [ ] No linter warnings
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Build succeeds in production mode
- [ ] Feature flags set correctly
- [ ] Monitoring/alerting configured
- [ ] Rollback plan documented
- [ ] Changelog updated
