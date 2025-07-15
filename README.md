# BMasterAI - Advanced Multi-Agent AI Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/travis-burmaster/bmasterai)

A comprehensive Python framework for building multi-agent AI systems with advanced logging, monitoring, and integrations. BMasterAI provides enterprise-ready features for developing, deploying, and managing AI agents at scale.

## 🚀 Features

### Core Framework
- **Multi-Agent Orchestration**: Coordinate multiple AI agents working together
- **Task Management**: Structured task execution with error handling and retries
- **LLM Integration**: Support for multiple language models (OpenAI, Anthropic, etc.)
- **YAML Configuration**: No-code setup for common workflows

### Advanced Monitoring & Logging
- **Comprehensive Logging**: Structured logging with JSON output and multiple levels
- **Real-time Monitoring**: System metrics, agent performance, and custom metrics
- **Performance Tracking**: Task duration, LLM usage, and resource consumption
- **Alert System**: Configurable alerts with multiple notification channels

### Enterprise Integrations
- **Slack Integration**: Real-time notifications and alerts
- **Email Notifications**: SMTP support for reports and alerts
- **Discord Integration**: Community and team notifications
- **Microsoft Teams**: Enterprise communication
- **Database Storage**: SQLite, MongoDB, and custom database connectors
- **Webhook Support**: Generic webhook integration for any service

### Developer Experience
- **Easy Installation**: Simple pip install with optional dependencies
- **Rich Examples**: Comprehensive examples and tutorials
- **Type Hints**: Full type annotation support
- **Testing Suite**: Built-in testing framework
- **Documentation**: Extensive documentation and API reference

## 📦 Installation

### Basic Installation
```bash
pip install bmasterai
```

### With All Integrations
```bash
pip install bmasterai[all]
```

### Development Installation
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
pip install -e .[dev]
```

## 🏃 Quick Start

### 1. Basic Agent Setup

```python
from bmasterai.logging import configure_logging, LogLevel
from bmasterai.monitoring import get_monitor
from bmasterai.integrations import get_integration_manager, SlackConnector

# Configure logging and monitoring
logger = configure_logging(log_level=LogLevel.INFO)
monitor = get_monitor()
monitor.start_monitoring()

# Setup integrations
integration_manager = get_integration_manager()
slack = SlackConnector(webhook_url="YOUR_SLACK_WEBHOOK")
integration_manager.add_connector("slack", slack)

# Create and run an agent
from bmasterai_examples import EnhancedAgent

agent = EnhancedAgent("agent-001", "DataProcessor")
agent.start()

# Execute tasks with full monitoring
result = agent.execute_task("data_analysis", {"dataset": "sales.csv"})
print(f"Task result: {result}")

# Get performance dashboard
dashboard = monitor.get_agent_dashboard("agent-001")
print(f"Agent performance: {dashboard}")

agent.stop()
```

### 2. Multi-Agent Coordination

```python
from bmasterai.examples import MultiAgentOrchestrator, EnhancedAgent

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

# Coordinate complex task across agents
task_assignments = {
    "data-agent": ("data_analysis", {"dataset": "sales_data.csv"}),
    "analysis-agent": ("trend_analysis", {"period": "monthly"}),
    "report-agent": ("generate_report", {"format": "pdf"})
}

results = orchestrator.coordinate_task("monthly_analysis", task_assignments)
print(f"Coordination results: {results}")
```

## 🖥️ Command Line Interface

BMasterAI includes a powerful CLI for project management, monitoring, and system administration.

### Installation & Setup

The CLI is automatically available after installation:

```bash
pip install bmasterai
bmasterai --help
```

### Available Commands

#### 1. Initialize New Project
Create a new BMasterAI project with proper structure and templates:

```bash
bmasterai init my-ai-project
```

This creates:
```
my-ai-project/
├── agents/my_agent.py      # Working agent template
├── config/config.yaml      # Configuration file
└── logs/                   # Log directory
```

The generated agent template includes:
- Correct import statements
- Proper logging and monitoring setup
- Task execution framework
- Error handling and metrics tracking

#### 2. System Status
Monitor your BMasterAI system in real-time:

```bash
bmasterai status
```

Output example:
```
🖥️  BMasterAI System Status
========================================
Timestamp: 2025-07-15T00:27:34.364134
Active Agents: 3
Total Agents: 5

📊 System Metrics:
  CPU Usage: 45.2% (avg)
  Memory Usage: 67.8% (avg)

🔗 Integrations:
  Active: 2
    ✅ slack
    ✅ email

🚨 Recent Alerts:
  ⚠️  cpu_percent: CPU usage above 80%
  ⚠️  agent_errors: High error rate detected
```

#### 3. Real-time Monitoring
Start continuous system monitoring:

```bash
bmasterai monitor
```

Features:
- Real-time system metrics display
- Live agent status updates
- Performance monitoring
- Press Ctrl+C to stop

Example output:
```
🔍 Starting BMasterAI monitoring...
✅ Monitoring started
📊 System metrics being collected every 30 seconds

💻 CPU: 45.1% | 🧠 Memory: 67.8% | 🤖 Agents: 3
```

#### 4. Test Integrations
Verify all configured integrations are working:

```bash
bmasterai test-integrations
```

Output example:
```
🧪 Testing integrations...
✅ slack: Connection successful
✅ email: SMTP connection verified
❌ discord: Webhook URL not configured
✅ database: SQLite connection active
```

#### 5. Configuration File Support
Use custom configuration files:

```bash
bmasterai --config /path/to/config.yaml status
bmasterai -c production.yaml monitor
```

### CLI Usage Examples

#### Quick Project Setup
```bash
# Create new project
bmasterai init customer-support-ai
cd customer-support-ai

# Edit configuration
nano config/config.yaml

# Customize the agent
nano agents/my_agent.py

# Run the agent
python agents/my_agent.py

# Monitor system
bmasterai status
```

#### Production Monitoring
```bash
# Check system health
bmasterai status

# Start monitoring daemon
bmasterai monitor &

# Test all integrations
bmasterai test-integrations

# Use production config
bmasterai --config production.yaml status
```

#### Development Workflow
```bash
# Initialize development project
bmasterai init dev-project

# Start monitoring in background
bmasterai monitor &

# Develop and test agents
python agents/my_agent.py

# Check status periodically
bmasterai status
```

### Generated Project Structure

When you run `bmasterai init`, you get a complete, working project:

**config/config.yaml:**
```yaml
# BMasterAI Configuration
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
```

**agents/my_agent.py:**
```python
from bmasterai.logging import get_logger, EventType, LogLevel
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

    def execute_task(self, task_name: str, task_data: dict = None):
        # Full implementation with logging, monitoring, and error handling
        # ... (complete working code)

if __name__ == "__main__":
    agent = MyAgent("my-agent", "MyCustomAgent")
    agent.start()
    result = agent.execute_task("custom_task", {"data": "example"})
    print(f"Result: {result}")
    agent.stop()
```

### CLI Benefits

- **🚀 Quick Start**: Get up and running in seconds
- **📊 Real-time Monitoring**: Live system status and metrics
- **🔧 Easy Configuration**: YAML-based configuration management
- **🧪 Integration Testing**: Verify all connections work
- **📁 Project Templates**: Working code from day one
- **🔍 System Visibility**: Comprehensive status reporting

### 3. Configuration-Driven Setup

Create a `config.yaml` file:

```yaml
logging:
  level: INFO
  enable_console: true
  enable_file: true

monitoring:
  collection_interval: 30

alerts:
  - metric: "cpu_percent"
    threshold: 80
    condition: "greater_than"
    duration_minutes: 5

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
```

## 📊 Monitoring & Analytics

BMasterAI provides comprehensive monitoring out of the box:

### System Metrics
- CPU and memory usage
- Disk space and network I/O
- Agent performance metrics
- Task execution times

### Custom Metrics
- LLM token usage and costs
- Task success/failure rates
- Agent communication patterns
- Custom business metrics

### Alerting
- Configurable thresholds
- Multiple notification channels
- Alert escalation
- Custom alert callbacks

### Dashboards
```python
# Get real-time system health
health = monitor.get_system_health()

# Get agent-specific dashboard
dashboard = monitor.get_agent_dashboard("agent-001")

# Generate daily reports
from bmasterai_examples import generate_daily_report
report = generate_daily_report()
```

## 🔌 Integrations

### Slack Integration
```python
from bmasterai_integrations import SlackConnector

slack = SlackConnector(webhook_url="YOUR_WEBHOOK_URL")
slack.send_message("Agent task completed successfully!")
slack.send_alert(alert_data)
```

### Email Integration
```python
from bmasterai_integrations import EmailConnector

email = EmailConnector(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password"
)
email.send_report(["admin@company.com"], report_data)
```

### Database Integration
```python
from bmasterai_integrations import DatabaseConnector

db = DatabaseConnector(db_type="sqlite", connection_string="agents.db")
db.store_agent_data(agent_id, name, status, metadata)
history = db.get_agent_history(agent_id)
```

## 🏗️ Architecture

BMasterAI is built with a modular architecture:

```
bmasterai/
├── logging/          # Structured logging system
├── monitoring/       # Metrics collection and alerting
├── integrations/     # External service connectors
├── agents/          # Agent base classes and utilities
├── orchestration/   # Multi-agent coordination
└── examples/        # Usage examples and templates
```

### Key Components

1. **Logging System**: Structured, multi-level logging with JSON output
2. **Monitoring Engine**: Real-time metrics collection and analysis
3. **Integration Manager**: Unified interface for external services
4. **Agent Framework**: Base classes for building AI agents
5. **Orchestrator**: Multi-agent coordination and workflow management

## 🔧 Configuration

BMasterAI supports multiple configuration methods:

### Environment Variables
```bash
export BMASTERAI_LOG_LEVEL=INFO
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
export EMAIL_USERNAME=your-email@gmail.com
```

### YAML Configuration
```yaml
# config.yaml
logging:
  level: INFO
  enable_json: true

agents:
  default_timeout: 300
  max_retries: 3
```

### Programmatic Configuration
```python
from bmasterai.logging import configure_logging, LogLevel

logger = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True
)
```

## 📈 Performance & Scalability

BMasterAI is designed for production use:

- **Async Support**: Non-blocking operations for high throughput
- **Resource Management**: Automatic cleanup and resource monitoring
- **Horizontal Scaling**: Multi-process and distributed agent support
- **Caching**: Built-in caching for improved performance
- **Load Balancing**: Intelligent task distribution

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=bmasterai
```

## 📚 Examples

Check out the `examples/` directory for comprehensive examples:

- **Basic Agent**: Simple agent with logging and monitoring
- **Multi-Agent System**: Coordinated agents working together
- **Integration Examples**: Using Slack, email, and database integrations
- **Custom Metrics**: Creating and tracking custom metrics
- **Alert Configuration**: Setting up monitoring alerts
- **Production Deployment**: Enterprise deployment examples

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
pip install -e .[dev]
pre-commit install
```

### Running Tests
```bash
pytest
black .
flake8
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/travis-burmaster/bmasterai/wiki)
- **Issues**: [GitHub Issues](https://github.com/travis-burmaster/bmasterai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/travis-burmaster/bmasterai/discussions)
- **Email**: travis@burmaster.com

## 🗺️ Roadmap

### Version 0.3.0 (Coming Soon)
- [ ] Web dashboard for monitoring
- [ ] Advanced multi-agent communication protocols
- [ ] Plugin system for custom integrations
- [ ] Kubernetes deployment support

### Version 0.4.0
- [ ] Visual workflow builder
- [ ] Advanced scheduling and cron support
- [ ] Machine learning model integration
- [ ] Advanced security features

### Version 1.0.0
- [ ] Production-ready enterprise features
- [ ] Advanced analytics and reporting
- [ ] Multi-cloud deployment support
- [ ] Enterprise security and compliance

## 🌟 Why BMasterAI?

BMasterAI bridges the gap between simple AI scripts and enterprise-grade AI systems:

- **Developer Friendly**: Easy to get started, powerful when you need it
- **Production Ready**: Built-in monitoring, logging, and error handling
- **Extensible**: Plugin architecture and custom integrations
- **Community Driven**: Open source with active community support
- **Enterprise Features**: Security, compliance, and scalability built-in

---

**Made with ❤️ by the BMasterAI community**

*Star ⭐ this repo if you find it useful!*
