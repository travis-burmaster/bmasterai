# BMasterAI + Amazon Bedrock AgentCore

Deploy a **BMasterAI Research Agent** to **Amazon Bedrock AgentCore Runtime** — AWS's fully managed infrastructure for production AI agents.

This example shows how to combine:
- **BMasterAI** — structured logging, monitoring, and telemetry for every agent event
- **Amazon Bedrock AgentCore** — managed container runtime, auto-scaling, native A2A support
- **Strands Agents** — LLM + tool orchestration framework

No Dockerfile. No manual ECR push. The starter toolkit handles container build and deployment automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Amazon Bedrock AgentCore Runtime          │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │              agent.py (entry point)          │  │
│  │                                              │  │
│  │   BedrockAgentCoreApp  ←→  Strands Agent    │  │
│  │          │                      │            │  │
│  │    @app.entrypoint        @tool functions    │  │
│  │          │                      │            │  │
│  │    BMasterAI Logger     Research Tools       │  │
│  │    BMasterAI Monitor    (search/analyze/     │  │
│  │    (JSONL telemetry)     fetch/summarize)    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  AgentCore Memory  │  CloudWatch Logs  │  X-Ray    │
└─────────────────────────────────────────────────────┘
```

**Request flow:**
1. Caller invokes the AgentCore Runtime endpoint (A2A or direct)
2. `@app.entrypoint` receives the payload and extracts the user message
3. BMasterAI logs `TASK_START` with full metadata
4. Strands Agent selects and calls the appropriate `@tool`
5. BMasterAI logs `TOOL_USE` → `TASK_COMPLETE` with duration
6. Response returned to caller; telemetry in JSONL + CloudWatch

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS credentials configured (`aws configure` or IAM role)
- Bedrock model access enabled in your AWS account:
  - `us.anthropic.claude-3-5-sonnet-20241022-v2:0` (or update `MODEL_ID`)

---

## Quick Start

### 1. Install dependencies
```bash
uv sync
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set AWS_REGION and optionally KNOWLEDGE_BASE_ID or BRAVE_API_KEY
```

### 3. Test locally (no deployment needed)
```bash
# Run tool unit tests only
uv run python test_local.py --tools-only

# Run a full agent query locally (calls Bedrock)
uv run python test_local.py --query "What are the key differences between EC2 and Lambda?"
```

### 4. Deploy to AgentCore
```bash
uv run python deploy.py
```

This will:
- Create an IAM execution role with the required permissions
- Provision AgentCore Memory (semantic + user preference strategies)
- Build a container image and push it to ECR automatically
- Launch the AgentCore Runtime and save the ARN to `.agent_arn`

### 5. Tail logs after deployment
```bash
AGENT_ID=$(cat .agent_arn | awk -F/ '{print $NF}')
aws logs tail /aws/bedrock-agentcore/runtimes/${AGENT_ID}-DEFAULT --follow
```

### 6. Clean up
```bash
uv run python cleanup.py
# Add --keep-memory to retain AgentCore Memory for future deploys
```

---

## Project Structure

```
amazon-bedrock-agentcore/
├── agent.py              # AgentCore entry point — BedrockAgentCoreApp + Strands + BMasterAI
├── deploy.py             # Automated deployment: IAM → Memory → ECR → Runtime
├── cleanup.py            # Tear down all provisioned resources
├── test_local.py         # Local test runner (no AgentCore runtime needed)
├── tools/
│   ├── __init__.py
│   └── research_tools.py # Tool implementations: search, summarize, analyze, fetch
├── pyproject.toml        # Dependencies (uv)
├── .env.example          # Environment variable template
└── README.md
```

---

## BMasterAI Telemetry

Every agent event is captured by BMasterAI's structured logger:

```jsonl
{"timestamp": "...", "event_type": "agent_start",    "agent_id": "...", "message": "BMasterAI Research Agent starting"}
{"timestamp": "...", "event_type": "task_start",      "agent_id": "...", "message": "Received task: '...'"}
{"timestamp": "...", "event_type": "llm_call",        "agent_id": "...", "message": "Invoking Strands agent"}
{"timestamp": "...", "event_type": "tool_use",        "agent_id": "...", "message": "Tool: research_topic | query='...'"}
{"timestamp": "...", "event_type": "task_complete",   "agent_id": "...", "duration_ms": 1234}
```

Logs written to:
- `logs/bmasterai.log` — human-readable
- `logs/bmasterai.jsonl` — structured JSONL for log aggregators (CloudWatch Insights, Datadog, etc.)

---

## Tools

| Tool | Description |
|---|---|
| `research_topic(query)` | Search knowledge base or web (Bedrock KB → Brave → DuckDuckGo) |
| `summarize(text)` | Extractive summarization of long text |
| `analyze(data, question)` | Analyze JSON or CSV data to answer a question |
| `fetch_page(url)` | Fetch and extract plain text content from a URL |

### Swap in your own tools

Add a function to `tools/research_tools.py`, create a `@tool` wrapper in `agent.py`, and add it to the `Agent(tools=[...])` list. The Strands framework handles tool selection automatically based on docstrings.

---

## AgentCore Memory

Two memory strategies are provisioned automatically:

| Strategy | Name | Purpose |
|---|---|---|
| Semantic | `ResearchContext` | Retains research findings and analytical patterns across sessions |
| User Preference | `UserPreferences` | Remembers output format and domain preferences per user |

Memory ARN is persisted in SSM Parameter Store at `/bmasterai/agentcore/memory-arn` so redeployments reuse the same memory store.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MODEL_ID` | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model for the Strands agent |
| `AWS_REGION` | `us-east-1` | Deployment region |
| `KNOWLEDGE_BASE_ID` | *(empty)* | Bedrock Knowledge Base ID (optional) |
| `BRAVE_API_KEY` | *(empty)* | Brave Search API key for web search fallback |
| `MEMORY_ARN` | Set by deploy.py | AgentCore Memory ARN |

---

## Related Examples

- [`google-adk-a2a/`](../google-adk-a2a/) — A2A agent patterns with Google ADK
- [`ai-stock-research-agent/`](../ai-stock-research-agent/) — domain-specific research agent
- [`webmcp-gcp-agent/`](../webmcp-gcp-agent/) — GCP-hosted agent with MCP tools
