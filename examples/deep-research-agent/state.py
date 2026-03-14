"""
Shared state flowing through the LangGraph deep research pipeline.
"""
from typing import TypedDict, Optional


class ResearchState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────────
    topic: str                      # User-supplied research question

    # ── Planner output ─────────────────────────────────────────────────────────
    sub_questions: list[str]        # 3–5 focused sub-questions to research
    plan_reasoning: str             # Planner's rationale for the breakdown

    # ── Web Searcher output ────────────────────────────────────────────────────
    search_results: list[dict]      # Raw Tavily results per sub-question
                                    # Each: {question, results: [{url, title, content}]}

    # ── Analyzer output ────────────────────────────────────────────────────────
    findings: list[str]             # Synthesized finding per sub-question

    # ── Reflector output ───────────────────────────────────────────────────────
    reflection: str                 # Gaps identified, quality assessment
    needs_more_research: bool       # Whether to loop back for another round
    follow_up_questions: list[str]  # Additional questions if gaps found
    reflection_count: int           # Number of reflection loops completed

    # ── Synthesizer output ─────────────────────────────────────────────────────
    report: str                     # Final structured research report

    # ── Metadata ───────────────────────────────────────────────────────────────
    errors: list[str]               # Any errors from any node
    sources: list[str]              # All URLs cited (deduplicated)
