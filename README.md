# BMasterAI - Advanced Multi-Agent AI Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/travis-burmaster/bmasterai)
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
from bmasterai.examples import EnhancedAgent

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

**Ready to build production-scale AI systems? 🚀**

[**→ Start with Kubernetes**](README-k8s.md) | [**→ Local Development**](#-installation) | [**→ View Examples**](examples/)

**Made with ❤️ by the BMasterAI community**

*Star ⭐ this repo if you find it useful!*
