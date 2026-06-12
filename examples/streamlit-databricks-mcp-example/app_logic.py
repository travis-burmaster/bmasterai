"""Pure, Streamlit-free helpers for the Databricks MCP assistant.

Kept import-safe (no streamlit, no network) so it can be unit-tested.
"""

from __future__ import annotations

from typing import Any

INTERPRET_SYSTEM_PROMPT = """You interpret user questions about a Databricks workspace and choose one MCP action.

Available actions:
- list_jobs: list all jobs
- get_job_runs {job_id}: recent runs for a job
- run_job {job_id}: trigger a job
- get_failed_jobs: jobs whose latest run failed
- run_sql {query}: run a READ-ONLY SQL query (SELECT/SHOW/DESCRIBE/EXPLAIN/WITH only)
- list_catalogs: list Unity Catalog catalogs
- list_schemas {catalog}: list schemas in a catalog
- list_tables {catalog, schema}: list tables in a schema

Respond with a JSON object: {"action": ..., "parameters": {...}, "explanation": ...}.

Examples:
User: "What jobs failed?" -> {"action": "get_failed_jobs", "parameters": {}, "explanation": "Listing failed jobs"}
User: "List tables in workspace.sales" -> {"action": "list_tables", "parameters": {"catalog": "workspace", "schema": "sales"}, "explanation": "Listing tables in workspace.sales"}
User: "How many rows in workspace.mem.semantic?" -> {"action": "run_sql", "parameters": {"query": "SELECT count(*) FROM workspace.mem.semantic"}, "explanation": "Counting rows"}"""


def memory_enabled(env: dict[str, str]) -> bool:
    """Memory is on only when the flag is truthy AND a VS endpoint is set."""
    flag = str(env.get("ENABLE_MEMORY", "")).strip().lower() in {"1", "true", "yes"}
    return flag and bool(env.get("DATABRICKS_VECTOR_SEARCH_ENDPOINT"))


def render_recall_context(facts: list[dict[str, Any]]) -> str:
    """Build the 'what you remember' block injected into interpretation; blank if none."""
    items = [f.get("text", "") for f in facts if f.get("text")]
    if not items:
        return ""
    bullets = "\n".join(f"- {t}" for t in items)
    return f"What you remember about this user:\n{bullets}\n"


def build_extract_prompt(user_query: str, answer: str) -> str:
    """Prompt that asks the model to distill ONE durable preference fact, or 'none'."""
    return (
        "From this exchange, extract ONE durable fact about the user's preferences or "
        "context worth remembering for future sessions (e.g. a preferred catalog, a job "
        "they watch). Reply with the single fact as a short sentence, or exactly 'none'.\n\n"
        f"User asked: {user_query}\nAssistant answered: {answer}\n\nFact:"
    )
