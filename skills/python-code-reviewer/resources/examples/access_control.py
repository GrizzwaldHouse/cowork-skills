# access_control.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Demonstrates proper access control patterns in Python with before/after examples.

"""
Access Control & Encapsulation Examples

Shows proper use of @property decorators, private attributes,
and controlled mutation for read-only public state.
"""

from typing import List, Optional
from enum import Enum


# ============================================================================
# EXAMPLE 1: Read-Only Public State
# ============================================================================

# BAD: Unrestricted mutable public state
class PlayerBad:
    """Player with unrestricted health modification."""

    def __init__(self, name: str):
        self.name = name
        self.health = 100  # Anyone can modify: player.health = -999


# GOOD: Read-only state with controlled mutation
class PlayerGood:
    """Player with encapsulated health management."""

    MAX_HEALTH = 100

    def __init__(self, name: str):
        self._name = name
        self._health = self.MAX_HEALTH

    @property
    def name(self) -> str:
        """Player name (read-only)."""
        return self._name

    @property
    def health(self) -> int:
        """Current health (read-only). Use take_damage() to modify."""
        return self._health

    def take_damage(self, amount: int) -> None:
        """Apply damage with validation.

        Args:
            amount: Damage amount (must be non-negative)

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Damage amount must be non-negative")

        self._health = max(0, self._health - amount)

    def heal(self, amount: int) -> None:
        """Restore health with validation.

        Args:
            amount: Heal amount (must be non-negative)

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Heal amount must be non-negative")

        self._health = min(self.MAX_HEALTH, self._health + amount)


# ============================================================================
# EXAMPLE 2: Protecting Mutable Collections
# ============================================================================

# BAD: Direct access to mutable collection
class InventoryBad:
    """Inventory with unprotected item list."""

    def __init__(self):
        self.items = []  # External code can: inv.items.clear()


# GOOD: Return copy of collection
class InventoryGood:
    """Inventory with protected item list."""

    def __init__(self):
        self._items: List[str] = []

    @property
    def items(self) -> List[str]:
        """Current items (read-only copy)."""
        return self._items.copy()

    @property
    def item_count(self) -> int:
        """Number of items in inventory."""
        return len(self._items)

    def add_item(self, item: str) -> None:
        """Add item to inventory with validation."""
        if not item or not item.strip():
            raise ValueError("Item name cannot be empty")

        self._items.append(item)

    def remove_item(self, item: str) -> bool:
        """Remove item from inventory.

        Args:
            item: Item name to remove

        Returns:
            True if item was removed, False if not found
        """
        try:
            self._items.remove(item)
            return True
        except ValueError:
            return False


# ============================================================================
# EXAMPLE 3: Class-Level Configuration
# ============================================================================

class ConnectionStatus(Enum):
    """Connection status enumeration."""

    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


# BAD: Class-level mutable state
class ConnectionBad:
    """Connection with shared mutable state."""

    retry_count = 0  # Shared across all instances - bad!
    max_retries = 3


# GOOD: Instance-level state with class-level constants
class ConnectionGood:
    """Connection with proper state encapsulation."""

    MAX_RETRIES = 3  # Class constant
    DEFAULT_TIMEOUT = 30

    def __init__(self, host: str, port: int, timeout: int = DEFAULT_TIMEOUT):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._retry_count = 0  # Instance state
        self._status = ConnectionStatus.IDLE

    @property
    def host(self) -> str:
        """Connection host (read-only)."""
        return self._host

    @property
    def port(self) -> int:
        """Connection port (read-only)."""
        return self._port

    @property
    def status(self) -> ConnectionStatus:
        """Current connection status (read-only)."""
        return self._status

    @property
    def retry_count(self) -> int:
        """Number of retry attempts (read-only)."""
        return self._retry_count

    def can_retry(self) -> bool:
        """Check if retry is allowed."""
        return self._retry_count < self.MAX_RETRIES


# ============================================================================
# EXAMPLE 4: Dependency Injection for External Resources
# ============================================================================

from typing import Protocol


class ISettings(Protocol):
    """Settings interface for dependency injection."""

    def value(self, key: str, default: Optional[str] = None) -> str:
        """Get setting value."""
        ...

    def setValue(self, key: str, value: str) -> None:
        """Set setting value."""
        ...


# BAD: Direct instantiation of external dependency
class ThemeManagerBad:
    """Theme manager with tight coupling to QSettings."""

    def __init__(self):
        from PySide6.QtCore import QSettings

        self.settings = QSettings("App", "Settings")  # Tight coupling
        self.theme = self.settings.value("theme", "light")


# GOOD: Dependency injection for testability
class ThemeManagerGood:
    """Theme manager with injected settings dependency."""

    class Theme(str, Enum):
        """Available theme options."""

        LIGHT = "light"
        DARK = "dark"

    DEFAULT_THEME = Theme.LIGHT

    def __init__(self, settings: ISettings):
        """Initialize with settings dependency.

        Args:
            settings: Settings storage implementing ISettings protocol
        """
        self._settings = settings
        theme_value = settings.value("theme", self.DEFAULT_THEME.value)
        self._current_theme = self.Theme(theme_value)

    @property
    def current_theme(self) -> Theme:
        """Current theme (read-only)."""
        return self._current_theme

    def set_theme(self, theme: Theme) -> None:
        """Change theme with validation and persistence.

        Args:
            theme: New theme to apply

        Raises:
            ValueError: If theme is not a valid Theme enum value
        """
        if not isinstance(theme, self.Theme):
            raise ValueError(f"Theme must be Theme enum, got {type(theme)}")

        self._current_theme = theme
        self._settings.setValue("theme", theme.value)


# ============================================================================
# EXAMPLE 5: Controlled Mutation with Validation
# ============================================================================

# BAD: Public setter without validation
class ConfigBad:
    """Config with unvalidated mutation."""

    def __init__(self):
        self.timeout = 30

    def set_timeout(self, value):
        self.timeout = value  # No validation!


# GOOD: Property with validated setter
class ConfigGood:
    """Config with validated mutation."""

    MIN_TIMEOUT = 1
    MAX_TIMEOUT = 300

    def __init__(self, timeout: int = 30):
        # Use property setter for validation
        self.timeout = timeout

    @property
    def timeout(self) -> int:
        """Connection timeout in seconds."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: int) -> None:
        """Set timeout with range validation.

        Args:
            value: Timeout in seconds

        Raises:
            ValueError: If timeout is out of valid range
        """
        if not isinstance(value, int):
            raise TypeError(f"Timeout must be int, got {type(value)}")

        if not self.MIN_TIMEOUT <= value <= self.MAX_TIMEOUT:
            raise ValueError(
                f"Timeout must be between {self.MIN_TIMEOUT} and {self.MAX_TIMEOUT}, got {value}"
            )

        self._timeout = value


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Read-only state
    player = PlayerGood("Hero")
    print(f"Health: {player.health}")  # Read-only access
    player.take_damage(25)  # Controlled mutation
    print(f"After damage: {player.health}")

    # Example 2: Protected collections
    inventory = InventoryGood()
    inventory.add_item("Sword")
    inventory.add_item("Shield")
    items_copy = inventory.items  # Returns copy
    items_copy.clear()  # Doesn't affect original
    print(f"Inventory count: {inventory.item_count}")  # Still 2

    # Example 3: Instance state
    conn1 = ConnectionGood("localhost", 8080)
    conn2 = ConnectionGood("remote", 443)
    print(f"Separate retry counts: {conn1.retry_count}, {conn2.retry_count}")

    # Example 5: Validated mutation
    config = ConfigGood()
    config.timeout = 60  # Validated
    try:
        config.timeout = 999  # Raises ValueError
    except ValueError as e:
        print(f"Validation caught: {e}")
