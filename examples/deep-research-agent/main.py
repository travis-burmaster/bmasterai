"""
Deep Research Agent — powered by LangGraph + BMasterAI

Usage:
    python main.py "What is the current state of AI agents in enterprise software?"
    python main.py  # prompts interactively

Features:
    - Planner decomposes topic into sub-questions
    - Parallel Tavily searches per sub-question
    - Analyzer synthesizes each result set
    - Reflector evaluates quality and loops if needed (max 2 loops)
    - Synthesizer produces a final structured report
    - BMasterAI logs every LLM call, tool use, agent event, and reasoning step
"""
import sys
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# Change to example dir so BMasterAI writes logs relative to here
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/reasoning", exist_ok=True)

# Validate required env vars
required = ["ANTHROPIC_API_KEY", "TAVILY_API_KEY"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print(f"❌ Missing required environment variables: {', '.join(missing)}")
    print("   Copy .env.example → .env and fill in your keys.")
    sys.exit(1)

from graph import build_graph
from agents import monitor, bm
from bmasterai.logging import EventType

DIVIDER = "─" * 70


def print_report(state: dict) -> None:
    print(f"\n{'═'*70}")
    print("📊  DEEP RESEARCH REPORT")
    print("═" * 70)
    print(f"\n🔍  Topic: {state.get('topic', '—')}\n")
    print(DIVIDER)
    print(state.get("report", "No report generated."))

    if state.get("errors"):
        print(f"\n⚠️  Errors encountered:")
        for e in state["errors"]:
            print(f"   • {e}")

    print(f"\n{DIVIDER}")
    print(f"Sources consulted: {len(state.get('sources', []))}")
    print(f"Reflection loops:  {state.get('reflection_count', 0)}")
    print(f"Sub-questions:     {len(state.get('sub_questions', []))}")


def print_telemetry(agent_id: str = "deep_research_pipeline") -> None:
    """Print BMasterAI telemetry dashboard."""
    print(f"\n{'═'*70}")
    print("📈  BMASTERAI TELEMETRY")
    print("═" * 70)
    try:
        dashboard = monitor.get_agent_dashboard()
        health = monitor.get_system_health()

        print(f"\nSystem Health:  {health.get('status', 'unknown').upper()}")

        agents = dashboard.get("agents", {})
        for aid, metrics in agents.items():
            print(f"\nAgent: {aid}")
            print(f"  LLM calls:    {metrics.get('llm_calls', 0)}")
            print(f"  Total tokens: {metrics.get('total_tokens', 0)}")
            print(f"  Avg latency:  {metrics.get('avg_latency', 0):.2f}s")
            print(f"  Errors:       {metrics.get('error_count', 0)}")

        # Export raw logs path
        log_dir = Path("logs")
        print(f"\nLogs written to: {log_dir.resolve()}/")
        print(f"  research.log   — human-readable event log")
        print(f"  research.jsonl — structured JSON telemetry (pipe to any analytics tool)")
    except Exception as e:
        print(f"Telemetry unavailable: {e}")


def main():
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        print("\n🔬  Deep Research Agent (BMasterAI + LangGraph)")
        print(DIVIDER)
        topic = input("Research question: ").strip()
        if not topic:
            topic = "What is the current state of multi-agent AI systems in 2026?"

    print(f"\n🚀  Starting deep research on: {topic}")
    print(DIVIDER)

    # Track overall pipeline
    pipeline_id = "deep_research_pipeline"
    monitor.track_agent_start(pipeline_id)
    bm.log_event(
        event_type=EventType.AGENT_START,
        agent_id=pipeline_id,
        data={"topic": topic},
    )
    t_start = time.time()

    graph = build_graph()

    # Stream node completions so user sees progress
    print("\n📋  Plan:         ", end="", flush=True)
    final_state = None

    for chunk in graph.stream({"topic": topic}):
        for node_name, node_state in chunk.items():
            if node_name == "planner":
                qs = node_state.get("sub_questions", [])
                print(f"{len(qs)} sub-questions")
                for i, q in enumerate(qs, 1):
                    print(f"   {i}. {q}")
            elif node_name == "web_searcher":
                count = len(node_state.get("search_results", []))
                print(f"🔎  Web search:    {count} query batches completed")
            elif node_name == "analyzer":
                count = len(node_state.get("findings", []))
                print(f"🧪  Analysis:      {count} findings synthesized")
            elif node_name == "reflector":
                score_msg = "needs more research" if node_state.get("needs_more_research") else "approved for synthesis"
                loops = node_state.get("reflection_count", 1)
                print(f"🪞  Reflection {loops}:  {score_msg}")
            elif node_name == "synthesizer":
                print("📝  Synthesizing final report...")
            final_state = node_state

    elapsed = time.time() - t_start

    # Merge final state for display (stream gives partial states per node)
    full_state = graph.invoke({"topic": topic})  # type: ignore

    monitor.track_task_duration(pipeline_id, "full_pipeline", elapsed)
    monitor.track_agent_stop(pipeline_id)
    bm.log_event(
        event_type=EventType.AGENT_STOP,
        agent_id=pipeline_id,
        data={"elapsed_seconds": round(elapsed, 2), "topic": topic},
    )

    print_report(full_state)
    print_telemetry()
    print(f"\n✅  Completed in {elapsed:.1f}s\n")


if __name__ == "__main__":
    main()
