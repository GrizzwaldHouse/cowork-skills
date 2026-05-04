# Blueprint Naming Conventions

> Consistent naming prevents confusion as projects grow.

## Blueprint Class Naming

| Type | Prefix | Example |
|------|--------|---------|
| Actor | A_ or BP_ | BP_EnemySpawner |
| Character | BP_ | BP_PlayerCharacter |
| Component | BPC_ | BPC_InventoryComponent |
| Widget | WBP_ or W_ | WBP_HealthBar |
| Game Mode | GM_ | GM_DefaultGameMode |
| Game State | GS_ | GS_MatchState |
| Player Controller | PC_ | PC_DefaultController |
| AI Controller | AIC_ | AIC_EnemyController |
| Animation Blueprint | ABP_ | ABP_PlayerAnimations |
| Interface | BPI_ | BPI_Interactable |
| Function Library | BPFL_ | BPFL_MathHelpers |
| Enum | E_ | E_WeaponType |
| Structure | F_ or S_ | S_InventorySlot |
| Data Asset | DA_ | DA_RifleStats |
| Data Table | DT_ | DT_WeaponDatabase |

## Variable Naming

| Type | Convention | Example |
|------|-----------|---------|
| Boolean | b prefix | bIsAlive, bCanJump |
| Integer | Descriptive | CurrentHealth, AmmoCount |
| Float | Descriptive | MoveSpeed, DamageMultiplier |
| Array | Plural | Enemies, PatrolPoints |
| Map | Key + Values | ItemPrices, PlayerScores |
| Object Reference | Ref suffix (optional) | TargetActorRef, WeaponMeshRef |

## Folder Structure (Content Browser)

```
Content/
  Blueprints/
    Characters/
      BP_PlayerCharacter
      BP_EnemyBase
    Components/
      BPC_HealthComponent
      BPC_InventoryComponent
    GameModes/
      GM_DefaultGameMode
    UI/
      WBP_MainMenu
      WBP_HUD
    FunctionLibraries/
      BPFL_MathHelpers
      BPFL_UIHelpers
  DataAssets/
    Weapons/
      DA_Rifle
      DA_Shotgun
    Characters/
      DA_EnemyStats
  DataTables/
    DT_WeaponDatabase
    DT_LootTable
```

## Function / Event Naming

- Functions: verb + noun (GetHealth, CalculateDamage, SpawnProjectile)
- Custom Events: On + event description (OnDamageTaken, OnItemPickedUp)
- Event Dispatchers: On + state change (OnHealthChanged, OnAmmoUpdated)
- Interface Functions: verb form (Interact, TakeDamage, GetDisplayName)

## Comment Box Color Conventions

| System | Color | Hex |
|--------|-------|-----|
| Movement / Navigation | Blue | #4A90D9 |
| Combat / Damage | Red | #D94A4A |
| UI / HUD | Green | #4AD94A |
| AI / Behavior | Purple | #9B4AD9 |
| Audio / VFX | Orange | #D99B4A |
| Initialization / Setup | Gray | #808080 |
| Networking / Replication | Cyan | #4AD9D9 |
