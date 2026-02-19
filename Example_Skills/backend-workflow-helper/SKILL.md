# Backend Workflow Helper

## Name

Backend Workflow Helper

## Description

A skill for designing, implementing, and debugging back-end services and workflows. It covers API design, database queries, authentication flows, background jobs, and service-to-service communication patterns.

## Prerequisites

- A back-end project in a supported language/framework (Node.js/Express, Python/FastAPI, C#/.NET, Go, etc.)
- Database access if working with data layers (PostgreSQL, MongoDB, SQLite, etc.)
- Basic understanding of REST or GraphQL API conventions

## Usage

1. Describe the back-end task or workflow you need help with.
2. Specify the language, framework, and any relevant infrastructure (database, message queue, etc.).
3. Provide existing code or schema if modifying an existing system.
4. Review the generated implementation and integrate it.

### Prompt Pattern

```
I need to implement [feature/workflow] in my [language/framework] project.
Database: [type and version]
Current architecture: [monolith/microservices/serverless]
Requirements: [list specific requirements]
```

## Examples

### Example 1: REST Endpoint with Validation

**Input:**
```
I need a POST endpoint for creating user accounts in my Express.js API.
Database: PostgreSQL with Prisma ORM
Requirements: Email validation, password hashing, duplicate check, return JWT on success.
```

**Output:**
```javascript
router.post('/users', async (req, res) => {
  const { email, password } = req.body;

  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Invalid email format' });
  }

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    return res.status(409).json({ error: 'Email already registered' });
  }

  const hashedPassword = await bcrypt.hash(password, 12);
  const user = await prisma.user.create({
    data: { email, password: hashedPassword },
  });

  const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET);
  return res.status(201).json({ token });
});
```

## Configuration

| Parameter       | Default    | Description                                |
|-----------------|------------|--------------------------------------------|
| language        | javascript | Target programming language                |
| framework       | express    | Back-end framework                         |
| auth_pattern    | jwt        | Authentication strategy (jwt, session, oauth) |
| error_style     | json       | Error response format (json, problem+json) |

## Notes

- Always validate inputs at the API boundary.
- Follow the project's existing error-handling patterns when they exist.
- See `resources/` for reusable middleware snippets and schema examples.
