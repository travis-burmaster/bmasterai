# OpenClaw Telemetry - Quick Start

Get real-time observability for your OpenClaw AI agent in 3 minutes.

## Prerequisites

- OpenClaw installed and running ([openclaw.ai](https://openclaw.ai))
- Python 3.8+
- Some OpenClaw sessions (have at least one conversation)

## Installation

### 1. Clone BMasterAI

```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai/examples/openclaw-telemetry
```

### 2. Run the Dashboard

```bash
chmod +x start.sh
./start.sh
```

That's it! The dashboard will open at **http://localhost:8501**

## What You'll See

### Overview Metrics (Top Row)

- **Total Sessions** - Number of OpenClaw conversations + cron jobs
- **Total Messages** - LLM API calls made
- **Total Tokens** - Input + output tokens used
- **Total Cost** - API costs across all models

### Token Breakdown

- **Input Tokens** - Your prompts and system context
- **Output Tokens** - AI responses
- **Cache Read** - Reused context (saves ~90% cost!)
- **Cache Write** - New context being cached

### Usage Over Time Chart

Shows your message volume and costs by hour/day/week. Use the sidebar to filter by:
- All Time
- Today
- Last 7 Days
- Last 30 Days

### Tool Usage Chart

Bar chart showing which OpenClaw tools you use most:
- web_search
- exec
- Read/Write
- browser
- etc.

### Model Breakdown Table

Shows which AI models you're using and their costs:
- Model name (e.g., claude-sonnet-4-5)
- Provider (anthropic, openai, etc.)
- Session count
- Token usage
- Total cost

### Recent Sessions Table

Last 20 sessions with:
- Session ID
- Start time
- Model used
- Messages sent
- Tools called
- Total tokens
- Cost

Includes your direct chats AND background cron jobs!

### Exec Command History

**NEW!** The dashboard includes a 5th tab: **⚡ Exec History**

This lets you drill down into every bash command OpenClaw has executed:

- **Full command history** - See all `exec` tool calls with complete commands
- **Search/filter** - Type "git", "grep", "cd", etc. to filter commands
- **Statistics** - Total commands, most common command, unique sessions
- **Top 10 chart** - Bar chart of most frequently used commands
- **Configurable limit** - Show 50, 100, 200, or 500 recent commands

**Why this matters:**
- **Debug automation** - See exactly what commands your agent ran
- **Security audit** - Review all system-level operations
- **Pattern analysis** - Identify most-used commands and workflows
- **Troubleshooting** - Trace command history when something goes wrong

**How to access:**
1. Open the dashboard (http://localhost:8501)
2. Click the **⚡ Exec History** tab
3. Browse all commands or use the search box to filter

**Example use cases:**
- "Show me all git commands" → Type "git" in search
- "What files did I read recently?" → Filter for "cat" or "head"
- "Debug a failed cron job" → Filter by session ID

This is perfect for understanding your agent's automation patterns and ensuring it's executing commands as expected!

## Understanding Costs

### Typical OpenClaw Usage

- **Light usage** (few conversations/day): $1-5/month
- **Moderate usage** (active conversations + some cron jobs): $10-30/month
- **Heavy usage** (many cron jobs, long contexts): $50-100/month

### Cache Optimization

Look at your "Cache Read" tokens. High cache reads = saving money!

OpenClaw caches files like:
- AGENTS.md
- SOUL.md
- USER.md
- Long conversation contexts

Instead of sending these every time (~$3 per million tokens), cache reads cost ~$0.30 per million tokens (10x cheaper).

## Updating Data

The dashboard refreshes automatically when you:

1. **Enable Auto-refresh** - Check "Auto-refresh (30s)" in sidebar
2. **Manual refresh** - Click "🔄 Refresh Now"
3. **Re-parse sessions** - Run `python session_parser.py`

## Common Questions

### Q: Do I need to run this constantly?

No! Run it when you want to check costs or analyze usage. Close it when done.

### Q: Will this slow down OpenClaw?

No. The parser reads session files after they're created. Zero impact on OpenClaw performance.

### Q: Can I track multiple OpenClaw instances?

Yes! Edit `session_parser.py` and point to different session directories. Or parse multiple directories into separate databases.

### Q: How do I reduce costs?

1. **Optimize prompts** - Shorter, clearer prompts = fewer input tokens
2. **Use cache effectively** - Keep stable files in workspace for caching
3. **Choose right models** - Use faster/cheaper models for simple tasks
4. **Monitor cron jobs** - They can consume lots of tokens if running frequently

### Q: Where's the data stored?

`openclaw_telemetry.db` - A SQLite database in the example directory. Safe to delete and re-parse anytime.

## Advanced: Auto-Parse New Sessions

Set up hourly auto-parsing with cron:

```bash
crontab -e
```

Add:
```cron
0 * * * * cd /path/to/bmasterai/examples/openclaw-telemetry && python3 session_parser.py > /dev/null 2>&1
```

Now the dashboard always has fresh data!

## Troubleshooting

### "Database not found"

Run the parser first:
```bash
python session_parser.py
```

### No data showing

Make sure you have OpenClaw sessions:
```bash
ls ~/.openclaw/agents/main/sessions/
```

Should show `*.jsonl` files. If empty, have a conversation with OpenClaw first.

### Port 8501 in use

Run on a different port:
```bash
streamlit run dashboard.py --server.port 8502
```

## Next Steps

- Check out the full [README.md](README.md) for advanced features
- Explore session-level cost breakdowns
- Set up production deployment with systemd/nginx
- Integrate with BMasterAI's Prometheus/Grafana stack

## Feedback

Questions or issues?
- [OpenClaw Discord](https://discord.gg/clawd)
- [BMasterAI GitHub Issues](https://github.com/travis-burmaster/bmasterai/issues)

---

**Happy monitoring!** 🔍
