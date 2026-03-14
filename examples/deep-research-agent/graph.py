"""
LangGraph pipeline for the deep research agent.

Flow:
  planner → web_searcher → analyzer → reflector
                                           ↓
                               needs_more_research?
                                /               \\
                              yes               no
                               ↓                ↓
                          web_searcher      synthesizer → END
                         (follow-ups)
"""
from langgraph.graph import StateGraph, END

from state import ResearchState
from agents import planner, web_searcher, analyzer, reflector, synthesizer


def should_continue(state: ResearchState) -> str:
    """Route after reflection: loop back for more research or synthesize."""
    if state.get("needs_more_research") and state.get("follow_up_questions"):
        return "more_research"
    return "synthesize"


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    # Register nodes
    graph.add_node("planner",     planner)
    graph.add_node("web_searcher", web_searcher)
    graph.add_node("analyzer",    analyzer)
    graph.add_node("reflector",   reflector)
    graph.add_node("synthesizer", synthesizer)

    # Define edges
    graph.set_entry_point("planner")
    graph.add_edge("planner",      "web_searcher")
    graph.add_edge("web_searcher", "analyzer")
    graph.add_edge("analyzer",     "reflector")

    # Conditional: loop or finish
    graph.add_conditional_edges(
        "reflector",
        should_continue,
        {
            "more_research": "web_searcher",
            "synthesize":    "synthesizer",
        },
    )
    graph.add_edge("synthesizer", END)

    return graph.compile()
