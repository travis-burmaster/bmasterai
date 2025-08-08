
"""BMasterAI-style monitoring implementation for MCP GitHub Analyzer"""
import time
import psutil
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
import json
from collections import defaultdict, deque
import streamlit as st

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int

@dataclass
class AgentMetrics:
    """Agent-specific metrics"""
    agent_id: str
    tasks_completed: int
    tasks_failed: int
    average_task_duration: float
    total_execution_time: float
    error_rate: float
    last_activity: str

@dataclass
class AlertRule:
    """Alert rule configuration"""
    metric_name: str
    threshold: float
    condition: str  # "greater_than", "less_than", "equals"
    duration_minutes: int
    callback: Optional[Callable] = None

class MetricsCollector:
    """Metrics collection and alerting system"""
    
    def __init__(self):
        self.system_metrics_history = deque(maxlen=1000)
        self.agent_metrics = defaultdict(lambda: {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "task_durations": deque(maxlen=100),
            "total_execution_time": 0.0,
            "last_activity": None
        })
        self.custom_metrics = defaultdict(deque)
        self.alert_rules = []
        self.active_alerts = {}
        self.is_collecting = False
        self.collection_thread = None
        
    def start_collection(self, interval_seconds: int = 30):
        """Start metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.collection_thread.start()
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1)
    
    def _collect_metrics_loop(self, interval_seconds: int):
        """Main metrics collection loop"""
        while self.is_collecting:
            try:
                self._collect_system_metrics()
                self._check_alert_rules()
                time.sleep(interval_seconds)
            except Exception as e:
                print(f"Error in metrics collection: {e}")
                time.sleep(interval_seconds)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=(disk.used / disk.total) * 100,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv
            )
            
            self.system_metrics_history.append(metrics)
            
            # Store in custom metrics for alerting
            self.record_custom_metric("cpu_percent", cpu_percent, {})
            self.record_custom_metric("memory_percent", memory.percent, {})
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
    
    def track_agent_start(self, agent_id: str):
        """Track agent start event"""
        self.agent_metrics[agent_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
    
    def track_agent_stop(self, agent_id: str):
        """Track agent stop event"""
        self.agent_metrics[agent_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
    
    def track_task_duration(self, agent_id: str, task_name: str, duration_ms: float):
        """Track task execution duration"""
        metrics = self.agent_metrics[agent_id]
        metrics["tasks_completed"] += 1
        metrics["task_durations"].append(duration_ms)
        metrics["total_execution_time"] += duration_ms
        metrics["last_activity"] = datetime.now(timezone.utc).isoformat()
    
    def track_error(self, agent_id: str, error_type: str):
        """Track error occurrence"""
        metrics = self.agent_metrics[agent_id]
        metrics["tasks_failed"] += 1
        metrics["last_activity"] = datetime.now(timezone.utc).isoformat()
        
        # Record error metric
        self.record_custom_metric("agent_errors", 1, {"agent_id": agent_id, "error_type": error_type})
    
    def track_llm_call(self, agent_id: str, model: str, tokens_used: int, duration_ms: float):
        """Track LLM call metrics"""
        self.record_custom_metric("llm_tokens_used", tokens_used, 
                                {"agent_id": agent_id, "model": model})
        self.record_custom_metric("llm_call_duration", duration_ms,
                                {"agent_id": agent_id, "model": model})
    
    def record_custom_metric(self, metric_name: str, value: float, tags: Dict[str, str]):
        """Record a custom metric"""
        metric_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": value,
            "tags": tags
        }
        self.custom_metrics[metric_name].append(metric_entry)
        
        # Keep only recent metrics (last 1000 entries)
        if len(self.custom_metrics[metric_name]) > 1000:
            self.custom_metrics[metric_name].popleft()
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules.append(rule)
    
    def _check_alert_rules(self):
        """Check all alert rules and trigger alerts"""
        for rule in self.alert_rules:
            try:
                self._check_single_rule(rule)
            except Exception as e:
                print(f"Error checking alert rule {rule.metric_name}: {e}")
    
    def _check_single_rule(self, rule: AlertRule):
        """Check a single alert rule"""
        metric_name = rule.metric_name
        
        # Get recent values for the metric
        if metric_name not in self.custom_metrics:
            return
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=rule.duration_minutes)
        recent_values = []
        
        for entry in self.custom_metrics[metric_name]:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff_time:
                recent_values.append(entry["value"])
        
        if not recent_values:
            return
        
        # Check condition
        avg_value = sum(recent_values) / len(recent_values)
        triggered = False
        
        if rule.condition == "greater_than" and avg_value > rule.threshold:
            triggered = True
        elif rule.condition == "less_than" and avg_value < rule.threshold:
            triggered = True
        elif rule.condition == "equals" and abs(avg_value - rule.threshold) < 0.001:
            triggered = True
        
        alert_key = f"{metric_name}_{rule.threshold}_{rule.condition}"
        
        if triggered and alert_key not in self.active_alerts:
            # New alert
            alert_data = {
                "metric_name": metric_name,
                "threshold": rule.threshold,
                "current_value": avg_value,
                "condition": rule.condition,
                "duration_minutes": rule.duration_minutes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"{metric_name} {rule.condition} {rule.threshold} for {rule.duration_minutes} minutes"
            }
            
            self.active_alerts[alert_key] = alert_data
            
            if rule.callback:
                try:
                    rule.callback(alert_data)
                except Exception as e:
                    print(f"Error executing alert callback: {e}")
        
        elif not triggered and alert_key in self.active_alerts:
            # Alert resolved
            del self.active_alerts[alert_key]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health dashboard"""
        if not self.system_metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.system_metrics_history[-1]
        
        # Calculate active agents
        active_agents = len([
            agent_id for agent_id, metrics in self.agent_metrics.items()
            if metrics["last_activity"] and 
            datetime.fromisoformat(metrics["last_activity"]) > 
            datetime.now(timezone.utc) - timedelta(minutes=10)
        ])
        
        # Calculate totals
        total_tasks = sum(metrics["tasks_completed"] for metrics in self.agent_metrics.values())
        total_errors = sum(metrics["tasks_failed"] for metrics in self.agent_metrics.values())
        
        # Calculate average task duration
        all_durations = []
        for metrics in self.agent_metrics.values():
            all_durations.extend(list(metrics["task_durations"]))
        avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
        
        return {
            "timestamp": latest_metrics.timestamp,
            "active_agents": active_agents,
            "total_tasks_completed": total_tasks,
            "total_errors": total_errors,
            "average_task_duration": avg_duration,
            "error_rate": (total_errors / max(total_tasks, 1)) * 100,
            "system_metrics": {
                "cpu": {"current": latest_metrics.cpu_percent},
                "memory": {"current": latest_metrics.memory_percent},
                "disk": {"current": latest_metrics.disk_usage_percent}
            },
            "active_alerts": list(self.active_alerts.values())
        }
    
    def get_agent_dashboard(self, agent_id: str) -> Dict[str, Any]:
        """Get agent-specific dashboard"""
        if agent_id not in self.agent_metrics:
            return {"agent_id": agent_id, "status": "not_found"}
        
        metrics = self.agent_metrics[agent_id]
        
        # Calculate average duration
        durations = list(metrics["task_durations"])
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Calculate error rate
        total_tasks = metrics["tasks_completed"] + metrics["tasks_failed"]
        error_rate = (metrics["tasks_failed"] / max(total_tasks, 1)) * 100
        
        return AgentMetrics(
            agent_id=agent_id,
            tasks_completed=metrics["tasks_completed"],
            tasks_failed=metrics["tasks_failed"],
            average_task_duration=avg_duration,
            total_execution_time=metrics["total_execution_time"],
            error_rate=error_rate,
            last_activity=metrics["last_activity"] or "Never"
        )
    
    def get_metrics_history(self, metric_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get historical data for a metric"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        if metric_name == "system":
            return [
                asdict(metrics) for metrics in self.system_metrics_history
                if datetime.fromisoformat(metrics.timestamp) >= cutoff_time
            ]
        elif metric_name in self.custom_metrics:
            return [
                entry for entry in self.custom_metrics[metric_name]
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
            ]
        else:
            return []

class Monitor:
    """Main monitoring system"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self._started = False
    
    def start_monitoring(self, collection_interval: int = 30):
        """Start the monitoring system"""
        if not self._started:
            self.metrics_collector.start_collection(collection_interval)
            self._started = True
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        if self._started:
            self.metrics_collector.stop_collection()
            self._started = False
    
    def track_agent_start(self, agent_id: str):
        """Track agent start"""
        self.metrics_collector.track_agent_start(agent_id)
    
    def track_agent_stop(self, agent_id: str):
        """Track agent stop"""
        self.metrics_collector.track_agent_stop(agent_id)
    
    def track_task_duration(self, agent_id: str, task_name: str, duration_ms: float):
        """Track task duration"""
        self.metrics_collector.track_task_duration(agent_id, task_name, duration_ms)
    
    def track_error(self, agent_id: str, error_type: str):
        """Track error"""
        self.metrics_collector.track_error(agent_id, error_type)
    
    def track_llm_call(self, agent_id: str, model: str, tokens_used: int, duration_ms: float):
        """Track LLM call"""
        self.metrics_collector.track_llm_call(agent_id, model, tokens_used, duration_ms)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health dashboard"""
        return self.metrics_collector.get_system_health()
    
    def get_agent_dashboard(self, agent_id: str) -> Dict[str, Any]:
        """Get agent dashboard"""
        return self.metrics_collector.get_agent_dashboard(agent_id)

# Global monitor instance
_monitor_instance = None

@st.cache_resource
def get_monitor() -> Monitor:
    """Get the global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = Monitor()
    return _monitor_instance
