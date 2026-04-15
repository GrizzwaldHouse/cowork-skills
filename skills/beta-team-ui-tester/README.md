# Beta Team: UI/UX Tester

A design-obsessed client that uses Playwright to test your app's UI across every device, breakpoint, and accessibility standard.

## What It Does

Writes and runs real Playwright tests covering: visual inventory (screenshots at 3 breakpoints), layout audit, accessibility (axe-core), interaction testing, dark mode, and performance metrics. Produces reusable test files your team can run again.

## How to Use

```
/beta-team-ui-tester
> Audit the UI at http://localhost:3000
```

Requires a running app URL. The skill will install Playwright if needed.

## What It Catches

- Responsive layout breaks (horizontal scroll, overflow, tiny text)
- Accessibility violations (missing alt text, contrast, keyboard nav, ARIA)
- Interaction bugs (forms, modals, navigation, loading states)
- Visual inconsistencies across breakpoints
- Performance issues (slow LCP, layout shifts)
- Dark mode / theme problems

## Output

Screenshots saved to `tests/beta-team-ui/screenshots/`, reusable Playwright test files, and a structured audit report with accessibility violations table and performance metrics.

## Part of the Beta Team

One of 5 specialized testers. See also: `beta-team-code-debugger`, `beta-team-db-tester`, `beta-team-path-tester`, `beta-team-button-pusher`.
