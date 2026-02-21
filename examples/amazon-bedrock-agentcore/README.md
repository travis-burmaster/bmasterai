# BMasterAI + Amazon Bedrock AgentCore — Cost Optimization Agent

A **Strands agent** that monitors AWS spend, detects anomalies, forecasts costs,
and analyzes service-level breakdowns — with **bmasterai structured telemetry**
logged on every agent action.

Inspired by [awslabs/amazon-bedrock-agentcore-samples #695](https://github.com/awslabs/amazon-bedrock-agentcore-samples/pull/695).

---

## Features

| # | Feature | Tool | AWS API |
|---|---|---|---|
| 1 | **Cost Anomaly Detection** | `analyze_cost_anomalies(days)` | Cost Anomaly Detection |
| 2 | **Budget Monitoring** | `get_budget_information(name)` | AWS Budgets |
| 3 | **Cost Forecasting** | `forecast_future_costs(days_ahead)` | Cost Explorer Forecast |
| 4 | **Service Breakdown** | `get_service_cost_breakdown(service, period)` | Cost Explorer |
| 5 | **Current Spending** | `get_current_month_costs()` | Cost Explorer + Burn Rate |

BMasterAI logs every `AGENT_START`, `TASK_START`, `LLM_CALL`, `TOOL_USE`, and `TASK_COMPLETE` event to structured JSONL — ready for CloudWatch Insights, Datadog, or any log aggregator.

---

## Architecture

```
User (FinOps)
     │ Query
     ▼
Amazon Bedrock AgentCore Runtime
     │ Request
     ▼
Strands AI Agent ◄──────────────► Amazon Bedrock (LLM reasoning)
     │                              Tool Selection ◄──────────────┘
     │ Request
     ▼
┌─────────────────────────────────────────────────────┐
│  Agent Tools                                        │
│                                                     │
│  [Budget Status]  [Anomaly Detection]               │
│  [Cost Forecast]  [Service Breakdown]  [MTD Costs]  │
└──────────────┬──────────────┬──────────────────────┘
               │              │
        ┌──────┴──────┐  ┌────┴──────────────┐
        │ AWS Budgets │  │ Amazon CloudWatch  │
        └─────────────┘  │ AWS Cost Explorer  │
                         └───────────────────┘

📊 BMasterAI telemetry → logs/bmasterai.jsonl → CloudWatch Logs
```

---

## Quick Start

```bash
# Install deps
uv sync

# Configure AWS credentials
aws configure   # or export AWS_PROFILE=...

# Test tools locally (no LLM call)
uv run python test_local.py --tools-only

# Full local agent test (calls Bedrock)
uv run python test_local.py

# Deploy to AgentCore
uv run python deploy.py
```

---

## BMasterAI Telemetry

Every agent event is captured as structured JSONL:

```jsonl
{"event_type": "agent_start",   "message": "BMasterAI Cost Optimization Agent starting..."}
{"event_type": "task_start",    "message": "Task received: 'Show me cost anomalies...'"}
{"event_type": "llm_call",      "message": "Invoking Strands agent", "metadata": {...}}
{"event_type": "tool_use",      "message": "Tool: analyze_cost_anomalies", "metadata": {"days": 7}}
{"event_type": "task_complete", "message": "analyze_cost_anomalies completed in 842ms", "duration_ms": 842}
{"event_type": "task_complete", "message": "Task completed in 3214ms", "duration_ms": 3214}
```

Logs written to:
- `logs/bmasterai.log` — human-readable
- `logs/bmasterai.jsonl` — structured JSONL for aggregators

After deployment, logs also stream to CloudWatch:
```bash
AGENT_ID=$(cat .agent_arn | awk -F/ '{print $NF}')
aws logs tail /aws/bedrock-agentcore/runtimes/${AGENT_ID}-DEFAULT --follow
```

---

## Project Structure

```
amazon-bedrock-agentcore/
├── agent.py              # AgentCore entry point — 5 @tool wrappers + bmasterai telemetry
├── deploy.py             # Automated deploy: IAM → Memory → ECR → Runtime
├── cleanup.py            # Tear down all AWS resources
├── test_local.py         # Tool unit tests + agent test (no deploy needed)
├── tools/
│   ├── cost_explorer_tools.py  # get_cost_and_usage, forecast, anomalies, service breakdown
│   └── budget_tools.py         # get_all_budgets, get_budget_status, calculate_burn_rate
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Example Queries

```
"Show me any cost anomalies in the last 7 days"
"Are any of my budgets at risk of being exceeded?"
"Forecast my AWS spend for the next 30 days"
"What are my top 10 most expensive services this month?"
"What's my current month-to-date spend and daily burn rate?"
```

---

## Related

- [awslabs/amazon-bedrock-agentcore-samples #695](https://github.com/awslabs/amazon-bedrock-agentcore-samples/pull/695) — original cost optimization agent (no bmasterai)
- [google-adk-a2a/](../google-adk-a2a/) — A2A agent patterns with Google ADK
- [ai-stock-research-agent/](../ai-stock-research-agent/) — domain-specific research agent
