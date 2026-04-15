# Beta Team: Path Tester

An obsessive route mapper that finds every endpoint, link, and file path in your app — then tries to break them all.

## What It Does

Runs a 6-phase path audit: Route Discovery, Endpoint Analysis, Path Traversal Testing, Navigation Flow Testing, Edge Case Paths, and Auth Boundary Testing. Produces a complete route map and vulnerability report.

## How to Use

```
/beta-team-path-tester
> Map and test all routes in D:\MyProject
```

## What It Catches

- Auth bypasses and IDOR (accessing other users' data via ID manipulation)
- Path traversal vulnerabilities (../../etc/passwd style attacks)
- Unprotected API endpoints missing auth middleware
- Dead links and orphan routes
- Missing input validation on route parameters
- Edge case URL handling (unicode, special chars, double slashes)
- Privilege escalation via hidden admin endpoints

## Output

Structured Markdown report with full route map table, security vulnerabilities, auth boundary issues, and edge case failures.

## Part of the Beta Team

One of 5 specialized testers. See also: `beta-team-code-debugger`, `beta-team-db-tester`, `beta-team-ui-tester`, `beta-team-button-pusher`.
