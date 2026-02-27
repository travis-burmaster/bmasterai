"""
Browser Search Tool
===================
Uses AgentCore's managed Browser tool to perform web searches and extract
content from web pages. Each invocation spins up an isolated, ephemeral
Chromium session.

For simple search queries, the tool navigates to DuckDuckGo, enters the
query, and extracts the top results — avoiding the need for a paid search
API. For direct URL fetches, it navigates and extracts page text.
"""

import json
import logging
import time

import boto3
from strands.tools import tool

logger = logging.getLogger(__name__)

_browser_client = boto3.client("bedrock-agentcore", region_name="us-east-1")

# ---------------------------------------------------------------------------
# Browser session lifecycle
# ---------------------------------------------------------------------------

def _create_session(timeout_minutes: int = 5) -> dict:
    """Start an ephemeral browser session."""
    response = _browser_client.create_browser_session(
        browserType="aws.browser.v1",
        sessionTimeoutMinutes=timeout_minutes,
    )
    session_id = response["sessionId"]
    automation_endpoint = response["automationEndpoint"]
    logger.info("Browser session created: %s", session_id)
    return {"session_id": session_id, "endpoint": automation_endpoint}


def _close_session(session_id: str) -> None:
    """Terminate a browser session."""
    try:
        _browser_client.delete_browser_session(sessionId=session_id)
        logger.info("Browser session closed: %s", session_id)
    except Exception:
        logger.warning("Failed to close browser session %s", session_id)


# ---------------------------------------------------------------------------
# Browser automation helpers
# ---------------------------------------------------------------------------

def _navigate(session_id: str, url: str) -> dict:
    """Navigate to a URL and return page content."""
    response = _browser_client.send_browser_command(
        sessionId=session_id,
        command={
            "action": "navigate",
            "url": url,
        },
    )
    return response


def _get_page_text(session_id: str) -> str:
    """Extract visible text from the current page."""
    response = _browser_client.send_browser_command(
        sessionId=session_id,
        command={
            "action": "get_text",
        },
    )
    return response.get("text", "")


def _screenshot(session_id: str) -> str:
    """Take a screenshot, return base64-encoded PNG."""
    response = _browser_client.send_browser_command(
        sessionId=session_id,
        command={
            "action": "screenshot",
        },
    )
    return response.get("image", "")


# ---------------------------------------------------------------------------
# Strands tool definitions
# ---------------------------------------------------------------------------

@tool
def browser_search(query: str, max_results: int = 5) -> dict:
    """
    Search the web using an isolated browser and return the top results.

    Use this tool when you need up-to-date information from the internet,
    such as current events, documentation, pricing, or facts you're unsure of.

    Args:
        query: The search query string.
        max_results: Number of results to return (1-10). Defaults to 5.

    Returns:
        dict with keys:
          - results: list of {title, url, snippet}
          - raw_text: full page text (truncated) for deeper extraction
    """
    max_results = max(1, min(max_results, 10))
    session = None

    try:
        session = _create_session(timeout_minutes=3)
        sid = session["session_id"]

        # Navigate to DuckDuckGo
        search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&t=h_&ia=web"
        _navigate(sid, search_url)

        # Give the page time to render
        time.sleep(2)

        # Extract page text
        page_text = _get_page_text(sid)

        # Parse results from page text (basic extraction)
        results = _parse_search_results(page_text, max_results)

        return {
            "results": results,
            "raw_text": page_text[:3000],  # truncate for context window
        }

    except Exception as e:
        logger.exception("Browser search failed")
        return {
            "results": [],
            "raw_text": "",
            "error": str(e),
        }
    finally:
        if session:
            _close_session(session["session_id"])


@tool
def browser_fetch_url(url: str) -> dict:
    """
    Navigate to a specific URL and extract its text content.

    Use this tool when you need to read a specific web page — documentation,
    articles, API responses, etc.

    Args:
        url: The full URL to fetch.

    Returns:
        dict with keys: title, text, url
    """
    session = None
    try:
        session = _create_session(timeout_minutes=3)
        sid = session["session_id"]

        _navigate(sid, url)
        time.sleep(2)

        page_text = _get_page_text(sid)

        return {
            "title": _extract_title(page_text),
            "text": page_text[:5000],
            "url": url,
        }

    except Exception as e:
        logger.exception("Browser fetch failed for %s", url)
        return {"title": "", "text": "", "url": url, "error": str(e)}
    finally:
        if session:
            _close_session(session["session_id"])


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_search_results(page_text: str, max_results: int) -> list[dict]:
    """
    Best-effort extraction of search results from DuckDuckGo page text.
    In production, you'd use Playwright selectors for more robust parsing.
    """
    results = []
    lines = page_text.strip().split("\n")
    current_result = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # DuckDuckGo results typically have URL patterns
        if line.startswith("http://") or line.startswith("https://"):
            if current_result.get("title"):
                current_result["url"] = line
                results.append(current_result)
                current_result = {}
                if len(results) >= max_results:
                    break
        elif not current_result.get("title") and len(line) > 10:
            current_result = {"title": line, "url": "", "snippet": ""}
        elif current_result.get("title") and not current_result.get("snippet"):
            current_result["snippet"] = line

    # Append any trailing result
    if current_result.get("title") and len(results) < max_results:
        results.append(current_result)

    return results


def _extract_title(page_text: str) -> str:
    """Extract the first meaningful line as a title."""
    for line in page_text.strip().split("\n"):
        line = line.strip()
        if len(line) > 5:
            return line[:200]
    return "Untitled"


class BrowserSearchTool:
    """Wrapper class for Strands Agent tool registration."""

    def __call__(self):
        return [browser_search, browser_fetch_url]
