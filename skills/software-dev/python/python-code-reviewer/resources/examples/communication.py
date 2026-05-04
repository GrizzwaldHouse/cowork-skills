# communication.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Demonstrates event-driven communication patterns - observer pattern, callbacks, signals instead of polling loops.

"""
Communication Patterns Examples

Shows proper event-driven communication using observer pattern,
callbacks, and signals. Demonstrates why polling is an anti-pattern.
"""

from typing import Callable, List, Optional, Any, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time


# ============================================================================
# EXAMPLE 1: Polling vs Event-Driven (The Problem)
# ============================================================================

# BAD: Polling loop
class DataMonitorBad:
    """Data monitor using polling (CPU-intensive, inefficient)."""

    def __init__(self, data_source):
        self.data_source = data_source
        self.last_value = None

    def monitor(self):
        """Continuously poll for changes - BAD!"""
        while True:
            current = self.data_source.get_value()
            if current != self.last_value:
                self.update_display(current)
                self.last_value = current
            time.sleep(0.1)  # Still wastes CPU

    def update_display(self, value):
        print(f"Display updated: {value}")


# GOOD: Event-driven with callback
class DataMonitorGood:
    """Data monitor using event-driven callback pattern."""

    def __init__(self, data_source: "DataSourceGood"):
        """Initialize monitor with data source.

        Args:
            data_source: Data source that emits change events
        """
        self._data_source = data_source
        # Subscribe to changes - no polling needed
        self._data_source.subscribe(self._on_data_changed)

    def _on_data_changed(self, new_value: Any) -> None:
        """Handle data change event.

        Args:
            new_value: New data value
        """
        self._update_display(new_value)

    def _update_display(self, value: Any) -> None:
        """Update display with new value."""
        print(f"Display updated: {value}")

    def cleanup(self) -> None:
        """Clean up subscriptions."""
        self._data_source.unsubscribe(self._on_data_changed)


# ============================================================================
# EXAMPLE 2: Simple Observer Pattern
# ============================================================================

EventListener = Callable[[Any], None]


class DataSourceGood:
    """Data source with event emission."""

    def __init__(self):
        self._value: Optional[Any] = None
        self._listeners: List[EventListener] = []

    @property
    def value(self) -> Optional[Any]:
        """Current value (read-only)."""
        return self._value

    def subscribe(self, listener: EventListener) -> None:
        """Subscribe to value changes.

        Args:
            listener: Callback function(new_value) to invoke on changes
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: EventListener) -> None:
        """Unsubscribe from value changes.

        Args:
            listener: Callback to remove

        Raises:
            ValueError: If listener not found
        """
        self._listeners.remove(listener)

    def set_value(self, new_value: Any) -> None:
        """Update value and notify subscribers.

        Args:
            new_value: New value to set
        """
        if new_value != self._value:
            self._value = new_value
            self._notify_listeners(new_value)

    def _notify_listeners(self, value: Any) -> None:
        """Notify all subscribers of change.

        Args:
            value: New value to broadcast
        """
        for listener in self._listeners.copy():  # Copy to allow unsubscribe during callback
            try:
                listener(value)
            except Exception as e:
                print(f"Error in listener: {e}")


# ============================================================================
# EXAMPLE 3: Observer Pattern with Typed Events
# ============================================================================

@dataclass
class HealthChangedEvent:
    """Event data for health changes."""

    old_value: int
    new_value: int
    source: "Player"


@dataclass
class LevelUpEvent:
    """Event data for level up."""

    new_level: int
    player: "Player"


class IObserver(Protocol):
    """Observer interface for type-safe callbacks."""

    def on_health_changed(self, event: HealthChangedEvent) -> None:
        """Handle health change event."""
        ...

    def on_level_up(self, event: LevelUpEvent) -> None:
        """Handle level up event."""
        ...


class Player:
    """Player with typed event emission."""

    MAX_HEALTH = 100

    def __init__(self, name: str):
        self._name = name
        self._health = self.MAX_HEALTH
        self._level = 1
        self._observers: List[IObserver] = []

    @property
    def health(self) -> int:
        """Current health (read-only)."""
        return self._health

    @property
    def level(self) -> int:
        """Current level (read-only)."""
        return self._level

    def subscribe(self, observer: IObserver) -> None:
        """Subscribe to player events.

        Args:
            observer: Observer implementing IObserver protocol
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: IObserver) -> None:
        """Unsubscribe from player events.

        Args:
            observer: Observer to remove
        """
        self._observers.remove(observer)

    def take_damage(self, amount: int) -> None:
        """Apply damage and emit event.

        Args:
            amount: Damage amount (non-negative)
        """
        if amount < 0:
            raise ValueError("Damage must be non-negative")

        old_health = self._health
        self._health = max(0, self._health - amount)

        if old_health != self._health:
            event = HealthChangedEvent(
                old_value=old_health, new_value=self._health, source=self
            )
            self._notify_health_changed(event)

    def level_up(self) -> None:
        """Increase level and emit event."""
        self._level += 1
        event = LevelUpEvent(new_level=self._level, player=self)
        self._notify_level_up(event)

    def _notify_health_changed(self, event: HealthChangedEvent) -> None:
        """Notify observers of health change."""
        for observer in self._observers.copy():
            observer.on_health_changed(event)

    def _notify_level_up(self, event: LevelUpEvent) -> None:
        """Notify observers of level up."""
        for observer in self._observers.copy():
            observer.on_level_up(event)


class UIController:
    """UI controller observing player events."""

    def on_health_changed(self, event: HealthChangedEvent) -> None:
        """Update health bar on health change."""
        print(f"Health bar updated: {event.old_value} -> {event.new_value}")

    def on_level_up(self, event: LevelUpEvent) -> None:
        """Show level up notification."""
        print(f"Level up notification: Now level {event.new_level}!")


class AudioController:
    """Audio controller observing player events."""

    def on_health_changed(self, event: HealthChangedEvent) -> None:
        """Play damage sound on health decrease."""
        if event.new_value < event.old_value:
            print("Playing damage sound effect")

    def on_level_up(self, event: LevelUpEvent) -> None:
        """Play level up fanfare."""
        print("Playing level up fanfare")


# ============================================================================
# EXAMPLE 4: Abstract Base Class Observer Pattern
# ============================================================================

class Observer(ABC):
    """Abstract observer base class."""

    @abstractmethod
    def update(self, subject: "Subject", data: Any) -> None:
        """Handle subject state change.

        Args:
            subject: Subject that changed
            data: Change data
        """
        pass


class Subject:
    """Observable subject with observer management."""

    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Attach observer.

        Args:
            observer: Observer to attach
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach observer.

        Args:
            observer: Observer to detach
        """
        self._observers.remove(observer)

    def notify(self, data: Any) -> None:
        """Notify all observers of change.

        Args:
            data: Change data to broadcast
        """
        for observer in self._observers.copy():
            observer.update(self, data)


class StockPrice(Subject):
    """Stock price observable."""

    def __init__(self, symbol: str, initial_price: float):
        super().__init__()
        self._symbol = symbol
        self._price = initial_price

    @property
    def symbol(self) -> str:
        """Stock symbol."""
        return self._symbol

    @property
    def price(self) -> float:
        """Current price."""
        return self._price

    def set_price(self, new_price: float) -> None:
        """Update price and notify observers.

        Args:
            new_price: New stock price
        """
        if new_price != self._price:
            old_price = self._price
            self._price = new_price
            self.notify({"old": old_price, "new": new_price})


class PriceAlertObserver(Observer):
    """Observer that alerts on price thresholds."""

    def __init__(self, threshold: float):
        self._threshold = threshold

    def update(self, subject: Subject, data: Any) -> None:
        """Handle price update."""
        if isinstance(subject, StockPrice):
            if data["new"] > self._threshold:
                print(f"ALERT: {subject.symbol} exceeded ${self._threshold}!")


# ============================================================================
# EXAMPLE 5: Event Bus Pattern
# ============================================================================

class EventBus:
    """Centralized event bus for decoupled communication."""

    def __init__(self):
        self._subscribers: dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type.

        Args:
            event_type: Event type identifier
            handler: Callback function to invoke
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type.

        Args:
            event_type: Event type identifier
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    def publish(self, event_type: str, data: Any) -> None:
        """Publish event to all subscribers.

        Args:
            event_type: Event type identifier
            data: Event data payload
        """
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type].copy():
                try:
                    handler(data)
                except Exception as e:
                    print(f"Error handling {event_type} event: {e}")


# Usage with event bus
event_bus = EventBus()


class AnalyticsService:
    """Analytics service listening to app events."""

    def __init__(self, bus: EventBus):
        bus.subscribe("user.login", self._track_login)
        bus.subscribe("purchase.completed", self._track_purchase)

    def _track_login(self, data: dict) -> None:
        """Track user login event."""
        print(f"Analytics: User {data['user_id']} logged in")

    def _track_purchase(self, data: dict) -> None:
        """Track purchase event."""
        print(f"Analytics: Purchase ${data['amount']} by {data['user_id']}")


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    print("=== Example 2: Simple Observer ===")
    source = DataSourceGood()
    monitor = DataMonitorGood(source)
    source.set_value(42)  # Triggers display update
    monitor.cleanup()

    print("\n=== Example 3: Typed Events ===")
    player = Player("Hero")
    ui = UIController()
    audio = AudioController()

    player.subscribe(ui)
    player.subscribe(audio)

    player.take_damage(25)  # Both UI and audio notified
    player.level_up()  # Both UI and audio notified

    print("\n=== Example 4: Abstract Observer ===")
    stock = StockPrice("AAPL", 150.0)
    alert = PriceAlertObserver(threshold=160.0)
    stock.attach(alert)
    stock.set_price(165.0)  # Triggers alert

    print("\n=== Example 5: Event Bus ===")
    bus = EventBus()
    analytics = AnalyticsService(bus)
    bus.publish("user.login", {"user_id": "user123"})
    bus.publish("purchase.completed", {"user_id": "user123", "amount": 99.99})
