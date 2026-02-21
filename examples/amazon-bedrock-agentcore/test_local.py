"""
Local test — run tool unit tests and a full agent query without deploying.

Usage:
    uv run python test_local.py
    uv run python test_local.py --tools-only
    uv run python test_local.py --query "Show me any cost anomalies from the last 7 days"
"""

import argparse
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def run_tool_tests():
    """Unit-test each tool independently (no LLM, minimal AWS calls)."""
    import json
    from tools.budget_tools import calculate_burn_rate, get_all_budgets
    from tools.cost_explorer_tools import detect_cost_anomalies, get_service_costs

    print("\n── Tool Tests ──────────────────────────────────────────────")

    tests = [
        ("get_all_budgets",       lambda: get_all_budgets()),
        ("calculate_burn_rate",   lambda: calculate_burn_rate("LAST_7_DAYS")),
        ("detect_cost_anomalies", lambda: detect_cost_anomalies(7)),
        ("get_service_costs",     lambda: get_service_costs("Amazon Bedrock", "LAST_30_DAYS")),
    ]

    for name, fn in tests:
        try:
            result = fn()
            data   = json.loads(result)
            status = "ERROR" if "error" in data else "OK"
            print(f"  [{status}] {name}: {result[:120].replace(chr(10),' ')}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    print("\n✅ Tool tests complete — check logs/ for bmasterai JSONL telemetry\n")


def run_agent(query: str):
    """Invoke the agent locally — requires Bedrock model access."""
    import time
    from agent import handle

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    t0     = time.time()
    result = handle({"message": query})
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"Response ({elapsed:.1f}s):")
    print(f"{'='*60}")
    print(result)
    print(f"\n{'='*60}")
    print("📄 Check logs/bmasterai.jsonl for full telemetry")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="What are my top 5 most expensive AWS services this month?")
    parser.add_argument("--tools-only", action="store_true")
    args = parser.parse_args()

    run_tool_tests()
    if not args.tools_only:
        run_agent(args.query)


if __name__ == "__main__":
    main()
