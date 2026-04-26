---
name: ue5-build-verify
description: >
  Post-code-write verification gate for Unreal Engine 5 C++ projects.
  Scans all modified files for known silent-failure patterns specific to this
  codebase (wrong SLOG macro syntax, FString::FromBool, EditAnywhere, etc.)
  then triggers a full UE5 build and surfaces every error/warning with file+line.
  Run automatically after writing any .cpp/.h file in the project.
user-invocable: true
allowed-tools:
  - Bash
  - Grep
  - Glob
  - Read
  - Edit
---

# UE5 Build Verify

> Catches codebase-specific anti-patterns and build errors immediately after code
> is written — before they accumulate across multiple files and sessions.

## Root Cause This Skill Was Created From

**Phase 4 (April 20, 2026):** An agent added SLOG_EVENT instrumentation using a
brace-initializer syntax `{{"key", val}}` that is invalid for these variadic macros.
It also used `FString::FromBool()` which does not exist in UE5. Neither error was
caught because no build was run before committing. The result was 150+ cascade
errors across 10 files that had to be manually traced and fixed in a later session.

**Rule:** Every time C++ code is written into this project, this skill runs.

---

## When to Activate

- **Automatically** after writing or editing any `.cpp` or `.h` file in the project
- **Manually** via `/ue5-build-verify` when you want an explicit gate before committing
- **Always** when adding new macro usage (SLOG_*, UPROPERTY, UFUNCTION, DECLARE_*)

---

## Step 1: Static Pattern Scan (fast, runs first)

Grep all staged/modified `.cpp` and `.h` files for known bad patterns **before**
invoking the compiler. Fix any hits immediately, then proceed to Step 2.

### Pattern Checklist

Run these grep checks against every modified file:

**1. Wrong SLOG macro syntax (brace-initializer)**
```bash
# BAD: {{"key", value}} — compiles to nothing, causes cascade parse errors
grep -n '{\s*{' <file> | grep -v "//.*{{"
```
Correct form: `Metadata.Add(TEXT("key"), value);` as semicolon-separated statements inside the macro's variadic arg.

**2. FString::FromBool — does not exist in UE5**
```bash
grep -n "FString::FromBool" <file>
```
Fix: replace with `x ? TEXT("true") : TEXT("false")`

**3. EditAnywhere — forbidden by project standards**
```bash
grep -n "EditAnywhere" <file>
```
Fix: replace with `EditDefaultsOnly` or `EditInstanceOnly`

**4. Hardcoded FName string literals in BT nodes**
```bash
grep -n 'GetValueAs.*TEXT("' <file>
grep -n 'SetValueAs.*TEXT("' <file>
```
Fix: use the `FName` key name properties from the controller/node header.

**5. FBlackboardKeySelector missing AddFilter in constructor**
```bash
grep -n "FBlackboardKeySelector" <file>
```
For every `FBlackboardKeySelector` property: verify constructor has
`AddObjectFilter`/`AddBoolFilter`/`AddVectorFilter` AND `InitializeFromAsset`
override has `ResolveSelectedKey`. Both required — silent failure without both.

**6. GameplayStatics cross-system calls (forbidden)**
```bash
grep -n "UGameplayStatics::" <file>
```
Fix: use TActorIterator, cached TWeakObjectPtr, or Observer delegates.

**7. ConstructorHelpers (forbidden)**
```bash
grep -n "ConstructorHelpers::" <file>
```
Fix: use EditDefaultsOnly UPROPERTY and assign in Blueprint.

**8. Polling in Tick / BTService TickNode**
```bash
grep -n "GetAuthGameMode\|GetGameMode" <file>
```
If inside a Tick/TickNode/TickTask function: forbidden. Use delegate binding.

**9. Missing semicolon after SLOG macro call**
```bash
grep -n "^    SLOG_" <file> | grep -v ",$\|;$\|)$"
```
SLOG macros expand to `{ ... }` blocks — they don't need a trailing semicolon,
but the Metadata.Add lines inside the variadic body each need one.

**10. `/** */` docblock comments (style violation)**
```bash
grep -n "/\*\*" <file>
```
Fix: replace with `//` line comments per Nick Penney AAA standards.

---

## Step 2: UE5 Compiler Build

After the static scan passes (zero hits), run the full build:

```bash
"C:\Program Files\Epic Games\UE_5.4\Engine\Build\BatchFiles\Build.bat" \
  END2507Editor Win64 Development \
  -Project="C:\Users\daley\UnrealProjects\BaseGame\WizardJam2.0.uproject" \
  -WaitMutex -FromMsBuild -architecture=x64
```

### Interpreting Build Output

Parse the output for these patterns:

| Pattern | Meaning | Action |
|---|---|---|
| `error C2065: 'Metadata': undeclared identifier` | SLOG called outside enabled block or wrong syntax | Check macro call in that file |
| `error C2059: syntax error: '{'` | Brace-initializer in SLOG variadic arg | Convert to `Metadata.Add()` statements |
| `error C3861: 'FromBool': identifier not found` | `FString::FromBool()` usage | Replace with ternary |
| `error C2614: illegal member initialization` | Property in constructor init list but not declared | Check header declaration order |
| `warning C5038: ... will be initialized after` | Init list order doesn't match declaration order | Reorder init list to match header |
| `'->': trailing return type not allowed` | Cascade from earlier syntax error | Fix the root error first |
| `missing function header (old-style formal list?)` | Cascade from earlier syntax error | Fix the root error first |

**Cascade error rule:** When you see 50+ errors, look for the FIRST error in the
output — it is almost always the root cause. Fix it and rebuild before touching
anything else.

---

## Step 3: Resolve and Re-Verify

For each error found:

1. Open the file at the reported line number
2. Apply the fix from the pattern checklist or error table above
3. Re-run Step 1 static scan on the changed file
4. Re-run Step 2 build — do not stop until exit code is 0

**Do not commit until the build exits with code 0.**

---

## SLOG Macro Reference (this codebase)

The `SLOG_*` macros in `Plugins/StructuredLogging/Source/StructuredLogging/Public/StructuredLoggingMacros.h` use `__VA_ARGS__` to inject code into a block that already has a `TMap<FString,FString> Metadata` local variable declared.

```cpp
// ✅ CORRECT — variadic body is semicolon-separated Metadata.Add() statements
SLOG_EVENT(this, "AI.Flight", "FlightTargetSet",
    Metadata.Add(TEXT("target_location"), TargetLocation.ToString());
    Metadata.Add(TEXT("pawn_name"), GetPawn()->GetName());
)

// ✅ CORRECT — no metadata (variadic arg omitted entirely)
SLOG_EVENT(this, "AI.Flight", "FlightTargetCleared")

// ❌ WRONG — brace-initializer. Causes cascade parse errors across entire file.
SLOG_EVENT(this, "AI.Flight", "FlightTargetSet", {
    {"target_location", TargetLocation.ToString()}
})

// ❌ WRONG — FString::FromBool does not exist in UE5
Metadata.Add(TEXT("is_flying"), FString::FromBool(bIsFlying));

// ✅ CORRECT — ternary instead
Metadata.Add(TEXT("is_flying"), bIsFlying ? TEXT("true") : TEXT("false"));
```

No trailing semicolon after the closing `)` — the macro expands to a `{ }` block.

---

## FBlackboardKeySelector Reference (this codebase)

Every `FBlackboardKeySelector` property requires **both** of these or it silently
returns `IsSet() == false` at runtime even when configured in the editor:

```cpp
// In constructor — registers valid key types for editor dropdown
MyKey.AddBoolFilter(this, GET_MEMBER_NAME_CHECKED(UMyBTNode, MyKey));
// Also: AddObjectFilter(..., AActor::StaticClass()), AddVectorFilter(...)

// In InitializeFromAsset override — resolves name to actual BB slot
void UMyBTNode::InitializeFromAsset(UBehaviorTree& Asset)
{
    Super::InitializeFromAsset(Asset);
    if (UBlackboardData* BBAsset = GetBlackboardAsset())
        MyKey.ResolveSelectedKey(*BBAsset);
}
```

---

## Quick Reference: Forbidden Patterns

| Pattern | Why Forbidden | Fix |
|---|---|---|
| `EditAnywhere` | Allows instance override of defaults | `EditDefaultsOnly` or `EditInstanceOnly` |
| `FString::FromBool(x)` | Doesn't exist in UE5 | `x ? TEXT("true") : TEXT("false")` |
| `UGameplayStatics::GetGameMode` | Tight coupling | Cache + Observer delegates |
| `ConstructorHelpers::FObjectFinder` | Loads at construction time | `EditDefaultsOnly` + Blueprint assign |
| `/** */` docblocks | Style violation (Nick Penney standard) | `//` line comments only |
| Hardcoded FName strings in BT nodes | Not designer-configurable | FName property + QuidditchBBKeys:: constants |
| Polling in `Tick()` / `TickNode()` | Breaks Observer pattern | Delegate binding at BeginPlay |

---

## Notes

- This skill was created after the Phase 4 build failure (April 26, 2026) where
  37 bad SLOG calls across 10 files went undetected because no build was run.
- The UE5 build command takes ~2-5 minutes on this machine — run it every session,
  not just before commit.
- The static pattern scan (Step 1) is fast and should run after every file write.
- "Fix it now" is always cheaper than "fix it later across 10 files."
