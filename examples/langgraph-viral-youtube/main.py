"""
Entry point. Run from CLI:
    python main.py "AI agents taking over software engineering"
    python main.py  # prompts interactively
"""
import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
os.makedirs("logs", exist_ok=True)

from graph import build_graph
from state import VideoState


DIVIDER = "─" * 60


def print_result(state: VideoState) -> None:
    print(f"\n{'═'*60}")
    print("🎬  VIRAL YOUTUBE SHORT — PRODUCTION PACKAGE")
    print('═'*60)

    print(f"\n📌  TITLE\n{DIVIDER}")
    print(state.get("title", "—"))

    print(f"\n🎣  HOOK  (first 3–5 seconds)")
    print(DIVIDER)
    print(state.get("hook", "—"))

    print(f"\n📝  SCRIPT")
    print(DIVIDER)
    print(state.get("script", "—"))

    print(f"\n🏷️   TAGS")
    print(DIVIDER)
    print(", ".join(state.get("tags", [])))

    print(f"\n🖼️   THUMBNAIL CONCEPT")
    print(DIVIDER)
    print(state.get("thumbnail_concept", "—"))

    print(f"\n📊  TREND ANGLE")
    print(DIVIDER)
    print(state.get("trending_angle", "—"))
    print(state.get("trend_context", "—"))

    if state.get("errors"):
        print(f"\n⚠️   WARNINGS")
        print(DIVIDER)
        for e in state["errors"]:
            print(f"  • {e}")

    approved = state.get("approved", False)
    iterations = state.get("iterations", 0)
    print(f"\n{'✅' if approved else '⚠️ '} Quality gate: {'PASSED' if approved else 'MAX RETRIES'} "
          f"(iteration {iterations})")
    print('═'*60)

    # Save to file
    out_file = Path("output.json")
    out_file.write_text(json.dumps(dict(state), indent=2))
    print(f"\n💾  Full output saved to {out_file.resolve()}\n")


def main():
    topic = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not topic:
        topic = input("🎯  Enter your video topic or niche: ").strip()
    if not topic:
        print("No topic provided. Exiting.")
        sys.exit(1)

    print(f"\n🚀  Generating viral YouTube Short for: \"{topic}\"")
    print(f"    4 agents working in parallel via LangGraph + BMasterAI telemetry\n")

    graph = build_graph()

    initial_state: VideoState = {
        "topic": topic,
        "trending_angle": "",
        "trend_context": "",
        "competitor_hooks": [],
        "hook": "",
        "script": "",
        "title": "",
        "tags": [],
        "thumbnail_concept": "",
        "errors": [],
        "iterations": 0,
        "approved": None,
    }

    final_state = graph.invoke(initial_state)
    print_result(final_state)


if __name__ == "__main__":
    main()
