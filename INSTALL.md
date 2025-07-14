# BMasterAI v0.2.0 Complete Installation Instructions

## Overview

This package contains the complete BMasterAI v0.2.0 framework with:
- ✅ **Stateful Agents** with memory and task history
- ✅ **Multi-Agent Orchestration** with coordination capabilities  
- ✅ **Advanced Logging** with structured JSON output
- ✅ **Real-time Monitoring** with metrics and alerts
- ✅ **Enterprise Integrations** (Slack, Email, Discord, Teams)
- ✅ **Command Line Interface** for project management
- ✅ **Comprehensive Examples** and test suite

## Quick Installation

1. **Extract the zip file** to your desired location
2. **Navigate to the directory**:
   ```bash
   cd bmasterai
   ```
3. **Install the package**:
   ```bash
   pip install -e .
   ```

## Development Installation

For development with all dependencies:
```bash
pip install -e .[dev,integrations]
```

## Verify Installation

Test the installation:
```bash
bmasterai status
```

## Run Examples

### Quick Start - Run All Examples
```bash
cd examples
python run_examples.py
```

### Individual Examples

1. **Stateful Agent with Logging**:
   ```bash
   python -c "from examples.enhanced_examples import example_stateful_agent_with_logging; example_stateful_agent_with_logging()"
   ```

2. **Multi-Agent Coordination**:
   ```bash
   python -c "from examples.enhanced_examples import example_multi_agent_coordination_with_logging; example_multi_agent_coordination_with_logging()"
   ```

3. **Advanced Monitoring**:
   ```bash
   python -c "from examples.enhanced_examples import example_advanced_monitoring_and_alerts; example_advanced_monitoring_and_alerts()"
   ```

## Initialize a New Project

Create a new BMasterAI project:
```bash
bmasterai init my-ai-project
cd my-ai-project
```

This creates:
```
my-ai-project/
├── agents/my_agent.py     # Custom agent template
├── config/config.yaml     # Configuration file
└── logs/                  # Log directory
```

## Configuration

1. **Copy the configuration template**:
   ```bash
   cp config/config.yaml ./config.yaml
   ```

2. **Edit configuration** with your settings

3. **Set environment variables** for sensitive data:
   ```bash
   export SLACK_WEBHOOK_URL="your-slack-webhook"
   export EMAIL_USERNAME="your-email@domain.com"
   export EMAIL_PASSWORD="your-app-password"
   ```

## Key Features Demonstrated

### 1. Stateful Agents
- **Memory Management**: Agents maintain state across tasks
- **Task History**: Complete history of executed tasks
- **State Persistence**: Agent state survives across operations
- **Heartbeat Monitoring**: Continuous health monitoring

### 2. Multi-Agent Coordination
- **Orchestrated Workflows**: Coordinate complex tasks across agents
- **Task Assignment**: Distribute work to specialized agents
- **Result Aggregation**: Collect and combine results
- **Error Handling**: Graceful handling of agent failures

### 3. Advanced Logging
- **Structured Events**: JSON-formatted log events
- **Event Types**: Categorized logging (AGENT_STARTED, TASK_COMPLETED, etc.)
- **Thread-Safe**: Safe for multi-threaded agent operations
- **Multiple Outputs**: Console, file, and JSON logging

### 4. Real-time Monitoring
- **System Metrics**: CPU, memory, disk usage
- **Agent Metrics**: Task performance, success rates
- **Custom Alerts**: Configurable thresholds and notifications
- **Performance Dashboards**: Real-time agent performance data

### 5. Enterprise Integrations
- **Slack Notifications**: Real-time alerts and status updates
- **Email Reports**: Automated reporting via email
- **Database Storage**: Persistent storage of agent data
- **Webhook Support**: Generic webhook integration

## File Structure

```
bmasterai/
├── src/bmasterai/              # Main package
│   ├── __init__.py
│   ├── cli.py                 # Command line interface
│   ├── logging.py             # Advanced logging system
│   ├── monitoring.py          # Monitoring and metrics
│   └── integrations.py        # External integrations
├── examples/                   # Usage examples
│   ├── enhanced_examples.py   # Stateful & multi-agent examples
│   ├── basic_usage.py         # Basic usage patterns
│   └── run_examples.py        # Example runner script
├── tests/                      # Test suite
│   ├── test_enhanced_functionality.py
│   └── __init__.py
├── config/                     # Configuration templates
│   └── config.yaml
├── docs/                       # Documentation
├── requirements.txt            # Dependencies
├── pyproject.toml             # Modern Python packaging
├── setup.py                   # Legacy packaging
└── README.md                  # Main documentation
```

## Running Tests

```bash
# Install test dependencies
pip install -e .[dev]

# Run all tests
pytest

# Run with coverage
pytest --cov=bmasterai

# Run specific test file
pytest tests/test_enhanced_functionality.py -v
```

## CLI Commands

```bash
# Initialize new project
bmasterai init my-project

# Show system status
bmasterai status

# Start monitoring mode
bmasterai monitor

# Test integrations
bmasterai test-integrations
```

## Example Usage Patterns

### Basic Stateful Agent
```python
from examples.enhanced_examples import StatefulAgent

agent = StatefulAgent("my-agent", "MyAgent")
agent.start()

# Execute tasks - state persists between calls
result1 = agent.execute_task("data_processing", {"data": [1,2,3], "operation": "sum"})
result2 = agent.execute_task("memory_operation", {"operation": "list"})

agent.stop()
```

### Multi-Agent Coordination
```python
from examples.enhanced_examples import StatefulAgent, MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()
agent1 = StatefulAgent("agent-1", "DataProcessor")
agent2 = StatefulAgent("agent-2", "Analyzer")

orchestrator.add_agent(agent1)
orchestrator.add_agent(agent2)
orchestrator.start_all_agents()

# Coordinate complex workflow
result = orchestrator.coordinate_task("workflow-1", {
    "agent-1": ("data_processing", {"data": [1,2,3]}),
    "agent-2": ("analysis", {"type": "trend"})
})

orchestrator.stop_all_agents()
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to install with `pip install -e .`
2. **Permission Errors**: Check file permissions for log directory
3. **Port Conflicts**: Ensure monitoring ports are available
4. **Memory Issues**: Monitor system resources during heavy usage

### Debug Mode

Enable debug logging:
```python
from bmasterai.logging import configure_logging, LogLevel
configure_logging(log_level=LogLevel.DEBUG)
```

### Log Files

Check log files for detailed information:
- `bmasterai.log` - Main application log
- `bmasterai.jsonl` - Structured JSON events

## Support

- **GitHub**: https://github.com/travis-burmaster/bmasterai
- **Issues**: https://github.com/travis-burmaster/bmasterai/issues
- **Email**: travis@burmaster.com

## Next Steps

1. **Explore Examples**: Run the example scripts to understand capabilities
2. **Create Custom Agents**: Extend StatefulAgent for your use cases
3. **Configure Integrations**: Set up Slack, email, or other notifications
4. **Build Workflows**: Use MultiAgentOrchestrator for complex tasks
5. **Monitor Performance**: Use the monitoring system to optimize agents

Happy building with BMasterAI! 🚀
