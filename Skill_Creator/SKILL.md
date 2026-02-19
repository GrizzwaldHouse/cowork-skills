# Skill Creator - Meta Template

> Use this template as a starting point when creating any new Claude Skill.
> Copy this file into your new skill folder and fill in each section.

---

## Name

<!-- Replace with the skill name. Use a clear, descriptive title. -->
[Skill Name]

## Description

<!-- Summarize what this skill does in 2-3 sentences. -->
[A concise explanation of the skill's purpose and the problem it solves.]

## Prerequisites

<!-- List any tools, accounts, APIs, or dependencies the user needs before using this skill. -->
- [Prerequisite 1]
- [Prerequisite 2]

## Usage

<!-- Describe how to invoke or apply this skill. Include the expected workflow. -->

1. [Step 1 - e.g., Open the project folder]
2. [Step 2 - e.g., Provide the required context to Claude]
3. [Step 3 - e.g., Review and apply the generated output]

### Prompt Pattern

```
[Include a sample prompt or invocation pattern here]
```

## Examples

<!-- Provide at least one concrete example showing input and expected output. -->

### Example 1: [Title]

**Input:**
```
[Sample input or prompt]
```

**Output:**
```
[Expected output or behavior]
```

## Configuration

<!-- List any configurable options, parameters, or environment variables. -->

| Parameter       | Default | Description                        |
|-----------------|---------|------------------------------------|
| [param_name]    | [value] | [What this parameter controls]     |

## File Structure

```
Skill_Name/
  SKILL.md        # This skill definition file
  README.md       # Overview and quick-start guide
  resources/      # Supporting files (prompts, configs, assets)
```

## Notes

<!-- Any additional context, known limitations, or tips. -->
- Skills should use relative paths for portability across machines.
- Keep resource files in the `resources/` subfolder.
- Update `cloud/main_cloud.json` when registering a new skill.
