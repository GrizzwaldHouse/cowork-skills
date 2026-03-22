# Task: Health & Damage System with AC_HealthComponent Pattern

## Purpose
Implement a reusable health/damage system using ActorComponent composition and delegate-driven death handling. This pattern enables modular health tracking for any actor without inheritance, with automatic cleanup and event broadcasting on death.

## Prerequisites
- Unreal Engine 5.4 C++ project
- Understanding of ActorComponent lifecycle (BeginPlay, EndPlay)
- Familiarity with DECLARE_DYNAMIC_MULTICAST_DELEGATE macros
- Knowledge of Unreal's TakeDamage system integration

## Source Code Reference
**Island Escape (BaseGame/END2507):**
- `Source/END2507/Code/Components/AC_HealthComponent.h` (lines 1-50)
- `Source/END2507/Code/Components/AC_HealthComponent.cpp` (lines 1-120)

**Key Pattern Elements:**
- Single float HP with max HP property
- OnDeath delegate for cleanup coordination
- Integration with AActor::TakeDamage() flow
- Constructor initialization list for defaults

## Implementation Steps

### Step 1: Create Component Header
```cpp
// AC_HealthComponent.h
// Developer: [Your Name]
// Date: [YYYY-MM-DD]
// Purpose: Reusable health tracking component with delegate-driven death handling
// Usage: Add to any actor requiring health/damage functionality

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "AC_HealthComponent.generated.h"

// Delegate signature: broadcasts when health reaches zero
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDeath, AActor*, DeadActor);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURPROJECT_API UAC_HealthComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UAC_HealthComponent();

    // ====================================================================
    // PUBLIC API
    // ====================================================================

    // Apply damage to this component's owner
    UFUNCTION(BlueprintCallable, Category = "Health")
    void TakeDamage(float DamageAmount, AActor* DamageCauser);

    // Restore health (clamped to MaxHealth)
    UFUNCTION(BlueprintCallable, Category = "Health")
    void Heal(float HealAmount);

    // Query current health state
    UFUNCTION(BlueprintPure, Category = "Health")
    float GetCurrentHealth() const { return CurrentHealth; }

    UFUNCTION(BlueprintPure, Category = "Health")
    float GetMaxHealth() const { return MaxHealth; }

    UFUNCTION(BlueprintPure, Category = "Health")
    float GetHealthRatio() const { return CurrentHealth / MaxHealth; }

    UFUNCTION(BlueprintPure, Category = "Health")
    bool IsDead() const { return CurrentHealth <= 0.0f; }

    // ====================================================================
    // DELEGATES
    // ====================================================================

    // Fired when health reaches zero
    UPROPERTY(BlueprintAssignable, Category = "Health|Events")
    FOnDeath OnDeath;

protected:
    virtual void BeginPlay() override;

private:
    // ====================================================================
    // PROPERTIES (EditDefaultsOnly - designer configures per class)
    // ====================================================================

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health",
        meta = (AllowPrivateAccess = "true", ClampMin = "1.0"))
    float MaxHealth;

    // Current health (runtime state)
    UPROPERTY()
    float CurrentHealth;
};
```

### Step 2: Implement Component Logic
```cpp
// AC_HealthComponent.cpp

#include "AC_HealthComponent.h"
#include "GameFramework/Actor.h"

// Constructor: Initialize with defaults via init list
UAC_HealthComponent::UAC_HealthComponent()
    : MaxHealth(100.0f)
    , CurrentHealth(0.0f)  // Set in BeginPlay
{
    PrimaryComponentTick.bCanEverTick = false;  // No tick needed
}

void UAC_HealthComponent::BeginPlay()
{
    Super::BeginPlay();

    // Initialize current health to max at start of play
    CurrentHealth = MaxHealth;

    UE_LOG(LogTemp, Log, TEXT("[%s] HealthComponent initialized: %.1f / %.1f HP"),
        *GetOwner()->GetName(), CurrentHealth, MaxHealth);
}

void UAC_HealthComponent::TakeDamage(float DamageAmount, AActor* DamageCauser)
{
    if (DamageAmount <= 0.0f || IsDead())
    {
        return;  // Ignore negative damage or damage to dead actors
    }

    // Reduce health
    CurrentHealth = FMath::Max(0.0f, CurrentHealth - DamageAmount);

    UE_LOG(LogTemp, Log, TEXT("[%s] Took %.1f damage from [%s]. HP: %.1f / %.1f"),
        *GetOwner()->GetName(),
        DamageAmount,
        DamageCauser ? *DamageCauser->GetName() : TEXT("Unknown"),
        CurrentHealth,
        MaxHealth);

    // Check for death
    if (IsDead())
    {
        UE_LOG(LogTemp, Warning, TEXT("[%s] DIED! Broadcasting OnDeath delegate."),
            *GetOwner()->GetName());

        // Broadcast death event - listeners handle cleanup
        OnDeath.Broadcast(GetOwner());
    }
}

void UAC_HealthComponent::Heal(float HealAmount)
{
    if (HealAmount <= 0.0f || IsDead())
    {
        return;  // Ignore negative heal or healing dead actors
    }

    // Restore health (clamped to max)
    float OldHealth = CurrentHealth;
    CurrentHealth = FMath::Min(MaxHealth, CurrentHealth + HealAmount);

    float ActualHealed = CurrentHealth - OldHealth;
    UE_LOG(LogTemp, Log, TEXT("[%s] Healed %.1f HP. HP: %.1f / %.1f"),
        *GetOwner()->GetName(), ActualHealed, CurrentHealth, MaxHealth);
}
```

### Step 3: Integrate with Actor TakeDamage Flow
```cpp
// In your actor class (e.g., ABaseCharacter.cpp):

float ABaseCharacter::TakeDamage(float DamageAmount, FDamageEvent const& DamageEvent,
    AController* EventInstigator, AActor* DamageCauser)
{
    // Always call super first
    float ActualDamage = Super::TakeDamage(DamageAmount, DamageEvent, EventInstigator, DamageCauser);

    // Forward to health component if present
    if (HealthComponent)
    {
        HealthComponent->TakeDamage(ActualDamage, DamageCauser);
    }

    return ActualDamage;
}
```

### Step 4: Bind Death Delegate for Cleanup
```cpp
// In actor BeginPlay:
void ABaseCharacter::BeginPlay()
{
    Super::BeginPlay();

    // Find health component
    HealthComponent = FindComponentByClass<UAC_HealthComponent>();

    if (HealthComponent)
    {
        // Bind death handler
        HealthComponent->OnDeath.AddDynamic(this, &ThisClass::HandleDeath);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("[%s] No HealthComponent found!"), *GetName());
    }
}

void ABaseCharacter::HandleDeath(AActor* DeadActor)
{
    // Disable input
    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        DisableInput(PC);
    }

    // Stop AI
    if (AAIController* AI = Cast<AAIController>(GetController()))
    {
        AI->GetBrainComponent()->StopLogic(TEXT("Dead"));
    }

    // Disable collision
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    // Start death animation or destroy after delay
    FTimerHandle DeathTimer;
    GetWorldTimerManager().SetTimer(DeathTimer, [this]()
    {
        Destroy();
    }, 3.0f, false);
}
```

## Delegate Signatures

### FOnDeath
```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDeath, AActor*, DeadActor);
```
**Parameters:**
- `AActor* DeadActor` - The actor that died (owner of HealthComponent)

**Typical Listeners:**
- Actor itself (cleanup/destroy)
- GameMode (respawn logic, wave tracking)
- UI widgets (death screen, respawn timer)
- Achievement system (death counters)

## Common Pitfalls

### ❌ MISTAKE 1: Forgetting RemoveDynamic in EndPlay
```cpp
// WRONG - Never unbind delegates
void ABaseCharacter::BeginPlay()
{
    HealthComponent->OnDeath.AddDynamic(this, &ThisClass::HandleDeath);
}
// Missing RemoveDynamic in EndPlay!
```

**CORRECT:**
```cpp
void ABaseCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (HealthComponent)
    {
        HealthComponent->OnDeath.RemoveDynamic(this, &ThisClass::HandleDeath);
    }
    Super::EndPlay(EndPlayReason);
}
```

### ❌ MISTAKE 2: Initializing Health in Header
```cpp
// WRONG - Default values in header
UPROPERTY()
float MaxHealth = 100.0f;  // Don't do this
```

**CORRECT:**
```cpp
// Use constructor initialization list
UAC_HealthComponent::UAC_HealthComponent()
    : MaxHealth(100.0f)
{
}
```

### ❌ MISTAKE 3: Not Checking for Null DamageCauser
```cpp
// WRONG - Crash if DamageCauser is null
UE_LOG(LogTemp, Log, TEXT("Damaged by: %s"), *DamageCauser->GetName());
```

**CORRECT:**
```cpp
// Null-check before dereferencing
UE_LOG(LogTemp, Log, TEXT("Damaged by: %s"),
    DamageCauser ? *DamageCauser->GetName() : TEXT("Unknown"));
```

### ❌ MISTAKE 4: Using EditAnywhere Instead of EditDefaultsOnly
```cpp
// WRONG - Designers shouldn't change MaxHealth per instance
UPROPERTY(EditAnywhere)
float MaxHealth;
```

**CORRECT:**
```cpp
// EditDefaultsOnly - set in class defaults, not per-instance
UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health")
float MaxHealth;
```

## Testing / Verification

### Console Commands for Testing
Add exec functions to your character:
```cpp
UFUNCTION(Exec)
void DealDamage(float Amount)
{
    if (HealthComponent)
    {
        HealthComponent->TakeDamage(Amount, this);
    }
}

UFUNCTION(Exec)
void HealSelf(float Amount)
{
    if (HealthComponent)
    {
        HealthComponent->Heal(Amount);
    }
}
```

### Test Checklist
- [ ] Component initializes with MaxHealth at BeginPlay
- [ ] TakeDamage reduces CurrentHealth correctly
- [ ] Negative damage values are ignored
- [ ] Health cannot go below zero
- [ ] OnDeath fires exactly once when health reaches zero
- [ ] Death handler executes (collision disabled, actor destroyed)
- [ ] Heal restores health (clamped to MaxHealth)
- [ ] Cannot heal dead actors
- [ ] Logs show correct damage source names

### PIE Testing Workflow
1. Place actor with HealthComponent in level
2. PIE and type: `DealDamage 50`
3. Verify log shows damage applied
4. Type: `DealDamage 60`
5. Verify OnDeath fires and actor destroys after delay
6. Repeat with `HealSelf 30` to test healing

## Deep Command Adaptation

### Zone-Based Hull Damage
Deep Command extends this pattern to 5 hull zones:
```cpp
// AC_HullComponent replaces single HP with per-zone integrity
UPROPERTY(EditDefaultsOnly, Category = "Hull")
TArray<FHullZoneConfig> HullZones;  // Bow, Midship, Stern, Keel, Superstructure

// Delegates become zone-specific
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnHullZoneDamaged,
    EHullZone, Zone, float, CurrentIntegrity, float, DamageAmount);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnHullZoneBreached,
    EHullZone, Zone);
```

### Cascading Damage
When Keel breaches, flooding spreads to adjacent zones. When all zones critical, ship sinks.

### Key Differences from Base Pattern
- **Single HP → Zone array:** 5 independent integrity pools
- **OnDeath → OnShipSinking:** More specific terminology
- **Heal() → RepairZone():** Zone-targeted restoration
- **Additional state:** Flooding rate, fire propagation per zone

### Preserved Principles
- Still ActorComponent composition
- Still delegate-driven event flow
- Still constructor initialization
- Still no polling - all event-based
- Still EditDefaultsOnly for MaxIntegrity values
