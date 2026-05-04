# Benchmark Prompt Templates

Standard prompts for evaluating Ollama models. Each prompt tests a specific capability.

---

## BM-001: Morning Brief Generation

**Task Type:** morning_brief
**Expected:** Markdown with sections, actionable items, professional tone

```
System: You are a daily briefing assistant for a freelance developer and game developer.
Generate a concise morning brief covering: today's priorities, pending tasks, and one motivational insight.
Keep it under 300 words. Use markdown headers and bullet points.

User: Generate my morning brief. I'm a freelance developer working on a portfolio website (Next.js 15),
an AI companion project (Node.js), and a Quidditch game in Unreal Engine 5. I have 2 hours available today.
```

**Scoring:** Structure (headers present), actionable (specific next steps), concise (under 300 words), tone (professional but friendly)

---

## BM-002: Code Review

**Task Type:** code_review
**Expected:** Line-specific feedback, severity ratings, improvement suggestions

```
System: You are a senior code reviewer. Review code for: correctness, security, performance,
and adherence to clean code principles. Provide line-specific feedback with severity
(CRITICAL/HIGH/MEDIUM/LOW).

User: Review this JavaScript function:

function getUser(id) {
  var data = JSON.parse(fs.readFileSync('users.json'));
  for (var i = 0; i < data.length; i++) {
    if (data[i].id == id) return data[i];
  }
  return null;
}
```

**Expected Issues:** Sync I/O, var usage, loose equality, no error handling, no caching, reads entire file every call

---

## BM-003: Email Parsing

**Task Type:** email_parsing
**Expected:** Clean JSON extraction

```
System: Extract structured data from freelance platform emails. Return valid JSON only.

User: Extract order details:
"New order from TechStartup_Mike! Project: Build a REST API for their inventory system.
Budget: $500. Deadline: 2 weeks. Requirements: Node.js, PostgreSQL, authentication, Swagger docs.
Mike says: 'Need it production-ready with tests.'"
```

**Expected Output:**
```json
{"client":"TechStartup_Mike","project":"REST API for inventory system","budget":500,"deadline":"2 weeks","tech":["Node.js","PostgreSQL"],"requirements":["authentication","Swagger docs","production-ready","tests"]}
```

---

## BM-004: PR Analysis

**Task Type:** pr_analysis
**Expected:** Risk assessment, specific suggestions, clear approve/reject

```
System: Analyze this pull request diff. Assess risk level (LOW/MEDIUM/HIGH/CRITICAL).
Identify bugs, security issues, and improvements. Give a clear APPROVE or REQUEST CHANGES verdict.

User: PR diff:
- Adds new /api/admin/delete-user endpoint
- Uses req.query.userId without validation
- No authentication middleware on route
- Deletes user with: await db.query(`DELETE FROM users WHERE id = ${userId}`)
- No audit logging
```

**Expected Issues:** SQL injection, missing auth, no input validation, no audit trail — CRITICAL risk

---

## BM-005: Complex Reasoning

**Task Type:** complex_reasoning
**Expected:** Architecture diagram, tradeoffs, clear recommendation

```
System: You are a senior software architect. Design systems with clear tradeoffs and justifications.

User: Design a plugin marketplace system for a SaaS platform. Requirements: paid and free plugins,
revenue split with developers, sandboxed execution, version control, security scanning.
Budget is limited — suggest an MVP approach.
```

**Scoring:** Completeness (all requirements addressed), feasibility (MVP-scoped), security (sandbox design), business logic (revenue split)

---

## BM-006: Client Communication

**Task Type:** client_communication
**Expected:** Professional email, appropriate tone, clear next steps

```
System: Draft professional client communications for a freelance developer.
Tone: friendly but professional. Always include clear next steps.

User: Draft a response to a client who is asking for a 50% scope increase
with no budget change. The original project was a REST API for $500,
now they want a frontend dashboard too.
```

**Scoring:** Tone (professional, not confrontational), clear scope explanation, proposed options (with costs), next steps

---

## BM-007: Autocomplete

**Task Type:** autocomplete
**Expected:** Valid code completion, correct types, idiomatic

```
Complete this function. Return only the code, no explanation.

export function calculateProjectScore(project) {
  const weights = { completion: 0.3, quality: 0.25, onTime: 0.2, clientSatisfaction: 0.25 };
```

**Scoring:** Correct math, handles edge cases (null/undefined), returns number, clean code

---

## BM-008: Coding Standards Compliance

**Task Type:** coding_standards
**Expected:** Refactored code that passes all standard checks

```
System: Refactor the following code to follow clean architecture principles:
- No magic numbers
- Dependency injection
- Separation of concerns
- No global mutable state
- Typed error handling
- ES Modules (import/export)

User:
let users = [];
const TAX = 0.08;

function addUser(name, salary) {
  users.push({ name, salary, tax: salary * TAX, net: salary - (salary * TAX) });
}

function getHighEarners() {
  return users.filter(u => u.salary > 100000);
}

module.exports = { addUser, getHighEarners };
```

**Expected:** Named constants, injected store, ES Module exports, separated tax calculation, threshold as parameter
