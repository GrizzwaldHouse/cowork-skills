# Deep Command DataAsset Property Schemas

Developer: Marcus Daley
Date: 2026-03-02
Engine: Unreal Engine 5.4 (C++)
Standards: Nick Penney AAA Coding Standards

All gameplay values live in DataAssets. Zero hardcoded numbers in source.
Designers configure everything in the Unreal Editor.

---

## 1. UShipClassData (28 properties)

```cpp
// ShipClassData.h
// Developer: Marcus Daley
// Date: 2026-03-02
// Purpose: Defines a class of naval vessel with all physical characteristics.
// Usage: Create DataAsset instances (DA_Destroyer_FletcherClass, DA_Sub_GatoClass, etc.)
//        and assign to ShipPawn Blueprint defaults.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "DeepCommand/Code/Utility/Enums/DeepCommandEnums.h"
#include "DeepCommand/Code/Utility/Structs/NavalStructs.h"
#include "ShipClassData.generated.h"

class UStaticMesh;
class UTexture2D;

UCLASS(BlueprintType)
class DEEPCOMMAND_API UShipClassData : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // ====================================================================
    // IDENTITY
    // ====================================================================

    // Internal name for this ship class (e.g., "FletcherClass", "GatoClass")
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FName ShipClassName;

    // Ship type classification (Destroyer, Submarine, Battleship, etc.)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    EShipClassification ShipClassification;

    // Nation that originally designed this class
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FName NationOfOrigin;

    // Display name for UI
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FText DisplayName;

    // ====================================================================
    // MOVEMENT PARAMETERS
    // ====================================================================

    // Maximum surface speed in knots
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Movement",
        meta = (ClampMin = "0.0", ClampMax = "45.0"))
    float MaxSpeedKnots;

    // How quickly the ship reaches max speed (knots per second)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Movement",
        meta = (ClampMin = "0.0"))
    float AccelerationRate;

    // Maximum turn rate in degrees per second at full rudder
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Movement",
        meta = (ClampMin = "0.0", ClampMax = "15.0"))
    float TurnRateDegreesPerSecond;

    // Ship draft in meters (affects shallow water navigation)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Movement",
        meta = (ClampMin = "0.0"))
    float DraftMeters;

    // Maximum dive depth in meters (0 for surface vessels)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Movement",
        meta = (ClampMin = "0.0"))
    float MaxDepthMeters;

    // Fuel consumption multiplier at flank speed relative to half ahead
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Movement",
        meta = (ClampMin = "1.0", ClampMax = "5.0"))
    float FlankSpeedFuelMultiplier;

    // ====================================================================
    // HULL PARAMETERS
    // ====================================================================

    // Per-zone hull configuration (Bow, Midship, Stern, Keel, Superstructure)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    TArray<FHullZoneConfig> HullZones;

    // Overall armor rating (damage reduction factor 0-1)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float TotalArmorRating;

    // Ship displacement in tons (affects inertia and ramming damage)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull",
        meta = (ClampMin = "0.0"))
    float DisplacementTons;

    // ====================================================================
    // DETECTION PARAMETERS
    // ====================================================================

    // Maximum radar detection range in nautical miles
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Detection",
        meta = (ClampMin = "0.0"))
    float RadarRange;

    // Maximum active sonar detection range in nautical miles
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Detection",
        meta = (ClampMin = "0.0"))
    float SonarRange;

    // Maximum visual detection range in nautical miles
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Detection",
        meta = (ClampMin = "0.0"))
    float VisualRange;

    // How visible this ship is to enemy radar (0 = stealth, 1 = large)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Detection|Signature",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float RadarCrossSection;

    // How audible this ship is to enemy sonar (0 = silent, 1 = loud)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Detection|Signature",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float AcousticSignature;

    // Magnetic signature for mine/torpedo detection (0 = none, 1 = strong)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Detection|Signature",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float MagneticSignature;

    // ====================================================================
    // WEAPON MOUNTS
    // ====================================================================

    // Weapon mount configurations for this ship class
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapons")
    TArray<FWeaponMountConfig> WeaponMounts;

    // ====================================================================
    // CREW PARAMETERS
    // ====================================================================

    // Total crew complement
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crew",
        meta = (ClampMin = "1"))
    int32 CrewComplement;

    // Number of officer slots (for trait assignment)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crew",
        meta = (ClampMin = "0"))
    int32 OfficerSlots;

    // Number of damage control teams (simultaneous repairs)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Crew",
        meta = (ClampMin = "0"))
    int32 DamageControlTeams;

    // ====================================================================
    // SUPPLY PARAMETERS
    // ====================================================================

    // Maximum fuel capacity (abstract units)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply",
        meta = (ClampMin = "0.0"))
    float FuelCapacity;

    // Ammo storage per weapon type (WeaponTypeName -> max rounds)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply")
    TMap<FName, int32> AmmoStorage;

    // Maximum days of provisions before crew efficiency degrades
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply",
        meta = (ClampMin = "0.0"))
    float MaxProvisionsDays;

    // ====================================================================
    // VISUALS
    // ====================================================================

    // Ship mesh for 3D rendering (soft reference for async loading)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    TSoftObjectPtr<UStaticMesh> ShipMesh;

    // Ship icon for strategic map display
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    TSoftObjectPtr<UTexture2D> ShipIcon;
};
```

---

## 2. UWeaponData (19 properties)

```cpp
// WeaponData.h
// Developer: Marcus Daley
// Date: 2026-03-02
// Purpose: Defines a weapon type with ballistic, damage, and ammo characteristics.
// Usage: Create DataAsset instances (DA_5inchGun, DA_21inchTorpedo, DA_DepthCharge, etc.)
//        and reference from FWeaponMountConfig in UShipClassData.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "DeepCommand/Code/Utility/Enums/CombatEnums.h"
#include "WeaponData.generated.h"

class UNiagaraSystem;
class USoundBase;

UCLASS(BlueprintType)
class DEEPCOMMAND_API UWeaponData : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // ====================================================================
    // IDENTITY
    // ====================================================================

    // Internal weapon name (e.g., "5inch38cal", "Mk14Torpedo")
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FName WeaponName;

    // Weapon classification
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    EWeaponType WeaponType;

    // Display name for UI
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FText DisplayName;

    // ====================================================================
    // BALLISTIC PARAMETERS
    // ====================================================================

    // Maximum effective range in nautical miles
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ballistics",
        meta = (ClampMin = "0.0"))
    float Range;

    // Base accuracy at optimal range (0.0 = miss always, 1.0 = perfect)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ballistics",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float Accuracy;

    // Time to reload between shots (seconds)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ballistics",
        meta = (ClampMin = "0.1"))
    float ReloadTimeSeconds;

    // How fast the turret/mount rotates (degrees per second)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ballistics",
        meta = (ClampMin = "0.0"))
    float TraverseRateDegreesPerSec;

    // Minimum gun elevation in degrees (negative = depress below horizon)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ballistics")
    float ElevationMin;

    // Maximum gun elevation in degrees
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ballistics")
    float ElevationMax;

    // ====================================================================
    // DAMAGE PARAMETERS
    // ====================================================================

    // Base damage per hit
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage",
        meta = (ClampMin = "0.0"))
    float BaseDamage;

    // Armor penetration capability (compared against ArmorRating)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float ArmorPenetration;

    // Splash damage radius in meters (0 = direct hit only)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage",
        meta = (ClampMin = "0.0"))
    float SplashRadius;

    // FName damage type for extensibility (HE, AP, Torpedo, DepthCharge)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
    FName DamageTypeName;

    // ====================================================================
    // AMMO PARAMETERS
    // ====================================================================

    // Rounds per magazine/load
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ammo",
        meta = (ClampMin = "1"))
    int32 AmmoPerLoad;

    // Maximum ammo that can be carried in reserve
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ammo",
        meta = (ClampMin = "0"))
    int32 MaxAmmoReserve;

    // ====================================================================
    // FIRING CONSTRAINTS
    // ====================================================================

    // Total firing arc in degrees (360 = full rotation)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Firing",
        meta = (ClampMin = "0.0", ClampMax = "360.0"))
    float FiringArcDegrees;

    // Whether this weapon can fire while ship is moving
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Firing")
    bool bCanFireWhileMoving;

    // Minimum range to engage (prevents firing too close)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Firing",
        meta = (ClampMin = "0.0"))
    float MinEngagementRange;

    // ====================================================================
    // VISUALS
    // ====================================================================

    // Muzzle flash or launch VFX
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    TSoftObjectPtr<UNiagaraSystem> MuzzleFlashVFX;

    // Projectile actor to spawn when firing
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    TSubclassOf<AActor> ProjectileClass;

    // Firing sound effect
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Visuals")
    TSoftObjectPtr<USoundBase> FiringSound;
};
```

---

## 3. UNationData (14 properties)

```cpp
// NationData.h
// Developer: Marcus Daley
// Date: 2026-03-02
// Purpose: Defines a nation with starting forces, AI personality, and economy.
// Usage: Create DataAsset instances (DA_Nation_USN, DA_Nation_IJN, DA_Nation_RN, etc.)
//        and assign to DiplomacySubsystem at scenario start.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "DeepCommand/Code/Utility/Enums/DiplomacyEnums.h"
#include "DeepCommand/Code/Utility/Structs/FleetStructs.h"
#include "NationData.generated.h"

class UTexture2D;

UCLASS(BlueprintType)
class DEEPCOMMAND_API UNationData : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // ====================================================================
    // IDENTITY
    // ====================================================================

    // Internal nation identifier (e.g., "USN", "IJN", "RN", "KM")
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FName NationName;

    // Display name for UI
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FText DisplayName;

    // Nation flag texture for UI
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    TSoftObjectPtr<UTexture2D> NationFlag;

    // Nation color for map markers and UI elements
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
    FLinearColor NationColor;

    // ====================================================================
    // STARTING FORCES
    // ====================================================================

    // Fleet templates to spawn at scenario start
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Starting Forces")
    TArray<FFleetTemplate> StartingFleets;

    // Home port locations (world space coordinates)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Starting Forces")
    TArray<FVector> HomePorts;

    // ====================================================================
    // AI PERSONALITY
    // ====================================================================

    // How aggressively AI pursues combat (0 = defensive, 1 = reckless)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Personality",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float Aggressiveness;

    // How actively AI seeks to control territory (0 = static, 1 = expansive)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Personality",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float Expansionism;

    // Overall naval doctrine guiding fleet composition and tactics
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "AI Personality")
    ENavalDoctrine NavalDoctrine;

    // ====================================================================
    // TECHNOLOGY BONUSES
    // ====================================================================

    // Named bonuses applied to all ships (e.g., "speed_bonus" -> 0.1 = +10%)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Technology")
    TMap<FName, float> TechBonuses;

    // ====================================================================
    // ECONOMY
    // ====================================================================

    // Base resource generation per game day
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Economy",
        meta = (ClampMin = "0.0"))
    float BaseResourceGeneration;

    // Supply chain efficiency multiplier (1.0 = normal)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Economy",
        meta = (ClampMin = "0.1", ClampMax = "3.0"))
    float SupplyEfficiency;

    // Ship construction speed multiplier (1.0 = normal)
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Economy",
        meta = (ClampMin = "0.1", ClampMax = "3.0"))
    float ShipbuildingSpeed;
};
```

---

## 4. Supporting Structs

\`\`\`cpp
// NavalStructs.h
// Developer: Marcus Daley
// Date: 2026-03-02
// Purpose: Core struct definitions for ship configuration and combat data.

#pragma once

#include "CoreMinimal.h"
#include "DeepCommand/Code/Utility/Enums/DeepCommandEnums.h"
#include "DeepCommand/Code/Utility/Enums/CombatEnums.h"
#include "NavalStructs.generated.h"

class UWeaponData;
class AShipPawn;

// Per-zone hull parameters
USTRUCT(BlueprintType)
struct DEEPCOMMAND_API FHullZoneConfig
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    EHullZone Zone;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull",
        meta = (ClampMin = "0.0"))
    float MaxIntegrity;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float ArmorRating;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    bool bCanFlood;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull",
        meta = (ClampMin = "0.0", EditCondition = "bCanFlood"))
    float FloodRatePerSecond;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Hull")
    bool bCanCatchFire;

    FHullZoneConfig()
        : Zone(EHullZone::Midship)
        , MaxIntegrity(100.0f)
        , ArmorRating(0.0f)
        , bCanFlood(false)
        , FloodRatePerSecond(0.0f)
        , bCanCatchFire(true)
    {}
};

// Weapon placement on a ship
USTRUCT(BlueprintType)
struct DEEPCOMMAND_API FWeaponMountConfig
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    FName MountName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    UWeaponData* WeaponData;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    FVector MountOffset;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon",
        meta = (ClampMin = "0.0", ClampMax = "360.0"))
    float FiringArcDegrees;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    float MountRotationOffset;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
    EHullZone MountZone;

    FWeaponMountConfig()
        : WeaponData(nullptr)
        , MountOffset(FVector::ZeroVector)
        , FiringArcDegrees(180.0f)
        , MountRotationOffset(0.0f)
        , MountZone(EHullZone::Superstructure)
    {}
};

// Detected contact data
USTRUCT(BlueprintType)
struct DEEPCOMMAND_API FContactInfo
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Contact")
    TWeakObjectPtr<AActor> DetectedActor;

    UPROPERTY(BlueprintReadOnly, Category = "Contact")
    FVector LastKnownPosition;

    UPROPERTY(BlueprintReadOnly, Category = "Contact",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float DetectionConfidence;

    UPROPERTY(BlueprintReadOnly, Category = "Contact")
    EContactClassification Classification;

    UPROPERTY(BlueprintReadOnly, Category = "Contact")
    EDetectionMethod DetectionMethod;

    UPROPERTY(BlueprintReadOnly, Category = "Contact")
    float TimeSinceLastContact;

    FContactInfo()
        : LastKnownPosition(FVector::ZeroVector)
        , DetectionConfidence(0.0f)
        , Classification(EContactClassification::Unknown)
        , DetectionMethod(EDetectionMethod::Visual)
        , TimeSinceLastContact(0.0f)
    {}
};

// Damage distribution profile
USTRUCT(BlueprintType)
struct DEEPCOMMAND_API FDamageProfile
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
    FName DamageTypeName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
    TMap<EHullZone, float> ZoneDamageMultipliers;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
    bool bCanStartFire;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage")
    bool bCanCauseFlooding;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Damage",
        meta = (ClampMin = "0.0"))
    float CrewCasualtyMultiplier;

    FDamageProfile()
        : bCanStartFire(false)
        , bCanCauseFlooding(false)
        , CrewCasualtyMultiplier(1.0f)
    {}
};

// Fleet spawning template
USTRUCT(BlueprintType)
struct DEEPCOMMAND_API FFleetTemplate
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    FName FleetName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    TArray<TSubclassOf<AShipPawn>> ShipClasses;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    FVector SpawnAreaCenter;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet",
        meta = (ClampMin = "0.0"))
    float SpawnAreaRadius;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fleet")
    EFleetFormation DefaultFormation;

    FFleetTemplate()
        : SpawnAreaCenter(FVector::ZeroVector)
        , SpawnAreaRadius(500.0f)
        , DefaultFormation(EFleetFormation::LineAhead)
    {}
};

// Supply delivery contents
USTRUCT(BlueprintType)
struct DEEPCOMMAND_API FSupplyManifest
{
    GENERATED_BODY()

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply",
        meta = (ClampMin = "0.0"))
    float Fuel;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply")
    TMap<FName, int32> Ammo;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply",
        meta = (ClampMin = "0.0"))
    float Provisions;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Supply",
        meta = (ClampMin = "0"))
    int32 ReplacementCrew;

    FSupplyManifest()
        : Fuel(0.0f)
        , Provisions(0.0f)
        , ReplacementCrew(0)
    {}
};
\`\`\`

---

End of DataAsset Property Schemas
