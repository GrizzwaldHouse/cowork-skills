# Deep Command Architecture Design

Developer: Marcus Daley
Architect: Architecture Planner Agent
Date: 2026-03-02
Engine: Unreal Engine 5.4 (C++)
Standards: Nick Penney AAA Coding Standards
Source Projects: Island Escape (BaseGame/END2507), WizardJam (Quidditch subsystem)

---

## 1. Component Mapping (Island Escape -> Deep Command)

| Source (Island Escape) | Target (Deep Command) | Key Changes |
|---|---|---|
| AC_HealthComponent | AC_HullComponent | Single HP -> zone-based (Bow/Mid/Stern/Keel/Super) |
| AC_StaminaComponent | AC_FuelComponent | Stamina drain -> fuel consumption per engine order |
| BaseProjectile | ATorpedo / AShell | Add ballistic arc, torpedo guidance, depth charges |
| BaseCharacter | ABaseVessel (ShipPawn) | Character -> Pawn with ship components |
| BaseAgent | ASurfaceShip | IEnemyInterface -> IShipInterface |
| BaseSpawner | ANavalBase | Spawn points -> dockyard + repair berths |
| BasePlayer | APlayerFlagship | Enhanced Input for helm/weapons/detection |
| BatAgent | ASubmarineVessel | Boss AI -> depth + stealth management |
| AIC_BaseAgentAIController | AIC_ShipController | Ammo tracking moves to weapon component |
| BasePickup | ASupplyCrate | Floating supply drops, convoy cargo |
| HideWall | ASmokescreenZone | Detection-blocking volume |
| BroomCollectible | ASupplyDepot | Static supply point actors |
| WorldSignalEmitter | ABattleSignalEmitter | Orchestration signals |
| IDamageable | IDamageableInterface | Complete with zone damage params |
| IPickupInterface | IResupplyInterface | Health/ammo -> fuel/ammo/provisions |
| IGenericTeamAgentInterface | INationInterface + IGTAI | Team ID -> Nation identity |
| IslandEscapeGameMode | ADeepCommandGameMode | Wave tracking -> scenario phases |

### Key Translation Principles

1. Health -> Hull Zones: Single float splits into zones (bow, midship, stern, keel)
   each with independent integrity, flooding rate, and fire state.
2. Stamina -> Fuel + Crew Fatigue: Drain/regen maps to fuel (consumed by movement)
   and crew fatigue (degraded by combat, recovered during port).
3. Broom Flight -> Naval Movement: 3D aerial maps to 2D surface + depth for subs.
   Velocity-based approach (no NavMesh) translates directly.
4. Spell Channels -> Weapon Types: FName-based channels become FName weapon types.
   Designer-expandable without C++ changes.

---

## 2. Component Mapping (WizardJam Quidditch -> Deep Command)

| Source (WizardJam) | Target (Deep Command) | Key Changes |
|---|---|---|
| AC_BroomComponent | AC_NavalMovementComponent | Flight toggle -> engine orders, rudder, depth |
| QuidditchGameMode (state machine) | UBattleSubsystem | Match states -> battle phases |
| QuidditchGameMode (agent registry) | UFleetManagerSubsystem | RegisterAgent -> RegisterShip (persistent) |
| QuidditchGameMode (team system) | UDiplomacySubsystem | 2 teams -> N nations with attitude matrix |
| QuidditchGameMode (Gas Station) | All subsystems | Delegates update BB, decorators re-evaluate |
| AIC_QuidditchController | AIC_ShipController | Flight target -> fleet orders + formations |
| BTService_FindCollectible | BTService_ScanContacts | Perception -> radar/sonar contact sweep |
| BTTask_ControlFlight | BTTask_NavigateShip | Vertical input -> engine order + rudder |
| BTTask_FlyToStagingZone | BTTask_MoveToWaypoint | Staging zone -> formation position |
| BTTask_ChaseSnitch | BTTask_PursueTarget | Close distance with intercept courses |
| BTTask_EvadeSeeker | BTTask_EvadeContact | Break contact via heading, speed, smoke |
| BTService_SyncFlightState | BTService_UpdateNavigation | IsFlying BB -> Hull/Fuel/Ammo BB |
| AIPerception wrapper | AC_DetectionComponent | Sight -> radar/sonar/visual/ESM senses |
| ASnitchBall | AConvoyShip | Autonomous actors with own movement |
| AQuidditchStagingZone | APatrolZone / AEngagementArea | Area triggers for subsystem notify |
| QuidditchBallSpawner | AReinforcementSpawner | Signal-driven reinforcement waves |

### Core API Pattern (BroomComponent -> NavalMovement)

BroomComponent Core API where both player input and AI call the same verb
functions is the CORRECT architecture for Deep Command:

- SetVerticalInput(float) -> SetRudder(float)
- SetBoostEnabled(bool) -> SetEngineOrder(EEngineOrder)
- SetFlightEnabled(bool) -> SetTargetDepth(float) [submarines]
- IsFlying() -> IsSubmerged()

Component does not care if caller is player input or AI BT task.

### Critical Architectural Lessons Carried Forward

1. FBlackboardKeySelector MUST have AddObjectFilter + InitializeFromAsset -- silent failure.
2. Delegate unbinding mandatory -- every AddDynamic needs RemoveDynamic.
3. State machine transitions must broadcast -- every transition fires delegate.
4. BB keys need full init chain -- asset + FName + constructor + setup + runtime + binding.
5. No NavMesh for non-ground movement -- direct velocity only.

---

## 3. Delegate Infrastructure

All cross-system communication uses the Observer Pattern. No polling. No direct calls.

### Subsystem-Level Delegates

```cpp
// UFleetManagerSubsystem
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnShipRegistered,
    AShipPawn*, Ship, FName, FleetName, EShipRole, AssignedRole);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnShipUnregistered,
    AShipPawn*, Ship, FName, FleetName);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnFleetFormationChanged,
    FName, FleetName, EFleetFormation, NewFormation);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnFleetOrderIssued,
    FName, FleetName, EFleetOrder, Order, FVector, TargetLocation);

// UBattleSubsystem
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnBattlePhaseChanged,
    EBattlePhase, OldPhase, EBattlePhase, NewPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnEngagementStarted,
    FName, EngagementId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnEngagementEnded,
    FName, EngagementId, EEngagementResult, Result);

// USupplyChainSubsystem
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSupplyDelivered,
    AShipPawn*, Receiver, FSupplyManifest, Manifest);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnConvoyUnderAttack,
    FName, ConvoyId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSupplyRouteDisrupted,
    FName, RouteId);

// UDiplomacySubsystem
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnDiplomaticStatusChanged,
    FName, NationA, FName, NationB, EDiplomaticStatus, NewStatus);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnWarDeclared,
    FName, Aggressor, FName, Defender);

// UTimeManagerSubsystem
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTimeScaleChanged,
    float, NewScale);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnGamePaused);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnGameResumed);

// UIntelligenceSubsystem
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnContactDetected,
    AActor*, Actor, EDetectionMethod, Method, float, Confidence);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnContactLost,
    AActor*, Actor, EDetectionMethod, Method);
```

### Component-Level Delegates (per-vessel, bound at BeginPlay)

```cpp
// AC_HullComponent
FOnHullZoneDamaged(EHullZone Zone, float CurrentIntegrity, float MaxIntegrity)
FOnHullZoneBreached(EHullZone Zone)
FOnFloodingChanged(EHullZone Zone, float FloodPercent)
FOnFireStateChanged(EHullZone Zone, bool bOnFire)
FOnShipSinking(AShipPawn* Ship)

// AC_NavalMovementComponent
FOnSpeedChanged(EEngineOrder NewOrder, float CurrentKnots)
FOnHeadingChanged(float NewHeadingDegrees)
FOnDepthChanged(float NewDepthMeters)

// AC_WeaponSystemComponent
FOnWeaponFired(int32 MountIndex, FName WeaponType)
FOnWeaponReloaded(int32 MountIndex, int32 AmmoRemaining)
FOnWeaponAmmoExpended(int32 MountIndex)
FOnWeaponMountDestroyed(int32 MountIndex, EHullZone DestroyedByZone)

// AC_DetectionComponent
FOnContactDetected(AActor* Actor, EDetectionMethod Method, float Confidence)
FOnContactLost(AActor* Actor, EDetectionMethod Method)

// AC_CrewComponent
FOnCrewCasualty(EHullZone Zone, int32 Casualties)
FOnMoraleChanged(float NewMorale)
FOnCrewEfficiencyChanged(float NewEfficiency)

// AC_FuelComponent
FOnFuelChanged(float RemainingPercent)
FOnFuelDepleted()
FOnResupplied(float AmountReceived)
```

### Component Cross-Binding at BeginPlay

These delegate bindings happen inside the ShipPawn actor at BeginPlay:

- HullComponent::OnHullZoneBreached -> WeaponSystem::HandleHullZoneDestroyed (disable mounts)
- HullComponent::OnHullZoneBreached -> CrewComponent::HandleHullZoneDamaged (casualties)
- CrewComponent::OnCrewEfficiencyChanged -> WeaponSystem (reload speed modifier)
- CrewComponent::OnCrewEfficiencyChanged -> NavalMovement (max speed modifier)
- FuelComponent::OnFuelDepleted -> NavalMovement::HandleFuelDepleted (AllStop)
- FuelComponent::OnFuelDepleted -> WeaponSystem::HandleAmmoExhausted
- DetectionComponent::OnContactDetected -> IntelligenceSubsystem::AggregateContact

### Controller Binding Pattern (from QuidditchController)

```cpp
void AAIC_ShipController::BeginPlay()
{
    Super::BeginPlay();
    if (UFleetManagerSubsystem* FleetMgr =
        GetGameInstance()->GetSubsystem<UFleetManagerSubsystem>())
    {
        FleetMgr->OnFleetOrderIssued.AddDynamic(
            this, &ThisClass::HandleFleetOrderIssued);
    }
}

void AAIC_ShipController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UFleetManagerSubsystem* FleetMgr =
        GetGameInstance()->GetSubsystem<UFleetManagerSubsystem>())
    {
        FleetMgr->OnFleetOrderIssued.RemoveDynamic(
            this, &ThisClass::HandleFleetOrderIssued);
    }
    Super::EndPlay(EndPlayReason);
}
```

---
## 4. AI Architecture

### 4.1 AI Controller Hierarchy

AIC_ShipController (base for all AI ships)
  - Extends AAIController + IGenericTeamAgentInterface
  - Owns Blackboard + BehaviorTree setup
  - Binds to FleetManager and scenario delegates
  - Updates BB keys on delegate events (Gas Station Pattern)
  - Manages AIPerception via AC_DetectionComponent wrapper
  |
  +-- AIC_FleetCommanderController (task force lead)
  |     - Issues formation orders to subordinate ships
  |     - Evaluates tactical situation via EQS queries
  |     - Decides engage/withdraw/reposition
  |
  +-- AIC_SubmarineController (extends AIC_ShipController)
        - Depth management (periscope, attack, deep)
        - Stealth state tracking (detected/undetected)
        - Additional BB keys: TargetDepth, IsSubmerged, IsDetected, TorpedoSolution

### 4.2 Blackboard Keys

Key Name              | Type    | Written By                    | Read By
----------------------|---------|-------------------------------|--------
SelfActor             | Object  | Controller (OnPossess)        | All tasks
NationID              | Enum    | Controller (OnPossess)        | Decorators
CurrentOrder          | Enum    | FleetManager delegate         | Root selector
TargetLocation        | Vector  | BTService_ScanContacts        | BTTask_NavigateShip
TargetActor           | Object  | BTService_ScanContacts        | BTTask_PursueTarget
FormationPosition     | Vector  | FleetManager delegate         | BTTask_MoveToWaypoint
EngagementID          | Int     | FleetManager delegate         | Decorators
HullIntegrity         | Float   | HullComponent delegate        | BTDecorator_HullCritical
FuelRemaining         | Float   | FuelComponent delegate        | BTDecorator_FuelLow
AmmoState             | Enum    | WeaponSystem delegate         | BTDecorator_HasAmmo
HasActiveContact      | Bool    | DetectionComponent delegate   | Selector branch
IsSubmerged           | Bool    | NavalMovement delegate        | Submarine branch
IsDetected            | Bool    | DetectionComponent delegate   | Submarine evasion
TorpedoSolution       | Bool    | BTService_ComputeFiringSolution | Attack task
PatrolRouteIndex      | Int     | BTTask_AdvancePatrol          | BTTask_MoveToWaypoint
NearestFriendly       | Object  | BTService_ScanContacts        | BTTask_FormUp
ScenarioPhase         | Enum    | GameMode delegate             | Root selector
ConvoyTarget          | Object  | FleetManager delegate         | Escort/attack branch

### 4.3 Behavior Tree Nodes

#### Tasks (9)
BTTask_NavigateShip        -- Set engine order + rudder toward target location
BTTask_MoveToWaypoint      -- Navigate to assigned formation/patrol position
BTTask_PursueTarget        -- Intercept course toward TargetActor
BTTask_EvadeContact        -- Break contact via heading change, speed, smoke
BTTask_FireWeapon          -- Execute weapon firing sequence
BTTask_LaunchTorpedo       -- Submarine torpedo attack with solution check
BTTask_SetDepth            -- Change submarine depth (periscope/attack/deep)
BTTask_ResupplyAtPort      -- Dock and resupply at friendly NavalBase
BTTask_AdvancePatrol       -- Increment patrol route index and set next waypoint

#### Services (4)
BTService_ScanContacts     -- Sweep AC_DetectionComponent contacts, pick priority target
BTService_UpdateNavigation -- Sync BB with hull/fuel/ammo states from components
BTService_ComputeFiringSolution -- Calculate torpedo/gun solution against TargetActor
BTService_EvaluateThreat   -- Score threat level from detected contacts

#### Decorators (3)
BTDecorator_HullCritical   -- Abort if hull integrity below threshold
BTDecorator_HasAmmo        -- Gate weapon tasks on ammo availability
BTDecorator_FuelLow        -- Force RTB when fuel below reserve

### 4.4 Behavior Tree Structure

Root: BT_SurfaceShip
  Selector (priority)
  |
  +-- [Decorator: HullCritical] Emergency Branch
  |     +-- BTTask_EvadeContact
  |     +-- BTTask_ResupplyAtPort
  |
  +-- [Decorator: FuelLow] RTB Branch
  |     +-- BTTask_NavigateShip (to nearest port)
  |
  +-- [BB: CurrentOrder == Engage] Combat Branch
  |     +-- BTService_ScanContacts
  |     +-- BTService_ComputeFiringSolution
  |     +-- Sequence:
  |           +-- BTTask_PursueTarget
  |           +-- BTTask_FireWeapon
  |
  +-- [BB: CurrentOrder == Escort] Escort Branch
  |     +-- BTService_ScanContacts
  |     +-- BTTask_MoveToWaypoint (formation on convoy)
  |     +-- [Decorator: HasActiveContact] Intercept Threat
  |
  +-- [BB: CurrentOrder == Patrol] Patrol Branch
  |     +-- BTService_ScanContacts
  |     +-- BTTask_MoveToWaypoint (patrol route)
  |     +-- BTTask_AdvancePatrol
  |
  +-- Default: BTTask_MoveToWaypoint (hold position)

Root: BT_Submarine (extends surface pattern)
  Selector (priority)
  |
  +-- [Decorator: IsDetected] Evasion Branch
  |     +-- BTTask_SetDepth (deep)
  |     +-- BTTask_EvadeContact
  |
  +-- [BB: CurrentOrder == Hunt] Attack Branch
  |     +-- BTTask_SetDepth (periscope)
  |     +-- BTService_ScanContacts
  |     +-- BTService_ComputeFiringSolution
  |     +-- [Decorator: TorpedoSolution] Fire
  |           +-- BTTask_LaunchTorpedo
  |
  +-- [BB: CurrentOrder == Patrol] Silent Patrol
        +-- BTTask_SetDepth (attack)
        +-- BTTask_MoveToWaypoint
        +-- BTTask_AdvancePatrol

### 4.5 Fleet Coordination Pattern

Fleet coordination uses the Gas Station Pattern from QuidditchGameMode:

1. UFleetManagerSubsystem holds all fleet state (ship registry, task forces, orders)
2. Player issues orders via UI -> subsystem updates state -> broadcasts delegate
3. AIC_ShipController listens to delegate -> updates Blackboard keys
4. BT decorators re-evaluate automatically when BB changes
5. No polling, no direct controller-to-controller calls

Formation positions calculated by FleetManager and pushed to each ship
via FOnFormationOrdered delegate. Each controller writes its assigned
position to BB FormationPosition key.

---

## 5. GameMode -> Subsystem Extraction

QuidditchGameMode held fleet/team/sync state in one class. Works for single-level matches.
Deep Command campaigns span multiple maps, so persistent state needs GameInstanceSubsystems.

### UFleetManagerSubsystem
- Ship registration/unregistration (from QuidditchGameMode.RegisterQuidditchAgent)
- Task force creation and disbanding
- Formation management (line abreast, column, screening, diamond)
- Fleet order dispatch (move, patrol, engage, withdraw, escort)
- Ship queries by nation (from QuidditchGameMode.GetTeamMembers)
- Data: TMap<FName, FFleetData> ActiveFleets

### UBattleSubsystem
- Battle phase state machine (from QuidditchGameMode MatchState)
- Engagement tracking (which ships fighting which)
- Victory/defeat condition evaluation
- Battle result recording
- Data: EBattlePhase CurrentPhase, TMap<FName, FEngagementData>

### USupplyChainSubsystem
- Supply route definition and management (new system)
- Convoy spawning and tracking (from BaseSpawner channels)
- Resource flow (fuel, ammo, provisions per tick)
- Disruption detection (route under attack -> reroute)
- Data: TMap<FName, FSupplyRoute>, TMap<FName, FConvoyData>

### UDiplomacySubsystem
- Nation relationship matrix (QuidditchTeam 2-team -> N-nation)
- Treaty management, war declaration
- AI personality influence on diplomatic decisions
- Data: TMap<FName, EDiplomaticStatus> Relationships

### UTimeManagerSubsystem
- Pause/play/speed control (1x, 2x, 4x, 8x)
- Auto-pause on significant events
- Game time tracking, day advancement
- Data: float TimeScale, bool bIsPaused

### UIntelligenceSubsystem
- Contact aggregation from all friendly vessels
- Fog of war per nation
- Contact classification (unknown -> probable -> confirmed)
- Data: TMap<TWeakObjectPtr<AActor>, FContactInfo> KnownContacts
---

## 6. DataAsset Structure

All gameplay values live in DataAssets. Zero hardcoded numbers.

### 6.1 UShipClassData (UPrimaryDataAsset)

- Identity: ShipClassName (FName), ShipClassification (EShipClassification), NationOfOrigin (FName)
- Movement: MaxSpeedKnots (float), AccelerationRate (float), TurnRateDegreesPerSecond (float),
  DraftMeters (float), MaxDepthMeters (float, subs only)
- Hull: HullZones (TArray FHullZoneConfig), TotalArmorRating (float), DisplacementTons (float)
- Detection: RadarRange (float), SonarRange (float), VisualRange (float),
  RadarCrossSection (float), AcousticSignature (float), MagneticSignature (float)
- Weapons: WeaponMounts (TArray FWeaponMountConfig)
- Crew: CrewComplement (int32), OfficerSlots (int32), DamageControlTeams (int32)
- Supply: FuelCapacity (float), AmmoStorage (TMap FName->int32), MaxProvisionsDays (float)
- Visuals: ShipMesh (TSoftObjectPtr UStaticMesh), ShipIcon (TSoftObjectPtr UTexture2D)

### 6.2 UWeaponData (UPrimaryDataAsset)

- Identity: WeaponName (FName), WeaponType (EWeaponType)
- Ballistics: Range (float), Accuracy (float), ReloadTimeSeconds (float),
  TraverseRateDegreesPerSec (float), ElevationMin (float), ElevationMax (float)
- Damage: BaseDamage (float), ArmorPenetration (float), SplashRadius (float),
  DamageTypeName (FName)
- Ammo: AmmoPerLoad (int32), MaxAmmoReserve (int32), AmmoWeight (float)
- Firing: FiringArcDegrees (float), bCanFireWhileMoving (bool), MinEngagementRange (float)
- Visuals: MuzzleFlashVFX (TSoftObjectPtr), ProjectileClass (TSubclassOf AActor),
  FiringSound (TSoftObjectPtr USoundBase)

### 6.3 UNationData (UPrimaryDataAsset)

- Identity: NationName (FName), NationFlag (TSoftObjectPtr UTexture2D), NationColor (FLinearColor)
- Starting Forces: StartingFleets (TArray FFleetTemplate), HomePorts (TArray FVector)
- AI Personality: Aggressiveness (float 0-1), Expansionism (float 0-1), NavalDoctrine (ENavalDoctrine)
- Tech: TechBonuses (TMap FName->float)
- Economy: BaseResourceGeneration (float), SupplyEfficiency (float), ShipbuildingSpeed (float)

### 6.4 UOfficerTraitData (UPrimaryDataAsset)

- Identity: TraitName (FName), TraitDescription (FText), TraitIcon (TSoftObjectPtr)
- Modifiers: StatModifiers (TMap FName->float)
- Conditions: UnlockCondition (EUnlockCondition), RequiredExperience (int32)

### 6.5 UScenarioData (UPrimaryDataAsset)

- Identity: ScenarioName (FText), ScenarioDescription (FText), MapRegion (TSoftObjectPtr UWorld)
- Forces: NationForces (TMap FName -> TArray FFleetTemplate)
- Objectives: VictoryConditions (TArray FVictoryCondition), TimeLimitSeconds (float)
- Environment: SeaState (ESeaState), Weather (EWeatherCondition), TimeOfDay (float), Visibility (float)

### 6.6 Supporting Structs

```cpp
USTRUCT(BlueprintType)
struct FHullZoneConfig
{
    GENERATED_BODY()
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    EHullZone Zone;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    float MaxIntegrity;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    float ArmorRating;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    bool bCanFlood;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    float FloodRatePerSecond;
};

USTRUCT(BlueprintType)
struct FWeaponMountConfig
{
    GENERATED_BODY()
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    FName MountName;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    UWeaponData* WeaponData;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    FVector MountOffset;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    float FiringArcDegrees;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    float MountRotationOffset;
};

USTRUCT(BlueprintType)
struct FContactInfo
{
    GENERATED_BODY()
    UPROPERTY(BlueprintReadOnly)
    TWeakObjectPtr<AActor> DetectedActor;
    UPROPERTY(BlueprintReadOnly)
    FVector LastKnownPosition;
    UPROPERTY(BlueprintReadOnly)
    float DetectionConfidence;
    UPROPERTY(BlueprintReadOnly)
    EContactClassification Classification;
    UPROPERTY(BlueprintReadOnly)
    EDetectionMethod DetectionMethod;
    UPROPERTY(BlueprintReadOnly)
    float TimeSinceLastContact;
};

USTRUCT(BlueprintType)
struct FFleetTemplate
{
    GENERATED_BODY()
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    FName FleetName;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    TArray<TSubclassOf<AShipPawn>> ShipClasses;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    FVector SpawnAreaCenter;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    float SpawnAreaRadius;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    EFleetFormation DefaultFormation;
};

USTRUCT(BlueprintType)
struct FSupplyManifest
{
    GENERATED_BODY()
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply")
    float Fuel;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply")
    TMap<FName, int32> Ammo;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply")
    float Provisions;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply")
    int32 ReplacementCrew;
};
```

---

## 7. File Organization

```
Source/DeepCommand/Code/
|
+-- Actors/
|   +-- ShipPawn.h/.cpp                   // Base ship actor (composition root)
|   +-- SubmarinePawn.h/.cpp              // Extends ShipPawn with depth
|   +-- NavalBase.h/.cpp                  // Port/base actor
|   +-- WeaponMount.h/.cpp                // Physical weapon placement
|   +-- Torpedo.h/.cpp                    // Torpedo projectile
|   +-- Shell.h/.cpp                      // Gun shell projectile
|   +-- DepthCharge.h/.cpp                // Depth charge projectile
|   +-- SupplyCrate.h/.cpp                // Floating supply pickup
|   +-- SupplyDepot.h/.cpp                // Static supply point
|   +-- SmokescreenZone.h/.cpp            // Detection-blocking volume
|   +-- PatrolZone.h/.cpp                 // Area trigger
|   +-- EngagementArea.h/.cpp             // Battle boundary
|   +-- BattleSignalEmitter.h/.cpp        // Orchestration signals
|   +-- ReinforcementSpawner.h/.cpp       // Signal-driven reinforcements
|
+-- Components/
|   +-- AC_HullComponent.h/.cpp           // Per-zone hull, flooding, fire
|   +-- AC_NavalMovementComponent.h/.cpp  // Ship physics, heading, speed, depth
|   +-- AC_HelmComponent.h/.cpp           // Rudder + engine order telegraph
|   +-- AC_WeaponSystemComponent.h/.cpp   // Weapon mounts, fire control
|   +-- AC_DetectionComponent.h/.cpp      // Sonar, radar, visual, ESM
|   +-- AC_CrewComponent.h/.cpp           // Crew count, morale, damage control
|   +-- AC_FuelComponent.h/.cpp           // Fuel consumption and refuel
|   +-- AC_ShipStatusBarComponent.h/.cpp  // Overhead status display
|   +-- AC_OrderSystemComponent.h/.cpp    // Player order processing
|
+-- AI/
|   +-- AIC_ShipController.h/.cpp         // Base AI controller
|   +-- AIC_CapitalShipController.h/.cpp  // Battleship/carrier AI
|   +-- AIC_EscortController.h/.cpp       // Destroyer/frigate AI
|   +-- AIC_SubmarineController.h/.cpp    // Submarine stealth AI
|   +-- AIC_ConvoyController.h/.cpp       // Merchant waypoint AI
|   +-- Tasks/
|   |   +-- BTTask_NavigateShip.h/.cpp
|   |   +-- BTTask_EngageTarget.h/.cpp
|   |   +-- BTTask_EvadeContact.h/.cpp
|   |   +-- BTTask_MoveToWaypoint.h/.cpp
|   |   +-- BTTask_FormUp.h/.cpp
|   |   +-- BTTask_FireWeapon.h/.cpp
|   |   +-- BTTask_LaunchTorpedo.h/.cpp
|   |   +-- BTTask_ChangeDepth.h/.cpp
|   |   +-- BTTask_PatrolRoute.h/.cpp
|   |   +-- BTTask_DamageControl.h/.cpp
|   |   +-- BTTask_Resupply.h/.cpp
|   +-- Services/
|   |   +-- BTService_ScanContacts.h/.cpp
|   |   +-- BTService_TrackThreat.h/.cpp
|   |   +-- BTService_UpdateNavigation.h/.cpp
|   |   +-- BTService_AssessThreat.h/.cpp
|   |   +-- BTService_CheckSupply.h/.cpp
|   +-- Decorators/
|       +-- BTDecorator_HasRole.h/.cpp
|       +-- BTDecorator_HasAmmo.h/.cpp
|       +-- BTDecorator_IsEngaged.h/.cpp
|       +-- BTDecorator_BattlePhase.h/.cpp
|       +-- BTDecorator_HullAbove.h/.cpp
|
+-- Utility/
|   +-- Interfaces/
|   |   +-- IShipInterface.h
|   |   +-- INationInterface.h
|   |   +-- IDamageableInterface.h
|   |   +-- IDetectableInterface.h
|   +-- Enums/
|   |   +-- DeepCommandEnums.h
|   |   +-- NavalMovementEnums.h
|   |   +-- CombatEnums.h
|   |   +-- DiplomacyEnums.h
|   +-- Structs/
|   |   +-- NavalStructs.h
|   |   +-- ContactStructs.h
|   |   +-- FleetStructs.h
|   |   +-- SupplyStructs.h
|   +-- Helpers/
|       +-- NavalMath.h/.cpp
|       +-- BallisticsHelper.h/.cpp
|
+-- UI/
|   +-- StrategicMapWidget.h/.cpp
|   +-- TacticalHUDWidget.h/.cpp
|   +-- ShipInfoPanel.h/.cpp
|   +-- FleetPanel.h/.cpp
|   +-- DiplomacyPanel.h/.cpp
|   +-- TimeControlWidget.h/.cpp
|   +-- MiniMapWidget.h/.cpp
|
+-- GameModes/
|   +-- DeepCommandGameMode.h/.cpp
|   +-- DeepCommandGameInstance.h/.cpp
|
+-- Subsystems/
|   +-- FleetManagerSubsystem.h/.cpp
|   +-- BattleSubsystem.h/.cpp
|   +-- SupplyChainSubsystem.h/.cpp
|   +-- DiplomacySubsystem.h/.cpp
|   +-- TimeManagerSubsystem.h/.cpp
|   +-- IntelligenceSubsystem.h/.cpp
|
+-- Data/
    +-- ShipClassData.h/.cpp
    +-- WeaponData.h/.cpp
    +-- NationData.h/.cpp
    +-- OfficerTraitData.h/.cpp
    +-- ScenarioData.h/.cpp
```

### File Count

| Category | Pairs (h+cpp) | Notes |
|---|---|---|
| Actors | 14 | Ship types + projectiles + world actors |
| Components | 9 | Core ship systems |
| AI Controllers | 5 | Per ship archetype |
| AI BT Tasks | 11 | Actions |
| AI BT Services | 5 | Monitoring |
| AI BT Decorators | 5 | Conditions |
| Utility | 10 | Interfaces + enums + structs + helpers |
| UI | 7 | Widgets |
| GameModes | 2 | Mode + Instance |
| Subsystems | 6 | Persistent state managers |
| Data | 5 | DataAsset definitions |
| **TOTAL** | **79 pairs (158 files)** | |

---

## Appendix A: Implementation Priority

Phase 1 (Vertical Slice):
ShipPawn + AC_HullComponent + AC_NavalMovementComponent + AC_HelmComponent +
AIC_ShipController + BTTask_NavigateShip + TimeManagerSubsystem

Phase 2 (Combat):
AC_WeaponSystemComponent + AC_DetectionComponent + Shell + Torpedo +
BattleSubsystem + BTTask_FireWeapon + BTTask_EngageTarget

Phase 3 (Fleet):
FleetManagerSubsystem + Formations + Fleet orders + Multiple controllers

Phase 4 (Supply):
AC_FuelComponent + AC_CrewComponent + SupplyChainSubsystem + Convoys

Phase 5 (Diplomacy):
DiplomacySubsystem + NationData + AI personalities + Treaties

Phase 6 (Polish):
UI widgets + Strategic map + Scenarios + Balancing

---

## Appendix B: Design Decisions

| Decision | Rationale | Alternative |
|---|---|---|
| GameInstanceSubsystems | Persists across levels | GameMode (single level only) |
| Per-zone hull | Tactical targeting of sections | Single HP pool |
| Velocity-based movement | Ships not on walkable surfaces | NavMesh (broken for ships) |
| DataAssets for config | Native UE5 editor workflow | INI files |
| Separate Detection comp | Confidence + classification | Raw AI Perception |
| FName for types | Designer-expandable | Enums (recompile per type) |
| Observer everywhere | Proven in Quidditch audit | Direct calls (coupling) |
| Composition over inherit | Different component combos | Deep class hierarchy |

---


---

## 8. Component Architecture Detail

### 8.1 AC_HullComponent (from AC_HealthComponent)

Source: AC_HealthComponent (single float HP with OnDeath delegate)
Target: 5-zone hull system with flooding and fire propagation

Core API (player input and AI call the same functions):
- ApplyZoneDamage(EHullZone Zone, float Damage, AActor* Instigator)
- RepairZone(EHullZone Zone, float Amount)
- GetZoneIntegrity(EHullZone Zone) -> float
- GetOverallIntegrity() -> float  // weighted average
- IsZoneCritical(EHullZone Zone) -> bool
- IsFlooding() -> bool
- HasFire() -> bool

Internal state per zone (USTRUCT FHullZoneState):
- float CurrentIntegrity
- float MaxIntegrity  // from ShipClassData
- float FloodingRate  // 0.0 = none, increases as integrity drops
- bool bOnFire
- float FireSpreadTimer

Cascading damage rules:
- Keel breach -> flooding spreads to adjacent zones
- Superstructure destroyed -> detection range halved
- Stern destroyed -> max speed halved
- Bow destroyed -> turning rate halved
- All zones below 25% -> ship sinks (FOnShipDestroyed broadcast)

### 8.2 AC_NavalMovementComponent (from AC_BroomComponent)

Source: AC_BroomComponent (SetVerticalInput, SetBoostEnabled, SetFlightEnabled)
Target: Ship movement with engine orders, rudder, and depth control

Core API:
- SetEngineOrder(EEngineOrder Order)  // replaces SetBoostEnabled
- SetRudder(float Angle)              // replaces SetVerticalInput
- SetTargetDepth(float Depth)          // replaces SetFlightEnabled (subs)
- GetCurrentSpeed() -> float
- GetCurrentHeading() -> float
- GetCurrentDepth() -> float           // 0 = surface
- IsSubmerged() -> bool                // replaces IsFlying()

EEngineOrder values:
AheadFlank, AheadFull, AheadStandard, AheadSlow, AllStop, AsternSlow, AsternFull

Movement is velocity-based (NO NavMesh). Direct world-space translation.
Fuel consumed per tick based on engine order from FuelComponent.
Speed affected by hull damage (stern zone integrity).

### 8.3 AC_WeaponSystemComponent

Source: AIC_BaseAgentAIController ammo tracking (moved to component)

Core API:
- Fire(FName WeaponType, AActor* Target)
- Reload(FName WeaponType)
- GetAmmo(FName WeaponType) -> int32
- GetWeaponMounts() -> TArray<FWeaponMount>
- CanFire(FName WeaponType) -> bool
- HasFiringSolution(FName WeaponType, AActor* Target) -> bool

Weapon mounts configured via ShipClassData.
WeaponData DataAssets define damage, range, reload, accuracy.
FName-based weapon types allow designer expansion without C++ changes.

### 8.4 AC_DetectionComponent

Source: AIPerception wrapper from QuidditchController

Core API:
- SetDetectionMode(EDetectionMode Mode)  // Passive, Active, Silent
- GetDetectedContacts() -> TArray<FDetectedContact>
- GetContactByActor(AActor*) -> FDetectedContact
- IsContactValid(AActor*) -> bool

Detection methods:
- Radar: Long range, blocked by terrain, reveals bearing + range
- Sonar (passive): Medium range, detects submarines, bearing only
- Sonar (active): Long range, bearing + range, but reveals YOUR position
- Visual: Short range, affected by weather/time of day
- ESM: Detects radar emissions, bearing only

### 8.5 AC_CrewComponent

Core API:
- GetCrewCount() -> int32
- GetCrewEfficiency() -> float  // 0.0-1.0, affects all ship performance
- ApplyCasualties(int32 Count)
- RestCrew(float DeltaTime)
- GetMorale() -> float

Crew efficiency multiplies weapon accuracy, speed, detection range.
Below MinimumCrew from ShipClassData, severe penalties apply.

### 8.6 AC_FuelComponent

Source: AC_StaminaComponent drain/regen pattern

Core API:
- GetFuelLevel() -> float
- GetFuelPercentage() -> float
- ConsumeFuel(float Amount)
- Refuel(float Amount)
- GetEstimatedRange(EEngineOrder Order) -> float

Drain rate from ShipClassData FuelConsumptionPerKnot * current speed.
Broadcasts FOnFuelLow at 25%, FOnFuelCritical at 10%.

## 9. Enum Definitions (DeepCommandTypes.h)

UENUM(BlueprintType)
enum class ENation : uint8
{
    None           UMETA(DisplayName = "None"),
    UnitedStates   UMETA(DisplayName = "United States"),
    UnitedKingdom  UMETA(DisplayName = "United Kingdom"),
    Germany        UMETA(DisplayName = "Germany"),
    Japan          UMETA(DisplayName = "Japan"),
    Italy          UMETA(DisplayName = "Italy"),
    France         UMETA(DisplayName = "France"),
    SovietUnion    UMETA(DisplayName = "Soviet Union"),
    MAX            UMETA(Hidden)
};

// Closed set: nations are historical, not designer-expandable.
// Use UENUM (not FName) because nation identity drives
// compile-time branching in diplomacy, AI, and GenericTeamAgent.

UENUM(BlueprintType)
enum class EHullZone : uint8
{
    Bow, Midships, Stern, Keel, Superstructure, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EEngineOrder : uint8
{
    AheadFlank, AheadFull, AheadStandard, AheadSlow,
    AllStop,
    AsternSlow, AsternFull,
    MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EShipCategory : uint8
{
    Destroyer, Cruiser, Battleship, Carrier, Submarine, Transport, Auxiliary,
    MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EWeaponCategory : uint8
{
    Gun, Torpedo, DepthCharge, Mine, AntiAir, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EDetectionMethod : uint8
{
    Radar, SonarPassive, SonarActive, Visual, ESM, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EDetectionMode : uint8
{
    Passive, Active, Silent, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EDiplomaticStatus : uint8
{
    Allied, Friendly, Neutral, Hostile, AtWar, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EScenarioPhase : uint8
{
    Setup, Deployment, Active, Resolution, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EFleetOrder : uint8
{
    HoldPosition, Patrol, Engage, Escort, Withdraw, Resupply, Hunt,
    MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EFormationType : uint8
{
    LineAhead, LineAbreast, Diamond, Screen, Convoy, Scattered,
    MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class ESupplyType : uint8
{
    Fuel, Ammunition, Provisions, RepairMaterials, MAX UMETA(Hidden)
};

UENUM(BlueprintType)
enum class EContactClassification : uint8
{
    Unknown, Possible, Probable, Confirmed, MAX UMETA(Hidden)
};
---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1-2)
Priority: Get a ship moving and taking damage.

1. DeepCommandTypes.h -- All enums and structs
2. AC_HullComponent -- 5-zone hull with delegates
3. AC_NavalMovementComponent -- Engine orders + rudder
4. AC_FuelComponent -- Fuel consumption
5. ABaseVessel -- Pawn with all components attached
6. APlayerFlagship -- Enhanced Input bindings
7. ADeepCommandGameMode -- Minimal scenario loading

Vertical slice: Player ship moves, turns, takes zone damage, sinks.

### Phase 2: Combat (Week 3-4)
Priority: Ships can fight each other.

1. AC_WeaponSystemComponent -- Weapon mounts, firing, ammo
2. AShell + ATorpedo -- Projectile actors
3. AC_DetectionComponent -- Radar + visual detection
4. UShipClassData + UWeaponData -- DataAssets
5. ASurfaceShip -- AI-controlled surface vessel
6. AIC_ShipController -- Base AI with BB keys
7. BTTask_NavigateShip + BTTask_FireWeapon -- Core BT nodes

Vertical slice: Player and AI ships detect and shoot each other.

### Phase 3: Fleet Management (Week 5-6)
Priority: Multiple ships under player command.

1. UFleetManagerSubsystem -- Ship registry + task forces
2. UFormationData -- Formation positions
3. BTTask_MoveToWaypoint -- Formation keeping
4. AIC_FleetCommanderController -- Task force AI
5. UFleetOrderWidget -- Player fleet command UI
6. UTacticalHUDWidget -- Ship status HUD

Vertical slice: Player commands a task force in formation.

### Phase 4: Submarines (Week 7-8)
Priority: Submarine stealth gameplay loop.

1. ASubmarineVessel -- Depth management
2. AIC_SubmarineController -- Depth + stealth AI
3. Sonar detection in AC_DetectionComponent
4. ATorpedo guidance system
5. ADepthCharge -- Anti-sub weapon
6. BTTask_SetDepth + BTTask_LaunchTorpedo

Vertical slice: Submarine hunts convoy, escorts counter-attack.

### Phase 5: Supply and Diplomacy (Week 9-10)
Priority: Strategic layer.

1. USupplyChainSubsystem -- Routes, convoys, ports
2. UDiplomacySubsystem -- Nation attitudes, treaties
3. UIntelligenceSubsystem -- Fog of war
4. UTimeManagerSubsystem -- Pause/speed control
5. UNationData + UScenarioData -- DataAssets
6. UStrategicMapWidget -- Top-down overview
7. UDiplomacyPanelWidget

Vertical slice: Full scenario with supply lines and nation AI.

### Phase 6: Polish (Week 11-12)
Priority: Steam Early Access readiness.

1. AC_CrewComponent -- Crew progression
2. UOfficerTraitData -- Officer traits
3. UShipStatusWidget -- Detailed ship view
4. Save/Load system
5. Main menu and settings
6. Tutorial scenario
---

## 11. Design Decisions and Risk Assessment

### 11.1 Key Architecture Decisions

Decision 1: GameInstanceSubsystem over GameMode for fleet state
- Rationale: Fleet composition must persist across level transitions.
  GameMode is destroyed on map change. GameInstanceSubsystem survives.
- Trade-off: More complex initialization, but correct for strategy game.
- Source: QuidditchGameMode was a monolith. This decomposes into 5 subsystems.

Decision 2: UENUM for ENation (not FName)
- Rationale: Nations are a closed historical set (7 WW2 nations).
  FName is for designer-expandable types (weapon names, ship classes).
  Nation identity drives compile-time branching in diplomacy and AI.
- Trade-off: Adding a nation requires C++ rebuild. Acceptable for DLC-level content.

Decision 3: 5-zone hull model (not single HP float)
- Rationale: Zone damage creates tactical depth (bow vs stern vs keel).
  Cascading effects (flooding, fire) emerge from zone interactions.
- Trade-off: Complexity lives in AC_HullComponent. External API stays simple.

Decision 4: Velocity-based movement (no NavMesh)
- Rationale: Ships in open water need no pathfinding. Direct velocity from
  AC_BroomComponent pattern. Submarines add depth axis.
- Source: WizardJam broom flight uses pure velocity. Zero NavMesh confirmed.

Decision 5: Core API pattern (player and AI share same interface)
- Rationale: SetEngineOrder(), SetRudder(), SetTargetDepth() work identically
  from Enhanced Input or BT task. Component is caller-agnostic.
- Source: AC_BroomComponent SetVerticalInput/SetBoostEnabled/SetFlightEnabled.

Decision 6: AC_DetectionComponent wraps AIPerception
- Rationale: Naval detection has multiple methods (radar, sonar, visual, ESM).
  Component provides naval-specific API while using AIPerception internally.

Decision 7: FName for weapon types (not UENUM)
- Rationale: Designers add weapon variants without C++ changes.
  Same category (Gun) can have many FName variants with different DataAssets.
- Source: WizardJam spell channels use FName. Designer-expandable.
### 11.2 Risk Assessment

Risk 1: Subsystem initialization order
- Likelihood: Medium
- Issue: GameInstanceSubsystems init in undefined order.
- Mitigation: No cross-subsystem calls in Initialize().
  Lazy resolution on first use. Cache pointer.
- Fallback: Custom GameInstance with explicit init ordering.

Risk 2: Delegate unbinding on level transition
- Likelihood: High
- Issue: Ships destroyed during transition may leave dangling bindings.
- Mitigation: TWeakObjectPtr for ship references in subsystems.
  RemoveDynamic in both EndPlay AND OnUnPossess.
- Fallback: Subsystem ClearAllDelegates() on level pre-load.

Risk 3: Blackboard silent failures
- Likelihood: High (proven in WizardJam)
- Issue: FBlackboardKeySelector without filter + resolve silently fails.
- Mitigation: Mandatory review checklist for ALL BT nodes.
  Linked Systems Checklist before feature sign-off.

Risk 4: Save/Load with 5 subsystems
- Likelihood: Medium
- Issue: Serialization must capture all subsystem state atomically.
- Mitigation: ISaveableSubsystem interface with Serialize/Deserialize.
- Fallback: Defer save/load to Phase 6 (polish).

Risk 5: Performance with 50+ ships
- Likelihood: Low-Medium
- Issue: Many ships with 7 components each could strain frame budget.
- Mitigation: Stagger BTService ticks. AIPerception spatial partitioning.
  LOD for distant ship component updates.
- Fallback: Pool/deactivate ships outside camera frustum.
---

## 12. Interface Specifications

### IShipInterface
// All ship actors implement. Uniform access to ship data.
virtual FName GetShipClassName() const = 0;
virtual ENation GetNation() const = 0;
virtual EShipCategory GetShipCategory() const = 0;
virtual AC_HullComponent* GetHullComponent() const = 0;
virtual AC_NavalMovementComponent* GetMovementComponent() const = 0;
virtual AC_WeaponSystemComponent* GetWeaponSystem() const = 0;
virtual AC_DetectionComponent* GetDetectionComponent() const = 0;

### IDamageableInterface
// Any actor receiving zone-based damage.
virtual void ApplyDamage(float Damage, EHullZone Zone, AActor* Instigator) = 0;
virtual float GetIntegrity(EHullZone Zone) const = 0;
virtual bool IsDestroyed() const = 0;

### IDetectableInterface
// Any actor detectable by radar/sonar/visual.
virtual float GetRadarCrossSection() const = 0;
virtual float GetAcousticSignature() const = 0;
virtual float GetVisualProfile() const = 0;
virtual bool IsSubmerged() const = 0;

### IResupplyInterface
// Ports and supply ships that resupply other ships.
virtual bool CanResupply(ESupplyType Type) const = 0;
virtual float TransferSupply(ESupplyType Type, float RequestedAmount) = 0;
virtual bool CanRepair() const = 0;
virtual void RepairShip(AActor* Ship, EHullZone Zone, float Amount) = 0;

### INationInterface
// Nation state objects.
virtual ENation GetNationID() const = 0;
virtual EDiplomaticStatus GetAttitudeToward(ENation Other) const = 0;
virtual FLinearColor GetNationColor() const = 0;

### IDockyardInterface
// Ports with repair and refit capability.
virtual bool HasRepairCapacity() const = 0;
virtual float GetRepairRate() const = 0;
virtual bool CanRefit(UShipClassData* NewClass) const = 0;

### IBoardableInterface
// Ships that can be boarded and captured.
virtual bool CanBeBoarded() const = 0;
virtual int32 GetDefenderCount() const = 0;
virtual void OnBoarded(AActor* Boarder) = 0;
---

## Summary

Total source files: ~60 (30 headers + 30 implementations)
Components: 7 (Hull, Movement, Weapon, Detection, Crew, Supply, Fuel)
Interfaces: 7 (Ship, Damageable, Detectable, Nation, Resupply, Dockyard, Boardable)
Subsystems: 5 (FleetManager, SupplyChain, Diplomacy, TimeManager, Intelligence)
DataAssets: 6 (ShipClass, Weapon, Nation, OfficerTrait, Scenario, Formation)
AI Controllers: 3 (Ship, FleetCommander, Submarine)
BT Nodes: 16 (9 tasks, 4 services, 3 decorators)
Enums: 13

Every component follows the Core API pattern: player input and AI
call the same verb functions. Components do not care who calls them.

All cross-system communication via DECLARE_DYNAMIC_MULTICAST_DELEGATE.
Zero polling. Zero GameplayStatics. Zero direct GameMode calls.

All gameplay values from UPrimaryDataAsset subclasses.
Zero hardcoded numbers in C++ source.
