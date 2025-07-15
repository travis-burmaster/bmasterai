# Command Line Interface (CLI) Overview

BMasterAI includes a powerful command-line interface that makes it easy to manage projects, monitor systems, and perform administrative tasks.

## 🚀 Installation & Access

The CLI is automatically available after installing BMasterAI:

```bash
pip install bmasterai
bmasterai --help
```

## 📋 Available Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Initialize a new BMasterAI project | `bmasterai init my-project` |
| `status` | Show system status and metrics | `bmasterai status` |
| `monitor` | Start real-time monitoring | `bmasterai monitor` |
| `test-integrations` | Test all configured integrations | `bmasterai test-integrations` |

### Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `--config`, `-c` | Specify configuration file | `bmasterai -c config.yaml status` |
| `--help`, `-h` | Show help information | `bmasterai --help` |

## 🎯 Command Details

### `bmasterai init`

Initialize a new BMasterAI project with proper structure and templates.

```bash
bmasterai init <project-name>
```

**What it creates:**
```
my-project/
├── agents/my_agent.py      # Working agent template
├── config/config.yaml      # Configuration file
└── logs/                   # Log directory
```

**Features:**
- ✅ **Working Code**: Generated agent runs immediately
- ✅ **Correct Imports**: Uses proper BMasterAI import statements
- ✅ **Full Integration**: Logging, monitoring, and error handling
- ✅ **Best Practices**: Follows BMasterAI patterns and conventions

**Example:**
```bash
bmasterai init customer-support-ai
cd customer-support-ai
python agents/my_agent.py
```

### `bmasterai status`

Display comprehensive system status and metrics.

```bash
bmasterai status
```

**Output includes:**
- 🖥️ **System Status**: Current timestamp and overall health
- 📊 **System Metrics**: CPU, memory, and disk usage
- 🤖 **Agent Information**: Active and total agent counts
- 🔗 **Integrations**: Status of connected services
- 🚨 **Recent Alerts**: Latest system alerts and warnings

**Example output:**
```
🖥️  BMasterAI System Status
========================================
Timestamp: 2025-01-15T10:30:45.123456
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

### `bmasterai monitor`

Start continuous real-time system monitoring.

```bash
bmasterai monitor
```

**Features:**
- 📊 **Real-time Metrics**: Live system performance data
- 🤖 **Agent Monitoring**: Track agent status and performance
- 📈 **Performance Tracking**: CPU, memory, and custom metrics
- 🔄 **Auto-refresh**: Updates every few seconds
- ⌨️ **Interactive**: Press Ctrl+C to stop

**Example output:**
```
🔍 Starting BMasterAI monitoring...
✅ Monitoring started
📊 System metrics being collected every 30 seconds

💻 CPU: 45.1% | 🧠 Memory: 67.8% | 🤖 Agents: 3
```

### `bmasterai test-integrations`

Test all configured integrations to verify connectivity.

```bash
bmasterai test-integrations
```

**What it tests:**
- 📧 **Email**: SMTP connection and authentication
- 💬 **Slack**: Webhook URL and message sending
- 🎮 **Discord**: Webhook connectivity
- 🗄️ **Database**: Connection and basic operations
- 🌐 **Custom**: Any custom integrations

**Example output:**
```
🧪 Testing integrations...
✅ slack: Connection successful
✅ email: SMTP connection verified
❌ discord: Webhook URL not configured
✅ database: SQLite connection active
```

## ⚙️ Configuration

### Using Configuration Files

Specify custom configuration files:

```bash
# Use specific config file
bmasterai --config production.yaml status

# Short form
bmasterai -c dev.yaml monitor
```

### Configuration File Format

```yaml
# config.yaml
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
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
  
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "${EMAIL_USERNAME}"
    password: "${EMAIL_PASSWORD}"
```

## 🔧 Environment Variables

Configure CLI behavior with environment variables:

```bash
# Logging configuration
export BMASTERAI_LOG_LEVEL=INFO
export BMASTERAI_LOG_FILE=bmasterai.log

# Integration settings
export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
export EMAIL_USERNAME=your-email@gmail.com
export EMAIL_PASSWORD=your-app-password

# Monitoring settings
export BMASTERAI_MONITOR_INTERVAL=30
```

## 📊 Practical Usage Examples

### Development Workflow

```bash
# 1. Create new project
bmasterai init my-ai-app
cd my-ai-app

# 2. Start monitoring in background
bmasterai monitor &

# 3. Develop and test your agents
python agents/my_agent.py

# 4. Check system status
bmasterai status

# 5. Test integrations
bmasterai test-integrations
```

### Production Monitoring

```bash
# Check system health
bmasterai status

# Start monitoring daemon
nohup bmasterai monitor > monitor.log 2>&1 &

# Test all integrations
bmasterai test-integrations

# Use production config
bmasterai --config production.yaml status
```

### Troubleshooting

```bash
# Check system status with detailed config
bmasterai --config debug.yaml status

# Test specific integration
bmasterai test-integrations

# Monitor system in real-time
bmasterai monitor
```

## 🎨 Customization

### Custom Configuration Locations

The CLI looks for configuration files in this order:

1. **Command line**: `--config specified-file.yaml`
2. **Current directory**: `./config.yaml`
3. **Project config**: `./config/config.yaml`
4. **User config**: `~/.bmasterai/config.yaml`
5. **System config**: `/etc/bmasterai/config.yaml`

### Environment Variable Override

Any configuration can be overridden with environment variables:

```bash
# Override log level
export BMASTERAI_LOG_LEVEL=DEBUG
bmasterai status

# Override monitoring interval
export BMASTERAI_MONITOR_INTERVAL=10
bmasterai monitor
```

## 🔍 Advanced Usage

### Scripting and Automation

```bash
#!/bin/bash
# health-check.sh

# Check system status
if bmasterai status > /dev/null 2>&1; then
    echo "✅ BMasterAI system healthy"
    exit 0
else
    echo "❌ BMasterAI system issues detected"
    bmasterai status
    exit 1
fi
```

### Integration with CI/CD

```yaml
# .github/workflows/bmasterai-check.yml
name: BMasterAI Health Check

on: [push, pull_request]

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install BMasterAI
        run: pip install bmasterai
      - name: Test integrations
        run: bmasterai test-integrations
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Monitoring Scripts

```bash
#!/bin/bash
# monitor-alerts.sh

# Check for high CPU usage
CPU_USAGE=$(bmasterai status | grep "CPU Usage" | awk '{print $3}' | sed 's/%//')
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "⚠️ High CPU usage: ${CPU_USAGE}%"
    # Send alert
fi

# Check for failed integrations
if ! bmasterai test-integrations | grep -q "All tests passed"; then
    echo "⚠️ Integration failures detected"
    bmasterai test-integrations
fi
```

## 🆘 Troubleshooting

### Common Issues

#### Command Not Found
```bash
# If bmasterai command is not found
pip install --upgrade bmasterai

# Or check if it's in PATH
which bmasterai
echo $PATH
```

#### Permission Errors
```bash
# If you get permission errors
sudo chown -R $USER ~/.bmasterai/
chmod 755 ~/.bmasterai/
```

#### Configuration Issues
```bash
# Validate configuration
bmasterai --config config.yaml status

# Check configuration file syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Set debug environment variable
export BMASTERAI_DEBUG=true
bmasterai status

# Or use verbose logging
export BMASTERAI_LOG_LEVEL=DEBUG
bmasterai monitor
```

## 🎯 Next Steps

### Learn More
- **[Project Management](project-management.md)** - Advanced project management
- **[System Monitoring](monitoring.md)** - Detailed monitoring guide
- **[Configuration Guide](../configuration.md)** - Complete configuration reference

### Integration
- **[Slack Integration](../integrations/slack.md)** - Set up Slack notifications
- **[Email Integration](../integrations/email.md)** - Configure email alerts
- **[Custom Integrations](../integrations/custom.md)** - Build custom integrations

---

*Master the BMasterAI CLI for efficient development and operations! 🚀*