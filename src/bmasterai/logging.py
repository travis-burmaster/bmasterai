
import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from pathlib import Path

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventType(Enum):
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    LLM_CALL = "llm_call"
    TOOL_USE = "tool_use"
    AGENT_COMMUNICATION = "agent_communication"
    PERFORMANCE_METRIC = "performance_metric"

@dataclass
class LogEntry:
    timestamp: str
    event_id: str
    agent_id: str
    event_type: EventType
    level: LogLevel
    message: str
    metadata: Dict[str, Any]
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms
        }

class BMasterLogger:
    def __init__(self, 
                 log_file: str = "bmasterai.log",
                 json_log_file: str = "bmasterai.jsonl",
                 log_level: LogLevel = LogLevel.INFO,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True):

        self.log_file = log_file
        self.json_log_file = json_log_file
        self.log_level = log_level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json

        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)

        # Setup standard logger
        self.logger = logging.getLogger("bmasterai")
        self.logger.setLevel(getattr(logging, log_level.value))

        # Clear existing handlers
        self.logger.handlers.clear()

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
            file_handler = logging.FileHandler(f"logs/{log_file}")
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Thread-safe event storage
        self._events: List[LogEntry] = []
        self._lock = threading.Lock()

    def log_event(self, 
                  agent_id: str,
                  event_type: EventType,
                  message: str,
                  level: LogLevel = LogLevel.INFO,
                  metadata: Optional[Dict[str, Any]] = None,
                  duration_ms: Optional[float] = None):

        if metadata is None:
            metadata = {}

        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            event_id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=event_type,
            level=level,
            message=message,
            metadata=metadata,
            duration_ms=duration_ms
        )

        # Thread-safe event storage
        with self._lock:
            self._events.append(entry)

        # Log to standard logger
        log_method = getattr(self.logger, level.value.lower())
        log_method(f"[{agent_id}] {event_type.value}: {message}")

        # Log to JSON file
        if self.enable_json:
            self._write_json_log(entry)

    def _write_json_log(self, entry: LogEntry):
        try:
            with open(f"logs/{self.json_log_file}", "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")

    def get_events(self, 
                   agent_id: Optional[str] = None,
                   event_type: Optional[EventType] = None,
                   level: Optional[LogLevel] = None,
                   limit: Optional[int] = None) -> List[LogEntry]:

        with self._lock:
            events = self._events.copy()

        # Filter events
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if level:
            events = [e for e in events if e.level == level]

        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            events = events[:limit]

        return events

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        events = self.get_events(agent_id=agent_id)

        stats = {
            "total_events": len(events),
            "event_types": {},
            "error_count": 0,
            "avg_task_duration": 0,
            "last_activity": None
        }

        task_durations = []

        for event in events:
            # Count event types
            event_type = event.event_type.value
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1

            # Count errors
            if event.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                stats["error_count"] += 1

            # Collect task durations
            if event.duration_ms:
                task_durations.append(event.duration_ms)

            # Track last activity
            if not stats["last_activity"] or event.timestamp > stats["last_activity"]:
                stats["last_activity"] = event.timestamp

        # Calculate average task duration
        if task_durations:
            stats["avg_task_duration"] = sum(task_durations) / len(task_durations)

        return stats

# Global logger instance
_logger_instance = None

def get_logger() -> BMasterLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = BMasterLogger()
    return _logger_instance

def configure_logging(log_file: str = "bmasterai.log",
                     json_log_file: str = "bmasterai.jsonl",
                     log_level: LogLevel = LogLevel.INFO,
                     enable_console: bool = True,
                     enable_file: bool = True,
                     enable_json: bool = True):
    global _logger_instance
    _logger_instance = BMasterLogger(
        log_file=log_file,
        json_log_file=json_log_file,
        log_level=log_level,
        enable_console=enable_console,
        enable_file=enable_file,
        enable_json=enable_json
    )
    return _logger_instance
