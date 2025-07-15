"""
BMasterAI Enhanced Examples with Logging and Monitoring

This module contains comprehensive examples showing how to use BMasterAI
with the original stateful agent and multi-agent capabilities enhanced
with advanced logging and monitoring.
"""

import time
import threading
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import the new logging and monitoring systems
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager, SlackConnector, EmailConnector


@dataclass
class AgentState:
    """Represents the state of an agent"""
    agent_id: str
    status: str
    current_task: Optional[str] = None
    task_count: int = 0
    last_activity: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_activity is None:
            self.last_activity = datetime.now()


class StatefulAgent:
    """
    Enhanced Stateful Agent with comprehensive logging and monitoring

    This agent maintains state across tasks and provides full observability
    into its operations through structured logging and metrics collection.
    """

    def __init__(self, agent_id: str, name: str, initial_state: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.name = name
        self.state = AgentState(
            agent_id=agent_id,
            status="initialized",
            metadata=initial_state or {}
        )

        # Setup logging
        self.logger = get_logger()

        # Setup monitoring
        self.monitor = get_monitor()

        # Task history and state management
        self.task_history: List[Dict[str, Any]] = []
        self.memory: Dict[str, Any] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Log agent creation
        self.logger.log_event(
            agent_id,
            EventType.AGENT_START,
            f"Stateful agent {name} created",
            metadata={
                "agent_id": agent_id,
                "name": name,
                "initial_state": initial_state
            }
        )

    def start(self):
        """Start the agent with full monitoring"""
        if self.running:
            self.logger.log_event(self.agent_id, EventType.TASK_ERROR, "Agent already running")
            return

        self.running = True
        self.state.status = "running"
        self.state.last_activity = datetime.now()

        # Register with monitor
        self.monitor.track_agent_start(self.agent_id)

        # Start heartbeat thread
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Stateful agent {self.name} started",
            metadata={"agent_id": self.agent_id}
        )

    def stop(self):
        """Stop the agent gracefully"""
        if not self.running:
            return

        self.running = False
        self.state.status = "stopped"

        # Track agent stop
        self.monitor.track_agent_stop(self.agent_id)

        if self.thread:
            self.thread.join(timeout=5)

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_STOP,
            f"Stateful agent {self.name} stopped",
            metadata={
                "agent_id": self.agent_id,
                "total_tasks": self.state.task_count,
                "final_state": self.get_state_summary()
            }
        )

    def _heartbeat_loop(self):
        """Send periodic heartbeats to monitoring system"""
        while self.running:
            try:
                # Record custom metric for agent status
                self.monitor.metrics_collector.record_custom_metric(
                    "agent_status",
                    1,
                    {
                        "agent_id": self.agent_id,
                        "status": self.state.status,
                        "task_count": str(self.state.task_count)
                    }
                )

                # Log heartbeat
                self.logger.log_event(
                    self.agent_id,
                    EventType.PERFORMANCE_METRIC,
                    f"Agent {self.name} heartbeat",
                    metadata={
                        "agent_id": self.agent_id,
                        "status": self.state.status,
                        "task_count": self.state.task_count
                    }
                )

                time.sleep(30)  # Heartbeat every 30 seconds

            except Exception as e:
                self.logger.log_event(
                    self.agent_id,
                    EventType.TASK_ERROR,
                    f"Heartbeat error for agent {self.name}",
                    metadata={"agent_id": self.agent_id, "error": str(e)}
                )
                time.sleep(60)  # Wait longer on error

    def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with full state management and logging"""
        if not self.running:
            error_msg = f"Agent {self.name} is not running"
            self.logger.log_event(EventType.TASK_ERROR, error_msg)
            return {"success": False, "error": error_msg}

        task_id = f"task_{int(time.time() * 1000)}"
        start_time = time.time()

        # Update state
        self.state.current_task = task_id
        self.state.last_activity = datetime.now()

        # Log task start
        self.logger.log_event(
            self.agent_id,
            EventType.TASK_START,
            f"Task {task_type} started",
            metadata={
                "agent_id": self.agent_id,
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data
            }
        )

        try:
            # Execute the actual task based on type
            if task_type == "data_processing":
                result = self._process_data(task_data)
            elif task_type == "analysis":
                result = self._analyze_data(task_data)
            elif task_type == "memory_operation":
                result = self._memory_operation(task_data)
            elif task_type == "state_query":
                result = self._query_state(task_data)
            else:
                result = self._custom_task(task_type, task_data)

            # Update task count and history
            self.state.task_count += 1
            execution_time = time.time() - start_time

            task_record = {
                "task_id": task_id,
                "task_type": task_type,
                "start_time": start_time,
                "execution_time": execution_time,
                "success": result.get("success", True),
                "result_summary": str(result)[:200]  # Truncated for storage
            }

            self.task_history.append(task_record)

            # Keep only last 100 tasks in history
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]

            # Log successful completion
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Task {task_type} completed successfully",
                metadata={
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "execution_time": execution_time,
                    "result": result
                }
            )

            # Record metrics
            self.monitor.track_task_duration(
                self.agent_id,
                task_type,
                execution_time * 1000  # Convert to milliseconds
            )

            return {
                "success": True,
                "task_id": task_id,
                "execution_time": execution_time,
                "result": result
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            # Log error
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Task {task_type} failed",
                metadata={
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "error": error_msg,
                    "execution_time": execution_time
                }
            )

            # Record failed metrics
            self.monitor.track_error(self.agent_id, "task_failure")
            self.monitor.track_task_duration(
                self.agent_id,
                task_type,
                execution_time * 1000  # Convert to milliseconds
            )

            return {
                "success": False,
                "task_id": task_id,
                "error": error_msg,
                "execution_time": execution_time
            }

        finally:
            self.state.current_task = None

    def _process_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data and update agent memory"""
        data = task_data.get("data", [])
        operation = task_data.get("operation", "count")

        if operation == "count":
            result = len(data)
        elif operation == "sum" and all(isinstance(x, (int, float)) for x in data):
            result = sum(data)
        elif operation == "average" and all(isinstance(x, (int, float)) for x in data):
            result = sum(data) / len(data) if data else 0
        else:
            result = f"Processed {len(data)} items"

        # Store in memory
        memory_key = f"last_processing_{int(time.time())}"
        self.memory[memory_key] = {
            "operation": operation,
            "data_size": len(data),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "operation": operation,
            "result": result,
            "data_size": len(data),
            "memory_key": memory_key
        }

    def _analyze_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data using agent's memory and state"""
        analysis_type = task_data.get("type", "basic")
        data = task_data.get("data", {})

        # Use previous processing results from memory
        processing_history = [
            v for k, v in self.memory.items() 
            if k.startswith("last_processing_")
        ]

        analysis_result = {
            "analysis_type": analysis_type,
            "current_data": data,
            "historical_processing_count": len(processing_history),
            "agent_task_count": self.state.task_count,
            "analysis_timestamp": datetime.now().isoformat()
        }

        if analysis_type == "trend" and processing_history:
            # Simple trend analysis based on historical data
            recent_results = [h.get("result", 0) for h in processing_history[-5:]]
            if len(recent_results) > 1:
                trend = "increasing" if recent_results[-1] > recent_results[0] else "decreasing"
                analysis_result["trend"] = trend

        # Store analysis in memory
        memory_key = f"analysis_{int(time.time())}"
        self.memory[memory_key] = analysis_result

        return analysis_result

    def _memory_operation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform operations on agent memory"""
        operation = task_data.get("operation", "list")

        if operation == "list":
            return {"memory_keys": list(self.memory.keys())}
        elif operation == "get":
            key = task_data.get("key")
            return {"key": key, "value": self.memory.get(key)}
        elif operation == "set":
            key = task_data.get("key")
            value = task_data.get("value")
            self.memory[key] = value
            return {"key": key, "set": True}
        elif operation == "clear":
            cleared_count = len(self.memory)
            self.memory.clear()
            return {"cleared_items": cleared_count}
        elif operation == "size":
            return {"memory_size": len(self.memory)}
        else:
            return {"error": f"Unknown memory operation: {operation}"}

    def _query_state(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Query agent state information"""
        return self.get_state_summary()

    def _custom_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom task types - override in subclasses"""
        return {
            "message": f"Custom task {task_type} executed",
            "task_data": task_data,
            "agent_state": self.get_state_summary()
        }

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's current state"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.state.status,
            "task_count": self.state.task_count,
            "current_task": self.state.current_task,
            "memory_size": len(self.memory),
            "last_activity": self.state.last_activity.isoformat() if self.state.last_activity else None,
            "recent_tasks": self.task_history[-5:] if self.task_history else []
        }


class MultiAgentOrchestrator:
    """
    Enhanced Multi-Agent Orchestrator with comprehensive logging and monitoring

    Coordinates multiple stateful agents and provides centralized management
    with full observability into multi-agent operations.
    """

    def __init__(self, orchestrator_id: str = "orchestrator"):
        self.orchestrator_id = orchestrator_id
        self.agents: Dict[str, StatefulAgent] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.coordination_history: List[Dict[str, Any]] = []

        # Setup logging and monitoring
        self.logger = get_logger()
        self.monitor = get_monitor()

        # Integration manager for notifications
        self.integration_manager = get_integration_manager()

        self.logger.log_event(
            orchestrator_id,
            EventType.AGENT_START,
            f"Multi-agent orchestrator {orchestrator_id} initialized",
            metadata={"orchestrator_id": orchestrator_id}
        )

    def add_agent(self, agent: StatefulAgent):
        """Add an agent to the orchestrator"""
        self.agents[agent.agent_id] = agent

        self.logger.log_event(
            self.orchestrator_id,
            EventType.AGENT_COMMUNICATION,
            f"Agent {agent.name} added to orchestrator",
            metadata={
                "orchestrator_id": self.orchestrator_id,
                "agent_id": agent.agent_id,
                "agent_name": agent.name
            }
        )

    def remove_agent(self, agent_id: str):
        """Remove an agent from the orchestrator"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.stop()
            del self.agents[agent_id]

            self.logger.log_event(
                self.orchestrator_id,
                EventType.AGENT_COMMUNICATION,
                f"Agent {agent_id} removed from orchestrator",
                metadata={
                    "orchestrator_id": self.orchestrator_id,
                    "agent_id": agent_id
                }
            )

    def start_all_agents(self):
        """Start all registered agents"""
        started_count = 0
        for agent in self.agents.values():
            try:
                agent.start()
                started_count += 1
            except Exception as e:
                self.logger.log_event(
                    EventType.AGENT_ERROR,
                    f"Failed to start agent {agent.agent_id}",
                    {"error": str(e)}
                )

        self.logger.log_event(
            self.orchestrator_id,
            EventType.AGENT_START,
            f"Started {started_count}/{len(self.agents)} agents",
            metadata={
                "orchestrator_id": self.orchestrator_id,
                "started_count": started_count,
                "total_agents": len(self.agents)
            }
        )

        return started_count

    def stop_all_agents(self):
        """Stop all agents gracefully"""
        stopped_count = 0
        for agent in self.agents.values():
            try:
                agent.stop()
                stopped_count += 1
            except Exception as e:
                self.logger.log_event(
                    EventType.AGENT_ERROR,
                    f"Failed to stop agent {agent.agent_id}",
                    {"error": str(e)}
                )

        self.logger.log_event(
            self.orchestrator_id,
            EventType.AGENT_STOP,
            f"Stopped {stopped_count}/{len(self.agents)} agents",
            metadata={
                "orchestrator_id": self.orchestrator_id,
                "stopped_count": stopped_count
            }
        )

        return stopped_count

    def coordinate_task(self, coordination_id: str, task_assignments: Dict[str, tuple]) -> Dict[str, Any]:
        """
        Coordinate a complex task across multiple agents

        Args:
            coordination_id: Unique identifier for this coordination
            task_assignments: Dict mapping agent_id to (task_type, task_data) tuples
        """
        start_time = time.time()

        self.logger.log_event(
            self.orchestrator_id,
            EventType.TASK_START,
            f"Multi-agent coordination {coordination_id} started",
            metadata={
                "orchestrator_id": self.orchestrator_id,
                "coordination_id": coordination_id,
                "agent_assignments": list(task_assignments.keys()),
                "total_tasks": len(task_assignments)
            }
        )

        results = {}
        errors = {}

        # Execute tasks on assigned agents
        for agent_id, (task_type, task_data) in task_assignments.items():
            if agent_id not in self.agents:
                error_msg = f"Agent {agent_id} not found in orchestrator"
                errors[agent_id] = error_msg
                self.logger.log_event(
                    EventType.TASK_ERROR,
                    error_msg,
                    {"coordination_id": coordination_id}
                )
                continue

            try:
                agent = self.agents[agent_id]
                result = agent.execute_task(task_type, task_data)
                results[agent_id] = result

                if not result.get("success", False):
                    errors[agent_id] = result.get("error", "Task failed")

            except Exception as e:
                error_msg = str(e)
                errors[agent_id] = error_msg
                self.logger.log_event(
                    EventType.TASK_ERROR,
                    f"Error executing task on agent {agent_id}",
                    {
                        "coordination_id": coordination_id,
                        "agent_id": agent_id,
                        "error": error_msg
                    }
                )

        execution_time = time.time() - start_time
        success = len(errors) == 0

        # Record coordination history
        coordination_record = {
            "coordination_id": coordination_id,
            "start_time": start_time,
            "execution_time": execution_time,
            "success": success,
            "agents_involved": list(task_assignments.keys()),
            "successful_agents": [aid for aid in results.keys() if aid not in errors],
            "failed_agents": list(errors.keys()),
            "timestamp": datetime.now().isoformat()
        }

        self.coordination_history.append(coordination_record)

        # Keep only last 50 coordination records
        if len(self.coordination_history) > 50:
            self.coordination_history = self.coordination_history[-50:]

        # Log completion
        if success:
            self.logger.log_event(
                self.orchestrator_id,
                EventType.TASK_COMPLETE,
                f"Multi-agent coordination {coordination_id} completed successfully",
                metadata={
                    "coordination_id": coordination_id,
                    "execution_time": execution_time,
                    "agents_count": len(results)
                }
            )

            # Send success notification
            self._send_coordination_notification(coordination_id, True, execution_time, len(results))

        else:
            self.logger.log_event(
                EventType.TASK_ERROR,
                f"Multi-agent coordination {coordination_id} completed with errors",
                {
                    "coordination_id": coordination_id,
                    "execution_time": execution_time,
                    "errors": errors
                }
            )

            # Send error notification
            self._send_coordination_notification(coordination_id, False, execution_time, len(results), errors)

        return {
            "coordination_id": coordination_id,
            "success": success,
            "execution_time": execution_time,
            "results": results,
            "errors": errors,
            "summary": {
                "total_agents": len(task_assignments),
                "successful_agents": len(results) - len(errors),
                "failed_agents": len(errors)
            }
        }

    def _send_coordination_notification(self, coordination_id: str, success: bool, 
                                      execution_time: float, agent_count: int, 
                                      errors: Dict[str, str] = None):
        """Send notification about coordination completion"""
        try:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            message = f"{status} Multi-Agent Coordination: {coordination_id}\n"
            message += f"⏱️ Execution Time: {execution_time:.2f}s\n"
            message += f"🤖 Agents Involved: {agent_count}\n"

            if errors:
                message += f"❌ Errors: {len(errors)}\n"
                for agent_id, error in errors.items():
                    message += f"  • {agent_id}: {error}\n"

            # Send to all configured notification channels
            self.integration_manager.send_notification(message)

        except Exception as e:
            self.logger.log_event(
                self.orchestrator_id,
                EventType.TASK_ERROR,
                f"Failed to send coordination notification",
                metadata={"error": str(e)}
            )

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status"""
        agent_statuses = {}
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = agent.get_state_summary()

        return {
            "orchestrator_id": self.orchestrator_id,
            "total_agents": len(self.agents),
            "running_agents": sum(1 for a in self.agents.values() if a.running),
            "total_coordinations": len(self.coordination_history),
            "recent_coordinations": self.coordination_history[-5:],
            "agent_statuses": agent_statuses,
            "system_health": self.monitor.get_system_health()
        }

    def get_agent_performance_report(self) -> Dict[str, Any]:
        """Generate performance report for all agents"""
        report = {
            "orchestrator_id": self.orchestrator_id,
            "report_timestamp": datetime.now().isoformat(),
            "agents": {}
        }

        for agent_id, agent in self.agents.items():
            agent_report = {
                "agent_summary": agent.get_state_summary(),
                "performance_metrics": self.monitor.get_agent_dashboard(agent_id)
            }
            report["agents"][agent_id] = agent_report

        return report


# Example usage functions
def example_stateful_agent_with_logging():
    """Example: Stateful agent with comprehensive logging"""
    print("🚀 Starting Stateful Agent Example with Logging")

    # Configure logging
    logger = configure_logging(log_level=LogLevel.INFO)

    # Start monitoring
    monitor = get_monitor()
    monitor.start_monitoring()

    # Setup integrations (optional)
    integration_manager = get_integration_manager()
    # Uncomment to add Slack notifications:
    # slack = SlackConnector(webhook_url="YOUR_WEBHOOK_URL")
    # integration_manager.add_connector("slack", slack)

    # Create and start agent
    agent = StatefulAgent("data-processor-001", "DataProcessor", {"version": "1.0"})
    agent.start()

    try:
        # Execute various tasks to demonstrate state management
        print("\n📊 Executing data processing tasks...")

        # Task 1: Process some data
        result1 = agent.execute_task("data_processing", {
            "data": [1, 2, 3, 4, 5],
            "operation": "sum"
        })
        print(f"Task 1 Result: {result1}")

        # Task 2: Analyze trends
        result2 = agent.execute_task("analysis", {
            "type": "trend",
            "data": {"current_value": 15}
        })
        print(f"Task 2 Result: {result2}")

        # Task 3: Memory operations
        result3 = agent.execute_task("memory_operation", {
            "operation": "set",
            "key": "user_preference",
            "value": {"theme": "dark", "notifications": True}
        })
        print(f"Task 3 Result: {result3}")

        # Task 4: Query state
        result4 = agent.execute_task("state_query", {})
        print(f"Task 4 Result: {result4}")

        # Show agent state
        print(f"\n🔍 Agent State Summary:")
        print(json.dumps(agent.get_state_summary(), indent=2))

        # Show performance metrics
        print(f"\n📈 Performance Dashboard:")
        dashboard = monitor.get_agent_dashboard(agent.agent_id)
        print(json.dumps(dashboard, indent=2))

    finally:
        agent.stop()
        monitor.stop_monitoring()
        print("\n✅ Stateful agent example completed")


def example_multi_agent_coordination_with_logging():
    """Example: Multi-agent coordination with comprehensive logging"""
    print("🚀 Starting Multi-Agent Coordination Example with Logging")

    # Configure logging
    logger = configure_logging(log_level=LogLevel.INFO)

    # Start monitoring
    monitor = get_monitor()
    monitor.start_monitoring()

    # Create orchestrator
    orchestrator = MultiAgentOrchestrator("main-orchestrator")

    # Create specialized agents
    data_agent = StatefulAgent("data-agent", "DataProcessor")
    analysis_agent = StatefulAgent("analysis-agent", "DataAnalyzer") 
    report_agent = StatefulAgent("report-agent", "ReportGenerator")

    # Add agents to orchestrator
    orchestrator.add_agent(data_agent)
    orchestrator.add_agent(analysis_agent)
    orchestrator.add_agent(report_agent)

    try:
        # Start all agents
        started_count = orchestrator.start_all_agents()
        print(f"✅ Started {started_count} agents")

        # Wait a moment for agents to initialize
        time.sleep(2)

        # Coordinate a complex multi-agent task
        print("\n🤝 Coordinating multi-agent task...")

        task_assignments = {
            "data-agent": ("data_processing", {
                "data": [10, 20, 30, 40, 50],
                "operation": "average"
            }),
            "analysis-agent": ("analysis", {
                "type": "trend",
                "data": {"period": "daily", "metric": "sales"}
            }),
            "report-agent": ("memory_operation", {
                "operation": "set",
                "key": "report_config",
                "value": {"format": "pdf", "include_charts": True}
            })
        }

        coordination_result = orchestrator.coordinate_task(
            "daily_analysis_workflow",
            task_assignments
        )

        print(f"\n📋 Coordination Result:")
        print(json.dumps(coordination_result, indent=2))

        # Show orchestrator status
        print(f"\n🎛️ Orchestrator Status:")
        status = orchestrator.get_orchestrator_status()
        print(json.dumps(status, indent=2))

        # Generate performance report
        print(f"\n📊 Performance Report:")
        performance_report = orchestrator.get_agent_performance_report()
        print(json.dumps(performance_report, indent=2))

    finally:
        orchestrator.stop_all_agents()
        monitor.stop_monitoring()
        print("\n✅ Multi-agent coordination example completed")


def example_advanced_monitoring_and_alerts():
    """Example: Advanced monitoring with custom alerts"""
    print("🚀 Starting Advanced Monitoring Example")

    # Configure logging with JSON output
    logger = configure_logging(
        log_level=LogLevel.INFO,
        enable_json=True,
        enable_file=True
    )

    # Start monitoring with custom configuration
    monitor = get_monitor()
    monitor.start_monitoring()

    # Setup custom alerts
    monitor.add_alert_rule({
        "metric_name": "agent_task_failure_rate",
        "threshold": 0.5,  # 50% failure rate
        "condition": "greater_than",
        "duration_minutes": 2,
        "callback": lambda alert: print(f"🚨 ALERT: {alert}")
    })

    # Create agents with different behaviors
    reliable_agent = StatefulAgent("reliable-agent", "ReliableAgent")
    unreliable_agent = StatefulAgent("unreliable-agent", "UnreliableAgent")

    # Custom unreliable agent that fails sometimes
    class UnreliableAgent(StatefulAgent):
        def _custom_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
            import random
            if random.random() < 0.6:  # 60% chance of failure
                raise Exception("Simulated task failure")
            return {"message": "Task succeeded"}

    unreliable_agent.__class__ = UnreliableAgent

    try:
        reliable_agent.start()
        unreliable_agent.start()

        # Execute tasks to trigger monitoring
        print("\n📊 Executing tasks to demonstrate monitoring...")

        for i in range(10):
            # Reliable agent tasks
            reliable_agent.execute_task("data_processing", {
                "data": list(range(i, i+5)),
                "operation": "sum"
            })

            # Unreliable agent tasks (will trigger alerts)
            unreliable_agent.execute_task("custom_task", {"iteration": i})

            time.sleep(1)

        # Wait for monitoring to collect data
        time.sleep(5)

        # Show monitoring results
        print(f"\n📈 System Health:")
        health = monitor.get_system_health()
        print(json.dumps(health, indent=2))

        print(f"\n📊 Agent Dashboards:")
        for agent_id in [reliable_agent.agent_id, unreliable_agent.agent_id]:
            dashboard = monitor.get_agent_dashboard(agent_id)
            print(f"\n{agent_id}:")
            print(json.dumps(dashboard, indent=2))

    finally:
        reliable_agent.stop()
        unreliable_agent.stop()
        monitor.stop_monitoring()
        print("\n✅ Advanced monitoring example completed")


if __name__ == "__main__":
    print("BMasterAI Enhanced Examples")
    print("=" * 50)

    # Run examples
    example_stateful_agent_with_logging()
    print("\n" + "="*50 + "\n")

    example_multi_agent_coordination_with_logging()
    print("\n" + "="*50 + "\n")

    example_advanced_monitoring_and_alerts()

    print("\n🎉 All examples completed successfully!")
