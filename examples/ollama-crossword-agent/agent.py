"""
agent.py — Crossword-solving agent with hybrid controller

Architecture:
  1. Playwright navigates to puzzle
  2. Screenshots and OCR via qwen2.5vl extracts clues
  3. Model proposes answers for each clue
  4. Constraint engine enforces crossing agreement
  5. Committed cells are typed into the puzzle
  6. Loop until solved or MAX_ROUNDS reached

Every step is instrumented with BMasterAI logging and monitoring.
"""

import time
import base64
import asyncio
from typing import Optional, Dict, List, Tuple
from pathlib import Path

from playwright.async_api import async_playwright, Page
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

from grid import CrosswordGrid
from vision import (
    screenshot_to_base64,
    extract_clues_from_screenshot,
    propose_answer,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

AGENT_ID = "ollama-crossword-agent"
MAX_ROUNDS = 5
MODEL = "qwen2.5vl:7b"
DEFAULT_PUZZLE_URL = "https://www.nytimes.com/crosswords/game/mini"
FALLBACK_PUZZLE_URL = "https://crosswordlabs.com"
GRID_SIZE = 5


# ─────────────────────────────────────────────────────────────────────────────
# Setup BMasterAI
# ─────────────────────────────────────────────────────────────────────────────


def setup_logging():
    """Configure BMasterAI logging and monitoring."""
    configure_logging(
        log_file="logs/agent.log",
        json_log_file="logs/agent.jsonl",
        reasoning_log_file="logs/agent_reasoning.jsonl",
        log_level=LogLevel.INFO,
        enable_console=True,
        enable_file=True,
        enable_json=True,
        enable_reasoning_logs=True,
    )
    return get_logger(), get_monitor()


# ─────────────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────────────


class CrosswordAgent:
    """
    Hybrid crossword-solving agent combining vision, web automation, and constraint logic.

    Flow:
      1. Navigate to puzzle URL via Playwright
      2. Screenshot and extract clues via qwen2.5vl
      3. For each clue, propose answer from model
      4. Constraint engine checks crossing agreements
      5. Commit agreed cells via Playwright
      6. Retry conflicted clues with crossing context
    """

    def __init__(
        self,
        puzzle_url: Optional[str] = None,
        verbose: bool = True,
        demo_mode: bool = False,
    ):
        """
        Initialize the agent.

        Args:
            puzzle_url: URL of crossword puzzle (default: NYT Mini)
            verbose: Enable console output with progress indicators
            demo_mode: Run without browser/Ollama (test mode)
        """
        self.puzzle_url = puzzle_url or DEFAULT_PUZZLE_URL
        self.verbose = verbose
        self.demo_mode = demo_mode
        self.bm, self.monitor = setup_logging()
        self.monitor.start_monitoring()

        self.grid = CrosswordGrid(size=GRID_SIZE)
        self.round = 0
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self) -> bool:
        """
        Run the agent on the puzzle.

        Returns:
            True if puzzle solved, False if not
        """
        self.monitor.track_agent_start(AGENT_ID)
        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.AGENT_START,
            message="Crossword agent started",
            metadata={
                "puzzle_url": self.puzzle_url,
                "grid_size": GRID_SIZE,
                "demo_mode": self.demo_mode,
            },
        )

        if self.verbose:
            print(f"\n{'═' * 70}")
            print(f"🧩  {AGENT_ID}")
            print(f"{'─' * 70}")
            print(f"🎯  Puzzle: {self.puzzle_url}")
            print(f"📊  Grid size: {GRID_SIZE}x{GRID_SIZE}")
            print(f"🤖  Model: {MODEL}")
            print(f"{'═' * 70}\n")

        try:
            if self.demo_mode:
                return await self._run_demo()
            else:
                return await self._run_real()

        except Exception as e:
            import traceback

            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.TASK_ERROR,
                message=f"Agent error: {type(e).__name__}: {e}",
                level=LogLevel.ERROR,
                metadata={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "round": self.round,
                    "traceback": traceback.format_exc(limit=5),
                },
            )
            self.monitor.track_error(AGENT_ID, type(e).__name__)
            raise

        finally:
            self.monitor.track_agent_stop(AGENT_ID)
            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.AGENT_STOP,
                message="Crossword agent stopped",
                metadata={"rounds_used": self.round, "demo_mode": self.demo_mode},
            )
            if self.verbose:
                self._print_dashboard()

    # ── Real mode (Playwright + Ollama) ───────────────────────────────────────

    async def _run_real(self) -> bool:
        """Run with real browser and vision model."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Navigate to puzzle
                if self.verbose:
                    print("🌐  Navigating to puzzle...")

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.TOOL_USE,
                    message="Navigate to puzzle URL",
                    metadata={"url": self.puzzle_url},
                )

                await page.goto(self.puzzle_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)

                # Main loop
                for self.round in range(1, MAX_ROUNDS + 1):
                    if self.verbose:
                        print(f"🔄  Round {self.round}/{MAX_ROUNDS}")

                    # Screenshot
                    screenshot_bytes = await page.screenshot()
                    screenshot_path = (
                        self.screenshots_dir / f"round_{self.round}.png"
                    )
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot_bytes)

                    image_b64 = screenshot_to_base64(screenshot_bytes)

                    self.bm.log_event(
                        agent_id=AGENT_ID,
                        event_type=EventType.TOOL_USE,
                        message=f"Screenshot captured (round {self.round})",
                        metadata={"screenshot": str(screenshot_path)},
                    )

                    # Extract clues on first round
                    if self.round == 1:
                        if self.verbose:
                            print("🧠  Extracting clues from image...")

                        clues = await asyncio.to_thread(
                            extract_clues_from_screenshot, image_b64
                        )
                        self._setup_grid_from_clues(clues)

                        self.bm.log_event(
                            agent_id=AGENT_ID,
                            event_type=EventType.LLM_CALL,
                            message="Clue extraction complete",
                            metadata={
                                "across_count": len(
                                    clues.get("across", {})
                                ),
                                "down_count": len(clues.get("down", {})),
                            },
                        )

                    # Propose answers for all clues
                    if self.verbose:
                        print("🧠  Proposing answers...")

                    await self._propose_all_answers(image_b64)

                    # Commit agreed cells
                    if self.verbose:
                        print("🔧  Checking constraints...")

                    committed = self.grid.commit_agreed_cells()

                    self.bm.log_event(
                        agent_id=AGENT_ID,
                        event_type=EventType.DECISION_POINT,
                        message=f"Committed {committed} cells",
                        metadata={
                            "round": self.round,
                            "cells_committed": committed,
                            "empty_cells": self.grid.get_empty_cell_count(),
                        },
                    )

                    if self.verbose:
                        print(self.grid.to_display_string())
                        print()

                    # Check if solved
                    if self.grid.is_solved():
                        if self.verbose:
                            print("✅  Puzzle solved!")

                        self.bm.log_event(
                            agent_id=AGENT_ID,
                            event_type=EventType.TASK_COMPLETE,
                            message="Puzzle solved",
                            metadata={"round": self.round},
                        )

                        return True

                    # Type answers into cells via Playwright
                    await self._type_answers_into_grid(page)

                # Reached max rounds
                if self.verbose:
                    print(f"⏱️   Reached MAX_ROUNDS ({MAX_ROUNDS})")

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.TASK_ERROR,
                    message=f"Max rounds reached without solving",
                    level=LogLevel.WARNING,
                    metadata={"max_rounds": MAX_ROUNDS},
                )

                return False

            finally:
                await browser.close()

    # ── Demo mode (no browser/Ollama) ──────────────────────────────────────────

    async def _run_demo(self) -> bool:
        """Run in demo mode with hardcoded clues and simulated answers."""
        if self.verbose:
            print("📋  Demo mode: using hardcoded clues\n")

        # Hardcoded demo clues
        demo_clues = {
            "across": {
                1: "Frozen water",
                4: "Not down",
                5: "Beverage",
                6: "Feline pet",
                7: "Opposite of cold",
            },
            "down": {
                1: "Burn with fire",
                2: "Opposite of off",
                3: "Cry of pain",
                4: "Hasty or reckless",
                5: "Consume food",
            },
        }

        self._setup_grid_from_clues(demo_clues)

        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message="Demo mode: clues loaded",
            metadata={
                "across_count": len(demo_clues["across"]),
                "down_count": len(demo_clues["down"]),
            },
        )

        # Simulate answers
        demo_answers = {
            (1, "ACROSS"): "ICE",
            (4, "ACROSS"): "UP",
            (5, "ACROSS"): "TEA",
            (6, "ACROSS"): "CAT",
            (7, "ACROSS"): "HOT",
            (1, "DOWN"): "IGNITE",
            (2, "DOWN"): "ON",
            (3, "DOWN"): "OW",
            (4, "DOWN"): "RASH",
            (5, "DOWN"): "EAT",
        }

        for self.round in range(1, MAX_ROUNDS + 1):
            if self.verbose:
                print(f"🔄  Round {self.round}/{MAX_ROUNDS}")
                print("💭  Proposing answers (simulated)...")

            # Propose answers
            for (number, direction), answer in demo_answers.items():
                self.grid.propose_answer(number, direction, answer)

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.LLM_REASONING,
                    message=f"Proposed answer for clue {number} {direction}",
                    metadata={
                        "number": number,
                        "direction": direction,
                        "answer": answer,
                    },
                )

            # Commit
            committed = self.grid.commit_agreed_cells()

            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.DECISION_POINT,
                message=f"Committed {committed} cells",
                metadata={
                    "round": self.round,
                    "cells_committed": committed,
                    "empty_cells": self.grid.get_empty_cell_count(),
                },
            )

            if self.verbose:
                print(self.grid.to_display_string())
                print()

            if self.grid.is_solved():
                if self.verbose:
                    print("✅  Puzzle solved!")

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.TASK_COMPLETE,
                    message="Puzzle solved",
                    metadata={"round": self.round},
                )

                return True

        if self.verbose:
            print(f"⏱️   Reached MAX_ROUNDS ({MAX_ROUNDS})")

        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TASK_ERROR,
            message=f"Max rounds reached without solving",
            level=LogLevel.WARNING,
            metadata={"max_rounds": MAX_ROUNDS},
        )

        return False

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _setup_grid_from_clues(self, clues: Dict[str, Dict[int, str]]) -> None:
        """
        Set up the grid structure from extracted clues.

        For demo purposes, assumes standard 5x5 grid layout:
        ACROSS: 1 (row 0, col 0), 4 (row 1, col 0), etc.
        DOWN: 1 (row 0, col 0), 2 (row 0, col 1), etc.
        """
        # Standard 5x5 mini crossword layout
        across_clues = clues.get("across", {})
        down_clues = clues.get("down", {})

        # Add ACROSS clues
        for number, clue_text in across_clues.items():
            # Simplified: assume 5-letter across starting at calculated positions
            # In real scenario, this would be parsed from grid visualization
            if number == 1:
                self.grid.add_clue(1, "ACROSS", 0, 0, 5, clue_text)
            elif number == 4:
                self.grid.add_clue(4, "ACROSS", 1, 0, 5, clue_text)
            elif number == 5:
                self.grid.add_clue(5, "ACROSS", 2, 0, 5, clue_text)
            elif number == 6:
                self.grid.add_clue(6, "ACROSS", 3, 0, 5, clue_text)
            elif number == 7:
                self.grid.add_clue(7, "ACROSS", 4, 0, 5, clue_text)

        # Add DOWN clues
        for number, clue_text in down_clues.items():
            # Simplified: assume 5-letter down columns
            if number == 1:
                self.grid.add_clue(1, "DOWN", 0, 0, 5, clue_text)
            elif number == 2:
                self.grid.add_clue(2, "DOWN", 0, 1, 5, clue_text)
            elif number == 3:
                self.grid.add_clue(3, "DOWN", 0, 2, 5, clue_text)
            elif number == 4:
                self.grid.add_clue(4, "DOWN", 0, 3, 5, clue_text)
            elif number == 5:
                self.grid.add_clue(5, "DOWN", 0, 4, 5, clue_text)

    async def _propose_all_answers(self, image_b64: str) -> None:
        """Propose answers for all clues using the vision model."""
        start_time = time.time()

        for (number, direction), clue_info in self.grid.clues.items():
            clue_text = clue_info["clue_text"]
            length = clue_info["length"]
            context = self.grid.get_context_for_clue(number, direction)

            # Call vision model
            answer = await asyncio.to_thread(
                propose_answer,
                clue_text,
                length,
                context,
                image_b64,
                MODEL,
            )

            self.grid.propose_answer(number, direction, answer)

            self.bm.log_event(
                agent_id=AGENT_ID,
                event_type=EventType.LLM_CALL,
                message=f"Proposed answer for {number} {direction}",
                metadata={
                    "clue_number": number,
                    "direction": direction,
                    "answer": answer,
                    "length": length,
                    "context": context,
                },
            )

        latency_ms = int((time.time() - start_time) * 1000)
        self.monitor.track_task_duration(
            AGENT_ID, f"propose_answers_round_{self.round}", latency_ms
        )

    async def _type_answers_into_grid(self, page: Page) -> None:
        """
        Type committed answers into the puzzle via Playwright.

        This is a simplified placeholder — actual implementation would:
        - Find grid input cells by position
        - Click each cell
        - Type the committed letter
        """
        # Placeholder: in real implementation, would click cells and type
        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TOOL_USE,
            message="Type answers into grid (placeholder)",
            metadata={"round": self.round},
        )

    def _print_dashboard(self) -> None:
        """Print telemetry dashboard at the end."""
        if not self.verbose:
            return

        dashboard = self.monitor.get_agent_dashboard(AGENT_ID)

        print(f"\n{'═' * 70}")
        print(f"📊  TELEMETRY DASHBOARD")
        print(f"{'─' * 70}")
        print(f"Agent ID:           {dashboard.get('agent_id', 'N/A')}")
        print(f"Status:             {dashboard.get('status', 'N/A')}")
        print(f"Rounds:             {self.round}/{MAX_ROUNDS}")
        print(f"Grid state:         {self.grid.get_empty_cell_count()} empty cells")
        print(f"Solved:             {self.grid.is_solved()}")
        print(f"{'═' * 70}\n")
