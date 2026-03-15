# BMasterAI

> **Production-ready AI agent monitoring, logging, and observability for Python.**
> Drop-in telemetry for agents built on Claude, Gemini, LangGraph, or any LLM stack.

[![PyPI](https://img.shields.io/pypi/v/bmasterai)](https://pypi.org/project/bmasterai/)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

```python
from bmasterai.logging import get_logger, EventType
from bmasterai.monitoring import get_monitor

logger = get_logger("my-agent")
monitor = get_monitor()

logger.log_event(EventType.TASK_START, "Agent started", {"task": "summarize"})
monitor.record_metric("tokens_used", 1240)
```

---

## Examples

Real-world agents you can clone and run. Most recent first.

---

### 2026

#### [Claude Web + Computer Agent — Native Tool-Use Loop](examples/claude-web-computer-agent/) `NEW`
*March 2026*

A bare-metal Claude tool-use agent combining **web search** (Tavily) and **computer use** (screenshot/click/type/key/scroll) — no LangGraph, no framework, just the Anthropic SDK — fully instrumented with BMasterAI logging and telemetry. The foundational pattern that every Claude agent is built on.

**Stack:** Claude (Anthropic), Tavily, xdotool + scrot, BMasterAI

**What it demonstrates:**
- The raw Anthropic `tool_use` / `tool_result` message cycle — the core loop behind every Claude agent
- Multimodal tool results: screenshots sent back to Claude as image blocks so it can see the screen
- BMasterAI telemetry on every LLM call, tool dispatch, decision point, and error path
- Structured JSONL telemetry at `logs/agent.jsonl` — pipe to any analytics tool

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY + TAVILY_API_KEY
python main.py "Search for today's top AI news, open a browser to the first result, take a screenshot, and summarize what you see."
```

---

#### [Deep Research Agent — LangGraph + BMasterAI Telemetry](examples/deep-research-agent/)
*March 2026*

A multi-step web research agent built with **LangGraph** and fully instrumented with **BMasterAI** logging and telemetry. Inspired by [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents). Give it any research question and it plans, searches, analyzes, reflects on quality, and synthesizes a structured report — automatically looping back for more research if gaps are found.

**Stack:** LangGraph, Claude (Anthropic), Tavily, BMasterAI

**What it demonstrates:**
- Multi-node LangGraph pipeline with a conditional reflection loop (planner → search → analyze → reflect → synthesize)
- Quality-gated research: reflector scores findings 1–10, loops back for follow-up searches when score < 7 (max 2 loops)
- BMasterAI on every step: `track_agent_start/stop`, `track_llm_call`, `track_task_duration`, `log_event(TOOL_USE)`, `log_reasoning_chain`, `log_event(DECISION_POINT)`
- Structured JSONL telemetry at `logs/research.jsonl` — pipe to any analytics tool

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY + TAVILY_API_KEY
python main.py "What is the current state of multi-agent AI systems in 2026?"
```

---

#### [Viral YouTube Short Generator — LangGraph](examples/langgraph-viral-youtube/) 
*March 2026*

A four-agent LangGraph pipeline that researches trending topics and generates complete viral YouTube Short production packages — title, hook, 45-60 second script, tags, and thumbnail concept — with a quality gate that retries automatically if the output doesn't meet bar.

**Stack:** LangGraph, Claude (Anthropic), Tavily, BMasterAI

**What it demonstrates:**
- Four specialist agents in sequence: Trend Researcher → Hook Writer → Script Writer → Title & Tags
- Quality gate node with automatic retry (max 2 loops) using LangGraph conditional edges
- BMasterAI structured logging on every agent call: `configure_logging`, `track_agent_start/stop`, `track_llm_call`, `log_event(EventType.*)` 
- Shared `VideoState` TypedDict flowing through all nodes — clean state handoff pattern

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY + TAVILY_API_KEY
python main.py "AI agents taking over software engineering"
```

---

#### [A2A Real Estate Multi-Agent — AgentCore Edition](examples/a2a-realestate-agentcore/)
*March 2026*

A BMasterAI adaptation of the [AWS Labs A2A Real Estate sample](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/A2A-realestate-agentcore-multiagents). Three Strands agents — Property Search, Property Booking, and a Coordinator — communicate over the A2A (Agent-to-Agent) protocol, with every tool call and A2A hop instrumented via BMasterAI structured telemetry.

**Stack:** AWS Bedrock AgentCore, Strands, A2A Protocol, OAuth 2.0 (Cognito), BMasterAI

**What it demonstrates:**
- Multi-agent orchestration with the A2A protocol: coordinator delegates to specialized sub-agents at runtime
- BMasterAI telemetry replacing custom loggers: `TOOL_USE`, `TASK_COMPLETE`, `TASK_ERROR` on every operation across all three agents
- Bearer token forwarding from AgentCore Runtime context to sub-agent A2A calls
- Local REPL mode for development + `BedrockAgentCoreApp` path for serverless deployment

```bash
# Start all three agents locally + interactive REPL
pip install -r realestate_coordinator/requirements.txt
python run_local.py
```

---

#### [AgentCore Memory Agent + BMasterAI Telemetry](examples/agentcore-memory-agent/)
*February 2026*

A Telegram bot with persistent memory built on AWS Bedrock AgentCore — fully instrumented with BMasterAI structured telemetry. The agent remembers past conversations, learns user preferences across sessions, and can execute bash commands, search the web, and send files. No Mac mini, no local server — just AWS and a Telegram message.

**Stack:** AWS Bedrock AgentCore, Strands, Claude (Bedrock), DynamoDB, Lambda, API Gateway, Cedar policies, BMasterAI

**What it demonstrates:**
- Three-strategy persistent memory (user preferences, session summaries, semantic facts) via AgentCore Memory
- Serverless Telegram webhook with session lifecycle management
- Cedar policy enforcement at the AgentCore Gateway boundary
- BMasterAI telemetry on every agent lifecycle event, memory retrieval, tool invocation, and error path — output to console, flat log, and structured JSONL

```bash
pip install -r requirements.txt
# Deploy to AgentCore Runtime:
./scripts/deploy.sh
# Set Telegram webhook:
./scripts/setup_telegram_webhook.sh
```

---

#### [Amazon Bedrock AgentCore — Cost Optimization Agent](examples/amazon-bedrock-agentcore/)
*February 2026*

A Strands agent that monitors AWS spend, detects anomalies, forecasts costs, and analyzes service-level breakdowns — with BMasterAI structured telemetry logged on every agent action. Inspired by the awslabs/amazon-bedrock-agentcore-samples reference implementation.

**Stack:** AWS Bedrock AgentCore, Strands, AWS Cost Explorer, AWS Budgets, Cost Anomaly Detection, BMasterAI

**What it demonstrates:**
- Cost anomaly detection, budget monitoring, and ML-based cost forecasting via Strands tools
- Full BMasterAI instrumentation: `AGENT_START`, `TASK_START`, `LLM_CALL`, `TOOL_USE`, `TASK_COMPLETE` on every operation
- Structured JSONL output ready for CloudWatch Insights, Datadog, or any log aggregator
- AgentCore Runtime deployment with `bedrock-agentcore-starter-toolkit`

```bash
pip install -r requirements.txt
python agent.py
```

---

#### [WebMCP + GCP Agent Runtime](examples/webmcp-gcp-agent/)
*February 2026*

An AI agent running on GCP Cloud Run that controls a website by calling its browser-native [WebMCP](https://webmachinelearning.github.io/webmcp/) tools via a Playwright bridge. The agent uses Gemini to complete shopping tasks by discovering and calling JavaScript tools registered in the browser via `navigator.modelContext` — instrumented end-to-end with BMasterAI.

**Stack:** FastAPI, Playwright, Vertex AI (Gemini 2.0 Flash), GCP Cloud Run, Docker Compose

**What it demonstrates:**
- WebMCP browser-native tool calling from Python via Playwright CDP bridge
- Gemini agent loop with dynamic tool discovery
- IAM-authenticated Cloud Run deployment with one-command deploy script
- BMasterAI structured logging and metrics across the full agent lifecycle

```bash
docker-compose up  # starts demo store + agent at localhost:8081
curl -X POST http://localhost:8081/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Find me a laptop under $1000 and add it to the cart"}'
```

---

#### [OpenClaw Telemetry Dashboard](examples/openclaw-telemetry/) 
*February 2026*

Real-time observability dashboard for [OpenClaw](https://openclaw.ai) AI agent sessions. Tracks LLM usage, token counts, cost estimates, tool call analytics, and session history — all in a Streamlit UI backed by BMasterAI telemetry.

**Stack:** Streamlit, BMasterAI, OpenClaw session logs

---

#### [Google ADK Agent-to-Agent (A2A)](examples/google-adk-a2a/)
*January 2026*

Agent-to-Agent interaction pattern using the Google Agent Development Kit and FastMCP. A Trip Planner Agent (client) consults a Weather Agent (server) using real-time forecasts to plan trips — demonstrating multi-agent orchestration with BMasterAI monitoring at every hop.

**Stack:** Google ADK, FastMCP, BMasterAI

---

### 2025

#### [AI LinkedIn Stress Analysis + Reasoning](examples/ai-stress-linkedin-reasoning/)
*August 2025*

Streamlit app showing real-time Gemini reasoning transparency. Analyzes LinkedIn profiles using Tavily search and provides personalized stress reduction suggestions with full chain-of-thought visibility via BMasterAI.

**Stack:** Streamlit, Gemini 2.5 Pro, Tavily, BMasterAI

---

#### [Gemini Reasoning Streamlit](examples/gemini-reasoning-streamlit/)
*August 2025*

Watch Gemini 2.5 Pro think in real time. Streams chain-of-thought reasoning for complex research tasks (AI podcast influencer discovery) with Tavily web search and Firecrawl email extraction.

**Stack:** Streamlit, Gemini 2.5 Pro, Tavily, Firecrawl, BMasterAI

---

#### [Streamlit + Airflow MCP Chatbot](examples/streamlit-airflow-mcp-example/)
*August 2025*

Natural-language interface to Apache Airflow via an MCP server. Ask questions about your DAGs, pipeline runs, and task status in plain English.

**Stack:** Streamlit, OpenAI, Airflow MCP, BMasterAI

---

#### [RAG with Qdrant](examples/rag-qdrant/)
*August 2025*

Production-ready Retrieval-Augmented Generation with async processing, intelligent caching, and real-time performance monitoring. A complete RAG reference implementation.

**Stack:** Qdrant, async Python, BMasterAI

---

#### [Kubernetes Telemetry](examples/kubernetes-telemetry/)
*August 2025*

Kubernetes-native LLM cost analysis and observability. Wires BMasterAI metrics into OpenTelemetry, Grafana, Prometheus, Loki, and Tempo for production-grade agent monitoring at scale.

**Stack:** Kubernetes, Helm, OpenTelemetry, Grafana, Prometheus, BMasterAI

---

#### [Gradio + Anthropic Claude](examples/gradio-anthropic/)
*August 2025*

Modern Gradio web interface for Claude-powered agents with BMasterAI monitoring. Clean starting point for building chat-style agent UIs.

**Stack:** Gradio, Claude (Anthropic), BMasterAI

---

#### [MCP GitHub Streamlit](examples/mcp-github-streamlit/)
*August 2025*

Automated GitHub repo analysis and improvement suggestions using AI agents and Model Context Protocol integration.

**Stack:** Streamlit, MCP, BMasterAI

---

#### [Enhanced GitHub MCP](examples/enhanced-github-mcp-streamlit/)
*August 2025*

Advanced multi-agent system for GitHub repo analysis and automated feature implementation.

**Stack:** Streamlit, multi-agent, MCP, BMasterAI

---

#### [AI Stock Research Agent](examples/ai-stock-research-agent/)
*August 2025*

Real-time market data, web research, and AI analysis combined into intelligent stock recommendations.

**Stack:** yfinance, web search, BMasterAI

---

#### [Agno Telemetry Integration](examples/agno-telemetry/)
*August 2025*

Full observability integration between the [Agno](https://github.com/agno-ai/agno) agent framework and BMasterAI telemetry. Production-ready agents with monitoring from day one.

**Stack:** Agno, BMasterAI

---

#### [AI Real Estate Agent Team](examples/ai-real-estate-agent-team/)
*August 2025*

Multi-agent property search and analysis platform with comprehensive BMasterAI logging across agent performance, task execution, and market analysis flows.

**Stack:** Multi-agent, BMasterAI

---

#### [Streamlit Business Consultant](examples/streamlit-app/)
*July 2025*

AI-powered business consultant with market analysis, competitor research, strategic recommendations, and risk assessment in a Streamlit UI.

**Stack:** Streamlit, BMasterAI

---

#### [Google ADK Enterprise Consultant](examples/google-adk/)
*July 2025*

Enterprise-grade AI business consultant integrating Google's Agent Development Kit with BMasterAI monitoring and management.

**Stack:** Google ADK, BMasterAI

---

#### [Minimal RAG](examples/minimal-rag/)
*July 2025*

Minimal working RAG implementation. Simplest possible starting point for retrieval-augmented agents.

---

## Install

```bash
pip install bmasterai
```

Or from source:

```bash
git clone https://github.com/travis-burmaster/bmasterai.git
cd bmasterai
pip install -e .[dev]
```

## Quickstart

```python
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

configure_logging(log_level=LogLevel.INFO, enable_console=True, enable_file=True)
logger = get_logger("my-agent")
monitor = get_monitor()

# Log agent events
logger.log_event(EventType.TASK_START, "Starting summarization task", {"model": "claude-3-5-sonnet"})

# Record metrics
monitor.record_metric("tokens_used", 1240)
monitor.record_metric("latency_ms", 850)

logger.log_event(EventType.TASK_COMPLETE, "Task done", {"success": True})
```

See [`examples/basic_usage.py`](examples/basic_usage.py) for a full working example.

## Documentation

Full API reference and deployment guides: [`README.content.md`](README.content.md)

Kubernetes deployment: [`README-k8s.md`](README-k8s.md)

## Contributing

New examples welcome. Open a PR with:
- A clear learning objective
- Working code that runs end to end
- A README explaining the architecture and how to run it

## License

MIT
