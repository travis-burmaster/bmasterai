"""
WebMCP GCP Agent
================
A GCP Cloud Run agent that:
  1. Connects to a website via the WebMCP bridge
  2. Discovers available tools via navigator.modelContext
  3. Runs a Gemini-powered agent loop to complete a shopping task
  4. Instruments everything with bmasterai monitoring

Deploy on GCP Cloud Run:
    gcloud run deploy webmcp-agent --source . --region us-central1 --allow-unauthenticated

Environment variables:
    DEMO_SITE_URL       URL of the WebMCP demo site (default: http://demo-site:8080)
    GOOGLE_CLOUD_PROJECT  GCP project ID (required for Vertex AI)
    GEMINI_MODEL        Gemini model to use (default: gemini-2.0-flash)
    PORT                HTTP port (default: 8080, set by Cloud Run)
"""

import os
import json
import asyncio
import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    FunctionDeclaration,
    Tool,
    Content,
    Part,
)

# BMasterAI imports
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

from webmcp_bridge import WebMCPBridge

# ─── Configuration ───────────────────────────────────────────────────────────

DEMO_SITE_URL = os.environ.get("DEMO_SITE_URL", "http://localhost:8080")
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
GCP_REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
MAX_TOOL_ROUNDS = int(os.environ.get("MAX_TOOL_ROUNDS", "8"))

# ─── BMasterAI setup ─────────────────────────────────────────────────────────

configure_logging(
    log_file="agent.log",
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
)
logger = get_logger()
monitor = get_monitor()

# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="WebMCP GCP Agent",
    description="AI agent that controls websites via WebMCP tools",
    version="1.0.0",
)


class TaskRequest(BaseModel):
    task: str
    site_url: str | None = None  # Override demo site URL per-request


class TaskResponse(BaseModel):
    task: str
    result: str
    tool_calls: list[dict]
    success: bool
    error: str | None = None


# ─── Vertex AI / Gemini helpers ───────────────────────────────────────────────

def init_vertex():
    if GCP_PROJECT:
        vertexai.init(project=GCP_PROJECT, location=GCP_REGION)


def webmcp_tools_to_vertex(tools: list[dict]) -> Tool:
    """Convert WebMCP tool descriptors to Vertex AI FunctionDeclarations."""
    declarations = []
    for t in tools:
        schema = t.get("inputSchema", {})
        # Vertex AI expects properties as a dict of {name: {type, description}}
        props = schema.get("properties", {})
        required = schema.get("required", [])

        declarations.append(
            FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters={
                    "type": "object",
                    "properties": {
                        k: {
                            "type": v.get("type", "string"),
                            "description": v.get("description", ""),
                            **({"enum": v["enum"]} if "enum" in v else {}),
                        }
                        for k, v in props.items()
                    },
                    "required": required,
                },
            )
        )
    return Tool(function_declarations=declarations)


# ─── Agent loop ───────────────────────────────────────────────────────────────

async def run_agent(task: str, site_url: str) -> TaskResponse:
    """
    Main agent loop:
      1. Connect to website via WebMCP bridge
      2. Discover tools
      3. Run Gemini with tools in a loop until done
      4. Return final answer
    """
    session_id = f"webmcp-{os.urandom(4).hex()}"
    tool_call_log: list[dict] = []

    logger.log_event(
        EventType.TASK_START,
        f"Starting task: {task[:80]}",
        {"session_id": session_id, "site_url": site_url},
    )
    monitor.record_custom_metric("agent_task_started", 1)

    async with WebMCPBridge(site_url, headless=True) as bridge:
        # ── Discover WebMCP tools ─────────────────────────────────────────
        webmcp_tools = await bridge.list_tools()
        tool_names = [t["name"] for t in webmcp_tools]

        logger.log_event(
            EventType.TOOL_CALL,
            f"WebMCP tools discovered: {tool_names}",
            {"count": len(webmcp_tools)},
        )
        monitor.record_custom_metric("webmcp_tools_discovered", len(webmcp_tools))

        if not webmcp_tools:
            return TaskResponse(
                task=task,
                result="No WebMCP tools found on the page.",
                tool_calls=[],
                success=False,
                error="No tools registered via navigator.modelContext",
            )

        # ── Set up Gemini ─────────────────────────────────────────────────
        vertex_tools = webmcp_tools_to_vertex(webmcp_tools)
        model = GenerativeModel(
            GEMINI_MODEL,
            tools=[vertex_tools],
            system_instruction=(
                "You are a helpful shopping assistant. Use the available tools "
                "to help the user complete their task. Always search for products "
                "before adding them to the cart. Be concise and efficient."
            ),
        )

        chat = model.start_chat()

        # ── Agent loop ────────────────────────────────────────────────────
        messages = [task]
        final_answer = ""
        rounds = 0

        while rounds < MAX_TOOL_ROUNDS:
            rounds += 1

            # Send to Gemini
            response = chat.send_message(messages[-1] if isinstance(messages[-1], str) else messages[-1])
            monitor.record_custom_metric("gemini_api_calls", 1)

            candidate = response.candidates[0]
            content = candidate.content

            # Check for tool calls
            tool_calls_in_response = [
                p for p in content.parts if hasattr(p, "function_call") and p.function_call
            ]

            if not tool_calls_in_response:
                # Model responded with text — we're done
                final_answer = content.text if hasattr(content, "text") else str(content)
                break

            # Execute tool calls via WebMCP bridge
            tool_results = []
            for part in tool_calls_in_response:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                logger.log_event(
                    EventType.TOOL_CALL,
                    f"Calling WebMCP tool: {tool_name}",
                    {"args": tool_args, "round": rounds},
                )
                monitor.record_custom_metric("webmcp_tool_calls", 1)

                try:
                    result = await bridge.call_tool(tool_name, tool_args)
                    tool_call_log.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                        "success": True,
                    })
                    tool_results.append(
                        Part.from_function_response(name=tool_name, response={"result": result})
                    )
                except Exception as e:
                    error_msg = str(e)
                    logger.log_event(
                        EventType.ERROR,
                        f"Tool call failed: {tool_name}: {error_msg}",
                    )
                    tool_call_log.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "error": error_msg,
                        "success": False,
                    })
                    tool_results.append(
                        Part.from_function_response(
                            name=tool_name,
                            response={"error": error_msg},
                        )
                    )

            # Feed results back to Gemini
            messages.append(Content(role="function", parts=tool_results))

        else:
            final_answer = f"Reached maximum tool rounds ({MAX_TOOL_ROUNDS}). Last partial result."

        # ── Metrics + logging ─────────────────────────────────────────────
        success = bool(final_answer and "error" not in final_answer.lower()[:20])
        monitor.record_custom_metric("agent_task_completed", 1 if success else 0)
        monitor.record_custom_metric("agent_tool_calls_total", len(tool_call_log))

        logger.log_event(
            EventType.TASK_COMPLETE,
            f"Task complete — {len(tool_call_log)} tool calls, {rounds} rounds",
            {"session_id": session_id, "success": success},
        )

        return TaskResponse(
            task=task,
            result=final_answer,
            tool_calls=tool_call_log,
            success=success,
        )


# ─── HTTP endpoints ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_vertex()
    logger.log_event(EventType.SYSTEM, "WebMCP GCP Agent starting up", {
        "demo_site": DEMO_SITE_URL,
        "model": GEMINI_MODEL,
    })


@app.get("/health")
async def health():
    return {"status": "ok", "model": GEMINI_MODEL, "site": DEMO_SITE_URL}


@app.get("/tools")
async def list_tools(site_url: str = DEMO_SITE_URL):
    """Inspect what WebMCP tools are registered on the target site."""
    async with WebMCPBridge(site_url, headless=True) as bridge:
        tools = await bridge.list_tools()
    return {"site_url": site_url, "tools": tools}


@app.post("/run", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    """Run an agent task against the WebMCP-enabled website."""
    site_url = request.site_url or DEMO_SITE_URL

    if not request.task.strip():
        raise HTTPException(status_code=400, detail="task must not be empty")

    try:
        return await run_agent(request.task, site_url)
    except Exception as e:
        logger.log_event(EventType.ERROR, f"Agent run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "service": "WebMCP GCP Agent",
        "description": "AI agent that controls websites via WebMCP tools",
        "endpoints": {
            "GET /health": "Health check",
            "GET /tools": "List WebMCP tools from target site",
            "POST /run": "Run an agent task",
        },
        "example": {
            "POST /run": {
                "task": "Find me a laptop under $1000 and add it to the cart",
                "site_url": DEMO_SITE_URL,
            }
        },
    }


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
