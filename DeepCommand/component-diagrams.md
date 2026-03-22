# Deep Command Component Architecture Diagrams

Developer: Marcus Daley
Date: 2026-03-02
Engine: Unreal Engine 5.4 (C++)

---

## 1. Component Inheritance Hierarchy

```
UActorComponent (Engine)
|
+-- AC_HullComponent
|   // Per-zone integrity, flooding, fire, sinking detection
|   // Delegates: OnHullZoneDamaged, OnHullZoneBreached,
|   //   OnFloodingChanged, OnFireStateChanged, OnShipSinking
|
+-- AC_NavalMovementComponent
|   // Ship physics: heading, speed, rudder, engine orders, depth
|   // Delegates: OnSpeedChanged, OnHeadingChanged, OnDepthChanged
|   // Core API: SetRudder(), SetEngineOrder(), SetTargetDepth()
|
+-- AC_HelmComponent
|   // Engine order telegraph + rudder command processing
|   // Translates player/AI commands into NavalMovement inputs
|
+-- AC_WeaponSystemComponent
|   // Manages TArray<FWeaponMountConfig>, fire control, ammo
|   // Delegates: OnWeaponFired, OnWeaponReloaded,
|   //   OnWeaponAmmoExpended, OnWeaponMountDestroyed
|
+-- AC_DetectionComponent
|   // Sonar, radar, visual, ESM with confidence levels
|   // Wraps AI Perception with classification logic
|   // Delegates: OnContactDetected, OnContactLost
|
+-- AC_CrewComponent
|   // Crew count, morale, damage control teams, efficiency
|   // Delegates: OnCrewCasualty, OnMoraleChanged,
|   //   OnCrewEfficiencyChanged
|
+-- AC_FuelComponent
|   // Fuel consumption per engine order, refuel from supply
|   // Delegates: OnFuelChanged, OnFuelDepleted, OnResupplied
|
+-- AC_ShipStatusBarComponent
|   // Overhead widget showing hull %, speed, alerts
|   // Binds to HullComponent + NavalMovement delegates
|
+-- AC_OrderSystemComponent
    // Player order input: move, attack, patrol, escort
    // Translates UI clicks into fleet subsystem commands
```

---

## 2. Ship Actor Composition

### 2.1 AShipPawn (Surface Vessel)

```
AShipPawn : APawn, IShipInterface, IDamageableInterface, IDetectableInterface
|
+-- UStaticMeshComponent* ShipMesh          [Root]
|
+-- AC_HullComponent* HullComp             [Required]
|   5 zones: Bow, Midship, Stern, Keel, Superstructure
|   Each zone: independent integrity, armor, flood/fire state
|   Configured via UShipClassData->HullZones array
|
+-- AC_NavalMovementComponent* MovementComp [Required]
|   Heading, speed, engine orders
|   Reads MaxSpeed/Acceleration/TurnRate from UShipClassData
|   Core API used by both player input and AI BT tasks
|
+-- AC_HelmComponent* HelmComp              [Required]
|   Processes rudder and engine telegraph commands
|   Applies turn rate and acceleration limits
|
+-- AC_WeaponSystemComponent* WeaponComp    [Optional per class]
|   TArray<FWeaponMountConfig> from UShipClassData
|   Each mount: position, firing arc, weapon data, ammo
|   Transport/Tanker ships may have no weapons
|
+-- AC_DetectionComponent* DetectionComp    [Required]
|   Radar range, sonar range, visual range from UShipClassData
|   Feeds contacts to IntelligenceSubsystem
|
+-- AC_CrewComponent* CrewComp              [Required]
|   CrewComplement from UShipClassData
|   Morale affects weapon reload and movement efficiency
|
+-- AC_FuelComponent* FuelComp              [Required]
|   FuelCapacity from UShipClassData
|   Drain rate varies by EEngineOrder
|
+-- UAIPerceptionStimuliSourceComponent*    [Required]
    Makes ship detectable by other AI perception systems
    Radar cross section + acoustic signature from UShipClassData
```

### 2.2 ASubmarinePawn (Extends ShipPawn)

```
ASubmarinePawn : AShipPawn
|
+-- [All ShipPawn components inherited]
|
+-- Additional NavalMovement capabilities:
|   SetTargetDepth(float) -- submarine-only API
|   OnDepthChanged delegate -- broadcasts depth changes
|   MaxDepthMeters from UShipClassData
|
+-- Detection behavior changes with depth:
|   Periscope depth: visual + radar available
|   Submerged: sonar only, reduced radar cross section
|   Deep: passive sonar only, minimal detection signature
|
+-- Unique BB keys: CurrentDepth, TargetDepth, bIsSubmerged,
    bPeriscopeUp, bDetectedByEnemy, TorpedoCount
```

### 2.3 Component Lifecycle

```
Constructor:
  Create all components with CreateDefaultSubobject
  Initialize defaults from constructor init list
  NO gameplay logic

BeginPlay:
  1. Load UShipClassData and apply to components
  2. Bind cross-component delegates:
     HullComp->OnHullZoneBreached -> WeaponComp::HandleZoneDestroyed
     HullComp->OnHullZoneBreached -> CrewComp::HandleZoneDamaged
     CrewComp->OnCrewEfficiencyChanged -> WeaponComp (reload speed)
     CrewComp->OnCrewEfficiencyChanged -> MovementComp (max speed)
     FuelComp->OnFuelDepleted -> MovementComp::HandleFuelDepleted
  3. Register with FleetManagerSubsystem
  4. Register with IntelligenceSubsystem

EndPlay:
  1. Unbind ALL cross-component delegates (RemoveDynamic)
  2. Unregister from FleetManagerSubsystem
  3. Unregister from IntelligenceSubsystem
```

---

## 3. Delegate Communication Flow

### 3.1 Damage Event Flow

```
Incoming Damage (ATorpedo/AShell hit)
|
v
AC_HullComponent::ApplyDamage(Zone, Amount, DamageType)
|
+-- Reduce zone integrity
|
+-- OnHullZoneDamaged.Broadcast(Zone, NewIntegrity, DamageAmount)
|   |
|   +---> AC_CrewComponent::HandleHullZoneDamaged()
|   |     Calculate crew casualties for zone
|   |     OnCrewCasualty.Broadcast(Zone, Casualties)
|   |     Recalculate crew efficiency
|   |     OnCrewEfficiencyChanged.Broadcast(NewEfficiency)
|   |           |
|   |           +---> AC_WeaponSystemComponent (reload speed modifier)
|   |           +---> AC_NavalMovementComponent (max speed modifier)
|   |
|   +---> AAIC_ShipController::HandleHullDamaged()
|   |     SetBB("HullIntegrity", OverallIntegrity)
|   |     SetBB("IsUnderAttack", true)
|   |     BT decorators auto re-evaluate
|   |
|   +---> TacticalHUDWidget::HandleHullUpdate()
|         Update hull diagram display
|
+-- [If integrity <= 0] OnHullZoneBreached.Broadcast(Zone)
|   |
|   +---> AC_WeaponSystemComponent::HandleZoneDestroyed()
|   |     Disable weapon mounts in this zone
|   |     OnWeaponMountDestroyed.Broadcast(MountIndex, Zone)
|   |
|   +---> [If bCanFlood] OnFloodingChanged.Broadcast(Zone, FloodPercent)
|         Flooding increases over time in TickComponent
|         If total flooding exceeds threshold:
|         OnShipSinking.Broadcast(Ship)
```

### 3.2 Fleet Order Flow (Gas Station Pattern)

```
Player issues fleet order via UI
|
v
AC_OrderSystemComponent::IssueFleetOrder(FleetName, Order, Target)
|
v
UFleetManagerSubsystem::DispatchOrder(FleetName, Order, Target)
|
+-- OnFleetOrderIssued.Broadcast(FleetName, Order, Target)
    |
    +---> AAIC_ShipController_1::HandleFleetOrderIssued()
    |     if (MyFleetName != FleetName) return;  // Filter
    |     SetBB("OrderType", Order)
    |     SetBB("TargetLocation", Target)
    |     BT root re-evaluates -> Execute Orders branch activates
    |
    +---> AAIC_ShipController_2::HandleFleetOrderIssued()
    |     Same filtering + BB update
    |
    +---> FleetPanel::HandleOrderConfirmed()
          Update UI order indicator
```

### 3.3 Detection -> Intelligence Flow

```
AC_DetectionComponent::TickComponent()
|
+-- Process AI Perception updates
+-- For each new detection:
    |
    v
    OnContactDetected.Broadcast(Actor, Method, Confidence)
    |
    +---> AAIC_ShipController::HandleContactDetected()
    |     SetBB("HasTarget", true)
    |     SetBB("TargetActor", HighestPriorityContact)
    |     BTService_AssessThreat recalculates threat level
    |
    +---> UIntelligenceSubsystem::AggregateContact()
    |     Merge with other ships detecting same contact
    |     Increase confidence if multiple detections
    |     Classify: Unknown -> Probable -> Confirmed
    |     Share with allied nations
    |
    +---> StrategicMapWidget::HandleNewContact()
          Add/update contact marker on map
```

### 3.4 Supply Chain Flow

```
USupplyChainSubsystem::DispatchConvoy(Route)
|
+-- Spawn AConvoyShip actors
+-- AIC_ConvoyController possesses each ship
+-- Convoy follows waypoint route
|
[Convoy arrives at destination]
|
v
OnSupplyDelivered.Broadcast(ReceiverShip, Manifest)
|
+---> AC_FuelComponent::HandleResupply(Manifest.Fuel)
|     Restore fuel -> OnFuelChanged.Broadcast(NewPercent)
|
+---> AC_WeaponSystemComponent::HandleResupply(Manifest.Ammo)
|     Reload weapon mounts -> OnWeaponReloaded.Broadcast()
|
+---> AC_CrewComponent::HandleReplacements(Manifest.ReplacementCrew)
      Add crew, recalculate efficiency
```

---

## 4. AI Controller -> Ship Pawn Data Flow

### 4.1 OnPossess Sequence

```
AAIC_ShipController::OnPossess(InPawn)
|
+-- Super::OnPossess(InPawn)
|
+-- Cache component pointers:
|   HullComp = InPawn->FindComponentByClass<AC_HullComponent>()
|   MovementComp = InPawn->FindComponentByClass<AC_NavalMovementComponent>()
|   WeaponComp = InPawn->FindComponentByClass<AC_WeaponSystemComponent>()
|   DetectionComp = InPawn->FindComponentByClass<AC_DetectionComponent>()
|   FuelComp = InPawn->FindComponentByClass<AC_FuelComponent>()
|
+-- SetupBlackboard(InPawn):
|   BB->SetValueAsObject("SelfActor", InPawn)
|   BB->SetValueAsFloat("HullIntegrity", 1.0f)
|   BB->SetValueAsFloat("FuelRemaining", 1.0f)
|   BB->SetValueAsBool("HasTarget", false)
|   BB->SetValueAsBool("IsEngaged", false)
|   BB->SetValueAsBool("IsUnderAttack", false)
|   BB->SetValueAsName("ShipRole", ShipRole)
|   BB->SetValueAsName("FleetName", FleetName)
|
+-- Bind component delegates:
|   HullComp->OnHullZoneDamaged.AddDynamic(this, &HandleHullDamaged)
|   MovementComp->OnSpeedChanged.AddDynamic(this, &HandleSpeedChanged)
|   DetectionComp->OnContactDetected.AddDynamic(this, &HandleContact)
|   FuelComp->OnFuelChanged.AddDynamic(this, &HandleFuelChanged)
|
+-- Bind subsystem delegates:
|   FleetMgr->OnFleetOrderIssued.AddDynamic(this, &HandleFleetOrder)
|   BattleSub->OnBattlePhaseChanged.AddDynamic(this, &HandlePhase)
|
+-- RunBehaviorTree(BehaviorTreeAsset)
```

### 4.2 Delegate -> Blackboard -> BT Flow

```
[Component state changes]
|
v
Delegate fires (e.g., OnHullZoneDamaged)
|
v
AAIC_ShipController::HandleHullDamaged(Zone, Integrity, Amount)
|
+-- BB->SetValueAsFloat("HullIntegrity", CalcOverallIntegrity())
+-- BB->SetValueAsBool("IsUnderAttack", true)
|
v
[Blackboard value changed]
|
v
BT Decorators auto re-evaluate:
  BTDecorator_HullAbove checks BB.HullIntegrity
  -> If below threshold, Emergency branch activates
  -> BTTask_DamageControl executes
  -> BTTask_NavigateShip to nearest port
```

### 4.3 BT Task -> Component Command Flow

```
BTTask_NavigateShip::ExecuteTask()
|
+-- Read BB.TargetLocation
+-- Calculate heading to target
+-- Calculate distance
|
+-- Call component Core API:
|   MovementComp->SetRudder(DesiredTurnRate)
|   MovementComp->SetEngineOrder(DesiredSpeed)
|
+-- MovementComp::TickComponent() applies physics
|   Updates heading, applies acceleration, moves pawn
|   OnSpeedChanged.Broadcast() -> Controller updates BB
|   OnHeadingChanged.Broadcast() -> Controller updates BB
|
+-- BTTask checks arrival:
    if (Distance < AcceptRadius)
        return EBTNodeResult::Succeeded
```

### 4.4 OnUnPossess Cleanup

```
AAIC_ShipController::OnUnPossess()
|
+-- Unbind ALL component delegates:
|   HullComp->OnHullZoneDamaged.RemoveDynamic(this, &HandleHull)
|   MovementComp->OnSpeedChanged.RemoveDynamic(this, &HandleSpeed)
|   DetectionComp->OnContactDetected.RemoveDynamic(this, &HandleContact)
|   FuelComp->OnFuelChanged.RemoveDynamic(this, &HandleFuel)
|
+-- Unbind ALL subsystem delegates:
|   FleetMgr->OnFleetOrderIssued.RemoveDynamic(this, &HandleOrder)
|   BattleSub->OnBattlePhaseChanged.RemoveDynamic(this, &HandlePhase)
|
+-- Super::OnUnPossess()
```

---

End of Component Architecture Diagrams
