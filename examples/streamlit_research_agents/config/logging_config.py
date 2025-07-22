
"""
BMasterAI Logging and Monitoring Configuration
Integrates BMasterAI logging capabilities with Google Gemini agents
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

try:
    from bmasterai.logging import BMLogger, LogLevel, MetricType
    from bmasterai.monitoring import PerformanceMonitor, AgentMonitor
    from bmasterai.utils import get_config_value
    BMASTERAI_AVAILABLE = True
except ImportError:
    BMASTERAI_AVAILABLE = False
    print("Warning: BMasterAI library not available. Falling back to standard logging.")

class BMasterAILoggingConfig:
    """Configuration class for BMasterAI logging integration"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.bmasterai_available = BMASTERAI_AVAILABLE
        self.logger = None
        self.performance_monitor = None
        self.agent_monitor = None
        
        if self.bmasterai_available:
            self._initialize_bmasterai_logging()
        else:
            self._initialize_fallback_logging()
    
    def _initialize_bmasterai_logging(self):
        """Initialize BMasterAI logging components"""
        try:
            # Initialize BMasterAI logger
            self.logger = BMLogger(
                service_name="research_agents",
                environment=os.getenv("ENVIRONMENT", "development"),
                log_level=LogLevel.INFO,
                enable_structured_logging=True,
                enable_metrics=True,
                enable_tracing=True
            )
            
            # Initialize performance monitoring
            self.performance_monitor = PerformanceMonitor(
                service_name="research_agents",
                enable_memory_tracking=True,
                enable_cpu_tracking=True,
                enable_api_timing=True
            )
            
            # Initialize agent monitoring
            self.agent_monitor = AgentMonitor(
                service_name="research_agents",
                track_agent_performance=True,
                track_task_completion=True,
                track_error_rates=True
            )
            
            # Configure logging settings
            self._configure_logging_settings()
            
            print("BMasterAI logging initialized successfully")
            
        except Exception as e:
            print(f"Error initializing BMasterAI logging: {e}")
            self._initialize_fallback_logging()
    
    def _initialize_fallback_logging(self):
        """Initialize fallback logging when BMasterAI is not available"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('research_agents.log')
            ]
        )
        self.logger = logging.getLogger("research_agents")
        print("Fallback logging initialized")
    
    def _configure_logging_settings(self):
        """Configure BMasterAI logging settings"""
        if not self.bmasterai_available:
            return
        
        # Configure log levels for different components
        log_config = {
            "agents": LogLevel.INFO,
            "api_calls": LogLevel.DEBUG,
            "performance": LogLevel.INFO,
            "errors": LogLevel.ERROR,
            "user_interactions": LogLevel.INFO
        }
        
        for component, level in log_config.items():
            self.logger.set_component_log_level(component, level)
        
        # Configure metrics collection
        self.logger.enable_metric_collection([
            MetricType.COUNTER,
            MetricType.HISTOGRAM,
            MetricType.GAUGE,
            MetricType.TIMER
        ])
    
    def get_logger(self, component_name: str = "default"):
        """Get logger instance for a specific component"""
        if self.bmasterai_available and self.logger:
            return self.logger.get_component_logger(component_name)
        else:
            return logging.getLogger(f"research_agents.{component_name}")
    
    def get_performance_monitor(self):
        """Get performance monitor instance"""
        return self.performance_monitor
    
    def get_agent_monitor(self):
        """Get agent monitor instance"""
        return self.agent_monitor
    
    def log_agent_start(self, agent_name: str, task_id: str, task_description: str):
        """Log agent task start"""
        if self.bmasterai_available and self.agent_monitor:
            self.agent_monitor.log_task_start(
                agent_name=agent_name,
                task_id=task_id,
                task_description=task_description,
                timestamp=datetime.now()
            )
        else:
            logger = self.get_logger("agent_lifecycle")
            logger.info(f"Agent {agent_name} started task {task_id}: {task_description}")
    
    def log_agent_completion(self, agent_name: str, task_id: str, success: bool, 
                           duration: float, result_size: int = 0):
        """Log agent task completion"""
        if self.bmasterai_available and self.agent_monitor:
            self.agent_monitor.log_task_completion(
                agent_name=agent_name,
                task_id=task_id,
                success=success,
                duration=duration,
                result_size=result_size,
                timestamp=datetime.now()
            )
        else:
            logger = self.get_logger("agent_lifecycle")
            status = "completed" if success else "failed"
            logger.info(f"Agent {agent_name} {status} task {task_id} in {duration:.2f}s")
    
    def log_api_call(self, api_name: str, endpoint: str, duration: float, 
                     status_code: int, request_size: int = 0, response_size: int = 0):
        """Log API call metrics"""
        if self.bmasterai_available and self.performance_monitor:
            self.performance_monitor.log_api_call(
                api_name=api_name,
                endpoint=endpoint,
                duration=duration,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size
            )
        else:
            logger = self.get_logger("api_calls")
            logger.info(f"API call to {api_name}/{endpoint}: {status_code} in {duration:.2f}s")
    
    def log_error(self, component: str, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        if self.bmasterai_available and self.logger:
            self.logger.log_error(
                component=component,
                error=error,
                context=context or {},
                timestamp=datetime.now()
            )
        else:
            logger = self.get_logger("errors")
            logger.error(f"Error in {component}: {str(error)}", exc_info=True)
            if context:
                logger.error(f"Error context: {json.dumps(context, default=str)}")
    
    def log_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Log custom metric"""
        if self.bmasterai_available and self.logger:
            self.logger.log_metric(
                metric_name=metric_name,
                value=value,
                tags=tags or {},
                timestamp=datetime.now()
            )
        else:
            logger = self.get_logger("metrics")
            logger.info(f"Metric {metric_name}: {value} {tags or ''}")
    
    def create_performance_context(self, operation_name: str):
        """Create performance monitoring context"""
        if self.bmasterai_available and self.performance_monitor:
            return self.performance_monitor.create_context(operation_name)
        else:
            # Return a simple context manager for fallback
            return SimplePerformanceContext(operation_name, self.get_logger("performance"))

class SimplePerformanceContext:
    """Simple performance context for fallback logging"""
    
    def __init__(self, operation_name: str, logger):
        self.operation_name = operation_name
        self.logger = logger
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                self.logger.error(f"Operation {self.operation_name} failed after {duration:.2f}s")
            else:
                self.logger.info(f"Operation {self.operation_name} completed in {duration:.2f}s")

# Global logging configuration instance
_logging_config = None

def get_logging_config() -> BMasterAILoggingConfig:
    """Get global logging configuration instance"""
    global _logging_config
    if _logging_config is None:
        _logging_config = BMasterAILoggingConfig()
    return _logging_config

def initialize_logging(config_path: Optional[str] = None) -> BMasterAILoggingConfig:
    """Initialize BMasterAI logging configuration"""
    global _logging_config
    _logging_config = BMasterAILoggingConfig(config_path)
    return _logging_config
