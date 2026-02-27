"""
AgentCore Memory Agent — Main Entrypoint
=========================================
A memory-enabled agent deployed on AgentCore Runtime with:
  - Short-term memory  (multi-turn context within a session)
  - Long-term memory   (preferences, facts, summaries across sessions)
  - Bash execution     (via Code Interpreter)
  - Browser search     (via AgentCore Browser tool)
  - Telegram messaging (via Gateway MCP tool)

BMasterAI telemetry is instrumented on every agent lifecycle event,
LLM call, memory operation, tool invocation, and error path.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone

import boto3
from strands import Agent
from strands.models.bedrock import BedrockModel

from bmasterai.logging import configure_logging, LogLevel, EventType

from memory.manager import MemoryManager
from tools.bash_tool import BashTool
from tools.browser_tool import BrowserSearchTool
from tools.telegram_tool import TelegramTool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MEMORY_ID = os.environ["MEMORY_ID"]
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AGENT_ID = os.environ.get("AGENT_ID", "agentcore-memory-agent")

# ---------------------------------------------------------------------------
# BMasterAI — structured telemetry
# ---------------------------------------------------------------------------
bm = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True,       # → logs/bmasterai.jsonl  (structured JSONL)
    enable_reasoning_logs=True,
)

bm.log_event(
    agent_id=AGENT_ID,
    event_type=EventType.AGENT_START,
    message="AgentCore Memory Agent starting",
    metadata={
        "model_id": MODEL_ID,
        "memory_id": MEMORY_ID,
        "aws_region": AWS_REGION,
    },
)

# ---------------------------------------------------------------------------
# Initialise shared clients
# ---------------------------------------------------------------------------
bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)
agentcore_data = boto3.client("bedrock-agentcore", region_name=AWS_REGION)
agentcore_control = boto3.client("bedrock-agentcore-control", region_name=AWS_REGION)

memory_mgr = MemoryManager(
    agentcore_data=agentcore_data,
    memory_id=MEMORY_ID,
)

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """\
You are a helpful personal assistant with persistent memory. You remember past
conversations, learn user preferences over time, and can take real actions.

## Capabilities
- **Bash**: Run shell commands to automate tasks, process files, query APIs.
- **Browser Search**: Search the web for up-to-date information.
- **Telegram**: Send messages back to the user on Telegram.

## Memory Context
The following memories are relevant to this conversation:
{memory_context}

## Guidelines
1. Use memory context to personalise responses. Reference past conversations
   naturally (e.g. "Last time you mentioned...").
2. When the user asks you to remember something, acknowledge it — the memory
   system will extract and store it automatically.
3. Prefer bash for quick computations or file operations.
4. Use browser search when you need current information.
5. Be concise. The user is on Telegram — keep messages readable on mobile.
"""


def build_system_prompt(memories: list[dict]) -> str:
    """Format retrieved memories into the system prompt."""
    if not memories:
        memory_context = "(No prior memories found for this user.)"
    else:
        lines = []
        for i, mem in enumerate(memories, 1):
            content = mem.get("content", {}).get("text", "")
            mem_type = mem.get("memoryStrategyName", "unknown")
            lines.append(f"  [{mem_type}] {content}")
        memory_context = "\n".join(lines)

    return SYSTEM_PROMPT_TEMPLATE.format(memory_context=memory_context)


# ---------------------------------------------------------------------------
# Telemetry helpers
# ---------------------------------------------------------------------------
def _log_tool(tool_name: str, metadata: dict) -> None:
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message=f"Tool invoked: {tool_name}",
        metadata={"tool": tool_name, **metadata},
    )


def _log_done(label: str, duration_ms: float, extra: dict | None = None) -> None:
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_COMPLETE,
        message=f"{label} completed in {duration_ms:.0f}ms",
        metadata={"label": label, **(extra or {})},
        duration_ms=duration_ms,
    )


def _log_err(label: str, error: Exception) -> None:
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_ERROR,
        message=f"{label} failed: {error}",
        metadata={"label": label, "error": str(error)},
    )


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------
def create_agent(actor_id: str, session_id: str, user_message: str) -> Agent:
    """
    Build a Strands Agent wired up with memory context and all tools.
    """
    t0 = time.monotonic()

    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_START,
        message="Building agent with memory context",
        metadata={"actor_id": actor_id, "session_id": session_id},
    )

    # 1. Retrieve relevant long-term memories
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.DECISION_POINT,
        message="Retrieving long-term memories",
        metadata={"actor_id": actor_id, "query_preview": user_message[:80]},
    )

    memories = memory_mgr.retrieve(
        actor_id=actor_id,
        query=user_message,
        max_results=10,
    )

    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.PERFORMANCE_METRIC,
        message=f"Memory retrieval complete — {len(memories)} records returned",
        metadata={"actor_id": actor_id, "memory_count": len(memories)},
        duration_ms=(time.monotonic() - t0) * 1000,
    )

    # 2. Build personalised system prompt
    system_prompt = build_system_prompt(memories)

    # 3. Set up the model
    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.LLM_CALL,
        message="Initialising Bedrock model",
        metadata={"model_id": MODEL_ID, "region": AWS_REGION},
    )

    model = BedrockModel(
        model_id=MODEL_ID,
        region_name=AWS_REGION,
    )

    # 4. Register tools
    tools = [
        BashTool(),
        BrowserSearchTool(),
        TelegramTool(actor_id=actor_id),
    ]

    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message="Registering agent tools",
        metadata={"tools": ["BashTool", "BrowserSearchTool", "TelegramTool"]},
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
    )

    _log_done("create_agent", (time.monotonic() - t0) * 1000, {"actor_id": actor_id})
    return agent


# ---------------------------------------------------------------------------
# Main handler — invoked by AgentCore Runtime
# ---------------------------------------------------------------------------
def handler(event: dict, context: dict) -> dict:
    """
    AgentCore Runtime entrypoint.

    Expected event shape:
    {
        "actor_id":   "tg_123456789",
        "session_id": "sess_abc",
        "prompt":     "What's the weather in Seattle?"
    }
    """
    actor_id = event.get("actor_id", "anonymous")
    session_id = event.get("session_id", f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    user_message = event.get("prompt", "")

    if not user_message:
        bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message="Handler invoked with empty prompt",
            metadata={"actor_id": actor_id, "session_id": session_id},
        )
        return {"status": "error", "message": "No prompt provided."}

    t0 = time.monotonic()

    bm.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_START,
        message="Handling incoming message",
        metadata={
            "actor_id": actor_id,
            "session_id": session_id,
            "prompt_len": len(user_message),
        },
    )

    logger.info(
        "Handling message actor=%s session=%s len=%d",
        actor_id,
        session_id,
        len(user_message),
    )

    try:
        # Build the agent with memory-hydrated prompt
        agent = create_agent(actor_id, session_id, user_message)

        # Run the agent
        bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message="Invoking agent on user message",
            metadata={"actor_id": actor_id, "session_id": session_id},
        )

        t_infer = time.monotonic()
        result = agent(user_message)
        response_text = str(result)
        inference_ms = (time.monotonic() - t_infer) * 1000

        bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.PERFORMANCE_METRIC,
            message="Agent inference complete",
            metadata={
                "actor_id": actor_id,
                "session_id": session_id,
                "response_len": len(response_text),
            },
            duration_ms=inference_ms,
        )

        # Store the conversation turn in short-term memory
        _log_tool("MemoryManager.store_turn", {
            "actor_id": actor_id,
            "session_id": session_id,
        })

        memory_mgr.store_turn(
            actor_id=actor_id,
            session_id=session_id,
            user_message=user_message,
            assistant_message=response_text,
        )

        total_ms = (time.monotonic() - t0) * 1000
        _log_done("handler", total_ms, {
            "actor_id": actor_id,
            "session_id": session_id,
            "response_len": len(response_text),
        })

        logger.info("Response generated, len=%d", len(response_text))

        return {
            "status": "success",
            "response": response_text,
            "session_id": session_id,
        }

    except Exception as exc:
        _log_err("handler", exc)
        logger.exception("Agent execution failed")
        return {
            "status": "error",
            "message": "An internal error occurred. Please try again.",
        }
