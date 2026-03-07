"""
Real Estate Coordinator Agent — BMasterAI + Strands A2A Implementation

Orchestrates property search and booking by delegating to specialized sub-agents
via the A2A (Agent-to-Agent) protocol.

Local mode  : runs as an A2AServer itself (coordinator is also an A2A server)
AgentCore   : wrap with BedrockAgentCoreApp and set sub-agent URLs via env vars
"""

import asyncio
import contextvars
import os
import time
from typing import Optional
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

from strands import Agent, tool

from bmasterai.logging import configure_logging, LogLevel, EventType

# ── Config ────────────────────────────────────────────────────────────────────
AGENT_ID  = os.getenv("AGENT_ID", "realestate-coordinator")
MODEL_ID  = os.getenv("MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")
TIMEOUT   = int(os.getenv("A2A_TIMEOUT", "300"))

# Sub-agent URLs — set these before running
SEARCH_AGENT_URL  = os.getenv("PROPERTY_SEARCH_AGENT_URL",  "http://localhost:5002")
BOOKING_AGENT_URL = os.getenv("PROPERTY_BOOKING_AGENT_URL", "http://localhost:5001")

# ── BMasterAI telemetry ───────────────────────────────────────────────────────
bm = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True,
)

bm.log_event(
    agent_id=AGENT_ID,
    event_type=EventType.AGENT_START,
    message="Real Estate Coordinator starting",
    metadata={"model_id": MODEL_ID, "search_url": SEARCH_AGENT_URL, "booking_url": BOOKING_AGENT_URL},
)


def _log_tool(name: str, meta: dict):
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TOOL_USE,
                 message=f"Tool: {name}", metadata={"tool": name, **meta})


def _log_done(name: str, dur: float, extra: dict = {}):
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_COMPLETE,
                 message=f"{name} completed in {dur:.0f}ms",
                 metadata={"tool": name, **extra}, duration_ms=dur)


def _log_err(name: str, error: Exception):
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_ERROR,
                 message=f"{name} failed: {error}",
                 metadata={"tool": name, "error": str(error)})


# ── Bearer token helpers ──────────────────────────────────────────────────────
# For local use: no auth required.
# For AgentCore: the incoming Authorization header is forwarded to sub-agents.

_bearer_token_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "bearer_token", default=None
)


def _get_httpx_client(bearer_token: Optional[str] = None) -> httpx.AsyncClient:
    """Build an httpx client. Adds Authorization header when a token is available."""
    headers = {}

    # Try BedrockAgentCoreContext first (AgentCore runtime)
    if not bearer_token:
        try:
            from bedrock_agentcore.runtime import BedrockAgentCoreContext  # type: ignore
            req_headers = BedrockAgentCoreContext.get_request_headers() or {}
            auth = req_headers.get("authorization", "")
            if auth.startswith("Bearer "):
                bearer_token = auth[7:]
                bm.log_event(agent_id=AGENT_ID, event_type=EventType.TOOL_USE,
                             message="Bearer token obtained from AgentCoreContext")
        except Exception:
            pass  # local mode — no auth

    # Fall back to context var
    if not bearer_token:
        bearer_token = _bearer_token_var.get()

    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    return httpx.AsyncClient(timeout=TIMEOUT, headers=headers)


# ── A2A message helpers ───────────────────────────────────────────────────────

def _make_message(text: str) -> Message:
    return Message(
        kind="message",
        role=Role.user,
        parts=[Part(TextPart(kind="text", text=text))],
        message_id=uuid4().hex,
    )


async def _send_to_agent(message: str, agent_url: str, agent_name: str) -> str:
    """Send a message to a sub-agent via A2A and return its text response."""
    t0 = time.time()
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TOOL_USE,
                 message=f"A2A → {agent_name}",
                 metadata={"agent": agent_name, "url": agent_url, "message_preview": message[:100]})
    try:
        client = _get_httpx_client()
        session_id = str(uuid4())
        client.headers["X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"] = session_id

        resolver = A2ACardResolver(httpx_client=client, base_url=agent_url)
        agent_card = await resolver.get_agent_card()

        config = ClientConfig(httpx_client=client, streaming=False)
        a2a = ClientFactory(config).create(agent_card)

        msg = _make_message(message)
        response_text: Optional[str] = None

        async for event in a2a.send_message(msg):
            if isinstance(event, Message):
                for part in event.parts:
                    if hasattr(part, "text"):
                        response_text = part.text
                        break
                if response_text:
                    break

            elif isinstance(event, tuple) and len(event) == 2:
                task, _ = event
                # Walk task attributes to extract text
                for attr in ("artifacts", "result", "parts"):
                    container = getattr(task, attr, None)
                    if not container:
                        continue
                    items = container if isinstance(container, (list, tuple)) else [container]
                    for item in items:
                        parts = getattr(item, "parts", [item])
                        for p in parts:
                            root = getattr(p, "root", p)
                            t = getattr(root, "text", None)
                            if t:
                                response_text = t
                                break
                        if response_text:
                            break
                    if response_text:
                        break

                if not response_text:
                    t = getattr(task, "text", None)
                    if t:
                        response_text = t

                if response_text:
                    break

        dur = (time.time() - t0) * 1000
        if response_text:
            bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_COMPLETE,
                         message=f"A2A ← {agent_name} ({dur:.0f}ms)",
                         metadata={"agent": agent_name}, duration_ms=dur)
            return response_text

        return f"Error: No response received from {agent_name}."

    except Exception as e:
        _log_err(f"A2A→{agent_name}", e)
        return f"Error communicating with {agent_name}: {e}"


# ── Coordinator tools ─────────────────────────────────────────────────────────

@tool
async def search_properties(query: str) -> str:
    """
    Search for properties using the Property Search Agent via A2A protocol.

    Args:
        query: Natural-language search query (e.g., 'apartments in New York under $4000 with 2 bedrooms')

    Returns:
        List of matching properties from the search agent
    """
    _log_tool("search_properties", {"query_preview": query[:100]})

    if not SEARCH_AGENT_URL:
        return "Error: PROPERTY_SEARCH_AGENT_URL environment variable is not set."

    result = await _send_to_agent(query, SEARCH_AGENT_URL, "Property Search Agent")
    _log_done("search_properties", 0)
    return result


@tool
async def book_property(booking_request: str) -> str:
    """
    Book a property using the Property Booking Agent via A2A protocol.

    Args:
        booking_request: Booking details as a natural-language string, e.g.:
            'Book PROP001 for Jane Smith, email jane@example.com, phone 555-9999, move-in 2025-09-01, 12 months'

    Returns:
        Booking confirmation or error
    """
    _log_tool("book_property", {"request_preview": booking_request[:100]})

    if not BOOKING_AGENT_URL:
        return "Error: PROPERTY_BOOKING_AGENT_URL environment variable is not set."

    result = await _send_to_agent(booking_request, BOOKING_AGENT_URL, "Property Booking Agent")
    _log_done("book_property", 0)
    return result


@tool
async def check_booking(query: str) -> str:
    """
    Check booking status or list customer bookings via the Property Booking Agent.

    Args:
        query: Query string, e.g.:
            'Check status of booking BOOK-ABC123' or 'List all bookings for jane@example.com'

    Returns:
        Booking status or list from the booking agent
    """
    _log_tool("check_booking", {"query_preview": query[:100]})

    if not BOOKING_AGENT_URL:
        return "Error: PROPERTY_BOOKING_AGENT_URL environment variable is not set."

    result = await _send_to_agent(query, BOOKING_AGENT_URL, "Property Booking Agent")
    _log_done("check_booking", 0)
    return result


# ── Agent factory ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Real Estate Coordinator Agent that helps users find and book properties.

You coordinate between two specialized agents using the A2A protocol:
1. **Property Search Agent** — finds listings by location, price, type, and bedrooms
2. **Property Booking Agent** — handles bookings, cancellations, and status checks

Your workflow:
- Property search requests → use `search_properties`
- Booking a specific property → use `book_property`
- Checking or cancelling bookings → use `check_booking`
- Search-then-book flows → call `search_properties` first, then `book_property`

Always give the user clear, actionable summaries of what each sub-agent returned.
"""


def create_coordinator() -> Agent:
    return Agent(
        system_prompt=SYSTEM_PROMPT,
        description=os.getenv(
            "AGENT_DESCRIPTION",
            "Coordinates real estate property search and booking via A2A protocol",
        ),
        tools=[search_properties, book_property, check_booking],
        model=MODEL_ID,
    )


# ── AgentCore integration (optional) ─────────────────────────────────────────

def create_agentcore_app():
    """
    Wrap the coordinator in a BedrockAgentCoreApp for deployment.
    Only import bedrock_agentcore when running on AgentCore runtime.
    """
    from bedrock_agentcore.runtime import BedrockAgentCoreApp  # type: ignore

    app = BedrockAgentCoreApp()
    coordinator = create_coordinator()

    @app.entrypoint
    async def handle(payload):
        bm.log_event(agent_id=AGENT_ID, event_type=EventType.TOOL_USE,
                     message="AgentCore entrypoint invoked",
                     metadata={"payload_keys": list(payload.keys())})
        user_message = payload.get("inputText") or payload.get("message", "")
        response = coordinator(user_message)
        return {"response": str(response)}

    return app


# ── Local entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--agentcore":
        app = create_agentcore_app()
        app.run()
    else:
        # Interactive local REPL
        print("Real Estate Coordinator — local mode")
        print(f"  Search agent : {SEARCH_AGENT_URL}")
        print(f"  Booking agent: {BOOKING_AGENT_URL}")
        print("Type 'quit' to exit.\n")

        coordinator = create_coordinator()

        async def repl():
            while True:
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if user_input.lower() in ("quit", "exit", "q"):
                    break
                if not user_input:
                    continue
                t0 = time.time()
                response = coordinator(user_input)
                dur = (time.time() - t0) * 1000
                print(f"\nCoordinator ({dur:.0f}ms):\n{response}\n")

        asyncio.run(repl())
