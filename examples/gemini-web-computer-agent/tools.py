"""
tools.py — Tool schemas and dispatch for gemini-web-computer-agent

Defines two tool types:
  1. web_search    — Tavily search (client-side wrapper)
  2. computer_use  — screenshot, click, type, key, scroll via xdotool + scrot

All tools log TOOL_USE events via BMasterAI before and after execution.
"""

import os
import base64
import subprocess
from typing import Any, Dict, List, Optional

# ── Optional imports (graceful degradation) ──────────────────────────────────
try:
    from tavily import TavilyClient
    _tavily_available = True
except ImportError:
    _tavily_available = False


# ─────────────────────────────────────────────────────────────────────────────
# Tool JSON schemas (passed to Gemini in the `tools` array)
# ─────────────────────────────────────────────────────────────────────────────

WEB_SEARCH_SCHEMA = {
    "name": "web_search",
    "description": (
        "Search the web for current information using Tavily. "
        "Use this when you need up-to-date facts, news, documentation, or any "
        "information that may not be in your training data."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (1–10). Defaults to 5.",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

COMPUTER_USE_SCHEMA = {
    "name": "computer_use",
    "description": (
        "Take a screenshot of the current screen, click on UI elements, "
        "type text, or press keys. Use this to interact with desktop "
        "applications, browsers, or observe the current screen state."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["screenshot", "click", "type", "key", "scroll"],
                "description": (
                    "Action to perform:\n"
                    "  screenshot — capture current screen\n"
                    "  click      — click at (x, y)\n"
                    "  type       — type a string of text\n"
                    "  key        — press a keyboard shortcut (e.g. 'ctrl+c')\n"
                    "  scroll     — scroll at (x, y) by delta"
                ),
            },
            "x": {
                "type": "integer",
                "description": "X coordinate (required for click/scroll).",
            },
            "y": {
                "type": "integer",
                "description": "Y coordinate (required for click/scroll).",
            },
            "text": {
                "type": "string",
                "description": "Text to type (required for type action).",
            },
            "key": {
                "type": "string",
                "description": "Key or key combo to press (required for key action). E.g. 'Return', 'ctrl+c'.",
            },
            "delta_y": {
                "type": "integer",
                "description": "Scroll delta in pixels, positive = down (required for scroll).",
                "default": 300,
            },
        },
        "required": ["action"],
    },
}

# All schemas to pass to Gemini
ALL_TOOL_SCHEMAS: List[Dict] = [
    WEB_SEARCH_SCHEMA,
    COMPUTER_USE_SCHEMA,
]


# ─────────────────────────────────────────────────────────────────────────────
# Tool implementations
# ─────────────────────────────────────────────────────────────────────────────

def _run_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Execute a Tavily web search."""
    if not _tavily_available:
        return {"error": "tavily-python not installed. Run: pip install tavily-python"}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY not set in environment."}

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, max_results=max_results)

    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", "")[:500],  # truncate for token efficiency
            "score": r.get("score", 0),
        })

    return {
        "query": query,
        "results": results,
        "result_count": len(results),
    }


_SUBPROCESS_TIMEOUT = 10  # seconds — prevents hanging processes

def _run_computer_use(action: str, x: Optional[int] = None, y: Optional[int] = None,
                      text: Optional[str] = None, key: Optional[str] = None,
                      delta_y: int = 300) -> Dict[str, Any]:
    """
    Execute a computer use action. Uses xdotool + scrot on Linux,
    and screencapture + cliclick on macOS.
    Returns result dict; screenshots are base64-encoded PNG data.
    """
    import sys
    try:
        if action == "screenshot":
            if sys.platform == "darwin":
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    tmp_path = tf.name
                subprocess.run(
                    ["screencapture", "-x", tmp_path],
                    check=True, timeout=_SUBPROCESS_TIMEOUT,
                    capture_output=True, text=True
                )
                with open(tmp_path, "rb") as f:
                    img_data = f.read()
                os.remove(tmp_path)
            else:
                result = subprocess.run(
                    ["scrot", "-", "--quality", "80"],
                    capture_output=True, check=True,
                    timeout=_SUBPROCESS_TIMEOUT,
                )
                img_data = result.stdout

            img_b64 = base64.b64encode(img_data).decode("utf-8")
            return {
                "action": "screenshot",
                "success": True,
                "image_base64": img_b64,
                "format": "png",
                "note": "Screenshot captured. Describe what you see.",
            }

        elif action == "click":
            if x is None or y is None:
                return {"error": "click requires x and y coordinates."}
            if sys.platform == "darwin":
                subprocess.run(["cliclick", f"c:{x},{y}"], check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True)
            else:
                subprocess.run(
                    ["xdotool", "mousemove", str(x), str(y), "click", "1"],
                    check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True
                )
            return {"action": "click", "success": True, "x": x, "y": y}

        elif action == "type":
            if not text:
                return {"error": "type requires text parameter."}
            if sys.platform == "darwin":
                subprocess.run(["cliclick", "-r", f"t:{text}"], check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True)
            else:
                subprocess.run(
                    ["xdotool", "type", "--clearmodifiers", "--", text],
                    check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True
                )
            return {"action": "type", "success": True, "typed": text}

        elif action == "key":
            if not key:
                return {"error": "key requires key parameter."}
            if sys.platform == "darwin":
                subprocess.run(["cliclick", f"kp:{key}"], check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True)
            else:
                subprocess.run(
                    ["xdotool", "key", "--", key],
                    check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True
                )
            return {"action": "key", "success": True, "key": key}

        elif action == "scroll":
            if x is None or y is None:
                return {"error": "scroll requires x and y coordinates."}
            if sys.platform == "darwin":
                return {"error": "scroll is not fully supported on macOS via cliclick without custom scripts"}
            else:
                direction = "5" if delta_y > 0 else "4"  # button 5 = scroll down, 4 = up
                steps = max(1, abs(delta_y) // 100)
                for _ in range(steps):
                    subprocess.run(
                        ["xdotool", "mousemove", str(x), str(y), "click", direction],
                        check=True, timeout=_SUBPROCESS_TIMEOUT, capture_output=True, text=True
                    )
            return {"action": "scroll", "success": True, "x": x, "y": y, "delta_y": delta_y}

        else:
            return {"error": f"Unknown action: {action}"}

    except subprocess.TimeoutExpired:
        return {"error": f"Timed out after {_SUBPROCESS_TIMEOUT}s", "action": action, "success": False}
    except FileNotFoundError as e:
        if sys.platform == "darwin":
            tool = "cliclick" if "cliclick" in str(e) else "screencapture"
            install_cmd = f"brew install {tool}"
        else:
            tool = "scrot" if "scrot" in str(e) else "xdotool"
            install_cmd = f"sudo apt-get install {tool}"
            
        return {
            "error": f"{tool} not found. Install with: {install_cmd}",
            "action": action,
            "success": False,
        }
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        if sys.platform == "darwin" and action == "screenshot" and "could not create image from display" in err_msg:
            err_msg += " (Error implies headless environment or missing Screen Recording permissions in macOS System Settings > Privacy & Security.)"
        return {"error": err_msg, "action": action, "success": False}


# ─────────────────────────────────────────────────────────────────────────────
# Dispatch router
# ─────────────────────────────────────────────────────────────────────────────

def dispatch_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Route a tool_use block to the correct implementation."""
    if tool_name == "web_search":
        return _run_web_search(
            query=tool_input["query"],
            max_results=tool_input.get("max_results", 5),
        )
    elif tool_name == "computer_use":
        return _run_computer_use(
            action=tool_input["action"],
            x=tool_input.get("x"),
            y=tool_input.get("y"),
            text=tool_input.get("text"),
            key=tool_input.get("key"),
            delta_y=tool_input.get("delta_y", 300),
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}
