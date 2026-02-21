"""
Research tools for the BMasterAI AgentCore agent.

These functions are called by the @tool decorated wrappers in agent.py.
Swap these implementations for your own data sources, APIs, or RAG pipelines.
"""

import json
import re
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
import requests


# ── Knowledge Base / Search ────────────────────────────────────────────────────

def search_knowledge_base(query: str, max_results: int = 5) -> str:
    """
    Search a Bedrock Knowledge Base if configured, otherwise fall back
    to a mock web search via the Brave Search API or DuckDuckGo.

    Set KNOWLEDGE_BASE_ID in your environment to use a Bedrock Knowledge Base.
    Set BRAVE_API_KEY to use Brave Search as the web fallback.
    """
    kb_id = os.getenv("KNOWLEDGE_BASE_ID")

    if kb_id:
        return _search_bedrock_kb(query, kb_id, max_results)

    brave_key = os.getenv("BRAVE_API_KEY")
    if brave_key:
        return _search_brave(query, brave_key, max_results)

    # Fallback: DuckDuckGo Instant Answer API (no key required)
    return _search_duckduckgo(query)


def _search_bedrock_kb(query: str, kb_id: str, max_results: int) -> str:
    """Query an Amazon Bedrock Knowledge Base via RetrieveAndGenerate."""
    client = boto3.client("bedrock-agent-runtime")
    try:
        response = client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": max_results}
            },
        )
        results = response.get("retrievalResults", [])
        if not results:
            return f"No results found in knowledge base for: {query}"

        lines = [f"Knowledge Base results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            content = r.get("content", {}).get("text", "")
            score = r.get("score", 0)
            lines.append(f"{i}. (score: {score:.3f})\n{content}\n")
        return "\n".join(lines)

    except Exception as e:
        return f"Knowledge base search failed: {e}"


def _search_brave(query: str, api_key: str, max_results: int) -> str:
    """Search the web using the Brave Search API."""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": max_results}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])

        if not results:
            return f"No web results found for: {query}"

        lines = [f"Web search results for '{query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.get('title', '')}\n   {r.get('url', '')}\n   {r.get('description', '')}\n")
        return "\n".join(lines)

    except Exception as e:
        return f"Brave search failed: {e}"


def _search_duckduckgo(query: str) -> str:
    """DuckDuckGo Instant Answer API — no key required, limited results."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        abstract = data.get("AbstractText", "")
        answer = data.get("Answer", "")
        related = [r.get("Text", "") for r in data.get("RelatedTopics", [])[:3] if r.get("Text")]

        parts = []
        if abstract:
            parts.append(f"Summary: {abstract}")
        if answer:
            parts.append(f"Answer: {answer}")
        if related:
            parts.append("Related:\n" + "\n".join(f"- {t}" for t in related))

        return "\n\n".join(parts) if parts else f"No instant answer found for: {query}"

    except Exception as e:
        return f"DuckDuckGo search failed: {e}"


# ── Summarization ──────────────────────────────────────────────────────────────

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Lightweight extractive summarization — picks the most information-dense
    sentences. For production, consider calling Bedrock directly here.
    """
    if not text or not text.strip():
        return "No text provided to summarize."

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text.strip()

    # Score by word count (proxy for information density) and position
    scored = []
    for i, sentence in enumerate(sentences):
        words = sentence.split()
        # Favor longer sentences and those near the start
        position_bonus = 1.2 if i < 3 else 1.0
        score = len(words) * position_bonus
        scored.append((score, i, sentence))

    # Pick top N by score, restore original order
    top = sorted(scored, reverse=True)[:max_sentences]
    top_ordered = sorted(top, key=lambda x: x[1])

    return " ".join(s for _, _, s in top_ordered)


# ── Data Analysis ──────────────────────────────────────────────────────────────

def analyze_data(data: str, question: str) -> str:
    """
    Analyze JSON or CSV data to answer a question.
    For complex analysis, this can invoke Bedrock's Code Interpreter.
    """
    if not data.strip():
        return "No data provided for analysis."

    # Try JSON first
    try:
        parsed = json.loads(data)
        return _analyze_json(parsed, question)
    except json.JSONDecodeError:
        pass

    # Try CSV
    if "\n" in data and ("," in data or "\t" in data):
        return _analyze_csv(data, question)

    # Plain text analysis
    word_count = len(data.split())
    line_count = len(data.splitlines())
    return (
        f"Text data analysis:\n"
        f"- Lines: {line_count}\n"
        f"- Words: {word_count}\n"
        f"- Characters: {len(data)}\n\n"
        f"Question: '{question}'\n"
        f"The data appears to be plain text. Consider using the summarize tool "
        f"to extract key points, then ask your analytical question."
    )


def _analyze_json(data: object, question: str) -> str:
    """Basic structural analysis of parsed JSON data."""
    if isinstance(data, list):
        count = len(data)
        keys = list(data[0].keys()) if count > 0 and isinstance(data[0], dict) else []
        return (
            f"JSON Array Analysis:\n"
            f"- Records: {count}\n"
            f"- Fields: {', '.join(keys) if keys else 'N/A'}\n\n"
            f"Question: '{question}'\n"
            f"Sample (first record): {json.dumps(data[0], indent=2) if count > 0 else 'empty'}"
        )
    elif isinstance(data, dict):
        return (
            f"JSON Object Analysis:\n"
            f"- Top-level keys: {', '.join(data.keys())}\n\n"
            f"Question: '{question}'\n"
            f"Data: {json.dumps(data, indent=2)[:2000]}"
        )
    else:
        return f"JSON value: {data}\nQuestion: '{question}'"


def _analyze_csv(data: str, question: str) -> str:
    """Basic CSV analysis without pandas dependency."""
    lines = [l for l in data.strip().splitlines() if l.strip()]
    if not lines:
        return "Empty CSV data."

    delimiter = "\t" if "\t" in lines[0] else ","
    headers = [h.strip() for h in lines[0].split(delimiter)]
    rows = lines[1:]

    return (
        f"CSV Analysis:\n"
        f"- Columns: {', '.join(headers)}\n"
        f"- Rows: {len(rows)}\n\n"
        f"Question: '{question}'\n"
        f"Sample (first 3 rows):\n" +
        "\n".join(f"  {r}" for r in rows[:3])
    )


# ── URL Fetching ───────────────────────────────────────────────────────────────

def fetch_url_content(url: str, timeout: int = 15) -> str:
    """
    Fetch a URL and extract readable text content.
    Strips HTML tags for clean plain-text output.
    """
    if not url.startswith(("http://", "https://")):
        return f"Invalid URL: must start with http:// or https://"

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; BMasterAI-AgentCore/1.0; research-agent)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")

        if "json" in content_type:
            return json.dumps(resp.json(), indent=2)[:5000]

        # Strip HTML tags
        text = resp.text
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s{2,}", " ", text).strip()

        # Return first 5000 chars to keep context manageable
        if len(text) > 5000:
            text = text[:5000] + f"\n\n[... truncated — full page is {len(resp.text)} chars]"

        return f"Content from {url}:\n\n{text}"

    except requests.exceptions.Timeout:
        return f"Request timed out fetching: {url}"
    except requests.exceptions.HTTPError as e:
        return f"HTTP error {e.response.status_code} fetching: {url}"
    except Exception as e:
        return f"Error fetching {url}: {e}"
