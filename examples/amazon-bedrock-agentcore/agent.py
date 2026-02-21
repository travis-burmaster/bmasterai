"""
BMasterAI + Amazon Bedrock AgentCore — Cost Optimization Agent
==============================================================
A Strands agent that monitors AWS spend, detects anomalies, forecasts costs,
and analyzes service-level breakdowns — with bmasterai structured telemetry
logged on every agent action.

Entry point for `bedrock-agentcore-starter-toolkit` Runtime.

Features:
  - Cost Anomaly Detection  : unusual spending spikes via AWS Cost Anomaly Detection
  - Budget Monitoring       : utilization tracking and overrun forecasting
  - Cost Forecasting        : ML-based future spend prediction with confidence intervals
  - Service Breakdown       : per-service, per-usage-type cost drill-down
  - Current Spending        : month-to-date and daily cost visibility + burn rate
"""

import os
import time
import uuid
from datetime import datetime, timedelta

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

from bmasterai.logging import configure_logging, LogLevel, EventType

from tools.cost_explorer_tools import (
    get_cost_and_usage,
    get_cost_forecast,
    detect_cost_anomalies,
    get_service_costs,
)
from tools.budget_tools import (
    get_all_budgets,
    get_budget_status,
    calculate_burn_rate,
)

# ── Config ─────────────────────────────────────────────────────────────────────
MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
AGENT_ID  = os.getenv("AGENT_ID", "bmasterai-cost-agent")

# ── BMasterAI — structured telemetry ──────────────────────────────────────────
bm = configure_logging(
    log_level=LogLevel.INFO,
    enable_console=True,
    enable_file=True,
    enable_json=True,   # → logs/bmasterai.jsonl
)

bm.log_event(
    agent_id=AGENT_ID,
    event_type=EventType.AGENT_START,
    message="BMasterAI Cost Optimization Agent starting on AgentCore Runtime",
    metadata={"model_id": MODEL_ID},
)

# ── AgentCore app ──────────────────────────────────────────────────────────────
app = BedrockAgentCoreApp()


# ── Helper: wrap every tool call with bmasterai telemetry ────────────────────
def _log_tool(name: str, metadata: dict):
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TOOL_USE,
                 message=f"Tool: {name}", metadata={"tool": name, **metadata})

def _log_done(name: str, duration_ms: float, extra: dict = {}):
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_COMPLETE,
                 message=f"{name} completed in {duration_ms:.0f}ms",
                 metadata={"tool": name, **extra}, duration_ms=duration_ms)

def _log_err(name: str, error: Exception):
    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_ERROR,
                 message=f"{name} failed: {error}",
                 metadata={"tool": name, "error": str(error)})


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — Cost Anomaly Detection
# ══════════════════════════════════════════════════════════════════════════════
@tool
def analyze_cost_anomalies(days: int = 7) -> str:
    """
    Detect unusual spending spikes or anomalies in AWS costs.

    Uses AWS Cost Anomaly Detection to identify unexpected cost increases
    with root-cause analysis by service and region.

    Args:
        days: Number of days to analyze for anomalies (default: 7).

    Returns:
        str: Detected anomalies ranked by financial impact, with root causes.
    """
    t0 = time.time()
    _log_tool("analyze_cost_anomalies", {"days": days})
    try:
        result = detect_cost_anomalies(days)
        _log_done("analyze_cost_anomalies", (time.time()-t0)*1000)
        return result
    except Exception as e:
        _log_err("analyze_cost_anomalies", e)
        return f"Error detecting anomalies: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — Budget Monitoring
# ══════════════════════════════════════════════════════════════════════════════
@tool
def get_budget_information(budget_name: str = "") -> str:
    """
    Retrieve AWS budget status and utilization.

    Shows budget limits, actual spend, forecasted spend, utilization percentage,
    and overrun risk. Returns all budgets if no name is specified.

    Args:
        budget_name: Specific budget name to check. If empty, returns all budgets.

    Returns:
        str: Budget utilization with OK / WARNING / EXCEEDED status per budget.
    """
    t0 = time.time()
    _log_tool("get_budget_information", {"budget_name": budget_name or "ALL"})
    try:
        result = get_budget_status(budget_name) if budget_name else get_all_budgets()
        _log_done("get_budget_information", (time.time()-t0)*1000)
        return result
    except Exception as e:
        _log_err("get_budget_information", e)
        return f"Error fetching budgets: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — Cost Forecasting
# ══════════════════════════════════════════════════════════════════════════════
@tool
def forecast_future_costs(days_ahead: int = 30) -> str:
    """
    Predict future AWS costs using machine learning.

    Generates a cost forecast with 80% confidence interval bounds based on
    historical spend patterns. Also includes burn rate trend analysis.

    Args:
        days_ahead: Number of days to forecast (default: 30, max: 90).

    Returns:
        str: Cost forecast with mean, lower bound, upper bound, and burn rate trend.
    """
    t0 = time.time()
    _log_tool("forecast_future_costs", {"days_ahead": days_ahead})
    try:
        forecast_start = datetime.now().strftime("%Y-%m-%d")
        forecast_end   = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        forecast = get_cost_forecast(forecast_start, forecast_end)
        burn     = calculate_burn_rate("LAST_7_DAYS")

        _log_done("forecast_future_costs", (time.time()-t0)*1000, {"days_ahead": days_ahead})
        return f"Cost Forecast:\n{forecast}\n\nCurrent Burn Rate:\n{burn}"
    except Exception as e:
        _log_err("forecast_future_costs", e)
        return f"Error generating forecast: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — Service Breakdown
# ══════════════════════════════════════════════════════════════════════════════
@tool
def get_service_cost_breakdown(service_name: str = "", time_period: str = "LAST_30_DAYS") -> str:
    """
    Get detailed AWS cost breakdown by service or across all services.

    Breaks costs down by usage type within a service, or returns the top 10
    most expensive services if no service name is provided.

    Args:
        service_name: AWS service name (e.g., "Amazon Bedrock", "Amazon EC2").
                      Leave empty to get a ranked list of all services.
        time_period:  LAST_7_DAYS | LAST_30_DAYS | LAST_90_DAYS (default: LAST_30_DAYS).

    Returns:
        str: Cost breakdown sorted by spend, with per-usage-type detail.
    """
    t0 = time.time()
    _log_tool("get_service_cost_breakdown", {"service": service_name or "ALL", "period": time_period})
    try:
        if service_name:
            result = get_service_costs(service_name, time_period)
        else:
            # Rank all services by cost
            import json
            days = {"LAST_7_DAYS": 7, "LAST_30_DAYS": 30, "LAST_90_DAYS": 90}.get(time_period, 30)
            end   = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            raw = get_cost_and_usage(
                start, end, "MONTHLY",
                [{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
            data = json.loads(raw)
            svc_totals: dict = {}
            for period in data.get("results", []):
                for group in period.get("groups", []):
                    svc = group["keys"][0]
                    svc_totals[svc] = svc_totals.get(svc, 0) + group["cost"]

            ranked = sorted(svc_totals.items(), key=lambda x: x[1], reverse=True)
            lines  = [f"Top AWS Services by Cost ({time_period}):\n"]
            for i, (svc, cost) in enumerate(ranked[:10], 1):
                lines.append(f"  {i:2d}. {svc:<45} ${cost:>10.2f}")
            lines.append(f"\n  Total: ${sum(svc_totals.values()):.2f}")
            result = "\n".join(lines)

        _log_done("get_service_cost_breakdown", (time.time()-t0)*1000)
        return result
    except Exception as e:
        _log_err("get_service_cost_breakdown", e)
        return f"Error getting service breakdown: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — Current Spending (MTD + Daily)
# ══════════════════════════════════════════════════════════════════════════════
@tool
def get_current_month_costs() -> str:
    """
    Get month-to-date cost visibility and daily spend breakdown.

    Retrieves every day's cost since the start of the current month,
    grouped by AWS service, plus burn rate analysis for the last 7 days.

    Returns:
        str: MTD total, daily costs by service, and current burn rate.
    """
    t0 = time.time()
    _log_tool("get_current_month_costs", {})
    try:
        start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        end   = datetime.now().strftime("%Y-%m-%d")

        mtd   = get_cost_and_usage(start, end, "DAILY",
                                   [{"Type": "DIMENSION", "Key": "SERVICE"}])
        burn  = calculate_burn_rate("LAST_7_DAYS")

        _log_done("get_current_month_costs", (time.time()-t0)*1000)
        return f"Month-to-Date Costs ({start} → {end}):\n{mtd}\n\nBurn Rate (last 7 days):\n{burn}"
    except Exception as e:
        _log_err("get_current_month_costs", e)
        return f"Error fetching current month costs: {e}"


# ── Strands Agent ──────────────────────────────────────────────────────────────
agent = Agent(
    model=BedrockModel(model_id=MODEL_ID),
    tools=[
        analyze_cost_anomalies,    # Feature 1 — Anomaly Detection
        get_budget_information,    # Feature 2 — Budget Monitoring
        forecast_future_costs,     # Feature 3 — Cost Forecasting
        get_service_cost_breakdown, # Feature 4 — Service Breakdown
        get_current_month_costs,   # Feature 5 — Current Spending
    ],
    system_prompt=(
        "You are an expert AWS FinOps assistant running inside Amazon Bedrock AgentCore. "
        "You have real-time access to AWS cost data via five specialized tools:\n\n"
        "  1. analyze_cost_anomalies      — detect unexpected spending spikes\n"
        "  2. get_budget_information      — check budget utilization and overrun risk\n"
        "  3. forecast_future_costs       — predict future spend with confidence intervals\n"
        "  4. get_service_cost_breakdown  — drill into per-service cost detail\n"
        "  5. get_current_month_costs     — see MTD spend and daily burn rate\n\n"
        "Always use live data. Provide specific numbers, flag risks clearly, and suggest "
        "concrete actions when costs are anomalous or budgets are at risk."
    ),
)


# ── AgentCore Entry Point ──────────────────────────────────────────────────────
@app.entrypoint
def handle(payload: dict) -> str:
    """
    AgentCore Runtime entry point — called for every inbound task.

    Accepts A2A / direct invocation payloads. Extracts the user message,
    invokes the Strands agent, and returns the response.
    """
    task_id = str(uuid.uuid4())
    t0 = time.time()

    user_message = (
        payload.get("message")
        or payload.get("text")
        or payload.get("input")
        or str(payload)
    )

    bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_START,
                 message=f"Task received: '{user_message[:120]}'",
                 metadata={"task_id": task_id})

    bm.log_event(agent_id=AGENT_ID, event_type=EventType.LLM_CALL,
                 message="Invoking Strands agent",
                 metadata={"task_id": task_id, "model_id": MODEL_ID})

    try:
        response = agent(user_message)
        result   = str(response)
        duration = (time.time() - t0) * 1000

        bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_COMPLETE,
                     message=f"Task completed in {duration:.0f}ms",
                     metadata={"task_id": task_id, "response_length": len(result)},
                     duration_ms=duration)
        return result

    except Exception as e:
        bm.log_event(agent_id=AGENT_ID, event_type=EventType.TASK_ERROR,
                     message=f"Task failed: {e}",
                     metadata={"task_id": task_id, "error": str(e)},
                     duration_ms=(time.time()-t0)*1000)
        raise
