import asyncio
import json
import logging
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
# A2A Imports
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    DataPart,
    GetTaskRequest,
    Message,
    MessageSendParams,
    Part,
    SendMessageRequest,
    SendMessageSuccessResponse,
    Task,
    TaskIdParams,
    TaskState,
    TextPart,
)
import httpx

import bmasterai

# Initialize BMasterAI Logging
bmasterai.configure_logging(log_file='trip_planner.log', json_log_file='trip_planner.jsonl')
logger = bmasterai.get_logger()

# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
# logger = logging.getLogger("trip-planner")

load_dotenv()

WEATHER_AGENT_URL = os.getenv("WEATHER_AGENT_URL", "http://127.0.0.1:10000")

# --- Helpers ---------------------------------------------------------------

def _parts_to_text(parts: Optional[list[Part]]) -> Optional[str]:
    """Convert the list of parts into a readable text blob."""
    if not parts:
        return None

    chunks: list[str] = []
    for part in parts:
        content = getattr(part, "root", part)
        if isinstance(content, TextPart) and content.text:
            chunks.append(content.text.strip())
        elif isinstance(content, DataPart):
            chunks.append(json.dumps(content.data, indent=2, sort_keys=True))

    combined = "\n".join(chunk for chunk in chunks if chunk).strip()
    return combined or None


def _message_to_text(message: Optional[Message]) -> Optional[str]:
    return None if message is None else _parts_to_text(message.parts)


def _agent_task_reply(task: Task) -> Optional[str]:
    """Extract the last agent-authored message from the task history."""
    history = task.history or []
    for message in reversed(history):
        if message.role == "agent":
            text = _message_to_text(message)
            if text:
                return text

    # Fallback to any status message if history was empty
    return _message_to_text(getattr(task.status, "message", None))

# --- Tool to call Weather Agent ---

async def call_weather_agent(query: str) -> str:
    """
    Calls the external Weather Agent to get weather information.

    Args:
        query: The natural language query for the weather agent (e.g., "What is the weather in Paris for the next 3 days?").

    Returns:
        The response from the weather agent.
    """

    logger.logger.info(f"--- 📞 Calling Weather Agent with query: '{query}' ---")
    logger.log_event(
        agent_id="trip_planner",
        event_type=bmasterai.EventType.AGENT_COMMUNICATION,
        message="Calling Weather Agent",
        metadata={"query": query},
    )
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            # 1. Resolve Agent Card
            resolver = A2ACardResolver(httpx_client=http_client, base_url=WEATHER_AGENT_URL)
            agent_card = await resolver.get_agent_card()
            
            # 2. Create Client
            client = A2AClient(httpx_client=http_client, agent_card=agent_card)
            
            # 3. Send Message
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": query}],
                    "messageId": uuid.uuid4().hex,
                }
            }
            
            request = SendMessageRequest(
                id=str(uuid.uuid4()), 
                params=MessageSendParams(**payload)
            )
            
            response = await client.send_message(request)

            if isinstance(response.root, SendMessageSuccessResponse):
                result = response.root.result

                if isinstance(result, Task):
                    # Poll for completion
                    task_id = result.id
                    max_retries = 10
                    for attempt in range(max_retries):
                        state = result.status.state
                        if state == TaskState.completed:
                            agent_reply = _agent_task_reply(result)
                            if agent_reply:
                                return agent_reply
                            return f"Task {task_id} completed but returned no text."
                        
                        if state == TaskState.failed:
                             error_msg = getattr(result.status, "message", "Unknown error")
                             # Try to get more details if available
                             return f"Weather Agent Task {task_id} FAILED. Error: {error_msg}"
                        
                        logger.logger.info(f"Task {task_id} state: {state}. Polling ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(1.0)
                        
                        # Refresh task
                        get_task_req = GetTaskRequest(id=str(uuid.uuid4()), params=TaskIdParams(id=task_id))
                        get_task_response = await client.get_task(get_task_req)
                        
                        if get_task_response.is_error:
                             return f"Error polling task {task_id}: {get_task_response.error}"
                        result = get_task_response.root
                    
                    return f"Timeout waiting for Weather Agent task {task_id} to complete."

                if isinstance(result, Message):
                    text = _message_to_text(result)
                    if text:
                        return text
                    return "Weather Agent responded, but no readable content was returned."

            return f"Failed to get successful response from Weather Agent. Response: {response}"

    except Exception as e:
        logger.logger.error(f"❌ Error calling Weather Agent: {e}")
        return f"Error communicating with Weather Agent: {str(e)}"

# --- Trip Planner Agent Setup ---

SYSTEM_INSTRUCTION = (
    "You are an expert Trip Planner. "
    "Your goal is to plan detailed trips for users. "
    "CRITICAL: Before planning any activities, you MUST check the weather for the destination using the 'call_weather_agent' tool. "
    "Use the weather information to suggest appropriate activities (indoor vs outdoor). "
)

# Wrapper for ADK Tool not needed if passing function directly

    
trip_planner = LlmAgent(
    model="gemini-2.5-flash",
    name="trip_planner",
    description="Plans trips based on weather.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[call_weather_agent], 
)

# Simple CLI entry point to interact with Trip Planner
# --- Trip Planner Execution ---

async def run_trip_planner():
    """Run the Trip Planner Agent to verify connectivity."""
    print("🌍 Trip Planner Agent: Starting Verification...")
    
    # Check if we have API key for full agent run
    has_creds = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_CLOUD_PROJECT")
    
    if has_creds:
        print("\nℹ️  Credentials detected. (Note: Full agent execution requires a Runner, skipping to Keep It Simple)")
    else:
        print("\n⚠️  No Google API Key found. This is expected in this demo environment.")

    # Always run the tool check as it proves the A2A connection which is the main goal.
    print("\n🧪 Verifying A2A Connection to Weather Agent...")
    print("   Sending query: 'What is the weather in Indianapolis?'")
    
    response = await call_weather_agent("What is the weather in Indianapolis?")
    
    print("\n✅ Verification Result:")
    print(f"   Response from Weather Agent: {response}")
    
    if "Weather Agent Task Completed" in response or "Successfully sent query" in response or "Indianapolis" in str(response):
        print("\n🚀 SUCCESS: Trip Planner successfully communicated with Weather Agent via A2A!")
    else:
        print("\n❌ FAILURE: Did not get expected response.")

if __name__ == "__main__":
    asyncio.run(run_trip_planner())
