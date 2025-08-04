import requests
from typing import Dict, Any, Optional

class MCPClient:
    """Client for interacting with a running Airflow MCP server instance."""

    def __init__(self, server_url: str = "http://localhost:3000"):
        self.server_url = server_url.rstrip("/")

    def run_mcp_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Send a command to the MCP server via HTTP."""
        try:
            response = requests.post(
                f"{self.server_url}/command",
                json={"command": command},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"output": None, "error": str(e)}
    
    def get_dags(self) -> Optional[Dict[str, Any]]:
        """Get list of DAGs from Airflow via MCP."""
        return self.run_mcp_command("list_dags")

    def get_dag_runs(self, dag_id: str) -> Optional[Dict[str, Any]]:
        """Get runs for a specific DAG."""
        return self.run_mcp_command(f"get_dag_runs {dag_id}")

    def trigger_dag(self, dag_id: str) -> Optional[Dict[str, Any]]:
        """Trigger a DAG run."""
        return self.run_mcp_command(f"trigger_dag {dag_id}")

    def get_failed_dags(self) -> Optional[Dict[str, Any]]:
        """Get list of failed DAGs."""
        return self.run_mcp_command("get_failed_dags")


