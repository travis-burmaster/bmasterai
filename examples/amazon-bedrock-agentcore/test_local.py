"""
Local test — invoke the agent without deploying to AgentCore.
Run this before deploying to verify your tools and logging work correctly.

Usage:
    uv run python test_local.py
    uv run python test_local.py --query "What is Amazon Bedrock AgentCore?"
"""

import argparse
import json
import os
import sys
import time

# ── Optional: load .env for local development ─────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional for local runs


def run_local(query: str) -> None:
    """Import and invoke the agent handler directly (no AgentCore runtime needed)."""
    print(f"\n{'='*60}")
    print("BMasterAI AgentCore — Local Test")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")

    start = time.time()

    try:
        # Import triggers bmasterai logging + monitoring setup
        from agent import handle

        payload = {"message": query}
        result = handle(payload)

        elapsed = time.time() - start
        print(f"\n{'='*60}")
        print(f"Response ({elapsed:.1f}s):")
        print(f"{'='*60}")
        print(result)
        print(f"\n{'='*60}")
        print("✅ Local test passed")
        print("📄 Check logs/bmasterai.log and logs/bmasterai.jsonl for telemetry")

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Run: uv sync")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


def run_tool_tests() -> None:
    """Unit-test each tool independently."""
    from tools.research_tools import (
        search_knowledge_base,
        summarize_text,
        analyze_data,
        fetch_url_content,
    )

    print("\n── Tool Tests ─────────────────────────────────────────────")

    # summarize
    print("\n[1/4] summarize_text")
    sample = (
        "Amazon Bedrock AgentCore is a fully managed service from AWS that provides "
        "a scalable runtime for deploying AI agents. It handles container orchestration, "
        "security, and scaling automatically. Developers can focus on agent logic rather "
        "than infrastructure. It integrates natively with Bedrock models and knowledge bases. "
        "AgentCore also provides built-in memory and code interpreter capabilities."
    )
    result = summarize_text(sample, max_sentences=2)
    print(f"   Input: {len(sample)} chars → Summary: {result[:120]}...")
    print("   ✅ OK")

    # analyze_data (JSON)
    print("\n[2/4] analyze_data (JSON)")
    data = json.dumps([
        {"service": "EC2", "cost_usd": 245.50, "region": "us-east-1"},
        {"service": "S3", "cost_usd": 12.30, "region": "us-east-1"},
        {"service": "Bedrock", "cost_usd": 88.00, "region": "us-east-1"},
    ])
    result = analyze_data(data, "Which service costs the most?")
    print(f"   Result: {result[:200]}")
    print("   ✅ OK")

    # analyze_data (CSV)
    print("\n[3/4] analyze_data (CSV)")
    csv_data = "date,revenue,units\n2026-01-01,10500,42\n2026-01-02,9800,38\n2026-01-03,11200,47"
    result = analyze_data(csv_data, "What is the trend?")
    print(f"   Result: {result[:200]}")
    print("   ✅ OK")

    # fetch_url_content
    print("\n[4/4] fetch_url_content")
    result = fetch_url_content("https://httpbin.org/json")
    print(f"   Result: {result[:200]}")
    print("   ✅ OK")

    print("\n✅ All tool tests passed\n")


def main():
    parser = argparse.ArgumentParser(description="Local test for BMasterAI AgentCore agent")
    parser.add_argument(
        "--query",
        default="Summarize the key benefits of Amazon Bedrock AgentCore for AI agent deployment.",
        help="Research query to send to the agent",
    )
    parser.add_argument(
        "--tools-only",
        action="store_true",
        help="Only run tool unit tests (no LLM call)",
    )
    args = parser.parse_args()

    if args.tools_only:
        run_tool_tests()
    else:
        run_tool_tests()
        run_local(args.query)


if __name__ == "__main__":
    main()
