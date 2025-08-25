
import logging
import json
import time
import uuid
from datetime import datetime, timezone
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
    LLM_REASONING = "llm_reasoning"
    LLM_THINKING_STEP = "llm_thinking_step"
    TOOL_USE = "tool_use"
    AGENT_COMMUNICATION = "agent_communication"
    PERFORMANCE_METRIC = "performance_metric"
    DECISION_POINT = "decision_point"
    REASONING_CHAIN = "reasoning_chain"

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
    reasoning_step: Optional[int] = None
    parent_event_id: Optional[str] = None
    thinking_chain: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type.value,
            "level": self.level.value,
            "message": self.message,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
            "reasoning_step": self.reasoning_step,
            "parent_event_id": self.parent_event_id,
            "thinking_chain": self.thinking_chain
        }

class BMasterLogger:
    def __init__(self, 
                 log_file: str = "bmasterai.log",
                 json_log_file: str = "bmasterai.jsonl",
                 reasoning_log_file: str = "bmasterai_reasoning.jsonl",
                 log_level: LogLevel = LogLevel.INFO,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True,
                 enable_reasoning_logs: bool = True):

        self.log_file = log_file
        self.json_log_file = json_log_file
        self.reasoning_log_file = reasoning_log_file
        self.log_level = log_level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.enable_reasoning_logs = enable_reasoning_logs

        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        if enable_reasoning_logs:
            Path("logs/reasoning").mkdir(exist_ok=True)

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
                  duration_ms: Optional[float] = None,
                  reasoning_step: Optional[int] = None,
                  parent_event_id: Optional[str] = None,
                  thinking_chain: Optional[List[str]] = None):

        if metadata is None:
            metadata = {}

        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=event_type,
            level=level,
            message=message,
            metadata=metadata,
            duration_ms=duration_ms,
            reasoning_step=reasoning_step,
            parent_event_id=parent_event_id,
            thinking_chain=thinking_chain
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
        
        # Log reasoning events to separate file
        if (self.enable_reasoning_logs and 
            event_type in [EventType.LLM_REASONING, EventType.LLM_THINKING_STEP, 
                          EventType.DECISION_POINT, EventType.REASONING_CHAIN]):
            self._write_reasoning_log(entry)

    def _write_json_log(self, entry: LogEntry):
        try:
            with open(f"logs/{self.json_log_file}", "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")
    
    def _write_reasoning_log(self, entry: LogEntry):
        """Write reasoning-specific logs to dedicated file"""
        try:
            reasoning_data = {
                "timestamp": entry.timestamp,
                "agent_id": entry.agent_id,
                "event_type": entry.event_type.value,
                "reasoning_step": entry.reasoning_step,
                "parent_event_id": entry.parent_event_id,
                "thinking_chain": entry.thinking_chain,
                "message": entry.message,
                "metadata": entry.metadata
            }
            with open(f"logs/reasoning/{self.reasoning_log_file}", "a") as f:
                f.write(json.dumps(reasoning_data, indent=2) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write reasoning log: {e}")

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
    
    def log_llm_reasoning_start(self, agent_id: str, task_description: str, 
                               model: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start logging an LLM reasoning session"""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "task_description": task_description,
            "model": model,
            "reasoning_session_start": True
        })
        
        self.log_event(
            agent_id=agent_id,
            event_type=EventType.LLM_REASONING,
            message=f"Starting LLM reasoning for task: {task_description}",
            level=LogLevel.INFO,
            metadata=metadata,
            reasoning_step=0
        )
        
        # Return session ID for tracking
        return f"reasoning_session_{agent_id}_{int(time.time())}"
    
    def log_thinking_step(self, agent_id: str, step_number: int, thinking_content: str,
                         session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an individual thinking step in the reasoning process"""
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "session_id": session_id,
            "thinking_content": thinking_content,
            "step_type": "thinking_step"
        })
        
        self.log_event(
            agent_id=agent_id,
            event_type=EventType.LLM_THINKING_STEP,
            message=f"Thinking step {step_number}: {thinking_content[:100]}{'...' if len(thinking_content) > 100 else ''}",
            level=LogLevel.DEBUG,
            metadata=metadata,
            reasoning_step=step_number
        )
    
    def log_decision_point(self, agent_id: str, decision_description: str, 
                          options: List[str], chosen_option: str, reasoning: str,
                          session_id: str, step_number: int, 
                          metadata: Optional[Dict[str, Any]] = None):
        """Log a decision point in the reasoning process"""
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "session_id": session_id,
            "decision_description": decision_description,
            "available_options": options,
            "chosen_option": chosen_option,
            "decision_reasoning": reasoning,
            "step_type": "decision_point"
        })
        
        self.log_event(
            agent_id=agent_id,
            event_type=EventType.DECISION_POINT,
            message=f"Decision: {decision_description} -> {chosen_option}",
            level=LogLevel.INFO,
            metadata=metadata,
            reasoning_step=step_number
        )
    
    def log_reasoning_chain(self, agent_id: str, thinking_chain: List[str],
                           final_conclusion: str, session_id: str,
                           metadata: Optional[Dict[str, Any]] = None):
        """Log the complete reasoning chain"""
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "session_id": session_id,
            "final_conclusion": final_conclusion,
            "chain_length": len(thinking_chain),
            "step_type": "reasoning_chain"
        })
        
        self.log_event(
            agent_id=agent_id,
            event_type=EventType.REASONING_CHAIN,
            message=f"Reasoning chain complete: {final_conclusion}",
            level=LogLevel.INFO,
            metadata=metadata,
            thinking_chain=thinking_chain
        )
    
    def get_reasoning_session(self, session_id: str) -> List[LogEntry]:
        """Retrieve all logs for a specific reasoning session"""
        with self._lock:
            events = [e for e in self._events 
                     if (e.metadata.get("session_id") == session_id or
                         e.event_id == session_id)]
        
        # Sort by reasoning step
        events.sort(key=lambda x: (x.reasoning_step or 0))
        return events
    
    def export_reasoning_logs(self, agent_id: Optional[str] = None, 
                            session_id: Optional[str] = None,
                            output_format: str = "json") -> str:
        """Export reasoning logs in various formats"""
        with self._lock:
            events = self._events.copy()
        
        # Filter reasoning events
        reasoning_events = [e for e in events if e.event_type in [
            EventType.LLM_REASONING, EventType.LLM_THINKING_STEP,
            EventType.DECISION_POINT, EventType.REASONING_CHAIN
        ]]
        
        if agent_id:
            reasoning_events = [e for e in reasoning_events if e.agent_id == agent_id]
        
        if session_id:
            reasoning_events = [e for e in reasoning_events 
                              if e.metadata.get("session_id") == session_id]
        
        # Sort by timestamp
        reasoning_events.sort(key=lambda x: x.timestamp)
        
        if output_format == "json":
            return json.dumps([e.to_dict() for e in reasoning_events], indent=2)
        elif output_format == "markdown":
            return self._format_reasoning_as_markdown(reasoning_events)
        else:
            return str([e.to_dict() for e in reasoning_events])
    
    def _format_reasoning_as_markdown(self, events: List[LogEntry]) -> str:
        """Format reasoning logs as readable markdown"""
        markdown = "# LLM Reasoning Log\n\n"
        
        current_session = None
        for event in events:
            session_id = event.metadata.get("session_id", "unknown")
            
            if session_id != current_session:
                current_session = session_id
                markdown += f"## Reasoning Session: {session_id}\n"
                markdown += f"**Agent:** {event.agent_id}  \n"
                markdown += f"**Timestamp:** {event.timestamp}  \n\n"
            
            if event.event_type == EventType.LLM_REASONING:
                markdown += f"### Task: {event.metadata.get('task_description', 'N/A')}\n"
                markdown += f"**Model:** {event.metadata.get('model', 'N/A')}  \n\n"
            
            elif event.event_type == EventType.LLM_THINKING_STEP:
                step_num = event.reasoning_step or 0
                thinking = event.metadata.get('thinking_content', event.message)
                markdown += f"**Step {step_num}:** {thinking}\n\n"
            
            elif event.event_type == EventType.DECISION_POINT:
                markdown += f"**Decision:** {event.metadata.get('decision_description', 'N/A')}\n"
                options = event.metadata.get('available_options', [])
                chosen = event.metadata.get('chosen_option', 'N/A')
                reasoning = event.metadata.get('decision_reasoning', 'N/A')
                
                markdown += f"- **Options:** {', '.join(options)}\n"
                markdown += f"- **Chosen:** {chosen}\n"
                markdown += f"- **Reasoning:** {reasoning}\n\n"
            
            elif event.event_type == EventType.REASONING_CHAIN:
                conclusion = event.metadata.get('final_conclusion', 'N/A')
                markdown += f"**Final Conclusion:** {conclusion}\n\n"
                
                if event.thinking_chain:
                    markdown += "**Complete Thinking Chain:**\n"
                    for i, thought in enumerate(event.thinking_chain, 1):
                        markdown += f"{i}. {thought}\n"
                    markdown += "\n"
            
            markdown += "---\n\n"
        
        return markdown

# Global logger instance
_logger_instance = None

def get_logger() -> BMasterLogger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = BMasterLogger()
    return _logger_instance

def configure_logging(log_file: str = "bmasterai.log",
                     json_log_file: str = "bmasterai.jsonl",
                     reasoning_log_file: str = "bmasterai_reasoning.jsonl",
                     log_level: LogLevel = LogLevel.INFO,
                     enable_console: bool = True,
                     enable_file: bool = True,
                     enable_json: bool = True,
                     enable_reasoning_logs: bool = True):
    global _logger_instance
    _logger_instance = BMasterLogger(
        log_file=log_file,
        json_log_file=json_log_file,
        reasoning_log_file=reasoning_log_file,
        log_level=log_level,
        enable_console=enable_console,
        enable_file=enable_file,
        enable_json=enable_json,
        enable_reasoning_logs=enable_reasoning_logs
    )
    return _logger_instance
