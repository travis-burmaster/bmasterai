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
