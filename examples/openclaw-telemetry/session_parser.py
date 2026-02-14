"""
OpenClaw Session Parser
Parses OpenClaw JSONL session files and extracts telemetry data

Enhanced with BMasterAI monitoring and alerting
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sqlite3

# BMasterAI integration
try:
    from bmasterai import configure_logging, get_logger, get_monitor, EventType, LogLevel
    BMASTERAI_AVAILABLE = True
except ImportError:
    BMASTERAI_AVAILABLE = False
    print("⚠️ bmasterai not installed. Install with: pip install bmasterai==0.2.1")


class OpenClawSessionParser:
    def __init__(self, sessions_dir: str, db_path: str = "openclaw_telemetry.db", 
                 enable_bmasterai: bool = True):
        self.sessions_dir = Path(sessions_dir)
        self.db_path = db_path
        self.enable_bmasterai = enable_bmasterai and BMASTERAI_AVAILABLE
        
        # Initialize BMasterAI if available
        if self.enable_bmasterai:
            self.logger = configure_logging(
                log_level=LogLevel.INFO,
                log_file="openclaw_telemetry.log",
                json_log_file="openclaw_telemetry.jsonl"
            )
            self.monitor = get_monitor()
            self.monitor.start_monitoring()
            
            # Configure alert rules
            self._setup_alerts()
            print("✅ BMasterAI monitoring enabled")
        else:
            self.logger = None
            self.monitor = None
        
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for telemetry storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                model TEXT,
                provider TEXT,
                thinking_level TEXT,
                total_messages INTEGER DEFAULT 0,
                total_tool_calls INTEGER DEFAULT 0,
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                total_cache_read_tokens INTEGER DEFAULT 0,
                total_cache_write_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0
            )
        """)
        
        # Messages table (for timeline)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                role TEXT,
                message_type TEXT,
                model TEXT,
                provider TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cache_read_tokens INTEGER DEFAULT 0,
                cache_write_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                stop_reason TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Tool calls table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                message_id TEXT,
                timestamp TEXT,
                tool_name TEXT,
                parameters TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _setup_alerts(self):
        """Configure BMasterAI alert rules"""
        if not self.enable_bmasterai:
            return
        
        # Note: Alert rules require bmasterai >=0.2.1
        # For now, we'll track metrics and check thresholds manually
        try:
            # Alert if session cost exceeds $1
            self.monitor.add_alert_rule(
                name="high_session_cost",
                metric="session_cost",
                condition="greater_than",
                threshold=1.0,
                notification_channels=["console"]
            )
            
            # Alert if token rate is very high (>20k tokens in a session)
            self.monitor.add_alert_rule(
                name="high_token_usage",
                metric="session_total_tokens",
                condition="greater_than",
                threshold=20000,
                notification_channels=["console"]
            )
        except AttributeError:
            # Older version of bmasterai doesn't support alert rules
            pass
    
    def _record_bmasterai_metrics(self, session_data: Dict[str, Any]):
        """Record custom metrics to BMasterAI monitor"""
        if not self.enable_bmasterai:
            return
        
        try:
            totals = session_data['totals']
            labels = {
                "session_id": session_data['session_id'],
                "model": session_data['model'] or "unknown",
                "provider": session_data['provider'] or "unknown"
            }
            
            # Only record if the method exists (bmasterai >=0.2.1)
            if hasattr(self.monitor, 'record_custom_metric'):
                # Record session-level metrics
                self.monitor.record_custom_metric(
                    "session_total_tokens",
                    totals['total_tokens'],
                    labels
                )
                
                self.monitor.record_custom_metric(
                    "session_cost",
                    totals['cost'],
                    labels
                )
                
                self.monitor.record_custom_metric(
                    "session_tool_calls",
                    totals['tool_call_count'],
                    labels
                )
                
                # Calculate cache hit rate
                total_tokens = totals['input_tokens'] + totals['output_tokens']
                if total_tokens > 0:
                    cache_hit_rate = totals['cache_read_tokens'] / total_tokens
                    self.monitor.record_custom_metric(
                        "cache_hit_rate",
                        cache_hit_rate,
                        labels
                    )
                
                # Calculate cost efficiency (tokens per dollar)
                if totals['cost'] > 0:
                    tokens_per_dollar = totals['total_tokens'] / totals['cost']
                    self.monitor.record_custom_metric(
                        "tokens_per_dollar",
                        tokens_per_dollar,
                        labels
                    )
        except Exception as e:
            # Silently fail if bmasterai API doesn't match
            pass
    
    def parse_session_file(self, session_file: Path) -> Dict[str, Any]:
        """Parse a single session JSONL file"""
        session_id = session_file.stem
        
        session_data = {
            "session_id": session_id,
            "start_time": None,
            "end_time": None,
            "model": None,
            "provider": None,
            "thinking_level": None,
            "messages": [],
            "tool_calls": [],
            "totals": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "message_count": 0,
                "tool_call_count": 0
            }
        }
        
        with open(session_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_type = event.get('type')
                    
                    # Session metadata
                    if event_type == 'session':
                        session_data['start_time'] = event.get('timestamp')
                    
                    elif event_type == 'model_change':
                        session_data['provider'] = event.get('provider')
                        session_data['model'] = event.get('modelId')
                    
                    elif event_type == 'thinking_level_change':
                        session_data['thinking_level'] = event.get('thinkingLevel')
                    
                    # Messages with usage data
                    elif event_type == 'message':
                        msg = event.get('message', {})
                        usage = msg.get('usage', {})
                        
                        if usage:  # Only track assistant messages with usage
                            message_data = {
                                "id": event.get('id'),
                                "session_id": session_id,
                                "timestamp": event.get('timestamp'),
                                "role": msg.get('role'),
                                "message_type": event_type,
                                "model": msg.get('model'),
                                "provider": msg.get('provider'),
                                "input_tokens": usage.get('input', 0),
                                "output_tokens": usage.get('output', 0),
                                "cache_read_tokens": usage.get('cacheRead', 0),
                                "cache_write_tokens": usage.get('cacheWrite', 0),
                                "total_tokens": usage.get('totalTokens', 0),
                                "cost": usage.get('cost', {}).get('total', 0.0),
                                "stop_reason": msg.get('stopReason')
                            }
                            
                            session_data['messages'].append(message_data)
                            session_data['end_time'] = event.get('timestamp')
                            
                            # Update totals
                            session_data['totals']['input_tokens'] += message_data['input_tokens']
                            session_data['totals']['output_tokens'] += message_data['output_tokens']
                            session_data['totals']['cache_read_tokens'] += message_data['cache_read_tokens']
                            session_data['totals']['cache_write_tokens'] += message_data['cache_write_tokens']
                            session_data['totals']['total_tokens'] += message_data['total_tokens']
                            session_data['totals']['cost'] += message_data['cost']
                            session_data['totals']['message_count'] += 1
                            
                            # Extract tool calls from content
                            content = msg.get('content', [])
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'toolCall':
                                    # Serialize parameters as JSON (OpenClaw uses "arguments" field)
                                    params = item.get('arguments', {})
                                    params_json = json.dumps(params) if params else None
                                    
                                    tool_call = {
                                        "id": item.get('id'),
                                        "session_id": session_id,
                                        "message_id": event.get('id'),
                                        "timestamp": event.get('timestamp'),
                                        "tool_name": item.get('name'),
                                        "parameters": params_json
                                    }
                                    session_data['tool_calls'].append(tool_call)
                                    session_data['totals']['tool_call_count'] += 1
                
                except json.JSONDecodeError:
                    continue
        
        return session_data
    
    def save_to_database(self, session_data: Dict[str, Any]):
        """Save parsed session data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or update session
        cursor.execute("""
            INSERT OR REPLACE INTO sessions 
            (session_id, start_time, end_time, model, provider, thinking_level,
             total_messages, total_tool_calls, total_input_tokens, total_output_tokens,
             total_cache_read_tokens, total_cache_write_tokens, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data['session_id'],
            session_data['start_time'],
            session_data['end_time'],
            session_data['model'],
            session_data['provider'],
            session_data['thinking_level'],
            session_data['totals']['message_count'],
            session_data['totals']['tool_call_count'],
            session_data['totals']['input_tokens'],
            session_data['totals']['output_tokens'],
            session_data['totals']['cache_read_tokens'],
            session_data['totals']['cache_write_tokens'],
            session_data['totals']['cost']
        ))
        
        # Insert messages
        for msg in session_data['messages']:
            cursor.execute("""
                INSERT OR REPLACE INTO messages
                (id, session_id, timestamp, role, message_type, model, provider,
                 input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                 total_tokens, cost, stop_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                msg['id'], msg['session_id'], msg['timestamp'], msg['role'],
                msg['message_type'], msg['model'], msg['provider'],
                msg['input_tokens'], msg['output_tokens'], msg['cache_read_tokens'],
                msg['cache_write_tokens'], msg['total_tokens'], msg['cost'],
                msg['stop_reason']
            ))
        
        # Insert tool calls
        for tool in session_data['tool_calls']:
            cursor.execute("""
                INSERT OR REPLACE INTO tool_calls
                (id, session_id, message_id, timestamp, tool_name, parameters)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tool['id'], tool['session_id'], tool['message_id'],
                tool['timestamp'], tool['tool_name'], tool.get('parameters')
            ))
        
        conn.commit()
        conn.close()
        
        # Record BMasterAI metrics
        self._record_bmasterai_metrics(session_data)
    
    def get_bmasterai_alerts(self):
        """Get active alerts from BMasterAI monitor"""
        if not self.enable_bmasterai:
            return []
        
        try:
            if hasattr(self.monitor, 'get_active_alerts'):
                return self.monitor.get_active_alerts()
        except:
            pass
        return []
    
    def get_bmasterai_metrics(self, metric_name: str, duration_minutes: int = 60):
        """Get metric statistics from BMasterAI monitor"""
        if not self.enable_bmasterai:
            return {}
        
        try:
            if hasattr(self.monitor, 'get_metric_stats'):
                return self.monitor.get_metric_stats(metric_name, duration_minutes)
        except:
            pass
        return {}
    
    def get_exec_history(self, limit: int = 100):
        """Get history of all exec command calls with parameters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                t.timestamp,
                t.session_id,
                s.model,
                t.parameters
            FROM tool_calls t
            LEFT JOIN sessions s ON t.session_id = s.session_id
            WHERE t.tool_name = 'exec'
            ORDER BY t.timestamp DESC
            LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        results = []
        
        for row in cursor.fetchall():
            timestamp, session_id, model, params_json = row
            
            # Parse parameters JSON
            command = None
            if params_json:
                try:
                    params = json.loads(params_json)
                    command = params.get('command', 'N/A')
                except:
                    command = 'Error parsing params'
            else:
                command = 'No params stored'
            
            results.append({
                'timestamp': timestamp,
                'session_id': session_id[:8] + '...' if session_id else 'N/A',
                'model': model or 'N/A',
                'command': command
            })
        
        conn.close()
        return results
    
    def scan_all_sessions(self):
        """Scan all session files in the sessions directory"""
        print(f"Scanning sessions in {self.sessions_dir}...")
        session_files = list(self.sessions_dir.glob("*.jsonl"))
        
        for idx, session_file in enumerate(session_files, 1):
            print(f"Processing {idx}/{len(session_files)}: {session_file.name}")
            try:
                session_data = self.parse_session_file(session_file)
                self.save_to_database(session_data)
            except Exception as e:
                print(f"Error processing {session_file.name}: {e}")
        
        print(f"✅ Processed {len(session_files)} sessions")
        
        # Show BMasterAI summary if enabled
        if self.enable_bmasterai:
            print("\n📊 BMasterAI Metrics Summary:")
            
            # Get active alerts
            alerts = self.get_bmasterai_alerts()
            if alerts:
                print(f"   🚨 Active Alerts: {len(alerts)}")
                for alert in alerts:
                    print(f"      - {alert['name']}: {alert.get('message', 'N/A')}")
            else:
                print("   ✅ No active alerts")
            
            # Show some key metrics
            metrics_to_show = [
                ("session_cost", "Session Cost"),
                ("session_total_tokens", "Total Tokens"),
                ("cache_hit_rate", "Cache Hit Rate")
            ]
            
            for metric_name, display_name in metrics_to_show:
                stats = self.get_bmasterai_metrics(metric_name)
                if stats:
                    print(f"   {display_name}: avg={stats.get('avg', 0):.2f}, max={stats.get('max', 0):.2f}")


if __name__ == "__main__":
    # Default OpenClaw sessions directory
    sessions_dir = "/home/tadmin/.openclaw/agents/main/sessions"
    
    parser = OpenClawSessionParser(sessions_dir)
    parser.scan_all_sessions()
