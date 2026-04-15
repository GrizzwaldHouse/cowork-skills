# Comment-Driven Development (CDD)

## The Core Idea

Before writing ANY implementation code in a function, write step-by-step
comments that describe what the function will do and WHY each step exists.

These comments serve three critical purposes:
1. **Recovery contract** — If a session drops mid-implementation, the next
   agent reads these comments and knows exactly what remains
2. **Intent verification** — After implementing, compare code against comments
   to catch divergence between design and implementation
3. **Architecture enforcement** — Writing the steps first forces you to think
   through the design before you start typing code

## Format

```
// PURPOSE: [Why this function exists in the system architecture]
// STEP 1: [What to do and WHY this step is necessary]
// STEP 2: [Next action and WHY]
// STEP 3: [Continue pattern...]
```

## Rules

1. Comments explain WHY, never WHAT
   - BAD:  `// Loop through the array`
   - GOOD: `// Iterate registered listeners to broadcast the state change event`

2. Each step should map to 3-15 lines of implementation code
   - If a step needs more than 15 lines, break it into sub-steps
   - If a step needs fewer than 3 lines, consider merging with adjacent step

3. Steps should be independently verifiable
   - After implementing Step N, you should be able to confirm it works
     before moving to Step N+1

4. Step comments stay in the code permanently
   - They are documentation, not scaffolding
   - Future developers benefit from seeing the reasoning

## Language-Specific Examples

### C++ (Unreal Engine)
```cpp
void USpawnManager::ExecuteBatchSpawn(const FBatchSpawnRequest& Request)
{
    // PURPOSE: Process a batch spawn request without blocking the game thread.
    //          Uses async tasks to distribute work across available cores while
    //          maintaining proper actor registration order.

    // STEP 1: Validate the spawn request against configured limits
    //         (fail fast with delegate broadcast if request exceeds budget)

    // STEP 2: Partition the request into thread-safe chunks
    //         (chunk size from config, not hardcoded — allows tuning per hardware)

    // STEP 3: Dispatch each chunk as an async task via the engine's task graph
    //         (FAsyncTask ensures proper lifecycle management)

    // STEP 4: Collect results on the game thread via delegate callback
    //         (never touch UObjects from background threads)

    // STEP 5: Register spawned actors with the scene memory system
    //         (broadcast OnBatchComplete for UI progress update)
}
```

### C# (.NET)
```csharp
public async Task<SpawnResult> ProcessSpawnRequestAsync(SpawnRequest request)
{
    // PURPOSE: Orchestrate a spawn operation through validation, execution,
    //          and notification phases. Each phase is a separate concern
    //          handled by injected services.

    // STEP 1: Validate request through the injected ISpawnValidator
    //         (throws TypedValidationException on failure — callers handle)

    // STEP 2: Check spatial index for collision via ISceneMemory
    //         (returns alternative position if collision detected)

    // STEP 3: Execute spawn through ISpawnExecutor
    //         (executor abstracts the actual engine API — testable)

    // STEP 4: Register result in scene memory for future context resolution
    //         (enables "make IT bigger" style follow-up commands)

    // STEP 5: Broadcast SpawnCompleted event via IEventBus
    //         (UI, logging, and analytics subscribe independently)
}
```

### Python
```python
async def process_natural_language_command(self, raw_input: str) -> CommandResult:
    """Decompose a natural language command into atomic actions and execute them."""
    
    # PURPOSE: Bridge between human-readable commands and the atomic action
    #          library. Uses the LLM to understand intent, then maps to
    #          concrete operations without the LLM needing to know engine details.
    
    # STEP 1: Sanitize and validate raw input
    #         (reject empty/too-long inputs before wasting API tokens)
    
    # STEP 2: Query scene memory for context resolution
    #         (resolve pronouns like "it" and "that" to concrete actor IDs)
    
    # STEP 3: Send enriched prompt to LLM for intent decomposition
    #         (prompt includes scene context + available atomic actions)
    
    # STEP 4: Parse LLM response into ActionPlan dataclass
    #         (typed parsing catches malformed responses before execution)
    
    # STEP 5: Execute action plan through the batch spawner
    #         (spawner handles threading, collision, and progress)
    
    # STEP 6: Update scene memory with results
    #         (future commands can reference what was just created)
```

## Recovery Detection

The `detect_interruption.py` script looks for CDD patterns to find where
work was interrupted. Specifically:

- **COMMENTS_ONLY**: Step-comments exist but no implementation code follows them.
  This is the highest-confidence interruption signal — the agent wrote the plan
  but was cut off before implementing it.

- **PARTIAL_IMPL**: Some steps have implementation, others don't. The agent was
  mid-implementation when the session dropped.

- **EMPTY_BODY**: Function signature exists with an empty body and no step-comments.
  The agent may have been planning to implement this function next.

## Integration with Supervisor Review

The supervisor specifically checks comment-code alignment:
- Does each step-comment have corresponding implementation beneath it?
- Does the implementation match what the comment describes?
- If they disagree, was the COMMENT updated (not just the code)?

A function that compiles and runs correctly but has outdated step-comments
will fail supervisor review. The comments are the specification — they
must stay current.
