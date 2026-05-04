# Access Control Quick Reference

## Decision Matrix

| Question | Answer | Access Level |
|----------|--------|-------------|
| Does external code need to read this? | No | Private/protected |
| Does external code need to read this? | Yes, but never write | Read-only public (getter only) |
| Is this set once per class/type? | Yes | Class-level config (constructor param with default) |
| Is this set once per instance? | Yes | Instance-level config (constructor injection) |
| Does this change at runtime? | Yes, internally only | Private with event broadcast on change |
| Does this change at runtime? | Yes, externally too | Public setter with validation + event broadcast |

## Language Cheat Sheet

### C++ (UE5)

```cpp
// Read-only public state
UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health")
float CurrentHealth;

// Class-level config (set in Blueprint defaults)
UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Health")
float MaxHealth;

// Instance-level config (set per placed actor)
UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Team")
int32 TeamID;

// BANNED: EditAnywhere (ambiguous scope)
```

### TypeScript

```typescript
// Read-only public state
class GameCharacter {
  private _health: number;
  get health(): number { return this._health; }
}

// Config via constructor
class ApiClient {
  constructor(
    private readonly baseUrl: string,
    private readonly timeout: number = 5000,
  ) {}
}
```

### Python

```python
class GameCharacter:
    def __init__(self, max_health: float = 100.0):
        self._max_health = max_health  # class-level config
        self._health = max_health      # runtime state

    @property
    def health(self) -> float:
        """Read-only public access to current health."""
        return self._health
```

### C#

```csharp
public class GameCharacter
{
    // Read-only public state
    public float Health { get; private set; }

    // Class-level config
    public float MaxHealth { get; }

    public GameCharacter(float maxHealth = 100f)
    {
        MaxHealth = maxHealth;
        Health = maxHealth;
    }
}
```

### Rust

```rust
pub struct GameCharacter {
    health: f32,     // private
    max_health: f32, // private
}

impl GameCharacter {
    pub fn new(max_health: f32) -> Self {
        Self { health: max_health, max_health }
    }

    pub fn health(&self) -> f32 { self.health }
    pub fn max_health(&self) -> f32 { self.max_health }
}
```
