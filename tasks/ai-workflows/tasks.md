# AI Workflow Task Templates

Reusable task templates for AI agent workflows, design generation, document creation, and automation.

---

## Canva Design Generation Workflow

### Preparation
- [ ] Define design purpose and audience
- [ ] Choose design type (logo, presentation, poster, social media, infographic)
- [ ] Select color palette from design-system (Professional, Startup, Warm, Nature, Luxury)
- [ ] Choose typography pairing appropriate for audience
- [ ] Determine correct dimensions for platform (check dimensions-reference.md)

### Generation
- [ ] Craft detailed query using prompt-patterns.md templates
- [ ] Include: style direction, color guidance, layout intent, audience, text hierarchy
- [ ] Add "generous whitespace and clean layout" to query
- [ ] Generate 4 candidates and present all to user
- [ ] Let user select preferred design

### Quality Review (Before Commit)
- [ ] Run through quality-checklist.md
- [ ] Text readable and no placeholders remaining
- [ ] Color cohesive (max 3 primary + neutrals)
- [ ] Adequate whitespace (20%+)
- [ ] Correct dimensions for target platform
- [ ] Get user approval before committing

### Export
- [ ] Choose correct format (PNG for web, PDF for print, PPTX for editing)
- [ ] Export at correct resolution (72 DPI screen, 300 DPI print)
- [ ] Provide download link to user

---

## Document Generation Workflow (cowork-win)

### Planning
- [ ] Identify document type (report, memo, proposal, spreadsheet, presentation, PDF)
- [ ] Define audience and purpose
- [ ] Outline key sections/content
- [ ] Choose appropriate template from document-designer skill

### Excel Workbook
- [ ] Plan sheet structure (Summary sheet first, then detail sheets)
- [ ] Define headers with units (e.g., "Revenue ($M)")
- [ ] Format data consistently (currency, percentages, dates)
- [ ] Include totals row for numerical columns
- [ ] Verify JSON is valid before calling create_excel

### Word Document
- [ ] Choose template (memo, report, proposal, meeting minutes)
- [ ] Write H1 title, followed by content sections
- [ ] Never put two headings back-to-back
- [ ] Include tables for structured data
- [ ] Keep paragraphs to 3-5 sentences

### PowerPoint Presentation
- [ ] First slide: "title" layout with title + subtitle + date
- [ ] Body slides: "title_and_content" with active titles
- [ ] Follow 6x6 rule (max 6 bullets, max 6 words each)
- [ ] One idea per slide
- [ ] Final slide: summary/CTA/next steps

### PDF Document
- [ ] Start with title heading + intro paragraph
- [ ] Structure as heading/paragraph pairs
- [ ] Keep paragraphs under 100 words
- [ ] Use numbered lists within paragraphs (no bullet support)
- [ ] Proofread before generating (PDF is static)

---

## AI Agent Safety Review

- [ ] Review system prompt for over-agentic language
- [ ] Ensure multi-objective optimization (not single-metric)
- [ ] Verify ethical constraints are present
- [ ] Check for unauthorized initiative risks
- [ ] Confirm credential handling is explicit
- [ ] Test: does the agent stop when it should?
- [ ] Test: does the agent refuse unethical requests?
- [ ] Run red-team evaluation against prompt
- [ ] Document risk score and findings

---

## Prompt Engineering Workflow

### Writing Phase
- [ ] Define the task clearly (what, not how)
- [ ] Specify the role/persona
- [ ] Include constraints and boundaries
- [ ] Add output format requirements
- [ ] Include 1-2 examples if format is specific
- [ ] Set tone and audience

### Testing Phase
- [ ] Test with 3 different inputs (easy, medium, edge case)
- [ ] Check output quality and consistency
- [ ] Verify constraints are respected
- [ ] Test adversarial inputs (what shouldn't work)
- [ ] Iterate on weak points

### Deployment Phase
- [ ] Document the final prompt with version number
- [ ] Record test results
- [ ] Set up monitoring for output quality
- [ ] Plan review schedule (monthly prompt audit)

---

## Multi-Agent Task Decomposition

- [ ] Describe the high-level goal
- [ ] Break into 3-7 independent subtasks
- [ ] For each subtask:
  - [ ] Define clear input and expected output
  - [ ] Identify which tools are needed
  - [ ] Estimate complexity (simple/medium/complex)
  - [ ] Assign to main agent or sub-agent
- [ ] Define execution order (parallel where possible)
- [ ] Define success criteria for the overall task
- [ ] Plan verification step (read back results, cross-check)

---

## MCP Server Integration

- [ ] Identify target service (Canva, Figma, GitHub, Slack, etc.)
- [ ] Check if MCP connector exists (search registry)
- [ ] If exists: connect and test basic operations
- [ ] If not: evaluate building custom MCP server
- [ ] Test tool discovery and invocation
- [ ] Document available tools and their parameters
- [ ] Create skill file for optimized usage patterns
- [ ] Add error handling for connection failures
