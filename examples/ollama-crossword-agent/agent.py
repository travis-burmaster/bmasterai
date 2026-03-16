"""
agent.py — Crossword-solving agent with hybrid controller

Architecture:
  1. Playwright navigates to The Atlantic's daily crossword (PuzzleMe widget)
  2. Clues are extracted from the DOM (more reliable than OCR)
  3. Grid structure is inferred from clue numbers and black cells
  4. Ollama proposes answers for each clue
  5. Constraint engine enforces crossing agreement
  6. Answers are typed into the puzzle via keyboard
  7. Loop until solved or MAX_ROUNDS reached

Every step is instrumented with BMasterAI logging and monitoring.
"""

import time
import re
import base64
import asyncio
from typing import Optional, Dict, List, Tuple
from pathlib import Path

from playwright.async_api import async_playwright, Page, Frame
from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
from bmasterai.monitoring import get_monitor

from grid import CrosswordGrid
from vision import (
    screenshot_to_base64,
    propose_answer,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

AGENT_ID = "ollama-crossword-agent"
MAX_ROUNDS = 100
MODEL = "qwen2.5:7b"
DEFAULT_PUZZLE_URL = "https://www.theatlantic.com/games/daily-crossword/"
FALLBACK_PUZZLE_URL = "https://crosswordlabs.com"
GRID_SIZE = 5


# ─────────────────────────────────────────────────────────────────────────────
# Setup BMasterAI
# ─────────────────────────────────────────────────────────────────────────────


def setup_logging():
    """Configure BMasterAI logging and monitoring."""
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
        """Run with real browser and vision model against The Atlantic's PuzzleMe widget."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})

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

                await page.goto(self.puzzle_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)

                # Click "Play" button on the landing page
                play_btn = page.get_by_role("button", name="Play")
                if await play_btn.is_visible():
                    if self.verbose:
                        print("▶️   Clicking Play...")
                    await play_btn.click()
                    await page.wait_for_timeout(3000)

                # Find the PuzzleMe iframe
                iframe = await self._get_puzzle_iframe(page)
                if not iframe:
                    raise RuntimeError("Could not find PuzzleMe iframe")

                if self.verbose:
                    print("📋  Found PuzzleMe iframe")

                # Extract clues from the DOM
                if self.verbose:
                    print("📖  Extracting clues from DOM...")

                clues = await self._extract_clues_from_dom(iframe)
                grid_layout = await self._detect_grid_layout(iframe)

                if not clues.get("across") and not clues.get("down"):
                    raise RuntimeError(
                        "Could not extract any clues from the puzzle. "
                        "The PuzzleMe widget structure may have changed."
                    )

                self._setup_grid_dynamic(clues, grid_layout)

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.LLM_CALL,
                    message="Clue extraction complete",
                    metadata={
                        "across_count": len(clues.get("across", {})),
                        "down_count": len(clues.get("down", {})),
                        "grid_layout": str(grid_layout),
                    },
                )

                if self.verbose:
                    print(f"   Found {len(clues.get('across', {}))} across, {len(clues.get('down', {}))} down clues")
                    for direction in ["across", "down"]:
                        for num, text in sorted(clues.get(direction, {}).items()):
                            length = self.grid.clues.get((num, direction.upper()), {}).get("length", "?")
                            print(f"   {num} {direction.upper()} ({length} letters): {text}")

                # Main solving loop
                for self.round in range(1, MAX_ROUNDS + 1):
                    if self.verbose:
                        print(f"\n🔄  Round {self.round}/{MAX_ROUNDS}")

                    # Screenshot for reference
                    screenshot_bytes = await page.screenshot()
                    screenshot_path = self.screenshots_dir / f"round_{self.round}.png"
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot_bytes)

                    self.bm.log_event(
                        agent_id=AGENT_ID,
                        event_type=EventType.TOOL_USE,
                        message=f"Screenshot captured (round {self.round})",
                        metadata={"screenshot": str(screenshot_path)},
                    )

                    # Propose answers using Ollama
                    if self.verbose:
                        print("🧠  Proposing answers...")

                    await self._propose_all_answers_text()

                    # Commit agreed cells
                    if self.verbose:
                        print("🔧  Checking constraints...")

                    # Trust the solver — commit all proposed answers each round
                    # PuzzleMe will validate correctness when we type them in
                    if len(self.grid.proposed_answers) >= len(self.grid.clues):
                        committed = self.grid.commit_all_proposed()
                    else:
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

                    # Check if grid is full — type answers and verify with PuzzleMe
                    if self.grid.is_solved():
                        if self.verbose:
                            print("📝  Grid full — typing into puzzle...")

                        await self._type_answers_into_puzzleme(iframe)
                        await page.wait_for_timeout(2000)

                        # Check if PuzzleMe shows congratulations
                        puzzle_solved = await self._check_puzzle_complete(iframe, page)

                        if puzzle_solved:
                            if self.verbose:
                                print("✅  Puzzle solved! PuzzleMe confirmed correct!")

                            final_ss = await page.screenshot()
                            with open(self.screenshots_dir / "final.png", "wb") as f:
                                f.write(final_ss)

                            self.bm.log_event(
                                agent_id=AGENT_ID,
                                event_type=EventType.TASK_COMPLETE,
                                message="Puzzle solved",
                                metadata={"round": self.round},
                            )

                            return True
                        else:
                            if self.verbose:
                                print("❌  PuzzleMe did not confirm — answers may be wrong.")
                                print("🔄  Clearing grid and retrying...\n")

                            # Reset internal grid and clear PuzzleMe
                            await self._clear_puzzleme_grid(iframe, page)
                            self.grid.proposed_answers.clear()
                            for r in range(self.grid.size):
                                for c in range(self.grid.size):
                                    if self.grid.grid[r][c] != "#":
                                        self.grid.grid[r][c] = "."

                # Reached max rounds — still type what we have
                if self.verbose:
                    print(f"\n⏱️   Reached MAX_ROUNDS ({MAX_ROUNDS})")
                    print("📝  Typing best answers into grid...")

                await self._type_answers_into_puzzleme(iframe)

                final_ss = await page.screenshot()
                with open(self.screenshots_dir / "final.png", "wb") as f:
                    f.write(final_ss)

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.TASK_ERROR,
                    message="Max rounds reached without solving",
                    level=LogLevel.WARNING,
                    metadata={"max_rounds": MAX_ROUNDS},
                )

                return False

            finally:
                # Keep browser open briefly so user can see result
                if self.verbose:
                    print("\n⏳  Browser stays open for 20 seconds...")
                await page.wait_for_timeout(20000)
                await browser.close()

    # ── Demo mode (no browser/Ollama) ──────────────────────────────────────────

    async def _run_demo(self) -> bool:
        """Run in demo mode with The Atlantic's March 16, 2026 puzzle."""
        if self.verbose:
            print("📋  Demo mode: The Atlantic daily crossword (March 16, 2026)\n")
            print("   By Amanda Rafkin; edited by Kelsey Dixon\n")

        # The Atlantic daily crossword — March 16, 2026
        demo_clues = {
            "across": {
                1: "Retailer that sells litter and leashes",
                6: "Love Story actor Pidgeon",
                7: "Like an inexpressive person",
                8: "Oklahoma city where some of Reservation Dogs was filmed",
                9: "Sneaky strategy",
            },
            "down": {
                1: "Attention-getting sound",
                2: '"Dig in!"',
                3: "Someone who intentionally provokes people online",
                4: "Childish comeback",
                5: '"So stoked about that!"',
            },
        }

        # Grid layout: 5x5 with black cell at (4,0)
        self.grid.grid[4][0] = "#"

        # Set up clues with correct positions
        self.grid.add_clue(1, "ACROSS", 0, 0, 5, demo_clues["across"][1])
        self.grid.add_clue(6, "ACROSS", 1, 0, 5, demo_clues["across"][6])
        self.grid.add_clue(7, "ACROSS", 2, 0, 5, demo_clues["across"][7])
        self.grid.add_clue(8, "ACROSS", 3, 0, 5, demo_clues["across"][8])
        self.grid.add_clue(9, "ACROSS", 4, 1, 4, demo_clues["across"][9])
        self.grid.add_clue(1, "DOWN", 0, 0, 4, demo_clues["down"][1])
        self.grid.add_clue(2, "DOWN", 0, 1, 5, demo_clues["down"][2])
        self.grid.add_clue(3, "DOWN", 0, 2, 5, demo_clues["down"][3])
        self.grid.add_clue(4, "DOWN", 0, 3, 5, demo_clues["down"][4])
        self.grid.add_clue(5, "DOWN", 0, 4, 5, demo_clues["down"][5])

        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.LLM_CALL,
            message="Demo mode: clues loaded",
            metadata={
                "across_count": len(demo_clues["across"]),
                "down_count": len(demo_clues["down"]),
            },
        )

        if self.verbose:
            print("   Across:")
            for num, clue in sorted(demo_clues["across"].items()):
                length = self.grid.clues[(num, "ACROSS")]["length"]
                print(f"     {num}. {clue} ({length} letters)")
            print("   Down:")
            for num, clue in sorted(demo_clues["down"].items()):
                length = self.grid.clues[(num, "DOWN")]["length"]
                print(f"     {num}. {clue} ({length} letters)")
            print()

        # Solved answers (verified with all crossings)
        demo_answers = {
            (1, "ACROSS"): "PETCO",
            (6, "ACROSS"): "SARAH",
            (7, "ACROSS"): "STONY",
            (8, "ACROSS"): "TULSA",
            (9, "ACROSS"): "PLOY",
            (1, "DOWN"): "PSST",
            (2, "DOWN"): "EATUP",
            (3, "DOWN"): "TROLL",
            (4, "DOWN"): "CANSO",
            (5, "DOWN"): "OHYAY",
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

    # ── PuzzleMe iframe helpers ────────────────────────────────────────────────

    async def _get_puzzle_iframe(self, page: Page) -> Optional[Frame]:
        """Find the PuzzleMe iframe within the page."""
        # Primary: look for amuselabs/puzzleme URL
        for frame in page.frames:
            url = frame.url
            if "amuselabs" in url or "puzzleme" in url.lower():
                return frame
        # Fallback: look for frame with crossword content
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                has_clues = await frame.query_selector(".clue, .crossword, .box")
                if has_clues:
                    return frame
            except Exception:
                continue
        return None

    async def _extract_clues_from_dom(self, iframe: Frame) -> Dict[str, Dict[int, str]]:
        """Extract crossword clues from the PuzzleMe iframe DOM."""
        clues = {"across": {}, "down": {}}

        # First, dump the raw text so we can debug
        try:
            page_text = await iframe.evaluate("() => document.body.innerText")
            if self.verbose:
                print(f"   [debug] iframe text length: {len(page_text)}")
                # Print first 500 chars for debugging
                for line in page_text.split("\n")[:30]:
                    stripped = line.strip()
                    if stripped:
                        print(f"   [debug] > {stripped}")
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Could not read iframe text: {e}")
            page_text = ""

        # Try parsing from text content
        clues = self._parse_clues_from_text(page_text)

        # If that didn't work, try JS-based extraction
        if not clues["across"] and not clues["down"]:
            if self.verbose:
                print("   🔄  Text parsing failed, trying JS extraction...")
            try:
                clues = await iframe.evaluate("""
                    () => {
                        const result = {across: {}, down: {}};
                        const allDivs = [...document.querySelectorAll('div')];
                        let direction = null;

                        for (let i = 0; i < allDivs.length; i++) {
                            const div = allDivs[i];
                            const text = div.textContent.trim();
                            const ownText = div.childNodes.length === 1 &&
                                            div.childNodes[0].nodeType === 3 ?
                                            div.childNodes[0].textContent.trim() : null;

                            if (ownText === 'Across') { direction = 'across'; continue; }
                            if (ownText === 'Down') { direction = 'down'; continue; }

                            // Look for clue number + text pairs
                            if (direction) {
                                const numEl = div.querySelector('div');
                                if (numEl) {
                                    const numText = numEl.textContent.trim().replace(/"/g, '');
                                    const num = parseInt(numText);
                                    if (!isNaN(num) && num > 0 && num < 50) {
                                        // Get the sibling or next div for clue text
                                        const siblings = [...div.children];
                                        if (siblings.length >= 2) {
                                            const clueText = siblings[1].textContent.trim();
                                            if (clueText && clueText.length > 2) {
                                                result[direction][num] = clueText;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        return result;
                    }
                """)
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  JS extraction failed: {e}")

        return clues

    def _parse_clues_from_text(self, text: str) -> Dict[str, Dict[int, str]]:
        """Parse clues from the page text content."""
        clues = {"across": {}, "down": {}}
        lines = text.split("\n")
        current_direction = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower = line.lower()
            if lower == "across":
                current_direction = "across"
                continue
            elif lower == "down":
                current_direction = "down"
                continue

            if current_direction:
                # Match lines like:
                # "1 Retailer that sells litter and leashes"
                # '"1" Retailer that sells...'
                # "1" followed by text on next line
                match = re.match(r'^["\u201c]?(\d+)["\u201d]?\s*(.*)$', line)
                if match:
                    num = int(match.group(1))
                    clue_text = match.group(2).strip()
                    if clue_text and len(clue_text) > 1:
                        clues[current_direction][num] = clue_text
                    elif current_direction and num > 0:
                        # Number might be on its own line, clue on next line
                        # Store the number and pick up text from next iteration
                        clues.setdefault("_pending_num", {})[current_direction] = num

                elif "_pending_num" in clues and current_direction in clues["_pending_num"]:
                    # This line is the clue text for the pending number
                    pending_num = clues["_pending_num"].pop(current_direction)
                    if line and len(line) > 1:
                        clues[current_direction][pending_num] = line

        # Clean up temp key
        clues.pop("_pending_num", None)
        return clues

    async def _detect_grid_layout(self, iframe: Frame) -> Dict:
        """
        Detect the grid layout from the PuzzleMe iframe.

        Returns dict with:
          - size: grid dimension
          - black_cells: list of [row, col] that are black/blocked
          - numbered_cells: dict of number_str -> [row, col]
          - all_cells: list of {row, col, black, number}
        """
        layout = await iframe.evaluate("""
            () => {
                const result = {cells: [], size: 0, black_cells: [], numbered_cells: {}, debug: ''};

                // PuzzleMe uses .box elements for grid cells (ordered L-to-R, T-to-B)
                const boxes = document.querySelectorAll('.box');
                if (boxes.length === 0) {
                    result.debug = 'No .box elements found';
                    return result;
                }

                // Determine grid size from total box count (square grid)
                const gridSize = Math.round(Math.sqrt(boxes.length));
                result.size = gridSize;
                result.debug = `Found ${boxes.length} boxes, grid size ${gridSize}x${gridSize}`;

                // Map each box to (row, col) based on sequential order
                for (let i = 0; i < boxes.length; i++) {
                    const box = boxes[i];
                    const row = Math.floor(i / gridSize);
                    const col = i % gridSize;

                    // Black cells have class 'empty' (no 'letter' class)
                    const isBlack = box.classList.contains('empty') ||
                                    (!box.classList.contains('letter') && !box.classList.contains('block'));

                    // Get clue number if present
                    const numEl = box.querySelector('.cluenum-in-box');
                    let number = null;
                    if (numEl) {
                        // Remove zero-width joiners
                        number = numEl.textContent.replace(/\\u200d/g, '').trim();
                    }

                    result.cells.push({row, col, black: isBlack, number});
                    if (isBlack) result.black_cells.push([row, col]);
                    if (number && /^\\d+$/.test(number)) result.numbered_cells[number] = [row, col];
                }

                return result;
            }
        """)

        if self.verbose:
            print(f"   Grid layout: size={layout.get('size', '?')}, "
                  f"cells={len(layout.get('cells', []))}, "
                  f"black={layout.get('black_cells', [])}, "
                  f"numbered={layout.get('numbered_cells', {})}")
            if layout.get('debug'):
                print(f"   [debug DOM] {layout['debug']}")

        return layout

    def _setup_grid_dynamic(self, clues: Dict[str, Dict[int, str]], layout: Dict) -> None:
        """
        Set up the grid from clues and detected DOM layout.

        Uses the actual cell positions from the PuzzleMe DOM when available,
        falling back to heuristic inference.
        """
        across_clues = clues.get("across", {})
        down_clues = clues.get("down", {})

        if self.verbose:
            print(f"   Across clue numbers: {sorted(across_clues.keys())}")
            print(f"   Down clue numbers: {sorted(down_clues.keys())}")

        # Get numbered cell positions from DOM layout
        numbered_cells = layout.get("numbered_cells", {})
        black_cells_list = layout.get("black_cells", [])
        dom_size = layout.get("size", 0)

        # Update grid size if DOM detected it and found actual cells
        has_dom_data = len(layout.get("cells", [])) > 0
        if has_dom_data and dom_size > 1 and dom_size != self.grid.size:
            if self.verbose:
                print(f"   Resizing grid from {self.grid.size} to {dom_size}")
            self.grid = CrosswordGrid(size=dom_size)

        # Convert numbered_cells keys from string to int and values to tuples
        num_positions = {}
        for num_str, pos in numbered_cells.items():
            num_positions[int(num_str)] = (pos[0], pos[1])

        # Mark black cells in grid
        black_set = set()
        for bc in black_cells_list:
            r, c = bc[0], bc[1]
            self.grid.grid[r][c] = "#"
            black_set.add((r, c))

        if self.verbose and num_positions:
            print(f"   DOM numbered positions: {num_positions}")
            print(f"   DOM black cells: {black_set}")

        # If DOM didn't give us positions, infer them
        if not num_positions:
            num_positions = self._infer_numbered_positions(
                sorted(set(list(across_clues.keys()) + list(down_clues.keys()))),
                across_clues, down_clues
            )

        grid_size = self.grid.size

        # Add across clues
        for num, clue_text in across_clues.items():
            if num in num_positions:
                row, col = num_positions[num]
                # Calculate length: extend right until edge or black cell
                length = 0
                for c in range(col, grid_size):
                    if (row, c) in black_set:
                        break
                    length += 1
                if length > 0:
                    self.grid.add_clue(num, "ACROSS", row, col, length, clue_text)

        # Add down clues
        for num, clue_text in down_clues.items():
            if num in num_positions:
                row, col = num_positions[num]
                # Calculate length: extend down until edge or black cell
                length = 0
                for r in range(row, grid_size):
                    if (r, col) in black_set:
                        break
                    length += 1
                if length > 0:
                    self.grid.add_clue(num, "DOWN", row, col, length, clue_text)

    def _infer_numbered_positions(
        self,
        all_nums: List[int],
        across_clues: Dict[int, str],
        down_clues: Dict[int, str],
    ) -> Dict[int, Tuple[int, int]]:
        """
        Fallback: infer (row, col) positions for numbered cells.

        Used when DOM detection doesn't return cell positions.
        """
        positions = {}
        across_nums = sorted(across_clues.keys())
        down_nums = sorted(down_clues.keys())

        # Row 0: all down entries start here, plus first across
        col = 0
        for num in sorted(set([across_nums[0]] + down_nums)):
            if num in positions:
                continue
            positions[num] = (0, col)
            col += 1

        # Remaining across clues go to subsequent rows
        row = 1
        for num in across_nums[1:]:
            if num in positions:
                row += 1
                continue

            expected_at_row_0 = max(positions.keys()) + 1 if positions else num
            if num == expected_at_row_0:
                positions[num] = (row, 0)
            else:
                positions[num] = (row, 1)
                self.grid.grid[row][0] = "#"

            row += 1

        return positions

    async def _propose_all_answers_text(self) -> None:
        """Propose answers for all clues using Claude CLI."""
        import subprocess
        start_time = time.time()

        # Build a single prompt with ALL clues for cross-referencing
        clue_lines = []
        for (number, direction), clue_info in sorted(self.grid.clues.items()):
            context = self.grid.get_context_for_clue(number, direction)
            ctx_str = ""
            if any(c.isalpha() for c in context):
                ctx_str = f" [known letters: {context}]"
            clue_lines.append(
                f"{number} {direction} ({clue_info['length']} letters): "
                f"{clue_info['clue_text']}{ctx_str}"
            )

        prompt = f"""Crossword puzzle. Answers must interlock. Reply ONLY with answers, no explanation.

{chr(10).join(clue_lines)}

Format:
1 ACROSS: XXXXX
6 ACROSS: XXXXX
7 ACROSS: XXXXX
8 ACROSS: XXXXX
9 ACROSS: XXXX
1 DOWN: XXXX
2 DOWN: XXXXX
3 DOWN: XXXXX
4 DOWN: XXXXX
5 DOWN: XXXXX"""

        if self.verbose:
            print("   📡  Calling Claude CLI...")

        try:
            # Write prompt to temp file and pipe it to claude
            import tempfile, os
            prompt_file = tempfile.mktemp(suffix=".txt")
            with open(prompt_file, "w") as f:
                f.write(prompt)

            result = await asyncio.to_thread(
                subprocess.run,
                f'cat "{prompt_file}" | claude -p',
                capture_output=True,
                text=True,
                shell=True,
                timeout=300,
            )

            os.unlink(prompt_file)

            if result.returncode != 0:
                raise RuntimeError(f"Claude CLI error: {result.stderr.strip()}")

            raw = result.stdout.strip()

            if self.verbose:
                print(f"   [claude response]\n{raw}\n")

            # Parse response — collect all answer sets, use the last complete one
            # (Claude sometimes revises mid-response)
            answers = {}
            for line in raw.split("\n"):
                line = line.strip()
                if not line:
                    continue
                match = re.match(
                    r'(\d+)\s*(ACROSS|DOWN|A|D)[:\s]+([A-Za-z]+)',
                    line, re.IGNORECASE
                )
                if match:
                    num = int(match.group(1))
                    dir_raw = match.group(2).upper()
                    direction = "ACROSS" if dir_raw in ("ACROSS", "A") else "DOWN"
                    answer = match.group(3).upper()
                    key = (num, direction)
                    if key in self.grid.clues:
                        # Overwrite with latest answer (last revision wins)
                        answers[key] = answer

            # Apply collected answers
            for key, answer in answers.items():
                num, direction = key
                expected_len = self.grid.clues[key]["length"]
                if len(answer) > expected_len:
                    answer = answer[:expected_len]
                elif len(answer) < expected_len:
                    answer = answer.ljust(expected_len, "_")

                self.grid.propose_answer(num, direction, answer)

                if self.verbose:
                    ctx = self.grid.get_context_for_clue(num, direction)
                    print(f"   {num} {direction}: {answer} (context: {ctx})")

                self.bm.log_event(
                    agent_id=AGENT_ID,
                    event_type=EventType.LLM_CALL,
                    message=f"Proposed answer for {num} {direction}",
                    metadata={
                        "clue_number": num,
                        "direction": direction,
                        "answer": answer,
                        "length": expected_len,
                    },
                )

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Claude CLI failed: {e}")
                print("   🔄  Falling back to Ollama...")
            # Fallback to Ollama
            for (number, direction), clue_info in self.grid.clues.items():
                answer = await asyncio.to_thread(
                    propose_answer,
                    clue_info["clue_text"],
                    clue_info["length"],
                    self.grid.get_context_for_clue(number, direction),
                    None, MODEL,
                )
                clean = re.sub(r'[^A-Z]', '', answer.upper())
                length = clue_info["length"]
                if len(clean) > length:
                    clean = clean[:length]
                elif len(clean) < length:
                    clean = clean.ljust(length, "_")
                self.grid.propose_answer(number, direction, clean)

        latency_ms = int((time.time() - start_time) * 1000)
        self.monitor.track_task_duration(
            AGENT_ID, f"propose_answers_round_{self.round}", latency_ms
        )

    async def _type_answers_into_puzzleme(self, iframe: Frame) -> None:
        """
        Type committed answers into the PuzzleMe grid.

        Strategy: for each across clue, click the starting cell, verify
        we're in ACROSS mode via the clue bar, then type each letter.
        """
        self.bm.log_event(
            agent_id=AGENT_ID,
            event_type=EventType.TOOL_USE,
            message="Typing answers into PuzzleMe grid",
            metadata={"round": self.round},
        )

        # Dismiss any modal dialogs first
        try:
            modal_btns = iframe.locator('.confirm-yes, .confirm-no, .close-btn, [class*="modal"] button')
            if await modal_btns.first.is_visible(timeout=1000):
                await modal_btns.first.click(force=True)
                await asyncio.sleep(0.5)
        except Exception:
            pass

        grid_size = self.grid.size
        page = iframe.page

        for (num, direction), clue_info in sorted(self.grid.clues.items()):
            if direction != "ACROSS":
                continue

            cells = clue_info["cells"]
            clue_text = clue_info["clue_text"]
            answer = ""
            for row, col in cells:
                cell_val = self.grid.grid[row][col]
                if cell_val in (".", "#", "_"):
                    answer += " "
                else:
                    answer += cell_val

            if not answer.strip():
                continue

            try:
                # Click the starting cell
                start_row, start_col = cells[0]
                box_index = start_row * grid_size + start_col
                box_el = iframe.locator('.box').nth(box_index)
                await box_el.click(force=True, timeout=5000)
                await asyncio.sleep(0.3)

                # Check clue bar to see if we're in ACROSS mode
                clue_bar = await iframe.evaluate(
                    "() => document.querySelector('.clue-bar-text-content')?.textContent || ''"
                )

                # If clue bar doesn't match our across clue, click again to toggle
                if clue_text not in clue_bar:
                    await box_el.click(force=True, timeout=3000)
                    await asyncio.sleep(0.3)

                # Type each letter with delay
                for ch in answer:
                    if ch == " ":
                        await page.keyboard.press("ArrowRight")
                    else:
                        await page.keyboard.press(ch.lower())
                    await asyncio.sleep(0.15)

                if self.verbose:
                    print(f"   ✏️  Typed {num} {direction}: {answer}")

                await asyncio.sleep(0.3)

            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Could not type {num} {direction}: {e}")

    async def _check_puzzle_complete(self, iframe: Frame, page: Page) -> bool:
        """Check if PuzzleMe shows a congratulations/completion message."""
        try:
            # PuzzleMe shows a modal with "Congratulations" when solved
            page_text = await page.evaluate("() => document.body.innerText")
            if "congratulations" in page_text.lower():
                return True

            # Also check iframe
            iframe_text = await iframe.evaluate("() => document.body.innerText")
            if "congratulations" in iframe_text.lower():
                return True
            if "completed" in iframe_text.lower():
                return True

            return False
        except Exception:
            return False

    async def _clear_puzzleme_grid(self, iframe: Frame, page: Page) -> None:
        """Clear all entries in the PuzzleMe grid for a retry."""
        try:
            # Click first cell
            first_box = iframe.locator('.box').first
            await first_box.click(force=True, timeout=3000)
            await asyncio.sleep(0.3)

            # Select all and delete — Ctrl+A then delete each cell
            # PuzzleMe: use Assist > Clear Puzzle if available, or manually clear
            # Try clicking Assist button
            assist_btn = iframe.locator('button:has-text("Assist")')
            if await assist_btn.is_visible(timeout=2000):
                await assist_btn.click(force=True)
                await asyncio.sleep(0.5)

                # Look for "Clear all" or "Reset" option
                clear_btn = iframe.locator('text=/clear|reset/i').first
                if await clear_btn.is_visible(timeout=2000):
                    await clear_btn.click(force=True)
                    await asyncio.sleep(0.5)

                    # Confirm if needed
                    confirm_btn = iframe.locator('.confirm-yes, button:has-text("Yes")').first
                    if await confirm_btn.is_visible(timeout=1000):
                        await confirm_btn.click(force=True)
                        await asyncio.sleep(0.5)
                    return

            # Fallback: manually clear by typing spaces/delete in each cell
            for i in range(self.grid.size * self.grid.size):
                box = iframe.locator('.box.letter').nth(i)
                try:
                    await box.click(force=True, timeout=1000)
                    await page.keyboard.press("Delete")
                    await asyncio.sleep(0.05)
                except Exception:
                    continue

        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Could not clear grid: {e}")

    # ── Legacy internal helpers (kept for demo mode) ─────────────────────────

    def _setup_grid_from_clues(self, clues: Dict[str, Dict[int, str]]) -> None:
        """Set up grid from clues — legacy method for demo mode."""
        across_clues = clues.get("across", {})
        down_clues = clues.get("down", {})

        for number, clue_text in across_clues.items():
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

        for number, clue_text in down_clues.items():
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
