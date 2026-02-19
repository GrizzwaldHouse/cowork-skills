# Documentation & Blog Generator

## Name

Documentation & Blog Generator

## Description

A skill for generating technical documentation, blog posts, changelogs, and developer guides. It produces well-structured Markdown content from code, commit history, or topic descriptions.

## Prerequisites

- A project or topic to document
- Access to source code or API definitions if generating reference docs
- Markdown rendering environment (GitHub, static site generator, etc.)

## Usage

1. Specify the type of content you need (docs, blog post, changelog, tutorial).
2. Provide source material -- code files, API schemas, commit logs, or a topic outline.
3. Set tone and audience (developer docs, end-user guide, marketing blog, etc.).
4. Review and publish the generated content.

### Prompt Pattern

```
Generate a [content type] about [topic].
Source material: [code, schema, commits, or outline]
Audience: [developers, end users, stakeholders]
Tone: [technical, conversational, formal]
Format: [Markdown, HTML, RST]
```

## Examples

### Example 1: API Endpoint Documentation

**Input:**
```
Generate API documentation for the /users endpoint.
Source material: Express route handler in routes/users.js
Audience: developers integrating with the API
Tone: technical
Format: Markdown
```

**Output:**
```markdown
## POST /users

Create a new user account.

### Request Body

| Field    | Type   | Required | Description          |
|----------|--------|----------|----------------------|
| email    | string | yes      | Valid email address   |
| password | string | yes      | Minimum 8 characters |

### Response

**201 Created**
​```json
{ "token": "eyJhbGci..." }
​```

**409 Conflict** -- Email already registered.
```

## Configuration

| Parameter       | Default    | Description                                   |
|-----------------|------------|-----------------------------------------------|
| content_type    | docs       | Type of content (docs, blog, changelog, tutorial) |
| tone            | technical  | Writing tone                                  |
| format          | markdown   | Output format                                 |
| include_toc     | true       | Generate a table of contents                  |

## Notes

- For changelogs, provide a range of git commits or a version tag.
- Blog posts benefit from an outline or key points before generation.
- See `resources/` for content templates and style guides.
