
"""
Logging mixin for agents to integrate BMasterAI logging capabilities
"""

import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

from config.logging_config import get_logging_config

class LoggingMixin:
    """Mixin class to add BMasterAI logging capabilities to agents"""
    
    def __init__(self, *args, **kwargs):
        # Initialize logging components without calling super()
        # since this is a mixin class
        try:
            self.logging_config = get_logging_config()
            self.component_logger = self.logging_config.get_logger(self.__class__.__name__)
        except Exception as e:
            # Fallback to standard logging if BMasterAI config fails
            import logging
            self.logging_config = None
            self.component_logger = logging.getLogger(self.__class__.__name__)
            
        self.current_task_id = None
        self.task_start_time = None
        
        # Call super() only if there are other classes in the MRO
        if hasattr(super(), '__init__'):
            super().__init__(*args, **kwargs)
    
    def start_task_logging(self, task_description: str, task_id: Optional[str] = None):
        """Start logging for a new task"""
        self.current_task_id = task_id or str(uuid.uuid4())
        self.task_start_time = time.time()
        
        if self.logging_config:
            self.logging_config.log_agent_start(
                agent_name=self.__class__.__name__,
                task_id=self.current_task_id,
                task_description=task_description
            )
        
        self.component_logger.info(f"Started task: {task_description} (ID: {self.current_task_id})")
        return self.current_task_id
    
    def complete_task_logging(self, success: bool = True, result_size: int = 0):
        """Complete logging for the current task"""
        if self.current_task_id and self.task_start_time:
            duration = time.time() - self.task_start_time
            
            if self.logging_config:
                self.logging_config.log_agent_completion(
                    agent_name=self.__class__.__name__,
                    task_id=self.current_task_id,
                    success=success,
                    duration=duration,
                    result_size=result_size
                )
            
            status = "completed" if success else "failed"
            self.component_logger.info(f"Task {status}: {self.current_task_id} in {duration:.2f}s")
            
            # Reset task tracking
            self.current_task_id = None
            self.task_start_time = None
    
    def log_api_call(self, api_name: str, endpoint: str, duration: float, 
                     status_code: int, request_size: int = 0, response_size: int = 0):
        """Log API call metrics"""
        if self.logging_config:
            self.logging_config.log_api_call(
                api_name=api_name,
                endpoint=endpoint,
                duration=duration,
                status_code=status_code,
                request_size=request_size,
                response_size=response_size
            )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        error_context = context or {}
        if self.current_task_id:
            error_context['task_id'] = self.current_task_id
        
        if self.logging_config:
            self.logging_config.log_error(
                component=self.__class__.__name__,
                error=error,
                context=error_context
            )
        else:
            self.component_logger.error(f"Error: {str(error)}", exc_info=True)
    
    def log_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Log custom metric"""
        metric_tags = tags or {}
        metric_tags['agent'] = self.__class__.__name__
        if self.current_task_id:
            metric_tags['task_id'] = self.current_task_id
        
        if self.logging_config:
            self.logging_config.log_metric(metric_name, value, metric_tags)
        else:
            self.component_logger.info(f"Metric {metric_name}: {value} {metric_tags}")
    
    def log_info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message with optional extra data"""
        if extra:
            self.component_logger.info(f"{message} | Extra: {extra}")
        else:
            self.component_logger.info(message)
    
    def log_warning(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message with optional extra data"""
        if extra:
            self.component_logger.warning(f"{message} | Extra: {extra}")
        else:
            self.component_logger.warning(message)
    
    def log_debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message with optional extra data"""
        if extra:
            self.component_logger.debug(f"{message} | Extra: {extra}")
        else:
            self.component_logger.debug(message)
    
    def create_performance_context(self, operation_name: str):
        """Create performance monitoring context"""
        if self.logging_config:
            return self.logging_config.create_performance_context(
                f"{self.__class__.__name__}.{operation_name}"
            )
        else:
            # Simple fallback context
            class SimpleContext:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return SimpleContext()

def log_agent_method(method_name: Optional[str] = None):
    """Decorator to automatically log agent method calls"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if not hasattr(self, 'component_logger'):
                return await func(self, *args, **kwargs)
            
            operation_name = method_name or func.__name__
            start_time = time.time()
            
            try:
                self.log_debug(f"Starting method: {operation_name}")
                result = await func(self, *args, **kwargs)
                
                duration = time.time() - start_time
                self.log_metric(f"method_duration_{operation_name}", duration)
                self.log_debug(f"Completed method: {operation_name} in {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                self.log_error(e, {
                    'method': operation_name,
                    'duration': duration,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                raise
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if not hasattr(self, 'component_logger'):
                return func(self, *args, **kwargs)
            
            operation_name = method_name or func.__name__
            start_time = time.time()
            
            try:
                self.log_debug(f"Starting method: {operation_name}")
                result = func(self, *args, **kwargs)
                
                duration = time.time() - start_time
                self.log_metric(f"method_duration_{operation_name}", duration)
                self.log_debug(f"Completed method: {operation_name} in {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                self.log_error(e, {
                    'method': operation_name,
                    'duration': duration,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                raise
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
