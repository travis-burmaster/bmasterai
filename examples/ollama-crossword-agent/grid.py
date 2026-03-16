"""
grid.py — Crossword grid state management and constraint engine

Manages the crossword grid and enforces crossing constraints:
  - Stores clue definitions (ACROSS and DOWN)
  - Tracks proposed answers for each clue
  - Commits cells only when all crossings agree
  - Provides crossing context hints ("_ R _ N _") for retries
"""

from typing import Dict, List, Tuple, Optional, Set


class CrosswordGrid:
    """
    Manages a crossword grid with constraint enforcement.

    The grid is indexed as grid[row][col].
    Each clue is identified by (number, direction) where direction is "ACROSS" or "DOWN".
    """

    def __init__(self, size: int = 5):
        """Initialize an empty crossword grid of given size."""
        self.size = size
        self.grid: List[List[str]] = [["." for _ in range(size)] for _ in range(size)]
        self.clues: Dict[Tuple[int, str], Dict] = {}
        self.proposed_answers: Dict[Tuple[int, str], str] = {}

    def add_clue(
        self,
        number: int,
        direction: str,
        start_row: int,
        start_col: int,
        length: int,
        clue_text: str,
    ) -> None:
        """
        Add a clue to the grid.

        Args:
            number: Clue number (1, 2, 3, ...)
            direction: "ACROSS" or "DOWN"
            start_row: Row index of clue start
            start_col: Column index of clue start
            length: Number of cells for this clue
            clue_text: The clue description
        """
        key = (number, direction)
        self.clues[key] = {
            "direction": direction,
            "start_row": start_row,
            "start_col": start_col,
            "length": length,
            "clue_text": clue_text,
            "cells": self._get_cells(start_row, start_col, direction, length),
        }

    def _get_cells(
        self, start_row: int, start_col: int, direction: str, length: int
    ) -> List[Tuple[int, int]]:
        """Get list of (row, col) cells for a clue."""
        cells = []
        for i in range(length):
            if direction == "ACROSS":
                cells.append((start_row, start_col + i))
            else:  # DOWN
                cells.append((start_row + i, start_col))
        return cells

    def propose_answer(self, number: int, direction: str, answer: str) -> bool:
        """
        Propose an answer for a clue.

        Args:
            number: Clue number
            direction: "ACROSS" or "DOWN"
            answer: Proposed answer (uppercase)

        Returns:
            True if answer is valid for the grid, False if it exceeds bounds
        """
        key = (number, direction)
        if key not in self.clues:
            return False

        clue = self.clues[key]
        if len(answer) != clue["length"]:
            return False

        self.proposed_answers[key] = answer.upper()
        return True

    def commit_agreed_cells(self) -> int:
        """
        Commit cells where all crossing answers agree on the same letter.

        Returns:
            Number of cells committed
        """
        committed_count = 0

        # For each cell in the grid
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] != ".":
                    continue  # Already filled or blocked

                # Find all proposed answers that affect this cell
                proposed_letters: Set[str] = set()
                for (num, direction), answer in self.proposed_answers.items():
                    clue = self.clues[(num, direction)]
                    cells = clue["cells"]
                    if (row, col) in cells:
                        cell_index = cells.index((row, col))
                        proposed_letters.add(answer[cell_index])

                # Commit only if there is exactly one proposed letter (and it's a real letter)
                if len(proposed_letters) == 1:
                    letter = proposed_letters.pop()
                    if letter.isalpha():
                        self.grid[row][col] = letter
                        committed_count += 1

        return committed_count

    def commit_all_proposed(self) -> int:
        """
        Force-commit all proposed answers to the grid (trust the solver).

        ACROSS answers are committed first, then DOWN fills remaining cells.
        This ensures ACROSS answers take priority at crossings.

        Returns:
            Number of cells committed
        """
        committed_count = 0
        # Commit ACROSS first
        for (num, direction), answer in self.proposed_answers.items():
            if direction != "ACROSS":
                continue
            clue = self.clues[(num, direction)]
            for i, (row, col) in enumerate(clue["cells"]):
                if self.grid[row][col] == "#":
                    continue
                letter = answer[i]
                if letter.isalpha():
                    self.grid[row][col] = letter
                    committed_count += 1
        # Then DOWN (only fills cells not already set by ACROSS)
        for (num, direction), answer in self.proposed_answers.items():
            if direction != "DOWN":
                continue
            clue = self.clues[(num, direction)]
            for i, (row, col) in enumerate(clue["cells"]):
                if self.grid[row][col] not in (".", "#"):
                    continue  # Already filled by ACROSS
                letter = answer[i]
                if letter.isalpha():
                    self.grid[row][col] = letter
                    committed_count += 1
        return committed_count

    def get_conflicts(self) -> List[Tuple[Tuple[int, int], Set[str]]]:
        """
        Identify conflicted cells (where crossings disagree).

        Returns:
            List of (cell, proposed_letters) tuples
        """
        conflicts = []

        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] != ".":
                    continue

                proposed_letters: Set[str] = set()
                for (num, direction), answer in self.proposed_answers.items():
                    clue = self.clues[(num, direction)]
                    cells = clue["cells"]
                    if (row, col) in cells:
                        cell_index = cells.index((row, col))
                        proposed_letters.add(answer[cell_index])

                # If more than one distinct letter proposed, it's a conflict
                if len(proposed_letters) > 1:
                    conflicts.append(((row, col), proposed_letters))

        return conflicts

    def get_context_for_clue(self, number: int, direction: str) -> str:
        """
        Get crossing context for a clue (e.g., "_ R _ N _" for position hints).

        Returns:
            String representation of grid positions for this clue
        """
        key = (number, direction)
        if key not in self.clues:
            return ""

        clue = self.clues[key]
        cells = clue["cells"]
        parts = []

        for row, col in cells:
            cell_value = self.grid[row][col]
            if cell_value == ".":
                parts.append("_")
            else:
                parts.append(cell_value)

        return " ".join(parts)

    def is_solved(self) -> bool:
        """Check if the entire grid is filled (all non-blocked cells have letters)."""
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == ".":
                    return False
        return True

    def to_display_string(self) -> str:
        """Return ASCII art representation of current grid state."""
        lines = []
        lines.append("┌" + "─" * (self.size * 2 - 1) + "┐")

        for row in range(self.size):
            row_chars = []
            for col in range(self.size):
                cell = self.grid[row][col]
                if cell == ".":
                    row_chars.append("·")
                elif cell == "#":
                    row_chars.append("█")
                else:
                    row_chars.append(cell)
            lines.append("│" + " ".join(row_chars) + "│")

        lines.append("└" + "─" * (self.size * 2 - 1) + "┘")
        return "\n".join(lines)

    def get_empty_cell_count(self) -> int:
        """Return number of unfilled cells (excluding black cells)."""
        count = 0
        for row in range(self.size):
            for col in range(self.size):
                if self.grid[row][col] == ".":
                    count += 1
        return count

    def clear_proposed_answers(self) -> None:
        """Clear all proposed answers (for retry scenarios)."""
        self.proposed_answers.clear()
