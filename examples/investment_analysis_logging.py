"""Investment analysis example using Agno Agent with BMasterAI logging.

This script demonstrates how to combine the Agno agent framework with
BMasterAI's structured logging utilities. The agent is asked to invest
$50K split between Apple (AAPL) and Tesla (TSLA), project a 15% gain, and
report the return on investment (ROI).
"""

import time
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.calculator import CalculatorTools
from agno.tools.yfinance import YFinanceTools
from bmasterai.logging import (
    configure_logging,
    get_logger,
    LogLevel,
    EventType,
)


def main() -> None:
    """Run the investment analysis task with logging."""
    # Configure BMasterAI logging and obtain logger instance
    configure_logging(log_level=LogLevel.INFO)
    logger = get_logger()

    agent_id = "investment_agent"
    task_id = "investment_task"

    # Log agent start
    logger.log_event(
        agent_id=agent_id,
        event_type=EventType.AGENT_START,
        message="Starting investment analysis agent",
    )

    # Define the investment analysis task
    task = (
        "Invest $50K split between AAPL and TSLA.\n"
        "Calculate shares, project 15% gains, show ROI.\n"
        "Think through each step."
    )

    # Configure the Claude model
    claude_model = Claude(
        id="claude-sonnet-4-20250514",
        thinking={"type": "enabled", "budget_tokens": 2048},
        default_headers={"anthropic-beta": "interleaved-thinking-2025-05-14"},
    )

    # Create the agent with required tools
    agent = Agent(
        model=claude_model,
        tools=[
            CalculatorTools(enable_all=True),
            YFinanceTools(stock_price=True),
        ],
        instructions=[
            "You are a financial analyst with calculator and stock tools.",
            "Think through each step before and after using tools.",
            "Show reasoning and explain calculations clearly.",
        ],
    )

    # Execute the task with logging
    start_time = time.time()
    logger.log_event(
        agent_id=agent_id,
        event_type=EventType.TASK_START,
        message="Executing investment task",
        metadata={"task_id": task_id},
    )

    try:
        agent.print_response(task, stream=True)
        duration_ms = (time.time() - start_time) * 1000
        logger.log_event(
            agent_id=agent_id,
            event_type=EventType.TASK_COMPLETE,
            message="Investment task completed",
            metadata={"task_id": task_id},
            duration_ms=duration_ms,
        )
    except Exception as exc:  # pragma: no cover - example runtime
        duration_ms = (time.time() - start_time) * 1000
        logger.log_event(
            agent_id=agent_id,
            event_type=EventType.TASK_ERROR,
            message=f"Investment task failed: {exc}",
            level=LogLevel.ERROR,
            metadata={"task_id": task_id},
            duration_ms=duration_ms,
        )
    finally:
        logger.log_event(
            agent_id=agent_id,
            event_type=EventType.AGENT_STOP,
            message="Investment analysis agent finished",
        )


if __name__ == "__main__":
    main()
