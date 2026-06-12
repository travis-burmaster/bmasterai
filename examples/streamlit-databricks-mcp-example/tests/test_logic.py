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
