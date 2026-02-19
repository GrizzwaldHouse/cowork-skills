# Workflow Productivity

## Name

Workflow Productivity

## Description

A skill for automating repetitive development tasks, streamlining workflows, and boosting day-to-day productivity. Covers scripting, CI/CD pipelines, file management, batch operations, and tool configuration.

## Prerequisites

- A shell environment (Bash, PowerShell, or Zsh)
- Familiarity with your project's build tools and task runners
- Access to any external services you want to automate (GitHub, Jira, Slack, etc.)

## Usage

1. Describe the repetitive task or workflow bottleneck.
2. Specify the tools and environment involved.
3. Provide any existing scripts or configuration for context.
4. Review and adopt the generated automation.

### Prompt Pattern

```
I want to automate [task description].
Environment: [OS, shell, tools]
Current process: [manual steps being done today]
Desired outcome: [what the automation should achieve]
```

## Examples

### Example 1: Batch Rename Files

**Input:**
```
I want to automate renaming all .jpeg files to .jpg in a folder recursively.
Environment: Windows 11, PowerShell
Current process: Manual rename one by one.
Desired outcome: A script that renames all .jpeg to .jpg recursively.
```

**Output:**
```powershell
Get-ChildItem -Path . -Filter *.jpeg -Recurse | Rename-Item -NewName { $_.Name -replace '\.jpeg$', '.jpg' }
```

## Configuration

| Parameter       | Default    | Description                                  |
|-----------------|------------|----------------------------------------------|
| shell           | powershell | Target shell (bash, powershell, zsh)         |
| dry_run         | true       | Preview changes without applying them        |
| verbose         | false      | Show detailed output during execution        |

## Notes

- Always prefer a dry-run first to verify behavior before applying changes.
- Keep scripts idempotent where possible so they can be safely re-run.
- See `resources/` for reusable script templates and CI/CD pipeline examples.
