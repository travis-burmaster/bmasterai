
"""BMasterAI-style logging implementation for MCP GitHub Analyzer"""
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path
import os

class LogLevel(Enum):
    """Log levels following BMasterAI patterns"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level_str: str):
        """Create LogLevel from string, with fallback to INFO"""
        try:
            return getattr(cls, level_str.upper())
        except AttributeError:
            return cls.INFO

class EventType(Enum):
    """Event types for structured logging"""
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    LLM_CALL = "llm_call"
    AGENT_COMMUNICATION = "agent_communication"
    PERFORMANCE_METRIC = "performance_metric"
    USER_ACTION = "user_action"
    GITHUB_OPERATION = "github_operation"
    MCP_OPERATION = "mcp_operation"

class StructuredLogger:
    """BMasterAI-style structured logger"""
    
    def __init__(self, name: str = "mcp_github_analyzer"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.session_id = str(uuid.uuid4())
        
    def configure_logging(self, 
                         log_level: LogLevel = LogLevel.INFO,
                         enable_console: bool = True,
                         enable_file: bool = True,
                         enable_json: bool = True,
                         log_file: str = "logs/mcp_github_analyzer.log",
                         json_log_file: str = "logs/mcp_github_analyzer.jsonl"):
        """Configure logging following BMasterAI patterns"""
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(getattr(logging, log_level.value))
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if enable_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # JSON handler
        if enable_json:
            json_handler = logging.FileHandler(json_log_file)
            json_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(json_handler)
        
        return self
    
    def log_event(self,
                 agent_id: str,
                 event_type: EventType,
                 message: str,
                 level: LogLevel = LogLevel.INFO,
                 metadata: Optional[Dict[str, Any]] = None,
                 duration_ms: Optional[float] = None):
        """Log an event with structured metadata"""
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "agent_id": agent_id,
            "event_type": event_type.value,
            "message": message,
            "level": level.value,
            "metadata": metadata or {},
        }
        
        if duration_ms is not None:
            log_entry["duration_ms"] = duration_ms
        
        # Log to structured logger
        log_level = getattr(logging, level.value)
        self.logger.log(log_level, json.dumps(log_entry))
        
        return log_entry
    
    def log_agent_start(self, agent_id: str, agent_name: str, metadata: Dict[str, Any] = None):
        """Log agent start event"""
        return self.log_event(
            agent_id=agent_id,
            event_type=EventType.AGENT_START,
            message=f"Agent {agent_name} started",
            metadata={"agent_name": agent_name, **(metadata or {})}
        )
    
    def log_agent_stop(self, agent_id: str, agent_name: str, metadata: Dict[str, Any] = None):
        """Log agent stop event"""
        return self.log_event(
            agent_id=agent_id,
            event_type=EventType.AGENT_STOP,
            message=f"Agent {agent_name} stopped",
            metadata={"agent_name": agent_name, **(metadata or {})}
        )
    
    def log_task_start(self, agent_id: str, task_name: str, task_id: str, metadata: Dict[str, Any] = None):
        """Log task start event"""
        return self.log_event(
            agent_id=agent_id,
            event_type=EventType.TASK_START,
            message=f"Started task: {task_name}",
            metadata={"task_name": task_name, "task_id": task_id, **(metadata or {})}
        )
    
    def log_task_complete(self, agent_id: str, task_name: str, task_id: str, 
                         duration_ms: float, metadata: Dict[str, Any] = None):
        """Log task completion event"""
        return self.log_event(
            agent_id=agent_id,
            event_type=EventType.TASK_COMPLETE,
            message=f"Completed task: {task_name}",
            duration_ms=duration_ms,
            metadata={"task_name": task_name, "task_id": task_id, **(metadata or {})}
        )
    
    def log_task_error(self, agent_id: str, task_name: str, task_id: str, 
                      error: str, duration_ms: float, metadata: Dict[str, Any] = None):
        """Log task error event"""
        return self.log_event(
            agent_id=agent_id,
            event_type=EventType.TASK_ERROR,
            message=f"Task failed: {task_name} - {error}",
            level=LogLevel.ERROR,
            duration_ms=duration_ms,
            metadata={"task_name": task_name, "task_id": task_id, "error": error, **(metadata or {})}
        )
    
    def log_llm_call(self, agent_id: str, model: str, prompt_length: int, 
                    max_tokens: int, metadata: Dict[str, Any] = None):
        """Log LLM call event"""
        return self.log_event(
            agent_id=agent_id,
            event_type=EventType.LLM_CALL,
            message=f"LLM call: {model}",
            metadata={
                "model": model,
                "prompt_length": prompt_length,
                "max_tokens": max_tokens,
                **(metadata or {})
            }
        )
    
    def log_user_action(self, user_session: str, action: str, metadata: Dict[str, Any] = None):
        """Log user action event"""
        return self.log_event(
            agent_id="streamlit_app",
            event_type=EventType.USER_ACTION,
            message=f"User action: {action}",
            metadata={"user_session": user_session, "action": action, **(metadata or {})}
        )

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs"""
    
    def format(self, record):
        """Format log record as JSON"""
        return record.getMessage()

# Global logger instance
_logger_instance = None

def configure_logging(log_level: LogLevel = LogLevel.INFO,
                     enable_console: bool = True,
                     enable_file: bool = True,
                     enable_json: bool = True,
                     log_file: str = "logs/mcp_github_analyzer.log",
                     json_log_file: str = "logs/mcp_github_analyzer.jsonl") -> StructuredLogger:
    """Configure global logging instance"""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = StructuredLogger()
    
    return _logger_instance.configure_logging(
        log_level=log_level,
        enable_console=enable_console,
        enable_file=enable_file,
        enable_json=enable_json,
        log_file=log_file,
        json_log_file=json_log_file
    )

def get_logger() -> StructuredLogger:
    """Get the global logger instance"""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = StructuredLogger()
        _logger_instance.configure_logging()
    
    return _logger_instance
