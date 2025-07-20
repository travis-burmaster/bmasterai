
# MCP GitHub Analyzer

A comprehensive Streamlit application that integrates git MCP capabilities with BMasterAI logging and monitoring for automated GitHub repository analysis and improvement suggestions.

## Features

### 🔍 Core Functionality
- **Repository Analysis**: Automated analysis of GitHub repositories using MCP tools and AI
- **Code Quality Assessment**: Comprehensive code structure and quality metrics
- **Security Analysis**: Security vulnerability detection and best practices evaluation
- **Improvement Suggestions**: AI-powered suggestions for repository enhancements
- **Pull Request Creation**: Automated creation of feature branches with improvements

### 🤖 BMasterAI Integration
- **Structured Logging**: Complete logging with event types (AGENT_START, TASK_START, etc.)
- **Real-time Monitoring**: System metrics, performance tracking, and agent monitoring
- **Error Handling**: Comprehensive error logging and monitoring
- **Dashboard**: Real-time monitoring dashboard integrated in the UI

### 🔧 MCP Integration
- **Git Operations**: Repository cloning, branch creation, and PR management
- **GitHub API**: Repository information, file analysis, and statistics
- **Mock Support**: Mock MCP client for testing without external dependencies

### 📊 UI/UX Features
- **Clean Interface**: Intuitive Streamlit interface with multiple pages
- **Progress Tracking**: Real-time analysis progress and status updates
- **Results Display**: Comprehensive analysis results with charts and metrics
- **History Management**: Session-based analysis history tracking
- **Settings**: Configurable analysis parameters and system settings

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd /home/ubuntu/mcp-github-analyzer/app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file with your API keys
   echo "GITHUB_TOKEN=your_github_token_here" >> .env
   # ABACUSAI_API_KEY is already configured
   ```

4. **Create logs directory**:
   ```bash
   mkdir -p logs
   ```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Using the Application

1. **Repository Analysis**:
   - Enter a GitHub repository URL
   - Select analysis type (comprehensive, quick, security-focused)
   - Configure options (PR creation, security analysis, etc.)
   - Click "Analyze Repository"

2. **Monitoring Dashboard**:
   - View real-time system metrics
   - Monitor agent performance
   - Check active alerts
   - Review error rates and task completion

3. **Analysis History**:
   - Review past analyses
   - View detailed results
   - Track analysis trends

4. **Settings**:
   - Configure monitoring settings
   - Set default analysis options
   - Manage session data

## Architecture

### Component Structure
```
app/
├── agents/                 # AI agents for different tasks
│   ├── github_analyzer.py  # Repository analysis agent
│   ├── pr_creator.py       # Pull request creation agent
│   └── coordinator.py      # Multi-agent workflow coordinator
├── components/             # Streamlit UI components
│   └── ui_components.py    # Reusable UI components
├── integrations/           # External service integrations
│   ├── github_client.py    # GitHub API client
│   └── mcp_client.py       # MCP client for git operations
├── utils/                  # Utility modules
│   ├── bmasterai_logging.py   # BMasterAI logging implementation
│   ├── bmasterai_monitoring.py # BMasterAI monitoring implementation
│   ├── llm_client.py          # LLM API client with streaming
│   └── session_manager.py     # Session management
├── api/                    # API routes (for future extensions)
├── logs/                   # Application logs
├── config.py              # Configuration management
├── config.yaml           # Application configuration
└── app.py                # Main Streamlit application
```

### Key Components

#### Agents
- **GitHubAnalyzerAgent**: Performs comprehensive repository analysis
- **PRCreatorAgent**: Creates pull requests with improvement suggestions
- **WorkflowCoordinator**: Orchestrates multi-agent workflows

#### Monitoring & Logging
- **BMasterAI Logging**: Structured event logging with JSON output
- **BMasterAI Monitoring**: Real-time metrics collection and alerting
- **Session Management**: User session tracking and history

#### Integrations
- **GitHub Client**: GitHub API integration with rate limiting
- **MCP Client**: Git operations through Model Context Protocol
- **LLM Client**: Streaming LLM API client for AI analysis

## Configuration

### Environment Variables
- `GITHUB_TOKEN`: GitHub personal access token
- `ABACUSAI_API_KEY`: LLM API key (automatically configured)

### Configuration File (config.yaml)
```yaml
logging:
  level: INFO
  enable_console: true
  enable_file: true
  enable_json: true

monitoring:
  collection_interval: 30
  enable_system_metrics: true
  enable_custom_metrics: true

agents:
  default_timeout: 300
  max_retries: 3
  enable_monitoring: true
  enable_logging: true
```

## BMasterAI Patterns Implementation

### Logging Patterns
```python
# Agent lifecycle logging
logger.log_agent_start(agent_id, agent_name, metadata)
logger.log_agent_stop(agent_id, agent_name, metadata)

# Task execution logging
logger.log_task_start(agent_id, task_name, task_id, metadata)
logger.log_task_complete(agent_id, task_name, task_id, duration_ms, metadata)
logger.log_task_error(agent_id, task_name, task_id, error, duration_ms, metadata)

# LLM call logging
logger.log_llm_call(agent_id, model, prompt_length, max_tokens, metadata)
```

### Monitoring Patterns
```python
# Performance tracking
monitor.track_agent_start(agent_id)
monitor.track_task_duration(agent_id, task_name, duration_ms)
monitor.track_error(agent_id, error_type)
monitor.track_llm_call(agent_id, model, tokens_used, duration_ms)

# System health
health = monitor.get_system_health()
agent_dashboard = monitor.get_agent_dashboard(agent_id)
```

## Features

### Analysis Capabilities
- **Code Structure Analysis**: File organization, quality metrics
- **Security Assessment**: Vulnerability detection, best practices
- **Documentation Review**: README, licensing, contributing guidelines
- **Repository Health**: Overall health score and recommendations

### Improvement Suggestions
- **Automated Implementation**: Security fixes, documentation improvements
- **Manual Recommendations**: Code quality, testing, architecture
- **Priority Levels**: High, medium, low priority categorization
- **Implementation Guidance**: Step-by-step instructions

### Pull Request Creation
- **Branch Management**: Automated branch creation with descriptive names
- **File Modifications**: Automated file improvements (README, .gitignore, etc.)
- **PR Descriptions**: AI-generated comprehensive PR descriptions
- **Change Tracking**: Detailed tracking of all modifications

## Monitoring & Observability

### System Metrics
- CPU and memory usage monitoring
- Disk space and network utilization
- Alert thresholds with notifications

### Agent Metrics
- Task completion rates and durations
- Error rates and failure analysis
- Agent activity and performance trends

### Application Metrics
- Analysis success rates
- User session tracking
- Feature usage analytics

## Security Features

### GitHub Integration
- Secure token-based authentication
- Rate limiting and API quota management
- Repository access validation

### Data Protection
- No sensitive data storage
- Secure environment variable handling
- Audit logging for all operations

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**:
   - Ensure GitHub token is configured
   - Monitor rate limit usage in logs
   - Use appropriate delays between requests

2. **LLM API Errors**:
   - Check ABACUSAI_API_KEY configuration
   - Monitor token usage and limits
   - Review error logs for specific issues

3. **Monitoring Issues**:
   - Check system permissions for metrics collection
   - Verify log file write permissions
   - Review monitoring configuration settings

### Debug Mode
Enable debug logging in settings or set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## Contributing

1. Follow BMasterAI logging patterns for all new features
2. Add comprehensive error handling and monitoring
3. Update configuration files for new settings
4. Write tests for new functionality
5. Update documentation

## License

This project follows the same license terms as the BMasterAI framework.
