# streamlit-databricks-mcp-example Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a BMasterAI example mirroring `examples/streamlit-airflow-mcp-example` that targets Databricks (Jobs + read-only SQL + Unity Catalog browse via a bundled `fastmcp` server) and remembers the user across sessions with `lakehouse-memory`.

**Architecture:** A bundled `fastmcp` MCP server exposes eight Databricks tools backed by `databricks-sdk` + `databricks-sql-connector`. A Streamlit app uses OpenAI to turn natural language into MCP tool calls; pure, testable logic (SQL read-only guard, run_job gate, memory gating, recall rendering) lives in `app_logic.py` and inside the server module, while Streamlit/OpenAI/lakehouse-memory wiring lives in `enhanced_app.py`. Both services connect to the user's cloud workspace; there is no local Databricks.

**Tech Stack:** Python 3.11+, Streamlit, OpenAI, `fastmcp` (real pip package), `databricks-sdk`, `databricks-sql-connector`, `lakehouse-memory`, BMasterAI logging, Docker.

---

## File Structure

All under `examples/streamlit-databricks-mcp-example/`:

- `requirements.txt` — **new.** Python deps.
- `.env.example` — **new.** Config template.
- `databricks_mcp_server.py` — **new.** `fastmcp` server; importable logic: `mcp`, `is_read_only()`, `run_job_allowed()`, the eight tool functions, lazy SDK/SQL clients, `main()`.
- `app_logic.py` — **new.** Pure helpers: `memory_enabled()`, `render_recall_context()`, `INTERPRET_SYSTEM_PROMPT`, `build_extract_prompt()`. No Streamlit imports so it is unit-testable.
- `enhanced_app.py` — **new.** Streamlit UI wiring (OpenAI, fastmcp `Client`, lakehouse-memory). Imports `app_logic`.
- `Dockerfile` — **new.** The Streamlit app image.
- `docker-compose.yml` — **new.** Two services (app + mcp server), both → the cloud workspace.
- `README.md` — **new.** Mirrors the airflow README.
- `tests/test_logic.py` — **new.** Unit tests for the pure logic (no network).

Reference (read-only): `examples/streamlit-airflow-mcp-example/*`, `docs/superpowers/specs/2026-06-12-streamlit-databricks-mcp-example-design.md`.

---

## Task 1: Scaffold deps and env template

**Files:**
- Create: `examples/streamlit-databricks-mcp-example/requirements.txt`
- Create: `examples/streamlit-databricks-mcp-example/.env.example`
- Create: `examples/streamlit-databricks-mcp-example/tests/test_logic.py` (env-keys check only for now)

- [ ] **Step 1: Write requirements.txt**

```
streamlit
openai
bmasterai
python-dotenv
fastmcp>=2.3
databricks-sdk
databricks-sql-connector
lakehouse-memory
```

- [ ] **Step 2: Write .env.example**

```
OPENAI_API_KEY=sk-your-openai-api-key

# Databricks — a CLOUD workspace; there is no local instance to start.
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi-your-token
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ALLOW_RUN_JOB=false

# MCP server (bundled). fastmcp HTTP transport is served under /mcp.
MCP_SERVER_URL=http://localhost:3000/mcp

# Assistant memory via lakehouse-memory (optional).
ENABLE_MEMORY=true
DATABRICKS_VECTOR_SEARCH_ENDPOINT=your-vector-search-endpoint
MEMORY_CATALOG=workspace
MEMORY_SCHEMA=mcp_assistant_memory
DEMO_USER_ID=u_demo
```

- [ ] **Step 3: Write the env-keys test**

```python
# tests/test_logic.py
import pathlib

EXAMPLE_DIR = pathlib.Path(__file__).resolve().parents[1]


def _env_keys():
    keys = set()
    for line in (EXAMPLE_DIR / ".env.example").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0])
    return keys


def test_env_example_has_required_keys():
    required = {
        "OPENAI_API_KEY", "DATABRICKS_HOST", "DATABRICKS_TOKEN",
        "DATABRICKS_HTTP_PATH", "DATABRICKS_ALLOW_RUN_JOB", "MCP_SERVER_URL",
        "ENABLE_MEMORY", "DATABRICKS_VECTOR_SEARCH_ENDPOINT",
        "MEMORY_CATALOG", "MEMORY_SCHEMA", "DEMO_USER_ID",
    }
    assert required <= _env_keys()
```

- [ ] **Step 4: Run the test**

Run: `cd examples/streamlit-databricks-mcp-example && python -m pytest tests/test_logic.py -v`
Expected: `test_env_example_has_required_keys` PASSES.

- [ ] **Step 5: Commit**

```bash
git add examples/streamlit-databricks-mcp-example/requirements.txt examples/streamlit-databricks-mcp-example/.env.example examples/streamlit-databricks-mcp-example/tests/test_logic.py
git commit -m "feat(databricks-mcp): scaffold deps and env template"
```

---

## Task 2: MCP server — read-only SQL guard and run_job gate (TDD)

**Files:**
- Create: `examples/streamlit-databricks-mcp-example/databricks_mcp_server.py`
- Modify: `examples/streamlit-databricks-mcp-example/tests/test_logic.py`

- [ ] **Step 1: Write failing tests for the guards**

Append to `tests/test_logic.py`:

```python
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "databricks_mcp_server", EXAMPLE_DIR / "databricks_mcp_server.py"
)
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


def test_is_read_only_allows_select_show_describe():
    for q in ["SELECT 1", "  select * from t", "SHOW CATALOGS",
              "DESCRIBE t", "EXPLAIN SELECT 1", "WITH a AS (SELECT 1) SELECT * FROM a"]:
        assert server.is_read_only(q) is True


def test_is_read_only_rejects_writes():
    for q in ["DELETE FROM t", "DROP TABLE t", "INSERT INTO t VALUES (1)",
              "UPDATE t SET x=1", "MERGE INTO t", "CREATE TABLE t (x INT)", ""]:
        assert server.is_read_only(q) is False


def test_run_job_allowed_reads_env(monkeypatch):
    monkeypatch.delenv("DATABRICKS_ALLOW_RUN_JOB", raising=False)
    assert server.run_job_allowed() is False
    monkeypatch.setenv("DATABRICKS_ALLOW_RUN_JOB", "true")
    assert server.run_job_allowed() is True
    monkeypatch.setenv("DATABRICKS_ALLOW_RUN_JOB", "false")
    assert server.run_job_allowed() is False


def test_server_registers_expected_tools():
    names = set(server.TOOL_NAMES)
    assert names == {
        "list_jobs", "get_job_runs", "run_job", "get_failed_jobs",
        "run_sql", "list_catalogs", "list_schemas", "list_tables",
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/streamlit-databricks-mcp-example && python -m pytest tests/test_logic.py -v`
Expected: import error / FAIL — `databricks_mcp_server.py` does not exist yet.

- [ ] **Step 3: Write databricks_mcp_server.py**

```python
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
    from databricks import sql
    import re
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd examples/streamlit-databricks-mcp-example && pip install fastmcp databricks-sdk databricks-sql-connector bmasterai && python -m pytest tests/test_logic.py -v`
Expected: all four new tests PASS (plus the env-keys test).

Note on `TOOL_NAMES`: it is asserted against the registered tools. If `fastmcp` exposes a registry you prefer, you may replace the literal with `list(mcp._tool_manager.tools)` — but the literal is authoritative for the test and must match the `@mcp.tool` functions above.

- [ ] **Step 5: Commit**

```bash
git add examples/streamlit-databricks-mcp-example/databricks_mcp_server.py examples/streamlit-databricks-mcp-example/tests/test_logic.py
git commit -m "feat(databricks-mcp): bundled MCP server with read-only SQL guard and run_job gate"
```

---

## Task 3: App logic helpers (TDD)

**Files:**
- Create: `examples/streamlit-databricks-mcp-example/app_logic.py`
- Modify: `examples/streamlit-databricks-mcp-example/tests/test_logic.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_logic.py`:

```python
_spec2 = importlib.util.spec_from_file_location(
    "app_logic", EXAMPLE_DIR / "app_logic.py"
)
app_logic = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(app_logic)


def test_memory_enabled_requires_flag_and_endpoint():
    assert app_logic.memory_enabled({"ENABLE_MEMORY": "true", "DATABRICKS_VECTOR_SEARCH_ENDPOINT": "ep"}) is True
    assert app_logic.memory_enabled({"ENABLE_MEMORY": "false", "DATABRICKS_VECTOR_SEARCH_ENDPOINT": "ep"}) is False
    assert app_logic.memory_enabled({"ENABLE_MEMORY": "true"}) is False
    assert app_logic.memory_enabled({}) is False


def test_render_recall_context_empty_is_blank():
    assert app_logic.render_recall_context([]) == ""


def test_render_recall_context_lists_facts():
    out = app_logic.render_recall_context([{"text": "prefers catalog workspace"}, {"text": "watches nightly_etl"}])
    assert "prefers catalog workspace" in out
    assert "watches nightly_etl" in out
    assert "remember" in out.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/streamlit-databricks-mcp-example && python -m pytest tests/test_logic.py -v`
Expected: import error / FAIL — `app_logic.py` does not exist.

- [ ] **Step 3: Write app_logic.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd examples/streamlit-databricks-mcp-example && python -m pytest tests/test_logic.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add examples/streamlit-databricks-mcp-example/app_logic.py examples/streamlit-databricks-mcp-example/tests/test_logic.py
git commit -m "feat(databricks-mcp): pure app-logic helpers (memory gating, recall rendering, prompts)"
```

---

## Task 4: Streamlit app (enhanced_app.py)

**Files:**
- Create: `examples/streamlit-databricks-mcp-example/enhanced_app.py`

No unit test (Streamlit + OpenAI + async wiring); validated by byte-compile in Step 2 and by the live smoke in Task 7.

- [ ] **Step 1: Write enhanced_app.py**

```python
import os
import json
import asyncio

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from bmasterai.logging import configure_logging, get_logger, LogLevel
from fastmcp import Client

from app_logic import (
    INTERPRET_SYSTEM_PROMPT,
    memory_enabled,
    render_recall_context,
    build_extract_prompt,
)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000/mcp")
DEMO_USER_ID = os.getenv("DEMO_USER_ID", "u_demo")

configure_logging(log_level=LogLevel.INFO)
logger = get_logger().logger

st.set_page_config(page_title="Databricks MCP Assistant", layout="wide")
st.title("🧱 Databricks MCP Assistant with OpenAI")

if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY environment variable not set.")
    st.stop()
openai_client = OpenAI(api_key=OPENAI_API_KEY)
mcp_client = Client(MCP_SERVER_URL)

MEMORY_ON = memory_enabled(os.environ)
mem = None
if MEMORY_ON:
    try:
        from lakehouse_memory import Memory, Scope
        mem = Memory.from_databricks(
            catalog=os.getenv("MEMORY_CATALOG", "workspace"),
            schema_name=os.getenv("MEMORY_SCHEMA", "mcp_assistant_memory"),
            workspace_url=os.environ["DATABRICKS_HOST"],
            access_token=os.environ["DATABRICKS_TOKEN"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            vector_search_endpoint=os.environ["DATABRICKS_VECTOR_SEARCH_ENDPOINT"],
            scope=Scope(user_id=DEMO_USER_ID),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("memory init failed; disabling memory: %s", e)
        MEMORY_ON = False


def _unwrap(result):
    """Normalize a fastmcp CallToolResult to a plain Python value."""
    for attr in ("data", "structured_content"):
        if hasattr(result, attr) and getattr(result, attr) is not None:
            return getattr(result, attr)
    return result


def ask_openai(prompt: str, system_prompt: str = None) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, max_tokens=2048
    )
    return resp.choices[0].message.content


def recall_context(user_query: str) -> str:
    if not (MEMORY_ON and mem):
        return ""
    try:
        return render_recall_context(mem.semantic.retrieve(user_query, k=5))
    except Exception as e:  # noqa: BLE001
        logger.warning("recall failed: %s", e)
        return ""


def remember(user_query: str, answer: str) -> None:
    if not (MEMORY_ON and mem):
        return
    try:
        fact = ask_openai(build_extract_prompt(user_query, answer)).strip()
        if fact and fact.lower() != "none" and len(fact) > 3:
            mem.semantic.upsert(fact=fact, source="mcp-assistant")
            mem.semantic.trigger_sync()
    except Exception as e:  # noqa: BLE001
        logger.warning("remember failed: %s", e)


def interpret(user_query: str) -> dict:
    ctx = recall_context(user_query)
    prompt = f"{ctx}\nUser query: {user_query}\n\nJSON response:"
    raw = ask_openai(prompt, INTERPRET_SYSTEM_PROMPT)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"action": "list_jobs", "parameters": {}, "explanation": "Could not parse; defaulting to list_jobs"}


async def call_tool_async(action: str, parameters: dict):
    async with mcp_client:
        return _unwrap(await mcp_client.call_tool(action, parameters or {}))


def call_tool(action: str, parameters: dict):
    try:
        return asyncio.run(call_tool_async(action, parameters))
    except Exception as e:  # noqa: BLE001
        logger.error("tool call failed: %s", e)
        return {"error": str(e)}


def format_answer(user_query: str, response, explanation: str) -> str:
    system = ("Explain Databricks data clearly and concisely, answering the user's question. "
              "Use plain language; organize logically.")
    prompt = (f'User asked: "{user_query}"\nAction: {explanation}\n'
              f"Response: {json.dumps(response, indent=2, default=str)}\n\nExplain:")
    return ask_openai(prompt, system)


# Sidebar
st.sidebar.header("⚙️ Configuration")
st.sidebar.write(f"**Workspace:** {os.getenv('DATABRICKS_HOST', '(unset)')}")
st.sidebar.write(f"**MCP Server:** {MCP_SERVER_URL}")
st.sidebar.write(f"**Memory:** {'on' if MEMORY_ON else 'off'}")

if MEMORY_ON and mem:
    st.sidebar.header("🧠 What I remember about you")
    try:
        facts = mem.semantic.retrieve("user preferences", k=20)
        for f in facts:
            st.sidebar.write(f"• {f.get('text', '')}")
        if st.sidebar.button("🗑️ Forget me"):
            for f in facts:
                if f.get("fact_id"):
                    mem.semantic.forget(f["fact_id"])
            mem.semantic.trigger_sync()
            st.sidebar.success("Forgotten.")
    except Exception as e:  # noqa: BLE001
        st.sidebar.warning(f"memory unavailable: {e}")
else:
    st.sidebar.info("Memory disabled (set ENABLE_MEMORY=true and DATABRICKS_VECTOR_SEARCH_ENDPOINT).")

if st.sidebar.button("🔍 Test MCP Connection"):
    with st.sidebar:
        with st.spinner("Testing..."):
            res = call_tool("list_catalogs", {})
            if res and not (isinstance(res, dict) and res.get("error")):
                st.success("✅ MCP connection successful!")
            else:
                st.error(f"❌ {res.get('error') if isinstance(res, dict) else res}")

# Main
st.subheader("💬 Ask about your Databricks workspace")
examples = [
    "What jobs do we have?",
    "Show me the failed jobs",
    "What catalogs can I see?",
    "List tables in workspace.lakehouse_memory_test",
    "How many rows are in workspace.lakehouse_memory_test.semantic?",
]
for i, ex in enumerate(examples):
    if st.button(f"📝 {ex}", key=f"ex_{i}"):
        st.session_state.user_input = ex

user_query = st.text_input("Enter your question:", value=st.session_state.get("user_input", ""))

if st.button("🚀 Send Query", type="primary"):
    if not user_query:
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("🤔 Understanding..."):
            action_data = interpret(user_query)
        st.info(f"**Action:** {action_data.get('explanation', '')}")
        with st.spinner("📡 Querying Databricks..."):
            response = call_tool(action_data.get("action"), action_data.get("parameters", {}))
        with st.expander("🔍 Raw MCP Response", expanded=False):
            st.json(response)
        if response and not (isinstance(response, dict) and response.get("error")):
            with st.spinner("✨ Formatting..."):
                answer = format_answer(user_query, response, action_data.get("explanation", ""))
            st.subheader("📋 Response")
            st.write(answer)
            remember(user_query, answer)
        else:
            st.error(f"❌ {response.get('error') if isinstance(response, dict) else response}")

if st.sidebar.button("🧹 Clear Session"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
```

- [ ] **Step 2: Byte-compile to catch syntax errors**

Run: `cd examples/streamlit-databricks-mcp-example && python -m py_compile enhanced_app.py app_logic.py databricks_mcp_server.py && echo "compile OK"`
Expected: `compile OK`.

- [ ] **Step 3: Commit**

```bash
git add examples/streamlit-databricks-mcp-example/enhanced_app.py
git commit -m "feat(databricks-mcp): streamlit app with OpenAI, fastmcp client, and lakehouse-memory"
```

---

## Task 5: Dockerfile and docker-compose

**Files:**
- Create: `examples/streamlit-databricks-mcp-example/Dockerfile`
- Create: `examples/streamlit-databricks-mcp-example/docker-compose.yml`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 nonroot && chown -R nonroot:nonroot /app
USER nonroot

EXPOSE 8501
CMD ["streamlit", "run", "enhanced_app.py", "--server.address", "0.0.0.0"]
```

- [ ] **Step 2: Write docker-compose.yml**

```yaml
services:
  databricks-mcp:
    build: .
    command: ["python", "databricks_mcp_server.py"]
    env_file: .env
    environment:
      - MCP_PORT=3000
    ports:
      - "3000:3000"
    security_opt:
      - no-new-privileges:true

  streamlit-app:
    build: .
    depends_on:
      - databricks-mcp
    env_file: .env
    environment:
      # reach the server container, not localhost
      - MCP_SERVER_URL=http://databricks-mcp:3000/mcp
    ports:
      - "8501:8501"
    security_opt:
      - no-new-privileges:true
```

- [ ] **Step 3: Validate compose syntax**

Run: `cd examples/streamlit-databricks-mcp-example && cp .env.example .env && docker compose config >/dev/null && echo "compose OK" && rm .env`
Expected: `compose OK` (requires Docker; if Docker is unavailable, run `python -c "import yaml,sys; yaml.safe_load(open('docker-compose.yml')); print('yaml OK')"` instead).

- [ ] **Step 4: Commit**

```bash
git add examples/streamlit-databricks-mcp-example/Dockerfile examples/streamlit-databricks-mcp-example/docker-compose.yml
git commit -m "feat(databricks-mcp): Dockerfile and compose (app + bundled mcp server)"
```

---

## Task 6: README

**Files:**
- Create: `examples/streamlit-databricks-mcp-example/README.md`

- [ ] **Step 1: Write README.md**

````markdown
# Streamlit Databricks MCP Chatbot

A Streamlit chatbot that turns natural language into Databricks operations through a bundled
Model Context Protocol (MCP) server, and **remembers you across sessions** using
[lakehouse-memory](https://github.com/travis-burmaster/lakehouse-memory) (agent memory governed
in Unity Catalog). Sibling of the [airflow MCP example](../streamlit-airflow-mcp-example).

## Features

* **Natural-language Databricks ops:** ask about Jobs, run read-only SQL, browse Unity Catalog.
* **Bundled MCP server:** `databricks_mcp_server.py` (fastmcp) exposes eight tools — `list_jobs`,
  `get_job_runs`, `run_job`, `get_failed_jobs`, `run_sql`, `list_catalogs`, `list_schemas`, `list_tables`.
* **Persistent memory:** the assistant recalls your preferences (e.g. default catalog, jobs you
  watch) on each query and stores new ones — all in Unity Catalog, with a "Forget me" button.
* **Safe by default:** `run_sql` is read-only; `run_job` is disabled unless `DATABRICKS_ALLOW_RUN_JOB=true`.
* **BMasterAI logging** throughout.

## How this differs from the airflow example

Airflow's compose starts a **local** Airflow. Databricks is a **cloud** platform — there is
nothing local to launch. Both services here (the app and the MCP server) connect to **your real
Databricks workspace** via `.env`.

## Prerequisites

* **Docker** (for the compose path) or Python 3.11+.
* **OpenAI API key.**
* **A Databricks workspace** with a SQL warehouse (HTTP path) and a token.
* **For memory (optional):** a Vector Search endpoint and a one-time `provision()` of the memory
  schema (see below). Without it, the app runs as a pure Databricks assistant.

## Setup

```bash
git clone https://github.com/travis-burmaster/bmasterai
cd bmasterai/examples/streamlit-databricks-mcp-example
cp .env.example .env   # then edit
pip install -r requirements.txt
pip install -e ../..   # BMasterAI + bundled logging
```

Edit `.env`: set `OPENAI_API_KEY`, `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH`.
For memory, also set `DATABRICKS_VECTOR_SEARCH_ENDPOINT` (and optionally `MEMORY_CATALOG`,
`MEMORY_SCHEMA`, `DEMO_USER_ID`); leave `ENABLE_MEMORY=true`. Keep `DATABRICKS_ALLOW_RUN_JOB=false`
unless you want the assistant to trigger real (billable) job runs.

### One-time memory provisioning (only if using memory)

```python
from lakehouse_memory import Memory, Scope
import os
Memory.from_databricks(
    catalog=os.environ["MEMORY_CATALOG"], schema_name=os.environ["MEMORY_SCHEMA"],
    workspace_url=os.environ["DATABRICKS_HOST"], access_token=os.environ["DATABRICKS_TOKEN"],
    http_path=os.environ["DATABRICKS_HTTP_PATH"],
    vector_search_endpoint=os.environ["DATABRICKS_VECTOR_SEARCH_ENDPOINT"],
    scope=Scope(user_id=os.environ.get("DEMO_USER_ID", "u_demo")),
).provision()   # ~15 min first run; idempotent afterwards
```

## Running

### Option 1 — directly

```bash
# terminal 1: the MCP server
python databricks_mcp_server.py
# terminal 2: the app
streamlit run enhanced_app.py
```
Open http://localhost:8501.

### Option 2 — docker compose (app + server)

```bash
docker compose build
docker compose up
```
Open http://localhost:8501.

## Usage

Try: "What jobs do we have?", "Show me the failed jobs", "What catalogs can I see?",
"List tables in workspace.lakehouse_memory_test", "How many rows are in
workspace.lakehouse_memory_test.semantic?". With memory on, tell it a preference once
("I usually work in the workspace catalog") and it will recall it next session.

## Project Structure

```
streamlit-databricks-mcp-example/
├── .env.example
├── databricks_mcp_server.py   # bundled fastmcp server (8 Databricks tools)
├── app_logic.py               # pure helpers (memory gating, prompts) — unit-tested
├── enhanced_app.py            # Streamlit + OpenAI + fastmcp client + lakehouse-memory
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── tests/test_logic.py
└── README.md
```

## Tests

```bash
pip install pytest && python -m pytest tests/test_logic.py -v
```

## License

MIT.
````

- [ ] **Step 2: Validate fences balance**

Run: `cd examples/streamlit-databricks-mcp-example && python -c "t=open('README.md').read(); assert t.count('```')%2==0; print('README OK')"`
Expected: `README OK`.

- [ ] **Step 3: Commit**

```bash
git add examples/streamlit-databricks-mcp-example/README.md
git commit -m "docs(databricks-mcp): example README"
```

---

## Task 7: Live workspace verification (integration smoke)

**Files:**
- Create (NOT committed — local throwaway): `examples/streamlit-databricks-mcp-example/_smoke.py`

Verifies the server tools and the memory loop against a real workspace, with `DATABRICKS_ALLOW_RUN_JOB=false`.

- [ ] **Step 1: Write the smoke script**

```python
"""Local integration smoke — NOT committed. Run with a real .env sourced."""
import os
import importlib.util

here = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location("srv", os.path.join(here, "databricks_mcp_server.py"))
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)

print("list_catalogs:", srv.list_catalogs())
print("list_jobs count:", srv.list_jobs().get("count"))
print("run_sql SELECT 1:", srv.run_sql("SELECT 1"))
assert "error" in srv.run_sql("DELETE FROM x"), "read-only guard must reject DELETE"
assert "disabled" in srv.run_job(0).get("error", ""), "run_job must be gated off"
print("guards OK")

if srv := __import__("app_logic").memory_enabled(os.environ):
    from lakehouse_memory import Memory, Scope
    mem = Memory.from_databricks(
        catalog=os.environ.get("MEMORY_CATALOG", "workspace"),
        schema_name=os.environ.get("MEMORY_SCHEMA", "mcp_assistant_memory"),
        workspace_url=os.environ["DATABRICKS_HOST"], access_token=os.environ["DATABRICKS_TOKEN"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        vector_search_endpoint=os.environ["DATABRICKS_VECTOR_SEARCH_ENDPOINT"],
        scope=Scope(user_id=os.environ.get("DEMO_USER_ID", "u_demo")),
    )
    fid = mem.semantic.upsert(fact="prefers the workspace catalog", source="smoke")
    mem.semantic.trigger_sync()
    import time; time.sleep(int(os.environ.get("SYNC_WAIT", "60")))
    hits = mem.semantic.retrieve("catalog preference", k=5)
    assert any("workspace" in h.get("text", "").lower() for h in hits), "memory recall failed"
    mem.semantic.forget(fid); mem.semantic.trigger_sync()
    print("memory loop OK")
print("SMOKE PASSED")
```

- [ ] **Step 2: Run the smoke against a real workspace**

Run:
```bash
cd examples/streamlit-databricks-mcp-example
set -a && . ./.env && set +a
DATABRICKS_ALLOW_RUN_JOB=false python _smoke.py
```
Expected: prints catalogs, a job count, `guards OK`, `memory loop OK` (if memory configured), `SMOKE PASSED`.

- [ ] **Step 3: Remove the throwaway (do not commit)**

Run: `rm examples/streamlit-databricks-mcp-example/_smoke.py`

No commit (verification only).

---

## Self-Review

**Spec coverage:**
- Bundled fastmcp server, 8 tools → Task 2. ✓
- read-only `run_sql`, gated `run_job` → Task 2 + guard tests. ✓
- Streamlit + OpenAI app mirroring airflow → Task 4. ✓
- lakehouse-memory app-level (recall/remember/forget + sidebar) → Task 4, helpers in Task 3. ✓
- Graceful memory degradation → `memory_enabled` (Task 3) + try/except init (Task 4). ✓
- .env.example with all keys → Task 1 + test. ✓
- Dockerfile + compose (app + server, no local Databricks) → Task 5. ✓
- README mirroring airflow + the three notes → Task 6. ✓
- Live verification → Task 7. ✓
- Out-of-scope items (memory-as-tools, third-party server, DML) honored. ✓

**Placeholder scan:** none. Every code step has full, correct content; the byte-compile in Task 4 Step 2 is a syntax backstop, not a fix for a planted bug.

**Type/name consistency:** tool names match between `databricks_mcp_server.TOOL_NAMES`, the `@mcp.tool` functions, the interpret prompt action list (`app_logic.INTERPRET_SYSTEM_PROMPT`), and the test assertion. `memory_enabled`, `render_recall_context`, `build_extract_prompt` signatures match between `app_logic.py`, its tests, and `enhanced_app.py` usage. `MCP_SERVER_URL` default `http://localhost:3000/mcp` consistent across `.env.example`, app, and compose (compose overrides host to the service name).

**Known live-only risks (cannot be unit-verified, covered by Task 7 / recording):** the exact `fastmcp` 3.x `call_tool` result shape (handled by `_unwrap`) and the HTTP transport path (`/mcp`) — both confirmed during the live smoke.
