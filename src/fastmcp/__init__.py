"""Lightweight fallback implementation of the fastmcp package.

This module provides minimal client and server stubs so the examples and
library can run in environments where the real ``fastmcp`` dependency is
unavailable.  It is **not** a full implementation of the Model Context
Protocol and only supports the limited HTTP interactions used in the
examples.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional
import requests

from bmasterai.logging import get_logger

# Use the underlying Python logger from BMasterAI's logging system
_bm_logger = get_logger()
logger = _bm_logger.logger


class FastMCP:
    """Very small stand‑in for the real FastMCP server class.

    The implementation only stores tools registered via the ``tool``
    decorator.  The ``serve`` method is a no-op; it merely logs that the
    stub server cannot actually start.
    """

    def __init__(self, name: str, instructions: str = "") -> None:
        self.name = name
        self.instructions = instructions
        self.tools: Dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[func.__name__] = func
            return func

        return decorator

    def serve(self, host: str = "0.0.0.0", port: int = 3000) -> None:
        logger.warning(
            "FastMCP stub server invoked; no server will actually be started."
        )


class MCPClient:
    """HTTP-based client used by the examples.

    It mirrors the API of the real ``fastmcp`` client enough for the
    Streamlit examples to interact with a running ``airflow-mcp`` server.
    """

    def __init__(self, server_url: str = "http://localhost:3000") -> None:
        self.server_url = server_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{self.server_url}{path}", json=payload, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:  # pragma: no cover - network errors
            logger.error("MCP request failed: %s", e)
            return {"output": None, "error": str(e)}

    def query(self, query: str) -> Dict[str, Any]:
        return self._post("/query", {"query": query})

    def command(self, command: str) -> Dict[str, Any]:
        return self._post("/command", {"command": command})

    # Convenience helpers used by the Streamlit example
    def get_dags(self) -> Dict[str, Any]:
        return self.command("list_dags")

    def get_dag_runs(self, dag_id: str) -> Dict[str, Any]:
        return self.command(f"get_dag_runs {dag_id}")

    def trigger_dag(self, dag_id: str) -> Dict[str, Any]:
        return self.command(f"trigger_dag {dag_id}")

    def get_failed_dags(self) -> Dict[str, Any]:
        return self.command("get_failed_dags")


__all__ = ["FastMCP", "MCPClient"]
