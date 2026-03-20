"""
BMasterAI — Native OTLP Export Example

Demonstrates automatic trace + metric export to any OTel-compatible backend.
All you need is configure_otlp() before your first monitor call.

Run with a local Jaeger instance:
    docker run -d --name jaeger -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one:latest
    python agent_with_otlp.py
    open http://localhost:16686
"""

import time
import os
from bmasterai import configure_otlp, get_monitor, configure_logging, LogLevel

# ── 1. Configure OTLP ─────────────────────────────────────────────────────────
# All subsequent monitor calls will automatically emit spans + metrics.
otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
otlp_headers = {}
if os.getenv("OTLP_API_KEY"):
    otlp_headers["x-api-key"] = os.getenv("OTLP_API_KEY")

success = configure_otlp(
    endpoint=otlp_endpoint,
    service_name="bmasterai-example",
    service_version="0.2.3",
    headers=otlp_headers,
)

if success:
    print(f"✅ OTLP configured → {otlp_endpoint}")
else:
    print("⚠️  OTLP not available (opentelemetry-sdk not installed). Continuing without export.")
    print("   Install with: pip install 'bmasterai[otlp]'")

# ── 2. Normal bmasterai setup ─────────────────────────────────────────────────
configure_logging(log_level=LogLevel.INFO)
monitor = get_monitor()
monitor.start_monitoring()


# ── 3. Simulate a multi-step research agent ───────────────────────────────────
def run_research_agent():
    agent_id = "research-agent-01"
    print(f"\n🤖 Starting agent: {agent_id}")

    monitor.track_agent_start(agent_id)
    # → OTLP: opens root span "agent.research-agent-01"

    # Step 1: Web search task
    print("  🔎 Running web search...")
    time.sleep(0.3)
    monitor.track_task_duration(agent_id, "web_search", 312)
    # → OTLP: child span "task.web_search" with duration_ms=312

    # Step 2: LLM analysis call
    print("  🧠 Calling LLM for analysis...")
    time.sleep(0.5)
    monitor.track_llm_call(
        agent_id=agent_id,
        model="claude-3-5-sonnet-20241022",
        tokens_used=1847,
        duration_ms=1203,
        reasoning_steps=4,
    )
    # → OTLP: child span "llm.call" + increments bmasterai.llm.tokens_used counter

    # Step 3: Synthesis task
    print("  📝 Synthesizing results...")
    time.sleep(0.2)
    monitor.track_task_duration(agent_id, "synthesize", 198)
    # → OTLP: child span "task.synthesize"

    # Step 4: Simulate an error
    print("  ⚠️  Simulating transient error...")
    monitor.track_error(agent_id, "rate_limit")
    # → OTLP: increments bmasterai.agent.errors counter, adds event to root span

    # Retry
    print("  🔁 Retrying after backoff...")
    time.sleep(0.1)
    monitor.track_llm_call(
        agent_id=agent_id,
        model="claude-3-5-haiku-20241022",
        tokens_used=924,
        duration_ms=620,
    )

    # Custom metric
    monitor.record_custom_metric("documents_processed", 12, {"agent_id": agent_id})
    # → OTLP: increments bmasterai.custom.metric{metric_name=documents_processed}

    monitor.track_agent_stop(agent_id)
    # → OTLP: closes root span with runtime_seconds

    print(f"  ✅ Agent {agent_id} complete\n")


def run_pipeline():
    """Run multiple agents to show multi-agent tracing."""
    agents = [
        ("planner-agent", "claude-3-5-haiku-20241022", 450, 380),
        ("research-agent", "claude-3-5-sonnet-20241022", 2100, 1840),
        ("writer-agent", "claude-3-5-sonnet-20241022", 3200, 2100),
    ]

    print("\n🏭 Running multi-agent pipeline...")
    for agent_id, model, tokens, latency in agents:
        monitor.track_agent_start(agent_id)
        time.sleep(0.1)
        monitor.track_llm_call(agent_id, model, tokens, latency)
        monitor.track_task_duration(agent_id, "main_task", latency * 1.2)
        monitor.track_agent_stop(agent_id)
        print(f"  ✅ {agent_id} ({model}) — {tokens} tokens in {latency}ms")


if __name__ == "__main__":
    run_research_agent()
    run_pipeline()

    # Dashboard check
    dashboard = monitor.get_agent_dashboard("research-agent-01")
    health = monitor.get_system_health()

    print("=" * 50)
    print("📊 BMasterAI Dashboard (research-agent-01)")
    print(f"   Status: {dashboard['status']}")
    print(f"   Tasks:  {list(dashboard['performance'].keys())}")
    print(f"   Errors: {dashboard['metrics'].get('total_errors', 0)}")
    print()
    print(f"🖥️  System: CPU {health['system_metrics']['cpu'].get('latest', 0):.1f}% | "
          f"Mem {health['system_metrics']['memory'].get('latest', 0):.1f}%")
    print(f"🤖 Agents: {health['active_agents']} active / {health['total_agents']} total")

    if success:
        print(f"\n🔭 View traces at your OTel backend")
        print(f"   (Jaeger: http://localhost:16686 → search 'bmasterai-example')")

    # Give batch exporter time to flush
    time.sleep(2)
    monitor.stop_monitoring()
