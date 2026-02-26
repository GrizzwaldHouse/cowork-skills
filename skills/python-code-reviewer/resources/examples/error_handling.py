# error_handling.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Demonstrates proper error handling - specific exceptions, validation at boundaries, contextual error messages, no swallowing errors.

"""
Error Handling Examples

Shows proper exception handling, input validation, null checks,
and typed error patterns. Demonstrates anti-patterns to avoid.
"""

from typing import Optional, Union, TypeVar, Generic
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json


# ============================================================================
# EXAMPLE 1: Bare Except vs Specific Exceptions
# ============================================================================

# BAD: Bare except swallows all errors
def load_config_bad(path: str) -> dict:
    """Load config with bare except - BAD!"""
    try:
        return json.load(open(path))
    except:  # Catches EVERYTHING including KeyboardInterrupt!
        return {}  # Silent failure - no way to know what went wrong


# GOOD: Specific exceptions with context
def load_config_good(path: Path) -> dict:
    """Load configuration from JSON file.

    Args:
        path: Path to configuration file

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If file contains invalid JSON or wrong type
        PermissionError: If file cannot be read due to permissions
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        if not isinstance(config, dict):
            raise ValueError(
                f"Configuration must be a JSON object, got {type(config).__name__}"
            )

        return config

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file {path}: {e}") from e
    except PermissionError as e:
        raise PermissionError(f"Cannot read configuration file {path}: {e}") from e


# ============================================================================
# EXAMPLE 2: Input Validation at Boundaries
# ============================================================================

# BAD: No validation, fails with cryptic errors
def calculate_discount_bad(price, discount_percent):
    """Calculate discount - no validation."""
    return price - (price * discount_percent / 100)


# GOOD: Validate at boundary with clear errors
def calculate_discount_good(price: float, discount_percent: float) -> float:
    """Calculate discounted price with validation.

    Args:
        price: Original price (must be non-negative)
        discount_percent: Discount percentage (0-100)

    Returns:
        Price after discount

    Raises:
        ValueError: If price is negative or discount is out of range
        TypeError: If arguments are not numeric
    """
    # Type validation
    if not isinstance(price, (int, float)):
        raise TypeError(f"Price must be numeric, got {type(price).__name__}")

    if not isinstance(discount_percent, (int, float)):
        raise TypeError(
            f"Discount must be numeric, got {type(discount_percent).__name__}"
        )

    # Value validation
    if price < 0:
        raise ValueError(f"Price cannot be negative: {price}")

    if not 0 <= discount_percent <= 100:
        raise ValueError(
            f"Discount percent must be between 0 and 100, got {discount_percent}"
        )

    discount_amount = price * discount_percent / 100
    return price - discount_amount


# ============================================================================
# EXAMPLE 3: Null/None Checks
# ============================================================================

# BAD: No null checks
def process_user_bad(user):
    """Process user - assumes user is not None."""
    return user.name.upper()  # Crashes if user or name is None


# GOOD: Explicit None checks
def process_user_good(user: Optional[dict]) -> str:
    """Process user data with None safety.

    Args:
        user: User dictionary with 'name' field

    Returns:
        Uppercase username

    Raises:
        ValueError: If user is None or missing required fields
    """
    if user is None:
        raise ValueError("User cannot be None")

    if "name" not in user:
        raise ValueError("User must have 'name' field")

    name = user["name"]
    if name is None:
        raise ValueError("User name cannot be None")

    if not isinstance(name, str):
        raise TypeError(f"User name must be string, got {type(name).__name__}")

    return name.upper()


# ============================================================================
# EXAMPLE 4: Result Type Pattern (Typed Error Handling)
# ============================================================================

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Ok(Generic[T]):
    """Success result."""

    value: T


@dataclass
class Err(Generic[E]):
    """Error result."""

    error: E


Result = Union[Ok[T], Err[E]]


class ValidationError(Exception):
    """Custom validation error with details."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def parse_age(value: str) -> Result[int, ValidationError]:
    """Parse age from string with Result type.

    Args:
        value: String to parse

    Returns:
        Ok(age) if valid, Err(error) if invalid
    """
    try:
        age = int(value)
    except ValueError:
        return Err(ValidationError("age", f"Must be a number, got '{value}'"))

    if age < 0:
        return Err(ValidationError("age", f"Cannot be negative: {age}"))

    if age > 150:
        return Err(ValidationError("age", f"Unrealistic age: {age}"))

    return Ok(age)


# Usage of Result type
def process_age_input(user_input: str) -> None:
    """Process age input with Result pattern."""
    result = parse_age(user_input)

    match result:
        case Ok(age):
            print(f"Valid age: {age}")
        case Err(error):
            print(f"Error: {error.message}")


# ============================================================================
# EXAMPLE 5: Custom Exception Hierarchy
# ============================================================================

class DatabaseError(Exception):
    """Base exception for database errors."""

    pass


class ConnectionError(DatabaseError):
    """Database connection failed."""

    def __init__(self, host: str, port: int, reason: str):
        self.host = host
        self.port = port
        self.reason = reason
        super().__init__(f"Failed to connect to {host}:{port} - {reason}")


class QueryError(DatabaseError):
    """Database query failed."""

    def __init__(self, query: str, error: str):
        self.query = query
        self.error = error
        super().__init__(f"Query failed: {error}\nQuery: {query}")


class RecordNotFoundError(DatabaseError):
    """Database record not found."""

    def __init__(self, table: str, record_id: str):
        self.table = table
        self.record_id = record_id
        super().__init__(f"Record not found in {table}: {record_id}")


def fetch_user(user_id: str) -> dict:
    """Fetch user with specific error types.

    Args:
        user_id: User identifier

    Returns:
        User data dictionary

    Raises:
        ConnectionError: If database connection fails
        RecordNotFoundError: If user doesn't exist
        QueryError: If query execution fails
    """
    # Simulate different error conditions
    if not user_id:
        raise ValueError("User ID cannot be empty")

    # Example: connection failure
    # raise ConnectionError("localhost", 5432, "Connection refused")

    # Example: record not found
    # raise RecordNotFoundError("users", user_id)

    # Example: successful fetch
    return {"id": user_id, "name": "Test User"}


# ============================================================================
# EXAMPLE 6: Context Managers for Resource Cleanup
# ============================================================================

# BAD: Manual resource cleanup (easy to forget)
def process_file_bad(path: str) -> str:
    """Process file without context manager."""
    f = open(path)
    try:
        data = f.read()
        return data.upper()
    finally:
        f.close()  # Easy to forget!


# GOOD: Context manager ensures cleanup
def process_file_good(path: Path) -> str:
    """Process file with context manager.

    Args:
        path: File path

    Returns:
        Processed file contents

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = f.read()
            return data.upper()
    except PermissionError as e:
        raise PermissionError(f"Cannot read file {path}: {e}") from e
    except UnicodeDecodeError as e:
        raise ValueError(f"File {path} is not valid UTF-8: {e}") from e


# ============================================================================
# EXAMPLE 7: Fail Fast Principle
# ============================================================================

# BAD: Continue with bad data
def calculate_total_bad(items: list) -> float:
    """Calculate total - allows invalid data."""
    total = 0
    for item in items:
        total += item.get("price", 0)  # Silently uses 0 for missing price
    return total


# GOOD: Fail fast on invalid data
def calculate_total_good(items: list[dict]) -> float:
    """Calculate total with strict validation.

    Args:
        items: List of item dictionaries with 'price' field

    Returns:
        Total price

    Raises:
        ValueError: If any item is invalid or missing price
    """
    if not items:
        raise ValueError("Items list cannot be empty")

    total = 0.0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item {index} must be dict, got {type(item).__name__}")

        if "price" not in item:
            raise ValueError(f"Item {index} missing required 'price' field")

        price = item["price"]

        if not isinstance(price, (int, float)):
            raise ValueError(
                f"Item {index} price must be numeric, got {type(price).__name__}"
            )

        if price < 0:
            raise ValueError(f"Item {index} price cannot be negative: {price}")

        total += price

    return total


# ============================================================================
# EXAMPLE 8: Error Recovery vs Propagation
# ============================================================================

class RetryableError(Exception):
    """Error that can be retried."""

    pass


class FatalError(Exception):
    """Error that cannot be recovered from."""

    pass


def fetch_data_with_retry(url: str, max_attempts: int = 3) -> dict:
    """Fetch data with retry on transient errors.

    Args:
        url: URL to fetch
        max_attempts: Maximum retry attempts

    Returns:
        Fetched data

    Raises:
        FatalError: If error is not recoverable
        RetryableError: If max retries exceeded
    """
    for attempt in range(max_attempts):
        try:
            # Simulate fetch operation
            return _fetch_from_network(url)

        except ConnectionError as e:
            # Transient error - can retry
            if attempt == max_attempts - 1:
                raise RetryableError(
                    f"Failed after {max_attempts} attempts: {e}"
                ) from e
            print(f"Attempt {attempt + 1} failed, retrying...")

        except ValueError as e:
            # Fatal error - invalid URL, no point retrying
            raise FatalError(f"Invalid URL format: {e}") from e

    # Should never reach here due to raise in loop
    raise RetryableError(f"Failed after {max_attempts} attempts")


def _fetch_from_network(url: str) -> dict:
    """Simulate network fetch."""
    if not url.startswith("http"):
        raise ValueError(f"URL must start with http: {url}")
    # Simulate success
    return {"status": "ok"}


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    print("=== Example 1: Specific Exceptions ===")
    try:
        config = load_config_good(Path("config.json"))
        print(f"Config loaded: {config}")
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")

    print("\n=== Example 2: Input Validation ===")
    try:
        discounted = calculate_discount_good(100.0, 20.0)
        print(f"Discounted price: ${discounted}")

        # This will fail with clear error
        calculate_discount_good(-50.0, 20.0)
    except ValueError as e:
        print(f"Validation caught: {e}")

    print("\n=== Example 4: Result Type ===")
    process_age_input("25")  # Valid
    process_age_input("not a number")  # Invalid
    process_age_input("-5")  # Invalid

    print("\n=== Example 5: Custom Exceptions ===")
    try:
        user = fetch_user("user123")
        print(f"Fetched user: {user}")
    except RecordNotFoundError as e:
        print(f"Not found: {e}")
    except DatabaseError as e:
        print(f"Database error: {e}")

    print("\n=== Example 7: Fail Fast ===")
    try:
        items = [{"price": 10.0}, {"price": 20.0}, {"price": 15.0}]
        total = calculate_total_good(items)
        print(f"Total: ${total}")

        # This will fail fast
        invalid_items = [{"price": 10.0}, {"name": "Item"}]  # Missing price
        calculate_total_good(invalid_items)
    except ValueError as e:
        print(f"Validation caught: {e}")
