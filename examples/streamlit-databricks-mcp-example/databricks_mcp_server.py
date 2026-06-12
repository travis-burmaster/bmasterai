"""Bundled Databricks MCP server for the BMasterAI example.

Exposes eight tools (Jobs, read-only SQL, Unity Catalog browse) over fastmcp's
HTTP transport. Clients (SDK / SQL connector) are created lazily so the module
imports without credentials — keeping the pure logic unit-testable.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastmcp import FastMCP

from bmasterai.logging import configure_logging, get_logger, LogLevel

configure_logging(log_level=LogLevel.INFO)
logger = get_logger().logger

mcp = FastMCP("databricks-mcp")

_READ_ONLY_PREFIXES = ("SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN", "WITH")


def is_read_only(query: str) -> bool:
    """True only if the query's first keyword is a read-only statement."""
    stripped = (query or "").strip()
    if not stripped:
        return False
    first = stripped.split(None, 1)[0].upper()
    return first in _READ_ONLY_PREFIXES


def run_job_allowed() -> bool:
    """Real job execution is gated behind DATABRICKS_ALLOW_RUN_JOB."""
    return os.getenv("DATABRICKS_ALLOW_RUN_JOB", "false").strip().lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def _workspace():
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )


def _sql(query: str, max_rows: int = 100) -> dict[str, Any]:
    import re
    from databricks import sql
    host = re.sub(r"^https?://", "", os.environ["DATABRICKS_HOST"]).rstrip("/")
    q = query if " limit " in query.lower() else f"{query.rstrip(';')} LIMIT {max_rows}"
    conn = sql.connect(
        server_hostname=host,
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    )
    try:
        cur = conn.cursor()
        cur.execute(q)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchmany(max_rows)]
        return {"columns": cols, "rows": rows, "row_count": len(rows)}
    finally:
        conn.close()


@mcp.tool
def list_jobs() -> dict[str, Any]:
    """List Databricks Jobs (id, name, creator)."""
    try:
        jobs = [
            {"job_id": j.job_id,
             "name": getattr(j.settings, "name", None),
             "creator": j.creator_user_name}
            for j in _workspace().jobs.list()
        ]
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:  # noqa: BLE001
        logger.error("list_jobs failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def get_job_runs(job_id: int) -> dict[str, Any]:
    """Recent runs for a job (state + result)."""
    try:
        runs = [
            {"run_id": r.run_id,
             "state": getattr(r.state, "life_cycle_state", None) and r.state.life_cycle_state.value,
             "result": getattr(r.state, "result_state", None) and r.state.result_state.value,
             "start_time": r.start_time}
            for r in _workspace().jobs.list_runs(job_id=job_id, limit=10)
        ]
        return {"job_id": job_id, "runs": runs}
    except Exception as e:  # noqa: BLE001
        logger.error("get_job_runs failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def run_job(job_id: int) -> dict[str, Any]:
    """Trigger a job. Disabled unless DATABRICKS_ALLOW_RUN_JOB is set."""
    if not run_job_allowed():
        return {"error": "job execution disabled (set DATABRICKS_ALLOW_RUN_JOB=true)"}
    try:
        wait = _workspace().jobs.run_now(job_id=job_id)
        return {"job_id": job_id, "run_id": wait.run_id, "triggered": True}
    except Exception as e:  # noqa: BLE001
        logger.error("run_job failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def get_failed_jobs() -> dict[str, Any]:
    """Jobs whose most recent run failed."""
    try:
        w = _workspace()
        failed = []
        for j in w.jobs.list():
            latest = next(iter(w.jobs.list_runs(job_id=j.job_id, limit=1)), None)
            if latest and getattr(latest.state, "result_state", None) and latest.state.result_state.value == "FAILED":
                failed.append({"job_id": j.job_id, "name": getattr(j.settings, "name", None)})
        return {"failed_jobs": failed, "count": len(failed)}
    except Exception as e:  # noqa: BLE001
        logger.error("get_failed_jobs failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def run_sql(query: str) -> dict[str, Any]:
    """Run a READ-ONLY SQL query on the configured SQL warehouse."""
    if not is_read_only(query):
        return {"error": "only read-only queries are allowed (SELECT/SHOW/DESCRIBE/EXPLAIN/WITH)"}
    try:
        return _sql(query)
    except Exception as e:  # noqa: BLE001
        logger.error("run_sql failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def list_catalogs() -> dict[str, Any]:
    """List Unity Catalog catalogs."""
    try:
        names = [c.name for c in _workspace().catalogs.list()]
        return {"catalogs": names}
    except Exception as e:  # noqa: BLE001
        logger.error("list_catalogs failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def list_schemas(catalog: str) -> dict[str, Any]:
    """List schemas in a catalog."""
    try:
        names = [s.name for s in _workspace().schemas.list(catalog_name=catalog)]
        return {"catalog": catalog, "schemas": names}
    except Exception as e:  # noqa: BLE001
        logger.error("list_schemas failed: %s", e)
        return {"error": str(e)}


@mcp.tool
def list_tables(catalog: str, schema: str) -> dict[str, Any]:
    """List tables in a catalog.schema."""
    try:
        names = [t.name for t in _workspace().tables.list(catalog_name=catalog, schema_name=schema)]
        return {"catalog": catalog, "schema": schema, "tables": names}
    except Exception as e:  # noqa: BLE001
        logger.error("list_tables failed: %s", e)
        return {"error": str(e)}


TOOL_NAMES = [
    "list_jobs", "get_job_runs", "run_job", "get_failed_jobs",
    "run_sql", "list_catalogs", "list_schemas", "list_tables",
]


def main() -> None:
    port = int(os.getenv("MCP_PORT", "3000"))
    logger.info("starting databricks-mcp on :%d", port)
    mcp.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
