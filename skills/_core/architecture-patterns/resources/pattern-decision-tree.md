# Pattern Decision Tree

## When to Use Which Pattern

### "System A needs to know when System B's state changes"
**Use: Observer Pattern**
- System B broadcasts an event
- System A subscribes to that event
- System B never knows System A exists

### "I need to swap out one implementation for another"
**Use: Interface-Driven Design + Repository Pattern**
- Define an interface for the contract
- Implement concrete versions
- Inject the implementation via constructor

### "This class is getting too big / doing too many things"
**Use: Component Composition + Separation of Concerns**
- Extract each responsibility into its own component/service
- Compose them together via dependency injection
- Each piece should be describable in one sentence

### "Non-developers need to change behavior without code changes"
**Use: Data-Driven Design**
- Move the configurable values to config files, data assets, or environment variables
- Logic reads configuration at runtime
- Changes require a config update, not a code deploy

### "I'm building a deep inheritance hierarchy"
**Use: Composition Over Inheritance**
- Extract shared behavior into components/mixins/traits
- Compose objects from small, focused pieces
- Only use inheritance for genuine "is-a" relationships with substantial shared behavior

### "Multiple places in the code do the same thing slightly differently"
**Use: Strategy Pattern (via Interface-Driven Design)**
- Define a common interface for the varying behavior
- Implement each variant as a separate strategy
- Select strategy via configuration or injection

## Pattern Compatibility Matrix

| Pattern | Works Well With | Avoid Combining With |
|---------|----------------|---------------------|
| Observer | All patterns | Polling (by definition) |
| Composition | Interface-driven, Data-driven | Deep inheritance |
| Interface-driven | Repository, DI, Strategy | Concrete dependencies |
| Data-driven | Observer (config change events), Repository | Hardcoded values |
| Repository | Interface-driven, DI | Direct DB calls in business logic |
| Separation of Concerns | All patterns | God objects |

## Quick Decision: "Should I Create an Abstraction?"

1. Is this behavior used in more than one place? -> Yes -> Abstract it
2. Will this behavior likely change independently? -> Yes -> Abstract it
3. Do I need to test this in isolation? -> Yes -> Abstract it
4. Is this a one-time operation with no variation? -> Inline it (no abstraction needed)
5. Am I guessing about future requirements? -> Don't abstract yet (YAGNI)
