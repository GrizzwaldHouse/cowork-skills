# initialization.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Demonstrates proper initialization patterns - all defaults in __init__, no magic numbers/strings, no mutable default arguments.

"""
Initialization Rules Examples

Shows proper default value handling, constant extraction,
enum usage, and avoiding mutable default argument gotchas.
"""

from typing import List, Optional, Dict
from enum import Enum, auto
from dataclasses import dataclass, field


# ============================================================================
# EXAMPLE 1: All Defaults in __init__
# ============================================================================

# BAD: Defaults scattered, set outside __init__
class GameSettingsBad:
    """Game settings with scattered initialization."""

    def __init__(self):
        self.volume = 0.8

    def setup(self):
        self.difficulty = "normal"  # Should be in __init__
        self.music_enabled = True  # Should be in __init__


# GOOD: All defaults in __init__
class GameSettingsGood:
    """Game settings with centralized initialization."""

    class Difficulty(str, Enum):
        """Difficulty levels."""

        EASY = "easy"
        NORMAL = "normal"
        HARD = "hard"

    DEFAULT_VOLUME = 0.8

    def __init__(
        self,
        volume: float = DEFAULT_VOLUME,
        difficulty: Difficulty = Difficulty.NORMAL,
        music_enabled: bool = True,
    ):
        """Initialize with all default values.

        Args:
            volume: Audio volume (0.0 to 1.0)
            difficulty: Game difficulty level
            music_enabled: Whether background music is enabled
        """
        self._volume = volume
        self._difficulty = difficulty
        self._music_enabled = music_enabled


# ============================================================================
# EXAMPLE 2: No Magic Numbers
# ============================================================================

# BAD: Magic numbers scattered throughout
class RetryHandlerBad:
    """Retry handler with magic numbers."""

    def __init__(self):
        self.attempts = 0

    def should_retry(self) -> bool:
        return self.attempts < 3  # What is 3?

    def backoff_delay(self) -> float:
        return min(2 ** self.attempts, 60)  # What are 2 and 60?


# GOOD: Named constants for all numbers
class RetryHandlerGood:
    """Retry handler with named constants."""

    MAX_RETRY_ATTEMPTS = 3
    BACKOFF_BASE = 2.0
    MAX_BACKOFF_SECONDS = 60.0
    INITIAL_DELAY_SECONDS = 1.0

    def __init__(
        self,
        max_attempts: int = MAX_RETRY_ATTEMPTS,
        initial_delay: float = INITIAL_DELAY_SECONDS,
    ):
        """Initialize retry handler.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay before first retry
        """
        self._max_attempts = max_attempts
        self._initial_delay = initial_delay
        self._attempts = 0

    @property
    def attempts(self) -> int:
        """Number of attempts made."""
        return self._attempts

    def should_retry(self) -> bool:
        """Check if retry is allowed."""
        return self._attempts < self._max_attempts

    def backoff_delay(self) -> float:
        """Calculate exponential backoff delay.

        Returns:
            Delay in seconds (capped at MAX_BACKOFF_SECONDS)
        """
        delay = self._initial_delay * (self.BACKOFF_BASE ** self._attempts)
        return min(delay, self.MAX_BACKOFF_SECONDS)


# ============================================================================
# EXAMPLE 3: No Magic Strings - Use Enums
# ============================================================================

# BAD: Magic strings for state
class OrderBad:
    """Order with string-based state."""

    def __init__(self):
        self.status = "pending"  # Typo risk, no autocomplete

    def process(self):
        if self.status == "pending":  # Repeated string literals
            self.status = "processing"


# GOOD: Enum for type-safe state
class OrderGood:
    """Order with enum-based state."""

    class Status(Enum):
        """Order status enumeration."""

        PENDING = auto()
        PROCESSING = auto()
        COMPLETED = auto()
        CANCELLED = auto()

    def __init__(self, order_id: str):
        """Initialize order.

        Args:
            order_id: Unique order identifier
        """
        self._order_id = order_id
        self._status = self.Status.PENDING

    @property
    def status(self) -> Status:
        """Current order status (read-only)."""
        return self._status

    def process(self) -> None:
        """Begin processing order.

        Raises:
            ValueError: If order is not in PENDING state
        """
        if self._status != self.Status.PENDING:
            raise ValueError(f"Cannot process order in {self._status} state")

        self._status = self.Status.PROCESSING


# ============================================================================
# EXAMPLE 4: Mutable Default Arguments - THE GOTCHA
# ============================================================================

# BAD: Mutable default argument (shared across calls!)
def add_item_bad(item: str, items: List[str] = []) -> List[str]:
    """WRONG: List is shared across all calls."""
    items.append(item)
    return items


# GOOD: Use None, create fresh list in body
def add_item_good(item: str, items: Optional[List[str]] = None) -> List[str]:
    """Create fresh list if not provided."""
    if items is None:
        items = []

    items.append(item)
    return items


# BAD: Mutable default in class
class ShoppingCartBad:
    """Cart with mutable default argument."""

    def __init__(self, items: List[str] = []):  # WRONG: Shared across instances!
        self.items = items


# GOOD: Use None, create fresh list
class ShoppingCartGood:
    """Cart with proper default handling."""

    def __init__(self, items: Optional[List[str]] = None):
        """Initialize cart.

        Args:
            items: Initial items (creates empty list if None)
        """
        self._items = items if items is not None else []

    @property
    def items(self) -> List[str]:
        """Current items (read-only copy)."""
        return self._items.copy()


# ============================================================================
# EXAMPLE 5: Using dataclass with field() for Defaults
# ============================================================================

# BAD: Manual __init__ with mutable defaults
class ConfigBad:
    """Config with manual initialization."""

    def __init__(self, name: str, tags: List[str] = []):  # WRONG
        self.name = name
        self.tags = tags


# GOOD: dataclass with field() for mutable defaults
@dataclass
class ConfigGood:
    """Config using dataclass with safe defaults."""

    name: str
    timeout: int = 30
    tags: List[str] = field(default_factory=list)  # Safe mutable default
    metadata: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# EXAMPLE 6: Initialize at Declaration
# ============================================================================

# BAD: Uninitialized variables
class DataProcessorBad:
    """Processor with uninitialized variables."""

    def __init__(self):
        self.data = None  # Initialized but to None
        self.processed = None

    def load(self, data):
        self.data = data  # Risk: what if load() never called?

    def process(self):
        result = self.data.process()  # May fail if load() not called


# GOOD: Initialize with sensible defaults
class DataProcessorGood:
    """Processor with proper initialization."""

    def __init__(self, data: Optional[List[int]] = None):
        """Initialize processor.

        Args:
            data: Initial data to process (empty list if None)
        """
        self._data: List[int] = data if data is not None else []
        self._processed: bool = False
        self._result: Optional[List[int]] = None

    def load(self, data: List[int]) -> None:
        """Load data for processing.

        Args:
            data: Data to process

        Raises:
            ValueError: If data is empty
        """
        if not data:
            raise ValueError("Data cannot be empty")

        self._data = data
        self._processed = False
        self._result = None

    def process(self) -> List[int]:
        """Process loaded data.

        Returns:
            Processed data

        Raises:
            ValueError: If no data loaded
        """
        if not self._data:
            raise ValueError("No data loaded for processing")

        self._result = [x * 2 for x in self._data]
        self._processed = True
        return self._result


# ============================================================================
# EXAMPLE 7: Complex Object Construction
# ============================================================================

# BAD: Complex initialization in __init__
class DatabaseConnectionBad:
    """Database connection with complex setup."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        # Complex setup in __init__ - hard to test
        self.connection = self._connect()
        self.pool = self._create_pool()


# GOOD: Factory method or builder pattern
class DatabaseConnectionGood:
    """Database connection with factory method."""

    DEFAULT_PORT = 5432
    DEFAULT_POOL_SIZE = 10

    def __init__(
        self, host: str, port: int = DEFAULT_PORT, pool_size: int = DEFAULT_POOL_SIZE
    ):
        """Initialize connection parameters.

        Args:
            host: Database host
            port: Database port
            pool_size: Connection pool size
        """
        self._host = host
        self._port = port
        self._pool_size = pool_size
        self._connection: Optional[object] = None
        self._pool: Optional[object] = None

    @classmethod
    def create_with_defaults(cls, host: str) -> "DatabaseConnectionGood":
        """Factory method for common configuration.

        Args:
            host: Database host

        Returns:
            Configured database connection
        """
        return cls(host=host, port=cls.DEFAULT_PORT, pool_size=cls.DEFAULT_POOL_SIZE)

    @classmethod
    def create_production(cls, host: str) -> "DatabaseConnectionGood":
        """Factory method for production configuration.

        Args:
            host: Database host

        Returns:
            Production-ready connection with large pool
        """
        PRODUCTION_POOL_SIZE = 50
        PRODUCTION_PORT = 5432

        return cls(host=host, port=PRODUCTION_PORT, pool_size=PRODUCTION_POOL_SIZE)


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 4: Demonstrating the mutable default argument gotcha
    print("=== Mutable Default Argument Gotcha ===")

    # BAD: Shows the problem
    result1 = add_item_bad("apple")
    result2 = add_item_bad("banana")
    print(f"Bad result1: {result1}")  # ['apple', 'banana'] - SHARED!
    print(f"Bad result2: {result2}")  # ['apple', 'banana'] - SAME LIST!

    # GOOD: Each call gets fresh list
    result3 = add_item_good("apple")
    result4 = add_item_good("banana")
    print(f"Good result3: {result3}")  # ['apple']
    print(f"Good result4: {result4}")  # ['banana']

    # BAD: Class instance sharing
    cart1 = ShoppingCartBad()
    cart1.items.append("apple")
    cart2 = ShoppingCartBad()
    print(f"Cart2 items: {cart2.items}")  # ['apple'] - WRONG!

    # GOOD: Each instance gets own list
    cart3 = ShoppingCartGood()
    cart3._items.append("apple")
    cart4 = ShoppingCartGood()
    print(f"Cart4 items: {cart4.items}")  # [] - Correct!

    # Example 5: dataclass with field()
    config1 = ConfigGood(name="app1")
    config1.tags.append("production")
    config2 = ConfigGood(name="app2")
    print(f"Config2 tags: {config2.tags}")  # [] - Separate lists!

    # Example 7: Factory methods
    db = DatabaseConnectionGood.create_production("db.example.com")
    print(f"Production DB pool size: {db._pool_size}")
