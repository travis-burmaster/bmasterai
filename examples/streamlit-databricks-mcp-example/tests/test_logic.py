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
