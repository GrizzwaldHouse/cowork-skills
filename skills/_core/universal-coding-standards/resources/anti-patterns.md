# Anti-Patterns Reference

## Quick Scan Checklist

Use this checklist to review any code before presenting it to Marcus.

- [ ] No unrestricted mutable public state
- [ ] All defaults set at construction (not scattered)
- [ ] No polling loops (use events/observers)
- [ ] No magic numbers or magic strings
- [ ] No hardcoded config values (URLs, colors, timeouts)
- [ ] Dependencies minimized in declarations/headers
- [ ] Comments explain WHY, not WHAT
- [ ] No block comments for code flow explanation
- [ ] File header present (filename, developer, date, purpose)
- [ ] Error handling is explicit, not swallowed
- [ ] No global mutable state
- [ ] No secrets in source code
- [ ] Build config changes are project-scoped, not global

## Detailed Anti-Patterns

### 1. Unrestricted Mutable Public State

**Bad:**
```typescript
// Anyone can modify cart total directly
export class ShoppingCart {
  public total: number = 0;
  public items: CartItem[] = [];
}
```

**Good:**
```typescript
export class ShoppingCart {
  private _items: CartItem[] = [];

  get total(): number {
    return this._items.reduce((sum, item) => sum + item.price, 0);
  }

  get items(): readonly CartItem[] {
    return this._items;
  }

  addItem(item: CartItem): void {
    this._items.push(item);
    this.onCartChanged.emit(this.total);
  }
}
```

### 2. Scattered Defaults

**Bad:**
```python
class ApiClient:
    def __init__(self):
        self.base_url = ""  # set later in configure()

    def configure(self):
        self.base_url = "https://api.example.com"
        self.timeout = 30  # first time this appears
```

**Good:**
```python
class ApiClient:
    def __init__(
        self,
        base_url: str = "https://api.example.com",
        timeout: int = 30,
    ):
        self._base_url = base_url
        self._timeout = timeout
```

### 3. Polling Instead of Events

**Bad:**
```javascript
setInterval(() => {
  const data = fetchLatestData();
  if (data !== lastData) {
    updateUI(data);
    lastData = data;
  }
}, 100);
```

**Good:**
```javascript
dataStore.on('change', (newData) => {
  updateUI(newData);
});
```

### 4. Magic Numbers

**Bad:**
```cpp
if (Player->GetHealth() < 25.0f)
{
    SetTintColor(FLinearColor(1.0f, 0.0f, 0.0f, 0.5f));
}
```

**Good:**
```cpp
// Health threshold and visual feedback configured per-class
if (Player->GetHealth() < LowHealthThreshold)
{
    SetTintColor(LowHealthTintColor);
}
```

### 5. Tight Coupling via Direct Calls

**Bad:**
```csharp
public class HealthComponent
{
    private UIManager _uiManager;
    private AudioManager _audioManager;
    private AIController _aiController;

    public void TakeDamage(float amount)
    {
        Health -= amount;
        _uiManager.UpdateHealthBar(Health);     // knows about UI
        _audioManager.PlayDamageSound();         // knows about audio
        _aiController.OnAllyDamaged(this);       // knows about AI
    }
}
```

**Good:**
```csharp
public class HealthComponent
{
    public event Action<float> OnHealthChanged;

    public void TakeDamage(float amount)
    {
        Health -= amount;
        OnHealthChanged?.Invoke(Health);
        // UI, audio, AI all subscribe independently
    }
}
```
