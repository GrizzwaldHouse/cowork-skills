# Task: Team & Faction System with IGenericTeamAgentInterface

## Purpose
Implement Unreal's built-in team identification system using IGenericTeamAgentInterface for AI perception attitude detection and faction-based targeting. Enables AI to distinguish friend from foe without hardcoded checks.

## Prerequisites
- Unreal Engine 5.4 C++ project
- Understanding of UE5 interface implementation (I prefix classes)
- Familiarity with AI Perception team attitude system
- Knowledge of FGenericTeamId struct (0-254 valid, 255 = NoTeam)

## Source Code Reference
**Island Escape (BaseGame/END2507):**
- `Source/END2507/Code/Actors/BaseAgent.h` (lines 1-60)
- `Source/END2507/Code/Actors/BaseAgent.cpp` (lines 1-120)

**Unreal Engine Documentation:**
- GenericTeamAgentInterface.h (Engine/Source/Runtime/AIModule/Classes/GenericTeamAgentInterface.h)

**Key Pattern Elements:**
- IGenericTeamAgentInterface provides GetGenericTeamId()
- FGenericTeamId is a simple struct wrapping uint8 (0-255)
- AI Perception uses team IDs for attitude queries (Friendly, Neutral, Hostile)
- ETeamAttitude enum controls perception filtering

## Implementation Steps

### Step 1: Understand FGenericTeamId
```cpp
// From Engine/Source/Runtime/AIModule/Classes/GenericTeamAgentInterface.h

struct FGenericTeamId
{
    static constexpr uint8 NoTeam = 255;

    FGenericTeamId(uint8 InTeamID = NoTeam) : TeamID(InTeamID) {}

    uint8 GetId() const { return TeamID; }

    bool operator==(const FGenericTeamId& Other) const
    {
        return TeamID == Other.TeamID;
    }

    bool operator!=(const FGenericTeamId& Other) const
    {
        return TeamID != Other.TeamID;
    }

private:
    uint8 TeamID;
};

// Attitude query result
enum class ETeamAttitude : uint8
{
    Friendly,
    Neutral,
    Hostile
};
```

### Step 2: Implement Interface in Actor Header
```cpp
// BaseAgent.h
// Developer: [Your Name]
// Date: [YYYY-MM-DD]
// Purpose: AI-controlled actor with team identification for perception
// Usage: Base class for enemies, NPCs, or any AI actor needing team affiliation

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GenericTeamAgentInterface.h"  // REQUIRED include
#include "BaseAgent.generated.h"

UCLASS()
class YOURPROJECT_API ABaseAgent : public ACharacter, public IGenericTeamAgentInterface
{
    GENERATED_BODY()

public:
    ABaseAgent();

    // ====================================================================
    // IGenericTeamAgentInterface IMPLEMENTATION (REQUIRED)
    // ====================================================================

    // Returns this actor's team ID for AI perception
    virtual FGenericTeamId GetGenericTeamId() const override;

    // ====================================================================
    // TEAM MANAGEMENT API
    // ====================================================================

    // Set team ID at runtime (for dynamic team assignment)
    UFUNCTION(BlueprintCallable, Category = "Team")
    void SetTeamID(uint8 NewTeamID);

    // Query team ID
    UFUNCTION(BlueprintPure, Category = "Team")
    uint8 GetTeamID() const { return TeamID; }

    // Check if actor is on specific team
    UFUNCTION(BlueprintPure, Category = "Team")
    bool IsOnTeam(uint8 TestTeamID) const { return TeamID == TestTeamID; }

    // Check if actor is on same team as another
    UFUNCTION(BlueprintPure, Category = "Team")
    bool IsSameTeam(const AActor* OtherActor) const;

protected:
    virtual void BeginPlay() override;

private:
    // ====================================================================
    // TEAM CONFIGURATION
    // ====================================================================

    // Team ID for this agent (0-254, 255 = NoTeam)
    // EditInstanceOnly: Set per-placed actor in level
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Team",
        meta = (AllowPrivateAccess = "true", ClampMin = "0", ClampMax = "255"))
    uint8 TeamID;
};
```

### Step 3: Implement Interface Methods
```cpp
// BaseAgent.cpp

#include "BaseAgent.h"

ABaseAgent::ABaseAgent()
    : TeamID(FGenericTeamId::NoTeam)  // Default: No team
{
    PrimaryActorTick.bCanEverTick = false;
}

void ABaseAgent::BeginPlay()
{
    Super::BeginPlay();

    UE_LOG(LogTemp, Log, TEXT("[%s] BaseAgent spawned on Team %d"),
        *GetName(), TeamID);
}

// CRITICAL: This function is called by AI Perception to determine attitude
FGenericTeamId ABaseAgent::GetGenericTeamId() const
{
    return FGenericTeamId(TeamID);
}

void ABaseAgent::SetTeamID(uint8 NewTeamID)
{
    if (NewTeamID > 254)
    {
        UE_LOG(LogTemp, Warning, TEXT("[%s] Invalid TeamID %d (max 254). Setting to NoTeam."),
            *GetName(), NewTeamID);
        TeamID = FGenericTeamId::NoTeam;
    }
    else
    {
        TeamID = NewTeamID;
        UE_LOG(LogTemp, Log, TEXT("[%s] Team changed to %d"), *GetName(), TeamID);
    }
}

bool ABaseAgent::IsSameTeam(const AActor* OtherActor) const
{
    if (!OtherActor)
    {
        return false;
    }

    // Check if other actor implements IGenericTeamAgentInterface
    const IGenericTeamAgentInterface* OtherTeamAgent = Cast<IGenericTeamAgentInterface>(OtherActor);
    if (!OtherTeamAgent)
    {
        // Actor doesn't have team affiliation
        return false;
    }

    // Compare team IDs
    FGenericTeamId OtherTeamID = OtherTeamAgent->GetGenericTeamId();
    FGenericTeamId MyTeamID = GetGenericTeamId();

    return MyTeamID == OtherTeamID;
}
```

### Step 4: Configure AI Controller Team Interface
AI controllers should ALSO implement IGenericTeamAgentInterface and forward to their pawn:

```cpp
// AIC_BaseAgentController.h

#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "GenericTeamAgentInterface.h"
#include "AIC_BaseAgentController.generated.h"

UCLASS()
class YOURPROJECT_API AAIC_BaseAgentController : public AAIController, public IGenericTeamAgentInterface
{
    GENERATED_BODY()

public:
    AAIC_BaseAgentController();

    // IGenericTeamAgentInterface - forward to possessed pawn
    virtual FGenericTeamId GetGenericTeamId() const override;

protected:
    virtual void OnPossess(APawn* InPawn) override;
};
```

```cpp
// AIC_BaseAgentController.cpp

#include "AIC_BaseAgentController.h"
#include "Perception/AIPerceptionComponent.h"

AAIC_BaseAgentController::AAIC_BaseAgentController()
{
    // Configure AI Perception to use team attitude
    if (PerceptionComponent)
    {
        PerceptionComponent->SetDominantSense(*PerceptionComponent->GetDefaultSenseConfig()->GetSenseImplementation());
    }
}

FGenericTeamId AAIC_BaseAgentController::GetGenericTeamId() const
{
    // Forward to possessed pawn if it implements interface
    if (APawn* MyPawn = GetPawn())
    {
        if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(MyPawn))
        {
            return TeamAgent->GetGenericTeamId();
        }
    }

    // Fallback: No team
    return FGenericTeamId::NoTeam;
}

void AAIC_BaseAgentController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);

    // Optionally notify perception component of team change
    if (PerceptionComponent && InPawn)
    {
        PerceptionComponent->RequestStimuliListenerUpdate();
    }

    UE_LOG(LogTemp, Log, TEXT("[%s] Possessed pawn [%s] with Team %d"),
        *GetName(),
        *InPawn->GetName(),
        GetGenericTeamId().GetId());
}
```

### Step 5: Configure Team Attitudes in GameMode
Define how teams perceive each other (friend or foe):

```cpp
// YourGameMode.cpp

void AYourGameMode::BeginPlay()
{
    Super::BeginPlay();

    ConfigureTeamAttitudes();
}

void AYourGameMode::ConfigureTeamAttitudes()
{
    UGenericTeamAgentInterface::SetAttitude(
        FGenericTeamId(0),  // Team 0 (Player)
        FGenericTeamId(1),  // Team 1 (Enemies)
        ETeamAttitude::Hostile
    );

    UGenericTeamAgentInterface::SetAttitude(
        FGenericTeamId(1),  // Team 1 (Enemies)
        FGenericTeamId(0),  // Team 0 (Player)
        ETeamAttitude::Hostile
    );

    UGenericTeamAgentInterface::SetAttitude(
        FGenericTeamId(0),  // Team 0 (Player)
        FGenericTeamId(2),  // Team 2 (Allies)
        ETeamAttitude::Friendly
    );

    UGenericTeamAgentInterface::SetAttitude(
        FGenericTeamId(1),  // Team 1 (Enemies)
        FGenericTeamId(2),  // Team 2 (Allies)
        ETeamAttitude::Hostile
    );

    UE_LOG(LogTemp, Log, TEXT("Team attitudes configured: Player(0) vs Enemies(1) = Hostile"));
}
```

### Step 6: Use Team Filtering in AI Perception
Configure AI Perception to detect only hostile targets:

```cpp
// In AI Controller BeginPlay or SetupPerception()
void AAIC_BaseAgentController::SetupPerception()
{
    if (PerceptionComponent)
    {
        // Configure sight sense
        UAISenseConfig_Sight* SightConfig = CreateDefaultSubobject<UAISenseConfig_Sight>(TEXT("SightConfig"));
        SightConfig->SightRadius = 2000.0f;
        SightConfig->LoseSightRadius = 2500.0f;
        SightConfig->PeripheralVisionAngleDegrees = 90.0f;

        // CRITICAL: Set detection affiliation
        SightConfig->DetectionByAffiliation.bDetectEnemies = true;   // Detect hostile teams
        SightConfig->DetectionByAffiliation.bDetectNeutrals = false; // Ignore neutral teams
        SightConfig->DetectionByAffiliation.bDetectFriendlies = false; // Ignore same team

        PerceptionComponent->ConfigureSense(*SightConfig);
        PerceptionComponent->SetDominantSense(SightConfig->GetSenseImplementation());
    }
}
```

## Delegate Signatures

No custom delegates required - this pattern uses built-in Unreal systems.

## Common Pitfalls

### ❌ MISTAKE 1: Not Implementing Interface in Controller
```cpp
// WRONG - Only pawn implements interface
class ABaseAgent : public ACharacter, public IGenericTeamAgentInterface { };
class AAIC_Controller : public AAIController { };  // Missing interface!
```

**CORRECT:**
```cpp
// Both pawn AND controller implement interface
class ABaseAgent : public ACharacter, public IGenericTeamAgentInterface { };
class AAIC_Controller : public AAIController, public IGenericTeamAgentInterface { };
```

**Reason:** AI Perception queries the CONTROLLER's team, not the pawn's. Controller should forward to pawn.

### ❌ MISTAKE 2: Forgetting to Set Team Attitudes
```cpp
// WRONG - Teams defined but no attitude configured
SetTeamID(0);  // Player team
SetTeamID(1);  // Enemy team
// Missing: UGenericTeamAgentInterface::SetAttitude() calls!
```

**CORRECT:**
```cpp
// Configure attitude relationships in GameMode BeginPlay
UGenericTeamAgentInterface::SetAttitude(
    FGenericTeamId(0), FGenericTeamId(1), ETeamAttitude::Hostile);
```

### ❌ MISTAKE 3: Using TeamID > 254
```cpp
// WRONG - TeamID only supports 0-254 (255 = NoTeam)
SetTeamID(300);  // Invalid!
```

**CORRECT:**
```cpp
// Use 0-254 range, or FGenericTeamId::NoTeam (255)
SetTeamID(0);  // Valid
SetTeamID(254);  // Valid
SetTeamID(FGenericTeamId::NoTeam);  // Valid (255)
```

### ❌ MISTAKE 4: Not Configuring DetectionByAffiliation
```cpp
// WRONG - AI perception will detect EVERYTHING regardless of team
UAISenseConfig_Sight* SightConfig = CreateDefaultSubobject<UAISenseConfig_Sight>(TEXT("Sight"));
// Missing DetectionByAffiliation configuration!
```

**CORRECT:**
```cpp
SightConfig->DetectionByAffiliation.bDetectEnemies = true;
SightConfig->DetectionByAffiliation.bDetectNeutrals = false;
SightConfig->DetectionByAffiliation.bDetectFriendlies = false;
```

### ❌ MISTAKE 5: Casting to Wrong Interface Type
```cpp
// WRONG - Casting to interface pointer incorrectly
IGenericTeamAgentInterface* TeamAgent = (IGenericTeamAgentInterface*)OtherActor;  // UNSAFE!
```

**CORRECT:**
```cpp
// Use Cast<> for interface pointers
IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(OtherActor);
if (TeamAgent)
{
    FGenericTeamId OtherTeam = TeamAgent->GetGenericTeamId();
}
```

## Testing / Verification

### Console Commands for Testing
```cpp
// Add to PlayerController or Cheat Manager
UFUNCTION(Exec)
void SetMyTeam(int32 NewTeamID)
{
    if (APawn* MyPawn = GetPawn())
    {
        if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(MyPawn))
        {
            TeamAgent->SetGenericTeamId(FGenericTeamId(NewTeamID));
            UE_LOG(LogTemp, Log, TEXT("Player team set to %d"), NewTeamID);
        }
    }
}

UFUNCTION(Exec)
void LogTeamAttitude(int32 Team1, int32 Team2)
{
    ETeamAttitude::Type Attitude = FGenericTeamId::GetAttitude(
        FGenericTeamId(Team1),
        FGenericTeamId(Team2)
    );

    FString AttitudeStr;
    switch (Attitude)
    {
        case ETeamAttitude::Friendly: AttitudeStr = TEXT("Friendly"); break;
        case ETeamAttitude::Neutral: AttitudeStr = TEXT("Neutral"); break;
        case ETeamAttitude::Hostile: AttitudeStr = TEXT("Hostile"); break;
    }

    UE_LOG(LogTemp, Log, TEXT("Team %d sees Team %d as: %s"), Team1, Team2, *AttitudeStr);
}
```

### Test Checklist
- [ ] Actor implements IGenericTeamAgentInterface
- [ ] Controller implements IGenericTeamAgentInterface and forwards to pawn
- [ ] GetGenericTeamId() returns correct FGenericTeamId
- [ ] SetTeamID() updates team correctly
- [ ] Team attitudes configured in GameMode BeginPlay
- [ ] AI Perception DetectionByAffiliation set correctly
- [ ] AI only detects actors on hostile teams
- [ ] AI ignores actors on same team
- [ ] Console command `LogTeamAttitude 0 1` shows "Hostile"
- [ ] Changing player team with `SetMyTeam 1` causes AI to stop targeting

### PIE Testing Workflow
1. Place player character (Team 0) in level
2. Place enemy AI agents (Team 1) in level
3. Configure GameMode team attitudes (0 vs 1 = Hostile)
4. PIE - verify AI targets player
5. Console: `SetMyTeam 1` (switch to enemy team)
6. Verify AI stops targeting player (now friendly)
7. Console: `SetMyTeam 2` (neutral team)
8. Verify AI ignores player (neutral)

### Visual Debugging
Add debug sphere to show team detection:
```cpp
void AAIC_BaseAgentController::OnTargetPerceptionUpdated(AActor* Actor, FAIStimulus Stimulus)
{
    if (Stimulus.WasSuccessfullySensed())
    {
        IGenericTeamAgentInterface* TargetTeam = Cast<IGenericTeamAgentInterface>(Actor);
        if (TargetTeam)
        {
            ETeamAttitude::Type Attitude = FGenericTeamId::GetAttitude(
                GetGenericTeamId(),
                TargetTeam->GetGenericTeamId()
            );

            FColor DebugColor = FColor::White;
            if (Attitude == ETeamAttitude::Hostile) DebugColor = FColor::Red;
            if (Attitude == ETeamAttitude::Friendly) DebugColor = FColor::Green;

            DrawDebugSphere(GetWorld(), Actor->GetActorLocation(), 100.0f, 12, DebugColor, false, 2.0f);
        }
    }
}
```

## Deep Command Adaptation

### Nation-Based Team System
Deep Command uses ENation enum (closed set) instead of generic uint8 TeamID:

```cpp
// INationInterface.h (extends IGenericTeamAgentInterface)
class INationInterface : public IGenericTeamAgentInterface
{
public:
    virtual ENation GetNation() const = 0;

    // Forward nation to team ID
    virtual FGenericTeamId GetGenericTeamId() const override
    {
        return FGenericTeamId(static_cast<uint8>(GetNation()));
    }
};

// ENation enum (closed set - historical WW2 nations)
enum class ENation : uint8
{
    None = 255,  // Maps to FGenericTeamId::NoTeam
    UnitedStates = 0,
    UnitedKingdom = 1,
    Germany = 2,
    Japan = 3,
    Italy = 4,
    France = 5,
    SovietUnion = 6,
    MAX UMETA(Hidden)
};
```

### Diplomacy Subsystem Integration
```cpp
// UDiplomacySubsystem configures nation attitudes at runtime
void UDiplomacySubsystem::SetDiplomaticStatus(ENation NationA, ENation NationB, EDiplomaticStatus Status)
{
    ETeamAttitude::Type Attitude = ETeamAttitude::Neutral;

    switch (Status)
    {
        case EDiplomaticStatus::Allied:
        case EDiplomaticStatus::Friendly:
            Attitude = ETeamAttitude::Friendly;
            break;
        case EDiplomaticStatus::Hostile:
        case EDiplomaticStatus::AtWar:
            Attitude = ETeamAttitude::Hostile;
            break;
        default:
            Attitude = ETeamAttitude::Neutral;
            break;
    }

    // Update UE5 team attitude system
    FGenericTeamId TeamA(static_cast<uint8>(NationA));
    FGenericTeamId TeamB(static_cast<uint8>(NationB));
    FGenericTeamId::SetAttitude(TeamA, TeamB, Attitude);

    UE_LOG(LogDiplomacy, Log, TEXT("Nation %d vs %d: %s"),
        static_cast<uint8>(NationA),
        static_cast<uint8>(NationB),
        *UEnum::GetValueAsString(Status));
}
```

### Key Differences from Base Pattern
- **uint8 TeamID → ENation enum:** Type-safe nation identification
- **Static attitudes → Dynamic diplomacy:** Attitudes change during gameplay
- **2 teams → N nations:** 7 historical nations with complex relationships
- **INationInterface:** Extends IGenericTeamAgentInterface with nation-specific API

### Preserved Principles
- Still uses IGenericTeamAgentInterface for AI perception
- Still implements interface in both pawn and controller
- Still uses FGenericTeamId (0-255) internally
- Still uses ETeamAttitude for perception filtering
- Still configures DetectionByAffiliation in AI Perception
