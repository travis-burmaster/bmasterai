# OpenClaw Telemetry Integration

Real-time observability dashboard for [OpenClaw](https://openclaw.ai) AI agent sessions, featuring LLM usage tracking, token analysis, cost monitoring, and tool analytics.

This example demonstrates how to integrate BMasterAI telemetry concepts with OpenClaw's session data to provide production-grade observability for AI agent deployments.

## What is OpenClaw?

[OpenClaw](https://openclaw.ai) is a personal AI agent framework that runs locally and integrates with messaging platforms (Telegram, WhatsApp, Discord, etc.). It provides:

- **Multi-session agent orchestration** - Main sessions, isolated agents, cron jobs, sub-agents
- **Tool integration** - Browser automation, file operations, web search, code execution
- **Memory management** - Long-term and short-term context retention
- **Production features** - Scheduled tasks, background jobs, cross-session messaging

OpenClaw sessions generate structured JSONL logs containing detailed telemetry data - perfect for BMasterAI-style observability.

## Why This Integration?

OpenClaw users often run:
- **Continuous background agents** - Hourly task reviews, daily briefings, market monitoring
- **Multi-model workflows** - Different models for different tasks (reasoning vs speed)
- **High-volume automation** - Cron jobs generating thousands of tokens daily

Without observability, costs can spiral and performance issues go unnoticed. This integration provides:

✅ **Real-time cost tracking** across all sessions and models  
✅ **Token usage analytics** with cache optimization insights  
✅ **Tool usage patterns** to identify bottlenecks  
✅ **Timeline visualization** of agent activity  
✅ **Session-level breakdowns** for debugging expensive runs  

## Features

### 📊 Comprehensive Metrics

- **Overview Dashboard**
  - Total sessions, messages, tool calls
  - Aggregate token counts (input, output, cache read/write)
  - Total API costs across all models
  
- **Timeline Visualization**
  - Usage patterns over time (hourly, daily, monthly)
  - Cost trends and spikes
  - Message volume tracking

- **Model Analytics**
  - Per-model cost breakdown
  - Token distribution by provider
  - Session count by model
  - Cost distribution pie charts

- **Tool Usage Tracking**
  - Most frequently used tools
  - Tool call patterns
  - Performance insights

- **Session History**
  - Recent session details
  - Per-session token and cost data
  - Cron job and sub-agent tracking

### 🚨 BMasterAI Integration (Requires bmasterai>=0.2.3)

- **Alert System**
  - Real-time notifications for cost/token thresholds
  - Color-coded severity levels (info, warning, critical)
  - Alert rules: high session cost (>$1), high token usage (>100k)
  
- **Custom Metrics**
  - Session cost statistics (mean, max, percentiles)
  - Token efficiency tracking (tokens per dollar)
  - Cache hit rate monitoring
  - Time-windowed metric aggregation (15min to 24hr)

- **Enterprise Observability**
  - Structured logging with JSON format
  - Performance monitoring with custom metrics
  - Alert rule configuration
  - Graceful degradation (works with bmasterai 0.2.0+, full metrics require 0.2.3+)

### 🎯 Time Filtering

- **All Time** - Complete historical data
- **Today** - Last 24 hours
- **Last 7 Days** - Weekly view
- **Last 30 Days** - Monthly view

### 🔄 Auto-Refresh

- Real-time monitoring during active sessions
- 30-second refresh interval
- Manual refresh on demand

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Main Session │  │  Cron Jobs   │  │  Sub-Agents  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                            │                             │
└────────────────────────────┼─────────────────────────────┘
                             │
                    Session JSONL Files
              ~/.openclaw/agents/main/sessions/*.jsonl
                             │
                             ▼
                   ┌──────────────────┐
                   │ Session Parser   │
                   │  (session_parser.py) │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   SQLite DB      │
                   │ openclaw_telemetry.db │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │ Streamlit Dashboard │
                   │   (dashboard.py)   │
                   └────────┬─────────┘
                            │
                            ▼
                   Web UI (localhost:8501)
                   Real-time Observability
```

### Data Flow

1. **OpenClaw generates session JSONL files** during agent execution
2. **Session Parser** reads JSONL, extracts telemetry (tokens, costs, tools)
3. **SQLite Database** stores structured metrics for fast queries
4. **Streamlit Dashboard** provides interactive web UI for visualization
5. **Auto-refresh** keeps data current during active agent sessions

## Prerequisites

### OpenClaw Setup

Install OpenClaw first:
```bash
npm install -g openclaw
openclaw gateway start
```

See [OpenClaw documentation](https://docs.openclaw.ai) for full setup.

### Python Environment

- Python 3.8+
- pip or pip3

## Quick Start

### 1. Clone BMasterAI

```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai/examples/openclaw-telemetry
```

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Session Directory

Edit `session_parser.py` to point to your OpenClaw sessions directory:

```python
# Default OpenClaw sessions directory
sessions_dir = "/home/tadmin/.openclaw/agents/main/sessions"

# Or use environment variable
import os
sessions_dir = os.getenv("OPENCLAW_SESSIONS_DIR", "/home/tadmin/.openclaw/agents/main/sessions")
```

### 4. Parse OpenClaw Sessions

```bash
python session_parser.py
```

Output:
```
Scanning sessions in /home/tadmin/.openclaw/agents/main/sessions...
Processing 1/26: 741ef758-4cf0-454e-91bf-6094594efad5.jsonl
Processing 2/26: 3f27bc67-0933-47e7-a199-73743ff295f3.jsonl
...
✅ Processed 26 sessions
```

### 5. Launch Dashboard

**Option A: Basic Dashboard** (lightweight, no bmasterai dependency)
```bash
streamlit run dashboard.py
```

**Option B: Enhanced Dashboard** (with bmasterai metrics & alerts)
```bash
streamlit run dashboard_enhanced.py
```

Dashboard opens at: **http://localhost:8501**

The enhanced dashboard adds:
- ⚠️ Real-time alert notifications for cost/token thresholds
- 📈 BMasterAI custom metrics (session cost, tokens, cache hit rate, efficiency)
- 📊 Time-windowed metric statistics (15min, 1hr, 24hr)
- 🔔 Alert rule visualization

### 6. (Optional) Use Launch Script

```bash
chmod +x start.sh
./start.sh
```

The script handles venv creation, dependency installation, session parsing, and dashboard launch.

## Requirements

Create `requirements.txt`:

```
streamlit==1.31.0
pandas==2.2.0
plotly==5.18.0
watchdog==4.0.0
sqlalchemy==2.0.25
```

## Database Schema

### `sessions` Table

| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT | Unique session identifier |
| start_time | TEXT | ISO timestamp of session start |
| end_time | TEXT | ISO timestamp of last message |
| model | TEXT | LLM model used (e.g., claude-sonnet-4-5) |
| provider | TEXT | Model provider (anthropic, openai, etc.) |
| thinking_level | TEXT | Reasoning mode (low, medium, high) |
| total_messages | INTEGER | Number of LLM API calls |
| total_tool_calls | INTEGER | Number of tool invocations |
| total_input_tokens | INTEGER | Sum of input tokens |
| total_output_tokens | INTEGER | Sum of output tokens |
| total_cache_read_tokens | INTEGER | Sum of cache read tokens |
| total_cache_write_tokens | INTEGER | Sum of cache write tokens |
| total_cost | REAL | Total API cost ($USD) |

### `messages` Table

Per-message telemetry for detailed analysis:

- Message ID, timestamp, role
- Model and provider
- Token breakdown (input, output, cache)
- Cost per message
- Stop reason

### `tool_calls` Table

Tool invocation tracking:

- Tool call ID and name
- Associated session and message
- Timestamp

## Usage Examples

### Monitor Daily Costs

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('openclaw_telemetry.db')

# Get today's costs by model
query = """
    SELECT 
        model,
        SUM(total_cost) as cost,
        SUM(total_input_tokens + total_output_tokens) as tokens
    FROM sessions
    WHERE date(start_time) = date('now')
    GROUP BY model
"""

df = pd.read_sql_query(query, conn)
print(df)
```

### Identify Expensive Sessions

```python
# Top 10 most expensive sessions
query = """
    SELECT 
        session_id,
        start_time,
        model,
        total_cost,
        total_messages,
        total_tool_calls
    FROM sessions
    ORDER BY total_cost DESC
    LIMIT 10
"""

df = pd.read_sql_query(query, conn)
print(df)
```

### Track Tool Usage Over Time

```python
query = """
    SELECT 
        date(timestamp) as day,
        tool_name,
        COUNT(*) as calls
    FROM tool_calls
    WHERE timestamp >= datetime('now', '-7 days')
    GROUP BY day, tool_name
    ORDER BY day DESC, calls DESC
"""

df = pd.read_sql_query(query, conn)
print(df)
```

## Production Deployment

### Automated Session Parsing

Set up a cron job to auto-parse new sessions:

```bash
crontab -e
```

Add:
```cron
# Parse OpenClaw sessions every hour
0 * * * * cd /path/to/bmasterai/examples/openclaw-telemetry && /path/to/.venv/bin/python session_parser.py >> /var/log/openclaw-parser.log 2>&1
```

### Dashboard as a Service

Run the dashboard as a systemd service:

```ini
# /etc/systemd/system/openclaw-telemetry.service
[Unit]
Description=OpenClaw Telemetry Dashboard
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/bmasterai/examples/openclaw-telemetry
ExecStart=/path/to/.venv/bin/streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable openclaw-telemetry
sudo systemctl start openclaw-telemetry
```

### Nginx Reverse Proxy

Expose the dashboard securely:

```nginx
server {
    listen 80;
    server_name telemetry.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Integration with BMasterAI Ecosystem

This example demonstrates BMasterAI telemetry patterns adapted for OpenClaw:

### From BMasterAI

- **Structured logging** - JSON-based session storage
- **Token tracking** - Granular input/output/cache metrics
- **Cost analysis** - Per-model and aggregate cost tracking
- **Observability patterns** - Real-time monitoring and visualization

### OpenClaw Additions

- **Multi-session types** - Main, isolated, cron, sub-agents
- **Tool call analytics** - OpenClaw-specific tool tracking
- **JSONL parsing** - Handles OpenClaw's session format
- **Cache optimization** - Tracks OpenClaw's prompt caching

### Scaling to Enterprise

For production deployments, extend with BMasterAI's full observability stack:

1. **Replace SQLite with PostgreSQL** for multi-user access
2. **Export metrics to Prometheus** using bmasterai_telemetry package
3. **Build Grafana dashboards** with bmasterai templates
4. **Add OpenTelemetry tracing** for distributed agent workflows
5. **Deploy to Kubernetes** with bmasterai Helm charts

See [BMasterAI Kubernetes Telemetry](../kubernetes-telemetry/) for enterprise patterns.

## Customization

### Custom Metrics

Add new metrics by extending `session_parser.py`:

```python
def calculate_thinking_cost(session_data):
    """Calculate cost for thinking tokens separately"""
    thinking_cost = 0.0
    for msg in session_data['messages']:
        # Extract thinking tokens from content
        # Calculate premium for reasoning mode
        pass
    return thinking_cost
```

### Dashboard Enhancements

Extend `dashboard.py` with new visualizations:

```python
def show_reasoning_analysis():
    """Show thinking mode usage and costs"""
    st.subheader("🧠 Reasoning Analysis")
    
    query = """
        SELECT 
            thinking_level,
            COUNT(*) as sessions,
            AVG(total_cost) as avg_cost
        FROM sessions
        WHERE thinking_level IS NOT NULL
        GROUP BY thinking_level
    """
    
    df = pd.read_sql_query(query, conn)
    
    fig = px.bar(df, x='thinking_level', y='avg_cost',
                 color='sessions', title='Average Cost by Thinking Level')
    st.plotly_chart(fig)
```

### Alert Thresholds

Add cost/token alerts:

```python
def check_alerts():
    """Alert on high costs or token usage"""
    conn = get_connection()
    
    # Check today's total cost
    query = """
        SELECT SUM(total_cost) as daily_cost
        FROM sessions
        WHERE date(start_time) = date('now')
    """
    
    daily_cost = pd.read_sql_query(query, conn).iloc[0]['daily_cost']
    
    if daily_cost > 10.0:  # $10 threshold
        st.warning(f"⚠️ Daily cost ${daily_cost:.2f} exceeds threshold!")
```

## Troubleshooting

### Database Not Found

**Symptom:** Dashboard shows "Database not found" error

**Solution:** Run session parser first:
```bash
python session_parser.py
```

### No Data Showing

**Symptom:** Dashboard loads but shows zero metrics

**Possible causes:**
1. OpenClaw hasn't created any sessions yet - have a conversation first
2. Session directory path is wrong - check `session_parser.py` configuration
3. Permissions issue - ensure read access to `~/.openclaw/agents/main/sessions/`

**Debug:**
```bash
ls -la ~/.openclaw/agents/main/sessions/
python session_parser.py  # Watch for errors
```

### Costs Show $0.00

**Symptom:** Sessions parse but costs are zero

**Possible causes:**
1. OpenClaw session didn't complete - incomplete JSONL files
2. Model doesn't embed cost data - older OpenClaw versions
3. Database schema mismatch

**Debug:**
```bash
# Check a session file for usage data
grep -i "usage" ~/.openclaw/agents/main/sessions/*.jsonl | head -5

# Verify database schema
sqlite3 openclaw_telemetry.db ".schema sessions"
```

### Port 8501 Already in Use

**Solution:** Run on different port:
```bash
streamlit run dashboard.py --server.port 8502
```

## Example Session Data

Here's what OpenClaw session JSONL looks like:

```json
{
  "type": "message",
  "id": "abc123",
  "timestamp": "2026-02-14T10:11:42.768Z",
  "message": {
    "role": "assistant",
    "model": "claude-sonnet-4-5",
    "provider": "anthropic",
    "usage": {
      "input": 500,
      "output": 1200,
      "cacheRead": 15000,
      "cacheWrite": 300,
      "totalTokens": 17000,
      "cost": {
        "input": 0.0015,
        "output": 0.018,
        "cacheRead": 0.0045,
        "cacheWrite": 0.00112,
        "total": 0.02512
      }
    },
    "content": [
      {"type": "text", "text": "..."},
      {"type": "toolCall", "name": "web_search", "id": "call_1"}
    ]
  }
}
```

The parser extracts:
- **Tokens**: 500 input, 1200 output, 15000 cache reads, 300 cache writes
- **Cost**: $0.02512 for this message
- **Tool calls**: web_search invoked
- **Metadata**: Model, provider, timestamp

## Performance

**Parsing Speed:**
- ~1000 sessions/second on typical hardware
- SQLite handles millions of messages efficiently
- Dashboard loads instantly with indexed queries

**Resource Usage:**
- Database: ~1MB per 100 sessions
- Dashboard: ~50MB RAM
- Parser: Negligible CPU during batch processing

## Roadmap

Planned enhancements:

- [ ] **Real-time webhook ingestion** - Parse sessions as they're created
- [ ] **Multi-agent comparison** - Compare different agent configurations
- [ ] **Session replay** - Debug sessions step-by-step
- [ ] **Cost forecasting** - Predict monthly costs from usage trends
- [ ] **Integration with bmasterai reasoning logs** - Combine telemetry with thought processes
- [ ] **Export to Prometheus** - Enterprise monitoring integration
- [ ] **Grafana dashboard templates** - Pre-built production dashboards

## Contributing

This integration is part of the BMasterAI examples collection. Contributions welcome!

### Development Setup

```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai/examples/openclaw-telemetry
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black *.py
flake8 *.py
```

## License

MIT - Same as BMasterAI

## Credits

- **OpenClaw** - [@openclaw](https://github.com/openclaw/openclaw)
- **BMasterAI** - [@travis-burmaster](https://github.com/travis-burmaster/bmasterai)
- **Streamlit** - Dashboard framework
- **Plotly** - Interactive charts

## Related Examples

- [Kubernetes Telemetry](../kubernetes-telemetry/) - Enterprise observability with Prometheus/Grafana
- [Agno Telemetry](../agno-telemetry/) - Agent telemetry patterns
- [Reasoning Logging](../reasoning_logging_example.py) - LLM reasoning capture

## Support

- **OpenClaw Discord:** [discord.gg/clawd](https://discord.gg/clawd)
- **OpenClaw Docs:** [docs.openclaw.ai](https://docs.openclaw.ai)
- **BMasterAI Issues:** [GitHub Issues](https://github.com/travis-burmaster/bmasterai/issues)
- **BMasterAI Discussions:** [GitHub Discussions](https://github.com/travis-burmaster/bmasterai/discussions)

---

**Built with BMasterAI telemetry patterns for OpenClaw users** 🐾
