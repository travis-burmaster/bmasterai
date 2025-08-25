
import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
import json
from collections import defaultdict, deque
import statistics

@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    labels: Dict[str, str]

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]

class MetricsCollector:
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Dict[str, Any]] = []
        self.alert_rules: List[Dict[str, Any]] = []
        self._running = False
        self._thread = None

    def start_collection(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()

    def stop_collection(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def _collect_loop(self):
        while self._running:
            try:
                self._collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                print(f"Error collecting metrics: {e}")

    def _collect_system_metrics(self):
        timestamp = datetime.now(timezone.utc)

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics['cpu_percent'].append(MetricPoint(timestamp, cpu_percent, {}))

        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics['memory_percent'].append(MetricPoint(timestamp, memory.percent, {}))
        self.metrics['memory_used_mb'].append(MetricPoint(timestamp, memory.used / 1024 / 1024, {}))

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.metrics['disk_usage_percent'].append(MetricPoint(timestamp, disk_percent, {}))

        # Network metrics
        net_io = psutil.net_io_counters()
        self.metrics['network_bytes_sent'].append(MetricPoint(timestamp, net_io.bytes_sent, {}))
        self.metrics['network_bytes_recv'].append(MetricPoint(timestamp, net_io.bytes_recv, {}))

        # Check alerts
        self._check_alerts()

    def record_custom_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        if labels is None:
            labels = {}

        timestamp = datetime.now(timezone.utc)
        self.custom_metrics[name].append(MetricPoint(timestamp, value, labels))

    def get_metric_stats(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, float]:
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)

        # Check both system and custom metrics
        metric_data = None
        if metric_name in self.metrics:
            metric_data = self.metrics[metric_name]
        elif metric_name in self.custom_metrics:
            metric_data = self.custom_metrics[metric_name]
        else:
            return {}

        # Filter by time
        recent_points = [p for p in metric_data if p.timestamp >= cutoff_time]

        if not recent_points:
            return {}

        values = [p.value for p in recent_points]

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': statistics.mean(values),
            'median': statistics.median(values),
            'latest': values[-1] if values else 0
        }

    def add_alert_rule(self, 
                      metric_name: str, 
                      threshold: float, 
                      condition: str = 'greater_than',
                      duration_minutes: int = 5,
                      callback: Optional[Callable] = None):

        rule = {
            'id': len(self.alert_rules),
            'metric_name': metric_name,
            'threshold': threshold,
            'condition': condition,
            'duration_minutes': duration_minutes,
            'callback': callback,
            'triggered': False,
            'trigger_time': None
        }
        self.alert_rules.append(rule)

    def _check_alerts(self):
        for rule in self.alert_rules:
            stats = self.get_metric_stats(rule['metric_name'], rule['duration_minutes'])

            if not stats:
                continue

            current_value = stats['latest']
            threshold = rule['threshold']
            condition = rule['condition']

            triggered = False
            if condition == 'greater_than' and current_value > threshold:
                triggered = True
            elif condition == 'less_than' and current_value < threshold:
                triggered = True
            elif condition == 'equals' and current_value == threshold:
                triggered = True

            if triggered and not rule['triggered']:
                # New alert
                alert = {
                    'rule_id': rule['id'],
                    'metric_name': rule['metric_name'],
                    'current_value': current_value,
                    'threshold': threshold,
                    'condition': condition,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'message': f"Alert: {rule['metric_name']} is {current_value} (threshold: {threshold})"
                }
                self.alerts.append(alert)
                rule['triggered'] = True
                rule['trigger_time'] = datetime.now(timezone.utc)

                if rule['callback']:
                    try:
                        rule['callback'](alert)
                    except Exception as e:
                        print(f"Error in alert callback: {e}")

            elif not triggered and rule['triggered']:
                # Alert resolved
                rule['triggered'] = False
                rule['trigger_time'] = None

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return sorted(self.alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def export_metrics(self, format: str = 'json') -> str:
        data = {
            'system_metrics': {},
            'custom_metrics': {},
            'export_time': datetime.now(timezone.utc).isoformat()
        }

        # Export system metrics
        for name, points in self.metrics.items():
            data['system_metrics'][name] = [
                {
                    'timestamp': p.timestamp.isoformat(),
                    'value': p.value,
                    'labels': p.labels
                } for p in list(points)[-100:]  # Last 100 points
            ]

        # Export custom metrics
        for name, points in self.custom_metrics.items():
            data['custom_metrics'][name] = [
                {
                    'timestamp': p.timestamp.isoformat(),
                    'value': p.value,
                    'labels': p.labels
                } for p in list(points)[-100:]  # Last 100 points
            ]

        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            return str(data)

class AgentMonitor:
    def __init__(self):
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.task_timings: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.metrics_collector = MetricsCollector()

    def start_monitoring(self):
        self.metrics_collector.start_collection()

    def stop_monitoring(self):
        self.metrics_collector.stop_collection()

    def track_agent_start(self, agent_id: str):
        self.agent_metrics[agent_id]['start_time'] = datetime.now(timezone.utc)
        self.agent_metrics[agent_id]['status'] = 'running'
        self.metrics_collector.record_custom_metric('agents_active', 1, {'agent_id': agent_id})

    def track_agent_stop(self, agent_id: str):
        if agent_id in self.agent_metrics:
            start_time = self.agent_metrics[agent_id].get('start_time')
            if start_time:
                runtime = (datetime.now(timezone.utc) - start_time).total_seconds()
                self.agent_metrics[agent_id]['total_runtime'] = runtime
                self.metrics_collector.record_custom_metric('agent_runtime_seconds', runtime, {'agent_id': agent_id})

            self.agent_metrics[agent_id]['status'] = 'stopped'
            self.agent_metrics[agent_id]['stop_time'] = datetime.now(timezone.utc)

    def track_task_duration(self, agent_id: str, task_name: str, duration_ms: float):
        self.task_timings[f"{agent_id}:{task_name}"].append(duration_ms)
        self.metrics_collector.record_custom_metric(
            'task_duration_ms', 
            duration_ms, 
            {'agent_id': agent_id, 'task_name': task_name}
        )

    def track_error(self, agent_id: str, error_type: str = 'general'):
        key = f"{agent_id}:{error_type}"
        self.error_counts[key] += 1
        self.metrics_collector.record_custom_metric(
            'agent_errors', 
            1, 
            {'agent_id': agent_id, 'error_type': error_type}
        )

    def track_llm_call(self, agent_id: str, model: str, tokens_used: int, duration_ms: float,
                      reasoning_steps: Optional[int] = None, thinking_depth: Optional[int] = None):
        self.metrics_collector.record_custom_metric(
            'llm_tokens_used', 
            tokens_used, 
            {'agent_id': agent_id, 'model': model}
        )
        self.metrics_collector.record_custom_metric(
            'llm_call_duration_ms', 
            duration_ms, 
            {'agent_id': agent_id, 'model': model}
        )
        
        # Track reasoning-specific metrics
        if reasoning_steps is not None:
            self.metrics_collector.record_custom_metric(
                'llm_reasoning_steps',
                reasoning_steps,
                {'agent_id': agent_id, 'model': model}
            )
        
        if thinking_depth is not None:
            self.metrics_collector.record_custom_metric(
                'llm_thinking_depth',
                thinking_depth,
                {'agent_id': agent_id, 'model': model}
            )
    
    def track_reasoning_session(self, agent_id: str, session_id: str, 
                              total_steps: int, duration_ms: float,
                              decision_points: int, final_confidence: Optional[float] = None):
        """Track metrics for a complete reasoning session"""
        labels = {'agent_id': agent_id, 'session_id': session_id}
        
        self.metrics_collector.record_custom_metric('reasoning_session_steps', total_steps, labels)
        self.metrics_collector.record_custom_metric('reasoning_session_duration_ms', duration_ms, labels)
        self.metrics_collector.record_custom_metric('reasoning_decision_points', decision_points, labels)
        
        if final_confidence is not None:
            self.metrics_collector.record_custom_metric('reasoning_confidence_score', final_confidence, labels)

    def get_agent_dashboard(self, agent_id: str) -> Dict[str, Any]:
        dashboard = {
            'agent_id': agent_id,
            'status': self.agent_metrics.get(agent_id, {}).get('status', 'unknown'),
            'metrics': {},
            'recent_errors': [],
            'performance': {}
        }

        # Get task performance
        task_keys = [k for k in self.task_timings.keys() if k.startswith(f"{agent_id}:")]
        for key in task_keys:
            task_name = key.split(':', 1)[1]
            durations = self.task_timings[key]
            if durations:
                dashboard['performance'][task_name] = {
                    'avg_duration_ms': statistics.mean(durations),
                    'min_duration_ms': min(durations),
                    'max_duration_ms': max(durations),
                    'total_calls': len(durations)
                }

        # Get error counts
        error_keys = [k for k in self.error_counts.keys() if k.startswith(f"{agent_id}:")]
        total_errors = sum(self.error_counts[k] for k in error_keys)
        dashboard['metrics']['total_errors'] = total_errors

        # Get system metrics
        dashboard['system'] = {
            'cpu_usage': self.metrics_collector.get_metric_stats('cpu_percent', 10),
            'memory_usage': self.metrics_collector.get_metric_stats('memory_percent', 10)
        }

        return dashboard

    def get_system_health(self) -> Dict[str, Any]:
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system_metrics': {
                'cpu': self.metrics_collector.get_metric_stats('cpu_percent', 30),
                'memory': self.metrics_collector.get_metric_stats('memory_percent', 30),
                'disk': self.metrics_collector.get_metric_stats('disk_usage_percent', 30)
            },
            'active_agents': len([a for a in self.agent_metrics.values() if a.get('status') == 'running']),
            'total_agents': len(self.agent_metrics),
            'recent_alerts': self.metrics_collector.get_recent_alerts(10)
        }

# Global monitor instance
_monitor_instance = None

def get_monitor() -> AgentMonitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AgentMonitor()
    return _monitor_instance
