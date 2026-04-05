# test_agent_lifecycle.py
# Developer: Marcus Daley
# Date: 2026-04-04
# Purpose: Tests for agent lifecycle state machine, registry, and runtime

import pytest
from scripts.agent_base import BaseAgent
from scripts.agent_protocol import AgentStatus, AgentInfo, Agent
from scripts.agent_registry import AgentRegistry
from scripts.agent_event_bus import EventBus


class TestBaseAgentLifecycle:

    def test_initial_status_uninitialized(self):
        agent = BaseAgent("test", "test-type")
        assert agent.status == AgentStatus.UNINITIALIZED

    def test_configure_transitions_to_configured(self):
        agent = BaseAgent("test", "test-type")
        agent.configure({})
        assert agent.status == AgentStatus.CONFIGURED

    def test_start_transitions_to_running(self):
        agent = BaseAgent("test", "test-type")
        agent.configure({})
        agent.start()
        assert agent.status == AgentStatus.RUNNING

    def test_pause_transitions_to_paused(self):
        agent = BaseAgent("test", "test-type")
        agent.configure({})
        agent.start()
        agent.pause()
        assert agent.status == AgentStatus.PAUSED

    def test_resume_transitions_to_running(self):
        agent = BaseAgent("test", "test-type")
        agent.configure({})
        agent.start()
        agent.pause()
        agent.resume()
        assert agent.status == AgentStatus.RUNNING

    def test_stop_transitions_to_stopped(self):
        agent = BaseAgent("test", "test-type")
        agent.configure({})
        agent.start()
        agent.stop()
        assert agent.status == AgentStatus.STOPPED

    def test_invalid_transition_raises(self):
        agent = BaseAgent("test", "test-type")
        with pytest.raises(RuntimeError, match="invalid transition"):
            agent.start()  # Can't go UNINITIALIZED -> RUNNING

    def test_get_info_returns_agent_info(self):
        agent = BaseAgent("test", "test-type")
        info = agent.get_info()
        assert isinstance(info, AgentInfo)
        assert info.name == "test"
        assert info.agent_type == "test-type"
        assert info.status == AgentStatus.UNINITIALIZED

    def test_satisfies_agent_protocol(self):
        agent = BaseAgent("test", "test-type")
        assert isinstance(agent, Agent)

    def test_metrics_tracking(self):
        agent = BaseAgent("test", "test-type")
        agent.configure({})
        agent.start()
        agent._record_processed()
        agent._record_processed()
        agent._record_emitted()
        info = agent.get_info()
        assert info.events_processed == 2
        assert info.events_emitted == 1


class TestAgentRegistry:

    def test_register_and_get(self):
        registry = AgentRegistry()
        agent = BaseAgent("a1", "test")
        registry.register(agent)
        assert registry.get("a1") is agent

    def test_duplicate_register_raises(self):
        registry = AgentRegistry()
        agent = BaseAgent("a1", "test")
        registry.register(agent)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(agent)

    def test_unregister(self):
        registry = AgentRegistry()
        agent = BaseAgent("a1", "test")
        registry.register(agent)
        registry.unregister("a1")
        assert registry.get("a1") is None

    def test_get_by_type(self):
        registry = AgentRegistry()
        registry.register(BaseAgent("a1", "extractor"))
        registry.register(BaseAgent("a2", "validator"))
        registry.register(BaseAgent("a3", "extractor"))
        extractors = registry.get_by_type("extractor")
        assert len(extractors) == 2

    def test_get_by_status(self):
        registry = AgentRegistry()
        a1 = BaseAgent("a1", "test")
        a2 = BaseAgent("a2", "test")
        a1.configure({})
        registry.register(a1)
        registry.register(a2)
        configured = registry.get_by_status(AgentStatus.CONFIGURED)
        assert len(configured) == 1
        assert configured[0].name == "a1"

    def test_start_all(self):
        registry = AgentRegistry()
        a1 = BaseAgent("a1", "test")
        a2 = BaseAgent("a2", "test")
        a1.configure({})
        a2.configure({})
        registry.register(a1)
        registry.register(a2)
        started = registry.start_all()
        assert len(started) == 2

    def test_stop_all(self):
        registry = AgentRegistry()
        a1 = BaseAgent("a1", "test")
        a1.configure({})
        a1.start()
        registry.register(a1)
        stopped = registry.stop_all()
        assert len(stopped) == 1

    def test_count(self):
        registry = AgentRegistry()
        assert registry.count == 0
        registry.register(BaseAgent("a1", "test"))
        assert registry.count == 1

    def test_get_all_info(self):
        registry = AgentRegistry()
        registry.register(BaseAgent("a1", "test"))
        registry.register(BaseAgent("a2", "test"))
        infos = registry.get_all_info()
        assert len(infos) == 2
        assert all(isinstance(i, AgentInfo) for i in infos)
