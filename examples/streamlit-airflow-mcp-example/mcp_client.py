import json
import subprocess
import os
from typing import Dict, Any, Optional

class MCPClient:
    """Client for interacting with the Airflow MCP server."""
    
    def __init__(self, airflow_api_url: str = "http://localhost:8088/api/v1", 
                 airflow_username: str = "airflow", 
                 airflow_password: str = "airflow"):
        self.airflow_api_url = airflow_api_url
        self.airflow_username = airflow_username
        self.airflow_password = airflow_password
        
    def run_mcp_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Run an MCP command using Docker."""
        try:
            # Set up environment variables for the Docker command
            env = os.environ.copy()
            env.update({
                "airflow_api_url": self.airflow_api_url,
                "airflow_username": self.airflow_username,
                "airflow_password": self.airflow_password
            })
            
            # Run the Docker command
            docker_cmd = [
                "docker", "run", "-i", "--rm",
                "-e", "airflow_api_url",
                "-e", "airflow_username", 
                "-e", "airflow_password",
                "hipposysai/airflow-mcp:latest"
            ]
            
            # Send the command as input to the Docker container
            process = subprocess.Popen(
                docker_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            stdout, stderr = process.communicate(input=command)
            
            if process.returncode == 0:
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError:
                    return {"output": stdout, "error": None}
            else:
                return {"output": None, "error": stderr}
                
        except Exception as e:
            return {"output": None, "error": str(e)}
    
    def get_dags(self) -> Optional[Dict[str, Any]]:
        """Get list of DAGs from Airflow."""
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


