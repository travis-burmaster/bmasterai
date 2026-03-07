# A2A Real Estate Multi-Agent — BMasterAI Edition

A **BMasterAI** adaptation of the AWS Labs
[A2A Real Estate AgentCore sample](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/A2A-realestate-agentcore-multiagents).

## Architecture

```
User / AgentCore Runtime
        │
        ▼
Real Estate Coordinator (realestate_coordinator/agent.py)
   ├─ search_properties ──► Property Search Agent  (port 5002)
   │                              └─ search_properties tool
   │                              └─ get_property_details tool
   └─ book_property ──────► Property Booking Agent (port 5001)
   └─ check_booking ──────►        └─ create_booking tool
                                   └─ check_booking_status tool
                                   └─ cancel_booking tool
                                   └─ list_customer_bookings tool
```

All three agents use:
- **[Strands Agents](https://github.com/strands-agents/sdk-python)** for tool-calling and LLM
- **A2A protocol** for inter-agent communication
- **BMasterAI** for structured telemetry (JSON logs + console)

## Key Differences from the AWS Sample

| AWS Sample | This Example |
|---|---|
| `common.utils.logging_config` (custom logger) | `bmasterai.logging` (structured telemetry) |
| `setup_logging()` + `log_tool_execution()` + `log_error()` | `bm.log_event(EventType.TOOL_USE / TASK_COMPLETE / TASK_ERROR)` |
| Separate `common/` module shared via `sys.path` | Each agent is self-contained |
| AgentCore deployment scripts included | Deployment left to `bedrock-agentcore-starter-toolkit` |

## Quick Start (Local)

```bash
# Install deps for all three agents
pip install -r propertysearchagent/requirements.txt
pip install -r propertybookingagent/requirements.txt
pip install -r realestate_coordinator/requirements.txt

# Start everything (sub-agents + coordinator REPL)
python run_local.py
```

Or start agents individually in separate terminals:

```bash
# Terminal 1 — Booking Agent
AGENT_PORT=5001 python propertybookingagent/agent.py

# Terminal 2 — Search Agent
AGENT_PORT=5002 python propertysearchagent/agent.py

# Terminal 3 — Coordinator (interactive REPL)
PROPERTY_SEARCH_AGENT_URL=http://localhost:5002 \
PROPERTY_BOOKING_AGENT_URL=http://localhost:5001 \
python realestate_coordinator/agent.py
```

## Example Queries

```
Find me a 2-bedroom apartment in New York under $4000/month

Book PROP001 for Jane Doe, email jane@example.com, phone 555-1234, move-in 2025-09-01

Check the status of booking BOOK-ABC12345

List all bookings for jane@example.com

Cancel booking BOOK-ABC12345 because I found a better option
```

## AgentCore Deployment

Each agent directory contains everything needed to deploy to Amazon Bedrock AgentCore:

1. **Sub-agents** (`propertysearchagent/`, `propertybookingagent/`) — deploy as A2A servers
2. **Coordinator** — deploy with `--agentcore` flag or use `create_agentcore_app()` directly

Set the following environment variables on the coordinator:
- `PROPERTY_SEARCH_AGENT_URL` — AgentCore runtime URL of the search agent
- `PROPERTY_BOOKING_AGENT_URL` — AgentCore runtime URL of the booking agent
- `MODEL_ID` — Bedrock model ID (default: `us.anthropic.claude-3-5-haiku-20241022-v1:0`)

The coordinator automatically forwards the incoming `Authorization` header to sub-agents
when running inside AgentCore Runtime (`BedrockAgentCoreContext`).

## BMasterAI Telemetry

Every tool call emits structured events:

```python
bm.log_event(
    agent_id=AGENT_ID,
    event_type=EventType.TOOL_USE,        # or TASK_COMPLETE / TASK_ERROR
    message="Tool: search_properties",
    metadata={"location": "New York", "max_price": 4000},
    duration_ms=45.2,
)
```

Logs are written to:
- Console (human-readable)
- `logs/bmasterai.jsonl` (structured JSON for downstream processing)
