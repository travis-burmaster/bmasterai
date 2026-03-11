"""
Four specialist agents + one quality-gate node.
Each is a plain function: (state) -> partial state dict.
BMasterAI logs every agent call.
"""
import os
from bmasterai.logging import configure_logging, EventType, LogLevel
from bmasterai.monitoring import get_monitor
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

from state import VideoState

# ── BMasterAI setup ───────────────────────────────────────────────────────────
bm = configure_logging(
    log_level=LogLevel.INFO,
    log_file="logs/agents.log",
    json_log_file="logs/agents.jsonl",
)
monitor = get_monitor()
monitor.start_monitoring()

# ── LLM + tools ───────────────────────────────────────────────────────────────
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", max_tokens=2048)
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def _llm(prompt: str, agent_name: str) -> str:
    """Call Claude and return the text response."""
    bm.log_event(
        EventType.LLM_CALL,
        agent_id=agent_name,
        metadata={"prompt_chars": len(prompt)},
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    bm.log_event(
        EventType.TASK_COMPLETE,
        agent_id=agent_name,
        metadata={"response_chars": len(response.content)},
    )
    return response.content.strip()


# ── Agent 1: Trend Researcher ─────────────────────────────────────────────────
def trend_researcher(state: VideoState) -> dict:
    """
    Searches for the most viral angle on the given topic right now.
    Uses Tavily to pull real-time context.
    """
    agent = "trend-researcher"
    bm.log_event(EventType.TASK_START, agent_id=agent, metadata={"topic": state["topic"]})

    try:
        results = tavily.search(
            query=f"viral YouTube Shorts {state['topic']} trending 2025",
            max_results=5,
            search_depth="advanced",
        )
        snippets = "\n".join(
            f"- {r['title']}: {r['content'][:200]}"
            for r in results.get("results", [])
        )

        prompt = f"""You are a viral YouTube Shorts trend analyst.

Topic: {state["topic"]}

Recent search results:
{snippets}

Identify:
1. The single most viral angle for a 60-second YouTube Short on this topic right now
2. Why it's trending (2-3 sentences of context)
3. Three example opening hooks from top-performing videos on this angle

Reply in this exact format:
ANGLE: <one sentence>
CONTEXT: <2-3 sentences>
HOOK_1: <hook>
HOOK_2: <hook>
HOOK_3: <hook>"""

        raw = _llm(prompt, agent)
        lines = {l.split(":")[0].strip(): ":".join(l.split(":")[1:]).strip()
                 for l in raw.splitlines() if ":" in l}

        return {
            "trending_angle": lines.get("ANGLE", ""),
            "trend_context": lines.get("CONTEXT", ""),
            "competitor_hooks": [
                lines.get("HOOK_1", ""),
                lines.get("HOOK_2", ""),
                lines.get("HOOK_3", ""),
            ],
            "errors": state.get("errors", []),
        }

    except Exception as e:
        bm.log_event(EventType.TASK_ERROR, agent_id=agent, metadata={"error": str(e)})
        return {"errors": state.get("errors", []) + [f"{agent}: {e}"]}


# ── Agent 2: Hook Writer ──────────────────────────────────────────────────────
def hook_writer(state: VideoState) -> dict:
    """
    Writes the single best opening hook — the first 3–5 seconds that stop
    the scroll before YouTube decides to keep showing the video.
    """
    agent = "hook-writer"
    bm.log_event(EventType.TASK_START, agent_id=agent,
                 metadata={"angle": state.get("trending_angle", "")})

    try:
        prompt = f"""You are an elite YouTube Shorts hook writer.

Topic: {state["topic"]}
Trending angle: {state["trending_angle"]}
Trend context: {state["trend_context"]}

Competitor hooks for reference (don't copy, outperform):
{chr(10).join(f"- {h}" for h in state.get("competitor_hooks", []))}

Write ONE killer opening hook for a 60-second YouTube Short.
Rules:
- Maximum 12 words
- Creates immediate curiosity or shock
- Poses a question OR makes a bold claim
- Must make the viewer feel they'll miss something if they scroll
- No filler words ("Hey guys", "Welcome back", "In this video")

Reply with ONLY the hook text, nothing else."""

        hook = _llm(prompt, agent)
        return {"hook": hook, "errors": state.get("errors", [])}

    except Exception as e:
        bm.log_event(EventType.TASK_ERROR, agent_id=agent, metadata={"error": str(e)})
        return {"errors": state.get("errors", []) + [f"{agent}: {e}"]}


# ── Agent 3: Script Writer ────────────────────────────────────────────────────
def script_writer(state: VideoState) -> dict:
    """
    Writes the full 45–60 second script using the hook as the opening line.
    Structured for maximum retention: hook → conflict → payoff → CTA.
    """
    agent = "script-writer"
    bm.log_event(EventType.TASK_START, agent_id=agent,
                 metadata={"hook": state.get("hook", "")[:80]})

    try:
        prompt = f"""You are a viral YouTube Shorts script writer.

Topic: {state["topic"]}
Angle: {state["trending_angle"]}
Context: {state["trend_context"]}
Opening hook (first line, do not change): {state["hook"]}

Write a complete 45–60 second spoken script for a YouTube Short.

Structure:
1. HOOK (0–3s): Use the exact hook above
2. CONFLICT (3–20s): Introduce the problem / tension / surprising fact
3. BUILD (20–45s): Stack the value — 3 punchy points, each under 10 words
4. PAYOFF (45–55s): The satisfying reveal or actionable insight
5. CTA (55–60s): One specific call to action (follow, comment, or share — pick one)

Rules:
- Write for spoken delivery, not reading
- Short punchy sentences. One idea per line.
- No filler. Every word earns its place.
- Label each section clearly: [HOOK] [CONFLICT] [BUILD] [PAYOFF] [CTA]

Reply with ONLY the script."""

        script = _llm(prompt, agent)
        return {"script": script, "errors": state.get("errors", [])}

    except Exception as e:
        bm.log_event(EventType.TASK_ERROR, agent_id=agent, metadata={"error": str(e)})
        return {"errors": state.get("errors", []) + [f"{agent}: {e}"]}


# ── Agent 4: Title & Tags ─────────────────────────────────────────────────────
def title_and_tags(state: VideoState) -> dict:
    """
    Generates a viral title, SEO tags, and one-line thumbnail concept.
    """
    agent = "title-and-tags"
    bm.log_event(EventType.TASK_START, agent_id=agent,
                 metadata={"topic": state["topic"]})

    try:
        prompt = f"""You are a YouTube SEO and packaging expert specialising in Shorts.

Topic: {state["topic"]}
Angle: {state["trending_angle"]}
Hook: {state["hook"]}
Script excerpt: {state.get("script", "")[:300]}

Generate:
1. TITLE: A viral YouTube Shorts title (max 70 chars). Curiosity gap or bold claim. No clickbait.
2. TAGS: 10 SEO tags as a comma-separated list (mix broad + niche)
3. THUMBNAIL: One-line concept — bold text overlay + visual description (e.g. "RED TEXT: 'They lied to you' | background: shocked face close-up")

Reply in this exact format:
TITLE: <title>
TAGS: <tag1>, <tag2>, ...
THUMBNAIL: <concept>"""

        raw = _llm(prompt, agent)
        lines = {l.split(":")[0].strip(): ":".join(l.split(":")[1:]).strip()
                 for l in raw.splitlines() if ":" in l}

        tags_raw = lines.get("TAGS", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        return {
            "title": lines.get("TITLE", ""),
            "tags": tags,
            "thumbnail_concept": lines.get("THUMBNAIL", ""),
            "errors": state.get("errors", []),
        }

    except Exception as e:
        bm.log_event(EventType.TASK_ERROR, agent_id=agent, metadata={"error": str(e)})
        return {"errors": state.get("errors", []) + [f"{agent}: {e}"]}


# ── Quality Gate ──────────────────────────────────────────────────────────────
def quality_gate(state: VideoState) -> dict:
    """
    Checks the assembled package for quality.
    Returns approved=True or approved=False with feedback in errors.
    """
    agent = "quality-gate"
    bm.log_event(EventType.TASK_START, agent_id=agent)

    issues = []
    if not state.get("hook") or len(state["hook"].split()) > 15:
        issues.append("Hook is missing or too long (>15 words)")
    if not state.get("script") or len(state["script"]) < 200:
        issues.append("Script too short (<200 chars)")
    if not state.get("title"):
        issues.append("Title is missing")
    if len(state.get("tags", [])) < 5:
        issues.append("Not enough tags (<5)")

    approved = len(issues) == 0
    iterations = state.get("iterations", 0) + 1

    bm.log_event(
        EventType.TASK_COMPLETE,
        agent_id=agent,
        metadata={"approved": approved, "issues": issues, "iteration": iterations},
    )

    return {
        "approved": approved,
        "iterations": iterations,
        "errors": state.get("errors", []) + issues,
    }
