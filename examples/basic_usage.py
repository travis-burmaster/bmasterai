
# BMasterAI Enhanced Framework - Usage Examples

## 1. Basic Setup with Logging and Monitoring

```python
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager, SlackConnector, EmailConnector

# Configure logging
logger = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True
)

# Start monitoring
monitor = get_monitor()
monitor.start_monitoring()

# Setup integrations
integration_manager = get_integration_manager()

# Add Slack integration
slack = SlackConnector(webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK")
integration_manager.add_connector("slack", slack)

# Add email integration
email = EmailConnector(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password"
)
integration_manager.add_connector("email", email)
```

## 2. Enhanced Agent with Full Monitoring

```python
import time
import uuid
from datetime import datetime
from bmasterai.logging import get_logger, EventType, LogLevel
from bmasterai.monitoring import get_monitor

class EnhancedAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.status = "initialized"

        # Log agent creation
        self.logger.log_event(
            agent_id=self.agent_id,
            event_type=EventType.AGENT_START,
            message=f"Agent {self.name} initialized",
            metadata={"name": self.name}
        )

    def start(self):
        self.status = "running"
        self.monitor.track_agent_start(self.agent_id)

        self.logger.log_event(
            agent_id=self.agent_id,
            event_type=EventType.AGENT_START,
            message=f"Agent {self.name} started",
            level=LogLevel.INFO
        )

    def execute_task(self, task_name: str, task_data: dict = None):
        task_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Log task start
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message=f"Starting task: {task_name}",
                metadata={"task_id": task_id, "task_data": task_data or {}}
            )

            # Simulate task execution
            self._perform_task(task_name, task_data)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Track performance
            self.monitor.track_task_duration(self.agent_id, task_name, duration_ms)

            # Log task completion
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_COMPLETE,
                message=f"Completed task: {task_name}",
                metadata={"task_id": task_id, "duration_ms": duration_ms},
                duration_ms=duration_ms
            )

            return {"success": True, "task_id": task_id, "duration_ms": duration_ms}

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Track error
            self.monitor.track_error(self.agent_id, "task_execution")

            # Log error
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Task failed: {task_name} - {str(e)}",
                level=LogLevel.ERROR,
                metadata={"task_id": task_id, "error": str(e), "duration_ms": duration_ms},
                duration_ms=duration_ms
            )

            return {"success": False, "error": str(e), "task_id": task_id}

    def _perform_task(self, task_name: str, task_data: dict):
        # Simulate different types of tasks
        if task_name == "data_analysis":
            time.sleep(2)  # Simulate processing time
            return {"result": "Analysis complete", "records_processed": 1000}
        elif task_name == "send_email":
            time.sleep(0.5)
            return {"result": "Email sent", "recipients": task_data.get("recipients", [])}
        elif task_name == "generate_report":
            time.sleep(3)
            return {"result": "Report generated", "pages": 10}
        else:
            time.sleep(1)
            return {"result": f"Task {task_name} completed"}

    def call_llm(self, model: str, prompt: str, max_tokens: int = 100):
        start_time = time.time()

        try:
            # Log LLM call
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.LLM_CALL,
                message=f"Calling LLM: {model}",
                metadata={"model": model, "prompt_length": len(prompt), "max_tokens": max_tokens}
            )

            # Simulate LLM call
            time.sleep(1.5)  # Simulate API call time
            response = f"Response to: {prompt[:50]}..."
            tokens_used = min(len(response), max_tokens)

            duration_ms = (time.time() - start_time) * 1000

            # Track LLM metrics
            self.monitor.track_llm_call(self.agent_id, model, tokens_used, duration_ms)

            return {"response": response, "tokens_used": tokens_used}

        except Exception as e:
            self.monitor.track_error(self.agent_id, "llm_call")
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"LLM call failed: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"model": model, "error": str(e)}
            )
            raise

    def stop(self):
        self.status = "stopped"
        self.monitor.track_agent_stop(self.agent_id)

        self.logger.log_event(
            agent_id=self.agent_id,
            event_type=EventType.AGENT_STOP,
            message=f"Agent {self.name} stopped",
            level=LogLevel.INFO
        )

# Example usage
if __name__ == "__main__":
    # Create and start agent
    agent = EnhancedAgent("agent-001", "DataProcessor")
    agent.start()

    # Execute various tasks
    agent.execute_task("data_analysis", {"dataset": "customer_data.csv"})
    agent.execute_task("generate_report", {"type": "monthly"})
    agent.call_llm("gpt-4", "Analyze the following data...")

    # Get agent dashboard
    dashboard = get_monitor().get_agent_dashboard("agent-001")
    print("Agent Dashboard:", dashboard)

    # Stop agent
    agent.stop()
```

## 3. Multi-Agent System with Coordination

```python
from bmasterai.logging import get_logger, EventType
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager
import threading
import time

class MultiAgentOrchestrator:
    def __init__(self):
        self.agents = {}
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.integration_manager = get_integration_manager()

    def add_agent(self, agent: EnhancedAgent):
        self.agents[agent.agent_id] = agent

        self.logger.log_event(
            agent_id="orchestrator",
            event_type=EventType.AGENT_START,
            message=f"Added agent {agent.name} to orchestrator",
            metadata={"agent_id": agent.agent_id, "agent_name": agent.name}
        )

    def coordinate_task(self, task_name: str, agent_assignments: dict):
        """Coordinate a task across multiple agents"""

        self.logger.log_event(
            agent_id="orchestrator",
            event_type=EventType.TASK_START,
            message=f"Starting coordinated task: {task_name}",
            metadata={"assignments": agent_assignments}
        )

        # Start tasks in parallel
        threads = []
        results = {}

        def run_agent_task(agent_id, subtask, task_data):
            agent = self.agents[agent_id]
            results[agent_id] = agent.execute_task(subtask, task_data)

        for agent_id, (subtask, task_data) in agent_assignments.items():
            thread = threading.Thread(
                target=run_agent_task,
                args=(agent_id, subtask, task_data)
            )
            threads.append(thread)
            thread.start()

        # Wait for all tasks to complete
        for thread in threads:
            thread.join()

        # Log coordination completion
        self.logger.log_event(
            agent_id="orchestrator",
            event_type=EventType.TASK_COMPLETE,
            message=f"Coordinated task completed: {task_name}",
            metadata={"results": results}
        )

        # Send notification if any task failed
        failed_tasks = [aid for aid, result in results.items() if not result.get("success")]
        if failed_tasks:
            alert_data = {
                "metric_name": "coordinated_task_failure",
                "message": f"Task {task_name} had failures in agents: {failed_tasks}",
                "timestamp": datetime.now().isoformat(),
                "failed_agents": failed_tasks
            }
            self.integration_manager.send_alert_to_all(alert_data)

        return results

    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            "orchestrator": {
                "active_agents": len([a for a in self.agents.values() if a.status == "running"]),
                "total_agents": len(self.agents),
                "agent_details": {aid: {"name": a.name, "status": a.status} for aid, a in self.agents.items()}
            },
            "system_health": self.monitor.get_system_health(),
            "integration_status": self.integration_manager.get_status()
        }
        return status

# Example multi-agent workflow
if __name__ == "__main__":
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()

    # Create specialized agents
    data_agent = EnhancedAgent("data-agent", "DataProcessor")
    analysis_agent = EnhancedAgent("analysis-agent", "DataAnalyzer")
    report_agent = EnhancedAgent("report-agent", "ReportGenerator")

    # Add agents to orchestrator
    orchestrator.add_agent(data_agent)
    orchestrator.add_agent(analysis_agent)
    orchestrator.add_agent(report_agent)

    # Start all agents
    for agent in orchestrator.agents.values():
        agent.start()

    # Coordinate a complex task
    task_assignments = {
        "data-agent": ("data_analysis", {"dataset": "sales_data.csv"}),
        "analysis-agent": ("data_analysis", {"type": "trend_analysis"}),
        "report-agent": ("generate_report", {"format": "pdf", "sections": ["summary", "trends"]})
    }

    results = orchestrator.coordinate_task("monthly_sales_analysis", task_assignments)
    print("Coordination Results:", results)

    # Get system status
    status = orchestrator.get_system_status()
    print("System Status:", status)

    # Stop all agents
    for agent in orchestrator.agents.values():
        agent.stop()
```

## 4. Alert Configuration and Monitoring

```python
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager

# Setup monitoring with alerts
monitor = get_monitor()
monitor.start_monitoring()

# Configure system alerts
monitor.metrics_collector.add_alert_rule(
    metric_name="cpu_percent",
    threshold=80.0,
    condition="greater_than",
    duration_minutes=5,
    callback=lambda alert: get_integration_manager().send_alert_to_all(alert)
)

monitor.metrics_collector.add_alert_rule(
    metric_name="memory_percent",
    threshold=90.0,
    condition="greater_than",
    duration_minutes=3,
    callback=lambda alert: get_integration_manager().send_alert_to_all(alert)
)

# Configure custom agent alerts
monitor.metrics_collector.add_alert_rule(
    metric_name="agent_errors",
    threshold=5.0,
    condition="greater_than",
    duration_minutes=10,
    callback=lambda alert: get_integration_manager().send_alert_to_all(alert)
)

print("Monitoring and alerts configured successfully!")
```

## 5. Configuration File Example (config.yaml)

```yaml
# BMasterAI Configuration
logging:
  level: INFO
  enable_console: true
  enable_file: true
  enable_json: true
  log_file: "bmasterai.log"
  json_log_file: "bmasterai.jsonl"

monitoring:
  collection_interval: 30
  enable_system_metrics: true
  enable_custom_metrics: true

alerts:
  - metric: "cpu_percent"
    threshold: 80
    condition: "greater_than"
    duration_minutes: 5
  - metric: "memory_percent"
    threshold: 90
    condition: "greater_than"
    duration_minutes: 3
  - metric: "agent_errors"
    threshold: 5
    condition: "greater_than"
    duration_minutes: 10

integrations:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"

  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "${EMAIL_USERNAME}"
    password: "${EMAIL_PASSWORD}"
    use_tls: true

  discord:
    enabled: false
    webhook_url: "${DISCORD_WEBHOOK_URL}"

  database:
    enabled: true
    type: "sqlite"
    connection_string: "bmasterai.db"

agents:
  default_timeout: 300
  max_retries: 3
  enable_monitoring: true
  enable_logging: true
```

## 6. Dashboard and Reporting

```python
import json
from datetime import datetime, timedelta
from bmasterai.logging import get_logger
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager

def generate_daily_report():
    """Generate a comprehensive daily report"""

    monitor = get_monitor()
    logger = get_logger()
    integration_manager = get_integration_manager()

    # Get system health
    system_health = monitor.get_system_health()

    # Get recent events
    recent_events = logger.get_events(limit=100)

    # Generate report data
    report_data = {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "system_health": system_health,
        "event_summary": {
            "total_events": len(recent_events),
            "error_events": len([e for e in recent_events if e.level.value in ["ERROR", "CRITICAL"]]),
            "agent_starts": len([e for e in recent_events if e.event_type.value == "agent_start"]),
            "tasks_completed": len([e for e in recent_events if e.event_type.value == "task_complete"])
        },
        "integration_status": integration_manager.get_status()
    }

    # Send report via email
    email_connector = integration_manager.get_connector("email")
    if email_connector:
        email_connector.send_report(
            to_emails=["admin@company.com"],
            report_data=report_data
        )

    # Send summary to Slack
    slack_connector = integration_manager.get_connector("slack")
    if slack_connector:
        summary_message = f"""
📊 **Daily BMasterAI Report - {report_data['report_date']}**

🖥️ **System Health:**
- Active Agents: {system_health.get('active_agents', 0)}
- CPU Usage: {system_health.get('system_metrics', {}).get('cpu', {}).get('avg', 'N/A')}%
- Memory Usage: {system_health.get('system_metrics', {}).get('memory', {}).get('avg', 'N/A')}%

📈 **Activity Summary:**
- Total Events: {report_data['event_summary']['total_events']}
- Errors: {report_data['event_summary']['error_events']}
- Tasks Completed: {report_data['event_summary']['tasks_completed']}

🔗 **Integrations:** {len(integration_manager.active_integrations)} active
"""
        slack_connector.send_message(summary_message, channel="#bmasterai-reports")

    return report_data

# Schedule daily reports (you can use cron or a scheduler like APScheduler)
if __name__ == "__main__":
    report = generate_daily_report()
    print("Daily report generated:", json.dumps(report, indent=2))
```
