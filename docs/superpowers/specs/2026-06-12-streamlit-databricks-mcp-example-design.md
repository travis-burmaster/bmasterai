# streamlit-databricks-mcp-example — design

**Date:** 2026-06-12
**Status:** Approved design, pre-implementation
**Goal:** A BMasterAI example that mirrors `examples/streamlit-airflow-mcp-example`, but targets **Databricks**: a Streamlit + OpenAI chatbot that drives a bundled Databricks MCP server through natural language, and remembers the user across sessions using `lakehouse-memory` (agent memory governed in Unity Catalog).

## Why this example

The airflow example shows BMasterAI + an MCP server + OpenAI turning plain English into Airflow operations. This one does the same for Databricks — Jobs, SQL, and Unity Catalog browsing — and adds a second story on top: an assistant whose memory of *you* (your preferred catalog, the jobs you watch) persists across sessions and lives in Unity Catalog, not a sidecar store. It dogfoods `lakehouse-memory` in a believable setting and ties the two projects together.

## Structural difference from the airflow example

Airflow's `docker-compose.yml` stands up a **local** Airflow + Postgres. Databricks is a **cloud** platform — there is nothing local to start. Our compose runs only two services (the Streamlit app and the bundled MCP server), and **both connect to the user's real Databricks workspace** via `.env`. The README must call this out so nobody waits for a "local Databricks" that does not exist.

## fastmcp dependency note

The `fastmcp` module bundled in `bmasterai` (`src/fastmcp/`) is a **client-side stub**: its `FastMCP.serve()` is an explicit no-op and it exports only `FastMCP`/`MCPClient`. The airflow app already relies on the **real `fastmcp` pip package** (`from fastmcp import Client`, async `call_tool`). This example does the same — the real `fastmcp` pip package powers both the bundled server (`FastMCP` + `@mcp.tool`, HTTP transport) and the app's client (`Client`). `fastmcp` stays in `requirements.txt`.

## File layout

```
examples/streamlit-databricks-mcp-example/
├── .env.example             # OpenAI + Databricks creds + memory config + MCP_SERVER_URL
├── databricks_mcp_server.py # fastmcp server exposing the 8 Databricks tools
├── enhanced_app.py          # Streamlit + OpenAI + fastmcp client + lakehouse-memory
├── requirements.txt         # + databricks-sdk, databricks-sql-connector, lakehouse-memory
├── Dockerfile               # the Streamlit app
├── docker-compose.yml       # app + mcp server, both -> the user's cloud workspace
└── README.md
```

## Component 1 — the bundled MCP server (`databricks_mcp_server.py`)

A real `fastmcp` `FastMCP` server, HTTP transport on port 3000, eight tools. Auth from env (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH`). Every tool returns its result or `{"error": "..."}` so the UI degrades gracefully (matching the airflow pattern).

Jobs (via `databricks-sdk` `WorkspaceClient.jobs`):
- `list_jobs()` — job id + name + creator.
- `get_job_runs(job_id)` — recent runs with state/result.
- `run_job(job_id)` — **gated**: only runs if `DATABRICKS_ALLOW_RUN_JOB` is truthy; otherwise returns `{"error": "job execution disabled (set DATABRICKS_ALLOW_RUN_JOB=true)"}`. Off by default because it triggers real billable compute.
- `get_failed_jobs()` — jobs whose latest run failed.

SQL (via `databricks-sql-connector`, using `DATABRICKS_HTTP_PATH`):
- `run_sql(query)` — **read-only**: the query's first keyword must be one of `SELECT`, `SHOW`, `DESCRIBE`, `DESC`, `EXPLAIN`, `WITH`; anything else returns an error without executing. Returns columns + up to 100 rows (`LIMIT` applied if absent).

Unity Catalog (via `databricks-sdk`):
- `list_catalogs()`, `list_schemas(catalog)`, `list_tables(catalog, schema)`.

## Component 2 — the Streamlit app (`enhanced_app.py`)

Mirrors the airflow app: OpenAI (`gpt-4o-mini`) interprets the query into `{action, parameters, explanation}`; a `fastmcp.Client` calls the matching tool inside `async with`; OpenAI formats the raw response. Swapped vs airflow: the action list in the interpret prompt, the example queries, and the sidebar labels. Retained: the "Test MCP Connection" button, the raw-response expander, BMasterAI `configure_logging`/`get_logger` logging.

Example queries surfaced in the UI:
- "What jobs do we have?" · "Show me the failed jobs" · "Run the nightly_etl job"
- "What catalogs can I see?" · "List tables in workspace.lakehouse_memory_test"
- "How many rows are in workspace.lakehouse_memory_test.semantic?" (the one lakehouse-memory cross-reference)

## Component 3 — persistent assistant memory (`lakehouse-memory`)

Integrated only in `enhanced_app.py`. Gated by `ENABLE_MEMORY` **and** presence of `DATABRICKS_VECTOR_SEARCH_ENDPOINT`; if either is missing the app runs as a pure Databricks assistant and shows a "memory disabled" note (graceful degradation).

- On startup: `mem = Memory.from_databricks(catalog=MEMORY_CATALOG, schema_name=MEMORY_SCHEMA, workspace_url=..., access_token=..., http_path=..., vector_search_endpoint=..., scope=Scope(user_id=DEMO_USER_ID))`. Defaults: `MEMORY_CATALOG=workspace`, `MEMORY_SCHEMA=mcp_assistant_memory`, `DEMO_USER_ID=u_demo`. Reuses the same Databricks creds already in `.env`.
- **Before interpretation:** `recalled = mem.semantic.retrieve(user_query, k=5)`; recalled facts are injected into the interpret system prompt as "What you remember about this user," so the model can resolve "my usual job" / default the catalog.
- **After answering:** one short OpenAI extraction call returns a durable preference fact from the exchange or the literal `none`; non-`none`, non-trivial facts are stored via `mem.semantic.upsert(fact, source="mcp-assistant")` then `mem.semantic.trigger_sync()`.
- **Sidebar "🧠 What I remember about you":** lists `mem.semantic.retrieve("user preferences", k=20)` results; a **"Forget me"** button calls `mem.semantic.forget(fact_id)` for each, demonstrating governed deletion interactively.
- One-time prerequisite: `mem.provision()` for the memory schema + Vector Search index (documented; ~15 min first run, idempotent thereafter).

## Environment variables (`.env.example`)

```
OPENAI_API_KEY=sk-...
# Databricks (cloud workspace — no local instance)
DATABRICKS_HOST=https://<workspace>.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<id>
DATABRICKS_ALLOW_RUN_JOB=false          # gate real job execution
# MCP
MCP_SERVER_URL=http://localhost:3000
# Assistant memory (lakehouse-memory) — optional
ENABLE_MEMORY=true
DATABRICKS_VECTOR_SEARCH_ENDPOINT=<vs-endpoint>   # required for memory
MEMORY_CATALOG=workspace
MEMORY_SCHEMA=mcp_assistant_memory
DEMO_USER_ID=u_demo
```

## Data flow

```
user query
  -> (if memory) recall relevant memories  ── lakehouse-memory.semantic.retrieve
  -> OpenAI interpret (query + recalled context) -> {action, parameters}
  -> fastmcp Client.call_tool(action, parameters) -> databricks_mcp_server -> Databricks
  -> OpenAI format raw response -> answer shown
  -> (if memory) OpenAI extract durable fact -> lakehouse-memory.semantic.upsert
```

## Error handling

- Every MCP tool catches exceptions and returns `{"error": ...}`; the app shows the error and skips formatting.
- `run_sql` rejects non-read-only statements before execution.
- `run_job` is disabled unless explicitly enabled.
- Memory failures (no VS endpoint, unprovisioned schema) disable memory with a visible note rather than crashing the app.

## Testing / verification (before "done")

Against a real workspace (the maintainer's, with the existing `lakehouse_memory_test` Vector Search endpoint), with `DATABRICKS_ALLOW_RUN_JOB=false`:
1. Start `databricks_mcp_server.py`; call read-only tools: `list_jobs`, `list_catalogs`, `list_schemas("workspace")`, `run_sql("SELECT 1")`, and a count on `workspace.lakehouse_memory_test.semantic`.
2. Assert `run_sql("DELETE ...")` is rejected and `run_job(...)` returns the disabled message.
3. Exercise the memory loop directly: `upsert` a fact → `retrieve` returns it → `forget` clears it (mirrors the lakehouse-memory smoke test).
The example ships verified against a live workspace, not merely written.

## README

Mirrors the airflow README section-for-section — Features, Prerequisites, Setup & Installation, Running (direct + docker-compose), Usage, Project Structure, Contributing, License — adapted for Databricks, with explicit notes that (a) there is no local Databricks to launch, (b) `run_job` is off by default, and (c) memory requires a Vector Search endpoint and a one-time `provision()`.

## Out of scope

- Memory-as-MCP-tools (remember/recall/forget exposed to the model) — considered and deferred; memory is app-level only.
- Wrapping a third-party or Databricks-managed MCP server — we bundle our own.
- Write/DML SQL, cluster management, or DLT pipelines — read-only SQL + Jobs + Catalog browse only.
- Any change to the `bmasterai` library or the bundled `fastmcp` stub.
