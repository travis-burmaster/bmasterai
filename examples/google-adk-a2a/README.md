# Weather and Trip Planner Agents (A2A)

This bmasterai example demonstrates an **Agent-to-Agent (A2A)** interaction pattern using the Google ADK and FastMCP. It consists of a **Trip Planner Agent** (Client) that consults a **Weather Agent** (Server) to plan trips based on real-time weather forecasts.

## Components

### 1. Weather MCP Server (`weather_mcp/`)
- **Technology**: FastMCP (Python)
- **Role**: Backend tool provider.
- **Function**: Fetches real-time weather data from [Open-Meteo](https://open-meteo.com/).
- **Tools**: `get_weather_forecast(city, days)`
- **Port**: 8080

### 2. Weather Agent (`weather_agent/`)
- **Technology**: Google ADK + A2A SDK
- **Role**: A2A Server.
- **Function**: Wraps the Weather MCP server and exposes it to other agents via the A2A protocol.
- **Port**: 10000

### 3. Trip Planner Agent (`trip_planner/`)
- **Technology**: Google ADK + A2A SDK
- **Role**: A2A Client.
- **Function**: Sends natural language queries (e.g., "Weather in Tokyo") to the Weather Agent and integrates the results into trip plans.
- **Features**:
  - Robust polling for async task completion.
  - Automatic error handling and retries.

## Features
- **Real-time Weather**: Live data from Open-Meteo (Celsius & Fahrenheit).
- **Structured Logging**: Uses `bmasterai` for observing agent internals and events.
- **Agent-to-Agent Communication**: Demonstrates the full A2A handshake and message exchange protocol.
- **Verification**: Includes a robust verification script (`verify_setup.py`) to test the entire chain.

## Quick Start

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Run Verification**:
   This script starts all servers and runs a test query.
   ```bash
   uv run verify_setup.py
   ```

3. **View Logs**:
   Check `weather_mcp.log`, `weather_agent.log`, and `trip_planner.log` for detailed execution traces.

## Project Structure

```
├── weather_mcp/       # FastMCP Server
├── weather_agent/     # A2A Server Agent
├── trip_planner/      # A2A Client Agent
├── verify_setup.py    # Orchestration & Verification Script
├── pyproject.toml     # Dependencies (Python 3.11+)
└── README.md          # This file
```
