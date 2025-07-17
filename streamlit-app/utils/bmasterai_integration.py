"""
BMasterAI integration for logging, monitoring, and notifications.

This module provides integration with the BMasterAI framework for enhanced
logging, monitoring, and notification capabilities in the Streamlit app.
"""

import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Try to import BMasterAI components, with fallbacks if not available
BMASTERAI_AVAILABLE = False
try:
    from bmasterai.logging import configure_logging, get_logger, LogLevel, EventType
    from bmasterai.monitoring import get_monitor
    from bmasterai.integrations import get_integration_manager, SlackConnector, EmailConnector
    BMASTERAI_AVAILABLE = True
    print("✅ BMasterAI framework loaded successfully")
except ImportError as e:
    print(f"⚠️ BMasterAI framework not available: {e}")
    print("Running with fallback logging and monitoring")
    
    # Create fallback classes and functions
    import logging
    
    class EventType(Enum):
        """Event types for logging."""
        TASK_START = "task_start"
        TASK_COMPLETE = "task_complete"
        TASK_ERROR = "task_error"
        AGENT_START = "agent_start"
        AGENT_STOP = "agent_stop"
        LLM_REQUEST = "llm_request"
        LLM_RESPONSE = "llm_response"
        LLM_ERROR = "llm_error"
        USER_INTERACTION = "user_interaction"
        SYSTEM_EVENT = "system_event"
    
    class LogLevel(Enum):
        """Log levels."""
        DEBUG = logging.DEBUG
        INFO = logging.INFO
        WARNING = logging.WARNING
        ERROR = logging.ERROR
    
    class FallbackLogger:
        """Fallback logger when BMasterAI is not available."""
        
        def __init__(self):
            self.logger = logging.getLogger("bmasterai_fallback")
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        def log_event(self, agent_id: str, event_type: EventType, message: str, metadata: Dict[str, Any] = None):
            """Log an event with metadata."""
            metadata_str = f" | {metadata}" if metadata else ""
            self.logger.info(f"[{agent_id}] {event_type.value}: {message}{metadata_str}")
    
    class FallbackMonitor:
        """Fallback monitor when BMasterAI is not available."""
        
        def __init__(self):
            self.metrics = {}
            self.start_time = time.time()
        
        def start_monitoring(self):
            """Start monitoring."""
            self.start_time = time.time()
            print("📊 Fallback monitoring started")
        
        def track_agent_start(self, agent_id: str):
            """Track agent start."""
            if agent_id not in self.metrics:
                self.metrics[agent_id] = {
                    "start_time": time.time(),
                    "tasks": {},
                    "errors": 0,
                    "llm_usage": {
                        "total_tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "requests": 0
                    }
                }
            print(f"🤖 Agent started: {agent_id}")
        
        def track_agent_stop(self, agent_id: str):
            """Track agent stop."""
            if agent_id in self.metrics:
                duration = time.time() - self.metrics[agent_id]["start_time"]
                print(f"🛑 Agent stopped: {agent_id} (duration: {duration:.2f}s)")
        
        def track_task_duration(self, agent_id: str, task_name: str, duration_ms: float):
            """Track task duration."""
            if agent_id not in self.metrics:
                self.metrics[agent_id] = {"tasks": {}}
            
            if task_name not in self.metrics[agent_id]["tasks"]:
                self.metrics[agent_id]["tasks"][task_name] = {
                    "count": 0,
                    "total_duration": 0,
                    "min_duration": float('inf'),
                    "max_duration": 0
                }
            
            task_metrics = self.metrics[agent_id]["tasks"][task_name]
            task_metrics["count"] += 1
            task_metrics["total_duration"] += duration_ms
            task_metrics["min_duration"] = min(task_metrics["min_duration"], duration_ms)
            task_metrics["max_duration"] = max(task_metrics["max_duration"], duration_ms)
        
        def track_error(self, agent_id: str, error_type: str):
            """Track error."""
            if agent_id not in self.metrics:
                self.metrics[agent_id] = {"errors": 0}
            else:
                self.metrics[agent_id]["errors"] = self.metrics[agent_id].get("errors", 0) + 1
        
        def track_llm_usage(self, agent_id: str, model: str, input_tokens: int, output_tokens: int):
            """Track LLM usage."""
            if agent_id not in self.metrics:
                self.metrics[agent_id] = {
                    "llm_usage": {
                        "total_tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "requests": 0
                    }
                }
            
            llm_usage = self.metrics[agent_id].get("llm_usage", {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "requests": 0
            })
            
            llm_usage["total_tokens"] += input_tokens + output_tokens
            llm_usage["input_tokens"] += input_tokens
            llm_usage["output_tokens"] += output_tokens
            llm_usage["requests"] += 1
        
        def get_metrics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
            """Get metrics for an agent or all agents."""
            if agent_id:
                return self.metrics.get(agent_id, {})
            return self.metrics
    
    class FallbackIntegrationManager:
        """Fallback integration manager when BMasterAI is not available."""
        
        def __init__(self):
            self.connectors = {}
            self.logger = logging.getLogger("bmasterai_integrations")
        
        def register_connector(self, name: str, connector: Any):
            """Register a connector."""
            self.connectors[name] = connector
            self.logger.info(f"Registered connector: {name}")
        
        def get_connector(self, name: str) -> Any:
            """Get a connector by name."""
            return self.connectors.get(name)
        
        def send_notification(self, connector_name: str, message: str, **kwargs):
            """Send a notification using a connector."""
            connector = self.get_connector(connector_name)
            if connector:
                try:
                    if hasattr(connector, "send_message"):
                        connector.send_message(message, **kwargs)
                    self.logger.info(f"Notification sent via {connector_name}")
                except Exception as e:
                    self.logger.error(f"Error sending notification via {connector_name}: {e}")
            else:
                self.logger.warning(f"Connector not found: {connector_name}")
    
    class FallbackSlackConnector:
        """Fallback Slack connector."""
        
        def __init__(self, webhook_url: str):
            self.webhook_url = webhook_url
            self.logger = logging.getLogger("slack_connector")
        
        def send_message(self, message: str, **kwargs):
            """Send a message to Slack."""
            if not self.webhook_url or self.webhook_url.startswith("your_"):
                self.logger.warning("Slack webhook URL not configured")
                return
            
            try:
                import requests
                response = requests.post(
                    self.webhook_url,
                    json={"text": message, **kwargs},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                self.logger.info("Slack message sent successfully")
            except Exception as e:
                self.logger.error(f"Error sending Slack message: {e}")
    
    class FallbackEmailConnector:
        """Fallback email connector."""
        
        def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
            self.username = username
            self.password = password
            self.logger = logging.getLogger("email_connector")
        
        def send_message(self, message: str, subject: str = "Notification", recipients: List[str] = None, **kwargs):
            """Send an email."""
            if not self.username or not self.password or self.username.startswith("your_"):
                self.logger.warning("Email credentials not configured")
                return
            
            if not recipients:
                recipients = [self.username]
            
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg["From"] = self.username
                msg["To"] = ", ".join(recipients)
                msg["Subject"] = subject
                
                msg.attach(MIMEText(message, "plain"))
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                
                self.logger.info(f"Email sent to {len(recipients)} recipients")
            except Exception as e:
                self.logger.error(f"Error sending email: {e}")
    
    def configure_logging(log_level: LogLevel = LogLevel.INFO, enable_json: bool = False, 
                         enable_file: bool = False, log_file: str = None):
        """Configure logging."""
        level = log_level.value if isinstance(log_level, LogLevel) else log_level
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=log_file if enable_file and log_file else None
        )
        
        print(f"📝 Fallback logging configured (level: {logging.getLevelName(level)})")
    
    def get_logger():
        """Get a logger instance."""
        return FallbackLogger()
    
    def get_monitor():
        """Get a monitor instance."""
        return FallbackMonitor()
    
    def get_integration_manager():
        """Get an integration manager instance."""
        return FallbackIntegrationManager()


class BMasterAIManager:
    """Manager for BMasterAI integration."""
    
    def __init__(self, agent_id: str = "streamlit-app"):
        """Initialize the BMasterAI manager."""
        self.agent_id = agent_id
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.integration_manager = get_integration_manager()
        
        # Initialize monitoring
        self.monitor.start_monitoring()
        self.monitor.track_agent_start(self.agent_id)
        
        # Log agent start
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_START,
            "BMasterAI integration initialized",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "bmasterai_available": BMASTERAI_AVAILABLE
            }
        )
    
    def configure_integrations(self, config: Dict[str, Any]):
        """Configure integrations based on config."""
        # Configure Slack integration
        if config.get("slack_webhook_url"):
            if BMASTERAI_AVAILABLE:
                slack_connector = SlackConnector(config["slack_webhook_url"])
                self.integration_manager.register_connector("slack", slack_connector)
            else:
                slack_connector = FallbackSlackConnector(config["slack_webhook_url"])
                self.integration_manager.register_connector("slack", slack_connector)
            
            self.logger.log_event(
                self.agent_id,
                EventType.SYSTEM_EVENT,
                "Slack integration configured",
                metadata={"connector": "slack"}
            )
        
        # Configure Email integration
        if config.get("email_username") and config.get("email_password"):
            if BMASTERAI_AVAILABLE:
                email_connector = EmailConnector(
                    smtp_server=config.get("smtp_server", "smtp.gmail.com"),
                    smtp_port=config.get("smtp_port", 587),
                    username=config["email_username"],
                    password=config["email_password"]
                )
                self.integration_manager.register_connector("email", email_connector)
            else:
                email_connector = FallbackEmailConnector(
                    smtp_server=config.get("smtp_server", "smtp.gmail.com"),
                    smtp_port=config.get("smtp_port", 587),
                    username=config["email_username"],
                    password=config["email_password"]
                )
                self.integration_manager.register_connector("email", email_connector)
            
            self.logger.log_event(
                self.agent_id,
                EventType.SYSTEM_EVENT,
                "Email integration configured",
                metadata={"connector": "email"}
            )
    
    def log_user_interaction(self, user_input: str, metadata: Dict[str, Any] = None):
        """Log user interaction."""
        metadata = metadata or {}
        self.logger.log_event(
            self.agent_id,
            EventType.USER_INTERACTION,
            f"User input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}",
            metadata={
                "input_length": len(user_input),
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
        )
    
    def log_llm_request(self, model: str, prompt_length: int, metadata: Dict[str, Any] = None):
        """Log LLM request."""
        metadata = metadata or {}
        self.logger.log_event(
            self.agent_id,
            EventType.LLM_REQUEST,
            f"LLM request to {model}",
            metadata={
                "model": model,
                "prompt_length": prompt_length,
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
        )
    
    def log_llm_response(self, model: str, response_length: int, 
                        input_tokens: int = None, output_tokens: int = None,
                        metadata: Dict[str, Any] = None):
        """Log LLM response."""
        metadata = metadata or {}
        
        # Track LLM usage if token counts are provided
        if input_tokens is not None and output_tokens is not None:
            self.monitor.track_llm_usage(
                self.agent_id,
                model,
                input_tokens,
                output_tokens
            )
        
        self.logger.log_event(
            self.agent_id,
            EventType.LLM_RESPONSE,
            f"LLM response from {model}",
            metadata={
                "model": model,
                "response_length": response_length,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
        )
    
    def log_task_start(self, task_name: str, metadata: Dict[str, Any] = None):
        """Log task start."""
        metadata = metadata or {}
        self.logger.log_event(
            self.agent_id,
            EventType.TASK_START,
            f"Starting task: {task_name}",
            metadata={
                "task_name": task_name,
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
        )
        
        # Store task start time in metadata for duration tracking
        return time.time()
    
    def log_task_complete(self, task_name: str, start_time: float, metadata: Dict[str, Any] = None):
        """Log task completion."""
        metadata = metadata or {}
        duration_ms = (time.time() - start_time) * 1000
        
        self.monitor.track_task_duration(
            self.agent_id,
            task_name,
            duration_ms
        )
        
        self.logger.log_event(
            self.agent_id,
            EventType.TASK_COMPLETE,
            f"Task completed: {task_name}",
            metadata={
                "task_name": task_name,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
        )
    
    def log_error(self, error_type: str, error_message: str, metadata: Dict[str, Any] = None):
        """Log error."""
        metadata = metadata or {}
        
        self.monitor.track_error(self.agent_id, error_type)
        
        self.logger.log_event(
            self.agent_id,
            EventType.TASK_ERROR,
            f"Error: {error_message}",
            metadata={
                "error_type": error_type,
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
        )
    
    def send_notification(self, message: str, connector: str = "slack", **kwargs):
        """Send notification using configured connector."""
        try:
            self.integration_manager.send_notification(connector, message, **kwargs)
            
            self.logger.log_event(
                self.agent_id,
                EventType.SYSTEM_EVENT,
                f"Notification sent via {connector}",
                metadata={
                    "connector": connector,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            self.logger.log_event(
                self.agent_id,
                EventType.TASK_ERROR,
                f"Error sending notification: {e}",
                metadata={
                    "connector": connector,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics."""
        return self.monitor.get_metrics(self.agent_id)
    
    def shutdown(self):
        """Shutdown the BMasterAI manager."""
        self.logger.log_event(
            self.agent_id,
            EventType.AGENT_STOP,
            "BMasterAI integration shutting down",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.monitor.start_time
            }
        )
        
        if hasattr(self.monitor, "track_agent_stop"):
            self.monitor.track_agent_stop(self.agent_id)


# Initialize BMasterAI manager
bmasterai_manager = BMasterAIManager()