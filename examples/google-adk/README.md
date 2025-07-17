# 🤖 AI Consultant Agent with Google ADK and BMasterAI

A powerful enterprise-grade AI business consultant that integrates Google's Agent Development Kit (ADK) with the comprehensive monitoring and management capabilities of the BMasterAI framework.

## 🌟 Features

### Core Capabilities
- **Real-time Market Research**: Uses Perplexity AI for current market data, trends, and competitor intelligence
- **Strategic Business Consulting**: Comprehensive market analysis and actionable recommendations
- **Risk Assessment**: Detailed risk analysis with mitigation strategies
- **Competitor Analysis**: In-depth competitive landscape evaluation
- **Implementation Planning**: Detailed roadmaps with timelines and success metrics

### Enterprise Features (BMasterAI)
- **Advanced Monitoring**: Real-time performance tracking and system health monitoring
- **Comprehensive Logging**: Structured logging with JSON output and multiple levels
- **Intelligent Alerting**: Configurable alerts with multiple notification channels
- **Multi-Integration Support**: Slack, Email, Discord, Teams, and database connectors
- **Performance Analytics**: Task duration tracking, success rates, and custom metrics
- **Automated Reporting**: Daily, weekly, and monthly consultation reports

### Google ADK Integration
- **Advanced LLM Capabilities**: Leverages Gemini 2.5 Flash for intelligent responses
- **Tool Integration**: Seamless integration with custom business tools
- **Session Management**: Sophisticated conversation and context handling
- **Web Interface**: Clean, professional interface for consultations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google API key (for Gemini model)
- Perplexity API key (for real-time web search)
- BMasterAI framework installed

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/ai-consultant-bmasterai.git
   cd ai-consultant-bmasterai
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Required
   export GOOGLE_API_KEY=your-google-api-key
   export PERPLEXITY_API_KEY=your-perplexity-api-key
   
   # Optional integrations
   export SLACK_WEBHOOK_URL=your-slack-webhook
   export EMAIL_USERNAME=your-email@gmail.com
   export EMAIL_PASSWORD=your-app-password
   export SMTP_SERVER=smtp.gmail.com
   export SMTP_PORT=587
   ```

4. **Initialize the project**:
   ```bash
   # Create necessary directories
   mkdir -p logs data backups
   
   # Initialize BMasterAI
   bmasterai init ai-consultant-project
   ```

5. **Start the agent**:
   ```bash
   python ai_consultant_agent_bmasterai.py
   ```

6. **Launch the web interface**:
   ```bash
   adk web
   ```

7. **Access the interface**:
   - Open your browser and navigate to `http://localhost:8000`
   - Select "AI Business Consultant" from available agents

## 📊 Usage Examples

### Basic Consultation
```python
from ai_consultant_agent_bmasterai import get_consultant_agent

# Get the agent instance
agent = get_consultant_agent()

# Start the agent
agent.start()

# Execute a consultation
result = agent.execute_consultation(
    "I want to launch a SaaS startup for small businesses in the accounting space"
)

print(f"Consultation ID: {result['consultation_id']}")
print(f"Response: {result['response']}")
print(f"Duration: {result['duration_ms']}ms")
```

### Advanced Consultation with Context
```python
result = agent.execute_consultation(
    query="Should I expand my retail business to e-commerce?",
    context={
        "industry": "retail",
        "current_revenue": "$2M",
        "team_size": 25,
        "location": "United States"
    }
)
```

### Getting Performance Dashboard
```python
dashboard = agent.get_agent_dashboard()
print(f"Success Rate: {dashboard['performance']['success_rate']}%")
print(f"Average Response Time: {dashboard['performance']['avg_response_time']}ms")
```

### Generating Reports
```python
report = agent.generate_consultation_report(time_period="24h")
print(f"Total Consultations: {report['consultation_metrics']['total_consultations']}")
print(f"Success Rate: {report['consultation_metrics']['success_rate']}%")
```

## 🔧 Configuration

The agent can be configured through the `config.yaml` file:

```yaml
# Core settings
app:
  name: "ai_consultant_agent_bmasterai"
  version: "1.0.0"

# Google ADK settings
google_adk:
  model: "gemini-2.5-flash"
  timeout: 30

# Monitoring settings
monitoring:
  enabled: true
  collection_interval: 30

# Integration settings
integrations:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
  email:
    enabled: true
    smtp_server: "${SMTP_SERVER}"
```

## 📈 Monitoring and Alerting

### Built-in Metrics
- **Consultation Metrics**: Success rate, response time, volume
- **System Metrics**: CPU usage, memory usage, disk space
- **Performance Metrics**: Tool execution time, error rates
- **Custom Metrics**: Business-specific KPIs

### Alert Rules
- **High Error Rate**: Triggers when error rate exceeds threshold
- **Slow Response Time**: Alerts on performance degradation
- **High Volume**: Notifications for unusual consultation volume
- **System Health**: Alerts for resource utilization issues

### Reporting
- **Daily Reports**: Comprehensive daily performance summaries
- **Weekly Reports**: Trend analysis and insights
- **Monthly Reports**: Strategic performance review
- **Real-time Dashboards**: Live system monitoring

## 🛠️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (ADK)                     │
├─────────────────────────────────────────────────────────────┤
│               BMasterAI Consultant Agent                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Google ADK    │  │   BMasterAI     │  │ Perplexity  │ │
│  │   (LLM Core)    │  │  (Monitoring)   │  │  (Search)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────