# Beta Team: Button Pusher

The chaos monkey of QA. Uses Playwright to click every button, fill every form with garbage, toggle every switch rapidly, and log exactly what breaks.

## What It Does

Writes and runs real Playwright tests across 6 phases: Element Census, Button Push Sequence, Form Chaos, Toggle Tornado, Scroll Abyss, and Rapid Fire stress tests. Generates reusable test files and a detailed interaction log in JSON.

## How to Use

```
/beta-team-button-pusher
> Push every button at http://localhost:3000
```

Requires a running app URL. Installs Playwright if needed.

## What It Catches

- Buttons that crash the app or produce console errors
- Forms without validation (empty submit, XSS, SQL injection, wrong types)
- Double-click bugs (duplicate submissions)
- Toggle state inconsistencies under rapid interaction
- Missing loading/disabled states during async operations
- Network errors triggered by UI interactions
- Unresponsive states and UI lockups

## Output

JSON results log at `tests/beta-team-button-push/button-results.json`, 6 reusable Playwright test files, and a structured report with element census, button push results, and form chaos findings.

## Part of the Beta Team

The most chaotic of 5 specialized testers. See also: `beta-team-code-debugger`, `beta-team-db-tester`, `beta-team-path-tester`, `beta-team-ui-tester`.
