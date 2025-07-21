
# 🤖 MCP GitHub Analyzer

A powerful Streamlit application that provides automated GitHub repository analysis and improvement suggestions using AI-powered agents, Model Context Protocol (MCP) integration, and comprehensive monitoring with BMasterAI.

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Setup Instructions](#-setup-instructions)
- [Usage Guide](#-usage-guide)
- [Architecture Documentation](#-architecture-documentation)
- [Features Documentation](#-features-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🎯 Project Overview

The MCP GitHub Analyzer is an intelligent application designed to analyze GitHub repositories and provide actionable improvement suggestions. It leverages a multi-agent architecture to perform comprehensive code analysis, security audits, and automatically create pull requests with suggested improvements.

### What It Does

- **Repository Analysis**: Performs deep analysis of code quality, structure, documentation, and security
- **AI-Powered Suggestions**: Uses Anthropic's Claude models to generate intelligent improvement recommendations
- **Automated PR Creation**: Creates pull requests with implementable suggestions automatically
- **Real-Time Monitoring**: Tracks application performance and agent activities with BMasterAI integration
- **MCP Integration**: Utilizes Model Context Protocol for advanced Git operations

### Key Benefits

- ✅ **Automated Code Review**: Get instant feedback on repository quality
- ✅ **Security Analysis**: Identify potential security vulnerabilities
- ✅ **Time Saving**: Automated PR creation for common improvements
- ✅ **Comprehensive Monitoring**: Full observability with BMasterAI logging
- ✅ **Extensible Architecture**: Agent-based design for easy customization

## 🚀 Key Features

### Repository Analysis
- **Code Quality Assessment**: Analyzes code structure, documentation, and best practices
- **Security Scanning**: Identifies potential security vulnerabilities and risks
- **Documentation Review**: Evaluates README files, comments, and project documentation
- **Dependency Analysis**: Reviews project dependencies and suggests updates

### AI-Powered Suggestions
- **Intelligent Recommendations**: AI-generated suggestions for code improvements
- **Priority Classification**: Suggestions categorized by priority (High, Medium, Low)
- **Category Filtering**: Organized by type (Security, Documentation, Performance, etc.)
- **Implementation Guidance**: Detailed steps for manual suggestions

### Automated Improvements
- **Smart PR Creation**: Automatically implements certain types of improvements
- **Branch Management**: Creates feature branches with descriptive names
- **Change Documentation**: Comprehensive commit messages and PR descriptions
- **Review-Ready PRs**: Properly formatted pull requests ready for team review

### Monitoring & Observability
- **Real-Time Metrics**: Live monitoring of application performance
- **Agent Tracking**: Detailed logging of all agent activities
- **Error Monitoring**: Comprehensive error tracking and alerting
- **Performance Analytics**: Response times, success rates, and usage statistics

## 🛠 Technology Stack

### Core Technologies
- **Python 3.11+**: Primary programming language
- **Streamlit**: Web application framework
- **Anthropic API**: AI/LLM capabilities using Claude models
- **GitHub API**: Repository operations and management
- **BMasterAI**: Logging and monitoring framework

### Key Libraries
- **asyncio/aiohttp**: Asynchronous operations
- **PyGithub**: GitHub API integration
- **Plotly**: Data visualization and dashboards
- **Pandas**: Data manipulation and analysis
- **PyYAML**: Configuration management
- **psutil**: System monitoring

### External Integrations
- **Model Context Protocol (MCP)**: Advanced Git operations
- **GitHub API**: Repository access and PR management
- **Anthropic Claude**: AI-powered analysis and suggestions

## 📦 Setup Instructions

### Prerequisites

1. **Python 3.11 or higher**
2. **Git** installed on your system
3. **GitHub Personal Access Token** with appropriate permissions
4. **Anthropic API Key** for Claude access
5. **MCP Server** (optional, for enhanced Git operations)

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd mcp-github-streamlit
   ```

2. **Navigate to Application Directory**
   ```bash
  ls
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   
   Create a `.env` file in the app directory:
   ```bash
   # Required
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GITHUB_TOKEN=your_github_token_here
   
   # Optional
   MCP_SERVER_HOST=localhost
   MCP_SERVER_PORT=8080
   LOG_LEVEL=INFO
   ENVIRONMENT=development
   ```

5. **Configure Application**
   
   Edit `config.yaml` to customize settings:
   ```yaml
   logging:
     level: INFO
     enable_console: true
     enable_file: true
   
   integrations:
     anthropic:
       enabled: true
       timeout_seconds: 30
     github:
       enabled: true
       rate_limit_per_hour: 5000
   ```

6. **Create Logs Directory**
   ```bash
   mkdir -p logs
   ```

### Environment Variables Setup

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key for Claude access | - |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token | - |
| `MCP_SERVER_HOST` | ❌ | MCP server hostname | localhost |
| `MCP_SERVER_PORT` | ❌ | MCP server port | 8080 |
| `LOG_LEVEL` | ❌ | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `ENVIRONMENT` | ❌ | Environment name | development |

### GitHub Token Permissions

Your GitHub token needs the following permissions:
- `repo` (Full control of private repositories)
- `read:org` (Read org and team membership)
- `workflow` (Update GitHub Action workflows)

## 🎮 Usage Guide

### Starting the Application

1. **Navigate to App Directory**
   ```bash
   cd /examples/mcp-github-streamlit
   ```

2. **Run the Application**
   ```bash
   streamlit run app.py
   ```

3. **Access the Interface**
   Open your browser to `http://localhost:8501`

### Step-by-Step Analysis

#### 1. Repository Input
- Enter the GitHub repository URL
- Select analysis type (Quick, Standard, Comprehensive)
- Choose whether to create pull requests automatically
- Configure analysis filters (optional)

#### 2. Analysis Execution
- The application will display real-time progress
- Multiple agents work together to analyze the repository
- View live status updates and metrics

#### 3. Results Review
- **Analysis Results**: Code quality, security scores, and detailed findings
- **Suggestions Tab**: AI-generated improvement recommendations
- **Pull Request Tab**: Automated PRs created (if enabled)

#### 4. Take Action
- Review suggested improvements
- Merge automatically created pull requests
- Implement manual suggestions using provided guidance

### Navigation Overview

- **🔍 Repository Analysis**: Main analysis interface
- **📊 Monitoring Dashboard**: Real-time metrics and system status
- **📋 Analysis History**: Previous analysis results and trends
- **⚙️ Settings**: Application configuration and preferences

### Example Workflow

```
1. Enter repository URL: https://github.com/username/repository
2. Select "Comprehensive" analysis
3. Enable "Create Pull Request" option
4. Click "Start Analysis"
5. Monitor progress in real-time
6. Review results and suggestions
7. Check created pull request
8. Implement manual recommendations
```

## 🏗 Architecture Documentation

### Agent-Based Architecture

The application uses a multi-agent architecture coordinated by the `WorkflowCoordinator`:

```
WorkflowCoordinator
├── GitHubAnalyzerAgent (Repository analysis)
├── PRCreatorAgent (Pull request creation)
└── Integration Clients
    ├── GitHubClient (GitHub API operations)
    ├── MCPClient (Git operations via MCP)
    └── LLMClient (AI analysis with Anthropic)
```

### Core Components

#### 1. Workflow Coordinator (`agents/coordinator.py`)
- Orchestrates the entire analysis workflow
- Manages agent communication and data flow
- Handles error recovery and monitoring
- Generates comprehensive workflow summaries

#### 2. GitHub Analyzer Agent (`agents/github_analyzer.py`)
- Performs repository analysis using multiple techniques
- Integrates with GitHub API and MCP for data collection
- Uses LLM for intelligent code analysis
- Generates structured analysis results

#### 3. PR Creator Agent (`agents/pr_creator.py`)
- Creates improvement pull requests automatically
- Implements specific types of suggestions
- Manages branch creation and PR formatting
- Handles Git operations through MCP integration

### BMasterAI Integration

The application is fully integrated with BMasterAI for comprehensive observability:

#### Logging Framework (`utils/bmasterai_logging.py`)
- **Structured Logging**: JSON-formatted logs with metadata
- **Event Types**: Categorized events (agent_start, task_complete, errors, etc.)
- **Agent Tracking**: Complete lifecycle tracking of all agents
- **LLM Call Logging**: Detailed tracking of AI interactions

#### Monitoring System (`utils/bmasterai_monitoring.py`)
- **Real-Time Metrics**: System performance, agent status, error rates
- **Custom Dashboards**: Live visualization of application health
- **Alerting**: Configurable alerts for critical issues
- **Performance Analytics**: Response times, throughput, success rates

### MCP Server Integration

Model Context Protocol integration provides advanced Git capabilities:

- **Repository Operations**: Clone, fetch, branch management
- **File Analysis**: Content extraction and structure analysis
- **Change Management**: Diff generation and commit operations
- **Security**: Isolated Git operations with proper error handling

### Data Flow

```
1. User Input → Streamlit UI
2. UI → WorkflowCoordinator
3. Coordinator → GitHubAnalyzerAgent
4. Analyzer → GitHub API + MCP + LLM
5. Results → PRCreatorAgent (if enabled)
6. PR Creator → GitHub API + MCP
7. Final Results → UI Display
8. All Operations → BMasterAI Logging/Monitoring
```

## 🎯 Features Documentation

### Repository Analysis Features

#### Code Quality Assessment
- **Structure Analysis**: File organization, naming conventions, project structure
- **Documentation Quality**: README completeness, code comments, API documentation
- **Best Practices**: Coding standards, design patterns, maintainability metrics
- **Dependency Management**: Package versions, security vulnerabilities, updates needed

#### Security Analysis
- **Vulnerability Scanning**: Known security issues in dependencies
- **Code Pattern Analysis**: Potential security anti-patterns
- **Configuration Review**: Security-related configuration files
- **Secret Detection**: Hardcoded secrets and sensitive information

#### Performance Analysis
- **Code Efficiency**: Performance bottlenecks and optimization opportunities
- **Resource Usage**: Memory and CPU optimization suggestions
- **Scalability**: Architecture scalability recommendations

### AI-Powered Suggestions

#### Suggestion Categories
- **Security**: Security improvements and vulnerability fixes
- **Documentation**: Documentation enhancements and additions
- **Performance**: Code optimization and efficiency improvements
- **Maintainability**: Code organization and structure improvements
- **Testing**: Test coverage and quality improvements

#### Priority Levels
- **High**: Critical issues requiring immediate attention
- **Medium**: Important improvements with significant impact
- **Low**: Nice-to-have enhancements and optimizations

#### Implementation Types
- **Automatic**: Can be implemented automatically via PR
- **Manual**: Requires human implementation with provided guidance

### Pull Request Creation

#### Automated Improvements
- **Documentation Updates**: README improvements, missing documentation
- **Configuration Files**: Adding missing configuration files
- **Security Fixes**: Basic security improvements
- **Code Formatting**: Consistent code style and formatting

#### PR Management
- **Smart Branching**: Descriptive branch names with improvement categories
- **Comprehensive Descriptions**: Detailed PR descriptions with change rationale
- **Review Guidelines**: Clear instructions for reviewers
- **Change Documentation**: Complete commit history with meaningful messages

### Monitoring and Analytics

#### Real-Time Dashboards
- **System Metrics**: CPU, memory, disk usage
- **Application Metrics**: Request rates, response times, error rates
- **Agent Status**: Active agents, task progress, completion rates
- **GitHub Integration**: API rate limits, request success rates

#### Historical Analytics
- **Analysis Trends**: Repository analysis patterns over time
- **Improvement Tracking**: Success rates of suggested improvements
- **Performance Metrics**: Application performance trends
- **Usage Statistics**: Feature usage and user patterns

## ⚙️ Configuration

### Configuration File (`config.yaml`)

The application uses a comprehensive YAML configuration file:

```yaml
# Logging Configuration
logging:
  level: INFO                    # Log level (DEBUG, INFO, WARNING, ERROR)
  enable_console: true          # Console logging
  enable_file: true             # File logging
  enable_json: true             # JSON structured logs
  log_file: "logs/mcp_github_analyzer.log"
  json_log_file: "logs/mcp_github_analyzer.jsonl"

# Monitoring Configuration
monitoring:
  collection_interval: 30       # Metrics collection interval (seconds)
  enable_system_metrics: true   # System performance metrics
  enable_custom_metrics: true   # Custom application metrics
  dashboard_refresh_interval: 5 # Dashboard refresh rate (seconds)

# Integration Settings
integrations:
  github:
    enabled: true
    rate_limit_per_hour: 5000   # GitHub API rate limit
    timeout_seconds: 30         # Request timeout
  
  mcp:
    enabled: true
    server_host: "localhost"    # MCP server host
    server_port: 8080          # MCP server port
    timeout_seconds: 30        # Request timeout
  
  anthropic:
    enabled: true
    timeout_seconds: 30        # Request timeout
    max_tokens: 4096          # Maximum tokens per request

# Agent Configuration
agents:
  default_timeout: 300          # Default agent timeout (seconds)
  max_retries: 3               # Maximum retry attempts
  enable_monitoring: true       # Agent monitoring
  enable_logging: true         # Agent logging
  
  github_analyzer:
    max_files_to_analyze: 100   # Maximum files to analyze
    analysis_depth: "comprehensive"  # Analysis depth level
  
  pr_creator:
    default_branch_prefix: "bmasterai/improvement"
    max_changes_per_pr: 10      # Maximum changes per PR

# Alert Configuration
alerts:
  - metric: "cpu_percent"
    threshold: 80
    condition: "greater_than"
    duration_minutes: 5
  - metric: "memory_percent"
    threshold: 90
    condition: "greater_than"
    duration_minutes: 3
```

### Environment Override

Environment variables automatically override configuration values:

| Environment Variable | Configuration Path | Description |
|---------------------|-------------------|-------------|
| `GITHUB_TOKEN` | `integrations.github.token` | GitHub API token |
| `ANTHROPIC_API_KEY` | `integrations.anthropic.api_key` | Anthropic API key |
| `MCP_SERVER_HOST` | `integrations.mcp.server_host` | MCP server host |
| `MCP_SERVER_PORT` | `integrations.mcp.server_port` | MCP server port |
| `LOG_LEVEL` | `logging.level` | Logging level |

### Customization Options

#### Analysis Customization
- **Analysis Depth**: Quick, Standard, Comprehensive
- **File Limits**: Maximum files to analyze per repository
- **Priority Filters**: Filter suggestions by priority level
- **Category Filters**: Focus on specific improvement categories

#### PR Creation Customization
- **Branch Naming**: Customize branch prefix and naming patterns
- **PR Templates**: Customize pull request description templates
- **Auto-merge Settings**: Configure automatic merge criteria
- **Change Limits**: Maximum changes per pull request

#### Monitoring Customization
- **Metric Collection**: Configure which metrics to collect
- **Alert Thresholds**: Set custom alert thresholds
- **Dashboard Layout**: Customize monitoring dashboard
- **Retention Policies**: Configure log and metric retention

## 🛠 Development

### Project Structure

```
mcp-github-streamlit/
├── app/                          # Main application directory
│   ├── agents/                   # Agent implementations
│   │   ├── __init__.py
│   │   ├── coordinator.py        # Workflow coordinator agent
│   │   ├── github_analyzer.py    # Repository analysis agent
│   │   └── pr_creator.py         # Pull request creation agent
│   ├── components/               # UI components
│   │   ├── __init__.py
│   │   └── ui_components.py      # Streamlit UI components
│   ├── integrations/             # External integrations
│   │   ├── __init__.py
│   │   ├── github_client.py      # GitHub API client
│   │   └── mcp_client.py         # MCP client
│   ├── utils/                    # Utility modules
│   │   ├── __init__.py
│   │   ├── bmasterai_logging.py  # BMasterAI logging framework
│   │   ├── bmasterai_monitoring.py # BMasterAI monitoring
│   │   ├── llm_client.py         # LLM client (Anthropic)
│   │   └── session_manager.py    # Session management
│   ├── logs/                     # Log files
│   ├── app.py                    # Main Streamlit application
│   ├── config.py                 # Configuration management
│   ├── config.yaml               # Configuration file
│   └── requirements.txt          # Python dependencies
└── README.md                     # This file
```

### Key Components Explained

#### 1. Agents (`agents/`)
- **Coordinator**: Orchestrates workflow between agents
- **GitHub Analyzer**: Handles repository analysis logic
- **PR Creator**: Manages pull request creation and Git operations

#### 2. Integrations (`integrations/`)
- **GitHub Client**: Wrapper for GitHub API operations
- **MCP Client**: Interface for Model Context Protocol operations

#### 3. Utils (`utils/`)
- **BMasterAI Logging**: Structured logging with event tracking
- **BMasterAI Monitoring**: Real-time monitoring and metrics
- **LLM Client**: Anthropic API integration with streaming support
- **Session Manager**: User session and state management

#### 4. Components (`components/`)
- **UI Components**: Reusable Streamlit interface components

### Adding New Features

#### Creating a New Agent

1. **Create Agent Class**
   ```python
   # agents/new_agent.py
   from utils.bmasterai_logging import get_logger
   from utils.bmasterai_monitoring import get_monitor
   
   class NewAgent:
       def __init__(self, agent_id="new_agent"):
           self.agent_id = agent_id
           self.logger = get_logger()
           self.monitor = get_monitor()
   ```

2. **Register with Coordinator**
   ```python
   # agents/coordinator.py
   from agents.new_agent import NewAgent
   
   class WorkflowCoordinator:
       def __init__(self):
           self.new_agent = NewAgent()
   ```

#### Adding New Integrations

1. **Create Integration Client**
   ```python
   # integrations/new_service.py
   class NewServiceClient:
       def __init__(self):
           self.logger = get_logger()
           self.monitor = get_monitor()
   ```

2. **Add Configuration**
   ```yaml
   # config.yaml
   integrations:
     new_service:
       enabled: true
       api_key: ${NEW_SERVICE_API_KEY}
   ```

#### Extending UI Components

1. **Add New Component**
   ```python
   # components/ui_components.py
   def render_new_feature():
       st.markdown("### New Feature")
       # Implementation here
   ```

2. **Integrate with Main App**
   ```python
   # app.py
   from components.ui_components import render_new_feature
   
   def main():
       render_new_feature()
   ```

### Testing

#### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test module
python -m pytest tests/test_agents.py

# Run with coverage
python -m pytest --cov=app tests/
```

#### Test Structure
```
tests/
├── test_agents/
├── test_integrations/
├── test_utils/
└── test_components/
```

### Deployment

#### Local Development
```bash
streamlit run app.py
```

#### Production Deployment
```bash
# Using Docker
docker build -t mcp-github-analyzer .
docker run -p 8501:8501 mcp-github-analyzer

# Using systemd service
sudo systemctl start mcp-github-analyzer
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: GitHub API authentication failures
```
Error: GitHub API authentication failed
```

**Solutions**:
- Verify `GITHUB_TOKEN` environment variable is set
- Check token permissions (needs `repo`, `read:org`, `workflow` scopes)
- Ensure token hasn't expired
- Test token manually: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

**Problem**: Anthropic API authentication failures
```
Error: ANTHROPIC_API_KEY environment variable is required
```

**Solutions**:
- Set `ANTHROPIC_API_KEY` environment variable
- Verify API key is valid and has sufficient credits
- Check API key format (should start with `sk-ant-`)

#### 2. Connection Issues

**Problem**: MCP server connection failures
```
Error: Failed to connect to MCP server at localhost:8080
```

**Solutions**:
- Verify MCP server is running: `curl http://localhost:8080/health`
- Check `MCP_SERVER_HOST` and `MCP_SERVER_PORT` environment variables
- Disable MCP integration in config.yaml if not needed:
  ```yaml
  integrations:
    mcp:
      enabled: false
  ```

**Problem**: GitHub API rate limiting
```
Error: GitHub API rate limit exceeded
```

**Solutions**:
- Wait for rate limit reset (shown in error message)
- Use authenticated requests (provides higher rate limits)
- Reduce analysis frequency
- Configure rate limiting in config.yaml:
  ```yaml
  integrations:
    github:
      rate_limit_per_hour: 1000
  ```

#### 3. Application Errors

**Problem**: Streamlit startup failures
```
Error: ModuleNotFoundError: No module named 'anthropic'
```

**Solutions**:
- Install dependencies: `pip install -r requirements.txt`
- Verify Python version (3.11+ required)
- Check virtual environment activation

**Problem**: Configuration errors
```
Error: Failed to load configuration
```

**Solutions**:
- Verify `config.yaml` file exists and is valid YAML
- Check file permissions
- Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`

**Problem**: Memory issues during analysis
```
Error: MemoryError during repository analysis
```

**Solutions**:
- Reduce `max_files_to_analyze` in config.yaml
- Use "Quick" instead of "Comprehensive" analysis
- Increase system memory
- Close other applications

#### 4. Agent-Specific Issues

**Problem**: Agent initialization failures
```
Error: Failed to initialize GitHub Analyzer Agent
```

**Solutions**:
- Check agent dependencies (GitHub token, LLM API key)
- Verify BMasterAI logging configuration
- Check logs directory permissions
- Review agent-specific configuration in config.yaml

**Problem**: Workflow coordination errors
```
Error: Workflow coordination failed
```

**Solutions**:
- Check individual agent status
- Review workflow logs in `logs/mcp_github_analyzer.jsonl`
- Verify agent timeout settings
- Check system resources (CPU, memory)

### Debugging Guide

#### 1. Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
streamlit run app.py
```

#### 2. Check Log Files
```bash
# Application logs
tail -f logs/mcp_github_analyzer.log

# JSON structured logs
tail -f logs/mcp_github_analyzer.jsonl | jq '.'
```

#### 3. Monitor System Resources
```bash
# Check memory usage
free -h

# Check CPU usage
htop

# Check disk space
df -h
```

#### 4. Test Components Individually

**Test GitHub Integration**:
```python
from integrations.github_client import get_github_client
client = get_github_client()
repo_info = client.get_repository_info("owner/repo")
print(repo_info)
```

**Test LLM Integration**:
```python
from utils.llm_client import get_llm_client
client = get_llm_client()
result = client.call_llm("claude-3-sonnet-20240229", "Hello, test message")
print(result)
```

**Test MCP Integration**:
```python
from integrations.mcp_client import get_mcp_client
async with get_mcp_client() as client:
    result = await client.clone_repository("https://github.com/owner/repo")
    print(result)
```

#### 5. Configuration Validation
```python
from config import get_config_manager
config = get_config_manager()
print("GitHub config:", config.get_github_config())
print("Anthropic config:", config.get_anthropic_config())
print("MCP config:", config.get_mcp_config())
```

### Getting Help

#### Log Analysis
When reporting issues, include:
- Application logs from `logs/mcp_github_analyzer.log`
- JSON logs from `logs/mcp_github_analyzer.jsonl`
- System information (OS, Python version)
- Configuration details (sanitized)

#### Performance Issues
For performance problems, provide:
- Repository size and complexity
- Analysis type used
- System specifications
- Memory and CPU usage during analysis

#### Error Reporting
For errors, include:
- Complete error message and stack trace
- Steps to reproduce
- Environment configuration
- Recent changes made

## 🤝 Contributing

We welcome contributions to the MCP GitHub Analyzer! Please follow these guidelines:

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Set up development environment
4. Make changes with proper testing
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code style
- Include docstrings for all functions and classes
- Add type hints where appropriate
- Write comprehensive tests for new features

### Testing Requirements
- All new features must include tests
- Maintain test coverage above 80%
- Test both success and failure scenarios
- Include integration tests for external services

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **BMasterAI** for comprehensive logging and monitoring framework
- **Anthropic** for powerful Claude AI models
- **Streamlit** for excellent web application framework
- **Model Context Protocol (MCP)** for advanced Git integration capabilities

---

*For more information or support, please contact the development team or create an issue in the repository.*
