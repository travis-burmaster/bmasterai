# Running Trip Planner and Weather Agents with ADK Web

This guide provides the steps to run the complete Agent-to-Agent (A2A) stack and interact with the **Trip Planner** via the ADK Web UI.

## 1. Prerequisites

Ensure you have your environment variables set in `.env` or your shell:
- `GOOGLE_API_KEY`: Required for Gemini LLM.
- `WEATHER_AGENT_URL`: Defaults to `http://localhost:10000`.

## 2. Start the Backend Stack

### Step A: Start the Weather MCP Server
The MCP server provides the raw tools for weather data.
```bash
# Terminal 1
PORT=8080 uv run weather_mcp/server.py
```

### Step B: Start the Weather Agent (A2A Server)
The Weather Agent wraps the MCP server and exposes it via A2A.
```bash
# Terminal 2
MCP_SERVER_URL=http://localhost:8080/mcp uv run uvicorn weather_agent.agent:a2a_app --port 10000
```

---

## 3. Run with ADK Web

To use the **Trip Planner** in the Web UI, you need to run `adk web` from the project root.

### Step C: (Optional) Prepare Weather Agent for Discovery
If you want the Weather Agent to also appear as a standalone agent in the Web UI:
```bash
curl http://localhost:10000/.well-known/agent-card.json -o weather_agent/agent.json
```

### Step D: Launch ADK Web
Run this command from the `google-adk-a2a` directory:
```bash
# Terminal 3
WEATHER_AGENT_URL=http://localhost:10000 uv run adk web .
```

1. Open your browser to `http://localhost:8000`.
2. Select **trip_planner** from the agent list.
3. Ask it to "Plan a trip to Indianapolis" to see the A2A flow in action!