# Task: Spawning System with Channel-Based Activation

## Purpose
Implement a reusable actor spawner with weighted random selection, scene component spawn points, and FName-based channel activation. Enables designers to create enemy waves, loot drops, or reinforcement spawns without C++ changes.

## Prerequisites
- Unreal Engine 5.4 C++ project
- Understanding of USceneComponent hierarchy
- Familiarity with FName for designer-expandable systems
- Knowledge of TSubclassOf<> for class references
- UE5 weighted random selection patterns

## Source Code Reference
**Island Escape (BaseGame/END2507):**
- `Source/END2507/Code/Actors/BaseSpawner.h` (lines 1-80)
- `Source/END2507/Code/Actors/BaseSpawner.cpp` (lines 1-200)

**WizardJam Quidditch:**
- Channel-based activation pattern from elemental wall matching

**Key Pattern Elements:**
- FName channels for designer configuration
- Weighted spawn tables (TMap<TSubclassOf<>, float>)
- TArray<USceneComponent*> for spawn point hierarchy
- GameMode registration for population tracking

## Implementation Steps

### Step 1: Create Spawner Actor Header
```cpp
// BaseSpawner.h
// Developer: [Your Name]
// Date: [YYYY-MM-DD]
// Purpose: Reusable spawner with channel-based activation and weighted spawn tables
// Usage: Place in level, configure SpawnTables and Channels in Blueprint

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BaseSpawner.generated.h"

// Forward declarations
class USceneComponent;
class UBoxComponent;

UCLASS()
class YOURPROJECT_API ABaseSpawner : public AActor
{
    GENERATED_BODY()

public:
    ABaseSpawner();

    // ====================================================================
    // PUBLIC API
    // ====================================================================

    // Trigger spawn via channel name
    UFUNCTION(BlueprintCallable, Category = "Spawner")
    void ActivateChannel(FName ChannelName);

    // Spawn specific actor class at random spawn point
    UFUNCTION(BlueprintCallable, Category = "Spawner")
    AActor* SpawnActorAtPoint(TSubclassOf<AActor> ActorClass, int32 SpawnPointIndex = -1);

    // Query active spawns
    UFUNCTION(BlueprintPure, Category = "Spawner")
    int32 GetActiveSpawnCount() const { return ActiveSpawns.Num(); }

    UFUNCTION(BlueprintPure, Category = "Spawner")
    int32 GetMaxPopulation() const { return MaxPopulation; }

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    // ====================================================================
    // SPAWN TABLE LOGIC
    // ====================================================================

    // Select actor class from weighted table
    TSubclassOf<AActor> SelectWeightedActorClass(FName ChannelName) const;

    // Get random spawn point index
    int32 GetRandomSpawnPointIndex() const;

    // Handle spawned actor death/destruction
    UFUNCTION()
    void HandleSpawnDestroyed(AActor* DestroyedActor);

    // ====================================================================
    // COMPONENTS
    // ====================================================================

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components",
        meta = (AllowPrivateAccess = "true"))
    USceneComponent* RootSceneComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components",
        meta = (AllowPrivateAccess = "true"))
    UBoxComponent* SpawnerVolume;

    // ====================================================================
    // SPAWN CONFIGURATION
    // ====================================================================

    // Spawn tables per channel: ChannelName -> { ActorClass: Weight }
    // Example: "EnemyWave1" -> { BP_Zombie_C: 5.0, BP_FastZombie_C: 2.0 }
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spawner|Configuration",
        meta = (AllowPrivateAccess = "true"))
    TMap<FName, TMap<TSubclassOf<AActor>, float>> SpawnTables;

    // Spawn point scene components (children of this actor)
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Spawner|Configuration",
        meta = (AllowPrivateAccess = "true"))
    TArray<USceneComponent*> SpawnPoints;

    // Maximum simultaneous spawns from this spawner
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spawner|Configuration",
        meta = (AllowPrivateAccess = "true", ClampMin = "1"))
    int32 MaxPopulation;

    // Spawn vertical offset (to avoid spawning inside floor)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Spawner|Configuration",
        meta = (AllowPrivateAccess = "true"))
    float SpawnHeightOffset;

    // ====================================================================
    // RUNTIME STATE
    // ====================================================================

    // Currently active spawns (for population tracking)
    UPROPERTY()
    TArray<TWeakObjectPtr<AActor>> ActiveSpawns;
};
```

### Step 2: Implement Constructor and Setup
```cpp
// BaseSpawner.cpp

#include "BaseSpawner.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"

ABaseSpawner::ABaseSpawner()
    : MaxPopulation(10)
    , SpawnHeightOffset(100.0f)
{
    PrimaryActorTick.bCanEverTick = false;

    // Root scene component
    RootSceneComponent = CreateDefaultSubobject<USceneComponent>(TEXT("RootScene"));
    RootComponent = RootSceneComponent;

    // Visual volume for editor (non-collision)
    SpawnerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("SpawnerVolume"));
    SpawnerVolume->SetupAttachment(RootComponent);
    SpawnerVolume->SetBoxExtent(FVector(500.0f, 500.0f, 250.0f));
    SpawnerVolume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SpawnerVolume->ShapeColor = FColor::Orange;
}

void ABaseSpawner::BeginPlay()
{
    Super::BeginPlay();

    // Validate configuration
    if (SpawnTables.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("[%s] No spawn tables configured!"), *GetName());
    }

    if (SpawnPoints.Num() == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("[%s] No spawn points configured! Using actor location."),
            *GetName());
    }

    UE_LOG(LogTemp, Log, TEXT("[%s] BaseSpawner ready. Channels: %d, SpawnPoints: %d, MaxPop: %d"),
        *GetName(), SpawnTables.Num(), SpawnPoints.Num(), MaxPopulation);
}

void ABaseSpawner::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    // Clean up weak pointer tracking
    ActiveSpawns.Empty();

    Super::EndPlay(EndPlayReason);
}
```

### Step 3: Implement Channel Activation
```cpp
void ABaseSpawner::ActivateChannel(FName ChannelName)
{
    // Check population limit
    if (ActiveSpawns.Num() >= MaxPopulation)
    {
        UE_LOG(LogTemp, Warning, TEXT("[%s] Cannot spawn - max population reached (%d/%d)"),
            *GetName(), ActiveSpawns.Num(), MaxPopulation);
        return;
    }

    // Validate channel exists
    if (!SpawnTables.Contains(ChannelName))
    {
        UE_LOG(LogTemp, Error, TEXT("[%s] Channel '%s' not found in SpawnTables!"),
            *GetName(), *ChannelName.ToString());
        return;
    }

    // Select actor class from weighted table
    TSubclassOf<AActor> ActorClass = SelectWeightedActorClass(ChannelName);
    if (!ActorClass)
    {
        UE_LOG(LogTemp, Error, TEXT("[%s] Failed to select actor class for channel '%s'"),
            *GetName(), *ChannelName.ToString());
        return;
    }

    // Spawn actor
    AActor* SpawnedActor = SpawnActorAtPoint(ActorClass);
    if (SpawnedActor)
    {
        UE_LOG(LogTemp, Log, TEXT("[%s] Spawned [%s] via channel '%s'. Population: %d/%d"),
            *GetName(),
            *SpawnedActor->GetName(),
            *ChannelName.ToString(),
            ActiveSpawns.Num(),
            MaxPopulation);
    }
}
```

### Step 4: Implement Weighted Selection
```cpp
TSubclassOf<AActor> ABaseSpawner::SelectWeightedActorClass(FName ChannelName) const
{
    const TMap<TSubclassOf<AActor>, float>* WeightTable = SpawnTables.Find(ChannelName);
    if (!WeightTable || WeightTable->Num() == 0)
    {
        return nullptr;
    }

    // Calculate total weight
    float TotalWeight = 0.0f;
    for (const auto& Entry : *WeightTable)
    {
        TotalWeight += Entry.Value;
    }

    if (TotalWeight <= 0.0f)
    {
        UE_LOG(LogTemp, Error, TEXT("[%s] Channel '%s' has zero total weight!"),
            *GetName(), *ChannelName.ToString());
        return nullptr;
    }

    // Random selection
    float RandomValue = FMath::FRandRange(0.0f, TotalWeight);
    float AccumulatedWeight = 0.0f;

    for (const auto& Entry : *WeightTable)
    {
        AccumulatedWeight += Entry.Value;
        if (RandomValue <= AccumulatedWeight)
        {
            return Entry.Key;  // Selected class
        }
    }

    // Fallback (should never reach here)
    return WeightTable->begin()->Key;
}
```

### Step 5: Implement Spawn Logic
```cpp
AActor* ABaseSpawner::SpawnActorAtPoint(TSubclassOf<AActor> ActorClass, int32 SpawnPointIndex)
{
    if (!ActorClass)
    {
        UE_LOG(LogTemp, Error, TEXT("[%s] Cannot spawn - ActorClass is null"), *GetName());
        return nullptr;
    }

    // Determine spawn transform
    FVector SpawnLocation;
    FRotator SpawnRotation = GetActorRotation();

    if (SpawnPointIndex < 0)
    {
        // Random spawn point
        SpawnPointIndex = GetRandomSpawnPointIndex();
    }

    if (SpawnPoints.IsValidIndex(SpawnPointIndex) && SpawnPoints[SpawnPointIndex])
    {
        // Use spawn point transform
        SpawnLocation = SpawnPoints[SpawnPointIndex]->GetComponentLocation();
        SpawnRotation = SpawnPoints[SpawnPointIndex]->GetComponentRotation();
    }
    else
    {
        // Fallback to spawner location
        SpawnLocation = GetActorLocation();
    }

    // Apply height offset
    SpawnLocation.Z += SpawnHeightOffset;

    // Spawn actor
    FActorSpawnParameters SpawnParams;
    SpawnParams.Owner = this;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

    AActor* SpawnedActor = GetWorld()->SpawnActor<AActor>(ActorClass, SpawnLocation, SpawnRotation, SpawnParams);

    if (SpawnedActor)
    {
        // Track spawned actor
        ActiveSpawns.Add(SpawnedActor);

        // Bind destruction delegate for cleanup
        SpawnedActor->OnDestroyed.AddDynamic(this, &ThisClass::HandleSpawnDestroyed);

        UE_LOG(LogTemp, Log, TEXT("[%s] Spawned [%s] at point %d. Location: %s"),
            *GetName(),
            *SpawnedActor->GetName(),
            SpawnPointIndex,
            *SpawnLocation.ToString());
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[%s] Failed to spawn actor class [%s]"),
            *GetName(),
            *ActorClass->GetName());
    }

    return SpawnedActor;
}

int32 ABaseSpawner::GetRandomSpawnPointIndex() const
{
    if (SpawnPoints.Num() == 0)
    {
        return -1;  // No spawn points
    }

    return FMath::RandRange(0, SpawnPoints.Num() - 1);
}
```

### Step 6: Implement Population Tracking
```cpp
void ABaseSpawner::HandleSpawnDestroyed(AActor* DestroyedActor)
{
    if (!DestroyedActor)
    {
        return;
    }

    // Remove from active spawns
    ActiveSpawns.RemoveAll([DestroyedActor](const TWeakObjectPtr<AActor>& WeakPtr)
    {
        return !WeakPtr.IsValid() || WeakPtr.Get() == DestroyedActor;
    });

    UE_LOG(LogTemp, Log, TEXT("[%s] Spawn destroyed: [%s]. Population: %d/%d"),
        *GetName(),
        *DestroyedActor->GetName(),
        ActiveSpawns.Num(),
        MaxPopulation);
}
```

## Delegate Signatures

### Built-In AActor::OnDestroyed
```cpp
// Already declared in Engine - we bind to this
DECLARE_DYNAMIC_MULTICAST_SPARSE_DELEGATE_OneParam(FActorDestroyedSignature, AActor, OnDestroyed, AActor*, DestroyedActor);
```

**Usage in Spawner:**
```cpp
SpawnedActor->OnDestroyed.AddDynamic(this, &ABaseSpawner::HandleSpawnDestroyed);
```

## Common Pitfalls

### ❌ MISTAKE 1: Not Cleaning Up Weak Pointers
```cpp
// WRONG - Leaves invalid weak pointers in array
void HandleSpawnDestroyed(AActor* DestroyedActor)
{
    // Forgot to remove from ActiveSpawns!
}
```

**CORRECT:**
```cpp
void HandleSpawnDestroyed(AActor* DestroyedActor)
{
    ActiveSpawns.RemoveAll([DestroyedActor](const TWeakObjectPtr<AActor>& WeakPtr)
    {
        return !WeakPtr.IsValid() || WeakPtr.Get() == DestroyedActor;
    });
}
```

### ❌ MISTAKE 2: Using Hard-Coded Spawn Tables
```cpp
// WRONG - C++ hardcoding prevents designer iteration
TMap<FName, TSubclassOf<AActor>> SpawnTable;
SpawnTable.Add(TEXT("Wave1"), BP_Zombie);  // Don't hardcode in C++!
```

**CORRECT:**
```cpp
// EditDefaultsOnly - designers configure in Blueprint
UPROPERTY(EditDefaultsOnly, Category = "Spawner")
TMap<FName, TMap<TSubclassOf<AActor>, float>> SpawnTables;
```

### ❌ MISTAKE 3: Forgetting Spawn Point Validation
```cpp
// WRONG - Crashes if SpawnPoints array is empty
FVector SpawnLoc = SpawnPoints[0]->GetComponentLocation();
```

**CORRECT:**
```cpp
if (SpawnPoints.IsValidIndex(SpawnPointIndex) && SpawnPoints[SpawnPointIndex])
{
    SpawnLoc = SpawnPoints[SpawnPointIndex]->GetComponentLocation();
}
else
{
    SpawnLoc = GetActorLocation();  // Fallback
}
```

### ❌ MISTAKE 4: Not Checking Population Limit
```cpp
// WRONG - Spawns unlimited actors
void ActivateChannel(FName ChannelName)
{
    SpawnActorAtPoint(SelectClass(ChannelName));  // No limit check!
}
```

**CORRECT:**
```cpp
if (ActiveSpawns.Num() >= MaxPopulation)
{
    UE_LOG(LogTemp, Warning, TEXT("Max population reached"));
    return;
}
```

## Testing / Verification

### Blueprint Configuration Example
1. Create BP_EnemySpawner from ABaseSpawner
2. Add SpawnPoints (Scene Components as children):
   - SpawnPoint_North
   - SpawnPoint_South
   - SpawnPoint_East
   - SpawnPoint_West
3. Configure SpawnTables:
   ```
   Channel: "Wave1"
     BP_Zombie_C -> Weight: 5.0
     BP_FastZombie_C -> Weight: 2.0

   Channel: "Wave2"
     BP_Zombie_C -> Weight: 3.0
     BP_TankZombie_C -> Weight: 1.0
   ```
4. Set MaxPopulation: 10

### Console Command Testing
```cpp
// Add to PlayerController or Cheat Manager
UFUNCTION(Exec)
void SpawnWave(FName ChannelName)
{
    TArray<AActor*> Spawners;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), ABaseSpawner::StaticClass(), Spawners);

    for (AActor* Actor : Spawners)
    {
        if (ABaseSpawner* Spawner = Cast<ABaseSpawner>(Actor))
        {
            Spawner->ActivateChannel(ChannelName);
        }
    }
}
```

### Test Checklist
- [ ] Spawner initializes with configured channels
- [ ] ActivateChannel spawns from correct weighted table
- [ ] Weighted random selection produces expected distribution (run 100x)
- [ ] Spawn points used correctly (4 points = 25% each over time)
- [ ] MaxPopulation enforced (cannot exceed limit)
- [ ] ActiveSpawns decreases when spawned actors die
- [ ] Spawner handles empty SpawnPoints array (uses actor location)
- [ ] Invalid channel names log error and don't crash

### PIE Testing Workflow
1. Place BP_EnemySpawner in level
2. Configure spawn tables with test actors
3. PIE and type: `SpawnWave Wave1`
4. Verify actors spawn at random spawn points
5. Kill spawned actors
6. Verify population count decreases
7. Spam spawn command to test population limit

## Deep Command Adaptation

### Naval Base Spawner
Deep Command uses this pattern for naval reinforcement spawning:

```cpp
// ANavalBase extends ABaseSpawner
UPROPERTY(EditDefaultsOnly, Category = "Naval Base")
TMap<FName, TMap<TSubclassOf<AShipPawn>, float>> ReinforcementFleets;

// Channels: "ScreeningForce", "CapitalFleet", "SubmarinePatrol"
// Spawns ships at dockyard berths (spawn points)
```

### Signal-Driven Reinforcements
```cpp
// AReinforcementSpawner listens to battle signals
void AReinforcementSpawner::BeginPlay()
{
    Super::BeginPlay();

    if (UBattleSubsystem* BattleSub = GetGameInstance()->GetSubsystem<UBattleSubsystem>())
    {
        BattleSub->OnEngagementStarted.AddDynamic(this, &ThisClass::HandleEngagement);
    }
}

void AReinforcementSpawner::HandleEngagement(FName EngagementID)
{
    // Trigger reinforcement wave via channel
    ActivateChannel(TEXT("ReinforcementWave"));
}
```

### Key Differences from Base Pattern
- **Spawn actors:** Ships instead of ground enemies
- **Spawn points:** Dockyard berths with specific orientations
- **Population tracking:** Ships report to FleetManagerSubsystem
- **Trigger source:** Subsystem delegates, not manual activation

### Preserved Principles
- Still FName channels for designer expansion
- Still weighted spawn tables
- Still scene component spawn point hierarchy
- Still population limit enforcement
- Still delegate-driven cleanup tracking
