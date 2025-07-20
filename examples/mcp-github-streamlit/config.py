
"""Configuration management for MCP GitHub Analyzer"""
import os
import yaml
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class LoggingConfig:
    level: str = "INFO"
    enable_console: bool = True
    enable_file: bool = True
    enable_json: bool = True
    log_file: str = "logs/mcp_github_analyzer.log"
    json_log_file: str = "logs/mcp_github_analyzer.jsonl"

@dataclass
class MonitoringConfig:
    collection_interval: int = 30
    enable_system_metrics: bool = True
    enable_custom_metrics: bool = True
    dashboard_refresh_interval: int = 5

@dataclass
class GitHubConfig:
    enabled: bool = True
    rate_limit_per_hour: int = 5000
    timeout_seconds: int = 30
    token: Optional[str] = None

@dataclass
class MCPConfig:
    enabled: bool = True
    server_host: str = "localhost"
    server_port: int = 8080
    timeout_seconds: int = 30

@dataclass
class AgentConfig:
    default_timeout: int = 300
    max_retries: int = 3
    enable_monitoring: bool = True
    enable_logging: bool = True

class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = None
        self._env_loaded = False
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file and environment variables"""
        # Load from YAML file
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {}
        
        # Load environment variables
        if not self._env_loaded:
            from dotenv import load_dotenv
            load_dotenv()
            self._env_loaded = True
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        env_mappings = {
            'GITHUB_TOKEN': ['integrations', 'github', 'token'],
            'MCP_SERVER_HOST': ['integrations', 'mcp', 'server_host'],
            'MCP_SERVER_PORT': ['integrations', 'mcp', 'server_port'],
            'LOG_LEVEL': ['logging', 'level'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_value(self._config, config_path, env_value)
    
    def _set_nested_value(self, config: dict, path: list, value: str):
        """Set a nested configuration value"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert types for specific known values
        if path[-1] in ['server_port', 'timeout_seconds', 'collection_interval']:
            value = int(value)
        elif path[-1] in ['enabled', 'enable_console', 'enable_file', 'enable_json']:
            value = value.lower() in ('true', '1', 'yes', 'on')
        
        current[path[-1]] = value
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        logging_config = self._config.get('logging', {})
        return LoggingConfig(**logging_config)
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        monitoring_config = self._config.get('monitoring', {})
        return MonitoringConfig(**monitoring_config)
    
    def get_github_config(self) -> GitHubConfig:
        """Get GitHub configuration"""
        github_config = self._config.get('integrations', {}).get('github', {})
        github_config['token'] = os.getenv('GITHUB_TOKEN')
        return GitHubConfig(**github_config)
    
    def get_mcp_config(self) -> MCPConfig:
        """Get MCP configuration"""
        mcp_config = self._config.get('integrations', {}).get('mcp', {})
        return MCPConfig(**mcp_config)
    
    def get_agent_config(self) -> AgentConfig:
        """Get agent configuration"""
        agent_config = self._config.get('agents', {})
        return AgentConfig(**agent_config)
    
    def get_config_value(self, path: str, default=None):
        """Get a configuration value by dot-separated path"""
        keys = path.split('.')
        current = self._config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def update_config(self, path: str, value):
        """Update a configuration value"""
        keys = path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def save_config(self):
        """Save configuration back to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

# Global configuration instance
@st.cache_resource
def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    return ConfigManager()
