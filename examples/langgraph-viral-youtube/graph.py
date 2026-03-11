"""
LangGraph pipeline: 4 specialist agents → quality gate → retry or publish.

Flow:
  trend_researcher → hook_writer → script_writer → title_and_tags
                                                         ↓
                                                   quality_gate
                                                    /         \
                                              approved      rejected (retry ≤2)
                                                 ↓                ↓
                                             END         hook_writer (retry)
"""
from langgraph.graph import StateGraph, END

from state import VideoState
from agents import (
    trend_researcher,
    hook_writer,
    script_writer,
    title_and_tags,
    quality_gate,
)


def should_retry(state: VideoState) -> str:
    """Routing function after quality gate."""
    if state.get("approved"):
        return "approved"
    if state.get("iterations", 0) >= 2:
        # Max retries hit — publish anyway with warnings
        return "approved"
    return "retry"


def build_graph() -> StateGraph:
    g = StateGraph(VideoState)

    # Register nodes
    g.add_node("trend_researcher", trend_researcher)
    g.add_node("hook_writer", hook_writer)
    g.add_node("script_writer", script_writer)
    g.add_node("title_and_tags", title_and_tags)
    g.add_node("quality_gate", quality_gate)

    # Linear pipeline
    g.set_entry_point("trend_researcher")
    g.add_edge("trend_researcher", "hook_writer")
    g.add_edge("hook_writer", "script_writer")
    g.add_edge("script_writer", "title_and_tags")
    g.add_edge("title_and_tags", "quality_gate")

    # Quality gate routing
    g.add_conditional_edges(
        "quality_gate",
        should_retry,
        {
            "approved": END,
            "retry": "hook_writer",   # retry from hook stage
        },
    )

    return g.compile()
