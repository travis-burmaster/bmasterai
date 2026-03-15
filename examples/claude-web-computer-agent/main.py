"""
main.py — CLI entry point for claude-web-computer-agent

Usage:
    python main.py "Search for the latest Claude API pricing and calculate the cost
                    of 1000 calls at 10k tokens each."

    python main.py   # interactive prompt
"""

import sys
import os


def check_env():
    """Warn about missing environment variables before starting."""
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY  (optional — web_search tool will be disabled)")
    if missing:
        for m in missing:
            print(f"  ⚠️  {m} not set")
        if "ANTHROPIC_API_KEY" in str(missing):
            print("\nSet ANTHROPIC_API_KEY to continue. Exiting.")
            sys.exit(1)
        print()


def main():
    print("\n" + "═" * 60)
    print("  claude-web-computer-agent")
    print("  web search + computer use + calculator + BMasterAI")
    print("═" * 60)

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    check_env()

    # Lazy import after env check
    from agent import WebComputerAgent

    # Get query from CLI args or interactive prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("\nEnter your query (or Ctrl+C to quit):")
        print("Examples:")
        print('  "Search for the latest LangChain release notes"')
        print('  "Take a screenshot and describe what you see"')
        print('  "What is 2^32 and how many GB is that?"')
        print()
        try:
            query = input("Query: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            sys.exit(0)

    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)

    # Run
    agent = WebComputerAgent(model="claude-opus-4-6", verbose=True)
    response = agent.run(query)

    print("\n" + "═" * 60)
    print("🗒️  FINAL RESPONSE")
    print("─" * 60)
    print(response)
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
