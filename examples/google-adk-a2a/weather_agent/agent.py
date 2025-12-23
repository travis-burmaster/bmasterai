import logging
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
import bmasterai
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Initialize BMasterAI Logging
bmasterai.configure_logging(log_file='weather_agent.log', json_log_file='weather_agent.jsonl')
logger = bmasterai.get_logger()

# Setup logging
# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
# logger = logging.getLogger("weather-agent")

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are a helpful weather assistant. "
    "Your main task is to provide weather forecasts using the 'get_weather_forecast' tool. "
    "When asked for weather, always retrieve the data and summarize it clearly for the user. "
    "If the tool fails or returns an error, explain it politely."
)

logger.logger.info("--- 🔧 Configured Weather Agent... ---")

# Define the Agent
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="weather_agent",
    description="A helpful agent that provides weather forecasts.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8080/mcp")
            )
        )
    ],
)

# Convert to A2A App
# Expose on port 10000 (standard for this agent)
a2a_app = to_a2a(root_agent, port=10000)

if __name__ == "__main__":
    import uvicorn
    # This entry point is mostly for debugging. 
    # Production run should use: uvicorn weather_agent.agent:a2a_app --port 10000
    uvicorn.run(a2a_app, host="0.0.0.0", port=10000)
