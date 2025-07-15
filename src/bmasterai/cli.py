#!/usr/bin/env python3
"""
BMasterAI Command Line Interface
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any

from bmasterai.logging import configure_logging, get_logger, LogLevel
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        print("PyYAML is required for YAML configuration files")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)


def init_command(args):
    """Initialize a new BMasterAI project"""
    project_dir = Path(args.name)
    project_dir.mkdir(exist_ok=True)

    # Create basic structure
    (project_dir / "agents").mkdir(exist_ok=True)
    (project_dir / "config").mkdir(exist_ok=True)
    (project_dir / "logs").mkdir(exist_ok=True)

    # Create basic config file
    config_content = '''# BMasterAI Configuration
logging:
  level: INFO
  enable_console: true
  enable_file: true
  enable_json: true

monitoring:
  collection_interval: 30

agents:
  default_timeout: 300
  max_retries: 3

integrations:
  slack:
    enabled: false
    webhook_url: "${SLACK_WEBHOOK_URL}"
'''

    with open(project_dir / "config" / "config.yaml", "w") as f:
        f.write(config_content)

    # Create basic agent template
    agent_template = '''from bmasterai.logging import get_logger, EventType, LogLevel
from bmasterai.monitoring import get_monitor
import time
import uuid

class MyAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.status = "initialized"

        # Log agent creation
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Agent {self.name} initialized",
            metadata={"name": self.name}
        )

    def start(self):
        self.status = "running"
        self.monitor.track_agent_start(self.agent_id)

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Agent {self.name} started",
            level=LogLevel.INFO
        )

    def execute_task(self, task_name: str, task_data: dict = None):
        task_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Log task start
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Starting task: {task_name}",
                metadata={"task_id": task_id, "task_data": task_data or {}}
            )

            # Your custom task logic here
            result = self.custom_task(task_data or {})

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Track performance
            self.monitor.track_task_duration(self.agent_id, task_name, duration_ms)

            # Log task completion
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Completed task: {task_name}",
                metadata={"task_id": task_id, "duration_ms": duration_ms, "result": result},
                duration_ms=duration_ms
            )

            return {"success": True, "task_id": task_id, "result": result}

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Track error
            self.monitor.track_error(self.agent_id, "task_execution")

            # Log error
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Task failed: {task_name} - {str(e)}",
                level=LogLevel.ERROR,
                metadata={"task_id": task_id, "error": str(e)},
                duration_ms=duration_ms
            )

            return {"success": False, "error": str(e), "task_id": task_id}

    def custom_task(self, task_data: dict):
        """Implement your custom task logic here"""
        # Simulate some work
        time.sleep(1)
        return {"message": "Task completed successfully", "data": task_data}

    def stop(self):
        self.status = "stopped"
        self.monitor.track_agent_stop(self.agent_id)

        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_STOP,
            f"Agent {self.name} stopped",
            level=LogLevel.INFO
        )

if __name__ == "__main__":
    agent = MyAgent("my-agent", "MyCustomAgent")
    agent.start()

    result = agent.execute_task("custom_task", {"data": "example"})
    print(f"Result: {result}")

    agent.stop()
'''

    with open(project_dir / "agents" / "my_agent.py", "w") as f:
        f.write(agent_template)

    print(f"✅ Initialized BMasterAI project in {project_dir}")
    print(f"📁 Project structure:")
    print(f"   {project_dir}/")
    print(f"   ├── agents/my_agent.py")
    print(f"   ├── config/config.yaml")
    print(f"   └── logs/")
    print(f"\n🚀 Next steps:")
    print(f"   1. cd {project_dir}")
    print(f"   2. Edit config/config.yaml")
    print(f"   3. Customize agents/my_agent.py")
    print(f"   4. Run: python agents/my_agent.py")


def status_command(args):
    """Show system status"""
    monitor = get_monitor()
    integration_manager = get_integration_manager()

    # Get system health
    health = monitor.get_system_health()

    print("🖥️  BMasterAI System Status")
    print("=" * 40)
    print(f"Timestamp: {health['timestamp']}")
    print(f"Active Agents: {health['active_agents']}")
    print(f"Total Agents: {health['total_agents']}")

    print("\n📊 System Metrics:")
    cpu = health['system_metrics']['cpu']
    memory = health['system_metrics']['memory']
    print(f"  CPU Usage: {cpu.get('avg', 'N/A')}% (avg)")
    print(f"  Memory Usage: {memory.get('avg', 'N/A')}% (avg)")

    print("\n🔗 Integrations:")
    integration_status = integration_manager.get_status()
    print(f"  Active: {len(integration_status['active_integrations'])}")
    for name in integration_status['active_integrations']:
        print(f"    ✅ {name}")

    print("\n🚨 Recent Alerts:")
    alerts = health['recent_alerts']
    if alerts:
        for alert in alerts[:5]:  # Show last 5 alerts
            print(f"  ⚠️  {alert['metric_name']}: {alert['message']}")
    else:
        print("  No recent alerts")


def monitor_command(args):
    """Start monitoring mode"""
    print("🔍 Starting BMasterAI monitoring...")

    monitor = get_monitor()
    monitor.start_monitoring()

    print("✅ Monitoring started")
    print("📊 System metrics being collected every 30 seconds")
    print("🔗 Check logs/ directory for detailed logs")
    print("\nPress Ctrl+C to stop monitoring")

    try:
        import time
        while True:
            time.sleep(10)
            health = monitor.get_system_health()
            cpu = health['system_metrics']['cpu'].get('latest', 0)
            memory = health['system_metrics']['memory'].get('latest', 0)
            print(f"\r💻 CPU: {cpu:.1f}% | 🧠 Memory: {memory:.1f}% | 🤖 Agents: {health['active_agents']}", end="")
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped")
        monitor.stop_monitoring()


def test_integrations_command(args):
    """Test all configured integrations"""
    integration_manager = get_integration_manager()

    print("🧪 Testing integrations...")
    results = integration_manager.test_all_connections()

    for name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {name}: {result.get('message', result.get('error', 'Unknown'))}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="BMasterAI - Advanced Multi-Agent AI Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Configuration file path (default: config.yaml)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new BMasterAI project")
    init_parser.add_argument("name", help="Project name")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    # Monitor command
    subparsers.add_parser("monitor", help="Start monitoring mode")

    # Test integrations command
    subparsers.add_parser("test-integrations", help="Test all configured integrations")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Load configuration if it exists
    if Path(args.config).exists():
        config = load_config(args.config)

        # Configure logging
        log_config = config.get('logging', {})
        configure_logging(
            log_level=LogLevel[log_config.get('level', 'INFO')],
            enable_console=log_config.get('enable_console', True),
            enable_file=log_config.get('enable_file', True),
            enable_json=log_config.get('enable_json', True)
        )

    # Execute command
    if args.command == "init":
        init_command(args)
    elif args.command == "status":
        status_command(args)
    elif args.command == "monitor":
        monitor_command(args)
    elif args.command == "test-integrations":
        test_integrations_command(args)


if __name__ == "__main__":
    main()
