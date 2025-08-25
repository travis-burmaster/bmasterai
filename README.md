# BMasterAI - Advanced Multi-Agent AI Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.1-green.svg)](https://github.com/travis-burmaster/bmasterai)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-brightgreen.svg)](https://kubernetes.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

A comprehensive Python framework for building multi-agent AI systems with advanced logging, monitoring, and integrations. BMasterAI provides enterprise-ready features for developing, deploying, and managing AI agents at scale.

## ⚡ **NEW: Kubernetes Deployment Support for AWS EKS**

🚀 **BMasterAI now includes full production-ready Kubernetes deployment support!**

Deploy BMasterAI on Amazon EKS with enterprise features:
- **🐳 Production Docker images** with security best practices
- **⚙️ Complete Kubernetes manifests** for EKS deployment  
- **📊 Helm charts** for easy installation and management
- **🔧 Auto-scaling** with Horizontal Pod Autoscaler
- **📈 Monitoring & observability** with Prometheus and Grafana
- **🔒 Enterprise security** with RBAC, Pod Security Standards, and IAM integration

[**→ Quick Start with Kubernetes**](README-k8s.md) | [**→ Complete Deployment Guide**](docs/kubernetes-deployment.md)

---

## 📚 **NEW: Comprehensive Learning Resources**

🎓 **Learn BMasterAI with hands-on tutorials and real-world examples!**

Our new lessons directory provides step-by-step tutorials covering:
- **🔧 GitHub MCP Integration** with Streamlit interfaces
- **📊 Repository Analysis** using AI agents and MCP protocols
- **🚀 Feature Request Workflows** with automated analysis
- **🤖 Multi-Agent Orchestration** for complex tasks
- **📋 PDF Documentation** for offline learning

[**→ Browse All Lessons**](lessons/) | [**→ Start with GitHub MCP Tutorial**](lessons/lesson-01-github-mcp-streamlit/)

---

## 📊 **NEW: Kubernetes LLM Cost Analysis Telemetry**

💰 **Monitor and optimize your LLM costs in Kubernetes environments!**

Our comprehensive telemetry system provides real-time insights into LLM usage and costs:
- **Real-time LLM cost tracking** by model and namespace
- **Token usage monitoring** (input/output tokens)
- **Performance metrics and error rates**
- **Distributed tracing** for LLM workflows
- **Custom Kubernetes resources** for LLM run tracking
- **Grafana dashboards** for visualization

[**→ View Telemetry Examples**](examples/kubernetes-telemetry/) | [**→ Learn Telemetry Setup**](examples/kubernetes-telemetry/README.md)

---

## 🧠 **NEW: Advanced LLM Reasoning Logging**

🔍 **Capture and analyze how your AI agents think and make decisions!**

BMasterAI now includes comprehensive LLM reasoning logging that captures:
- **🤔 Thinking Steps**: Record each step of the reasoning process
- **⚖️ Decision Points**: Log decision options, choices, and reasoning
- **🔗 Reasoning Chains**: Track complete thought processes from start to finish
- **📊 Confidence Scores**: Monitor agent confidence throughout reasoning
- **📈 Reasoning Metrics**: Analyze reasoning patterns and performance
- **📝 Export Formats**: JSON, Markdown, HTML, and CSV exports

[**→ View Reasoning Example**](examples/reasoning_logging_example.py) | [**→ Configuration Guide**](config/reasoning_config.yaml)

### Quick Usage

**Context Manager Approach:**
```python
from bmasterai import ReasoningSession

with ReasoningSession("agent-001", "Analyze sentiment", "gpt-4") as session:
    session.think("First, I'll examine the word choice...")
    session.decide("Classification", ["positive", "negative"], "positive", 
                  "More positive words detected")
    session.conclude("Text has positive sentiment")
```

**Chain of Thought:**
```python
from bmasterai import ChainOfThought

cot = ChainOfThought("agent-001", "Solve math problem", "gpt-4")
result = cot.step("Identify the problem type...") \
           .step("Apply relevant formula...") \
           .conclude("The answer is 42")
```

**Quick Logging:**
```python
from bmasterai import log_reasoning

log_reasoning("agent-001", "Analysis task", 
             ["Step 1: Analyze", "Step 2: Decide"], 
             "Final conclusion")
```

### Reasoning Logs Location
- **Main logs**: `logs/bmasterai.jsonl` 
- **Reasoning logs**: `logs/reasoning/bmasterai_reasoning.jsonl`
- **Exported reports**: Various formats available

---

## 🚀 Features

### Core Framework
- **Multi-Agent Orchestration**: Coordinate multiple AI agents working together
- **Task Management**: Structured task execution with error handling and retries
- **LLM Integration**: Support for multiple language models (OpenAI, Anthropic, etc.)
- **YAML Configuration**: No-code setup for common workflows

### Advanced Monitoring & Logging
- **LLM Reasoning Logging**: Capture thinking steps, decision points, and reasoning chains
- **Comprehensive Logging**: Structured logging with JSON output and multiple levels  
- **Real-time Monitoring**: System metrics, agent performance, and reasoning metrics
- **Performance Tracking**: Task duration, LLM usage, reasoning complexity, and resource consumption
- **Alert System**: Configurable alerts with multiple notification channels
- **Export & Analysis**: Reasoning logs in multiple formats (JSON, Markdown, HTML, CSV)

### Enterprise Integrations
- **Slack Integration**: Real-time notifications and alerts
- **Email Notifications**: SMTP support for reports and alerts
- **Discord Integration**: Community and team notifications
- **Microsoft Teams**: Enterprise communication
- **Database Storage**: SQLite, MongoDB, and custom database connectors
- **Webhook Support**: Generic webhook integration for any service

### 🚢 Production Deployment
- **Kubernetes Native**: Complete EKS deployment with Helm charts
- **Docker Ready**: Production-optimized container images
- **Auto-scaling**: Horizontal Pod Autoscaler with custom metrics
- **Monitoring Stack**: Prometheus, Grafana, and CloudWatch integration
- **Security First**: RBAC, Pod Security Standards, and secrets management
- **CI/CD Pipeline**: GitHub Actions for automated deployment

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

### Kubernetes Deployment
```bash
# Quick start with automated scripts
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
./eks/setup-scripts/01-create-cluster.sh
./eks/setup-scripts/02-deploy-bmasterai.sh

# Or using Helm
helm install bmasterai ./helm/bmasterai --namespace bmasterai --create-namespace
```

### Development Installation
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
pip install -e .[dev]
```

## 🏃 Quick Start

### 1. Basic Agent Setup with Reasoning Logging

```python
from bmasterai import (
    configure_logging, get_monitor, get_integration_manager,
    ReasoningSession, LogLevel
)

# Configure logging with reasoning capture enabled
logger = configure_logging(
    log_level=LogLevel.INFO,
    enable_reasoning_logs=True
)
monitor = get_monitor()
monitor.start_monitoring()

# Example: Agent with reasoning logging
def analyze_sentiment(text):
    with ReasoningSession("agent-001", "Sentiment Analysis", "gpt-4") as session:
        # Step 1: Analyze the text
        session.think(f"Analyzing text: '{text}'. Looking for emotional indicators.")
        
        # Step 2: Make decision
        if "good" in text.lower() or "great" in text.lower():
            sentiment = "positive"
            reasoning = "Found positive words like 'good' or 'great'"
        else:
            sentiment = "neutral" 
            reasoning = "No clear positive or negative indicators"
        
        session.decide(
            "Sentiment classification", 
            ["positive", "negative", "neutral"], 
            sentiment, 
            reasoning
        )
        
        # Step 3: Conclude
        result = f"Text sentiment: {sentiment}"
        session.conclude(result)
        return result

# Run analysis with automatic reasoning logging
result = analyze_sentiment("This product is really good!")
print(result)

# Export reasoning logs
reasoning_report = logger.export_reasoning_logs(format="markdown")
print("Reasoning process captured and logged!")
```

### 2. Kubernetes Deployment

```bash
# Deploy on EKS with monitoring
./eks/setup-scripts/01-create-cluster.sh    # Create EKS cluster
./eks/setup-scripts/02-deploy-bmasterai.sh  # Deploy BMasterAI
./eks/setup-scripts/03-install-monitoring.sh # Install Prometheus/Grafana

# Check deployment status
kubectl get pods -n bmasterai
kubectl get svc -n bmasterai

# Access monitoring dashboard
kubectl port-forward svc/prometheus-operator-grafana 3000:80 -n monitoring
```

### 3. Multi-Agent Coordination

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

### 3. Advanced Reasoning Logging Patterns

```python
from bmasterai import ChainOfThought, with_reasoning_logging, log_reasoning

# Pattern 1: Chain of Thought for complex reasoning
def solve_math_problem(problem):
    cot = ChainOfThought("math-agent", f"Solve: {problem}", "gpt-4")
    
    return cot.step("Identify the type of mathematical problem") \
             .step("Break down the problem into smaller parts") \
             .step("Apply relevant mathematical principles") \
             .step("Check the solution for accuracy") \
             .conclude("Final answer with verification")

# Pattern 2: Decorator-based reasoning logging
@with_reasoning_logging("Process customer query", "claude-3")
def handle_customer_query(agent_id, query, reasoning_session=None):
    if reasoning_session:
        reasoning_session.think("Analyzing customer intent...")
        reasoning_session.decide("Response type", ["info", "action", "escalate"], 
                                "info", "Query seeks information")
        reasoning_session.conclude("Providing informational response")
    
    return "Customer query processed"

# Pattern 3: Quick reasoning logging for simple cases  
def quick_analysis(data):
    steps = [
        "Received data for analysis",
        "Checking data quality and format", 
        "Applying analysis algorithms",
        "Validating results"
    ]
    
    conclusion = "Analysis completed successfully"
    session_id = log_reasoning("analysis-agent", "Data Analysis", 
                              steps, conclusion, "analysis-model")
    return f"Analysis done (logged as {session_id})"

# Export and analyze reasoning logs
logger = get_logger()

# Get logs for specific agent
agent_reasoning = logger.export_reasoning_logs(
    agent_id="math-agent", 
    output_format="markdown"
)

# Get logs for specific session
session_details = logger.get_reasoning_session("session_id_here")

# Export all reasoning logs as JSON for analysis
all_reasoning = logger.export_reasoning_logs(output_format="json")
```

### 4. Reasoning Log Analysis

```python
# Analyze reasoning patterns and performance
monitor = get_monitor()

# Get reasoning metrics
reasoning_stats = {
    'avg_steps': monitor.metrics_collector.get_metric_stats('reasoning_session_steps'),
    'avg_duration': monitor.metrics_collector.get_metric_stats('reasoning_session_duration_ms'),
    'decision_frequency': monitor.metrics_collector.get_metric_stats('reasoning_decision_points')
}

print("Reasoning Performance:")
for metric, stats in reasoning_stats.items():
    if stats:
        print(f"  {metric}: avg={stats['avg']:.1f}, max={stats['max']}")

# Export reasoning logs for external analysis tools
reasoning_data = logger.export_reasoning_logs(output_format="csv")
# Can be imported into pandas, Excel, or BI tools for deeper analysis
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

#### 2. System Status
Monitor your BMasterAI system in real-time:

```bash
bmasterai status
```

#### 3. Real-time Monitoring
Start continuous system monitoring:

```bash
bmasterai monitor
```

#### 4. Test Integrations
Verify all configured integrations are working:

```bash
bmasterai test-integrations
```

## 🚢 Kubernetes Features

### Enterprise-Ready Deployment
- **High Availability**: Multi-replica deployment with pod anti-affinity
- **Auto-scaling**: HPA with CPU/memory metrics and custom metrics support
- **Rolling Updates**: Zero-downtime deployments
- **Health Checks**: Comprehensive liveness, readiness, and startup probes

### Security & Compliance
- **RBAC**: Minimal required permissions with service accounts
- **Pod Security**: Non-root execution, read-only filesystem, dropped capabilities
- **Network Policies**: Traffic isolation and egress control
- **Secrets Management**: Encrypted storage of API keys and credentials

### Monitoring & Observability
- **Prometheus Metrics**: System and application metrics collection
- **Grafana Dashboards**: Pre-built dashboards for BMasterAI monitoring
- **CloudWatch Integration**: AWS native logging and metrics
- **Distributed Tracing**: Request flow tracking across services

### Cost Optimization
- **Resource Right-sizing**: Optimized CPU/memory requests and limits
- **Spot Instances**: Support for cost-effective compute
- **Auto-scaling**: Dynamic scaling based on workload
- **Storage Optimization**: GP3 volumes with encryption

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

### Kubernetes Monitoring Commands

```bash
# Check deployment status
kubectl get pods -n bmasterai
kubectl get hpa -n bmasterai

# View logs
kubectl logs -f deployment/bmasterai-agent -n bmasterai

# Scale manually
kubectl scale deployment bmasterai-agent --replicas=5 -n bmasterai

# Port forward for direct access
kubectl port-forward svc/bmasterai-service 8080:80 -n bmasterai

# Access Grafana dashboard
kubectl port-forward svc/prometheus-operator-grafana 3000:80 -n monitoring
```

## 🔌 Integrations

### Slack Integration
```python
from bmasterai.integrations import SlackConnector

slack = SlackConnector(webhook_url="YOUR_WEBHOOK_URL")
slack.send_message("Agent task completed successfully!")
slack.send_alert(alert_data)
```

### Email Integration
```python
from bmasterai.integrations import EmailConnector

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
from bmasterai.integrations import DatabaseConnector

db = DatabaseConnector(db_type="sqlite", connection_string="agents.db")
db.store_agent_data(agent_id, name, status, metadata)
history = db.get_agent_history(agent_id)
```

## 🔄 Model Context Protocol (MCP)

BMasterAI now includes support for the Model Context Protocol (MCP), enabling seamless integration with external tools and services through standardized interfaces.

### What is MCP?

Model Context Protocol is a standardized way for AI models to interact with external tools and services. It allows BMasterAI agents to:

- Access external data sources and APIs
- Execute specialized functions
- Integrate with domain-specific tools
- Extend agent capabilities without code changes

### MCP Configuration

Configure MCP servers in your project:

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Using MCP in Your Agents

```python
from bmasterai.mcp import MCPClient

# Initialize MCP client
mcp_client = MCPClient()

# Register available MCP servers
mcp_client.register_server("aws-docs")

# Use MCP tools in your agent
response = agent.execute_with_tools(
    "Find information about EC2 instance types",
    tools=mcp_client.get_tools("aws-docs")
)

# Access specific MCP tool
result = mcp_client.execute_tool(
    server_name="aws-docs",
    tool_name="search_documentation",
    parameters={"query": "EKS cluster autoscaling"}
)
```

### Available MCP Servers

BMasterAI supports various MCP servers out of the box:

- **AWS Documentation**: Access AWS service documentation
- **Code Analysis**: Code parsing, analysis, and transformation
- **Data Processing**: Data extraction, transformation, and analysis
- **Web Search**: Internet search capabilities
- **Custom Tools**: Build and integrate your own MCP servers

### Creating Custom MCP Servers

Extend BMasterAI with your own MCP servers:

```python
from bmasterai.mcp import MCPServer, Tool

class CustomMCPServer(MCPServer):
    def __init__(self):
        super().__init__("custom-tools")
        self.register_tool(
            Tool(
                name="custom_function",
                description="Performs a custom operation",
                parameters={
                    "input": {"type": "string", "description": "Input data"}
                },
                handler=self.custom_function
            )
        )
    
    def custom_function(self, input):
        # Custom implementation
        return {"result": process_data(input)}

# Register your custom server
mcp_client.register_custom_server(CustomMCPServer())
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
├── k8s/             # Kubernetes manifests
├── helm/            # Helm chart for deployment
├── eks/             # EKS-specific configuration
├── lessons/         # Comprehensive tutorials and guides
└── examples/        # Usage examples and templates
```

### Key Components

1. **Logging System**: Structured, multi-level logging with JSON output
2. **Monitoring Engine**: Real-time metrics collection and analysis
3. **Integration Manager**: Unified interface for external services
4. **Agent Framework**: Base classes for building AI agents
5. **Orchestrator**: Multi-agent coordination and workflow management
6. **Kubernetes Operator**: Native Kubernetes deployment and management

## 📈 Performance & Scalability

BMasterAI is designed for production use:

- **Async Support**: Non-blocking operations for high throughput
- **Resource Management**: Automatic cleanup and resource monitoring
- **Horizontal Scaling**: Multi-process and distributed agent support
- **Kubernetes Native**: Auto-scaling with HPA and cluster autoscaler
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

# Test Kubernetes deployment
kubectl apply --dry-run=client -f k8s/
helm template bmasterai ./helm/bmasterai | kubectl apply --dry-run=client -f -
```

## 📚 Examples

Check out the `examples/` directory for comprehensive examples:

### 🤖 Core Framework Examples
- **[Basic Agent](examples/basic_usage.py)**: Simple agent with logging and monitoring
- **[Enhanced Examples](examples/enhanced_examples.py)**: Advanced multi-agent system with full BMasterAI integration
- **[Multi-Agent System](examples/enhanced_examples.py)**: Coordinated agents working together
- **[Integration Examples](examples/enhanced_examples.py)**: Using Slack, email, and database integrations

### 🧠 LLM Reasoning Examples
- **[Reasoning Logging Demo](examples/reasoning_logging_example.py)**: Complete demonstration of LLM reasoning capture
- **[Chain of Thought](examples/reasoning_logging_example.py#analyze_with_chain_of_thought)**: Step-by-step reasoning patterns
- **[Decision Logging](examples/reasoning_logging_example.py#log_decision_point)**: Capture decision points and alternatives
- **[Reasoning Export](examples/reasoning_logging_example.py#export_reasoning_logs)**: Export reasoning logs in multiple formats

### 🧠 RAG (Retrieval-Augmented Generation) Examples
- **[Qdrant Cloud RAG](examples/minimal-rag/bmasterai_rag_qdrant_cloud.py)**: Advanced RAG system with Qdrant Cloud vector database
- **[Interactive RAG UI](examples/minimal-rag/gradio_qdrant_rag.py)**: Gradio web interface for RAG system with chat, document management, and monitoring

### 🌐 Web Interface Examples  
- **[Gradio Anthropic Chat](examples/gradio-anthropic/gradio-app-bmasterai.py)**: Interactive chat interface with Anthropic Claude models
- **[RAG Web Interface](examples/minimal-rag/gradio_qdrant_rag.py)**: Full-featured RAG system with web UI

### 🚢 Deployment Examples
- **[Docker Deployment](Dockerfile)**: Production-ready container image
- **[Kubernetes Manifests](k8s/)**: Complete Kubernetes deployment configuration
- **[Helm Chart](helm/bmasterai/)**: Helm chart for easy deployment and management
- **[EKS Setup Scripts](eks/setup-scripts/)**: Automated EKS cluster creation and deployment

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
- **Kubernetes Guide**: [Complete Deployment Guide](docs/kubernetes-deployment.md)
- **Issues**: [GitHub Issues](https://github.com/travis-burmaster/bmasterai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/travis-burmaster/bmasterai/discussions)
- **Email**: travis@burmaster.com

## 🗺️ Roadmap

### Version 0.3.0 (Coming Soon)
- [x] **Kubernetes deployment support** ✅ **COMPLETED**
- [x] **Comprehensive learning resources** ✅ **COMPLETED**
- [ ] Web dashboard for monitoring
- [ ] Advanced multi-agent communication protocols
- [ ] Plugin system for custom integrations

### Version 0.4.0
- [ ] Visual workflow builder
- [ ] Advanced scheduling and cron support
- [ ] Machine learning model integration
- [ ] Multi-cloud deployment (GKE, AKS)

### Version 1.0.0
- [ ] Production-ready enterprise features
- [ ] Advanced analytics and reporting
- [ ] Multi-cloud deployment support
- [ ] Enterprise security and compliance

## 🌟 Why BMasterAI?

BMasterAI bridges the gap between simple AI scripts and enterprise-grade AI systems:

- **Developer Friendly**: Easy to get started, powerful when you need it
- **Production Ready**: Built-in monitoring, logging, and error handling
- **Cloud Native**: Kubernetes-ready with enterprise security features
- **Extensible**: Plugin architecture and custom integrations
- **Community Driven**: Open source with active community support
- **Enterprise Features**: Security, compliance, and scalability built-in

## 🚀 Get Started

Choose your deployment method:

### Local Development
```bash
pip install bmasterai
bmasterai init my-project

# Try reasoning logging example
cd my-project
python -c "
from bmasterai import ReasoningSession, configure_logging
configure_logging(enable_reasoning_logs=True)

with ReasoningSession('demo-agent', 'Hello World', 'demo-model') as session:
    session.think('This is my first reasoning step!')
    session.conclude('Reasoning logging is working!')

print('✅ Reasoning logs saved to logs/reasoning/')
"
```

### Kubernetes Production
```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
./eks/setup-scripts/01-create-cluster.sh
./eks/setup-scripts/02-deploy-bmasterai.sh
```

### Helm Deployment
```bash
helm repo add bmasterai https://travis-burmaster.github.io/bmasterai
helm install bmasterai bmasterai/bmasterai
```

---

**Ready to build production-scale AI systems with full reasoning visibility? 🚀**

[**→ Start with Kubernetes**](README-k8s.md) | [**→ Learn with Tutorials**](lessons/) | [**→ Try Reasoning Logging**](examples/reasoning_logging_example.py) | [**→ Local Development**](#-installation) | [**→ View Examples**](examples/)

**Made with ❤️ by the BMasterAI community**

*Star ⭐ this repo if you find it useful!*