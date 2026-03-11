"""
Shared state flowing through the LangGraph pipeline.
Each agent reads from and writes to this TypedDict.
"""
from typing import TypedDict, Optional


class VideoState(TypedDict):
    # Input
    topic: str                      # User-supplied topic or niche

    # Trend Research Agent output
    trending_angle: str             # The specific viral angle found
    trend_context: str              # Supporting data / why it's trending
    competitor_hooks: list[str]     # Sample hooks from top-performing videos

    # Hook Agent output
    hook: str                       # Opening 3–5 second line to stop the scroll

    # Script Agent output
    script: str                     # Full 45–60 second script

    # Title & Tags Agent output
    title: str                      # Viral-optimised title (< 70 chars)
    tags: list[str]                 # SEO tags
    thumbnail_concept: str          # One-line thumbnail text / visual idea

    # Coordinator metadata
    errors: list[str]               # Any agent errors collected
    iterations: int                 # Retry count (quality gate)
    approved: Optional[bool]        # Quality gate result
