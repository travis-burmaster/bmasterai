"""
BMasterAI + Amazon Bedrock AgentCore — Research Agent
======================================================
A general-purpose research agent that runs inside Bedrock AgentCore Runtime
and uses bmasterai for structured logging, monitoring, and telemetry.

Entry point for `bedrock-agentcore-starter-toolkit` Runtime.
"""

import os
import time
import uuid

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

from tools.research_tools import (
    search_knowledge_base,
    summarize_text,
    analyze_data,
    fetch_url_content,
)

# ── Configuration ──────────────────────────────────────────────────────────────
MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
AGENT_ID = os.getenv("AGENT_ID", f"bmasterai-agentcore-{uuid.uuid4().hex[:8]}")

# ── BMasterAI Logging & Monitoring ─────────────────────────────────────────────
bm_logger = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True,
)
monitor = get_monitor()
monitor.start_monitoring()

bm_logger.log_event(
    agent_id=AGENT_ID,
    event_type=EventType.AGENT_START,
    message="BMasterAI Research Agent starting inside AgentCore Runtime",
    metadata={"model_id": MODEL_ID, "agent_id": AGENT_ID},
)

# ── AgentCore App ──────────────────────────────────────────────────────────────
app = BedrockAgentCoreApp()


# ── Strands Tool Wrappers (with bmasterai telemetry) ──────────────────────────

@tool
def research_topic(query: str, max_results: int = 5) -> str:
    """
    Search a knowledge base or web source for information on a topic.

    Args:
        query: The research question or topic to search for.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        str: Relevant information found for the query.
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    bm_logger.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message=f"Tool: research_topic | query='{query}'",
        metadata={"tool": "research_topic", "query": query, "max_results": max_results, "task_id": task_id},
    )

    try:
        result = search_knowledge_base(query, max_results)
        duration_ms = (time.time() - start_time) * 1000

        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_COMPLETE,
            message=f"research_topic completed in {duration_ms:.0f}ms",
            metadata={"task_id": task_id, "result_length": len(result)},
            duration_ms=duration_ms,
        )
        return result

    except Exception as e:
        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"research_topic failed: {e}",
            metadata={"task_id": task_id, "error": str(e)},
        )
        return f"Error performing research: {e}"


@tool
def summarize(text: str, max_sentences: int = 5) -> str:
    """
    Summarize a block of text into key points.

    Args:
        text: The text to summarize.
        max_sentences: Target number of sentences in the summary (default: 5).

    Returns:
        str: A concise summary of the provided text.
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    bm_logger.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message="Tool: summarize",
        metadata={"tool": "summarize", "input_length": len(text), "task_id": task_id},
    )

    try:
        result = summarize_text(text, max_sentences)
        duration_ms = (time.time() - start_time) * 1000

        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_COMPLETE,
            message=f"summarize completed in {duration_ms:.0f}ms",
            metadata={"task_id": task_id, "summary_length": len(result)},
            duration_ms=duration_ms,
        )
        return result

    except Exception as e:
        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"summarize failed: {e}",
            metadata={"task_id": task_id, "error": str(e)},
        )
        return f"Error summarizing text: {e}"


@tool
def analyze(data: str, question: str) -> str:
    """
    Analyze structured or unstructured data to answer a specific question.

    Args:
        data: Raw data in JSON, CSV, or plain text format.
        question: The analytical question to answer about the data.

    Returns:
        str: Analysis results and insights.
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    bm_logger.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message=f"Tool: analyze | question='{question}'",
        metadata={"tool": "analyze", "question": question, "data_length": len(data), "task_id": task_id},
    )

    try:
        result = analyze_data(data, question)
        duration_ms = (time.time() - start_time) * 1000

        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_COMPLETE,
            message=f"analyze completed in {duration_ms:.0f}ms",
            metadata={"task_id": task_id},
            duration_ms=duration_ms,
        )
        return result

    except Exception as e:
        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"analyze failed: {e}",
            metadata={"task_id": task_id, "error": str(e)},
        )
        return f"Error analyzing data: {e}"


@tool
def fetch_page(url: str) -> str:
    """
    Fetch and extract readable text content from a URL.

    Args:
        url: The HTTP/HTTPS URL to fetch content from.

    Returns:
        str: Extracted text content from the page.
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    bm_logger.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TOOL_USE,
        message=f"Tool: fetch_page | url='{url}'",
        metadata={"tool": "fetch_page", "url": url, "task_id": task_id},
    )

    try:
        result = fetch_url_content(url)
        duration_ms = (time.time() - start_time) * 1000

        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_COMPLETE,
            message=f"fetch_page completed in {duration_ms:.0f}ms | {len(result)} chars",
            metadata={"task_id": task_id, "content_length": len(result)},
            duration_ms=duration_ms,
        )
        return result

    except Exception as e:
        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"fetch_page failed: {e}",
            metadata={"task_id": task_id, "url": url, "error": str(e)},
        )
        return f"Error fetching page: {e}"


# ── Strands Agent ──────────────────────────────────────────────────────────────
agent = Agent(
    model=BedrockModel(model_id=MODEL_ID),
    tools=[research_topic, summarize, analyze, fetch_page],
    system_prompt=(
        "You are a precise research and analysis assistant powered by BMasterAI "
        "and running inside Amazon Bedrock AgentCore Runtime. "
        "Use your tools to gather information, analyze data, and produce clear, "
        "well-structured responses. Always cite your sources and be transparent "
        "about confidence levels. When unsure, say so."
    ),
)


# ── AgentCore Request Handler ──────────────────────────────────────────────────
@app.entrypoint
def handle(payload: dict) -> str:
    """
    AgentCore Runtime entry point. Called for each inbound task.

    Args:
        payload: AgentCore request payload containing the user message.

    Returns:
        str: Agent response text.
    """
    task_id = str(uuid.uuid4())
    start_time = time.time()

    # Extract message from A2A / AgentCore payload
    user_message = (
        payload.get("message")
        or payload.get("text")
        or payload.get("input")
        or str(payload)
    )

    bm_logger.log_event(
        agent_id=AGENT_ID,
        event_type=EventType.TASK_START,
        message=f"Received task: '{user_message[:100]}...'",
        metadata={"task_id": task_id, "payload_keys": list(payload.keys())},
    )

    try:
        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message="Invoking Strands agent",
            metadata={"task_id": task_id, "model_id": MODEL_ID},
        )

        response = agent(user_message)
        result_text = str(response)
        duration_ms = (time.time() - start_time) * 1000

        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_COMPLETE,
            message=f"Task completed in {duration_ms:.0f}ms",
            metadata={"task_id": task_id, "response_length": len(result_text)},
            duration_ms=duration_ms,
        )

        return result_text

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        bm_logger.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"Task failed: {e}",
            metadata={"task_id": task_id, "error": str(e)},
            duration_ms=duration_ms,
        )
        raise
