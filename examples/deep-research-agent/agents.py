"""
Research agent nodes for the LangGraph deep research pipeline.
Each node is a plain function: (state) -> partial state dict.
BMasterAI logs every agent call, LLM call, tool use, and reasoning step.
"""
import os
import time
from typing import Any

from bmasterai.logging import configure_logging, EventType, LogLevel
from bmasterai.monitoring import get_monitor
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from tavily import TavilyClient

from state import ResearchState

# ── BMasterAI setup ────────────────────────────────────────────────────────────
# BMasterAI always prepends "logs/" — ensure that directory exists relative to cwd
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/reasoning", exist_ok=True)

bm = configure_logging(
    log_level=LogLevel.INFO,
    log_file="research.log",
    json_log_file="research.jsonl",
)
monitor = get_monitor()
monitor.start_monitoring()

# ── LLM + tools ───────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
    max_tokens=2048,
)
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

MAX_REFLECTION_LOOPS = 2


# ── Shared LLM helper ─────────────────────────────────────────────────────────
def _call_llm(prompt: str, agent_name: str, task: str = "") -> str:
    """Call Claude with BMasterAI telemetry."""
    t0 = time.time()
    bm.log_event(
        event_type=EventType.LLM_CALL,
        agent_id=agent_name,
        data={"task": task, "prompt_chars": len(prompt)},
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    elapsed = time.time() - t0
    text = response.content if hasattr(response, "content") else str(response)

    monitor.track_llm_call(
        agent_id=agent_name,
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
        tokens_used=getattr(response, "usage_metadata", {}).get("total_tokens", 0) if hasattr(response, "usage_metadata") else 0,
        duration=elapsed,
    )
    return text


# ── Node: Planner ─────────────────────────────────────────────────────────────
def planner(state: ResearchState) -> dict:
    """
    Break the research topic into 3–5 focused sub-questions.
    Logs a reasoning chain showing the decomposition rationale.
    """
    agent_id = "planner"
    monitor.track_agent_start(agent_id)
    t0 = time.time()

    bm.log_event(
        event_type=EventType.TASK_START,
        agent_id=agent_id,
        data={"topic": state["topic"]},
    )

    prompt = f"""You are a research planning agent. Your job is to break down a complex research topic into 3–5 focused sub-questions that together will fully answer the main question.

Research topic: {state['topic']}

Output ONLY valid JSON in this format:
{{
  "sub_questions": [
    "specific sub-question 1",
    "specific sub-question 2",
    "specific sub-question 3"
  ],
  "reasoning": "Brief explanation of why these sub-questions cover the topic"
}}

Make each sub-question specific and searchable. Avoid overlap between questions."""

    import json
    raw = _call_llm(prompt, agent_id, task="topic_decomposition")

    # Parse JSON
    try:
        # Strip markdown code fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        parsed = json.loads(clean)
        sub_questions = parsed.get("sub_questions", [])
        reasoning = parsed.get("reasoning", "")
    except Exception as e:
        # Fallback: treat the whole response as a single question
        sub_questions = [state["topic"]]
        reasoning = f"Parsing failed ({e}), falling back to direct search"

    # Log reasoning chain
    bm.log_reasoning_chain(
        agent_id=agent_id,
        chain=[
            {"step": f"Q{i+1}", "content": q}
            for i, q in enumerate(sub_questions)
        ],
    )
    bm.log_event(
        event_type=EventType.DECISION_POINT,
        agent_id=agent_id,
        data={"sub_questions": sub_questions, "count": len(sub_questions)},
    )

    monitor.track_task_duration(agent_id, "plan", time.time() - t0)
    monitor.track_agent_stop(agent_id)

    return {
        "sub_questions": sub_questions,
        "plan_reasoning": reasoning,
        "search_results": [],
        "findings": [],
        "reflection_count": 0,
        "needs_more_research": False,
        "follow_up_questions": [],
        "errors": [],
        "sources": [],
    }


# ── Node: Web Searcher ────────────────────────────────────────────────────────
def web_searcher(state: ResearchState) -> dict:
    """
    Run Tavily searches for each sub-question (+ any follow-up questions).
    Appends results to state without replacing existing ones (supports loops).
    """
    agent_id = "web_searcher"
    monitor.track_agent_start(agent_id)
    t0 = time.time()

    questions = state.get("sub_questions", [])
    if state.get("needs_more_research") and state.get("follow_up_questions"):
        questions = state["follow_up_questions"]

    all_results = list(state.get("search_results", []))
    all_sources = list(state.get("sources", []))
    errors = list(state.get("errors", []))

    for q in questions:
        bm.log_event(
            event_type=EventType.TOOL_USE,
            agent_id=agent_id,
            data={"tool": "tavily_search", "query": q},
        )
        try:
            result = tavily.search(
                query=q,
                search_depth="advanced",
                max_results=4,
                days=30,
            )
            hits = result.get("results", [])
            all_results.append({
                "question": q,
                "results": [
                    {"url": h.get("url"), "title": h.get("title"), "content": h.get("content", "")[:600]}
                    for h in hits
                ],
            })
            all_sources.extend([h.get("url", "") for h in hits])
        except Exception as e:
            errors.append(f"Search error for '{q}': {e}")

    monitor.track_task_duration(agent_id, "search", time.time() - t0)
    monitor.track_agent_stop(agent_id)

    return {
        "search_results": all_results,
        "sources": list(dict.fromkeys(all_sources)),  # deduplicate, preserve order
        "errors": errors,
    }


# ── Node: Analyzer ────────────────────────────────────────────────────────────
def analyzer(state: ResearchState) -> dict:
    """
    Synthesize search results into one clear finding per sub-question.
    Replaces previous findings with updated ones (safe for loops).
    """
    agent_id = "analyzer"
    monitor.track_agent_start(agent_id)
    t0 = time.time()

    findings = []
    errors = list(state.get("errors", []))

    for entry in state.get("search_results", []):
        question = entry["question"]
        sources_text = "\n\n".join(
            f"Source: {r['url']}\nTitle: {r['title']}\n{r['content']}"
            for r in entry.get("results", [])
        )

        if not sources_text.strip():
            findings.append(f"[{question}]\nNo results found.")
            continue

        prompt = f"""You are a research analyst. Synthesize the search results below into a clear, factual finding that answers the question.

Question: {question}

Search Results:
{sources_text}

Write 2–4 sentences that directly answer the question using the evidence above. Be specific and cite key facts. Do not speculate beyond the sources."""

        bm.log_event(
            event_type=EventType.LLM_REASONING,
            agent_id=agent_id,
            data={"question": question, "source_count": len(entry.get("results", []))},
        )

        finding = _call_llm(prompt, agent_id, task="source_synthesis")
        findings.append(f"**{question}**\n{finding.strip()}")

    monitor.track_task_duration(agent_id, "analyze", time.time() - t0)
    monitor.track_agent_stop(agent_id)

    return {"findings": findings, "errors": errors}


# ── Node: Reflector ────────────────────────────────────────────────────────────
def reflector(state: ResearchState) -> dict:
    """
    Evaluate research completeness. If gaps exist and loops remain, flag for
    another search round. Otherwise approve for synthesis.
    """
    agent_id = "reflector"
    monitor.track_agent_start(agent_id)
    t0 = time.time()

    reflection_count = state.get("reflection_count", 0)

    if reflection_count >= MAX_REFLECTION_LOOPS:
        bm.log_event(
            event_type=EventType.DECISION_POINT,
            agent_id=agent_id,
            data={"decision": "max_loops_reached", "loops": reflection_count},
        )
        monitor.track_agent_stop(agent_id)
        return {
            "reflection": "Max reflection loops reached — proceeding to synthesis.",
            "needs_more_research": False,
            "follow_up_questions": [],
            "reflection_count": reflection_count + 1,
        }

    findings_text = "\n\n".join(state.get("findings", []))
    original_topic = state["topic"]

    prompt = f"""You are a research quality reviewer. Evaluate whether the findings below adequately answer the original research question.

Original research question: {original_topic}

Current findings:
{findings_text}

Assess:
1. Are there significant gaps or unanswered aspects?
2. Is any finding too vague or lacking evidence?
3. Are there contradictions that need resolution?

Output ONLY valid JSON:
{{
  "quality_score": 1-10,
  "gaps": ["gap 1", "gap 2"],
  "needs_more_research": true/false,
  "follow_up_questions": ["question if needed"],
  "reflection": "Brief overall assessment"
}}

Set needs_more_research to true only if quality_score < 7 and there are clear, searchable gaps."""

    import json
    raw = _call_llm(prompt, agent_id, task="quality_reflection")

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        parsed = json.loads(clean)
        needs_more = parsed.get("needs_more_research", False)
        follow_ups = parsed.get("follow_up_questions", [])
        reflection = parsed.get("reflection", "")
        score = parsed.get("quality_score", 7)
    except Exception as e:
        needs_more = False
        follow_ups = []
        reflection = f"Reflection parse failed ({e}) — approving for synthesis."
        score = 7

    bm.log_event(
        event_type=EventType.DECISION_POINT,
        agent_id=agent_id,
        data={
            "quality_score": score,
            "needs_more_research": needs_more,
            "follow_up_count": len(follow_ups),
            "loop": reflection_count + 1,
        },
    )

    monitor.track_task_duration(agent_id, "reflect", time.time() - t0)
    monitor.track_agent_stop(agent_id)

    return {
        "reflection": reflection,
        "needs_more_research": needs_more,
        "follow_up_questions": follow_ups if needs_more else [],
        "reflection_count": reflection_count + 1,
    }


# ── Node: Synthesizer ─────────────────────────────────────────────────────────
def synthesizer(state: ResearchState) -> dict:
    """
    Combine all findings into a final structured research report.
    """
    agent_id = "synthesizer"
    monitor.track_agent_start(agent_id)
    t0 = time.time()

    findings_text = "\n\n".join(state.get("findings", []))
    sources = state.get("sources", [])
    topic = state["topic"]
    reflection = state.get("reflection", "")

    prompt = f"""You are a research synthesis agent. Write a comprehensive, well-structured research report based on the findings below.

Research question: {topic}

Findings:
{findings_text}

Quality notes from reviewer: {reflection}

Write a clear research report with these sections:
1. **Executive Summary** (2–3 sentences)
2. **Key Findings** (bullet points with the most important facts)
3. **Analysis** (2–3 paragraphs connecting the findings)
4. **Limitations** (what's still uncertain or not covered)

Use a professional, analytical tone. Be specific — cite facts, numbers, and evidence from the findings. Do not pad with filler."""

    bm.log_event(
        event_type=EventType.TASK_START,
        agent_id=agent_id,
        data={"findings_count": len(state.get("findings", [])), "source_count": len(sources)},
    )

    report = _call_llm(prompt, agent_id, task="final_synthesis")

    # Append source list to report
    if sources:
        source_list = "\n".join(f"- {url}" for url in sources[:20])
        report += f"\n\n---\n**Sources**\n{source_list}"

    monitor.track_task_duration(agent_id, "synthesize", time.time() - t0)
    monitor.track_agent_stop(agent_id)

    return {"report": report}
