"""
vision.py — Ollama vision model helpers

Provides high-level functions to interact with qwen2.5vl:7b for:
  - Extracting clues from crossword screenshots
  - Proposing answers for specific clues with context hints
"""

import base64
import json
from typing import Dict, Optional
import ollama


def screenshot_to_base64(image_bytes: bytes) -> str:
    """
    Convert image bytes to base64 string for Ollama API.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, etc.)

    Returns:
        Base64-encoded string
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def ask_vision(
    prompt: str, image_b64: str, model: str = "qwen2.5:7b"
) -> str:
    """
    Query the Ollama vision model with an image.

    Args:
        prompt: Text prompt for the model
        image_b64: Base64-encoded image string
        model: Model name (default: qwen2.5vl:7b)

    Returns:
        Model's text response
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Vision API error: {e}")


def extract_clues_from_screenshot(image_b64: str) -> Dict[str, Dict[int, str]]:
    """
    Extract crossword clues from a screenshot of the puzzle.

    Sends the screenshot to qwen2.5vl and asks it to identify all ACROSS and DOWN clues.

    Args:
        image_b64: Base64-encoded screenshot

    Returns:
        Dictionary with keys "across" and "down", each mapping number -> clue_text
        Example:
            {
                "across": {1: "Small dog", 2: "Not down", ...},
                "down": {1: "Frozen water", 3: "Beverage", ...}
            }
    """
    prompt = """Please analyze this crossword puzzle screenshot and extract all clues.

Return a JSON object with two keys: "across" and "down".
Each key maps clue number (as integer) to clue text (as string).

Example format:
{
    "across": {1: "Small dog", 2: "Not down"},
    "down": {1: "Frozen water", 3: "Beverage"}
}

Return ONLY the JSON object, no other text."""

    response_text = ask_vision(prompt, image_b64)

    try:
        # Try to extract JSON from the response (it might be wrapped in text)
        lines = response_text.strip().split("\n")
        json_str = ""
        in_json = False

        for line in lines:
            if "{" in line:
                in_json = True
            if in_json:
                json_str += line
            if "}" in line and in_json:
                break

        if not json_str:
            json_str = response_text.strip()

        # Parse and convert integer keys
        clues_raw = json.loads(json_str)

        # Ensure keys are integers
        result = {
            "across": {int(k): v for k, v in clues_raw.get("across", {}).items()},
            "down": {int(k): v for k, v in clues_raw.get("down", {}).items()},
        }
        return result
    except json.JSONDecodeError:
        # Fallback: return empty clues
        return {"across": {}, "down": {}}


def propose_answer(
    clue: str,
    length: int,
    context: str = "",
    image_b64: Optional[str] = None,
    model: str = "qwen2.5:7b",
) -> str:
    """
    Ask the model to propose an answer for a crossword clue.

    Args:
        clue: The clue text (e.g., "Small dog")
        length: Expected answer length
        context: Crossing hints (e.g., "C _ A N _") or empty string
        image_b64: Optional base64-encoded screenshot for visual context
        model: Model name

    Returns:
        Proposed answer (uppercase, exactly 'length' characters)
    """
    context_hint = ""
    if context and any(c.isalpha() for c in context):
        context_hint = f"\nSome letters are already known from crossing answers: {context}\nThe answer must match these known letters in their positions.\n"

    prompt = f"""Crossword clue: "{clue}"
The answer is a single word or phrase with exactly {length} letters, no more, no less.
{context_hint}
What is the {length}-letter answer? Reply with just the answer in UPPERCASE, nothing else."""

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    if image_b64:
        messages[0]["images"] = [image_b64]

    try:
        response = ollama.chat(model=model, messages=messages)
        raw = response["message"]["content"].strip()

        # Extract just alphabetic characters from the response
        import re
        # Try to find the answer: look for a word of the right length
        words = re.findall(r'[A-Za-z]+', raw)
        answer = ""

        # First try: exact length match
        for word in words:
            if len(word) == length:
                answer = word.upper()
                break

        # Second try: first word that's close to the right length
        if not answer:
            for word in words:
                if abs(len(word) - length) <= 1:
                    answer = word.upper()[:length]
                    break

        # Third try: concatenate all alpha chars and truncate
        if not answer:
            all_alpha = re.sub(r'[^A-Za-z]', '', raw).upper()
            if all_alpha:
                answer = all_alpha[:length]

        # Pad if needed
        if answer and len(answer) < length:
            answer = answer.ljust(length, "_")
        elif not answer:
            answer = "_" * length

        return answer
    except Exception as e:
        print(f"   [ollama error] {e}")
        return "_" * length
