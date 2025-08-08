## Agno + BMasterAI Telemetry Example

This example demonstrates the powerful integration between the [Agno](https://github.com/agno-ai/agno) agent framework and BMasterAI's comprehensive telemetry system. It shows how to build production-ready AI agents with full observability from day one.

### Why This Example is Important

This integration represents a critical advancement in AI agent development by solving the **observability gap** that plagues most AI applications in production. Here's why this matters:

#### **Production Readiness**

- **Real-world deployment** – Most AI demos work in isolation but fail in production due to lack of monitoring
- **Cost control** – Without telemetry, AI applications can quickly become expensive black boxes
- **Performance optimization** – You can't improve what you can't measure

#### **Enterprise Requirements**

- **Compliance & auditing** – Enterprise deployments require detailed logs of AI interactions
- **SLA monitoring** – Track response times, error rates, and availability metrics
- **Budget management** – Monitor token usage and costs across different models and use cases

#### **Developer Experience**

- **Debugging made easy** – Rich telemetry helps identify issues before they impact users
- **Performance insights** – Understand which prompts work best and optimize accordingly
- **Proactive alerting** – Get notified when things go wrong, not after users complain

### What Makes This Integration Powerful

- **Native Agno agent** – Uses the high-level `Agent` interface to interact with Gemini
- **Zero-overhead observability** – BMasterAI logging and monitoring capture agent lifecycle events, token usage, and latency metrics automatically
- **Smart alerting** – Token budgets can trigger Slack or Teams alerts via `bmasterai_telemetry`
- **Minimal setup** – A single script demonstrates enterprise-grade AI agent monitoring
- **Framework agnostic** – The patterns shown here work with any AI framework, not just Agno

### Requirements

- Python 3.10+
- Environment variable `GOOGLE_API_KEY` containing a valid Gemini API key.
- (Optional) `BMASTERAI_ALERTS_SLACK_WEBHOOK` and/or `BMASTERAI_ALERTS_TEAMS_WEBHOOK`
  for alert delivery.
- Install dependencies:

```bash
pip install agno google-generativeai bmasterai
```

### Run

```bash
export GOOGLE_API_KEY=your-key
./run_example.sh
```

Or manually:

```bash
PYTHONPATH=../.. ../../venv/bin/python gemini_agno_example.py
```

Set `TOKEN_BUDGET` to enable alerting when the token usage exceeds the limit. The script
prints the Gemini response and records structured telemetry in logs and metrics files,
sending optional alerts when budgets are breached.

### What You'll See

When you run this example, you'll observe:

1. **Agent lifecycle tracking** – Start/stop events with timestamps
2. **LLM call metrics** – Token usage, response times, model information
3. **Structured logging** – JSON-formatted logs ready for analysis
4. **Cost monitoring** – Track spending across different models and use cases
5. **Alert integration** – Optional Slack/Teams notifications for budget overruns

This gives you the foundation for building AI agents that are ready for production deployment with full observability from day one.
