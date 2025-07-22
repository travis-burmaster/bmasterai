# Lesson 01: GitHub MCP Streamlit Integration

## Overview

This comprehensive tutorial will guide you through setting up and using the GitHub MCP (Model Context Protocol) Streamlit application. You'll learn how to integrate GitHub repositories with AI agents, perform repository analysis, and create feature requests using BMasterAI.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation and Setup](#installation-and-setup)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Repository Analysis](#repository-analysis)
6. [Feature Request Workflow](#feature-request-workflow)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Next Steps](#next-steps)

## Prerequisites

Before starting this tutorial, ensure you have:

- **Python 3.8+** installed on your system
- **Git** installed and configured
- **GitHub account** with personal access token
- **Basic knowledge** of Python, Git, and command line
- **Text editor** or IDE (VS Code recommended)
- **Node.js 16+** (for MCP server components)

### Required Accounts and Tokens

1. **GitHub Personal Access Token**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate token with `repo`, `read:org`, and `read:user` scopes
   - Save token securely for later use

2. **OpenAI API Key** (optional but recommended)
   - Create account at OpenAI
   - Generate API key from dashboard
   - Required for AI-powered analysis features

## Installation and Setup

### Step 1: Clone the Repository

```bash
# Clone the enhanced GitHub MCP Streamlit repository
git clone https://github.com/your-org/enhanced-github-mcp-streamlit.git
cd enhanced-github-mcp-streamlit
```

### Step 2: Create Virtual Environment

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for MCP server
npm install
```

### Step 4: Verify Installation

```bash
# Check Python packages
pip list | grep streamlit
pip list | grep requests

# Check Node.js packages
npm list @modelcontextprotocol/sdk
```

## Configuration

### Step 1: Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` file with your credentials:

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_USERNAME=your_github_username

# OpenAI Configuration (optional)
OPENAI_API_KEY=sk-your_openai_key_here

# MCP Configuration
MCP_SERVER_PORT=3000
MCP_LOG_LEVEL=info

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Step 2: MCP Server Configuration

Create or verify `mcp-config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["build/index.js"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  },
  "logging": {
    "level": "info",
    "file": "logs/mcp.log"
  }
}
```

### Step 3: Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
address = "localhost"
maxUploadSize = 200

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[browser]
gatherUsageStats = false
```

## Basic Usage

### Step 1: Start the MCP Server

```bash
# Start MCP server in background
npm run start:mcp &

# Or start with logging
npm run start:mcp > logs/mcp.log 2>&1 &
```

### Step 2: Launch Streamlit Application

```bash
# Start Streamlit app
streamlit run app.py

# Or with custom configuration
streamlit run app.py --server.port 8501 --server.address localhost
```

### Step 3: Access the Application

1. Open browser to `http://localhost:8501`
2. You should see the GitHub MCP Streamlit interface
3. Verify connection status in the sidebar

### Step 4: Connect to GitHub

1. **Authentication Setup**
   - Navigate to "Settings" tab
   - Enter your GitHub token
   - Click "Test Connection"
   - Verify green status indicator

2. **Repository Selection**
   - Go to "Repository" tab
   - Enter repository URL or owner/repo format
   - Click "Load Repository"
   - Confirm repository details display

## Repository Analysis

### Basic Repository Information

```python
# Example: Get repository overview
def analyze_repository_basic(repo_url):
    """
    Perform basic repository analysis
    """
    # Repository metadata
    repo_info = {
        'name': 'enhanced-github-mcp-streamlit',
        'description': 'Enhanced GitHub MCP integration with Streamlit',
        'language': 'Python',
        'stars': 42,
        'forks': 8,
        'issues': 3
    }
    
    # File structure analysis
    file_structure = {
        'total_files': 156,
        'python_files': 23,
        'javascript_files': 12,
        'markdown_files': 8,
        'config_files': 5
    }
    
    return repo_info, file_structure
```

### Advanced Analysis Features

1. **Code Quality Assessment**
   ```bash
   # Run code quality checks
   python scripts/analyze_code_quality.py --repo-path ./
   ```

2. **Dependency Analysis**
   ```bash
   # Analyze dependencies
   python scripts/analyze_dependencies.py --requirements requirements.txt
   ```

3. **Security Scan**
   ```bash
   # Run security analysis
   python scripts/security_scan.py --target ./
   ```

### Using the Analysis Interface

1. **Load Repository**
   - Enter repository URL in the main interface
   - Click "Analyze Repository"
   - Wait for analysis to complete

2. **Review Results**
   - **Overview Tab**: Basic statistics and metrics
   - **Files Tab**: File structure and content analysis
   - **Dependencies Tab**: Package and library analysis
   - **Issues Tab**: Potential problems and suggestions

3. **Export Analysis**
   - Click "Export Report" button
   - Choose format (JSON, CSV, PDF)
   - Download generated report

## Feature Request Workflow

### Step 1: Create Feature Request

1. **Navigate to Feature Requests**
   - Click "Feature Requests" tab
   - Click "New Request" button

2. **Fill Request Details**
   ```markdown
   **Feature Title**: Add Dark Mode Support
   
   **Description**: 
   Implement dark mode theme for better user experience during night usage.
   
   **Requirements**:
   - Toggle switch in settings
   - Dark color scheme
   - Persistent user preference
   - Smooth theme transition
   
   **Priority**: Medium
   **Category**: UI/UX Enhancement
   ```

3. **Submit Request**
   - Click "Submit Request"
   - Note the generated request ID

### Step 2: AI-Powered Analysis

The system will automatically:

1. **Analyze Feasibility**
   - Check existing codebase
   - Identify required changes
   - Estimate implementation effort

2. **Generate Implementation Plan**
   - Break down into tasks
   - Suggest file modifications
   - Provide code examples

3. **Create Documentation**
   - Generate technical specifications
   - Create user stories
   - Produce acceptance criteria

### Step 3: Review and Approve

1. **Review Analysis Results**
   - Check feasibility assessment
   - Review implementation plan
   - Validate effort estimates

2. **Modify if Needed**
   - Edit requirements
   - Adjust scope
   - Update priorities

3. **Approve for Implementation**
   - Click "Approve Request"
   - Assign to development queue

## Advanced Features

### Custom Analysis Scripts

Create custom analysis scripts for specific needs:

```python
# scripts/custom_analysis.py
import os
import json
from pathlib import Path

class CustomAnalyzer:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        
    def analyze_test_coverage(self):
        """Analyze test coverage across the repository"""
        test_files = list(self.repo_path.glob("**/test_*.py"))
        source_files = list(self.repo_path.glob("**/*.py"))
        
        coverage_ratio = len(test_files) / len(source_files)
        
        return {
            'test_files': len(test_files),
            'source_files': len(source_files),
            'coverage_ratio': coverage_ratio,
            'status': 'good' if coverage_ratio > 0.7 else 'needs_improvement'
        }
    
    def analyze_documentation(self):
        """Analyze documentation completeness"""
        md_files = list(self.repo_path.glob("**/*.md"))
        py_files = list(self.repo_path.glob("**/*.py"))
        
        # Check for docstrings
        documented_functions = 0
        total_functions = 0
        
        for py_file in py_files:
            # Implementation for docstring analysis
            pass
            
        return {
            'markdown_files': len(md_files),
            'python_files': len(py_files),
            'documentation_ratio': documented_functions / max(total_functions, 1)
        }

# Usage
analyzer = CustomAnalyzer("./")
coverage_report = analyzer.analyze_test_coverage()
doc_report = analyzer.analyze_documentation()
```

### Integration with External Tools

```python
# Integration with GitHub API
import requests
from github import Github

class GitHubIntegration:
    def __init__(self, token):
        self.github = Github(token)
        
    def create_issue_from_feature_request(self, repo_name, feature_request):
        """Create GitHub issue from feature request"""
        repo = self.github.get_repo(repo_name)
        
        issue_body = f"""
        ## Feature Request
        
        **Description**: {feature_request['description']}
        
        **Requirements**:
        {feature_request['requirements']}
        
        **Priority**: {feature_request['priority']}
        
        ---
        *Generated automatically from BMasterAI Feature Request #{feature_request['id']}*
        """
        
        issue = repo.create_issue(
            title=feature_request['title'],
            body=issue_body,
            labels=['enhancement', 'feature-request']
        )
        
        return issue.number
```

### Webhook Integration

Set up webhooks for real-time updates:

```python
# webhook_handler.py
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/github', methods=['POST'])
def handle_github_webhook():
    """Handle GitHub webhook events"""
    signature = request.headers.get('X-Hub-Signature-256')
    payload = request.get_data()
    
    # Verify webhook signature
    if not verify_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 403
    
    event_type = request.headers.get('X-GitHub-Event')
    data = request.get_json()
    
    if event_type == 'push':
        handle_push_event(data)
    elif event_type == 'pull_request':
        handle_pr_event(data)
    elif event_type == 'issues':
        handle_issue_event(data)
    
    return jsonify({'status': 'success'})

def verify_signature(payload, signature):
    """Verify GitHub webhook signature"""
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Troubleshooting

### Common Issues and Solutions

1. **MCP Server Connection Failed**
   ```bash
   # Check if MCP server is running
   ps aux | grep node
   
   # Check port availability
   netstat -an | grep 3000
   
   # Restart MCP server
   npm run restart:mcp
   ```

2. **GitHub Authentication Error**
   ```bash
   # Verify token permissions
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   
   # Check token scopes
   curl -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

3. **Streamlit Performance Issues**
   ```python
   # Add caching to expensive operations
   @st.cache_data
   def load_repository_data(repo_url):
       # Expensive operation here
       return data
   
   # Use session state for persistence
   if 'repo_data' not in st.session_state:
       st.session_state.repo_data = load_repository_data(repo_url)
   ```

4. **Memory Issues with Large Repositories**
   ```python
   # Implement pagination for large datasets
   def paginate_files(files, page_size=100):
       for i in range(0, len(files), page_size):
           yield files[i:i + page_size]
   
   # Use generators for memory efficiency
   def analyze_files_generator(repo_path):
       for file_path in Path(repo_path).rglob("*.py"):
           yield analyze_single_file(file_path)
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variables
export STREAMLIT_DEBUG=true
export MCP_DEBUG=true
export GITHUB_MCP_LOG_LEVEL=debug

# Run with debug logging
streamlit run app.py --logger.level debug
```

### Log Analysis

```bash
# View MCP server logs
tail -f logs/mcp.log

# View Streamlit logs
tail -f logs/streamlit.log

# Search for specific errors
grep -i "error" logs/*.log
```

## Best Practices

### Security Best Practices

1. **Token Management**
   - Never commit tokens to version control
   - Use environment variables or secure vaults
   - Rotate tokens regularly
   - Use minimum required permissions

2. **Input Validation**
   ```python
   import re
   
   def validate_repo_url(url):
       """Validate GitHub repository URL"""
       pattern = r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
       return re.match(pattern, url) is not None
   
   def sanitize_input(user_input):
       """Sanitize user input to prevent injection"""
       # Remove potentially dangerous characters
       return re.sub(r'[<>"\']', '', user_input)
   ```

3. **Rate Limiting**
   ```python
   import time
   from functools import wraps
   
   def rate_limit(calls_per_minute=60):
       def decorator(func):
           last_called = [0.0]
           
           @wraps(func)
           def wrapper(*args, **kwargs):
               elapsed = time.time() - last_called[0]
               left_to_wait = 60.0 / calls_per_minute - elapsed
               
               if left_to_wait > 0:
                   time.sleep(left_to_wait)
               
               ret = func(*args, **kwargs)
               last_called[0] = time.time()
               return ret
           
           return wrapper
       return decorator
   ```

### Performance Optimization

1. **Caching Strategies**
   ```python
   # Cache repository metadata
   @st.cache_data(ttl=3600)  # Cache for 1 hour
   def get_repo_metadata(repo_url):
       return fetch_repo_data(repo_url)
   
   # Cache analysis results
   @st.cache_data(ttl=86400)  # Cache for 24 hours
   def analyze_repository(repo_url):
       return perform_analysis(repo_url)
   ```

2. **Async Operations**
   ```python
   import asyncio
   import aiohttp
   
   async def fetch_multiple_repos(repo_urls):
       """Fetch multiple repositories concurrently"""
       async with aiohttp.ClientSession() as session:
           tasks = [fetch_repo_async(session, url) for url in repo_urls]
           return await asyncio.gather(*tasks)
   ```

3. **Memory Management**
   ```python
   # Use generators for large datasets
   def process_large_repository(repo_path):
       for file_batch in batch_files(repo_path, batch_size=100):
           yield process_file_batch(file_batch)
           # Memory cleanup
           gc.collect()
   ```

### Code Organization

1. **Modular Structure**
   ```
   enhanced-github-mcp-streamlit/
   ├── app.py                 # Main Streamlit application
   ├── components/            # Reusable UI components
   │   ├── __init__.py
   │   ├── repository.py
   │   ├── analysis.py
   │   └── feature_requests.py
   ├── services/              # Business logic services
   │   ├── __init__.py
   │   ├── github_service.py
   │   ├── mcp_service.py
   │   └── analysis_service.py
   ├── utils/                 # Utility functions
   │   ├── __init__.py
   │   ├── validators.py
   │   ├── formatters.py
   │   └── helpers.py
   └── tests/                 # Test files
       ├── __init__.py
       ├── test_services.py
       └── test_utils.py
   ```

2. **Configuration Management**
   ```python
   # config.py
   import os
   from dataclasses import dataclass
   
   @dataclass
   class Config:
       github_token: str
       openai_api_key: str
       mcp_server_port: int
       streamlit_port: int
       debug_mode: bool
       
       @classmethod
       def from_env(cls):
           return cls(
               github_token=os.getenv('GITHUB_TOKEN'),
               openai_api_key=os.getenv('OPENAI_API_KEY'),
               mcp_server_port=int(os.getenv('MCP_SERVER_PORT', 3000)),
               streamlit_port=int(os.getenv('STREAMLIT_SERVER_PORT', 8501)),
               debug_mode=os.getenv('DEBUG', 'false').lower() == 'true'
           )
   ```

## Next Steps

### Extending the Application

1. **Add New Analysis Types**
   - Code complexity analysis
   - Performance profiling
   - Security vulnerability scanning
   - License compliance checking

2. **Integration with More Services**
   - GitLab support
   - Bitbucket integration
   - Azure DevOps connection
   - Jira integration

3. **Enhanced AI Features**
   - Code generation suggestions
   - Automated refactoring recommendations
   - Intelligent code review
   - Predictive maintenance alerts

### Learning Resources

1. **Documentation Links**
   - [Streamlit Documentation](https://docs.streamlit.io/)
   - [GitHub API Documentation](https://docs.github.com/en/rest)
   - [Model Context Protocol Specification](https://modelcontextprotocol.io/)

2. **Related Tutorials**
   - [Repository Analysis Guide](../shared/repository-analysis-guide.md)
   - [Feature Request Workflow](../shared/feature-request-workflow.md)
   - [Advanced MCP Integration](../lesson-02-advanced-mcp/README.md)

3. **Community Resources**
   - GitHub Discussions
   - Stack Overflow tags
   - Discord community server

### Practice Exercises

1. **Basic Exercise**: Set up the application and analyze a public repository
2. **Intermediate Exercise**: Create a custom analysis script for your specific needs
3. **Advanced Exercise**: Implement a new feature request workflow with AI integration

### Certification Path

Complete the following to earn your GitHub MCP Streamlit certification:

1. ✅ Successfully set up and configure the application
2. ✅ Perform repository analysis on 5 different repositories
3. ✅ Create and process 3 feature requests
4. ✅ Implement one custom analysis script
5. ✅ Deploy the application to a cloud platform

---

## Conclusion

You've now completed the comprehensive GitHub MCP Streamlit tutorial! You should be able to:

- Set up and configure the application
- Perform detailed repository analysis
- Create and manage feature requests
- Integrate with AI-powered analysis tools
- Troubleshoot common issues
- Follow security and performance best practices

Continue to the next lesson to explore advanced MCP integration patterns and build more sophisticated AI-powered development workflows.

---

**Need Help?**
- 📧 Email: travis@burmaster.com