---
name: deep-research
description: "Conduct thorough, multi-source research on any topic and produce detailed, cited reports. Use when the user asks for deep research, literature review, competitive analysis, technology evaluation, market research, or any task requiring comprehensive investigation across multiple sources. Trigger when the user says 'research this', 'deep dive into', 'investigate', 'analyze the landscape', 'compare options for', 'what are the best approaches to', or needs a thorough understanding before making a decision."
---

# Deep Research Skill

Conduct autonomous, thorough research using a structured planner-executor-publisher pipeline. Produce detailed, factual, and cited reports.

## Research Pipeline

### Phase 1: Planning

Before gathering information, create a research plan:

1. **Clarify the question**: What specific question(s) need answering?
2. **Identify sub-questions**: Break the main question into 3-7 specific sub-questions
3. **Determine source strategy**: What types of sources are needed?
   - Academic/technical documentation
   - Official project repositories
   - Community discussions and benchmarks
   - Industry reports and case studies
4. **Set scope boundaries**: What's in/out of scope? Time constraints?

```markdown
## Research Plan
**Main Question**: [The core question]
**Sub-Questions**:
1. [Specific aspect 1]
2. [Specific aspect 2]
3. [Specific aspect 3]
**Source Strategy**: [Types of sources to prioritize]
**Scope**: [What's included/excluded]
```

### Phase 2: Execution (Parallelized)

For each sub-question, gather information from multiple sources:

1. **Search broadly**: Use web search for initial landscape mapping
2. **Go deep**: Follow promising leads to primary sources
3. **Cross-reference**: Verify claims across independent sources
4. **Track sources**: Record URL, title, date, and key findings for every source
5. **Identify gaps**: Note what information is missing or contradictory

#### Source Tracking Format
```markdown
### Source: [Title]
- **URL**: [link]
- **Date**: [publication date]
- **Credibility**: [high/medium/low + reasoning]
- **Key Findings**: [bullet points]
- **Relevance**: [how this answers which sub-question]
```

#### Parallel Research Pattern
When subagents are available, spawn one per sub-question:
- Each agent researches independently
- Results are aggregated in the publisher phase
- Reduces total research time proportionally

### Phase 3: Synthesis & Analysis

After gathering raw information:

1. **Identify patterns**: What themes emerge across sources?
2. **Resolve conflicts**: Where sources disagree, investigate why
3. **Assess confidence**: Rate confidence level for each finding
4. **Draw conclusions**: What does the evidence support?
5. **Identify remaining unknowns**: What couldn't be determined?

### Phase 4: Publication

Produce a structured research report:

```markdown
# [Research Topic] - Deep Research Report

## Executive Summary
[2-3 paragraph overview of key findings]

## Key Findings
1. **[Finding 1]**: [Description with source citations]
2. **[Finding 2]**: [Description with source citations]
3. **[Finding 3]**: [Description with source citations]

## Detailed Analysis

### [Sub-Question 1]
[Thorough analysis with citations]

### [Sub-Question 2]
[Thorough analysis with citations]

## Comparison Matrix (if applicable)
| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| [Factor]  | [Rating] | [Rating] | [Rating] |

## Recommendations
[Actionable recommendations based on findings]

## Confidence Assessment
- **High confidence**: [Findings well-supported by multiple sources]
- **Medium confidence**: [Findings supported but with caveats]
- **Low confidence**: [Findings based on limited or conflicting data]

## Sources
1. [Author/Org]. "[Title]." [Date]. [URL]
2. ...

## Methodology
[How research was conducted, sources used, limitations]
```

## Research Quality Standards

### Source Evaluation
- **Primary sources** (official docs, original research) > secondary sources
- **Recent sources** preferred unless historical context is needed
- **Multiple independent sources** required for key claims
- **Credibility assessment** for each source (author expertise, publication quality)

### Bias Mitigation
- Seek sources from multiple perspectives
- Note when a source has potential conflicts of interest
- Distinguish facts from opinions
- Present counterarguments for contested claims

### Citation Standards
- Every factual claim must cite at least one source
- Include publication date for time-sensitive information
- Use inline citations `[Source Name]` with full references at end
- Note when information couldn't be independently verified

## Specialized Research Types

### Technology Evaluation
Focus on: maturity, community size, performance benchmarks, learning curve, ecosystem, licensing, long-term viability

### Competitive Analysis
Focus on: feature comparison, pricing, market positioning, strengths/weaknesses, customer sentiment, market share

### Architecture Decision
Focus on: scalability, maintainability, team expertise, migration cost, vendor lock-in, performance characteristics

### Market Research
Focus on: market size, growth trends, customer segments, pricing models, competitive landscape, entry barriers
