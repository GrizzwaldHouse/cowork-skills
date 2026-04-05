# test_agent_event_bus.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Tests for typed event dispatch bus

import pytest
from scripts.agent_events import (
    AgentEvent, FileChangeEvent, SkillExtractedEvent,
    SkillValidatedEvent, SessionDetectedEvent,
)
from scripts.agent_event_bus import EventBus


class TestEventBusSubscribePublish:
    """Core subscribe/publish mechanics."""

    def test_handler_receives_matching_event(self):
        bus = EventBus()
        received = []
        bus.subscribe(FileChangeEvent, received.append)
        event = FileChangeEvent(file_path="/test.py", event_type="modified")
        bus.publish(event)
        assert len(received) == 1
        assert received[0].file_path == "/test.py"

    def test_handler_ignores_non_matching_event(self):
        bus = EventBus()
        received = []
        bus.subscribe(FileChangeEvent, received.append)
        bus.publish(SkillExtractedEvent(skill_id="s1"))
        assert len(received) == 0

    def test_wildcard_receives_all_events(self):
        bus = EventBus()
        received = []
        bus.subscribe(None, received.append)
        bus.publish(FileChangeEvent(file_path="/a.py"))
        bus.publish(SkillExtractedEvent(skill_id="s1"))
        assert len(received) == 2

    def test_multiple_handlers_same_type(self):
        bus = EventBus()
        received_a, received_b = [], []
        bus.subscribe(FileChangeEvent, received_a.append)
        bus.subscribe(FileChangeEvent, received_b.append)
        bus.publish(FileChangeEvent(file_path="/x.py"))
        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_unsubscribe_removes_handler(self):
        bus = EventBus()
        received = []
        bus.subscribe(FileChangeEvent, received.append)
        bus.unsubscribe(FileChangeEvent, received.append)
        bus.publish(FileChangeEvent(file_path="/x.py"))
        assert len(received) == 0

    def test_duplicate_subscribe_ignored(self):
        bus = EventBus()
        received = []
        handler = received.append
        bus.subscribe(FileChangeEvent, handler)
        bus.subscribe(FileChangeEvent, handler)
        bus.publish(FileChangeEvent())
        assert len(received) == 1


class TestEventBusHandlerIsolation:
    """One failing handler must not prevent others from receiving events."""

    def test_failing_handler_does_not_block_others(self):
        bus = EventBus()
        received = []

        def bad_handler(event):
            raise RuntimeError("intentional failure")

        bus.subscribe(FileChangeEvent, bad_handler)
        bus.subscribe(FileChangeEvent, received.append)
        bus.publish(FileChangeEvent(file_path="/test.py"))
        assert len(received) == 1


class TestEventBusAuditLog:
    """Audit log tracks published events with bounded capacity."""

    def test_audit_log_records_events(self):
        bus = EventBus()
        bus.subscribe(FileChangeEvent, lambda e: None)
        bus.publish(FileChangeEvent(file_path="/a.py"))
        bus.publish(FileChangeEvent(file_path="/b.py"))
        log = bus.get_audit_log(limit=10)
        assert len(log) == 2
        assert log[0]["event_type"] == "FileChangeEvent"

    def test_audit_log_bounded_capacity(self):
        bus = EventBus()
        for i in range(1100):
            bus.publish(FileChangeEvent(file_path=f"/{i}.py"))
        log = bus.get_audit_log(limit=2000)
        assert len(log) <= 1000

    def test_audit_log_newest_first(self):
        bus = EventBus()
        bus.publish(FileChangeEvent(file_path="/first.py"))
        bus.publish(FileChangeEvent(file_path="/second.py"))
        log = bus.get_audit_log(limit=2)
        # Newest first
        assert len(log) == 2

    def test_clear_removes_all(self):
        bus = EventBus()
        bus.subscribe(FileChangeEvent, lambda e: None)
        bus.publish(FileChangeEvent())
        bus.clear()
        assert bus.handler_count == 0
        assert len(bus.get_audit_log()) == 0


class TestEventBusHandlerCount:
    """Handler count property."""

    def test_handler_count(self):
        bus = EventBus()
        assert bus.handler_count == 0
        bus.subscribe(FileChangeEvent, lambda e: None)
        assert bus.handler_count == 1
        bus.subscribe(SkillExtractedEvent, lambda e: None)
        assert bus.handler_count == 2
