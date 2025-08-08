#!/usr/bin/env python3
"""
BMasterAI MCP Server

This module provides a Model Context Protocol (MCP) server that exposes
BMasterAI system status information, including agent metrics, system health,
integrations, and alerts.

Usage:
    As a module: python -m bmasterai.mcp_server
    Direct: python mcp_server.py
    Import: from bmasterai.mcp_server import create_mcp_server
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP not found. Please install with: pip install fastmcp"
    )

from .monitoring import get_monitor
from .integrations import get_integration_manager


def create_mcp_server() -> FastMCP:
    """
    Create and configure the BMasterAI MCP server.
    
    Returns:
        FastMCP: Configured MCP server instance
    """
    # Create the MCP server
    mcp = FastMCP(
        name="BMasterAI Status",
        instructions="""This server provides access to BMasterAI system status and monitoring information.
        
Available tools:
- get_system_status: Returns overall system health including agents, CPU, memory
- get_integration_status: Shows status of all configured integrations
- get_recent_alerts: Returns recent system alerts
- get_agent_dashboard: Get detailed metrics for a specific agent
"""
    )

    @mcp.tool()
    def get_system_status() -> Dict[str, Any]:
        """
        Get the current BMasterAI system status including active agents,
        system metrics (CPU, memory, disk), and overall health.
        
        Returns a dictionary with:
        - timestamp: Current time in ISO format
        - active_agents: Number of currently running agents
        - total_agents: Total number of registered agents
        - system_metrics: CPU, memory, and disk usage statistics
        - status: Overall system status (healthy/warning/critical)
        """
        try:
            monitor = get_monitor()
            health = monitor.get_system_health()
            
            # Calculate overall status based on metrics
            cpu_avg = health['system_metrics']['cpu'].get('avg', 0)
            memory_avg = health['system_metrics']['memory'].get('avg', 0)
            
            if cpu_avg > 90 or memory_avg > 90:
                status = "critical"
            elif cpu_avg > 75 or memory_avg > 75:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "timestamp": health['timestamp'],
                "status": status,
                "agents": {
                    "active": health['active_agents'],
                    "total": health['total_agents']
                },
                "system_metrics": {
                    "cpu": {
                        "current": health['system_metrics']['cpu'].get('latest', 0),
                        "average": health['system_metrics']['cpu'].get('avg', 0),
                        "min": health['system_metrics']['cpu'].get('min', 0),
                        "max": health['system_metrics']['cpu'].get('max', 0)
                    },
                    "memory": {
                        "current": health['system_metrics']['memory'].get('latest', 0),
                        "average": health['system_metrics']['memory'].get('avg', 0),
                        "min": health['system_metrics']['memory'].get('min', 0),
                        "max": health['system_metrics']['memory'].get('max', 0)
                    },
                    "disk": {
                        "current": health['system_metrics']['disk'].get('latest', 0),
                        "average": health['system_metrics']['disk'].get('avg', 0)
                    }
                }
            }
        except Exception as e:
            return {
                "error": f"Failed to get system status: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    @mcp.tool()
    def get_integration_status() -> Dict[str, Any]:
        """
        Get the status of all configured BMasterAI integrations.
        
        Returns a dictionary with:
        - total_connectors: Number of configured integrations
        - active_integrations: List of active integration names
        - integration_details: Status details for each integration
        """
        try:
            integration_manager = get_integration_manager()
            status = integration_manager.get_status()
            
            # Get detailed status for each integration
            integration_details = {}
            for name, connector_status in status.get('connector_status', {}).items():
                integration_details[name] = {
                    "active": name in status['active_integrations'],
                    "success": connector_status.get('success', False),
                    "message": connector_status.get('message', connector_status.get('error', 'Unknown status'))
                }
            
            return {
                "total_connectors": status['total_connectors'],
                "active_integrations": status['active_integrations'],
                "integration_details": integration_details
            }
        except Exception as e:
            return {
                "error": f"Failed to get integration status: {str(e)}",
                "total_connectors": 0,
                "active_integrations": []
            }

    @mcp.tool()
    def get_recent_alerts(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent system alerts from BMasterAI monitoring.
        
        Args:
            limit: Maximum number of alerts to return (default: 10)
        
        Returns:
            List of alert dictionaries, each containing:
            - metric_name: The metric that triggered the alert
            - message: Alert message
            - timestamp: When the alert was triggered
            - current_value: The value that triggered the alert
            - threshold: The threshold that was exceeded
        """
        try:
            monitor = get_monitor()
            health = monitor.get_system_health()
            alerts = health.get('recent_alerts', [])[:limit]
            
            # Format alerts for better readability
            formatted_alerts = []
            for alert in alerts:
                formatted_alerts.append({
                    "metric_name": alert.get('metric_name', 'Unknown'),
                    "message": alert.get('message', 'No message'),
                    "timestamp": alert.get('timestamp', 'Unknown'),
                    "current_value": alert.get('current_value', 'N/A'),
                    "threshold": alert.get('threshold', 'N/A'),
                    "condition": alert.get('condition', 'Unknown')
                })
            
            return formatted_alerts
        except Exception as e:
            return [{
                "error": f"Failed to get alerts: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]

    @mcp.tool()
    def get_agent_dashboard(agent_id: str) -> Dict[str, Any]:
        """
        Get detailed performance dashboard for a specific agent.
        
        Args:
            agent_id: The ID of the agent to get metrics for
        
        Returns:
            Dictionary containing:
            - agent_id: The agent identifier
            - status: Current agent status (running/stopped/unknown)
            - performance: Task performance metrics
            - errors: Error counts and types
            - system_usage: CPU and memory usage when the agent is active
        """
        try:
            monitor = get_monitor()
            dashboard = monitor.get_agent_dashboard(agent_id)
            
            return {
                "agent_id": dashboard['agent_id'],
                "status": dashboard['status'],
                "performance": dashboard.get('performance', {}),
                "total_errors": dashboard.get('metrics', {}).get('total_errors', 0),
                "system_usage": {
                    "cpu": dashboard.get('system', {}).get('cpu_usage', {}),
                    "memory": dashboard.get('system', {}).get('memory_usage', {})
                }
            }
        except Exception as e:
            return {
                "agent_id": agent_id,
                "error": f"Failed to get agent dashboard: {str(e)}",
                "status": "error"
            }

    return mcp


# Create a module-level server instance
mcp_server = create_mcp_server()


if __name__ == "__main__":
    # Run the server when executed directly
    mcp_server.run(transport="stdio")