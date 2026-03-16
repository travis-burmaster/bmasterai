"""
main.py — CLI entry point for ollama-crossword-agent

Usage:
    python main.py                          # default NYT Mini
    python main.py --url "https://..."      # custom puzzle URL
    python main.py --demo                   # demo mode (no browser)
"""

import sys
import asyncio
import argparse
from pathlib import Path


def check_dependencies():
    """Check that required dependencies are available."""
    missing = []

    try:
        import ollama  # noqa: F401
    except ImportError:
        missing.append("ollama")

    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        missing.append("playwright")

    try:
        from bmasterai.logging import configure_logging  # noqa: F401
    except ImportError:
        missing.append("bmasterai")

    if missing:
        print(f"\n❌  Missing dependencies: {', '.join(missing)}")
        print(f"    Run: pip install -r requirements.txt")
        sys.exit(1)


def main():
    """Main entry point."""
    print("\n" + "═" * 70)
    print("  ollama-crossword-agent")
    print("  Hybrid crossword solver: qwen2.5vl + Playwright + constraint engine")
    print("═" * 70)

    # Load .env if present
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="Solve crossword puzzles with Ollama vision model"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Puzzle URL (default: NYT Mini)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=5,
        help="Grid size (default: 5x5)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo mode (no browser/Ollama needed)",
    )

    args = parser.parse_args()

    # Check dependencies
    check_dependencies()

    # Lazy import after env check
    from agent import CrosswordAgent

    # Run agent
    agent = CrosswordAgent(
        puzzle_url=args.url,
        verbose=True,
        demo_mode=args.demo,
    )

    try:
        result = asyncio.run(agent.run())
        exit_code = 0 if result else 1
    except KeyboardInterrupt:
        print("\n\n⏸️   Interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n\n❌  Error: {e}")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
