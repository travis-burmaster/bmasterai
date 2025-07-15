"""
Comprehensive tests for BMasterAI including stateful agents and multi-agent coordination
"""

import pytest
import sys
import os
import time
import threading
from unittest.mock import Mock, patch

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bmasterai.logging import configure_logging, LogLevel, EventType
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager


class TestStatefulAgent:
    """Test the StatefulAgent functionality"""

    def setup_method(self):
        """Setup for each test"""
        # Import here to avoid circular imports
        from examples.enhanced_examples import StatefulAgent
        self.StatefulAgent = StatefulAgent

        # Configure logging for tests
        configure_logging(log_level=LogLevel.INFO)

    def test_agent_creation(self):
        """Test agent creation and initialization"""
        agent = self.StatefulAgent("test-agent", "TestAgent", {"test": True})

        assert agent.agent_id == "test-agent"
        assert agent.name == "TestAgent"
        assert agent.state.agent_id == "test-agent"
        assert agent.state.status == "initialized"
        assert agent.state.metadata["test"] is True
        assert len(agent.task_history) == 0
        assert len(agent.memory) == 0

    def test_agent_start_stop(self):
        """Test agent start and stop functionality"""
        agent = self.StatefulAgent("test-agent", "TestAgent")

        # Test start
        agent.start()
        assert agent.running is True
        assert agent.state.status == "running"
        assert agent.thread is not None

        # Test stop
        agent.stop()
        assert agent.running is False
        assert agent.state.status == "stopped"

    def test_data_processing_task(self):
        """Test data processing task execution"""
        agent = self.StatefulAgent("test-agent", "TestAgent")
        agent.start()

        try:
            # Test sum operation
            result = agent.execute_task("data_processing", {
                "data": [1, 2, 3, 4, 5],
                "operation": "sum"
            })

            assert result["success"] is True
            assert result["result"]["result"] == 15
            assert result["result"]["operation"] == "sum"
            assert agent.state.task_count == 1

            # Test average operation
            result = agent.execute_task("data_processing", {
                "data": [10, 20, 30],
                "operation": "average"
            })

            assert result["success"] is True
            assert result["result"]["result"] == 20.0
            assert agent.state.task_count == 2

        finally:
            agent.stop()

    def test_memory_operations(self):
        """Test agent memory operations"""
        agent = self.StatefulAgent("test-agent", "TestAgent")
        agent.start()

        try:
            # Test set operation
            result = agent.execute_task("memory_operation", {
                "operation": "set",
                "key": "test_key",
                "value": "test_value"
            })

            assert result["success"] is True
            assert result["result"]["set"] is True
            assert agent.memory["test_key"] == "test_value"

            # Test get operation
            result = agent.execute_task("memory_operation", {
                "operation": "get",
                "key": "test_key"
            })

            assert result["success"] is True
            assert result["result"]["value"] == "test_value"

            # Test size operation
            result = agent.execute_task("memory_operation", {
                "operation": "size"
            })

            assert result["success"] is True
            assert result["result"]["memory_size"] > 0  # Should have processing results + test_key

        finally:
            agent.stop()

    def test_state_persistence(self):
        """Test that agent state persists across tasks"""
        agent = self.StatefulAgent("test-agent", "TestAgent")
        agent.start()

        try:
            # Execute multiple tasks
            for i in range(3):
                agent.execute_task("data_processing", {
                    "data": [i, i+1, i+2],
                    "operation": "sum"
                })

            # Check state
            state = agent.get_state_summary()
            assert state["task_count"] == 3
            assert len(state["recent_tasks"]) == 3
            assert len(agent.memory) > 0  # Should have processing results

        finally:
            agent.stop()


class TestMultiAgentOrchestrator:
    """Test the MultiAgentOrchestrator functionality"""

    def setup_method(self):
        """Setup for each test"""
        from examples.enhanced_examples import StatefulAgent, MultiAgentOrchestrator
        self.StatefulAgent = StatefulAgent
        self.MultiAgentOrchestrator = MultiAgentOrchestrator

        configure_logging(log_level=LogLevel.INFO)

    def test_orchestrator_creation(self):
        """Test orchestrator creation"""
        orchestrator = self.MultiAgentOrchestrator("test-orchestrator")

        assert orchestrator.orchestrator_id == "test-orchestrator"
        assert len(orchestrator.agents) == 0
        assert len(orchestrator.coordination_history) == 0

    def test_agent_management(self):
        """Test adding and removing agents"""
        orchestrator = self.MultiAgentOrchestrator("test-orchestrator")
        agent1 = self.StatefulAgent("agent-1", "Agent1")
        agent2 = self.StatefulAgent("agent-2", "Agent2")

        # Test adding agents
        orchestrator.add_agent(agent1)
        orchestrator.add_agent(agent2)

        assert len(orchestrator.agents) == 2
        assert "agent-1" in orchestrator.agents
        assert "agent-2" in orchestrator.agents

        # Test removing agent
        orchestrator.remove_agent("agent-1")
        assert len(orchestrator.agents) == 1
        assert "agent-1" not in orchestrator.agents

    def test_agent_lifecycle_management(self):
        """Test starting and stopping all agents"""
        orchestrator = self.MultiAgentOrchestrator("test-orchestrator")
        agent1 = self.StatefulAgent("agent-1", "Agent1")
        agent2 = self.StatefulAgent("agent-2", "Agent2")

        orchestrator.add_agent(agent1)
        orchestrator.add_agent(agent2)

        # Test starting all agents
        started_count = orchestrator.start_all_agents()
        assert started_count == 2
        assert agent1.running is True
        assert agent2.running is True

        # Test stopping all agents
        stopped_count = orchestrator.stop_all_agents()
        assert stopped_count == 2
        assert agent1.running is False
        assert agent2.running is False

    def test_task_coordination(self):
        """Test coordinating tasks across multiple agents"""
        orchestrator = self.MultiAgentOrchestrator("test-orchestrator")
        agent1 = self.StatefulAgent("agent-1", "Agent1")
        agent2 = self.StatefulAgent("agent-2", "Agent2")

        orchestrator.add_agent(agent1)
        orchestrator.add_agent(agent2)
        orchestrator.start_all_agents()

        try:
            # Define task assignments
            task_assignments = {
                "agent-1": ("data_processing", {
                    "data": [1, 2, 3],
                    "operation": "sum"
                }),
                "agent-2": ("memory_operation", {
                    "operation": "set",
                    "key": "test",
                    "value": "coordination_test"
                })
            }

            # Coordinate tasks
            result = orchestrator.coordinate_task("test-coordination", task_assignments)

            assert result["success"] is True
            assert result["coordination_id"] == "test-coordination"
            assert len(result["results"]) == 2
            assert "agent-1" in result["results"]
            assert "agent-2" in result["results"]
            assert len(result["errors"]) == 0

            # Check coordination history
            assert len(orchestrator.coordination_history) == 1

        finally:
            orchestrator.stop_all_agents()

    def test_orchestrator_status(self):
        """Test getting orchestrator status"""
        orchestrator = self.MultiAgentOrchestrator("test-orchestrator")
        agent = self.StatefulAgent("agent-1", "Agent1")

        orchestrator.add_agent(agent)
        orchestrator.start_all_agents()

        try:
            # Execute a task to generate some activity
            agent.execute_task("data_processing", {
                "data": [1, 2, 3],
                "operation": "sum"
            })

            # Get status
            status = orchestrator.get_orchestrator_status()

            assert status["orchestrator_id"] == "test-orchestrator"
            assert status["total_agents"] == 1
            assert status["running_agents"] == 1
            assert "agent-1" in status["agent_statuses"]
            assert status["agent_statuses"]["agent-1"]["task_count"] == 1

        finally:
            orchestrator.stop_all_agents()


class TestLoggingIntegration:
    """Test logging integration with agents"""

    def test_logging_configuration(self):
        """Test basic logging configuration"""
        logger = configure_logging(log_level=LogLevel.INFO)
        assert logger is not None

    def test_agent_logging_events(self):
        """Test that agents generate proper logging events"""
        from examples.enhanced_examples import StatefulAgent

        configure_logging(log_level=LogLevel.INFO)
        agent = StatefulAgent("test-agent", "TestAgent")

        # Mock the logger to capture events
        with patch.object(agent.logger, 'log_event') as mock_log:
            agent.start()
            agent.execute_task("data_processing", {"data": [1, 2, 3], "operation": "sum"})
            agent.stop()

            # Verify logging events were called
            assert mock_log.call_count >= 3  # At least start, task, stop events

            # Check for specific event types
            event_types = [call[0][1] for call in mock_log.call_args_list]  # event_type is the second parameter
            assert EventType.AGENT_START in event_types
            assert EventType.TASK_START in event_types
            assert EventType.TASK_COMPLETE in event_types
            assert EventType.AGENT_STOP in event_types


class TestMonitoringIntegration:
    """Test monitoring integration with agents"""

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        monitor = get_monitor()
        assert monitor is not None

    def test_agent_registration_with_monitor(self):
        """Test that agents register with the monitor"""
        from examples.enhanced_examples import StatefulAgent

        configure_logging(log_level=LogLevel.INFO)
        monitor = get_monitor()

        agent = StatefulAgent("test-agent", "TestAgent")

        # Mock the monitor to capture agent tracking
        with patch.object(monitor, 'track_agent_start') as mock_track_start:
            agent.start()
            mock_track_start.assert_called_once_with("test-agent")
            agent.stop()


def test_integration_manager():
    """Test integration manager initialization"""
    manager = get_integration_manager()
    assert manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
