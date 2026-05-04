# Beta Team: Code Debugger

A picky beta client that audits your source code and sends back a brutally honest fix list.

## What It Does

Runs a 5-phase code audit: Discovery, Static Analysis, Dependency Audit, Standards Check, and Bug Hunt. Produces a prioritized fix list with file paths, line numbers, and severity ratings.

## How to Use

```
/beta-team-code-debugger
> Audit my project at D:\MyProject
```

Or just tell Claude to run a code audit with a picky client personality.

## What It Catches

- Dead code, unused imports, unreachable branches
- Security issues (eval, SQL injection, hardcoded secrets, XSS)
- Anti-patterns (god classes, magic numbers, DRY violations)
- Missing error handling, type safety gaps
- Outdated/vulnerable dependencies
- Test coverage gaps
- Naming and documentation inconsistencies

## Output

Structured Markdown report with sections: Critical, Major, Minor, Nitpicks, plus dependency health and test coverage tables. Every issue has a file path and line number.

## Part of the Beta Team

One of 5 specialized testers. See also: `beta-team-db-tester`, `beta-team-path-tester`, `beta-team-ui-tester`, `beta-team-button-pusher`.
