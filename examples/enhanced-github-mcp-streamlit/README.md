# Enhanced MCP GitHub Analyzer

An advanced multi-agent system for GitHub repository analysis and automated feature implementation, powered by BMasterAI.

## ⚡ Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd examples/enhanced-github-mcp-streamlit
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Required API Keys:**
   - Get your [OpenAI API key](https://platform.openai.com/api-keys)
   - Get your [Anthropic API key](https://console.anthropic.com/)
   - Create a [GitHub Personal Access Token](https://github.com/settings/tokens)

4. **Run:**
   ```bash
   streamlit run app.py
   ```

> **⚠️ Important**: Never commit your `.env` file! It contains sensitive API keys.

## 🚀 New Features

### Feature Addition Mode
The enhanced version now includes a powerful **Feature Addition Mode** alongside the existing security analysis capabilities:

- **Natural Language Feature Requests**: Describe features in plain English (e.g., "Add a login system with JWT authentication", "Fix the bug in user profile update", "Add dark mode toggle")
- **Intelligent Code Generation**: AI-powered analysis of repository structure and automatic code generation
- **Automated Branch Management**: Creates feature branches automatically with meaningful names
- **Pull Request Automation**: Generates comprehensive pull requests with detailed descriptions, testing recommendations, and implementation notes
- **Multi-Language Support**: Works with Python, JavaScript/TypeScript, Java, Rust, Go, and more

### Enhanced Architecture
- **Feature Agent**: New specialized agent for handling feature implementation requests
- **Dual-Mode Interface**: Seamless switching between Security Analysis and Feature Addition modes
- **Advanced Progress Tracking**: Real-time progress indicators for both analysis and feature implementation
- **Comprehensive Results Display**: Detailed breakdowns of implementation plans, code changes, and testing strategies

## 🎯 Operation Modes

### 1. Security Analysis Mode (Original)
- Comprehensive repository security scanning
- Code quality analysis
- Automated improvement suggestions
- Security vulnerability detection
- Pull request creation with fixes

### 2. Feature Addition Mode (New)
- Natural language feature description
- Repository structure analysis
- Implementation plan generation
- Automated code changes
- Feature branch creation
- Pull request generation with comprehensive documentation

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd examples/enhanced-github-mcp-streamlit
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your actual API keys and configuration
   nano .env  # or use your preferred editor
   ```

4. **Configure your .env file:**
   Open `.env` and replace the placeholder values with your actual API keys and settings.

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## 🔧 Configuration

### Environment Variables Setup

The application uses a `.env` file for configuration. This approach provides better security and flexibility compared to hardcoded values or command-line exports.

#### Required Setup Steps:

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your actual values:**
   ```bash
   # API Keys (Required)
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
   GITHUB_TOKEN=your_actual_github_token_here
   ```

#### Complete Environment Variables Reference:

##### API Keys (Required)
- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models  
- `GITHUB_TOKEN`: GitHub personal access token with repo permissions

##### Model Configuration
- `DEFAULT_LLM_MODEL`: Default model for general use (default: `claude-4-sonnet`)
- `FALLBACK_LLM_MODEL`: Fallback model if primary fails (default: `gpt-4o-mini`)
- `FEATURE_AGENT_MODEL`: Model for feature implementation (default: `claude-4-sonnet`)
- `ANALYZER_MODEL`: Model for repository analysis (default: `gpt-4o-mini`)
- `PR_CREATOR_MODEL`: Model for PR generation (default: `gpt-4o-mini`)

##### Application Settings
- `APP_NAME`: Application display name (default: `MCP GitHub Analyzer`)
- `DEBUG`: Enable debug mode (default: `false`)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: `INFO`)

##### GitHub Configuration
- `GITHUB_RATE_LIMIT`: API rate limit per hour (default: `5000`)
- `GITHUB_TIMEOUT`: Request timeout in seconds (default: `30`)

##### MCP Configuration
- `MCP_ENABLED`: Enable MCP integration (default: `true`)
- `MCP_TIMEOUT`: MCP request timeout (default: `30`)

##### Monitoring Configuration
- `MONITORING_ENABLED`: Enable system monitoring (default: `true`)
- `MONITORING_INTERVAL`: Monitoring collection interval in seconds (default: `30`)

##### Logging Configuration
- `LOG_TO_FILE`: Enable file logging (default: `true`)
- `LOG_TO_CONSOLE`: Enable console logging (default: `true`)
- `LOG_JSON_FORMAT`: Use JSON log format (default: `true`)
- `LOG_FILE`: Log file path (default: `logs/mcp_github_analyzer.log`)
- `JSON_LOG_FILE`: JSON log file path (default: `logs/mcp_github_analyzer.jsonl`)

##### Security Settings
- `SESSION_SECRET`: Secret key for session management
- `ENCRYPTION_KEY`: Key for data encryption

#### Example .env File:
```bash
# API Keys - Replace with your actual keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GITHUB_TOKEN=ghp_your-github-token-here

# Model Configuration
DEFAULT_LLM_MODEL=claude-4-sonnet
FALLBACK_LLM_MODEL=gpt-4o-mini
FEATURE_AGENT_MODEL=claude-4-sonnet
ANALYZER_MODEL=gpt-4o-mini
PR_CREATOR_MODEL=gpt-4o-mini

# Application Settings
APP_NAME=MCP GitHub Analyzer
DEBUG=false
LOG_LEVEL=INFO

# GitHub Configuration
GITHUB_RATE_LIMIT=5000
GITHUB_TIMEOUT=30
```

### Configuration Priority

The application loads configuration in the following order (later sources override earlier ones):

1. **Default values** (hardcoded in the application)
2. **config.yaml file** (if present)
3. **Environment variables** (highest priority)

This allows for flexible deployment scenarios where you can use different configuration methods as needed.

### GitHub Token Permissions
Your GitHub token needs the following permissions:
- `repo`: Full repository access
- `workflow`: GitHub Actions workflow access (if applicable)
- `read:org`: Organization read access (for organization repositories)

## 📖 Usage Guide

### Security Analysis Mode

1. **Select Mode**: Choose "🔍 Security Analysis" from the mode selector
2. **Enter Repository**: Provide the GitHub repository URL
3. **Configure Analysis**: 
   - Choose analysis type (comprehensive, quick, security-focused)
   - Enable/disable PR creation
   - Set suggestion filters and limits
4. **Run Analysis**: Click "🚀 Analyze Repository"
5. **Review Results**: Examine security findings, code quality metrics, and improvement suggestions

### Feature Addition Mode

1. **Select Mode**: Choose "🚀 Feature Addition" from the mode selector
2. **Enter Repository**: Provide the GitHub repository URL
3. **Describe Feature**: Write a natural language description of what you want to implement
4. **Configure Options**:
   - Set base branch (default: main)
   - Specify feature branch name (optional, auto-generated if empty)
   - Enable/disable automatic PR creation
   - Set complexity limits
5. **Implement Feature**: Click "🚀 Implement Feature"
6. **Review Results**: Examine the implementation plan, code changes, and created pull request

## 🏗️ Architecture

### Multi-Agent System
- **Workflow Coordinator**: Orchestrates all agent interactions and workflows
- **GitHub Analyzer**: Handles repository analysis and security scanning
- **PR Creator**: Manages pull request creation and management
- **Feature Agent**: New agent specialized in feature implementation
- **Feature PR Worker**: Utility functions for feature branch and PR operations

### Core Components
- **BMasterAI Integration**: Advanced logging, monitoring, and performance tracking
- **LLM Integration**: Support for multiple language models (Claude, GPT-4)
- **GitHub Integration**: Comprehensive GitHub API integration
- **Session Management**: User session tracking and history
- **UI Components**: Modular Streamlit interface components

### Data Flow
1. **User Input**: Repository URL and feature description/analysis configuration
2. **Repository Analysis**: Structure analysis, language detection, file categorization
3. **AI Processing**: LLM-powered plan generation and code creation
4. **GitHub Operations**: Branch creation, file modifications, PR creation
5. **Results Display**: Comprehensive results with actionable insights

## 🔍 Feature Implementation Process

### 1. Repository Analysis
- Fetches repository structure and metadata
- Analyzes programming languages and frameworks
- Identifies key configuration files and patterns
- Reads README and documentation

### 2. Implementation Planning
- Generates detailed feature implementation plan
- Identifies files that need modification
- Plans code architecture and integration points
- Estimates complexity and implementation time
- Suggests testing strategies

### 3. Code Generation
- Creates new code following repository patterns
- Modifies existing files with proper integration
- Maintains code style and best practices
- Includes error handling and documentation

### 4. Branch and PR Management
- Creates feature branches with descriptive names
- Applies code changes with meaningful commit messages
- Generates comprehensive pull request descriptions
- Includes testing recommendations and potential issues

## 📊 Monitoring and Logging

### BMasterAI Integration
- **Real-time Monitoring**: System performance and agent activity tracking
- **Comprehensive Logging**: Detailed event logging with structured metadata
- **Error Tracking**: Automatic error detection and reporting
- **Performance Metrics**: Task duration and success rate monitoring

### Dashboard Features
- System health indicators
- Active agent monitoring
- Session duration tracking
- Analysis history and statistics

## 🧪 Testing and Quality Assurance

### Automated Testing Recommendations
The Feature Agent provides testing strategies including:
- Unit test suggestions
- Integration test recommendations
- Manual testing procedures
- Edge case considerations

### Code Quality
- Follows repository coding standards
- Includes proper error handling
- Maintains documentation standards
- Implements security best practices

## 🔒 Security Considerations

### Environment Variables Security
- **Never commit .env files**: The `.env` file contains sensitive API keys and should never be committed to version control
- **Use .env.example**: Share configuration structure using `.env.example` without actual secrets
- **Secure storage**: Store API keys securely and rotate them regularly
- **Access control**: Limit access to the `.env` file on your system
- **Production deployment**: Use secure environment variable management in production (e.g., Docker secrets, Kubernetes secrets, cloud provider secret managers)

### Data Privacy
- No code is stored permanently
- GitHub tokens are handled securely
- All API communications are encrypted
- Session data is managed locally
- API keys are loaded from environment variables only

### Access Control
- Requires valid GitHub token with appropriate permissions
- Respects repository access controls
- Operates within GitHub API rate limits
- Follows GitHub's terms of service
- Environment-based configuration prevents accidental exposure of credentials

## 🚨 Limitations and Considerations

### Current Limitations
- **Complexity Bounds**: Very complex features may require manual review
- **Language Support**: Best performance with popular languages and frameworks
- **Repository Size**: Large repositories may take longer to analyze
- **API Limits**: Subject to GitHub API rate limits and LLM token limits

### Best Practices
- **Start Small**: Begin with simple feature requests to understand the system
- **Review Changes**: Always review generated code before merging
- **Test Thoroughly**: Follow provided testing recommendations
- **Backup Important**: Ensure important branches are backed up before modifications

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Standards
- Follow existing code style and patterns
- Include comprehensive docstrings
- Add appropriate logging and monitoring
- Update documentation as needed

## 📝 Changelog

### Version 2.1.0 (Latest)
- 🆕 **Updated to Claude 4 Sonnet**: Default model upgraded from Claude 3.5 Sonnet to Claude 4 Sonnet for improved performance and capabilities
- ⚡ **Enhanced AI Performance**: Better code generation and analysis with the latest Claude model
- 🔧 **Updated Configuration**: All model references updated to use Claude 4 Sonnet by default

### Version 2.0.0 (Enhanced)
- ✨ Added Feature Addition Mode
- 🤖 New Feature Agent with intelligent code generation
- 🌿 Automated branch and PR management
- 📋 Comprehensive implementation planning
- 🧪 Advanced testing strategy recommendations
- 🎯 Dual-mode interface with seamless switching
- 📊 Enhanced progress tracking and results display

### Version 1.0.0 (Original)
- 🔍 Repository security analysis
- 🛡️ Vulnerability scanning
- 📈 Code quality metrics
- 🔧 Automated improvement suggestions
- 📝 Pull request creation
- 📊 BMasterAI monitoring integration

## 🔧 Troubleshooting

### Common Environment Variable Issues

#### "API key not configured" Error
- **Problem**: Missing or invalid API keys
- **Solution**: 
  1. Ensure `.env` file exists in the project root
  2. Check that API keys are properly set without quotes
  3. Verify API keys are valid and active
  4. Restart the application after changing `.env`

#### "Module not found" Errors
- **Problem**: Missing python-dotenv dependency
- **Solution**: 
  ```bash
  pip install python-dotenv
  # or
  pip install -r requirements.txt
  ```

#### Environment Variables Not Loading
- **Problem**: `.env` file not in the correct location or format
- **Solution**:
  1. Ensure `.env` is in the same directory as `app.py`
  2. Check file format: `KEY=value` (no spaces around `=`)
  3. No quotes needed around values unless they contain spaces
  4. Use `#` for comments

#### Model Configuration Issues
- **Problem**: Invalid model names or unavailable models
- **Solution**:
  1. Check model names in `.env` match available models
  2. Ensure you have access to the specified models (Claude 4 Sonnet requires appropriate API access)
  3. Use fallback models if primary models fail

#### GitHub Token Issues
- **Problem**: GitHub API errors or permission denied
- **Solution**:
  1. Verify token has required permissions (repo, workflow)
  2. Check token hasn't expired
  3. Ensure token format is correct (starts with `ghp_` for personal tokens)

### Debug Mode
Enable debug mode for more detailed error information:
```bash
# In your .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📞 Support

For issues, questions, or feature requests:
1. Check the existing documentation
2. Review the troubleshooting section above
3. Verify your `.env` configuration
4. Check the application logs in the `logs/` directory
5. Create an issue in the repository
6. Provide detailed information about your setup and the problem

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using BMasterAI, Streamlit, and advanced AI agents**
