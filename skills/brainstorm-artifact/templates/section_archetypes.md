# Section Archetypes

Pre-built section templates for the four common project shapes Marcus works with. Pull the archetype that matches the project, then adapt question text and options to the specific work.

---

## Archetype 1: Platform or Product Build

Use this for SaaS apps, multi-component web platforms, AI agent products. Examples from Marcus's portfolio: Bob Career Ops, SentinelMail, VetAssist, AgentForge.

Recommended sections:

```
## POSITIONING AND AUDIENCE
- Who is the primary user
- What problem does this solve that no existing tool does well
- What audiences should the MVP target versus defer
- How should we frame the product to avoid scope creep into adjacent legal or regulated territory

## TECH STACK AND ARCHITECTURE
- Backend framework and runtime
- Data store choice with reasoning about schema rigidity
- Frontend framework and component strategy
- Authentication provider and session model

## AI AND ML ENGINE
- Which models or APIs power core intelligence
- Self-hosted versus managed trade-offs
- Latency and cost budget per request
- Privacy and PII handling at the model layer

## MVP FEATURE LOCK
- Which features ship in MVP
- Which features are explicitly deferred to phase two
- What is the smallest demonstrable end-to-end flow
- What is the hard ship criteria

## COMPLIANCE AND SECURITY
- Accessibility standard target
- AI disclosure and regulatory requirements
- Cryptography and FIPS posture
- Crisis or content gates required before AI responds
- PII storage and logging policy

## FUNDING AND INFRASTRUCTURE
- Hosting credit sources, especially GitHub Student Pack and Azure
- Foundation grant pathways relevant to audience
- Nonprofit or LLC formation decisions

## LAUNCH CHANNEL AND VOICE
- Primary channel for MVP launch
- Founder story versus data story
- Beta cohort size and selection
```

---

## Archetype 2: Game Development Feature

Use this for Unreal Engine 5 features, gameplay systems, AI behavior, level design work. Examples from Marcus's portfolio: Quidditch AI Flight System, IslandEscape survival, MCP Command Panel.

Recommended sections:

```
## GAMEPLAY LOOP AND PLAYER INTENT
- What is the player trying to accomplish
- What is the failure state
- How is the loop introduced to the player
- What is the time-to-fun budget

## AI AND BEHAVIOR SYSTEMS
- Behavior Tree, State Tree, or custom architecture
- Blackboard key strategy
- C plus plus authority versus Blueprint authority split
- Debug visualization requirements

## DATA MODEL AND COMPONENTS
- ActorComponent breakdown
- Data Asset versus Data Table choice
- Save and load contract
- Network replication scope

## UI AND FEEDBACK
- HUD elements required
- Diegetic versus non-diegetic UI mix
- Tooltip and dialogue system
- Audio and haptic feedback hooks

## PERFORMANCE BUDGET
- Target frame rate and platform
- Tick frequency for AI and gameplay components
- Memory budget per gameplay system

## POLISH AND GAME FEEL
- Camera behavior
- Animation and transition timing
- Visual effects budget

## TESTING AND VALIDATION
- Automated test coverage targets
- Playtest scenarios
- Build verification gates before submission
```

---

## Archetype 3: Backend System or API

Use this for FastAPI services, microservices, internal tools, MCP servers. Examples from Marcus's portfolio: SentinelMail backend, MCP Command Panel server, Bob Phase 2 ML pipeline.

Recommended sections:

```
## API SURFACE AND CONTRACT
- REST, GraphQL, gRPC, or MCP protocol
- Versioning strategy
- Request and response envelope shape
- Error code taxonomy

## DATA MODEL AND PERSISTENCE
- Primary data store and rationale
- Caching layer and invalidation strategy
- Migration tooling
- Backup and restore plan

## AUTHENTICATION AND AUTHORIZATION
- Identity provider
- Token format and lifetime
- Scope or permission model
- Multi-tenancy posture

## OBSERVABILITY
- Structured logging library and format
- Metrics provider
- Distributed tracing
- Alert thresholds

## DEPLOYMENT AND INFRASTRUCTURE
- Container or serverless choice
- Cloud provider and credit source
- CI and CD pipeline
- Environment promotion path

## FAILURE MODES
- Retry strategy
- Circuit breaker thresholds
- Graceful degradation paths
- Disaster recovery plan

## TESTING GATES
- Unit, integration, and end-to-end split
- Coverage targets
- Pre-commit hooks
- Required reviewers
```

---

## Archetype 4: AI Agent or Skill Build

Use this when Marcus is building a Claude Code skill, an AI agent, or an MCP-driven workflow. Examples from Marcus's portfolio: cowork-skills entries, AgentForge knowledge base, Marcus Check-In Protocol.

Recommended sections:

```
## TRIGGER CONDITIONS AND INTENT
- When should this skill or agent activate
- What user phrases or contexts signal a match
- How do we avoid over-triggering on adjacent tasks
- How do we avoid under-triggering when relevant

## TOOL USE AND ACTION SURFACE
- Which tools or APIs the agent can invoke
- Read versus write boundaries
- Confirmation gates before destructive operations
- Rate limit handling

## OUTPUT FORMAT
- Structured artifact, prose, code, or hybrid
- File creation versus in-conversation rendering
- Required headers, metadata, or frontmatter

## SAFETY GATES
- Refusal triggers
- PII detection and scrubbing
- Crisis or harm detection requirements

## MEMORY AND CONTEXT BUDGET
- What persists across sessions
- What gets pulled from prior conversations
- Token budget per invocation
- Context compression strategy

## EVALUATION
- Test prompts and expected behaviors
- Quantitative metrics
- Qualitative review process

## DISTRIBUTION AND PACKAGING
- cowork-skills repo path
- Cross-machine sync via setup script
- Versioning and changelog approach
```
