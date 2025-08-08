import os
import time

from agno.agent import Agent
from agno.models.google import Gemini

from bmasterai.logging import configure_logging, LogLevel, EventType
from bmasterai.monitoring import get_monitor


def main() -> None:
    """Run a simple Gemini prompt using the Agno agent framework.

    The example shows how to combine Agno with BMasterAI telemetry. It records
    agent lifecycle events and basic LLM metrics for a single Gemini call.
    An environment variable named ``GOOGLE_API_KEY`` must contain a valid
    Gemini API key for the call to succeed.
    """
    # Set up BMasterAI logging and monitoring
    logger = configure_logging(log_level=LogLevel.INFO, enable_console=True)
    monitor = get_monitor()
    monitor.start_monitoring()

    agent_id = "agno-gemini-example"
    monitor.track_agent_start(agent_id)

    # Create an Agno agent that talks to Gemini
    agent = Agent(
        model=Gemini(id="gemini-1.5-flash", api_key=os.environ.get("GOOGLE_API_KEY")),
        markdown=True,
        description="A helpful agent demonstrating Agno + BMasterAI telemetry",
    )

    prompt = "Write a short haiku about observability for AI agents."

    start_time = time.time()
    response = agent.run(prompt)
    duration_ms = (time.time() - start_time) * 1000

    tokens_used = 0
    raw = getattr(response, "raw_response", None)
    if raw is not None:
        usage = getattr(raw, "usage_metadata", None)
        if usage and getattr(usage, "total_token_count", None) is not None:
            tokens_used = usage.total_token_count

    # Record metrics and log the LLM call
    monitor.track_llm_call(agent_id, "gemini-1.5-flash", tokens_used, duration_ms)
    logger.log_event(
        agent_id=agent_id,
        event_type=EventType.LLM_CALL,
        message="Gemini response received",
        metadata={"tokens_used": tokens_used},
        duration_ms=duration_ms,
    )

    print(response.content)

    monitor.track_agent_stop(agent_id)
    logger.log_event(
        agent_id=agent_id,
        event_type=EventType.AGENT_STOP,
        message="Example complete",
    )


if __name__ == "__main__":
    main()
