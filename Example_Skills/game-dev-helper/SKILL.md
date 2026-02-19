# Game Dev Helper

## Name

Game Dev Helper

## Description

A skill for game development tasks including gameplay mechanics, AI behavior trees, level design scripting, shader authoring, and engine-specific workflows. Supports Unreal Engine 5, Unity, and Godot.

## Prerequisites

- A game project in a supported engine (Unreal Engine 5, Unity, or Godot)
- Appropriate SDK and build tools installed
- Familiarity with the engine's core concepts (Actors/Components in UE5, GameObjects in Unity, Nodes in Godot)

## Usage

1. Describe the gameplay feature, system, or bug you need help with.
2. Specify your engine, language (C++, C#, GDScript), and relevant subsystems.
3. Provide existing code, blueprints, or design documents for context.
4. Review the generated implementation and test it in-engine.

### Prompt Pattern

```
I need to implement [gameplay feature] in [engine].
Language: [C++/C#/GDScript/Blueprints]
Subsystem: [AI, Physics, Animation, UI, Networking, etc.]
Current setup: [brief description of existing architecture]
```

## Examples

### Example 1: Simple Enemy Patrol (UE5 C++)

**Input:**
```
I need an enemy AI that patrols between waypoints in Unreal Engine 5.
Language: C++
Subsystem: AI (Behavior Tree + Blackboard)
Current setup: I have an AEnemyCharacter class with a NavMesh in the level.
```

**Output:**
```cpp
// BTTask_PatrolToNextWaypoint.cpp
EBTNodeResult::Type UBTTask_PatrolToNextWaypoint::ExecuteTask(
    UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory)
{
    AAIController* Controller = OwnerComp.GetAIOwner();
    if (!Controller) return EBTNodeResult::Failed;

    UBlackboardComponent* BB = OwnerComp.GetBlackboardComponent();
    int32 Index = BB->GetValueAsInt(PatrolIndexKey.SelectedKeyName);

    AEnemyCharacter* Enemy = Cast<AEnemyCharacter>(Controller->GetPawn());
    if (!Enemy || Enemy->PatrolPoints.Num() == 0)
        return EBTNodeResult::Failed;

    FVector Target = Enemy->PatrolPoints[Index % Enemy->PatrolPoints.Num()];
    Controller->MoveToLocation(Target);

    BB->SetValueAsInt(PatrolIndexKey.SelectedKeyName, Index + 1);
    return EBTNodeResult::InProgress;
}
```

## Configuration

| Parameter       | Default | Description                                 |
|-----------------|---------|---------------------------------------------|
| engine          | ue5     | Target game engine (ue5, unity, godot)      |
| language        | cpp     | Programming language                        |
| subsystem       | ai      | Engine subsystem focus area                 |

## Notes

- For UE5 C++ code, follow the engine's naming conventions (F, U, A prefixes).
- Use `UPROPERTY`/`UFUNCTION` macros where appropriate for UE5.
- See `resources/` for reusable behavior tree templates and utility snippets.
