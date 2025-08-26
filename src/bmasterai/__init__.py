"""
BMasterAI - Advanced Multi-Agent AI Framework

A comprehensive Python framework for building multi-agent AI systems
with advanced logging, monitoring, and integrations.
"""

__version__ = "0.2.2"
__author__ = "Travis Burmaster"
__email__ = "travis@burmaster.com"

from .logging import configure_logging, get_logger, LogLevel, EventType
from .monitoring import get_monitor
from .integrations import get_integration_manager
from .mcp_server import  mcp_server
from .reasoning_logger import (
    ReasoningSession, ChainOfThought, with_reasoning_logging, log_reasoning
)

__all__ = [
    "configure_logging",
    "get_logger", 
    "LogLevel",
    "EventType",
    "get_monitor",
    "get_integration_manager",
    "mcp_server",
    "ReasoningSession",
    "ChainOfThought", 
    "with_reasoning_logging",
    "log_reasoning"
]