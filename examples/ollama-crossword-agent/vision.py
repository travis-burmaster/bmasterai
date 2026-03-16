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
    prompt: str, image_b64: str, model: str = "qwen2.5vl:7b"
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
    model: str = "qwen2.5vl:7b",
) -> str:
    """
    Ask the vision model to propose an answer for a clue.

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
    if context:
        context_hint = f"\n\nCrossing context: {context}\n(Use this to resolve conflicts with crossing answers)"

    image_part = ""
    if image_b64:
        image_part = "\n\nFor reference, the crossword grid is shown in the image."

    prompt = f"""Solve this crossword clue:

Clue: {clue}
Answer length: {length} letters{context_hint}{image_part}

Return ONLY the answer in uppercase, exactly {length} letters. No explanation."""

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
        answer = response["message"]["content"].strip().upper()

        # Ensure answer is exactly the right length (truncate or pad if needed)
        if len(answer) > length:
            answer = answer[:length]
        elif len(answer) < length:
            answer = answer.ljust(length, "_")

        return answer
    except Exception as e:
        # Return placeholder on error
        return "_" * length
