# Beta Team: Database Tester

A paranoid DBA that audits your database layer and assumes your data is one bad migration away from oblivion.

## What It Does

Runs a 6-phase database audit: Schema Discovery, Schema Analysis, Query Audit, Migration Safety, Connection Management, and Data Integrity. Produces a prioritized report organized by data loss risk.

## How to Use

```
/beta-team-db-tester
> Audit the database layer of D:\MyProject
```

## What It Catches

- SQL injection (raw queries without parameterization)
- N+1 query patterns and missing pagination
- Missing indexes, foreign keys, and constraints
- Destructive migrations without rollbacks
- Connection leaks and missing pool configuration
- Missing transaction boundaries on multi-step writes
- Hardcoded credentials in connection strings

## Output

Structured Markdown report with data loss risks, performance bombs, schema issues, query smells, and a full schema summary table.

## Part of the Beta Team

One of 5 specialized testers. See also: `beta-team-code-debugger`, `beta-team-path-tester`, `beta-team-ui-tester`, `beta-team-button-pusher`.
