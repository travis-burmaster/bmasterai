# Quick Start Guide

Get up and running with BMasterAI in minutes! This guide will walk you through installation, basic setup, and your first AI agent.

## 🚀 Installation

### Basic Installation
```bash
pip install bmasterai
```

### With All Features
```bash
pip install bmasterai[all]
```

### Development Installation
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
pip install -e .[dev]
```

## 🎯 Your First Agent

### 1. Basic Agent Example

Create a file called `my_first_agent.py`:

```python
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor
import time

# Configure logging
configure_logging(log_level=LogLevel.INFO)

# Start monitoring
monitor = get_monitor()
monitor.start_monitoring()

class MyFirstAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = get_logger()
        self.monitor = monitor
        
        # Log agent creation
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            f"Agent {self.name} initialized",
            metadata={"name": self.name}
        )
    
    def execute_task(self, task_name: str, task_data: dict = None):
        start_time = time.time()
        
        try:
            # Log task start
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_START,
                f"Starting task: {task_name}",
                metadata={"task_data": task_data or {}}
            )
            
            # Simulate task execution
            time.sleep(1)  # Your actual task logic here
            result = {"status": "completed", "task": task_name}
            
            # Calculate duration and track performance
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.track_task_duration(self.agent_id, task_name, duration_ms)
            
            # Log task completion
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_COMPLETE,
                f"Completed task: {task_name}",
                duration_ms=duration_ms,
                metadata={"result": result}
            )
            
            return result
            
        except Exception as e:
            # Log error
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Task failed: {task_name} - {str(e)}",
                level=LogLevel.ERROR
            )
            
            self.monitor.track_error(self.agent_id, "task_execution")
            return {"status": "failed", "error": str(e)}

# Create and run your agent
if __name__ == "__main__":
    agent = MyFirstAgent("my-agent-001", "MyFirstAgent")
    
    # Execute some tasks
    result1 = agent.execute_task("data_processing", {"input": "sample_data"})
    result2 = agent.execute_task("analysis", {"type": "basic"})
    
    print(f"Task 1 result: {result1}")
    print(f"Task 2 result: {result2}")
    
    # Get performance dashboard
    dashboard = monitor.get_agent_dashboard("my-agent-001")
    print(f"Agent performance: {dashboard}")
```

### 2. Run Your Agent

```bash
python my_first_agent.py
```

You should see output like:
```
2025-01-15 10:30:15,123 - bmasterai - INFO - [my-agent-001] agent_start: Agent MyFirstAgent initialized
2025-01-15 10:30:15,124 - bmasterai - INFO - [my-agent-001] task_start: Starting task: data_processing
2025-01-15 10:30:16,125 - bmasterai - INFO - [my-agent-001] task_complete: Completed task: data_processing
Task 1 result: {'status': 'completed', 'task': 'data_processing'}
```

## 🖥️ Using the CLI

BMasterAI includes a powerful command-line interface:

### Initialize a New Project
```bash
bmasterai init my-ai-project
cd my-ai-project
```

### Check System Status
```bash
bmasterai status
```

### Start Monitoring
```bash
bmasterai monitor
```

## 🧠 Try RAG (Retrieval-Augmented Generation)

### 1. Install RAG Dependencies
```bash
pip install -r examples/minimal-rag/requirements_qdrant.txt
```

### 2. Set Up Environment Variables
```bash
export QDRANT_URL="https://your-cluster.qdrant.io"
export QDRANT_API_KEY="your-qdrant-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Test Connections
```bash
python examples/minimal-rag/test_qdrant_connection.py
```

### 4. Launch RAG Web Interface
```bash
python examples/minimal-rag/gradio_qdrant_rag.py
```

Open your browser to `http://localhost:7860` to access the interactive RAG interface!

## 🌐 Web Interface Example

Try the Gradio chat interface with Anthropic Claude:

### 1. Install Dependencies
```bash
pip install gradio anthropic
```

### 2. Set API Key
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. Launch Chat Interface
```bash
python examples/gradio-anthropic/gradio-app-bmasterai.py
```

## 📊 What You Get Out of the Box

With BMasterAI, every agent automatically includes:

### ✅ Comprehensive Logging
- Structured JSON logs
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Event-based logging with metadata
- File and console output

### ✅ Real-time Monitoring
- System metrics (CPU, memory, disk)
- Agent performance tracking
- Task duration monitoring
- Error rate tracking
- Custom metrics support

### ✅ Production Features
- Error handling and recovery
- Performance optimization
- Resource management
- Alert system
- Integration support

## 🎯 Next Steps

Now that you have BMasterAI running, explore these areas:

### 🤖 Build More Advanced Agents
- **[Agent Development Guide](agents.md)** - Learn advanced agent patterns
- **[Multi-Agent Systems](multi-agent.md)** - Coordinate multiple agents
- **[Task Management](tasks.md)** - Advanced task execution patterns

### 🧠 Explore RAG Capabilities
- **[RAG Overview](rag/overview.md)** - Understanding RAG with BMasterAI
- **[Qdrant Cloud Setup](rag/qdrant-cloud.md)** - Vector database integration
- **[RAG Examples](rag/examples.md)** - Complete RAG tutorials

### 🔌 Add Integrations
- **[Slack Integration](integrations/slack.md)** - Get notifications in Slack
- **[Email Integration](integrations/email.md)** - Send reports via email
- **[Database Integration](integrations/database.md)** - Store data persistently

### 📊 Advanced Monitoring
- **[Custom Metrics](monitoring/metrics.md)** - Track business-specific metrics
- **[Alerting](monitoring/alerts.md)** - Set up intelligent alerts
- **[Dashboards](web/dashboards.md)** - Create monitoring dashboards

## 🆘 Need Help?

- **[Troubleshooting Guide](advanced/troubleshooting.md)** - Common issues and solutions
- **[GitHub Issues](https://github.com/travis-burmaster/bmasterai/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/travis-burmaster/bmasterai/discussions)** - Ask questions
- **Email**: travis@burmaster.com

## 📚 Learn More

- **[Configuration Guide](configuration.md)** - Detailed configuration options
- **[API Reference](api/core.md)** - Complete API documentation
- **[Examples](examples/basic.md)** - More example code and tutorials

---

*Ready to build something amazing? Let's go! 🚀*