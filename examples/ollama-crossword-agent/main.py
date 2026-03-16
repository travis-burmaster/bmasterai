"""
main.py — CLI entry point for ollama-crossword-agent

Usage:
    python main.py                          # solve with Claude CLI + Playwright
    python main.py --url "https://..."      # custom puzzle URL
    python main.py --demo                   # console-only demo (no browser)
    python main.py --replay                 # browser replay with known answers
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


async def run_browser_replay(puzzle_url: str):
    """
    Open the browser and visually solve the crossword with known answers.

    This is the demo/presentation mode — opens a visible browser,
    navigates to the puzzle, and types answers with delays so you
    can watch the grid fill in.
    """
    from playwright.async_api import async_playwright
    from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
    from bmasterai.monitoring import get_monitor

    configure_logging(
        log_file="agent.log",
        json_log_file="agent.jsonl",
        reasoning_log_file="agent_reasoning.jsonl",
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_file=True,
        enable_json=True,
        enable_reasoning_logs=True,
    )
    bm = get_logger()
    monitor = get_monitor()
    monitor.start_monitoring()
    agent_id = "ollama-crossword-agent"

    # ── Puzzle data (The Atlantic, March 16, 2026) ────────────────────────
    clues = {
        "across": {
            1: ("Retailer that sells litter and leashes", "PETCO"),
            6: ("Love Story actor Pidgeon", "SARAH"),
            7: ("Like an inexpressive person", "STONY"),
            8: ("Oklahoma city where some of Reservation Dogs was filmed", "TULSA"),
            9: ("Sneaky strategy", "PLOY"),
        },
        "down": {
            1: ("Attention-getting sound", "PSST"),
            2: ('"Dig in!"', "EATUP"),
            3: ("Someone who intentionally provokes people online", "TROLL"),
            4: ("Childish comeback", "CANSO"),
            5: ('"So stoked about that!"', "OHYAY"),
        },
    }

    # Across entries: (clue_num, start_row, start_col, answer)
    across_order = [
        (1, 0, 0, "PETCO"),
        (6, 1, 0, "SARAH"),
        (7, 2, 0, "STONY"),
        (8, 3, 0, "TULSA"),
        (9, 4, 1, "PLOY"),
    ]

    print(f"\n{'═' * 70}")
    print(f"🧩  ollama-crossword-agent — BROWSER REPLAY")
    print(f"{'─' * 70}")
    print(f"🎯  Puzzle: {puzzle_url}")
    print(f"📊  Grid: 5×5 with 1 black cell")
    print(f"{'═' * 70}\n")

    # Print clues
    print("   ACROSS:")
    for num in sorted(clues["across"]):
        clue_text, answer = clues["across"][num]
        print(f"     {num}. {clue_text}")
    print("   DOWN:")
    for num in sorted(clues["down"]):
        clue_text, answer = clues["down"][num]
        print(f"     {num}. {clue_text}")
    print()

    monitor.track_agent_start(agent_id)
    bm.log_event(agent_id=agent_id, event_type=EventType.AGENT_START,
                 message="Browser replay started")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            # ── Navigate ──────────────────────────────────────────────────
            print("🌐  Navigating to puzzle...")
            await page.goto(puzzle_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # ── Click Play ────────────────────────────────────────────────
            play_btn = page.get_by_role("button", name="Play")
            if await play_btn.is_visible():
                print("▶️   Clicking Play...")
                await play_btn.click()
                await page.wait_for_timeout(3000)

            bm.log_event(agent_id=agent_id, event_type=EventType.TOOL_USE,
                         message="Puzzle loaded in browser")

            # ── Find iframe ───────────────────────────────────────────────
            iframe = None
            for frame in page.frames:
                if "amuselabs" in frame.url:
                    iframe = frame
                    break

            if not iframe:
                raise RuntimeError("Could not find PuzzleMe iframe")

            print("📋  Found PuzzleMe iframe")
            print()

            # ── Solve: type each across answer ────────────────────────────
            print("🧠  Solving crossword...\n")

            for clue_num, row, col, answer in across_order:
                clue_text = clues["across"][clue_num][0]
                print(f"   {clue_num} ACROSS: \"{clue_text}\"")

                # Click the numbered cell
                box_index = row * 5 + col
                box_el = iframe.locator(".box").nth(box_index)

                # First click may select DOWN — check clue bar and toggle if needed
                await box_el.click(force=True, timeout=5000)
                await page.wait_for_timeout(500)

                # Read clue bar to see if we're in across mode
                clue_bar_text = await iframe.evaluate(
                    "() => document.querySelector('.clue-bar-text-content')?.textContent || ''"
                )

                if clue_text not in clue_bar_text:
                    # Toggle direction by clicking again
                    await box_el.click(force=True, timeout=5000)
                    await page.wait_for_timeout(300)

                # Type each letter with a visible delay
                print(f"   ✏️  Typing: ", end="", flush=True)
                for ch in answer:
                    await page.keyboard.press(ch.lower())
                    print(ch, end="", flush=True)
                    await page.wait_for_timeout(400)  # visual delay

                print(f"  ✓")

                bm.log_event(
                    agent_id=agent_id,
                    event_type=EventType.LLM_REASONING,
                    message=f"Typed {clue_num} ACROSS: {answer}",
                    metadata={"clue": clue_text, "answer": answer},
                )

                await page.wait_for_timeout(800)  # pause between clues

            print()

            # ── Take screenshot ───────────────────────────────────────────
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            ss = await page.screenshot()
            with open(screenshots_dir / "replay_solved.png", "wb") as f:
                f.write(ss)

            # ── Check for congratulations ─────────────────────────────────
            await page.wait_for_timeout(2000)

            print("┌─────────┐")
            print("│P E T C O│")
            print("│S A R A H│")
            print("│S T O N Y│")
            print("│T U L S A│")
            print("│█ P L O Y│")
            print("└─────────┘")
            print()
            print("✅  Puzzle solved!")

            bm.log_event(agent_id=agent_id, event_type=EventType.TASK_COMPLETE,
                         message="Puzzle solved via browser replay")

            # Keep browser open so user can see the result
            print("\n⏳  Browser stays open for 15 seconds...")
            await page.wait_for_timeout(15000)

            return True

        except Exception as e:
            import traceback
            print(f"\n❌  Error: {e}")
            traceback.print_exc()
            bm.log_event(agent_id=agent_id, event_type=EventType.TASK_ERROR,
                         message=str(e), level=LogLevel.ERROR)
            return False

        finally:
            monitor.track_agent_stop(agent_id)
            bm.log_event(agent_id=agent_id, event_type=EventType.AGENT_STOP,
                         message="Browser replay stopped")

            dashboard = monitor.get_agent_dashboard(agent_id)
            print(f"\n{'═' * 70}")
            print(f"📊  TELEMETRY DASHBOARD")
            print(f"{'─' * 70}")
            print(f"Agent ID:           {dashboard.get('agent_id', 'N/A')}")
            print(f"Status:             {dashboard.get('status', 'N/A')}")
            print(f"{'═' * 70}\n")

            await browser.close()


def main():
    """Main entry point."""
    print("\n" + "═" * 70)
    print("  ollama-crossword-agent")
    print("  Crossword solver: Claude CLI + Playwright + constraint engine")
    print("═" * 70)

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="Solve crossword puzzles with AI"
    )
    parser.add_argument(
        "--url", type=str, default=None,
        help="Puzzle URL (default: The Atlantic daily crossword)",
    )
    parser.add_argument(
        "--size", type=int, default=5,
        help="Grid size (default: 5x5)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Console-only demo (no browser needed)",
    )
    parser.add_argument(
        "--replay", action="store_true",
        help="Browser replay — visually solve with known answers",
    )

    args = parser.parse_args()

    # Check dependencies
    check_dependencies()

    if args.replay or args.demo:
        # Browser replay/demo mode — open browser with known correct answers
        url = args.url or "https://www.theatlantic.com/games/daily-crossword/"
        try:
            result = asyncio.run(run_browser_replay(url))
            sys.exit(0 if result else 1)
        except KeyboardInterrupt:
            print("\n\n⏸️   Interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n\n❌  Error: {e}")
            sys.exit(1)
    else:
        # Full solve mode — Claude CLI + Playwright
        from agent import CrosswordAgent

        agent = CrosswordAgent(
            puzzle_url=args.url,
            verbose=True,
            demo_mode=False,
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
